import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Extreme Totals NO Finder", page_icon="🎯", layout="wide")

# ============================================================
# SOUND ALERT SYSTEM
# ============================================================
def play_alert_sound(alert_type="edge"):
    """Play sound alert using Web Audio API"""
    
    # Different frequencies for different alerts
    sounds = {
        "edge": {"freq": 800, "duration": 0.3, "repeat": 2},      # High beep x2 - Edge found
        "watchlist": {"freq": 600, "duration": 0.2, "repeat": 1}, # Medium beep - Watchlist team
        "mispriced": {"freq": 1000, "duration": 0.15, "repeat": 3}, # Fast high beeps - Mispriced!
        "q1_ended": {"freq": 500, "duration": 0.5, "repeat": 1},  # Long low beep - Q1 ended
    }
    
    sound = sounds.get(alert_type, sounds["edge"])
    
    js_code = f"""
    <script>
    (function() {{
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const freq = {sound['freq']};
        const duration = {sound['duration']};
        const repeat = {sound['repeat']};
        
        for (let i = 0; i < repeat; i++) {{
            setTimeout(() => {{
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + duration);
            }}, i * (duration * 1000 + 100));
        }}
    }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

def check_and_alert(markets, live_scores, watchlist):
    """Check for alert conditions and return alerts to display"""
    alerts = []
    
    for m in markets:
        away = m["away_team"]
        home = m["home_team"]
        no_ask = m["no_ask"]
        threshold = m["threshold"]
        
        # Check watchlist
        has_watchlist = away in watchlist or home in watchlist
        wl_team = away if away in watchlist else (home if home in watchlist else None)
        
        # Get live data
        live = get_live_game_data(away, home, live_scores)
        
        # ALERT 1: Watchlist team with good pregame price
        if has_watchlist and no_ask <= 0.68:
            alerts.append({
                "type": "edge",
                "message": f"🔥 EDGE: {wl_team} game at {no_ask:.2f} (threshold {threshold})",
                "priority": 1
            })
        
        # ALERT 2: Mispriced (very good price)
        if no_ask <= 0.60:
            alerts.append({
                "type": "mispriced",
                "message": f"💰 MISPRICED: {away}@{home} NO at {no_ask:.2f}!",
                "priority": 2
            })
        
        # ALERT 3: Q1 just ended with good total
        if live:
            if live['period'] == 1 and "End" in str(live.get('quarter', '')):
                if live['total'] < 50:
                    alerts.append({
                        "type": "q1_ended",
                        "message": f"✅ Q1 ENDED: {away}@{home} - Total {live['total']} - CHECK NOW!",
                        "priority": 1
                    })
            
            # ALERT 4: Q1 in progress with low score
            if live['period'] == 1 and live['status'] == "🟢 LIVE":
                if live['total'] < 40 and has_watchlist:
                    alerts.append({
                        "type": "watchlist",
                        "message": f"🎯 Q1 WATCH: {wl_team} game at {live['total']} pts - Monitor for entry",
                        "priority": 3
                    })
    
    # Sort by priority
    alerts.sort(key=lambda x: x["priority"])
    return alerts

# ============================================================
# ESPN LIVE SCORES
# ============================================================
@st.cache_data(ttl=30)  # Refresh every 30 seconds
def fetch_espn_live_scores():
    """Pull live NBA scores from ESPN API"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
        
        data = response.json()
        games = {}
        
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            
            if len(competitors) < 2:
                continue
            
            # Get teams
            home_team = None
            away_team = None
            home_score = 0
            away_score = 0
            
            for comp in competitors:
                team_name = comp.get("team", {}).get("displayName", "")
                score = int(comp.get("score", 0) or 0)
                if comp.get("homeAway") == "home":
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            # Game status
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            display_clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            
            if status_type == "STATUS_SCHEDULED":
                status = "🟡 SCHEDULED"
                quarter = ""
                clock = ""
            elif status_type == "STATUS_IN_PROGRESS":
                status = "🟢 LIVE"
                quarter = f"Q{period}"
                clock = display_clock
            elif status_type == "STATUS_HALFTIME":
                status = "🟠 HALFTIME"
                quarter = "HALF"
                clock = ""
            elif status_type == "STATUS_END_PERIOD":
                status = "🟢 LIVE"
                quarter = f"End Q{period}"
                clock = ""
            elif status_type == "STATUS_FINAL":
                status = "🔴 FINAL"
                quarter = "FINAL"
                clock = ""
            else:
                status = "🟡 PENDING"
                quarter = ""
                clock = ""
            
            # Normalize team names
            home_normalized = normalize_team_name(home_team)
            away_normalized = normalize_team_name(away_team)
            
            game_key = f"{away_normalized}@{home_normalized}"
            
            games[game_key] = {
                "away_team": away_normalized,
                "home_team": home_normalized,
                "away_score": away_score,
                "home_score": home_score,
                "total": away_score + home_score,
                "status": status,
                "quarter": quarter,
                "clock": clock,
                "period": period
            }
        
        return games
    except Exception as e:
        return {}

