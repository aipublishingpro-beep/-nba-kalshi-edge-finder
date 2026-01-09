import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

# Complete team stats (2024-25 season)
TEAM_STATS = {
    "Atlanta": {"net_rating": -1.5, "def_rank": 22, "pace": 100.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "ft_rate": 0.25, "reb_rate": 50.2, "three_pct": 0.355},
    "Boston": {"net_rating": 10.5, "def_rank": 2, "pace": 98.5, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "ft_rate": 0.28, "reb_rate": 52.5, "three_pct": 0.385},
    "Brooklyn": {"net_rating": -5.2, "def_rank": 25, "pace": 99.8, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "ft_rate": 0.23, "reb_rate": 48.8, "three_pct": 0.345},
    "Charlotte": {"net_rating": -6.8, "def_rank": 27, "pace": 101.5, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "ft_rate": 0.22, "reb_rate": 49.2, "three_pct": 0.335},
    "Chicago": {"net_rating": -3.5, "def_rank": 20, "pace": 98.2, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "ft_rate": 0.24, "reb_rate": 50.0, "three_pct": 0.348},
    "Cleveland": {"net_rating": 9.8, "def_rank": 3, "pace": 97.5, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "ft_rate": 0.27, "reb_rate": 53.2, "three_pct": 0.372},
    "Dallas": {"net_rating": 3.2, "def_rank": 12, "pace": 99.5, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "ft_rate": 0.26, "reb_rate": 50.8, "three_pct": 0.365},
    "Denver": {"net_rating": 5.5, "def_rank": 8, "pace": 98.8, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "ft_rate": 0.25, "reb_rate": 52.0, "three_pct": 0.358},
    "Detroit": {"net_rating": -4.8, "def_rank": 24, "pace": 100.5, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "ft_rate": 0.23, "reb_rate": 49.5, "three_pct": 0.340},
    "Golden State": {"net_rating": 2.8, "def_rank": 14, "pace": 99.2, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "ft_rate": 0.24, "reb_rate": 50.5, "three_pct": 0.378},
    "Houston": {"net_rating": 4.5, "def_rank": 6, "pace": 99.8, "home_win_pct": 0.60, "away_win_pct": 0.48, "division": "Southwest", "ft_rate": 0.26, "reb_rate": 51.8, "three_pct": 0.352},
    "Indiana": {"net_rating": 1.2, "def_rank": 18, "pace": 102.5, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central", "ft_rate": 0.25, "reb_rate": 50.2, "three_pct": 0.368},
    "LA Clippers": {"net_rating": 0.5, "def_rank": 15, "pace": 97.8, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "ft_rate": 0.24, "reb_rate": 50.0, "three_pct": 0.355},
    "LA Lakers": {"net_rating": 2.5, "def_rank": 16, "pace": 98.5, "home_win_pct": 0.62, "away_win_pct": 0.42, "division": "Pacific", "ft_rate": 0.26, "reb_rate": 51.2, "three_pct": 0.345},
    "Memphis": {"net_rating": 3.8, "def_rank": 10, "pace": 100.8, "home_win_pct": 0.58, "away_win_pct": 0.45, "division": "Southwest", "ft_rate": 0.27, "reb_rate": 52.5, "three_pct": 0.342},
    "Miami": {"net_rating": 1.8, "def_rank": 11, "pace": 97.2, "home_win_pct": 0.60, "away_win_pct": 0.38, "division": "Southeast", "ft_rate": 0.25, "reb_rate": 50.8, "three_pct": 0.362},
    "Milwaukee": {"net_rating": 4.2, "def_rank": 9, "pace": 98.8, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Central", "ft_rate": 0.28, "reb_rate": 52.0, "three_pct": 0.358},
    "Minnesota": {"net_rating": 6.5, "def_rank": 4, "pace": 97.8, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Northwest", "ft_rate": 0.26, "reb_rate": 53.5, "three_pct": 0.355},
    "New Orleans": {"net_rating": -2.8, "def_rank": 21, "pace": 99.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southwest", "ft_rate": 0.24, "reb_rate": 50.5, "three_pct": 0.348},
    "New York": {"net_rating": 5.8, "def_rank": 5, "pace": 97.5, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Atlantic", "ft_rate": 0.27, "reb_rate": 52.8, "three_pct": 0.365},
    "Oklahoma City": {"net_rating": 11.2, "def_rank": 1, "pace": 98.2, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "ft_rate": 0.28, "reb_rate": 53.0, "three_pct": 0.375},
    "Orlando": {"net_rating": 3.5, "def_rank": 7, "pace": 96.8, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast", "ft_rate": 0.25, "reb_rate": 52.2, "three_pct": 0.342},
    "Philadelphia": {"net_rating": 0.8, "def_rank": 17, "pace": 98.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Atlantic", "ft_rate": 0.28, "reb_rate": 51.0, "three_pct": 0.352},
    "Phoenix": {"net_rating": 2.2, "def_rank": 19, "pace": 99.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "ft_rate": 0.25, "reb_rate": 50.2, "three_pct": 0.358},
    "Portland": {"net_rating": -7.5, "def_rank": 28, "pace": 100.2, "home_win_pct": 0.35, "away_win_pct": 0.20, "division": "Northwest", "ft_rate": 0.22, "reb_rate": 48.5, "three_pct": 0.338},
    "Sacramento": {"net_rating": -1.2, "def_rank": 23, "pace": 100.5, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific", "ft_rate": 0.24, "reb_rate": 49.8, "three_pct": 0.362},
    "San Antonio": {"net_rating": -4.5, "def_rank": 26, "pace": 99.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "ft_rate": 0.23, "reb_rate": 50.0, "three_pct": 0.345},
    "Toronto": {"net_rating": -3.2, "def_rank": 29, "pace": 99.5, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic", "ft_rate": 0.23, "reb_rate": 49.2, "three_pct": 0.348},
    "Utah": {"net_rating": -8.5, "def_rank": 30, "pace": 100.8, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "ft_rate": 0.22, "reb_rate": 48.0, "three_pct": 0.335},
    "Washington": {"net_rating": -9.2, "def_rank": 30, "pace": 101.2, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast", "ft_rate": 0.21, "reb_rate": 47.5, "three_pct": 0.332},
}

KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte",
    "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas", "DEN": "Denver",
    "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami",
    "MIL": "Milwaukee", "MIN": "Minnesota", "NOP": "New Orleans", "NYK": "New York",
    "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia", "PHX": "Phoenix",
    "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto",
    "UTA": "Utah", "WAS": "Washington"
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
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021),
}

def calculate_travel_distance(team1, team2):
    loc1, loc2 = TEAM_LOCATIONS.get(team1), TEAM_LOCATIONS.get(team2)
    if not loc1 or not loc2: return 0
    lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
    lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(3956 * 2 * math.asin(math.sqrt(a)))

@st.cache_data(ttl=300)
def fetch_kalshi_nba_games():
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for market in data.get('markets', []):
            ticker = market.get('ticker', '')
            if '-' not in ticker: continue
            game_code = ticker.split('-')[1] if len(ticker.split('-')) > 1 else ''
            if len(game_code) < 6: continue
            
            away_abbrev = game_code[-6:-3].upper()
            home_abbrev = game_code[-3:].upper()
            away_team = KALSHI_ABBREV_MAP.get(away_abbrev, away_abbrev)
            home_team = KALSHI_ABBREV_MAP.get(home_abbrev, home_abbrev)
            
            yes_bid = market.get('yes_bid', 0) or 0
            yes_ask = market.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
            
            game_date_str = ""
            try:
                date_part = game_code[:-6]
                if len(date_part) >= 7:
                    month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
                                 'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
                    game_date_str = f"{month_map.get(date_part[2:5].upper(), date_part[2:5])} {date_part[5:7]}"
            except: pass
            
            games.append({
                'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'yes_price': yes_price, 'volume': market.get('volume', 0), 'game_date': game_date_str
            })
        
        # Deduplicate: keep highest volume market per matchup
        seen = {}
        for g in games:
            key = f"{g['away_team']}@{g['home_team']}_{g['game_date']}"
            if key not in seen or g['volume'] > seen[key]['volume']:
                seen[key] = g
        
        # Sort by date (today first)
        month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                       'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        def date_sort_key(g):
            try:
                parts = g['game_date'].split()
                return (month_order.get(parts[0], 0), int(parts[1]))
            except:
                return (99, 99)
        
        return sorted(seen.values(), key=date_sort_key)
    except: return []

@st.cache_data(ttl=14400)
def fetch_nba_injuries():
    try:
        resp = requests.get("https://www.espn.com/nba/injuries", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(resp.content, 'lxml')
        injuries = {}
        for team in soup.find_all('div', class_='ResponsiveTable'):
            header = team.find_previous('div', class_='Table__Title')
            if header:
                team_name = header.text.strip()
                injuries[team_name] = []
                for row in team.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        injuries[team_name].append(f"{cells[0].text.strip()} ({cells[2].text.strip()})")
        return injuries
    except: return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    try:
        team_last_game = {}
        today = datetime.now()
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            for market in resp.json().get('markets', []):
                ticker = market.get('ticker', '')
                close_time = market.get('close_time', '')
                if not close_time or '-' not in ticker: continue
                try:
                    game_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)
                    days_ago = (today - game_dt).days
                    if days_ago < 0 or days_ago > 5: continue
                    game_code = ticker.split('-')[1]
                    if len(game_code) >= 6:
                        for abbrev in [game_code[-6:-3].upper(), game_code[-3:].upper()]:
                            name = KALSHI_ABBREV_MAP.get(abbrev)
                            if name and name not in team_last_game:
                                team_last_game[name] = days_ago
                except: continue
        return team_last_game
    except: return {}

def calculate_edge(home_team, away_team, kalshi_price, home_rest, away_rest, home_injuries, away_injuries, travel_miles, ref_bias, weights):
    home_stats = TEAM_STATS.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    away_stats = TEAM_STATS.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    
    rest_diff = home_rest - away_rest
    rest_score = max(-6, min(6, rest_diff * 2))
    def_score = (away_stats['def_rank'] - home_stats['def_rank']) * 0.15
    injury_score = (away_injuries - home_injuries) * 1.5
    pace_diff = home_stats['pace'] - away_stats['pace']
    pace_score = pace_diff * 0.1 if home_stats['net_rating'] > away_stats['net_rating'] else -pace_diff * 0.1
    net_score = (home_stats['net_rating'] - away_stats['net_rating']) * 0.8
    travel_score = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    home_split_advantage = (home_stats['home_win_pct'] - 0.5) * 10
    away_split_disadvantage = (0.5 - away_stats['away_win_pct']) * 10
    split_score = home_split_advantage + away_split_disadvantage
    same_division = home_stats['division'] == away_stats['division']
    h2h_score = 1.5 if same_division else 0
    ref_score = ref_bias
    ft_diff = (home_stats['ft_rate'] - away_stats['ft_rate']) * 20
    ft_score = ft_diff
    reb_diff = (home_stats['reb_rate'] - away_stats['reb_rate']) * 0.3
    reb_score = reb_diff
    three_diff = (home_stats['three_pct'] - away_stats['three_pct']) * 50
    three_score = three_diff
    home_court = 3.0
    
    weighted_spread = (
        home_court +
        rest_score * weights['rest'] +
        def_score * weights['defense'] +
        injury_score * weights['injury'] +
        pace_score * weights['pace'] +
        net_score * weights['net_rating'] +
        travel_score * weights['travel'] +
        split_score * weights['splits'] +
        h2h_score * weights['h2h'] +
        ref_score * weights['refs'] +
        ft_score * weights['ft'] +
        reb_score * weights['reb'] +
        three_score * weights['three']
    )
    
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    edge = home_win_prob - kalshi_price
    ev = (home_win_prob/100)*(100-kalshi_price) - ((100-home_win_prob)/100)*kalshi_price if edge > 0 else ((100-home_win_prob)/100)*kalshi_price - (home_win_prob/100)*(100-kalshi_price)
    
    return {
        'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1), 'expected_spread': round(weighted_spread, 1),
        'expected_value': round(ev, 2), 'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW'),
        'factors': {
            'rest': round(rest_score * weights['rest'], 2), 'defense': round(def_score * weights['defense'], 2),
            'injury': round(injury_score * weights['injury'], 2), 'pace': round(pace_score * weights['pace'], 2),
            'net_rating': round(net_score * weights['net_rating'], 2), 'travel': round(travel_score * weights['travel'], 2),
            'splits': round(split_score * weights['splits'], 2), 'h2h': round(h2h_score * weights['h2h'], 2),
            'refs': round(ref_score * weights['refs'], 2), 'ft': round(ft_score * weights['ft'], 2),
            'reb': round(reb_score * weights['reb'], 2), 'three': round(three_score * weights['three'], 2),
            'home_court': home_court
        },
        'raw': {
            'rest_diff': rest_diff, 'def_diff': away_stats['def_rank']-home_stats['def_rank'],
            'injury_diff': away_injuries-home_injuries, 'pace_diff': round(pace_diff, 1),
            'net_diff': round(home_stats['net_rating']-away_stats['net_rating'], 1),
            'travel_miles': travel_miles, 'split_diff': round(split_score, 2),
            'same_div': same_division, 'ref_bias': ref_bias,
            'ft_diff': round(ft_diff, 3), 'reb_diff': round(reb_diff, 2), 'three_diff': round(three_diff, 3),
            'home_win_pct': home_stats['home_win_pct'], 'away_win_pct': away_stats['away_win_pct'],
            'home_def_rank': home_stats['def_rank'], 'away_def_rank': away_stats['def_rank'],
            'home_net': home_stats['net_rating'], 'away_net': away_stats['net_rating'],
            'home_pace': home_stats['pace'], 'away_pace': away_stats['pace'],
            'home_ft': home_stats['ft_rate'], 'away_ft': away_stats['ft_rate'],
            'home_reb': home_stats['reb_rate'], 'away_reb': away_stats['reb_rate'],
            'home_3pt': home_stats['three_pct'], 'away_3pt': away_stats['three_pct']
        }
    }

# ========== UI ==========
st.title("🏀 NBA Kalshi Edge Finder")
st.markdown("**12-Factor Edge Model** — Powered by Kalshi API")
now = datetime.now()
st.caption(f"📅 {now.strftime('%A, %B %d, %Y')} | ⏰ {now.strftime('%I:%M %p')} | Auto-refresh: 5 min")

# ========== SIDEBAR ==========
st.sidebar.header("⚙️ Factor Weights")
st.sidebar.caption("0 = off, 1 = normal, 2 = double impact")

# FACTOR LEGEND - Shows what each factor ACTUALLY measures
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Factor Legend")
st.sidebar.markdown("""
| Factor | What It Measures |
|--------|------------------|
| 🛏️ Rest | Days since last game (home vs away) |
| 🛡️ Defense | Defensive rank (1-30, lower = better) |
| 🏥 Injury | # of injured players (from ESPN) |
| ⚡ Pace | Possessions per game |
| 📊 Net Rtg | Point differential per 100 poss |
| ✈️ Travel | Miles traveled by away team |
| 🏠 Splits | Home win% vs Away win% |
| ⚔️ H2H | Divisional rivalry bonus |
| 👨‍⚖️ Refs | Referee home-team bias |
| 🎯 FT | Free throw rate difference |
| 🏀 Reb | Rebound rate difference |
| 🎯 3PT | 3-point shooting % difference |
""")

st.sidebar.markdown("---")
with st.sidebar.expander("🏀 Core Factors", expanded=True):
    w_rest = st.slider("🛏️ Rest (days diff)", 0.0, 2.0, 1.0, 0.1, key="w1")
    w_def = st.slider("🛡️ Defense (rank 1-30)", 0.0, 2.0, 1.0, 0.1, key="w2")
    w_inj = st.slider("🏥 Injuries (count)", 0.0, 2.0, 1.0, 0.1, key="w3")
    w_pace = st.slider("⚡ Pace (poss/game)", 0.0, 2.0, 1.0, 0.1, key="w4")
    w_net = st.slider("📊 Net Rating (+/-)", 0.0, 2.0, 1.0, 0.1, key="w5")
    w_travel = st.slider("✈️ Travel (miles)", 0.0, 2.0, 1.0, 0.1, key="w6")

with st.sidebar.expander("📈 Advanced Factors", expanded=True):
    w_splits = st.slider("🏠 Home/Away Splits", 0.0, 2.0, 1.0, 0.1, key="w7")
    w_h2h = st.slider("⚔️ Divisional Rivalry", 0.0, 2.0, 1.0, 0.1, key="w8")
    w_refs = st.slider("👨‍⚖️ Ref Bias", 0.0, 2.0, 1.0, 0.1, key="w9")
    w_ft = st.slider("🎯 Free Throw Rate", 0.0, 2.0, 1.0, 0.1, key="w10")
    w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1, key="w11")
    w_three = st.slider("🎯 3PT Shooting", 0.0, 2.0, 1.0, 0.1, key="w12")

weights = {'rest': w_rest, 'defense': w_def, 'injury': w_inj, 'pace': w_pace, 'net_rating': w_net,
           'travel': w_travel, 'splits': w_splits, 'h2h': w_h2h, 'refs': w_refs, 'ft': w_ft, 'reb': w_reb, 'three': w_three}

st.sidebar.markdown("---")
st.sidebar.header("🎯 Display")
show_filter = st.sidebar.radio("Show:", ["🔥 High Edge Only", "✅ All with Edge", "📋 All Games"], index=0)
min_edge = st.sidebar.slider("Min Edge %", 0, 25, 5)

st.sidebar.markdown("---")
st.sidebar.header("📅 Defaults")
default_home_rest = st.sidebar.number_input("Default Home Rest", 1, 7, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 1, 7, 2)
st.sidebar.caption("0=Away-friendly | 1=Neutral | 2=Home-friendly")
default_ref_bias = st.sidebar.slider("Default Ref Bias", 0.0, 2.0, 1.0, 0.1)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ========== DATA ==========
games = fetch_kalshi_nba_games()
injuries = fetch_nba_injuries()
rest_days_data = fetch_rest_days()

if rest_days_data:
    st.sidebar.caption(f"✅ Rest data: {len(rest_days_data)} teams")

if not games:
    st.warning("No NBA games on Kalshi right now.")
else:
    games_with_analysis = []
    for game in games:
        home, away = game['home_team'], game['away_team']
        home_inj_list, away_inj_list = injuries.get(home, []), injuries.get(away, [])
        travel = calculate_travel_distance(away, home)
        home_rest = rest_days_data.get(home, default_home_rest)
        away_rest = rest_days_data.get(away, default_away_rest)
        analysis = calculate_edge(home, away, game['yes_price'], home_rest, away_rest, len(home_inj_list), len(away_inj_list), travel, default_ref_bias, weights)
        games_with_analysis.append((game, analysis, home_inj_list, away_inj_list, home_rest, away_rest, travel))
    
    high_ct = sum(1 for _, a, *_ in games_with_analysis if a['recommendation'] != 'NO EDGE' and a['confidence'] == 'HIGH' and abs(a['edge']) >= min_edge)
    edge_ct = sum(1 for _, a, *_ in games_with_analysis if a['recommendation'] != 'NO EDGE' and abs(a['edge']) >= min_edge)
    st.success(f"✅ **{len(games)} games** | 🔥 **{high_ct} high-edge** | ✅ **{edge_ct} with edge**")
    
    # ========== TOP EDGES SUMMARY ==========
    top_edges = sorted(games_with_analysis, key=lambda x: abs(x[1]['edge']), reverse=True)[:3]
    if top_edges and high_ct > 0:
        st.markdown("### 🔥 Top Edges Today")
        for game, analysis, *_ in top_edges:
            if analysis['recommendation'] == 'NO EDGE': continue
            home, away = game['home_team'], game['away_team']
            r = analysis['raw']
            factors = []
            if r['rest_diff'] != 0: factors.append(f"Rest {r['rest_diff']:+d}d")
            if r['injury_diff'] != 0: factors.append(f"Injuries {r['injury_diff']:+d}")
            if r['travel_miles'] > 1000: factors.append(f"Travel {r['travel_miles']}mi")
            if abs(r['net_diff']) > 5: factors.append(f"Net {r['net_diff']:+.1f}")
            if r['same_div']: factors.append("Division")
            why = ", ".join(factors[:3]) if factors else "Multiple factors"
            icon = "🟢" if analysis['recommendation'] == 'BUY YES' else "🔴"
            bet_on = home if analysis['recommendation'] == 'BUY YES' else away
            st.markdown(f"{icon} **{away} @ {home}** → **{analysis['recommendation']}** ({analysis['edge']:+.1f}%) — *{why}*")
        st.markdown("---")
    
    # ========== GAME CARDS ==========
    displayed = 0
    for game, analysis, home_inj_list, away_inj_list, home_rest, away_rest, travel in games_with_analysis:
        home, away = game['home_team'], game['away_team']
        
        if show_filter == "🔥 High Edge Only" and not (analysis['recommendation'] != 'NO EDGE' and analysis['confidence'] == 'HIGH' and abs(analysis['edge']) >= min_edge):
            continue
        if show_filter == "✅ All with Edge" and not (analysis['recommendation'] != 'NO EDGE' and abs(analysis['edge']) >= min_edge):
            continue
        
        color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
        r = analysis['raw']
        key_stats = []
        if r['rest_diff'] != 0: key_stats.append(f"Rest:{r['rest_diff']:+d}")
        if r['injury_diff'] != 0: key_stats.append(f"Inj:{r['injury_diff']:+d}")
        if r['travel_miles'] > 500: key_stats.append(f"✈️{r['travel_miles']}mi")
        if abs(r['net_diff']) > 3: key_stats.append(f"Net:{r['net_diff']:+.1f}")
        stats_str = " | ".join(key_stats[:3]) if key_stats else ""
        header_extra = f" | {stats_str}" if stats_str else ""
        
        with st.expander(f"{color} {game['game_date']} | {away} @ {home}{header_extra} | Edge: {analysis['edge']:+.1f}% | {analysis['recommendation']}", expanded=False):
            st.markdown("### ⚙️ Adjustments")
            c1, c2, c3 = st.columns(3)
            g_away_rest = c1.number_input(f"{away} rest", 0, 7, away_rest, key=f"ar_{game['ticker']}")
            g_home_rest = c2.number_input(f"{home} rest", 0, 7, home_rest, key=f"hr_{game['ticker']}")
            c3.caption("0=Away-friendly | 1=Neutral | 2=Home-friendly")
            g_ref_bias = c3.slider("Ref bias", 0.0, 2.0, default_ref_bias, 0.1, key=f"ref_{game['ticker']}")
            
            if g_away_rest != away_rest or g_home_rest != home_rest or g_ref_bias != default_ref_bias:
                analysis = calculate_edge(home, away, game['yes_price'], g_home_rest, g_away_rest, len(home_inj_list), len(away_inj_list), travel, g_ref_bias, weights)
                r = analysis['raw']
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.markdown("### 📊 Kalshi")
            col1.metric(f"{home} (YES)", f"{game['yes_price']:.0f}¢")
            col1.metric(f"{away} (NO)", f"{100-game['yes_price']:.0f}¢")
            col1.caption(f"Vol: {game['volume']:,}")
            
            col2.markdown("### 🎯 Model")
            col2.metric(f"{home} Win", f"{analysis['home_win_prob']:.1f}%")
            col2.metric("Spread", f"{home} {analysis['expected_spread']:+.1f}")
            
            col3.markdown("### 💰 Action")
            col3.metric("Edge", f"{analysis['edge']:+.1f}%", delta=analysis['confidence'])
            col3.metric("EV", f"{analysis['expected_value']:+.2f}¢")
            url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{game['ticker'].lower()}"
            if analysis['recommendation'] == 'BUY YES':
                col3.link_button(f"🟢 BUY YES", url, use_container_width=True)
            elif analysis['recommendation'] == 'BUY NO':
                col3.link_button(f"🔴 BUY NO", url, use_container_width=True)
            
            # ========== 12-FACTOR BREAKDOWN WITH RAW VALUES ==========
            st.markdown("---")
            st.markdown("### 📈 12-Factor Breakdown (Raw Values)")
            f = analysis['factors']
            
            r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
            r1c1.metric("🛏️ Rest", f"{f['rest']:+.2f}", f"H:{home_rest}d A:{away_rest}d")
            r1c2.metric("🛡️ Defense", f"{f['defense']:+.2f}", f"H:#{r['home_def_rank']} A:#{r['away_def_rank']}")
            r1c3.metric("🏥 Injury", f"{f['injury']:+.2f}", f"H:{len(home_inj_list)} A:{len(away_inj_list)}")
            r1c4.metric("⚡ Pace", f"{f['pace']:+.2f}", f"H:{r['home_pace']} A:{r['away_pace']}")
            r1c5.metric("📊 Net Rtg", f"{f['net_rating']:+.2f}", f"H:{r['home_net']:+.1f} A:{r['away_net']:+.1f}")
            r1c6.metric("✈️ Travel", f"{f['travel']:+.2f}", f"{r['travel_miles']} mi")
            
            r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns(6)
            r2c1.metric("🏠 Splits", f"{f['splits']:+.2f}", f"H:{r['home_win_pct']:.0%} A:{r['away_win_pct']:.0%}")
            r2c2.metric("⚔️ H2H", f"{f['h2h']:+.2f}", "DIV" if r['same_div'] else "—")
            r2c3.metric("👨‍⚖️ Refs", f"{f['refs']:+.2f}", f"Bias:{r['ref_bias']:.1f}")
            r2c4.metric("🎯 FT", f"{f['ft']:+.2f}", f"H:{r['home_ft']:.0%} A:{r['away_ft']:.0%}")
            r2c5.metric("🏀 Reb", f"{f['reb']:+.2f}", f"H:{r['home_reb']:.1f} A:{r['away_reb']:.1f}")
            r2c6.metric("🎯 3PT", f"{f['three']:+.2f}", f"H:{r['home_3pt']:.1%} A:{r['away_3pt']:.1%}")
            
            st.caption(f"🏠 Home Court: +{f['home_court']} (baseline)")
            
            st.markdown("---")
            i1, i2 = st.columns(2)
            i1.markdown(f"**🏥 {away} Injuries ({len(away_inj_list)})**")
            i1.caption(", ".join(away_inj_list[:4]) if away_inj_list else "None reported")
            i2.markdown(f"**🏥 {home} Injuries ({len(home_inj_list)})**")
            i2.caption(", ".join(home_inj_list[:4]) if home_inj_list else "None reported")
        
        displayed += 1
    
    if displayed == 0:
        st.info("No games match filter. Try 'All with Edge' or 'All Games'.")

st.markdown("---")
st.caption("⚠️ **Disclaimer:** Entertainment only. Not financial advice. Trade responsibly.")
