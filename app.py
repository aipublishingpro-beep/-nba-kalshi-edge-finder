import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import uuid
import base64

# Try to import cryptography for trading (optional)
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== STYLING (NO AUTO-REFRESH) ==========
st.markdown("""
<style>
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

# ============================================================
# KALSHI TRADING API
# ============================================================
def init_trading():
    if 'kalshi_api_key' not in st.session_state:
        try:
            st.session_state.kalshi_api_key = st.secrets.get("KALSHI_API_KEY", "")
        except:
            st.session_state.kalshi_api_key = ""
    if 'kalshi_private_key' not in st.session_state:
        try:
            st.session_state.kalshi_private_key = st.secrets.get("KALSHI_PRIVATE_KEY", "")
        except:
            st.session_state.kalshi_private_key = ""
    if 'trading_enabled' not in st.session_state:
        st.session_state.trading_enabled = bool(st.session_state.kalshi_api_key and st.session_state.kalshi_private_key)
    if 'default_contracts' not in st.session_state:
        st.session_state.default_contracts = 10

def create_kalshi_signature(private_key_pem, timestamp, method, path):
    if not CRYPTO_AVAILABLE:
        return None
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )
        path_without_query = path.split('?')[0]
        message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
        signature = private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    except:
        return None

def place_kalshi_order(ticker, side, price_cents, count, api_key, private_key_pem):
    if not CRYPTO_AVAILABLE:
        return False, "cryptography library not installed"
    try:
        path = '/trade-api/v2/portfolio/orders'
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = create_kalshi_signature(private_key_pem, timestamp, "POST", path)
        if not signature:
            return False, "Failed to create signature"
        headers = {
            'KALSHI-ACCESS-KEY': api_key,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        order_data = {
            "ticker": ticker, "action": "buy", "side": side.lower(),
            "count": count, "type": "limit", "client_order_id": str(uuid.uuid4())
        }
        if side.lower() == "no":
            order_data["no_price"] = price_cents
        else:
            order_data["yes_price"] = price_cents
        response = requests.post(f"https://api.elections.kalshi.com{path}", headers=headers, json=order_data, timeout=10)
        if response.status_code == 201:
            return True, f"✅ Order placed! {count}x {side} @ {price_cents}¢"
        else:
            error_msg = response.json().get('error', {}).get('message', response.text)
            return False, f"❌ Error: {error_msg}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

init_trading()

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
    away_code = KALSHI_CODES.get(away_team, "xxx")
    home_code = KALSHI_CODES.get(home_team, "xxx")
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").lower()
    ticker = f"kxnbatotal-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/kxnbatotal/pro-basketball-total-points/{ticker}"

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx")
    home_code = KALSHI_CODES.get(home_team, "xxx")
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").lower()
    ticker = f"kxnbagame-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/kxnbagame/pro-basketball-moneyline/{ticker}"

def build_kalshi_ticker(away_team, home_team, threshold):
    away_code = KALSHI_CODES.get(away_team, "xxx")
    home_code = KALSHI_CODES.get(home_team, "xxx")
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    thresh_str = f"{float(threshold):.1f}".rstrip('0').rstrip('.')
    if '.' not in thresh_str:
        thresh_str += ".5"
    return f"KXNBATOTAL-{date_str}{away_code.upper()}{home_code.upper()}-T{thresh_str}"

def fetch_kalshi_market_line(away_team, home_team):
    try:
        away_code = KALSHI_CODES.get(away_team, "xxx")
        home_code = KALSHI_CODES.get(home_team, "xxx")
        today = datetime.now(pytz.timezone('US/Eastern'))
        date_str = today.strftime("%y%b%d").upper()
        event_ticker = f"KXNBATOTAL-{date_str}{away_code.upper()}{home_code.upper()}"
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker={event_ticker}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None, None, {}
        data = resp.json()
        markets = data.get("markets", [])
        if not markets:
            return None, None, {}
        best_threshold = None
        best_diff = 100
        all_thresholds = []
        for market in markets:
            thresh = market.get("floor_strike")
            yes_price = market.get("yes_ask") or market.get("last_price") or 50
            if thresh:
                all_thresholds.append({"threshold": thresh, "yes_price": yes_price})
                diff = abs(yes_price - 50)
                if diff < best_diff:
                    best_diff = diff
                    best_threshold = thresh
        return best_threshold, all_thresholds, {}
    except:
        return None, None, {}

if "positions" not in st.session_state:
    st.session_state.positions = []

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("📖 LEGEND")
    st.subheader("🎯 ML Signal Tiers")
    st.markdown("🟢 **STRONG BUY** → 8.0+\n🔵 **BUY** → 6.5 - 7.9\n⚪ Below 6.5 → Skip")
    st.divider()
    st.subheader("📊 10-Factor ML System")
    st.markdown("1. Rest Advantage\n2. Net Rating Edge\n3. Defense Ranking\n4. Home Court\n5. Injury Impact\n6. Travel Fatigue\n7. Home/Away Splits\n8. Division Rivalry\n9. Altitude (Denver)\n10. Team Quality")
    st.divider()
    st.subheader("🎯 Totals Signal Tiers")
    st.markdown("🟢 **STRONG** → 8.0+\n🔵 **Regular** → 6.5 - 7.9\n⚪ Below 6.5 → Skip")
    st.divider()
    st.subheader("Cushion Scanner")
    st.markdown("🟢 **+20** → 2x size\n🔵 **+12-19** → 1x size\n🟡 **+6-11** → 0.5x size\n❌ Under +6 → Skip")
    st.divider()
    st.subheader("Pace Benchmarks")
    st.markdown("🟢 SLOW → Under 4.5/min\n🟡 AVG → 4.5-4.8/min\n🟠 FAST → 4.8-5.2/min\n🔴 SHOOTOUT → 5.2+/min")
    st.divider()
    st.subheader("🚀 ONE-CLICK TRADING")
    if not CRYPTO_AVAILABLE:
        st.warning("Add `cryptography` to requirements.txt")
    else:
        st.session_state.trading_enabled = st.toggle("Enable Trading", value=st.session_state.trading_enabled)
        if st.session_state.trading_enabled:
            if st.session_state.kalshi_api_key:
                st.success("✅ API Key loaded")
            else:
                st.session_state.kalshi_api_key = st.text_input("API Key", type="password")
            if st.session_state.kalshi_private_key:
                st.success("✅ Private Key loaded")
            else:
                st.session_state.kalshi_private_key = st.text_area("Private Key (PEM)", height=100)
            st.session_state.default_contracts = st.number_input("Default Contracts", min_value=1, max_value=500, value=st.session_state.default_contracts)
            if st.session_state.kalshi_api_key and st.session_state.kalshi_private_key:
                st.success("✅ Ready to trade!")
    st.divider()
    st.caption("v15.0")

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

def fetch_espn_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
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
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "")
                injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

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
            if is_star:
                out_stars.append(name)
        elif "DAY-TO-DAY" in status or "GTD" in status or "QUESTIONABLE" in status:
            score += 2.5 if is_star else 0.5
    return score, out_stars

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 0
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
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_12_factor_edge(home_team, away_team, home_rest, away_rest, home_inj, away_inj, kalshi_price):
    home = TEAM_STATS.get(home_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    away = TEAM_STATS.get(away_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    home_loc = TEAM_LOCATIONS.get(home_team, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away_team, (0, 0))
    travel_miles = calc_distance(away_loc, home_loc)
    rest_diff = home_rest - away_rest
    rest_score = max(-6, min(6, rest_diff * 2))
    def_score = (away['def_rank'] - home['def_rank']) * 0.15
    injury_score = (away_inj - home_inj) * 1.5
    pace_diff = home['pace'] - away['pace']
    pace_score = pace_diff * 0.1 if home['net_rating'] > away['net_rating'] else -pace_diff * 0.1
    net_score = (home['net_rating'] - away['net_rating']) * 0.8
    travel_score = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_score = (home.get('home_win_pct', 0.5) - 0.5) * 10 + (0.5 - away.get('away_win_pct', 0.5)) * 10
    h2h_score = 1.5 if home.get('division') == away.get('division') and home.get('division') else 0
    altitude_score = 2.0 if home_team == "Denver" else 0
    ft_score = (home.get('ft_rate', 0.25) - away.get('ft_rate', 0.25)) * 20
    reb_score = (home.get('reb_rate', 50) - away.get('reb_rate', 50)) * 0.3
    three_score = (home.get('three_pct', 36) - away.get('three_pct', 36)) * 0.5
    home_court = 3.0
    weighted_spread = home_court + rest_score + def_score + injury_score + pace_score + net_score + travel_score + split_score + h2h_score + altitude_score + ft_score + reb_score + three_score
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    edge = home_win_prob - kalshi_price
    return {'home_win_prob': round(home_win_prob, 1), 'kalshi_price': kalshi_price, 'edge': round(edge, 1), 'expected_spread': round(weighted_spread, 1)}

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
    elif net_diff > 0:
        score_home += 0.5
    elif net_diff > -2:
        score_away += 0.5
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
    elif home_def <= 15:
        score_home += 0.4
    if away_def <= 5:
        score_away += 1.0
        reasons_away.append(f"🛡️ #{away_def} DEF")
    elif away_def <= 10:
        score_away += 0.7
        reasons_away.append(f"🛡️ #{away_def} DEF")
    elif away_def <= 15:
        score_away += 0.4
    score_home += 1.0
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    inj_diff = away_inj - home_inj
    if inj_diff > 3:
        score_home += 1.0
        if away_stars:
            reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff > 1:
        score_home += 0.6
        if away_stars:
            reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff < -3:
        score_away += 1.0
        if home_stars:
            reasons_away.append(f"🏥 {home_stars[0][:10]} OUT")
    elif inj_diff < -1:
        score_away += 0.6
        if home_stars:
            reasons_away.append(f"🏥 {home_stars[0][:10]} OUT")
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
    elif travel_miles > 1000:
        score_home += 0.5
    elif travel_miles > 500:
        score_home += 0.3
    home_hw = home.get('home_win_pct', 0.5)
    away_aw = away.get('away_win_pct', 0.5)
    reasons_home.append(f"🏠 {int(home_hw*100)}% home")
    if home_hw > 0.65:
        score_home += 0.8
    elif home_hw > 0.55:
        score_home += 0.5
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
        if f"📊 Net +{home_net:.1f}" not in reasons_home:
            reasons_home.append("⭐ Elite")
    if away_net > 5:
        score_away += 0.5
        if f"📊 Net +{away_net:.1f}" not in reasons_away:
            reasons_away.append("⭐ Elite")
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
    if score >= 8.0:
        return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5:
        return "🔵 BUY", "#00aaff"
    return None, None

def calc_projected_total(home_team, away_team, yesterday_teams):
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    base_total = 225
    home_pace = home.get('pace', 100)
    away_pace = away.get('pace', 100)
    avg_pace = (home_pace + away_pace) / 2
    pace_adj = (avg_pace - 100) * 2
    home_def = home.get('def_rank', 15)
    away_def = away.get('def_rank', 15)
    avg_def = (home_def + away_def) / 2
    def_adj = (avg_def - 15) * 0.8
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if home_b2b and away_b2b:
        fatigue_adj = -6
    elif home_b2b or away_b2b:
        fatigue_adj = -3
    else:
        fatigue_adj = 0
    altitude_adj = -4 if home_team == "Denver" else 0
    return round(base_total + pace_adj + def_adj + fatigue_adj + altitude_adj)

def calc_recommended_threshold(kalshi_line, pick, score):
    if score >= 10:
        cushion = 6
    elif score >= 9:
        cushion = 8
    elif score >= 8:
        cushion = 10
    elif score >= 7:
        cushion = 12
    else:
        cushion = 14
    if pick == "NO":
        threshold = kalshi_line + cushion
    else:
        threshold = kalshi_line - cushion
    threshold = round(threshold * 2) / 2
    if threshold == int(threshold):
        threshold += 0.5
    return threshold

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
    if score >= 8.0:
        return f"🟢 STRONG {pick}", "#00ff00"
    elif score >= 6.5:
        return f"🔵 {pick}", "#00aaff"
    return None, None

# ========== FETCH DATA ==========
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')} | v15.0 | 🔄 Press R to refresh")

# ========== ML BIG SNAPSHOT ==========
st.subheader("🎯 BIG SNAPSHOT - TODAY'S ML PICKS")
if game_list:
    all_picks = []
    for game_key in game_list:
        parts = game_key.split("@")
        away_team, home_team = parts[0], parts[1]
        pick, score, edge, reasons, home_out, away_out = calc_ml_score(home_team, away_team, yesterday_teams, injuries)
        signal, color = get_signal_tier(score)
        if signal:
            all_picks.append({'game': game_key, 'home': home_team, 'away': away_team, 'pick': pick, 'score': score, 'edge': edge, 'signal': signal, 'color': color, 'reasons': reasons})
    all_picks.sort(key=lambda x: x['score'], reverse=True)
    strong_buys = [p for p in all_picks if p['score'] >= 8.0]
    buys = [p for p in all_picks if 6.5 <= p['score'] < 8.0]
    if strong_buys:
        st.markdown("### 🟢 STRONG BUY")
        for p in strong_buys:
            reasons_str = " • ".join(p['reasons']) if p['reasons'] else "Multiple factors"
            is_home = p['pick'] == p['home']
            opp = p['away'] if is_home else p['home']
            tag = "🏠" if is_home else "✈️"
            col1, col2, col3, col4 = st.columns([3, 2, 4, 2])
            col1.markdown(f"**<span style='color:#00ff00'>{p['pick']}</span>** {tag} vs {opp}", unsafe_allow_html=True)
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10 | +{p['edge']:.0f}%</span>", unsafe_allow_html=True)
            col3.markdown(f"<span style='color:#aaa;font-size:0.9em'>{reasons_str}</span>", unsafe_allow_html=True)
            col4.link_button(f"🚀 BUY", build_kalshi_ml_url(p['away'], p['home']))
    if buys:
        st.markdown("### 🔵 BUY")
        for p in buys:
            reasons_str = " • ".join(p['reasons']) if p['reasons'] else "Multiple factors"
            is_home = p['pick'] == p['home']
            opp = p['away'] if is_home else p['home']
            tag = "🏠" if is_home else "✈️"
            col1, col2, col3, col4 = st.columns([3, 2, 4, 2])
            col1.markdown(f"**<span style='color:#00aaff'>{p['pick']}</span>** {tag} vs {opp}", unsafe_allow_html=True)
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10 | +{p['edge']:.0f}%</span>", unsafe_allow_html=True)
            col3.markdown(f"<span style='color:#aaa;font-size:0.9em'>{reasons_str}</span>", unsafe_allow_html=True)
            col4.link_button(f"🔗 BUY", build_kalshi_ml_url(p['away'], p['home']))
    if not strong_buys and not buys:
        st.info("⚪ No actionable ML plays today")
else:
    st.info("No games scheduled today")

st.divider()

# ========== TOTALS BIG SNAPSHOT ==========
st.subheader("🎯 TOTALS BIG SNAPSHOT - TODAY'S OVER/UNDER PICKS")
if game_list:
    all_totals = []
    for game_key in game_list:
        parts = game_key.split("@")
        away_team, home_team = parts[0], parts[1]
        pick, score, reasons = calc_totals_score(home_team, away_team, yesterday_teams, injuries)
        signal, color = get_totals_signal_tier(score, pick)
        projected = calc_projected_total(home_team, away_team, yesterday_teams)
        kalshi_line, _, _ = fetch_kalshi_market_line(away_team, home_team)
        if not kalshi_line:
            kalshi_line = 232
        rec_threshold = calc_recommended_threshold(kalshi_line, pick, score)
        if signal:
            all_totals.append({'game': game_key, 'home': home_team, 'away': away_team, 'pick': pick, 'score': score, 'signal': signal, 'color': color, 'reasons': reasons, 'projected': projected, 'kalshi_line': kalshi_line, 'rec_threshold': rec_threshold})
    all_totals.sort(key=lambda x: x['score'], reverse=True)
    strong_no = [p for p in all_totals if p['score'] >= 8.0 and p['pick'] == "NO"]
    strong_yes = [p for p in all_totals if p['score'] >= 8.0 and p['pick'] == "YES"]
    reg_no = [p for p in all_totals if 6.5 <= p['score'] < 8.0 and p['pick'] == "NO"]
    reg_yes = [p for p in all_totals if 6.5 <= p['score'] < 8.0 and p['pick'] == "YES"]
    if strong_no:
        st.markdown("### 🟢 STRONG NO (Under)")
        for p in strong_no:
            col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
            col1.markdown(f"**{p['away']}** @ **{p['home']}**")
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10</span>", unsafe_allow_html=True)
            col3.markdown(f"Model: <b>{p['projected']}</b> | Kalshi: <b>{p['kalshi_line']}</b> → <span style='color:#00ff00;font-weight:bold'>SAFE: NO @ {p['rec_threshold']}+</span>", unsafe_allow_html=True)
            col4.link_button(f"🚀 BUY NO", build_kalshi_totals_url(p['away'], p['home']))
    if strong_yes:
        st.markdown("### 🟢 STRONG YES (Over)")
        for p in strong_yes:
            col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
            col1.markdown(f"**{p['away']}** @ **{p['home']}**")
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10</span>", unsafe_allow_html=True)
            col3.markdown(f"Model: <b>{p['projected']}</b> | Kalshi: <b>{p['kalshi_line']}</b> → <span style='color:#00ff00;font-weight:bold'>SAFE: YES @ {p['rec_threshold']}-</span>", unsafe_allow_html=True)
            col4.link_button(f"🚀 BUY YES", build_kalshi_totals_url(p['away'], p['home']))
    if reg_no:
        st.markdown("### 🔵 NO (Under)")
        for p in reg_no:
            col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
            col1.markdown(f"**{p['away']}** @ **{p['home']}**")
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10</span>", unsafe_allow_html=True)
            col3.markdown(f"Model: <b>{p['projected']}</b> | Kalshi: <b>{p['kalshi_line']}</b> → <span style='color:#00aaff;font-weight:bold'>SAFE: NO @ {p['rec_threshold']}+</span>", unsafe_allow_html=True)
            col4.link_button(f"🔗 BUY NO", build_kalshi_totals_url(p['away'], p['home']))
    if reg_yes:
        st.markdown("### 🔵 YES (Over)")
        for p in reg_yes:
            col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
            col1.markdown(f"**{p['away']}** @ **{p['home']}**")
            col2.markdown(f"<span style='color:{p['color']};font-weight:bold'>{p['score']}/10</span>", unsafe_allow_html=True)
            col3.markdown(f"Model: <b>{p['projected']}</b> | Kalshi: <b>{p['kalshi_line']}</b> → <span style='color:#00aaff;font-weight:bold'>SAFE: YES @ {p['rec_threshold']}-</span>", unsafe_allow_html=True)
            col4.link_button(f"🔗 BUY YES", build_kalshi_totals_url(p['away'], p['home']))
    if not strong_no and not strong_yes and not reg_no and not reg_yes:
        st.info("⚪ No actionable totals plays today")
else:
    st.info("No games scheduled today")

st.divider()

if yesterday_teams:
    st.info(f"📅 **B2B Teams Today:** {', '.join(sorted(yesterday_teams))}")

# ========== BLOWOUT RISK ==========
st.subheader("🔥 TOP PICKS - BLOWOUT RISK (Tired Away @ Fresh Home)")
if game_list:
    top_picks = []
    for game_key in game_list:
        parts = game_key.split("@")
        away_t, home_t = parts[0], parts[1]
        if away_t in yesterday_teams and home_t not in yesterday_teams:
            home_i, _ = get_injury_score(home_t, injuries)
            away_i, _ = get_injury_score(away_t, injuries)
            res = calc_12_factor_edge(home_t, away_t, 1, 0, home_i, away_i, 50)
            top_picks.append({'game': game_key, 'home_team': home_t, 'away_team': away_t, 'home_win_prob': res['home_win_prob'], 'spread': res['expected_spread']})
    top_picks.sort(key=lambda x: x['home_win_prob'], reverse=True)
    if top_picks:
        for pick in top_picks:
            st.markdown(f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid #00ff00;margin-bottom:10px'>
                <span style='color:#00ff00;font-size:1.8em;font-weight:bold'>🎯 BUY {pick['home_team']} ML</span>
                <span style='color:#00ff00;font-size:1.1em;margin-left:15px'>HIGH CONFIDENCE</span>
                <br><span style='color:#aaa;font-size:0.9em'>{pick['game'].replace('@', ' @ ')} | {pick['home_team']} {pick['home_win_prob']:.0f}% to win | 🔴 {pick['away_team']} B2B</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("⚪ No BLOWOUT RISK games today")
else:
    st.info("No games today")

st.divider()

# ========== ADD POSITION ==========
st.subheader("➕ ADD NEW POSITION")
game_options = ["Select a game..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("🏀 Game", game_options, key="game_select")
threshold_select = st.number_input("🎯 Threshold", min_value=180.0, max_value=280.0, value=225.5, step=3.0, key="threshold_select")
if selected_game != "Select a game...":
    parts = selected_game.replace(" @ ", "@").split("@")
    st.link_button(f"🔗 View {selected_game} on Kalshi", build_kalshi_totals_url(parts[0], parts[1]), use_container_width=True)

with st.form("add_position_form"):
    p1, p2, p3 = st.columns(3)
    side = p1.selectbox("📊 Side", ["NO (Under)", "YES (Over)"], key="side_form")
    price_paid = p2.number_input("💵 Price (¢)", min_value=1, max_value=99, value=50, step=1, key="price_form")
    contracts = p3.number_input("📄 Contracts", min_value=1, max_value=1000, value=st.session_state.default_contracts, step=1)
    if st.session_state.trading_enabled and st.session_state.kalshi_api_key and st.session_state.kalshi_private_key:
        buy_col, add_col = st.columns(2)
        buy_now = buy_col.form_submit_button("🚀 BUY ON KALSHI NOW", use_container_width=True, type="primary")
        add_manual = add_col.form_submit_button("✅ ADD POSITION (manual)", use_container_width=True)
    else:
        buy_now = False
        add_manual = st.form_submit_button("✅ ADD POSITION", use_container_width=True)
    if selected_game != "Select a game...":
        game_key = selected_game.replace(" @ ", "@")
        side_clean = "NO" if "NO" in side else "YES"
        parts = game_key.split("@")
        if buy_now:
            ticker = build_kalshi_ticker(parts[0], parts[1], threshold_select)
            success, msg = place_kalshi_order(ticker, side_clean, price_paid, contracts, st.session_state.kalshi_api_key, st.session_state.kalshi_private_key)
            if success:
                st.success(msg)
                st.session_state.positions.append({'game': game_key, 'side': side_clean, 'threshold': threshold_select, 'price': price_paid, 'contracts': contracts, 'cost': round(price_paid * contracts / 100, 2)})
                st.rerun()
            else:
                st.error(msg)
        if add_manual:
            st.session_state.positions.append({'game': game_key, 'side': side_clean, 'threshold': threshold_select, 'price': price_paid, 'contracts': contracts, 'cost': round(price_paid * contracts / 100, 2)})
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
        if g:
            total = g['total']
            mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            projected = round((total / mins) * 48) if mins > 0 else None
            cushion = (pos['threshold'] - projected) if pos['side'] == "NO" and projected else ((projected - pos['threshold']) if projected else 0)
            potential_win = round((100 - price) * contracts / 100, 2)
            potential_loss = cost
            if is_final:
                won = (total < pos['threshold']) if pos['side'] == "NO" else (total > pos['threshold'])
                status_label = "✅ WON!" if won else "❌ LOST"
                status_color = "#00ff00" if won else "#ff0000"
                pnl_display = f"+${potential_win:.2f}" if won else f"-${potential_loss:.2f}"
                pnl_color = "#00ff00" if won else "#ff0000"
            elif projected:
                if cushion >= 15:
                    status_label, status_color = "🟢 VERY SAFE", "#00ff00"
                elif cushion >= 8:
                    status_label, status_color = "🟢 LOOKING GOOD", "#00ff00"
                elif cushion >= 3:
                    status_label, status_color = "🟡 ON TRACK", "#ffff00"
                elif cushion >= -3:
                    status_label, status_color = "🟠 WARNING", "#ff8800"
                else:
                    status_label, status_color = "🔴 AT RISK", "#ff0000"
                pnl_display = f"Win: +${potential_win:.2f}"
                pnl_color = "#888888"
            else:
                status_label, status_color = "⏳ WAITING", "#888888"
                pnl_display = f"Win: +${potential_win:.2f}"
                pnl_color = "#888888"
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            st.markdown(f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div><span style='color:#fff;font-size:1.2em;font-weight:bold'>{game_key.replace('@', ' @ ')}</span><span style='color:#888;margin-left:10px'>{game_status}</span></div>
                    <span style='color:{status_color};font-size:1.3em;font-weight:bold'>{status_label}</span>
                </div>
                <div style='margin-top:10px;display:flex;gap:30px'>
                    <span style='color:#aaa'>📊 <b style="color:#fff">{pos['side']} {pos['threshold']}</b></span>
                    <span style='color:#aaa'>💵 <b style="color:#fff">{contracts}x @ {price}¢</b> (${cost:.2f})</span>
                    <span style='color:#aaa'>📈 Proj: <b style="color:#fff">{projected if projected else '—'}</b></span>
                    <span style='color:#aaa'>🎯 Cushion: <b style="color:{status_color}">{cushion:+.0f}</b></span>
                    <span style='color:{pnl_color}'>{pnl_display}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            btn1, btn2 = st.columns([3, 1])
            parts = game_key.split("@")
            btn1.link_button(f"🔗 Trade on Kalshi", build_kalshi_totals_url(parts[0], parts[1]), use_container_width=True)
            if btn2.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
        else:
            st.markdown(f"""<div style='background:#1a1a2e;padding:15px;border-radius:10px;border:1px solid #444;margin-bottom:10px'>
                <span style='color:#888'>{game_key.replace('@', ' @ ')} — {pos['side']} {pos['threshold']} — {contracts}x @ {price}¢</span>
                <span style='color:#666;margin-left:15px'>⏳ Game not started</span>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked — add your first position above")

st.divider()

# ========== CUSHION SCANNER (FIXED v15.0) ==========
st.subheader("🎯 CUSHION SCANNER - ALL THRESHOLDS")

MIN_CUSHION = 6
ALL_THRESHOLDS = [215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

cs1, cs2 = st.columns([1, 1])
cush_window = cs1.selectbox("Stability Window", [6, 9, 12, 18, 24], index=1, key="cush_window")

for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins < cush_window:
        continue
    if g['status_type'] == "STATUS_FINAL":
        continue
    
    proj = round((g['total'] / mins) * 48) if mins > 0 else 0
    pace_val = g['total'] / mins if mins > 0 else 0
    away_team = g.get('away_team', '')
    home_team = g.get('home_team', '')
    
    # Pace label
    if pace_val < 4.5:
        pace_label, pace_color = "🟢 SLOW", "#00ff00"
    elif pace_val < 4.8:
        pace_label, pace_color = "🟡 AVG", "#ffff00"
    elif pace_val < 5.2:
        pace_label, pace_color = "🟠 FAST", "#ff8800"
    else:
        pace_label, pace_color = "🔴 SHOOTOUT", "#ff0000"
    
    # Game header
    st.markdown(f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;margin-bottom:5px;margin-top:15px'>
        <span style='color:#fff;font-size:1.3em;font-weight:bold'>{away_team} @ {home_team}</span>
        <span style='color:#888;margin-left:15px'>{mins:.0f} min played</span>
        <span style='color:{pace_color};margin-left:15px;font-weight:bold'>{pace_label} {pace_val:.2f}/min</span>
        <span style='color:#fff;margin-left:15px'>📈 Proj: <b>{proj}</b></span>
    </div>""", unsafe_allow_html=True)
    
    # Build threshold rows - NO ONLY for shootouts
    threshold_rows = []
    for thresh in ALL_THRESHOLDS:
        no_cushion = thresh - proj
        yes_cushion = proj - thresh
        
        # For shootouts (pace >= 5.0), only show NO options
        if pace_val >= 5.0:
            if no_cushion >= MIN_CUSHION:
                if no_cushion >= 20:
                    size_label, size_color = "2x", "#00ff00"
                elif no_cushion >= 12:
                    size_label, size_color = "1x", "#00aaff"
                else:
                    size_label, size_color = "0.5x", "#ffff00"
                threshold_rows.append({
                    'thresh': thresh, 'side': 'NO', 'cushion': no_cushion,
                    'size_label': size_label, 'size_color': size_color
                })
        else:
            # Normal pace - show both sides
            if no_cushion >= MIN_CUSHION:
                if no_cushion >= 20:
                    size_label, size_color = "2x", "#00ff00"
                elif no_cushion >= 12:
                    size_label, size_color = "1x", "#00aaff"
                else:
                    size_label, size_color = "0.5x", "#ffff00"
                threshold_rows.append({
                    'thresh': thresh, 'side': 'NO', 'cushion': no_cushion,
                    'size_label': size_label, 'size_color': size_color
                })
            if yes_cushion >= MIN_CUSHION:
                if yes_cushion >= 20:
                    size_label, size_color = "2x", "#00ff00"
                elif yes_cushion >= 12:
                    size_label, size_color = "1x", "#00aaff"
                else:
                    size_label, size_color = "0.5x", "#ffff00"
                threshold_rows.append({
                    'thresh': thresh, 'side': 'YES', 'cushion': yes_cushion,
                    'size_label': size_label, 'size_color': size_color
                })
    
    # Sort by cushion descending
    threshold_rows.sort(key=lambda x: x['cushion'], reverse=True)
    
    if threshold_rows:
        for tr in threshold_rows:
            cush_color = "#00ff00" if tr['cushion'] >= 20 else ("#00aaff" if tr['cushion'] >= 12 else "#ffff00")
            st.markdown(f"""<div style='background:#0d1117;padding:10px 15px;border-left:4px solid {cush_color};margin-bottom:3px;display:flex;justify-content:space-between;align-items:center'>
                <span style='color:#fff;font-weight:bold'>BUY {tr['side']} @ {tr['thresh']}</span>
                <span style='color:{cush_color};font-weight:bold'>+{tr['cushion']:.0f} cushion</span>
                <span style='color:{tr['size_color']}'>Size: {tr['size_label']}</span>
            </div>""", unsafe_allow_html=True)
        
        kalshi_url = build_kalshi_totals_url(away_team, home_team)
        st.link_button(f"🚀 Trade {away_team} @ {home_team} on Kalshi", kalshi_url, use_container_width=True)
    else:
        st.markdown(f"<div style='color:#666;padding:10px'>⚪ No thresholds with +{MIN_CUSHION} cushion</div>", unsafe_allow_html=True)

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
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']} pts in {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

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
