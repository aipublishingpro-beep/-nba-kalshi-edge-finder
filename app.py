import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== INITIALIZE SESSION STATE ==========
if "positions" not in st.session_state:
    st.session_state.positions = []

# ========== SIDEBAR LEGEND ==========
with st.sidebar:
    st.header("📖 LEGEND")
    
    st.subheader("⚡ Edge Scanner")
    st.markdown("""
    🟢 **8-10** → STRONG — Size up  
    🟢 **6-7** → GOOD — Standard  
    🟡 **4-5** → LEAN — Small size  
    🔴 **0-3** → SKIP — No edge
    """)
    
    st.markdown("""
    **NO scoring:**  
    • Tired teams = +pts  
    • Slow pace = +pts  
    • Rested = -pts  
    
    **YES scoring:**  
    • Rested teams = +pts  
    • Fast/Shootout = +pts  
    • Blowout risk = +pts
    """)
    
    st.divider()
    
    st.subheader("Size Tiers (Cushion)")
    st.markdown("""
    🟢 **BIG** → +20 pts or more  
    🟡 **MEDIUM** → +10 to +19  
    🟠 **SMALL** → +5 to +9  
    🔴 **SKIP** → Under +5
    """)
    
    st.divider()
    
    st.subheader("Fatigue Scanner")
    st.markdown("""
    **Score 3+** → FATIGUED 🔴  
    *(Back-to-back + Road = prime NO target)*
    
    **Score 2** → TIRED 🟡  
    *(Back-to-back only or Road only)*
    
    **Score 0-1** → Fresh  
    *(No fatigue edge)*
    """)
    
    st.markdown("""
    **Factors:**  
    • Back-to-back (played yesterday) = +2  
    • Road game = +1  
    • Home court = +2 (for home team ML)
    """)
    
    st.divider()
    
    st.subheader("Matchup Types")
    st.markdown("""
    🏠 **HOME COURT**  
    *Home team +2 pts — 55-60% historical win rate*
    
    🟢 **BOTH TIRED**  
    *Both teams fatigued = pace drags, sloppy game, STRONG Under*
    
    🔥 **BLOWOUT RISK**  
    *Fatigued @ Fresh Home = Skip NO, consider ML on fresh home team*
    
    🏔️ **ALTITUDE**  
    *Denver home = visitors fatigue at 5,280 ft, lean Under*
    
    ⚡ **RESTED**  
    *3+ days rest = team comes out hot, Over risk*
    
    🏆 **DIVISION RIVALS**  
    *Same division = physical game, lean Under*
    
    ⚪ **NEUTRAL**  
    *Fresh vs Fresh = no fatigue edge*
    """)
    
    st.divider()
    
    st.subheader("Pace Scanner")
    st.markdown("""
    🟢 **SLOW** → Under 4.5/min  
    *(Good NO spot)*
    
    🟡 **AVG** → 4.5 - 4.8/min  
    *(Neutral)*
    
    🟠 **FAST** → 4.8 - 5.2/min  
    *(Caution for NO)*
    
    🔴 **SHOOTOUT** → Over 5.2/min  
    *(Avoid NO, consider YES)*
    """)
    
    st.divider()
    
    st.subheader("Pace Edge (NO bets)")
    st.markdown("""
    **+1.0+** → Comfortable 🟢  
    **+0.5 to +1.0** → Okay 🟡  
    **0 to +0.5** → Tight 🟠  
    **Negative** → Underwater 🔴
    """)
    
    st.divider()
    st.caption("v10.31")

TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

NBA_DIVISIONS = {
    "Atlantic": ["Boston", "Brooklyn", "New York", "Philadelphia", "Toronto"],
    "Central": ["Chicago", "Cleveland", "Detroit", "Indiana", "Milwaukee"],
    "Southeast": ["Atlanta", "Charlotte", "Miami", "Orlando", "Washington"],
    "Northwest": ["Denver", "Minnesota", "Oklahoma City", "Portland", "Utah"],
    "Pacific": ["Golden State", "LA Clippers", "LA Lakers", "Phoenix", "Sacramento"],
    "Southwest": ["Dallas", "Houston", "Memphis", "New Orleans", "San Antonio"]
}

def are_division_rivals(team1, team2):
    for division, teams in NBA_DIVISIONS.items():
        if team1 in teams and team2 in teams:
            return True
    return False

def fetch_espn_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score = team_name, score
                else:
                    away_team, away_score = team_name, score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except:
        return {}

def fetch_yesterday_teams():
    yesterday = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

