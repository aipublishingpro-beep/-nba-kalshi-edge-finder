import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== DAILY DATE KEY (INVALIDATION GATE) ==========
today_str = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d")

# Fixed CSS - works with current Streamlit DOM structure
st.markdown("""
<style>
/* Make radio labels clickable again */
div[role="radiogroup"] label {
    cursor: pointer;
}

/* YES / NO pill styling */
div[role="radiogroup"] label span {
    padding: 8px 18px;
    border-radius: 10px;
    display: inline-block;
    font-weight: 700;
}

/* Selected state */
div[role="radiogroup"] input:checked + div span {
    box-shadow: inset 0 0 0 2px white;
}

/* NO (first option) - Green */
div[role="radiogroup"] label:nth-of-type(1) span {
    background: linear-gradient(135deg, #102a1a, #163a26);
    border: 2px solid #00ff88;
    color: #ccffee;
}

/* YES (second option) - Red */
div[role="radiogroup"] label:nth-of-type(2) span {
    background: linear-gradient(135deg, #2a1515, #3a1a1a);
    border: 2px solid #ff4444;
    color: #ffcccc;
}

.stLinkButton > a {
    background-color: #00aa00 !important;
    border-color: #00aa00 !important;
    color: white !important;
}
.stLinkButton > a:hover {
    background-color: #00cc00 !important;
    border-color: #00cc00 !important;
}
</style>
""", unsafe_allow_html=True)

# ========== ENCRYPTION FUNCTIONS ==========
SALT = b'nba_edge_finder_2025'

def get_encryption_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_api_key(api_key: str, password: str) -> str:
    key = get_encryption_key(password)
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str, password: str) -> str:
    try:
        key = get_encryption_key(password)
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode()).decode()
    except:
        return None

# ========== PERSISTENT STORAGE ==========
POSITIONS_FILE = "nba_positions.json"
CREDENTIALS_FILE = "kalshi_creds.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load positions: {e}")
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save positions: {e}")

