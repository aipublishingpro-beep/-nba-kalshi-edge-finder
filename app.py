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
    "Atlanta": {"net_rating": -1.5, "def_rank": 22, "pace": 100.2, "ppg": 118.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pct": 0.355, "ft_rate": 0.25, "reb_rate": 50.2},
    "Boston": {"net_rating": 10.5, "def_rank": 2, "pace": 98.5, "ppg": 120.8, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic", "three_pct": 0.385, "ft_rate": 0.28, "reb_rate": 52.5},
    "Brooklyn": {"net_rating": -5.2, "def_rank": 25, "pace": 99.8, "ppg": 108.5, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.345, "ft_rate": 0.23, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -6.8, "def_rank": 27, "pace": 101.5, "ppg": 106.8, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 49.2},
    "Chicago": {"net_rating": -3.5, "def_rank": 20, "pace": 98.2, "ppg": 112.5, "home_win_pct": 0.45, "away_win_pct": 0.32, "division": "Central", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 50.0},
    "Cleveland": {"net_rating": 9.8, "def_rank": 3, "pace": 97.5, "ppg": 118.5, "home_win_pct": 0.76, "away_win_pct": 0.62, "division": "Central", "three_pct": 0.372, "ft_rate": 0.27, "reb_rate": 53.2},
    "Dallas": {"net_rating": 3.2, "def_rank": 12, "pace": 99.5, "ppg": 117.2, "home_win_pct": 0.58, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.365, "ft_rate": 0.26, "reb_rate": 50.8},
    "Denver": {"net_rating": 5.5, "def_rank": 8, "pace": 98.8, "ppg": 118.8, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.25, "reb_rate": 52.0},
    "Detroit": {"net_rating": -4.8, "def_rank": 24, "pace": 100.5, "ppg": 110.2, "home_win_pct": 0.40, "away_win_pct": 0.28, "division": "Central", "three_pct": 0.340, "ft_rate": 0.23, "reb_rate": 49.5},
    "Golden State": {"net_rating": 2.8, "def_rank": 14, "pace": 99.2, "ppg": 117.5, "home_win_pct": 0.68, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.378, "ft_rate": 0.24, "reb_rate": 50.5},
    "Houston": {"net_rating": 1.5, "def_rank": 15, "pace": 100.8, "ppg": 114.2, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest", "three_pct": 0.352, "ft_rate": 0.28, "reb_rate": 51.8},
    "Indiana": {"net_rating": 0.5, "def_rank": 28, "pace": 103.2, "ppg": 123.5, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Central", "three_pct": 0.368, "ft_rate": 0.25, "reb_rate": 49.8},
    "LA Clippers": {"net_rating": -1.2, "def_rank": 18, "pace": 98.5, "ppg": 110.8, "home_win_pct": 0.48, "away_win_pct": 0.35, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 50.2},
    "LA Lakers": {"net_rating": 2.5, "def_rank": 13, "pace": 99.8, "ppg": 115.2, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Pacific", "three_pct": 0.358, "ft_rate": 0.27, "reb_rate": 51.5},
    "Memphis": {"net_rating": 4.2, "def_rank": 10, "pace": 101.2, "ppg": 119.8, "home_win_pct": 0.65, "away_win_pct": 0.48, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.26, "reb_rate": 52.8},
    "Miami": {"net_rating": 0.8, "def_rank": 11, "pace": 97.8, "ppg": 110.5, "home_win_pct": 0.58, "away_win_pct": 0.38, "division": "Southeast", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.8},
    "Milwaukee": {"net_rating": 3.5, "def_rank": 16, "pace": 99.5, "ppg": 118.2, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Central", "three_pct": 0.365, "ft_rate": 0.28, "reb_rate": 51.2},
    "Minnesota": {"net_rating": 5.8, "def_rank": 4, "pace": 98.2, "ppg": 112.8, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Northwest", "three_pct": 0.358, "ft_rate": 0.26, "reb_rate": 53.5},
    "New Orleans": {"net_rating": -2.5, "def_rank": 23, "pace": 100.5, "ppg": 113.8, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.27, "reb_rate": 50.5},
    "New York": {"net_rating": 6.2, "def_rank": 7, "pace": 98.8, "ppg": 118.5, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Atlantic", "three_pct": 0.368, "ft_rate": 0.26, "reb_rate": 51.8},
    "Oklahoma City": {"net_rating": 11.2, "def_rank": 1, "pace": 99.8, "ppg": 120.2, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest", "three_pct": 0.375, "ft_rate": 0.27, "reb_rate": 52.2},
    "Orlando": {"net_rating": 4.5, "def_rank": 5, "pace": 97.5, "ppg": 110.5, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southeast", "three_pct": 0.342, "ft_rate": 0.25, "reb_rate": 52.5},
    "Philadelphia": {"net_rating": -0.5, "def_rank": 19, "pace": 98.2, "ppg": 112.8, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic", "three_pct": 0.358, "ft_rate": 0.29, "reb_rate": 50.8},
    "Phoenix": {"net_rating": 1.8, "def_rank": 17, "pace": 98.5, "ppg": 114.8, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific", "three_pct": 0.362, "ft_rate": 0.25, "reb_rate": 50.2},
    "Portland": {"net_rating": -7.5, "def_rank": 29, "pace": 100.2, "ppg": 106.5, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pct": 0.338, "ft_rate": 0.23, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.8, "def_rank": 26, "pace": 100.8, "ppg": 116.2, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Pacific", "three_pct": 0.355, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -5.5, "def_rank": 21, "pace": 99.5, "ppg": 110.2, "home_win_pct": 0.42, "away_win_pct": 0.25, "division": "Southwest", "three_pct": 0.345, "ft_rate": 0.25, "reb_rate": 50.5},
    "Toronto": {"net_rating": -4.2, "def_rank": 23, "pace": 99.2, "ppg": 111.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic", "three_pct": 0.348, "ft_rate": 0.24, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.2, "def_rank": 30, "pace": 100.5, "ppg": 106.2, "home_win_pct": 0.30, "away_win_pct": 0.15, "division": "Northwest", "three_pct": 0.335, "ft_rate": 0.22, "reb_rate": 48.2},
    "Washington": {"net_rating": -9.5, "def_rank": 30, "pace": 101.2, "ppg": 109.5, "home_win_pct": 0.25, "away_win_pct": 0.12, "division": "Southeast", "three_pct": 0.332, "ft_rate": 0.23, "reb_rate": 47.8}
}

CITY_COORDS = {
    "Atlanta": (33.749, -84.388), "Boston": (42.361, -71.057), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -104.999), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.980, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

# APP PURPOSE: Edge finder only - not a Kalshi bridge

def calc_travel(away, home):
    if away not in CITY_COORDS or home not in CITY_COORDS:
        return 0
    lat1, lon1 = CITY_COORDS[away]
    lat2, lon2 = CITY_COORDS[home]
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1)/2)**2
    return 3956 * 2 * math.asin(math.sqrt(a))

def calc_edge(home, away, price, hr, ar, hi, ai, travel, ref, w):
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    t = 0
    t += (hr - ar) * 2.5 * w.get('rest', 1)
    t += ((ar == 0) * 8 - (hr == 0) * 8) * w.get('b2b', 1)
    t += (aws.get('def_rank', 15) - hs.get('def_rank', 15)) * 0.8 * w.get('def', 1)
    t += (ai - hi) * 3 * w.get('inj', 1)
    t += (hs.get('net_rating', 0) - aws.get('net_rating', 0)) * 0.5 * w.get('net', 1)
    t += min(travel / 500, 3) * w.get('travel', 1)
    t += ((hs.get('home_win_pct', 0.5) - 0.5) * 20 - (aws.get('away_win_pct', 0.5) - 0.5) * 20) * w.get('home', 1)
    t += (5 if hs.get('division') == aws.get('division') else 0) * w.get('h2h', 1)
    t += (ref - 1) * 5 * w.get('refs', 1)
    t += (hs.get('ft_rate', 0.25) - aws.get('ft_rate', 0.25)) * 40 * w.get('ft', 1)
    t += (hs.get('reb_rate', 50) - aws.get('reb_rate', 50)) * 0.5 * w.get('reb', 1)
    t += (hs.get('three_pct', 0.35) - aws.get('three_pct', 0.35)) * 100 * w.get('3pt', 1)
    prob = max(25, min(75, 50 + t))
    edge = prob - price
    if edge > 7: rec, conf = "BUY YES", "HIGH"
    elif edge > 4: rec, conf = "BUY YES", "MED"
    elif edge < -7: rec, conf = "BUY NO", "HIGH"
    elif edge < -4: rec, conf = "BUY NO", "MED"
    else: rec, conf = "PASS", "LOW"
    return {'prob': round(prob, 1), 'edge': round(edge, 1), 'rec': rec, 'conf': conf}

def calc_kelly(prob, price, bank, frac):
    try:
        p = prob / 100
        odds = (100 - price) / price if price > 0 else 0
        k = (p * odds - (1 - p)) / odds if odds > 0 else 0
        return round(bank * max(0, k * frac), 2)
    except:
        return 0

def parse_teams(ticker):
    try:
        code = ticker.split('-')[1]
        return KALSHI_ABBREV_MAP.get(code[-3:].upper()), KALSHI_ABBREV_MAP.get(code[-6:-3].upper())
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_markets():
    out = {'ml': [], 'tot': [], 'spr': []}
    today = datetime.now().date()
    for key, series in [('ml', 'KXNBAGAME'), ('tot', 'KXNBATOTAL'), ('spr', 'KXNBASPREAD')]:
        try:
            r = requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series}&status=open", timeout=10)
            for m in r.json().get('markets', []):
                ticker = m.get('ticker', '')
                home, away = parse_teams(ticker)
                if not home or not away:
                    continue
                ct = m.get('close_time', '')
                try:
                    dt = datetime.fromisoformat(ct.replace('Z', '+00:00')).replace(tzinfo=None)
                    if dt.date() < today:
                        continue
                    date_str = dt.strftime('%b %d')
                except:
                    continue
                info = {'ticker': ticker, 'home': home, 'away': away, 'price': m.get('yes_ask', 50), 'date': date_str, 'ct': ct}
                if key == 'tot':
                    info['line'] = m.get('floor_strike', 220)
                out[key].append(info)
        except:
            pass
    for k in out:
        out[k].sort(key=lambda x: x.get('ct', ''))
    return out

@st.cache_data(ttl=300)
def fetch_rest():
    rest = {}
    try:
        now = datetime.now()
        r = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=settled&limit=200", timeout=10)
        for m in r.json().get('markets', []):
            ticker, ct = m.get('ticker', ''), m.get('close_time', '')
            if not ct or '-' not in ticker:
                continue
            try:
                days = (now - datetime.fromisoformat(ct.replace('Z', '+00:00')).replace(tzinfo=None)).days
                if 0 <= days <= 5:
                    code = ticker.split('-')[1]
                    for abbr in [code[-6:-3].upper(), code[-3:].upper()]:
                        team = KALSHI_ABBREV_MAP.get(abbr)
                        if team and team not in rest:
                            rest[team] = days
            except:
                pass
    except:
        pass
    return rest

st.title("🏀 NBA Kalshi Edge Finder")
st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')} | 🟢 BUY YES | 🔴 BUY NO")

st.sidebar.header("⚙️ 12 Sauces")
with st.sidebar.expander("🏀 Core", expanded=True):
    w_rest = st.slider("🛏️ Rest", 0.0, 2.0, 1.0, 0.1)
    w_b2b = st.slider("⏰ B2B", 0.0, 2.0, 1.0, 0.1)
    w_def = st.slider("🛡️ Defense", 0.0, 2.0, 1.0, 0.1)
    w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1)
    w_pace = st.slider("🏃 Pace", 0.0, 2.0, 1.0, 0.1)
    w_net = st.slider("📊 Net Rtg", 0.0, 2.0, 1.0, 0.1)
with st.sidebar.expander("🎯 Advanced", expanded=True):
    w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1)
    w_home = st.slider("🏠 Home", 0.0, 2.0, 1.0, 0.1)
    w_h2h = st.slider("⚔️ Division", 0.0, 2.0, 1.0, 0.1)
    w_refs = st.slider("👨‍⚖️ Refs", 0.0, 2.0, 1.0, 0.1)
    w_ft = st.slider("🎯 FT", 0.0, 2.0, 1.0, 0.1)
    w_reb = st.slider("🏀 Reb", 0.0, 2.0, 1.0, 0.1)
    w_3pt = st.slider("🎯 3PT", 0.0, 2.0, 1.0, 0.1)

w = {'rest': w_rest, 'b2b': w_b2b, 'def': w_def, 'inj': w_inj, 'pace': w_pace, 'net': w_net, 'travel': w_travel, 'home': w_home, 'h2h': w_h2h, 'refs': w_refs, 'ft': w_ft, 'reb': w_reb, '3pt': w_3pt}

st.sidebar.markdown("---")
bank = st.sidebar.number_input("💰 Bankroll", 100, 100000, 1000, 100)
kf = st.sidebar.slider("Kelly %", 0.1, 1.0, 0.25, 0.05)
min_e = st.sidebar.slider("Min Edge", 1.0, 15.0, 5.0, 0.5)
ref_bias = st.sidebar.slider("Ref Bias", 0.0, 2.0, 1.0, 0.1)
def_hr = st.sidebar.number_input("Def Home Rest", 1, 5, 2)
def_ar = st.sidebar.number_input("Def Away Rest", 1, 5, 2)

mkts = fetch_markets()
rest = fetch_rest()

edges = []
for g in mkts['ml']:
    home, away, price = g['home'], g['away'], g['price']
    hr, ar = rest.get(home, def_hr), rest.get(away, def_ar)
    a = calc_edge(home, away, price, hr, ar, 0, 0, calc_travel(away, home), ref_bias, w)
    if a['rec'] != 'PASS' and abs(a['edge']) >= min_e:
        team = home if a['rec'] == 'BUY YES' else away
        prob = a['prob'] if a['rec'] == 'BUY YES' else 100 - a['prob']
        px = price if a['rec'] == 'BUY YES' else 100 - price
        edges.append({'t': 'ML', 'g': f"{away} @ {home}", 'd': g['date'], 'e': abs(a['edge']), 'team': team, 'amt': calc_kelly(prob, px, bank, kf), 'c': '🟢' if a['rec'] == 'BUY YES' else '🔴'})

for g in mkts['tot']:
    home, away, price, line = g['home'], g['away'], g['price'], g.get('line', 220)
    hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
    proj = (hs.get('ppg', 110) + aws.get('ppg', 110)) * ((hs.get('pace', 100) + aws.get('pace', 100)) / 200)
    diff = proj - line
    if abs(diff) >= min_e:
        rec = "OVER" if diff > 0 else "UNDER"
        edges.append({'t': 'TOT', 'g': f"{away} @ {home}", 'd': g['date'], 'e': abs(diff), 'team': f"{rec} {line}", 'amt': calc_kelly(50 + abs(diff), price if diff > 0 else 100 - price, bank, kf), 'c': '🟢' if diff > 0 else '🔴'})

for g in mkts['spr']:
    home, away, price = g['home'], g['away'], g['price']
    diff = 50 - price
    if abs(diff) >= min_e:
        team = f"{home} COVERS" if diff > 0 else f"{away} COVERS"
        edges.append({'t': 'SPR', 'g': f"{away} @ {home}", 'd': g['date'], 'e': abs(diff), 'team': team, 'amt': calc_kelly(50 + abs(diff), price if diff > 0 else 100 - price, bank, kf), 'c': '🟢' if diff > 0 else '🔴'})

edges.sort(key=lambda x: x['e'], reverse=True)

st.subheader("🔥 TOP 3 EDGES")
if edges:
    for i, e in enumerate(edges[:3]):
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.markdown(f"**#{i+1} {e['c']} [{e['t']}] {e['g']}**")
        c1.caption(f"{e['d']} | Edge: {e['e']:.1f}%")
        c2.markdown(f"**→ {e['team']}**")
        c3.metric("BET", f"${e['amt']:.0f}")
else:
    st.info("No edges found today")

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📈 Moneyline", "📊 Totals", "📉 Spreads"])

with tab1:
    for g in mkts['ml'][:15]:
        home, away, price = g['home'], g['away'], g['price']
        hr, ar = rest.get(home, def_hr), rest.get(away, def_ar)
        a = calc_edge(home, away, price, hr, ar, 0, 0, calc_travel(away, home), ref_bias, w)
        ind = "🟢" if a['rec'] == 'BUY YES' else "🔴" if a['rec'] == 'BUY NO' else "⚪"
        with st.expander(f"{ind} {away} @ {home} | {g['date']} | {price}¢ | Edge: {a['edge']:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Model", f"{a['prob']}%")
            c1.metric("Kalshi", f"{price}¢")
            c2.metric("Edge", f"{a['edge']:+.1f}%")
            c2.metric("Conf", a['conf'])
            if a['rec'] != 'PASS' and abs(a['edge']) >= min_e:
                team = home if a['rec'] == 'BUY YES' else away
                prob = a['prob'] if a['rec'] == 'BUY YES' else 100 - a['prob']
                px = price if a['rec'] == 'BUY YES' else 100 - price
                c3.markdown(f"**{a['rec']}**")
                c3.metric("Bet", f"${calc_kelly(prob, px, bank, kf):.0f}")

with tab2:
    for g in mkts['tot'][:15]:
        home, away, price, line = g['home'], g['away'], g['price'], g.get('line', 220)
        hs, aws = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
        proj = (hs.get('ppg', 110) + aws.get('ppg', 110)) * ((hs.get('pace', 100) + aws.get('pace', 100)) / 200)
        diff = proj - line
        ind = "🟢" if diff > min_e else "🔴" if diff < -min_e else "⚪"
        with st.expander(f"{ind} {away} @ {home} | Line: {line} | Proj: {proj:.0f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Line", str(line))
            c1.metric("Proj", f"{proj:.0f}")
            c2.metric("Diff", f"{diff:+.1f}")
            if abs(diff) >= min_e:
                rec = "OVER" if diff > 0 else "UNDER"
                c3.markdown(f"**BUY {rec}**")
                c3.metric("Bet", f"${calc_kelly(50 + abs(diff), price if diff > 0 else 100 - price, bank, kf):.0f}")

with tab3:
    for g in mkts['spr'][:15]:
        home, away, price = g['home'], g['away'], g['price']
        diff = 50 - price
        ind = "🟢" if diff > min_e else "🔴" if diff < -min_e else "⚪"
        with st.expander(f"{ind} {away} @ {home} | {price}¢ | Edge: {diff:+.1f}%"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Price", f"{price}¢")
            c2.metric("Edge", f"{diff:+.1f}%")
            if abs(diff) >= min_e:
                team = home if diff > 0 else away
                c3.markdown(f"**{team} COVERS**")
                c3.metric("Bet", f"${calc_kelly(50 + abs(diff), price if diff > 0 else 100 - price, bank, kf):.0f}")

with st.expander("🔧 Debug"):
    st.write(f"**Today:** {datetime.now().date()}")
    st.write(f"**Games:** ML={len(mkts['ml'])}, TOT={len(mkts['tot'])}, SPR={len(mkts['spr'])}")
    st.write(f"**Edges:** {len(edges)}")
