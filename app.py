import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stAlert {margin-top: 1rem;}
    .metric-card {background: #1E1E1E; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;}
    div[data-testid="stMetricValue"] {font-size: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# Team stats (2024-25 season estimates - update as needed)
TEAM_STATS = {
    "Atlanta": {"abbrev": "ATL", "net_rating": -1.5, "def_rank": 22, "pace": 100.2},
    "Boston": {"abbrev": "BOS", "net_rating": 10.5, "def_rank": 2, "pace": 98.5},
    "Brooklyn": {"abbrev": "BKN", "net_rating": -5.2, "def_rank": 25, "pace": 99.8},
    "Charlotte": {"abbrev": "CHA", "net_rating": -6.8, "def_rank": 27, "pace": 101.5},
    "Chicago": {"abbrev": "CHI", "net_rating": -3.5, "def_rank": 20, "pace": 98.2},
    "Cleveland": {"abbrev": "CLE", "net_rating": 9.8, "def_rank": 3, "pace": 97.5},
    "Dallas": {"abbrev": "DAL", "net_rating": 3.2, "def_rank": 12, "pace": 99.5},
    "Denver": {"abbrev": "DEN", "net_rating": 5.5, "def_rank": 8, "pace": 98.8},
    "Detroit": {"abbrev": "DET", "net_rating": -4.8, "def_rank": 24, "pace": 100.5},
    "Golden State": {"abbrev": "GSW", "net_rating": 2.8, "def_rank": 14, "pace": 99.2},
    "Houston": {"abbrev": "HOU", "net_rating": 4.5, "def_rank": 6, "pace": 99.8},
    "Indiana": {"abbrev": "IND", "net_rating": 1.2, "def_rank": 18, "pace": 102.5},
    "LA Clippers": {"abbrev": "LAC", "net_rating": 0.5, "def_rank": 15, "pace": 97.8},
    "LA Lakers": {"abbrev": "LAL", "net_rating": 2.5, "def_rank": 16, "pace": 98.5},
    "Memphis": {"abbrev": "MEM", "net_rating": 3.8, "def_rank": 10, "pace": 100.8},
    "Miami": {"abbrev": "MIA", "net_rating": 1.8, "def_rank": 11, "pace": 97.2},
    "Milwaukee": {"abbrev": "MIL", "net_rating": 4.2, "def_rank": 9, "pace": 98.8},
    "Minnesota": {"abbrev": "MIN", "net_rating": 6.5, "def_rank": 4, "pace": 97.8},
    "New Orleans": {"abbrev": "NOP", "net_rating": -2.8, "def_rank": 21, "pace": 99.5},
    "New York": {"abbrev": "NYK", "net_rating": 5.8, "def_rank": 5, "pace": 97.5},
    "Oklahoma City": {"abbrev": "OKC", "net_rating": 11.2, "def_rank": 1, "pace": 98.2},
    "Orlando": {"abbrev": "ORL", "net_rating": 3.5, "def_rank": 7, "pace": 96.8},
    "Philadelphia": {"abbrev": "PHI", "net_rating": 0.8, "def_rank": 17, "pace": 98.5},
    "Phoenix": {"abbrev": "PHX", "net_rating": 2.2, "def_rank": 19, "pace": 99.2},
    "Portland": {"abbrev": "POR", "net_rating": -7.5, "def_rank": 28, "pace": 100.2},
    "Sacramento": {"abbrev": "SAC", "net_rating": -1.2, "def_rank": 23, "pace": 100.5},
    "San Antonio": {"abbrev": "SAS", "net_rating": -4.5, "def_rank": 26, "pace": 99.8},
    "Toronto": {"abbrev": "TOR", "net_rating": -3.2, "def_rank": 29, "pace": 99.5},
    "Utah": {"abbrev": "UTA", "net_rating": -8.5, "def_rank": 30, "pace": 100.8},
    "Washington": {"abbrev": "WAS", "net_rating": -9.2, "def_rank": 30, "pace": 101.2},
}

# Team city coordinates for travel distance (lat, lon)
TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396),
    "Boston": (42.366, -71.062),
    "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839),
    "Chicago": (41.881, -87.674),
    "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810),
    "Denver": (39.749, -105.010),
    "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388),
    "Houston": (29.751, -95.362),
    "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267),
    "LA Lakers": (34.043, -118.267),
    "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188),
    "Milwaukee": (43.045, -87.917),
    "Minnesota": (44.979, -93.276),
    "New Orleans": (29.949, -90.082),
    "New York": (40.751, -73.994),
    "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384),
    "Philadelphia": (39.901, -75.172),
    "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667),
    "Sacramento": (38.580, -121.500),
    "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379),
    "Utah": (40.768, -111.901),
    "Washington": (38.898, -77.021),
}

