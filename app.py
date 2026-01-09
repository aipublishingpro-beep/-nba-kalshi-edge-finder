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
st.write("**Real Today's Games • Auto Rest Detection • 9 Edge Factors**")

team_mapping = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
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

INJURY_LEVELS = {
    0: "No key injuries",
    1: "Rotation player out",
    2: "Star questionable / limited",
    3: "Star confirmed OUT"
}

def injury_points(level):
    return {0: 0.0, 1: 1.0, 2: 2.5, 3: 4.0}.get(level, 0.0)

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

def get_timezone_disadvantage(home_team, away_team):
    home_loc = team_locations.get(home_team)
    away_loc = team_locations.get(away_team)
    if not home_loc or not away_loc:
        return 0
    tz_diff = abs(home_loc["tz"] - away_loc["tz"])
    if away_loc["tz"] < home_loc["tz"]:
        return tz_diff * 0.3
    return 0

def fetch_todays_games():
    try:
        url = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.nba.com/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for game in data.get('games', []):
                home_team = game['homeTeam']['teamName']
                away_team = game['awayTeam']['teamName']
                game_time = game['gameTimeUTC']
                game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                game_time_local = game_dt.astimezone().strftime('%I:%M %p')
                home_full = next((k for k in team_mapping.keys() if home_team in k), home_team)
                away_full = next((k for k in team_mapping.keys() if away_team in k), away_team)
                games.append({
                    'home_team': home_full,
                    'away_team': away_full,
                    'game_time': game_time_local,
                    'game_id': game['gameId']
                })
            return games
        else:
            return []
    except Exception as e:
        st.error(f"❌ Failed to fetch games: {e}")
        return []

def fetch_team_rest_days():
    """Check last 5 days of ESPN scoreboards to find when each team last played"""
    try:
        today = datetime.now().date()
        last_game = {}
        
        # ESPN team abbreviation to full name mapping
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
        
        # Check last 5 days
        for days_ago in range(1, 6):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime('%Y%m%d')
            
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for event in data.get('events', []):
                        for comp in event.get('competitions', []):
                            for team in comp.get('competitors', []):
                                abbrev = team.get('team', {}).get('abbreviation', '')
                                full_name = espn_teams.get(abbrev)
                                
                                if full_name and full_name not in last_game:
                                    last_game[full_name] = check_date
            except:
                continue
        
        # Calculate rest days: played yesterday = 0 rest, played 2 days ago = 1 rest
        rest_days = {}
        for team, last_date in last_game.items():
            days_since = (today - last_date).days
            rest = max(0, days_since - 1)
            rest_days[team] = rest
        
        return rest_days
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)
def get_cached_rest_days():
    return fetch_team_rest_days()

def fetch_team_record():
    try:
        url = "https://cdn.nba.com/static/json/liveData/standings/standings_00.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.nba.com/'
        }
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
                          home_injury_level, away_injury_level, kalshi_yes_price,
                          home_b2b, away_b2b):
    home_stats = team_stats.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    away_stats = team_stats.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    
    standings = get_cached_standings()
    home_form = standings.get(home_team, {'l10_wins': 5, 'streak': 0})
    away_form = standings.get(away_team, {'l10_wins': 5, 'streak': 0})
    
    rest_advantage = (home_rest - away_rest) * st.session_state.get('rest_weight', 0.75)
    defense_advantage = (away_stats["def_rank"] - home_stats["def_rank"]) * 0.2 * st.session_state.get('defense_weight', 1.0)
    pace_advantage = (home_stats["pace"] - away_stats["pace"]) * 0.015 * st.session_state.get('pace_weight', 0.6)
    
    home_injury_impact = injury_points(home_injury_level)
    away_injury_impact = injury_points(away_injury_level)
    net_injury_impact = (away_injury_impact - home_injury_impact) * st.session_state.get('injury_weight', 1.25)
    
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
        "rest": rest_advantage,
        "defense": defense_advantage,
        "pace": pace_advantage,
        "injury": net_injury_impact,
        "net_rating": net_rating_advantage,
        "altitude": altitude_advantage,
        "b2b": b2b_impact,
        "travel": travel_impact,
        "form": form_impact
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
        "kalshi_recommendation": kalshi_recommendation,
        "reasoning": reasoning,
        "confidence_score": confidence_score,
        "edge_size": edge_size,
        "adjusted_spread": adjusted_spread,
        "expected_value": ev,
        "factors": factors,
        "distance": distance
    }

# Sidebar
st.sidebar.header("🎯 Kalshi Settings")
st.session_state.confidence_threshold = st.sidebar.slider("Confidence Threshold", 50, 90, 65)
st.session_state.min_edge = st.sidebar.slider("Minimum Edge", 0.5, 5.0, 1.0)

