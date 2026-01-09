import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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

def calculate_edge(home_team, away_team, kalshi_home_price, home_injuries=0, away_injuries=0):
    """Calculate edge based on team stats vs Kalshi price"""
    
    home_stats = TEAM_STATS.get(home_team, {"net_rating": 0, "def_rank": 15, "pace": 99})
    away_stats = TEAM_STATS.get(away_team, {"net_rating": 0, "def_rank": 15, "pace": 99})
    
    # Net rating difference (most important factor)
    net_diff = home_stats['net_rating'] - away_stats['net_rating']
    
    # Home court advantage (~3 points historically)
    home_advantage = 3.0
    
    # Defense matchup
    def_advantage = (away_stats['def_rank'] - home_stats['def_rank']) * 0.1
    
    # Injury impact (rough estimate)
    injury_impact = (away_injuries - home_injuries) * 1.5
    
    # Calculate expected point spread
    expected_spread = net_diff + home_advantage + def_advantage + injury_impact
    
    # Convert spread to win probability (using standard conversion)
    # Each point of spread ≈ 2.5-3% win probability
    spread_to_prob = 0.025
    home_win_prob = 50 + (expected_spread * spread_to_prob * 100)
    home_win_prob = max(5, min(95, home_win_prob))  # Cap between 5-95%
    
    # Calculate edge vs Kalshi price
    edge = home_win_prob - kalshi_home_price
    
    return {
        'home_win_prob': round(home_win_prob, 1),
        'kalshi_price': kalshi_home_price,
        'edge': round(edge, 1),
        'expected_spread': round(expected_spread, 1),
        'recommendation': 'BUY YES' if edge > 5 else ('BUY NO' if edge < -5 else 'NO EDGE'),
        'confidence': 'HIGH' if abs(edge) > 10 else ('MEDIUM' if abs(edge) > 5 else 'LOW')
    }

# ========== MAIN APP ==========

st.title("🏀 NBA Kalshi Edge Finder")
st.markdown("**Powered by Kalshi API** - Real-time prices direct from Kalshi")

# Sidebar settings
st.sidebar.header("⚙️ Settings")
min_edge = st.sidebar.slider("Minimum Edge to Show", 0, 20, 5, help="Only show games with this much edge or more")
show_all = st.sidebar.checkbox("Show all games (including no-edge)", value=True)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Fetch data
with st.spinner("Fetching Kalshi NBA markets..."):
    games = fetch_kalshi_nba_games()
    injuries = fetch_nba_injuries()

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
        home_injuries = len(injuries.get(home, []))
        away_injuries = len(injuries.get(away, []))
        
        # Calculate edge
        analysis = calculate_edge(home, away, kalshi_price, home_injuries, away_injuries)
        
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
        
        with st.expander(f"{rec_color} {away} @ {home} | Edge: {analysis['edge']:+.1f}%", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📊 Kalshi Prices**")
                st.metric(f"{home} (YES)", f"{kalshi_price:.0f}¢")
                st.metric(f"{away} (NO)", f"{100-kalshi_price:.0f}¢")
                st.caption(f"Volume: {game['volume']:,} contracts")
            
            with col2:
                st.markdown("**🎯 Our Model**")
                st.metric(f"{home} Win Prob", f"{analysis['home_win_prob']:.1f}%")
                st.metric("Expected Spread", f"{home} {analysis['expected_spread']:+.1f}")
            
            with col3:
                st.markdown("**💰 Edge Analysis**")
                edge_val = analysis['edge']
                st.metric("Edge", f"{edge_val:+.1f}%", delta=f"{analysis['confidence']} confidence")
                
                if analysis['recommendation'] == 'BUY YES':
                    st.success(f"**{analysis['recommendation']}** on {home}")
                elif analysis['recommendation'] == 'BUY NO':
                    st.error(f"**{analysis['recommendation']}** (bet {away})")
                else:
                    st.info("No significant edge")
            
            # Injury report
            st.markdown("---")
            inj_col1, inj_col2 = st.columns(2)
            with inj_col1:
                st.markdown(f"**🏥 {away} Injuries ({away_injuries})**")
                away_inj = injuries.get(away, [])
                st.caption(", ".join(away_inj[:5]) if away_inj else "None reported")
            
            with inj_col2:
                st.markdown(f"**🏥 {home} Injuries ({home_injuries})**")
                home_inj = injuries.get(home, [])
                st.caption(", ".join(home_inj[:5]) if home_inj else "None reported")
            
            # Direct link to Kalshi market
            st.markdown(f"[📈 Trade on Kalshi](https://kalshi.com/markets/kxnbagame/professional-basketball-game/{game['ticker'].lower()})")

# Summary table
st.markdown("---")
st.subheader("📋 Edge Summary")

summary_data = []
for game in games:
    home = game['home_team']
    away = game['away_team']
    home_injuries = len(injuries.get(home, []))
    away_injuries = len(injuries.get(away, []))
    analysis = calculate_edge(home, away, game['yes_price'], home_injuries, away_injuries)
    
    summary_data.append({
        'Matchup': f"{away} @ {home}",
        'Kalshi YES': f"{game['yes_price']:.0f}¢",
        'Model Prob': f"{analysis['home_win_prob']:.1f}%",
        'Edge': f"{analysis['edge']:+.1f}%",
        'Signal': analysis['recommendation'],
        'Confidence': analysis['confidence']
    })

if summary_data:
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption("⚠️ **Disclaimer:** For educational and entertainment purposes only. Not financial advice. Past performance does not guarantee future results. Only trade what you can afford to lose.")
st.caption("Data: Kalshi API (prices), ESPN (injuries) | Refresh rate: 5 minutes")