def normalize_team_name(name):
    """Convert ESPN team names to our format"""
    mappings = {
        "Atlanta Hawks": "Atlanta",
        "Boston Celtics": "Boston",
        "Brooklyn Nets": "Brooklyn",
        "Charlotte Hornets": "Charlotte",
        "Chicago Bulls": "Chicago",
        "Cleveland Cavaliers": "Cleveland",
        "Dallas Mavericks": "Dallas",
        "Denver Nuggets": "Denver",
        "Detroit Pistons": "Detroit",
        "Golden State Warriors": "Golden State",
        "Houston Rockets": "Houston",
        "Indiana Pacers": "Indiana",
        "LA Clippers": "LA Clippers",
        "Los Angeles Clippers": "LA Clippers",
        "LA Lakers": "LA Lakers",
        "Los Angeles Lakers": "LA Lakers",
        "Memphis Grizzlies": "Memphis",
        "Miami Heat": "Miami",
        "Milwaukee Bucks": "Milwaukee",
        "Minnesota Timberwolves": "Minnesota",
        "New Orleans Pelicans": "New Orleans",
        "New York Knicks": "New York",
        "Oklahoma City Thunder": "Oklahoma City",
        "Orlando Magic": "Orlando",
        "Philadelphia 76ers": "Philadelphia",
        "Phoenix Suns": "Phoenix",
        "Portland Trail Blazers": "Portland",
        "Sacramento Kings": "Sacramento",
        "San Antonio Spurs": "San Antonio",
        "Toronto Raptors": "Toronto",
        "Utah Jazz": "Utah",
        "Washington Wizards": "Washington"
    }
    return mappings.get(name, name)

def get_live_game_data(away, home, live_scores):
    """Match Kalshi market to ESPN live data"""
    game_key = f"{away}@{home}"
    if game_key in live_scores:
        return live_scores[game_key]
    
    # Try reverse
    game_key_rev = f"{home}@{away}"
    if game_key_rev in live_scores:
        g = live_scores[game_key_rev]
        return {
            "away_team": away,
            "home_team": home,
            "away_score": g["home_score"],
            "home_score": g["away_score"],
            "total": g["total"],
            "status": g["status"],
            "quarter": g["quarter"],
            "clock": g["clock"],
            "period": g["period"]
        }
    
    return None

# ============================================================
# TEAM DATA (Updated weekly - reliable fallback)
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

# ============================================================
# CORE FUNCTIONS
# ============================================================
def get_bottom_3pt_teams(n=8):
    sorted_teams = sorted(TEAM_3PT_PCT.items(), key=lambda x: x[1])
    return [team for team, pct in sorted_teams[:n]]

def get_bottom_pace_teams(n=10):
    sorted_teams = sorted(TEAM_PACE.items(), key=lambda x: x[1])
    return [team for team, pace in sorted_teams[:n]]

def get_primary_watchlist():
    bottom_3pt = set(get_bottom_3pt_teams(8))
    bottom_pace = set(get_bottom_pace_teams(10))
    return bottom_3pt.intersection(bottom_pace)

