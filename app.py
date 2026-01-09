import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math
import re

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

# Team stats (2024-25 season) - Full stats for totals prediction
TEAM_STATS = {
    "Atlanta": {"net_rating": -1.5, "off_rating": 114.2, "def_rating": 115.7, "pace": 100.2, "ppg": 118.2, "opp_ppg": 120.1, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pa": 38.5, "three_pct": 0.355, "oreb_pct": 27.5, "tov_pct": 13.2},
    "Boston": {"net_rating": 10.5, "off_rating": 120.5, "def_rating": 110.0, "pace": 98.5, "ppg": 120.8, "opp_ppg": 110.3, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "three_pa": 42.5, "three_pct": 0.385, "oreb_pct": 25.8, "tov_pct": 12.5},
    "Brooklyn": {"net_rating": -5.2, "off_rating": 109.8, "def_rating": 115.0, "pace": 99.8, "ppg": 108.5, "opp_ppg": 113.7, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pa": 35.2, "three_pct": 0.345, "oreb_pct": 26.2, "tov_pct": 14.1},
    "Charlotte": {"net_rating": -6.8, "off_rating": 108.5, "def_rating": 115.3, "pace": 101.5, "ppg": 106.8, "opp_ppg": 113.6, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pa": 34.8, "three_pct": 0.335, "oreb_pct": 28.1, "tov_pct": 14.5},
    "Chicago": {"net_rating": -3.5, "off_rating": 111.2, "def_rating": 114.7, "pace": 98.2, "ppg": 111.5, "opp_ppg": 115.0, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pa": 33.5, "three_pct": 0.348, "oreb_pct": 27.0, "tov_pct": 13.8},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.5, "def_rating": 108.7, "pace": 97.5, "ppg": 118.2, "opp_ppg": 108.4, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pa": 36.2, "three_pct": 0.372, "oreb_pct": 28.5, "tov_pct": 12.2},
    "Dallas": {"net_rating": 3.2, "off_rating": 115.8, "def_rating": 112.6, "pace": 99.5, "ppg": 117.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pa": 40.2, "three_pct": 0.365, "oreb_pct": 26.5, "tov_pct": 13.0},
    "Denver": {"net_rating": 5.5, "off_rating": 117.2, "def_rating": 111.7, "pace": 98.8, "ppg": 116.5, "opp_ppg": 111.0, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pa": 35.8, "three_pct": 0.358, "oreb_pct": 29.2, "tov_pct": 12.8, "altitude": True},
    "Detroit": {"net_rating": -4.8, "off_rating": 110.5, "def_rating": 115.3, "pace": 100.5, "ppg": 110.2, "opp_ppg": 115.0, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pa": 36.5, "three_pct": 0.340, "oreb_pct": 27.8, "tov_pct": 14.2},
    "Golden State": {"net_rating": 2.8, "off_rating": 115.2, "def_rating": 112.4, "pace": 99.2, "ppg": 115.8, "opp_ppg": 113.0, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 43.5, "three_pct": 0.378, "oreb_pct": 25.2, "tov_pct": 13.5},
    "Houston": {"net_rating": 4.5, "off_rating": 114.8, "def_rating": 110.3, "pace": 99.8, "ppg": 114.5, "opp_ppg": 110.0, "home_win_pct": 0.60, "away_win_pct": 0.48, "division": "Southwest", "three_pa": 41.2, "three_pct": 0.352, "oreb_pct": 29.5, "tov_pct": 13.2},
    "Indiana": {"net_rating": 1.2, "off_rating": 118.5, "def_rating": 117.3, "pace": 102.5, "ppg": 123.2, "opp_ppg": 122.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central", "three_pa": 39.8, "three_pct": 0.368, "oreb_pct": 28.0, "tov_pct": 12.5},
    "LA Clippers": {"net_rating": 0.5, "off_rating": 112.8, "def_rating": 112.3, "pace": 97.8, "ppg": 110.5, "opp_ppg": 110.0, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "three_pa": 36.0, "three_pct": 0.355, "oreb_pct": 26.8, "tov_pct": 13.0},
    "LA Lakers": {"net_rating": 2.5, "off_rating": 114.5, "def_rating": 112.0, "pace": 98.5, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.62, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 34.5, "three_pct": 0.345, "oreb_pct": 28.2, "tov_pct": 13.5},
    "Memphis": {"net_rating": 3.8, "off_rating": 116.2, "def_rating": 112.4, "pace": 100.8, "ppg": 118.5, "opp_ppg": 114.7, "home_win_pct": 0.58, "away_win_pct": 0.45, "division": "Southwest", "three_pa": 35.0, "three_pct": 0.342, "oreb_pct": 30.5, "tov_pct": 13.8},
    "Miami": {"net_rating": 1.8, "off_rating": 112.5, "def_rating": 110.7, "pace": 97.2, "ppg": 110.8, "opp_ppg": 109.0, "home_win_pct": 0.60, "away_win_pct": 0.38, "division": "Southeast", "three_pa": 38.5, "three_pct": 0.362, "oreb_pct": 26.0, "tov_pct": 12.8},
    "Milwaukee": {"net_rating": 4.2, "off_rating": 116.8, "def_rating": 112.6, "pace": 98.8, "ppg": 117.5, "opp_ppg": 113.3, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Central", "three_pa": 40.0, "three_pct": 0.358, "oreb_pct": 27.5, "tov_pct": 12.2},
    "Minnesota": {"net_rating": 6.5, "off_rating": 113.5, "def_rating": 107.0, "pace": 97.8, "ppg": 112.2, "opp_ppg": 105.7, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Northwest", "three_pa": 37.2, "three_pct": 0.355, "oreb_pct": 29.0, "tov_pct": 12.5},
    "New Orleans": {"net_rating": -2.8, "off_rating": 112.8, "def_rating": 115.6, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.3, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southwest", "three_pa": 36.8, "three_pct": 0.348, "oreb_pct": 28.5, "tov_pct": 14.0},
    "New York": {"net_rating": 5.8, "off_rating": 117.2, "def_rating": 111.4, "pace": 97.5, "ppg": 116.8, "opp_ppg": 111.0, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Atlantic", "three_pa": 37.5, "three_pct": 0.365, "oreb_pct": 29.8, "tov_pct": 12.0},
    "Oklahoma City": {"net_rating": 11.2, "off_rating": 119.8, "def_rating": 108.6, "pace": 98.2, "ppg": 119.5, "opp_ppg": 108.3, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pa": 39.5, "three_pct": 0.375, "oreb_pct": 30.2, "tov_pct": 11.8},
    "Orlando": {"net_rating": 3.5, "off_rating": 111.2, "def_rating": 107.7, "pace": 96.8, "ppg": 108.5, "opp_ppg": 105.0, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast", "three_pa": 35.5, "three_pct": 0.342, "oreb_pct": 30.0, "tov_pct": 13.2},
    "Philadelphia": {"net_rating": 0.8, "off_rating": 113.5, "def_rating": 112.7, "pace": 98.5, "ppg": 114.2, "opp_ppg": 113.4, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Atlantic", "three_pa": 36.2, "three_pct": 0.352, "oreb_pct": 28.0, "tov_pct": 13.5},
    "Phoenix": {"net_rating": 2.2, "off_rating": 115.5, "def_rating": 113.3, "pace": 99.2, "ppg": 116.2, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 37.0, "three_pct": 0.358, "oreb_pct": 26.5, "tov_pct": 13.0},
    "Portland": {"net_rating": -7.5, "off_rating": 108.2, "def_rating": 115.7, "pace": 100.2, "ppg": 107.5, "opp_ppg": 115.0, "home_win_pct": 0.35, "away_win_pct": 0.20, "division": "Northwest", "three_pa": 34.0, "three_pct": 0.338, "oreb_pct": 27.0, "tov_pct": 14.5},
    "Sacramento": {"net_rating": -1.2, "off_rating": 114.5, "def_rating": 115.7, "pace": 100.5, "ppg": 117.8, "opp_ppg": 119.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific", "three_pa": 36.5, "three_pct": 0.362, "oreb_pct": 27.2, "tov_pct": 13.8},
    "San Antonio": {"net_rating": -4.5, "off_rating": 111.8, "def_rating": 116.3, "pace": 99.8, "ppg": 112.5, "opp_ppg": 117.0, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "three_pa": 37.8, "three_pct": 0.345, "oreb_pct": 28.5, "tov_pct": 14.2},
    "Toronto": {"net_rating": -3.2, "off_rating": 112.2, "def_rating": 115.4, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.7, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic", "three_pa": 38.0, "three_pct": 0.348, "oreb_pct": 27.8, "tov_pct": 13.5},
    "Utah": {"net_rating": -8.5, "off_rating": 108.5, "def_rating": 117.0, "pace": 100.8, "ppg": 108.2, "opp_ppg": 116.7, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pa": 39.0, "three_pct": 0.335, "oreb_pct": 26.5, "tov_pct": 15.0, "altitude": True},
    "Washington": {"net_rating": -9.2, "off_rating": 107.8, "def_rating": 117.0, "pace": 101.2, "ppg": 108.5, "opp_ppg": 117.7, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast", "three_pa": 35.5, "three_pct": 0.332, "oreb_pct": 26.0, "tov_pct": 15.2},
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

def calculate_kelly(win_prob, kalshi_price, bankroll=1000, fraction=0.25):
    p = win_prob / 100
    q = 1 - p
    b = (100 - kalshi_price) / kalshi_price if kalshi_price > 0 else 0
    kelly_pct = (b * p - q) / b if b > 0 else 0
    kelly_pct = max(0, kelly_pct)
    adj_kelly = kelly_pct * fraction
    bet_amount = bankroll * adj_kelly
    profit_if_win = (100 - kalshi_price) / kalshi_price if kalshi_price > 0 else 0
    ev_per_dollar = (p * profit_if_win) - (q * 1)
    ev_on_bet = ev_per_dollar * bet_amount
    return {
        'full_kelly_pct': round(kelly_pct * 100, 1),
        'adj_kelly_pct': round(adj_kelly * 100, 1),
        'bet_amount': round(bet_amount, 2),
        'edge_pct': round((p - kalshi_price/100) * 100, 1),
        'ev_per_dollar': round(ev_per_dollar, 3),
        'ev_on_bet': round(ev_on_bet, 2)
    }

def calculate_total_points(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "off_rating": 112, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13})
    away = TEAM_STATS.get(away_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "off_rating": 112, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13})
    
    home_expected = (home['ppg'] + away['opp_ppg']) / 2
    away_expected = (away['ppg'] + home['opp_ppg']) / 2
    base_total = home_expected + away_expected
    
    avg_pace = (home['pace'] + away['pace']) / 2
    pace_adj = (avg_pace - 99.5) * 0.5
    
    home_b2b = home_rest == 0 or home_rest == 1
    away_b2b = away_rest == 0 or away_rest == 1
    if home_b2b and away_b2b: rest_adj = -5
    elif home_b2b: rest_adj = -2.5
    elif away_b2b: rest_adj = -2.5
    elif home_rest >= 2 and away_rest >= 2: rest_adj = 3
    else: rest_adj = 0
    
    combined_3pa = home.get('three_pa', 36) + away.get('three_pa', 36)
    three_volume_adj = (combined_3pa - 72) * 0.12
    avg_3pct = (home.get('three_pct', 0.35) + away.get('three_pct', 0.35)) / 2
    three_pct_adj = 2 if avg_3pct > 0.37 else (-2 if avg_3pct < 0.34 else 0)
    three_adj = three_volume_adj + three_pct_adj
    
    avg_def_rating = (home['def_rating'] + away['def_rating']) / 2
    defense_adj = (avg_def_rating - 112) * 0.4
    
    travel_adj = -3 if travel_miles > 2000 else (-2 if travel_miles > 1500 else (-1 if travel_miles > 1000 else 0))
    injury_adj = -(home_injuries + away_injuries) * 1.5
    
    avg_oreb = (home.get('oreb_pct', 27) + away.get('oreb_pct', 27)) / 2
    oreb_adj = (avg_oreb - 27) * 0.3
    
    avg_tov = (home.get('tov_pct', 13) + away.get('tov_pct', 13)) / 2
    tov_adj = -(avg_tov - 13) * 0.4
    
    altitude_adj = 2.5 if home_team == "Denver" else (1.5 if home_team == "Utah" else 0)
    
    spread_diff = abs(home['net_rating'] - away['net_rating'])
    ot_adj = 1.5 if spread_diff < 3 else (0.75 if spread_diff < 6 else 0)
    
    predicted_total = base_total + pace_adj + rest_adj + three_adj + defense_adj + travel_adj + injury_adj + oreb_adj + tov_adj + altitude_adj + ot_adj
    
    return {
        'predicted_total': round(predicted_total, 1),
        'factors': {
            'base_total': round(base_total, 1), 'pace': round(pace_adj, 1), 'rest': round(rest_adj, 1),
            '3pt': round(three_adj, 1), 'defense': round(defense_adj, 1), 'travel': round(travel_adj, 1),
            'injury': round(injury_adj, 1), 'oreb': round(oreb_adj, 1), 'turnover': round(tov_adj, 1),
            'altitude': round(altitude_adj, 1), 'ot_prob': round(ot_adj, 1)
        }
    }

def calculate_spread(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "home_win_pct": 0.5})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "away_win_pct": 0.5})
    
    net_diff = home['net_rating'] - away['net_rating']
    home_court = 3.5
    rest_adj = (home_rest - away_rest) * 1.5
    injury_adj = (away_injuries - home_injuries) * 1.5
    travel_adj = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_adj = (home['home_win_pct'] - 0.5) * 5 + (0.5 - away['away_win_pct']) * 5
    
    predicted_spread = net_diff + home_court + rest_adj + injury_adj + travel_adj + split_adj
    
    return {
        'predicted_spread': round(predicted_spread, 1),
        'factors': {
            'net_rating': round(net_diff, 1), 'home_court': home_court, 'rest': round(rest_adj, 1),
            'injury': round(injury_adj, 1), 'travel': round(travel_adj, 1), 'splits': round(split_adj, 1)
        }
    }

def calculate_moneyline(home_team, away_team, kalshi_price, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    spread_data = calculate_spread(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles)
    spread = spread_data['predicted_spread']
    home_win_prob = max(5, min(95, 50 + spread * 2.5))
    edge = home_win_prob - kalshi_price
    return {
        'home_win_prob': round(home_win_prob, 1), 'edge': round(edge, 1), 'spread': round(spread, 1),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW')
    }

def parse_game_code(game_code):
    """Parse moneyline game code like '26JAN09NOPWAS'"""
    if len(game_code) < 6:
        return None, None, None
    away_abbrev = game_code[-6:-3].upper()
    home_abbrev = game_code[-3:].upper()
    away_team = KALSHI_ABBREV_MAP.get(away_abbrev, away_abbrev)
    home_team = KALSHI_ABBREV_MAP.get(home_abbrev, home_abbrev)
    game_date_str = ""
    try:
        date_part = game_code[:-6]
        if len(date_part) >= 7:
            month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
                         'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
            game_date_str = f"{month_map.get(date_part[2:5].upper(), date_part[2:5])} {date_part[5:7]}"
    except: pass
    return game_date_str, away_team, home_team

def parse_event_ticker(event_ticker):
    """Parse event_ticker like 'KXNBATOTAL-26JAN09NOPWAS' to get date and teams"""
    try:
        parts = event_ticker.split('-')
        if len(parts) < 2:
            return "", None, None
        game_code = parts[1]  # "26JAN09NOPWAS"
        month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 
                    'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AUG': 'Aug', 
                    'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
        month_str = game_code[2:5].upper()
        day_str = game_code[5:7]
        game_date = f"{month_map.get(month_str, month_str)} {day_str}"
        teams_part = game_code[7:]  # "NOPWAS"
        if len(teams_part) >= 6:
            away_abbrev = teams_part[:3].upper()
            home_abbrev = teams_part[3:6].upper()
            away_team = KALSHI_ABBREV_MAP.get(away_abbrev, away_abbrev)
            home_team = KALSHI_ABBREV_MAP.get(home_abbrev, home_abbrev)
            return game_date, away_team, home_team
        return game_date, None, None
    except:
        return "", None, None

@st.cache_data(ttl=300)
def fetch_kalshi_nba_markets():
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    
    month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                   'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    def date_sort_key(g):
        try:
            parts = g['game_date'].split()
            return (month_order.get(parts[0], 0), int(parts[1]))
        except: return (99, 99)
    
    # === MONEYLINE ===
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100"
        resp = requests.get(url, timeout=10)
        for m in resp.json().get('markets', []):
            ticker = m.get('ticker', '')
            if '-' not in ticker: continue
            game_code = ticker.split('-')[1] if len(ticker.split('-')) > 1 else ''
            game_date, away_team, home_team = parse_game_code(game_code)
            if not home_team: continue
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
            markets['moneyline'].append({
                'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'yes_price': yes_price, 'volume': m.get('volume', 0), 'game_date': game_date
            })
    except Exception as e:
        st.sidebar.error(f"Moneyline error: {e}")
    
    # === TOTALS - FIXED PARSING ===
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open&limit=200"
        resp = requests.get(url, timeout=10)
        for m in resp.json().get('markets', []):
            event_ticker = m.get('event_ticker', '')
            ticker = m.get('ticker', '')
            game_date, away_team, home_team = parse_event_ticker(event_ticker)
            if not home_team: continue
            
            # USE floor_strike FOR THE LINE (not regex from title!)
            line = m.get('floor_strike', 0)
            
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
            
            markets['totals'].append({
                'ticker': ticker, 'event_ticker': event_ticker,
                'title': m.get('title', ''), 'subtitle': m.get('yes_sub_title', ''),
                'away_team': away_team, 'home_team': home_team,
                'line': line, 'yes_price': yes_price, 'volume': m.get('volume', 0), 'game_date': game_date
            })
    except Exception as e:
        st.sidebar.error(f"Totals error: {e}")
    
    # === SPREADS - FIXED PARSING ===
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
        resp = requests.get(url, timeout=10)
        for m in resp.json().get('markets', []):
            event_ticker = m.get('event_ticker', '')
            ticker = m.get('ticker', '')
            title = m.get('title', '')
            game_date, away_team, home_team = parse_event_ticker(event_ticker)
            if not home_team: continue
            
            # USE floor_strike FOR THE SPREAD
            line = m.get('floor_strike', 0)
            
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
            
            # Parse spread team from ticker: "KXNBASPREAD-26JAN09NOPWAS-WAS7"
            spread_team = None
            ticker_parts = ticker.split('-')
            if len(ticker_parts) >= 3:
                team_part = ticker_parts[-1][:3].upper()  # "WAS" from "WAS7"
                spread_team = KALSHI_ABBREV_MAP.get(team_part)
            if not spread_team:
                for team in [home_team, away_team]:
                    if team and team.lower() in title.lower():
                        spread_team = team
                        break
            if not spread_team:
                spread_team = home_team
            
            markets['spreads'].append({
                'ticker': ticker, 'event_ticker': event_ticker,
                'title': title, 'subtitle': m.get('yes_sub_title', ''),
                'away_team': away_team, 'home_team': home_team, 'spread_team': spread_team,
                'line': line, 'yes_price': yes_price, 'volume': m.get('volume', 0), 'game_date': game_date
            })
    except Exception as e:
        st.sidebar.error(f"Spreads error: {e}")
    
    # Deduplicate moneyline
    seen = {}
    for g in markets['moneyline']:
        key = f"{g['away_team']}@{g['home_team']}_{g['game_date']}"
        if key not in seen or g['volume'] > seen[key]['volume']:
            seen[key] = g
    markets['moneyline'] = sorted(seen.values(), key=date_sort_key)
    markets['totals'] = sorted(markets['totals'], key=date_sort_key)
    markets['spreads'] = sorted(markets['spreads'], key=date_sort_key)
    
    return markets

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

# ========== UI ==========
st.title("🏀 NBA Kalshi Edge Finder")
st.markdown("**Moneyline • Totals • Spreads** + Kelly Calculator")
now = datetime.now()
st.caption(f"📅 {now.strftime('%A, %B %d, %Y')} | ⏰ {now.strftime('%I:%M %p')}")
st.caption("🟢 = BUY YES (home wins / over / covers) | 🔴 = BUY NO (away wins / under / doesn't cover)")

tab1, tab2, tab3 = st.tabs(["🎯 Moneyline", "📊 Over/Under Totals", "📏 Spreads"])

markets = fetch_kalshi_nba_markets()
injuries = fetch_nba_injuries()
rest_days = fetch_rest_days()
all_teams = sorted(list(TEAM_STATS.keys()))

# Sidebar
st.sidebar.header("⚙️ Settings")
st.sidebar.markdown("🟢 = **BUY YES** | 🔴 = **BUY NO**")
st.sidebar.markdown("---")
default_home_rest = st.sidebar.number_input("Default Home Rest", 0, 7, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 0, 7, 2)
min_edge = st.sidebar.slider("Min Edge %", 0, 25, 5)
st.sidebar.markdown("---")
st.sidebar.header("💰 Kelly Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.select_slider("Kelly Fraction", options=[0.1, 0.25, 0.5, 1.0], value=0.25,
                                          format_func=lambda x: {0.1: "1/10", 0.25: "1/4", 0.5: "1/2", 1.0: "Full"}[x])
if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# Show API status in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 API Status")
st.sidebar.write(f"Moneyline: {len(markets['moneyline'])}")
st.sidebar.write(f"Totals: {len(markets['totals'])}")
st.sidebar.write(f"Spreads: {len(markets['spreads'])}")

# TAB 1: MONEYLINE
with tab1:
    st.markdown("### 🎯 Moneyline Analysis")
    games = markets['moneyline']
    if not games:
        st.warning("No moneyline markets found")
    else:
        for game in games:
            home, away = game['home_team'], game['away_team']
            home_inj = len(injuries.get(home, []))
            away_inj = len(injuries.get(away, []))
            travel = calculate_travel_distance(away, home)
            home_rest = rest_days.get(home, default_home_rest)
            away_rest = rest_days.get(away, default_away_rest)
            analysis = calculate_moneyline(home, away, game['yes_price'], home_rest, away_rest, home_inj, away_inj, travel)
            if abs(analysis['edge']) < min_edge: continue
            color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
            with st.expander(f"{color} {game['game_date']} | {away} @ {home} | Edge: {analysis['edge']:+.1f}%"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Kalshi Price", f"{game['yes_price']:.0f}¢ {home}")
                c2.metric("Model Win%", f"{analysis['home_win_prob']:.1f}%")
                c3.metric("Edge", f"{analysis['edge']:+.1f}%", analysis['confidence'])
                if analysis['recommendation'] == 'BUY YES':
                    kelly = calculate_kelly(analysis['home_win_prob'], game['yes_price'], bankroll, kelly_fraction)
                else:
                    kelly = calculate_kelly(100 - analysis['home_win_prob'], 100 - game['yes_price'], bankroll, kelly_fraction)
                st.markdown("---")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/Dollar", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV on Bet", f"${kelly['ev_on_bet']:+.2f}")
                url = f"https://kalshi.com/markets/kxnbagame/{game['ticker'].lower()}"
                if analysis['recommendation'] == 'BUY YES':
                    st.link_button(f"🟢 {home} to WIN - ${kelly['bet_amount']:.2f}", url, use_container_width=True)
                elif analysis['recommendation'] == 'BUY NO':
                    st.link_button(f"🔴 {away} to WIN - ${kelly['bet_amount']:.2f}", url, use_container_width=True)

# TAB 2: TOTALS
with tab2:
    st.markdown("### 📊 Over/Under Totals")
    totals_markets = markets['totals']
    if totals_markets:
        st.success(f"✅ Found **{len(totals_markets)} totals markets**")
        for tm in totals_markets:
            home, away = tm['home_team'], tm['away_team']
            line = tm['line']
            yes_price = tm['yes_price']
            home_inj = len(injuries.get(home, []))
            away_inj = len(injuries.get(away, []))
            travel = calculate_travel_distance(away, home)
            home_rest = rest_days.get(home, default_home_rest)
            away_rest = rest_days.get(away, default_away_rest)
            totals = calculate_total_points(home, away, home_rest, away_rest, home_inj, away_inj, travel)
            predicted = totals['predicted_total']
            diff = predicted - line
            if diff > 3: rec, rec_color, win_prob = "OVER", "🟢", min(85, 50 + diff * 5)
            elif diff < -3: rec, rec_color, win_prob = "UNDER", "🔴", min(85, 50 + abs(diff) * 5)
            else: rec, rec_color, win_prob = "NO EDGE", "⚪", 50
            if rec == "NO EDGE" and min_edge > 0: continue
            with st.expander(f"{rec_color} {tm['game_date']} | {away} @ {home} | Line: {line} | {rec} ({diff:+.1f}pts)"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Predicted", f"{predicted}")
                c2.metric("Line", f"{line}")
                c3.metric("Edge", f"{diff:+.1f} pts")
                if rec == "OVER": kelly = calculate_kelly(win_prob, yes_price, bankroll, kelly_fraction)
                elif rec == "UNDER": kelly = calculate_kelly(win_prob, 100 - yes_price, bankroll, kelly_fraction)
                else: kelly = {'bet_amount': 0, 'adj_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0}
                st.markdown("---")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric("Bet", f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/$", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV", f"${kelly['ev_on_bet']:+.2f}")
                f = totals['factors']
                st.markdown("**Factors:** " + " | ".join([f"Base:{f['base_total']}", f"Pace:{f['pace']:+.1f}", f"Rest:{f['rest']:+.1f}", f"3PT:{f['3pt']:+.1f}", f"Def:{f['defense']:+.1f}"]))
                url = f"https://kalshi.com/markets/kxnbatotal/{tm['ticker'].lower()}"
                if rec == "OVER": st.link_button(f"🟢 OVER {line} - ${kelly['bet_amount']:.2f}", url, use_container_width=True)
                elif rec == "UNDER": st.link_button(f"🔴 UNDER {line} - ${kelly['bet_amount']:.2f}", url, use_container_width=True)
    else:
        st.warning("No totals markets found")

# TAB 3: SPREADS
with tab3:
    st.markdown("### 📏 Spread Analysis")
    spread_markets = markets['spreads']
    if spread_markets:
        st.success(f"✅ Found **{len(spread_markets)} spread markets**")
        for sm in spread_markets:
            home, away = sm['home_team'], sm['away_team']
            line = sm['line']
            yes_price = sm['yes_price']
            spread_team = sm['spread_team']
            home_inj = len(injuries.get(home, []))
            away_inj = len(injuries.get(away, []))
            travel = calculate_travel_distance(away, home)
            home_rest = rest_days.get(home, default_home_rest)
            away_rest = rest_days.get(away, default_away_rest)
            spread = calculate_spread(home, away, home_rest, away_rest, home_inj, away_inj, travel)
            predicted = spread['predicted_spread']
            if spread_team == home:
                spread_diff = predicted - line
                if spread_diff > 3: rec, rec_color, win_prob = f"{home} COVERS", "🟢", min(80, 50 + spread_diff * 4)
                elif spread_diff < -3: rec, rec_color, win_prob = f"{home} DOESN'T COVER", "🔴", min(80, 50 + abs(spread_diff) * 4)
                else: rec, rec_color, win_prob = "NO EDGE", "⚪", 50
            else:
                spread_diff = -predicted - line
                if spread_diff > 3: rec, rec_color, win_prob = f"{away} COVERS", "🟢", min(80, 50 + spread_diff * 4)
                elif spread_diff < -3: rec, rec_color, win_prob = f"{away} DOESN'T COVER", "🔴", min(80, 50 + abs(spread_diff) * 4)
                else: rec, rec_color, win_prob = "NO EDGE", "⚪", 50
            if rec == "NO EDGE" and min_edge > 0: continue
            with st.expander(f"{rec_color} {sm['game_date']} | {away} @ {home} | {spread_team} -{line} | {rec}"):
                st.caption(f"**Kalshi:** {sm['title']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Model", f"{home} {predicted:+.1f}")
                c2.metric("Line", f"{spread_team} -{line}")
                c3.metric("Edge", f"{spread_diff:+.1f} pts")
                if "COVERS" in rec and "DOESN'T" not in rec:
                    kelly = calculate_kelly(win_prob, yes_price, bankroll, kelly_fraction)
                elif "DOESN'T" in rec:
                    kelly = calculate_kelly(win_prob, 100 - yes_price, bankroll, kelly_fraction)
                else:
                    kelly = {'bet_amount': 0, 'adj_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0}
                st.markdown("---")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric("Bet", f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/$", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV", f"${kelly['ev_on_bet']:+.2f}")
                url = f"https://kalshi.com/markets/kxnbaspread/{sm['ticker'].lower()}"
                if "COVERS" in rec and "DOESN'T" not in rec:
                    st.link_button(f"🟢 YES - ${kelly['bet_amount']:.2f}", url, use_container_width=True)
                elif "DOESN'T" in rec:
                    st.link_button(f"🔴 NO - ${kelly['bet_amount']:.2f}", url, use_container_width=True)
    else:
        st.warning("No spread markets found")

st.markdown("---")
st.caption("⚠️ **Disclaimer:** Entertainment only. Not financial advice.")