def calculate_travel_distance(team1, team2):
    """Calculate approximate travel distance in miles between two teams"""
    import math
    loc1 = TEAM_LOCATIONS.get(team1)
    loc2 = TEAM_LOCATIONS.get(team2)
    if not loc1 or not loc2:
        return 0
    # Haversine formula
    lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
    lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    miles = 3956 * c  # Earth radius in miles
    return round(miles)

# Kalshi abbreviation to full name mapping
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_kalshi_nba_games():
    """Fetch NBA games directly from Kalshi API"""
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=100"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        games = []
        markets = data.get('markets', [])
        
        for market in markets:
            ticker = market.get('ticker', '')
            title = market.get('title', '')
            
            # Parse the ticker to get teams (format: KXNBAGAME-25JAN09TORBOS)
            if '-' in ticker:
                game_code = ticker.split('-')[1] if len(ticker.split('-')) > 1 else ''
                # Extract team abbreviations from ticker (last 6 chars are 2 teams)
                if len(game_code) >= 6:
                    away_abbrev = game_code[-6:-3].upper()
                    home_abbrev = game_code[-3:].upper()
                    
                    away_team = KALSHI_ABBREV_MAP.get(away_abbrev, away_abbrev)
                    home_team = KALSHI_ABBREV_MAP.get(home_abbrev, home_abbrev)
                    
                    # Get prices from Kalshi (in cents)
                    yes_bid = market.get('yes_bid', 0) or 0
                    yes_ask = market.get('yes_ask', 0) or 0
                    no_bid = market.get('no_bid', 0) or 0
                    no_ask = market.get('no_ask', 0) or 0
                    
                    # Use mid price
                    yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid
                    
                    # Get game time
                    close_time = market.get('close_time', '')
                    
                    games.append({
                        'ticker': ticker,
                        'title': title,
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_abbrev': away_abbrev,
                        'home_abbrev': home_abbrev,
                        'yes_price': yes_price,  # Home team win price
                        'no_price': 100 - yes_price if yes_price else 0,  # Away team win price
                        'yes_bid': yes_bid,
                        'yes_ask': yes_ask,
                        'volume': market.get('volume', 0),
                        'close_time': close_time,
                        'subtitle': market.get('subtitle', ''),
                        'event_ticker': market.get('event_ticker', '')
                    })
        
        return games
    except Exception as e:
        st.error(f"Error fetching Kalshi data: {e}")
        return []

@st.cache_data(ttl=14400)  # Cache for 4 hours
def fetch_nba_injuries():
    """Scrape ESPN for NBA injuries"""
    try:
        url = "https://www.espn.com/nba/injuries"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, 'lxml')
        
        injuries = {}
        teams = soup.find_all('div', class_='ResponsiveTable')
        
        for team in teams:
            header = team.find_previous('div', class_='Table__Title')
            if header:
                team_name = header.text.strip()
                injuries[team_name] = []
                rows = team.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        player = cells[0].text.strip()
                        status = cells[2].text.strip() if len(cells) > 2 else "Unknown"
                        injuries[team_name].append(f"{player} ({status})")
        
        return injuries
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_team_last_games():
    """Fetch recent NBA schedule to calculate rest days for each team"""
    try:
        # Get games from the last 7 days
        team_last_game = {}
        today = datetime.now()
        
        # NBA API for scoreboard - check last 7 days
        for days_ago in range(1, 8):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime("%Y-%m-%d")
            
            url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
            # Use the historical endpoint
            hist_url = f"https://stats.nba.com/stats/scoreboardv2?GameDate={date_str}&LeagueID=00"
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.nba.com/',
                'Accept': 'application/json'
            }
            
            try:
                resp = requests.get(hist_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    game_header = data.get('resultSets', [{}])[0]
                    headers_list = game_header.get('headers', [])
                    rows = game_header.get('rowSet', [])
                    
                    if 'HOME_TEAM_ID' in headers_list and 'VISITOR_TEAM_ID' in headers_list:
                        home_idx = headers_list.index('HOME_TEAM_ID')
                        away_idx = headers_list.index('VISITOR_TEAM_ID')
                        
                        for row in rows:
                            # Map team IDs to names and store last game date
                            pass  # Complex mapping needed
            except:
                pass
        
        return team_last_game
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)  # Cache for 1 hour  
def fetch_rest_days_espn():
    """Fetch rest days from ESPN schedule"""
    try:
        team_rest = {}
        today = datetime.now()
        
        # Scrape ESPN schedule for last 5 days
        for days_ago in range(1, 6):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime("%Y%m%d")
            
            url = f"https://www.espn.com/nba/schedule/_/date/{date_str}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.content, 'lxml')
                
                # Find all team links in the schedule
                team_links = soup.find_all('a', class_='AnchorLink')
                for link in team_links:
                    href = link.get('href', '')
                    if '/nba/team/' in href:
                        team_name = link.text.strip()
                        # Map ESPN names to our names
                        team_mapped = map_espn_team_name(team_name)
                        if team_mapped and team_mapped not in team_rest:
                            team_rest[team_mapped] = days_ago
            except:
                continue
        
        return team_rest
    except:
        return {}