def get_price_tolerance(q1_total):
    """Hard rules. Simple. Enforceable."""
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
        month = months.get(month_str, "01")
        return f"{year}-{month}-{day}"
    except:
        return None

def parse_teams_from_ticker(ticker_code):
    if len(ticker_code) < 12:
        return None, None
    teams_part = ticker_code[7:]
    away_code = teams_part[:3]
    home_code = teams_part[3:6] if len(teams_part) >= 6 else teams_part[3:]
    away = TICKER_ABBREVS.get(away_code.upper(), away_code)
    home = TICKER_ABBREVS.get(home_code.upper(), home_code)
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
        markets = data.get("markets", [])
        extreme_markets = []
        
        for m in markets:
            floor_strike = m.get("floor_strike", 0)
            if floor_strike and floor_strike >= min_threshold:
                event_ticker = m.get("event_ticker", "")
                parts = event_ticker.split("-")
                if len(parts) >= 2:
                    game_code = parts[1]
                    game_date = parse_game_date(game_code)
                    if game_date != today:
                        continue
                    
                    away, home = parse_teams_from_ticker(game_code)
                    yes_ask = m.get("yes_ask", 0) or 0
                    no_ask = m.get("no_ask", 0) or 0
                    if no_ask == 0 and yes_ask > 0:
                        no_ask = 1 - yes_ask
                    
                    # Get game status
                    close_time = m.get("close_time", "")
                    status = "🟡 PENDING"
                    
                    extreme_markets.append({
                        "ticker": m.get("ticker", ""),
                        "threshold": floor_strike,
                        "away_team": away,
                        "home_team": home,
                        "yes_ask": yes_ask,
                        "no_ask": no_ask,
                        "volume": m.get("volume", 0),
                        "close_time": close_time,
                        "status": status
                    })
        
        extreme_markets.sort(key=lambda x: x["threshold"], reverse=True)
        return extreme_markets, None, today
    except Exception as e:
        return [], str(e), today

def calculate_confidence(market, q1_total, watchlist, spread_est=5):
    away = market["away_team"]
    home = market["home_team"]
    threshold = market["threshold"]
    no_ask = market["no_ask"]
    
    # GATE 1: Q1 too high
    if q1_total is not None and q1_total >= 55:
        return 0, "🚫 Q1 ≥ 55 - NO TRADE", "red", {"REJECTED": "Q1 too high"}
    
    # GATE 2: Price check
    max_price, regime = get_price_tolerance(q1_total)
    if q1_total is not None and no_ask > max_price:
        return 0, f"🚫 Price {no_ask:.2f} > {max_price} for {regime}", "red", {"REJECTED": "Overpriced"}
    
    if q1_total is None:
        return 0, "⏳ WAIT FOR Q1", "gray", {}
    
    # SCORING
    score = 0
    breakdown = {}
    
    # Q1 Score (30 max)
    if q1_total < 45:
        q1_pts = 30
    elif q1_total < 48:
        q1_pts = 27
    elif q1_total < 50:
        q1_pts = 22
    else:
        q1_pts = 15
    score += q1_pts
    breakdown["Q1 Regime"] = f"{q1_pts}/30"
    
    # Watchlist (20 max)
    if away in watchlist or home in watchlist:
        score += 20
        breakdown["Watchlist"] = "✅ +20"
    else:
        breakdown["Watchlist"] = "❌ +0"
    
    # Price buffer (20 max)
    buffer = max_price - no_ask
    if buffer >= 0.10:
        price_pts = 20
    elif buffer >= 0.06:
        price_pts = 15
    elif buffer >= 0.03:
        price_pts = 10
    else:
        price_pts = 5
    score += price_pts
    breakdown["Price Buffer"] = f"{price_pts}/20"
    
    # Threshold (10 max)
    if threshold >= 252:
        score += 10
    elif threshold >= 250:
        score += 7
    elif threshold >= 248:
        score += 5
    else:
        score += 3
    breakdown["Threshold"] = f"{threshold}"
    
    # Spread/OT (8 max)
    if spread_est >= 7:
        score += 8
    elif spread_est >= 5:
        score += 5
    else:
        score += 2
    breakdown["OT Risk"] = f"Spread {spread_est}"
    
    # Recommendation
    if score >= 75:
        rec = "🚀 STRONG BET"
        color = "green"
    elif score >= 60:
        rec = "✅ GOOD BET"
        color = "green"
    elif score >= 45:
        rec = "🟡 MARGINAL"
        color = "yellow"
    else:
        rec = "⚠️ WEAK"
        color = "orange"
    
    return score, rec, color, breakdown

