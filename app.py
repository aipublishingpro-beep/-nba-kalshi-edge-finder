import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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
st.write("**Real Today's Games • Manual Injury Input • Clean Signal**")

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

INJURY_LEVELS = {
    0: "No key injuries",
    1: "Rotation player out",
    2: "Star questionable / limited",
    3: "Star confirmed OUT"
}

def injury_points(level):
    return {0: 0.0, 1: 1.0, 2: 2.5, 3: 4.0}.get(level, 0.0)

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

def calculate_kalshi_edge(home_team, away_team, market_spread, home_rest, away_rest, home_injury_level, away_injury_level, kalshi_yes_price):
    home_stats = team_stats.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    away_stats = team_stats.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 95})
    
    rest_advantage = (home_rest - away_rest) * st.session_state.get('rest_weight', 0.75)
    defense_advantage = (away_stats["def_rank"] - home_stats["def_rank"]) * 0.2 * st.session_state.get('defense_weight', 1.0)
    pace_advantage = (home_stats["pace"] - away_stats["pace"]) * 0.015 * st.session_state.get('pace_weight', 0.6)
    
    home_injury_impact = injury_points(home_injury_level)
    away_injury_impact = injury_points(away_injury_level)
    net_injury_impact = (away_injury_impact - home_injury_impact) * st.session_state.get('injury_weight', 1.25)
    
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

# Sidebar
st.sidebar.header("🎯 Kalshi Settings")
st.session_state.confidence_threshold = st.sidebar.slider("Confidence Threshold", 50, 90, 65)
st.session_state.min_edge = st.sidebar.slider("Minimum Edge", 0.5, 5.0, 1.0)
st.sidebar.header("🧠 Model Weights")
st.session_state.rest_weight = st.sidebar.slider("Rest Advantage", 0.0, 2.0, 0.75)
st.session_state.defense_weight = st.sidebar.slider("Defense Mismatch", 0.0, 2.0, 1.0)
st.session_state.injury_weight = st.sidebar.slider("Injury Impact", 0.0, 3.0, 1.25)
st.session_state.pace_weight = st.sidebar.slider("Pace Impact", 0.0, 2.0, 0.6)

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
st.write("**Select teams and set injury status manually for accurate analysis**")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🏠 Home Team")
    manual_home = st.selectbox("Home Team", list(team_mapping.keys()), index=13)
    manual_home_rest = st.number_input("Home Rest Days", 1, 7, 2)
    home_injury_level = st.selectbox(
        "Home Injury Status",
        options=list(INJURY_LEVELS.keys()),
        format_func=lambda x: INJURY_LEVELS[x],
        key="home_injury"
    )

with col2:
    st.subheader("✈️ Away Team")
    manual_away = st.selectbox("Away Team", list(team_mapping.keys()), index=9)
    manual_away_rest = st.number_input("Away Rest Days", 1, 7, 1)
    away_injury_level = st.selectbox(
        "Away Injury Status",
        options=list(INJURY_LEVELS.keys()),
        format_func=lambda x: INJURY_LEVELS[x],
        key="away_injury"
    )

st.subheader("📊 Market Data")
col3, col4 = st.columns(2)
with col3:
    manual_spread = st.slider("Spread Line (- = home favored)", -15.0, 15.0, -3.5, 0.5)
with col4:
    manual_yes_price = st.slider("Kalshi YES Price (cents)", 10, 90, 50)

if st.button("📈 Analyze Game", type="primary"):
    result = calculate_kalshi_edge(
        manual_home, manual_away, manual_spread, manual_home_rest, manual_away_rest,
        home_injury_level, away_injury_level, manual_yes_price
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
    
    with st.expander("View Factor Breakdown"):
        factors = result['factors']
        st.write(f"• Rest Advantage: {factors[0]:+.2f}")
        st.write(f"• Defense Advantage: {factors[1]:+.2f}")
        st.write(f"• Pace Advantage: {factors[2]:+.2f}")
        st.write(f"• Injury Impact: {factors[3]:+.2f}")
        st.write(f"• Net Rating Advantage: {factors[4]:+.2f}")

# Sidebar info
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

st.sidebar.header("📡 Status")
st.sidebar.write(f"• Games today: {len(todays_games)}")
st.sidebar.write(f"• Updated: {datetime.now().strftime('%I:%M %p')}")

st.markdown("---")
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. Past performance does not guarantee future results. You may lose money. Only bet what you can afford to lose. The creator assumes no liability for any losses.")