def map_espn_team_name(espn_name):
    """Map ESPN team names to our standard names"""
    espn_map = {
        "Hawks": "Atlanta", "Celtics": "Boston", "Nets": "Brooklyn",
        "Hornets": "Charlotte", "Bulls": "Chicago", "Cavaliers": "Cleveland",
        "Mavericks": "Dallas", "Nuggets": "Denver", "Pistons": "Detroit",
        "Warriors": "Golden State", "Rockets": "Houston", "Pacers": "Indiana",
        "Clippers": "LA Clippers", "Lakers": "LA Lakers", "Grizzlies": "Memphis",
        "Heat": "Miami", "Bucks": "Milwaukee", "Timberwolves": "Minnesota",
        "Pelicans": "New Orleans", "Knicks": "New York", "Thunder": "Oklahoma City",
        "Magic": "Orlando", "76ers": "Philadelphia", "Suns": "Phoenix",
        "Trail Blazers": "Portland", "Blazers": "Portland", "Kings": "Sacramento",
        "Spurs": "San Antonio", "Raptors": "Toronto", "Jazz": "Utah",
        "Wizards": "Washington",
        # Full names
        "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston",
        "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte",
        "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
        "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver",
        "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State",
        "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
        "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
        "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
        "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
        "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota",
        "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York",
        "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
        "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix",
        "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento",
        "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
        "Utah Jazz": "Utah", "Washington Wizards": "Washington"
    }
    return espn_map.get(espn_name, None)

def get_team_rest_days(team_name, rest_data, default=2):
    """Get rest days for a team, with fallback to default"""
    return rest_data.get(team_name, default)

