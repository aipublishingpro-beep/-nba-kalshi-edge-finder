import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime, timedelta
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
    "Atlanta": {"net_rating": -1.8, "off_rating": 115.2, "def_rating": 117.0, "def_rank": 21, "pace": 101.2, "ppg": 118.5, "opp_ppg": 120.3, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southeast", "three_pct": 0.365, "ft_rate": 0.25, "reb_rate": 49.5},
    "Boston": {"net_rating": 11.2, "off_rating": 122.5, "def_rating": 111.3, "def_rank": 2, "pace": 99.8, "ppg": 120.5, "opp_ppg": 109.3, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Atlantic", "three_pct": 0.385, "ft_rate": 0.22, "reb_rate": 50.2},
    "Brooklyn": {"net_rating": -3.2, "off_rating": 111.5, "def_rating": 114.7, "def_rank": 22, "pace": 96.3, "ppg": 108.2, "opp_ppg": 111.4, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.358, "ft_rate": 0.24, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -5.5, "off_rating": 109.8, "def_rating": 115.3, "def_rank": 25, "pace": 100.5, "ppg": 110.5, "opp_ppg": 116.0, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pct": 0.342, "ft_rate": 0.23, "reb_rate": 49.0},
    "Chicago": {"net_rating": -2.5, "off_rating": 112.8, "def_rating": 115.3, "def_rank": 18, "pace": 98.5, "ppg": 112.0, "opp_ppg": 114.5, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Central", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 49.2},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.5, "def_rating": 108.7, "def_rank": 1, "pace": 97.2, "ppg": 116.8, "opp_ppg": 107.0, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Central", "three_pct": 0.378, "ft_rate": 0.26, "reb_rate": 51.0},
    "Dallas": {"net_rating": 3.5, "off_rating": 116.2, "def_rating": 112.7, "def_rank": 12, "pace": 99.8, "ppg": 117.5, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest", "three_pct": 0.362, "ft_rate": 0.24, "reb_rate": 49.5},
    "Denver": {"net_rating": 4.2, "off_rating": 117.8, "def_rating": 113.6, "def_rank": 15, "pace": 98.5, "ppg": 116.2, "opp_ppg": 112.0, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Northwest", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 51.5},
    "Detroit": {"net_rating": -6.2, "off_rating": 110.5, "def_rating": 116.7, "def_rank": 27, "pace": 99.2, "ppg": 110.8, "opp_ppg": 117.0, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central", "three_pct": 0.338, "ft_rate": 0.23, "reb_rate": 49.8},
    "Golden State": {"net_rating": 2.8, "off_rating": 115.5, "def_rating": 112.7, "def_rank": 11, "pace": 100.2, "ppg": 115.8, "opp_ppg": 113.0, "home_win_pct": 0.62, "away_win_pct": 0.38, "division": "Pacific", "three_pct": 0.375, "ft_rate": 0.22, "reb_rate": 48.5},
    "Houston": {"net_rating": 3.2, "off_rating": 113.8, "def_rating": 110.6, "def_rank": 5, "pace": 99.5, "ppg": 114.2, "opp_ppg": 111.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.28, "reb_rate": 52.0},
    "Indiana": {"net_rating": 2.5, "off_rating": 118.2, "def_rating": 115.7, "def_rank": 24, "pace": 103.5, "ppg": 121.5, "opp_ppg": 119.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 49.0},
    "LA Clippers": {"net_rating": 1.5, "off_rating": 113.5, "def_rating": 112.0, "def_rank": 10, "pace": 98.5, "ppg": 112.8, "opp_ppg": 111.3, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "three_pct": 0.358, "ft_rate": 0.26, "reb_rate": 50.0},
    "LA Lakers": {"net_rating": 1.8, "off_rating": 114.2, "def_rating": 112.4, "def_rank": 13, "pace": 99.8, "ppg": 115.5, "opp_ppg": 113.7, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific", "three_pct": 0.358, "ft_rate": 0.27, "reb_rate": 50.5},
    "Memphis": {"net_rating": 2.2, "off_rating": 115.8, "def_rating": 113.6, "def_rank": 16, "pace": 100.8, "ppg": 117.2, "opp_ppg": 115.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest", "three_pct": 0.348, "ft_rate": 0.28, "reb_rate": 51.2},
    "Miami": {"net_rating": 0.5, "off_rating": 111.8, "def_rating": 111.3, "def_rank": 8, "pace": 97.5, "ppg": 110.5, "opp_ppg": 110.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pct": 0.362, "ft_rate": 0.24, "reb_rate": 49.5},
    "Milwaukee": {"net_rating": 3.8, "off_rating": 116.5, "def_rating": 112.7, "def_rank": 14, "pace": 100.5, "ppg": 118.2, "opp_ppg": 114.4, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Central", "three_pct": 0.365, "ft_rate": 0.28, "reb_rate": 51.0},
    "Minnesota": {"net_rating": 5.5, "off_rating": 113.2, "def_rating": 107.7, "def_rank": 3, "pace": 97.8, "ppg": 112.5, "opp_ppg": 107.0, "home_win_pct": 0.65, "away_win_pct": 0.50, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 52.5},
    "New Orleans": {"net_rating": -2.0, "off_rating": 112.5, "def_rating": 114.5, "def_rank": 19, "pace": 99.0, "ppg": 113.2, "opp_ppg": 115.2, "home_win_pct": 0.45, "away_win_pct": 0.28, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.26, "reb_rate": 50.5},
    "New York": {"net_rating": 5.8, "off_rating": 117.2, "def_rating": 111.4, "def_rank": 6, "pace": 98.5, "ppg": 117.8, "opp_ppg": 112.0, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic", "three_pct": 0.372, "ft_rate": 0.26, "reb_rate": 52.0},
    "Oklahoma City": {"net_rating": 10.5, "off_rating": 118.8, "def_rating": 108.3, "def_rank": 4, "pace": 99.5, "ppg": 119.5, "opp_ppg": 109.0, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Northwest", "three_pct": 0.378, "ft_rate": 0.27, "reb_rate": 52.5},
    "Orlando": {"net_rating": 4.8, "off_rating": 110.5, "def_rating": 105.7, "def_rank": 2, "pace": 96.5, "ppg": 108.5, "opp_ppg": 103.7, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southeast", "three_pct": 0.345, "ft_rate": 0.28, "reb_rate": 53.0},
    "Philadelphia": {"net_rating": 1.2, "off_rating": 113.5, "def_rating": 112.3, "def_rank": 9, "pace": 98.2, "ppg": 113.8, "opp_ppg": 112.6, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic", "three_pct": 0.355, "ft_rate": 0.30, "reb_rate": 50.5},
    "Phoenix": {"net_rating": 2.5, "off_rating": 115.8, "def_rating": 113.3, "def_rank": 17, "pace": 98.8, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 49.0},
    "Portland": {"net_rating": -6.8, "off_rating": 108.5, "def_rating": 115.3, "def_rank": 28, "pace": 98.2, "ppg": 107.5, "opp_ppg": 114.3, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.338, "ft_rate": 0.22, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.2, "off_rating": 114.5, "def_rating": 115.7, "def_rank": 23, "pace": 100.5, "ppg": 117.8, "opp_ppg": 119.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific", "three_pct": 0.362, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -4.5, "off_rating": 111.8, "def_rating": 116.3, "def_rank": 26, "pace": 99.8, "ppg": 112.5, "opp_ppg": 117.0, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.23, "reb_rate": 50.0},
    "Toronto": {"net_rating": -3.2, "off_rating": 112.2, "def_rating": 115.4, "def_rank": 20, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.7, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic", "three_pct": 0.348, "ft_rate": 0.23, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.5, "off_rating": 108.5, "def_rating": 117.0, "def_rank": 29, "pace": 100.8, "ppg": 108.2, "opp_ppg": 116.7, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 48.0},
    "Washington": {"net_rating": -9.2, "off_rating": 107.8, "def_rating": 117.0, "def_rank": 30, "pace": 101.2, "ppg": 108.5, "opp_ppg": 117.7, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast", "three_pct": 0.332, "ft_rate": 0.21, "reb_rate": 47.5},
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976), "Charlotte": (35.225, -80.839),
    "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688), "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010),
    "Detroit": (42.341, -83.055), "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051), "Miami": (25.781, -80.188),
    "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276), "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994),
    "Oklahoma City": (35.463, -97.515), "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438), "Toronto": (43.643, -79.379),
    "Utah": (40.768, -111.901), "Washington": (38.898, -77.021),
}

def calculate_travel_distance(away_team, home_team):
    if away_team not in TEAM_LOCATIONS or home_team not in TEAM_LOCATIONS:
        return 0
    lat1, lon1 = TEAM_LOCATIONS[away_team]
    lat2, lon2 = TEAM_LOCATIONS[home_team]
    R = 3959
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)))

def parse_teams(ticker):
    try:
        code = ticker.split('-')[1]
        away_abbr = code[-6:-3].upper()
        home_abbr = code[-3:].upper()
        date_part = code[:-6]
        year = int("20" + date_part[:2])
        month_str = date_part[2:5].upper()
        day = int(date_part[5:7])
        month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                     'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
        game_date = datetime(year, month_map.get(month_str, 1), day)
        return KALSHI_ABBREV_MAP.get(home_abbr), KALSHI_ABBREV_MAP.get(away_abbr), game_date
    except:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_markets():
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for mtype, series in [('moneyline', 'KXNBAGAME'), ('totals', 'KXNBATOTAL'), ('spreads', 'KXNBASPREAD')]:
        try:
            resp = requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open", timeout=10)
            for m in resp.json().get('markets', []):
                ticker = m.get('ticker', '')
                home, away, game_date = parse_teams(ticker)
                if not home or not away or not game_date or game_date.date() < today.date():
                    continue
                
                yes_bid = m.get('yes_bid', 0) or 0
                yes_ask = m.get('yes_ask', 0) or 0
                yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid or 50
                
                date_display = game_date.strftime('%b %d')
                is_today = game_date.date() == today.date()
                
                info = {'ticker': ticker, 'home': home, 'away': away, 'yes_price': yes_price, 
                        'game_date': date_display, 'game_dt': game_date, 'is_today': is_today}
                
                if mtype == 'totals':
                    info['line'] = m.get('floor_strike', 220)
                elif mtype == 'spreads':
                    info['line'] = m.get('floor_strike', 5)
                    try:
                        info['spread_team'] = KALSHI_ABBREV_MAP.get(ticker.split('-')[-1][:3].upper(), home)
                    except:
                        info['spread_team'] = home
                
                markets[mtype].append(info)
        except Exception as e:
            st.sidebar.warning(f"{series} error: {e}")
    
    for k in markets:
        markets[k].sort(key=lambda x: x.get('game_dt', datetime.max))
    return markets

@st.cache_data(ttl=3600)
def fetch_rest_days():
    rest = {team: 2 for team in TEAM_STATS.keys()}
    try:
        now = datetime.now()
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        for m in resp.json().get('markets', []):
            home, away, game_date = parse_teams(m.get('ticker', ''))
            if not home or not away or not game_date:
                continue
            days = (now - game_date).days
            if 0 <= days <= 5:
                if days < rest.get(home, 99):
                    rest[home] = days
                if days < rest.get(away, 99):
                    rest[away] = days
    except:
        pass
    return rest

def calculate_edge(home, away, kalshi_price, home_rest, away_rest, home_inj, away_inj, travel, weights):
    """REALISTIC edge calculation with haircuts"""
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    
    if not hs or not aws:
        return {"prob": 50, "adj_prob": 50, "raw_edge": 0, "adj_edge": 0, "factors": {}, "raw": {}, "rec": "NO DATA", "conf": "LOW", "haircut": 5}
    
    factors, raw = {}, {}
    
    # REALISTIC WEIGHTS (scaled down)
    
    # 1. Rest: 1.0 per day diff (was 2.5)
    rest_diff = home_rest - away_rest
    factors["rest"] = max(-3, min(3, rest_diff * 1.0 * weights["rest"]))
    raw["home_rest"], raw["away_rest"] = home_rest, away_rest
    
    # 2. Defense: 0.1 per rank diff (was 0.15)
    def_diff = aws.get("def_rank", 15) - hs.get("def_rank", 15)
    factors["defense"] = max(-2, min(2, def_diff * 0.1 * weights["defense"]))
    raw["home_def"], raw["away_def"] = hs.get("def_rank", 15), aws.get("def_rank", 15)
    
    # 3. Injury: 1.0 per level (was 1.5)
    inj_diff = away_inj - home_inj
    factors["injury"] = max(-3, min(3, inj_diff * 1.0 * weights["injury"]))
    raw["home_inj"], raw["away_inj"] = home_inj, away_inj
    
    # 4. Pace: minimal impact
    pace_diff = hs.get("pace", 100) - aws.get("pace", 100)
    factors["pace"] = max(-1, min(1, pace_diff * 0.05 * weights["pace"]))
    raw["home_pace"], raw["away_pace"] = hs.get("pace", 100), aws.get("pace", 100)
    
    # 5. Net Rating: 0.4 per point (was 0.8) - CAPPED
    net_diff = hs.get("net_rating", 0) - aws.get("net_rating", 0)
    factors["net_rating"] = max(-6, min(6, net_diff * 0.4 * weights["net_rating"]))
    raw["home_net"], raw["away_net"] = hs.get("net_rating", 0), aws.get("net_rating", 0)
    
    # 6. Travel: 0.3 per 1000mi (was 0.8)
    travel_factor = min(travel / 1000, 3) * 0.3 * weights["travel"]
    factors["travel"] = max(0, min(1.5, travel_factor))
    raw["travel"] = travel
    
    # 7. Splits: 3.0 multiplier (was 8)
    split_diff = hs.get("home_win_pct", 0.5) - aws.get("away_win_pct", 0.5)
    factors["splits"] = max(-2, min(2, split_diff * 3.0 * weights["splits"]))
    raw["home_pct"], raw["away_pct"] = hs.get("home_win_pct", 0.5), aws.get("away_win_pct", 0.5)
    
    # 8. Division: -1.0 (was -1.5)
    is_div = hs.get("division") == aws.get("division")
    factors["division"] = -1.0 * weights["division"] if is_div else 0
    raw["is_division"] = is_div
    
    # 9-12: Minor factors (reduced)
    ft_diff = hs.get("ft_rate", 0.25) - aws.get("ft_rate", 0.25)
    factors["ft_rate"] = max(-1, min(1, ft_diff * 5 * weights["ft_rate"]))
    raw["home_ft"], raw["away_ft"] = hs.get("ft_rate", 0.25), aws.get("ft_rate", 0.25)
    
    reb_diff = hs.get("reb_rate", 50) - aws.get("reb_rate", 50)
    factors["rebounding"] = max(-1, min(1, reb_diff * 0.1 * weights["rebounding"]))
    raw["home_reb"], raw["away_reb"] = hs.get("reb_rate", 50), aws.get("reb_rate", 50)
    
    three_diff = (hs.get("three_pct", 0.35) - aws.get("three_pct", 0.35)) * 100
    factors["three_pt"] = max(-1, min(1, three_diff * 0.15 * weights["three_pt"]))
    raw["home_3pt"], raw["away_3pt"] = hs.get("three_pct", 0.35), aws.get("three_pct", 0.35)
    
    # Calculate raw probability
    base_home_adv = 2.5  # Reduced from 3.5
    total_adj = sum(factors.values())
    total_adj = max(-10, min(10, total_adj))  # Cap total adjustment at ±10%
    
    raw_prob = 50 + base_home_adv + total_adj
    raw_prob = max(25, min(75, raw_prob))
    
    # MANDATORY HAIRCUTS - applied toward 50%
    haircut = 5  # Model uncertainty (3%) + NBA variance (2%)
    
    if raw_prob > 50:
        adj_prob = max(50, raw_prob - haircut)
    else:
        adj_prob = min(50, raw_prob + haircut)
    
    raw_edge = raw_prob - kalshi_price
    adj_edge = adj_prob - kalshi_price
    
    # REALISTIC THRESHOLDS
    if abs(adj_edge) < 2:
        rec, conf = "NO EDGE", "LOW"
    elif abs(adj_edge) < 3:
        rec = "SLIGHT HOME" if adj_edge > 0 else "SLIGHT AWAY"
        conf = "LOW"
    elif abs(adj_edge) < 5:
        rec = "FAVORS HOME" if adj_edge > 0 else "FAVORS AWAY"
        conf = "MED"
    else:
        rec = "CHECK MODEL" if adj_edge > 0 else "CHECK MODEL"
        conf = "HIGH"
    
    return {
        "prob": raw_prob, "adj_prob": adj_prob, "raw_edge": raw_edge, "adj_edge": adj_edge,
        "factors": factors, "raw": raw, "rec": rec, "conf": conf, "haircut": haircut
    }

def calculate_kelly(win_prob, price, bankroll, fraction):
    p = win_prob / 100
    b = (100 - price) / price if price > 0 else 1
    kelly = max(0, (p * b - (1 - p)) / b) if b > 0 else 0
    adj_kelly = kelly * fraction
    return {"kelly": round(kelly * 100, 2), "adj_kelly": round(adj_kelly * 100, 2), "bet": round(bankroll * adj_kelly, 2)}

# ========== UI ==========
st.title("🏀 NBA Edge Finder")
st.caption("Realistic Model • Haircuts Applied • For Analysis Only")

clicked_game = st.query_params.get("game", None)
if clicked_game:
    components.html(f'''<script>setTimeout(function(){{var el=window.parent.document.getElementById("game-{clicked_game}");if(el)el.scrollIntoView({{behavior:"smooth",block:"start"}})}},500)</script>''', height=0)

st.markdown("""
<style>
    .prediction-banner {background: linear-gradient(135deg, rgba(255, 107, 53, 0.2) 0%, rgba(247, 147, 30, 0.1) 100%);
        border-left: 4px solid #FF6B35; border-radius: 8px; padding: 16px 20px; margin: 10px 0;}
    .prediction-banner:hover {transform: scale(1.01); box-shadow: 0 4px 20px rgba(255, 107, 53, 0.3);}
    .prediction-team {font-size: 1.5rem; font-weight: 700; color: #FAFAFA;}
    .prediction-edge {font-size: 1.8rem; font-weight: 800; color: #FF6B35;}
    .prediction-details {color: rgba(250, 250, 250, 0.7); font-size: 0.9rem; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Settings")
st.sidebar.markdown("**Realistic Weights**")
st.sidebar.caption("Scaled to produce 2-5% edges max")

with st.sidebar.expander("🎚️ Factor Weights", expanded=False):
    w_rest = st.slider("Rest", 0.0, 2.0, 1.0, 0.1, key="w1")
    w_def = st.slider("Defense", 0.0, 2.0, 1.0, 0.1, key="w2")
    w_inj = st.slider("Injuries", 0.0, 2.0, 1.0, 0.1, key="w3")
    w_pace = st.slider("Pace", 0.0, 2.0, 1.0, 0.1, key="w4")
    w_net = st.slider("Net Rating", 0.0, 2.0, 1.0, 0.1, key="w5")
    w_travel = st.slider("Travel", 0.0, 2.0, 1.0, 0.1, key="w6")
    w_splits = st.slider("Splits", 0.0, 2.0, 1.0, 0.1, key="w7")
    w_div = st.slider("Division", 0.0, 2.0, 1.0, 0.1, key="w8")
    w_ft = st.slider("FT Rate", 0.0, 2.0, 1.0, 0.1, key="w10")
    w_reb = st.slider("Rebounding", 0.0, 2.0, 1.0, 0.1, key="w11")
    w_three = st.slider("3PT", 0.0, 2.0, 1.0, 0.1, key="w12")

weights = {"rest": w_rest, "defense": w_def, "injury": w_inj, "pace": w_pace, "net_rating": w_net, 
           "travel": w_travel, "splits": w_splits, "division": w_div, "ft_rate": w_ft, 
           "rebounding": w_reb, "three_pt": w_three}

st.sidebar.markdown("---")
st.sidebar.markdown("**Haircuts (Always Applied)**")
st.sidebar.write("• Model uncertainty: -3%")
st.sidebar.write("• NBA variance: -2%")
st.sidebar.write("• **Total: -5%**")

st.sidebar.markdown("---")
st.sidebar.markdown("**Edge Thresholds**")
st.sidebar.write("• <2% = No edge")
st.sidebar.write("• 2-3% = Slight edge")
st.sidebar.write("• 3-5% = Good edge")
st.sidebar.write("• >5% = Check model")

with st.sidebar.expander("💰 Position Sizing"):
    bankroll = st.number_input("Bankroll ($)", 100, 100000, 1000)
    kelly_frac = st.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.query_params.clear()
    st.rerun()

markets = fetch_markets()
rest_days = fetch_rest_days()

st.sidebar.markdown("---")
st.sidebar.write(f"**Games:** {len(markets['moneyline'])}")

# Top Edges
st.markdown("---")
st.subheader("🎯 Top Edges (After Haircuts)")

all_edges = []
seen = set()
for g in markets['moneyline']:
    home, away = g['home'], g['away']
    key = f"{away} @ {home}"
    if key in seen or not g.get('is_today'):
        continue
    seen.add(key)
    
    travel = calculate_travel_distance(away, home)
    analysis = calculate_edge(home, away, g['yes_price'], rest_days.get(home, 2), rest_days.get(away, 2), 0, 0, travel, weights)
    
    if abs(analysis['adj_edge']) >= 2:
        pred_team = home if analysis['adj_edge'] > 0 else away
        all_edges.append({
            "game": key, "pred": pred_team, "adj_edge": abs(analysis['adj_edge']),
            "raw_edge": abs(analysis['raw_edge']), "rec": analysis['rec'], "conf": analysis['conf'],
            "date": g['game_date']
        })

all_edges.sort(key=lambda x: x['adj_edge'], reverse=True)

if all_edges[:3]:
    cols = st.columns(3)
    for i, e in enumerate(all_edges[:3]):
        with cols[i]:
            game_encoded = e['game'].replace(' ', '_').replace('@', 'at')
            edge_color = "#FF6B35" if e['adj_edge'] >= 3 else "#888"
            st.markdown(f'''
            <a href="?game={game_encoded}" style="text-decoration:none;">
                <div class="prediction-banner" style="cursor:pointer; border-left-color:{edge_color}">
                    <span class="prediction-team">{e["pred"]}</span><br>
                    <span class="prediction-edge" style="color:{edge_color}">+{e["adj_edge"]:.1f}%</span>
                    <div class="prediction-details">{e["date"]} • {e["game"]} • {e["conf"]}</div>
                    <div style="font-size:0.7rem; color:#888; margin-top:4px;">Raw: {e["raw_edge"]:.1f}% → Adj: {e["adj_edge"]:.1f}% (after -5% haircut)</div>
                </div>
            </a>
            ''', unsafe_allow_html=True)
else:
    st.info("No edges ≥2% after haircuts today. This is normal - pass most games.")

# Tabs
tab_ml, tab_tot, tab_spr = st.tabs(["🏀 Winner", "📊 Totals", "📏 Spreads"])

with tab_ml:
    st.subheader("Game Winner Analysis")
    
    seen_ml = set()
    for idx, g in enumerate(markets['moneyline']):
        home, away = g['home'], g['away']
        key = f"{away} @ {home}"
        if key in seen_ml:
            continue
        seen_ml.add(key)
        
        travel = calculate_travel_distance(away, home)
        h_rest, a_rest = rest_days.get(home, 2), rest_days.get(away, 2)
        analysis = calculate_edge(home, away, g['yes_price'], h_rest, a_rest, 0, 0, travel, weights)
        
        if analysis['adj_edge'] > 2:
            indicator = "🟢"
        elif analysis['adj_edge'] < -2:
            indicator = "🔴"
        else:
            indicator = "⚪"
        
        game_encoded = key.replace(' ', '_').replace('@', 'at')
        should_expand = (clicked_game == game_encoded)
        
        st.markdown(f'<div id="game-{game_encoded}" style="scroll-margin-top:100px;"></div>', unsafe_allow_html=True)
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | Adj: {analysis['adj_edge']:+.1f}% | {analysis['rec']}", expanded=should_expand):
            ic1, ic2 = st.columns(2)
            with ic1:
                home_inj = st.select_slider(f"🏥 {home}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","STAR GTD","STAR OUT"][x], key=f"ml_h_{idx}")
            with ic2:
                away_inj = st.select_slider(f"🏥 {away}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","STAR GTD","STAR OUT"][x], key=f"ml_a_{idx}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.0, 3: 3.0}
            analysis = calculate_edge(home, away, g['yes_price'], h_rest, a_rest, inj_map[home_inj], inj_map[away_inj], travel, weights)
            
            # Results
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Market", f"{g['yes_price']:.0f}%")
            c2.metric("Model", f"{analysis['prob']:.1f}%")
            c3.metric("Haircut", f"-{analysis['haircut']}%")
            c4.metric("Adj Model", f"{analysis['adj_prob']:.1f}%")
            c5.metric("ADJ EDGE", f"{analysis['adj_edge']:+.1f}%")
            
            if analysis['rec'] not in ["NO EDGE", "NO DATA"]:
                pred_team = home if analysis['adj_edge'] > 0 else away
                kelly = calculate_kelly(analysis['adj_prob'] if analysis['adj_edge'] > 0 else 100 - analysis['adj_prob'], 
                                        g['yes_price'] if analysis['adj_edge'] > 0 else 100 - g['yes_price'], bankroll, kelly_frac)
                st.markdown(f'''
                <div class="prediction-banner">
                    <span class="prediction-team">Model: {pred_team}</span>
                    <span class="prediction-edge" style="float:right">{analysis['adj_edge']:+.1f}%</span>
                    <div class="prediction-details">{analysis['rec']} • Kelly: ${kelly['bet']:.2f}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.info(f"No actionable edge. Raw: {analysis['raw_edge']:+.1f}% → After haircut: {analysis['adj_edge']:+.1f}%")
            
            with st.expander("📊 Factor Breakdown"):
                f = analysis['factors']
                for name, val in f.items():
                    st.write(f"• {name}: {val:+.2f}%")

with tab_tot:
    st.subheader("Total Points")
    seen_tot = set()
    for g in markets['totals']:
        home, away, line = g['home'], g['away'], g.get('line', 220)
        key = f"{away} @ {home}"
        if key in seen_tot:
            continue
        seen_tot.add(key)
        
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        projected = (hs.get('ppg', 110) + aws.get('ppg', 110)) - ((15 - hs.get('def_rank', 15)) + (15 - aws.get('def_rank', 15))) * 0.2
        raw_edge = projected - line
        adj_edge = raw_edge * 0.5  # Conservative haircut on totals
        
        indicator = "🟢" if adj_edge > 2 else ("🔴" if adj_edge < -2 else "⚪")
        rec = "OVER" if adj_edge > 2 else ("UNDER" if adj_edge < -2 else "NO EDGE")
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | O/U {line} | {adj_edge:+.1f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Line", f"{line}")
            c2.metric("Projected", f"{projected:.1f}")
            c3.metric("Adj Edge", f"{adj_edge:+.1f}")

with tab_spr:
    st.subheader("Spreads")
    seen_spr = set()
    for g in markets['spreads']:
        home, away, line = g['home'], g['away'], g.get('line', 5)
        key = f"{away} @ {home}"
        if key in seen_spr:
            continue
        seen_spr.add(key)
        
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        predicted = (hs.get('net_rating', 0) - aws.get('net_rating', 0)) * 0.4 + 2.5
        raw_edge = predicted - line
        adj_edge = raw_edge * 0.5
        
        indicator = "🟢" if adj_edge > 2 else ("🔴" if adj_edge < -2 else "⚪")
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | {g.get('spread_team', home)} -{line} | {adj_edge:+.1f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Line", f"-{line}")
            c2.metric("Model", f"{predicted:+.1f}")
            c3.metric("Adj Edge", f"{adj_edge:+.1f}")

st.markdown("---")
st.caption("⚠️ **Realistic edges are 2-5%.** If you see 10%+ edges, the model is wrong, not the market. Always apply haircuts. Pass 90% of games.")