# ============================================================
# APP LAYOUT
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
    st.markdown("""
| Q1 | Max NO |
|:--:|:------:|
| <48 | 0.78 |
| 48-49 | 0.75 |
| 50-54 | 0.70 |
| ≥55 | NO TRADE |
""")
    st.caption("Pregame: 0.68 max")
    
    st.divider()
    st.subheader("📋 Watchlist")
    st.caption("Bottom 8 3PT% ∩ Bottom 10 Pace")
    if watchlist:
        for t in sorted(watchlist):
            st.write(f"• **{t}**")
    else:
        st.warning("No teams qualify")
    
    st.divider()
    st.error("🛑 KILL SWITCH: If NO jumps +5¢ in 30s → ABORT")
    
    st.divider()
    st.subheader("🔊 SOUND ALERTS")
    st.caption("Alerts trigger when:")
    st.write("🔥 **Edge** - Watchlist + price ≤0.68")
    st.write("💰 **Mispriced** - Any NO ≤0.60")
    st.write("✅ **Q1 Ended** - Q1 done, total <50")
    st.write("🎯 **Q1 Watch** - Watchlist, Q1 <40")
    
    st.divider()
    st.caption("💡 Click Refresh to update live scores")

# MAIN CONTENT
if st.button("🔄 Refresh Markets & Scores", type="primary"):
    st.cache_data.clear()

markets, error, today_date = fetch_extreme_totals(min_threshold)
live_scores = fetch_espn_live_scores()

st.caption(f"📅 Games for: **{today_date}** | Live scores refresh every 30s")

# ============================================================
# SOUND ALERTS SECTION
# ============================================================
if not error and markets:
    # Check for alerts
    alerts = check_and_alert(markets, live_scores, watchlist)
    
    # Sound toggle in session state
    if 'sound_enabled' not in st.session_state:
        st.session_state.sound_enabled = True
    if 'last_alert_count' not in st.session_state:
        st.session_state.last_alert_count = 0
    
    # Sound control
    col_sound1, col_sound2 = st.columns([1, 4])
    with col_sound1:
        sound_on = st.toggle("🔊 Sound Alerts", value=st.session_state.sound_enabled)
        st.session_state.sound_enabled = sound_on
    
    # Display alerts if any
    if alerts:
        with st.expander(f"🚨 **{len(alerts)} ALERT(S) DETECTED** - Click to view", expanded=True):
            for alert in alerts:
                if alert["type"] == "edge":
                    st.error(alert["message"])
                elif alert["type"] == "mispriced":
                    st.warning(alert["message"])
                elif alert["type"] == "q1_ended":
                    st.success(alert["message"])
                else:
                    st.info(alert["message"])
        
        # Play sound if enabled and new alerts
        if sound_on and len(alerts) > st.session_state.last_alert_count:
            # Play the highest priority alert sound
            top_alert = alerts[0]
            play_alert_sound(top_alert["type"])
        
        st.session_state.last_alert_count = len(alerts)
    else:
        st.session_state.last_alert_count = 0

if error:
    st.error(f"API Error: {error}")
elif not markets:
    st.warning(f"No extreme totals (≥{min_threshold}) for today.")
