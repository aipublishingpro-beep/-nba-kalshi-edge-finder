import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ============================================================
# TEAM DATA - 3PT% AND PACE (UPDATE WEEKLY)
# ============================================================

# 3PT% rankings (lower = worse shooting, more likely to suppress totals)
# Data source: NBA.com/stats - update weekly
TEAM_3PT_PCT = {
    "Atlanta": 0.362, "Boston": 0.382, "Brooklyn": 0.348, "Charlotte": 0.341,
    "Chicago": 0.352, "Cleveland": 0.358, "Dallas": 0.371, "Denver": 0.365,
    "Detroit": 0.339, "Golden State": 0.378, "Houston": 0.344, "Indiana": 0.374,
    "LA Clippers": 0.356, "LA Lakers": 0.349, "Memphis": 0.332, "Miami": 0.355,
    "Milwaukee": 0.363, "Minnesota": 0.357, "New Orleans": 0.346, "New York": 0.361,
    "Oklahoma City": 0.369, "Orlando": 0.343, "Philadelphia": 0.359, "Phoenix": 0.367,
    "Portland": 0.347, "Sacramento": 0.364, "San Antonio": 0.338, "Toronto": 0.351,
    "Utah": 0.345, "Washington": 0.336
}

# Pace rankings (possessions per 48 min - lower = slower, suppresses totals)
TEAM_PACE = {
    "Atlanta": 100.2, "Boston": 98.1, "Brooklyn": 99.4, "Charlotte": 101.3,
    "Chicago": 97.8, "Cleveland": 96.5, "Dallas": 98.7, "Denver": 97.2,
    "Detroit": 99.1, "Golden State": 100.8, "Houston": 101.5, "Indiana": 102.4,
    "LA Clippers": 97.4, "LA Lakers": 99.8, "Memphis": 99.6, "Miami": 96.8,
    "Milwaukee": 98.3, "Minnesota": 97.1, "New Orleans": 100.1, "New York": 96.2,
    "Oklahoma City": 99.3, "Orlando": 97.6, "Philadelphia": 98.5, "Phoenix": 99.9,
    "Portland": 100.6, "Sacramento": 101.1, "San Antonio": 98.9, "Toronto": 100.4,
    "Utah": 98.2, "Washington": 101.8
}

# Team abbreviation mappings
ABBREV_TO_FULL = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte",
    "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas", "DEN": "Denver",
    "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami",
    "MIL": "Milwaukee", "MIN": "Minnesota", "NOP": "New Orleans", "NYK": "New York",
    "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia", "PHX": "Phoenix",
    "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto",
    "UTA": "Utah", "WAS": "Washington"
}

TICKER_ABBREVS = {
    "ATL": "Atlanta", "BOS": "Boston", "BRO": "Brooklyn", "BKN": "Brooklyn",
    "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas",
    "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "GS": "Golden State",
    "HOU": "Houston", "IND": "Indiana", "LAC": "LA Clippers", "LAL": "LA Lakers",
    "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NO": "New Orleans", "NYK": "New York", "NY": "New York",
    "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia", "PHX": "Phoenix",
    "PHO": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio",
    "SA": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
}

# ============================================================
# STEP 1: GENERATE PRIMARY WATCHLIST
# ============================================================

def get_bottom_3pt_teams(n=8):
    """Bottom N teams by 3PT% - these can't inflate totals through variance"""
    sorted_teams = sorted(TEAM_3PT_PCT.items(), key=lambda x: x[1])
    return [team for team, pct in sorted_teams[:n]]

def get_bottom_pace_teams(n=10):
    """Bottom N teams by pace - these limit possession volume"""
    sorted_teams = sorted(TEAM_PACE.items(), key=lambda x: x[1])
    return [team for team, pace in sorted_teams[:n]]

def get_primary_watchlist():
    """Intersection of bottom 3PT% AND bottom pace teams"""
    bottom_3pt = set(get_bottom_3pt_teams(8))
    bottom_pace = set(get_bottom_pace_teams(10))
    return bottom_3pt.intersection(bottom_pace)

# ============================================================
# REST DAY CALCULATIONS
# ============================================================

