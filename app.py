import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math

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

# ========== KELLY CRITERION CALCULATOR ==========
def calculate_kelly(win_prob, kalshi_price, bankroll=1000, fraction=0.25):
    """
    Kelly Criterion for Kalshi betting
    win_prob: your estimated probability (0-100)
    kalshi_price: price in cents (0-100)
    fraction: Kelly fraction (0.25 = quarter Kelly, safer)
    """
    p = win_prob / 100  # Convert to decimal
    q = 1 - p
    
    # For YES bet at kalshi_price cents
    # Win: gain (100 - kalshi_price) cents
    # Lose: lose kalshi_price cents
    b = (100 - kalshi_price) / kalshi_price if kalshi_price > 0 else 0  # Odds ratio
    
    kelly_pct = (b * p - q) / b if b > 0 else 0
    kelly_pct = max(0, kelly_pct)  # Can't bet negative
    
    # Apply fraction (quarter Kelly default)
    adj_kelly = kelly_pct * fraction
    
    bet_amount = bankroll * adj_kelly
    
    # Expected Value per $1 bet
    # EV = (win_prob × profit) - (lose_prob × cost)
    profit_if_win = (100 - kalshi_price) / kalshi_price if kalshi_price > 0 else 0  # Per $1 bet
    ev_per_dollar = (p * profit_if_win) - (q * 1)  # Win pays profit, lose costs $1
    ev_on_bet = ev_per_dollar * bet_amount  # EV on recommended bet
    
    return {
        'full_kelly_pct': round(kelly_pct * 100, 1),
        'adj_kelly_pct': round(adj_kelly * 100, 1),
        'bet_amount': round(bet_amount, 2),
        'edge_pct': round((p - kalshi_price/100) * 100, 1),
        'ev_per_dollar': round(ev_per_dollar, 3),
        'ev_on_bet': round(ev_on_bet, 2)
    }

