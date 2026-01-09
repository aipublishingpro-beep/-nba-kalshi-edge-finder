import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

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

KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NYK": "New York", "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia",
    "PHX": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
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

def calculate_edge(home_team, away_team, kalshi_price, home_rest, away_rest, home_injuries, away_injuries, travel_miles, ref_bias, weights):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 99, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": "", "ft_rate": 0.25, "reb_rate": 50, "three_pct": 0.35})
    
    rest_score = max(-6, min(6, (home_rest - away_rest) * 2))
    def_score = (away.get('def_rank', 15) - home.get('def_rank', 15)) * 0.15
    injury_score = (away_injuries - home_injuries) * 1.5
    pace_diff = home['pace'] - away['pace']
    pace_score = pace_diff * 0.1 if home['net_rating'] > away['net_rating'] else -pace_diff * 0.1
    net_score = (home['net_rating'] - away['net_rating']) * 0.8
    travel_score = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_score = (home['home_win_pct'] - 0.5) * 10 + (0.5 - away['away_win_pct']) * 10
    h2h_score = 1.5 if home.get('division') == away.get('division') else 0
    ref_score = ref_bias
    ft_score = (home.get('ft_rate', 0.25) - away.get('ft_rate', 0.25)) * 20
    reb_score = (home.get('reb_rate', 50) - away.get('reb_rate', 50)) * 0.3
    three_score = (home.get('three_pct', 0.35) - away.get('three_pct', 0.35)) * 50
    home_court = 3.0
    
    weighted_spread = (home_court + rest_score * weights['rest'] + def_score * weights['defense'] + injury_score * weights['injury'] +
                       pace_score * weights['pace'] + net_score * weights['net_rating'] + travel_score * weights['travel'] +
                       split_score * weights['splits'] + h2h_score * weights['h2h'] + ref_score * weights['refs'] +
                       ft_score * weights['ft'] + reb_score * weights['reb'] + three_score * weights['three'])
    
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    edge = home_win_prob - kalshi_price
    
    return {
        'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1), 'expected_spread': round(weighted_spread, 1),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW'),
        'factors': {
            'rest': round(rest_score * weights['rest'], 2), 'defense': round(def_score * weights['defense'], 2),
            'injury': round(injury_score * weights['injury'], 2), 'pace': round(pace_score * weights['pace'], 2),
            'net_rating': round(net_score * weights['net_rating'], 2), 'travel': round(travel_score * weights['travel'], 2),
            'splits': round(split_score * weights['splits'], 2), 'h2h': round(h2h_score * weights['h2h'], 2),
            'refs': round(ref_score * weights['refs'], 2), 'ft': round(ft_score * weights['ft'], 2),
            'reb': round(reb_score * weights['reb'], 2), 'three': round(three_score * weights['three'], 2), 'home_court': home_court
        },
        'raw': {
            'rest_diff': home_rest - away_rest, 'def_diff': away.get('def_rank', 15) - home.get('def_rank', 15),
            'injury_diff': away_injuries - home_injuries, 'pace_diff': round(pace_diff, 1),
            'net_diff': round(home['net_rating'] - away['net_rating'], 1), 'travel_miles': travel_miles,
            'same_div': home.get('division') == away.get('division'), 'ref_bias': ref_bias,
            'home_def_rank': home.get('def_rank', 15), 'away_def_rank': away.get('def_rank', 15),
            'home_win_pct': home['home_win_pct'], 'away_win_pct': away['away_win_pct']
        }
    }

