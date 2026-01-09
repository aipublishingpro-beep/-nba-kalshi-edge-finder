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
    """Extract home and away teams from ticker like KXNBAGAME-26JAN09BOSTOR"""
    try:
        code = ticker.split('-')[1]
        away_abbr = code[-6:-3].upper()
        home_abbr = code[-3:].upper()
        return KALSHI_ABBREV_MAP.get(home_abbr), KALSHI_ABBREV_MAP.get(away_abbr)
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_markets():
    """Fetch NBA markets from Kalshi API - TODAY's games only"""
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    today = datetime.now().date()
    
    for mtype, series in [('moneyline', 'KXNBAGAME'), ('totals', 'KXNBATOTAL'), ('spreads', 'KXNBASPREAD')]:
        try:
            resp = requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open", timeout=10)
            for m in resp.json().get('markets', []):
                ticker = m.get('ticker', '')
                home, away = parse_teams(ticker)
                if not home or not away:
                    continue
                
                close_time = m.get('close_time', '')
                try:
                    game_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)
                    if game_dt.date() < today:
                        continue
                    game_date = game_dt.strftime('%b %d')
                except:
                    continue
                
                yes_bid = m.get('yes_bid', 0) or 0
                yes_ask = m.get('yes_ask', 0) or 0
                yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid or 50
                
                info = {'ticker': ticker, 'home': home, 'away': away, 'yes_price': yes_price, 'game_date': game_date, 'close_time': close_time}
                
                if mtype == 'totals':
                    info['line'] = m.get('floor_strike', 220)
                elif mtype == 'spreads':
                    info['line'] = m.get('floor_strike', 5)
                    # Extract spread team from ticker
                    try:
                        spread_abbr = ticker.split('-')[-1][:3].upper()
                        info['spread_team'] = KALSHI_ABBREV_MAP.get(spread_abbr, home)
                    except:
                        info['spread_team'] = home
                
                markets[mtype].append(info)
        except Exception as e:
            st.sidebar.warning(f"{series} fetch error: {e}")
    
    for k in markets:
        markets[k].sort(key=lambda x: x.get('close_time', ''))
    
    return markets

@st.cache_data(ttl=3600)
def fetch_rest_days():
    """Get rest days from settled games"""
    rest = {team: 2 for team in TEAM_STATS.keys()}
    try:
        now = datetime.now()
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        for m in resp.json().get('markets', []):
            ticker = m.get('ticker', '')
            close_time = m.get('close_time', '')
            if not close_time or '-' not in ticker:
                continue
            try:
                days = (now - datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)).days
                if 0 <= days <= 5:
                    home, away = parse_teams(ticker)
                    if home and days < rest.get(home, 99):
                        rest[home] = days
                    if away and days < rest.get(away, 99):
                        rest[away] = days
            except:
                pass
    except:
        pass
    return rest

