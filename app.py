import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="Extreme Totals NO Finder", page_icon="🎯", layout="wide")

# ============================================================
# SOUND ALERT SYSTEM
# ============================================================
def play_alert_sound(alert_type="edge"):
    sounds = {
        "edge": {"freq": 800, "duration": 0.3, "repeat": 2},
        "watchlist": {"freq": 600, "duration": 0.2, "repeat": 1},
        "mispriced": {"freq": 1000, "duration": 0.15, "repeat": 3},
        "q1_ended": {"freq": 500, "duration": 0.5, "repeat": 1},
    }
    sound = sounds.get(alert_type, sounds["edge"])
    js_code = f"""
    <script>
    (function() {{
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        for (let i = 0; i < {sound['repeat']}; i++) {{
            setTimeout(() => {{
                const osc = audioContext.createOscillator();
                const gain = audioContext.createGain();
                osc.connect(gain);
                gain.connect(audioContext.destination);
                osc.frequency.value = {sound['freq']};
                osc.type = 'sine';
                gain.gain.setValueAtTime(0.3, audioContext.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + {sound['duration']});
                osc.start(audioContext.currentTime);
                osc.stop(audioContext.currentTime + {sound['duration']});
            }}, i * ({sound['duration']} * 1000 + 100));
        }}
    }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

# ============================================================
# ESPN LIVE SCORES
# ============================================================
@st.cache_data(ttl=30)
def fetch_espn_live_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
        data = response.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score = normalize_team_name(name), score
                else:
                    away_team, away_score = normalize_team_name(name), score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            if status_type == "STATUS_SCHEDULED":
                status, quarter = "🟡 SCHEDULED", ""
            elif status_type == "STATUS_IN_PROGRESS":
                status, quarter = "🟢 LIVE", f"Q{period}"
            elif status_type == "STATUS_HALFTIME":
                status, quarter = "🟠 HALFTIME", "HALF"
            elif status_type == "STATUS_END_PERIOD":
                status, quarter = "🟢 LIVE", f"End Q{period}"
            elif status_type == "STATUS_FINAL":
                status, quarter = "🔴 FINAL", "FINAL"
            else:
                status, quarter = "🟡 PENDING", ""
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score, "status": status,
                "quarter": quarter, "clock": clock, "period": period
            }
        return games
    except:
        return {}

def normalize_team_name(name):
    mappings = {
        "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
        "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
        "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
        "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
        "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
        "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
        "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee",
        "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
        "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City",
        "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix",
        "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento",
        "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
        "Utah Jazz": "Utah", "Washington Wizards": "Washington"
    }
    return mappings.get(name, name)

def get_live_game_data(away, home, live_scores):
    game_key = f"{away}@{home}"
    if game_key in live_scores:
        return live_scores[game_key]
    game_key_rev = f"{home}@{away}"
    if game_key_rev in live_scores:
        g = live_scores[game_key_rev]
        return {"away_team": away, "home_team": home, "away_score": g["home_score"],
                "home_score": g["away_score"], "total": g["total"], "status": g["status"],
                "quarter": g["quarter"], "clock": g["clock"], "period": g["period"]}
    return None

# ============================================================
# TEAM DATA
# ============================================================
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

def get_bottom_3pt_teams(n=8):
    return [t for t, _ in sorted(TEAM_3PT_PCT.items(), key=lambda x: x[1])[:n]]

def get_bottom_pace_teams(n=10):
    return [t for t, _ in sorted(TEAM_PACE.items(), key=lambda x: x[1])[:n]]

def get_primary_watchlist():
    return set(get_bottom_3pt_teams(8)).intersection(set(get_bottom_pace_teams(10)))

# ============================================================
# KALSHI API
# ============================================================
def get_kalshi_url(market):
    event_ticker = market.get("event_ticker", "")
    if event_ticker:
        return f"https://kalshi.com/events/{event_ticker}"
    return "https://kalshi.com/sports/basketball/Pro%20Basketball%20(M)"

def get_price_tolerance(q1_total):
    if q1_total is None:
        return 0.68, "Pregame"
    elif q1_total < 48:
        return 0.78, "Q1 < 48"
    elif q1_total < 50:
        return 0.75, "Q1 48-49"
    elif q1_total < 55:
        return 0.70, "Q1 50-54"
    else:
        return 0.00, "Q1 ≥ 55"

def parse_game_date(game_code):
    try:
        year = "20" + game_code[:2]
        month_str = game_code[2:5].upper()
        day = game_code[5:7]
        months = {"JAN":"01","FEB":"02","MAR":"03","APR":"04","MAY":"05","JUN":"06",
                  "JUL":"07","AUG":"08","SEP":"09","OCT":"10","NOV":"11","DEC":"12"}
        return f"{year}-{months.get(month_str,'01')}-{day}"
    except:
        return None

def parse_teams_from_ticker(ticker_code):
    if len(ticker_code) < 12:
        return None, None
    teams_part = ticker_code[7:]
    away = TICKER_ABBREVS.get(teams_part[:3].upper(), teams_part[:3])
    home = TICKER_ABBREVS.get(teams_part[3:6].upper(), teams_part[3:6])
    return away, home

@st.cache_data(ttl=300)
def fetch_extreme_totals(min_threshold=245):
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": "KXNBATOTAL", "status": "open", "limit": 200}
    et = pytz.timezone('US/Eastern')
    today = datetime.now(et).strftime("%Y-%m-%d")
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return [], f"API Error: {response.status_code}", today
        data = response.json()
        markets = []
        for m in data.get("markets", []):
            floor_strike = m.get("floor_strike", 0)
            if floor_strike and floor_strike >= min_threshold:
                event_ticker = m.get("event_ticker", "")
                parts = event_ticker.split("-")
                if len(parts) >= 2:
                    game_code = parts[1]
                    if parse_game_date(game_code) != today:
                        continue
                    away, home = parse_teams_from_ticker(game_code)
                    yes_ask = m.get("yes_ask", 0) or 0
                    no_ask = m.get("no_ask", 0) or 0
                    if no_ask == 0 and yes_ask > 0:
                        no_ask = 1 - yes_ask
                    markets.append({
                        "ticker": m.get("ticker", ""),
                        "event_ticker": event_ticker,
                        "threshold": floor_strike,
                        "away_team": away,
                        "home_team": home,
                        "yes_ask": yes_ask,
                        "no_ask": no_ask,
                        "volume": m.get("volume", 0)
                    })
        markets.sort(key=lambda x: x["threshold"], reverse=True)
        return markets, None, today
    except Exception as e:
        return [], str(e), today

def calculate_confidence(market, q1_total, watchlist, spread_est=5):
    away, home = market["away_team"], market["home_team"]
    threshold, no_ask = market["threshold"], market["no_ask"]
    
    if q1_total is not None and q1_total >= 55:
        return 0, "🚫 Q1 ≥ 55 - NO TRADE", "red", {"REJECTED": "Q1 too high"}
    
    max_price, regime = get_price_tolerance(q1_total)
    if q1_total is not None and no_ask > max_price:
        return 0, f"🚫 Price {no_ask:.2f} > {max_price} for {regime}", "red", {"REJECTED": "Overpriced"}
    
    if q1_total is None:
        return 0, "⏳ WAIT FOR Q1", "gray", {}
    
    score, breakdown = 0, {}
    
    # Q1 Score
    q1_pts = 30 if q1_total < 45 else 27 if q1_total < 48 else 22 if q1_total < 50 else 15
    score += q1_pts
    breakdown["Q1 Regime"] = f"{q1_pts}/30"
    
    # Watchlist
    if away in watchlist or home in watchlist:
        score += 20
        breakdown["Watchlist"] = "✅ +20"
    else:
        breakdown["Watchlist"] = "❌ +0"
    
    # Price buffer
    buffer = max_price - no_ask
    price_pts = 20 if buffer >= 0.10 else 15 if buffer >= 0.06 else 10 if buffer >= 0.03 else 5
    score += price_pts
    breakdown["Price Buffer"] = f"{price_pts}/20"
    
    # Threshold
    score += 10 if threshold >= 252 else 7 if threshold >= 250 else 5 if threshold >= 248 else 3
    breakdown["Threshold"] = f"{threshold}"
    
    # Spread
    score += 8 if spread_est >= 7 else 5 if spread_est >= 5 else 2
    breakdown["OT Risk"] = f"Spread {spread_est}"
    
    if score >= 75:
        return score, "🚀 STRONG BET", "green", breakdown
    elif score >= 60:
        return score, "✅ GOOD BET", "green", breakdown
    elif score >= 45:
        return score, "🟡 MARGINAL", "yellow", breakdown
    else:
        return score, "⚠️ WEAK", "orange", breakdown

def check_and_alert(markets, live_scores, watchlist):
    alerts = []
    for m in markets:
        away, home, no_ask, threshold = m["away_team"], m["home_team"], m["no_ask"], m["threshold"]
        has_wl = away in watchlist or home in watchlist
        wl_team = away if away in watchlist else (home if home in watchlist else None)
        live = get_live_game_data(away, home, live_scores)
        
        if has_wl and no_ask <= 0.68:
            alerts.append({"type": "edge", "message": f"🔥 EDGE: {wl_team} at {no_ask:.2f} (≥{threshold})", "priority": 1})
        if no_ask <= 0.60:
            alerts.append({"type": "mispriced", "message": f"💰 MISPRICED: {away}@{home} NO at {no_ask:.2f}!", "priority": 2})
        if live:
            if live['period'] == 1 and "End" in str(live.get('quarter', '')) and live['total'] < 50:
                alerts.append({"type": "q1_ended", "message": f"✅ Q1 ENDED: {away}@{home} - {live['total']} pts!", "priority": 1})
            if live['period'] == 1 and live['status'] == "🟢 LIVE" and live['total'] < 40 and has_wl:
                alerts.append({"type": "watchlist", "message": f"🎯 Q1 WATCH: {wl_team} at {live['total']} pts", "priority": 3})
    alerts.sort(key=lambda x: x["priority"])
    return alerts

# ============================================================
# APP
# ============================================================
st.title("🎯 KALSHI EXTREME TOTALS - NO FINDER")
st.caption("Tail-risk exploitation system. You are not betting averages. You are betting tail collapse.")

watchlist = get_primary_watchlist()

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Settings")
    min_threshold = st.selectbox("Min Threshold", [245, 248, 250, 252], index=0)
    st.divider()
    st.subheader("💰 PRICE RULES")
    st.markdown("|Q1|Max NO|\n|:-:|:-:|\n|<48|0.78|\n|48-49|0.75|\n|50-54|0.70|\n|≥55|NO TRADE|")
    st.caption("Pregame: 0.68 max")
    st.divider()
    st.subheader("📋 Watchlist Teams")
    st.caption("Bottom 8 3PT% ∩ Bottom 10 Pace")
    for t in sorted(watchlist):
        st.success(f"⭐ **{t}**")
    st.divider()
    st.subheader("🔊 Sound Alerts")
    st.write("🔥 Edge | 💰 Mispriced | ✅ Q1 End | 🎯 Q1 Watch")
    if st.button("🔔 Test Sound"):
        st.session_state.test_sound = True
    st.divider()
    st.error("🛑 KILL: +5¢ in 30s → ABORT")

# MAIN
if st.button("🔄 Refresh Markets & Scores", type="primary"):
    st.cache_data.clear()
    st.rerun()

if st.session_state.get('test_sound'):
    play_alert_sound("edge")
    st.session_state.test_sound = False
    st.success("🔔 Sound test played!")

markets, error, today_date = fetch_extreme_totals(min_threshold)
live_scores = fetch_espn_live_scores()
st.caption(f"📅 Games for: **{today_date}** | Live scores refresh every 30s")

if not error and markets:
    alerts = check_and_alert(markets, live_scores, watchlist)
    if 'sound_enabled' not in st.session_state:
        st.session_state.sound_enabled = True
    if 'last_alert_count' not in st.session_state:
        st.session_state.last_alert_count = 0
    
    sound_on = st.toggle("🔊 Sound Alerts", value=st.session_state.sound_enabled)
    st.session_state.sound_enabled = sound_on
    
    if alerts:
        with st.expander(f"🚨 **{len(alerts)} ALERT(S)**", expanded=True):
            for a in alerts:
                if a["type"] == "edge":
                    st.error(a["message"])
                elif a["type"] == "mispriced":
                    st.warning(a["message"])
                elif a["type"] == "q1_ended":
                    st.success(a["message"])
                else:
                    st.info(a["message"])
        if sound_on and len(alerts) > st.session_state.last_alert_count:
            play_alert_sound(alerts[0]["type"])
        st.session_state.last_alert_count = len(alerts)

if error:
    st.error(f"API Error: {error}")
elif not markets:
    st.warning(f"No extreme totals (≥{min_threshold}) for today.")
else:
    # LIVE SCOREBOARD
    if live_scores:
        st.subheader("📺 LIVE SCOREBOARD")
        games_list = list(live_scores.values())
        for row_start in range(0, len(games_list), 4):
            cols = st.columns(min(4, len(games_list) - row_start))
            for i, game in enumerate(games_list[row_start:row_start+4]):
                with cols[i]:
                    st.write(f"**{game['away_team']}** {game['away_score']}")
                    st.write(f"**{game['home_team']}** {game['home_score']}")
                    st.caption(f"{game['status']} {game['quarter']} {game['clock']}")
                    if game['status'] == "🟢 LIVE" and game['period'] == 1:
                        st.success(f"Q1: {game['total']}")
        st.divider()
    
    st.markdown("**Status:** 🟡 SCHEDULED | 🟢 LIVE | 🟠 HALFTIME | 🔴 FINAL")
    
    # ============================================================
    # 🎯 TODAY'S WATCHLIST GAMES - PROMINENT SECTION
    # ============================================================
    watchlist_games = [m for m in markets if m["away_team"] in watchlist or m["home_team"] in watchlist]
    
    if watchlist_games:
        st.markdown("---")
        st.markdown("## 🎯 TODAY'S WATCHLIST GAMES")
        st.markdown("### *These games have STRUCTURAL BRAKES on scoring*")
        
        for m in watchlist_games:
            wl_team = m["away_team"] if m["away_team"] in watchlist else m["home_team"]
            live = get_live_game_data(m["away_team"], m["home_team"], live_scores)
            
            # Big colored box for watchlist games
            st.success(f"""
            ### 🏀 {m["away_team"]} @ {m["home_team"]}
            **⭐ WATCHLIST TEAM: {wl_team}** (Bottom 8 3PT% + Bottom 10 Pace)
            
            **Threshold:** {m["threshold"]} | **NO Price:** {m["no_ask"]:.2f} | **Live:** {f"{live['away_score']}-{live['home_score']} ({live['status']})" if live else "Not started"}
            """)
            
            # Price status for this game
            if m["no_ask"] <= 0.68:
                st.info(f"💰 Price {m['no_ask']:.2f} is UNDER pregame limit (0.68) - Monitor for Q1!")
            elif m["no_ask"] <= 0.78:
                st.warning(f"⏳ Price {m['no_ask']:.2f} - Will unlock with good Q1 score")
            else:
                st.error(f"🔴 Price {m['no_ask']:.2f} - Currently too expensive")
            
            st.link_button(f"🔗 Open Kalshi - {m['threshold']}", get_kalshi_url(m), type="primary")
            st.markdown("---")
    else:
        st.warning("⚠️ No watchlist team games found today")
    
    # TOP EDGES
    st.header("🔥 ALL TODAY'S TARGETS")
    st.caption("Games with good pregame prices (≤0.68)")
    scored = [m for m in markets if m["no_ask"] <= 0.68]
    for m in scored:
        has_wl = m["away_team"] in watchlist or m["home_team"] in watchlist
        m["score"] = (30 if has_wl else 0) + (25 if m["no_ask"] <= 0.60 else 15 if m["no_ask"] <= 0.65 else 0)
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    if scored[:3]:
        cols = st.columns(len(scored[:3]))
        for i, edge in enumerate(scored[:3]):
            with cols[i]:
                has_wl = edge["away_team"] in watchlist or edge["home_team"] in watchlist
                wl_team = edge["away_team"] if edge["away_team"] in watchlist else (edge["home_team"] if edge["home_team"] in watchlist else None)
                
                st.subheader(f"#{i+1} {edge['away_team']} @ {edge['home_team']}")
                
                # BIG watchlist indicator
                if has_wl:
                    st.success(f"⭐ **WATCHLIST: {wl_team}**")
                else:
                    st.warning("⚠️ No watchlist team")
                
                live = get_live_game_data(edge['away_team'], edge['home_team'], live_scores)
                if live:
                    st.write(f"**{live['status']}** {live['quarter']} {live['clock']}")
                    st.metric("LIVE", f"{live['away_score']}-{live['home_score']}", f"Total: {live['total']}")
                else:
                    st.write("🟡 **PENDING**")
                st.metric("Threshold", edge["threshold"])
                st.metric("NO Price", f"{edge['no_ask']:.2f}")
                st.link_button("🔗 Open Kalshi", get_kalshi_url(edge), type="secondary")
    else:
        st.info("No pregame edges ≤0.68")
    
    st.divider()
    
    # ALL MARKETS
    st.header("📊 All Markets")
    for m in markets:
        away, home, no_ask = m["away_team"], m["home_team"], m["no_ask"]
        has_wl = away in watchlist or home in watchlist
        wl_team = away if away in watchlist else (home if home in watchlist else None)
        live = get_live_game_data(away, home, live_scores)
        p_status = "🟢 OK" if no_ask <= 0.68 else "🟡 Q1 50-54" if no_ask <= 0.70 else "🟡 Q1 48-49" if no_ask <= 0.75 else "🟠 Q1<48" if no_ask <= 0.78 else "🔴 Expensive"
        
        # Highlight watchlist games with colored container
        if has_wl:
            st.markdown(f"### ⭐ WATCHLIST: {wl_team}")
        
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        c1.subheader(f"🏀 {away} @ {home}")
        c2.metric("LIVE", f"{live['away_score']}-{live['home_score']}" if live else "—")
        c3.metric("Threshold", m["threshold"])
        c4.metric("NO Price", f"{no_ask:.2f}")
        
        if live:
            if live['period'] == 1 and live['status'] == "🟢 LIVE":
                st.success(f"🎯 Q1 IN PROGRESS | Total: {live['total']} | {live['clock']}")
            elif live['period'] == 1 and "End" in live['quarter']:
                st.info(f"✅ Q1 ENDED | Total: {live['total']} | Enter in scorer!")
            else:
                st.write(f"{live['status']} {live['quarter']} | Total: {live['total']} | {p_status}")
        else:
            if has_wl:
                st.success(f"🟡 PENDING | ⭐ **WATCHLIST TEAM: {wl_team}** | {p_status}")
            else:
                st.write(f"🟡 PENDING | {p_status}")
        
        st.link_button("🔗 Open Kalshi", get_kalshi_url(m), type="secondary")
        st.divider()
    
    # CONFIDENCE SCORER
    st.header("🎯 CONFIDENCE SCORER")
    col1, col2 = st.columns([1, 2])
    with col1:
        opts = [f"{m['away_team']} @ {m['home_team']} ({m['threshold']})" for m in markets]
        sel_idx = st.selectbox("Select Game", range(len(opts)), format_func=lambda x: opts[x])
        sel = markets[sel_idx]
        
        # Check watchlist for selected game
        sel_has_wl = sel["away_team"] in watchlist or sel["home_team"] in watchlist
        sel_wl_team = sel["away_team"] if sel["away_team"] in watchlist else (sel["home_team"] if sel["home_team"] in watchlist else None)
        
        if sel_has_wl:
            st.success(f"⭐ **WATCHLIST TEAM: {sel_wl_team}**")
        else:
            st.warning("⚠️ No watchlist team in this game")
        
        live = get_live_game_data(sel['away_team'], sel['home_team'], live_scores)
        
        if live:
            st.success(f"**{live['status']}** {live['quarter']} {live['clock']}")
            st.metric("LIVE", f"{live['away_score']}-{live['home_score']}", f"Total: {live['total']}")
            default_q1 = live['total'] if live['period'] == 1 and "End" in str(live.get('quarter', '')) else 0
        else:
            st.info("🟡 PENDING")
            default_q1 = 0
        
        q1 = st.number_input("Q1 Score", 0, 100, default_q1)
        spread = st.number_input("Spread", 0.0, 30.0, 5.0, 0.5)
    
    with col2:
        q1_val = q1 if q1 > 0 else None
        score, rec, color, breakdown = calculate_confidence(sel, q1_val, watchlist, spread)
        
        if q1_val is None:
            st.warning("⏳ WAITING FOR Q1")
            st.write(f"NO Price: {sel['no_ask']:.2f} | Pregame limit: 0.68")
        else:
            st.subheader(f"Score: {score}/100")
            st.progress(min(score/100, 1.0))
            if color == "green":
                st.success(rec)
            elif color == "yellow":
                st.warning(rec)
            elif color == "red":
                st.error(rec)
            else:
                st.warning(rec)
            if "REJECTED" not in breakdown:
                for k, v in breakdown.items():
                    st.write(f"• {k}: {v}")
            if score >= 45:
                st.link_button(f"🚀 BET NO on {sel['threshold']}", get_kalshi_url(sel), type="primary")
                st.caption("🛑 ABORT if +5¢ spike")
        
        st.divider()
        st.link_button("🔗 Open Kalshi", get_kalshi_url(sel), type="secondary")
        st.caption("Navigation shortcut")

st.divider()
st.caption("v4.2 | ESPN Live | Sound Alerts | Q1 is King")
