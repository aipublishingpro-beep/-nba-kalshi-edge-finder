import streamlit as st
import requests
from datetime import datetime
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

# ========== TEAM MAPPINGS ==========
KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NYK": "New York", "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia",
    "PHX": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"net_rating": -1.5, "off_rating": 114.2, "def_rating": 115.7, "def_rank": 22, "pace": 100.2, "ppg": 118.2, "opp_ppg": 120.1, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pct": 0.355, "ft_rate": 0.25, "reb_rate": 50.2},
    "Boston": {"net_rating": 10.5, "off_rating": 120.5, "def_rating": 110.0, "def_rank": 2, "pace": 98.5, "ppg": 120.8, "opp_ppg": 110.3, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "three_pct": 0.385, "ft_rate": 0.28, "reb_rate": 52.5},
    "Brooklyn": {"net_rating": -5.2, "off_rating": 109.8, "def_rating": 115.0, "def_rank": 25, "pace": 99.8, "ppg": 108.5, "opp_ppg": 113.7, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.345, "ft_rate": 0.23, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -6.8, "off_rating": 108.5, "def_rating": 115.3, "def_rank": 27, "pace": 101.5, "ppg": 106.8, "opp_ppg": 113.6, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 49.2},
    "Chicago": {"net_rating": -3.5, "off_rating": 111.2, "def_rating": 114.7, "def_rank": 20, "pace": 98.2, "ppg": 112.5, "opp_ppg": 116.0, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 50.0},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.2, "def_rating": 108.4, "def_rank": 3, "pace": 97.5, "ppg": 118.5, "opp_ppg": 108.7, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 53.2},
    "Dallas": {"net_rating": 3.2, "off_rating": 115.8, "def_rating": 112.6, "def_rank": 12, "pace": 99.5, "ppg": 117.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.365, "ft_rate": 0.26, "reb_rate": 50.8},
    "Denver": {"net_rating": 5.5, "off_rating": 117.5, "def_rating": 112.0, "def_rank": 8, "pace": 98.8, "ppg": 118.8, "opp_ppg": 113.3, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 52.0},
    "Detroit": {"net_rating": -4.8, "off_rating": 110.5, "def_rating": 115.3, "def_rank": 24, "pace": 100.5, "ppg": 110.2, "opp_ppg": 115.0, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pct": 0.340, "ft_rate": 0.23, "reb_rate": 49.5},
    "Golden State": {"net_rating": 2.8, "off_rating": 115.2, "def_rating": 112.4, "def_rank": 14, "pace": 99.2, "ppg": 117.5, "opp_ppg": 114.7, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.378, "ft_rate": 0.24, "reb_rate": 50.5},
    "Houston": {"net_rating": 1.5, "off_rating": 113.8, "def_rating": 112.3, "def_rank": 15, "pace": 100.8, "ppg": 114.2, "opp_ppg": 112.7, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.28, "reb_rate": 51.8},
    "Indiana": {"net_rating": 0.5, "off_rating": 118.5, "def_rating": 118.0, "def_rank": 28, "pace": 103.2, "ppg": 123.5, "opp_ppg": 123.0, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Central", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 49.8},
    "LA Clippers": {"net_rating": -1.2, "off_rating": 112.5, "def_rating": 113.7, "def_rank": 18, "pace": 98.5, "ppg": 110.8, "opp_ppg": 112.0, "home_win_pct": 0.48, "away_win_pct": 0.35, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 50.2},
    "LA Lakers": {"net_rating": 2.5, "off_rating": 114.8, "def_rating": 112.3, "def_rank": 13, "pace": 99.8, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Pacific", "three_pct": 0.358, "ft_rate": 0.27, "reb_rate": 51.5},
    "Memphis": {"net_rating": 4.2, "off_rating": 116.5, "def_rating": 112.3, "def_rank": 10, "pace": 101.2, "ppg": 119.8, "opp_ppg": 115.6, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.26, "reb_rate": 52.8},
    "Miami": {"net_rating": 0.8, "off_rating": 112.2, "def_rating": 111.4, "def_rank": 11, "pace": 97.8, "ppg": 110.5, "opp_ppg": 109.7, "home_win_pct": 0.58, "away_win_pct": 0.38, "division": "Southeast", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.8},
    "Milwaukee": {"net_rating": 3.5, "off_rating": 116.8, "def_rating": 113.3, "def_rank": 16, "pace": 99.5, "ppg": 118.2, "opp_ppg": 114.7, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Central", "three_pct": 0.365, "ft_rate": 0.28, "reb_rate": 51.2},
    "Minnesota": {"net_rating": 5.8, "off_rating": 114.5, "def_rating": 108.7, "def_rank": 4, "pace": 98.2, "ppg": 112.8, "opp_ppg": 107.0, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.26, "reb_rate": 53.5},
    "New Orleans": {"net_rating": -2.5, "off_rating": 113.2, "def_rating": 115.7, "def_rank": 23, "pace": 100.5, "ppg": 113.8, "opp_ppg": 116.3, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.27, "reb_rate": 50.5},
    "New York": {"net_rating": 6.2, "off_rating": 117.8, "def_rating": 111.6, "def_rank": 7, "pace": 98.8, "ppg": 118.5, "opp_ppg": 112.3, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Atlantic", "three_pct": 0.368, "ft_rate": 0.26, "reb_rate": 51.8},
    "Oklahoma City": {"net_rating": 11.2, "off_rating": 119.5, "def_rating": 108.3, "def_rank": 1, "pace": 99.8, "ppg": 120.2, "opp_ppg": 109.0, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pct": 0.375, "ft_rate": 0.27, "reb_rate": 52.2},
    "Orlando": {"net_rating": 4.5, "off_rating": 112.8, "def_rating": 108.3, "def_rank": 5, "pace": 97.5, "ppg": 110.5, "opp_ppg": 106.0, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southeast", "three_pct": 0.342, "ft_rate": 0.25, "reb_rate": 52.5},
    "Philadelphia": {"net_rating": -0.5, "off_rating": 113.5, "def_rating": 114.0, "def_rank": 19, "pace": 98.2, "ppg": 112.8, "opp_ppg": 113.3, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic", "three_pct": 0.358, "ft_rate": 0.29, "reb_rate": 50.8},
    "Phoenix": {"net_rating": 1.8, "off_rating": 115.2, "def_rating": 113.4, "def_rank": 17, "pace": 98.5, "ppg": 114.8, "opp_ppg": 113.0, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.2},
    "Portland": {"net_rating": -7.5, "off_rating": 108.2, "def_rating": 115.7, "def_rank": 29, "pace": 100.2, "ppg": 106.5, "opp_ppg": 114.0, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.338, "ft_rate": 0.23, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.8, "off_rating": 114.5, "def_rating": 116.3, "def_rank": 26, "pace": 100.8, "ppg": 116.2, "opp_ppg": 118.0, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -5.5, "off_rating": 110.8, "def_rating": 116.3, "def_rank": 21, "pace": 99.5, "ppg": 110.2, "opp_ppg": 115.7, "home_win_pct": 0.42, "away_win_pct": 0.25, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.25, "reb_rate": 50.5},
    "Toronto": {"net_rating": -4.2, "off_rating": 111.5, "def_rating": 115.7, "def_rank": 23, "pace": 99.2, "ppg": 111.8, "opp_ppg": 116.0, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.2, "off_rating": 107.5, "def_rating": 115.7, "def_rank": 30, "pace": 100.5, "ppg": 106.2, "opp_ppg": 114.4, "home_win_pct": 0.30, "away_win_pct": 0.15, "division": "Northwest", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 48.2},
    "Washington": {"net_rating": -9.5, "off_rating": 108.8, "def_rating": 118.3, "def_rank": 30, "pace": 101.2, "ppg": 109.5, "opp_ppg": 119.0, "home_win_pct": 0.25, "away_win_pct": 0.12, "division": "Southeast", "three_pct": 0.332, "ft_rate": 0.23, "reb_rate": 47.8}
}

# City coordinates for travel distance
CITY_COORDS = {
    "Atlanta": (33.749, -84.388), "Boston": (42.361, -71.057), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -104.999), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.980, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

def calculate_travel_distance(away_team, home_team):
    if away_team not in CITY_COORDS or home_team not in CITY_COORDS:
        return 0
    lat1, lon1 = CITY_COORDS[away_team]
    lat2, lon2 = CITY_COORDS[home_team]
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 3956 * 2 * math.asin(math.sqrt(a))

def calculate_edge(home, away, yes_price, home_rest, away_rest, home_inj, away_inj, travel_dist, ref_bias, weights):
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    factors = {
        'rest': (home_rest - away_rest) * 2.5 * weights['rest'],
        'live_rest': ((away_rest == 0) * 8 - (home_rest == 0) * 8) * weights['live_rest'],
        'defense': (away_stats.get('def_rank', 15) - home_stats.get('def_rank', 15)) * 0.8 * weights['defense'],
        'injuries': (away_inj - home_inj) * 3 * weights['injuries'],
        'pace': 0 if abs(home_stats.get('pace', 100) - away_stats.get('pace', 100)) < 2 else ((home_stats.get('pace', 100) > away_stats.get('pace', 100)) * 2 - 1) * 1.5 * weights['pace'],
        'net_rating': (home_stats.get('net_rating', 0) - away_stats.get('net_rating', 0)) * 0.5 * weights['net_rating'],
        'travel': min(travel_dist / 500, 3) * weights['travel'],
        'home_away': ((home_stats.get('home_win_pct', 0.5) - 0.5) * 20 - (away_stats.get('away_win_pct', 0.5) - 0.5) * 20) * weights['home_away'],
        'h2h': (5 if home_stats.get('division') == away_stats.get('division') else 0) * weights['h2h'],
        'refs': (ref_bias - 1) * 5 * weights['refs'],
        'ft_rate': (home_stats.get('ft_rate', 0.25) - away_stats.get('ft_rate', 0.25)) * 40 * weights['ft_rate'],
        'rebounding': (home_stats.get('reb_rate', 50) - away_stats.get('reb_rate', 50)) * 0.5 * weights['rebounding'],
        'three_pt': (home_stats.get('three_pct', 0.35) - away_stats.get('three_pct', 0.35)) * 100 * weights['three_pt']
    }
    
    total_adjustment = sum(factors.values())
    home_win_prob = max(25, min(75, 50 + total_adjustment))
    edge = home_win_prob - yes_price
    
    if edge > 7:
        rec, conf = "BUY YES", "HIGH"
    elif edge > 4:
        rec, conf = "BUY YES", "MEDIUM"
    elif edge < -7:
        rec, conf = "BUY NO", "HIGH"
    elif edge < -4:
        rec, conf = "BUY NO", "MEDIUM"
    else:
        rec, conf = "NO EDGE", "LOW"
    
    return {'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1), 'recommendation': rec, 'confidence': conf, 'factors': factors}

def calculate_kelly(win_prob, price, bankroll, fraction=0.25):
    p = win_prob / 100
    odds = (100 - price) / price if price > 0 else 0
    kelly = (p * odds - (1 - p)) / odds if odds > 0 else 0
    adj_kelly = max(0, kelly * fraction)
    return {'kelly_pct': round(kelly * 100, 2), 'adj_kelly_pct': round(adj_kelly * 100, 2), 'bet_amount': round(bankroll * adj_kelly, 2)}

def parse_teams_from_ticker(ticker):
    """Extract home and away teams from Kalshi ticker"""
    try:
        if '-' not in ticker:
            return None, None
        game_code = ticker.split('-')[1]
        away_abbrev = game_code[-6:-3].upper()
        home_abbrev = game_code[-3:].upper()
        away_team = KALSHI_ABBREV_MAP.get(away_abbrev)
        home_team = KALSHI_ABBREV_MAP.get(home_abbrev)
        return home_team, away_team
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_kalshi_markets():
    """Fetch all NBA markets from Kalshi"""
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    
    endpoints = [
        ('moneyline', 'KXNBAGAME'),
        ('totals', 'KXNBATOTAL'),
        ('spreads', 'KXNBASPREAD')
    ]
    
    for market_type, series in endpoints:
        try:
            resp = requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open", timeout=10)
            data = resp.json().get('markets', [])
            
            for m in data:
                ticker = m.get('ticker', '')
                home_team, away_team = parse_teams_from_ticker(ticker)
                
                if not home_team or not away_team:
                    continue
                
                close_time = m.get('close_time', '')
                game_date = ''
                if close_time:
                    try:
                        dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                        game_date = dt.strftime('%b %d')
                    except:
                        pass
                
                market_info = {
                    'ticker': ticker,
                    'title': m.get('title', f"{away_team} @ {home_team}"),
                    'home_team': home_team,
                    'away_team': away_team,
                    'yes_price': m.get('yes_ask', 50),
                    'game_date': game_date,
                    'close_time': close_time
                }
                
                if market_type == 'totals':
                    floor_value = m.get('floor_strike')
                    if floor_value is not None:
                        market_info['line'] = floor_value
                    else:
                        title = m.get('title', '')
                        import re
                        numbers = re.findall(r'\d+\.?\d*', title)
                        market_info['line'] = float(numbers[-1]) if numbers else 220
                
                markets[market_type].append(market_info)
        except Exception as e:
            st.error(f"Error fetching {market_type}: {e}")
    
    for key in markets:
        markets[key].sort(key=lambda x: x.get('close_time', ''))
    
    return markets

@st.cache_data(ttl=300)
def fetch_rest_days():
    """Fetch rest days from recent settled games"""
    try:
        team_last_game = {}
        today = datetime.now()
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        
        for m in resp.json().get('markets', []):
            ticker = m.get('ticker', '')
            close_time = m.get('close_time', '')
            if not close_time or '-' not in ticker:
                continue
            
            try:
                game_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)
                days_ago = (today - game_dt).days
                
                if 0 <= days_ago <= 5:
                    game_code = ticker.split('-')[1]
                    for abbrev in [game_code[-6:-3].upper(), game_code[-3:].upper()]:
                        team_name = KALSHI_ABBREV_MAP.get(abbrev)
                        if team_name and team_name not in team_last_game:
                            team_last_game[team_name] = days_ago
            except:
                continue
        
        return team_last_game
    except:
        return {}

# ========== UI ==========
st.title("🏀 NBA Kalshi Edge Finder")
st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | 🟢 = BUY YES | 🔴 = BUY NO")

# ========== SIDEBAR ==========
st.sidebar.header("⚙️ The 12 Sauces")
st.sidebar.caption("0 = off, 1 = normal, 2 = double weight")

with st.sidebar.expander("🏀 Core Factors", expanded=True):
    w_rest = st.slider("🛏️ Rest Days", 0.0, 2.0, 1.0, 0.1, help="Days of rest advantage. More rest = fresher legs = better performance.")
    w_live_rest = st.slider("⏰ B2B Fatigue", 0.0, 2.0, 1.0, 0.1, help="Back-to-back detection. 0 days rest = played yesterday = huge fatigue penalty.")
    w_def = st.slider("🛡️ Defense", 0.0, 2.0, 1.0, 0.1, help="Defensive efficiency ranking (1-30). Elite defense (#1-5) vs poor defense (#25-30).")
    w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1, help="Key player injuries. Stars out = major impact on team performance.")
    w_pace = st.slider("🏃 Pace", 0.0, 2.0, 1.0, 0.1, help="Pace mismatch. Fast vs slow teams create exploitable situations.")
    w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1, help="Overall team strength. Points scored minus points allowed per 100 possessions.")

with st.sidebar.expander("🎯 Advanced Factors", expanded=True):
    w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1, help="Travel distance fatigue. Cross-country trips hurt away team performance.")
    w_home = st.slider("🏠 Home/Away", 0.0, 2.0, 1.0, 0.1, help="Home court advantage. Some teams dominate at home, struggle on road.")
    w_h2h = st.slider("⚔️ Division Rival", 0.0, 2.0, 1.0, 0.1, help="Divisional matchups. Teams know each other well, games often closer.")
    w_refs = st.slider("👨‍⚖️ Refs", 0.0, 2.0, 1.0, 0.1, help="Referee tendencies. Some crews favor home teams more than others.")
    w_ft = st.slider("🎯 Free Throws", 0.0, 2.0, 1.0, 0.1, help="Free throw rate. Teams that attack the basket get to the line more.")
    w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1, help="Rebounding edge. Second chance points can swing games.")
    w_3pt = st.slider("🎯 3PT Shooting", 0.0, 2.0, 1.0, 0.1, help="Three-point shooting. Hot shooting teams can overcome deficits quickly.")

weights = {
    'rest': w_rest, 'live_rest': w_live_rest, 'defense': w_def, 'injuries': w_inj,
    'pace': w_pace, 'net_rating': w_net, 'travel': w_travel, 'home_away': w_home,
    'h2h': w_h2h, 'refs': w_refs, 'ft_rate': w_ft, 'rebounding': w_reb, 'three_pt': w_3pt
}

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Bet Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05, help="Portion of Kelly criterion to use. 0.25 = quarter Kelly (safer).")
min_edge = st.sidebar.slider("Min Edge %", 1.0, 15.0, 5.0, 0.5, help="Minimum edge required to show a bet recommendation.")
default_ref_bias = st.sidebar.slider("Default Ref Bias", 0.0, 2.0, 1.0, 0.1, help="0 = away-friendly, 1 = neutral, 2 = home-friendly")
default_home_rest = st.sidebar.number_input("Default Home Rest", 1, 5, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 1, 5, 2)

# ========== FETCH DATA ==========
markets = fetch_kalshi_markets()
rest_days = fetch_rest_days()

# ========== BUILD TOP EDGES - THE KEY FIX ==========
# We build edge dicts with ALL data including URL at creation time
# This ensures each edge has its own unique URL stored in the dict

top_edges = []

# Process MONEYLINE markets
for game in markets['moneyline']:
    home = game['home_team']
    away = game['away_team']
    ticker = game['ticker']  # Capture ticker for THIS game
    yes_price = game['yes_price']
    
    home_rest = rest_days.get(home, default_home_rest)
    away_rest = rest_days.get(away, default_away_rest)
    travel = calculate_travel_distance(away, home)
    
    analysis = calculate_edge(home, away, yes_price, home_rest, away_rest, 0, 0, travel, default_ref_bias, weights)
    
    if analysis['recommendation'] != 'NO EDGE' and abs(analysis['edge']) >= min_edge:
        if analysis['recommendation'] == 'BUY YES':
            bet_team = home
            win_prob = analysis['home_win_prob']
            price = yes_price
        else:
            bet_team = away
            win_prob = 100 - analysis['home_win_prob']
            price = 100 - yes_price
        
        kelly = calculate_kelly(win_prob, price, bankroll, kelly_fraction)
        
        # CREATE URL HERE - stored in dict, not a variable that gets overwritten
        game_url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker.lower()}"
        
        top_edges.append({
            'type': 'ML',
            'game': f"{away} @ {home}",
            'date': game['game_date'],
            'ticker': ticker,  # Store ticker for debugging
            'edge': abs(analysis['edge']),
            'rec': f"{bet_team} WINS",
            'bet_team': bet_team,
            'bet_amount': kelly['bet_amount'],
            'url': game_url,  # URL stored at creation time
            'color': '🟢' if analysis['recommendation'] == 'BUY YES' else '🔴'
        })

# Process TOTALS markets
for game in markets['totals']:
    home = game['home_team']
    away = game['away_team']
    ticker = game['ticker']  # Capture ticker for THIS game
    yes_price = game['yes_price']
    line = game.get('line', 220)
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    combined_pace = (home_stats.get('pace', 100) + away_stats.get('pace', 100)) / 2
    projected_total = (home_stats.get('ppg', 110) + away_stats.get('ppg', 110)) * (combined_pace / 100)
    
    diff = projected_total - line
    
    if abs(diff) >= min_edge:
        rec = "OVER" if diff > 0 else "UNDER"
        kelly = calculate_kelly(50 + abs(diff), yes_price if diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
        
        # CREATE URL HERE - stored in dict
        game_url = f"https://kalshi.com/markets/kxnbatotal/{ticker.lower()}"
        
        top_edges.append({
            'type': 'TOT',
            'game': f"{away} @ {home}",
            'date': game['game_date'],
            'ticker': ticker,
            'edge': abs(diff),
            'rec': f"{rec} {line}",
            'bet_team': rec,
            'bet_amount': kelly['bet_amount'],
            'url': game_url,
            'color': '🟢' if rec == "OVER" else '🔴'
        })

# Process SPREAD markets
for game in markets['spreads']:
    home = game['home_team']
    away = game['away_team']
    ticker = game['ticker']  # Capture ticker for THIS game
    yes_price = game['yes_price']
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    spread_diff = 50 - yes_price
    
    if abs(spread_diff) >= min_edge:
        if spread_diff > 0:
            rec = "COVERS"
            spread_team = home
            color = '🟢'
        else:
            rec = "FAILS"
            spread_team = away
            color = '🔴'
        
        kelly = calculate_kelly(50 + abs(spread_diff), yes_price if spread_diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
        
        # CREATE URL HERE - stored in dict
        game_url = f"https://kalshi.com/markets/kxnbaspread/{ticker.lower()}"
        
        top_edges.append({
            'type': 'SPR',
            'game': f"{away} @ {home}",
            'date': game['game_date'],
            'ticker': ticker,
            'edge': abs(spread_diff),
            'rec': f"{spread_team} {rec}",
            'bet_team': spread_team,
            'bet_amount': kelly['bet_amount'],
            'url': game_url,
            'color': color
        })

# Sort by edge size
top_edges.sort(key=lambda x: x['edge'], reverse=True)

# ========== DISPLAY TOP 3 EDGES ==========
st.subheader("🔥 TOP 3 EDGES")

if top_edges:
    for i, edge in enumerate(top_edges[:3], 1):
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            st.markdown(f"**#{i} {edge['color']} [{edge['type']}] {edge['game']}**")
            st.caption(f"{edge['date']} | Edge: {edge['edge']:.1f}%")
        
        with col2:
            st.markdown(f"**→ {edge['rec']}**")
        
        with col3:
            # THE FIX: Each button uses edge['url'] which was set when the edge was created
            # Not a loop variable that gets overwritten
            st.link_button(
                f"BET {edge['bet_team'].upper()} ${edge['bet_amount']:.0f}",
                edge['url'],  # This is the stored URL from when the edge was created
                use_container_width=True,
                key=f"top_edge_btn_{i}_{edge['ticker']}"  # Unique key per button
            )
else:
    st.info("No edges found meeting minimum threshold. Try lowering the min edge % in settings.")

st.markdown("---")

# ========== TABS FOR ALL MARKETS ==========
tab1, tab2, tab3 = st.tabs(["📈 Moneyline", "📊 Totals", "📉 Spreads"])

with tab1:
    st.subheader("Moneyline Markets")
    
    for idx, game in enumerate(markets['moneyline'][:15]):
        home = game['home_team']
        away = game['away_team']
        ticker = game['ticker']
        yes_price = game['yes_price']
        
        home_rest = rest_days.get(home, default_home_rest)
        away_rest = rest_days.get(away, default_away_rest)
        travel = calculate_travel_distance(away, home)
        
        analysis = calculate_edge(home, away, yes_price, home_rest, away_rest, 0, 0, travel, default_ref_bias, weights)
        
        if analysis['recommendation'] == 'BUY YES':
            indicator = "🟢"
        elif analysis['recommendation'] == 'BUY NO':
            indicator = "🔴"
        else:
            indicator = "⚪"
        
        with st.expander(f"{indicator} {away} @ {home} | {game['game_date']} | Kalshi: {yes_price}¢ | Edge: {analysis['edge']:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("Model Prob", f"{analysis['home_win_prob']}%")
                st.metric("Kalshi Price", f"{yes_price}¢")
            
            with c2:
                st.metric("Edge", f"{analysis['edge']:+.1f}%")
                st.metric("Confidence", analysis['confidence'])
            
            with c3:
                if analysis['recommendation'] != 'NO EDGE' and abs(analysis['edge']) >= min_edge:
                    bet_team = home if analysis['recommendation'] == 'BUY YES' else away
                    win_prob = analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob']
                    price = yes_price if analysis['recommendation'] == 'BUY YES' else 100 - yes_price
                    kelly = calculate_kelly(win_prob, price, bankroll, kelly_fraction)
                    
                    st.markdown(f"**{analysis['recommendation']}**")
                    st.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
                    
                    # Build URL for THIS specific game
                    game_url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker.lower()}"
                    st.link_button(
                        f"BET {bet_team.upper()} ${kelly['bet_amount']:.0f}",
                        game_url,
                        use_container_width=True,
                        key=f"ml_btn_{idx}_{ticker}"
                    )
                else:
                    st.info("No edge")

with tab2:
    st.subheader("Totals Markets")
    
    for idx, game in enumerate(markets['totals'][:15]):
        home = game['home_team']
        away = game['away_team']
        ticker = game['ticker']
        yes_price = game['yes_price']
        line = game.get('line', 220)
        
        home_stats = TEAM_STATS.get(home, {})
        away_stats = TEAM_STATS.get(away, {})
        combined_pace = (home_stats.get('pace', 100) + away_stats.get('pace', 100)) / 2
        projected = (home_stats.get('ppg', 110) + away_stats.get('ppg', 110)) * (combined_pace / 100)
        diff = projected - line
        
        if diff > min_edge:
            indicator, rec = "🟢", "OVER"
        elif diff < -min_edge:
            indicator, rec = "🔴", "UNDER"
        else:
            indicator, rec = "⚪", "PASS"
        
        with st.expander(f"{indicator} {away} @ {home} | Line: {line} | Price: {yes_price}¢ | Proj: {projected:.0f}"):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("Line", f"{line}")
                st.metric("Projected", f"{projected:.1f}")
            
            with c2:
                st.metric("Difference", f"{diff:+.1f}")
                st.metric("Yes Price", f"{yes_price}¢")
            
            with c3:
                if abs(diff) >= min_edge:
                    kelly = calculate_kelly(50 + abs(diff), yes_price if diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
                    st.markdown(f"**BUY {rec}**")
                    st.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
                    
                    game_url = f"https://kalshi.com/markets/kxnbatotal/{ticker.lower()}"
                    st.link_button(
                        f"BET {rec} ${kelly['bet_amount']:.0f}",
                        game_url,
                        use_container_width=True,
                        key=f"tot_btn_{idx}_{ticker}"
                    )
                else:
                    st.info("No edge")

with tab3:
    st.subheader("Spread Markets")
    
    for idx, game in enumerate(markets['spreads'][:15]):
        home = game['home_team']
        away = game['away_team']
        ticker = game['ticker']
        yes_price = game['yes_price']
        
        spread_edge = 50 - yes_price
        
        if spread_edge > min_edge:
            indicator, rec, bet_team = "🟢", "COVERS", home
        elif spread_edge < -min_edge:
            indicator, rec, bet_team = "🔴", "FAILS", away
        else:
            indicator, rec, bet_team = "⚪", "PASS", ""
        
        with st.expander(f"{indicator} {away} @ {home} | Price: {yes_price}¢ | Edge: {spread_edge:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("Yes Price", f"{yes_price}¢")
            
            with c2:
                st.metric("Edge", f"{spread_edge:+.1f}%")
            
            with c3:
                if abs(spread_edge) >= min_edge:
                    kelly = calculate_kelly(50 + abs(spread_edge), yes_price if spread_edge > 0 else 100 - yes_price, bankroll, kelly_fraction)
                    st.markdown(f"**{bet_team} {rec}**")
                    st.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
                    
                    game_url = f"https://kalshi.com/markets/kxnbaspread/{ticker.lower()}"
                    st.link_button(
                        f"BET {bet_team.upper()} ${kelly['bet_amount']:.0f}",
                        game_url,
                        use_container_width=True,
                        key=f"spr_btn_{idx}_{ticker}"
                    )
                else:
                    st.info("No edge")

# ========== DEBUG SECTION ==========
with st.expander("🔧 Debug: API Tickers"):
    st.caption("Verify each game has a unique ticker")
    
    if markets['moneyline']:
        st.write("**Moneyline Tickers:**")
        for g in markets['moneyline'][:5]:
            st.code(f"{g['away_team']} @ {g['home_team']}: {g['ticker']}")
    
    if top_edges:
        st.write("**Top Edges Tickers:**")
        for e in top_edges[:3]:
            st.code(f"{e['game']}: {e['ticker']} → {e['url']}")