def calculate_edge(home, away, kalshi_price, home_rest, away_rest, home_inj, away_inj, travel, ref_bias, weights):
    """Calculate model probability and edge"""
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    
    if not hs or not aws:
        return {"prob": 50, "edge": 0, "factors": {}, "raw": {}, "rec": "NO TRADE", "conf": "LOW"}
    
    factors, raw = {}, {}
    
    # 1. Rest
    rest_diff = home_rest - away_rest
    factors["rest"] = rest_diff * 2.5 * weights["rest"]
    raw["home_rest"], raw["away_rest"] = home_rest, away_rest
    
    # 2. Defense
    def_diff = aws.get("def_rank", 15) - hs.get("def_rank", 15)
    factors["defense"] = def_diff * 0.15 * weights["defense"]
    raw["home_def"], raw["away_def"] = hs.get("def_rank", 15), aws.get("def_rank", 15)
    
    # 3. Injury (manual input)
    inj_diff = away_inj - home_inj
    factors["injury"] = inj_diff * 1.5 * weights["injury"]
    raw["home_inj"], raw["away_inj"] = home_inj, away_inj
    
    # 4. Pace
    pace_diff = hs.get("pace", 100) - aws.get("pace", 100)
    factors["pace"] = pace_diff * 0.1 * weights["pace"]
    raw["home_pace"], raw["away_pace"] = hs.get("pace", 100), aws.get("pace", 100)
    
    # 5. Net Rating
    net_diff = hs.get("net_rating", 0) - aws.get("net_rating", 0)
    factors["net_rating"] = net_diff * 0.8 * weights["net_rating"]
    raw["home_net"], raw["away_net"] = hs.get("net_rating", 0), aws.get("net_rating", 0)
    
    # 6. Travel
    travel_factor = min(travel / 1000, 3) * 0.8 * weights["travel"]
    factors["travel"] = travel_factor
    raw["travel"] = travel
    
    # 7. Splits
    split_diff = hs.get("home_win_pct", 0.5) - aws.get("away_win_pct", 0.5)
    factors["splits"] = split_diff * 8 * weights["splits"]
    raw["home_pct"], raw["away_pct"] = hs.get("home_win_pct", 0.5), aws.get("away_win_pct", 0.5)
    
    # 8. Division
    is_div = hs.get("division") == aws.get("division")
    factors["division"] = -1.5 * weights["division"] if is_div else 0
    raw["is_division"] = is_div
    
    # 9. Refs
    factors["refs"] = ref_bias * weights["refs"]
    raw["ref_bias"] = ref_bias
    
    # 10. FT Rate
    ft_diff = hs.get("ft_rate", 0.25) - aws.get("ft_rate", 0.25)
    factors["ft_rate"] = ft_diff * 15 * weights["ft_rate"]
    raw["home_ft"], raw["away_ft"] = hs.get("ft_rate", 0.25), aws.get("ft_rate", 0.25)
    
    # 11. Rebounding
    reb_diff = hs.get("reb_rate", 50) - aws.get("reb_rate", 50)
    factors["rebounding"] = reb_diff * 0.2 * weights["rebounding"]
    raw["home_reb"], raw["away_reb"] = hs.get("reb_rate", 50), aws.get("reb_rate", 50)
    
    # 12. 3PT
    three_diff = (hs.get("three_pct", 0.35) - aws.get("three_pct", 0.35)) * 100
    factors["three_pt"] = three_diff * 0.3 * weights["three_pt"]
    raw["home_3pt"], raw["away_3pt"] = hs.get("three_pct", 0.35), aws.get("three_pct", 0.35)
    
    # Calculate final probability
    base_home_adv = 3.5
    total_adj = sum(factors.values())
    prob = max(15, min(85, 50 + base_home_adv + total_adj))
    
    edge = prob - kalshi_price
    
    if edge > 3:
        rec, conf = "FAVORS HOME", "HIGH" if edge > 6 else "MED"
    elif edge < -3:
        rec, conf = "FAVORS AWAY", "HIGH" if edge < -6 else "MED"
    else:
        rec, conf = "NO EDGE", "LOW"
    
    return {"prob": prob, "edge": edge, "factors": factors, "raw": raw, "rec": rec, "conf": conf}

def calculate_kelly(win_prob, price, bankroll, fraction):
    p = win_prob / 100
    b = (100 - price) / price if price > 0 else 1
    kelly = max(0, (p * b - (1 - p)) / b) if b > 0 else 0
    adj_kelly = kelly * fraction
    bet = bankroll * adj_kelly
    ev = bet * (p * b - (1 - p))
    return {"kelly": round(kelly * 100, 2), "adj_kelly": round(adj_kelly * 100, 2), "bet": round(bet, 2), "ev": round(ev, 2)}

# ========== UI ==========
st.title("🏀 NBA Edge Finder")
st.caption("12-Factor Prediction Model • For Analysis Only • Not Financial Advice")

# Sidebar
st.sidebar.header("🎚️ Factor Weights")