def calculate_total_points(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13, "net_rating": 0})
    away = TEAM_STATS.get(away_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13, "net_rating": 0})
    
    base_total = ((home['ppg'] + away['opp_ppg']) / 2) + ((away['ppg'] + home['opp_ppg']) / 2)
    pace_adj = ((home['pace'] + away['pace']) / 2 - 99.5) * 0.5
    home_b2b, away_b2b = home_rest <= 1, away_rest <= 1
    rest_adj = -5 if home_b2b and away_b2b else (-2.5 if home_b2b or away_b2b else (3 if home_rest >= 2 and away_rest >= 2 else 0))
    three_adj = ((home.get('three_pa', 36) + away.get('three_pa', 36)) - 72) * 0.12
    three_adj += 2 if (home.get('three_pct', 0.35) + away.get('three_pct', 0.35)) / 2 > 0.37 else (-2 if (home.get('three_pct', 0.35) + away.get('three_pct', 0.35)) / 2 < 0.34 else 0)
    defense_adj = ((home['def_rating'] + away['def_rating']) / 2 - 112) * 0.4
    travel_adj = -3 if travel_miles > 2000 else (-2 if travel_miles > 1500 else (-1 if travel_miles > 1000 else 0))
    injury_adj = -(home_injuries + away_injuries) * 1.5
    oreb_adj = ((home.get('oreb_pct', 27) + away.get('oreb_pct', 27)) / 2 - 27) * 0.3
    tov_adj = -((home.get('tov_pct', 13) + away.get('tov_pct', 13)) / 2 - 13) * 0.4
    altitude_adj = 2.5 if home_team == "Denver" else (1.5 if home_team == "Utah" else 0)
    ot_adj = 1.5 if abs(home.get('net_rating', 0) - away.get('net_rating', 0)) < 3 else (0.75 if abs(home.get('net_rating', 0) - away.get('net_rating', 0)) < 6 else 0)
    
    predicted = base_total + pace_adj + rest_adj + three_adj + defense_adj + travel_adj + injury_adj + oreb_adj + tov_adj + altitude_adj + ot_adj
    return {'predicted_total': round(predicted, 1), 'factors': {'base_total': round(base_total, 1), 'pace': round(pace_adj, 1), 'rest': round(rest_adj, 1),
            '3pt': round(three_adj, 1), 'defense': round(defense_adj, 1), 'travel': round(travel_adj, 1), 'injury': round(injury_adj, 1),
            'oreb': round(oreb_adj, 1), 'turnover': round(tov_adj, 1), 'altitude': round(altitude_adj, 1), 'ot_prob': round(ot_adj, 1)}}

def calculate_spread(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "home_win_pct": 0.5, "away_win_pct": 0.5})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "home_win_pct": 0.5, "away_win_pct": 0.5})
    net_diff, home_court = home['net_rating'] - away['net_rating'], 3.5
    rest_adj, injury_adj = (home_rest - away_rest) * 1.5, (away_injuries - home_injuries) * 1.5
    travel_adj = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_adj = (home['home_win_pct'] - 0.5) * 5 + (0.5 - away['away_win_pct']) * 5
    predicted = net_diff + home_court + rest_adj + injury_adj + travel_adj + split_adj
    return {'predicted_spread': round(predicted, 1), 'factors': {'net_rating': round(net_diff, 1), 'home_court': home_court,
            'rest': round(rest_adj, 1), 'injury': round(injury_adj, 1), 'travel': round(travel_adj, 1), 'splits': round(split_adj, 1)}}

def parse_game_code(game_code):
    if len(game_code) < 6: return None, None, None
    away_team, home_team = KALSHI_ABBREV_MAP.get(game_code[-6:-3].upper()), KALSHI_ABBREV_MAP.get(game_code[-3:].upper())
    game_date_str = ""
    try:
        if len(game_code[:-6]) >= 7:
            month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
            game_date_str = f"{month_map.get(game_code[2:5].upper(), game_code[2:5])} {game_code[5:7]}"
    except: pass
    return game_date_str, away_team, home_team

def parse_event_ticker(event_ticker):
    try:
        parts = event_ticker.split('-')
        if len(parts) < 2: return "", None, None
        game_code = parts[1]
        month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
        game_date = f"{month_map.get(game_code[2:5].upper(), game_code[2:5])} {game_code[5:7]}"
        teams_part = game_code[7:]
        if len(teams_part) >= 6: return game_date, KALSHI_ABBREV_MAP.get(teams_part[:3].upper()), KALSHI_ABBREV_MAP.get(teams_part[3:6].upper())
        return game_date, None, None
    except: return "", None, None

