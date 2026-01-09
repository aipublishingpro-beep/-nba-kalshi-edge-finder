import streamlit as st
import requests
from datetime import datetime
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="basketball", layout="wide")

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
    "Chicago": {"net_rating": -3.5, "off_rating": 111.2, "def_rating": 114.7, "def_rank": 20, "pace": 98.2, "ppg": 111.5, "opp_ppg": 115.0, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 50.0},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.5, "def_rating": 108.7, "def_rank": 3, "pace": 97.5, "ppg": 118.2, "opp_ppg": 108.4, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 53.2},
    "Dallas": {"net_rating": 3.2, "off_rating": 115.8, "def_rating": 112.6, "def_rank": 12, "pace": 99.5, "ppg": 117.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.365, "ft_rate": 0.26, "reb_rate": 50.8},
    "Denver": {"net_rating": 5.5, "off_rating": 117.2, "def_rating": 111.7, "def_rank": 8, "pace": 98.8, "ppg": 115.5, "opp_ppg": 110.0, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 52.0},
    "Detroit": {"net_rating": -4.8, "off_rating": 110.5, "def_rating": 115.3, "def_rank": 24, "pace": 100.5, "ppg": 110.2, "opp_ppg": 115.0, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pct": 0.340, "ft_rate": 0.23, "reb_rate": 49.5},
    "Golden State": {"net_rating": 2.8, "off_rating": 114.5, "def_rating": 111.7, "def_rank": 14, "pace": 99.2, "ppg": 114.8, "opp_ppg": 112.0, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.378, "ft_rate": 0.24, "reb_rate": 49.8},
    "Houston": {"net_rating": 4.5, "off_rating": 113.8, "def_rating": 109.3, "def_rank": 6, "pace": 99.8, "ppg": 114.5, "opp_ppg": 110.0, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.28, "reb_rate": 52.8},
    "Indiana": {"net_rating": 1.2, "off_rating": 118.5, "def_rating": 117.3, "def_rank": 18, "pace": 102.5, "ppg": 123.2, "opp_ppg": 121.0, "home_win_pct": 0.55, "away_win_pct": 0.42, "division": "Central", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 50.5},
    "LA Clippers": {"net_rating": 0.8, "off_rating": 112.2, "def_rating": 111.4, "def_rank": 15, "pace": 98.5, "ppg": 110.5, "opp_ppg": 109.7, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 50.2},
    "LA Lakers": {"net_rating": 2.5, "off_rating": 114.8, "def_rating": 112.3, "def_rank": 13, "pace": 99.0, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.60, "away_win_pct": 0.45, "division": "Pacific", "three_pct": 0.352, "ft_rate": 0.26, "reb_rate": 51.5},
    "Memphis": {"net_rating": 3.8, "off_rating": 115.5, "def_rating": 111.7, "def_rank": 10, "pace": 100.8, "ppg": 117.8, "opp_ppg": 113.0, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.27, "reb_rate": 53.0},
    "Miami": {"net_rating": -1.2, "off_rating": 110.5, "def_rating": 111.7, "def_rank": 16, "pace": 97.8, "ppg": 108.5, "opp_ppg": 109.7, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 50.0},
    "Milwaukee": {"net_rating": 4.2, "off_rating": 116.5, "def_rating": 112.3, "def_rank": 11, "pace": 98.2, "ppg": 115.8, "opp_ppg": 111.6, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Central", "three_pct": 0.362, "ft_rate": 0.28, "reb_rate": 52.2},
    "Minnesota": {"net_rating": 6.5, "off_rating": 112.8, "def_rating": 106.3, "def_rank": 4, "pace": 97.2, "ppg": 110.5, "opp_ppg": 104.0, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Northwest", "three_pct": 0.355, "ft_rate": 0.26, "reb_rate": 53.5},
    "New Orleans": {"net_rating": -2.5, "off_rating": 111.8, "def_rating": 114.3, "def_rank": 19, "pace": 99.5, "ppg": 112.0, "opp_ppg": 114.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.27, "reb_rate": 51.0},
    "New York": {"net_rating": 5.8, "off_rating": 117.2, "def_rating": 111.4, "def_rank": 7, "pace": 98.8, "ppg": 118.5, "opp_ppg": 112.7, "home_win_pct": 0.70, "away_win_pct": 0.55, "division": "Atlantic", "three_pct": 0.368, "ft_rate": 0.26, "reb_rate": 51.8},
    "Oklahoma City": {"net_rating": 11.2, "off_rating": 118.8, "def_rating": 107.6, "def_rank": 1, "pace": 99.5, "ppg": 120.2, "opp_ppg": 109.0, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 52.0},
    "Orlando": {"net_rating": 4.8, "off_rating": 110.2, "def_rating": 105.4, "def_rank": 5, "pace": 97.5, "ppg": 108.5, "opp_ppg": 103.7, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Southeast", "three_pct": 0.342, "ft_rate": 0.25, "reb_rate": 52.5},
    "Philadelphia": {"net_rating": -0.5, "off_rating": 112.5, "def_rating": 113.0, "def_rank": 17, "pace": 98.0, "ppg": 111.2, "opp_ppg": 111.7, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Atlantic", "three_pct": 0.358, "ft_rate": 0.28, "reb_rate": 50.8},
    "Phoenix": {"net_rating": 1.5, "off_rating": 114.2, "def_rating": 112.7, "def_rank": 14, "pace": 98.5, "ppg": 113.8, "opp_ppg": 112.3, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.365, "ft_rate": 0.25, "reb_rate": 50.5},
    "Portland": {"net_rating": -8.5, "off_rating": 107.8, "def_rating": 116.3, "def_rank": 28, "pace": 99.2, "ppg": 105.5, "opp_ppg": 114.0, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.332, "ft_rate": 0.22, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.8, "off_rating": 113.5, "def_rating": 115.3, "def_rank": 21, "pace": 100.2, "ppg": 114.8, "opp_ppg": 116.6, "home_win_pct": 0.50, "away_win_pct": 0.35, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -6.2, "off_rating": 110.8, "def_rating": 117.0, "def_rank": 26, "pace": 100.5, "ppg": 110.5, "opp_ppg": 116.7, "home_win_pct": 0.38, "away_win_pct": 0.25, "division": "Southwest", "three_pct": 0.338, "ft_rate": 0.24, "reb_rate": 50.2},
    "Toronto": {"net_rating": -5.8, "off_rating": 111.2, "def_rating": 117.0, "def_rank": 23, "pace": 99.8, "ppg": 110.8, "opp_ppg": 116.6, "home_win_pct": 0.40, "away_win_pct": 0.25, "division": "Atlantic", "three_pct": 0.342, "ft_rate": 0.23, "reb_rate": 49.0},
    "Utah": {"net_rating": -9.2, "off_rating": 108.5, "def_rating": 117.7, "def_rank": 29, "pace": 100.8, "ppg": 108.2, "opp_ppg": 117.4, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Northwest", "three_pct": 0.328, "ft_rate": 0.22, "reb_rate": 48.2},
    "Washington": {"net_rating": -10.5, "off_rating": 107.2, "def_rating": 117.7, "def_rank": 30, "pace": 101.2, "ppg": 106.5, "opp_ppg": 117.0, "home_win_pct": 0.22, "away_win_pct": 0.12, "division": "Southeast", "three_pct": 0.325, "ft_rate": 0.21, "reb_rate": 47.8},
}

TEAM_LOCATIONS = {
    "Atlanta": {"lat": 33.757, "lon": -84.396}, "Boston": {"lat": 42.366, "lon": -71.062},
    "Brooklyn": {"lat": 40.683, "lon": -73.976}, "Charlotte": {"lat": 35.225, "lon": -80.839},
    "Chicago": {"lat": 41.881, "lon": -87.674}, "Cleveland": {"lat": 41.497, "lon": -81.688},
    "Dallas": {"lat": 32.790, "lon": -96.810}, "Denver": {"lat": 39.749, "lon": -105.008},
    "Detroit": {"lat": 42.341, "lon": -83.055}, "Golden State": {"lat": 37.768, "lon": -122.388},
    "Houston": {"lat": 29.751, "lon": -95.362}, "Indiana": {"lat": 39.764, "lon": -86.156},
    "LA Clippers": {"lat": 34.043, "lon": -118.267}, "LA Lakers": {"lat": 34.043, "lon": -118.267},
    "Memphis": {"lat": 35.138, "lon": -90.051}, "Miami": {"lat": 25.781, "lon": -80.188},
    "Milwaukee": {"lat": 43.045, "lon": -87.917}, "Minnesota": {"lat": 44.980, "lon": -93.276},
    "New Orleans": {"lat": 29.949, "lon": -90.082}, "New York": {"lat": 40.751, "lon": -73.994},
    "Oklahoma City": {"lat": 35.463, "lon": -97.515}, "Orlando": {"lat": 28.539, "lon": -81.384},
    "Philadelphia": {"lat": 39.901, "lon": -75.172}, "Phoenix": {"lat": 33.446, "lon": -112.071},
    "Portland": {"lat": 45.532, "lon": -122.667}, "Sacramento": {"lat": 38.580, "lon": -121.500},
    "San Antonio": {"lat": 29.427, "lon": -98.438}, "Toronto": {"lat": 43.643, "lon": -79.379},
    "Utah": {"lat": 40.768, "lon": -111.901}, "Washington": {"lat": 38.898, "lon": -77.021},
}

# ========== HELPER FUNCTIONS ==========
def calculate_distance(team1, team2):
    loc1 = TEAM_LOCATIONS.get(team1, {"lat": 0, "lon": 0})
    loc2 = TEAM_LOCATIONS.get(team2, {"lat": 0, "lon": 0})
    lat1, lon1 = math.radians(loc1["lat"]), math.radians(loc1["lon"])
    lat2, lon2 = math.radians(loc2["lat"]), math.radians(loc2["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 3959 * 2 * math.asin(math.sqrt(a))

def calculate_kelly(win_prob, price, bankroll, fraction):
    if price <= 0 or price >= 100:
        return {"bet_amount": 0, "kelly_pct": 0}
    decimal_odds = 100 / price
    q = 1 - (win_prob / 100)
    p = win_prob / 100
    kelly = (p * decimal_odds - 1) / (decimal_odds - 1) if decimal_odds > 1 else 0
    kelly = max(0, kelly) * fraction
    return {"bet_amount": round(bankroll * kelly, 2), "kelly_pct": round(kelly * 100, 2)}

@st.cache_data(ttl=300)
def fetch_kalshi_markets():
    markets = {"moneyline": [], "totals": [], "spreads": []}
    try:
        # Moneyline
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open", timeout=10)
        if resp.status_code == 200:
            for m in resp.json().get("markets", []):
                ticker = m.get("ticker", "")
                if "KXNBAGAME" in ticker:
                    markets["moneyline"].append({
                        "ticker": ticker,
                        "title": m.get("title", ""),
                        "yes_price": m.get("yes_ask", 50),
                        "no_price": m.get("no_ask", 50),
                    })
        # Totals
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open", timeout=10)
        if resp.status_code == 200:
            for m in resp.json().get("markets", []):
                markets["totals"].append({
                    "ticker": m.get("ticker", ""),
                    "title": m.get("title", ""),
                    "line": m.get("floor_strike", 220),
                    "yes_price": m.get("yes_ask", 50),
                })
        # Spreads
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open", timeout=10)
        if resp.status_code == 200:
            for m in resp.json().get("markets", []):
                markets["spreads"].append({
                    "ticker": m.get("ticker", ""),
                    "title": m.get("title", ""),
                    "yes_price": m.get("yes_ask", 50),
                })
    except:
        pass
    return markets

def calculate_edge(home, away, kalshi_price, home_rest, away_rest, home_inj, away_inj, travel, ref_bias, weights):
    home_stats = TEAM_STATS.get(home, TEAM_STATS["Atlanta"])
    away_stats = TEAM_STATS.get(away, TEAM_STATS["Atlanta"])
    
    # Base probability from net rating
    net_diff = home_stats["net_rating"] - away_stats["net_rating"]
    base_prob = 50 + (net_diff * 2.5 * weights["net_rating"])
    
    # Apply factors
    base_prob += (home_rest - away_rest) * 2 * weights["rest"]
    base_prob += (30 - home_stats["def_rank"]) * 0.3 * weights["defense"]
    base_prob += (away_inj - home_inj) * 3 * weights["injuries"]
    base_prob += (home_stats["pace"] - away_stats["pace"]) * 0.2 * weights["pace"]
    base_prob -= min(travel / 500, 5) * weights["travel"]
    base_prob += (home_stats["home_win_pct"] - away_stats["away_win_pct"]) * 15 * weights["splits"]
    base_prob += 3 if home_stats["division"] == away_stats["division"] else 0
    base_prob += ref_bias * weights["refs"]
    base_prob += (home_stats["ft_rate"] - away_stats["ft_rate"]) * 20 * weights["ft_rate"]
    base_prob += (home_stats["reb_rate"] - away_stats["reb_rate"]) * 0.5 * weights["rebounding"]
    base_prob += (home_stats["three_pct"] - away_stats["three_pct"]) * 100 * weights["three_pct"]
    
    base_prob = max(5, min(95, base_prob))
    edge = base_prob - kalshi_price
    
    return {
        "home_win_prob": round(base_prob, 1),
        "edge": round(edge, 1),
        "recommendation": "BUY YES" if edge > 5 else "BUY NO" if edge < -5 else "NO EDGE",
        "confidence": "HIGH" if abs(edge) > 10 else "MEDIUM" if abs(edge) > 5 else "LOW"
    }

# ========== SIDEBAR - 12 SAUCES ==========
st.sidebar.title("Settings")
st.sidebar.markdown("### Color Key")
st.sidebar.markdown("GREEN = BUY YES")
st.sidebar.markdown("RED = BUY NO")
st.sidebar.markdown("---")

st.sidebar.markdown("### Core Factors")
w_rest = st.sidebar.slider("Rest Days", 0.0, 2.0, 1.0, 0.1, key="w1", help="Days since last game. Back-to-backs (0-1 days) hurt performance. 2+ days rest = fresh legs.")
w_def = st.sidebar.slider("Defense Rating", 0.0, 2.0, 1.0, 0.1, key="w2", help="Defensive efficiency ranking (1-30). Elite defenses (#1-5) force bad shots. Poor defenses (#25-30) give up easy buckets.")
w_inj = st.sidebar.slider("Injuries", 0.0, 2.0, 1.0, 0.1, key="w3", help="Count of injured players per team. Star injuries hurt more than bench players. More injuries = weaker team.")
w_pace = st.sidebar.slider("Pace", 0.0, 2.0, 1.0, 0.1, key="w4", help="Possessions per game. Fast teams (100+) push tempo. Slow teams (96-98) grind it out. Pace mismatches create edges.")
w_net = st.sidebar.slider("Net Rating", 0.0, 2.0, 1.0, 0.1, key="w5", help="Points scored minus points allowed per 100 possessions. THE core quality metric. +10 = elite, 0 = average, -10 = tanking.")
w_travel = st.sidebar.slider("Travel Distance", 0.0, 2.0, 1.0, 0.1, key="w6", help="Miles traveled by away team. Long flights (1500+ mi) cause fatigue. Cross-country + time zones = sluggish starts.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Advanced Factors")
w_splits = st.sidebar.slider("Home/Away Splits", 0.0, 2.0, 1.0, 0.1, key="w7", help="Home vs away win percentages. Some teams dominate at home but struggle on road. Big splits = exploit matchups.")
w_div = st.sidebar.slider("Divisional Rivalry", 0.0, 2.0, 1.0, 0.1, key="w8", help="Same-division matchups are more competitive. Teams know each other. Rivalries = extra intensity.")
w_refs = st.sidebar.slider("Ref Bias (Home)", 0.0, 2.0, 1.0, 0.1, key="w9", help="Home teams get ~2 more FTA/game on average. Some ref crews favor home crowds more.")
w_ft = st.sidebar.slider("Free Throw Rate", 0.0, 2.0, 1.0, 0.1, key="w10", help="Free throw attempts per field goal attempt. Teams that attack the rim get to the line more. Free points = easy offense.")
w_reb = st.sidebar.slider("Rebounding", 0.0, 2.0, 1.0, 0.1, key="w11", help="Total rebound rate. Offensive rebounds = second-chance points. Defensive rebounds = end opponent possessions.")
w_three = st.sidebar.slider("Three-Point Pct", 0.0, 2.0, 1.0, 0.1, key="w12", help="Three-point shooting percentage. Teams shooting 38%+ from three are dangerous. Volume + accuracy = blowouts.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Kelly Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", value=1000, min_value=100, step=100)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05, help="Fraction of Kelly to bet. Full Kelly (1.0) is aggressive. Quarter Kelly (0.25) is conservative.")
min_edge = st.sidebar.slider("Min Edge %", 0.0, 20.0, 5.0, 0.5, help="Minimum edge to show a bet. Higher = fewer but stronger bets.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Game Settings")
default_home_rest = st.sidebar.number_input("Default Home Rest", value=2, min_value=0, max_value=7)
default_away_rest = st.sidebar.number_input("Default Away Rest", value=2, min_value=0, max_value=7)
default_ref_bias = st.sidebar.slider("Default Ref Bias", 0.0, 5.0, 2.0, 0.5)

weights = {
    "rest": w_rest, "defense": w_def, "injuries": w_inj, "pace": w_pace,
    "net_rating": w_net, "travel": w_travel, "splits": w_splits, "divisional": w_div,
    "refs": w_refs, "ft_rate": w_ft, "rebounding": w_reb, "three_pct": w_three
}

# ========== MAIN CONTENT ==========
st.title("NBA Kalshi Edge Finder")
st.write("**12 Factors - Hover over sliders for explanations**")

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()

markets = fetch_kalshi_markets()

st.markdown(f"**Markets Found:** ML: {len(markets['moneyline'])} | TOT: {len(markets['totals'])} | SPR: {len(markets['spreads'])}")

# ========== TOP 3 EDGES ==========
def parse_teams_from_title(title):
    """Extract home and away teams from Kalshi title"""
    # Kalshi titles like "Boston Celtics vs Atlanta Hawks" or similar
    for team in TEAM_STATS.keys():
        if team in title:
            return team
    return None

def build_kalshi_url(market_type, ticker):
    """Build correct Kalshi URL from ticker"""
    ticker_lower = ticker.lower()
    if market_type == "ML":
        return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker_lower}"
    elif market_type == "TOT":
        return f"https://kalshi.com/markets/kxnbatotal/professional-basketball-total/{ticker_lower}"
    elif market_type == "SPR":
        return f"https://kalshi.com/markets/kxnbaspread/professional-basketball-spread/{ticker_lower}"
    return "#"

# Collect all edges
top_edges = []

for game in markets["moneyline"]:
    title = game["title"]
    yes_price = game["yes_price"]
    ticker = game["ticker"]
    
    # Try to parse teams - simplified for now
    home_team = "Boston"  # Default - would need better parsing
    away_team = "Atlanta"
    
    for team in TEAM_STATS.keys():
        if team.lower() in title.lower():
            if home_team == "Boston":
                home_team = team
            else:
                away_team = team
                break
    
    travel = calculate_distance(away_team, home_team)
    analysis = calculate_edge(home_team, away_team, yes_price, default_home_rest, default_away_rest, 0, 0, travel, default_ref_bias, weights)
    
    if abs(analysis["edge"]) >= min_edge:
        bet_team = home_team if analysis["recommendation"] == "BUY YES" else away_team
        kelly = calculate_kelly(
            analysis["home_win_prob"] if analysis["recommendation"] == "BUY YES" else 100 - analysis["home_win_prob"],
            yes_price if analysis["recommendation"] == "BUY YES" else 100 - yes_price,
            bankroll, kelly_fraction
        )
        top_edges.append({
            "type": "ML",
            "title": title,
            "ticker": ticker,
            "edge": abs(analysis["edge"]),
            "rec": analysis["recommendation"],
            "bet_team": bet_team,
            "bet_amount": kelly["bet_amount"],
            "url": build_kalshi_url("ML", ticker),
            "is_yes": analysis["recommendation"] == "BUY YES"
        })

for game in markets["totals"]:
    title = game["title"]
    line = game.get("line", 220)
    yes_price = game["yes_price"]
    ticker = game["ticker"]
    
    # Simple totals edge calc
    edge = 50 - yes_price  # Simplified
    if abs(edge) >= min_edge:
        direction = "OVER" if edge > 0 else "UNDER"
        kelly = calculate_kelly(50 + abs(edge), yes_price if edge > 0 else 100 - yes_price, bankroll, kelly_fraction)
        top_edges.append({
            "type": "TOT",
            "title": title,
            "ticker": ticker,
            "edge": abs(edge),
            "rec": f"BUY {direction}",
            "bet_team": f"{direction} {line}",
            "bet_amount": kelly["bet_amount"],
            "url": build_kalshi_url("TOT", ticker),
            "is_yes": edge > 0
        })

for game in markets["spreads"]:
    title = game["title"]
    yes_price = game["yes_price"]
    ticker = game["ticker"]
    
    edge = 50 - yes_price
    if abs(edge) >= min_edge:
        kelly = calculate_kelly(50 + abs(edge), yes_price if edge > 0 else 100 - yes_price, bankroll, kelly_fraction)
        top_edges.append({
            "type": "SPR",
            "title": title,
            "ticker": ticker,
            "edge": abs(edge),
            "rec": "BUY YES" if edge > 0 else "BUY NO",
            "bet_team": "COVERS" if edge > 0 else "FAILS TO COVER",
            "bet_amount": kelly["bet_amount"],
            "url": build_kalshi_url("SPR", ticker),
            "is_yes": edge > 0
        })

# Sort by edge and show top 3
top_edges.sort(key=lambda x: x["edge"], reverse=True)

st.markdown("---")
st.subheader("TOP 3 EDGES TODAY")

if top_edges:
    for i, edge in enumerate(top_edges[:3]):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        # Color based on YES/NO
        if edge["is_yes"]:
            indicator = "🟢"
            color = "green"
        else:
            indicator = "🔴"
            color = "red"
        
        with col1:
            st.markdown(f"**#{i+1} {indicator} [{edge['type']}]** {edge['title']}")
            st.markdown(f":{color}[**{edge['rec']}**] - {edge['bet_team']}")
        
        with col2:
            st.metric("Edge", f"+{edge['edge']:.1f}%")
        
        with col3:
            st.link_button(
                f"BET {edge['bet_team']} ${edge['bet_amount']:.0f}",
                edge["url"],
                use_container_width=True
            )
else:
    st.info("No edges found above minimum threshold. Try lowering Min Edge % in sidebar.")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Moneyline", "Totals", "Spreads"])

with tab1:
    st.subheader("Moneyline Markets")
    for game in markets["moneyline"][:10]:
        title = game["title"]
        yes_price = game["yes_price"]
        ticker = game["ticker"]
        
        with st.expander(f"{title} | Kalshi: {yes_price}c"):
            col1, col2 = st.columns(2)
            with col1:
                home_inj = st.number_input("Home Injuries", 0, 5, 0, key=f"hinj_{ticker}")
                away_inj = st.number_input("Away Injuries", 0, 5, 0, key=f"ainj_{ticker}")
            
            analysis = calculate_edge("Boston", "Atlanta", yes_price, default_home_rest, default_away_rest, home_inj, away_inj, 1000, default_ref_bias, weights)
            
            with col2:
                st.metric("Model Prob", f"{analysis['home_win_prob']}%")
                st.metric("Edge", f"{analysis['edge']}%")
            
            if analysis["recommendation"] != "NO EDGE":
                kelly = calculate_kelly(analysis["home_win_prob"], yes_price, bankroll, kelly_fraction)
                color = "green" if analysis["recommendation"] == "BUY YES" else "red"
                st.markdown(f":{color}[**{analysis['recommendation']}**] - Bet ${kelly['bet_amount']}")
                url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker.lower()}"
                st.link_button(f"BET on Kalshi", url)

with tab2:
    st.subheader("Totals (Over/Under)")
    for game in markets["totals"][:10]:
        with st.expander(f"{game['title']} | Line: {game['line']} | Price: {game['yes_price']}c"):
            st.write("Analysis coming soon")
            url = f"https://kalshi.com/markets/kxnbatotal/{game['ticker'].lower()}"
            st.link_button("View on Kalshi", url)

with tab3:
    st.subheader("Spreads")
    for game in markets["spreads"][:10]:
        with st.expander(f"{game['title']} | Price: {game['yes_price']}c"):
            st.write("Analysis coming soon")
            url = f"https://kalshi.com/markets/kxnbaspread/{game['ticker'].lower()}"
            st.link_button("View on Kalshi", url)

st.markdown("---")
st.caption("For entertainment only. Not financial advice.")
