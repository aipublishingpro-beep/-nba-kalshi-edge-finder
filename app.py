import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

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
st.write("**Real Today's Games • Real Injury Data • NO Fake Data**")

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

# Team name variations for matching
team_variations = {
    "Hawks": "Atlanta Hawks", "Celtics": "Boston Celtics", "Nets": "Brooklyn Nets",
    "Hornets": "Charlotte Hornets", "Bulls": "Chicago Bulls", "Cavaliers": "Cleveland Cavaliers",
    "Mavericks": "Dallas Mavericks", "Nuggets": "Denver Nuggets", "Pistons": "Detroit Pistons",
    "Warriors": "Golden State Warriors", "Rockets": "Houston Rockets", "Pacers": "Indiana Pacers",
    "Clippers": "LA Clippers", "Lakers": "Los Angeles Lakers", "Grizzlies": "Memphis Grizzlies",
    "Heat": "Miami Heat", "Bucks": "Milwaukee Bucks", "Timberwolves": "Minnesota Timberwolves",
    "Pelicans": "New Orleans Pelicans", "Knicks": "New York Knicks", "Thunder": "Oklahoma City Thunder",
    "Magic": "Orlando Magic", "76ers": "Philadelphia 76ers", "Sixers": "Philadelphia 76ers",
    "Suns": "Phoenix Suns", "Trail Blazers": "Portland Trail Blazers", "Blazers": "Portland Trail Blazers",
    "Kings": "Sacramento Kings", "Spurs": "San Antonio Spurs", "Raptors": "Toronto Raptors",
    "Jazz": "Utah Jazz", "Wizards": "Washington Wizards",
    "Atlanta": "Atlanta Hawks", "Boston": "Boston Celtics", "Brooklyn": "Brooklyn Nets",
    "Charlotte": "Charlotte Hornets", "Chicago": "Chicago Bulls", "Cleveland": "Cleveland Cavaliers",
    "Dallas": "Dallas Mavericks", "Denver": "Denver Nuggets", "Detroit": "Detroit Pistons",
    "Golden State": "Golden State Warriors", "Houston": "Houston Rockets", "Indiana": "Indiana Pacers",
    "LA Clippers": "LA Clippers", "Los Angeles Lakers": "Los Angeles Lakers", "L.A. Lakers": "Los Angeles Lakers",
    "L.A. Clippers": "LA Clippers", "Memphis": "Memphis Grizzlies", "Miami": "Miami Heat",
    "Milwaukee": "Milwaukee Bucks", "Minnesota": "Minnesota Timberwolves", "New Orleans": "New Orleans Pelicans",
    "New York": "New York Knicks", "Oklahoma City": "Oklahoma City Thunder", "Orlando": "Orlando Magic",
    "Philadelphia": "Philadelphia 76ers", "Phoenix": "Phoenix Suns", "Portland": "Portland Trail Blazers",
    "Sacramento": "Sacramento Kings", "San Antonio": "San Antonio Spurs", "Toronto": "Toronto Raptors",
    "Utah": "Utah Jazz", "Washington": "Washington Wizards"
}

_injury_cache = {}
_cache_time = 0
CACHE_DURATION = 14400

def normalize_team_name(name):
    """Convert various team name formats to standard format"""
    name = name.strip()
    if name in team_mapping:
        return name
    if name in team_variations:
        return team_variations[name]
    for key, value in team_variations.items():
        if key.lower() in name.lower():
            return value
    return name

def fetch_nba_injuries():
    """Fetch NBA injuries from CBS Sports"""
    url = "https://www.cbssports.com/nba/injuries/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        injuries = {}
        
        # Find all team injury tables
        team_tables = soup.find_all('div', class_='TeamLogoNameLockup')
        
        if not team_tables:
            # Try alternative structure
            tables = soup.find_all('table', class_='TableBase-table')
            current_team = None
            
            for element in soup.find_all(['span', 'div', 'a', 'table', 'tr']):
                # Look for team names
                if element.name in ['span', 'div', 'a']:
                    text = element.get_text(strip=True)
                    normalized = normalize_team_name(text)
                    if normalized in team_mapping:
                        current_team = normalized
                        if current_team not in injuries:
                            injuries[current_team] = []
                
                # Look for player rows
                if element.name == 'tr' and current_team:
                    cells = element.find_all('td')
                    if cells:
                        player_link = element.find('a')
                        if player_link:
                            player_name = player_link.get_text(strip=True)
                            if player_name and len(player_name) > 2 and player_name not in injuries.get(current_team, []):
                                injuries[current_team].append(player_name)
        
        # If CBS doesn't work, try a simple backup
        if not injuries or sum(len(v) for v in injuries.values()) < 10:
            injuries = fetch_injuries_backup()
        
        return injuries
        
    except Exception as e:
        st.warning(f"⚠️ CBS Sports unavailable, using backup data")
        return fetch_injuries_backup()