@st.cache_data(ttl=300)
def fetch_kalshi_nba_markets():
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    def date_sort_key(g):
        try: return (month_order.get(g['game_date'].split()[0], 0), int(g['game_date'].split()[1]))
        except: return (99, 99)
    
    try:
        for m in requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100", timeout=10).json().get('markets', []):
            ticker = m.get('ticker', '')
            if '-' not in ticker: continue
            game_date, away_team, home_team = parse_game_code(ticker.split('-')[1])
            if not home_team: continue
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            markets['moneyline'].append({'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid, 'volume': m.get('volume', 0), 'game_date': game_date})
    except: pass
    
    try:
        for m in requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open&limit=200", timeout=10).json().get('markets', []):
            game_date, away_team, home_team = parse_event_ticker(m.get('event_ticker', ''))
            if not home_team: continue
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            markets['totals'].append({'ticker': m.get('ticker', ''), 'title': m.get('title', ''), 'away_team': away_team, 'home_team': home_team,
                'line': m.get('floor_strike', 0), 'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid, 'volume': m.get('volume', 0), 'game_date': game_date})
    except: pass
    
    try:
        for m in requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200", timeout=10).json().get('markets', []):
            game_date, away_team, home_team = parse_event_ticker(m.get('event_ticker', ''))
            if not home_team: continue
            ticker, title = m.get('ticker', ''), m.get('title', '')
            yes_bid, yes_ask = m.get('yes_bid', 0) or 0, m.get('yes_ask', 0) or 0
            spread_team = KALSHI_ABBREV_MAP.get(ticker.split('-')[-1][:3].upper()) if len(ticker.split('-')) >= 3 else None
            if not spread_team:
                for t in [home_team, away_team]:
                    if t and t.lower() in title.lower(): spread_team = t; break
            markets['spreads'].append({'ticker': ticker, 'title': title, 'away_team': away_team, 'home_team': home_team, 'spread_team': spread_team or home_team,
                'line': m.get('floor_strike', 0), 'yes_price': (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid, 'volume': m.get('volume', 0), 'game_date': game_date})
    except: pass
    
    seen = {}
    for g in markets['moneyline']:
        key = f"{g['away_team']}@{g['home_team']}_{g['game_date']}"
        if key not in seen or g['volume'] > seen[key]['volume']: seen[key] = g
    markets['moneyline'], markets['totals'], markets['spreads'] = sorted(seen.values(), key=date_sort_key), sorted(markets['totals'], key=date_sort_key), sorted(markets['spreads'], key=date_sort_key)
    return markets

@st.cache_data(ttl=14400)
def fetch_nba_injuries():
    try:
        soup = BeautifulSoup(requests.get("https://www.espn.com/nba/injuries", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).content, 'lxml')
        injuries = {}
        for team in soup.find_all('div', class_='ResponsiveTable'):
            header = team.find_previous('div', class_='Table__Title')
            if header:
                injuries[header.text.strip()] = [f"{row.find_all('td')[0].text.strip()} ({row.find_all('td')[2].text.strip()})" for row in team.find_all('tr')[1:] if len(row.find_all('td')) >= 3]
        return injuries
    except: return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    try:
        team_last_game, today = {}, datetime.now()
        for market in requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10).json().get('markets', []):
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
st.markdown("**12-Factor Edge Model** — Moneyline • Totals • Spreads")
st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | 🟢 = BUY YES | 🔴 = BUY NO")

# ========== SIDEBAR WITH 12 FACTORS ==========
st.sidebar.header("⚙️ Factor Weights")
st.sidebar.caption("0 = off, 1 = normal, 2 = double impact")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Factor Legend")
st.sidebar.markdown("""
| Factor | Measures |
|--------|----------|
| 🛏️ Rest | Days since last game |
| 🛡️ Defense | Defensive rank (1-30) |
| 🏥 Injury | # injured players |
| ⚡ Pace | Possessions/game |
| 📊 Net Rtg | Point diff per 100 |
| ✈️ Travel | Away team miles |
| 🏠 Splits | Home/Away win % |
| ⚔️ H2H | Division rivalry |
| 👨‍⚖️ Refs | Ref home bias |
| 🎯 FT | Free throw rate |
| 🏀 Reb | Rebound rate |
| 🎯 3PT | 3-point % |
""")

st.sidebar.markdown("---")
with st.sidebar.expander("🏀 Core Factors", expanded=True):
    w_rest = st.slider("🛏️ Rest", 0.0, 2.0, 1.0, 0.1, key="w1")
    w_def = st.slider("🛡️ Defense", 0.0, 2.0, 1.0, 0.1, key="w2")
    w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1, key="w3")
    w_pace = st.slider("⚡ Pace", 0.0, 2.0, 1.0, 0.1, key="w4")
    w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1, key="w5")
    w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1, key="w6")

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
st.sidebar.header("🎯 Settings")
default_home_rest = st.sidebar.number_input("Default Home Rest", 0, 7, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 0, 7, 2)
st.sidebar.caption("Ref Bias: 0=Away | 1=Neutral | 2=Home")
default_ref_bias = st.sidebar.slider("Default Ref Bias", 0.0, 2.0, 1.0, 0.1)
min_edge = st.sidebar.slider("Min Edge %", 0, 25, 5)

st.sidebar.markdown("---")
st.sidebar.header("💰 Kelly Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.slider("Kelly Fraction %", 1, 100, 10, 1)
kelly_fraction = kelly_fraction / 100  # Convert to decimal
st.sidebar.markdown(f"""
**What is Kelly?**

Kelly tells you how much of your bankroll to risk when you have an edge, so you grow fastest without blowing up.

Not *if* you should bet — *how big* the bet should be.

**Your setting:** {int(kelly_fraction*100)}% Kelly (lower = safer)
""")

if st.sidebar.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 API Status")
markets, injuries, rest_days = fetch_kalshi_nba_markets(), fetch_nba_injuries(), fetch_rest_days()
st.sidebar.write(f"Moneyline: {len(markets['moneyline'])}")
st.sidebar.write(f"Totals: {len(markets['totals'])}")
st.sidebar.write(f"Spreads: {len(markets['spreads'])}")

# ========== TOP 3 EDGES SECTION ==========
st.markdown("### 🔥 Top 3 Edges Today")
st.caption(f"💰 **Kelly Criterion:** Bigger edge = bigger bet. Your {int(kelly_fraction*100)}% Kelly setting reduces full bet for safety. Adjust in sidebar.")

top_edges = []

# Collect moneyline edges
for game in markets['moneyline']:
    home, away = game['home_team'], game['away_team']
    home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
    travel = calculate_travel_distance(away, home)
    home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
    analysis = calculate_edge(home, away, game['yes_price'], home_rest, away_rest, home_inj, away_inj, travel, default_ref_bias, weights)
    if analysis['recommendation'] != 'NO EDGE':
        bet_team = home if analysis['recommendation'] == 'BUY YES' else away
        kelly = calculate_kelly(analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob'], 
                                game['yes_price'] if analysis['recommendation'] == 'BUY YES' else 100 - game['yes_price'], bankroll, kelly_fraction)
        top_edges.append({
            'type': 'ML', 'game': f"{away} @ {home}", 'date': game['game_date'],
            'edge': abs(analysis['edge']), 'edge_raw': analysis['edge'],
            'rec': f"{bet_team} WINS", 'confidence': analysis['confidence'],
            'bet_amount': kelly['bet_amount'], 'kelly_pct': kelly['adj_kelly_pct'],
            'url': f"https://kalshi.com/markets/kxnbagame/{game['ticker'].lower()}",
            'color': '🟢' if analysis['recommendation'] == 'BUY YES' else '🔴'
        })

# Collect totals edges
for tm in markets['totals']:
    home, away, line = tm['home_team'], tm['away_team'], tm['line']
    home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
    travel = calculate_travel_distance(away, home)
    home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
    totals = calculate_total_points(home, away, home_rest, away_rest, home_inj, away_inj, travel)
    diff = totals['predicted_total'] - line
    if abs(diff) > 3:
        rec = "OVER" if diff > 3 else "UNDER"
        win_prob = min(85, 50 + abs(diff) * 5)
        kelly = calculate_kelly(win_prob, tm['yes_price'] if rec == "OVER" else 100 - tm['yes_price'], bankroll, kelly_fraction)
        top_edges.append({
            'type': 'TOT', 'game': f"{away} @ {home}", 'date': tm['game_date'],
            'edge': abs(diff), 'edge_raw': diff,
            'rec': f"{rec} {line}", 'confidence': 'HIGH' if abs(diff) > 6 else 'MEDIUM',
            'bet_amount': kelly['bet_amount'], 'kelly_pct': kelly['adj_kelly_pct'],
            'url': f"https://kalshi.com/markets/kxnbatotal/{tm['ticker'].lower()}",
            'color': '🟢' if rec == "OVER" else '🔴'
        })

# Collect spread edges
for sm in markets['spreads']:
    home, away, line, spread_team = sm['home_team'], sm['away_team'], sm['line'], sm['spread_team']
    home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
    travel = calculate_travel_distance(away, home)
    home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
    spread = calculate_spread(home, away, home_rest, away_rest, home_inj, away_inj, travel)
    predicted = spread['predicted_spread']
    spread_diff = (predicted - line) if spread_team == home else (-predicted - line)
    if abs(spread_diff) > 3:
        if spread_diff > 3:
            rec, bet_team = f"{spread_team} COVERS -{line}", spread_team
            win_prob = min(80, 50 + spread_diff * 4)
            kelly = calculate_kelly(win_prob, sm['yes_price'], bankroll, kelly_fraction)
            color = '🟢'
        else:
            rec = f"{spread_team} MISSES -{line}"
            bet_team = away if spread_team == home else home
            win_prob = min(80, 50 + abs(spread_diff) * 4)
            kelly = calculate_kelly(win_prob, 100 - sm['yes_price'], bankroll, kelly_fraction)
            color = '🔴'
        top_edges.append({
            'type': 'SPR', 'game': f"{away} @ {home}", 'date': sm['game_date'],
            'edge': abs(spread_diff), 'edge_raw': spread_diff,
            'rec': rec, 'confidence': 'HIGH' if abs(spread_diff) > 6 else 'MEDIUM',
            'bet_amount': kelly['bet_amount'], 'kelly_pct': kelly['adj_kelly_pct'],
            'url': f"https://kalshi.com/markets/kxnbaspread/{sm['ticker'].lower()}",
            'color': color
        })

# Sort by edge and show top 3
top_edges = sorted(top_edges, key=lambda x: x['edge'], reverse=True)[:3]

if top_edges:
    for i, edge in enumerate(top_edges, 1):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**#{i} {edge['color']} [{edge['type']}] {edge['date']} | {edge['game']}** → **{edge['rec']}** ({edge['edge']:.1f}% edge) • {edge['confidence']}")
        with col2:
            st.link_button(f"{edge['rec']} ${edge['bet_amount']:.0f}", edge['url'], use_container_width=True)
    st.markdown("---")
else:
    st.info("No high-confidence edges found. Adjust Min Edge % in sidebar.")
    st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎯 Moneyline", "📊 Over/Under Totals", "📏 Spreads"])

# TAB 1: MONEYLINE
with tab1:
    st.markdown("### 🎯 Moneyline Analysis (12 Factors)")
    for game in markets['moneyline']:
        home, away = game['home_team'], game['away_team']
        home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
        travel = calculate_travel_distance(away, home)
        home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
        analysis = calculate_edge(home, away, game['yes_price'], home_rest, away_rest, home_inj, away_inj, travel, default_ref_bias, weights)
        if abs(analysis['edge']) < min_edge: continue
        
        color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
        bet_team = home if analysis['recommendation'] == 'BUY YES' else away
        
        with st.expander(f"{color} {game['game_date']} | {away} @ {home} | Edge: {analysis['edge']:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi Price", f"{game['yes_price']:.0f}¢ {home}")
            c2.metric("Model Win%", f"{analysis['home_win_prob']:.1f}%")
            c3.metric("Edge", f"{analysis['edge']:+.1f}%", analysis['confidence'])
            
            kelly = calculate_kelly(analysis['home_win_prob'], game['yes_price'], bankroll, kelly_fraction) if analysis['recommendation'] == 'BUY YES' else calculate_kelly(100 - analysis['home_win_prob'], 100 - game['yes_price'], bankroll, kelly_fraction)
            
            st.markdown("---")
            st.markdown("**💰 Kelly Criterion**")
            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.metric(f"Bet {bet_team}", f"${kelly['bet_amount']:.2f}")
            kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
            kc3.metric("EV/Dollar", f"${kelly['ev_per_dollar']:.3f}")
            kc4.metric("EV on Bet", f"${kelly['ev_on_bet']:+.2f}")
            
            st.markdown("---")
            st.markdown("**📈 12-Factor Breakdown**")
            f, r = analysis['factors'], analysis['raw']
            fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
            fc1.metric("🛏️ Rest", f"{f['rest']:+.2f}", f"H:{home_rest}d A:{away_rest}d")
            fc2.metric("🛡️ Defense", f"{f['defense']:+.2f}", f"H:#{r['home_def_rank']} A:#{r['away_def_rank']}")
            fc3.metric("🏥 Injury", f"{f['injury']:+.2f}", f"Diff:{r['injury_diff']:+d}")
            fc4.metric("⚡ Pace", f"{f['pace']:+.2f}", f"Diff:{r['pace_diff']:+.1f}")
            fc5.metric("📊 Net Rtg", f"{f['net_rating']:+.2f}", f"Diff:{r['net_diff']:+.1f}")
            fc6.metric("✈️ Travel", f"{f['travel']:+.2f}", f"{r['travel_miles']}mi")
            
            fc7, fc8, fc9, fc10, fc11, fc12 = st.columns(6)
            fc7.metric("🏠 Splits", f"{f['splits']:+.2f}", f"H:{r['home_win_pct']:.0%} A:{r['away_win_pct']:.0%}")
            fc8.metric("⚔️ H2H", f"{f['h2h']:+.2f}", "DIV" if r['same_div'] else "—")
            fc9.metric("👨‍⚖️ Refs", f"{f['refs']:+.2f}", f"Bias:{r['ref_bias']:.1f}")
            fc10.metric("🎯 FT", f"{f['ft']:+.2f}")
            fc11.metric("🏀 Reb", f"{f['reb']:+.2f}")
            fc12.metric("🎯 3PT", f"{f['three']:+.2f}")
            
            st.caption(f"🏠 Home Court: +{f['home_court']} (baseline)")
            
            url = f"https://kalshi.com/markets/kxnbagame/{game['ticker'].lower()}"
            st.link_button(f"🎯 BET {bet_team.upper()} TO WIN → ${kelly['bet_amount']:.2f}", url, use_container_width=True)

# TAB 2: TOTALS
with tab2:
    st.markdown("### 📊 Over/Under Totals (11 Factors)")
    if markets['totals']:
        st.success(f"✅ {len(markets['totals'])} totals markets")
        for tm in markets['totals']:
            home, away, line, yes_price = tm['home_team'], tm['away_team'], tm['line'], tm['yes_price']
            home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
            travel = calculate_travel_distance(away, home)
            home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
            totals = calculate_total_points(home, away, home_rest, away_rest, home_inj, away_inj, travel)
            predicted, diff = totals['predicted_total'], totals['predicted_total'] - line
            
            if diff > 3: rec, rec_color, win_prob = "OVER", "🟢", min(85, 50 + diff * 5)
            elif diff < -3: rec, rec_color, win_prob = "UNDER", "🔴", min(85, 50 + abs(diff) * 5)
            else: rec, rec_color, win_prob = "NO EDGE", "⚪", 50
            if rec == "NO EDGE" and min_edge > 0: continue
            
            with st.expander(f"{rec_color} {tm['game_date']} | {away} @ {home} | Line: {line} | {rec} ({diff:+.1f}pts)"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Predicted", f"{predicted}")
                c2.metric("Line", f"{line}")
                c3.metric("Edge", f"{diff:+.1f} pts")
                
                kelly = calculate_kelly(win_prob, yes_price, bankroll, kelly_fraction) if rec == "OVER" else (calculate_kelly(win_prob, 100 - yes_price, bankroll, kelly_fraction) if rec == "UNDER" else {'bet_amount': 0, 'adj_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0})
                bet_label = f"Bet OVER {line}" if rec == "OVER" else (f"Bet UNDER {line}" if rec == "UNDER" else "No Bet")
                
                st.markdown("---")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric(bet_label, f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/$", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV", f"${kelly['ev_on_bet']:+.2f}")
                
                st.markdown("---")
                st.markdown("**📈 11-Factor Breakdown**")
                f = totals['factors']
                fc1, fc2, fc3, fc4 = st.columns(4)
                fc1.metric("Base", f"{f['base_total']}")
                fc2.metric("Pace", f"{f['pace']:+.1f}")
                fc3.metric("Rest", f"{f['rest']:+.1f}")
                fc4.metric("3PT", f"{f['3pt']:+.1f}")
                fc5, fc6, fc7, fc8 = st.columns(4)
                fc5.metric("Defense", f"{f['defense']:+.1f}")
                fc6.metric("Travel", f"{f['travel']:+.1f}")
                fc7.metric("Injury", f"{f['injury']:+.1f}")
                fc8.metric("OREB", f"{f['oreb']:+.1f}")
                fc9, fc10, fc11, _ = st.columns(4)
                fc9.metric("TOV", f"{f['turnover']:+.1f}")
                fc10.metric("Altitude", f"{f['altitude']:+.1f}")
                fc11.metric("OT Prob", f"{f['ot_prob']:+.1f}")
                
                url = f"https://kalshi.com/markets/kxnbatotal/{tm['ticker'].lower()}"
                if rec == "OVER": st.link_button(f"🎯 BET OVER {line} → ${kelly['bet_amount']:.2f}", url, use_container_width=True)
                elif rec == "UNDER": st.link_button(f"🎯 BET UNDER {line} → ${kelly['bet_amount']:.2f}", url, use_container_width=True)
    else:
        st.warning("No totals markets found")

# TAB 3: SPREADS
with tab3:
    st.markdown("### 📏 Spread Analysis")
    if markets['spreads']:
        st.success(f"✅ {len(markets['spreads'])} spread markets")
        for sm in markets['spreads']:
            home, away, line, yes_price, spread_team = sm['home_team'], sm['away_team'], sm['line'], sm['yes_price'], sm['spread_team']
            home_inj, away_inj = len(injuries.get(home, [])), len(injuries.get(away, []))
            travel = calculate_travel_distance(away, home)
            home_rest, away_rest = rest_days.get(home, default_home_rest), rest_days.get(away, default_away_rest)
            spread = calculate_spread(home, away, home_rest, away_rest, home_inj, away_inj, travel)
            predicted = spread['predicted_spread']
            
            if spread_team == home:
                spread_diff = predicted - line
                if spread_diff > 3: rec, win_prob, bet_team = f"{home} COVERS", min(80, 50 + spread_diff * 4), home
                elif spread_diff < -3: rec, win_prob, bet_team = f"{home} DOESN'T COVER", min(80, 50 + abs(spread_diff) * 4), away
                else: rec, win_prob, bet_team = "NO EDGE", 50, None
            else:
                spread_diff = -predicted - line
                if spread_diff > 3: rec, win_prob, bet_team = f"{away} COVERS", min(80, 50 + spread_diff * 4), away
                elif spread_diff < -3: rec, win_prob, bet_team = f"{away} DOESN'T COVER", min(80, 50 + abs(spread_diff) * 4), home
                else: rec, win_prob, bet_team = "NO EDGE", 50, None
            
            rec_color = "🟢" if "COVERS" in rec and "DOESN'T" not in rec else ("🔴" if "DOESN'T" in rec else "⚪")
            if rec == "NO EDGE" and min_edge > 0: continue
            
            with st.expander(f"{rec_color} {sm['game_date']} | {away} @ {home} | {spread_team} -{line} | {rec}"):
                st.caption(f"**Kalshi:** {sm['title']}")
                c1, c2, c3 = st.columns(3)
                # Show model spread from SAME TEAM's perspective as Kalshi for easy comparison
                if spread_team == home:
                    model_spread_display = f"{spread_team} {predicted:+.1f}"
                else:
                    # Kalshi is asking about away team, flip our home-based spread
                    model_spread_display = f"{spread_team} {-predicted:+.1f}"
                c1.metric("Model Spread", model_spread_display)
                c2.metric("Kalshi Line", f"{spread_team} -{line}")
                c3.metric("Edge", f"{spread_diff:+.1f} pts")
                
                if "COVERS" in rec and "DOESN'T" not in rec:
                    kelly, bet_label = calculate_kelly(win_prob, yes_price, bankroll, kelly_fraction), f"Bet {bet_team} COVERS"
                    btn_text = f"🎯 BET {bet_team.upper()} COVERS -{line} → ${kelly['bet_amount']:.2f}"
                elif "DOESN'T" in rec:
                    kelly, bet_label = calculate_kelly(win_prob, 100 - yes_price, bankroll, kelly_fraction), f"Bet {spread_team} MISSES"
                    btn_text = f"🎯 BET {spread_team.upper()} DOESN'T COVER → ${kelly['bet_amount']:.2f}"
                else:
                    kelly, bet_label, btn_text = {'bet_amount': 0, 'adj_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0}, "No Bet", None
                
                st.markdown("---")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric(bet_label, f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/$", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV", f"${kelly['ev_on_bet']:+.2f}")
                
                if btn_text:
                    url = f"https://kalshi.com/markets/kxnbaspread/{sm['ticker'].lower()}"
                    st.link_button(btn_text, url, use_container_width=True)
    else:
        st.warning("No spread markets found")

st.markdown("---")
st.caption("⚠️ **Disclaimer:** Entertainment only. Not financial advice.")