def load_credentials():
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_credentials(creds):
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(creds, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save credentials: {e}")

# ========== KALSHI API FUNCTIONS ==========
KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

def kalshi_login(email: str, password: str):
    try:
        resp = requests.post(f"{KALSHI_API_BASE}/login", json={"email": email, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("token"), data.get("member_id")
        return None, None
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None, None

def kalshi_get_balance(token: str):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{KALSHI_API_BASE}/portfolio/balance", headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("balance", 0) / 100
        return None
    except:
        return None

def resolve_kalshi_market_id(ticker):
    """Resolve ticker slug to numeric market_id"""
    try:
        resp = requests.get(
            f"{KALSHI_API_BASE}/markets",
            params={"ticker": ticker, "status": "open"},
            timeout=10
        )
        if resp.status_code != 200:
            return None, f"API error: {resp.status_code}"
        markets = resp.json().get("markets", [])
        for m in markets:
            if m.get("ticker") == ticker:
                return m.get("id"), None  # Return numeric ID
        # Try search if exact match fails
        resp2 = requests.get(
            f"{KALSHI_API_BASE}/markets",
            params={"search": ticker, "status": "open"},
            timeout=10
        )
        if resp2.status_code == 200:
            markets2 = resp2.json().get("markets", [])
            for m in markets2:
                if ticker.lower() in m.get("ticker", "").lower():
                    return m.get("id"), None
        return None, "Market not found in open markets"
    except Exception as e:
        return None, str(e)

def kalshi_place_order_by_id(market_id: str, side: str, yes_no: str, price: int, contracts: int):
    """Place order using market_id instead of ticker"""
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        import time
        
        api_key = st.session_state.kalshi_api_key
        private_key_pem = st.session_state.kalshi_private_key
        
        if not api_key or not private_key_pem:
            return False, "API keys not configured"
        
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        timestamp = str(int(time.time() * 1000))
        method = "POST"
        path = "/trade-api/v2/portfolio/orders"
        message = f"{timestamp}{method}{path}"
        
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        sig_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        
        order_data = {
            "ticker": market_id,  # Kalshi accepts ticker here
            "action": side,
            "side": yes_no.lower(),
            "type": "limit",
            "count": contracts,
            "yes_price": price
        }
        
        resp = requests.post(f"{KALSHI_API_BASE}/portfolio/orders", headers=headers, json=order_data, timeout=10)
        if resp.status_code in [200, 201]:
            return True, resp.json()
        return False, f"Status {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def kalshi_place_order(ticker: str, side: str, yes_no: str, price: int, contracts: int):
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        import time
        
        api_key = st.session_state.kalshi_api_key
        private_key_pem = st.session_state.kalshi_private_key
        
        if not api_key or not private_key_pem:
            return False, "API keys not configured"
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        # Create signature - Kalshi uses RSA-PSS, not PKCS1v15
        timestamp = str(int(time.time() * 1000))
        method = "POST"
        path = "/trade-api/v2/portfolio/orders"
        message = f"{timestamp}{method}{path}"
        
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        sig_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        
        order_data = {
            "ticker": ticker,
            "action": side,
            "side": yes_no.lower(),
            "type": "limit",
            "count": contracts,
            "yes_price" if yes_no.upper() == "YES" else "no_price": price
        }
        
        resp = requests.post(f"{KALSHI_API_BASE}/portfolio/orders", headers=headers, json=order_data, timeout=10)
        if resp.status_code in [200, 201]:
            return True, resp.json()
        return False, f"Status {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def get_kalshi_ticker(away_team, home_team, market_type="totals"):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    if market_type == "totals":
        return f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    else:
        return f"KXNBAGAME-{date_str}{away_code}{home_code}"

def get_kalshi_ml_ticker(team):
    """Get ML ticker for a specific team win market"""
    team_code = KALSHI_CODES.get(team)
    if not team_code:
        return None
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%Y%m%d")  # YYYYMMDD format for NBA
    return f"kxnbagame-{date_str}-{team_code}"

# ========== SESSION STATE INIT ==========
# Prevent phantom rerenders by setting defaults first
st.session_state.setdefault("totals_side_radio", "NO (Under)")
st.session_state.setdefault("ml_pick_radio", None)

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if 'default_contracts' not in st.session_state:
    st.session_state.default_contracts = 1
if "selected_side" not in st.session_state:
    st.session_state.selected_side = "NO"
if "selected_threshold" not in st.session_state:
    st.session_state.selected_threshold = 225.5
if "selected_ml_pick" not in st.session_state:
    st.session_state.selected_ml_pick = None
if "kalshi_token" not in st.session_state:
    st.session_state.kalshi_token = None
if "kalshi_balance" not in st.session_state:
    st.session_state.kalshi_balance = None
if "trading_enabled" not in st.session_state:
    st.session_state.trading_enabled = False
if "kalshi_api_key" not in st.session_state:
    st.session_state.kalshi_api_key = ""
if "kalshi_private_key" not in st.session_state:
    st.session_state.kalshi_private_key = ""

# ========== DATE INVALIDATION GUARD ==========
# Wipe stale snapshot/scores when date changes (midnight reset)
if "snapshot_date" not in st.session_state or st.session_state["snapshot_date"] != today_str:
    st.session_state["snapshot_date"] = today_str
    st.session_state.pop("big_snapshot", None)
    st.session_state.pop("ml_picks", None)
    st.session_state.pop("cached_games", None)
    st.session_state.pop("cached_injuries", None)

if st.session_state.auto_refresh:
    st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

# ========== KALSHI TEAM CODES ==========
KALSHI_CODES = {
    "Atlanta": "atl", "Boston": "bos", "Brooklyn": "bkn", "Charlotte": "cha",
    "Chicago": "chi", "Cleveland": "cle", "Dallas": "dal", "Denver": "den",
    "Detroit": "det", "Golden State": "gsw", "Houston": "hou", "Indiana": "ind",
    "LA Clippers": "lac", "LA Lakers": "lal", "Memphis": "mem", "Miami": "mia",
    "Milwaukee": "mil", "Minnesota": "min", "New Orleans": "nop", "New York": "nyk",
    "Oklahoma City": "okc", "Orlando": "orl", "Philadelphia": "phi", "Phoenix": "phx",
    "Portland": "por", "Sacramento": "sac", "San Antonio": "sas", "Toronto": "tor",
    "Utah": "uta", "Washington": "was"
}

def build_kalshi_totals_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    ticker = f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBATOTAL/{ticker}"

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBAGAME/{ticker}"

# ========== STAR PLAYERS DATABASE ==========
STAR_PLAYERS_DB = {
    "Atlanta": {"Trae Young": (3, "O"), "Dejounte Murray": (2, "B"), "Jalen Johnson": (2, "B")},
    "Boston": {"Jayson Tatum": (3, "B"), "Jaylen Brown": (3, "O"), "Derrick White": (2, "D"), "Kristaps Porzingis": (2, "B")},
    "Brooklyn": {"Mikal Bridges": (2, "B"), "Cam Thomas": (2, "O"), "Ben Simmons": (1, "D")},
    "Charlotte": {"LaMelo Ball": (3, "O"), "Brandon Miller": (2, "O"), "Miles Bridges": (2, "B")},
    "Chicago": {"Zach LaVine": (2, "O"), "DeMar DeRozan": (2, "O"), "Coby White": (2, "O")},
    "Cleveland": {"Donovan Mitchell": (3, "O"), "Darius Garland": (2, "O"), "Evan Mobley": (2, "D"), "Jarrett Allen": (2, "D")},
    "Dallas": {"Luka Doncic": (3, "O"), "Kyrie Irving": (3, "O"), "PJ Washington": (2, "D"), "Dereck Lively II": (2, "D")},
    "Denver": {"Nikola Jokic": (3, "B"), "Jamal Murray": (3, "O"), "Aaron Gordon": (2, "D"), "Michael Porter Jr.": (2, "O")},
    "Detroit": {"Cade Cunningham": (2, "O"), "Jaden Ivey": (2, "O"), "Jalen Duren": (1, "D")},
    "Golden State": {"Stephen Curry": (3, "O"), "Draymond Green": (2, "D"), "Andrew Wiggins": (2, "B"), "Klay Thompson": (2, "O")},
    "Houston": {"Jalen Green": (2, "O"), "Alperen Sengun": (2, "B"), "Fred VanVleet": (2, "O"), "Jabari Smith Jr.": (2, "D")},
    "Indiana": {"Tyrese Haliburton": (3, "O"), "Pascal Siakam": (2, "B"), "Myles Turner": (2, "D"), "Bennedict Mathurin": (2, "O")},
    "LA Clippers": {"Kawhi Leonard": (3, "B"), "Paul George": (3, "B"), "James Harden": (3, "O"), "Norman Powell": (2, "O")},
    "LA Lakers": {"LeBron James": (3, "B"), "Anthony Davis": (3, "B"), "Austin Reaves": (2, "O"), "D'Angelo Russell": (2, "O")},
    "Memphis": {"Ja Morant": (3, "O"), "Desmond Bane": (2, "O"), "Jaren Jackson Jr.": (2, "D"), "Marcus Smart": (2, "D")},
    "Miami": {"Jimmy Butler": (3, "B"), "Bam Adebayo": (3, "D"), "Tyler Herro": (2, "O"), "Terry Rozier": (2, "O")},
    "Milwaukee": {"Giannis Antetokounmpo": (3, "B"), "Damian Lillard": (3, "O"), "Khris Middleton": (2, "O"), "Brook Lopez": (2, "D")},
    "Minnesota": {"Anthony Edwards": (3, "O"), "Karl-Anthony Towns": (2, "O"), "Rudy Gobert": (3, "D"), "Jaden McDaniels": (2, "D")},
    "New Orleans": {"Zion Williamson": (3, "O"), "Brandon Ingram": (2, "O"), "CJ McCollum": (2, "O"), "Herb Jones": (2, "D")},
    "New York": {"Jalen Brunson": (3, "O"), "Julius Randle": (2, "B"), "RJ Barrett": (2, "O"), "Mitchell Robinson": (2, "D")},
    "Oklahoma City": {"Shai Gilgeous-Alexander": (3, "O"), "Chet Holmgren": (3, "D"), "Jalen Williams": (2, "B"), "Lu Dort": (2, "D")},
    "Orlando": {"Paolo Banchero": (3, "O"), "Franz Wagner": (2, "B"), "Wendell Carter Jr.": (2, "D"), "Jalen Suggs": (2, "D")},
    "Philadelphia": {"Joel Embiid": (3, "B"), "Tyrese Maxey": (2, "O"), "Tobias Harris": (2, "O")},
    "Phoenix": {"Kevin Durant": (3, "O"), "Devin Booker": (3, "O"), "Bradley Beal": (2, "O"), "Jusuf Nurkic": (2, "D")},
    "Portland": {"Anfernee Simons": (2, "O"), "Scoot Henderson": (2, "O"), "Jerami Grant": (2, "B")},
    "Sacramento": {"De'Aaron Fox": (3, "O"), "Domantas Sabonis": (3, "B"), "Keegan Murray": (2, "O"), "Malik Monk": (2, "O")},
    "San Antonio": {"Victor Wembanyama": (3, "B"), "Devin Vassell": (2, "O"), "Keldon Johnson": (2, "O")},
    "Toronto": {"Scottie Barnes": (2, "B"), "Pascal Siakam": (2, "B"), "RJ Barrett": (2, "O")},
    "Utah": {"Lauri Markkanen": (2, "O"), "Jordan Clarkson": (2, "O"), "Walker Kessler": (2, "D")},
    "Washington": {"Jordan Poole": (2, "O"), "Kyle Kuzma": (2, "O"), "Bilal Coulibaly": (1, "D")}
}

# ========== SIDEBAR LEGEND ==========
with st.sidebar:
    # ========== KALSHI TRADING (AUTO-CONNECT VIA SECRETS) ==========
    st.header("🔗 KALSHI")
    
    # Auto-load API keys from Streamlit Secrets (for future API support)
    try:
        kalshi_api_key = st.secrets.get("KALSHI_API_KEY", "")
        kalshi_private_key = st.secrets.get("KALSHI_PRIVATE_KEY", "")
        if kalshi_api_key and kalshi_private_key:
            st.session_state.trading_enabled = True
            st.session_state.kalshi_api_key = kalshi_api_key
            st.session_state.kalshi_private_key = kalshi_private_key
    except:
        pass
    
    st.caption("⚠️ NBA not on trade API yet")
    st.caption("Track here → Execute on web")
    
    st.divider()
    
    # ========== LEGEND ==========
    st.header("📖 LEGEND")
    st.subheader("🎯 ML Signal Tiers")
    st.markdown("🟢 **STRONG BUY** → 8.0+ score\n\n🔵 **BUY** → 6.5 - 7.9 score\n\n🟡 **LEAN** → 5.5 - 6.4 score\n\n⚪ **TOSS-UP** → 4.5 - 5.4 score\n\n🔴 **SKIP** → Below 4.5")
    st.divider()
    st.subheader("🎯 Totals Signal Tiers")
    st.markdown("🟢 **STRONG NO/YES** → 8.0+ score\n\n🔵 **NO/YES** → 6.5 - 7.9 score\n\n🟡 **LEAN NO/YES** → 5.5 - 6.4\n\n⚪ **TOSS-UP** → 4.5 - 5.4\n\n🔴 **SKIP** → Below 4.5")
    st.divider()
    st.subheader("⭐ Star Injury Weights")
    st.markdown("⭐⭐⭐ **Superstar** → 3x weight\n\n⭐⭐ **All-Star** → 2x weight\n\n⭐ **Rotation** → 1x weight\n\n🔥 Offense | 🛡️ Defense | ⚔️ Both")
    st.divider()
    st.subheader("🔥 Pace Labels")
    st.markdown("🟢 **SLOW** → Under 4.5/min\n\n🟡 **AVG** → 4.5 - 4.8/min\n\n🟠 **FAST** → 4.8 - 5.2/min\n\n🔴 **SHOOTOUT** → Over 5.2/min")
    st.divider()
    st.caption("v15.28")
    st.caption("💾 Positions persist")
    st.caption("🔗 Trade via Kalshi UI")

# ========== TEAM DATA ==========
TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "ft_rate": 0.26, "reb_rate": 49.5, "three_pct": 36.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast"},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "ft_rate": 0.24, "reb_rate": 51.2, "three_pct": 38.5, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic"},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "ft_rate": 0.23, "reb_rate": 48.8, "three_pct": 35.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic"},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "ft_rate": 0.25, "reb_rate": 48.2, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.22, "division": "Southeast"},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "ft_rate": 0.24, "reb_rate": 49.8, "three_pct": 35.2, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Central"},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "ft_rate": 0.27, "reb_rate": 52.5, "three_pct": 36.8, "home_win_pct": 0.75, "away_win_pct": 0.58, "division": "Central"},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "ft_rate": 0.26, "reb_rate": 50.2, "three_pct": 37.5, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southwest"},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "ft_rate": 0.25, "reb_rate": 51.8, "three_pct": 36.5, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest"},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 34.2, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central"},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "ft_rate": 0.23, "reb_rate": 50.5, "three_pct": 38.2, "home_win_pct": 0.65, "away_win_pct": 0.42, "division": "Pacific"},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "ft_rate": 0.28, "reb_rate": 50.8, "three_pct": 35.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "ft_rate": 0.26, "reb_rate": 49.2, "three_pct": 37.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Central"},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "ft_rate": 0.25, "reb_rate": 50.0, "three_pct": 36.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Pacific"},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "ft_rate": 0.27, "reb_rate": 51.0, "three_pct": 35.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific"},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "ft_rate": 0.26, "reb_rate": 52.2, "three_pct": 35.2, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southwest"},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "ft_rate": 0.24, "reb_rate": 50.8, "three_pct": 36.5, "home_win_pct": 0.65, "away_win_pct": 0.45, "division": "Southeast"},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "ft_rate": 0.28, "reb_rate": 51.5, "three_pct": 37.2, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Central"},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "ft_rate": 0.25, "reb_rate": 52.8, "three_pct": 36.2, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Northwest"},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "ft_rate": 0.27, "reb_rate": 50.5, "three_pct": 36.8, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "ft_rate": 0.25, "reb_rate": 51.2, "three_pct": 37.0, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic"},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "ft_rate": 0.26, "reb_rate": 52.0, "three_pct": 37.5, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest"},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "ft_rate": 0.26, "reb_rate": 51.5, "three_pct": 35.5, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast"},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "ft_rate": 0.28, "reb_rate": 50.2, "three_pct": 36.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Atlantic"},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "ft_rate": 0.25, "reb_rate": 49.8, "three_pct": 36.8, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific"},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 35.0, "home_win_pct": 0.40, "away_win_pct": 0.25, "division": "Northwest"},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "ft_rate": 0.25, "reb_rate": 49.5, "three_pct": 36.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific"},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "ft_rate": 0.26, "reb_rate": 49.0, "three_pct": 34.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest"},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "ft_rate": 0.24, "reb_rate": 49.5, "three_pct": 35.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Atlantic"},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "ft_rate": 0.25, "reb_rate": 48.0, "three_pct": 35.2, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Northwest"},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "ft_rate": 0.27, "reb_rate": 48.8, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.25, "division": "Southeast"}
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young"], "Boston": ["Jayson Tatum", "Jaylen Brown"], "Brooklyn": ["Mikal Bridges"],
    "Charlotte": ["LaMelo Ball"], "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Desmond Bane"], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Julius Randle"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"], "Portland": ["Anfernee Simons"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"], "San Antonio": ["Victor Wembanyama"],
    "Toronto": ["Scottie Barnes"], "Utah": ["Lauri Markkanen"], "Washington": ["Jordan Poole"]
}

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_espn_scores(date_key=None):
    """Fetch scores - date_key forces cache invalidation daily"""
    # Force TODAY's date explicitly to avoid ESPN returning yesterday's games
    eastern = pytz.timezone('US/Eastern')
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today_date}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score = team_name, score
                else:
                    away_team, away_score = team_name, score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except:
        return {}

