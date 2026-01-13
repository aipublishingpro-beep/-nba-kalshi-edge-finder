import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

if "positions" not in st.session_state:
    st.session_state.positions = []

# ========== SIDEBAR LEGEND ==========
with st.sidebar:
    st.header("📖 LEGEND")
    st.subheader("⚡ 12-Factor Edge")
    st.markdown("""
    **Edge > +10%** → HIGH confidence  
    **Edge +5 to +10%** → MEDIUM confidence  
    **Edge < +5%** → NO EDGE
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
    **Score 2** → TIRED 🟡  
    **Score 0-1** → Fresh
    """)
    st.divider()
    st.caption("v11.8")

# ========== TEAM DATA ==========
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

TEAM_STATS = {
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "ft_rate": 0.26, "reb_rate": 49.5, "three_pct": 36.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast"},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "ft_rate": 0.24, "reb_rate": 51.2, "three_pct": 38.5, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic"},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "ft_rate": 0.23, "reb_rate": 48.8, "three_pct": 35.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic"},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "ft_rate": 0.25, "reb_rate": 48.2, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.22, "division": "Southeast"},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "ft_rate": 0.24, "reb_rate": 49.8, "three_pct": 35.2, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Central"},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "ft_rate": 0.27, "reb_rate": 52.5, "three_pct": 36.8, "home_win_pct": 0.75, "away_win_pct": 0.58, "division": "Central"},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "ft_rate": 0.26, "reb_rate": 50.2, "three_pct": 37.5, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southwest"},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "ft_rate": 0.25, "reb_rate": 51.8, "three_pct": 36.5, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest"},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 34.2, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central"},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "ft_rate": 0.23, "reb_rate": 50.5, "three_pct": 38.2, "home_win_pct": 0.65, "away_win_pct": 0.42, "division": "Pacific"},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "ft_rate": 0.28, "reb_rate": 50.8, "three_pct": 35.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "ft_rate": 0.26, "reb_rate": 49.2, "three_pct": 37.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Central"},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "ft_rate": 0.25, "reb_rate": 50.0, "three_pct": 36.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Pacific"},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "ft_rate": 0.27, "reb_rate": 51.0, "three_pct": 35.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific"},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "ft_rate": 0.26, "reb_rate": 52.2, "three_pct": 35.2, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southwest"},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "ft_rate": 0.24, "reb_rate": 50.8, "three_pct": 36.5, "home_win_pct": 0.65, "away_win_pct": 0.45, "division": "Southeast"},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "ft_rate": 0.28, "reb_rate": 51.5, "three_pct": 37.2, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Central"},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "ft_rate": 0.25, "reb_rate": 52.8, "three_pct": 36.2, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Northwest"},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "ft_rate": 0.27, "reb_rate": 50.5, "three_pct": 36.8, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "ft_rate": 0.25, "reb_rate": 51.2, "three_pct": 37.0, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic"},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "ft_rate": 0.26, "reb_rate": 52.0, "three_pct": 37.5, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest"},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "ft_rate": 0.26, "reb_rate": 51.5, "three_pct": 35.5, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast"},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "ft_rate": 0.28, "reb_rate": 50.2, "three_pct": 36.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Atlantic"},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "ft_rate": 0.25, "reb_rate": 49.8, "three_pct": 36.8, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific"},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "ft_rate": 0.24, "reb_rate": 48.5, "three_pct": 35.0, "home_win_pct": 0.40, "away_win_pct": 0.25, "division": "Northwest"},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "ft_rate": 0.25, "reb_rate": 49.5, "three_pct": 36.5, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific"},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "ft_rate": 0.26, "reb_rate": 49.0, "three_pct": 34.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest"},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "ft_rate": 0.24, "reb_rate": 49.5, "three_pct": 35.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Atlantic"},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "ft_rate": 0.25, "reb_rate": 48.0, "three_pct": 35.2, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Northwest"},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "ft_rate": 0.27, "reb_rate": 48.8, "three_pct": 34.5, "home_win_pct": 0.38, "away_win_pct": 0.25, "division": "Southeast"}
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young"], "Boston": ["Jayson Tatum", "Jaylen Brown"], "Brooklyn": ["Mikal Bridges"],
    "Charlotte": ["LaMelo Ball"], "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Desmond Bane"], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Julius Randle"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"], "Portland": ["Anfernee Simons"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"], "San Antonio": ["Victor Wembanyama"],
    "Toronto": ["Scottie Barnes"], "Utah": ["Lauri Markkanen"], "Washington": ["Jordan Poole"]
}

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

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
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "")
                injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