def calculate_edge(home_team, away_team, kalshi_home_price, home_rest, away_rest, home_injuries, away_injuries, away_travel_miles, weights):
    """Calculate edge based on 6 factors with adjustable weights"""
    
    home_stats = TEAM_STATS.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 99})
    away_stats = TEAM_STATS.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 99})
    
    # ===== FACTOR 1: REST ADVANTAGE =====
    rest_diff = home_rest - away_rest
    if rest_diff > 0:
        rest_score = min(rest_diff * 2, 6)  # Max 6 points for rest advantage
    elif rest_diff < 0:
        rest_score = max(rest_diff * 2, -6)
    else:
        rest_score = 0
    
    # ===== FACTOR 2: DEFENSE MISMATCH =====
    # Lower rank = better defense. If home has better D (lower rank), positive score
    def_diff = away_stats['def_rank'] - home_stats['def_rank']
    def_score = def_diff * 0.15  # Scale factor
    
    # ===== FACTOR 3: INJURY IMPACT =====
    injury_diff = away_injuries - home_injuries
    injury_score = injury_diff * 1.5  # Each injury worth ~1.5 points
    
    # ===== FACTOR 4: PACE DIFFERENTIAL =====
    pace_diff = home_stats['pace'] - away_stats['pace']
    # Higher pace can benefit better offensive teams
    if home_stats['net_rating'] > away_stats['net_rating']:
        pace_score = pace_diff * 0.1
    else:
        pace_score = -pace_diff * 0.1
    
    # ===== FACTOR 5: NET RATING =====
    net_diff = home_stats['net_rating'] - away_stats['net_rating']
    net_score = net_diff * 0.8  # Primary factor
    
    # ===== FACTOR 6: TRAVEL FATIGUE =====
    # Away team traveling long distance = advantage for home
    # 0-500 miles = no impact, 500-1500 = small impact, 1500+ = bigger impact
    if away_travel_miles > 1500:
        travel_score = 2.5
    elif away_travel_miles > 1000:
        travel_score = 1.5
    elif away_travel_miles > 500:
        travel_score = 0.75
    else:
        travel_score = 0
    
    # ===== HOME COURT ADVANTAGE (baseline) =====
    home_court = 3.0
    
    # ===== WEIGHTED COMBINATION =====
    weighted_spread = (
        home_court +
        rest_score * weights['rest'] +
        def_score * weights['defense'] +
        injury_score * weights['injury'] +
        pace_score * weights['pace'] +
        net_score * weights['net_rating'] +
        travel_score * weights['travel']
    )
    
    # Convert spread to win probability
    spread_to_prob = 0.025
    home_win_prob = 50 + (weighted_spread * spread_to_prob * 100)
    home_win_prob = max(5, min(95, home_win_prob))
    
    # Calculate edge vs Kalshi price
    edge = home_win_prob - kalshi_home_price
    
    # Expected value calculation
    if edge > 0:
        ev = (home_win_prob / 100) * (100 - kalshi_home_price) - ((100 - home_win_prob) / 100) * kalshi_home_price
    else:
        ev = ((100 - home_win_prob) / 100) * kalshi_home_price - (home_win_prob / 100) * (100 - kalshi_home_price)
    
    return {
        'home_win_prob': round(home_win_prob, 1),
        'kalshi_price': kalshi_home_price,
        'edge': round(edge, 1),
        'expected_spread': round(weighted_spread, 1),
        'expected_value': round(ev, 2),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW'),
        # Individual factor scores for breakdown
        'factors': {
            'rest': round(rest_score * weights['rest'], 2),
            'defense': round(def_score * weights['defense'], 2),
            'injury': round(injury_score * weights['injury'], 2),
            'pace': round(pace_score * weights['pace'], 2),
            'net_rating': round(net_score * weights['net_rating'], 2),
            'travel': round(travel_score * weights['travel'], 2),
            'home_court': home_court
        },
        # Raw values for display
        'raw': {
            'rest_diff': rest_diff,
            'def_diff': def_diff,
            'injury_diff': injury_diff,
            'pace_diff': round(pace_diff, 1),
            'net_diff': round(net_diff, 1),
            'travel_miles': away_travel_miles
        }
    }

# ========== MAIN APP ==========

st.title("🏀 NBA Kalshi Edge Finder")
st.markdown("**Powered by Kalshi API** - Real-time prices direct from Kalshi")

# ========== SIDEBAR ==========
st.sidebar.header("⚙️ Factor Weights")
st.sidebar.caption("Adjust how much each factor influences the edge calculation")

weights = {
    'rest': st.sidebar.slider("🛏️ Rest Advantage", 0.0, 2.0, 1.0, 0.1),
    'defense': st.sidebar.slider("🛡️ Defense Mismatch", 0.0, 2.0, 1.0, 0.1),
    'injury': st.sidebar.slider("🏥 Injury Impact", 0.0, 2.0, 1.0, 0.1),
    'pace': st.sidebar.slider("⚡ Pace Differential", 0.0, 2.0, 1.0, 0.1),
    'net_rating': st.sidebar.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1),
    'travel': st.sidebar.slider("✈️ Travel Fatigue", 0.0, 2.0, 1.0, 0.1),
}

st.sidebar.markdown("---")
st.sidebar.header("🎯 Display Settings")
min_edge = st.sidebar.slider("Minimum Edge to Highlight", 0, 20, 5)
show_all = st.sidebar.checkbox("Show all games", value=True)

st.sidebar.markdown("---")
st.sidebar.header("📅 Default Rest Days")
st.sidebar.caption("Fallback if auto-detection fails")
default_home_rest = st.sidebar.number_input("Default Home Rest", 1, 7, 2)
default_away_rest = st.sidebar.number_input("Default Away Rest", 1, 7, 2)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ========== FETCH DATA ==========
with st.spinner("Fetching Kalshi NBA markets..."):
    games = fetch_kalshi_nba_games()
    injuries = fetch_nba_injuries()
    rest_days_data = fetch_rest_days_espn()

if rest_days_data:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛏️ Auto Rest Days")
    st.sidebar.caption(f"Found rest data for {len(rest_days_data)} teams")
    st.sidebar.caption("(Days since last game)")