# Last game dates (UPDATE DAILY or pull from API)
# Format: "Team": "YYYY-MM-DD"
LAST_GAME_DATES = {
    "Atlanta": "2026-01-10", "Boston": "2026-01-10", "Brooklyn": "2026-01-09",
    "Charlotte": "2026-01-10", "Chicago": "2026-01-09", "Cleveland": "2026-01-10",
    "Dallas": "2026-01-10", "Denver": "2026-01-09", "Detroit": "2026-01-10",
    "Golden State": "2026-01-10", "Houston": "2026-01-09", "Indiana": "2026-01-10",
    "LA Clippers": "2026-01-09", "LA Lakers": "2026-01-10", "Memphis": "2026-01-10",
    "Miami": "2026-01-09", "Milwaukee": "2026-01-10", "Minnesota": "2026-01-09",
    "New Orleans": "2026-01-10", "New York": "2026-01-10", "Oklahoma City": "2026-01-09",
    "Orlando": "2026-01-10", "Philadelphia": "2026-01-09", "Phoenix": "2026-01-10",
    "Portland": "2026-01-09", "Sacramento": "2026-01-10", "San Antonio": "2026-01-09",
    "Toronto": "2026-01-10", "Utah": "2026-01-09", "Washington": "2026-01-10"
}

def get_rest_days(team):
    """Calculate days since last game"""
    if team not in LAST_GAME_DATES:
        return None
    last_game = datetime.strptime(LAST_GAME_DATES[team], "%Y-%m-%d")
    today = datetime.now()
    return (today - last_game).days

def get_rest_status(days):
    """Categorize rest status"""
    if days is None:
        return "Unknown", "⚪"
    elif days <= 1:
        return "Short Rest", "🔴"
    elif days == 2:
        return "Normal Rest", "🟡"
    else:
        return "Extended Rest", "🟢"

# ============================================================
# KALSHI API FUNCTIONS
# ============================================================

def parse_teams_from_ticker(ticker_code):
    """Parse team codes from ticker like '26JAN11NOPWAS' -> ('New Orleans', 'Washington')"""
    if len(ticker_code) < 12:
        return None, None
    teams_part = ticker_code[7:]
    if len(teams_part) == 6:
        away_code = teams_part[:3]
        home_code = teams_part[3:]
    else:
        away_code = teams_part[:3]
        home_code = teams_part[3:6] if len(teams_part) >= 6 else teams_part[3:]
    away = TICKER_ABBREVS.get(away_code.upper(), away_code)
    home = TICKER_ABBREVS.get(home_code.upper(), home_code)
    return away, home

