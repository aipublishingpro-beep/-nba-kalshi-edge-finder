import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import uuid
import base64
import time

# Try to import cryptography for trading (optional)
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== v13.9 ELITE TRADE-ONLY MODE ==========
# Philosophy: This is a TRADE AUTHORIZATION SYSTEM, not a dashboard.
# If a game is NOT tradable today, it must NOT appear anywhere in the UI.

# ========== AUTO-REFRESH (Only after 7PM ET) ==========
current_hour = datetime.now(pytz.timezone('US/Eastern')).hour
if current_hour >= 19:
    st.markdown("""
    <meta http-equiv="refresh" content="30">
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
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
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
    auto_status = "⏸️ Auto-refresh OFF (starts 7PM ET)"

# ========== EDGE TRACKING (for half-life) ==========
if 'edge_first_seen' not in st.session_state:
    st.session_state.edge_first_seen = {}

def get_edge_age_minutes(game_key, current_score, threshold=6.5):
    """Track how long an edge has existed. Returns age in minutes and label."""
    now = time.time()
    if current_score >= threshold:
        if game_key not in st.session_state.edge_first_seen:
            st.session_state.edge_first_seen[game_key] = now
        age_mins = (now - st.session_state.edge_first_seen[game_key]) / 60
    else:
        if game_key in st.session_state.edge_first_seen:
            del st.session_state.edge_first_seen[game_key]
        age_mins = 0
    
    if age_mins <= 3:
        label = "🟢 FRESH"
        decay = 0
    elif age_mins <= 6:
        label = "🟡 AGING"
        decay = 0.5
    elif age_mins <= 10:
        label = "🟠 STALE"
        decay = 1.5
    else:
        label = "🔴 EXPIRED"
        decay = 99  # Force non-tradable
    
    return age_mins, label, decay

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

if "positions" not in st.session_state:
    st.session_state.positions = []

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

# ============================================================
# v13.9 GATE SYSTEMS
# ============================================================

def calc_ml_score_with_factors(home_team, away_team, yesterday_teams, injuries):
    """Calculate 10-factor ML score with factor breakdown for gate checking."""
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    home_loc = TEAM_LOCATIONS.get(home_team, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away_team, (0, 0))
    
    factors = {
        'fatigue': 0, 'pace': 0, 'blowout': 0, 'travel': 0, 'net_rating': 0,
        'defense': 0, 'home_court': 0, 'injury': 0, 'splits': 0, 'quality': 0
    }
    reasons = []
    
    # 1. REST/FATIGUE
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if away_b2b and not home_b2b:
        factors['fatigue'] = 1.0
        reasons.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        factors['fatigue'] = -1.0
    else:
        factors['fatigue'] = 0.3
    
    # 2. NET RATING
    home_net = home.get('net_rating', 0)
    away_net = away.get('net_rating', 0)
    net_diff = home_net - away_net
    if net_diff > 5:
        factors['net_rating'] = 1.0
        reasons.append(f"📊 Net +{home_net:.1f}")
    elif net_diff > 2:
        factors['net_rating'] = 0.7
    elif net_diff > 0:
        factors['net_rating'] = 0.3
    elif net_diff > -2:
        factors['net_rating'] = -0.3
    elif net_diff > -5:
        factors['net_rating'] = -0.7
    else:
        factors['net_rating'] = -1.0
    
    # 3. DEFENSE
    home_def = home.get('def_rank', 15)
    if home_def <= 5:
        factors['defense'] = 1.0
        reasons.append(f"🛡️ #{home_def} DEF")
    elif home_def <= 10:
        factors['defense'] = 0.7
    elif home_def <= 15:
        factors['defense'] = 0.4
    else:
        factors['defense'] = 0.1
    
    # 4. HOME COURT
    factors['home_court'] = 1.0
    reasons.append(f"🏠 {int(home.get('home_win_pct', 0.5)*100)}% home")
    
    # 5. INJURY
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    inj_diff = away_inj - home_inj
    if inj_diff > 3:
        factors['injury'] = 1.0
        if away_stars:
            reasons.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff > 1:
        factors['injury'] = 0.6
    elif inj_diff < -3:
        factors['injury'] = -1.0
    elif inj_diff < -1:
        factors['injury'] = -0.6
    else:
        factors['injury'] = 0.2
    
    # 6. TRAVEL
    travel_miles = calc_distance(away_loc, home_loc)
    if travel_miles > 2000:
        factors['travel'] = 1.0
        reasons.append(f"✈️ {int(travel_miles)}mi")
    elif travel_miles > 1500:
        factors['travel'] = 0.7
    elif travel_miles > 1000:
        factors['travel'] = 0.5
    elif travel_miles > 500:
        factors['travel'] = 0.3
    else:
        factors['travel'] = 0.1
    
    # 7. SPLITS
    home_hw = home.get('home_win_pct', 0.5)
    away_aw = away.get('away_win_pct', 0.5)
    if home_hw > 0.65 and away_aw < 0.35:
        factors['splits'] = 1.0
    elif home_hw > 0.55:
        factors['splits'] = 0.5
    else:
        factors['splits'] = 0.2
    
    # 8. PACE (beneficial for stronger team)
    pace_diff = home.get('pace', 100) - away.get('pace', 100)
    if home_net > away_net and pace_diff > 0:
        factors['pace'] = 0.5
    else:
        factors['pace'] = 0.2
    
    # 9. BLOWOUT POTENTIAL
    if net_diff > 8:
        factors['blowout'] = 0.8
        reasons.append("💥 Mismatch")
    else:
        factors['blowout'] = 0.2
    
    # 10. QUALITY
    if home_net > 5:
        factors['quality'] = 0.5
    else:
        factors['quality'] = 0.2
    
    # Calculate total and normalize
    positive_sum = sum(max(0, v) for v in factors.values())
    negative_sum = abs(sum(min(0, v) for v in factors.values()))
    total = positive_sum + negative_sum
    
    if total > 0:
        home_score = round((positive_sum / total) * 10, 1)
    else:
        home_score = 5.0
    
    # Calculate max factor share for single-factor gate
    if positive_sum > 0:
        max_factor_share = max(max(0, v) for v in factors.values()) / positive_sum
    else:
        max_factor_share = 0
    
    # Determine dominant factor
    dominant_factor = max(factors.keys(), key=lambda k: factors[k])
    
    return {
        'pick': home_team,
        'score': home_score,
        'edge': round((home_score - 5) * 4, 0),
        'reasons': reasons[:4],
        'factors': factors,
        'max_factor_share': max_factor_share,
        'dominant_factor': dominant_factor,
        'home_stars': home_stars,
        'away_stars': away_stars
    }

def calc_totals_score_with_factors(home_team, away_team, yesterday_teams, injuries):
    """Calculate totals score with factor breakdown."""
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    
    factors = {
        'pace': 0, 'defense': 0, 'fatigue': 0, 'three_pct': 0,
        'injury': 0, 'blowout': 0, 'altitude': 0, 'ft_rate': 0,
        'rebounds': 0, 'home_scoring': 0
    }
    reasons_under = []
    reasons_over = []
    
    # 1. PACE
    avg_pace = (home.get('pace', 100) + away.get('pace', 100)) / 2
    if avg_pace < 98.5:
        factors['pace'] = 1.5
        reasons_under.append(f"🐢 Slow {avg_pace:.1f}")
    elif avg_pace < 99.5:
        factors['pace'] = 0.8
    elif avg_pace > 101:
        factors['pace'] = -1.5
        reasons_over.append(f"🔥 Fast {avg_pace:.1f}")
    elif avg_pace > 100:
        factors['pace'] = -0.8
    
    # 2. DEFENSE
    avg_def = (home.get('def_rank', 15) + away.get('def_rank', 15)) / 2
    if avg_def <= 8:
        factors['defense'] = 1.5
        reasons_under.append(f"🛡️ DEF #{int(avg_def)}")
    elif avg_def <= 12:
        factors['defense'] = 0.8
    elif avg_def >= 22:
        factors['defense'] = -1.5
        reasons_over.append(f"💥 DEF #{int(avg_def)}")
    elif avg_def >= 18:
        factors['defense'] = -0.8
    
    # 3. FATIGUE
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if home_b2b and away_b2b:
        factors['fatigue'] = 1.5
        reasons_under.append("🛏️ Both B2B")
    elif home_b2b or away_b2b:
        factors['fatigue'] = 0.6
        tired = home_team[:3] if home_b2b else away_team[:3]
        reasons_under.append(f"🛏️ {tired} B2B")
    
    # 4. 3PT%
    avg_3pt = (home.get('three_pct', 36) + away.get('three_pct', 36)) / 2
    if avg_3pt < 35.5:
        factors['three_pct'] = 0.8
        reasons_under.append(f"🎯 Low 3PT {avg_3pt:.1f}%")
    elif avg_3pt > 37.5:
        factors['three_pct'] = -0.8
        reasons_over.append(f"🎯 High 3PT {avg_3pt:.1f}%")
    
    # 5. INJURIES
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    if home_stars or away_stars:
        factors['injury'] = 0.8
        out_names = (home_stars + away_stars)[:2]
        reasons_under.append(f"🏥 {', '.join([n[:8] for n in out_names])} OUT")
    
    # 6. BLOWOUT
    net_diff = abs(home.get('net_rating', 0) - away.get('net_rating', 0))
    if net_diff > 10:
        factors['blowout'] = -0.6
        reasons_over.append("💥 Blowout risk")
    elif net_diff < 3:
        factors['blowout'] = 0.4
        reasons_under.append("⚔️ Close game")
    
    # 7. ALTITUDE
    if home_team == "Denver":
        factors['altitude'] = 0.6
        reasons_under.append("🏔️ Denver altitude")
    
    # 8. FT RATE
    avg_ft = (home.get('ft_rate', 0.25) + away.get('ft_rate', 0.25)) / 2
    if avg_ft > 0.27:
        factors['ft_rate'] = 0.4
        reasons_under.append("🎁 High FT rate")
    elif avg_ft < 0.23:
        factors['ft_rate'] = -0.4
        reasons_over.append("🏃 Low FT rate")
    
    # 9. REBOUNDS
    avg_reb = (home.get('reb_rate', 50) + away.get('reb_rate', 50)) / 2
    if avg_reb > 51.5:
        factors['rebounds'] = 0.4
        reasons_under.append("🏀 Control boards")
    
    # 10. HOME SCORING
    if home.get('home_win_pct', 0.5) > 0.65 and home.get('net_rating', 0) > 5:
        factors['home_scoring'] = -0.4
        reasons_over.append("🏠 Home scoring")
    
    # Calculate scores
    under_sum = sum(max(0, v) for v in factors.values())
    over_sum = abs(sum(min(0, v) for v in factors.values()))
    total = under_sum + over_sum
    
    if total > 0:
        under_score = round((under_sum / total) * 10, 1)
        over_score = round((over_sum / total) * 10, 1)
    else:
        under_score = 5.0
        over_score = 5.0
    
    # Max factor share
    all_abs = [abs(v) for v in factors.values()]
    max_abs = max(all_abs) if all_abs else 0
    max_factor_share = max_abs / total if total > 0 else 0
    dominant_factor = max(factors.keys(), key=lambda k: abs(factors[k]))
    
    if under_score >= over_score:
        return {
            'pick': "NO",
            'score': under_score,
            'reasons': reasons_under[:4],
            'factors': factors,
            'max_factor_share': max_factor_share,
            'dominant_factor': dominant_factor
        }
    else:
        return {
            'pick': "YES",
            'score': over_score,
            'reasons': reasons_over[:4],
            'factors': factors,
            'max_factor_share': max_factor_share,
            'dominant_factor': dominant_factor
        }

def calc_fill_score():
    """Estimate fill quality (simplified without live order book data)."""
    # Without real market data, estimate based on typical NBA market conditions
    # Real implementation would track bid-ask spread, depth stability, etc.
    base_score = 7.0  # NBA markets generally liquid
    return base_score

def check_no_trade_gate(ml_result, totals_result, cushion_result=None):
    """
    Check all NO_TRADE_GATE conditions.
    Returns (gate_triggered, reason)
    """
    # 1. SINGLE-FACTOR DEPENDENCE (>45% from one factor)
    if ml_result and ml_result.get('max_factor_share', 0) > 0.45:
        return True, f"Single-factor dependence: {ml_result['dominant_factor']} ({ml_result['max_factor_share']:.0%})"
    
    if totals_result and totals_result.get('max_factor_share', 0) > 0.45:
        return True, f"Single-factor dependence: {totals_result['dominant_factor']} ({totals_result['max_factor_share']:.0%})"
    
    # 2. CROWD ALIGNMENT RISK (all subsystems >= 8)
    ml_score = ml_result.get('score', 0) if ml_result else 0
    totals_score = totals_result.get('score', 0) if totals_result else 0
    cushion_score = cushion_result.get('score', 0) if cushion_result else 0
    
    if ml_score >= 8 and totals_score >= 8 and cushion_score >= 8:
        return True, "Crowd alignment: All systems showing high agreement (synchronization risk)"
    
    # 3. FILL QUALITY (simplified)
    fill_score = calc_fill_score()
    if fill_score < 6:
        return True, f"Poor fill quality: {fill_score}/10"
    
    return False, None

def get_signal_tier_v139(score):
    """v13.9 language: STRUCTURAL EDGE / CONSIDER instead of STRONG BUY / BUY"""
    if score >= 8.0:
        return "🟢 STRUCTURAL EDGE", "#00ff00"
    elif score >= 6.5:
        return "🔵 CONSIDER", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    elif score >= 4.5:
        return "⚪ NEUTRAL", "#888888"
    else:
        return "🔴 NO TRADE", "#ff0000"

def get_totals_signal_tier_v139(score, pick):
    if score >= 8.0:
        return f"🟢 STRUCTURAL {pick}", "#00ff00"
    elif score >= 6.5:
        return f"🔵 CONSIDER {pick}", "#00aaff"
    elif score >= 5.5:
        return f"🟡 LEAN {pick}", "#ffff00"
    elif score >= 4.5:
        return "⚪ NEUTRAL", "#888888"
    else:
        return "🔴 NO TRADE", "#ff0000"

# ========== FETCH DATA ==========
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

# ============================================================
# v13.9 CORE: COMPUTE ALL GATES BEFORE RENDERING
# ============================================================

def compute_trade_eligible_games(game_list, yesterday_teams, injuries):
    """
    GLOBAL EXECUTION FLOW:
    1. Load today's games
    2. Compute all scores and gates
    3. Filter to TRADE-ELIGIBLE only
    4. Return filtered list
    """
    trade_eligible = []
    filtered_out = []
    
    for game_key in game_list:
        parts = game_key.split("@")
        away_team = parts[0]
        home_team = parts[1]
        
        # Compute ML score with factors
        ml_result = calc_ml_score_with_factors(home_team, away_team, yesterday_teams, injuries)
        
        # Compute totals score with factors
        totals_result = calc_totals_score_with_factors(home_team, away_team, yesterday_teams, injuries)
        
        # Check edge age and decay
        edge_age, age_label, decay = get_edge_age_minutes(game_key, ml_result['score'])
        ml_result['score'] = max(0, ml_result['score'] - decay)
        ml_result['edge_age'] = edge_age
        ml_result['age_label'] = age_label
        
        totals_age, totals_age_label, totals_decay = get_edge_age_minutes(f"{game_key}_totals", totals_result['score'])
        totals_result['score'] = max(0, totals_result['score'] - totals_decay)
        totals_result['edge_age'] = totals_age
        totals_result['age_label'] = totals_age_label
        
        # Check NO_TRADE_GATE
        gate_triggered, gate_reason = check_no_trade_gate(ml_result, totals_result)
        
        # Trade eligibility: score >= 6.5 AND gate not triggered AND not STALE/EXPIRED
        ml_eligible = (
            ml_result['score'] >= 6.5 and 
            not gate_triggered and 
            age_label not in ["🟠 STALE", "🔴 EXPIRED"]
        )
        
        totals_eligible = (
            totals_result['score'] >= 6.5 and 
            not gate_triggered and 
            totals_age_label not in ["🟠 STALE", "🔴 EXPIRED"]
        )
        
        if ml_eligible or totals_eligible:
            trade_eligible.append({
                'game_key': game_key,
                'home': home_team,
                'away': away_team,
                'ml': ml_result if ml_eligible else None,
                'totals': totals_result if totals_eligible else None,
                'gate_triggered': gate_triggered,
                'gate_reason': gate_reason
            })
        else:
            filtered_out.append({
                'game_key': game_key,
                'reason': gate_reason if gate_triggered else f"Score below threshold (ML: {ml_result['score']}, Totals: {totals_result['score']})"
            })
    
    return trade_eligible, filtered_out

# Compute eligibility
trade_eligible, filtered_out = compute_trade_eligible_games(game_list, yesterday_teams, injuries)

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("📖 v13.9 ELITE MODE")
    
    st.markdown("""
    **Philosophy:**  
    This is a **TRADE AUTHORIZATION SYSTEM**.
    
    If a game is NOT tradable, it does NOT appear.
    """)
    
    st.divider()
    
    st.subheader("🚫 NO-TRADE GATES")
    st.markdown("""
    **Single-Factor (>45%)**  
    Edge depends too heavily on one factor
    
    **Crowd Alignment**  
    All systems agree = synchronization risk
    
    **Stale Edge (>6 min)**  
    Market has likely adjusted
    
    **Fill Quality (<6)**  
    Poor execution conditions
    """)
    
    st.divider()
    
    st.subheader("✅ TRADE SIGNALS")
    st.markdown("""
    🟢 **STRUCTURAL EDGE** → 8.0+  
    🔵 **CONSIDER** → 6.5 - 7.9  
    🟡 **LEAN** → 5.5 - 6.4  
    ⚪ **NEUTRAL** → Below 5.5  
    🔴 **NO TRADE** → Gated
    """)
    
    st.divider()
    
    st.subheader("⏱️ Edge Half-Life")
    st.markdown("""
    🟢 FRESH → 0-3 min (no decay)  
    🟡 AGING → 3-6 min (-0.5)  
    🟠 STALE → 6-10 min (-1.5)  
    🔴 EXPIRED → 10+ min (excluded)
    """)
    
    st.divider()
    
    st.subheader(f"📊 Filter Stats")
    st.markdown(f"""
    **Eligible:** {len(trade_eligible)} games  
    **Filtered:** {len(filtered_out)} games
    """)
    
    if filtered_out:
        with st.expander("View filtered games"):
            for f in filtered_out:
                st.caption(f"❌ {f['game_key']}: {f['reason'][:50]}...")
    
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
    st.caption("v13.9 ELITE TRADE-ONLY")

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"v13.9 ELITE TRADE-ONLY | {auto_status} | {now.strftime('%I:%M:%S %p ET')}")

# ============================================================
# v13.9 EMPTY STATE RULE
# ============================================================
if not trade_eligible:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:40px;border-radius:15px;border:2px solid #444;text-align:center;margin:40px 0'>
        <span style='font-size:3em'>🛡️</span>
        <h2 style='color:#888;margin:20px 0'>No tradeable edges today.</h2>
        <p style='color:#666;font-size:1.2em'>Capital preserved.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"📊 {len(filtered_out)} games analyzed. None passed all gates.")
    
    # Still show position tracker if positions exist
    if st.session_state.positions:
        st.divider()
        st.subheader("📈 ACTIVE POSITIONS")
        for idx, pos in enumerate(st.session_state.positions):
            game_key = pos['game']
            g = games.get(game_key)
            if g:
                total = g['total']
                mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
                is_final = g['status_type'] == "STATUS_FINAL"
                projected = round((total / mins) * 48) if mins > 0 else None
                cushion = (pos['threshold'] - projected) if pos['side'] == "NO" and projected else ((projected - pos['threshold']) if projected else 0)
                price = pos.get('price', 50)
                contracts = pos.get('contracts', 1)
                cost = pos.get('cost', round(price * contracts / 100, 2))
                potential_win = round((100 - price) * contracts / 100, 2)
                
                if is_final:
                    won = (total < pos['threshold']) if pos['side'] == "NO" else (total > pos['threshold'])
                    status_label = "✅ WON!" if won else "❌ LOST"
                    status_color = "#00ff00" if won else "#ff0000"
                else:
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
                
                game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
                st.markdown(f"""
                <div style='background:#1a1a2e;padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'>
                    <b>{game_key.replace('@', ' @ ')}</b> — {game_status} — 
                    <span style='color:{status_color}'>{status_label}</span> — 
                    {pos['side']} {pos['threshold']} — Proj: {projected if projected else '—'} — Cushion: {cushion:+.0f}
                </div>
                """, unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# RENDER TRADE-ELIGIBLE GAMES ONLY
# ============================================================

st.subheader("🎯 TRADE-ELIGIBLE ML PICKS")

ml_trades = [t for t in trade_eligible if t['ml'] is not None]
ml_trades.sort(key=lambda x: x['ml']['score'], reverse=True)

if ml_trades:
    for t in ml_trades:
        ml = t['ml']
        signal, color = get_signal_tier_v139(ml['score'])
        reasons_str = " • ".join(ml['reasons']) if ml['reasons'] else "Multiple factors"
        is_home_pick = ml['pick'] == t['home']
        opponent = t['away'] if is_home_pick else t['home']
        home_away_tag = "🏠" if is_home_pick else "✈️"
        
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {color};margin-bottom:10px'>
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <span style='color:{color};font-size:1.4em;font-weight:bold'>{ml['pick']} {home_away_tag}</span>
                <span style='color:{color}'>{signal} | {ml['score']}/10 | +{ml['edge']:.0f}%</span>
            </div>
            <div style='color:#aaa;margin-top:8px'>vs {opponent} | {reasons_str}</div>
            <div style='color:#666;font-size:0.85em;margin-top:5px'>{ml['age_label']} | Factor spread: {(1-ml['max_factor_share'])*100:.0f}% diversified</div>
        </div>
        """, unsafe_allow_html=True)
        
        kalshi_url = build_kalshi_ml_url(t['away'], t['home'])
        st.link_button(f"🚀 EXECUTE {ml['pick'].upper()}", kalshi_url)
        st.markdown("")
