import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(page_title="KALSHI NBA EDGE FINDER", layout="wide")

import streamlit.components.v1 as components
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-F6WSR1EZBS"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-F6WSR1EZBS');
</script>
""", height=0)

st.title("🎯 NBA Spread Predictor for Kalshi")
st.write("**100% Automatic • 9 Edge Factors • Real-Time Data**")

# Updated team_mapping with ESPN IDs for injury API
team_mapping = {
    "Atlanta Hawks": {"abbrev": "ATL", "espn_id": 1},
    "Boston Celtics": {"abbrev": "BOS", "espn_id": 2},
    "Brooklyn Nets": {"abbrev": "BKN", "espn_id": 17},
    "Charlotte Hornets": {"abbrev": "CHA", "espn_id": 30},
    "Chicago Bulls": {"abbrev": "CHI", "espn_id": 4},
    "Cleveland Cavaliers": {"abbrev": "CLE", "espn_id": 5},
    "Dallas Mavericks": {"abbrev": "DAL", "espn_id": 6},
    "Denver Nuggets": {"abbrev": "DEN", "espn_id": 7},
    "Detroit Pistons": {"abbrev": "DET", "espn_id": 8},
    "Golden State Warriors": {"abbrev": "GSW", "espn_id": 9},
    "Houston Rockets": {"abbrev": "HOU", "espn_id": 10},
    "Indiana Pacers": {"abbrev": "IND", "espn_id": 11},
    "LA Clippers": {"abbrev": "LAC", "espn_id": 12},
    "Los Angeles Lakers": {"abbrev": "LAL", "espn_id": 13},
    "Memphis Grizzlies": {"abbrev": "MEM", "espn_id": 29},
    "Miami Heat": {"abbrev": "MIA", "espn_id": 14},
    "Milwaukee Bucks": {"abbrev": "MIL", "espn_id": 15},
    "Minnesota Timberwolves": {"abbrev": "MIN", "espn_id": 16},
    "New Orleans Pelicans": {"abbrev": "NOP", "espn_id": 3},
    "New York Knicks": {"abbrev": "NYK", "espn_id": 18},
    "Oklahoma City Thunder": {"abbrev": "OKC", "espn_id": 25},
    "Orlando Magic": {"abbrev": "ORL", "espn_id": 19},
    "Philadelphia 76ers": {"abbrev": "PHI", "espn_id": 20},
    "Phoenix Suns": {"abbrev": "PHX", "espn_id": 21},
    "Portland Trail Blazers": {"abbrev": "POR", "espn_id": 22},
    "Sacramento Kings": {"abbrev": "SAC", "espn_id": 23},
    "San Antonio Spurs": {"abbrev": "SAS", "espn_id": 24},
    "Toronto Raptors": {"abbrev": "TOR", "espn_id": 28},
    "Utah Jazz": {"abbrev": "UTA", "espn_id": 26},
    "Washington Wizards": {"abbrev": "WAS", "espn_id": 27}
}

# TIERED player database - different point values for different importance
# Tier 1: MVP/Superstar (6 pts OUT, 3 pts questionable)
# Tier 2: All-Star caliber (4 pts OUT, 2 pts questionable)  
# Tier 3: Quality starter (2 pts OUT, 1 pt questionable)
player_tiers = {
    # TIER 1 - MVP/SUPERSTAR LEVEL (6 pts if OUT)
    "LeBron James": 1, "Stephen Curry": 1, "Kevin Durant": 1, "Giannis Antetokounmpo": 1,
    "Nikola Jokic": 1, "Joel Embiid": 1, "Luka Doncic": 1, "Jayson Tatum": 1,
    "Shai Gilgeous-Alexander": 1, "Anthony Davis": 1, "Damian Lillard": 1,
    "Kawhi Leonard": 1, "Jimmy Butler": 1, "Donovan Mitchell": 1, "Ja Morant": 1,
    "Anthony Edwards": 1, "Devin Booker": 1, "Tyrese Haliburton": 1,
    
    # TIER 2 - ALL-STAR CALIBER (4 pts if OUT)
    "Jaylen Brown": 2, "Paul George": 2, "Kyrie Irving": 2, "Zion Williamson": 2,
    "Trae Young": 2, "Bam Adebayo": 2, "Jamal Murray": 2, "Darius Garland": 2,
    "De'Aaron Fox": 2, "Jalen Brunson": 2, "LaMelo Ball": 2, "Chet Holmgren": 2,
    "Paolo Banchero": 2, "Evan Mobley": 2, "Scottie Barnes": 2, "Tyrese Maxey": 2,
    "Brandon Ingram": 2, "Pascal Siakam": 2, "Khris Middleton": 2, "Zach LaVine": 2,
    "Karl-Anthony Towns": 2, "Rudy Gobert": 2, "Julius Randle": 2, "Lauri Markkanen": 2,
    "Cade Cunningham": 2, "Franz Wagner": 2, "Jalen Williams": 2, "Victor Wembanyama": 2,
    "James Harden": 2, "Kristaps Porzingis": 2, "Dejounte Murray": 2, "CJ McCollum": 2,
    "Tyler Herro": 2, "Desmond Bane": 2, "Domantas Sabonis": 2, "Jarrett Allen": 2,
    
    # TIER 3 - QUALITY STARTER (2 pts if OUT)
    "Derrick White": 3, "Jrue Holiday": 3, "Mikal Bridges": 3, "Michael Porter Jr.": 3,
    "Aaron Gordon": 3, "Myles Turner": 3, "Brook Lopez": 3, "Draymond Green": 3,
    "Andrew Wiggins": 3, "Klay Thompson": 3, "D'Angelo Russell": 3, "Austin Reaves": 3,
    "Tobias Harris": 3, "Bradley Beal": 3, "Devin Vassell": 3, "Anfernee Simons": 3,
    "Jerami Grant": 3, "RJ Barrett": 3, "OG Anunoby": 3, "Immanuel Quickley": 3,
    "Alperen Sengun": 3, "Jabari Smith Jr.": 3, "Jalen Green": 3, "Coby White": 3,
    "DeMar DeRozan": 3, "Nikola Vucevic": 3, "Wendell Carter Jr.": 3, "Jalen Suggs": 3,
    "Marcus Smart": 3, "Jaren Jackson Jr.": 3, "Josh Giddey": 3, "Bennedict Mathurin": 3,
    "Cameron Johnson": 3, "Nic Claxton": 3, "Brandon Miller": 3, "Mark Williams": 3,
    "Herb Jones": 3, "Jaden McDaniels": 3, "Kyle Kuzma": 3, "Jordan Poole": 3,
    "Malik Monk": 3, "Keegan Murray": 3, "Jordan Clarkson": 3, "Collin Sexton": 3,
    "John Collins": 3, "Jakob Poeltl": 3, "Jaden Ivey": 3, "Ausar Thompson": 3,
    "Donte DiVincenzo": 3, "Keldon Johnson": 3, "Scoot Henderson": 3, "Jalen Johnson": 3
}

# Point values by tier and status
INJURY_POINTS = {
    1: {"out": 6.0, "questionable": 3.0, "day-to-day": 2.5},  # Superstar
    2: {"out": 4.0, "questionable": 2.0, "day-to-day": 1.5},  # All-Star
    3: {"out": 2.0, "questionable": 1.0, "day-to-day": 0.75}, # Starter
    4: {"out": 0.5, "questionable": 0.25, "day-to-day": 0.1}  # Role player
}

team_locations = {
    "Atlanta Hawks": {"lat": 33.757, "lon": -84.396, "altitude": 1050, "tz": 0},
    "Boston Celtics": {"lat": 42.366, "lon": -71.062, "altitude": 20, "tz": 0},
    "Brooklyn Nets": {"lat": 40.683, "lon": -73.976, "altitude": 30, "tz": 0},
    "Charlotte Hornets": {"lat": 35.225, "lon": -80.839, "altitude": 751, "tz": 0},
    "Chicago Bulls": {"lat": 41.881, "lon": -87.674, "altitude": 594, "tz": -1},
    "Cleveland Cavaliers": {"lat": 41.497, "lon": -81.688, "altitude": 653, "tz": 0},
    "Dallas Mavericks": {"lat": 32.790, "lon": -96.810, "altitude": 430, "tz": -1},
    "Denver Nuggets": {"lat": 39.749, "lon": -105.008, "altitude": 5280, "tz": -2},
    "Detroit Pistons": {"lat": 42.341, "lon": -83.055, "altitude": 600, "tz": 0},
    "Golden State Warriors": {"lat": 37.768, "lon": -122.388, "altitude": 10, "tz": -3},
    "Houston Rockets": {"lat": 29.751, "lon": -95.362, "altitude": 80, "tz": -1},
    "Indiana Pacers": {"lat": 39.764, "lon": -86.156, "altitude": 715, "tz": 0},
    "LA Clippers": {"lat": 34.043, "lon": -118.267, "altitude": 305, "tz": -3},
    "Los Angeles Lakers": {"lat": 34.043, "lon": -118.267, "altitude": 305, "tz": -3},
    "Memphis Grizzlies": {"lat": 35.138, "lon": -90.051, "altitude": 337, "tz": -1},
    "Miami Heat": {"lat": 25.781, "lon": -80.188, "altitude": 10, "tz": 0},
    "Milwaukee Bucks": {"lat": 43.045, "lon": -87.918, "altitude": 617, "tz": -1},
    "Minnesota Timberwolves": {"lat": 44.980, "lon": -93.276, "altitude": 830, "tz": -1},
    "New Orleans Pelicans": {"lat": 29.949, "lon": -90.082, "altitude": 3, "tz": -1},
    "New York Knicks": {"lat": 40.751, "lon": -73.994, "altitude": 33, "tz": 0},
    "Oklahoma City Thunder": {"lat": 35.463, "lon": -97.515, "altitude": 1201, "tz": -1},
    "Orlando Magic": {"lat": 28.539, "lon": -81.384, "altitude": 82, "tz": 0},
    "Philadelphia 76ers": {"lat": 39.901, "lon": -75.172, "altitude": 39, "tz": 0},
    "Phoenix Suns": {"lat": 33.446, "lon": -112.071, "altitude": 1086, "tz": -2},
    "Portland Trail Blazers": {"lat": 45.532, "lon": -122.667, "altitude": 50, "tz": -3},
    "Sacramento Kings": {"lat": 38.580, "lon": -121.500, "altitude": 30, "tz": -3},
    "San Antonio Spurs": {"lat": 29.427, "lon": -98.438, "altitude": 650, "tz": -1},
    "Toronto Raptors": {"lat": 43.643, "lon": -79.379, "altitude": 249, "tz": 0},
    "Utah Jazz": {"lat": 40.768, "lon": -111.901, "altitude": 4226, "tz": -2},
    "Washington Wizards": {"lat": 38.898, "lon": -77.021, "altitude": 40, "tz": 0}
}

def fetch_team_injuries(team_name):
    """Fetch injuries using ESPN Core API with team ID"""
    try:
        team_info = team_mapping.get(team_name)
        if not team_info:
            return []
        
        team_id = team_info["espn_id"]
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries?limit=100"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            injuries = []
            
            for item in data.get('items', []):
                if '$ref' in item:
                    try:
                        injury_resp = requests.get(item['$ref'], timeout=5)
                        if injury_resp.status_code == 200:
                            injury_data = injury_resp.json()
                            player_name = injury_data.get('athlete', {}).get('displayName', 'Unknown')
                            status = injury_data.get('status', 'Unknown')
                            if not player_name or player_name == 'Unknown':
                                athlete_ref = injury_data.get('athlete', {}).get('$ref', '')
                                if athlete_ref:
                                    ath_resp = requests.get(athlete_ref, timeout=5)
                                    if ath_resp.status_code == 200:
                                        player_name = ath_resp.json().get('displayName', 'Unknown')
                            injuries.append({'player': player_name, 'status': status})
                    except:
                        continue
                else:
                    player_name = item.get('athlete', {}).get('displayName', 'Unknown')
                    status = item.get('status', 'Unknown')
                    injuries.append({'player': player_name, 'status': status})
            
            return injuries
        return []
    except Exception as e:
        return []

def get_player_tier(player_name):
    """Get player tier (1=superstar, 2=all-star, 3=starter, 4=role player)"""
    for known_player, tier in player_tiers.items():
        if known_player.lower() in player_name.lower() or player_name.lower() in known_player.lower():
            return tier
    return 4  # Default to role player

def get_status_type(status):
    """Convert status string to category"""
    status_lower = status.lower()
    if 'out' in status_lower:
        return 'out'
    elif 'questionable' in status_lower or 'doubtful' in status_lower:
        return 'questionable'
    elif 'day-to-day' in status_lower or 'day to day' in status_lower:
        return 'day-to-day'
    return 'day-to-day'  # Default

def calculate_injury_impact(injuries):
    """
    Calculate TOTAL injury impact in points.
    Returns: (total_points, list of injury details)
    """
    if not injuries:
        return 0.0, []
    
    total_points = 0.0
    injury_details = []
    
    for injury in injuries:
        player = injury.get('player', 'Unknown')
        status = injury.get('status', 'Unknown')
        
        tier = get_player_tier(player)
        status_type = get_status_type(status)
        points = INJURY_POINTS.get(tier, INJURY_POINTS[4]).get(status_type, 0.5)
        
        total_points += points
        
        tier_label = {1: "⭐⭐⭐ MVP", 2: "⭐⭐ All-Star", 3: "⭐ Starter", 4: "Bench"}[tier]
        injury_details.append({
            'player': player,
            'status': status,
            'tier': tier,
            'tier_label': tier_label,
            'points': points
        })
    
    # Sort by impact (highest first)
    injury_details.sort(key=lambda x: x['points'], reverse=True)
    
    return total_points, injury_details

def get_injury_severity_label(total_points):
    """Convert total injury points to a severity label"""
    if total_points >= 6:
        return "🔴 CRITICAL", "critical"
    elif total_points >= 4:
        return "🟠 SEVERE", "severe"
    elif total_points >= 2:
        return "🟡 MODERATE", "moderate"
    elif total_points > 0:
        return "🟢 MINOR", "minor"
    return "✅ HEALTHY", "healthy"

@st.cache_data(ttl=1800)
def get_cached_injuries(team_name):
    return fetch_team_injuries(team_name)

def calculate_distance(team1, team2):
    loc1 = team_locations.get(team1)
    loc2 = team_locations.get(team2)
    if not loc1 or not loc2:
        return 0
    R = 3959
    lat1, lon1 = radians(loc1["lat"]), radians(loc1["lon"])
    lat2, lon2 = radians(loc2["lat"]), radians(loc2["lon"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_altitude_advantage(home_team):
    loc = team_locations.get(home_team)
    if not loc:
        return 0
    altitude = loc["altitude"]
    if altitude >= 5000:
        return 1.5
    elif altitude >= 4000:
        return 0.75
    return 0

def fetch_todays_games():
    try:
        today = datetime.now().strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            espn_teams = {
                "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
                "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
                "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
                "GS": "Golden State Warriors", "GSW": "Golden State Warriors",
                "HOU": "Houston Rockets", "IND": "Indiana Pacers",
                "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
                "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
                "NO": "New Orleans Pelicans", "NOP": "New Orleans Pelicans",
                "NY": "New York Knicks", "NYK": "New York Knicks",
                "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic",
                "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers",
                "SAC": "Sacramento Kings", "SA": "San Antonio Spurs", "SAS": "San Antonio Spurs",
                "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "UTAH": "Utah Jazz",
                "WAS": "Washington Wizards", "WSH": "Washington Wizards"
            }
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])
                if len(competitors) == 2:
                    home_team = None
                    away_team = None
                    for comp in competitors:
                        abbrev = comp.get('team', {}).get('abbreviation', '')
                        full_name = espn_teams.get(abbrev, comp.get('team', {}).get('displayName', ''))
                        if comp.get('homeAway') == 'home':
                            home_team = full_name
                        else:
                            away_team = full_name
                    game_time = event.get('date', '')
                    try:
                        game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                        game_time_local = game_dt.astimezone().strftime('%I:%M %p')
                    except:
                        game_time_local = event.get('status', {}).get('type', {}).get('shortDetail', 'TBD')
                    if home_team and away_team:
                        games.append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'game_time': game_time_local,
                            'game_id': event.get('id', '')
                        })
            return games
        return []
    except Exception as e:
        return []

def fetch_team_rest_days():
    try:
        today = datetime.now().date()
        last_game = {}
        espn_teams = {
            "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
            "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
            "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
            "GS": "Golden State Warriors", "GSW": "Golden State Warriors",
            "HOU": "Houston Rockets", "IND": "Indiana Pacers",
            "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
            "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
            "NO": "New Orleans Pelicans", "NOP": "New Orleans Pelicans",
            "NY": "New York Knicks", "NYK": "New York Knicks",
            "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic",
            "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers",
            "SAC": "Sacramento Kings", "SA": "San Antonio Spurs", "SAS": "San Antonio Spurs",
            "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "UTAH": "Utah Jazz",
            "WAS": "Washington Wizards", "WSH": "Washington Wizards"
        }
        for days_ago in range(1, 6):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime('%Y%m%d')
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for event in data.get('events', []):
                        for comp in event.get('competitions', [{}]):
                            for team in comp.get('competitors', []):
                                abbrev = team.get('team', {}).get('abbreviation', '')
                                full_name = espn_teams.get(abbrev)
                                if full_name and full_name not in last_game:
                                    last_game[full_name] = check_date
            except:
                continue
        rest_days = {}
        for team, last_date in last_game.items():
            days_since = (today - last_date).days
            rest = max(0, days_since - 1)
            rest_days[team] = rest
        return rest_days
    except:
        return {}

@st.cache_data(ttl=300)
def get_cached_rest_days():
    return fetch_team_rest_days()

def fetch_team_record():
    try:
        url = "https://cdn.nba.com/static/json/liveData/standings/standings_00.json"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.nba.com/'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = {}
            for team in data.get('standings', []):
                for full_name in team_mapping.keys():
                    if team.get('teamName', '') in full_name:
                        records[full_name] = {
                            'l10_wins': team.get('L10Win', 5),
                            'streak': team.get('strCurrentStreak', ''),
                            'win_pct': team.get('winPct', 0.5)
                        }
                        break
            return records
        return {}
    except:
        return {}

@st.cache_data(ttl=3600)
def get_cached_standings():
    return fetch_team_record()

team_stats = {
    "Boston Celtics": {"net_rating": 11.7, "def_rank": 2, "pace": 99.1},
    "Minnesota Timberwolves": {"net_rating": 8.2, "def_rank": 1, "pace": 97.8},
    "Oklahoma City Thunder": {"net_rating": 7.8, "def_rank": 5, "pace": 101.2},
    "Denver Nuggets": {"net_rating": 6.9, "def_rank": 8, "pace": 98.4},
    "LA Clippers": {"net_rating": 6.1, "def_rank": 12, "pace": 98.9},
    "Philadelphia 76ers": {"net_rating": 5.8, "def_rank": 7, "pace": 99.3},
    "Milwaukee Bucks": {"net_rating": 5.2, "def_rank": 19, "pace": 102.1},
    "New York Knicks": {"net_rating": 4.9, "def_rank": 3, "pace": 96.7},
    "Miami Heat": {"net_rating": 4.3, "def_rank": 6, "pace": 97.1},
    "Phoenix Suns": {"net_rating": 3.8, "def_rank": 14, "pace": 100.3},
    "Indiana Pacers": {"net_rating": 3.2, "def_rank": 24, "pace": 102.1},
    "Dallas Mavericks": {"net_rating": 2.9, "def_rank": 20, "pace": 99.8},
    "Los Angeles Lakers": {"net_rating": 2.5, "def_rank": 16, "pace": 99.8},
    "Cleveland Cavaliers": {"net_rating": 2.1, "def_rank": 4, "pace": 94.3},
    "Orlando Magic": {"net_rating": 1.8, "def_rank": 3, "pace": 95.9},
    "New Orleans Pelicans": {"net_rating": 1.2, "def_rank": 10, "pace": 90.8},
    "Sacramento Kings": {"net_rating": 0.8, "def_rank": 18, "pace": 100.5},
    "Golden State Warriors": {"net_rating": 0.3, "def_rank": 15, "pace": 102.4},
    "Houston Rockets": {"net_rating": -0.4, "def_rank": 9, "pace": 98.5},
    "Chicago Bulls": {"net_rating": -1.1, "def_rank": 15, "pace": 93.9},
    "Atlanta Hawks": {"net_rating": -1.8, "def_rank": 21, "pace": 101.2},
    "Utah Jazz": {"net_rating": -2.5, "def_rank": 20, "pace": 97.1},
    "Brooklyn Nets": {"net_rating": -3.2, "def_rank": 22, "pace": 96.3},
    "Toronto Raptors": {"net_rating": -4.1, "def_rank": 23, "pace": 96.8},
    "Memphis Grizzlies": {"net_rating": -5.2, "def_rank": 25, "pace": 95.2},
    "Portland Trail Blazers": {"net_rating": -6.8, "def_rank": 28, "pace": 89.7},
    "Charlotte Hornets": {"net_rating": -8.1, "def_rank": 27, "pace": 97.4},
    "San Antonio Spurs": {"net_rating": -9.5, "def_rank": 29, "pace": 90.2},
    "Washington Wizards": {"net_rating": -10.8, "def_rank": 26, "pace": 101.8},
    "Detroit Pistons": {"net_rating": -12.3, "def_rank": 30, "pace": 95.6}
}

def calculate_kalshi_edge(home_team, away_team, market_spread, home_rest, away_rest, 
                          home_injury_points, away_injury_points, kalshi_yes_price,
                          home_b2b, away_b2b):
    home_stats = team_stats.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    away_stats = team_stats.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    standings = get_cached_standings()
    home_form = standings.get(home_team, {'l10_wins': 5, 'streak': 0})
    away_form = standings.get(away_team, {'l10_wins': 5, 'streak': 0})
    
    rest_advantage = (home_rest - away_rest) * st.session_state.get('rest_weight', 0.75)
    defense_advantage = (away_stats["def_rank"] - home_stats["def_rank"]) * 0.2 * st.session_state.get('defense_weight', 1.0)
    pace_advantage = (home_stats["pace"] - away_stats["pace"]) * 0.015 * st.session_state.get('pace_weight', 0.6)
    
    # INJURY IMPACT - now using actual point values directly!
    net_injury_impact = (away_injury_points - home_injury_points) * st.session_state.get('injury_weight', 1.0)
    
    net_rating_advantage = (home_stats["net_rating"] - away_stats["net_rating"]) * 0.1
    altitude_advantage = get_altitude_advantage(home_team) * st.session_state.get('altitude_weight', 1.0)
    
    b2b_impact = 0
    if home_b2b:
        b2b_impact -= 1.5 * st.session_state.get('b2b_weight', 1.0)
    if away_b2b:
        b2b_impact += 1.5 * st.session_state.get('b2b_weight', 1.0)
    
    distance = calculate_distance(away_team, home_team)
    travel_impact = 0
    if distance > 2000:
        travel_impact = 0.75 * st.session_state.get('travel_weight', 0.8)
    elif distance > 1500:
        travel_impact = 0.4 * st.session_state.get('travel_weight', 0.8)
    
    home_l10 = home_form.get('l10_wins', 5) if isinstance(home_form.get('l10_wins'), (int, float)) else 5
    away_l10 = away_form.get('l10_wins', 5) if isinstance(away_form.get('l10_wins'), (int, float)) else 5
    form_diff = (home_l10 - away_l10) * 0.15
    form_impact = form_diff * st.session_state.get('form_weight', 0.7)
    
    total_adjustment = (rest_advantage + defense_advantage + pace_advantage + 
                       net_injury_impact + net_rating_advantage + altitude_advantage +
                       b2b_impact + travel_impact + form_impact)
    
    adjusted_spread = market_spread + total_adjustment
    edge_size = abs(adjusted_spread - market_spread)
    
    if market_spread < 0:
        if adjusted_spread < market_spread:
            kalshi_recommendation = "NO"
            reasoning = f"{away_team} likely to cover +{abs(market_spread):.1f}"
        else:
            kalshi_recommendation = "YES"
            reasoning = f"{home_team} likely to cover {market_spread:+.1f}"
    else:
        if adjusted_spread > market_spread:
            kalshi_recommendation = "YES"
            reasoning = f"{away_team} likely to cover {market_spread:+.1f}"
        else:
            kalshi_recommendation = "NO"
            reasoning = f"{home_team} likely to cover +{abs(market_spread):.1f}"
    
    factors = {
        "rest": rest_advantage, "defense": defense_advantage, "pace": pace_advantage,
        "injury": net_injury_impact, "net_rating": net_rating_advantage,
        "altitude": altitude_advantage, "b2b": b2b_impact, "travel": travel_impact, "form": form_impact
    }
    factor_agreement = len([v for v in factors.values() if abs(v) > 0.3])
    confidence_score = min(100, int(edge_size * 15 + factor_agreement * 10))
    
    kalshi_no_price = 100 - kalshi_yes_price
    if kalshi_recommendation == "YES":
        win_prob = confidence_score / 100
        ev = (win_prob * kalshi_yes_price) - ((1 - win_prob) * 100)
    else:
        win_prob = confidence_score / 100
        ev = (win_prob * kalshi_no_price) - ((1 - win_prob) * 100)
    
    return {
        "kalshi_recommendation": kalshi_recommendation, "reasoning": reasoning,
        "confidence_score": confidence_score, "edge_size": edge_size,
        "adjusted_spread": adjusted_spread, "expected_value": ev,
        "factors": factors, "distance": distance
    }

# Sidebar
st.sidebar.header("🎯 Kalshi Settings")
st.session_state.confidence_threshold = st.sidebar.slider("Confidence Threshold", 50, 90, 65)
st.session_state.min_edge = st.sidebar.slider("Minimum Edge", 0.5, 5.0, 1.0)

st.sidebar.header("🧠 Original Weights")
st.session_state.rest_weight = st.sidebar.slider("Rest Advantage", 0.0, 2.0, 0.75)
st.session_state.defense_weight = st.sidebar.slider("Defense Mismatch", 0.0, 2.0, 1.0)
st.session_state.injury_weight = st.sidebar.slider("Injury Impact", 0.0, 2.0, 1.0)
st.session_state.pace_weight = st.sidebar.slider("Pace Impact", 0.0, 2.0, 0.6)

st.sidebar.header("🆕 New Factor Weights")
st.session_state.altitude_weight = st.sidebar.slider("Altitude (DEN/UTA)", 0.0, 2.0, 1.0)
st.session_state.b2b_weight = st.sidebar.slider("Back-to-Back", 0.0, 2.0, 1.0)
st.session_state.travel_weight = st.sidebar.slider("Travel Distance", 0.0, 2.0, 0.8)
st.session_state.form_weight = st.sidebar.slider("Recent Form (L10)", 0.0, 2.0, 0.7)

# Get auto rest days
rest_data = get_cached_rest_days()
if not rest_data:
    st.cache_data.clear()
    rest_data = fetch_team_rest_days()

# Today's Games
st.header("📅 Today's NBA Games")
todays_games = fetch_todays_games()

if not todays_games:
    st.warning("🚫 No NBA games scheduled today. Use manual analysis below.")
    selected_game = None
else:
    st.success(f"🎯 Found {len(todays_games)} game(s) today - Click to analyze!")
    game_options = ["Select a game..."] + [f"{g['away_team']} @ {g['home_team']} - {g['game_time']}" for g in todays_games]
    selected_game_str = st.selectbox("🏀 Pick a game to analyze", game_options)
    if selected_game_str != "Select a game...":
        selected_game = None
        for g in todays_games:
            if f"{g['away_team']} @ {g['home_team']}" in selected_game_str:
                selected_game = g
                break
    else:
        selected_game = None

# Manual Analysis
st.header("🔍 Game Analysis")
st.write("**Select teams • Everything auto-detected • No manual input needed**")

if 'selected_game' in dir() and selected_game:
    try:
        home_index = list(team_mapping.keys()).index(selected_game['home_team'])
    except:
        home_index = 1
    try:
        away_index = list(team_mapping.keys()).index(selected_game['away_team'])
    except:
        away_index = 0
else:
    home_index = 1
    away_index = 0

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Home Team")
    manual_home = st.selectbox("Home Team", list(team_mapping.keys()), index=home_index)
    
    auto_home_rest = rest_data.get(manual_home, 1)
    manual_home_rest = st.number_input("Home Rest Days", 0, 7, min(auto_home_rest, 7), 
                                        help=f"Auto-detected: {auto_home_rest} days")
    
    # FULLY AUTOMATIC INJURY DETECTION
    home_injuries = get_cached_injuries(manual_home)
    home_injury_points, home_injury_details = calculate_injury_impact(home_injuries)
    home_severity_label, home_severity_class = get_injury_severity_label(home_injury_points)
    
    # Display injury status automatically - NO DROPDOWN
    st.markdown(f"**Injury Status:** {home_severity_label} ({home_injury_points:.1f} pts)")
    
    if home_injury_details:
        with st.expander(f"🏥 {len(home_injury_details)} injuries detected - Click for details"):
            for inj in home_injury_details:
                st.write(f"• {inj['tier_label']} **{inj['player']}**: {inj['status']} (-{inj['points']:.1f} pts)")
    else:
        st.write("✅ No injuries reported")
    
    home_b2b = manual_home_rest == 0
    if home_b2b:
        st.warning("⚠️ BACK-TO-BACK detected")

with col2:
    st.subheader("✈️ Away Team")
    manual_away = st.selectbox("Away Team", list(team_mapping.keys()), index=away_index)
    
    auto_away_rest = rest_data.get(manual_away, 1)
    manual_away_rest = st.number_input("Away Rest Days", 0, 7, min(auto_away_rest, 7),
                                        help=f"Auto-detected: {auto_away_rest} days")
    
    # FULLY AUTOMATIC INJURY DETECTION
    away_injuries = get_cached_injuries(manual_away)
    away_injury_points, away_injury_details = calculate_injury_impact(away_injuries)
    away_severity_label, away_severity_class = get_injury_severity_label(away_injury_points)
    
    # Display injury status automatically - NO DROPDOWN
    st.markdown(f"**Injury Status:** {away_severity_label} ({away_injury_points:.1f} pts)")
    
    if away_injury_details:
        with st.expander(f"🏥 {len(away_injury_details)} injuries detected - Click for details"):
            for inj in away_injury_details:
                st.write(f"• {inj['tier_label']} **{inj['player']}**: {inj['status']} (-{inj['points']:.1f} pts)")
    else:
        st.write("✅ No injuries reported")
    
    away_b2b = manual_away_rest == 0
    if away_b2b:
        st.warning("⚠️ BACK-TO-BACK detected")

distance = calculate_distance(manual_away, manual_home)
altitude = team_locations.get(manual_home, {}).get("altitude", 0)
st.info(f"📍 Travel distance: **{distance:.0f} miles** | 🏔️ Home altitude: **{altitude:,} ft**")

st.subheader("📊 Market Data")
col3, col4 = st.columns(2)
with col3:
    manual_spread = st.slider("Spread Line (- = home favored)", -15.0, 15.0, -3.5, 0.5)
with col4:
    manual_yes_price = st.slider("Kalshi YES Price (cents)", 10, 90, 50)

if st.button("📈 Analyze Game", type="primary"):
    result = calculate_kalshi_edge(
        manual_home, manual_away, manual_spread, manual_home_rest, manual_away_rest,
        home_injury_points, away_injury_points, manual_yes_price, home_b2b, away_b2b
    )
    
    st.subheader("📊 Analysis Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Market Spread", f"{manual_spread:+.1f}")
        st.metric("Adjusted Spread", f"{result['adjusted_spread']:+.1f}")
    
    with col2:
        st.metric("Edge Size", f"{result['edge_size']:.1f} pts")
        st.metric("Confidence", f"{result['confidence_score']}%")
    
    with col3:
        st.metric("Expected Value", f"{result['expected_value']:+.1f}¢")
        st.progress(result['confidence_score'] / 100)
    
    st.markdown("---")
    
    if result['edge_size'] >= st.session_state.min_edge and result['confidence_score'] >= st.session_state.confidence_threshold:
        if result['expected_value'] > 0:
            st.success(f"💰 **RECOMMENDATION: BUY {result['kalshi_recommendation']}**")
            st.info(f"📊 {result['reasoning']}")
        else:
            st.warning("⚖️ Edge detected but negative EV - PASS")
    else:
        st.error("🔍 Insufficient edge or confidence - NO TRADE")
    
    with st.expander("View Factor Breakdown (9 Factors)"):
        factors = result['factors']
        st.write("**Original Factors:**")
        st.write(f"• Rest Advantage: {factors['rest']:+.2f}")
        st.write(f"• Defense Advantage: {factors['defense']:+.2f}")
        st.write(f"• Pace Advantage: {factors['pace']:+.2f}")
        st.write(f"• 🏥 Injury Impact: {factors['injury']:+.2f} pts (Home: -{home_injury_points:.1f}, Away: -{away_injury_points:.1f})")
        st.write(f"• Net Rating Advantage: {factors['net_rating']:+.2f}")
        st.write("**New Factors:**")
        st.write(f"• 🏔️ Altitude Advantage: {factors['altitude']:+.2f}")
        st.write(f"• 🔄 Back-to-Back Impact: {factors['b2b']:+.2f}")
        st.write(f"• ✈️ Travel Fatigue: {factors['travel']:+.2f}")
        st.write(f"• 📈 Recent Form (L10): {factors['form']:+.2f}")

st.sidebar.markdown("---")
st.sidebar.header("💡 Guide")
st.sidebar.write("• EV > 5¢ = Good trade")
st.sidebar.write("• Confidence > 65% = High conviction")
st.sidebar.write("• Edge > 1.0 = Mispricing detected")

st.sidebar.header("🏥 Injury Point Values")
st.sidebar.write("**⭐⭐⭐ MVP OUT:** 6.0 pts")
st.sidebar.write("**⭐⭐ All-Star OUT:** 4.0 pts")
st.sidebar.write("**⭐ Starter OUT:** 2.0 pts")
st.sidebar.write("**Bench OUT:** 0.5 pts")

st.sidebar.header("📡 Status")
st.sidebar.write(f"• Games today: {len(todays_games)}")
st.sidebar.write(f"• Factors: 9 active")
st.sidebar.write(f"• Rest data: {'✅ Auto' if rest_data else '❌ Manual'}")
st.sidebar.write(f"• Injuries: ✅ Auto (ESPN)")
st.sidebar.write(f"• Updated: {datetime.now().strftime('%I:%M %p')}")

st.markdown("---")
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. Past performance does not guarantee future results. You may lose money. Only bet what you can afford to lose. The creator assumes no liability for any losses.")