def fetch_extreme_totals(min_threshold=245):
    """Fetch only extreme totals (≥245) from Kalshi"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": "KXNBATOTAL", "status": "open", "limit": 200}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return [], f"API Error: {response.status_code}"
        
        data = response.json()
        markets = data.get("markets", [])
        extreme_markets = []
        
        for m in markets:
            floor_strike = m.get("floor_strike", 0)
            if floor_strike and floor_strike >= min_threshold:
                event_ticker = m.get("event_ticker", "")
                parts = event_ticker.split("-")
                if len(parts) >= 2:
                    game_code = parts[1]
                    away, home = parse_teams_from_ticker(game_code)
                    
                    yes_ask = m.get("yes_ask", 0) or 0
                    no_ask = m.get("no_ask", 0) or 0
                    if no_ask == 0 and yes_ask > 0:
                        no_ask = 1 - yes_ask
                    
                    extreme_markets.append({
                        "ticker": m.get("ticker", ""),
                        "event_ticker": event_ticker,
                        "threshold": floor_strike,
                        "away_team": away,
                        "home_team": home,
                        "yes_ask": yes_ask,
                        "no_ask": no_ask,
                        "volume": m.get("volume", 0),
                        "title": m.get("title", "")
                    })
        
        extreme_markets.sort(key=lambda x: x["threshold"], reverse=True)
        return extreme_markets, None
        
    except Exception as e:
        return [], str(e)

# ============================================================
# FILTER LOGIC
# ============================================================

def check_all_filters(market, q1_total, watchlist, spread_estimate=5):
    """Run all 6 filters and return pass/fail for each"""
    away = market["away_team"]
    home = market["home_team"]
    threshold = market["threshold"]
    no_ask = market["no_ask"]
    
    filters = {}
    
    # Filter 1: Threshold ≥ 245
    filters["threshold"] = {
        "pass": threshold >= 245,
        "value": threshold,
        "rule": "≥ 245"
    }
    
    # Filter 2: NO ask ≤ 0.68
    filters["price"] = {
        "pass": no_ask <= 0.68,
        "value": f"{no_ask:.2f}",
        "rule": "≤ 0.68"
    }
    
    # Filter 3: Primary Watchlist team involved
    has_watchlist = away in watchlist or home in watchlist
    watchlist_team = away if away in watchlist else (home if home in watchlist else "None")
    filters["watchlist"] = {
        "pass": has_watchlist,
        "value": watchlist_team,
        "rule": "At least 1 team"
    }
    
    # Filter 4: Short rest (0-1 days)
    away_rest = get_rest_days(away)
    home_rest = get_rest_days(home)
    has_short_rest = (away_rest is not None and away_rest <= 1) or (home_rest is not None and home_rest <= 1)
    rest_info = f"{away}: {away_rest}d, {home}: {home_rest}d"
    filters["rest"] = {
        "pass": has_short_rest,
        "value": rest_info,
        "rule": "≤ 1 day for at least 1 team"
    }
    
    # Filter 5: Q1 Total < 50
    filters["q1"] = {
        "pass": q1_total < 50 if q1_total is not None else False,
        "value": q1_total if q1_total is not None else "Not entered",
        "rule": "< 50 (prefer < 48)"
    }
    
    # Filter 6: OT Risk (spread estimate)
    ot_ok = spread_estimate >= 5
    filters["ot_risk"] = {
        "pass": ot_ok,
        "value": f"Spread ~{spread_estimate}",
        "rule": "Spread ≥ 5 preferred"
    }
    
    # All pass?
    all_pass = all(f["pass"] for f in filters.values())
    
    return filters, all_pass

# ============================================================
# STREAMLIT APP
# ============================================================

st.set_page_config(
    page_title="Extreme Totals NO Finder",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 KALSHI EXTREME TOTALS - NO FINDER")
st.caption("Tail-risk exploitation system. You are not betting averages. You are betting tail collapse.")

# Sidebar
with st.sidebar:
    st.header("⚙️ System Settings")
    
    # Threshold filter
    min_threshold = st.selectbox(
        "Minimum Threshold",
        options=[245, 248, 250, 252, 255],
        index=0,
        help="Only show markets at or above this total"
    )
    
    # Max NO price
    max_no_price = st.slider(
        "Max NO Ask Price",
        min_value=0.50,
        max_value=0.75,
        value=0.68,
        step=0.01,
        help="Skip if NO is priced above this (safety already priced in)"
    )
    
    st.divider()
    
    # Primary Watchlist
    st.subheader("📋 Primary Watchlist")
    st.caption("Teams in BOTH bottom 8 3PT% AND bottom 10 pace")
    watchlist = get_primary_watchlist()
    
    if watchlist:
        for team in sorted(watchlist):
            st.write(f"• **{team}**")
            st.caption(f"  3PT: {TEAM_3PT_PCT[team]:.1%} | Pace: {TEAM_PACE[team]:.1f}")
    else:
        st.warning("No teams qualify this week")
    
    st.divider()
    
    # Component Lists
    with st.expander("🔍 Bottom 8 3PT% Teams"):
        for team in get_bottom_3pt_teams(8):
            st.write(f"• {team}: {TEAM_3PT_PCT[team]:.1%}")
    
    with st.expander("🐢 Bottom 10 Pace Teams"):
        for team in get_bottom_pace_teams(10):
            st.write(f"• {team}: {TEAM_PACE[team]:.1f}")
    
    st.divider()
    st.caption("Last updated: Update TEAM_3PT_PCT and TEAM_PACE weekly")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Extreme Totals Markets")
    
    # Fetch markets
    if st.button("🔄 Refresh Markets", type="primary"):
        st.cache_data.clear()
    
    @st.cache_data(ttl=300)
    def load_markets(threshold):
        return fetch_extreme_totals(threshold)
    
    markets, error = load_markets(min_threshold)
    
    if error:
        st.error(f"API Error: {error}")
    elif not markets:
        st.info(f"No extreme totals (≥{min_threshold}) found. Markets may not be posted yet.")
    else:
        # Filter by max NO price
        eligible_markets = [m for m in markets if m["no_ask"] <= max_no_price]
        
        st.success(f"Found {len(markets)} extreme totals, {len(eligible_markets)} within price range")
        
        for market in eligible_markets:
            away = market["away_team"]
            home = market["home_team"]
            threshold = market["threshold"]
            no_ask = market["no_ask"]
            
            # Check if watchlist team involved
            has_watchlist = away in watchlist or home in watchlist
            watchlist_badge = "✅ WATCHLIST" if has_watchlist else "⚠️ No watchlist team"
            
            # Rest info
            away_rest = get_rest_days(away)
            home_rest = get_rest_days(home)
            away_status, away_icon = get_rest_status(away_rest)
            home_status, home_icon = get_rest_status(home_rest)
            
            # Display card
            with st.container():
                st.subheader(f"🏀 {away} @ {home}")
                
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.metric("Threshold", f"{threshold}")
                with mcol2:
                    price_color = "🟢" if no_ask <= 0.65 else "🟡" if no_ask <= 0.68 else "🔴"
                    st.metric("NO Price", f"{price_color} {no_ask:.2f}")
                with mcol3:
                    st.write(f"**{watchlist_badge}**")
                
                # Rest status
                st.write(f"**Rest:** {away_icon} {away} ({away_rest}d) vs {home_icon} {home} ({home_rest}d)")
                
                # Kalshi link
                kalshi_url = f"https://kalshi.com/markets/{market['ticker']}"
                st.markdown(f"[View on Kalshi]({kalshi_url})")
                
                st.divider()

with col2:
    st.header("✅ ENTRY CHECKLIST")
    st.caption("ALL must pass before entry")
    
    # Select market for checklist
    if markets:
        market_options = [f"{m['away_team']} @ {m['home_team']} ({m['threshold']})" for m in markets]
        selected_idx = st.selectbox("Select Game", range(len(market_options)), format_func=lambda x: market_options[x])
        selected_market = markets[selected_idx]
        
        st.divider()
        
        # Q1 Input (LIVE CONFIRMATION)
        st.subheader("🔴 LIVE Q1 CHECK")
        q1_total = st.number_input(
            "Enter Q1 Total (after Q1 ends)",
            min_value=0,
            max_value=100,
            value=0,
            help="Wait for Q1 to complete. Enter combined score."
        )
        
        # Spread estimate
        spread_est = st.number_input(
            "Estimated Spread",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            help="Check pregame spread. ≥5 preferred for OT safety"
        )
        
        st.divider()
        
        # Run all filters
        q1_val = q1_total if q1_total > 0 else None
        filters, all_pass = check_all_filters(selected_market, q1_val, watchlist, spread_est)
        
        # Display each filter
        for name, result in filters.items():
            icon = "✅" if result["pass"] else "❌"
            st.write(f"{icon} **{name.upper()}**: {result['value']} (rule: {result['rule']})")
        
        st.divider()
        
        # FINAL VERDICT
        if all_pass:
            st.success("🚀 ALL FILTERS PASS - ENTRY ELIGIBLE")
            st.balloons()
            
            # Calculate suggested position
            st.write(f"**Suggested Action:** BET NO on {selected_market['threshold']}")
            st.write(f"**NO Price:** {selected_market['no_ask']:.2f}")
            
            kalshi_url = f"https://kalshi.com/markets/{selected_market['ticker']}"
            st.markdown(f"### [→ PLACE BET ON KALSHI]({kalshi_url})")
        else:
            failed = [k for k, v in filters.items() if not v["pass"]]
            st.error(f"❌ NO TRADE - Failed: {', '.join(failed)}")
            st.caption("Do not enter. Wait for better setup.")
    else:
        st.info("Load markets to use checklist")

# Bottom section - System Rules
st.divider()
with st.expander("📖 SYSTEM RULES (READ THIS)"):
    st.markdown("""
    ### THE EDGE
    You are exploiting tail-risk overpricing. The market overestimates the probability of extreme scoring.
    
    ### THE BRAKES
    1. **Low 3PT% teams** - Can't inflate totals through variance
    2. **Slow pace teams** - Limit possession volume  
    3. **Short rest** - Fatigue suppresses pace and shooting
    4. **Price discipline** - NO ≤ 0.68 or safety is already priced
    5. **OT avoidance** - Overtime kills extreme NOs
    6. **Q1 confirmation** - Slow Q1 = unsustainable pressure on later quarters
    
    ### THE DISCIPLINE
    - You will trade far less
    - You will skip many "obvious" games
    - You will feel bored most nights
    - **That boredom is the edge**
    
    ### NEVER
    - Chase the highest NO blindly
    - Enter pregame (ALWAYS wait for Q1)
    - Double down or martingale
    - Bet games without a watchlist team
    """)

# Footer
st.divider()
st.caption("Extreme Totals NO Finder v1.0 | System designed for patience, not action")