def fetch_yesterday_teams():
    yesterday = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injury_list = data.get("injuries", data.get("teams", []))
        for team_data in injury_list:
            team_name = team_data.get("team", {}).get("displayName", "")
            if not team_name: team_name = team_data.get("team", {}).get("name", "")
            if not team_name: team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key: continue
            injuries[team_key] = []
            player_list = team_data.get("injuries", team_data.get("athletes", []))
            for player in player_list:
                name = player.get("athlete", {}).get("displayName", "")
                if not name: name = player.get("displayName", "")
                if not name: name = player.get("name", "")
                status = player.get("status", "")
                if not status: status = player.get("type", {}).get("description", "")
                if name: injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

def get_star_tier(player_name, team):
    team_stars = STAR_PLAYERS_DB.get(team, {})
    for star_name, (tier, player_type) in team_stars.items():
        if star_name.lower() in player_name.lower() or player_name.lower() in star_name.lower():
            return tier, player_type
    return 0, None

def format_star_rating(tier):
    if tier == 3: return "⭐⭐⭐"
    elif tier == 2: return "⭐⭐"
    elif tier == 1: return "⭐"
    return ""

def format_player_type(player_type):
    if player_type == "O": return "🔥"
    elif player_type == "D": return "🛡️"
    elif player_type == "B": return "⚔️"
    return ""

