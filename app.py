import streamlit as st
import requests
from datetime import datetime
import math

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NYK": "New York", "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia",
    "PHX": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"net_rating": -1.8, "def_rank": 21, "pace": 101.2, "ppg": 118.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southeast"},
    "Boston": {"net_rating": 11.2, "def_rank": 2, "pace": 99.8, "ppg": 120.5, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Atlantic"},
    "Brooklyn": {"net_rating": -3.2, "def_rank": 22, "pace": 96.3, "ppg": 108.2, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic"},
    "Charlotte": {"net_rating": -5.5, "def_rank": 25, "pace": 100.5, "ppg": 110.5, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast"},
    "Chicago": {"net_rating": -2.5, "def_rank": 18, "pace": 98.5, "ppg": 112.0, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Central"},
    "Cleveland": {"net_rating": 9.8, "def_rank": 1, "pace": 97.2, "ppg": 116.8, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Central"},
    "Dallas": {"net_rating": 3.5, "def_rank": 12, "pace": 99.8, "ppg": 117.5, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest"},
    "Denver": {"net_rating": 4.2, "def_rank": 15, "pace": 98.5, "ppg": 116.2, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Northwest"},
    "Detroit": {"net_rating": -6.2, "def_rank": 27, "pace": 99.2, "ppg": 110.8, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central"},
    "Golden State": {"net_rating": 2.8, "def_rank": 11, "pace": 100.2, "ppg": 115.8, "home_win_pct": 0.62, "away_win_pct": 0.38, "division": "Pacific"},
    "Houston": {"net_rating": 3.2, "def_rank": 5, "pace": 99.5, "ppg": 114.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest"},
    "Indiana": {"net_rating": 2.5, "def_rank": 24, "pace": 103.5, "ppg": 121.5, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central"},
    "LA Clippers": {"net_rating": 1.5, "def_rank": 10, "pace": 98.5, "ppg": 112.8, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific"},
    "LA Lakers": {"net_rating": 1.8, "def_rank": 13, "pace": 99.8, "ppg": 115.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific"},
    "Memphis": {"net_rating": 2.2, "def_rank": 16, "pace": 100.8, "ppg": 117.2, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest"},
    "Miami": {"net_rating": 0.5, "def_rank": 8, "pace": 97.5, "ppg": 110.5, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast"},
    "Milwaukee": {"net_rating": 3.8, "def_rank": 14, "pace": 100.5, "ppg": 118.2, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Central"},
    "Minnesota": {"net_rating": 5.5, "def_rank": 3, "pace": 97.8, "ppg": 112.5, "home_win_pct": 0.65, "away_win_pct": 0.50, "division": "Northwest"},
    "New Orleans": {"net_rating": -2.0, "def_rank": 19, "pace": 99.0, "ppg": 113.2, "home_win_pct": 0.45, "away_win_pct": 0.28, "division": "Southwest"},
    "New York": {"net_rating": 5.8, "def_rank": 6, "pace": 98.5, "ppg": 117.8, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic"},
    "Oklahoma City": {"net_rating": 10.5, "def_rank": 4, "pace": 99.5, "ppg": 119.5, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Northwest"},
    "Orlando": {"net_rating": 4.8, "def_rank": 2, "pace": 96.5, "ppg": 108.5, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southeast"},
    "Philadelphia": {"net_rating": 1.2, "def_rank": 9, "pace": 98.2, "ppg": 113.8, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic"},
    "Phoenix": {"net_rating": 2.5, "def_rank": 17, "pace": 98.8, "ppg": 115.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific"},
    "Portland": {"net_rating": -6.8, "def_rank": 28, "pace": 98.2, "ppg": 107.5, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest"},
    "Sacramento": {"net_rating": -1.2, "def_rank": 23, "pace": 100.5, "ppg": 117.8, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific"},
    "San Antonio": {"net_rating": -4.5, "def_rank": 26, "pace": 99.8, "ppg": 112.5, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest"},
    "Toronto": {"net_rating": -3.2, "def_rank": 20, "pace": 99.5, "ppg": 113.5, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic"},
    "Utah": {"net_rating": -8.5, "def_rank": 29, "pace": 100.8, "ppg": 108.2, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest"},
    "Washington": {"net_rating": -9.2, "def_rank": 30, "pace": 101.2, "ppg": 108.5, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast"},
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976), "Charlotte": (35.225, -80.839),
    "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688), "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010),
    "Detroit": (42.341, -83.055), "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051), "Miami": (25.781, -80.188),
    "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276), "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994),
    "Oklahoma City": (35.463, -97.515), "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438), "Toronto": (43.643, -79.379),
    "Utah": (40.768, -111.901), "Washington": (38.898, -77.021),
}

def calc_travel(away, home):
    if away not in TEAM_LOCATIONS or home not in TEAM_LOCATIONS:
        return 0
    lat1, lon1 = TEAM_LOCATIONS[away]
    lat2, lon2 = TEAM_LOCATIONS[home]
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(3959 * 2 * math.asin(math.sqrt(a)))

def parse_teams(ticker):
    try:
        code = ticker.split('-')[1]
        away_abbr, home_abbr = code[-6:-3].upper(), code[-3:].upper()
        date_part = code[:-6]
        year = int("20" + date_part[:2])
        month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
        game_date = datetime(year, month_map.get(date_part[2:5].upper(), 1), int(date_part[5:7]))
        return KALSHI_ABBREV_MAP.get(home_abbr), KALSHI_ABBREV_MAP.get(away_abbr), game_date
    except:
        return None, None, None

@st.cache_data(ttl=300)
def fetch_markets():
    markets = []
    today = datetime.now().date()
    try:
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open", timeout=10)
        for m in resp.json().get('markets', []):
            home, away, game_date = parse_teams(m.get('ticker', ''))
            if not home or not away or not game_date or game_date.date() < today:
                continue
            yes_bid = m.get('yes_bid', 0) or 0
            yes_ask = m.get('yes_ask', 0) or 0
            yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else yes_ask or yes_bid or 50
            # KALSHI YES = Away wins, so home win % = 100 - yes_price
            home_prob = 100 - yes_price
            markets.append({
                'ticker': m.get('ticker'), 'home': home, 'away': away,
                'home_prob': home_prob, 'away_prob': yes_price,
                'game_date': game_date.strftime('%b %d'),
                'game_dt': game_date, 'is_today': game_date.date() == today
            })
    except Exception as e:
        st.error(f"API error: {e}")
    return sorted(markets, key=lambda x: x['game_dt'])

@st.cache_data(ttl=3600)
def fetch_rest():
    rest = {t: 2 for t in TEAM_STATS}
    try:
        resp = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        now = datetime.now()
        for m in resp.json().get('markets', []):
            home, away, gd = parse_teams(m.get('ticker', ''))
            if home and away and gd:
                days = (now - gd).days
                if 0 <= days <= 5:
                    rest[home] = min(rest.get(home, 99), days)
                    rest[away] = min(rest.get(away, 99), days)
    except:
        pass
    return rest

def calc_edge(home, away, market_home_prob, h_rest, a_rest, h_inj, a_inj, travel):
    """
    SIMPLE EDGE CALCULATION
    Market is 95% right. We only adjust for situational factors.
    """
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    if not hs or not aws:
        return {"edge": 0, "adj_edge": 0, "factors": {}, "rec": "NO DATA"}
    
    factors = {}
    
    # REST: +1% per day advantage, max ±2%
    rest_diff = h_rest - a_rest
    factors["rest"] = max(-2, min(2, rest_diff * 0.8))
    
    # INJURY: +1.5% per level, max ±3%
    inj_diff = a_inj - h_inj
    factors["injury"] = max(-3, min(3, inj_diff * 1.0))
    
    # TRAVEL: +0.5% if away traveled far
    factors["travel"] = 0.5 if travel > 2000 else (0.3 if travel > 1500 else 0)
    
    # DIVISION: -0.5% (games are tighter)
    factors["division"] = -0.5 if hs.get("division") == aws.get("division") else 0
    
    # SUM AND CAP
    raw_edge = sum(factors.values())
    raw_edge = max(-3, min(3, raw_edge))  # Cap at ±3%
    
    # HAIRCUT: Keep only 60% of edge
    adj_edge = raw_edge * 0.6
    
    # RECOMMENDATION
    abs_edge = abs(adj_edge)
    if abs_edge < 1.0:
        rec = "NO EDGE"
    elif abs_edge < 1.8:
        rec = "SLIGHT " + ("HOME" if adj_edge > 0 else "AWAY")
    elif abs_edge < 2.5:
        rec = "LEAN " + ("HOME" if adj_edge > 0 else "AWAY")
    else:
        rec = "EDGE " + ("HOME" if adj_edge > 0 else "AWAY")
    
    return {
        "raw_edge": round(raw_edge, 2),
        "adj_edge": round(adj_edge, 2),
        "factors": factors,
        "rec": rec,
        "h_rest": h_rest, "a_rest": a_rest,
        "travel": travel
    }

# ========== UI ==========
st.title("🏀 NBA Edge Finder")
st.caption("Market-adjusted • Situational edges only • Realistic 1-3%")

st.sidebar.header("⚙️ Settings")
st.sidebar.markdown("**Edge Thresholds**")
st.sidebar.write("• <1% = No edge")
st.sidebar.write("• 1-1.8% = Slight")
st.sidebar.write("• 1.8-2.5% = Lean")
st.sidebar.write("• 2.5%+ = Edge (rare)")
st.sidebar.markdown("---")
st.sidebar.write("**Haircut: 40%**")
st.sidebar.caption("We reduce edges by 40%")

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

markets = fetch_markets()
rest = fetch_rest()

st.sidebar.markdown("---")
st.sidebar.write(f"**Games:** {len(markets)}")

# Calculate all edges
results = []
for g in markets:
    if not g['is_today']:
        continue
    travel = calc_travel(g['away'], g['home'])
    analysis = calc_edge(g['home'], g['away'], g['home_prob'], rest.get(g['home'], 2), rest.get(g['away'], 2), 0, 0, travel)
    results.append({**g, **analysis})

# Sort by absolute edge
results.sort(key=lambda x: abs(x.get('adj_edge', 0)), reverse=True)

# TOP EDGES
st.markdown("---")
st.subheader("🎯 Today's Edges")

edges_found = [r for r in results if abs(r['adj_edge']) >= 1.0]
if edges_found:
    cols = st.columns(min(3, len(edges_found)))
    for i, r in enumerate(edges_found[:3]):
        with cols[i]:
            team = r['home'] if r['adj_edge'] > 0 else r['away']
            mkt = r['home_prob'] if r['adj_edge'] > 0 else r['away_prob']
            color = "#22c55e" if abs(r['adj_edge']) >= 1.8 else "#888"
            st.markdown(f'''
            <div style="background:rgba(34,197,94,0.1); border-left:4px solid {color}; border-radius:8px; padding:16px; margin:8px 0;">
                <div style="font-size:1.4rem; font-weight:700;">{team}</div>
                <div style="font-size:1.6rem; font-weight:800; color:{color};">+{abs(r["adj_edge"]):.1f}%</div>
                <div style="color:#888; font-size:0.85rem;">{r["game_date"]} • {r["away"]} @ {r["home"]}</div>
                <div style="color:#666; font-size:0.75rem;">{r["rec"]} • Market: {mkt:.0f}%</div>
            </div>
            ''', unsafe_allow_html=True)
else:
    st.info("✅ No actionable edges today. Market is efficient.")

st.caption("💡 Edges are 1-3%. If a model shows 10%+, it's broken.")

# GAME LIST
st.markdown("---")
st.subheader("📋 All Games")

for r in results:
    edge = r['adj_edge']
    ind = "🟢" if abs(edge) >= 1.8 else ("🟡" if abs(edge) >= 1.0 else "⚪")
    
    with st.expander(f"{ind} {r['game_date']} | {r['away']} @ {r['home']} | Edge: {edge:+.1f}% | {r['rec']}"):
        st.write(f"**Market:** {r['home']} {r['home_prob']:.0f}% | {r['away']} {r['away_prob']:.0f}%")
        
        c1, c2 = st.columns(2)
        with c1:
            h_inj = st.select_slider(f"🏥 {r['home']}", [0,1,2,3], 0, format_func=lambda x: ["Full","Minor","GTD","OUT"][x], key=f"h_{r['ticker']}")
        with c2:
            a_inj = st.select_slider(f"🏥 {r['away']}", [0,1,2,3], 0, format_func=lambda x: ["Full","Minor","GTD","OUT"][x], key=f"a_{r['ticker']}")
        
        # Recalculate with injuries
        new_analysis = calc_edge(r['home'], r['away'], r['home_prob'], r['h_rest'], r['a_rest'], h_inj, a_inj, r['travel'])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Raw Adj", f"{new_analysis['raw_edge']:+.1f}%")
        c2.metric("After Haircut", f"{new_analysis['adj_edge']:+.1f}%")
        c3.metric("Final Edge", f"{new_analysis['adj_edge']:+.1f}%")
        c4.metric("Rec", new_analysis['rec'])
        
        with st.expander("📊 Factors"):
            for k, v in new_analysis['factors'].items():
                st.write(f"• {k}: {v:+.2f}%")
            st.write(f"**Raw total:** {new_analysis['raw_edge']:+.2f}%")
            st.write(f"**After 40% haircut:** {new_analysis['adj_edge']:+.2f}%")

st.markdown("---")
st.caption("⚠️ Realistic edges are 1-3%. Pass 90% of games. Markets are efficient.")
