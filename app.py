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
    "Atlanta": {"net_rating": -1.5, "off_rating": 114.2, "def_rating": 115.7, "def_rank": 22, "pace": 100.2, "ppg": 118.2, "opp_ppg": 120.1, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pa": 38.5, "three_pct": 0.355, "oreb_pct": 27.5, "tov_pct": 13.2, "ft_rate": 0.25, "reb_rate": 50.2},
    "Boston": {"net_rating": 10.5, "off_rating": 120.5, "def_rating": 110.0, "def_rank": 2, "pace": 98.5, "ppg": 120.8, "opp_ppg": 110.3, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "three_pa": 42.5, "three_pct": 0.385, "oreb_pct": 25.8, "tov_pct": 12.5, "ft_rate": 0.28, "reb_rate": 52.5},
    "Brooklyn": {"net_rating": -5.2, "off_rating": 109.8, "def_rating": 115.0, "def_rank": 25, "pace": 99.8, "ppg": 108.5, "opp_ppg": 113.7, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pa": 35.2, "three_pct": 0.345, "oreb_pct": 26.2, "tov_pct": 14.1, "ft_rate": 0.23, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -6.8, "off_rating": 108.5, "def_rating": 115.3, "def_rank": 27, "pace": 101.5, "ppg": 106.8, "opp_ppg": 113.6, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pa": 34.8, "three_pct": 0.335, "oreb_pct": 28.1, "tov_pct": 14.5, "ft_rate": 0.22, "reb_rate": 49.2},
    "Chicago": {"net_rating": -3.5, "off_rating": 111.2, "def_rating": 114.7, "def_rank": 20, "pace": 98.2, "ppg": 111.5, "opp_ppg": 115.0, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pa": 33.5, "three_pct": 0.348, "oreb_pct": 27.0, "tov_pct": 13.8, "ft_rate": 0.24, "reb_rate": 50.0},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.5, "def_rating": 108.7, "def_rank": 3, "pace": 97.5, "ppg": 118.2, "opp_ppg": 108.4, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pa": 36.2, "three_pct": 0.372, "oreb_pct": 28.5, "tov_pct": 12.2, "ft_rate": 0.27, "reb_rate": 53.2},
    "Dallas": {"net_rating": 3.2, "off_rating": 115.8, "def_rating": 112.6, "def_rank": 12, "pace": 99.5, "ppg": 117.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pa": 40.2, "three_pct": 0.365, "oreb_pct": 26.5, "tov_pct": 13.0, "ft_rate": 0.26, "reb_rate": 50.8},
    "Denver": {"net_rating": 5.5, "off_rating": 117.2, "def_rating": 111.7, "def_rank": 8, "pace": 98.8, "ppg": 116.5, "opp_ppg": 111.0, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pa": 35.8, "three_pct": 0.358, "oreb_pct": 29.2, "tov_pct": 12.8, "ft_rate": 0.25, "reb_rate": 52.0},
    "Detroit": {"net_rating": -4.8, "off_rating": 110.5, "def_rating": 115.3, "def_rank": 24, "pace": 100.5, "ppg": 110.2, "opp_ppg": 115.0, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pa": 36.5, "three_pct": 0.340, "oreb_pct": 27.8, "tov_pct": 14.2, "ft_rate": 0.23, "reb_rate": 49.5},
    "Golden State": {"net_rating": 2.8, "off_rating": 115.2, "def_rating": 112.4, "def_rank": 14, "pace": 99.2, "ppg": 115.8, "opp_ppg": 113.0, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 43.5, "three_pct": 0.378, "oreb_pct": 25.2, "tov_pct": 13.5, "ft_rate": 0.24, "reb_rate": 50.5},
    "Houston": {"net_rating": 4.5, "off_rating": 114.8, "def_rating": 110.3, "def_rank": 6, "pace": 99.8, "ppg": 114.5, "opp_ppg": 110.0, "home_win_pct": 0.60, "away_win_pct": 0.48, "division": "Southwest", "three_pa": 41.2, "three_pct": 0.352, "oreb_pct": 29.5, "tov_pct": 13.2, "ft_rate": 0.26, "reb_rate": 51.8},
    "Indiana": {"net_rating": 1.2, "off_rating": 118.5, "def_rating": 117.3, "def_rank": 18, "pace": 102.5, "ppg": 123.2, "opp_ppg": 122.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central", "three_pa": 39.8, "three_pct": 0.368, "oreb_pct": 28.0, "tov_pct": 12.5, "ft_rate": 0.25, "reb_rate": 50.2},
    "LA Clippers": {"net_rating": 0.5, "off_rating": 112.8, "def_rating": 112.3, "def_rank": 15, "pace": 97.8, "ppg": 110.5, "opp_ppg": 110.0, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "three_pa": 36.0, "three_pct": 0.355, "oreb_pct": 26.8, "tov_pct": 13.0, "ft_rate": 0.24, "reb_rate": 50.0},
    "LA Lakers": {"net_rating": 2.5, "off_rating": 114.5, "def_rating": 112.0, "def_rank": 16, "pace": 98.5, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.62, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 34.5, "three_pct": 0.345, "oreb_pct": 28.2, "tov_pct": 13.5, "ft_rate": 0.26, "reb_rate": 51.2},
    "Memphis": {"net_rating": 3.8, "off_rating": 116.2, "def_rating": 112.4, "def_rank": 10, "pace": 100.8, "ppg": 118.5, "opp_ppg": 114.7, "home_win_pct": 0.58, "away_win_pct": 0.45, "division": "Southwest", "three_pa": 35.0, "three_pct": 0.342, "oreb_pct": 30.5, "tov_pct": 13.8, "ft_rate": 0.27, "reb_rate": 52.5},
    "Miami": {"net_rating": 1.8, "off_rating": 112.5, "def_rating": 110.7, "def_rank": 11, "pace": 97.2, "ppg": 110.8, "opp_ppg": 109.0, "home_win_pct": 0.60, "away_win_pct": 0.38, "division": "Southeast", "three_pa": 38.5, "three_pct": 0.362, "oreb_pct": 26.0, "tov_pct": 12.8, "ft_rate": 0.25, "reb_rate": 50.8},
    "Milwaukee": {"net_rating": 4.2, "off_rating": 116.8, "def_rating": 112.6, "def_rank": 9, "pace": 98.8, "ppg": 117.5, "opp_ppg": 113.3, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Central", "three_pa": 40.0, "three_pct": 0.358, "oreb_pct": 27.5, "tov_pct": 12.2, "ft_rate": 0.28, "reb_rate": 52.0},
    "Minnesota": {"net_rating": 6.5, "off_rating": 113.5, "def_rating": 107.0, "def_rank": 4, "pace": 97.8, "ppg": 112.2, "opp_ppg": 105.7, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Northwest", "three_pa": 37.2, "three_pct": 0.355, "oreb_pct": 29.0, "tov_pct": 12.5, "ft_rate": 0.26, "reb_rate": 53.5},
    "New Orleans": {"net_rating": -2.8, "off_rating": 112.8, "def_rating": 115.6, "def_rank": 21, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.3, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southwest", "three_pa": 36.8, "three_pct": 0.348, "oreb_pct": 28.5, "tov_pct": 14.0, "ft_rate": 0.24, "reb_rate": 50.5},
    "New York": {"net_rating": 5.8, "off_rating": 117.2, "def_rating": 111.4, "def_rank": 5, "pace": 97.5, "ppg": 116.8, "opp_ppg": 111.0, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Atlantic", "three_pa": 37.5, "three_pct": 0.365, "oreb_pct": 29.8, "tov_pct": 12.0, "ft_rate": 0.27, "reb_rate": 52.8},
    "Oklahoma City": {"net_rating": 11.2, "off_rating": 119.8, "def_rating": 108.6, "def_rank": 1, "pace": 98.2, "ppg": 119.5, "opp_ppg": 108.3, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pa": 39.5, "three_pct": 0.375, "oreb_pct": 30.2, "tov_pct": 11.8, "ft_rate": 0.28, "reb_rate": 53.0},
    "Orlando": {"net_rating": 3.5, "off_rating": 111.2, "def_rating": 107.7, "def_rank": 7, "pace": 96.8, "ppg": 108.5, "opp_ppg": 105.0, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast", "three_pa": 35.5, "three_pct": 0.342, "oreb_pct": 30.0, "tov_pct": 13.2, "ft_rate": 0.25, "reb_rate": 52.2},
    "Philadelphia": {"net_rating": 0.8, "off_rating": 113.5, "def_rating": 112.7, "def_rank": 17, "pace": 98.5, "ppg": 114.2, "opp_ppg": 113.4, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Atlantic", "three_pa": 36.2, "three_pct": 0.352, "oreb_pct": 28.0, "tov_pct": 13.5, "ft_rate": 0.28, "reb_rate": 51.0},
    "Phoenix": {"net_rating": 2.2, "off_rating": 115.5, "def_rating": 113.3, "def_rank": 19, "pace": 99.2, "ppg": 116.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 37.0, "three_pct": 0.358, "oreb_pct": 26.5, "tov_pct": 13.0, "ft_rate": 0.25, "reb_rate": 50.2},
    "Portland": {"net_rating": -7.5, "off_rating": 108.2, "def_rating": 115.7, "def_rank": 28, "pace": 100.2, "ppg": 107.5, "opp_ppg": 115.0, "home_win_pct": 0.35, "away_win_pct": 0.20, "division": "Northwest", "three_pa": 34.0, "three_pct": 0.338, "oreb_pct": 27.0, "tov_pct": 14.5, "ft_rate": 0.22, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.2, "off_rating": 114.5, "def_rating": 115.7, "def_rank": 23, "pace": 100.5, "ppg": 117.8, "opp_ppg": 119.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific", "three_pa": 36.5, "three_pct": 0.362, "oreb_pct": 27.2, "tov_pct": 13.8, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -4.5, "off_rating": 111.8, "def_rating": 116.3, "def_rank": 26, "pace": 99.8, "ppg": 112.5, "opp_ppg": 117.0, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "three_pa": 37.8, "three_pct": 0.345, "oreb_pct": 28.5, "tov_pct": 14.2, "ft_rate": 0.23, "reb_rate": 50.0},
    "Toronto": {"net_rating": -3.2, "off_rating": 112.2, "def_rating": 115.4, "def_rank": 29, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.7, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic", "three_pa": 38.0, "three_pct": 0.348, "oreb_pct": 27.8, "tov_pct": 13.5, "ft_rate": 0.23, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.5, "off_rating": 108.5, "def_rating": 117.0, "def_rank": 30, "pace": 100.8, "ppg": 108.2, "opp_ppg": 116.7, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pa": 39.0, "three_pct": 0.335, "oreb_pct": 26.5, "tov_pct": 15.0, "ft_rate": 0.22, "reb_rate": 48.0},
    "Washington": {"net_rating": -9.2, "off_rating": 107.8, "def_rating": 117.0, "def_rank": 30, "pace": 101.2, "ppg": 108.5, "opp_ppg": 117.7, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast", "three_pa": 35.5, "three_pct": 0.332, "oreb_pct": 26.0, "tov_pct": 15.2, "ft_rate": 0.21, "reb_rate": 47.5},
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

INJURY_REFERENCE = {
    "Boston": "Tatum (Achilles)", "Denver": "Jokic, Valanciunas, C.Johnson", 
    "Dallas": "Kyrie, Lively, Exum, PJ Washington", "Indiana": "Haliburton, Toppin, Mathurin",
    "Portland": "Lillard, Scoot, Grant, Holiday", "Houston": "VanVleet, Sengun",
    "Sacramento": "Sabonis, K.Murray", "LA Lakers": "LeBron, Reaves, Hachimura",
    "Orlando": "F.Wagner, Suggs, M.Wagner", "Detroit": "Cunningham, Duren, Harris",
    "Memphis": "Ja, Edey, Clarke", "Minnesota": "Edwards (rest)", "Charlotte": "B.Miller",
    "San Antonio": "Vassell", "Utah": "Kessler", "LA Clippers": "Beal, Bogdanovic",
    "Cleveland": "Strus", "Chicago": "Giddey, White", "Washington": "T.Young, Middleton",
    "Oklahoma City": "Hartenstein, Caruso", "New Orleans": "Murray, Jones, Murphy",
    "Toronto": "Ingram, Poeltl", "Golden State": "GP2", "New York": "Hart", "Phoenix": "J.Green",
}

# ========== URL BUILDERS - Direct to Kalshi event page ==========
def build_moneyline_url(ticker): 
    return f"https://kalshi.com/markets/{ticker}"

def build_totals_url(ticker): 
    return f"https://kalshi.com/markets/{ticker}"

def build_spread_url(ticker): 
    return f"https://kalshi.com/markets/{ticker}"

def calculate_travel_distance(team1, team2):
    loc1, loc2 = TEAM_LOCATIONS.get(team1), TEAM_LOCATIONS.get(team2)
    if not loc1 or not loc2: return 0
    lat1, lon1, lat2, lon2 = math.radians(loc1[0]), math.radians(loc1[1]), math.radians(loc2[0]), math.radians(loc2[1])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1)/2)**2
    return round(3956 * 2 * math.asin(math.sqrt(a)))

def calculate_kelly(win_prob, kalshi_price, bankroll=1000, fraction=0.25):
    p, q = win_prob / 100, 1 - win_prob / 100
    b = (100 - kalshi_price) / kalshi_price if kalshi_price > 0 else 0
    kelly_pct = max(0, (b * p - q) / b) if b > 0 else 0
    adj_kelly = kelly_pct * fraction
    bet_amount = bankroll * adj_kelly
    ev_per_dollar = (p * b) - q if b > 0 else 0
    return {'adj_kelly_pct': round(adj_kelly * 100, 1), 'bet_amount': round(bet_amount, 2),
            'ev_per_dollar': round(ev_per_dollar, 3), 'ev_on_bet': round(ev_per_dollar * bet_amount, 2)}

def calculate_live_rest_score(home_rest, away_rest):
    home_b2b, away_b2b = home_rest == 0, away_rest == 0
    if home_b2b and not away_b2b: return -4.0
    elif away_b2b and not home_b2b: return 4.0
    elif home_b2b and away_b2b: return 0.5
    if home_rest <= 1 and away_rest > 1: return -2.0
    elif away_rest <= 1 and home_rest > 1: return 2.0
    return max(-3, min(3, (home_rest - away_rest) * 1.0))

def calculate_edge(home_team, away_team, kalshi_price, home_rest, away_rest, home_inj_score, away_inj_score, travel_miles, ref_bias, weights):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    
    rest_score = max(-6, min(6, (home_rest - away_rest) * 2))
    live_rest_score = calculate_live_rest_score(home_rest, away_rest)
    def_score = (away.get('def_rank', 15) - home.get('def_rank', 15)) * 0.15
    injury_score = (away_inj_score - home_inj_score) * 1.0
    pace_diff = home['pace'] - away['pace']
    pace_score = pace_diff * 0.1 if home['net_rating'] > away['net_rating'] else -pace_diff * 0.1
    net_score = (home['net_rating'] - away['net_rating']) * 0.8
    travel_score = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_score = (home['home_win_pct'] - 0.5) * 10 + (0.5 - away['away_win_pct']) * 10
    h2h_score = 1.5 if home.get('division') == away.get('division') else 0
    home_court = 3.0
    
    weighted_spread = (home_court + rest_score * weights['rest'] + live_rest_score * weights['live_rest'] + 
                       def_score * weights['defense'] + injury_score * weights['injury'] +
                       pace_score * weights['pace'] + net_score * weights['net_rating'] + travel_score * weights['travel'] +
                       split_score * weights['splits'] + h2h_score * weights['h2h'] + ref_bias * weights['refs'])
    
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    edge = home_win_prob - kalshi_price
    
    return {
        'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW'),
        'factors': {'rest': round(rest_score * weights['rest'], 2), 'live_rest': round(live_rest_score * weights['live_rest'], 2),
            'defense': round(def_score * weights['defense'], 2), 'injury': round(injury_score * weights['injury'], 2), 
            'net_rating': round(net_score * weights['net_rating'], 2), 'travel': round(travel_score * weights['travel'], 2)},
        'raw': {'home_rest': home_rest, 'away_rest': away_rest, 'travel_miles': travel_miles,
            'home_def_rank': home.get('def_rank', 15), 'away_def_rank': away.get('def_rank', 15)}
    }

def calculate_total_points(home_team, away_team, home_rest, away_rest, home_inj_score, away_inj_score, travel_miles):
    home = TEAM_STATS.get(home_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "def_rating": 112, "net_rating": 0})
    away = TEAM_STATS.get(away_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "def_rating": 112, "net_rating": 0})
    
    base_total = ((home['ppg'] + away['opp_ppg']) / 2) + ((away['ppg'] + home['opp_ppg']) / 2)
    pace_adj = ((home['pace'] + away['pace']) / 2 - 99.5) * 0.5
    rest_adj = -5 if home_rest == 0 and away_rest == 0 else (-2.5 if home_rest == 0 or away_rest == 0 else 0)
    defense_adj = ((home['def_rating'] + away['def_rating']) / 2 - 112) * 0.4
    travel_adj = -2 if travel_miles > 1500 else (-1 if travel_miles > 1000 else 0)
    injury_adj = -(home_inj_score + away_inj_score) * 1.0
    altitude_adj = 2.5 if home_team == "Denver" else (1.5 if home_team == "Utah" else 0)
    
    predicted = base_total + pace_adj + rest_adj + defense_adj + travel_adj + injury_adj + altitude_adj
    return {'predicted_total': round(predicted, 1), 'factors': {'base_total': round(base_total, 1), 'pace': round(pace_adj, 1),
        'rest': round(rest_adj, 1), 'defense': round(defense_adj, 1), 'injury': round(injury_adj, 1), 'altitude': round(altitude_adj, 1)}}

def calculate_spread(home_team, away_team, home_rest, away_rest, home_inj_score, away_inj_score, travel_miles):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "home_win_pct": 0.5, "away_win_pct": 0.5})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "home_win_pct": 0.5, "away_win_pct": 0.5})
    
    net_diff = home['net_rating'] - away['net_rating']
    home_court = 3.5
    rest_adj = (home_rest - away_rest) * 1.5
    injury_adj = (away_inj_score - home_inj_score) * 1.0
    travel_adj = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else 0)
    
    predicted = net_diff + home_court + rest_adj + injury_adj + travel_adj
    return {'predicted_spread': round(predicted, 1), 'factors': {'net_rating': round(net_diff, 1), 'home_court': home_court,
        'rest': round(rest_adj, 1), 'injury': round(injury_adj, 1), 'travel': round(travel_adj, 1)}}

def parse_game_code(game_code):
    if len(game_code) < 6: return None, None, None
    away_team = KALSHI_ABBREV_MAP.get(game_code[-6:-3].upper())
    home_team = KALSHI_ABBREV_MAP.get(game_code[-3:].upper())
    game_date_str = ""
    try:
        month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
                     'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
        game_date_str = f"{month_map.get(game_code[2:5].upper(), '')} {game_code[5:7]}"
    except: pass
    return game_date_str, away_team, home_team

def parse_event_ticker(event_ticker):
    try:
        parts = event_ticker.split('-')
        if len(parts) < 2: return "", None, None
        game_code = parts[1]
        month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
                     'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
        game_date = f"{month_map.get(game_code[2:5].upper(), '')} {game_code[5:7]}"
        teams_part = game_code[7:]
        if len(teams_part) >= 6:
            return game_date, KALSHI_ABBREV_MAP.get(teams_part[:3].upper()), KALSHI_ABBREV_MAP.get(teams_part[3:6].upper())
        return game_date, None, None
    except: return "", None, None

def fetch_kalshi_nba_markets():
    """Fetch markets - NO CACHING to ensure fresh data"""
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    today = datetime.now()
    today_str = f"Jan {today.day:02d}" if today.month == 1 else f"Feb {today.day:02d}"
    
    try:
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100", timeout=10)
        for m in resp.json().get('markets', []):
            ticker = m.get('ticker', '')
            if '-' not in ticker: continue
            game_date, away_team, home_team = parse_game_code(ticker.split('-')[1])
            if not home_team or not game_date: continue
            # ONLY TODAY OR FUTURE
            try:
                day = int(game_date.split()[1])
                if "Jan" in game_date and day < today.day: continue
            except: pass
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            markets['moneyline'].append({
                'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid,
                'game_date': game_date
            })
    except: pass
    
    try:
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open&limit=200", timeout=10)
        for m in resp.json().get('markets', []):
            game_date, away_team, home_team = parse_event_ticker(m.get('event_ticker', ''))
            if not home_team or not game_date: continue
            try:
                day = int(game_date.split()[1])
                if "Jan" in game_date and day < today.day: continue
            except: pass
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            markets['totals'].append({
                'ticker': m.get('ticker', ''), 'away_team': away_team, 'home_team': home_team,
                'line': m.get('floor_strike', 0),
                'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid,
                'game_date': game_date
            })
    except: pass
    
    try:
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200", timeout=10)
        for m in resp.json().get('markets', []):
            game_date, away_team, home_team = parse_event_ticker(m.get('event_ticker', ''))
            if not home_team or not game_date: continue
            try:
                day = int(game_date.split()[1])
                if "Jan" in game_date and day < today.day: continue
            except: pass
            ticker = m.get('ticker', '')
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            spread_team = KALSHI_ABBREV_MAP.get(ticker.split('-')[-1][:3].upper()) if len(ticker.split('-')) >= 3 else home_team
            markets['spreads'].append({
                'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'spread_team': spread_team or home_team, 'line': m.get('floor_strike', 0),
                'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid,
                'game_date': game_date
            })
    except: pass
    
    return markets

def fetch_rest_days():
    try:
        team_last_game, today = {}, datetime.now()
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        for market in resp.json().get('markets', []):
            ticker, close_time = market.get('ticker', ''), market.get('close_time', '')
            if not close_time or '-' not in ticker: continue
            try:
                days_ago = (today - datetime.fromisoformat(close_time.replace('Z', '+00:00')).replace(tzinfo=None)).days
                if 0 <= days_ago <= 5:
                    game_code = ticker.split('-')[1]
                    for abbrev in [game_code[-6:-3].upper(), game_code[-3:].upper()]:
                        name = KALSHI_ABBREV_MAP.get(abbrev)
                        if name and name not in team_last_game: team_last_game[name] = days_ago
            except: continue
        return team_last_game
    except: return {}

# ========== UI ==========
st.title("🏀 NBA Kalshi Edge Finder")
st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | 🟢 = BUY YES | 🔴 = BUY NO")

# Sidebar
st.sidebar.header("⚙️ Settings")
with st.sidebar.expander("Factor Weights", expanded=False):
    w_rest = st.slider("Rest", 0.0, 2.0, 1.0, 0.1)
    w_live_rest = st.slider("B2B", 0.0, 2.0, 1.0, 0.1)
    w_def = st.slider("Defense", 0.0, 2.0, 1.0, 0.1)
    w_inj = st.slider("Injuries", 0.0, 2.0, 1.0, 0.1)
    w_pace = st.slider("Pace", 0.0, 2.0, 1.0, 0.1)
    w_net = st.slider("Net Rating", 0.0, 2.0, 1.0, 0.1)
    w_travel = st.slider("Travel", 0.0, 2.0, 1.0, 0.1)
    w_splits = st.slider("Splits", 0.0, 2.0, 1.0, 0.1)
    w_h2h = st.slider("Division", 0.0, 2.0, 1.0, 0.1)
    w_refs = st.slider("Refs", 0.0, 2.0, 1.0, 0.1)

weights = {'rest': w_rest, 'live_rest': w_live_rest, 'defense': w_def, 'injury': w_inj, 'pace': w_pace, 
           'net_rating': w_net, 'travel': w_travel, 'splits': w_splits, 'h2h': w_h2h, 'refs': w_refs}

ref_bias = st.sidebar.slider("Ref Bias", 0.0, 2.0, 1.0, 0.1)
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.slider("Kelly %", 1, 100, 10, 1) / 100

if st.sidebar.button("🔄 REFRESH DATA"):
    st.rerun()

# Fetch fresh data every time
markets = fetch_kalshi_nba_markets()
rest_days = fetch_rest_days()

st.sidebar.write(f"Games: ML:{len(markets['moneyline'])} TOT:{len(markets['totals'])} SPR:{len(markets['spreads'])}")

# ========== TOP 3 EDGES ==========
st.markdown("### 🔥 Top 3 Edges")

top_edges = []
for game in markets['moneyline']:
    home, away = game['home_team'], game['away_team']
    travel = calculate_travel_distance(away, home)
    home_rest, away_rest = rest_days.get(home, 2), rest_days.get(away, 2)
    analysis = calculate_edge(home, away, game['yes_price'], home_rest, away_rest, 0, 0, travel, ref_bias, weights)
    if analysis['recommendation'] != 'NO EDGE':
        bet_team = home if analysis['recommendation'] == 'BUY YES' else away
        kelly = calculate_kelly(
            analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob'],
            game['yes_price'] if analysis['recommendation'] == 'BUY YES' else 100 - game['yes_price'],
            bankroll, kelly_fraction
        )
        top_edges.append({
            'type': 'ML', 'matchup': f"{away} @ {home}", 'date': game['game_date'],
            'edge': abs(analysis['edge']), 'bet_team': bet_team,
            'bet_amount': kelly['bet_amount'], 'url': build_moneyline_url(game['ticker']),
            'color': '🟢' if analysis['recommendation'] == 'BUY YES' else '🔴'
        })

top_edges = sorted(top_edges, key=lambda x: x['edge'], reverse=True)[:3]

if top_edges:
    for i, e in enumerate(top_edges, 1):
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**#{i} {e['color']} {e['date']} | {e['matchup']}** → {e['bet_team']} ({e['edge']:.1f}%)")
        c2.link_button(f"🎯 BET {e['bet_team'].upper()} ${e['bet_amount']:.0f}", e['url'], use_container_width=True)
else:
    st.info("No edges found")

st.markdown("---")

# ========== TABS ==========
tab1, tab2, tab3 = st.tabs(["🎯 Moneyline", "📊 Totals", "📏 Spreads"])

with tab1:
    for idx, game in enumerate(markets['moneyline']):
        home, away = game['home_team'], game['away_team']
        travel = calculate_travel_distance(away, home)
        home_rest, away_rest = rest_days.get(home, 2), rest_days.get(away, 2)
        
        with st.expander(f"{game['game_date']} | {away} @ {home} | {game['yes_price']:.0f}¢"):
            st.markdown("**🏥 Injury Impact**")
            home_inj = st.select_slider(f"{home}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"ml_h_{idx}")
            st.caption(f"Ref: {INJURY_REFERENCE.get(home, 'None')}")
            away_inj = st.select_slider(f"{away}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"ml_a_{idx}")
            st.caption(f"Ref: {INJURY_REFERENCE.get(away, 'None')}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.5, 3: 4.0}
            analysis = calculate_edge(home, away, game['yes_price'], home_rest, away_rest, inj_map[home_inj], inj_map[away_inj], travel, ref_bias, weights)
            
            bet_team = home if analysis['recommendation'] == 'BUY YES' else away
            color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi", f"{game['yes_price']:.0f}¢")
            c2.metric("Model", f"{analysis['home_win_prob']:.1f}%")
            c3.metric("Edge", f"{analysis['edge']:+.1f}%", color)
            
            kelly = calculate_kelly(
                analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob'],
                game['yes_price'] if analysis['recommendation'] == 'BUY YES' else 100 - game['yes_price'],
                bankroll, kelly_fraction
            )
            
            if analysis['recommendation'] != 'NO EDGE':
                st.link_button(f"🎯 BET {bet_team.upper()} → ${kelly['bet_amount']:.2f}", build_moneyline_url(game['ticker']), use_container_width=True)

with tab2:
    for idx, tm in enumerate(markets['totals']):
        home, away, line = tm['home_team'], tm['away_team'], tm['line']
        travel = calculate_travel_distance(away, home)
        home_rest, away_rest = rest_days.get(home, 2), rest_days.get(away, 2)
        
        with st.expander(f"{tm['game_date']} | {away} @ {home} | Line: {line}"):
            home_inj = st.select_slider(f"{home}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"tot_h_{idx}")
            away_inj = st.select_slider(f"{away}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"tot_a_{idx}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.5, 3: 4.0}
            totals = calculate_total_points(home, away, home_rest, away_rest, inj_map[home_inj], inj_map[away_inj], travel)
            diff = totals['predicted_total'] - line
            
            rec = "OVER" if diff > 3 else ("UNDER" if diff < -3 else "NO EDGE")
            color = "🟢" if rec == "OVER" else ("🔴" if rec == "UNDER" else "⚪")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Predicted", f"{totals['predicted_total']}")
            c2.metric("Line", f"{line}")
            c3.metric("Edge", f"{diff:+.1f}", color)
            
            if rec != "NO EDGE":
                win_prob = min(85, 50 + abs(diff) * 5)
                kelly = calculate_kelly(win_prob, tm['yes_price'] if rec == "OVER" else 100 - tm['yes_price'], bankroll, kelly_fraction)
                st.link_button(f"🎯 BET {rec} {line} → ${kelly['bet_amount']:.2f}", build_totals_url(tm['ticker']), use_container_width=True)

with tab3:
    for idx, sm in enumerate(markets['spreads']):
        home, away, line, spread_team = sm['home_team'], sm['away_team'], sm['line'], sm['spread_team']
        travel = calculate_travel_distance(away, home)
        home_rest, away_rest = rest_days.get(home, 2), rest_days.get(away, 2)
        
        with st.expander(f"{sm['game_date']} | {away} @ {home} | {spread_team} -{line}"):
            home_inj = st.select_slider(f"{home}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"spr_h_{idx}")
            away_inj = st.select_slider(f"{away}", [0,1,2,3], 0, format_func=lambda x: ["HEALTHY","MINOR","BIG","HUGE"][x], key=f"spr_a_{idx}")
            
            inj_map = {0: 0, 1: 1.0, 2: 2.5, 3: 4.0}
            spread = calculate_spread(home, away, home_rest, away_rest, inj_map[home_inj], inj_map[away_inj], travel)
            predicted = spread['predicted_spread']
            spread_diff = (predicted - line) if spread_team == home else (-predicted - line)
            
            if spread_diff > 3: rec, bet_team = "COVERS", spread_team
            elif spread_diff < -3: rec, bet_team = "MISSES", away if spread_team == home else home
            else: rec, bet_team = "NO EDGE", None
            
            color = "🟢" if rec == "COVERS" else ("🔴" if rec == "MISSES" else "⚪")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Model", f"{predicted:+.1f}")
            c2.metric("Line", f"-{line}")
            c3.metric("Edge", f"{spread_diff:+.1f}", color)
            
            if rec != "NO EDGE":
                win_prob = min(80, 50 + abs(spread_diff) * 4)
                kelly = calculate_kelly(win_prob, sm['yes_price'] if rec == "COVERS" else 100 - sm['yes_price'], bankroll, kelly_fraction)
                st.link_button(f"🎯 BET {bet_team.upper()} → ${kelly['bet_amount']:.2f}", build_spread_url(sm['ticker']), use_container_width=True)

st.markdown("---")
st.caption("⚠️ Entertainment only. Not financial advice.")