def get_injury_score(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    score = 0
    out_stars = []
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            score += 4.0 if is_star else 1.0
            if is_star:
                out_stars.append(name)
        elif "DAY-TO-DAY" in status or "GTD" in status or "QUESTIONABLE" in status:
            score += 2.5 if is_star else 0.5
    return score, out_stars

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

def calc_12_factor_edge(home_team, away_team, home_rest, away_rest, home_inj, away_inj, kalshi_price, weights):
    home = TEAM_STATS.get(home_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    away = TEAM_STATS.get(away_team, {"pace": 100, "def_rank": 15, "net_rating": 0, "ft_rate": 0.25, "reb_rate": 50, "three_pct": 36, "home_win_pct": 0.5, "away_win_pct": 0.5, "division": ""})
    home_loc = TEAM_LOCATIONS.get(home_team, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away_team, (0, 0))
    travel_miles = calc_distance(away_loc, home_loc)
    
    rest_diff = home_rest - away_rest
    rest_score = max(-6, min(6, rest_diff * 2))
    def_score = (away['def_rank'] - home['def_rank']) * 0.15
    injury_score = (away_inj - home_inj) * 1.5
    pace_diff = home['pace'] - away['pace']
    pace_score = pace_diff * 0.1 if home['net_rating'] > away['net_rating'] else -pace_diff * 0.1
    net_score = (home['net_rating'] - away['net_rating']) * 0.8
    travel_score = 2.5 if travel_miles > 1500 else (1.5 if travel_miles > 1000 else (0.75 if travel_miles > 500 else 0))
    split_score = (home['home_win_pct'] - 0.5) * 10 + (0.5 - away['away_win_pct']) * 10
    h2h_score = 1.5 if home.get('division') == away.get('division') and home.get('division') else 0
    altitude_score = 2.0 if home_team == "Denver" else 0
    ft_score = (home.get('ft_rate', 0.25) - away.get('ft_rate', 0.25)) * 20
    reb_score = (home.get('reb_rate', 50) - away.get('reb_rate', 50)) * 0.3
    three_score = (home.get('three_pct', 36) - away.get('three_pct', 36)) * 0.5
    home_court = 3.0
    
    weighted_spread = (
        home_court +
        rest_score * weights['rest'] +
        def_score * weights['defense'] +
        injury_score * weights['injury'] +
        pace_score * weights['pace'] +
        net_score * weights['net_rating'] +
        travel_score * weights['travel'] +
        split_score * weights['splits'] +
        h2h_score * weights['h2h'] +
        altitude_score * weights['altitude'] +
        ft_score * weights['ft'] +
        reb_score * weights['reb'] +
        three_score * weights['three']
    )
    
    home_win_prob = max(5, min(95, 50 + weighted_spread * 2.5))
    edge = home_win_prob - kalshi_price
    
    if edge > 0:
        ev = (home_win_prob / 100) * (100 - kalshi_price) - ((100 - home_win_prob) / 100) * kalshi_price
    else:
        ev = ((100 - home_win_prob) / 100) * kalshi_price - (home_win_prob / 100) * (100 - kalshi_price)
    
    return {
        'home_win_prob': round(home_win_prob, 1),
        'kalshi_price': kalshi_price,
        'edge': round(edge, 1),
        'expected_spread': round(weighted_spread, 1),
        'expected_value': round(ev, 2),
        'factors': {
            'rest': round(rest_score * weights['rest'], 2),
            'defense': round(def_score * weights['defense'], 2),
            'injury': round(injury_score * weights['injury'], 2),
            'pace': round(pace_score * weights['pace'], 2),
            'net_rating': round(net_score * weights['net_rating'], 2),
            'travel': round(travel_score * weights['travel'], 2),
            'splits': round(split_score * weights['splits'], 2),
            'h2h': round(h2h_score * weights['h2h'], 2),
            'altitude': round(altitude_score * weights['altitude'], 2),
            'ft': round(ft_score * weights['ft'], 2),
            'reb': round(reb_score * weights['reb'], 2),
            'three': round(three_score * weights['three'], 2),
            'home_court': home_court
        },
        'raw': {
            'rest_diff': rest_diff,
            'def_diff': round(away['def_rank'] - home['def_rank'], 1),
            'injury_diff': round(away_inj - home_inj, 1),
            'pace_diff': round(pace_diff, 1),
            'net_diff': round(home['net_rating'] - away['net_rating'], 1),
            'travel_miles': round(travel_miles, 0),
            'is_division': home.get('division') == away.get('division'),
            'is_denver': home_team == "Denver"
        }
    }

# ========== FETCH DATA ==========
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')} | v11.8")

if yesterday_teams:
    st.info(f"📅 **B2B Teams Today:** {', '.join(sorted(yesterday_teams)) if yesterday_teams else 'None'}")

# ========== 🔥 TOP PICKS - BEST ML EDGES ==========
st.subheader("🔥 TOP PICKS - BEST ML EDGES")

if game_list:
    default_weights = {'rest': 1.0, 'defense': 1.0, 'injury': 1.0, 'pace': 1.0, 'net_rating': 1.0, 
                       'travel': 1.0, 'splits': 1.0, 'h2h': 1.0, 'altitude': 1.0, 'ft': 1.0, 'reb': 1.0, 'three': 1.0}
    
    all_edges = []
    for game_key in game_list:
        parts = game_key.split("@")
        away_t = parts[0]
        home_t = parts[1]
        
        away_b2b = away_t in yesterday_teams
        home_b2b = home_t in yesterday_teams
        away_r = 0 if away_b2b else 1
        home_r = 0 if home_b2b else 1
        
        home_i, _ = get_injury_score(home_t, injuries)
        away_i, _ = get_injury_score(away_t, injuries)
        
        # Use 50 as neutral Kalshi price to find raw edge
        res = calc_12_factor_edge(home_t, away_t, home_r, away_r, home_i, away_i, 50, default_weights)
        
        edge_val = res['home_win_prob'] - 50  # How much model favors home
        if edge_val > 5:
            pick_team = home_t
            pick_edge = edge_val
            pick_side = "HOME"
        elif edge_val < -5:
            pick_team = away_t
            pick_edge = abs(edge_val)
            pick_side = "AWAY"
        else:
            pick_team = None
            pick_edge = 0
            pick_side = None
        
        if pick_team:
            all_edges.append({
                'game': game_key,
                'pick_team': pick_team,
                'pick_edge': pick_edge,
                'pick_side': pick_side,
                'home_win_prob': res['home_win_prob'],
                'spread': res['expected_spread'],
                'away_b2b': away_b2b,
                'home_b2b': home_b2b
            })
    
    # Sort by edge strength
    all_edges.sort(key=lambda x: x['pick_edge'], reverse=True)
    
    if all_edges:
        for pick in all_edges:
            conf = "HIGH" if pick['pick_edge'] > 10 else "MEDIUM"
            conf_color = "#00ff00" if conf == "HIGH" else "#ffff00"
            edge_color = "#00ff00" if pick['pick_side'] == "HOME" else "#ff4444"
            
            b2b_note = ""
            if pick['away_b2b']:
                b2b_note += f" 🔴 {pick['game'].split('@')[0]} B2B"
            if pick['home_b2b']:
                b2b_note += f" 🔴 {pick['game'].split('@')[1]} B2B"
            
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {edge_color};margin-bottom:10px'>
                <span style='color:{edge_color};font-size:1.8em;font-weight:bold'>🎯 BUY {pick['pick_team']} ML</span>
                <span style='color:{conf_color};font-size:1.1em;margin-left:15px'>{conf} (+{pick['pick_edge']:.0f}% edge)</span>
                <br><span style='color:#aaa;font-size:0.9em'>{pick['game'].replace('@', ' @ ')} | Model: {pick['home_win_prob']:.0f}% home | Spread: {pick['spread']:+.1f}{b2b_note}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("⚪ No strong ML edges today - all games within 5% margin")
else:
    st.info("No games today")

st.divider()

# ========== 1. ACTIVE POSITIONS ==========
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        side = pos['side']
        threshold = pos['threshold']
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
                status, color = "⏳", "#888888"
            
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{game_key.replace('@', ' @ ')}**<br><small>{game_status} | {total} pts</small>", unsafe_allow_html=True)
            c2.markdown(f"**{side} {threshold}**")
            c3.markdown(f"Proj: **{projected if projected else '—'}**")
            c4.markdown(f"<span style='color:{color};font-size:1.2em'><b>{status}</b></span>", unsafe_allow_html=True)
            if c5.button("❌", key=f"del_{idx}"):
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
    st.info("No positions yet. Find edge below ⬇️")

st.divider()

# ========== 2. FATIGUE SCANNER ==========
st.subheader("😴 FATIGUE SCANNER")

if games:
    fatigue_games = []
    for game_key, g in games.items():
        away = g['away_team']
        home = g['home_team']
        away_b2b = away in yesterday_teams
        home_b2b = home in yesterday_teams
        away_score = (2 if away_b2b else 0) + 1
        home_score = 2 if home_b2b else 0
        
        fatigue_games.append({
            "game": game_key, "away": away, "home": home,
            "away_b2b": away_b2b, "home_b2b": home_b2b,
            "away_score": away_score, "home_score": home_score,
            "is_blowout_risk": away_score >= 3 and home_score == 0,
            "is_both_tired": away_b2b and home_b2b,
            "is_denver": home == "Denver"
        })
    
    fatigue_games.sort(key=lambda x: (x['is_blowout_risk'], x['is_both_tired'], x['away_score']), reverse=True)
    edge_games = [g for g in fatigue_games if g['is_blowout_risk'] or g['is_both_tired'] or g['is_denver'] or g['away_score'] >= 3]
    
    if edge_games:
        for gf in edge_games:
            st.markdown(f"### 🏀 {gf['away']} @ {gf['home']}")
            if gf['is_blowout_risk']:
                st.success(f"🔥 **BLOWOUT RISK** — Fatigued {gf['away']} @ Fresh {gf['home']}. **BUY {gf['home']} ML**")
            elif gf['is_both_tired']:
                st.info("🟢 **BOTH TIRED** — Strong Under spot")
            if gf['is_denver']:
                st.warning("🏔️ **ALTITUDE** — Denver home")
            st.markdown("---")
    else:
        st.info("No fatigue edges today")
else:
    st.info("No games today")

st.divider()

# ========== 3. 12-FACTOR ANALYSIS ==========
st.subheader("🔬 12-FACTOR ANALYSIS")

with st.expander("⚙️ Adjust Factor Weights", expanded=False):
    wcol1, wcol2, wcol3 = st.columns(3)
    with wcol1:
        w_rest = st.slider("🛏️ Rest", 0.0, 2.0, 1.0, 0.1)
        w_def = st.slider("🛡️ Defense", 0.0, 2.0, 1.0, 0.1)
        w_inj = st.slider("🏥 Injuries", 0.0, 2.0, 1.0, 0.1)
        w_pace = st.slider("⚡ Pace", 0.0, 2.0, 1.0, 0.1)
    with wcol2:
        w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1)
        w_travel = st.slider("✈️ Travel", 0.0, 2.0, 1.0, 0.1)
        w_splits = st.slider("🏠 Splits", 0.0, 2.0, 1.0, 0.1)
        w_h2h = st.slider("⚔️ Division", 0.0, 2.0, 1.0, 0.1)
    with wcol3:
        w_altitude = st.slider("🏔️ Altitude", 0.0, 2.0, 1.0, 0.1)
        w_ft = st.slider("🎯 FT Rate", 0.0, 2.0, 1.0, 0.1)
        w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1)
        w_three = st.slider("🎯 3PT%", 0.0, 2.0, 1.0, 0.1)