# ========== TOTAL POINTS CALCULATOR ==========
def calculate_total_points(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "off_rating": 112, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13})
    away = TEAM_STATS.get(away_team, {"ppg": 112, "opp_ppg": 112, "pace": 99, "off_rating": 112, "def_rating": 112, "three_pa": 36, "three_pct": 0.35, "oreb_pct": 27, "tov_pct": 13})
    
    # === FACTOR 1: BASE TOTAL ===
    # Average of what each team scores vs what opponent allows
    home_expected = (home['ppg'] + away['opp_ppg']) / 2
    away_expected = (away['ppg'] + home['opp_ppg']) / 2
    base_total = home_expected + away_expected
    
    # === FACTOR 2: PACE ===
    avg_pace = (home['pace'] + away['pace']) / 2
    league_avg_pace = 99.5
    pace_adj = (avg_pace - league_avg_pace) * 0.5
    
    # === FACTOR 3: REST (CORRECTED - tired = LOWER scores) ===
    home_b2b = home_rest == 0 or home_rest == 1
    away_b2b = away_rest == 0 or away_rest == 1
    home_rested = home_rest >= 2
    away_rested = away_rest >= 2
    
    if home_b2b and away_b2b:
        rest_adj = -5  # Both tired = sluggish low-scoring game
    elif home_b2b:
        rest_adj = -2.5  # Home tired
    elif away_b2b:
        rest_adj = -2.5  # Away tired
    elif home_rested and away_rested:
        rest_adj = 3  # Both fresh = run and gun
    else:
        rest_adj = 0
    
    # === FACTOR 4: 3-POINT SHOOTING ===
    combined_3pa = home.get('three_pa', 36) + away.get('three_pa', 36)
    league_avg_3pa = 72  # ~36 per team
    three_volume_adj = (combined_3pa - league_avg_3pa) * 0.12
    
    avg_3pct = (home.get('three_pct', 0.35) + away.get('three_pct', 0.35)) / 2
    if avg_3pct > 0.37:
        three_pct_adj = 2
    elif avg_3pct < 0.34:
        three_pct_adj = -2
    else:
        three_pct_adj = 0
    
    three_adj = three_volume_adj + three_pct_adj
    
    # === FACTOR 5: DEFENSE ===
    avg_def_rating = (home['def_rating'] + away['def_rating']) / 2
    league_avg_def = 112
    defense_adj = (avg_def_rating - league_avg_def) * 0.4  # Bad D = more points
    
    # === FACTOR 6: TRAVEL ===
    if travel_miles > 2000:
        travel_adj = -3  # Very long = exhausted = lower
    elif travel_miles > 1500:
        travel_adj = -2
    elif travel_miles > 1000:
        travel_adj = -1
    else:
        travel_adj = 0
    
    # === FACTOR 7: INJURIES ===
    injury_adj = -(home_injuries + away_injuries) * 1.5
    
    # === FACTOR 8: OFFENSIVE REBOUNDING ===
    avg_oreb = (home.get('oreb_pct', 27) + away.get('oreb_pct', 27)) / 2
    league_avg_oreb = 27
    oreb_adj = (avg_oreb - league_avg_oreb) * 0.3  # More OREBs = 2nd chance pts
    
    # === FACTOR 9: TURNOVERS ===
    avg_tov = (home.get('tov_pct', 13) + away.get('tov_pct', 13)) / 2
    league_avg_tov = 13
    tov_adj = -(avg_tov - league_avg_tov) * 0.4  # More TOs = fewer possessions = lower
    
    # === FACTOR 10: ALTITUDE (Denver, Utah) ===
    altitude_adj = 0
    if home_team == "Denver":
        altitude_adj = 2.5  # Visiting teams struggle, but ball travels = more points
    elif home_team == "Utah":
        altitude_adj = 1.5
    
    # === FACTOR 11: OVERTIME PROBABILITY ===
    spread_diff = abs(home['net_rating'] - away['net_rating'])
    if spread_diff < 3:
        ot_adj = 1.5  # Close game, higher OT chance
    elif spread_diff < 6:
        ot_adj = 0.75
    else:
        ot_adj = 0
    
    # === FINAL TOTAL ===
    predicted_total = (base_total + pace_adj + rest_adj + three_adj + defense_adj + 
                       travel_adj + injury_adj + oreb_adj + tov_adj + altitude_adj + ot_adj)
    
    return {
        'predicted_total': round(predicted_total, 1),
        'factors': {
            'base_total': round(base_total, 1),
            'pace': round(pace_adj, 1),
            'rest': round(rest_adj, 1),
            '3pt': round(three_adj, 1),
            'defense': round(defense_adj, 1),
            'travel': round(travel_adj, 1),
            'injury': round(injury_adj, 1),
            'oreb': round(oreb_adj, 1),
            'turnover': round(tov_adj, 1),
            'altitude': round(altitude_adj, 1),
            'ot_prob': round(ot_adj, 1)
        }
    }

