import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# AUTO-REFRESH EVERY 10 SECONDS
st.markdown('<meta http-equiv="refresh" content="10">', unsafe_allow_html=True)

# ============================================================
# ESPN LIVE SCORES
# ============================================================
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

@st.cache_data(ttl=10)
def fetch_espn_live_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {}
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
            if status_type == "STATUS_SCHEDULED":
                status = "🟡 SCHEDULED"
            elif status_type == "STATUS_IN_PROGRESS":
                status = "🟢 LIVE"
            elif status_type == "STATUS_HALFTIME":
                status = "🟠 HALFTIME"
            elif status_type == "STATUS_END_PERIOD":
                status = "🟢 END Q"
            elif status_type == "STATUS_FINAL":
                status = "🔴 FINAL"
            else:
                status = "🟡 PENDING"
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score, "status": status,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except:
        return {}

# ============================================================
# POSITION TRACKER FUNCTIONS
# ============================================================
if 'positions' not in st.session_state:
    st.session_state.positions = []

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 48
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        clock_mins = mins + secs / 60
        return (period - 1) * 12 + (12 - clock_mins)
    except:
        return (period - 1) * 12

def get_projected(total, minutes):
    if minutes <= 0:
        return None
    return round((total / minutes) * 48)

def get_status(threshold, total, projected, is_final):
    if is_final:
        return ("✅ WON!", "green") if total < threshold else ("❌ LOST", "red")
    if projected is None:
        return ("⏳ WAITING", "gray")
    cushion = threshold - projected
    if cushion > 15:
        return ("🟢 VERY SAFE", "green")
    elif cushion > 8:
        return ("🟢 LOOKING GOOD", "green")
    elif cushion > 3:
        return ("🟡 ON TRACK", "yellow")
    elif cushion > -3:
        return ("🟠 TIGHT", "orange")
    elif cushion > -10:
        return ("🔴 DANGER", "red")
    else:
        return ("🔴 LIKELY LOSS", "red")

# ============================================================
# APP UI
# ============================================================
st.title("🎯 NBA EDGE FINDER + POSITION TRACKER")
now = datetime.now(pytz.timezone('US/Eastern'))
st.caption(f"Auto-refresh 10s | {now.strftime('%I:%M:%S %p ET')}")

# Fetch scores
games = fetch_espn_live_scores()

# ============================================================
# POSITION TRACKER SECTION
# ============================================================
st.header("📊 POSITION TRACKER")

# Add position
with st.expander("➕ ADD NEW POSITION", expanded=len(st.session_state.positions) == 0):
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        game_list = list(games.keys())
        if game_list:
            sel_game = st.selectbox("Game", game_list, format_func=lambda x: x.replace("@", " @ "))
        else:
            sel_game = st.text_input("Game (e.g. Brooklyn@Memphis)")
    with col2:
        sel_threshold = st.number_input("Threshold", 180.0, 280.0, 237.5, 0.5)
    with col3:
        sel_price = st.number_input("Price ¢", 1, 99, 85)
    with col4:
        sel_contracts = st.number_input("Contracts", 1, 1000, 100)
    with col5:
        st.write("")
        st.write("")
        if st.button("➕ ADD", type="primary"):
            if sel_game:
                st.session_state.positions.append({
                    "game": sel_game,
                    "threshold": sel_threshold,
                    "price": sel_price,
                    "contracts": sel_contracts
                })
                st.rerun()

# Display positions
if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        game_data = games.get(pos['game'])
        
        if game_data:
            total = game_data['total']
            period = game_data['period']
            clock = game_data['clock']
            status_type = game_data['status_type']
            away_score = game_data['away_score']
            home_score = game_data['home_score']
            spread = abs(away_score - home_score)
            mins = get_minutes_played(period, clock, status_type)
            projected = get_projected(total, mins)
            is_final = status_type == "STATUS_FINAL"
        else:
            total, projected, mins, spread = 0, None, 0, 0
            away_score, home_score, period, clock = 0, 0, 0, ""
            is_final = False
        
        status_txt, status_color = get_status(pos['threshold'], total, projected, is_final)
        cushion = pos['threshold'] - projected if projected else None
        cost = pos['contracts'] * pos['price'] / 100
        win_profit = pos['contracts'] * (100 - pos['price']) / 100
        need_remaining = pos['threshold'] - total
        
        # Color styling
        if status_color == "green":
            st.success(f"**🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}**")
        elif status_color == "yellow":
            st.warning(f"**🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}**")
        elif status_color == "orange":
            st.warning(f"**🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}**")
        elif status_color == "red":
            st.error(f"**🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}**")
        else:
            st.info(f"**🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}**")
        
        if game_data:
            st.markdown(f"### {away_score} - {home_score} = **{total} pts** | Q{period} {clock}")
        
        st.markdown(f"## {status_txt}")
        
        # OT Warning
        if spread <= 5 and period >= 3 and not is_final:
            st.error(f"⚠️ **OT RISK — Spread only {spread} pts!**")
        
        # Metrics
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Position", f"{pos['contracts']} @ {pos['price']}¢")
        c2.metric("Cost", f"${cost:.2f}")
        if projected:
            c3.metric("Projected", f"{projected} pts")
            c4.metric("Cushion", f"{cushion:+.0f} pts" if cushion else "—")
        if total > 0:
            c5.metric("Need Under", f"{need_remaining:.1f} pts")
        c6.metric("If Win", f"+${win_profit:.2f}")
        
        if st.button(f"🗑️ Remove", key=f"rm_{i}"):
            st.session_state.positions.pop(i)
            st.rerun()
        
        st.divider()
else:
    st.info("👆 Add a position above to start tracking!")

# ============================================================
# LIVE SCOREBOARD
# ============================================================
st.header("📺 LIVE SCOREBOARD")

if games:
    cols = st.columns(4)
    for i, (key, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.markdown(f"**{g['away_team']}** {g['away_score']}")
            st.markdown(f"**{g['home_team']}** {g['home_score']}")
            st.caption(f"{g['status']} Q{g['period']} {g['clock']} | Total: {g['total']}")
else:
    st.warning("No games found")

st.divider()
st.caption("v8.0 | Auto-refresh 10s | ESPN Live Scores")