weights = {
    'rest': w_rest, 'defense': w_def, 'injury': w_inj, 'pace': w_pace,
    'net_rating': w_net, 'travel': w_travel, 'splits': w_splits, 'h2h': w_h2h,
    'altitude': w_altitude, 'ft': w_ft, 'reb': w_reb, 'three': w_three
}

if game_list:
    fc1, fc2 = st.columns([3, 1])
    analyze_game = fc1.selectbox("Select Game", game_list, format_func=lambda x: x.replace("@", " @ "), key="analyze_game")
    kalshi_price = fc2.number_input("Kalshi Price ¢", 1, 99, 60, key="kalshi_price")
    
    if analyze_game:
        parts = analyze_game.split("@")
        away_team = parts[0]
        home_team = parts[1]
        
        away_b2b = away_team in yesterday_teams
        home_b2b = home_team in yesterday_teams
        away_rest = 0 if away_b2b else 1
        home_rest = 0 if home_b2b else 1
        
        home_inj, home_stars = get_injury_score(home_team, injuries)
        away_inj, away_stars = get_injury_score(away_team, injuries)
        
        result = calc_12_factor_edge(home_team, away_team, home_rest, away_rest, home_inj, away_inj, kalshi_price, weights)
        
        st.markdown(f"## 🏀 {away_team} @ {home_team}")
        
        if away_b2b or home_b2b:
            b2b_msg = []
            if away_b2b:
                b2b_msg.append(f"🔴 {away_team} B2B")
            if home_b2b:
                b2b_msg.append(f"🔴 {home_team} B2B")
            st.warning(" | ".join(b2b_msg))
        
        # MAIN RECOMMENDATION - CLEAR AS DAY
        edge = result['edge']
        if edge > 5:
            rec_text = f"🟢 BUY {home_team} ML"
            rec_color = "#00ff00"
        elif edge < -5:
            rec_text = f"🔴 BUY {away_team} ML"
            rec_color = "#ff4444"
        else:
            rec_text = "⚪ NO EDGE - SKIP"
            rec_color = "#888888"
        
        conf = "HIGH" if abs(edge) > 10 else ("MEDIUM" if abs(edge) > 5 else "LOW")
        conf_color = "#00ff00" if conf == "HIGH" else ("#ffff00" if conf == "MEDIUM" else "#888888")
        
        # BIG BOX WITH TEAM NAME
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:25px;border-radius:15px;text-align:center;border:2px solid {rec_color};margin-bottom:20px'>
            <span style='color:{rec_color};font-size:2.5em;font-weight:bold'>{rec_text}</span><br>
            <span style='color:{conf_color};font-size:1.3em'>{conf} CONFIDENCE</span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Model Win Prob", f"{result['home_win_prob']}%")
        col2.metric("Kalshi Price", f"{result['kalshi_price']}¢")
        col3.metric("Edge", f"{result['edge']:+.1f}%")
        
        col4, col5 = st.columns(2)
        col4.metric("Expected Spread", f"{result['expected_spread']:+.1f}")
        col5.metric("Expected Value", f"{result['expected_value']:+.2f}¢")
        
        with st.expander("📊 FACTOR BREAKDOWN", expanded=True):
            factors = result['factors']
            raw = result['raw']
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                st.markdown(f"• 🛏️ **Rest:** {factors['rest']:+.2f}")
                st.markdown(f"• 🛡️ **Defense:** {factors['defense']:+.2f}")
                st.markdown(f"• 🏥 **Injuries:** {factors['injury']:+.2f}")
                st.markdown(f"• ⚡ **Pace:** {factors['pace']:+.2f}")
                st.markdown(f"• 📊 **Net Rating:** {factors['net_rating']:+.2f}")
                st.markdown(f"• ✈️ **Travel:** {factors['travel']:+.2f}")
            with bcol2:
                st.markdown(f"• 🏠 **Splits:** {factors['splits']:+.2f}")
                st.markdown(f"• ⚔️ **Division:** {factors['h2h']:+.2f}")
                st.markdown(f"• 🏔️ **Altitude:** {factors['altitude']:+.2f}")
                st.markdown(f"• 🎯 **FT Rate:** {factors['ft']:+.2f}")
                st.markdown(f"• 🏀 **Rebounding:** {factors['reb']:+.2f}")
                st.markdown(f"• 🎯 **3PT%:** {factors['three']:+.2f}")
            st.markdown(f"• 🏠 **Home Court:** +{factors['home_court']:.1f}")
            st.markdown(f"**TOTAL: {result['expected_spread']:+.1f}**")
        
        st.markdown("---")
        st.markdown("**Add Total Position:**")
        qc1, qc2, qc3, qc4 = st.columns([1, 2, 1, 1])
        q_side = qc1.selectbox("Side", ["NO", "YES"], key="q_side")
        q_threshold = qc2.number_input("Threshold", 200.0, 280.0, 235.5, 0.5, key="q_thresh")
        q_price = qc3.number_input("Price ¢", 1, 99, 75, key="q_price")
        q_contracts = qc4.number_input("Contracts", 1, 1000, 100, key="q_contracts")
        
        if st.button(f"➕ ADD {q_side} {q_threshold} TO TRACKER", type="primary", use_container_width=True):
            st.session_state.positions.append({
                "game": analyze_game, "side": q_side, "threshold": q_threshold,
                "price": q_price, "contracts": q_contracts
            })
            st.rerun()
else:
    st.warning("No games available")

st.divider()

# ========== 4. CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 18, 24], index=1, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

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

# ========== 5. PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({"game": gk, "pace": pace, "proj": proj, "total": g['total'], "mins": mins,
                         "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"})

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

# ========== 6. ALL GAMES ==========
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
st.caption("⚠️ For entertainment only. Not financial advice. You may lose money.")