with st.sidebar.expander("🏀 Core Factors", expanded=True):
    w_rest = st.slider("🛏️ Rest Days", 0.0, 2.0, 1.0, 0.1, key="w1", help="Rest advantage. B2B = fatigue.")
    w_def = st.slider("🛡️ Defense Rank", 0.0, 2.0, 1.0, 0.1, key="w2", help="Defensive rating diff.")
    w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1, key="w3", help="Manual injury input.")
    w_pace = st.slider("🏃 Pace", 0.0, 2.0, 1.0, 0.1, key="w4", help="Game tempo diff.")
    w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1, key="w5", help="Overall team quality.")
    w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1, key="w6", help="Away team miles.")

with st.sidebar.expander("📈 Advanced Factors", expanded=True):
    w_splits = st.slider("🏠 Splits", 0.0, 2.0, 1.0, 0.1, key="w7", help="Home/Away win %.")
    w_div = st.slider("⚔️ Division", 0.0, 2.0, 1.0, 0.1, key="w8", help="Rivalry = closer games.")
    w_refs = st.slider("👨‍⚖️ Refs", 0.0, 2.0, 1.0, 0.1, key="w9", help="Ref crew bias.")
    w_ft = st.slider("🎯 FT Rate", 0.0, 2.0, 1.0, 0.1, key="w10", help="Free throw rate.")
    w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1, key="w11", help="Rebound rate.")
    w_three = st.slider("🎯 3PT", 0.0, 2.0, 1.0, 0.1, key="w12", help="3-point %.")

weights = {"rest": w_rest, "defense": w_def, "injury": w_inj, "pace": w_pace, "net_rating": w_net, "travel": w_travel, "splits": w_splits, "division": w_div, "refs": w_refs, "ft_rate": w_ft, "rebounding": w_reb, "three_pt": w_three}

with st.sidebar.expander("⚙️ Settings"):
    default_ref_bias = st.slider("Ref Bias (+ = home)", -3.0, 3.0, 0.0, 0.5)
    min_edge = st.slider("Min Edge", 0.0, 10.0, 1.0, 0.5)

with st.sidebar.expander("📐 Position Sizing (Info Only)"):
    bankroll = st.number_input("Hypothetical Bankroll ($)", 100, 100000, 1000)
    kelly_frac = st.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# Load data
markets = fetch_markets()
rest_days = fetch_rest_days()

st.sidebar.markdown("---")
st.sidebar.write(f"**ML:** {len(markets['moneyline'])} | **TOT:** {len(markets['totals'])} | **SPR:** {len(markets['spreads'])}")

# Top 3 Edges
st.markdown("---")
st.subheader("🎯 Top 3 Model Predictions")

all_edges = []
for g in markets['moneyline']:
    home, away = g['home'], g['away']
    travel = calculate_travel_distance(away, home)
    h_rest, a_rest = rest_days.get(home, 2), rest_days.get(away, 2)
    analysis = calculate_edge(home, away, g['yes_price'], h_rest, a_rest, 0, 0, travel, default_ref_bias, weights)
    
    if abs(analysis['edge']) >= min_edge:
        pred_team = home if analysis['rec'] == 'FAVORS HOME' else away
        kelly = calculate_kelly(analysis['prob'] if analysis['rec'] == 'FAVORS HOME' else 100 - analysis['prob'], g['yes_price'] if analysis['rec'] == 'FAVORS HOME' else 100 - g['yes_price'], bankroll, kelly_frac)
        all_edges.append({"game": f"{away} @ {home}", "pred": pred_team, "edge": abs(analysis['edge']), "kelly": kelly['bet'], "rec": analysis['rec'], "conf": analysis['conf']})

all_edges.sort(key=lambda x: x['edge'], reverse=True)

if all_edges[:3]:
    cols = st.columns(3)
    for i, e in enumerate(all_edges[:3]):
        with cols[i]:
            color = "🟢" if "HOME" in e['rec'] else "🔴"
            st.metric(f"{color} {e['pred']}", f"+{e['edge']:.1f}% edge", f"Confidence: {e['conf']}")
            st.caption(f"{e['game']}")
