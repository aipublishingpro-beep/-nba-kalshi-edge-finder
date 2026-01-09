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
    """
    TRULY REALISTIC edge calculation
    
    Key insight: Kalshi prices ARE the market's probability estimate.
    Our model should only find SMALL deviations (2-5%) based on factors
    the market might be slightly mispricing.
    
    We DON'T calculate our own probability from scratch.
    We ADJUST the market price by small amounts.
    """
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    
    if not hs or not aws:
        return {"prob": kalshi_price, "adj_prob": kalshi_price, "raw_edge": 0, "adj_edge": 0, 
                "factors": {}, "raw": {}, "rec": "NO DATA", "conf": "LOW", "haircut": 0}
    
    factors, raw = {}, {}
    
    # ============================================================
    # ADJUSTMENT APPROACH: Start from market, add/subtract small edges
    # Each factor can only contribute ±0.5 to ±1.5% MAX
    # ============================================================
    
    # 1. REST ADVANTAGE (max ±1.5%)
    # Back-to-back vs 3+ days rest is meaningful
    rest_diff = home_rest - away_rest
    if rest_diff >= 2:  # Home well rested, away tired
        factors["rest"] = min(1.5, rest_diff * 0.5) * weights["rest"]
    elif rest_diff <= -2:  # Home tired, away rested
        factors["rest"] = max(-1.5, rest_diff * 0.5) * weights["rest"]
    else:
        factors["rest"] = rest_diff * 0.3 * weights["rest"]
    raw["home_rest"], raw["away_rest"] = home_rest, away_rest
    
    # 2. INJURIES (max ±2%)
    # Star out is significant but market usually prices this in
    inj_diff = away_inj - home_inj  # Positive = away more injured
    factors["injury"] = max(-2, min(2, inj_diff * 0.6)) * weights["injury"]
    raw["home_inj"], raw["away_inj"] = home_inj, away_inj
    
    # 3. TRAVEL FATIGUE (max ±0.5%)
    # Only matters for extreme distances, market mostly prices this
    if travel > 2000:
        factors["travel"] = 0.5 * weights["travel"]
    elif travel > 1500:
        factors["travel"] = 0.3 * weights["travel"]
    else:
        factors["travel"] = 0
    raw["travel"] = travel
    
    # 4. DIVISION GAME (max -0.5%)
    # Division games are tighter, reduces home edge
    is_div = hs.get("division") == aws.get("division")
    factors["division"] = -0.5 * weights["division"] if is_div else 0
    raw["is_division"] = is_div
    
    # ============================================================
    # FACTORS THE MARKET ALREADY PRICES WELL - MINIMAL ADJUSTMENT
    # These are for display only, near-zero weight
    # ============================================================
    
    # Net rating, defense, pace, splits - market knows these
    # Only include for transparency, not for edge calculation
    net_diff = hs.get("net_rating", 0) - aws.get("net_rating", 0)
    factors["net_rating"] = 0  # Market prices this perfectly
    raw["home_net"], raw["away_net"] = hs.get("net_rating", 0), aws.get("net_rating", 0)
    
    def_diff = aws.get("def_rank", 15) - hs.get("def_rank", 15)
    factors["defense"] = 0  # Market prices this perfectly
    raw["home_def"], raw["away_def"] = hs.get("def_rank", 15), aws.get("def_rank", 15)
    
    factors["pace"] = 0
    raw["home_pace"], raw["away_pace"] = hs.get("pace", 100), aws.get("pace", 100)
    
    factors["splits"] = 0
    raw["home_pct"], raw["away_pct"] = hs.get("home_win_pct", 0.5), aws.get("away_win_pct", 0.5)
    
    factors["ft_rate"] = 0
    factors["rebounding"] = 0
    factors["three_pt"] = 0
    
    # ============================================================
    # CALCULATE ADJUSTED PROBABILITY
    # ============================================================
    
    # Sum adjustments (should be small: typically -2% to +3%)
    total_adj = sum(factors.values())
    
    # HARD CAP: Never adjust more than ±4% from market
    total_adj = max(-4, min(4, total_adj))
    
    # Raw model probability = market + adjustments
    raw_prob = kalshi_price + total_adj
    raw_prob = max(20, min(80, raw_prob))
    
    # HAIRCUT: Assume we're probably wrong, regress toward market
    # Apply 40% haircut on any edge we think we found
    haircut_pct = 40
    if total_adj > 0:
        adj_prob = kalshi_price + (total_adj * (100 - haircut_pct) / 100)
    else:
        adj_prob = kalshi_price + (total_adj * (100 - haircut_pct) / 100)
    
    adj_prob = max(20, min(80, adj_prob))
    
    # Calculate edges
    raw_edge = raw_prob - kalshi_price  # Before haircut
    adj_edge = adj_prob - kalshi_price  # After haircut
    
    # ============================================================
    # RECOMMENDATIONS - VERY CONSERVATIVE
    # ============================================================
    
    if abs(adj_edge) < 1.5:
        rec, conf = "NO EDGE", "LOW"
    elif abs(adj_edge) < 2.5:
        rec = "SLIGHT HOME" if adj_edge > 0 else "SLIGHT AWAY"
        conf = "LOW"
    elif abs(adj_edge) < 3.5:
        rec = "LEAN HOME" if adj_edge > 0 else "LEAN AWAY"
        conf = "MED"
    else:
        rec = "EDGE HOME" if adj_edge > 0 else "EDGE AWAY"
        conf = "MED"
    
    return {
        "prob": raw_prob, 
        "adj_prob": adj_prob, 
        "raw_edge": raw_edge, 
        "adj_edge": adj_edge,
        "factors": factors, 
        "raw": raw, 
        "rec": rec, 
        "conf": conf, 
        "haircut": haircut_pct,
        "total_adj": total_adj
    }

