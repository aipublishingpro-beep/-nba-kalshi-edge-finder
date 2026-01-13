import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== INITIALIZE SESSION STATE ==========
if "positions" not in st.session_state:
    st.session_state.positions = []

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("📖 LEGEND")
    st.markdown("""
    **Edge Score:**  
    🟢 8+ STRONG | 🟢 6-7 GOOD  
    🟡 4-5 LEAN | 🔴 0-3 SKIP
    
    **Cushion (Size):**  
    🟢 +20 BIG | 🟡 +10-19 MED  
    🟠 +5-9 SMALL | 🔴 <5 SKIP
    
    **Pace:**  
    🟢 <4.5 SLOW | 🟡 4.5-4.8 AVG  
    🟠 4.8-5.2 FAST | 🔴 >5.2 SHOOTOUT
    """)
    st.divider()
    st.caption("v10.34")

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
        time_left = mins + secs/60
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

# Fetch data
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')}")

# ========== ACTIVE POSITIONS (TOP - always visible) ==========
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        side = pos['side']
        threshold = pos['threshold']
        price = pos['price']
        contracts = pos['contracts']
        
        g = games.get(game_key)
        
        if g:
            total = g['total']
            mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            projected = round((total / mins) * 48) if mins > 0 else None
            
            if side == "NO":
                cushion = (threshold - projected) if projected else 0
            else:
                cushion = (projected - threshold) if projected else 0
            
            if is_final:
                won = (total < threshold) if side == "NO" else (total > threshold)
                status = "✅ WON!" if won else "❌ LOST"
                color = "#00ff00" if won else "#ff0000"
            elif projected:
                if cushion > 10:
                    status, color = f"🟢 +{cushion:.0f}", "#00ff00"
                elif cushion > 3:
                    status, color = f"🟡 +{cushion:.0f}", "#ffff00"
                elif cushion > -3:
                    status, color = f"🟠 {cushion:+.0f}", "#ff8800"
                else:
                    status, color = f"🔴 {cushion:+.0f}", "#ff0000"
            else:
                status, color = "⏳ WAITING", "#888888"
            
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{game_key.replace('@', ' @ ')}**<br><small>{game_status} | {total} pts</small>", unsafe_allow_html=True)
            c2.markdown(f"**{side} {threshold}**")
            c3.markdown(f"Proj: **{projected if projected else '—'}**")
            c4.markdown(f"<span style='color:{color};font-size:1.2em'><b>{status}</b></span>", unsafe_allow_html=True)
            if c5.button("❌", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
        else:
            c1, c2 = st.columns([5, 1])
            c1.warning(f"Game not found: {game_key}")
            if c2.button("❌", key=f"del_m_{idx}"):
                st.session_state.positions.pop(idx)
                st.rerun()
    
    total_cost = sum(p['price'] * p['contracts'] for p in st.session_state.positions) / 100
    total_pot = sum((100 - p['price']) * p['contracts'] for p in st.session_state.positions) / 100
    sc1, sc2 = st.columns([4, 1])
    sc1.markdown(f"**💰 Risk: ${total_cost:.2f} | Potential: ${total_pot:.2f}**")
    if sc2.button("🗑️ Clear All"):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions yet. Add one below ⬇️")

st.divider()

# ========== ADD POSITION ==========
st.subheader("➕ ADD POSITION")

if game_list:
    ac1, ac2, ac3, ac4, ac5 = st.columns([3, 1, 1, 1, 1])
    with ac1:
        add_game = st.selectbox("Game", game_list, format_func=lambda x: x.replace("@", " @ "), key="add_game")
    with ac2:
        add_side = st.selectbox("Side", ["NO", "YES"], key="add_side")
    with ac3:
        add_threshold = st.number_input("Line", 200.0, 280.0, 235.5, 0.5, key="add_threshold")
    with ac4:
        add_price = st.number_input("Price ¢", 1, 99, 85, key="add_price")
    with ac5:
        add_contracts = st.number_input("Contracts", 1, 1000, 100, key="add_contracts")
    
    add_btn = st.button("➕ ADD TO TRACKER", type="primary", use_container_width=True)
    
    if add_btn:
        st.session_state.positions.append({
            "game": add_game,
            "side": add_side,
            "threshold": add_threshold,
            "price": add_price,
            "contracts": add_contracts
        })
        st.experimental_rerun()
else:
    st.warning("No games available")

st.divider()

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

cs1, cs2 = st.columns([1, 1])
with cs1:
    cush_min = st.selectbox("Min minutes", [6, 9, 12, 18, 24], index=1, format_func=lambda x: f"{x} min", key="cush_min")
with cs2:
    cush_side = st.selectbox("Side", ["NO", "YES"], key="cush_side")

thresholds = [225.5, 230.5, 235.5, 240.5, 245.5]
cush_data = []

for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= cush_min:
        proj = round((g['total'] / mins) * 48) if mins > 0 else 0
        cush_data.append({"game": gk, "proj": proj})

if cush_data:
    hcols = st.columns([2, 1] + [1]*len(thresholds))
    hcols[0].markdown("**Game**")
    hcols[1].markdown("**Proj**")
    for i, t in enumerate(thresholds):
        hcols[i+2].markdown(f"**{t}**")
    
    for cd in cush_data:
        rcols = st.columns([2, 1] + [1]*len(thresholds))
        rcols[0].write(cd['game'].replace("@", " @ "))
        rcols[1].write(f"{cd['proj']}")
        for i, t in enumerate(thresholds):
            c = (t - cd['proj']) if cush_side == "NO" else (cd['proj'] - t)
            if c >= 20:
                rcols[i+2].markdown(f"<span style='color:#00ff00'>**+{c:.0f}**</span>", unsafe_allow_html=True)
            elif c >= 10:
                rcols[i+2].markdown(f"<span style='color:#ffff00'>**+{c:.0f}**</span>", unsafe_allow_html=True)
            elif c >= 5:
                rcols[i+2].markdown(f"<span style='color:#ff8800'>**+{c:.0f}**</span>", unsafe_allow_html=True)
            elif c >= 0:
                rcols[i+2].markdown(f"<span style='color:#ff4444'>+{c:.0f}</span>", unsafe_allow_html=True)
            else:
                rcols[i+2].markdown(f"<span style='color:#ff0000'>{c:.0f}</span>", unsafe_allow_html=True)
else:
    st.info(f"No games with {cush_min}+ minutes played yet")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({
            "game": gk, "total": g['total'], "mins": mins, "pace": pace,
            "proj": proj, "period": g['period'], "clock": g['clock'],
            "final": g['status_type'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
        
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']} pts in {p['mins']:.0f} min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ========== FATIGUE SCANNER ==========
st.subheader("😴 FATIGUE SCANNER")

for gk, g in games.items():
    away, home = g['away_team'], g['home_team']
    away_b2b = away in yesterday_teams
    home_b2b = home in yesterday_teams
    
    if away_b2b or home_b2b:
        st.markdown(f"### 🏀 {away} @ {home}")
        if away_b2b:
            st.error(f"🔴 {away} on BACK-TO-BACK")
        if home_b2b:
            st.error(f"🔴 {home} on BACK-TO-BACK")
        if away_b2b and home_b2b:
            st.success("🟢 BOTH TIRED — Strong Under spot")
        elif away_b2b and not home_b2b:
            st.warning(f"🔥 BLOWOUT RISK — {away} tired @ fresh {home}")
        st.markdown("---")

st.divider()

# ========== SCOREBOARD ==========
st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()
    st.caption("v10.34")