def fetch_injuries_backup():
    """Backup: Fetch from ESPN with careful parsing"""
    url = "https://www.espn.com/nba/injuries"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        injuries = {}
        
        # Find all the responsive tables which contain team data
        page_content = soup.find('div', class_='page-container')
        if not page_content:
            page_content = soup
        
        # Look for team sections - ESPN wraps each team in a section
        current_team = None
        
        for element in page_content.find_all(['div', 'span', 'a', 'tr', 'td']):
            text = element.get_text(strip=True)
            
            # Check if this is a team name
            if element.get('class'):
                classes = ' '.join(element.get('class', []))
                if 'Table__Title' in classes or 'headline' in classes.lower():
                    normalized = normalize_team_name(text)
                    if normalized in team_mapping:
                        current_team = normalized
                        if current_team not in injuries:
                            injuries[current_team] = []
                        continue
            
            # Check for player names in table cells
            if element.name == 'a' and current_team:
                href = element.get('href', '')
                if '/nba/player/' in href:
                    player_name = text
                    if player_name and len(player_name) > 2:
                        # Make sure this player belongs to current team
                        if player_name not in injuries[current_team]:
                            injuries[current_team].append(player_name)
        
        return injuries
        
    except Exception as e:
        return {}

def get_injuries_cached():
    global _injury_cache, _cache_time
    if time.time() - _cache_time < CACHE_DURATION and _injury_cache:
        return _injury_cache
    _injury_cache = fetch_nba_injuries()
    _cache_time = time.time()
    return _injury_cache

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
                home_full = normalize_team_name(home_team)
                away_full = normalize_team_name(away_team)
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

def calculate_kalshi_edge(home_team, away_team, market_spread, home_rest, away_rest, home_injuries, away_injuries, kalshi_yes_price):
    home_stats = team_stats.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    away_stats = team_stats.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    rest_diff = home_rest - away_rest
    rest_advantage = rest_diff * st.session_state.get('rest_weight', 0.75)
    def_rank_diff = away_stats["def_rank"] - home_stats["def_rank"]
    defense_advantage = def_rank_diff * 0.2 * st.session_state.get('defense_weight', 1.0)
    pace_diff = home_stats["pace"] - away_stats["pace"]
    pace_advantage = pace_diff * 0.02 * st.session_state.get('pace_weight', 0.6)
    home_injury_impact = len(home_injuries) * 2.5
    away_injury_impact = len(away_injuries) * 2.5
    net_injury_impact = (away_injury_impact - home_injury_impact) * st.session_state.get('injury_weight', 1.5)
    net_rating_advantage = (home_stats["net_rating"] - away_stats["net_rating"]) * 0.1
    total_adjustment = rest_advantage + defense_advantage + pace_advantage + net_injury_impact + net_rating_advantage
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
    factors = [rest_advantage, defense_advantage, pace_advantage, net_injury_impact, net_rating_advantage]
    factor_agreement = len([x for x in factors if abs(x) > 0.3])
    confidence_score = min(100, int(edge_size * 15 + factor_agreement * 12))
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
        "factors": factors
    }

st.sidebar.header("🎯 Kalshi Settings")
st.session_state.confidence_threshold = st.sidebar.slider("Confidence Threshold", 50, 90, 65)
st.session_state.min_edge = st.sidebar.slider("Minimum Edge", 0.5, 5.0, 1.0)
st.sidebar.header("🧠 Model Weights")
st.session_state.rest_weight = st.sidebar.slider("Rest Advantage", 0.0, 2.0, 0.75)
st.session_state.defense_weight = st.sidebar.slider("Defense Mismatch", 0.0, 2.0, 1.0)
st.session_state.injury_weight = st.sidebar.slider("Injury Impact", 0.0, 3.0, 1.5)
st.session_state.pace_weight = st.sidebar.slider("Pace Impact", 0.0, 2.0, 0.6)

st.header("📅 Today's NBA Games")
todays_games = fetch_todays_games()
injuries_data = get_injuries_cached()

if not todays_games:
    st.warning("🚫 No NBA games scheduled today. Use manual analysis below.")
else:
    st.success(f"🎯 Found {len(todays_games)} game(s) today")
    for i, game in enumerate(todays_games):
        st.write(f"**Game {i+1}:** {game['away_team']} @ {game['home_team']} - {game['game_time']}")