def get_injury_score(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    score = 0
    out_stars = []
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            score += 4.0 if is_star else 1.0
            if is_star: out_stars.append(name)
        elif "DAY-TO-DAY" in status or "GTD" in status or "QUESTIONABLE" in status:
            score += 2.5 if is_star else 0.5
    return score, out_stars

def get_detailed_injuries(team, injuries):
    team_injuries = injuries.get(team, [])
    detailed = []
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        tier, player_type = get_star_tier(name, team)
        stars = format_star_rating(tier)
        type_emoji = format_player_type(player_type)
        if "OUT" in status: simple_status = "OUT"
        elif "DAY-TO-DAY" in status or "DTD" in status: simple_status = "DTD"
        elif "QUESTIONABLE" in status or "GTD" in status: simple_status = "GTD"
        else: simple_status = status[:10]
        detailed.append({"name": name, "status": simple_status, "tier": tier, "stars": stars, "type_emoji": type_emoji})
    detailed.sort(key=lambda x: x['tier'], reverse=True)
    return detailed

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        clock_str = str(clock)
        if ':' in clock_str:
            parts = clock_str.split(':')
            mins = int(parts[0])
            secs = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins = 0
            secs = float(clock_str) if clock_str else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_ml_score(home_team, away_team, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    home_loc = TEAM_LOCATIONS.get(home_team, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away_team, (0, 0))
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if away_b2b and not home_b2b:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    elif not home_b2b and not away_b2b:
        score_home += 0.5
        score_away += 0.5
    home_net = home.get('net_rating', 0)
    away_net = away.get('net_rating', 0)
    net_diff = home_net - away_net
    if net_diff > 5:
        score_home += 1.0
        reasons_home.append(f"📊 Net +{home_net:.1f}")
    elif net_diff > 2:
        score_home += 0.7
        reasons_home.append(f"📊 Net +{home_net:.1f}")
    elif net_diff > 0: score_home += 0.5
    elif net_diff > -2: score_away += 0.5
    elif net_diff > -5:
        score_away += 0.7
        reasons_away.append(f"📊 Net +{away_net:.1f}")
    else:
        score_away += 1.0
        reasons_away.append(f"📊 Net +{away_net:.1f}")
    home_def = home.get('def_rank', 15)
    away_def = away.get('def_rank', 15)
    if home_def <= 5:
        score_home += 1.0
        reasons_home.append(f"🛡️ #{home_def} DEF")
    elif home_def <= 10:
        score_home += 0.7
        reasons_home.append(f"🛡️ #{home_def} DEF")
    elif home_def <= 15: score_home += 0.4
    if away_def <= 5:
        score_away += 1.0
        reasons_away.append(f"🛡️ #{away_def} DEF")
    elif away_def <= 10:
        score_away += 0.7
        reasons_away.append(f"🛡️ #{away_def} DEF")
    elif away_def <= 15: score_away += 0.4
    score_home += 1.0
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    inj_diff = away_inj - home_inj
    if inj_diff > 3:
        score_home += 1.0
        if away_stars: reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff > 1:
        score_home += 0.6
        if away_stars: reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff < -3:
        score_away += 1.0
        if home_stars: reasons_away.append(f"🏥 {home_stars[0][:10]} OUT")
    elif inj_diff < -1:
        score_away += 0.6
        if home_stars: reasons_away.append(f"🏥 {home_stars[0][:10]} OUT")
    else:
        score_home += 0.3
        score_away += 0.3
    travel_miles = calc_distance(away_loc, home_loc)
    if travel_miles > 2000:
        score_home += 1.0
        reasons_home.append(f"✈️ {int(travel_miles)}mi")
    elif travel_miles > 1500:
        score_home += 0.7
        reasons_home.append(f"✈️ {int(travel_miles)}mi")
    elif travel_miles > 1000: score_home += 0.5
    elif travel_miles > 500: score_home += 0.3
    home_hw = home.get('home_win_pct', 0.5)
    away_aw = away.get('away_win_pct', 0.5)
    reasons_home.append(f"🏠 {int(home_hw*100)}% home")
    if home_hw > 0.65: score_home += 0.8
    elif home_hw > 0.55: score_home += 0.5
    if away_aw < 0.35:
        score_home += 0.5
        reasons_home.append(f"📉 Opp {int(away_aw*100)}% road")
    elif away_aw < 0.45:
        score_home += 0.3
        reasons_home.append(f"📉 Opp {int(away_aw*100)}% road")
    if home.get('division') == away.get('division') and home.get('division'):
        score_home += 0.5
        reasons_home.append("⚔️ Division")
    if home_team == "Denver":
        score_home += 1.0
        reasons_home.append("🏔️ Altitude")
    if home_net > 5:
        score_home += 0.5
        if f"📊 Net +{home_net:.1f}" not in reasons_home: reasons_home.append("⭐ Elite")
    if away_net > 5:
        score_away += 0.5
        if f"📊 Net +{away_net:.1f}" not in reasons_away: reasons_away.append("⭐ Elite")
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    if home_final >= away_final:
        return home_team, home_final, round((home_final - 5) * 4, 0), reasons_home[:4], home_stars, away_stars
    else:
        return away_team, away_final, round((away_final - 5) * 4, 0), reasons_away[:4], home_stars, away_stars

def get_signal_tier(score):
    if score >= 8.0: return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5: return "🔵 BUY", "#00aaff"
    elif score >= 5.5: return "🟡 LEAN", "#ffff00"
    elif score >= 4.5: return "⚪ TOSS-UP", "#888888"
    else: return "🔴 SKIP", "#ff0000"

def calc_totals_score(home_team, away_team, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    score_under, score_over = 0, 0
    reasons_under, reasons_over = [], []
    home_pace = home.get('pace', 100)
    away_pace = away.get('pace', 100)
    avg_pace = (home_pace + away_pace) / 2
    if avg_pace < 98.5:
        score_under += 1.5
        reasons_under.append(f"🐢 Slow {avg_pace:.1f}")
    elif avg_pace < 99.5:
        score_under += 1.0
        reasons_under.append(f"🐢 Pace {avg_pace:.1f}")
    elif avg_pace > 101:
        score_over += 1.5
        reasons_over.append(f"🔥 Fast {avg_pace:.1f}")
    elif avg_pace > 100:
        score_over += 1.0
        reasons_over.append(f"🔥 Pace {avg_pace:.1f}")
    home_def = home.get('def_rank', 15)
    away_def = away.get('def_rank', 15)
    avg_def = (home_def + away_def) / 2
    if avg_def <= 8:
        score_under += 1.5
        reasons_under.append(f"🛡️ DEF #{int(avg_def)}")
    elif avg_def <= 12:
        score_under += 1.0
        reasons_under.append(f"🛡️ DEF #{int(avg_def)}")
    elif avg_def >= 22:
        score_over += 1.5
        reasons_over.append(f"💥 DEF #{int(avg_def)}")
    elif avg_def >= 18:
        score_over += 1.0
        reasons_over.append(f"💥 DEF #{int(avg_def)}")
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if home_b2b and away_b2b:
        score_under += 1.5
        reasons_under.append("🛏️ Both B2B")
    elif home_b2b or away_b2b:
        score_under += 0.75
        tired_team = home_team if home_b2b else away_team
        reasons_under.append(f"🛏️ {tired_team[:3]} B2B")
    home_3pt = home.get('three_pct', 36)
    away_3pt = away.get('three_pct', 36)
    avg_3pt = (home_3pt + away_3pt) / 2
    if avg_3pt < 35.5:
        score_under += 1.0
        reasons_under.append(f"🎯 Low 3PT {avg_3pt:.1f}%")
    elif avg_3pt > 37.5:
        score_over += 1.0
        reasons_over.append(f"🎯 High 3PT {avg_3pt:.1f}%")
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    if home_stars or away_stars:
        score_under += 1.0
        out_names = (home_stars + away_stars)[:2]
        reasons_under.append(f"🏥 {', '.join([n[:8] for n in out_names])} OUT")
    home_net = home.get('net_rating', 0)
    away_net = away.get('net_rating', 0)
    net_diff = abs(home_net - away_net)
    if net_diff > 10:
        score_over += 0.75
        reasons_over.append("💥 Blowout risk")
    elif net_diff < 3:
        score_under += 0.5
        reasons_under.append("⚔️ Close game")
    if home_team == "Denver":
        score_under += 0.75
        reasons_under.append("🏔️ Denver altitude")
    home_ft = home.get('ft_rate', 0.25)
    away_ft = away.get('ft_rate', 0.25)
    avg_ft = (home_ft + away_ft) / 2
    if avg_ft > 0.27:
        score_under += 0.5
        reasons_under.append("🎁 High FT rate")
    elif avg_ft < 0.23:
        score_over += 0.5
        reasons_over.append("🏃 Low FT rate")
    home_reb = home.get('reb_rate', 50)
    away_reb = away.get('reb_rate', 50)
    avg_reb = (home_reb + away_reb) / 2
    if avg_reb > 51.5:
        score_under += 0.5
        reasons_under.append("🏀 Control boards")
    if home.get('home_win_pct', 0.5) > 0.65 and home_net > 5:
        score_over += 0.5
        reasons_over.append("🏠 Home scoring")
    total = score_under + score_over
    if total > 0:
        under_final = round((score_under / total) * 10, 1)
        over_final = round((score_over / total) * 10, 1)
    else:
        under_final, over_final = 5.0, 5.0
    if under_final >= over_final:
        return "NO", under_final, reasons_under[:4]
    else:
        return "YES", over_final, reasons_over[:4]

def get_totals_signal_tier(score, pick):
    if score >= 8.0: return f"🟢 STRONG {pick}", "#00ff00"
    elif score >= 6.5: return f"🔵 {pick}", "#00aaff"
    elif score >= 5.5: return f"🟡 LEAN {pick}", "#ffff00"
    elif score >= 4.5: return "⚪ TOSS-UP", "#888888"
    else: return "🔴 SKIP", "#ff0000"

# ========== FETCH DATA (with date_key for cache invalidation) ==========
games = fetch_espn_scores(date_key=today_str)
game_list = sorted(list(games.keys()))
yesterday_teams_raw = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

today_teams = set()
for game_key in games.keys():
    parts = game_key.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams_raw.intersection(today_teams)

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
hdr1.caption(f"{auto_status} | Last update: {now.strftime('%I:%M:%S %p ET')} | v15.28")

if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True):
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.rerun()

if hdr3.button("🔄 Refresh", use_container_width=True):
    st.rerun()

# ========== API STATUS BANNER ==========
if st.session_state.trading_enabled and st.session_state.kalshi_api_key:
    st.markdown(f"<div style='background:linear-gradient(135deg,#1a2a0a,#2a3a1a);padding:10px 15px;border-radius:8px;border:2px solid #aaaa00;margin-bottom:15px'><span style='color:#aaaa00;font-weight:bold'>🔗 NBA API NOT SUPPORTED</span> — Track positions here, execute on Kalshi web</div>", unsafe_allow_html=True)

# ========== INJURY REPORT ==========
st.subheader("🏥 INJURY REPORT - TODAY'S GAMES")

if game_list:
    teams_playing = set()
    for game_key in game_list:
        parts = game_key.split("@")
        teams_playing.add(parts[0])
        teams_playing.add(parts[1])
    
    star_injuries = []
    for team in sorted(teams_playing):
        team_injuries = get_detailed_injuries(team, injuries)
        for inj in team_injuries:
            if inj['tier'] >= 2:
                star_injuries.append((team, inj))
    
    if star_injuries:
        st.markdown("### ⭐ KEY PLAYER INJURIES")
        cols = st.columns(3)
        for idx, (team, inj) in enumerate(star_injuries):
            with cols[idx % 3]:
                status_color = "#ff0000" if inj['status'] == "OUT" else "#ffaa00"
                st.markdown(f"<div style='background:linear-gradient(135deg,#2a1a1a,#1a1a2e);padding:10px;border-radius:8px;border-left:4px solid {status_color};margin-bottom:8px'><span style='color:#fff;font-weight:bold'>{inj['stars']} {inj['name']}</span> {inj['type_emoji']}<br><span style='color:{status_color};font-size:0.9em'>{inj['status']}</span><span style='color:#888;font-size:0.85em'> • {team}</span></div>", unsafe_allow_html=True)
    else:
        st.info("✅ No key player injuries reported for today's games")
else:
    st.info("No games scheduled today")

st.divider()

if yesterday_teams:
    st.info(f"📅 **Back-to-Back Teams Today**: {', '.join(sorted(yesterday_teams))}")
else:
    st.info("📅 **No B2B teams today** — all teams are rested")

st.divider()

# ========== BIG SNAPSHOT – TODAY'S ML PICKS ==========
st.subheader("🎯 BIG SNAPSHOT – TODAY'S ML PICKS")
st.caption(f"📅 Snapshot date: {st.session_state.get('snapshot_date', 'N/A')}")

# Compute ML results fresh (no caching across days)
ml_results = []

for game_key, g in games.items():
    away = g["away_team"]
    home = g["home_team"]

    try:
        pick, score, edge, reasons, home_stars, away_stars = calc_ml_score(
            home, away, yesterday_teams, injuries
        )

        tier, color = get_signal_tier(score)
        
        # Check if blowout risk (tired away @ fresh home)
        away_b2b = away in yesterday_teams
        home_b2b = home in yesterday_teams
        is_blowout_risk = away_b2b and not home_b2b and pick == home

        ml_results.append({
            "game": f"{away} vs {home}",
            "pick": pick,
            "score": score,
            "edge": edge,
            "tier": tier,
            "color": color,
            "reasons": reasons,
            "away": away,
            "home": home,
            "blowout": is_blowout_risk
        })
    except:
        continue

# Store in session state for this date
st.session_state["big_snapshot"] = ml_results

# Sort by score descending
ml_results.sort(key=lambda x: x["score"], reverse=True)

# Bucket by tier
tiers = {
    "🟢 STRONG BUY": [],
    "🔵 BUY": [],
    "🟡 LEAN": [],
    "⚪ TOSS-UP": []
}

for r in ml_results:
    if r["score"] >= 8.0:
        tiers["🟢 STRONG BUY"].append(r)
    elif r["score"] >= 6.5:
        tiers["🔵 BUY"].append(r)
    elif r["score"] >= 5.5:
        tiers["🟡 LEAN"].append(r)
    else:
        tiers["⚪ TOSS-UP"].append(r)

for label, rows in tiers.items():
    if not rows:
        continue

    st.markdown(f"<div style='font-size:1.1em;font-weight:700;margin:8px 0 4px 0'>{label}</div>", unsafe_allow_html=True)

    for r in rows:
        kalshi_url = build_kalshi_ml_url(r["away"], r["home"])
        reasons = " • ".join(r["reasons"])
        edge_txt = f"+{int(r['edge'])}%"
        blowout_badge = "🔥 " if r.get("blowout") else ""

        st.markdown(
            f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        background:linear-gradient(135deg,#0f172a,#020617);
                        padding:6px 12px;margin-bottom:4px;border-radius:6px;
                        border-left:3px solid {r['color']}">
                <div style="flex:1;min-width:0">
                    <span style="color:#fff;font-size:0.9em;font-weight:600">{blowout_badge}{r['pick']}</span>
                    <span style="color:#666;font-size:0.85em"> vs {r['away'] if r['pick']==r['home'] else r['home']}</span>
                    <span style="color:#38bdf8;font-weight:600;font-size:0.85em;margin-left:8px">{r['score']}/10 | {edge_txt}</span>
                    <span style="color:#777;font-size:0.75em;margin-left:8px">{reasons}</span>
                </div>
                <a href="{kalshi_url}" target="_blank"
                   style="background:#16a34a;color:#fff;
                          padding:4px 10px;border-radius:5px;font-size:0.8em;
                          text-decoration:none;font-weight:600;white-space:nowrap">
                   BUY {r['pick'][:3].upper()}
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

st.divider()

# ========== BLOWOUT RISK - TIRED AWAY @ FRESH HOME ==========
st.subheader("🔥 BLOWOUT RISK — Tired Away @ Fresh Home")

blowout_games = []
for game_key, g in games.items():
    away = g["away_team"]
    home = g["home_team"]
    away_b2b = away in yesterday_teams
    home_b2b = home in yesterday_teams
    
    if away_b2b and not home_b2b:
        home_stats = TEAM_STATS.get(home, {})
        away_stats = TEAM_STATS.get(away, {})
        home_net = home_stats.get('net_rating', 0)
        away_net = away_stats.get('net_rating', 0)
        net_edge = home_net - away_net
        
        blowout_games.append({
            "game": game_key,
            "home": home,
            "away": away,
            "net_edge": net_edge,
            "home_net": home_net,
            "away_net": away_net
        })

blowout_games.sort(key=lambda x: x['net_edge'], reverse=True)

if blowout_games:
    for bg in blowout_games:
        kalshi_url = build_kalshi_ml_url(bg["away"], bg["home"])
        edge_color = "#00ff00" if bg['net_edge'] > 5 else "#ffff00" if bg['net_edge'] > 0 else "#ff8800"
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        background:linear-gradient(135deg,#2a1a0a,#1a0a0a);
                        padding:8px 12px;margin-bottom:4px;border-radius:6px;
                        border-left:3px solid #ff6600">
                <div style="flex:1">
                    <span style="color:#ff6600;font-weight:700">🔥 {bg['home']}</span>
                    <span style="color:#888"> vs tired {bg['away']}</span>
                    <span style="color:{edge_color};font-size:0.85em;margin-left:10px">Net: {bg['net_edge']:+.1f}</span>
                </div>
                <a href="{kalshi_url}" target="_blank"
                   style="background:#ff6600;color:#fff;
                          padding:4px 10px;border-radius:5px;font-size:0.8em;
                          text-decoration:none;font-weight:600">
                   ML {bg['home'][:3].upper()}
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("No blowout setups today — no tired away teams @ fresh home teams")

st.divider()

# ========== ADD NEW POSITION ==========
st.subheader("➕ ADD NEW POSITION")

game_options = ["Select a game..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("🏀 Game", game_options, key="game_select")

if selected_game != "Select a game...":
    parts = selected_game.replace(" @ ", "@").split("@")
    away_t, home_t = parts[0], parts[1]
    col_ml, col_tot = st.columns(2)
    col_ml.link_button(f"🔗 ML on Kalshi", build_kalshi_ml_url(away_t, home_t), use_container_width=True)
    col_tot.link_button(f"🔗 Totals on Kalshi", build_kalshi_totals_url(away_t, home_t), use_container_width=True)

market_type = st.radio("📈 Market Type", ["Moneyline (Winner)", "Totals (Over/Under)"], horizontal=True, key="mkt_type")

game_started = False
if selected_game != "Select a game...":
    gkey = selected_game.replace(" @ ", "@")
    g = games.get(gkey)
    if g and g["period"] > 0:
        game_started = True

p1, p2, p3 = st.columns(3)

if market_type == "Totals (Over/Under)":
    with p1:
        st.caption("📊 Side")
        yes_no = st.radio("", ["NO (Under)", "YES (Over)"], horizontal=True, key="totals_side_radio")
        st.session_state.selected_side = "NO" if yes_no.startswith("NO") else "YES"
    
    st.session_state.selected_threshold = st.number_input("🎯 Threshold", min_value=180.0, max_value=280.0, value=st.session_state.selected_threshold, step=0.5)
else:
    with p1:
        if selected_game != "Select a game...":
            parts = selected_game.replace(" @ ", "@").split("@")
            st.caption("📊 Pick Winner")
            st.session_state.selected_ml_pick = st.radio("", [parts[1], parts[0]], horizontal=True, key="ml_pick_radio")
        else:
            st.session_state.selected_ml_pick = None
            st.warning("⚠️ Select a game first")

price_paid = p2.number_input("💵 Price (¢)", min_value=1, max_value=99, value=50, step=1)
contracts = p3.number_input("📄 Contracts", min_value=1, value=st.session_state.default_contracts, step=1)

# Trading mode toggle - NBA not supported via API
if st.session_state.trading_enabled and st.session_state.kalshi_api_key:
    st.info("⚠️ **NBA markets require Kalshi web UI** — API trading not yet supported. Use Paper Track + link out.")
    trade_mode = "📝 Paper Track"
    is_live_trade = False
else:
    is_live_trade = False

btn_label = "✅ ADD POSITION"
btn_type = "primary"

if st.button(btn_label, use_container_width=True, type=btn_type):
    if selected_game == "Select a game...":
        st.error("Select a game first!")
    else:
        game_key = selected_game.replace(" @ ", "@")
        parts = game_key.split("@")
        away_t, home_t = parts[0], parts[1]
        
        if market_type == "Moneyline (Winner)":
            if st.session_state.selected_ml_pick is None:
                st.error("Pick a team first!")
            else:
                st.session_state.positions.append({"game": game_key, "type": "ml", "pick": st.session_state.selected_ml_pick, "price": price_paid, "contracts": contracts, "cost": round(price_paid * contracts / 100, 2)})
                save_positions(st.session_state.positions)
                st.success(f"✅ Position added: {st.session_state.selected_ml_pick} ML @ {price_paid}¢")
                st.rerun()
        else:
            st.session_state.positions.append({"game": game_key, "type": "totals", "side": st.session_state.selected_side, "threshold": st.session_state.selected_threshold, "price": price_paid, "contracts": contracts, "cost": round(price_paid * contracts / 100, 2)})
            save_positions(st.session_state.positions)
            st.success(f"✅ Position added: {st.session_state.selected_side} {st.session_state.selected_threshold} @ {price_paid}¢")
            st.rerun()

st.divider()

# ========== ACTIVE POSITIONS ==========
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        g = games.get(game_key)
        price = pos.get('price', 50)
        contracts = pos.get('contracts', 1)
        cost = pos.get('cost', round(price * contracts / 100, 2))
        pos_type = pos.get('type', 'totals')
        is_live = pos.get('live', False)
        potential_win = round((100 - price) * contracts / 100, 2)
        potential_loss = cost
        live_badge = "💰 LIVE" if is_live else "📝 Paper"
        
        if g:
            total = g['total']
            mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            
            if pos_type == 'ml':
                pick = pos.get('pick', '')
                parts = game_key.split("@")
                away_team, home_team = parts[0], parts[1]
                home_score, away_score = g['home_score'], g['away_score']
                pick_score = home_score if pick == home_team else away_score
                opp_score = away_score if pick == home_team else home_score
                lead = pick_score - opp_score
                
                if is_final:
                    won = pick_score > opp_score
                    if won:
                        status_label, status_color = "✅ WON!", "#00ff00"
                        pnl_display, pnl_color = f"+${potential_win:.2f}", "#00ff00"
                    else:
                        status_label, status_color = "❌ LOST", "#ff0000"
                        pnl_display, pnl_color = f"-${potential_loss:.2f}", "#ff0000"
                elif mins > 0:
                    if lead >= 15: status_label, status_color = "🟢 CRUISING", "#00ff00"
                    elif lead >= 8: status_label, status_color = "🟢 LEADING", "#00ff00"
                    elif lead >= 1: status_label, status_color = "🟡 AHEAD", "#ffff00"
                    elif lead >= -5: status_label, status_color = "🟠 CLOSE", "#ff8800"
                    else: status_label, status_color = "🔴 BEHIND", "#ff0000"
                    pnl_display, pnl_color = f"Win: +${potential_win:.2f}", "#888888"
                else:
                    status_label, status_color = "⏳ WAITING", "#888888"
                    lead = 0
                    pnl_display, pnl_color = f"Win: +${potential_win:.2f}", "#888888"
                
                st.markdown(f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'><div style='display:flex;justify-content:space-between;align-items:center'><div><span style='color:#fff;font-size:1.2em;font-weight:bold'>{game_key.replace('@', ' @ ')}</span><span style='color:#888;margin-left:10px'>{game_status}</span><span style='color:#00aaff;margin-left:10px;font-size:0.85em'>{live_badge}</span></div><span style='color:{status_color};font-size:1.3em;font-weight:bold'>{status_label}</span></div><div style='margin-top:10px;display:flex;gap:30px;flex-wrap:wrap'><span style='color:#aaa'>🎯 <b style=\"color:#fff\">ML: {pick}</b></span><span style='color:#aaa'>💵 <b style=\"color:#fff\">{contracts}x @ {price}¢</b> (${cost:.2f})</span><span style='color:#aaa'>📊 Score: <b style=\"color:#fff\">{pick_score}-{opp_score}</b></span><span style='color:#aaa'>📈 Lead: <b style=\"color:{status_color}\">{lead:+d}</b></span><span style='color:{pnl_color}'>{pnl_display}</span></div></div>", unsafe_allow_html=True)
            else:
                projected = round((total / mins) * 48) if mins > 0 else None
                cushion = (pos['threshold'] - projected) if pos.get('side') == "NO" and projected else ((projected - pos['threshold']) if projected else 0)
                
                if is_final:
                    won = (total < pos['threshold']) if pos.get('side') == "NO" else (total > pos['threshold'])
                    if won:
                        status_label, status_color = "✅ WON!", "#00ff00"
                        pnl_display, pnl_color = f"+${potential_win:.2f}", "#00ff00"
                    else:
                        status_label, status_color = "❌ LOST", "#ff0000"
                        pnl_display, pnl_color = f"-${potential_loss:.2f}", "#ff0000"
                elif projected:
                    if cushion >= 15: status_label, status_color = "🟢 VERY SAFE", "#00ff00"
                    elif cushion >= 8: status_label, status_color = "🟢 LOOKING GOOD", "#00ff00"
                    elif cushion >= 3: status_label, status_color = "🟡 ON TRACK", "#ffff00"
                    elif cushion >= -3: status_label, status_color = "🟠 WARNING", "#ff8800"
                    else: status_label, status_color = "🔴 AT RISK", "#ff0000"
                    pnl_display, pnl_color = f"Win: +${potential_win:.2f}", "#888888"
                else:
                    status_label, status_color = "⏳ WAITING", "#888888"
                    pnl_display, pnl_color = f"Win: +${potential_win:.2f}", "#888888"
                
                st.markdown(f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'><div style='display:flex;justify-content:space-between;align-items:center'><div><span style='color:#fff;font-size:1.2em;font-weight:bold'>{game_key.replace('@', ' @ ')}</span><span style='color:#888;margin-left:10px'>{game_status}</span><span style='color:#00aaff;margin-left:10px;font-size:0.85em'>{live_badge}</span></div><span style='color:{status_color};font-size:1.3em;font-weight:bold'>{status_label}</span></div><div style='margin-top:10px;display:flex;gap:30px;flex-wrap:wrap'><span style='color:#aaa'>📊 <b style=\"color:#fff\">{pos.get('side', 'NO')} {pos.get('threshold', 0)}</b></span><span style='color:#aaa'>💵 <b style=\"color:#fff\">{contracts}x @ {price}¢</b> (${cost:.2f})</span><span style='color:#aaa'>📈 Proj: <b style=\"color:#fff\">{projected if projected else '—'}</b></span><span style='color:#aaa'>🎯 Cushion: <b style=\"color:{status_color}\">{cushion:+.0f}</b></span><span style='color:{pnl_color}'>{pnl_display}</span></div></div>", unsafe_allow_html=True)
            
            btn1, btn2 = st.columns([3, 1])
            parts = game_key.split("@")
            if pos_type == 'ml': kalshi_url = build_kalshi_ml_url(parts[0], parts[1])
            else: kalshi_url = build_kalshi_totals_url(parts[0], parts[1])
            btn1.link_button(f"🔗 Trade on Kalshi", kalshi_url, use_container_width=True)
            if btn2.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
        else:
            if pos_type == 'ml': display_text = f"ML: {pos.get('pick', '?')}"
            else: display_text = f"{pos.get('side', 'NO')} {pos.get('threshold', 0)}"
            st.markdown(f"<div style='background:#1a1a2e;padding:15px;border-radius:10px;border:1px solid #444;margin-bottom:10px'><span style='color:#888'>{game_key.replace('@', ' @ ')} — {display_text} — {contracts}x @ {price}¢</span><span style='color:#666;margin-left:15px'>⏳ Game not started</span></div>", unsafe_allow_html=True)
            if st.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No positions tracked — use the form above to add your first position")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({"game": gk, "pace": pace, "proj": proj, "total": g['total'], "mins": mins, "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"})

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5: lbl, clr = "🟢 SLOW", "#00ff00"
        elif p['pace'] < 4.8: lbl, clr = "🟡 AVG", "#ffff00"
        elif p['pace'] < 5.2: lbl, clr = "🟠 FAST", "#ff8800"
        else: lbl, clr = "🔴 SHOOTOUT", "#ff0000"
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']} pts in {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

cush_col1, cush_col2 = st.columns(2)
min_minutes = cush_col1.selectbox("Min Minutes", [6, 9, 12, 15, 18], index=0, key="cush_min_select")
cush_side = cush_col2.selectbox("Side", ["NO (Under)", "YES (Over)"], key="cush_side_select")
is_no_side = "NO" in cush_side

cushion_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins < min_minutes:
        continue
    if g['status_type'] == "STATUS_FINAL":
        continue
    
    total = g['total']
    pace = total / mins if mins > 0 else 0
    proj = round(pace * 48)
    
    # Find recommended bet line
    if is_no_side:
        # NO: find first threshold ABOVE projection, then go one higher
        candidates = [t for t in THRESHOLDS if t > proj]
        if len(candidates) >= 2:
            bet_line = candidates[1]  # One level higher (safer)
        elif len(candidates) == 1:
            bet_line = candidates[0]
        else:
            continue
        cushion = bet_line - proj
    else:
        # YES: find first threshold BELOW projection, then go one lower
        candidates = [t for t in THRESHOLDS if t < proj]
        if len(candidates) >= 2:
            bet_line = candidates[-2]  # One level lower (safer)
        elif len(candidates) == 1:
            bet_line = candidates[-1]
        else:
            continue
        cushion = proj - bet_line
    
    if cushion < 6:
        continue
    
    # Pace alignment check
    if is_no_side:
        if pace < 4.5: pace_status = "✅ SLOW"
        elif pace < 4.8: pace_status = "⚠️ AVG"
        else: pace_status = "❌ FAST"
    else:
        if pace > 5.0: pace_status = "✅ FAST"
        elif pace > 4.7: pace_status = "⚠️ AVG"
        else: pace_status = "❌ SLOW"
    
    cushion_data.append({
        "game": gk,
        "status": f"Q{g['period']} {g['clock']}",
        "total": total,
        "proj": proj,
        "bet_line": bet_line,
        "cushion": cushion,
        "pace": pace,
        "pace_status": pace_status,
        "mins": mins
    })

cushion_data.sort(key=lambda x: x['cushion'], reverse=True)

if cushion_data:
    for c in cushion_data:
        side_label = "NO" if is_no_side else "YES"
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px 16px;margin-bottom:8px;border-radius:10px;border-left:4px solid #00ff00">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="color:#fff;font-weight:bold;font-size:1.1em">{c['game'].replace('@', ' @ ')}</span>
                        <span style="color:#888;margin-left:10px">{c['status']}</span>
                    </div>
                    <span style="color:#00ff00;font-weight:bold;font-size:1.2em">+{c['cushion']:.0f} cushion</span>
                </div>
                <div style="margin-top:8px;display:flex;gap:25px;flex-wrap:wrap">
                    <span style="color:#aaa">📊 Total: <b style="color:#fff">{c['total']}</b></span>
                    <span style="color:#aaa">📈 Proj: <b style="color:#fff">{c['proj']}</b></span>
                    <span style="color:#ff8800;font-weight:bold">🎯 {side_label} {c['bet_line']}</span>
                    <span style="color:#aaa">🔥 {c['pace']:.2f}/min {c['pace_status']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info(f"No games with {min_minutes}+ minutes and 6+ cushion found")

st.divider()

# ========== ALL GAMES ==========
st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()
st.caption("⚠️ For entertainment only. Not financial advice.")
st.caption("v15.28 - Paper track + link out (NBA API not supported)")