else:
    st.sidebar.caption("Rest days: using defaults")

if not games:
    st.warning("No NBA games found on Kalshi right now. Games appear closer to game time.")
    st.info("Check back when games are scheduled, or verify at: https://kalshi.com/sports/basketball/Pro%20Basketball%20(M)")
else:
    st.success(f"✅ Found **{len(games)} NBA games** on Kalshi")
    
    # Display games
    for game in games:
        home = game['home_team']
        away = game['away_team']
        kalshi_price = game['yes_price']
        
        # Count injuries
        home_injury_list = injuries.get(home, [])
        away_injury_list = injuries.get(away, [])
        home_injury_count = len(home_injury_list)
        away_injury_count = len(away_injury_list)
        
        # Calculate travel distance for away team
        away_travel = calculate_travel_distance(away, home)
        
        # Get auto rest days (fallback to sidebar default)
        auto_home_rest = get_team_rest_days(home, rest_days_data, default_home_rest)
        auto_away_rest = get_team_rest_days(away, rest_days_data, default_away_rest)
        
        # Calculate edge with all 6 factors
        analysis = calculate_edge(
            home, away, kalshi_price,
            home_rest=auto_home_rest,
            away_rest=auto_away_rest,
            home_injuries=home_injury_count,
            away_injuries=away_injury_count,
            away_travel_miles=away_travel,
            weights=weights
        )
        
        # Skip if below minimum edge and not showing all
        if not show_all and abs(analysis['edge']) < min_edge:
            continue
        
        # Color coding
        if analysis['recommendation'] == 'BUY YES':
            rec_color = "🟢"
        elif analysis['recommendation'] == 'BUY NO':
            rec_color = "🔴"
        else:
            rec_color = "⚪"
        
        # Parse game date from close_time
        game_date_str = ""
        if game['close_time']:
            try:
                game_dt = datetime.fromisoformat(game['close_time'].replace('Z', '+00:00'))
                game_date_str = game_dt.strftime("%b %d")  # e.g., "Jan 09"
            except:
                game_date_str = ""
        
        with st.expander(f"{rec_color} {game_date_str} | {away} @ {home} | Edge: {analysis['edge']:+.1f}% | {analysis['recommendation']}", expanded=False):
            
            # Rest days inputs for this specific game (auto-filled, can override)
            st.markdown("### 🛏️ Rest Days (Auto-detected, adjust if needed)")
            rest_col1, rest_col2 = st.columns(2)
            with rest_col1:
                game_away_rest = st.number_input(f"{away} rest days", 0, 7, auto_away_rest, key=f"away_rest_{game['ticker']}")
            with rest_col2:
                game_home_rest = st.number_input(f"{home} rest days", 0, 7, auto_home_rest, key=f"home_rest_{game['ticker']}")
            
            # Recalculate with user-input rest days
            analysis = calculate_edge(
                home, away, kalshi_price,
                home_rest=game_home_rest,
                away_rest=game_away_rest,
                home_injuries=home_injury_count,
                away_injuries=away_injury_count,
                away_travel_miles=away_travel,
                weights=weights
            )
            
            st.markdown("---")
            
            with col1:
                st.markdown("### 📊 Kalshi Prices")
                st.metric(f"{home} (YES)", f"{kalshi_price:.0f}¢")
                st.metric(f"{away} (NO)", f"{100-kalshi_price:.0f}¢")
                st.caption(f"Volume: {game['volume']:,} contracts")
            
            with col2:
                st.markdown("### 🎯 Our Model")
                st.metric(f"{home} Win Prob", f"{analysis['home_win_prob']:.1f}%")
                st.metric("Expected Spread", f"{home} {analysis['expected_spread']:+.1f}")
            
            with col3:
                st.markdown("### 💰 Recommendation")
                edge_val = analysis['edge']
                st.metric("Edge", f"{edge_val:+.1f}%", delta=f"{analysis['confidence']} confidence")
                st.metric("Expected Value", f"{analysis['expected_value']:+.2f}¢")
                
                # Clickable trade button
                kalshi_url = f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{game['ticker'].lower()}"
                
                if analysis['recommendation'] == 'BUY YES':
                    st.link_button(f"🟢 BUY YES on {home}", kalshi_url, use_container_width=True)
                elif analysis['recommendation'] == 'BUY NO':
                    st.link_button(f"🔴 BUY NO (bet {away})", kalshi_url, use_container_width=True)
                else:
                    st.info("No significant edge")
            
            # Row 2: Factor Breakdown
            st.markdown("---")
            st.markdown("### 📈 Factor Breakdown")
            
            factor_col1, factor_col2, factor_col3, factor_col4, factor_col5, factor_col6 = st.columns(6)
            
            factors = analysis['factors']
            raw = analysis['raw']
            
            with factor_col1:
                st.markdown("**🛏️ Rest**")
                st.metric("Impact", f"{factors['rest']:+.2f}")
                st.caption(f"Diff: {raw['rest_diff']:+d} days")
            
            with factor_col2:
                st.markdown("**🛡️ Defense**")
                st.metric("Impact", f"{factors['defense']:+.2f}")
                st.caption(f"Rank diff: {raw['def_diff']:+d}")
            
            with factor_col3:
                st.markdown("**🏥 Injuries**")
                st.metric("Impact", f"{factors['injury']:+.2f}")
                st.caption(f"Diff: {raw['injury_diff']:+d}")
            
            with factor_col4:
                st.markdown("**⚡ Pace**")
                st.metric("Impact", f"{factors['pace']:+.2f}")
                st.caption(f"Diff: {raw['pace_diff']:+.1f}")
            
            with factor_col5:
                st.markdown("**📊 Net Rating**")
                st.metric("Impact", f"{factors['net_rating']:+.2f}")
                st.caption(f"Diff: {raw['net_diff']:+.1f}")
            
            with factor_col6:
                st.markdown("**✈️ Travel**")
                st.metric("Impact", f"{factors['travel']:+.2f}")
                st.caption(f"{raw['travel_miles']:,} miles")
            
            st.caption(f"🏠 Home Court Baseline: +{factors['home_court']:.1f}")
            
            # Row 3: Injury Details
            st.markdown("---")
            st.markdown("### 🏥 Injury Report")
            inj_col1, inj_col2 = st.columns(2)
            
            with inj_col1:
                st.markdown(f"**{away} ({away_injury_count} injuries)**")
                if away_injury_list:
                    for inj in away_injury_list[:5]:
                        st.caption(f"• {inj}")
                    if len(away_injury_list) > 5:
                        st.caption(f"... and {len(away_injury_list) - 5} more")
                else:
                    st.caption("None reported")
            
            with inj_col2:
                st.markdown(f"**{home} ({home_injury_count} injuries)**")
                if home_injury_list:
                    for inj in home_injury_list[:5]:
                        st.caption(f"• {inj}")
                    if len(home_injury_list) > 5:
                        st.caption(f"... and {len(home_injury_list) - 5} more")
                else:
                    st.caption("None reported")
            
            # Trade link
            st.markdown("---")
            st.markdown(f"[📈 **Trade this game on Kalshi**](https://kalshi.com/markets/kxnbagame/professional-basketball-game/{game['ticker'].lower()})")