def fetch_recent_teams(days=3):
    """Fetch teams that played in the last X days"""
    recent_teams = set()
    for i in range(1, days + 1):
        date = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            for event in data.get("events", []):
                comp = event.get("competitions", [{}])[0]
                for c in comp.get("competitors", []):
                    name = c.get("team", {}).get("displayName", "")
                    team_name = TEAM_ABBREVS.get(name, name)
                    recent_teams.add(team_name)
        except:
            pass
    return recent_teams

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 0
    try:
        clock_str = str(clock)
        if ':' in clock_str:
            parts = clock_str.split(':')
            mins = int(parts[0])
            secs = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins = 0
            secs = float(clock_str) if clock_str else 0
        time_left_in_period = mins + secs/60
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left_in_period)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left_in_period)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def get_minutes_remaining(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 0
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 48
    try:
        clock_str = str(clock)
        if ':' in clock_str:
            parts = clock_str.split(':')
            mins = int(parts[0])
            secs = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins = 0
            secs = float(clock_str) if clock_str else 0
        time_left_in_period = mins + secs/60
        if period <= 4:
            return time_left_in_period + (4 - period) * 12
        else:
            return time_left_in_period
    except:
        return 0

def get_status_no(threshold, total, projected, is_final):
    if is_final:
        return ("✅ WON!", "#00ff00") if total < threshold else ("❌ LOST", "#ff0000")
    if projected is None:
        return ("⏳ WAITING", "#888888")
    cushion = threshold - projected
    if cushion > 15:
        return ("🟢 VERY SAFE", "#00ff00")
    elif cushion > 8:
        return ("🟢 LOOKING GOOD", "#00ff00")
    elif cushion > 3:
        return ("🟡 ON TRACK", "#ffff00")
    elif cushion > -3:
        return ("🟠 TIGHT", "#ff8800")
    elif cushion > -10:
        return ("🔴 DANGER", "#ff0000")
    else:
        return ("🔴 LIKELY LOSS", "#ff0000")

def get_status_yes(threshold, total, projected, is_final):
    if is_final:
        return ("✅ WON!", "#00ff00") if total > threshold else ("❌ LOST", "#ff0000")
    if projected is None:
        return ("⏳ WAITING", "#888888")
    cushion = projected - threshold
    if cushion > 15:
        return ("🟢 VERY SAFE", "#00ff00")
    elif cushion > 8:
        return ("🟢 LOOKING GOOD", "#00ff00")
    elif cushion > 3:
        return ("🟡 ON TRACK", "#ffff00")
    elif cushion > -3:
        return ("🟠 TIGHT", "#ff8800")
    elif cushion > -10:
        return ("🔴 DANGER", "#ff0000")
    else:
        return ("🔴 LIKELY LOSS", "#ff0000")

def get_size_tier(cushion):
    if cushion >= 20:
        return "🟢 BIG — Size up", "#00ff00"
    elif cushion >= 10:
        return "🟡 MEDIUM — Standard size", "#ffff00"
    elif cushion >= 5:
        return "🟠 SMALL — Caution", "#ff8800"
    else:
        return "🔴 SKIP — No edge", "#ff0000"

# Fetch data
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
recent_teams = fetch_recent_teams(3)
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')}")

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")
st.caption("Step 1: Find the fat edges — pick lowest green threshold")

cushion_col1, cushion_col2 = st.columns([1, 1])
with cushion_col1:
    cushion_min_minutes = st.selectbox("Min time played", [6, 9, 12, 18, 24], index=1, format_func=lambda x: f"{x} min", key="cushion_min")
with cushion_col2:
    cushion_side = st.selectbox("Bet side", ["NO", "YES"], key="cushion_side")

thresholds = [225.5, 230.5, 235.5, 240.5, 245.5]

cushion_data = []
for game_key, g in games.items():
    mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins_played >= cushion_min_minutes:
        pace = g['total'] / mins_played if mins_played > 0 else 0
        projected = round(pace * 48)
        cushion_data.append({
            "game": game_key,
            "projected": projected,
            "mins": mins_played,
            "is_final": g['status_type'] == "STATUS_FINAL"
        })

if cushion_data:
    header_cols = st.columns([2, 1] + [1]*len(thresholds))
    header_cols[0].markdown("**Game**")
    header_cols[1].markdown("**Proj**")
    for i, t in enumerate(thresholds):
        header_cols[i+2].markdown(f"**{t}**")
    
    for cd in cushion_data:
        row_cols = st.columns([2, 1] + [1]*len(thresholds))
        row_cols[0].write(cd['game'].replace("@", " @ "))
        row_cols[1].write(f"{cd['projected']}")
        
        for i, t in enumerate(thresholds):
            if cushion_side == "NO":
                cushion = t - cd['projected']
            else:
                cushion = cd['projected'] - t
            
            if cushion >= 20:
                row_cols[i+2].markdown(f"<span style='color:#00ff00'>**+{cushion:.0f}**</span>", unsafe_allow_html=True)
            elif cushion >= 10:
                row_cols[i+2].markdown(f"<span style='color:#ffff00'>**+{cushion:.0f}**</span>", unsafe_allow_html=True)
            elif cushion >= 5:
                row_cols[i+2].markdown(f"<span style='color:#ff8800'>**+{cushion:.0f}**</span>", unsafe_allow_html=True)
            elif cushion >= 0:
                row_cols[i+2].markdown(f"<span style='color:#ff4444'>+{cushion:.0f}</span>", unsafe_allow_html=True)
            else:
                row_cols[i+2].markdown(f"<span style='color:#ff0000'>{cushion:.0f}</span>", unsafe_allow_html=True)
else:
    st.info(f"No games with {cushion_min_minutes}+ minutes played yet")

st.divider()

# ========== EDGE SCANNER ==========
st.subheader("⚡ EDGE SCANNER")
st.caption(f"Step 2: Confirm 6+ score at your chosen threshold (using {cushion_side} from above)")

edge_col1, edge_col2 = st.columns([1, 1])
with edge_col1:
    edge_min_minutes = st.selectbox("Min time played", [6, 9, 12, 18, 24], index=2, format_func=lambda x: f"{x} min", key="edge_min")
with edge_col2:
    edge_threshold = st.number_input("Threshold", 210.0, 260.0, 235.5, 0.5, key="edge_threshold")

edge_side = cushion_side

edge_data = []
for game_key, g in games.items():
    mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
    
    away = g['away_team']
    home = g['home_team']
    total = g['total']
    is_final = g['status_type'] == "STATUS_FINAL"
    
    if mins_played >= edge_min_minutes:
        pace = total / mins_played if mins_played > 0 else 0
        projected = round(pace * 48)
        
        fatigue_pts = 0
        fatigue_tags = []
        
        away_b2b = away in yesterday_teams
        home_b2b = home in yesterday_teams
        
        away_rested = away not in recent_teams
        home_rested = home not in recent_teams
        
        is_division = are_division_rivals(away, home)
        
        away_fatigue_score = (2 if away_b2b else 0) + 1
        home_fatigue_score = 2 if home_b2b else 0
        is_blowout_risk = away_fatigue_score >= 3 and home_fatigue_score == 0
        
        if edge_side == "NO":
            if away_b2b:
                fatigue_pts += 2
                fatigue_tags.append("Away B2B +2")
            if away_b2b and home_b2b:
                fatigue_pts += 1
                fatigue_tags.append("Both tired +1")
            if home == "Denver":
                fatigue_pts += 1
                fatigue_tags.append("Altitude +1")
            if is_blowout_risk:
                fatigue_pts -= 2
                fatigue_tags.append("Blowout -2")
            if away_rested:
                fatigue_pts -= 1
                fatigue_tags.append(f"{away} rested -1")
            if home_rested:
                fatigue_pts -= 1
                fatigue_tags.append(f"{home} rested -1")
            if is_division:
                fatigue_pts += 1
                fatigue_tags.append("Division +1")
        else:
            if away_rested:
                fatigue_pts += 2
                fatigue_tags.append(f"{away} rested +2")
            if home_rested:
                fatigue_pts += 2
                fatigue_tags.append(f"{home} rested +2")
            if is_blowout_risk:
                fatigue_pts += 3
                fatigue_tags.append("Blowout +3")
            if home == "Denver":
                fatigue_pts -= 1
                fatigue_tags.append("Altitude -1")
        
        pace_pts = 0
        if edge_side == "NO":
            if pace < 4.5:
                pace_pts = 2
                pace_tag = "Slow +2"
            elif pace < 4.8:
                pace_pts = 1
                pace_tag = "Avg +1"
            elif pace < 5.2:
                pace_pts = 0
                pace_tag = "Fast +0"
            else:
                pace_pts = -1
                pace_tag = "Shootout -1"
        else:
            if pace >= 5.0:
                pace_pts = 3
                pace_tag = "Shootout +3"
            elif pace >= 4.8:
                pace_pts = 2
                pace_tag = "Fast +2"
            elif pace >= 4.5:
                pace_pts = 1
                pace_tag = "Avg +1"
            else:
                pace_pts = 0
                pace_tag = "Slow +0"
        
        if edge_side == "NO":
            cushion = edge_threshold - projected
        else:
            cushion = projected - edge_threshold
            
        if cushion >= 20:
            cushion_pts = 3
        elif cushion >= 10:
            cushion_pts = 2
        elif cushion >= 5:
            cushion_pts = 1
        else:
            cushion_pts = 0
        
        edge_score = fatigue_pts + pace_pts + cushion_pts
        
        edge_data.append({
            "game": game_key,
            "projected": projected,
            "pace": round(pace, 2),
            "cushion": cushion,
            "fatigue_pts": fatigue_pts,
            "pace_pts": pace_pts,
            "cushion_pts": cushion_pts,
            "edge_score": edge_score,
            "fatigue_tags": fatigue_tags,
            "pace_tag": pace_tag,
            "is_final": is_final
        })

edge_data.sort(key=lambda x: x['edge_score'], reverse=True)

if edge_data:
    for ed in edge_data:
        side_label = edge_side
        if ed['edge_score'] >= 8:
            rating = f"🟢 STRONG {side_label}"
            color = "#00ff00"
        elif ed['edge_score'] >= 6:
            rating = f"🟢 GOOD {side_label}"
            color = "#00ff00"
        elif ed['edge_score'] >= 4:
            rating = f"🟡 LEAN {side_label}"
            color = "#ffff00"
        else:
            rating = "🔴 SKIP"
            color = "#ff0000"
        
        status = "FINAL" if ed['is_final'] else "LIVE"
        
        st.markdown(f"### {ed['game'].replace('@', ' @ ')} — <span style='color:{color}'>**{ed['edge_score']} pts {rating}**</span>", unsafe_allow_html=True)
        
        score_cols = st.columns(4)
        score_cols[0].metric("Fatigue", f"+{ed['fatigue_pts']}" if ed['fatigue_pts'] >= 0 else f"{ed['fatigue_pts']}")
        score_cols[1].metric("Pace", f"+{ed['pace_pts']}" if ed['pace_pts'] >= 0 else f"{ed['pace_pts']}", delta=ed['pace_tag'])
        score_cols[2].metric("Cushion", f"+{ed['cushion_pts']}", delta=f"{ed['cushion']:+.0f} pts")
        score_cols[3].metric("Projected", f"{ed['projected']}", delta=status)
        
        st.markdown("---")
else:
    st.info(f"No games with {edge_min_minutes}+ minutes played yet")

st.divider()

# ========== PRE-BET ANALYSIS ==========
pba_header, pba_refresh = st.columns([4, 1])
with pba_header:
    st.subheader("📊 PRE-BET ANALYSIS")
    st.caption("Check your edge BEFORE entering a position")
with pba_refresh:
    st.write("")
    if st.button("🔄 REFRESH", key="refresh_analysis", type="primary"):
        st.rerun()

pa1, pa2, pa3 = st.columns([2, 1, 1])
with pa1:
    if game_list:
        analyze_game = st.selectbox("Game to analyze", game_list, format_func=lambda x: x.replace("@", " @ "), key="analyze_game")
    else:
        analyze_game = None
with pa2:
    analyze_side = st.selectbox("Side", ["NO", "YES"], key="analyze_side")
with pa3:
    analyze_threshold = st.number_input("Threshold", 180.0, 280.0, 235.5, 0.5, key="analyze_threshold")

if analyze_game:
    # Parse selected game and find matching data
    parts = analyze_game.split("@")
    if len(parts) == 2:
        selected_away = parts[0]
        selected_home = parts[1]
        
        # Find the game by team names (don't trust dictionary key)
        g = None
        for key, game_data in games.items():
            if game_data['away_team'] == selected_away and game_data['home_team'] == selected_home:
                g = game_data
                break
        
        if not g:
            st.error(f"⚠️ Game data not found for {selected_away} @ {selected_home}. Click REFRESH.")
            st.stop()
        
        away = selected_away
        home = selected_home
        total = g['total']
        mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
        
        # Show the matchup we're analyzing
        st.markdown(f"## 🏀 {away} @ {home}")
        
        # Check for key alerts FIRST
        away_b2b = away in yesterday_teams
        home_b2b = home in yesterday_teams
        away_rested = away not in recent_teams
        home_rested = home not in recent_teams
        is_division = are_division_rivals(away, home)
        away_fatigue_score = (2 if away_b2b else 0) + 1
        home_fatigue_score = 2 if home_b2b else 0
        is_blowout_risk = away_fatigue_score >= 3 and home_fatigue_score == 0
        
        # HOME COURT ADVANTAGE (always show)
        st.success(f"🏠 **HOME COURT** — {home} has home advantage (+2 pts)")
        
        # Show critical alerts at top
        if is_blowout_risk:
            if analyze_side == "NO":
                st.error(f"🔥 **BLOWOUT RISK** — Fatigued {away} @ Fresh {home}. Skip NO, consider ML on {home}")
            else:
                st.success(f"🔥 **BLOWOUT RISK** — Fatigued {away} @ Fresh {home}. Good YES/Over spot!")
        
        if away_b2b and home_b2b:
            st.success("🟢 **BOTH TIRED** — Strong Under spot, good NO!")
        
        if home == "Denver":
            st.info(f"🏔️ **ALTITUDE** — {away} traveling to Denver (5,280 ft)")
        
        if is_division:
            st.info(f"🏆 **DIVISION RIVALS** — Physical game expected")
    
    # === SITUATIONAL FACTORS (always show) ===
    st.markdown("---")
    st.markdown("### 📋 Situational Factors")
    
    away_b2b = away in yesterday_teams
    home_b2b = home in yesterday_teams
    away_rested = away not in recent_teams
    home_rested = home not in recent_teams
    is_division = are_division_rivals(away, home)
    away_fatigue_score = (2 if away_b2b else 0) + 1
    home_fatigue_score = 2 if home_b2b else 0
    is_blowout_risk = away_fatigue_score >= 3 and home_fatigue_score == 0
    
    situational_pts = 0
    factors_found = False
    
    # Always show team status
    col_away, col_home = st.columns(2)
    with col_away:
        st.markdown(f"**{away}** (Away)")
        if away_b2b:
            st.error("🔴 Back-to-back")
        elif away_rested:
            st.success("🟢 Rested (3+ days)")
        else:
            st.info("⚪ Normal rest")
    
    with col_home:
        st.markdown(f"**{home}** (Home)")
        if home_b2b:
            st.error("🔴 Back-to-back")
        elif home_rested:
            st.success("🟢 Rested (3+ days)")
        else:
            st.info("⚪ Normal rest")
    
    st.markdown("**Edge Factors:**")
    
    if analyze_side == "NO":
        if away_b2b:
            st.success(f"✅ {away} on B2B (+2 pts)")
            situational_pts += 2
            factors_found = True
        if home_b2b:
            st.success(f"✅ {home} on B2B (+2 pts)")
            situational_pts += 2
            factors_found = True
        if away_b2b and home_b2b:
            st.success("✅ BOTH TIRED — Strong Under spot (+1 bonus)")
            situational_pts += 1
            factors_found = True
        if home == "Denver":
            st.info("🏔️ ALTITUDE — Denver home (+1 pt)")
            situational_pts += 1
            factors_found = True
        if is_division:
            st.info("🏆 DIVISION RIVALS — Physical game (+1 pt)")
            situational_pts += 1
            factors_found = True
        if is_blowout_risk:
            st.warning("⚠️ BLOWOUT RISK — Fatigued road team @ fresh home (-2 pts)")
            situational_pts -= 2
            factors_found = True
        if away_rested:
            st.warning(f"⚠️ {away} RESTED 3+ days — Over risk (-1 pt)")
            situational_pts -= 1
            factors_found = True
        if home_rested:
            st.warning(f"⚠️ {home} RESTED 3+ days — Over risk (-1 pt)")
            situational_pts -= 1
            factors_found = True
    else:
        if away_rested:
            st.success(f"✅ {away} RESTED 3+ days (+2 pts)")
            situational_pts += 2
            factors_found = True
        if home_rested:
            st.success(f"✅ {home} RESTED 3+ days (+2 pts)")
            situational_pts += 2
            factors_found = True
        if is_blowout_risk:
            st.success("✅ BLOWOUT RISK — High scoring potential (+3 pts)")
            situational_pts += 3
            factors_found = True
        if home == "Denver":
            st.warning("⚠️ ALTITUDE — Denver home, pace may drag (-1 pt)")
            situational_pts -= 1
            factors_found = True
        if away_b2b or home_b2b:
            st.warning("⚠️ Tired team(s) — May slow pace (-1 pt)")
            situational_pts -= 1
            factors_found = True
    
    if not factors_found:
        st.caption("No special situational factors — standard matchup")
    
    if situational_pts >= 3:
        sit_color = "#00ff00"
        sit_label = "STRONG"
    elif situational_pts >= 1:
        sit_color = "#ffff00"
        sit_label = "LEAN"
    elif situational_pts >= 0:
        sit_color = "#ff8800"
        sit_label = "NEUTRAL"
    else:
        sit_color = "#ff0000"
        sit_label = "AVOID"
    
    st.markdown(f"**Situational Score:** <span style='color:{sit_color}'>**{situational_pts} pts — {sit_label} {analyze_side}**</span>", unsafe_allow_html=True)
    
    # === LIVE PROJECTION (only if game started) ===
    if mins_played >= 6:
        st.markdown("---")
        st.markdown("### 📊 Live Projection")
        
        projected = round((total / mins_played) * 48)
        
        if analyze_side == "NO":
            cushion = analyze_threshold - projected
        else:
            cushion = projected - analyze_threshold
        
        size_tier, tier_color = get_size_tier(cushion)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.metric("ESPN Projected Total", f"{projected} pts")
        
        with col_right:
            st.metric("Your Cushion", f"{cushion:+.0f} pts", 
                     delta="favorable" if cushion > 0 else "unfavorable",
                     delta_color="normal" if cushion > 0 else "inverse")
        
        st.markdown(f"### <span style='color:{tier_color}'>{size_tier}</span>", unsafe_allow_html=True)
        
        if cushion < 5:
            st.error("⛔ DO NOT ENTER — Cushion too thin. Wait for better spot or skip.")
        elif cushion < 10:
            st.warning("⚠️ Proceed with caution — Small edge only")
        elif cushion >= 20:
            st.success("✅ Strong edge — Consider sizing up")
    else:
        st.markdown("---")
        st.info(f"⏳ Live projection available after 6 min ({mins_played:.1f} played)")
    
    st.caption(f"Current: {g['away_team']} {g['away_score']} - {g['home_team']} {g['home_score']} = {total} pts | Q{g['period']} {g['clock']}")
    
    st.markdown("---")
    st.markdown("**Quick Add to Track:**")
    qa1, qa2, qa3, qa4 = st.columns([2, 1, 1, 1])
    with qa1:
        track_game = st.selectbox("Game", game_list, index=game_list.index(analyze_game) if analyze_game in game_list else 0, format_func=lambda x: x.replace("@", " @ "), key="track_game")
    with qa2:
        quick_price = st.number_input("Price ¢", 1, 99, 85, key="quick_price")
    with qa3:
        quick_contracts = st.number_input("Contracts", 1, 1000, 100, key="quick_contracts")
    with qa4:
        st.write("")
        st.write("")
        if st.button("➕ ADD", key="quick_add", type="primary"):
            st.session_state.positions.append({
                "game": track_game, "side": analyze_side, "threshold": analyze_threshold,
                "price": quick_price, "contracts": quick_contracts
            })
            st.rerun()
else:
    if not analyze_game:
        st.info("Select a game above to analyze")

st.divider()

# ========== FATIGUE SCANNER ==========
st.subheader("😴 FATIGUE SCANNER")
st.caption("Find teams on back-to-backs and road fatigue — check BEFORE games start")

if games:
    game_fatigue = []
    
    for game_key, g in games.items():
        away = g['away_team']
        home = g['home_team']
        
        away_b2b = away in yesterday_teams
        away_score = (2 if away_b2b else 0) + 1
        
        home_b2b = home in yesterday_teams
        home_score = 2 if home_b2b else 0
        
        max_score = max(away_score, home_score)
        if max_score >= 2:
            game_fatigue.append({
                "game_key": game_key,
                "away": away,
                "home": home,
                "away_b2b": away_b2b,
                "home_b2b": home_b2b,
                "away_score": away_score,
                "home_score": home_score,
                "max_score": max_score
            })
    
    game_fatigue.sort(key=lambda x: x['max_score'], reverse=True)
    
    if game_fatigue:
        for gf in game_fatigue:
            st.markdown(f"### 🏀 {gf['away']} @ {gf['home']}")
            
            if gf['away_score'] >= 2 and gf['home_score'] >= 2:
                st.success("🟢 **BOTH TIRED** — Strong Under spot")
            elif gf['away_score'] >= 3 and gf['home_score'] == 0:
                st.success(f"🔥 **BLOWOUT RISK** — Skip NO, consider ML on {gf['home']}")
            
            if gf['home'] == "Denver":
                st.info("🏔️ **ALTITUDE** — Denver home, visitors fatigue at 5,280 ft")
            
            away_rested = gf['away'] not in recent_teams
            home_rested = gf['home'] not in recent_teams
            
            if away_rested:
                st.warning(f"⚡ **RESTED** — {gf['away']} has 3+ days rest (Over risk)")
            if home_rested:
                st.warning(f"⚡ **RESTED** — {gf['home']} has 3+ days rest (Over risk)")
            
            if are_division_rivals(gf['away'], gf['home']):
                st.info("🏆 **DIVISION RIVALS** — Physical game, lean Under")
            
            away_tags = []
            if gf['away_b2b']:
                away_tags.append("PLAYED YESTERDAY")
            away_tags.append("ROAD")
            away_tag_str = " + ".join(away_tags)
            
            if gf['away_score'] >= 3:
                st.error(f"🔴 **{gf['away']}** (Score {gf['away_score']}) — {away_tag_str}")
            elif gf['away_score'] >= 2:
                st.warning(f"🟡 **{gf['away']}** (Score {gf['away_score']}) — {away_tag_str}")
            else:
                st.caption(f"⚪ {gf['away']} (Score {gf['away_score']}) — {away_tag_str}")
            
            if gf['home_b2b']:
                home_tag_str = "PLAYED YESTERDAY"
                if gf['home_score'] >= 2:
                    st.warning(f"🟡 **{gf['home']}** (Score {gf['home_score']}) — {home_tag_str}")
            else:
                st.caption(f"⚪ {gf['home']} (Score {gf['home_score']}) — HOME (fresh)")
            
            st.markdown("---")
    else:
        st.info("No fatigued teams today")
else:
    st.info("No games today to analyze")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")
st.caption("Find slow/fast games — check DURING games")

pace_col1, pace_col2 = st.columns([1, 1])
with pace_col1:
    min_minutes = st.selectbox("Minimum time played", [6, 9, 12, 18, 24], index=0, format_func=lambda x: f"{x} min")
with pace_col2:
    sort_order = st.selectbox("Sort by", ["Slowest first (NO hunting)", "Fastest first (YES hunting)"])

pace_data = []
for game_key, g in games.items():
    mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins_played >= min_minutes:
        pace = round(g['total'] / mins_played, 2) if mins_played > 0 else 0
        projected = round(pace * 48)
        pace_data.append({
            "game": game_key,
            "away": g['away_team'],
            "home": g['home_team'],
            "total": g['total'],
            "mins": mins_played,
            "pace": pace,
            "projected": projected,
            "period": g['period'],
            "clock": g['clock'],
            "is_final": g['status_type'] == "STATUS_FINAL"
        })

if sort_order == "Slowest first (NO hunting)":
    pace_data.sort(key=lambda x: x['pace'])
else:
    pace_data.sort(key=lambda x: x['pace'], reverse=True)

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5:
            pace_label = "🟢 SLOW"
            pace_color = "#00ff00"
        elif p['pace'] < 4.8:
            pace_label = "🟡 AVG"
            pace_color = "#ffff00"
        elif p['pace'] < 5.2:
            pace_label = "🟠 FAST"
            pace_color = "#ff8800"
        else:
            pace_label = "🔴 SHOOTOUT"
            pace_color = "#ff0000"
        
        status = "FINAL" if p['is_final'] else f"Q{p['period']} {p['clock']}"
        
        st.markdown(f"**{p['away']} @ {p['home']}** — {p['total']} pts in {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{pace_color}'>**{pace_label}**</span> — Proj: **{p['projected']}** — {status}", unsafe_allow_html=True)
else:
    st.info(f"No games with {min_minutes}+ minutes played yet")

st.divider()

# ========== SCOREBOARD ==========
st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            st.caption(f"Q{g['period']} {g['clock']} | {g['total']} pts")

st.divider()

# ========== HOW TO USE ==========
with st.expander("📚 HOW TO USE THIS TOOL"):
    st.markdown("""
    ## Two Betting Strategies
    
    This tool supports two distinct edges. Use the right approach for each bet type.
    
    ---
    
    ### 🎯 MONEYLINE BETS (Pre-Game)
    
    **When:** BEFORE tipoff
    
    **Use:** Pre-Bet Analysis → Situational Factors
    
    **What to look for:**
    - 🏠 **HOME COURT** — Home team always has +2 edge (55-60% historical win rate)
    - 🔥 **BLOWOUT RISK** — Fatigued road team @ fresh home = bet the home ML
    - 🟢 **B2B teams** — Back-to-back = tired legs, fade them
    - 🏔️ **ALTITUDE** — Teams visiting Denver struggle
    - 🏆 **DIVISION RIVALS** — Physical games, home team edge
    
    **The Logic:** Fatigue is baked in before tipoff. You don't need game data — the edge exists the moment the schedule is set.
    
    **Action:** Find BLOWOUT RISK or heavy fatigue mismatches → buy ML pre-game at best price.
    
    ---
    
    ### 📊 TOTAL BETS - NO/YES (Live)
    
    **When:** 6+ MINUTES into game
    
    **Use:** Cushion Scanner → Edge Scanner → Pre-Bet Analysis
    
    **Step-by-step:**
    1. **Cushion Scanner** — Find games with +10 or more cushion at your threshold
    2. **Edge Scanner** — Confirm 6+ edge score (fatigue + pace + cushion combined)
    3. **Pre-Bet Analysis** — Final check before entry
    
    **What to look for:**
    - 🟢 **+20 cushion** = BIG size (confident)
    - 🟡 **+10-19 cushion** = MEDIUM size (standard)
    - 🟠 **+5-9 cushion** = SMALL size (cautious)
    - 🔴 **Under +5** = SKIP (no edge)
    
    **Pace confirmation:**
    - For NO bets: Want SLOW pace (under 4.5/min)
    - For YES bets: Want FAST pace (over 4.8/min)
    
    **The Logic:** 6 minutes of game data reveals the actual pace. Combined with situational factors, you get a complete picture.
    
    **Action:** Wait for data → confirm cushion + pace + edge score → enter position.
    
    ---
    
    ### ⚠️ KEY RULES
    
    1. **Never bet NO on BLOWOUT RISK games** — Blowouts often push totals UP (garbage time)
    2. **Trust the cushion** — Under +5 = no edge, walk away
    3. **Edge Score 6+ required** — Below 6 = skip or reduce size
    4. **Rested teams push OVER** — 3+ days rest = fresh legs = more scoring
    5. **Both tired = UNDER** — Two fatigued teams = sloppy, slow game
    
    ---
    
    ### 📈 POSITION SIZING
    
    | Cushion | Edge Score | Size |
    |---------|------------|------|
    | +20 or more | 8+ | BIG — Max confidence |
    | +10 to +19 | 6-7 | MEDIUM — Standard |
    | +5 to +9 | 4-5 | SMALL — Reduced |
    | Under +5 | 0-3 | SKIP — No edge |
    
    ---
    
    ### 🔄 WORKFLOW SUMMARY
    
    **Pre-game:**
    1. Check Fatigue Scanner for B2B / BLOWOUT RISK
    2. Use Pre-Bet Analysis for situational score
    3. Buy ML on fresh home teams vs fatigued road teams
    
    **6+ minutes in:**
    1. Check Cushion Scanner for fat edges
    2. Confirm with Edge Scanner (need 6+ score)
    3. Final check in Pre-Bet Analysis
    4. Enter position on Kalshi
    """)

# ========== POSITION TRACKER ==========
st.subheader("📈 POSITION TRACKER")
st.caption("Track your active bets with live updates")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        side = pos['side']
        threshold = pos['threshold']
        price = pos['price']
        contracts = pos['contracts']
        
        # Find game data
        g = None
        parts = game_key.split("@")
        if len(parts) == 2:
            for key, game_data in games.items():
                if game_data['away_team'] == parts[0] and game_data['home_team'] == parts[1]:
                    g = game_data
                    break
        
        if g:
            total = g['total']
            mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            
            if mins_played > 0:
                pace = total / mins_played
                projected = round(pace * 48)
            else:
                projected = None
            
            # Calculate status
            if side == "NO":
                if is_final:
                    won = total < threshold
                    status_text = "✅ WON!" if won else "❌ LOST"
                    status_color = "#00ff00" if won else "#ff0000"
                elif projected:
                    cushion = threshold - projected
                    if cushion > 10:
                        status_text = f"🟢 SAFE (+{cushion:.0f})"
                        status_color = "#00ff00"
                    elif cushion > 3:
                        status_text = f"🟡 OK (+{cushion:.0f})"
                        status_color = "#ffff00"
                    elif cushion > -3:
                        status_text = f"🟠 TIGHT ({cushion:+.0f})"
                        status_color = "#ff8800"
                    else:
                        status_text = f"🔴 DANGER ({cushion:+.0f})"
                        status_color = "#ff0000"
                else:
                    status_text = "⏳ WAITING"
                    status_color = "#888888"
            else:  # YES
                if is_final:
                    won = total > threshold
                    status_text = "✅ WON!" if won else "❌ LOST"
                    status_color = "#00ff00" if won else "#ff0000"
                elif projected:
                    cushion = projected - threshold
                    if cushion > 10:
                        status_text = f"🟢 SAFE (+{cushion:.0f})"
                        status_color = "#00ff00"
                    elif cushion > 3:
                        status_text = f"🟡 OK (+{cushion:.0f})"
                        status_color = "#ffff00"
                    elif cushion > -3:
                        status_text = f"🟠 TIGHT ({cushion:+.0f})"
                        status_color = "#ff8800"
                    else:
                        status_text = f"🔴 DANGER ({cushion:+.0f})"
                        status_color = "#ff0000"
                else:
                    status_text = "⏳ WAITING"
                    status_color = "#888888"
            
            # Calculate P/L
            cost = price * contracts
            potential_win = (100 - price) * contracts
            
            # Display position
            pos_cols = st.columns([3, 1, 1, 1, 1, 1])
            pos_cols[0].markdown(f"**{game_key.replace('@', ' @ ')}**")
            pos_cols[1].markdown(f"**{side} {threshold}**")
            pos_cols[2].markdown(f"Proj: **{projected if projected else '—'}**")
            pos_cols[3].markdown(f"<span style='color:{status_color}'>{status_text}</span>", unsafe_allow_html=True)
            pos_cols[4].markdown(f"${cost/100:.2f} → ${potential_win/100:.2f}")
            if pos_cols[5].button("🗑️", key=f"remove_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
            
            # Show live score
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            st.caption(f"   Live: {g['away_team']} {g['away_score']} - {g['home_team']} {g['home_score']} = {total} pts | {game_status}")
            st.markdown("---")
        else:
            st.warning(f"⚠️ Game not found: {game_key}")
            if st.button(f"Remove", key=f"remove_missing_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
    
    # Summary
    st.markdown("### 💰 Summary")
    total_cost = sum(p['price'] * p['contracts'] for p in st.session_state.positions)
    total_potential = sum((100 - p['price']) * p['contracts'] for p in st.session_state.positions)
    st.markdown(f"**Total Risk:** ${total_cost/100:.2f} | **Total Potential Win:** ${total_potential/100:.2f}")
    
    if st.button("🗑️ CLEAR ALL POSITIONS", type="secondary"):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked yet. Use Pre-Bet Analysis → Quick Add to Track to add positions.")

st.divider()

st.caption("v10.30 | Edge Finder + Fatigue + Pace + Cushion + Position Tracker")
