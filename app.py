import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import uuid
import base64

try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

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
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None, backend=default_backend())
        message = f"{timestamp}{method}{path.split('?')[0]}".encode('utf-8')
        signature = private_key.sign(message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
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
        headers = {'KALSHI-ACCESS-KEY': api_key, 'KALSHI-ACCESS-SIGNATURE': signature, 'KALSHI-ACCESS-TIMESTAMP': timestamp, 'Content-Type': 'application/json'}
        order_data = {"ticker": ticker, "action": "buy", "side": side.lower(), "count": count, "type": "limit", "client_order_id": str(uuid.uuid4())}
        if side.lower() == "no":
            order_data["no_price"] = price_cents
        else:
            order_data["yes_price"] = price_cents
        response = requests.post(f"https://api.elections.kalshi.com{path}", headers=headers, json=order_data, timeout=10)
        if response.status_code == 201:
            return True, f"✅ Order placed! {count}x {side} @ {price_cents}¢"
        else:
            return False, f"❌ Error: {response.json().get('error', {}).get('message', response.text)}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

init_trading()

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
    return f"https://kalshi.com/markets/kxnbatotal/pro-basketball-total-points/kxnbatotal-{date_str}{away_code}{home_code}"

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx")
    home_code = KALSHI_CODES.get(home_team, "xxx")
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").lower()
    return f"https://kalshi.com/markets/kxnbagame/pro-basketball-moneyline/kxnbagame-{date_str}{away_code}{home_code}"

def build_kalshi_ticker(away_team, home_team, threshold):
    away_code = KALSHI_CODES.get(away_team, "xxx")
    home_code = KALSHI_CODES.get(home_team, "xxx")
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    thresh_str = f"{float(threshold):.1f}".rstrip('0').rstrip('.')
    if '.' not in thresh_str:
        thresh_str += ".5"
    return f"KXNBATOTAL-{date_str}{away_code.upper()}{home_code.upper()}-T{thresh_str}"

def fetch_kalshi_markets(away_team, home_team):
    try:
        away_code = KALSHI_CODES.get(away_team, "xxx")
        home_code = KALSHI_CODES.get(home_team, "xxx")
        today = datetime.now(pytz.timezone('US/Eastern'))
        date_str = today.strftime("%y%b%d").upper()
        event_ticker = f"KXNBATOTAL-{date_str}{away_code.upper()}{home_code.upper()}"
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker={event_ticker}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None, []
        data = resp.json()
        markets = data.get("markets", [])
        if not markets:
            return None, []
        all_thresholds = []
        best_threshold = None
        best_diff = 100
        for market in markets:
            thresh = market.get("floor_strike")
            yes_bid = market.get("yes_bid") or 0
            yes_ask = market.get("yes_ask") or 0
            no_bid = market.get("no_bid") or 0
            no_ask = market.get("no_ask") or 0
            last_price = market.get("last_price") or 50
            if thresh:
                all_thresholds.append({"threshold": thresh, "yes_bid": yes_bid, "yes_ask": yes_ask, "no_bid": no_bid, "no_ask": no_ask, "last_price": last_price})
                mid_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else last_price
                diff = abs(mid_price - 50)
                if diff < best_diff:
                    best_diff = diff
                    best_threshold = thresh
        all_thresholds.sort(key=lambda x: x['threshold'])
        return best_threshold, all_thresholds
    except:
        return None, []

def get_best_threshold(away_team, home_team, projected, pick_side):
    """Find best threshold from actual Kalshi brackets with safety buffer"""
    _, all_thresholds = fetch_kalshi_markets(away_team, home_team)
    if not all_thresholds:
        return None, None, None
    
    # Sort thresholds by value
    sorted_thresh = sorted(all_thresholds, key=lambda x: x['threshold'])
    
    if pick_side == "NO":
        # For NO: find brackets ABOVE projected, pick one with good cushion, then go one level HIGHER for safety
        candidates = []
        for idx, t in enumerate(sorted_thresh):
            thresh = t['threshold']
            cushion = thresh - projected
            if cushion >= 6:  # Minimum cushion
                no_price = t.get('no_bid') or (100 - (t.get('yes_ask') or 50))
                candidates.append({'idx': idx, 'threshold': thresh, 'cushion': cushion, 'price': no_price})
        
        if candidates:
            # Pick the one with best value (cushion vs price balance)
            best = max(candidates, key=lambda x: x['cushion'] * 0.5 + (70 - abs(x['price'] - 55)) * 0.3)
            # Safety buffer: go one level HIGHER
            safer_idx = best['idx'] + 1
            if safer_idx < len(sorted_thresh):
                safer = sorted_thresh[safer_idx]
                safer_cushion = safer['threshold'] - projected
                safer_price = safer.get('no_bid') or (100 - (safer.get('yes_ask') or 50))
                return safer['threshold'], safer_cushion, safer_price if safer_price > 0 else 50
            else:
                return best['threshold'], best['cushion'], best['price'] if best['price'] > 0 else 50
    else:
        # For YES: find brackets BELOW projected, pick one with good cushion, then go one level LOWER for safety
        candidates = []
        for idx, t in enumerate(sorted_thresh):
            thresh = t['threshold']
            cushion = projected - thresh
            if cushion >= 6:  # Minimum cushion
                yes_price = t.get('yes_bid') or (100 - (t.get('no_ask') or 50))
                candidates.append({'idx': idx, 'threshold': thresh, 'cushion': cushion, 'price': yes_price})
        
        if candidates:
            # Pick the one with best value
            best = max(candidates, key=lambda x: x['cushion'] * 0.5 + (70 - abs(x['price'] - 55)) * 0.3)
            # Safety buffer: go one level LOWER
            safer_idx = best['idx'] - 1
            if safer_idx >= 0:
                safer = sorted_thresh[safer_idx]
                safer_cushion = projected - safer['threshold']
                safer_price = safer.get('yes_bid') or (100 - (safer.get('no_ask') or 50))
                return safer['threshold'], safer_cushion, safer_price if safer_price > 0 else 50
            else:
                return best['threshold'], best['cushion'], best['price'] if best['price'] > 0 else 50
    
    return None, None, None

if "positions" not in st.session_state:
    st.session_state.positions = []

with st.sidebar:
    st.header("📖 LEGEND")
    st.subheader("🎯 ML Signal Tiers")
    st.markdown("🟢 **STRONG BUY** → 8.0+\n🔵 **BUY** → 6.5-7.9\n⚪ Below 6.5 → Skip")
    st.divider()
    st.subheader("📊 Totals Signal Tiers")
    st.markdown("🟢 **STRONG** → 7.0+\n🔵 **BUY** → 6.0-6.9\n⚪ Below 6.0 → No Trade")
    st.divider()
    st.subheader("⭐ Star Injury Impact")
    st.markdown("🏥 **Star OUT** → +1.0 to opponent\n🏥 **Star GTD** → +0.6 to opponent")
    st.divider()
    st.subheader("Cushion Scanner")
    st.markdown("🟢 **+20** → 2x size\n🔵 **+12-19** → 1x size\n🟡 **+6-11** → 0.5x\n❌ Under +6 → Skip")
    st.divider()
    st.subheader("Pace Benchmarks")
    st.markdown("🟢 SLOW → <4.5/min\n🟡 AVG → 4.5-4.8\n🟠 FAST → 4.8-5.2\n🔴 SHOOTOUT → 5.2+")
    st.divider()
    st.subheader("📊 Live Score Trend")
    st.markdown("🔥 **HOT** → +8 vs expected\n🟢 **WARM** → +4 to +8\n⚪ **NORMAL** → -4 to +4\n❄️ **COLD** → -4 to -8\n🧊 **ICE** → -8 vs expected")
    st.divider()
    st.subheader("🚀 TRADING")
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
    st.divider()
    st.caption("v16.2")

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
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "ft_rate": 0.26, "reb_rate": 49.5, "three_pct": 36.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "ppg": 117.5},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "ft_rate": 0.24, "reb_rate": 51.2, "three_pct": 38.5, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "ppg": 120.8},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "ft_rate": 0.23, "reb_rate": 48.8, "three_pct": 35.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic", "ppg": 108.2},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "ft_rate": 0.25, "reb_rate": 48.2, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.22, "division": "Southeast", "ppg": 106.5},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "ft_rate": 0.24, "reb_rate": 49.8, "three_pct": 35.2, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Central", "ppg": 111.2},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "ft_rate": 0.27, "reb_rate": 52.5, "three_pct": 36.8, "home_win_pct": 0.75, "away_win_pct": 0.58, "division": "Central", "ppg": 114.8},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "ft_rate": 0.26, "reb_rate": 50.2, "three_pct": 37.5, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southwest", "ppg": 117.2},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "ft_rate": 0.25, "reb_rate": 51.8, "three_pct": 36.5, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "ppg": 115.5},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 34.2, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central", "ppg": 104.8},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "ft_rate": 0.23, "reb_rate": 50.5, "three_pct": 38.2, "home_win_pct": 0.65, "away_win_pct": 0.42, "division": "Pacific", "ppg": 118.2},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "ft_rate": 0.28, "reb_rate": 50.8, "three_pct": 35.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest", "ppg": 114.5},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "ft_rate": 0.26, "reb_rate": 49.2, "three_pct": 37.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Central", "ppg": 123.2},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "ft_rate": 0.25, "reb_rate": 50.0, "three_pct": 36.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Pacific", "ppg": 110.8},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "ft_rate": 0.27, "reb_rate": 51.0, "three_pct": 35.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "ppg": 115.2},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "ft_rate": 0.26, "reb_rate": 52.2, "three_pct": 35.2, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southwest", "ppg": 116.8},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "ft_rate": 0.24, "reb_rate": 50.8, "three_pct": 36.5, "home_win_pct": 0.65, "away_win_pct": 0.45, "division": "Southeast", "ppg": 110.5},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "ft_rate": 0.28, "reb_rate": 51.5, "three_pct": 37.2, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Central", "ppg": 118.5},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "ft_rate": 0.25, "reb_rate": 52.8, "three_pct": 36.2, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Northwest", "ppg": 112.8},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "ft_rate": 0.27, "reb_rate": 50.5, "three_pct": 36.8, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest", "ppg": 115.2},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "ft_rate": 0.25, "reb_rate": 51.2, "three_pct": 37.0, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic", "ppg": 116.5},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "ft_rate": 0.26, "reb_rate": 52.0, "three_pct": 37.5, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "ppg": 119.8},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "ft_rate": 0.26, "reb_rate": 51.5, "three_pct": 35.5, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast", "ppg": 108.5},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "ft_rate": 0.28, "reb_rate": 50.2, "three_pct": 36.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Atlantic", "ppg": 113.2},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "ft_rate": 0.25, "reb_rate": 49.8, "three_pct": 36.8, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific", "ppg": 114.8},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 35.0, "home_win_pct": 0.40, "away_win_pct": 0.25, "division": "Northwest", "ppg": 107.5},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "ft_rate": 0.25, "reb_rate": 49.5, "three_pct": 36.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific", "ppg": 117.8},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "ft_rate": 0.26, "reb_rate": 49.0, "three_pct": 34.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "ppg": 110.2},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "ft_rate": 0.24, "reb_rate": 49.5, "three_pct": 35.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Atlantic", "ppg": 111.8},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "ft_rate": 0.25, "reb_rate": 48.0, "three_pct": 35.2, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Northwest", "ppg": 108.5},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "ft_rate": 0.27, "reb_rate": 48.8, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.25, "division": "Southeast", "ppg": 109.8}
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
            games[game_key] = {"away_team": away_team, "home_team": home_team, "away_score": away_score, "home_score": home_score, "total": away_score + home_score, "period": period, "clock": clock, "status_type": status_type}
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
                teams_played.add(TEAM_ABBREVS.get(full_name, full_name))
        return teams_played
    except:
        return set()

