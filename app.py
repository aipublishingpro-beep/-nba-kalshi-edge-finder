import streamlit as st
import requests
from datetime import datetime
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NYK": "New York", "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia",
    "PHX": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"net_rating": -1.5, "def_rank": 22, "pace": 100.2, "ppg": 118.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pct": 0.355, "ft_rate": 0.25, "reb_rate": 50.2},
    "Boston": {"net_rating": 10.5, "def_rank": 2, "pace": 98.5, "ppg": 120.8, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "three_pct": 0.385, "ft_rate": 0.28, "reb_rate": 52.5},
    "Brooklyn": {"net_rating": -5.2, "def_rank": 25, "pace": 99.8, "ppg": 108.5, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.345, "ft_rate": 0.23, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -6.8, "def_rank": 27, "pace": 101.5, "ppg": 106.8, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 49.2},
    "Chicago": {"net_rating": -3.5, "def_rank": 20, "pace": 98.2, "ppg": 112.5, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 50.0},
    "Cleveland": {"net_rating": 9.8, "def_rank": 3, "pace": 97.5, "ppg": 118.5, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 53.2},
    "Dallas": {"net_rating": 3.2, "def_rank": 12, "pace": 99.5, "ppg": 117.2, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.365, "ft_rate": 0.26, "reb_rate": 50.8},
    "Denver": {"net_rating": 5.5, "def_rank": 8, "pace": 98.8, "ppg": 118.8, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 52.0},
    "Detroit": {"net_rating": -4.8, "def_rank": 24, "pace": 100.5, "ppg": 110.2, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pct": 0.340, "ft_rate": 0.23, "reb_rate": 49.5},
    "Golden State": {"net_rating": 2.8, "def_rank": 14, "pace": 99.2, "ppg": 117.5, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.378, "ft_rate": 0.24, "reb_rate": 50.5},
    "Houston": {"net_rating": 1.5, "def_rank": 15, "pace": 100.8, "ppg": 114.2, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.28, "reb_rate": 51.8},
    "Indiana": {"net_rating": 0.5, "def_rank": 28, "pace": 103.2, "ppg": 123.5, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Central", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 49.8},
    "LA Clippers": {"net_rating": -1.2, "def_rank": 18, "pace": 98.5, "ppg": 110.8, "home_win_pct": 0.48, "away_win_pct": 0.35, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 50.2},
    "LA Lakers": {"net_rating": 2.5, "def_rank": 13, "pace": 99.8, "ppg": 115.2, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Pacific", "three_pct": 0.358, "ft_rate": 0.27, "reb_rate": 51.5},
    "Memphis": {"net_rating": 4.2, "def_rank": 10, "pace": 101.2, "ppg": 119.8, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.26, "reb_rate": 52.8},
    "Miami": {"net_rating": 0.8, "def_rank": 11, "pace": 97.8, "ppg": 110.5, "home_win_pct": 0.58, "away_win_pct": 0.38, "division": "Southeast", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.8},
    "Milwaukee": {"net_rating": 3.5, "def_rank": 16, "pace": 99.5, "ppg": 118.2, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Central", "three_pct": 0.365, "ft_rate": 0.28, "reb_rate": 51.2},
    "Minnesota": {"net_rating": 5.8, "def_rank": 4, "pace": 98.2, "ppg": 112.8, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.26, "reb_rate": 53.5},
    "New Orleans": {"net_rating": -2.5, "def_rank": 23, "pace": 100.5, "ppg": 113.8, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.27, "reb_rate": 50.5},
    "New York": {"net_rating": 6.2, "def_rank": 7, "pace": 98.8, "ppg": 118.5, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Atlantic", "three_pct": 0.368, "ft_rate": 0.26, "reb_rate": 51.8},
    "Oklahoma City": {"net_rating": 11.2, "def_rank": 1, "pace": 99.8, "ppg": 120.2, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pct": 0.375, "ft_rate": 0.27, "reb_rate": 52.2},
    "Orlando": {"net_rating": 4.5, "def_rank": 5, "pace": 97.5, "ppg": 110.5, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southeast", "three_pct": 0.342, "ft_rate": 0.25, "reb_rate": 52.5},
    "Philadelphia": {"net_rating": -0.5, "def_rank": 19, "pace": 98.2, "ppg": 112.8, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic", "three_pct": 0.358, "ft_rate": 0.29, "reb_rate": 50.8},
    "Phoenix": {"net_rating": 1.8, "def_rank": 17, "pace": 98.5, "ppg": 114.8, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.2},
    "Portland": {"net_rating": -7.5, "def_rank": 29, "pace": 100.2, "ppg": 106.5, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.338, "ft_rate": 0.23, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.8, "def_rank": 26, "pace": 100.8, "ppg": 116.2, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -5.5, "def_rank": 21, "pace": 99.5, "ppg": 110.2, "home_win_pct": 0.42, "away_win_pct": 0.25, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.25, "reb_rate": 50.5},
    "Toronto": {"net_rating": -4.2, "def_rank": 23, "pace": 99.2, "ppg": 111.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.2, "def_rank": 30, "pace": 100.5, "ppg": 106.2, "home_win_pct": 0.30, "away_win_pct": 0.15, "division": "Northwest", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 48.2},
    "Washington": {"net_rating": -9.5, "def_rank": 30, "pace": 101.2, "ppg": 109.5, "home_win_pct": 0.25, "away_win_pct": 0.12, "division": "Southeast", "three_pct": 0.332, "ft_rate": 0.23, "reb_rate": 47.8}
}

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
        'rest': (home_rest - away_rest) * 2.5 * weights.get('rest', 1),
        'live_rest': ((away_rest == 0) * 8 - (home_rest == 0) * 8) * weights.get('live_rest', 1),
        'defense': (away_stats.get('def_rank', 15) - home_stats.get('def_rank', 15)) * 0.8 * weights.get('defense', 1),
        'injuries': (away_inj - home_inj) * 3 * weights.get('injuries', 1),
        'pace': 0 if abs(home_stats.get('pace', 100) - away_stats.get('pace', 100)) < 2 else ((home_stats.get('pace', 100) > away_stats.get('pace', 100)) * 2 - 1) * 1.5 * weights.get('pace', 1),
        'net_rating': (home_stats.get('net_rating', 0) - away_stats.get('net_rating', 0)) * 0.5 * weights.get('net_rating', 1),
        'travel': min(travel_dist / 500, 3) * weights.get('travel', 1),
        'home_away': ((home_stats.get('home_win_pct', 0.5) - 0.5) * 20 - (away_stats.get('away_win_pct', 0.5) - 0.5) * 20) * weights.get('home_away', 1),
        'h2h': (5 if home_stats.get('division') == away_stats.get('division') else 0) * weights.get('h2h', 1),
        'refs': (ref_bias - 1) * 5 * weights.get('refs', 1),
        'ft_rate': (home_stats.get('ft_rate', 0.25) - away_stats.get('ft_rate', 0.25)) * 40 * weights.get('ft_rate', 1),
        'rebounding': (home_stats.get('reb_rate', 50) - away_stats.get('reb_rate', 50)) * 0.5 * weights.get('rebounding', 1),
        'three_pt': (home_stats.get('three_pct', 0.35) - away_stats.get('three_pct', 0.35)) * 100 * weights.get('three_pt', 1)
    }
    
    total_adjustment = sum(factors.values())
    home_win_prob = max(25, min(75, 50 + total_adjustment))
    edge = home_win_prob - yes_price
    
    if edge > 7: rec, conf = "BUY YES", "HIGH"
    elif edge > 4: rec, conf = "BUY YES", "MEDIUM"
    elif edge < -7: rec, conf = "BUY NO", "HIGH"
    elif edge < -4: rec, conf = "BUY NO", "MEDIUM"
    else: rec, conf = "NO EDGE", "LOW"
    
    return {'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1), 'recommendation': rec, 'confidence': conf}

def calculate_kelly(win_prob, price, bankroll, fraction=0.25):
    try:
        p = win_prob / 100
        odds = (100 - price) / price if price > 0 else 0
        kelly = (p * odds - (1 - p)) / odds if odds > 0 else 0
        adj_kelly = max(0, kelly * fraction)
        return round(bankroll * adj_kelly, 2)
    except:
        return 0.0

def parse_teams_from_ticker(ticker):
    try:
        if '-' not in ticker:
            return None, None
        game_code = ticker.split('-')[1]
        away_abbrev = game_code[-6:-3].upper()
        home_abbrev = game_code[-3:].upper()
        return KALSHI_ABBREV_MAP.get(home_abbrev), KALSHI_ABBREV_MAP.get(away_abbrev)
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_kalshi_markets():
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    endpoints = [('moneyline', 'KXNBAGAME'), ('totals', 'KXNBATOTAL'), ('spreads', 'KXNBASPREAD')]
    
    for market_type, series in endpoints:
        try:
            resp = requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open", timeout=10)
            for m in resp.json().get('markets', []):
                ticker = m.get('ticker', '')
                home_team, away_team = parse_teams_from_ticker(ticker)
                if not home_team or not away_team:
                    continue
                
                close_time = m.get('close_time', '')
                game_date = ''
                if close_time:
                    try:
                        game_date = datetime.fromisoformat(close_time.replace('Z', '+00:00')).strftime('%b %d')
                    except:
                        pass
                
                market_info = {
                    'ticker': ticker, 'home_team': home_team, 'away_team': away_team,
                    'yes_price': m.get('yes_ask', 50), 'game_date': game_date, 'close_time': close_time
                }
                
                if market_type == 'totals':
                    floor_value = m.get('floor_strike')
                    if floor_value is not None:
                        market_info['line'] = floor_value
                    else:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', m.get('title', ''))
                        market_info['line'] = float(numbers[-1]) if numbers else 220
                
                markets[market_type].append(market_info)
        except Exception as e:
            st.error(f"Error fetching {market_type}: {e}")
    
    for key in markets:
        markets[key].sort(key=lambda x: x.get('close_time', ''))
    return markets

@st.cache_data(ttl=300)
def fetch_rest_days():
    try:
        team_last_game, today = {}, datetime.now()
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        for m in resp.json().get('markets', []):
            ticker, close_time = m.get('ticker', ''), m.get('close_time', '')
            if not close_time or '-' not in ticker:
                continue
            try:
                days_ago = (today - datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)).days
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
    w_rest = st.slider("🛏️ Rest Days", 0.0, 2.0, 1.0, 0.1, help="Days of rest advantage.")
    w_live_rest = st.slider("⏰ B2B Fatigue", 0.0, 2.0, 1.0, 0.1, help="Back-to-back detection.")
    w_def = st.slider("🛡️ Defense", 0.0, 2.0, 1.0, 0.1, help="Defensive efficiency ranking.")
    w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1, help="Key player injuries.")
    w_pace = st.slider("🏃 Pace", 0.0, 2.0, 1.0, 0.1, help="Pace mismatch.")
    w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1, help="Overall team strength.")

with st.sidebar.expander("🎯 Advanced Factors", expanded=True):
    w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1, help="Travel distance fatigue.")
    w_home = st.slider("🏠 Home/Away", 0.0, 2.0, 1.0, 0.1, help="Home court advantage.")
    w_h2h = st.slider("⚔️ Division Rival", 0.0, 2.0, 1.0, 0.1, help="Divisional matchups.")
    w_refs = st.slider("👨‍⚖️ Refs", 0.0, 2.0, 1.0, 0.1, help="Referee tendencies.")
    w_ft = st.slider("🎯 Free Throws", 0.0, 2.0, 1.0, 0.1, help="Free throw rate.")
    w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1, help="Rebounding edge.")
    w_3pt = st.slider("🎯 3PT Shooting", 0.0, 2.0, 1.0, 0.1, help="Three-point shooting.")

weights = {'rest': w_rest, 'live_rest': w_live_rest, 'defense': w_def, 'injuries': w_inj, 'pace': w_pace, 'net_rating': w_net, 'travel': w_travel, 'home_away': w_home, 'h2h': w_h2h, 'refs': w_refs, 'ft_rate': w_ft, 'rebounding': w_reb, 'three_pt': w_3pt}

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Bet Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)
min_edge = st.sidebar.slider("Min Edge %", 1.0, 15.0, 5.0, 0.5)
default_ref_bias = st.sidebar.slider("Default Ref Bias", 0.0, 2.0, 1.0, 0.1)
default_home_rest = st.sidebar.number_input("Default Home Rest", 1, 5, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 1, 5, 2)

# ========== FETCH DATA ==========
markets = fetch_kalshi_markets()
rest_days = fetch_rest_days()

# ========== BUILD TOP EDGES ==========
top_edges = []

for game in markets['moneyline']:
    home, away, ticker = game['home_team'], game['away_team'], game['ticker']
    if not home or not away or not ticker:
        continue
    
    yes_price = game['yes_price']
    home_rest = rest_days.get(home, default_home_rest)
    away_rest = rest_days.get(away, default_away_rest)
    travel = calculate_travel_distance(away, home)
    analysis = calculate_edge(home, away, yes_price, home_rest, away_rest, 0, 0, travel, default_ref_bias, weights)
    
    if analysis['recommendation'] != 'NO EDGE' and abs(analysis['edge']) >= min_edge:
        if analysis['recommendation'] == 'BUY YES':
            bet_team, win_prob, price = home, analysis['home_win_prob'], yes_price
        else:
            bet_team, win_prob, price = away, 100 - analysis['home_win_prob'], 100 - yes_price
        
        bet_amt = calculate_kelly(win_prob, price, bankroll, kelly_fraction)
        game_url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker.lower()}"
        
        top_edges.append({
            'type': 'ML', 'game': f"{away} @ {home}", 'date': game['game_date'], 'ticker': ticker,
            'edge': abs(analysis['edge']), 'rec': f"{bet_team} WINS", 'bet_team': bet_team,
            'bet_amount': bet_amt, 'url': game_url,
            'color': '🟢' if analysis['recommendation'] == 'BUY YES' else '🔴'
        })