def calculate_kelly(win_prob, price, bankroll, fraction):
    p = win_prob / 100
    b = (100 - price) / price if price > 0 else 1
    kelly = max(0, (p * b - (1 - p)) / b) if b > 0 else 0
    adj_kelly = kelly * fraction
    return {"kelly": round(kelly * 100, 2), "adj_kelly": round(adj_kelly * 100, 2), "bet": round(bankroll * adj_kelly, 2)}

# ========== UI ==========
st.title("🏀 NBA Edge Finder")
st.caption("Realistic Model • Market-Adjusted • Small Edges Only")

clicked_game = st.query_params.get("game", None)
if clicked_game:
    components.html(f'''<script>setTimeout(function(){{var el=window.parent.document.getElementById("game-{clicked_game}");if(el)el.scrollIntoView({{behavior:"smooth",block:"start"}})}},500)</script>''', height=0)

st.markdown("""
<style>
    .prediction-banner {background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(34, 197, 94, 0.05) 100%);
        border-left: 4px solid #22c55e; border-radius: 8px; padding: 16px 20px; margin: 10px 0;}
    .prediction-banner:hover {transform: scale(1.01); box-shadow: 0 4px 20px rgba(34, 197, 94, 0.2);}
    .prediction-team {font-size: 1.4rem; font-weight: 700; color: #FAFAFA;}
    .prediction-edge {font-size: 1.6rem; font-weight: 800; color: #22c55e;}
    .prediction-details {color: rgba(250, 250, 250, 0.7); font-size: 0.85rem; margin-top: 4px;}
    .no-edge-banner {background: rgba(100, 100, 100, 0.1); border-left: 4px solid #666; border-radius: 8px; padding: 12px 16px; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Model Settings")

st.sidebar.markdown("**Philosophy**")
st.sidebar.caption("Market prices are ~95% accurate. We only find small edges from situational factors the market might underweight.")

with st.sidebar.expander("🎚️ Situational Weights", expanded=False):
    st.caption("Only factors that might be slightly mispriced")
    w_rest = st.slider("Rest Days", 0.0, 2.0, 1.0, 0.1, key="w1", help="Back-to-back situations")
    w_inj = st.slider("Injury News", 0.0, 2.0, 1.0, 0.1, key="w3", help="GTD/Out announcements")
    w_travel = st.slider("Travel", 0.0, 2.0, 1.0, 0.1, key="w6", help="Cross-country trips")
    w_div = st.slider("Division", 0.0, 2.0, 1.0, 0.1, key="w8", help="Division rivalry games")

# Disabled weights (market prices these accurately)
weights = {
    "rest": w_rest, 
    "injury": w_inj, 
    "travel": w_travel, 
    "division": w_div,
    # These are set to 0 in calculate_edge anyway
    "defense": 0, "pace": 0, "net_rating": 0, "splits": 0,
    "ft_rate": 0, "rebounding": 0, "three_pt": 0
}

st.sidebar.markdown("---")
st.sidebar.markdown("**Edge Thresholds**")
st.sidebar.write("• <1.5% = No edge")
st.sidebar.write("• 1.5-2.5% = Slight")
st.sidebar.write("• 2.5-3.5% = Lean")
st.sidebar.write("• 3.5%+ = Edge (rare)")

st.sidebar.markdown("---")
st.sidebar.markdown("**Haircut: 40%**")
st.sidebar.caption("We assume we're probably wrong and regress edges toward market")

with st.sidebar.expander("💰 Position Sizing"):
    bankroll = st.number_input("Bankroll ($)", 100, 100000, 1000)
    kelly_frac = st.slider("Kelly Fraction", 0.1, 0.5, 0.15, 0.05)

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
st.subheader("🎯 Today's Edges")

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
    
    pred_team = home if analysis['adj_edge'] > 0 else away
    all_edges.append({
        "game": key, "pred": pred_team, "adj_edge": analysis['adj_edge'],
        "raw_edge": analysis['raw_edge'], "rec": analysis['rec'], "conf": analysis['conf'],
        "date": g['game_date'], "market": g['yes_price']
    })

all_edges.sort(key=lambda x: abs(x['adj_edge']), reverse=True)

# Show top 3 (or message if no edges)
has_edge = [e for e in all_edges if abs(e['adj_edge']) >= 1.5]

if has_edge[:3]:
    cols = st.columns(3)
    for i, e in enumerate(has_edge[:3]):
        with cols[i]:
            game_encoded = e['game'].replace(' ', '_').replace('@', 'at')
            is_real_edge = abs(e['adj_edge']) >= 2.5
            
            if is_real_edge:
                st.markdown(f'''
                <a href="?game={game_encoded}" style="text-decoration:none;">
                    <div class="prediction-banner" style="cursor:pointer;">
                        <span class="prediction-team">{e["pred"]}</span><br>
                        <span class="prediction-edge">+{abs(e["adj_edge"]):.1f}%</span>
                        <div class="prediction-details">{e["date"]} • {e["game"]}</div>
                        <div style="font-size:0.75rem; color:#888; margin-top:4px;">{e["rec"]} • Market: {e["market"]:.0f}%</div>
                    </div>
                </a>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <a href="?game={game_encoded}" style="text-decoration:none;">
                    <div class="no-edge-banner" style="cursor:pointer;">
                        <span style="font-size:1.2rem; color:#aaa;">{e["pred"]}</span><br>
                        <span style="font-size:1.3rem; color:#888;">+{abs(e["adj_edge"]):.1f}%</span>
                        <div class="prediction-details">{e["date"]} • {e["game"]}</div>
                        <div style="font-size:0.75rem; color:#666; margin-top:4px;">Slight lean • Market: {e["market"]:.0f}%</div>
                    </div>
                </a>
                ''', unsafe_allow_html=True)
else:
    st.info("✅ No actionable edges today. Market is efficient. This is normal - pass most games.")

st.caption("💡 Realistic edges are 2-4%. If any model shows 10%+, it's broken.")

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
        
        if abs(analysis['adj_edge']) >= 2.5:
            indicator = "🟢"
        elif abs(analysis['adj_edge']) >= 1.5:
            indicator = "🟡"
        else:
            indicator = "⚪"
        
        game_encoded = key.replace(' ', '_').replace('@', 'at')
        should_expand = (clicked_game == game_encoded)
        
        st.markdown(f'<div id="game-{game_encoded}" style="scroll-margin-top:100px;"></div>', unsafe_allow_html=True)
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | Edge: {analysis['adj_edge']:+.1f}% | {analysis['rec']}", expanded=should_expand):
            
            st.caption(f"Market: {home} {g['yes_price']:.0f}% to win")
            
            ic1, ic2 = st.columns(2)
            with ic1:
                home_inj = st.select_slider(f"🏥 {home}", [0,1,2,3], 0, format_func=lambda x: ["Full","Minor","Star GTD","Star OUT"][x], key=f"ml_h_{idx}")
            with ic2:
                away_inj = st.select_slider(f"🏥 {away}", [0,1,2,3], 0, format_func=lambda x: ["Full","Minor","Star GTD","Star OUT"][x], key=f"ml_a_{idx}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.0, 3: 3.0}
            analysis = calculate_edge(home, away, g['yes_price'], h_rest, a_rest, inj_map[home_inj], inj_map[away_inj], travel, weights)
            
            # Results - cleaner display
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market", f"{g['yes_price']:.0f}%", help=f"{home} win probability per Kalshi")
            c2.metric("Adjustment", f"{analysis['total_adj']:+.1f}%", help="Our situational adjustment")
            c3.metric("After Haircut", f"{analysis['adj_edge']:+.1f}%", help="40% haircut applied")
            c4.metric("Final Edge", f"{analysis['adj_edge']:+.1f}%")
            
            if analysis['rec'] not in ["NO EDGE", "NO DATA"]:
                pred_team = home if analysis['adj_edge'] > 0 else away
                kelly = calculate_kelly(
                    analysis['adj_prob'] if analysis['adj_edge'] > 0 else 100 - analysis['adj_prob'], 
                    g['yes_price'] if analysis['adj_edge'] > 0 else 100 - g['yes_price'], 
                    bankroll, kelly_frac
                )
                
                edge_strength = "Small edge" if abs(analysis['adj_edge']) < 3 else "Decent edge"
                
                st.success(f"**{analysis['rec']}**: {pred_team} • {edge_strength} of {abs(analysis['adj_edge']):.1f}%")
                
                if kelly['bet'] > 0:
                    st.caption(f"Kelly suggests: ${kelly['bet']:.2f} ({kelly['adj_kelly']:.1f}% of bankroll)")
            else:
                st.info(f"No actionable edge. Market looks efficient here.")
            
            with st.expander("📊 Factor Breakdown"):
                st.write(f"**Rest**: Home {h_rest}d, Away {a_rest}d → {analysis['factors'].get('rest', 0):+.2f}%")
                st.write(f"**Injury**: Home {home_inj}, Away {away_inj} → {analysis['factors'].get('injury', 0):+.2f}%")
                st.write(f"**Travel**: {travel} mi → {analysis['factors'].get('travel', 0):+.2f}%")
                st.write(f"**Division**: {analysis['raw'].get('is_division', False)} → {analysis['factors'].get('division', 0):+.2f}%")
                st.markdown("---")
                st.write(f"**Total Adj**: {analysis['total_adj']:+.2f}%")
                st.write(f"**After 40% Haircut**: {analysis['adj_edge']:+.2f}%")

with tab_tot:
    st.subheader("Total Points")
    st.caption("Market prices totals efficiently. Edges are rare.")
    
    seen_tot = set()
    for g in markets['totals']:
        home, away, line = g['home'], g['away'], g.get('line', 220)
        key = f"{away} @ {home}"
        if key in seen_tot:
            continue
        seen_tot.add(key)
        
        # Simple projection - acknowledge market is usually right
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        combined_ppg = (hs.get('ppg', 110) + aws.get('ppg', 110)) / 2
        pace_factor = ((hs.get('pace', 100) + aws.get('pace', 100)) / 2 - 100) * 0.5
        projected = combined_ppg + pace_factor
        
        raw_diff = projected - line
        # Heavy haircut - market prices totals well
        adj_edge = raw_diff * 0.3
        
        indicator = "🟢" if abs(adj_edge) > 2 else "⚪"
        rec = "LEAN OVER" if adj_edge > 2 else ("LEAN UNDER" if adj_edge < -2 else "NO EDGE")
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | O/U {line} | {adj_edge:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Line", f"{line}")
            c2.metric("Est. Total", f"{projected:.0f}")
            c3.metric("Edge", f"{adj_edge:+.1f}%")
            
            if abs(adj_edge) < 2:
                st.info("Market looks efficient")

with tab_spr:
    st.subheader("Spreads")
    st.caption("Market prices spreads efficiently. Edges are rare.")
    
    seen_spr = set()
    for g in markets['spreads']:
        home, away, line = g['home'], g['away'], g.get('line', 5)
        key = f"{away} @ {home}"
        if key in seen_spr:
            continue
        seen_spr.add(key)
        
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        net_diff = hs.get('net_rating', 0) - aws.get('net_rating', 0)
        # Home court ~2.5 points
        predicted_margin = net_diff * 0.5 + 2.5
        
        raw_diff = predicted_margin - line
        adj_edge = raw_diff * 0.3  # Heavy haircut
        
        indicator = "🟢" if abs(adj_edge) > 2 else "⚪"
        
        with st.expander(f"{indicator} {g['game_date']} | {away} @ {home} | {g.get('spread_team', home)} -{line} | {adj_edge:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Line", f"-{line}")
            c2.metric("Model", f"{predicted_margin:+.1f}")
            c3.metric("Edge", f"{adj_edge:+.1f}%")

st.markdown("---")
st.caption("⚠️ **Realistic edges are 2-4%.** Markets are efficient. Pass 90% of games. If you see 10%+ edges, the model is wrong.")