else:
    st.info("No ML trades authorized")

st.divider()

st.subheader("🎯 TRADE-ELIGIBLE TOTALS")

totals_trades = [t for t in trade_eligible if t['totals'] is not None]
totals_trades.sort(key=lambda x: x['totals']['score'], reverse=True)

if totals_trades:
    for t in totals_trades:
        tot = t['totals']
        signal, color = get_totals_signal_tier_v139(tot['score'], tot['pick'])
        reasons_str = " • ".join(tot['reasons']) if tot['reasons'] else "Multiple factors"
        
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {color};margin-bottom:10px'>
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <span style='color:{color};font-size:1.4em;font-weight:bold'>{tot['pick']} ({t['away']} @ {t['home']})</span>
                <span style='color:{color}'>{signal} | {tot['score']}/10</span>
            </div>
            <div style='color:#aaa;margin-top:8px'>{reasons_str}</div>
            <div style='color:#666;font-size:0.85em;margin-top:5px'>{tot['age_label']} | Factor spread: {(1-tot['max_factor_share'])*100:.0f}% diversified</div>
        </div>
        """, unsafe_allow_html=True)
        
        kalshi_url = build_kalshi_totals_url(t['away'], t['home'])
        st.link_button(f"🚀 EXECUTE {tot['pick']}", kalshi_url)
        st.markdown("")
else:
    st.info("No totals trades authorized")

st.divider()

# ========== B2B INFO ==========
if yesterday_teams:
    st.info(f"📅 **B2B Teams Today:** {', '.join(sorted(yesterday_teams))}")

st.divider()

# ========== ADD POSITION (for authorized trades only) ==========
st.subheader("➕ ADD POSITION")

if trade_eligible:
    eligible_games = ["Select a game..."] + [t['game_key'].replace("@", " @ ") for t in trade_eligible]
    selected_game = st.selectbox("🏀 Game (trade-eligible only)", eligible_games, key="game_select")
    threshold_select = st.number_input("🎯 Threshold", min_value=180.0, max_value=280.0, value=225.5, step=3.0)
    
    if selected_game != "Select a game...":
        parts = selected_game.replace(" @ ", "@").split("@")
        kalshi_url = build_kalshi_totals_url(parts[0], parts[1])
        st.link_button(f"🔗 View on Kalshi", kalshi_url, use_container_width=True)
    
    with st.form("add_position_form"):
        p1, p2, p3 = st.columns(3)
        side = p1.selectbox("📊 Side", ["NO (Under)", "YES (Over)"])
        price_paid = p2.number_input("💵 Price (¢)", min_value=1, max_value=99, value=50, step=1)
        contracts = p3.number_input("📄 Contracts", min_value=1, max_value=1000, value=st.session_state.default_contracts)
        
        add_btn = st.form_submit_button("✅ ADD POSITION", use_container_width=True)
        
        if add_btn and selected_game != "Select a game...":
            game_key = selected_game.replace(" @ ", "@")
            side_clean = "NO" if "NO" in side else "YES"
            st.session_state.positions.append({
                'game': game_key,
                'side': side_clean,
                'threshold': threshold_select,
                'price': price_paid,
                'contracts': contracts,
                'cost': round(price_paid * contracts / 100, 2)
            })
            st.rerun()
else:
    st.info("No trade-eligible games — position entry disabled")

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
                pnl = f"+${potential_win:.2f}" if won else f"-${potential_loss:.2f}"
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
                pnl = f"Win: +${potential_win:.2f}"
                pnl_color = "#888"
            else:
                status_label, status_color = "⏳ WAITING", "#888"
                pnl = f"Win: +${potential_win:.2f}"
                pnl_color = "#888"
            
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <span style='color:#fff;font-size:1.2em;font-weight:bold'>{game_key.replace('@', ' @ ')}</span>
                        <span style='color:#888;margin-left:10px'>{game_status}</span>
                    </div>
                    <span style='color:{status_color};font-size:1.3em;font-weight:bold'>{status_label}</span>
                </div>
                <div style='margin-top:10px;display:flex;gap:30px;flex-wrap:wrap'>
                    <span style='color:#aaa'>📊 <b style="color:#fff">{pos['side']} {pos['threshold']}</b></span>
                    <span style='color:#aaa'>💵 <b style="color:#fff">{contracts}x @ {price}¢</b></span>
                    <span style='color:#aaa'>📈 Proj: <b style="color:#fff">{projected if projected else '—'}</b></span>
                    <span style='color:#aaa'>🎯 Cushion: <b style="color:{status_color}">{cushion:+.0f}</b></span>
                    <span style='color:{pnl_color}'>{pnl}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            btn1, btn2 = st.columns([3, 1])
            parts = game_key.split("@")
            kalshi_url = build_kalshi_totals_url(parts[0], parts[1])
            btn1.link_button(f"🔗 Trade on Kalshi", kalshi_url, use_container_width=True)
            if btn2.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
        else:
            st.markdown(f"""
            <div style='background:#1a1a2e;padding:15px;border-radius:10px;border:1px solid #444;margin-bottom:10px'>
                <span style='color:#888'>{game_key.replace('@', ' @ ')} — {pos['side']} {pos['threshold']} — ⏳ Game not started</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Remove", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
    
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked")

st.divider()

# ========== ALL GAMES (collapsed) ==========
with st.expander("📺 ALL GAMES (raw scores)"):
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
st.caption("⚠️ For entertainment only. Not financial advice. System designed to deny trades more often than allow them.")
