import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

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

# Initialize - MUST be at very top before any widgets
if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'initialized' not in st.session_state:
    st.session_state.initialized = True

# Fetch games
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA POSITION TRACKER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')}")

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

# Calculate pre-bet analysis
if analyze_game and analyze_game in games:
    g = games[analyze_game]
    total = g['total']
    mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
    
    if mins_played >= 6:
        projected = round((total / mins_played) * 48)
        
        if analyze_side == "NO":
            cushion = analyze_threshold - projected
        else:
            cushion = projected - analyze_threshold
        
        size_tier, tier_color = get_size_tier(cushion)
        
        # Display analysis box
        st.markdown("---")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.metric("ESPN Projected Total", f"{projected} pts")
        
        with col_right:
            st.metric("Your Cushion", f"{cushion:+.0f} pts", 
                     delta="favorable" if cushion > 0 else "unfavorable",
                     delta_color="normal" if cushion > 0 else "inverse")
        
        # Size recommendation
        st.markdown(f"### <span style='color:{tier_color}'>{size_tier}</span>", unsafe_allow_html=True)
        
        if cushion < 5:
            st.error("⛔ DO NOT ENTER — Cushion too thin. Wait for better spot or skip.")
        elif cushion < 10:
            st.warning("⚠️ Proceed with caution — Small edge only")
        elif cushion >= 20:
            st.success("✅ Strong edge — Consider sizing up")
        
        # Quick stats
        st.caption(f"Current: {g['away_team']} {g['away_score']} - {g['home_team']} {g['home_score']} = {total} pts | Q{g['period']} {g['clock']}")
    else:
        st.info(f"⏳ Game just started ({mins_played:.1f} min played). Wait for Q1 data before analyzing.")
        st.caption(f"Current: {g['away_team']} {g['away_score']} - {g['home_team']} {g['home_score']} = {total} pts | Q{g['period']} {g['clock']}")
else:
    st.info("Select a game above to analyze")

st.divider()

# ========== ADD POSITION ==========
st.subheader("➕ ADD POSITION")
with st.form("add_position_form", clear_on_submit=True):
    c1, c2, c3, c4, c5, c6 = st.columns([2,1,1,1,1,1])
    with c1:
        if game_list:
            new_game = st.selectbox("Game", game_list, format_func=lambda x: x.replace("@", " @ "), key="new_game")
        else:
            new_game = st.text_input("Game (e.g. Brooklyn@Memphis)")
    with c2:
        new_side = st.selectbox("Side", ["NO", "YES"], key="new_side")
    with c3:
        new_threshold = st.number_input("Threshold", 180.0, 280.0, 237.5, 0.5, key="new_threshold")
    with c4:
        new_price = st.number_input("Price ¢", 1, 99, 85, key="new_price")
    with c5:
        new_contracts = st.number_input("Contracts", 1, 1000, 100, key="new_contracts")
    with c6:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("➕ ADD", type="primary")
    
    if submitted:
        st.session_state.positions.append({
            "game": new_game, "side": new_side, "threshold": new_threshold,
            "price": new_price, "contracts": new_contracts
        })

st.divider()

# ========== POSITIONS ==========
st.subheader(f"📋 YOUR POSITIONS ({len(st.session_state.positions)})")
if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        g = games.get(pos['game'])
        side = pos.get('side', 'NO')
        
        if g:
            total = g['total']
            mins_played = get_minutes_played(g['period'], g['clock'], g['status_type'])
            mins_remaining = get_minutes_remaining(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            spread = abs(g['away_score'] - g['home_score'])
            actual_pace = round(total / mins_played, 2) if mins_played > 0 else 0
            
            if g['period'] > 4 and not is_final:
                projected = round(total + (actual_pace * mins_remaining))
            elif mins_played > 0:
                projected = round((total / mins_played) * 48)
            else:
                projected = None
        else:
            total, projected, mins_played, mins_remaining, spread, is_final, actual_pace = 0, None, 0, 48, 0, False, 0
        
        if side == "NO":
            status_txt, color = get_status_no(pos['threshold'], total, projected, is_final)
            cushion = pos['threshold'] - total if is_final else (pos['threshold'] - projected if projected else None)
            need = pos['threshold'] - total
            need_label = "Need Under"
            pace_allowed = round(need / mins_remaining, 2) if mins_remaining > 0 else 0
        else:
            status_txt, color = get_status_yes(pos['threshold'], total, projected, is_final)
            cushion = total - pos['threshold'] if is_final else (projected - pos['threshold'] if projected else None)
            need = pos['threshold'] - total + 1
            need_label = "Need Over"
            pace_allowed = round(need / mins_remaining, 2) if mins_remaining > 0 else 0
        
        cost = pos['contracts'] * pos['price'] / 100
        profit = pos['contracts'] * (100 - pos['price']) / 100
        
        st.markdown(f"### 🏀 {pos['game'].replace('@', ' @ ')} — {side} {pos['threshold']}")
        
        if g:
            st.markdown(f"**{g['away_team']}** <span style='color:#00ff00'>**{g['away_score']}**</span> - **{g['home_team']}** <span style='color:#00ff00'>**{g['home_score']}**</span> = <span style='color:#00ff00'>**{total} pts | Q{g['period']} {g['clock']} left | {mins_remaining:.1f} min total left**</span>", unsafe_allow_html=True)
        
        status_col, refresh_col = st.columns([4, 1])
        with status_col:
            st.markdown(f"## <span style='color:{color}'>{status_txt}</span>", unsafe_allow_html=True)
        with refresh_col:
            if st.button("🔄 REFRESH", key=f"refresh_{i}", type="primary"):
                st.rerun()
        
        if spread <= 5 and g and g['period'] >= 3 and not is_final:
            st.error(f"⚠️ OT RISK — Spread only {spread} pts!")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Position", f"{pos['contracts']} {side} @ {pos['price']}¢")
        m2.metric("Cost", f"${cost:.2f}")
        m3.metric("If Win", f"+${profit:.2f}")
        if projected:
            m4.metric("Projected", f"{projected}")
        
        if mins_played > 0:
            n1, n2, n3, n4 = st.columns(4)
            if cushion is not None:
                n1.metric("Cushion", f"{cushion:+.0f} pts")
            n2.metric(need_label, f"{need:.1f} pts")
            if mins_remaining > 0:
                n3.metric("Pace Allowed", f"{pace_allowed:.1f}/min")
                n4.metric("Actual Pace", f"{actual_pace:.1f}/min", 
                         delta=f"{pace_allowed - actual_pace:+.1f}" if side == "NO" else f"{actual_pace - pace_allowed:+.1f}",
                         delta_color="normal")
        
        if st.button("🗑️ Remove", key=f"del_{i}"):
            st.session_state.positions.pop(i)
            st.rerun()
        
        st.divider()
else:
    st.info("👆 Add a position to start tracking")

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
st.caption("v10.3 | Pre-Bet Analysis + Position Tracker")