def fetch_espn_injuries():
    injuries = {}
    timestamp = None
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        timestamp = datetime.now(pytz.timezone('US/Eastern'))
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                injuries[team_key].append({"name": player.get("athlete", {}).get("displayName", ""), "status": player.get("status", "")})
    except:
        pass
    return injuries, timestamp

def fetch_rotowire_injuries():
    injuries = {}
    try:
        url = "https://www.rotowire.com/basketball/tables/injury-report.php?team=ALL&pos=ALL"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for player in data:
                team = player.get('team', '')
                team_map = {
                    'ATL': 'Atlanta', 'BOS': 'Boston', 'BKN': 'Brooklyn', 'CHA': 'Charlotte',
                    'CHI': 'Chicago', 'CLE': 'Cleveland', 'DAL': 'Dallas', 'DEN': 'Denver',
                    'DET': 'Detroit', 'GSW': 'Golden State', 'HOU': 'Houston', 'IND': 'Indiana',
                    'LAC': 'LA Clippers', 'LAL': 'LA Lakers', 'MEM': 'Memphis', 'MIA': 'Miami',
                    'MIL': 'Milwaukee', 'MIN': 'Minnesota', 'NOP': 'New Orleans', 'NYK': 'New York',
                    'OKC': 'Oklahoma City', 'ORL': 'Orlando', 'PHI': 'Philadelphia', 'PHX': 'Phoenix',
                    'POR': 'Portland', 'SAC': 'Sacramento', 'SAS': 'San Antonio', 'TOR': 'Toronto',
                    'UTA': 'Utah', 'WAS': 'Washington'
                }
                team_key = team_map.get(team, team)
                if team_key not in injuries:
                    injuries[team_key] = []
                status = player.get('status', '').upper()
                injuries[team_key].append({"name": player.get('player', ''), "status": status})
    except:
        pass
    return injuries