for game in markets['totals']:
    home, away, ticker = game['home_team'], game['away_team'], game['ticker']
    if not home or not away or not ticker:
        continue
    
    yes_price, line = game['yes_price'], game.get('line', 220)
    home_stats, away_stats = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
    combined_pace = (home_stats.get('pace', 100) + away_stats.get('pace', 100)) / 2
    projected = (home_stats.get('ppg', 110) + away_stats.get('ppg', 110)) * (combined_pace / 100)
    diff = projected - line
    
    if abs(diff) >= min_edge:
        rec = "OVER" if diff > 0 else "UNDER"
        bet_amt = calculate_kelly(50 + abs(diff), yes_price if diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
        game_url = f"https://kalshi.com/markets/kxnbatotal/{ticker.lower()}"
        
        top_edges.append({
            'type': 'TOT', 'game': f"{away} @ {home}", 'date': game['game_date'], 'ticker': ticker,
            'edge': abs(diff), 'rec': f"{rec} {line}", 'bet_team': rec, 'bet_amount': bet_amt,
            'url': game_url, 'color': '🟢' if rec == "OVER" else '🔴'
        })

for game in markets['spreads']:
    home, away, ticker = game['home_team'], game['away_team'], game['ticker']
    if not home or not away or not ticker:
        continue
    
    yes_price = game['yes_price']
    spread_diff = 50 - yes_price
    
    if abs(spread_diff) >= min_edge:
        if spread_diff > 0:
            rec, spread_team, color = "COVERS", home, '🟢'
        else:
            rec, spread_team, color = "FAILS", away, '🔴'
        
        bet_amt = calculate_kelly(50 + abs(spread_diff), yes_price if spread_diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
        game_url = f"https://kalshi.com/markets/kxnbaspread/{ticker.lower()}"
        
        top_edges.append({
            'type': 'SPR', 'game': f"{away} @ {home}", 'date': game['game_date'], 'ticker': ticker,
            'edge': abs(spread_diff), 'rec': f"{spread_team} {rec}", 'bet_team': spread_team,
            'bet_amount': bet_amt, 'url': game_url, 'color': color
        })

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
            team_label = str(edge['bet_team']).upper()
            amount_label = float(edge['bet_amount'])
            btn_text = f"BET {team_label} ${amount_label:.0f}"
            st.link_button(btn_text, edge['url'], use_container_width=True, key=f"top_{i}_{edge['ticker']}")
else:
    st.info("No edges found. Try lowering the min edge % in settings.")

st.markdown("---")

# ========== TABS ==========
tab1, tab2, tab3 = st.tabs(["📈 Moneyline", "📊 Totals", "📉 Spreads"])

with tab1:
    st.subheader("Moneyline Markets")
    for idx, game in enumerate(markets['moneyline'][:15]):
        home, away, ticker = game['home_team'], game['away_team'], game['ticker']
        if not home or not away:
            continue
        yes_price = game['yes_price']
        home_rest = rest_days.get(home, default_home_rest)
        away_rest = rest_days.get(away, default_away_rest)
        travel = calculate_travel_distance(away, home)
        analysis = calculate_edge(home, away, yes_price, home_rest, away_rest, 0, 0, travel, default_ref_bias, weights)
        
        if analysis['recommendation'] == 'BUY YES': indicator = "🟢"
        elif analysis['recommendation'] == 'BUY NO': indicator = "🔴"
        else: indicator = "⚪"
        
        with st.expander(f"{indicator} {away} @ {home} | {game['game_date']} | {yes_price}¢ | Edge: {analysis['edge']:+.1f}%"):
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
                    bet_amt = calculate_kelly(win_prob, price, bankroll, kelly_fraction)
                    st.markdown(f"**{analysis['recommendation']}**")
                    st.metric("Bet Size", f"${bet_amt:.2f}")
                    game_url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker.lower()}"
                    st.link_button(f"BET {bet_team.upper()} ${bet_amt:.0f}", game_url, use_container_width=True, key=f"ml_{idx}_{ticker}")
                else:
                    st.info("No edge")

with tab2:
    st.subheader("Totals Markets")
    for idx, game in enumerate(markets['totals'][:15]):
        home, away, ticker = game['home_team'], game['away_team'], game['ticker']
        if not home or not away:
            continue
        yes_price, line = game['yes_price'], game.get('line', 220)
        home_stats, away_stats = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        combined_pace = (home_stats.get('pace', 100) + away_stats.get('pace', 100)) / 2
        projected = (home_stats.get('ppg', 110) + away_stats.get('ppg', 110)) * (combined_pace / 100)
        diff = projected - line
        
        if diff > min_edge: indicator, rec = "🟢", "OVER"
        elif diff < -min_edge: indicator, rec = "🔴", "UNDER"
        else: indicator, rec = "⚪", "PASS"
        
        with st.expander(f"{indicator} {away} @ {home} | Line: {line} | {yes_price}¢ | Proj: {projected:.0f}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Line", f"{line}")
                st.metric("Projected", f"{projected:.1f}")
            with c2:
                st.metric("Difference", f"{diff:+.1f}")
                st.metric("Yes Price", f"{yes_price}¢")
            with c3:
                if abs(diff) >= min_edge:
                    bet_amt = calculate_kelly(50 + abs(diff), yes_price if diff > 0 else 100 - yes_price, bankroll, kelly_fraction)
                    st.markdown(f"**BUY {rec}**")
                    st.metric("Bet Size", f"${bet_amt:.2f}")
                    game_url = f"https://kalshi.com/markets/kxnbatotal/{ticker.lower()}"
                    st.link_button(f"BET {rec} ${bet_amt:.0f}", game_url, use_container_width=True, key=f"tot_{idx}_{ticker}")
                else:
                    st.info("No edge")

with tab3:
    st.subheader("Spread Markets")
    for idx, game in enumerate(markets['spreads'][:15]):
        home, away, ticker = game['home_team'], game['away_team'], game['ticker']
        if not home or not away:
            continue
        yes_price = game['yes_price']
        spread_edge = 50 - yes_price
        
        if spread_edge > min_edge: indicator, rec, bet_team = "🟢", "COVERS", home
        elif spread_edge < -min_edge: indicator, rec, bet_team = "🔴", "FAILS", away
        else: indicator, rec, bet_team = "⚪", "PASS", ""
        
        with st.expander(f"{indicator} {away} @ {home} | {yes_price}¢ | Edge: {spread_edge:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Yes Price", f"{yes_price}¢")
            with c2:
                st.metric("Edge", f"{spread_edge:+.1f}%")
            with c3:
                if abs(spread_edge) >= min_edge:
                    bet_amt = calculate_kelly(50 + abs(spread_edge), yes_price if spread_edge > 0 else 100 - yes_price, bankroll, kelly_fraction)
                    st.markdown(f"**{bet_team} {rec}**")
                    st.metric("Bet Size", f"${bet_amt:.2f}")
                    game_url = f"https://kalshi.com/markets/kxnbaspread/{ticker.lower()}"
                    st.link_button(f"BET {bet_team.upper()} ${bet_amt:.0f}", game_url, use_container_width=True, key=f"spr_{idx}_{ticker}")
                else:
                    st.info("No edge")

# ========== DEBUG ==========
with st.expander("🔧 Debug: Verify Tickers"):
    if top_edges:
        for e in top_edges[:5]:
            st.code(f"{e['game']}: {e['ticker']} → {e['url']}")