# ========== SPREAD CALCULATOR ==========
def calculate_spread(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    home = TEAM_STATS.get(home_team, {"net_rating": 0, "home_win_pct": 0.5})
    away = TEAM_STATS.get(away_team, {"net_rating": 0, "away_win_pct": 0.5})
    
    net_diff = home['net_rating'] - away['net_rating']
    home_court = 3.5
    rest_diff = home_rest - away_rest
    rest_adj = rest_diff * 1.5
    injury_adj = (away_injuries - home_injuries) * 1.5
    
    if travel_miles > 1500: travel_adj = 2.5
    elif travel_miles > 1000: travel_adj = 1.5
    elif travel_miles > 500: travel_adj = 0.75
    else: travel_adj = 0
    
    home_boost = (home['home_win_pct'] - 0.5) * 5
    away_penalty = (0.5 - away['away_win_pct']) * 5
    split_adj = home_boost + away_penalty
    
    predicted_spread = net_diff + home_court + rest_adj + injury_adj + travel_adj + split_adj
    
    return {
        'predicted_spread': round(predicted_spread, 1),
        'factors': {
            'net_rating': round(net_diff, 1),
            'home_court': home_court,
            'rest': round(rest_adj, 1),
            'injury': round(injury_adj, 1),
            'travel': round(travel_adj, 1),
            'splits': round(split_adj, 1)
        }
    }

# ========== MONEYLINE CALCULATOR ==========
def calculate_moneyline(home_team, away_team, kalshi_price, home_rest, away_rest, home_injuries, away_injuries, travel_miles):
    spread_data = calculate_spread(home_team, away_team, home_rest, away_rest, home_injuries, away_injuries, travel_miles)
    spread = spread_data['predicted_spread']
    home_win_prob = max(5, min(95, 50 + spread * 2.5))
    edge = home_win_prob - kalshi_price
    
    return {
        'home_win_prob': round(home_win_prob, 1),
        'edge': round(edge, 1),
        'spread': round(spread, 1),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW')
    }

@st.cache_data(ttl=300)
def fetch_kalshi_nba_markets():
    markets = {'moneyline': [], 'totals': [], 'spreads': []}
    
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100"
        resp = requests.get(url, timeout=10)
        for m in resp.json().get('markets', []):
            ticker = m.get('ticker', '')
            if '-' not in ticker: continue
            game_code = ticker.split('-')[1] if len(ticker.split('-')) > 1 else ''
            if len(game_code) < 6: continue
            
            away_abbrev = game_code[-6:-3].upper()
            home_abbrev = game_code[-3:].upper()
            away_team = KALSHI_ABBREV_MAP.get(away_abbrev, away_abbrev)
            home_team = KALSHI_ABBREV_MAP.get(home_abbrev, home_abbrev)
            
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
            
            game_date_str = ""
            try:
                date_part = game_code[:-6]
                if len(date_part) >= 7:
                    month_map = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
                                 'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'}
                    game_date_str = f"{month_map.get(date_part[2:5].upper(), date_part[2:5])} {date_part[5:7]}"
            except: pass
            
            markets['moneyline'].append({
                'ticker': ticker, 'away_team': away_team, 'home_team': home_team,
                'yes_price': yes_price, 'volume': m.get('volume', 0), 'game_date': game_date_str
            })
    except: pass
    
    # Deduplicate and sort
    seen = {}
    for g in markets['moneyline']:
        key = f"{g['away_team']}@{g['home_team']}_{g['game_date']}"
        if key not in seen or g['volume'] > seen[key]['volume']:
            seen[key] = g
    
    month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                   'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    def date_sort_key(g):
        try:
            parts = g['game_date'].split()
            return (month_order.get(parts[0], 0), int(parts[1]))
        except: return (99, 99)
    
    markets['moneyline'] = sorted(seen.values(), key=date_sort_key)
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

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Moneyline", "📊 Over/Under Totals", "📏 Spreads"])

# Fetch data
markets = fetch_kalshi_nba_markets()
injuries = fetch_nba_injuries()
rest_days = fetch_rest_days()

# Sidebar
st.sidebar.header("⚙️ Settings")

st.sidebar.markdown("### 🎨 Color Key")
st.sidebar.markdown("🟢 = **BUY YES**")
st.sidebar.markdown("🔴 = **BUY NO**")
st.sidebar.markdown("---")

default_home_rest = st.sidebar.number_input("Default Home Rest", 0, 7, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 0, 7, 2)
min_edge = st.sidebar.slider("Min Edge %", 0, 25, 5)