def merge_injuries(espn_injuries, rotowire_injuries):
    merged = {}
    all_teams = set(list(espn_injuries.keys()) + list(rotowire_injuries.keys()))
    for team in all_teams:
        merged[team] = []
        espn_players = {p['name'].lower(): p for p in espn_injuries.get(team, [])}
        roto_players = {p['name'].lower(): p for p in rotowire_injuries.get(team, [])}
        all_players = set(list(espn_players.keys()) + list(roto_players.keys()))
        for player_key in all_players:
            espn_p = espn_players.get(player_key)
            roto_p = roto_players.get(player_key)
            if espn_p and roto_p:
                espn_status = espn_p['status'].upper()
                roto_status = roto_p['status'].upper()
                if 'OUT' in roto_status or 'OUT' in espn_status:
                    final_status = 'OUT'
                elif 'GTD' in roto_status or 'GTD' in espn_status or 'QUESTIONABLE' in roto_status or 'QUESTIONABLE' in espn_status or 'DAY-TO-DAY' in espn_status:
                    final_status = 'GTD'
                else:
                    final_status = espn_p['status']
                merged[team].append({"name": espn_p['name'], "status": final_status})
            elif espn_p:
                merged[team].append(espn_p)
            elif roto_p:
                merged[team].append(roto_p)
    return merged