else:
    st.info("No edges above threshold.")

# Tabs
tab_ml, tab_tot, tab_spr = st.tabs(["🏀 Winner", "📊 Totals", "📏 Spreads"])

with tab_ml:
    st.subheader("Game Winner Predictions")
    
    if not markets['moneyline']:
        st.warning("No games found for today.")
    
    for idx, g in enumerate(markets['moneyline']):
        home, away = g['home'], g['away']
        travel = calculate_travel_distance(away, home)
        h_rest, a_rest = rest_days.get(home, 2), rest_days.get(away, 2)
        
        with st.expander(f"{g['game_date']} | {away} @ {home}"):
            # Manual injury inputs
            ic1, ic2 = st.columns(2)
            with ic1:
                home_inj = st.select_slider(f"🏥 {home}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","STAR GTD","STAR OUT"][x], key=f"ml_h_{idx}")
            with ic2:
                away_inj = st.select_slider(f"🏥 {away}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","STAR GTD","STAR OUT"][x], key=f"ml_a_{idx}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.5, 3: 4.0}
            analysis = calculate_edge(home, away, g['yes_price'], h_rest, a_rest, inj_map[home_inj], inj_map[away_inj], travel, default_ref_bias, weights)
            
            color = "🟢" if analysis['rec'] == 'FAVORS HOME' else ("🔴" if analysis['rec'] == 'FAVORS AWAY' else "⚪")
            pred_team = home if analysis['rec'] == 'FAVORS HOME' else away
            
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kalshi Price", f"{g['yes_price']:.0f}¢ {home}")
            c2.metric("Model Prob", f"{analysis['prob']:.1f}%")
            c3.metric("Edge", f"{analysis['edge']:+.1f}%")
            c4.metric("Prediction", f"{color} {pred_team}")
            
            # Kelly (informational only)
            if analysis['rec'] != "NO EDGE":
                kelly = calculate_kelly(analysis['prob'] if analysis['rec'] == 'FAVORS HOME' else 100 - analysis['prob'], g['yes_price'] if analysis['rec'] == 'FAVORS HOME' else 100 - g['yes_price'], bankroll, kelly_frac)
                st.info(f"📊 **Model predicts {pred_team}** | Edge: {abs(analysis['edge']):.1f}% | Confidence: {analysis['conf']} | If wagering: ${kelly['bet']:.2f} (Kelly {kelly['adj_kelly']}%)")
            
            # 12-Factor Detail
            st.markdown("---")
            st.markdown("**📈 12-Factor Breakdown**")
            f, r = analysis['factors'], analysis['raw']
            
            # Row 1
            fc1, fc2, fc3, fc4 = st.columns(4)
            b2b_h = "⚠️B2B" if r['home_rest'] <= 1 else ""
            b2b_a = "⚠️B2B" if r['away_rest'] <= 1 else ""
            fc1.metric("🛏️ Rest", f"{f['rest']:+.2f}", f"H:{r['home_rest']}d {b2b_h} | A:{r['away_rest']}d {b2b_a}")
            fc2.metric("🏥 Injuries", f"{f['injury']:+.2f}", f"H:{r['home_inj']:.1f} | A:{r['away_inj']:.1f}")
            fc3.metric("🛡️ Defense", f"{f['defense']:+.2f}", f"H:#{r['home_def']} | A:#{r['away_def']}")
            fc4.metric("🏃 Pace", f"{f['pace']:+.2f}", f"H:{r['home_pace']:.1f} | A:{r['away_pace']:.1f}")
            
            # Row 2
            fc5, fc6, fc7, fc8 = st.columns(4)
            fc5.metric("📊 Net Rtg", f"{f['net_rating']:+.2f}", f"H:{r['home_net']:+.1f} | A:{r['away_net']:+.1f}")
            fc6.metric("✈️ Travel", f"{f['travel']:+.2f}", f"{r['travel']} mi")
            fc7.metric("🏠 Splits", f"{f['splits']:+.2f}", f"H:{r['home_pct']:.0%} | A:{r['away_pct']:.0%}")
            fc8.metric("⚔️ Div", f"{f['division']:+.2f}", "Yes" if r['is_division'] else "No")
            
            # Row 3
            fc9, fc10, fc11, fc12 = st.columns(4)
            fc9.metric("👨‍⚖️ Refs", f"{f['refs']:+.2f}", f"Bias:{r['ref_bias']:+.1f}")
            fc10.metric("🎯 FT", f"{f['ft_rate']:+.2f}", f"H:{r['home_ft']:.2f} | A:{r['away_ft']:.2f}")
            fc11.metric("🏀 Reb", f"{f['rebounding']:+.2f}", f"H:{r['home_reb']:.1f}% | A:{r['away_reb']:.1f}%")
            fc12.metric("🎯 3PT", f"{f['three_pt']:+.2f}", f"H:{r['home_3pt']:.1%} | A:{r['away_3pt']:.1%}")