else:
    # LIVE SCOREBOARD STRIP
    if live_scores:
        st.subheader("📺 LIVE SCOREBOARD (ESPN)")
        games_list = list(live_scores.values())
        
        # Display in rows of 4
        for row_start in range(0, len(games_list), 4):
            row_games = games_list[row_start:row_start + 4]
            score_cols = st.columns(len(row_games))
            
            for i, game in enumerate(row_games):
                with score_cols[i]:
                    st.write(f"**{game['away_team']}** {game['away_score']}")
                    st.write(f"**{game['home_team']}** {game['home_score']}")
                    st.caption(f"{game['status']} {game['quarter']} {game['clock']}")
                    if game['status'] == "🟢 LIVE" and game['period'] == 1:
                        st.success(f"Q1: {game['total']}")
        st.divider()
    else:
        st.info("No live games found. Games may not have started yet.")
    
    # STATUS LEGEND
    st.markdown("**Status:** 🟡 SCHEDULED | 🟢 LIVE | 🟠 HALFTIME | 🔴 FINAL")
    
    # TOP EDGES
    st.header("🔥 TODAY'S TARGETS")
    st.caption("Pregame rankings. WAIT FOR Q1 before betting.")
    
    scored = []
    for m in markets:
        if m["no_ask"] <= 0.68:
            pts = 0
            if m["away_team"] in watchlist or m["home_team"] in watchlist:
                pts += 30
            if m["no_ask"] <= 0.60:
                pts += 25
            elif m["no_ask"] <= 0.65:
                pts += 15
            if m["threshold"] >= 250:
                pts += 15
            scored.append({**m, "score": pts})
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    top3 = scored[:3]
    
    if top3:
        cols = st.columns(len(top3))
        for i, edge in enumerate(top3):
            with cols[i]:
                st.subheader(f"#{i+1} {edge['away_team']} @ {edge['home_team']}")
                
                # Get live score
                live = get_live_game_data(edge['away_team'], edge['home_team'], live_scores)
                if live:
                    st.write(f"**{live['status']}** {live['quarter']} {live['clock']}")
                    st.metric("LIVE SCORE", f"{live['away_score']} - {live['home_score']}", f"Total: {live['total']}")
                    if live['period'] == 1 and live['status'] == "🟢 LIVE":
                        st.success(f"🎯 Q1 Total: {live['total']} - Watch for entry!")
                else:
                    st.write("🟡 **PENDING - NOT STARTED**")
                
                st.metric("Threshold", edge["threshold"])
                st.metric("NO Price", f"{edge['no_ask']:.2f}")
                wl = "✅" if (edge["away_team"] in watchlist or edge["home_team"] in watchlist) else "⚠️"
                st.write(f"Watchlist: {wl}")
                
                # Direct Kalshi Link - Always visible
                st.link_button("🔗 Open Kalshi Market", f"https://kalshi.com/markets/{edge['ticker']}", type="secondary")
    else:
        st.info("No pregame edges under 0.68 — Check 'All Markets' below for full list with Kalshi links")
    
    st.divider()
    
    # ALL MARKETS
    st.header("📊 All Markets - LIVE SCORES")
    for m in markets:
        away, home = m["away_team"], m["home_team"]
        wl_badge = "✅ WL" if (away in watchlist or home in watchlist) else "⚠️"
        
        # Get live score
        live = get_live_game_data(away, home, live_scores)
        
        # Price status
        if m["no_ask"] <= 0.68:
            p_status = "🟢 Pregame OK"
        elif m["no_ask"] <= 0.70:
            p_status = "🟡 Needs Q1 50-54"
        elif m["no_ask"] <= 0.75:
            p_status = "🟡 Needs Q1 48-49"
        elif m["no_ask"] <= 0.78:
            p_status = "🟠 Needs Q1 <48"
        else:
            p_status = "🔴 Too expensive"
        
        with st.container():
            # Row 1: Team names and live score
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            
            with c1:
                st.subheader(f"🏀 {away} @ {home}")
            
            with c2:
                if live:
                    st.metric("LIVE", f"{live['away_score']} - {live['home_score']}")
                else:
                    st.metric("LIVE", "-- - --")
            
            with c3:
                st.metric("Threshold", m["threshold"])
            
            with c4:
                st.metric("NO Price", f"{m['no_ask']:.2f}")
            
            # Row 2: Status and details
            if live:
                status_text = f"{live['status']} {live['quarter']} {live['clock']}"
                total_text = f"**Current Total: {live['total']}**"
                
                # Q1 alert
                if live['period'] == 1 and live['status'] == "🟢 LIVE":
                    st.success(f"🎯 **Q1 IN PROGRESS** | Q1 Total: {live['total']} | {live['clock']} remaining")
                elif live['period'] == 1 and "End" in live['quarter']:
                    st.info(f"✅ **Q1 ENDED** | Q1 Final: {live['total']} | Enter this in scorer!")
                elif live['period'] > 1:
                    st.write(f"{status_text} | Total: {live['total']} | {wl_badge} | {p_status}")
                else:
                    st.write(f"{status_text} | {wl_badge} | {p_status}")
            else:
                st.write(f"🟡 **PENDING** | {wl_badge} | {p_status}")
            
            # Direct Kalshi Link - Always visible, neutral placement
            st.link_button("🔗 Open Kalshi Market", f"https://kalshi.com/markets/{m['ticker']}", type="secondary")
            st.divider()
    
    # CONFIDENCE SCORER
    st.header("🎯 CONFIDENCE SCORER")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        opts = [f"{m['away_team']} @ {m['home_team']} ({m['threshold']})" for m in markets]
        sel_idx = st.selectbox("Select Game", range(len(opts)), format_func=lambda x: opts[x])
        sel = markets[sel_idx]
        
        # Get live data for selected game
        live = get_live_game_data(sel['away_team'], sel['home_team'], live_scores)
        
        # Show live score box
        if live:
            st.success(f"**{live['status']}** {live['quarter']} {live['clock']}")
            st.metric("LIVE SCORE", f"{live['away_score']} - {live['home_score']}", f"Total: {live['total']}")
            
            # Auto-suggest Q1 if Q1 just ended
            if live['period'] == 1 and "End" in str(live.get('quarter', '')):
                st.info(f"✅ Q1 just ended! Total: **{live['total']}**")
                default_q1 = live['total']
            elif live['period'] > 1:
                st.warning(f"⚠️ Game past Q1. Current total: {live['total']}")
                default_q1 = 0
            else:
                default_q1 = 0
        else:
            st.info("🟡 **GAME NOT STARTED**")
            default_q1 = 0
        
        q1 = st.number_input("Q1 Combined Score", 0, 100, default_q1, help="Enter Q1 total after Q1 ends")
        spread = st.number_input("Pregame Spread", 0.0, 30.0, 5.0, 0.5)
    
    with col2:
        q1_val = q1 if q1 > 0 else None
        score, rec, color, breakdown = calculate_confidence(sel, q1_val, watchlist, spread)
        
        if q1_val is None:
            st.warning("⏳ **WAITING FOR Q1 DATA**")
            st.write("Game is **PENDING**. Enter Q1 combined score after first quarter ends.")
            st.write(f"**Current NO Price:** {sel['no_ask']:.2f}")
            max_p, regime = get_price_tolerance(None)
            st.write(f"**Pregame Limit:** {max_p}")
        else:
            st.subheader(f"Score: {score}/100")
            st.progress(min(score/100, 1.0))
            
            if color == "green":
                st.success(rec)
            elif color == "yellow":
                st.warning(rec)
            elif color == "orange":
                st.warning(rec)
            elif color == "red":
                st.error(rec)
            else:
                st.info(rec)
            
            if breakdown and "REJECTED" not in breakdown:
                st.write("**Breakdown:**")
                for k, v in breakdown.items():
                    st.write(f"• {k}: {v}")
            
            if score >= 45:
                st.link_button(f"BET NO on {sel['threshold']}", f"https://kalshi.com/markets/{sel['ticker']}", type="primary")
                st.caption("🛑 ABORT if price jumps +5¢ suddenly")

st.divider()
st.caption("v4.1 | 🟢 ESPN Live Scores | Q1 is King | Gate-First Logic")