def get_injury_score(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    score, out_stars, gtd_stars = 0, [], []
    for inj in team_injuries:
        name, status = inj.get("name", ""), inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            score += 4.0 if is_star else 1.0
            if is_star:
                out_stars.append(name)
        elif "DAY-TO-DAY" in status or "GTD" in status or "QUESTIONABLE" in status:
            score += 2.5 if is_star else 0.5
            if is_star:
                gtd_stars.append(name)
    return score, out_stars, gtd_stars

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
            mins, secs = int(parts[0]), int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins, secs = 0, float(clock_str) if clock_str else 0
        time_left = mins + secs/60
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def get_expected_total(home_team, away_team):
    home_ppg = TEAM_STATS.get(home_team, {}).get('ppg', 112)
    away_ppg = TEAM_STATS.get(away_team, {}).get('ppg', 112)
    return (home_ppg + away_ppg) / 2

def get_score_trend(game_data, home_team, away_team):
    mins = get_minutes_played(game_data['period'], game_data['clock'], game_data['status_type'])
    if mins < 6:
        return None, None, None
    actual_total = game_data['total']
    expected_total = get_expected_total(home_team, away_team)
    expected_at_time = (expected_total / 48) * mins
    diff = actual_total - expected_at_time
    if diff >= 8:
        return "🔥 HOT", "#ff4400", diff
    elif diff >= 4:
        return "🟢 WARM", "#00ff00", diff
    elif diff <= -8:
        return "🧊 ICE", "#00ccff", diff
    elif diff <= -4:
        return "❄️ COLD", "#88ccff", diff
    return "⚪ NORMAL", "#888888", diff

def calc_12_factor_edge(home_team, away_team, home_rest, away_rest, home_inj, away_inj, kalshi_price):
    home = TEAM_STATS.get(home_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    away = TEAM_STATS.get(away_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    travel_miles = calc_distance(TEAM_LOCATIONS.get(away_team, (0,0)), TEAM_LOCATIONS.get(home_team, (0,0)))
    rest_score = max(-6, min(6, (home_rest - away_rest) * 2))
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
    weighted_spread = 3.0 + rest_score + def_score + injury_score + pace_score + net_score + travel_score + split_score + h2h_score + altitude_score + ft_score + reb_score + three_score
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    return {'home_win_prob': round(home_win_prob, 1), 'kalshi_price': kalshi_price, 'edge': round(home_win_prob - kalshi_price, 1), 'expected_spread': round(weighted_spread, 1)}

def calc_ml_score(home_team, away_team, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    home_loc, away_loc = TEAM_LOCATIONS.get(home_team, (0,0)), TEAM_LOCATIONS.get(away_team, (0,0))
    score_home, score_away, reasons_home, reasons_away = 0, 0, [], []
    home_b2b, away_b2b = home_team in yesterday_teams, away_team in yesterday_teams
    if away_b2b and not home_b2b:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    else:
        score_home += 0.5
        score_away += 0.5
    home_net, away_net = home.get('net_rating', 0), away.get('net_rating', 0)
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
    home_def, away_def = home.get('def_rank', 15), away.get('def_rank', 15)
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
    home_inj, home_out, home_gtd = get_injury_score(home_team, injuries)
    away_inj, away_out, away_gtd = get_injury_score(away_team, injuries)
    inj_diff = away_inj - home_inj
    if inj_diff > 3:
        score_home += 1.0
        if away_out: reasons_home.append(f"🏥 {away_out[0][:12]} OUT")
    elif inj_diff > 1:
        score_home += 0.6
        if away_out: reasons_home.append(f"🏥 {away_out[0][:12]} OUT")
        elif away_gtd: reasons_home.append(f"🏥 {away_gtd[0][:12]} GTD")
    elif inj_diff < -3:
        score_away += 1.0
        if home_out: reasons_away.append(f"🏥 {home_out[0][:12]} OUT")
    elif inj_diff < -1:
        score_away += 0.6
        if home_out: reasons_away.append(f"🏥 {home_out[0][:12]} OUT")
        elif home_gtd: reasons_away.append(f"🏥 {home_gtd[0][:12]} GTD")
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
    home_hw, away_aw = home.get('home_win_pct', 0.5), away.get('away_win_pct', 0.5)
    reasons_home.append(f"🏠 {int(home_hw*100)}% home")
    if home_hw > 0.65: score_home += 0.8
    elif home_hw > 0.55: score_home += 0.5
    if away_aw < 0.35:
        score_home += 0.5
        reasons_home.append(f"📉 Opp {int(away_aw*100)}% road")
    elif away_aw < 0.45:
        score_home += 0.3
    if home.get('division') == away.get('division') and home.get('division'):
        score_home += 0.5
        reasons_home.append("⚔️ Division")
    if home_team == "Denver":
        score_home += 1.0
        reasons_home.append("🏔️ Altitude")
    if home_net > 5 and f"📊 Net +{home_net:.1f}" not in reasons_home:
        score_home += 0.5
        reasons_home.append("⭐ Elite")
    if away_net > 5 and f"📊 Net +{away_net:.1f}" not in reasons_away:
        score_away += 0.5
        reasons_away.append("⭐ Elite")
    total = score_home + score_away
    home_final = round((score_home / total) * 10, 1) if total > 0 else 5.0
    away_final = round((score_away / total) * 10, 1) if total > 0 else 5.0
    if home_final >= away_final:
        return home_team, home_final, round((home_final - 5) * 4, 0), reasons_home[:4], home_out, away_out, home_gtd, away_gtd
    return away_team, away_final, round((away_final - 5) * 4, 0), reasons_away[:4], home_out, away_out, home_gtd, away_gtd

def get_signal_tier(score):
    if score >= 8.0: return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5: return "🔵 BUY", "#00aaff"
    return None, None

def calc_projected_total(home_team, away_team, yesterday_teams):
    home, away = TEAM_STATS.get(home_team, {}), TEAM_STATS.get(away_team, {})
    home_ppg = home.get('ppg', 112)
    away_ppg = away.get('ppg', 112)
    base = home_ppg + away_ppg
    home_def = home.get('def_rank', 15)
    away_def = away.get('def_rank', 15)
    home_off_adj = (away_def - 15) * 0.4
    away_off_adj = (home_def - 15) * 0.4
    def_adj = home_off_adj + away_off_adj
    home_pace = home.get('pace', 100)
    away_pace = away.get('pace', 100)
    pace_factor = ((home_pace + away_pace) / 2 - 100) * 0.5
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    fatigue_adj = -4 if home_b2b and away_b2b else (-2 if home_b2b or away_b2b else 0)
    altitude_adj = -3 if home_team == "Denver" else 0
    projected = base + def_adj + pace_factor + fatigue_adj + altitude_adj
    return round(projected)

def calc_totals_score(home_team, away_team, yesterday_teams, injuries):
    home, away = TEAM_STATS.get(home_team, {}), TEAM_STATS.get(away_team, {})
    reasons = []
    pace_score = 0.0
    avg_pace = (home.get('pace', 100) + away.get('pace', 100)) / 2
    if avg_pace >= 101.5:
        pace_score = 1.75 * 1.2
        reasons.append(f"🔥 Fast {avg_pace:.1f}")
    elif avg_pace >= 100.5:
        pace_score = 1.0 * 1.1
        reasons.append(f"🔥 Pace {avg_pace:.1f}")
    elif avg_pace <= 97.5:
        pace_score = -1.5 * 0.7
        reasons.append(f"🐢 Slow {avg_pace:.1f}")
    elif avg_pace <= 98.5:
        pace_score = -0.75 * 0.6
        reasons.append(f"🐢 Pace {avg_pace:.1f}")
    pace_score = max(-1.75, min(1.75, pace_score))
    ppg_score = 0.0
    combined_ppg = home.get('ppg', 112) + away.get('ppg', 112)
    if combined_ppg >= 238:
        ppg_score = 1.75 * 1.3
        reasons.append(f"🔥 High PPG {combined_ppg:.0f}")
    elif combined_ppg >= 230:
        ppg_score = 1.0 * 1.2
        reasons.append(f"🔥 PPG {combined_ppg:.0f}")
    elif combined_ppg <= 212:
        ppg_score = -1.5 * 0.7
        reasons.append(f"🐢 Low PPG {combined_ppg:.0f}")
    elif combined_ppg <= 220:
        ppg_score = -0.75 * 0.6
        reasons.append(f"🐢 PPG {combined_ppg:.0f}")
    ppg_score = max(-1.75, min(1.75, ppg_score))
    def_score = 0.0
    avg_def = (home.get('def_rank', 15) + away.get('def_rank', 15)) / 2
    if avg_def >= 25:
        def_score = 1.25 * 1.1
        reasons.append(f"💥 Weak DEF #{int(avg_def)}")
    elif avg_def >= 21:
        def_score = 0.75 * 1.0
        reasons.append(f"💥 DEF #{int(avg_def)}")
    elif avg_def <= 5:
        def_score = -1.25 * 0.9
        reasons.append(f"🛡️ Elite DEF #{int(avg_def)}")
    elif avg_def <= 9:
        def_score = -0.75 * 0.8
        reasons.append(f"🛡️ DEF #{int(avg_def)}")
    def_score = max(-1.25, min(1.25, def_score))
    sit_score = 0.0
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if home_b2b and away_b2b:
        sit_score -= 0.75 * 1.0
        reasons.append("🛏️ Both B2B")
    elif home_b2b or away_b2b:
        sit_score -= 0.4 * 1.0
        reasons.append(f"🛏️ {(home_team if home_b2b else away_team)[:3]} B2B")
    if home_team == "Denver":
        sit_score -= 0.4
        reasons.append("🏔️ Altitude")
    sit_score = max(-1.0, min(1.0, sit_score))
    shoot_score = 0.0
    avg_3pt = (home.get('three_pct', 36) + away.get('three_pct', 36)) / 2
    if avg_3pt >= 37.5:
        shoot_score = 0.75 * 1.1
        reasons.append(f"🎯 High 3PT {avg_3pt:.1f}%")
    elif avg_3pt <= 34.5:
        shoot_score = -0.5 * 0.8
        reasons.append(f"🎯 Low 3PT {avg_3pt:.1f}%")
    avg_ft = (home.get('ft_rate', 0.25) + away.get('ft_rate', 0.25)) / 2
    if avg_ft >= 0.28:
        shoot_score -= 0.3
    elif avg_ft <= 0.22:
        shoot_score += 0.3
    shoot_score = max(-1.0, min(1.0, shoot_score))
    match_score = 0.0
    home_net = home.get('net_rating', 0)
    away_net = away.get('net_rating', 0)
    net_diff = abs(home_net - away_net)
    if home_net > 8 and away_net > 5:
        match_score = 0.75
        reasons.append("⭐ Both elite")
    elif net_diff >= 12:
        match_score = 0.5
        reasons.append("💥 Mismatch")
    elif net_diff <= 2:
        match_score = -0.4
        reasons.append("⚔️ Close game")
    match_score = max(-0.75, min(0.75, match_score))
    inj_score = 0.0
    _, home_out, _ = get_injury_score(home_team, injuries)
    _, away_out, _ = get_injury_score(away_team, injuries)
    if home_out or away_out:
        inj_score = -0.6
        reasons.append(f"🏥 {', '.join([n[:8] for n in (home_out + away_out)[:2]])} OUT")
    inj_score = max(-0.75, min(0.75, inj_score))
    raw_score = pace_score + ppg_score + def_score + sit_score + shoot_score + match_score + inj_score
    if abs(raw_score) < 0.75:
        return None, 5.0, ["No clear edge"]
    confidence = round(min(8.5, max(1.5, 5.0 + abs(raw_score) * 1.25)), 1)
    if raw_score < 0:
        under_reasons = [r for r in reasons if any(x in r for x in ["🐢", "🛡️", "🛏️", "🏔️", "⚔️", "🏥", "Low"])][:4]
        return "NO", confidence, under_reasons if under_reasons else ["Under signals"]
    else:
        over_reasons = [r for r in reasons if any(x in r for x in ["🔥", "💥", "⭐", "High"])][:4]
        return "YES", confidence, over_reasons if over_reasons else ["Over signals"]

def get_totals_signal_tier(score, pick):
    if pick is None:
        return None, None
    if score >= 7.0: return f"🟢 STRONG {pick}", "#00ff00"
    elif score >= 6.0: return f"🔵 {pick}", "#00aaff"
    return None, None

games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
espn_injuries, injury_timestamp = fetch_espn_injuries()
rotowire_injuries = fetch_rotowire_injuries()
injuries = merge_injuries(espn_injuries, rotowire_injuries)
now = datetime.now(pytz.timezone('US/Eastern'))

st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')} | v16.2 | 🔄 Press R to refresh")

injury_time_str = injury_timestamp.strftime('%I:%M %p') if injury_timestamp else "?"
roto_status = "✅" if rotowire_injuries else "❌"
espn_status = "✅" if espn_injuries else "❌"
st.markdown(f"<div style='background:#331a00;padding:8px 12px;border-radius:6px;border:1px solid #ff8800;margin-bottom:15px'><span style='color:#ff8800'>⚠️ <b>INJURY DATA:</b></span> ESPN {espn_status} | Rotowire {roto_status} | Updated: {injury_time_str} ET — <b>Always verify before betting!</b></div>", unsafe_allow_html=True)

st.subheader("🎯 BIG SNAPSHOT - TODAY'S ML PICKS")
if game_list:
    all_picks = []
    for game_key in game_list:
        parts = game_key.split("@")
        pick, score, edge, reasons, home_out, away_out, home_gtd, away_gtd = calc_ml_score(parts[1], parts[0], yesterday_teams, injuries)
        signal, color = get_signal_tier(score)
        if signal:
            g = games.get(game_key)
            trend_label, trend_color, trend_diff = None, None, None
            if g:
                trend_label, trend_color, trend_diff = get_score_trend(g, parts[1], parts[0])
            all_picks.append({'game': game_key, 'home': parts[1], 'away': parts[0], 'pick': pick, 'score': score, 'edge': edge, 'color': color, 'reasons': reasons, 'home_out': home_out, 'away_out': away_out, 'home_gtd': home_gtd, 'away_gtd': away_gtd, 'trend_label': trend_label, 'trend_color': trend_color, 'trend_diff': trend_diff, 'game_data': g})
    all_picks.sort(key=lambda x: x['score'], reverse=True)
    best_ml_pick = all_picks[0] if all_picks else None
    for tier, min_score, label in [("strong", 8.0, "### 🟢 STRONG BUY"), ("buy", 6.5, "### 🔵 BUY")]:
        picks = [p for p in all_picks if (p['score'] >= 8.0 if tier == "strong" else 6.5 <= p['score'] < 8.0)]
        if picks:
            st.markdown(label)
            for p in picks:
                is_best = (best_ml_pick and p['game'] == best_ml_pick['game'])
                if is_best:
                    st.markdown(f"""<div style='background:#2a1a00;padding:12px;border-radius:8px;border:2px solid #ff8800;margin-bottom:8px'>
                        <span style='color:#ff8800;font-weight:bold'>⭐ BEST VALUE</span>
                    </div>""", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3, 2, 4, 2])
                tag = "🏠" if p['pick'] == p['home'] else "✈️"
                opp = p['away'] if p['pick'] == p['home'] else p['home']
                display_color = "#ff8800" if is_best else p['color']
                opp_out = p['away_out'] if p['pick'] == p['home'] else p['home_out']
                opp_gtd = p['away_gtd'] if p['pick'] == p['home'] else p['home_gtd']
                pick_out = p['home_out'] if p['pick'] == p['home'] else p['away_out']
                pick_gtd = p['home_gtd'] if p['pick'] == p['home'] else p['away_gtd']
                col1.markdown(f"**<span style='color:{display_color}'>{p['pick']}</span>** {tag} vs {opp}", unsafe_allow_html=True)
                col2.markdown(f"<span style='color:{display_color};font-weight:bold'>{p['score']}/10 | +{p['edge']:.0f}%</span>", unsafe_allow_html=True)
                col3.markdown(f"<span style='color:#aaa'>{' • '.join(p['reasons'])}</span>", unsafe_allow_html=True)
                col4.link_button(f"⭐ BUY {p['pick']}" if is_best else (f"🚀 BUY {p['pick']}" if tier == "strong" else f"🔗 BUY {p['pick']}"), build_kalshi_ml_url(p['away'], p['home']))
                injury_info = []
                if opp_out:
                    injury_info.append(f"<span style='color:#00ff00'>✅ OPP STARS OUT: <b>{', '.join(opp_out)}</b></span>")
                if opp_gtd:
                    injury_info.append(f"<span style='color:#88ff88'>⚠️ OPP STARS GTD: <b>{', '.join(opp_gtd)}</b></span>")
                if pick_out:
                    injury_info.append(f"<span style='color:#ff4444'>⛔ YOUR PICK OUT: <b>{', '.join(pick_out)}</b></span>")
                if pick_gtd:
                    injury_info.append(f"<span style='color:#ffaa00'>⚠️ YOUR PICK GTD: <b>{', '.join(pick_gtd)}</b></span>")
                if injury_info:
                    st.markdown(f"<div style='margin-left:20px;font-size:0.9em'>{' | '.join(injury_info)}</div>", unsafe_allow_html=True)
                if p['trend_label'] and p['game_data']:
                    g = p['game_data']
                    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
                    if mins >= 6:
                        proj = round((g['total'] / mins) * 48)
                        game_status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}"
                        st.markdown(f"<div style='margin-left:20px;font-size:0.9em'><span style='color:{p['trend_color']}'>{p['trend_label']}</span> | Score: {g['total']} | Proj: {proj} | {game_status} | Diff: {p['trend_diff']:+.0f} vs expected</div>", unsafe_allow_html=True)
    if not all_picks:
        st.info("⚪ No actionable ML plays today")
else:
    st.info("No games scheduled today")

st.divider()

st.subheader("🎯 TOTALS BIG SNAPSHOT")
if game_list:
    all_totals = []
    for game_key in game_list:
        parts = game_key.split("@")
        pick, score, reasons = calc_totals_score(parts[1], parts[0], yesterday_teams, injuries)
        if pick is None:
            continue
        signal, color = get_totals_signal_tier(score, pick)
        if signal:
            projected = calc_projected_total(parts[1], parts[0], yesterday_teams)
            kalshi_line, _ = fetch_kalshi_markets(parts[0], parts[1])
            if not kalshi_line:
                kalshi_line = 232
            best_thresh, best_cushion, best_price = get_best_threshold(parts[0], parts[1], projected, pick)
            g = games.get(game_key)
            trend_label, trend_color, trend_diff = None, None, None
            if g:
                trend_label, trend_color, trend_diff = get_score_trend(g, parts[1], parts[0])
            _, home_out, home_gtd = get_injury_score(parts[1], injuries)
            _, away_out, away_gtd = get_injury_score(parts[0], injuries)
            all_totals.append({'game': game_key, 'home': parts[1], 'away': parts[0], 'pick': pick, 'score': score, 'color': color, 'projected': projected, 'kalshi_line': kalshi_line, 'best_thresh': best_thresh, 'best_cushion': best_cushion, 'best_price': best_price, 'reasons': reasons, 'trend_label': trend_label, 'trend_color': trend_color, 'trend_diff': trend_diff, 'game_data': g, 'home_out': home_out, 'away_out': away_out, 'home_gtd': home_gtd, 'away_gtd': away_gtd})
    all_totals.sort(key=lambda x: x['score'], reverse=True)
    best_no_pick = next((p for p in all_totals if p['pick'] == 'NO'), None)
    best_yes_pick = next((p for p in all_totals if p['pick'] == 'YES'), None)
    for tier, min_s, max_s, label in [("strong_no", 7.0, 99, "### 🟢 STRONG NO"), ("strong_yes", 7.0, 99, "### 🟢 STRONG YES"), ("no", 6.0, 7.0, "### 🔵 NO"), ("yes", 6.0, 7.0, "### 🔵 YES")]:
        side = "NO" if "no" in tier else "YES"
        picks = [p for p in all_totals if p['pick'] == side and ((p['score'] >= 7.0) if "strong" in tier else (6.0 <= p['score'] < 7.0))]
        if picks:
            st.markdown(label)
            for p in picks:
                is_best = (side == 'NO' and best_no_pick and p['game'] == best_no_pick['game']) or (side == 'YES' and best_yes_pick and p['game'] == best_yes_pick['game'])
                if is_best:
                    st.markdown(f"""<div style='background:#2a1a00;padding:12px;border-radius:8px;border:2px solid #ff8800;margin-bottom:8px'>
                        <span style='color:#ff8800;font-weight:bold'>⭐ BEST {side}</span>
                    </div>""", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
                display_color = "#ff8800" if is_best else p['color']
                col1.markdown(f"**{p['away']}** @ **{p['home']}**")
                col2.markdown(f"<span style='color:{display_color};font-weight:bold'>{p['score']}/10</span>", unsafe_allow_html=True)
                
                # Simple recommendation
                if p.get('best_thresh') and p.get('best_cushion'):
                    col3.markdown(f"🎯 <span style='color:#00ff00'><b>BUY {side} {p['best_thresh']}</b></span> (+{p['best_cushion']:.0f} cushion)", unsafe_allow_html=True)
                else:
                    col3.markdown(f"⚠️ Market closed", unsafe_allow_html=True)
                
                btn_label = f"⭐ BUY {side}" if is_best else (f"🚀 BUY {side}" if "strong" in tier else f"🔗 BUY {side}")
                col4.link_button(btn_label, build_kalshi_totals_url(p['away'], p['home']))
                if p.get('reasons'):
                    st.markdown(f"<div style='margin-left:20px;font-size:0.9em;color:#aaa'>{' • '.join(p['reasons'])}</div>", unsafe_allow_html=True)
                all_out = p['home_out'] + p['away_out']
                all_gtd = p['home_gtd'] + p['away_gtd']
                if all_out or all_gtd:
                    injury_parts = []
                    if all_out:
                        injury_parts.append(f"<span style='color:#ff6666'>🏥 OUT: {', '.join(all_out)}</span>")
                    if all_gtd:
                        injury_parts.append(f"<span style='color:#ffaa00'>⚠️ GTD: {', '.join(all_gtd)}</span>")
                    st.markdown(f"<div style='margin-left:20px;font-size:0.9em'>{' | '.join(injury_parts)}</div>", unsafe_allow_html=True)
                if p['trend_label'] and p['game_data']:
                    g = p['game_data']
                    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
                    if mins >= 6:
                        proj = round((g['total'] / mins) * 48)
                        game_status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}"
                        trend_help = "✅ Supports NO" if (p['pick'] == 'NO' and p['trend_diff'] < 0) or (p['pick'] == 'YES' and p['trend_diff'] > 0) else "⚠️ Against pick" if (p['pick'] == 'NO' and p['trend_diff'] > 4) or (p['pick'] == 'YES' and p['trend_diff'] < -4) else ""
                        st.markdown(f"<div style='margin-left:20px;font-size:0.9em'><span style='color:{p['trend_color']}'>{p['trend_label']}</span> | Live: {g['total']} | Proj: {proj} | {game_status} | {trend_help}</div>", unsafe_allow_html=True)
    if not all_totals:
        st.info("⚪ No actionable totals plays today")

st.divider()

if yesterday_teams:
    st.info(f"📅 **B2B Teams Today:** {', '.join(sorted(yesterday_teams))}")

st.subheader("⭐ STAR INJURY REPORT")
injury_time_str = injury_timestamp.strftime('%I:%M %p ET') if injury_timestamp else "Unknown"
st.warning(f"⚠️ **ALWAYS VERIFY INJURIES BEFORE BETTING** — Data from ESPN + Rotowire as of {injury_time_str}. Check [@ShamsCharania](https://twitter.com/ShamsCharania) and [@wojespn](https://twitter.com/wojespn) for late scratches.")
star_injuries = []
for team in TEAM_STATS.keys():
    _, out, gtd = get_injury_score(team, injuries)
    for name in out:
        star_injuries.append({'team': team, 'player': name, 'status': 'OUT', 'color': '#ff4444'})
    for name in gtd:
        star_injuries.append({'team': team, 'player': name, 'status': 'GTD', 'color': '#ffaa00'})
if star_injuries:
    cols = st.columns(3)
    for i, inj in enumerate(star_injuries):
        with cols[i % 3]:
            st.markdown(f"<span style='color:{inj['color']}'><b>{inj['player']}</b></span> ({inj['team']}) - {inj['status']}", unsafe_allow_html=True)
else:
    st.info("✅ No star players currently OUT or GTD")

st.divider()

st.subheader("🔥 TOP PICKS - BLOWOUT RISK")
if game_list:
    top_picks = []
    for game_key in game_list:
        parts = game_key.split("@")
        if parts[0] in yesterday_teams and parts[1] not in yesterday_teams:
            home_i, _, _ = get_injury_score(parts[1], injuries)
            away_i, _, _ = get_injury_score(parts[0], injuries)
            res = calc_12_factor_edge(parts[1], parts[0], 1, 0, home_i, away_i, 50)
            top_picks.append({'game': game_key, 'home': parts[1], 'away': parts[0], 'prob': res['home_win_prob']})
    top_picks.sort(key=lambda x: x['prob'], reverse=True)
    if top_picks:
        for p in top_picks:
            st.markdown(f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid #00ff00;margin-bottom:10px'>
                <span style='color:#00ff00;font-size:1.5em;font-weight:bold'>🎯 BUY {p['home']} ML</span>
                <br><span style='color:#aaa'>{p['game'].replace('@', ' @ ')} | {p['home']} {p['prob']:.0f}% | 🔴 {p['away']} B2B</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("⚪ No BLOWOUT RISK games today")

st.divider()

st.subheader("📊 LIVE SCORE TRENDS")
trend_data = []
for gk, g in games.items():
    parts = gk.split("@")
    trend_label, trend_color, trend_diff = get_score_trend(g, parts[1], parts[0])
    if trend_label:
        mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
        proj = round((g['total'] / mins) * 48) if mins > 0 else 0
        trend_data.append({'game': gk, 'label': trend_label, 'color': trend_color, 'diff': trend_diff, 'total': g['total'], 'proj': proj, 'mins': mins, 'period': g['period'], 'clock': g['clock'], 'final': g['status_type'] == "STATUS_FINAL"})
trend_data.sort(key=lambda x: x['diff'], reverse=True)
if trend_data:
    for t in trend_data:
        game_status = 'FINAL' if t['final'] else f"Q{t['period']} {t['clock']}"
        st.markdown(f"**{t['game'].replace('@', ' @ ')}** — <span style='color:{t['color']}'><b>{t['label']}</b></span> — Score: {t['total']} | Proj: {t['proj']} | Diff: <b>{t['diff']:+.0f}</b> vs expected — {game_status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played")

st.divider()

st.subheader("➕ ADD NEW POSITION")
game_options = ["Select a game..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("🏀 Game", game_options)
threshold_select = st.number_input("🎯 Threshold", min_value=180.0, max_value=280.0, value=225.5, step=0.5)
if selected_game != "Select a game...":
    parts = selected_game.replace(" @ ", "@").split("@")
    st.link_button(f"🔗 View on Kalshi", build_kalshi_totals_url(parts[0], parts[1]), use_container_width=True)
with st.form("add_position"):
    col1, col2, col3 = st.columns(3)
    side = col1.selectbox("Side", ["NO (Under)", "YES (Over)"])
    price = col2.number_input("Price (¢)", 1, 99, 50)
    contracts = col3.number_input("Contracts", 1, 1000, st.session_state.default_contracts)
    submitted = st.form_submit_button("✅ ADD POSITION", use_container_width=True)
    if submitted and selected_game != "Select a game...":
        game_key = selected_game.replace(" @ ", "@")
        st.session_state.positions.append({'game': game_key, 'side': "NO" if "NO" in side else "YES", 'threshold': threshold_select, 'price': price, 'contracts': contracts, 'cost': round(price * contracts / 100, 2)})
        st.rerun()

st.divider()

st.subheader("📈 ACTIVE POSITIONS")
if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        g = games.get(pos['game'])
        if g:
            mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            proj = round((g['total'] / mins) * 48) if mins > 0 else None
            cushion = (pos['threshold'] - proj) if pos['side'] == "NO" and proj else ((proj - pos['threshold']) if proj else 0)
            pot_win = round((100 - pos['price']) * pos['contracts'] / 100, 2)
            if is_final:
                won = (g['total'] < pos['threshold']) if pos['side'] == "NO" else (g['total'] > pos['threshold'])
                status, color = ("✅ WON!", "#00ff00") if won else ("❌ LOST", "#ff0000")
            elif proj:
                if cushion >= 15: status, color = "🟢 VERY SAFE", "#00ff00"
                elif cushion >= 8: status, color = "🟢 GOOD", "#00ff00"
                elif cushion >= 3: status, color = "🟡 ON TRACK", "#ffff00"
                elif cushion >= -3: status, color = "🟠 WARNING", "#ff8800"
                else: status, color = "🔴 AT RISK", "#ff0000"
            else: status, color = "⏳ WAITING", "#888888"
            game_status = 'FINAL' if is_final else f"Q{g['period']} {g['clock']}"
            st.markdown(f"""<div style='background:#1a1a2e;padding:15px;border-radius:10px;border:2px solid {color};margin-bottom:10px'>
                <b style='color:#fff'>{pos['game'].replace('@', ' @ ')}</b> <span style='color:#888'>{game_status}</span>
                <span style='color:{color};float:right;font-weight:bold'>{status}</span><br>
                <span style='color:#aaa'>{pos['side']} {pos['threshold']} | {pos['contracts']}x @ {pos['price']}¢ | Proj: {proj or '—'} | Cushion: <b style='color:{color}'>{cushion:+.0f}</b> | Win: +${pot_win}</span>
            </div>""", unsafe_allow_html=True)
        if st.button("🗑️ Remove", key=f"del_{idx}"):
            st.session_state.positions.pop(idx)
            st.rerun()
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked")

st.divider()

st.subheader("🎯 CUSHION SCANNER")
cush_side = st.selectbox("Bet Side", ["NO", "YES"])
thresholds = [219.5, 225.5, 231.5, 237.5, 243.5, 249.5]
cush_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins > 0 and g['status_type'] != "STATUS_FINAL":
        proj = round((g['total'] / mins) * 48) if mins > 0 else 0
        pace_val = g['total'] / mins if mins > 0 else 0
        cush_data.append({'game': gk, 'proj': proj, 'pace': pace_val, 'mins': mins, 'away': g['away_team'], 'home': g['home_team']})
if cush_data:
    hcols = st.columns([3, 1, 1, 1] + [1]*len(thresholds))
    hcols[0].markdown("**Game**")
    hcols[1].markdown("**Mins**")
    hcols[2].markdown("**Proj**")
    hcols[3].markdown("**Pace**")
    for i, t in enumerate(thresholds):
        hcols[i+4].markdown(f"**{t}**")
    for cd in cush_data:
        if cd['pace'] < 4.5: pace_color = "#00ff00"
        elif cd['pace'] < 4.8: pace_color = "#ffff00"
        elif cd['pace'] < 5.2: pace_color = "#ff8800"
        else: pace_color = "#ff0000"
        rcols = st.columns([3, 1, 1, 1] + [1]*len(thresholds))
        rcols[0].write(cd['game'].replace("@", " @ "))
        rcols[1].write(f"{cd['mins']:.0f}")
        rcols[2].write(f"{cd['proj']}")
        rcols[3].markdown(f"<span style='color:{pace_color}'>{cd['pace']:.2f}</span>", unsafe_allow_html=True)
        best_thresh, best_cushion = None, -999
        for t in thresholds:
            c = (t - cd['proj']) if cush_side == "NO" else (cd['proj'] - t)
            if 12 <= c < 20 and c > best_cushion:
                best_cushion, best_thresh = c, t
        if best_thresh is None:
            for t in thresholds:
                c = (t - cd['proj']) if cush_side == "NO" else (cd['proj'] - t)
                if 6 <= c < 12 and c > best_cushion:
                    best_cushion, best_thresh = c, t
        for i, t in enumerate(thresholds):
            cushion = (t - cd['proj']) if cush_side == "NO" else (cd['proj'] - t)
            is_best = (t == best_thresh)
            if is_best:
                rcols[i+4].markdown(f"<span style='color:#ff8800'>**⭐+{cushion:.0f}**</span>", unsafe_allow_html=True)
            elif cushion > 0:
                rcols[i+4].markdown(f"<span style='color:#00ff00'>**+{cushion:.0f}**</span>", unsafe_allow_html=True)
            else:
                rcols[i+4].markdown(f"<span style='color:#ff4444'>{cushion:.0f}</span>", unsafe_allow_html=True)
else:
    st.info("No live games right now")

st.divider()

st.subheader("🔥 PACE SCANNER")
pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        pace_data.append({"game": gk, "pace": pace, "proj": round(pace * 48), "total": g['total'], "mins": mins, "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"})
pace_data.sort(key=lambda x: x['pace'])
for p in pace_data:
    if p['pace'] < 4.5: lbl, clr = "🟢 SLOW", "#00ff00"
    elif p['pace'] < 4.8: lbl, clr = "🟡 AVG", "#ffff00"
    elif p['pace'] < 5.2: lbl, clr = "🟠 FAST", "#ff8800"
    else: lbl, clr = "🔴 SHOOTOUT", "#ff0000"
    status = 'FINAL' if p['final'] else f"Q{p['period']} {p['clock']}"
    st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']} pts / {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
if not pace_data:
    st.info("No games with 6+ minutes played")

st.divider()

st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            game_status = 'FINAL' if g['status_type'] == 'STATUS_FINAL' else f"Q{g['period']} {g['clock']}"
            st.caption(f"{game_status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()
st.caption("⚠️ For entertainment only. Not financial advice. Always verify information before placing any bets.")