st.sidebar.markdown("---")
st.sidebar.header("💰 Kelly Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", 100, 100000, 1000, 100)
kelly_fraction = st.sidebar.select_slider("Kelly Fraction", options=[0.1, 0.25, 0.5, 1.0], value=0.25,
                                          format_func=lambda x: {0.1: "1/10 Kelly", 0.25: "1/4 Kelly", 0.5: "1/2 Kelly", 1.0: "Full Kelly"}[x])

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# ========== TAB 1: MONEYLINE ==========
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
            
            if abs(analysis['edge']) < min_edge:
                continue
            
            color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
            
            with st.expander(f"{color} {game['game_date']} | {away} @ {home} | Edge: {analysis['edge']:+.1f}%"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Kalshi Price", f"{game['yes_price']:.0f}¢ {home}")
                c2.metric("Model Win%", f"{analysis['home_win_prob']:.1f}%")
                c3.metric("Edge", f"{analysis['edge']:+.1f}%", analysis['confidence'])
                
                # Kelly Calculator
                if analysis['recommendation'] == 'BUY YES':
                    kelly = calculate_kelly(analysis['home_win_prob'], game['yes_price'], bankroll, kelly_fraction)
                else:
                    kelly = calculate_kelly(100 - analysis['home_win_prob'], 100 - game['yes_price'], bankroll, kelly_fraction)
                
                st.markdown("---")
                st.markdown("**💰 Kelly + EV (Expected Value)**")
                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
                kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
                kc3.metric("EV/Dollar", f"${kelly['ev_per_dollar']:.3f}")
                kc4.metric("EV on Bet", f"${kelly['ev_on_bet']:+.2f}")
                
                url = f"https://kalshi.com/markets/kxnbagame/{game['ticker'].lower()}"
                if analysis['recommendation'] == 'BUY YES':
                    st.link_button(f"🟢 {home} to WIN (YES) - Bet ${kelly['bet_amount']:.2f}", url, use_container_width=True)
                elif analysis['recommendation'] == 'BUY NO':
                    st.link_button(f"🔴 {away} to WIN (NO) - Bet ${kelly['bet_amount']:.2f}", url, use_container_width=True)

# ========== TAB 2: TOTALS ==========
with tab2:
    st.markdown("### 📊 Over/Under Totals")
    st.caption("11 Factors: Base, Pace, Rest, 3PT, Defense, Travel, Injury, OREB, Turnovers, Altitude, OT Prob")
    
    all_teams = sorted(list(TEAM_STATS.keys()))
    
    col1, col2 = st.columns(2)
    away_team = col1.selectbox("Away Team", all_teams, index=all_teams.index("LA Lakers"))
    home_team = col2.selectbox("Home Team", all_teams, index=all_teams.index("Boston"))
    
    col3, col4 = st.columns(2)
    kalshi_line = col3.number_input("Kalshi Line", 180.0, 280.0, 230.5, 0.5)
    kalshi_over_price = col4.number_input("Over Price (¢)", 1, 99, 50)
    
    col5, col6 = st.columns(2)
    t_home_rest = col5.number_input("Home Rest Days", 0, 7, rest_days.get(home_team, default_home_rest), key="t_hr")
    t_away_rest = col6.number_input("Away Rest Days", 0, 7, rest_days.get(away_team, default_away_rest), key="t_ar")
    
    home_inj = len(injuries.get(home_team, []))
    away_inj = len(injuries.get(away_team, []))
    travel = calculate_travel_distance(away_team, home_team)
    
    st.caption(f"📍 Travel: {travel} miles | 🏥 Injuries: {home_team} ({home_inj}), {away_team} ({away_inj})")
    
    if st.button("🔍 Analyze Totals", use_container_width=True):
        totals = calculate_total_points(home_team, away_team, t_home_rest, t_away_rest, home_inj, away_inj, travel)
        
        predicted = totals['predicted_total']
        diff = predicted - kalshi_line
        
        if diff > 3:
            rec, rec_color = "OVER", "🟢"
            win_prob = min(85, 50 + diff * 5)
        elif diff < -3:
            rec, rec_color = "UNDER", "🔴"
            win_prob = min(85, 50 + abs(diff) * 5)
        else:
            rec, rec_color = "NO EDGE", "⚪"
            win_prob = 50
        
        st.markdown("---")
        st.markdown(f"## {rec_color} {rec} {kalshi_line}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Predicted Total", f"{predicted}")
        c2.metric("Kalshi Line", f"{kalshi_line}")
        c3.metric("Difference", f"{diff:+.1f} pts")
        
        # Kelly for totals
        if rec == "OVER":
            kelly = calculate_kelly(win_prob, kalshi_over_price, bankroll, kelly_fraction)
        elif rec == "UNDER":
            kelly = calculate_kelly(win_prob, 100 - kalshi_over_price, bankroll, kelly_fraction)
        else:
            kelly = {'bet_amount': 0, 'adj_kelly_pct': 0, 'full_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0}
        
        st.markdown("---")
        st.markdown("**💰 Kelly + EV (Expected Value)**")
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
        kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
        kc3.metric("EV/Dollar", f"${kelly['ev_per_dollar']:.3f}")
        kc4.metric("EV on Bet", f"${kelly['ev_on_bet']:+.2f}")
        
        st.markdown("---")
        st.markdown("**📈 11-Factor Breakdown**")
        f = totals['factors']
        
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("Base Total", f"{f['base_total']}")
        fc2.metric("Pace", f"{f['pace']:+.1f}")
        fc3.metric("Rest", f"{f['rest']:+.1f}")
        fc4.metric("3PT", f"{f['3pt']:+.1f}")
        
        fc5, fc6, fc7, fc8 = st.columns(4)
        fc5.metric("Defense", f"{f['defense']:+.1f}")
        fc6.metric("Travel", f"{f['travel']:+.1f}")
        fc7.metric("Injury", f"{f['injury']:+.1f}")
        fc8.metric("OREB", f"{f['oreb']:+.1f}")
        
        fc9, fc10, fc11, _ = st.columns(4)
        fc9.metric("Turnovers", f"{f['turnover']:+.1f}")
        fc10.metric("Altitude", f"{f['altitude']:+.1f}")
        fc11.metric("OT Prob", f"{f['ot_prob']:+.1f}")

# ========== TAB 3: SPREADS ==========
with tab3:
    st.markdown("### 📏 Spread Analysis")
    
    col1, col2 = st.columns(2)
    s_away_team = col1.selectbox("Away Team", all_teams, index=all_teams.index("LA Lakers"), key="s_away")
    s_home_team = col2.selectbox("Home Team", all_teams, index=all_teams.index("Boston"), key="s_home")
    
    col3, col4 = st.columns(2)
    kalshi_spread = col3.number_input("Kalshi Spread (- = home favored)", -30.0, 30.0, -5.5, 0.5)
    kalshi_cover_price = col4.number_input("Cover Price (¢)", 1, 99, 50, key="sp")
    
    col5, col6 = st.columns(2)
    s_home_rest = col5.number_input("Home Rest Days", 0, 7, rest_days.get(s_home_team, default_home_rest), key="s_hr")
    s_away_rest = col6.number_input("Away Rest Days", 0, 7, rest_days.get(s_away_team, default_away_rest), key="s_ar")
    
    s_home_inj = len(injuries.get(s_home_team, []))
    s_away_inj = len(injuries.get(s_away_team, []))
    s_travel = calculate_travel_distance(s_away_team, s_home_team)
    
    st.caption(f"📍 Travel: {s_travel} miles | 🏥 Injuries: {s_home_team} ({s_home_inj}), {s_away_team} ({s_away_inj})")
    
    if st.button("🔍 Analyze Spread", use_container_width=True):
        spread = calculate_spread(s_home_team, s_away_team, s_home_rest, s_away_rest, s_home_inj, s_away_inj, s_travel)
        
        predicted = spread['predicted_spread']
        # Kalshi spread is negative if home favored (e.g., -5.5)
        # Our spread is positive if home favored
        spread_diff = predicted - (-kalshi_spread)  # Convert Kalshi format
        
        if spread_diff > 3:
            rec = f"{s_home_team} COVERS"
            rec_color = "🟢"
            win_prob = min(80, 50 + spread_diff * 4)
        elif spread_diff < -3:
            rec = f"{s_away_team} COVERS"
            rec_color = "🔴"
            win_prob = min(80, 50 + abs(spread_diff) * 4)
        else:
            rec = "NO EDGE"
            rec_color = "⚪"
            win_prob = 50
        
        st.markdown("---")
        st.markdown(f"## {rec_color} {rec}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Predicted Spread", f"{s_home_team} {predicted:+.1f}")
        c2.metric("Kalshi Spread", f"{kalshi_spread:+.1f}")
        c3.metric("Edge", f"{spread_diff:+.1f} pts")
        
        # Kelly for spreads
        kelly = calculate_kelly(win_prob, kalshi_cover_price, bankroll, kelly_fraction) if rec != "NO EDGE" else {'bet_amount': 0, 'adj_kelly_pct': 0, 'full_kelly_pct': 0, 'ev_per_dollar': 0, 'ev_on_bet': 0}
        
        st.markdown("---")
        st.markdown("**💰 Kelly + EV (Expected Value)**")
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Bet Size", f"${kelly['bet_amount']:.2f}")
        kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
        kc3.metric("EV/Dollar", f"${kelly['ev_per_dollar']:.3f}")
        kc4.metric("EV on Bet", f"${kelly['ev_on_bet']:+.2f}")
        
        st.markdown("---")
        st.markdown("**📈 Factor Breakdown**")
        f = spread['factors']
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Net Rating", f"{f['net_rating']:+.1f}")
        fc2.metric("Home Court", f"+{f['home_court']}")
        fc3.metric("Rest", f"{f['rest']:+.1f}")
        
        fc4, fc5, fc6 = st.columns(3)
        fc4.metric("Injury", f"{f['injury']:+.1f}")
        fc5.metric("Travel", f"+{f['travel']}")
        fc6.metric("Splits", f"{f['splits']:+.1f}")

st.markdown("---")
st.caption("⚠️ **Disclaimer:** Entertainment only. Not financial advice. Trade responsibly.")