with tab_tot:
    st.subheader("Total Points Predictions")
    
    if not markets['totals']:
        st.warning("No totals data found for today.")
    
    for idx, g in enumerate(markets['totals']):
        home, away, line = g['home'], g['away'], g.get('line', 220)
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        
        combined_ppg = hs.get('ppg', 110) + aws.get('ppg', 110)
        def_adj = ((15 - hs.get('def_rank', 15)) + (15 - aws.get('def_rank', 15))) * 0.3
        projected = combined_ppg - def_adj
        edge = projected - line
        
        rec = "OVER" if edge > 2 else ("UNDER" if edge < -2 else "NO EDGE")
        color = "🟢" if rec == "OVER" else ("🔴" if rec == "UNDER" else "⚪")
        
        with st.expander(f"{color} {g['game_date']} | {away} @ {home} | Line: {line}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi Line", f"{line}")
            c2.metric("Model Projects", f"{projected:.1f}")
            c3.metric("Difference", f"{edge:+.1f} pts")
            
            st.markdown("**Factors:**")
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("📊 Combined PPG", f"{combined_ppg:.1f}")
            tc2.metric("🛡️ Def Adjustment", f"{def_adj:+.1f}")
            tc3.metric("Prediction", f"{color} {rec}")

with tab_spr:
    st.subheader("Spread Predictions")
    
    if not markets['spreads']:
        st.warning("No spread data found for today.")
    
    for idx, g in enumerate(markets['spreads']):
        home, away, line = g['home'], g['away'], g.get('line', 5)
        spread_team = g.get('spread_team', home)
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        
        net_diff = hs.get('net_rating', 0) - aws.get('net_rating', 0)
        predicted = net_diff + 3.5
        edge = predicted - line
        
        rec = "COVERS" if edge > 2 else ("MISSES" if edge < -2 else "NO EDGE")
        color = "🟢" if rec == "COVERS" else ("🔴" if rec == "MISSES" else "⚪")
        
        with st.expander(f"{color} {g['game_date']} | {away} @ {home} | {spread_team} -{line}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi Line", f"{spread_team} -{line}")
            c2.metric("Model Spread", f"{predicted:+.1f}")
            c3.metric("Difference", f"{edge:+.1f} pts")
            
            st.markdown("**Factors:**")
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("📊 Net Rating Diff", f"{net_diff:+.1f}")
            tc2.metric("🏠 Home Court", "+3.5")
            tc3.metric("Prediction", f"{color} {rec}")

st.markdown("---")
st.caption("⚠️ **DISCLAIMER:** This tool provides statistical analysis for educational purposes only. This is NOT financial advice. Predictions are based on historical data and may be incorrect. Past performance does not guarantee future results. If you choose to wager, only use funds you can afford to lose. The creators assume no liability for any decisions made based on this analysis.")
