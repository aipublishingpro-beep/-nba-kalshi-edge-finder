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
    
    st.subheader("⚡ 12-Factor Score")
    st.markdown("""
    🟢 **7-10** → STRONG — Size up  
    🟢 **5-6** → GOOD — Standard  
    🟡 **3-4** → LEAN — Small size  
    🔴 **0-2** → SKIP — No edge
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
    *(Back-to-back + Road = prime NO target)*
    
    **Score 2** → TIRED 🟡  
    *(Back-to-back only or Road only)*
    
    **Score 0-1** → Fresh  
    *(No fatigue edge)*
    """)
    
    st.markdown("""
    **Factors:**  
    • Back-to-back (played yesterday) = +2  
    • Road game = +1  
    • Home court = +2 (for home team ML)
    """)
    
    st.divider()
    
    st.subheader("Matchup Types")
    st.markdown("""
    🏠 **HOME COURT**  
    *Home team +2 pts — 55-60% historical win rate*
    
    🟢 **BOTH TIRED**  
    *Both teams fatigued = pace drags, sloppy game, STRONG Under*
    
    🔥 **BLOWOUT RISK**  
    *Fatigued @ Fresh Home = Skip NO, consider ML on fresh home team*
    
    🏔️ **ALTITUDE**  
    *Denver home = visitors fatigue at 5,280 ft, lean Under*
    
    ⚡ **RESTED**  
    *3+ days rest = team comes out hot, Over risk*
    
    🏆 **DIVISION RIVALS**  
    *Same division = physical game, lean Under*
    
    ⚪ **NEUTRAL**  
    *Fresh vs Fresh = no fatigue edge*
    """)
    
    st.divider()
    
    st.subheader("Pace Benchmarks")
    st.markdown("""
    🟢 **SLOW** → Under 4.5/min  
    *(Good NO spot)*
    
    🟡 **AVG** → 4.5 - 4.8/min  
    *(Neutral)*
    
    🟠 **FAST** → 4.8 - 5.2/min  
    *(Caution for NO)*
    
    🔴 **SHOOTOUT** → Over 5.2/min  
    *(Avoid NO, consider YES)*
    """)
    
    st.divider()
    
    st.subheader("Pace Edge (NO bets)")
    st.markdown("""
    **+1.0+** → Comfortable 🟢  
    **+0.5 to +1.0** → Okay 🟡  
    **0 to +0.5** → Tight 🟠  
    **Negative** → Underwater 🔴
    """)
    
    st.divider()
    
    st.subheader("Status")
    st.markdown("""
    🟢 VERY SAFE → +15 cushion  
    🟢 LOOKING GOOD → +8 to +15  
    🟡 ON TRACK → +3 to +8  
    🟠 TIGHT → -3 to +3  
    🔴 DANGER → -10 to -3  
    🔴 LIKELY LOSS → Under -10
    """)
    
    st.divider()
    st.caption("v11.1")

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
    "Atlanta": ["Trae Young"],
    "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Brooklyn": ["Mikal Bridges"],
    "Charlotte": ["LaMelo Ball"],
    "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham"],
    "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Desmond Bane"],
    "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"],
    "New York": ["Jalen Brunson", "Julius Randle"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
    "Portland": ["Anfernee Simons"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "San Antonio": ["Victor Wembanyama"],
    "Toronto": ["Scottie Barnes"],
    "Utah": ["Lauri Markkanen"],
    "Washington": ["Jordan Poole"]
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
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
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

def calc_12_factor_score(home, away, home_rest, away_rest, home_inj, away_inj, bet_side="NO"):
    hs = TEAM_STATS.get(home, {})
    aws = TEAM_STATS.get(away, {})
    
    factors = {}
    breakdown = []
    
    # 1. REST (0-1.5 pts)
    rest_score = 0
    if home_rest == 0:
        rest_score += 0.75
        breakdown.append(f"🔴 {home} B2B +0.75")
    if away_rest == 0:
        rest_score += 0.75
        breakdown.append(f"🔴 {away} B2B +0.75")
    factors["rest"] = rest_score
    
    # 2. DEFENSE (0-1.5 pts)
    home_def = hs.get("def_rank", 15)
    away_def = aws.get("def_rank", 15)
    avg_def = (home_def + away_def) / 2
    if avg_def <= 8:
        def_score = 1.5
        breakdown.append(f"🟢 Elite Def Matchup (avg #{avg_def:.0f}) +1.5")
    elif avg_def <= 15:
        def_score = 0.75
        breakdown.append(f"🟡 Good Def Matchup (avg #{avg_def:.0f}) +0.75")
    else:
        def_score = 0
        breakdown.append(f"⚪ Weak Def Matchup (avg #{avg_def:.0f}) +0")
    factors["defense"] = def_score
    
    # 3. INJURIES (0-2 pts)
    inj_total = home_inj + away_inj
    if inj_total >= 6:
        inj_score = 2.0
        breakdown.append(f"🔴 Heavy Injuries (impact {inj_total:.1f}) +2.0")
    elif inj_total >= 3:
        inj_score = 1.0
        breakdown.append(f"🟡 Moderate Injuries (impact {inj_total:.1f}) +1.0")
    else:
        inj_score = 0
        breakdown.append(f"⚪ Light Injuries (impact {inj_total:.1f}) +0")
    factors["injury"] = inj_score
    
    # 4. PACE (0-1 pt)
    home_pace = hs.get("pace", 100)
    away_pace = aws.get("pace", 100)
    avg_pace = (home_pace + away_pace) / 2
    if avg_pace < 98.5:
        pace_score = 1.0
        breakdown.append(f"🟢 Slow Pace ({avg_pace:.1f}) +1.0")
    elif avg_pace < 100:
        pace_score = 0.5
        breakdown.append(f"🟡 Avg Pace ({avg_pace:.1f}) +0.5")
    else:
        pace_score = 0
        breakdown.append(f"⚪ Fast Pace ({avg_pace:.1f}) +0")
    factors["pace"] = pace_score
    
    # 5. NET RATING (0-1 pt) - close matchup = lower scoring
    home_net = hs.get("net_rating", 0)
    away_net = aws.get("net_rating", 0)
    net_diff = abs(home_net - away_net)
    if net_diff < 3:
        net_score = 1.0
        breakdown.append(f"🟢 Close Matchup (diff {net_diff:.1f}) +1.0")
    elif net_diff < 6:
        net_score = 0.5
        breakdown.append(f"🟡 Moderate Gap (diff {net_diff:.1f}) +0.5")
    else:
        net_score = 0
        breakdown.append(f"⚪ Mismatch (diff {net_diff:.1f}) +0")
    factors["net_rating"] = net_score
    
    # 6. TRAVEL (0-0.75 pts)
    home_loc = TEAM_LOCATIONS.get(home, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away, (0, 0))
    travel = calc_distance(away_loc, home_loc)
    if travel > 1500:
        travel_score = 0.75
        breakdown.append(f"🟢 Long Travel ({travel:.0f} mi) +0.75")
    elif travel > 800:
        travel_score = 0.4
        breakdown.append(f"🟡 Med Travel ({travel:.0f} mi) +0.4")
    else:
        travel_score = 0
        breakdown.append(f"⚪ Short Travel ({travel:.0f} mi) +0")
    factors["travel"] = travel_score
    
    # 7. HOME/AWAY SPLITS (0-0.75 pts)
    home_pct = hs.get("home_win_pct", 0.5)
    away_pct = aws.get("away_win_pct", 0.5)
    split_edge = home_pct - away_pct
    if split_edge > 0.25:
        split_score = 0.75
        breakdown.append(f"🟢 Strong Split Edge ({split_edge:.0%}) +0.75")
    elif split_edge > 0.15:
        split_score = 0.4
        breakdown.append(f"🟡 Mod Split Edge ({split_edge:.0%}) +0.4")
    else:
        split_score = 0
        breakdown.append(f"⚪ No Split Edge ({split_edge:.0%}) +0")
    factors["splits"] = split_score
    
    # 8. DIVISION GAME (0-0.5 pts) - division games are tighter
    home_div = hs.get("division", "")
    away_div = aws.get("division", "")
    if home_div == away_div and home_div:
        div_score = 0.5
        breakdown.append(f"🏆 Division Rivalry +0.5")
    else:
        div_score = 0
        breakdown.append(f"⚪ Non-Division +0")
    factors["division"] = div_score
    
    # 9. 3PT% (0-0.75 pts) - bad shooters = lower scoring
    home_3pt = hs.get("three_pct", 36)
    away_3pt = aws.get("three_pct", 36)
    avg_3pt = (home_3pt + away_3pt) / 2
    if avg_3pt < 35.5:
        three_score = 0.75
        breakdown.append(f"🟢 Poor 3PT ({avg_3pt:.1f}%) +0.75")
    elif avg_3pt < 36.5:
        three_score = 0.4
        breakdown.append(f"🟡 Avg 3PT ({avg_3pt:.1f}%) +0.4")
    else:
        three_score = 0
        breakdown.append(f"⚪ Good 3PT ({avg_3pt:.1f}%) +0")
    factors["three_pct"] = three_score
    
    # 10. FT RATE (0-0.5 pts) - low FT = faster game, less stoppage
    home_ft = hs.get("ft_rate", 0.25)
    away_ft = aws.get("ft_rate", 0.25)
    avg_ft = (home_ft + away_ft) / 2
    if avg_ft < 0.24:
        ft_score = 0.5
        breakdown.append(f"🟢 Low FT Rate ({avg_ft:.2f}) +0.5")
    else:
        ft_score = 0
        breakdown.append(f"⚪ Normal FT Rate ({avg_ft:.2f}) +0")
    factors["ft_rate"] = ft_score
    
    # 11. REBOUNDING (0-0.5 pts) - good boards = controlled pace
    home_reb = hs.get("reb_rate", 50)
    away_reb = aws.get("reb_rate", 50)
    avg_reb = (home_reb + away_reb) / 2
    if avg_reb > 51:
        reb_score = 0.5
        breakdown.append(f"🟢 Strong Rebounding ({avg_reb:.1f}%) +0.5")
    else:
        reb_score = 0
        breakdown.append(f"⚪ Avg Rebounding ({avg_reb:.1f}%) +0")
    factors["rebounding"] = reb_score
    
    # 12. DENVER ALTITUDE (0-0.5 pts)
    if home == "Denver":
        alt_score = 0.5
        breakdown.append(f"🏔️ Denver Altitude +0.5")
    else:
        alt_score = 0
    factors["altitude"] = alt_score
    
    total = sum(factors.values())
    
    # Flip scoring for YES side
    if bet_side == "YES":
        total = 10 - total
        breakdown = [f"(YES mode - factors reversed)"] + breakdown
    
    return min(total, 10), factors, breakdown

# ========== FETCH DATA ==========
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')} | v11.1 | 12-Factor System")

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
    st.info("No positions yet. Find edge below ⬇️")

st.divider()

# ========== 2. CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 18, 24], index=1, format_func=lambda x: f"{x} min", key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

thresholds = [225.5, 230.5, 235.5, 240.5, 245.5]
cush_data = []

for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= cush_min:
        proj = round((g['total'] / mins) * 48) if mins > 0 else 0
        cush_data.append({"game": gk, "proj": proj, "mins": mins, "total": g['total'],
                          "home": g['home_team'], "away": g['away_team']})

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

# ========== 3. 12-FACTOR ANALYSIS ==========
st.subheader("🔬 12-FACTOR ANALYSIS")
st.caption("Confirm your cushion pick with fundamentals")

if game_list:
    fc1, fc2 = st.columns([3, 1])
    analyze_game = fc1.selectbox("Select Game", game_list, format_func=lambda x: x.replace("@", " @ "), key="analyze_game")
    factor_side = fc2.selectbox("Bet Side", ["NO", "YES"], key="factor_side")
    
    if analyze_game:
        parts = analyze_game.split("@")
        away_team = parts[0]
        home_team = parts[1]
        
        # Get rest days
        home_rest = 0 if home_team in yesterday_teams else 1
        away_rest = 0 if away_team in yesterday_teams else 1
        
        # Get injury scores
        home_inj, home_stars_out = get_injury_score(home_team, injuries)
        away_inj, away_stars_out = get_injury_score(away_team, injuries)
        
        # Calculate score
        score, factors, breakdown = calc_12_factor_score(
            home_team, away_team, home_rest, away_rest, home_inj, away_inj, factor_side
        )
        
        # Display score
        if score >= 7:
            score_color = "#00ff00"
            score_label = "🟢 STRONG"
        elif score >= 5:
            score_color = "#ffff00"
            score_label = "🟡 GOOD"
        elif score >= 3:
            score_color = "#ff8800"
            score_label = "🟠 LEAN"
        else:
            score_color = "#ff0000"
            score_label = "🔴 SKIP"
        
        st.markdown(f"### <span style='color:{score_color}'>{score:.1f}/10 {score_label}</span>", unsafe_allow_html=True)
        
        # Progress bar
        st.progress(min(score/10, 1.0))
        
        # Breakdown
        with st.expander("📊 Factor Breakdown", expanded=True):
            for line in breakdown:
                st.markdown(f"• {line}")
            
            # Injury details
            if home_stars_out or away_stars_out:
                st.markdown("---")
                st.markdown("**⭐ Star Players OUT:**")
                if home_stars_out:
                    st.markdown(f"• {home_team}: {', '.join(home_stars_out)}")
                if away_stars_out:
                    st.markdown(f"• {away_team}: {', '.join(away_stars_out)}")
        
        # Quick add button
        st.markdown("---")
        qc1, qc2, qc3 = st.columns([2, 1, 1])
        quick_threshold = qc1.number_input("Threshold", 200.0, 280.0, 235.5, 0.5, key="quick_thresh")
        quick_price = qc2.number_input("Price ¢", 1, 99, 75, key="quick_price")
        quick_contracts = qc3.number_input("Contracts", 1, 1000, 100, key="quick_contracts")
        
        if st.button(f"➕ ADD {factor_side} {quick_threshold} TO TRACKER", type="primary", use_container_width=True):
            st.session_state.positions.append({
                "game": analyze_game,
                "side": factor_side,
                "threshold": quick_threshold,
                "price": quick_price,
                "contracts": quick_contracts
            })
            st.rerun()
else:
    st.warning("No games available")

st.divider()

# ========== 4. PACE SCANNER ==========
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

# ========== 5. ALL GAMES ==========
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

# ========== 6. HOW TO USE ==========
with st.expander("📚 HOW TO USE THIS TOOL"):
    st.markdown("""
    ## Two Betting Strategies
    
    This tool supports two distinct edges. Use the right approach for each bet type.
    
    ---
    
    ### 🎯 MONEYLINE BETS (Pre-Game)
    
    **When:** BEFORE tipoff
    
    **Use:** 12-Factor Analysis → Situational Factors
    
    **What to look for:**
    - 🔥 **BLOWOUT RISK** — Fatigued road team @ fresh home = bet the home ML
    - 🟢 **B2B teams** — Back-to-back = tired legs, fade them
    - 🏔️ **ALTITUDE** — Teams visiting Denver struggle
    - 🏆 **DIVISION RIVALS** — Physical games, home team edge
    
    **The Logic:** Fatigue is baked in before tipoff. You don't need game data — the edge exists the moment the schedule is set.
    
    **Action:** Find BLOWOUT RISK or heavy fatigue mismatches → buy ML pre-game at best price.
    
    ---
    
    ### 📊 TOTAL BETS - NO/YES (Live)
    
    **When:** 6+ MINUTES into game
    
    **Use:** Cushion Scanner → 12-Factor Analysis → Add Position
    
    **Step-by-step:**
    1. **Cushion Scanner** — Find games with +10 or more cushion at your threshold
    2. **12-Factor Analysis** — Confirm 5+ score (fundamentals support the play)
    3. **Add Position** — Execute and track
    
    **What to look for:**
    - 🟢 **+20 cushion** = BIG size (confident)
    - 🟡 **+10-19 cushion** = MEDIUM size (standard)
    - 🟠 **+5-9 cushion** = SMALL size (cautious)
    - 🔴 **Under +5** = SKIP (no edge)
    
    **Pace confirmation:**
    - For NO bets: Want SLOW pace (under 4.5/min)
    - For YES bets: Want FAST pace (over 4.8/min)
    
    **The Logic:** 6 minutes of game data reveals the actual pace. Combined with 12-factor analysis, you get a complete picture.
    
    **Action:** Wait for data → confirm cushion + pace + factor score → enter position.
    
    ---
    
    ### ⚠️ KEY RULES
    
    1. **Never bet NO on BLOWOUT RISK games** — Blowouts often push totals UP (garbage time)
    2. **Cushion > Price** — 90¢ means nothing if projection is against you
    3. **Wait for Q1 data** — Pregame projections are guesses; live pace is real
    4. **Size based on cushion** — +20 = big, +10-15 = medium, <5 = skip
    5. **Trust the system** — Don't chase, don't double down, don't martingale
    
    ---
    
    ### 📋 THE 12 FACTORS
    
    | # | Factor | What It Measures |
    |---|--------|------------------|
    | 1 | Rest | Back-to-back penalty |
    | 2 | Defense | Defensive rating matchup |
    | 3 | Injuries | Star player impact (auto ESPN) |
    | 4 | Pace | Team tempo matchup |
    | 5 | Net Rating | Overall team quality gap |
    | 6 | Travel | Miles traveled by away team |
    | 7 | Splits | Home vs away win % |
    | 8 | Division | Rivalry game flag |
    | 9 | 3PT% | Shooting quality |
    | 10 | FT Rate | Free throw frequency |
    | 11 | Rebounding | Board control |
    | 12 | Altitude | Denver home game |
    
    ---
    
    ### 🔄 WORKFLOW SUMMARY
    
    **Before games:**
    1. Check 12-Factor Analysis for ML plays
    2. Look for BLOWOUT RISK matchups
    
    **During games (6+ min):**
    1. Cushion Scanner → Find all-green rows
    2. 12-Factor Analysis → Confirm score 5+
    3. Add Position → Enter the trade
    4. Active Positions → Monitor live
    
    **After games:**
    1. Review wins/losses
    2. Adjust strategy based on results
    """)

st.divider()
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. Past performance does not guarantee future results. You may lose money. Only bet what you can afford to lose.")
