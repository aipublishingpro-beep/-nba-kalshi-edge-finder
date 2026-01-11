import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

st.markdown('<meta http-equiv="refresh" content="10">', unsafe_allow_html=True)

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

def get_minutes(period, clock, status_type):
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
        return (period - 1) * 12 + (12 - mins - secs/60)
    except:
        return (period - 1) * 12

def get_status(threshold, total, projected, is_final):
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

# Initialize
if 'positions' not in st.session_state:
    st.session_state.positions = []

# Fetch games
games = fetch_espn_scores()
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA POSITION TRACKER")
st.caption(f"Auto-refresh 10s | {now.strftime('%I:%M:%S %p ET')}")

# ========== ADD POSITION ==========
st.subheader("➕ ADD POSITION")
c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
with c1:
    game_list = list(games.keys())
    if game_list:
        new_game = st.selectbox("Game", game_list, format_func=lambda x: x.replace("@", " @ "))
    else:
        new_game = st.text_input("Game (e.g. Brooklyn@Memphis)")
with c2:
    new_threshold = st.number_input("Threshold", 180.0, 280.0, 237.5, 0.5)
with c3:
    new_price = st.number_input("Price ¢", 1, 99, 85)
with c4:
    new_contracts = st.number_input("Contracts", 1, 1000, 100)
with c5:
    st.write("")
    st.write("")
    if st.button("➕ ADD", type="primary"):
        st.session_state.positions.append({
            "game": new_game,
            "threshold": new_threshold,
            "price": new_price,
            "contracts": new_contracts
        })
        st.rerun()

st.divider()

# ========== POSITIONS ==========
if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        g = games.get(pos['game'])
        
        if g:
            total = g['total']
            mins = get_minutes(g['period'], g['clock'], g['status_type'])
            projected = round((total / mins) * 48) if mins > 0 else None
            is_final = g['status_type'] == "STATUS_FINAL"
            spread = abs(g['away_score'] - g['home_score'])
        else:
            total, projected, mins, spread, is_final = 0, None, 0, 0, False
        
        status_txt, color = get_status(pos['threshold'], total, projected, is_final)
        cushion = pos['threshold'] - projected if projected else None
        cost = pos['contracts'] * pos['price'] / 100
        profit = pos['contracts'] * (100 - pos['price']) / 100
        need = pos['threshold'] - total
        
        # Display
        st.markdown(f"### 🏀 {pos['game'].replace('@', ' @ ')} — NO {pos['threshold']}")
        
        if g:
            st.markdown(f"**{g['away_score']} - {g['home_score']} = {total} pts** | Q{g['period']} {g['clock']}")
        
        st.markdown(f"## <span style='color:{color}'>{status_txt}</span>", unsafe_allow_html=True)
        
        if spread <= 5 and g and g['period'] >= 3 and not is_final:
            st.error(f"⚠️ OT RISK — Spread only {spread} pts!")
        
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Position", f"{pos['contracts']} @ {pos['price']}¢")
        m2.metric("Cost", f"${cost:.2f}")
        if projected:
            m3.metric("Projected", f"{projected}")
            m4.metric("Cushion", f"{cushion:+.0f}")
        if total > 0:
            m5.metric("Need Under", f"{need:.1f}")
        m6.metric("If Win", f"+${profit:.2f}")
        
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
st.caption("v8.1 | Position Tracker + Live ESPN")