# ========== SUMMARY TABLE ==========
st.markdown("---")
st.subheader("📋 Edge Summary")

summary_data = []
for game in games:
    home = game['home_team']
    away = game['away_team']
    home_injury_count = len(injuries.get(home, []))
    away_injury_count = len(injuries.get(away, []))
    away_travel = calculate_travel_distance(away, home)
    auto_home_rest = get_team_rest_days(home, rest_days_data, default_home_rest)
    auto_away_rest = get_team_rest_days(away, rest_days_data, default_away_rest)
    
    analysis = calculate_edge(
        home, away, game['yes_price'],
        auto_home_rest, auto_away_rest,
        home_injury_count, away_injury_count,
        away_travel, weights
    )
    
    summary_data.append({
        'Matchup': f"{away} @ {home}",
        'Kalshi YES': f"{game['yes_price']:.0f}¢",
        'Model Prob': f"{analysis['home_win_prob']:.1f}%",
        'Edge': f"{analysis['edge']:+.1f}%",
        'EV': f"{analysis['expected_value']:+.2f}¢",
        'Signal': analysis['recommendation'],
        'Confidence': analysis['confidence']
    })

if summary_data:
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ========== FOOTER ==========
st.markdown("---")
st.caption("⚠️ **Disclaimer:** For educational and entertainment purposes only. Not financial advice. Past performance does not guarantee future results. Only trade what you can afford to lose.")
st.caption("Data: Kalshi API (prices), ESPN (injuries) | Refresh rate: 5 minutes")