st.sidebar.header("🧠 Original Weights")
st.session_state.rest_weight = st.sidebar.slider("Rest Advantage", 0.0, 2.0, 0.75)
st.session_state.defense_weight = st.sidebar.slider("Defense Mismatch", 0.0, 2.0, 1.0)
st.session_state.injury_weight = st.sidebar.slider("Injury Impact", 0.0, 3.0, 1.25)
st.session_state.pace_weight = st.sidebar.slider("Pace Impact", 0.0, 2.0, 0.6)

st.sidebar.header("🆕 New Factor Weights")
st.session_state.altitude_weight = st.sidebar.slider("Altitude (DEN/UTA)", 0.0, 2.0, 1.0)
st.session_state.b2b_weight = st.sidebar.slider("Back-to-Back", 0.0, 2.0, 1.0)
st.session_state.travel_weight = st.sidebar.slider("Travel Distance", 0.0, 2.0, 0.8)
st.session_state.form_weight = st.sidebar.slider("Recent Form (L10)", 0.0, 2.0, 0.7)

# Get auto rest days
rest_data = get_cached_rest_days()

# Cache clear button
if st.sidebar.button("🔄 Refresh Rest Data"):
    st.cache_data.clear()
    st.rerun()

# Today's Games
st.header("📅 Today's NBA Games")
todays_games = fetch_todays_games()

if not todays_games:
    st.warning("🚫 No NBA games scheduled today. Use manual analysis below.")
else:
    st.success(f"🎯 Found {len(todays_games)} game(s) today")
    for i, game in enumerate(todays_games):
        st.write(f"**Game {i+1}:** {game['away_team']} @ {game['home_team']} - {game['game_time']}")

# Manual Analysis
st.header("🔍 Game Analysis")
st.write("**Select teams • Rest days auto-detected • Injury status manual**")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🏠 Home Team")
    manual_home = st.selectbox("Home Team", list(team_mapping.keys()), index=13)
    
    auto_home_rest = rest_data.get(manual_home, 1)
    home_is_b2b = auto_home_rest == 0
    manual_home_rest = st.number_input("Home Rest Days", 0, 7, min(auto_home_rest, 7), 
                                        help=f"Auto-detected: {auto_home_rest} days")
    home_injury_level = st.selectbox(
        "Home Injury Status",
        options=list(INJURY_LEVELS.keys()),
        format_func=lambda x: INJURY_LEVELS[x],
        key="home_injury"
    )
    home_b2b = st.checkbox("Home team on BACK-TO-BACK", value=home_is_b2b, key="home_b2b")

with col2:
    st.subheader("✈️ Away Team")
    manual_away = st.selectbox("Away Team", list(team_mapping.keys()), index=9)
    
    auto_away_rest = rest_data.get(manual_away, 1)
    away_is_b2b = auto_away_rest == 0
    manual_away_rest = st.number_input("Away Rest Days", 0, 7, min(auto_away_rest, 7),
                                        help=f"Auto-detected: {auto_away_rest} days")
    away_injury_level = st.selectbox(
        "Away Injury Status",
        options=list(INJURY_LEVELS.keys()),
        format_func=lambda x: INJURY_LEVELS[x],
        key="away_injury"
    )
    away_b2b = st.checkbox("Away team on BACK-TO-BACK", value=away_is_b2b, key="away_b2b")

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
        home_injury_level, away_injury_level, manual_yes_price, home_b2b, away_b2b
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
        st.write(f"• Injury Impact: {factors['injury']:+.2f}")
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

st.sidebar.header("🏥 Injury Levels")
st.sidebar.write("• 0 = Full strength")
st.sidebar.write("• 1 = Role player out")
st.sidebar.write("• 2 = Star questionable")
st.sidebar.write("• 3 = Star OUT")

st.sidebar.header("🆕 New Factors")
st.sidebar.write("• 🏔️ Denver = +1.5 pts")
st.sidebar.write("• 🏔️ Utah = +0.75 pts")
st.sidebar.write("• 🔄 B2B = 1.5 pt penalty")
st.sidebar.write("• ✈️ >2000mi = +0.75 pts")

st.sidebar.header("📡 Status")
st.sidebar.write(f"• Games today: {len(todays_games)}")
st.sidebar.write(f"• Factors: 9 active")
st.sidebar.write(f"• Rest data: {'✅ Loaded' if rest_data else '❌ Manual'}")
st.sidebar.write(f"• Updated: {datetime.now().strftime('%I:%M %p')}")

st.markdown("---")
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. Past performance does not guarantee future results. You may lose money. Only bet what you can afford to lose. The creator assumes no liability for any losses.")
