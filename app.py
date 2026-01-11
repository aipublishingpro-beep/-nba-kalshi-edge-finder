import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Extreme Totals NO Finder", page_icon="🎯", layout="wide")

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
                    
                    extreme_markets.append({
                        "ticker": m.get("ticker", ""),
                        "threshold": floor_strike,
                        "away_team": away,
                        "home_team": home,
                        "yes_ask": yes_ask,
                        "no_ask": no_ask,
                        "volume": m.get("volume", 0)
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

# MAIN CONTENT
if st.button("🔄 Refresh Markets", type="primary"):
    st.cache_data.clear()

markets, error, today_date = fetch_extreme_totals(min_threshold)
st.caption(f"📅 Games for: **{today_date}**")

if error:
    st.error(f"API Error: {error}")
elif not markets:
    st.warning(f"No extreme totals (≥{min_threshold}) for today.")
else:
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
                st.metric("Threshold", edge["threshold"])
                st.metric("NO Price", f"{edge['no_ask']:.2f}")
                wl = "✅" if (edge["away_team"] in watchlist or edge["home_team"] in watchlist) else "⚠️"
                st.write(f"Watchlist: {wl}")
    else:
        st.info("No pregame edges under 0.68")
    
    st.divider()
    
    # ALL MARKETS
    st.header("📊 All Markets")
    for m in markets:
        away, home = m["away_team"], m["home_team"]
        wl_badge = "✅ WL" if (away in watchlist or home in watchlist) else "⚠️"
        
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
            c1, c2, c3 = st.columns(3)
            c1.subheader(f"🏀 {away} @ {home}")
            c2.metric("Threshold", m["threshold"])
            c3.metric("NO Price", f"{m['no_ask']:.2f}")
            st.write(f"{wl_badge} | {p_status}")
            st.markdown(f"[Kalshi Link](https://kalshi.com/markets/{m['ticker']})")
            st.divider()
    
    # CONFIDENCE SCORER
    st.header("🎯 CONFIDENCE SCORER")
    st.caption("Enter Q1 after first quarter ends.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        opts = [f"{m['away_team']} @ {m['home_team']} ({m['threshold']})" for m in markets]
        sel_idx = st.selectbox("Select Game", range(len(opts)), format_func=lambda x: opts[x])
        sel = markets[sel_idx]
        
        q1 = st.number_input("Q1 Combined Score", 0, 100, 0)
        spread = st.number_input("Pregame Spread", 0.0, 30.0, 5.0, 0.5)
    
    with col2:
        q1_val = q1 if q1 > 0 else None
        score, rec, color, breakdown = calculate_confidence(sel, q1_val, watchlist, spread)
        
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
        
        if breakdown:
            st.write("**Breakdown:**")
            for k, v in breakdown.items():
                st.write(f"• {k}: {v}")
        
        if score >= 45 and q1_val:
            st.link_button(f"BET NO on {sel['threshold']}", f"https://kalshi.com/markets/{sel['ticker']}", type="primary")

st.divider()
st.caption("v4.0 | Q1 is King | Gate-First Logic")
