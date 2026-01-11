import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ============================================================
# LIVE DATA FUNCTIONS - NO MORE HARDCODING
# ============================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_live_team_stats():
    """
    Pull LIVE 3PT% and Pace from NBA.com stats API.
    Returns: dict with team stats, timestamp
    """
    # NBA.com stats endpoint for team stats
    url = "https://stats.nba.com/stats/leaguedashteamstats"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nba.com/",
        "Accept": "application/json",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true"
    }
    
    params = {
        "Conference": "",
        "DateFrom": "",
        "DateTo": "",
        "Division": "",
        "GameScope": "",
        "GameSegment": "",
        "Height": "",
        "LastNGames": "0",
        "LeagueID": "00",
        "Location": "",
        "MeasureType": "Base",
        "Month": "0",
        "OpponentTeamID": "0",
        "Outcome": "",
        "PORound": "0",
        "PaceAdjust": "N",
        "PerMode": "PerGame",
        "Period": "0",
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "Season": "2025-26",
        "SeasonSegment": "",
        "SeasonType": "Regular Season",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "TwoWay": "0",
        "VsConference": "",
        "VsDivision": ""
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"NBA API Error: {response.status_code}"
        
        data = response.json()
        headers_list = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        
        # Find column indices
        team_idx = headers_list.index("TEAM_NAME")
        fg3_pct_idx = headers_list.index("FG3_PCT")
        
        team_3pt = {}
        for row in rows:
            team_name = row[team_idx]
            # Clean team name (e.g., "LA Clippers" not "Los Angeles Clippers")
            team_name = team_name.replace("Los Angeles Clippers", "LA Clippers")
            team_name = team_name.replace("Los Angeles Lakers", "LA Lakers")
            team_3pt[team_name] = row[fg3_pct_idx]
        
        return team_3pt, None
        
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_live_pace():
    """
    Pull LIVE Pace from NBA.com stats API (Advanced stats).
    """
    url = "https://stats.nba.com/stats/leaguedashteamstats"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nba.com/",
        "Accept": "application/json",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true"
    }
    
    params = {
        "Conference": "",
        "DateFrom": "",
        "DateTo": "",
        "Division": "",
        "GameScope": "",
        "GameSegment": "",
        "Height": "",
        "LastNGames": "0",
        "LeagueID": "00",
        "Location": "",
        "MeasureType": "Advanced",  # Advanced for pace
        "Month": "0",
        "OpponentTeamID": "0",
        "Outcome": "",
        "PORound": "0",
        "PaceAdjust": "N",
        "PerMode": "PerGame",
        "Period": "0",
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "Season": "2025-26",
        "SeasonSegment": "",
        "SeasonType": "Regular Season",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "TwoWay": "0",
        "VsConference": "",
        "VsDivision": ""
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"NBA API Error: {response.status_code}"
        
        data = response.json()
        headers_list = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        
        team_idx = headers_list.index("TEAM_NAME")
        pace_idx = headers_list.index("PACE")
        
        team_pace = {}
        for row in rows:
            team_name = row[team_idx]
            team_name = team_name.replace("Los Angeles Clippers", "LA Clippers")
            team_name = team_name.replace("Los Angeles Lakers", "LA Lakers")
            team_pace[team_name] = row[pace_idx]
        
        return team_pace, None
        
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=1800)  # Cache for 30 min
def fetch_last_game_dates():
    """
    Pull last game date for each team from NBA scoreboard/schedule.
    """
    # Get yesterday and recent days' games
    et = pytz.timezone('US/Eastern')
    today = datetime.now(et)
    
    last_games = {}
    
    # Check last 5 days of games
    for days_ago in range(1, 6):
        game_date = today - timedelta(days=days_ago)
        date_str = game_date.strftime("%Y-%m-%d")
        
        url = f"https://stats.nba.com/stats/scoreboardv2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.nba.com/",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true"
        }
        params = {
            "GameDate": date_str,
            "LeagueID": "00",
            "DayOffset": "0"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                games = data["resultSets"][0]["rowSet"]
                headers_list = data["resultSets"][0]["headers"]
                
                home_idx = headers_list.index("HOME_TEAM_ID") if "HOME_TEAM_ID" in headers_list else None
                away_idx = headers_list.index("VISITOR_TEAM_ID") if "VISITOR_TEAM_ID" in headers_list else None
                
                # Also try GameHeader resultSet
                for rs in data["resultSets"]:
                    if rs["name"] == "GameHeader":
                        gh_headers = rs["headers"]
                        gh_rows = rs["rowSet"]
                        
                        for row in gh_rows:
                            home_id = row[gh_headers.index("HOME_TEAM_ID")]
                            away_id = row[gh_headers.index("VISITOR_TEAM_ID")]
                            
                            home_name = TEAM_ID_MAP.get(home_id, None)
                            away_name = TEAM_ID_MAP.get(away_id, None)
                            
                            if home_name and home_name not in last_games:
                                last_games[home_name] = date_str
                            if away_name and away_name not in last_games:
                                last_games[away_name] = date_str
        except:
            continue
    
    return last_games

# Team ID mapping for NBA API
TEAM_ID_MAP = {
    1610612737: "Atlanta", 1610612738: "Boston", 1610612739: "Cleveland",
    1610612740: "New Orleans", 1610612741: "Chicago", 1610612742: "Dallas",
    1610612743: "Denver", 1610612744: "Golden State", 1610612745: "Houston",
    1610612746: "LA Clippers", 1610612747: "LA Lakers", 1610612748: "Miami",
    1610612749: "Milwaukee", 1610612750: "Minnesota", 1610612751: "Brooklyn",
    1610612752: "New York", 1610612753: "Orlando", 1610612754: "Indiana",
    1610612755: "Philadelphia", 1610612756: "Phoenix", 1610612757: "Portland",
    1610612758: "Sacramento", 1610612759: "San Antonio", 1610612760: "Oklahoma City",
    1610612761: "Toronto", 1610612762: "Utah", 1610612763: "Memphis",
    1610612764: "Washington", 1610612765: "Detroit", 1610612766: "Charlotte"
}

# ============================================================
# FALLBACK DATA (only used if API fails)
# ============================================================

FALLBACK_3PT_PCT = {
    "Atlanta": 0.362, "Boston": 0.382, "Brooklyn": 0.348, "Charlotte": 0.341,
    "Chicago": 0.352, "Cleveland": 0.358, "Dallas": 0.371, "Denver": 0.365,
    "Detroit": 0.339, "Golden State": 0.378, "Houston": 0.344, "Indiana": 0.374,
    "LA Clippers": 0.356, "LA Lakers": 0.349, "Memphis": 0.332, "Miami": 0.355,
    "Milwaukee": 0.363, "Minnesota": 0.357, "New Orleans": 0.346, "New York": 0.361,
    "Oklahoma City": 0.369, "Orlando": 0.343, "Philadelphia": 0.359, "Phoenix": 0.367,
    "Portland": 0.347, "Sacramento": 0.364, "San Antonio": 0.338, "Toronto": 0.351,
    "Utah": 0.345, "Washington": 0.336
}

FALLBACK_PACE = {
    "Atlanta": 100.2, "Boston": 98.1, "Brooklyn": 99.4, "Charlotte": 101.3,
    "Chicago": 97.8, "Cleveland": 96.5, "Dallas": 98.7, "Denver": 97.2,
    "Detroit": 99.1, "Golden State": 100.8, "Houston": 101.5, "Indiana": 102.4,
    "LA Clippers": 97.4, "LA Lakers": 99.8, "Memphis": 99.6, "Miami": 96.8,
    "Milwaukee": 98.3, "Minnesota": 97.1, "New Orleans": 100.1, "New York": 96.2,
    "Oklahoma City": 99.3, "Orlando": 97.6, "Philadelphia": 98.5, "Phoenix": 99.9,
    "Portland": 100.6, "Sacramento": 101.1, "San Antonio": 98.9, "Toronto": 100.4,
    "Utah": 98.2, "Washington": 101.8
}

# ============================================================
# LOAD LIVE DATA (with fallback)
# ============================================================

def load_team_data():
    """Load live data, fall back to static if API fails."""
    # Try live 3PT%
    live_3pt, err_3pt = fetch_live_team_stats()
    if live_3pt:
        team_3pt = live_3pt
        source_3pt = "🟢 LIVE"
    else:
        team_3pt = FALLBACK_3PT_PCT
        source_3pt = f"🔴 FALLBACK ({err_3pt})"
    
    # Try live Pace
    live_pace, err_pace = fetch_live_pace()
    if live_pace:
        team_pace = live_pace
        source_pace = "🟢 LIVE"
    else:
        team_pace = FALLBACK_PACE
        source_pace = f"🔴 FALLBACK ({err_pace})"
    
    # Try live rest days
    live_rest = fetch_last_game_dates()
    if live_rest and len(live_rest) > 0:
        rest_data = live_rest
        source_rest = "🟢 LIVE"
    else:
        rest_data = {}
        source_rest = "🔴 UNAVAILABLE"
    
    return {
        "3pt": team_3pt,
        "pace": team_pace,
        "rest": rest_data,
        "sources": {
            "3pt": source_3pt,
            "pace": source_pace,
            "rest": source_rest
        }
    }

# ============================================================
# WATCHLIST & REST FUNCTIONS (now use live data)
# ============================================================

def get_bottom_3pt_teams(team_3pt, n=8):
    """Bottom N teams by 3PT% - these can't inflate totals through variance"""
    sorted_teams = sorted(team_3pt.items(), key=lambda x: x[1])
    return [team for team, pct in sorted_teams[:n]]

def get_bottom_pace_teams(team_pace, n=10):
    """Bottom N teams by pace - these limit possession volume"""
    sorted_teams = sorted(team_pace.items(), key=lambda x: x[1])
    return [team for team, pace in sorted_teams[:n]]

def get_primary_watchlist(team_3pt, team_pace):
    """Intersection of bottom 3PT% AND bottom pace teams"""
    bottom_3pt = set(get_bottom_3pt_teams(team_3pt, 8))
    bottom_pace = set(get_bottom_pace_teams(team_pace, 10))
    return bottom_3pt.intersection(bottom_pace)

def get_rest_days(team, rest_data):
    """Calculate days since last game using live data"""
    if team not in rest_data:
        return None
    try:
        last_game = datetime.strptime(rest_data[team], "%Y-%m-%d")
        today = datetime.now()
        return (today - last_game).days
    except:
        return None

def get_rest_status(days):
    """Categorize rest status"""
    if days is None:
        return "Unknown", "⚪"
    elif days <= 1:
        return "Short Rest", "🔴"
    elif days == 2:
        return "Normal Rest", "🟡"
    else:
        return "Extended Rest", "🟢"

# Team abbreviation mappings
ABBREV_TO_FULL = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte",
    "CHI": "Chicago", "CLE": "Cleveland", "DAL": "Dallas", "DEN": "Denver",
    "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami",
    "MIL": "Milwaukee", "MIN": "Minnesota", "NOP": "New Orleans", "NYK": "New York",
    "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia", "PHX": "Phoenix",
    "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto",
    "UTA": "Utah", "WAS": "Washington"
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
# STEP 1: GENERATE PRIMARY WATCHLIST
# ============================================================

def get_bottom_3pt_teams(n=8):
    """Bottom N teams by 3PT% - these can't inflate totals through variance"""
    sorted_teams = sorted(TEAM_3PT_PCT.items(), key=lambda x: x[1])
    return [team for team, pct in sorted_teams[:n]]

def get_bottom_pace_teams(n=10):
    """Bottom N teams by pace - these limit possession volume"""
    sorted_teams = sorted(TEAM_PACE.items(), key=lambda x: x[1])
    return [team for team, pace in sorted_teams[:n]]

def get_primary_watchlist():
    """Intersection of bottom 3PT% AND bottom pace teams"""
    bottom_3pt = set(get_bottom_3pt_teams(8))
    bottom_pace = set(get_bottom_pace_teams(10))
    return bottom_3pt.intersection(bottom_pace)

# ============================================================
# REST DAY CALCULATIONS
# ============================================================

# Last game dates (UPDATE DAILY or pull from API)
# Format: "Team": "YYYY-MM-DD"
LAST_GAME_DATES = {
    "Atlanta": "2026-01-10", "Boston": "2026-01-10", "Brooklyn": "2026-01-09",
    "Charlotte": "2026-01-10", "Chicago": "2026-01-09", "Cleveland": "2026-01-10",
    "Dallas": "2026-01-10", "Denver": "2026-01-09", "Detroit": "2026-01-10",
    "Golden State": "2026-01-10", "Houston": "2026-01-09", "Indiana": "2026-01-10",
    "LA Clippers": "2026-01-09", "LA Lakers": "2026-01-10", "Memphis": "2026-01-10",
    "Miami": "2026-01-09", "Milwaukee": "2026-01-10", "Minnesota": "2026-01-09",
    "New Orleans": "2026-01-10", "New York": "2026-01-10", "Oklahoma City": "2026-01-09",
    "Orlando": "2026-01-10", "Philadelphia": "2026-01-09", "Phoenix": "2026-01-10",
    "Portland": "2026-01-09", "Sacramento": "2026-01-10", "San Antonio": "2026-01-09",
    "Toronto": "2026-01-10", "Utah": "2026-01-09", "Washington": "2026-01-10"
}

def get_rest_days(team):
    """Calculate days since last game"""
    if team not in LAST_GAME_DATES:
        return None
    last_game = datetime.strptime(LAST_GAME_DATES[team], "%Y-%m-%d")
    today = datetime.now()
    return (today - last_game).days

def get_rest_status(days):
    """Categorize rest status"""
    if days is None:
        return "Unknown", "⚪"
    elif days <= 1:
        return "Short Rest", "🔴"
    elif days == 2:
        return "Normal Rest", "🟡"
    else:
        return "Extended Rest", "🟢"

# ============================================================
# KALSHI API FUNCTIONS
# ============================================================

def parse_teams_from_ticker(ticker_code):
    """Parse team codes from ticker like '26JAN11NOPWAS' -> ('New Orleans', 'Washington')"""
    if len(ticker_code) < 12:
        return None, None
    teams_part = ticker_code[7:]
    if len(teams_part) == 6:
        away_code = teams_part[:3]
        home_code = teams_part[3:]
    else:
        away_code = teams_part[:3]
        home_code = teams_part[3:6] if len(teams_part) >= 6 else teams_part[3:]
    away = TICKER_ABBREVS.get(away_code.upper(), away_code)
    home = TICKER_ABBREVS.get(home_code.upper(), home_code)
    return away, home

def parse_game_date(game_code):
    """Parse date from ticker like '26JAN11NOPWAS' -> '2026-01-11'"""
    try:
        year = "20" + game_code[:2]  # "26" -> "2026"
        month_str = game_code[2:5].upper()  # "JAN"
        day = game_code[5:7]  # "11"
        months = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
                  "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}
        month = months.get(month_str, "01")
        return f"{year}-{month}-{day}"
    except:
        return None

def fetch_extreme_totals(min_threshold=245):
    """Fetch only extreme totals (≥245) from Kalshi - TODAY'S GAMES ONLY"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": "KXNBATOTAL", "status": "open", "limit": 200}
    
    # Get today's date in ET
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
                    
                    # FILTER: Only today's games
                    game_date = parse_game_date(game_code)
                    if game_date != today:
                        continue  # Skip games not scheduled for today
                    
                    away, home = parse_teams_from_ticker(game_code)
                    
                    yes_ask = m.get("yes_ask", 0) or 0
                    no_ask = m.get("no_ask", 0) or 0
                    if no_ask == 0 and yes_ask > 0:
                        no_ask = 1 - yes_ask
                    
                    extreme_markets.append({
                        "ticker": m.get("ticker", ""),
                        "event_ticker": event_ticker,
                        "threshold": floor_strike,
                        "away_team": away,
                        "home_team": home,
                        "yes_ask": yes_ask,
                        "no_ask": no_ask,
                        "volume": m.get("volume", 0),
                        "title": m.get("title", ""),
                        "game_date": game_date
                    })
        
        extreme_markets.sort(key=lambda x: x["threshold"], reverse=True)
        return extreme_markets, None, today
        
    except Exception as e:
        return [], str(e), today

# ============================================================
# FILTER LOGIC
# ============================================================

def get_price_tolerance(q1_total):
    """
    REGIME-AWARE PRICE TOLERANCE
    Hard rules - simple, enforceable.
    """
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

def calculate_confidence_score(market, q1_total, watchlist, spread_estimate=5, early_entry=False, rest_data=None):
    """
    RESTRUCTURED: Gate first, then score.
    Q1 is a GATE, bonuses are ADDITIVE.
    Returns: total_score (0-100), breakdown dict, recommendation, rec_color, price_ok
    """
    if rest_data is None:
        rest_data = {}
    
    away = market["away_team"]
    home = market["home_team"]
    threshold = market["threshold"]
    no_ask = market["no_ask"]
    
    breakdown = {}
    
    # ============================================================
    # STEP 1: HARD GATES (must pass before scoring)
    # ============================================================
    
    # Gate 1: Q1 Regime Check
    if q1_total is not None and q1_total >= 55:
        breakdown["GATE FAILED"] = {"label": "🚫 Q1 ≥ 55 - AUTOMATIC REJECT"}
        return 0, breakdown, "🚫 NO TRADE - Q1 too high", "red", False
    
    # Gate 2: Price tolerance for Q1 regime
    max_price, regime = get_price_tolerance(q1_total)
    price_ok = no_ask <= max_price
    
    if not price_ok and q1_total is not None:
        breakdown["GATE FAILED"] = {"label": f"🚫 Price {no_ask:.2f} > {max_price:.2f} tolerance for {regime}"}
        return 0, breakdown, f"🚫 NO TRADE - Overpriced for {regime}", "red", False
    
    # ============================================================
    # STEP 2: Q1 REGIME SCORE (30 points max - reduced from 50)
    # ============================================================
    if q1_total is not None:
        if q1_total < 45:
            q1_pts = 30
            q1_label = "🔥 ELITE (<45)"
        elif q1_total < 48:
            q1_pts = 27
            q1_label = "🟢 Excellent (<48)"
        elif q1_total < 50:
            q1_pts = 22
            q1_label = "🟢 Good (48-49)"
        elif q1_total < 55:
            q1_pts = 15
            q1_label = "🟡 Marginal (50-54)"
        else:
            q1_pts = 0
            q1_label = "🔴 NO TRADE (≥55)"
    else:
        q1_pts = 0
        q1_label = "⚪ Not entered yet"
    
    breakdown["Q1 Regime"] = {"points": q1_pts, "max": 30, "value": q1_total, "label": q1_label}
    
    # ============================================================
    # STEP 3: BONUS FACTORS (70 points max - rebalanced)
    # ============================================================
    
    # Watchlist team (+20 max - increased importance)
    has_watchlist = away in watchlist or home in watchlist
    if has_watchlist:
        wl_pts = 20
        wl_team = away if away in watchlist else home
        wl_label = f"✅ {wl_team}"
    else:
        wl_pts = 0
        wl_label = "❌ None"
    breakdown["Watchlist Team"] = {"points": wl_pts, "max": 20, "label": wl_label}
    
    # Price quality RELATIVE TO REGIME (+20 max)
    if q1_total is not None:
        price_buffer = max_price - no_ask  # How much under tolerance
        if price_buffer >= 0.10:
            price_pts = 20
            price_label = f"🔥 Excellent ({no_ask:.2f}, {price_buffer:.0%} under limit)"
        elif price_buffer >= 0.06:
            price_pts = 15
            price_label = f"🟢 Good ({no_ask:.2f})"
        elif price_buffer >= 0.03:
            price_pts = 10
            price_label = f"🟡 Fair ({no_ask:.2f})"
        else:
            price_pts = 5
            price_label = f"🟠 Tight ({no_ask:.2f}, near limit)"
    else:
        # Pregame pricing
        if no_ask <= 0.60:
            price_pts = 20
            price_label = f"🔥 Elite pregame ({no_ask:.2f})"
        elif no_ask <= 0.65:
            price_pts = 15
            price_label = f"🟢 Good pregame ({no_ask:.2f})"
        elif no_ask <= 0.68:
            price_pts = 10
            price_label = f"🟡 OK pregame ({no_ask:.2f})"
        else:
            price_pts = 0
            price_label = f"🔴 Too expensive pregame ({no_ask:.2f})"
    breakdown["Price vs Regime"] = {"points": price_pts, "max": 20, "value": f"{no_ask:.2f}", "label": price_label}
    
    # Threshold height (+10 max)
    if threshold >= 255:
        thresh_pts = 10
        thresh_label = "🔥 Extreme (≥255)"
    elif threshold >= 252:
        thresh_pts = 8
        thresh_label = "🟢 Very high (≥252)"
    elif threshold >= 250:
        thresh_pts = 6
        thresh_label = "🟢 High (≥250)"
    elif threshold >= 248:
        thresh_pts = 4
        thresh_label = "🟡 Elevated (≥248)"
    else:
        thresh_pts = 2
        thresh_label = "🟡 Baseline (245-247)"
    breakdown["Threshold"] = {"points": thresh_pts, "max": 10, "value": threshold, "label": thresh_label}
    
    # Rest advantage (+12 max - uses live data)
    away_rest = get_rest_days(away, rest_data)
    home_rest = get_rest_days(home, rest_data)
    short_rest_count = sum([1 for r in [away_rest, home_rest] if r is not None and r <= 1])
    extended_rest_count = sum([1 for r in [away_rest, home_rest] if r is not None and r >= 3])
    
    if short_rest_count == 2:
        rest_pts = 12
        rest_label = "🔥 Both short rest"
    elif short_rest_count == 1 and extended_rest_count == 0:
        rest_pts = 9
        rest_label = "🟢 One short rest"
    elif short_rest_count == 1:
        rest_pts = 6
        rest_label = "🟡 Mixed rest"
    elif extended_rest_count == 2:
        rest_pts = 0
        rest_label = "🔴 Both extended (CAUTION)"
    else:
        rest_pts = 3
        rest_label = "🟡 Normal rest"
    breakdown["Rest Factor"] = {"points": rest_pts, "max": 12, "label": rest_label}
    
    # OT Risk / Spread (+8 max - increased)
    if spread_estimate >= 10:
        ot_pts = 8
        ot_label = "🟢 Low OT risk (≥10)"
    elif spread_estimate >= 7:
        ot_pts = 6
        ot_label = "🟢 Safe (≥7)"
    elif spread_estimate >= 5:
        ot_pts = 4
        ot_label = "🟡 OK (≥5)"
    elif spread_estimate >= 3:
        ot_pts = 2
        ot_label = "🟠 Risky (3-5)"
    else:
        ot_pts = 0
        ot_label = "🔴 High OT risk (<3)"
    breakdown["OT Risk"] = {"points": ot_pts, "max": 8, "value": spread_estimate, "label": ot_label}
    
    # Early entry bonus (+5 if flagged)
    if early_entry and q1_total is not None and q1_total < 50:
        early_pts = 5
        early_label = "🟢 Locked in early"
    else:
        early_pts = 0
        early_label = "—"
    if early_entry:
        breakdown["Early Entry"] = {"points": early_pts, "max": 5, "label": early_label}
    
    # ============================================================
    # STEP 4: TOTAL SCORE
    # ============================================================
    score = q1_pts + wl_pts + price_pts + thresh_pts + rest_pts + ot_pts + early_pts
    
    # ============================================================
    # STEP 5: RECOMMENDATION (requires Q1 confirmation)
    # ============================================================
    if q1_total is None:
        recommendation = "⏳ WAIT FOR Q1"
        rec_color = "gray"
    elif score >= 75:
        recommendation = "🚀 STRONG BET"
        rec_color = "green"
    elif score >= 60:
        recommendation = "✅ GOOD BET"
        rec_color = "green"
    elif score >= 45:
        recommendation = "🟡 MARGINAL - Small position only"
        rec_color = "yellow"
    elif score >= 30:
        recommendation = "⚠️ WEAK - Consider skipping"
        rec_color = "orange"
    else:
        recommendation = "🚫 NO TRADE - Score too low"
        rec_color = "red"
    
    return score, breakdown, recommendation, rec_color, price_ok

# ============================================================
# STREAMLIT APP
# ============================================================

st.set_page_config(
    page_title="Extreme Totals NO Finder",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 KALSHI EXTREME TOTALS - NO FINDER")
st.caption("Tail-risk exploitation system. You are not betting averages. You are betting tail collapse.")

# Sidebar
with st.sidebar:
    st.header("⚙️ System Settings")
    
    # Load live data FIRST
    with st.spinner("Loading live NBA data..."):
        live_data = load_team_data()
    
    TEAM_3PT_PCT = live_data["3pt"]
    TEAM_PACE = live_data["pace"]
    REST_DATA = live_data["rest"]
    sources = live_data["sources"]
    
    # Threshold filter
    min_threshold = st.selectbox(
        "Minimum Threshold",
        options=[245, 248, 250, 252, 255],
        index=0,
        help="Only show markets at or above this total"
    )
    
    st.divider()
    
    # DATA STATUS
    st.subheader("📡 DATA STATUS")
    st.write(f"3PT%: {sources['3pt']}")
    st.write(f"Pace: {sources['pace']}")
    st.write(f"Rest: {sources['rest']}")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    # PRICE TOLERANCE LEGEND - HARD RULES
    st.subheader("💰 PRICE TOLERANCE")
    st.caption("Hard rules. Simple. Enforceable.")
    st.markdown("""
    | Q1 Score | Max NO Ask |
    |:--------:|:----------:|
    | **< 48** | **0.78** |
    | **48-49** | **0.75** |
    | **50-54** | **0.70** |
    | **≥ 55** | **NO TRADE** |
    """)
    st.caption("Pregame (no Q1 yet): 0.68 max")
    
    st.divider()
    
    # Primary Watchlist - NOW LIVE
    st.subheader("📋 Primary Watchlist")
    st.caption("LIVE: Bottom 8 3PT% ∩ Bottom 10 pace")
    watchlist = get_primary_watchlist(TEAM_3PT_PCT, TEAM_PACE)
    
    if watchlist:
        for team in sorted(watchlist):
            st.write(f"• **{team}**")
            pct = TEAM_3PT_PCT.get(team, 0)
            pace = TEAM_PACE.get(team, 0)
            st.caption(f"  3PT: {pct:.1%} | Pace: {pace:.1f}")
    else:
        st.warning("No teams qualify this week")
    
    st.divider()
    
    # Component Lists - NOW LIVE
    with st.expander("🔍 Bottom 8 3PT% Teams"):
        for team in get_bottom_3pt_teams(TEAM_3PT_PCT, 8):
            pct = TEAM_3PT_PCT.get(team, 0)
            st.write(f"• {team}: {pct:.1%}")
    
    with st.expander("🐢 Bottom 10 Pace Teams"):
        for team in get_bottom_pace_teams(TEAM_PACE, 10):
            pace = TEAM_PACE.get(team, 0)
            st.write(f"• {team}: {pace:.1f}")
    
    st.divider()
    
    # Kill Switch Warning
    st.subheader("🛑 KILL SWITCH")
    st.error("If NO price jumps +5¢ in <30 sec → ABORT")
    st.caption("Protects against repricing spikes and bot front-running")

# Main content - CENTERED
if st.button("🔄 Refresh Markets", type="primary"):
    st.cache_data.clear()

@st.cache_data(ttl=300)
def load_markets(threshold):
    return fetch_extreme_totals(threshold)

markets, error, today_date = load_markets(min_threshold)

st.caption(f"📅 Showing games for: **{today_date}** (Eastern Time)")

if error:
    st.error(f"API Error: {error}")
elif not markets:
    st.warning(f"No extreme totals (≥{min_threshold}) found for today ({today_date}). Either no games today or markets not yet posted.")
    
    with st.expander("🔍 Diagnostic: Check all available markets"):
        diag_url = "https://api.elections.kalshi.com/trade-api/v2/markets"
        diag_params = {"series_ticker": "KXNBATOTAL", "status": "open", "limit": 50}
        try:
            diag_resp = requests.get(diag_url, params=diag_params, timeout=10)
            diag_data = diag_resp.json()
            diag_markets = diag_data.get("markets", [])
            if diag_markets:
                st.write(f"Found {len(diag_markets)} total KXNBATOTAL markets in API:")
                for dm in diag_markets[:10]:
                    et = dm.get("event_ticker", "")
                    fs = dm.get("floor_strike", 0)
                    st.write(f"• {et} | Threshold: {fs}")
            else:
                st.write("No KXNBATOTAL markets found in API at all")
        except Exception as e:
            st.write(f"Diagnostic error: {e}")
else:
    # No global price filter - regime-aware now
    eligible_markets = markets  # Show all, let regime logic handle it
    
    # ============================================================
    # TOP EDGES SECTION - BEST 2-3 OPPORTUNITIES (PREGAME)
    # ============================================================
    
    def score_pregame_edge(market, team_3pt, team_pace, rest_data):
        """Score each market for PREGAME edge quality. Higher = better."""
        away = market["away_team"]
        home = market["home_team"]
        no_ask = market["no_ask"]
        threshold = market["threshold"]
        
        # Pregame: must be under 0.68
        if no_ask > 0.68:
            return 0, ["🔴 Price too high for pregame"]
        
        # Get live watchlist
        wl = get_primary_watchlist(team_3pt, team_pace)
        
        score = 0
        reasons = []
        
        # Watchlist team = +30 points
        if away in wl or home in wl:
            score += 30
            wt = away if away in wl else home
            reasons.append(f"✅ Watchlist team ({wt})")
        
        # Price: Lower NO = better edge (pregame scale)
        if no_ask <= 0.58:
            score += 25
            reasons.append(f"🔥 Elite price ({no_ask:.2f})")
        elif no_ask <= 0.62:
            score += 20
            reasons.append(f"🟢 Great price ({no_ask:.2f})")
        elif no_ask <= 0.65:
            score += 15
            reasons.append(f"🟢 Good price ({no_ask:.2f})")
        elif no_ask <= 0.68:
            score += 10
            reasons.append(f"🟡 OK price ({no_ask:.2f})")
        
        # Higher threshold = more extreme = better
        if threshold >= 252:
            score += 20
            reasons.append(f"🔥 Very extreme ({threshold})")
        elif threshold >= 250:
            score += 15
            reasons.append(f"🟢 Extreme ({threshold})")
        elif threshold >= 248:
            score += 10
            reasons.append(f"🟡 High ({threshold})")
        else:
            score += 5
            reasons.append(f"Baseline ({threshold})")
        
        # Short rest bonus (live data)
        away_rest = get_rest_days(away, rest_data)
        home_rest = get_rest_days(home, rest_data)
        if (away_rest and away_rest <= 1) or (home_rest and home_rest <= 1):
            score += 15
            reasons.append("🟢 Short rest involved")
        
        # Both teams extended rest = penalty
        if (away_rest and away_rest >= 3) and (home_rest and home_rest >= 3):
            score -= 20
            reasons.append("⚠️ Both on extended rest")
        
        return score, reasons
    
    # Score all markets for pregame ranking
    scored_markets = []
    for m in eligible_markets:
        score, reasons = score_pregame_edge(m, TEAM_3PT_PCT, TEAM_PACE, REST_DATA)
        if score > 0:  # Only include if passes pregame price gate
            scored_markets.append({**m, "score": score, "reasons": reasons})
    
    # Sort by score, take top 3
    scored_markets.sort(key=lambda x: x["score"], reverse=True)
    top_edges = scored_markets[:3]
    
    # Display TOP EDGES
    st.header("🔥 TODAY'S TOP EDGES (PREGAME)")
    st.caption("Best pregame opportunities. Remember: WAIT FOR Q1 before betting. These are watchlist targets.")
    
    if top_edges:
        edge_cols = st.columns(len(top_edges))
        for i, edge in enumerate(top_edges):
            with edge_cols[i]:
                rank_emoji = ["🥇", "🥈", "🥉"][i]
                st.subheader(f"{rank_emoji} #{i+1} TARGET")
                
                st.markdown(f"### {edge['away_team']} @ {edge['home_team']}")
                st.metric("Threshold", f"≥ {edge['threshold']}")
                st.metric("Pregame NO", f"{edge['no_ask']:.2f}")
                
                st.write("**Why watch this:**")
                for reason in edge["reasons"]:
                    st.write(f"• {reason}")
                
                st.caption("⏳ Wait for Q1 < 55 before entry")
    else:
        st.warning("No games meet pregame price criteria (≤0.68). Wait for Q1 confirmation to unlock higher price tolerance.")
    
    st.divider()
    
    # ============================================================
    # ALL MARKETS - CENTERED LIST
    # ============================================================
    
    st.header("📊 All Extreme Totals Markets")
    pregame_eligible = len([m for m in markets if m["no_ask"] <= 0.68])
    st.success(f"Found {len(markets)} extreme totals | {pregame_eligible} under pregame limit (≤0.68) | All unlock after Q1")
    
    for market in eligible_markets:
        away = market["away_team"]
        home = market["home_team"]
        threshold = market["threshold"]
        no_ask = market["no_ask"]
        
        has_watchlist = away in watchlist or home in watchlist
        watchlist_badge = "✅ WATCHLIST" if has_watchlist else "⚠️ No watchlist team"
        
        away_rest = get_rest_days(away, REST_DATA)
        home_rest = get_rest_days(home, REST_DATA)
        away_status, away_icon = get_rest_status(away_rest)
        home_status, home_icon = get_rest_status(home_rest)
        
        # Price status based on hard rules
        if no_ask <= 0.68:
            price_status = "🟢 Pregame OK"
        elif no_ask <= 0.70:
            price_status = "🟡 Needs Q1 50-54"
        elif no_ask <= 0.75:
            price_status = "🟡 Needs Q1 48-49"
        elif no_ask <= 0.78:
            price_status = "🟠 Needs Q1 < 48"
        else:
            price_status = "🔴 Too expensive"
        
        with st.container():
            st.subheader(f"🏀 {away} @ {home}")
            
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.metric("Threshold", f"{threshold}")
            with mcol2:
                st.metric("NO Price", f"{no_ask:.2f}")
                st.caption(price_status)
            with mcol3:
                st.write(f"**{watchlist_badge}**")
            
            away_rest_str = f"{away_rest}d" if away_rest is not None else "?"
            home_rest_str = f"{home_rest}d" if home_rest is not None else "?"
            st.write(f"**Rest:** {away_icon} {away} ({away_rest_str}) vs {home_icon} {home} ({home_rest_str})")
            
            kalshi_url = f"https://kalshi.com/markets/{market['ticker']}"
            st.markdown(f"[View on Kalshi]({kalshi_url})")
            
            st.divider()
    
    # ============================================================
    # CONFIDENCE SCORER - BELOW MARKETS
    # ============================================================
    
    st.header("🎯 CONFIDENCE SCORER")
    st.caption("Gate-first logic: Q1 and price must pass BEFORE bonuses count. No more overconfidence on bad setups.")
    
    check_col1, check_col2 = st.columns([1, 2])
    
    with check_col1:
        market_options = [f"{m['away_team']} @ {m['home_team']} ({m['threshold']})" for m in markets]
        selected_idx = st.selectbox("Select Game", range(len(market_options)), format_func=lambda x: market_options[x])
        selected_market = markets[selected_idx]
        
        st.subheader("🔴 LIVE INPUTS")
        q1_total = st.number_input(
            "Q1 Combined Score",
            min_value=0, max_value=100, value=0,
            help="Enter AFTER Q1 ends. This is the primary gate."
        )
        
        spread_est = st.number_input(
            "Pregame Spread",
            min_value=0.0, max_value=30.0, value=5.0, step=0.5,
            help="Higher spread = less OT risk"
        )
        
        # Early entry flag
        st.divider()
        early_entry = st.checkbox(
            "🔒 Early Entry Lock-In",
            value=False,
            help="Check if entering with <90s left in Q1 and score clearly under pace"
        )
        if early_entry:
            st.caption("⚡ You're locking in before Q1 ends. Make sure pace is visibly slow.")
        
        # Current price for kill switch
        st.divider()
        st.write(f"**Current NO Price:** {selected_market['no_ask']:.2f}")
        q1_val = q1_total if q1_total > 0 else None
        max_price, regime = get_price_tolerance(q1_val)
        st.write(f"**Price Limit ({regime}):** {max_price:.2f}")
    
    with check_col2:
        score, breakdown, recommendation, rec_color, price_ok = calculate_confidence_score(
            selected_market, q1_val, watchlist, spread_est, early_entry, REST_DATA
        )
        
        # Check for gate failure
        gate_failed = "GATE FAILED" in breakdown
        
        if gate_failed:
            st.error(f"**{breakdown['GATE FAILED']['label']}**")
            st.caption("Trade rejected at gate level. Bonuses don't matter.")
        else:
            # Big score display
            st.subheader(f"📊 CONFIDENCE: {score}/100")
            st.progress(min(score / 100, 1.0))
            
            if rec_color == "green":
                st.success(f"**{recommendation}**")
            elif rec_color == "yellow":
                st.warning(f"**{recommendation}**")
            elif rec_color == "orange":
                st.warning(f"**{recommendation}**")
            elif rec_color == "red":
                st.error(f"**{recommendation}**")
            else:
                st.info(f"**{recommendation}**")
            
            # Breakdown table
            st.write("**Score Breakdown:**")
            for factor, data in breakdown.items():
                if factor == "GATE FAILED":
                    continue
                pts = data.get("points", 0)
                max_pts = data.get("max", 0)
                label = data.get("label", "")
                if max_pts > 0:
                    bar = "█" * int(pts * 10 / max_pts) + "░" * (10 - int(pts * 10 / max_pts))
                    st.write(f"**{factor}**: {pts}/{max_pts} {bar} {label}")
                else:
                    st.write(f"**{factor}**: {label}")
        
        st.divider()
        
        # Action button
        if not gate_failed and score >= 45 and q1_val is not None:
            kalshi_url = f"https://kalshi.com/markets/{selected_market['ticker']}"
            st.link_button(
                f"→ BET NO on {selected_market['threshold']} (Confidence: {score}%)", 
                kalshi_url, 
                type="primary"
            )
            st.caption("🛑 ABORT if price jumps +5¢ suddenly")
        elif q1_val is None:
            st.info("Enter Q1 score after first quarter ends")
        else:
            st.caption("Trade rejected. Wait for better setup.")

# Bottom section - System Rules
st.divider()
with st.expander("📖 SYSTEM RULES v4.0 (READ THIS)"):
    st.markdown("""
    ### 🟢 LIVE DATA
    - **3PT%**: Pulled from NBA.com (hourly refresh)
    - **Pace**: Pulled from NBA.com (hourly refresh)
    - **Rest Days**: Pulled from NBA scoreboard (30 min refresh)
    - **Watchlist**: Auto-calculated from live stats
    
    ### GATE-FIRST LOGIC
    
    **Step 1: Hard Gates (must pass)**
    - Q1 ≥ 55 → AUTOMATIC REJECT
    - Price over regime tolerance → REJECT
    
    **Step 2: Q1 Regime Score (30 pts max)**
    - Q1 < 45: 30 pts (ELITE)
    - Q1 < 48: 27 pts
    - Q1 48-49: 22 pts
    - Q1 50-54: 15 pts
    - Q1 ≥ 55: REJECTED AT GATE
    
    **Step 3: Bonus Factors (70 pts max)**
    - Watchlist Team: +20 pts
    - Price vs Regime: +20 pts
    - Rest Advantage: +12 pts
    - Threshold Height: +10 pts
    - Low OT Risk: +8 pts
    
    ### PRICE TOLERANCE (HARD RULES)
    | Q1 Score | Max NO Price |
    |----------|--------------|
    | < 48 | 0.78 |
    | 48-49 | 0.75 |
    | 50-54 | 0.70 |
    | ≥ 55 | NO TRADE |
    
    *Pregame (before Q1): 0.68 max*
    
    ### KILL SWITCH
    🛑 If NO price jumps +5¢ in <30 seconds → ABORT IMMEDIATELY
    
    ### RECOMMENDATIONS BY SCORE
    - **75-100**: 🚀 STRONG BET
    - **60-74**: ✅ GOOD BET  
    - **45-59**: 🟡 MARGINAL - Small position
    - **30-44**: ⚠️ WEAK - Skip
    - **<30**: 🚫 NO TRADE
    
    ### NEVER
    - Enter if Q1 ≥ 55
    - Chase price spikes
    - Double down or martingale
    """)

# Footer
st.divider()
st.caption("Extreme Totals NO Finder v4.0 | 🟢 LIVE DATA | Gate-First Logic | Regime-Aware Pricing")