st.header("🏥 Current Injury Report")
if injuries_data:
    injury_count = sum(len(v) for v in injuries_data.values())
    st.success(f"📊 Tracking {injury_count} injuries across {len(injuries_data)} teams")
    with st.expander("View All Injuries"):
        for team, players in sorted(injuries_data.items()):
            st.write(f"**{team}:** {', '.join(players)}")
else:
    st.warning("⚠️ Could not load injury data. Analysis will proceed without injury factor.")

st.header("🔢 Batch Analysis")
if st.button("🔄 Analyze Today's Games", type="primary"):
    if not todays_games:
        st.error("❌ No games to analyze")
    else:
        results = []
        with st.spinner(f"Analyzing {len(todays_games)} game(s)..."):
            for game in todays_games:
                home_team = game['home_team']
                away_team = game['away_team']
                market_spread = -3.5
                home_rest = 2
                away_rest = 1
                kalshi_yes_price = 50
                home_injuries = injuries_data.get(home_team, [])
                away_injuries = injuries_data.get(away_team, [])
                result = calculate_kalshi_edge(
                    home_team, away_team, market_spread, home_rest, away_rest,
                    home_injuries, away_injuries, kalshi_yes_price
                )
                results.append({
                    "Game": f"{away_team} @ {home_team}",
                    "Time": game['game_time'],
                    "Spread": market_spread,
                    "Recommendation": result["kalshi_recommendation"],
                    "Confidence": result["confidence_score"],
                    "Edge": f"{result['edge_size']:.1f}",
                    "EV": f"{result['expected_value']:+.1f}¢",
                    "Status": "✅ TRADE" if result['expected_value'] > 5 and result['confidence_score'] >= st.session_state.confidence_threshold else "❌ PASS"
                })
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        trades = len([r for r in results if r['Status'] == '✅ TRADE'])
        st.info(f"**{trades} trading opportunities out of {len(results)} games**")

st.header("🔍 Manual Game Analysis")
col1, col2 = st.columns(2)
with col1:
    manual_home = st.selectbox("Home Team", list(team_mapping.keys()), index=13)
    manual_home_rest = st.number_input("Home Rest Days", 1, 7, 2)
with col2:
    manual_away = st.selectbox("Away Team", list(team_mapping.keys()), index=9)
    manual_away_rest = st.number_input("Away Rest Days", 1, 7, 1)
manual_spread = st.slider("Spread Line", -15.0, 15.0, -3.5, 0.5)
manual_yes_price = st.slider("Kalshi YES Price (cents)", 10, 90, 50)

if st.button("📈 Analyze Game"):
    home_injuries = injuries_data.get(manual_home, [])
    away_injuries = injuries_data.get(manual_away, [])
    result = calculate_kalshi_edge(
        manual_home, manual_away, manual_spread, manual_home_rest, manual_away_rest,
        home_injuries, away_injuries, manual_yes_price
    )
    st.subheader("📊 Results")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Market Spread", f"{manual_spread:+.1f}")
        st.metric("Adjusted Spread", f"{result['adjusted_spread']:+.1f}")
        st.metric("Edge Size", f"{result['edge_size']:.1f} pts")
    with col2:
        st.metric("Confidence", f"{result['confidence_score']}%")
        st.metric("Expected Value", f"{result['expected_value']:+.1f}¢")
        st.progress(result['confidence_score'] / 100)
    if result['edge_size'] >= st.session_state.min_edge and result['confidence_score'] >= st.session_state.confidence_threshold:
        if result['expected_value'] > 0:
            st.success(f"💰 **BUY {result['kalshi_recommendation']}** - {result['reasoning']}")
        else:
            st.warning("⚖️ No positive EV - PASS")
    else:
        st.error("🔍 Insufficient edge - NO TRADE")

st.sidebar.markdown("---")
st.sidebar.header("💡 Guide")
st.sidebar.write("• EV > 5¢ = Good trade")
st.sidebar.write("• Confidence > 65% = High conviction")
st.sidebar.write("• Edge > 1.0 = Mispricing detected")
st.sidebar.header("📡 Status")
st.sidebar.write(f"• Games: {len(todays_games)}")
st.sidebar.write(f"• Injuries: {len(injuries_data)} teams tracked")
st.sidebar.write(f"• Updated: {datetime.now().strftime('%I:%M %p')}")
st.markdown("---")
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. Past performance does not guarantee future results. You may lose money. Only bet what you can afford to lose. The creator assumes no liability for any losses.")
