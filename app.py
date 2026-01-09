import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math
import re

st.set_page_config(page_title="NBA Kalshi Edge Finder", page_icon="🏀", layout="wide")

# ========== ESPN TEAM NAME MAPPING ==========
ESPN_TEAM_MAP = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
    "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
    "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee",
    "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City",
    "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia",
    "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio",
    "Toronto Raptors": "Toronto", "Utah Jazz": "Utah", "Washington Wizards": "Washington",
}

# ========== STAR PLAYERS DATABASE (tier, type: O=offense, D=defense, B=both) ==========
STAR_PLAYERS = {
    "Atlanta": {
        "Trae Young": (3, "O"), "Dejounte Murray": (2, "B"), "Jalen Johnson": (2, "B"),
        "De'Andre Hunter": (2, "O"), "Clint Capela": (1, "D"), "Bogdan Bogdanovic": (1, "O"),
        "Onyeka Okongwu": (1, "D"), "Dyson Daniels": (1, "D"), "Zaccharie Risacher": (1, "O"),
    },
    "Boston": {
        "Jayson Tatum": (3, "B"), "Jaylen Brown": (3, "B"), "Derrick White": (2, "B"),
        "Jrue Holiday": (2, "D"), "Kristaps Porzingis": (2, "B"), "Al Horford": (1, "D"),
        "Payton Pritchard": (1, "O"), "Sam Hauser": (1, "O"),
    },
    "Brooklyn": {
        "Cam Thomas": (2, "O"), "Mikal Bridges": (2, "B"), "Nic Claxton": (2, "D"),
        "Ben Simmons": (1, "D"), "Dorian Finney-Smith": (1, "D"), "Cameron Johnson": (1, "O"),
        "Dennis Schroder": (1, "O"), "Day'Ron Sharpe": (1, "D"),
    },
    "Charlotte": {
        "LaMelo Ball": (3, "O"), "Brandon Miller": (2, "O"), "Miles Bridges": (2, "B"),
        "Mark Williams": (2, "D"), "Nick Richards": (1, "D"), "Tre Mann": (1, "O"),
        "Cody Martin": (1, "D"), "Josh Green": (1, "D"),
    },
    "Chicago": {
        "Zach LaVine": (2, "O"), "Coby White": (2, "O"), "Nikola Vucevic": (2, "B"),
        "Josh Giddey": (2, "B"), "Patrick Williams": (1, "D"), "Ayo Dosunmu": (1, "B"),
        "Andre Drummond": (1, "D"), "Torrey Craig": (1, "D"),
    },
    "Cleveland": {
        "Donovan Mitchell": (3, "O"), "Darius Garland": (2, "O"), "Evan Mobley": (3, "D"),
        "Jarrett Allen": (2, "D"), "Max Strus": (1, "O"), "Caris LeVert": (1, "O"),
        "Isaac Okoro": (1, "D"), "Georges Niang": (1, "O"),
    },
    "Dallas": {
        "Luka Doncic": (3, "O"), "Kyrie Irving": (3, "O"), "PJ Washington": (2, "B"),
        "Daniel Gafford": (2, "D"), "Dereck Lively II": (2, "D"), "Klay Thompson": (2, "O"),
        "Naji Marshall": (1, "D"), "Quentin Grimes": (1, "O"),
    },
    "Denver": {
        "Nikola Jokic": (3, "B"), "Jamal Murray": (3, "O"), "Michael Porter Jr": (2, "O"),
        "Aaron Gordon": (2, "B"), "Christian Braun": (1, "B"), "Russell Westbrook": (1, "O"),
        "Peyton Watson": (1, "D"), "Dario Saric": (1, "O"),
    },
    "Detroit": {
        "Cade Cunningham": (3, "O"), "Jaden Ivey": (2, "O"), "Ausar Thompson": (2, "D"),
        "Jalen Duren": (2, "D"), "Tim Hardaway Jr": (1, "O"), "Tobias Harris": (1, "B"),
        "Isaiah Stewart": (1, "D"), "Malik Beasley": (1, "O"),
    },
    "Golden State": {
        "Stephen Curry": (3, "O"), "Draymond Green": (2, "D"), "Andrew Wiggins": (2, "B"),
        "Jonathan Kuminga": (2, "B"), "Kevon Looney": (1, "D"), "Brandin Podziemski": (1, "O"),
        "Buddy Hield": (1, "O"), "Gary Payton II": (1, "D"),
    },
    "Houston": {
        "Jalen Green": (2, "O"), "Alperen Sengun": (3, "B"), "Fred VanVleet": (2, "B"),
        "Jabari Smith Jr": (2, "B"), "Dillon Brooks": (1, "D"), "Amen Thompson": (2, "B"),
        "Tari Eason": (1, "D"), "Cam Whitmore": (1, "O"),
    },
    "Indiana": {
        "Tyrese Haliburton": (3, "O"), "Pascal Siakam": (2, "B"), "Myles Turner": (2, "D"),
        "Bennedict Mathurin": (2, "O"), "Aaron Nesmith": (1, "B"), "TJ McConnell": (1, "O"),
        "Obi Toppin": (1, "O"), "Andrew Nembhard": (1, "B"),
    },
    "LA Clippers": {
        "Kawhi Leonard": (3, "B"), "James Harden": (3, "O"), "Norman Powell": (2, "O"),
        "Ivica Zubac": (2, "D"), "Terance Mann": (1, "B"), "Derrick Jones Jr": (1, "D"),
        "Bones Hyland": (1, "O"), "Kris Dunn": (1, "D"),
    },
    "LA Lakers": {
        "LeBron James": (3, "B"), "Anthony Davis": (3, "B"), "Austin Reaves": (2, "O"),
        "D'Angelo Russell": (2, "O"), "Rui Hachimura": (1, "O"), "Gabe Vincent": (1, "O"),
        "Jarred Vanderbilt": (1, "D"), "Max Christie": (1, "D"),
    },
    "Memphis": {
        "Ja Morant": (3, "O"), "Desmond Bane": (2, "O"), "Jaren Jackson Jr": (3, "D"),
        "Marcus Smart": (2, "D"), "Santi Aldama": (1, "B"), "Luke Kennard": (1, "O"),
        "Brandon Clarke": (1, "D"), "Jake LaRavia": (1, "B"),
    },
    "Miami": {
        "Jimmy Butler": (3, "B"), "Bam Adebayo": (3, "D"), "Tyler Herro": (2, "O"),
        "Terry Rozier": (2, "O"), "Jaime Jaquez Jr": (1, "B"), "Duncan Robinson": (1, "O"),
        "Nikola Jovic": (1, "O"), "Haywood Highsmith": (1, "D"),
    },
    "Milwaukee": {
        "Giannis Antetokounmpo": (3, "B"), "Damian Lillard": (3, "O"), "Khris Middleton": (2, "O"),
        "Brook Lopez": (2, "D"), "Bobby Portis": (1, "B"), "Pat Connaughton": (1, "O"),
        "AJ Green": (1, "O"), "Gary Trent Jr": (1, "O"),
    },
    "Minnesota": {
        "Anthony Edwards": (3, "O"), "Julius Randle": (2, "B"), "Rudy Gobert": (3, "D"),
        "Jaden McDaniels": (2, "D"), "Mike Conley": (1, "O"), "Naz Reid": (1, "B"),
        "Nickeil Alexander-Walker": (1, "O"), "Donte DiVincenzo": (1, "O"),
    },
    "New Orleans": {
        "Zion Williamson": (3, "O"), "Brandon Ingram": (3, "O"), "CJ McCollum": (2, "O"),
        "Dejounte Murray": (2, "B"), "Herb Jones": (2, "D"), "Trey Murphy III": (1, "O"),
        "Jose Alvarado": (1, "D"), "Daniel Theis": (1, "D"),
    },
    "New York": {
        "Jalen Brunson": (3, "O"), "Karl-Anthony Towns": (3, "B"), "Mikal Bridges": (2, "B"),
        "OG Anunoby": (2, "D"), "Josh Hart": (2, "B"), "Donte DiVincenzo": (1, "O"),
        "Mitchell Robinson": (1, "D"), "Miles McBride": (1, "D"),
    },
    "Oklahoma City": {
        "Shai Gilgeous-Alexander": (3, "O"), "Chet Holmgren": (3, "B"), "Jalen Williams": (2, "B"),
        "Luguentz Dort": (2, "D"), "Isaiah Hartenstein": (2, "D"), "Alex Caruso": (2, "D"),
        "Aaron Wiggins": (1, "B"), "Cason Wallace": (1, "D"),
    },
    "Orlando": {
        "Paolo Banchero": (3, "O"), "Franz Wagner": (3, "B"), "Jalen Suggs": (2, "D"),
        "Wendell Carter Jr": (2, "D"), "Kentavious Caldwell-Pope": (1, "D"), "Gary Harris": (1, "D"),
        "Cole Anthony": (1, "O"), "Jonathan Isaac": (1, "D"),
    },
    "Philadelphia": {
        "Joel Embiid": (3, "B"), "Tyrese Maxey": (3, "O"), "Paul George": (3, "B"),
        "Caleb Martin": (1, "D"), "Kelly Oubre Jr": (1, "O"), "Kyle Lowry": (1, "B"),
        "Andre Drummond": (1, "D"), "Eric Gordon": (1, "O"),
    },
    "Phoenix": {
        "Kevin Durant": (3, "O"), "Devin Booker": (3, "O"), "Bradley Beal": (2, "O"),
        "Jusuf Nurkic": (2, "D"), "Grayson Allen": (1, "O"), "Royce O'Neale": (1, "D"),
        "Josh Okogie": (1, "D"), "Tyus Jones": (1, "O"),
    },
    "Portland": {
        "Anfernee Simons": (2, "O"), "Scoot Henderson": (2, "O"), "Jerami Grant": (2, "B"),
        "Deandre Ayton": (2, "D"), "Deni Avdija": (1, "B"), "Shaedon Sharpe": (1, "O"),
        "Robert Williams III": (1, "D"), "Toumani Camara": (1, "D"),
    },
    "Sacramento": {
        "De'Aaron Fox": (3, "O"), "Domantas Sabonis": (3, "B"), "DeMar DeRozan": (2, "O"),
        "Keegan Murray": (2, "B"), "Kevin Huerter": (1, "O"), "Malik Monk": (1, "O"),
        "Trey Lyles": (1, "B"), "Keon Ellis": (1, "D"),
    },
    "San Antonio": {
        "Victor Wembanyama": (3, "B"), "Devin Vassell": (2, "O"), "Jeremy Sochan": (2, "D"),
        "Keldon Johnson": (1, "O"), "Tre Jones": (1, "B"), "Zach Collins": (1, "D"),
        "Harrison Barnes": (1, "B"), "Malaki Branham": (1, "O"),
    },
    "Toronto": {
        "Scottie Barnes": (3, "B"), "RJ Barrett": (2, "O"), "Immanuel Quickley": (2, "O"),
        "Jakob Poeltl": (2, "D"), "Gradey Dick": (1, "O"), "Chris Boucher": (1, "D"),
        "Bruce Brown": (1, "B"), "Ochai Agbaji": (1, "D"),
    },
    "Utah": {
        "Lauri Markkanen": (3, "O"), "Collin Sexton": (2, "O"), "Jordan Clarkson": (2, "O"),
        "John Collins": (2, "B"), "Walker Kessler": (2, "D"), "Keyonte George": (1, "O"),
        "Taylor Hendricks": (1, "B"), "Brice Sensabaugh": (1, "O"),
    },
    "Washington": {
        "Jordan Poole": (2, "O"), "Kyle Kuzma": (2, "O"), "Bilal Coulibaly": (2, "D"),
        "Alex Sarr": (2, "D"), "Malcolm Brogdon": (1, "O"), "Corey Kispert": (1, "O"),
        "Jonas Valanciunas": (1, "D"), "Carlton Carrington": (1, "O"),
    },
}

# ========== TEAM STATS (Net Rating, Def Rank, Pace, etc.) ==========
TEAM_STATS = {
    "Atlanta": {"net_rating": -1.8, "off_rating": 115.2, "def_rating": 117.0, "def_rank": 21, "pace": 101.2, "ppg": 118.5, "opp_ppg": 120.3, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Southeast", "three_pa": 38.5, "three_pct": 0.365, "oreb_pct": 27.5, "tov_pct": 13.2, "ft_rate": 0.25, "reb_rate": 49.5},
    "Boston": {"net_rating": 11.2, "off_rating": 122.5, "def_rating": 111.3, "def_rank": 2, "pace": 99.8, "ppg": 120.5, "opp_ppg": 109.3, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Atlantic", "three_pa": 42.5, "three_pct": 0.385, "oreb_pct": 24.2, "tov_pct": 11.8, "ft_rate": 0.22, "reb_rate": 50.2},
    "Brooklyn": {"net_rating": -3.2, "off_rating": 111.5, "def_rating": 114.7, "def_rank": 22, "pace": 96.3, "ppg": 108.2, "opp_ppg": 111.4, "home_win_pct": 0.38, "away_win_pct": 0.28, "division": "Atlantic", "three_pa": 35.8, "three_pct": 0.358, "oreb_pct": 26.8, "tov_pct": 13.5, "ft_rate": 0.24, "reb_rate": 48.8},
    "Charlotte": {"net_rating": -5.5, "off_rating": 109.8, "def_rating": 115.3, "def_rank": 25, "pace": 100.5, "ppg": 110.5, "opp_ppg": 116.0, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Southeast", "three_pa": 36.2, "three_pct": 0.342, "oreb_pct": 28.0, "tov_pct": 14.0, "ft_rate": 0.23, "reb_rate": 49.0},
    "Chicago": {"net_rating": -2.5, "off_rating": 112.8, "def_rating": 115.3, "def_rank": 18, "pace": 98.5, "ppg": 112.0, "opp_ppg": 114.5, "home_win_pct": 0.45, "away_win_pct": 0.30, "division": "Central", "three_pa": 34.5, "three_pct": 0.355, "oreb_pct": 27.2, "tov_pct": 13.0, "ft_rate": 0.24, "reb_rate": 49.2},
    "Cleveland": {"net_rating": 9.8, "off_rating": 118.5, "def_rating": 108.7, "def_rank": 1, "pace": 97.2, "ppg": 116.8, "opp_ppg": 107.0, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Central", "three_pa": 37.0, "three_pct": 0.378, "oreb_pct": 26.5, "tov_pct": 12.2, "ft_rate": 0.26, "reb_rate": 51.0},
    "Dallas": {"net_rating": 3.5, "off_rating": 116.2, "def_rating": 112.7, "def_rank": 12, "pace": 99.8, "ppg": 117.5, "opp_ppg": 114.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest", "three_pa": 40.2, "three_pct": 0.362, "oreb_pct": 25.8, "tov_pct": 12.5, "ft_rate": 0.24, "reb_rate": 49.5},
    "Denver": {"net_rating": 4.2, "off_rating": 117.8, "def_rating": 113.6, "def_rank": 15, "pace": 98.5, "ppg": 116.2, "opp_ppg": 112.0, "home_win_pct": 0.68, "away_win_pct": 0.45, "division": "Northwest", "three_pa": 36.5, "three_pct": 0.372, "oreb_pct": 28.5, "tov_pct": 12.8, "ft_rate": 0.27, "reb_rate": 51.5},
    "Detroit": {"net_rating": -6.2, "off_rating": 110.5, "def_rating": 116.7, "def_rank": 27, "pace": 99.2, "ppg": 110.8, "opp_ppg": 117.0, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central", "three_pa": 35.0, "three_pct": 0.338, "oreb_pct": 29.0, "tov_pct": 14.2, "ft_rate": 0.23, "reb_rate": 49.8},
    "Golden State": {"net_rating": 2.8, "off_rating": 115.5, "def_rating": 112.7, "def_rank": 11, "pace": 100.2, "ppg": 115.8, "opp_ppg": 113.0, "home_win_pct": 0.62, "away_win_pct": 0.38, "division": "Pacific", "three_pa": 41.5, "three_pct": 0.375, "oreb_pct": 24.5, "tov_pct": 13.5, "ft_rate": 0.22, "reb_rate": 48.5},
    "Houston": {"net_rating": 3.2, "off_rating": 113.8, "def_rating": 110.6, "def_rank": 5, "pace": 99.5, "ppg": 114.2, "opp_ppg": 111.0, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Southwest", "three_pa": 38.0, "three_pct": 0.352, "oreb_pct": 30.5, "tov_pct": 13.8, "ft_rate": 0.28, "reb_rate": 52.0},
    "Indiana": {"net_rating": 2.5, "off_rating": 118.2, "def_rating": 115.7, "def_rank": 24, "pace": 103.5, "ppg": 121.5, "opp_ppg": 119.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Central", "three_pa": 39.5, "three_pct": 0.368, "oreb_pct": 26.0, "tov_pct": 12.0, "ft_rate": 0.25, "reb_rate": 49.0},
    "LA Clippers": {"net_rating": 1.5, "off_rating": 113.5, "def_rating": 112.0, "def_rank": 10, "pace": 98.5, "ppg": 112.8, "opp_ppg": 111.3, "home_win_pct": 0.52, "away_win_pct": 0.38, "division": "Pacific", "three_pa": 37.5, "three_pct": 0.358, "oreb_pct": 27.0, "tov_pct": 13.2, "ft_rate": 0.26, "reb_rate": 50.0},
    "LA Lakers": {"net_rating": 1.8, "off_rating": 114.2, "def_rating": 112.4, "def_rank": 13, "pace": 99.8, "ppg": 115.5, "opp_ppg": 113.7, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific", "three_pa": 35.5, "three_pct": 0.358, "oreb_pct": 28.0, "tov_pct": 13.0, "ft_rate": 0.27, "reb_rate": 50.5},
    "Memphis": {"net_rating": 2.2, "off_rating": 115.8, "def_rating": 113.6, "def_rank": 16, "pace": 100.8, "ppg": 117.2, "opp_ppg": 115.0, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Southwest", "three_pa": 36.0, "three_pct": 0.348, "oreb_pct": 29.5, "tov_pct": 14.5, "ft_rate": 0.28, "reb_rate": 51.2},
    "Miami": {"net_rating": 0.5, "off_rating": 111.8, "def_rating": 111.3, "def_rank": 8, "pace": 97.5, "ppg": 110.5, "opp_ppg": 110.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast", "three_pa": 37.0, "three_pct": 0.362, "oreb_pct": 26.5, "tov_pct": 12.5, "ft_rate": 0.24, "reb_rate": 49.5},
    "Milwaukee": {"net_rating": 3.8, "off_rating": 116.5, "def_rating": 112.7, "def_rank": 14, "pace": 100.5, "ppg": 118.2, "opp_ppg": 114.4, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Central", "three_pa": 38.5, "three_pct": 0.365, "oreb_pct": 27.5, "tov_pct": 13.0, "ft_rate": 0.28, "reb_rate": 51.0},
    "Minnesota": {"net_rating": 5.5, "off_rating": 113.2, "def_rating": 107.7, "def_rank": 3, "pace": 97.8, "ppg": 112.5, "opp_ppg": 107.0, "home_win_pct": 0.65, "away_win_pct": 0.50, "division": "Northwest", "three_pa": 38.0, "three_pct": 0.358, "oreb_pct": 28.0, "tov_pct": 13.2, "ft_rate": 0.25, "reb_rate": 52.5},
    "New Orleans": {"net_rating": -2.0, "off_rating": 112.5, "def_rating": 114.5, "def_rank": 19, "pace": 99.0, "ppg": 113.2, "opp_ppg": 115.2, "home_win_pct": 0.45, "away_win_pct": 0.28, "division": "Southwest", "three_pa": 36.5, "three_pct": 0.352, "oreb_pct": 28.5, "tov_pct": 13.5, "ft_rate": 0.26, "reb_rate": 50.5},
    "New York": {"net_rating": 5.8, "off_rating": 117.2, "def_rating": 111.4, "def_rank": 6, "pace": 98.5, "ppg": 117.8, "opp_ppg": 112.0, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic", "three_pa": 39.5, "three_pct": 0.372, "oreb_pct": 29.0, "tov_pct": 12.5, "ft_rate": 0.26, "reb_rate": 52.0},
    "Oklahoma City": {"net_rating": 10.5, "off_rating": 118.8, "def_rating": 108.3, "def_rank": 4, "pace": 99.5, "ppg": 119.5, "opp_ppg": 109.0, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Northwest", "three_pa": 40.0, "three_pct": 0.378, "oreb_pct": 28.5, "tov_pct": 11.5, "ft_rate": 0.27, "reb_rate": 52.5},
    "Orlando": {"net_rating": 4.8, "off_rating": 110.5, "def_rating": 105.7, "def_rank": 2, "pace": 96.5, "ppg": 108.5, "opp_ppg": 103.7, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southeast", "three_pa": 35.0, "three_pct": 0.345, "oreb_pct": 30.5, "tov_pct": 12.8, "ft_rate": 0.28, "reb_rate": 53.0},
    "Philadelphia": {"net_rating": 1.2, "off_rating": 113.5, "def_rating": 112.3, "def_rank": 9, "pace": 98.2, "ppg": 113.8, "opp_ppg": 112.6, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Atlantic", "three_pa": 36.0, "three_pct": 0.355, "oreb_pct": 27.5, "tov_pct": 13.5, "ft_rate": 0.30, "reb_rate": 50.5},
    "Phoenix": {"net_rating": 2.5, "off_rating": 115.8, "def_rating": 113.3, "def_rank": 17, "pace": 98.8, "ppg": 115.2, "opp_ppg": 112.7, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific", "three_pa": 38.5, "three_pct": 0.368, "oreb_pct": 26.0, "tov_pct": 12.8, "ft_rate": 0.25, "reb_rate": 49.0},
    "Portland": {"net_rating": -6.8, "off_rating": 108.5, "def_rating": 115.3, "def_rank": 28, "pace": 98.2, "ppg": 107.5, "opp_ppg": 114.3, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pa": 37.0, "three_pct": 0.338, "oreb_pct": 27.0, "tov_pct": 14.5, "ft_rate": 0.22, "reb_rate": 48.5},
    "Sacramento": {"net_rating": -1.2, "off_rating": 114.5, "def_rating": 115.7, "def_rank": 23, "pace": 100.5, "ppg": 117.8, "opp_ppg": 119.0, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Pacific", "three_pa": 36.5, "three_pct": 0.362, "oreb_pct": 27.2, "tov_pct": 13.8, "ft_rate": 0.24, "reb_rate": 49.8},
    "San Antonio": {"net_rating": -4.5, "off_rating": 111.8, "def_rating": 116.3, "def_rank": 26, "pace": 99.8, "ppg": 112.5, "opp_ppg": 117.0, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest", "three_pa": 37.8, "three_pct": 0.345, "oreb_pct": 28.5, "tov_pct": 14.2, "ft_rate": 0.23, "reb_rate": 50.0},
    "Toronto": {"net_rating": -3.2, "off_rating": 112.2, "def_rating": 115.4, "def_rank": 20, "pace": 99.5, "ppg": 113.5, "opp_ppg": 116.7, "home_win_pct": 0.42, "away_win_pct": 0.30, "division": "Atlantic", "three_pa": 38.0, "three_pct": 0.348, "oreb_pct": 27.8, "tov_pct": 13.5, "ft_rate": 0.23, "reb_rate": 49.2},
    "Utah": {"net_rating": -8.5, "off_rating": 108.5, "def_rating": 117.0, "def_rank": 29, "pace": 100.8, "ppg": 108.2, "opp_ppg": 116.7, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Northwest", "three_pa": 39.0, "three_pct": 0.335, "oreb_pct": 26.5, "tov_pct": 15.0, "ft_rate": 0.22, "reb_rate": 48.0},
    "Washington": {"net_rating": -9.2, "off_rating": 107.8, "def_rating": 117.0, "def_rank": 30, "pace": 101.2, "ppg": 108.5, "opp_ppg": 117.7, "home_win_pct": 0.28, "away_win_pct": 0.15, "division": "Southeast", "three_pa": 35.5, "three_pct": 0.332, "oreb_pct": 26.0, "tov_pct": 15.2, "ft_rate": 0.21, "reb_rate": 47.5},
}

# ========== TEAM LOCATIONS (lat, lon) ==========
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

KALSHI_ABBREV_MAP = {
    "ATL": "Atlanta", "BOS": "Boston", "BKN": "Brooklyn", "CHA": "Charlotte", "CHI": "Chicago", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GSW": "Golden State", "HOU": "Houston", "IND": "Indiana",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "MEM": "Memphis", "MIA": "Miami", "MIL": "Milwaukee", "MIN": "Minnesota",
    "NOP": "New Orleans", "NYK": "New York", "OKC": "Oklahoma City", "ORL": "Orlando", "PHI": "Philadelphia",
    "PHX": "Phoenix", "POR": "Portland", "SAC": "Sacramento", "SAS": "San Antonio", "TOR": "Toronto", "UTA": "Utah", "WAS": "Washington"
}

# ========== INJURY FUNCTIONS ==========
def get_star_rating(player_name, team):
    """Get star tier and type for a player - flexible matching"""
    team_stars = STAR_PLAYERS.get(team, {})
    player_name_lower = player_name.lower().strip()
    player_parts = player_name_lower.split()
    player_last = player_parts[-1] if player_parts else ""
    player_first = player_parts[0] if player_parts else ""
    
    for star_name, (tier, ptype) in team_stars.items():
        star_lower = star_name.lower()
        star_parts = star_lower.split()
        star_last = star_parts[-1] if star_parts else ""
        star_first = star_parts[0] if star_parts else ""
        
        if star_lower == player_name_lower: return tier, ptype
        if star_last == player_last and len(star_last) > 2: return tier, ptype
        if star_first == player_first and player_last and star_last.startswith(player_last[0]): return tier, ptype
        if star_lower in player_name_lower or player_name_lower in star_lower: return tier, ptype
    
    return 0, "B"

def calculate_weighted_injuries(team, injury_list):
    """Calculate weighted injury score with star system"""
    weighted_score, offensive_score, defensive_score, star_details = 0, 0, 0, []
    
    for injury_str in injury_list:
        player_name = injury_str.split("(")[0].strip()
        status = injury_str.split("(")[1].replace(")", "").strip() if "(" in injury_str else "Out"
        tier, ptype = get_star_rating(player_name, team)
        
        weight = {3: 3.0, 2: 2.0, 1: 1.0}.get(tier, 0.5)
        stars = {3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐"}.get(tier, "")
        
        if any(x in status for x in ["GTD", "Game Time", "Questionable", "Doubtful"]): weight *= 0.5
        
        weighted_score += weight
        if ptype == "O": offensive_score += weight
        elif ptype == "D": defensive_score += weight
        else: offensive_score += weight * 0.5; defensive_score += weight * 0.5
        
        name_parts = player_name.split()
        short_name = f"{name_parts[0][0]}. {name_parts[-1]}" if len(name_parts) >= 2 else player_name
        star_details.append({"name": short_name, "full_name": player_name, "status": status, "tier": tier, "stars": stars, "type": ptype, "weight": weight})
    
    return {"total": weighted_score, "offensive": offensive_score, "defensive": defensive_score, "details": star_details, "count": len(injury_list)}

@st.cache_data(ttl=1800)
def fetch_nba_injuries():
    """Scrape NBA injuries from ESPN"""
    try:
        url = "https://www.espn.com/nba/injuries"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        injuries = {}
        
        # Find all team sections
        for table in soup.find_all('div', class_='ResponsiveTable'):
            header = table.find_previous('div', class_='Table__Title')
            if not header: continue
            
            raw_team = header.text.strip()
            team_name = ESPN_TEAM_MAP.get(raw_team, None)
            
            if not team_name:
                for espn_name, our_name in ESPN_TEAM_MAP.items():
                    if any(x in raw_team for x in espn_name.split()):
                        team_name = our_name
                        break
            
            if not team_name: continue
            
            players = []
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    player = cells[0].text.strip()
                    status = cells[2].text.strip() if len(cells) > 2 else "Out"
                    if player: players.append(f"{player} ({status})")
            
            if players: injuries[team_name] = players
        
        return injuries
    except Exception as e:
        st.warning(f"ESPN injury scrape failed: {e}")
        return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    """Get rest days from NBA schedule - returns estimated rest"""
    return {team: 2 for team in TEAM_STATS.keys()}

def calculate_travel_distance(away_team, home_team):
    """Calculate travel distance in miles"""
    if away_team not in TEAM_LOCATIONS or home_team not in TEAM_LOCATIONS:
        return 0
    lat1, lon1 = TEAM_LOCATIONS[away_team]
    lat2, lon2 = TEAM_LOCATIONS[home_team]
    R = 3959
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)))

# ========== KALSHI API ==========
@st.cache_data(ttl=300)
def fetch_kalshi_nba_markets():
    """Fetch NBA markets from Kalshi"""
    markets = {"moneyline": [], "totals": [], "spreads": []}
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/events"
        params = {"series_ticker": "KXNBA", "status": "open", "limit": 200}
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            events = response.json().get("events", [])
            
            for event in events:
                event_ticker = event.get("event_ticker", "")
                title = event.get("title", "")
                
                # Parse date from title or ticker
                game_date = None
                date_match = re.search(r'(\d{1,2}/\d{1,2})', title)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        month, day = map(int, date_str.split('/'))
                        year = datetime.now().year
                        game_date = f"{year}-{month:02d}-{day:02d}"
                    except: pass
                
                # Skip non-today games
                if game_date and game_date != today:
                    continue
                
                # Fetch markets for this event
                markets_url = f"https://api.elections.kalshi.com/trade-api/v2/events/{event_ticker}/markets"
                markets_resp = requests.get(markets_url, timeout=10)
                
                if markets_resp.status_code == 200:
                    event_markets = markets_resp.json().get("markets", [])
                    
                    for mkt in event_markets:
                        ticker = mkt.get("ticker", "")
                        mkt_title = mkt.get("title", title)
                        yes_price = (mkt.get("yes_bid", 50) + mkt.get("yes_ask", 50)) / 2
                        
                        # Parse teams
                        teams = re.findall(r'\b([A-Z]{3})\b', ticker)
                        if len(teams) >= 2:
                            away = KALSHI_ABBREV_MAP.get(teams[0], teams[0])
                            home = KALSHI_ABBREV_MAP.get(teams[1], teams[1])
                        else:
                            continue
                        
                        market_data = {
                            "ticker": ticker,
                            "title": mkt_title,
                            "yes_price": yes_price,
                            "home_team": home,
                            "away_team": away,
                            "game_date": game_date or today,
                        }
                        
                        # Categorize market type
                        if "O/U" in ticker or "over" in mkt_title.lower() or "under" in mkt_title.lower():
                            total_match = re.search(r'(\d+\.?\d*)', mkt_title)
                            market_data["line"] = float(total_match.group(1)) if total_match else 220
                            markets["totals"].append(market_data)
                        elif any(x in ticker for x in ["-", "+"]) or "spread" in mkt_title.lower():
                            spread_match = re.search(r'[+-]?(\d+\.?\d*)', mkt_title)
                            market_data["line"] = float(spread_match.group(1)) if spread_match else 5
                            markets["spreads"].append(market_data)
                        else:
                            markets["moneyline"].append(market_data)
    
    except Exception as e:
        st.error(f"Kalshi API error: {e}")
    
    return markets

# ========== EDGE CALCULATION ==========
def calculate_edge(home, away, kalshi_price, home_rest, away_rest, home_injury_data, away_injury_data, travel_miles, ref_bias, weights):
    """Calculate model probability and edge vs Kalshi"""
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    if not home_stats or not away_stats:
        return {"home_win_prob": 50, "edge": 0, "factors": {}, "raw": {}, "recommendation": "NO TRADE", "confidence": "LOW", "injury_details": {"home": home_injury_data, "away": away_injury_data}}
    
    factors = {}
    raw = {}
    
    # 1. Rest advantage
    rest_diff = home_rest - away_rest
    factors["rest"] = rest_diff * 2.5 * weights.get("rest", 1.0)
    raw["home_rest"], raw["away_rest"] = home_rest, away_rest
    raw["rest_b2b_home"] = "B2B" if home_rest <= 1 else ""
    raw["rest_b2b_away"] = "B2B" if away_rest <= 1 else ""
    
    # 2. Defense advantage
    def_diff = away_stats.get("def_rank", 15) - home_stats.get("def_rank", 15)
    factors["defense"] = def_diff * 0.15 * weights.get("defense", 1.0)
    raw["home_def_rank"], raw["away_def_rank"] = home_stats.get("def_rank", 15), away_stats.get("def_rank", 15)
    
    # 3. Injury impact (weighted)
    injury_diff = away_injury_data["total"] - home_injury_data["total"]
    factors["injury"] = injury_diff * 1.5 * weights.get("injury", 1.0)
    raw["home_injuries"], raw["away_injuries"] = home_injury_data["count"], away_injury_data["count"]
    raw["home_inj_weighted"], raw["away_inj_weighted"] = home_injury_data["total"], away_injury_data["total"]
    
    # 4. Pace
    pace_diff = home_stats.get("pace", 100) - away_stats.get("pace", 100)
    factors["pace"] = pace_diff * 0.1 * weights.get("pace", 1.0)
    raw["home_pace"], raw["away_pace"] = home_stats.get("pace", 100), away_stats.get("pace", 100)
    
    # 5. Net rating
    net_diff = home_stats.get("net_rating", 0) - away_stats.get("net_rating", 0)
    factors["net_rating"] = net_diff * 0.8 * weights.get("net_rating", 1.0)
    raw["home_net"], raw["away_net"] = home_stats.get("net_rating", 0), away_stats.get("net_rating", 0)
    
    # 6. Travel
    travel_factor = min(travel_miles / 1000, 3) * 0.8 * weights.get("travel", 1.0)
    factors["travel"] = travel_factor
    raw["travel_miles"] = travel_miles
    
    # 7. Home/Away splits
    split_diff = home_stats.get("home_win_pct", 0.5) - away_stats.get("away_win_pct", 0.5)
    factors["splits"] = split_diff * 8 * weights.get("splits", 1.0)
    raw["home_win_pct"], raw["away_win_pct"] = home_stats.get("home_win_pct", 0.5), away_stats.get("away_win_pct", 0.5)
    
    # 8. Division rivalry
    is_division = home_stats.get("division") == away_stats.get("division")
    factors["division"] = -1.5 if is_division else 0
    factors["division"] *= weights.get("division", 1.0)
    raw["is_division_rival"] = is_division
    
    # 9. Ref bias (manual)
    factors["refs"] = ref_bias * weights.get("refs", 1.0)
    raw["ref_bias"] = ref_bias
    
    # 10. FT Rate
    ft_diff = home_stats.get("ft_rate", 0.25) - away_stats.get("ft_rate", 0.25)
    factors["ft_rate"] = ft_diff * 15 * weights.get("ft_rate", 1.0)
    raw["home_ft_rate"], raw["away_ft_rate"] = home_stats.get("ft_rate", 0.25), away_stats.get("ft_rate", 0.25)
    
    # 11. Rebounding
    reb_diff = home_stats.get("reb_rate", 50) - away_stats.get("reb_rate", 50)
    factors["rebounding"] = reb_diff * 0.2 * weights.get("rebounding", 1.0)
    raw["home_reb"], raw["away_reb"] = home_stats.get("reb_rate", 50), away_stats.get("reb_rate", 50)
    
    # 12. 3PT shooting
    three_diff = (home_stats.get("three_pct", 0.35) - away_stats.get("three_pct", 0.35)) * 100
    factors["three_pt"] = three_diff * 0.3 * weights.get("three_pt", 1.0)
    raw["home_3pct"], raw["away_3pct"] = home_stats.get("three_pct", 0.35), away_stats.get("three_pct", 0.35)
    
    # Home court base
    base_home_adv = 3.5
    total_adjustment = sum(factors.values())
    
    home_win_prob = 50 + base_home_adv + total_adjustment
    home_win_prob = max(15, min(85, home_win_prob))
    
    edge = home_win_prob - kalshi_price
    
    if edge > 3:
        rec, conf = "BUY YES", "HIGH" if edge > 6 else "MED"
    elif edge < -3:
        rec, conf = "BUY NO", "HIGH" if edge < -6 else "MED"
    else:
        rec, conf = "NO TRADE", "LOW"
    
    return {
        "home_win_prob": home_win_prob,
        "edge": edge,
        "factors": factors,
        "raw": raw,
        "recommendation": rec,
        "confidence": conf,
        "injury_details": {"home": home_injury_data, "away": away_injury_data}
    }

def calculate_kelly(win_prob, price, bankroll, fraction):
    """Kelly criterion bet sizing"""
    p = win_prob / 100
    b = (100 - price) / price if price > 0 else 1
    kelly = (p * b - (1 - p)) / b if b > 0 else 0
    kelly = max(0, kelly)
    adj_kelly = kelly * fraction
    bet_amount = bankroll * adj_kelly
    ev = bet_amount * (p * b - (1 - p))
    return {"kelly_pct": round(kelly * 100, 2), "adj_kelly_pct": round(adj_kelly * 100, 2), "bet_amount": round(bet_amount, 2), "ev_per_dollar": round(p * b - (1 - p), 3), "ev_on_bet": round(ev, 2)}

# ========== UI ==========
st.title("🏀 NBA Kalshi Edge Finder")
st.caption("12-Factor Model • Star-Weighted Injuries • Today's Games Only")

# Sidebar
st.sidebar.header("🎚️ Factor Weights")

with st.sidebar.expander("🏀 Core Factors", expanded=True):
    w_rest = st.slider("🛏️ Rest Days", 0.0, 2.0, 1.0, 0.1, key="w1", help="Rest advantage. Back-to-backs = fatigue.")
    w_def = st.slider("🛡️ Defense Rank", 0.0, 2.0, 1.0, 0.1, key="w2", help="Defensive rating differential.")
    w_inj = st.slider("🏥 Injuries (Star-Weighted)", 0.0, 2.0, 1.0, 0.1, key="w3", help="⭐⭐⭐=3x, ⭐⭐=2x, ⭐=1x, bench=0.5x")
    w_pace = st.slider("🏃 Pace", 0.0, 2.0, 1.0, 0.1, key="w4", help="Game tempo differential.")
    w_net = st.slider("📊 Net Rating", 0.0, 2.0, 1.0, 0.1, key="w5", help="Overall team quality.")
    w_travel = st.slider("✈️ Travel Fatigue", 0.0, 2.0, 1.0, 0.1, key="w6", help="Miles traveled by away team.")

with st.sidebar.expander("📈 Advanced Factors", expanded=True):
    w_splits = st.slider("🏠 Home/Away Splits", 0.0, 2.0, 1.0, 0.1, key="w7", help="Win % at home vs away.")
    w_div = st.slider("⚔️ Division Rivalry", 0.0, 2.0, 1.0, 0.1, key="w8", help="Same division = closer games.")
    w_refs = st.slider("👨‍⚖️ Ref Bias", 0.0, 2.0, 1.0, 0.1, key="w9", help="Manual ref crew adjustment.")
    w_ft = st.slider("🎯 FT Rate", 0.0, 2.0, 1.0, 0.1, key="w10", help="Free throw rate differential.")
    w_reb = st.slider("🏀 Rebounding", 0.0, 2.0, 1.0, 0.1, key="w11", help="Rebound rate differential.")
    w_three = st.slider("🎯 3PT Shooting", 0.0, 2.0, 1.0, 0.1, key="w12", help="3-point % differential.")

weights = {"rest": w_rest, "defense": w_def, "injury": w_inj, "pace": w_pace, "net_rating": w_net, "travel": w_travel, "splits": w_splits, "division": w_div, "refs": w_refs, "ft_rate": w_ft, "rebounding": w_reb, "three_pt": w_three}

with st.sidebar.expander("⚙️ Settings"):
    default_home_rest = st.number_input("Default Home Rest", 1, 5, 2)
    default_away_rest = st.number_input("Default Away Rest", 1, 5, 2)
    default_ref_bias = st.slider("Ref Bias (+ = home)", -3.0, 3.0, 0.0, 0.5)
    min_edge = st.slider("Min Edge to Show", 0.0, 10.0, 1.0, 0.5)

with st.sidebar.expander("💰 Kelly Settings"):
    bankroll = st.number_input("Bankroll ($)", 100, 100000, 1000)
    kelly_fraction = st.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load data
markets = fetch_kalshi_nba_markets()
injuries = fetch_nba_injuries()
rest_days = fetch_rest_days()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Data Status")
st.sidebar.write(f"**ML:** {len(markets['moneyline'])} | **TOT:** {len(markets['totals'])} | **SPR:** {len(markets['spreads'])}")
st.sidebar.write(f"**Injuries:** {len(injuries)} teams loaded")

# Debug injuries
with st.sidebar.expander("🔍 Injury Debug"):
    if injuries:
        star_count = 0
        for team, players in injuries.items():
            for p in players:
                name = p.split("(")[0].strip()
                tier, _ = get_star_rating(name, team)
                if tier >= 2:
                    star_count += 1
                    st.write(f"{'⭐'*tier} {name} ({team})")
        if star_count == 0:
            st.write("No major stars on injury report")
    else:
        st.write("❌ ESPN not loaded")

# Main content - Top Edges
st.markdown("---")
st.subheader("🎯 Top 3 Edges Today")

all_edges = []
for game in markets['moneyline']:
    home, away = game['home_team'], game['away_team']
    home_inj_data = calculate_weighted_injuries(home, injuries.get(home, []))
    away_inj_data = calculate_weighted_injuries(away, injuries.get(away, []))
    travel = calculate_travel_distance(away, home)
    h_rest = rest_days.get(home, default_home_rest)
    a_rest = rest_days.get(away, default_away_rest)
    
    analysis = calculate_edge(home, away, game['yes_price'], h_rest, a_rest, home_inj_data, away_inj_data, travel, default_ref_bias, weights)
    
    if abs(analysis['edge']) >= min_edge:
        kelly = calculate_kelly(
            analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob'],
            game['yes_price'] if analysis['recommendation'] == 'BUY YES' else 100 - game['yes_price'],
            bankroll, kelly_fraction
        )
        all_edges.append({
            "game": f"{away} @ {home}",
            "bet_team": home if analysis['recommendation'] == 'BUY YES' else away,
            "edge": abs(analysis['edge']),
            "rec": analysis['recommendation'],
            "bet_amount": kelly['bet_amount'],
            "conf": analysis['confidence']
        })

all_edges.sort(key=lambda x: x['edge'], reverse=True)
top3 = all_edges[:3]

if top3:
    cols = st.columns(3)
    for i, edge in enumerate(top3):
        with cols[i]:
            color = "🟢" if "YES" in edge['rec'] else "🔴"
            st.metric(f"{color} {edge['bet_team']}", f"+{edge['edge']:.1f}% Edge", f"${edge['bet_amount']:.0f} bet")
            st.caption(f"{edge['game']} | {edge['conf']}")
else:
    st.info("No edges above minimum threshold today.")

# Tabs
tab_ml, tab_tot, tab_spr = st.tabs(["💰 Moneyline", "📊 Totals", "📏 Spreads"])

with tab_ml:
    st.subheader("Moneyline Markets")
    
    if not markets['moneyline']:
        st.warning("No moneyline markets found for today.")
    
    for game in markets['moneyline']:
        home, away = game['home_team'], game['away_team']
        home_inj_list = injuries.get(home, [])
        away_inj_list = injuries.get(away, [])
        home_inj_data = calculate_weighted_injuries(home, home_inj_list)
        away_inj_data = calculate_weighted_injuries(away, away_inj_list)
        travel = calculate_travel_distance(away, home)
        h_rest = rest_days.get(home, default_home_rest)
        a_rest = rest_days.get(away, default_away_rest)
        
        analysis = calculate_edge(home, away, game['yes_price'], h_rest, a_rest, home_inj_data, away_inj_data, travel, default_ref_bias, weights)
        
        if abs(analysis['edge']) < min_edge:
            continue
        
        color = "🟢" if analysis['recommendation'] == 'BUY YES' else ("🔴" if analysis['recommendation'] == 'BUY NO' else "⚪")
        bet_team = home if analysis['recommendation'] == 'BUY YES' else away
        
        with st.expander(f"{color} {away} @ {home} | Edge: {analysis['edge']:+.1f}% | Bet: {bet_team}"):
            # Top metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kalshi Price", f"{game['yes_price']:.0f}¢ {home}")
            c2.metric("Model Prob", f"{analysis['home_win_prob']:.1f}%")
            c3.metric("Edge", f"{analysis['edge']:+.1f}%")
            c4.metric("Confidence", analysis['confidence'])
            
            # Kelly sizing
            kelly = calculate_kelly(
                analysis['home_win_prob'] if analysis['recommendation'] == 'BUY YES' else 100 - analysis['home_win_prob'],
                game['yes_price'] if analysis['recommendation'] == 'BUY YES' else 100 - game['yes_price'],
                bankroll, kelly_fraction
            )
            
            st.markdown("---")
            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.metric(f"💰 Bet {bet_team}", f"${kelly['bet_amount']:.2f}")
            kc2.metric("Kelly %", f"{kelly['adj_kelly_pct']}%")
            kc3.metric("EV/$", f"${kelly['ev_per_dollar']:.3f}")
            kc4.metric("Expected Value", f"${kelly['ev_on_bet']:+.2f}")
            
            # ========== DETAILED 12-FACTOR BREAKDOWN ==========
            st.markdown("---")
            st.markdown("### 📈 12-Factor Breakdown")
            
            f = analysis['factors']
            r = analysis['raw']
            
            # Row 1: Rest, Injuries, Defense, Pace
            fc1, fc2, fc3, fc4 = st.columns(4)
            
            # Rest
            rest_display = f"H:{r['home_rest']}d | A:{r['away_rest']}d"
            if r['rest_b2b_away']: rest_display += " ⚠️A-B2B"
            if r['rest_b2b_home']: rest_display += " ⚠️H-B2B"
            fc1.metric("🛏️ Rest", f"{f['rest']:+.2f}", rest_display)
            
            # Injuries with star breakdown
            inj_display = f"H:{r['home_inj_weighted']:.1f}★ | A:{r['away_inj_weighted']:.1f}★"
            fc2.metric("🏥 Injuries", f"{f['injury']:+.2f}", inj_display)
            
            # Defense
            fc3.metric("🛡️ Defense", f"{f['defense']:+.2f}", f"H:#{r['home_def_rank']} vs A:#{r['away_def_rank']}")
            
            # Pace
            fc4.metric("🏃 Pace", f"{f['pace']:+.2f}", f"H:{r['home_pace']:.1f} | A:{r['away_pace']:.1f}")
            
            # Row 2: Net Rating, Travel, Splits, Division
            fc5, fc6, fc7, fc8 = st.columns(4)
            fc5.metric("📊 Net Rating", f"{f['net_rating']:+.2f}", f"H:{r['home_net']:+.1f} | A:{r['away_net']:+.1f}")
            fc6.metric("✈️ Travel", f"{f['travel']:+.2f}", f"{r['travel_miles']} miles")
            fc7.metric("🏠 Splits", f"{f['splits']:+.2f}", f"H:{r['home_win_pct']:.0%} | A:{r['away_win_pct']:.0%}")
            fc8.metric("⚔️ Division", f"{f['division']:+.2f}", "Yes" if r['is_division_rival'] else "No")
            
            # Row 3: Refs, FT, Reb, 3PT
            fc9, fc10, fc11, fc12 = st.columns(4)
            fc9.metric("👨‍⚖️ Refs", f"{f['refs']:+.2f}", f"Bias: {r['ref_bias']:+.1f}")
            fc10.metric("🎯 FT Rate", f"{f['ft_rate']:+.2f}", f"H:{r['home_ft_rate']:.2f} | A:{r['away_ft_rate']:.2f}")
            fc11.metric("🏀 Rebounds", f"{f['rebounding']:+.2f}", f"H:{r['home_reb']:.1f}% | A:{r['away_reb']:.1f}%")
            fc12.metric("🎯 3PT", f"{f['three_pt']:+.2f}", f"H:{r['home_3pct']:.1%} | A:{r['away_3pct']:.1%}")
            
            # ========== INJURY REPORT WITH STARS ==========
            st.markdown("---")
            st.markdown("### 🏥 Injury Report (Star-Weighted)")
            
            inj_c1, inj_c2 = st.columns(2)
            
            with inj_c1:
                st.markdown(f"**{home}** (Total: {home_inj_data['total']:.1f}★)")
                if home_inj_data['details']:
                    for p in sorted(home_inj_data['details'], key=lambda x: x['tier'], reverse=True):
                        type_icon = "🔥" if p['type'] == "O" else ("🛡️" if p['type'] == "D" else "⚡")
                        st.write(f"{p['stars']} {p['full_name']} ({p['status']}) {type_icon}")
                else:
                    st.write("✅ Full strength")
            
            with inj_c2:
                st.markdown(f"**{away}** (Total: {away_inj_data['total']:.1f}★)")
                if away_inj_data['details']:
                    for p in sorted(away_inj_data['details'], key=lambda x: x['tier'], reverse=True):
                        type_icon = "🔥" if p['type'] == "O" else ("🛡️" if p['type'] == "D" else "⚡")
                        st.write(f"{p['stars']} {p['full_name']} ({p['status']}) {type_icon}")
                else:
                    st.write("✅ Full strength")

with tab_tot:
    st.subheader("Over/Under Totals")
    
    if not markets['totals']:
        st.warning("No totals markets found for today.")
    
    for game in markets['totals']:
        home, away = game['home_team'], game['away_team']
        line = game.get('line', 220)
        
        home_stats = TEAM_STATS.get(home, {})
        away_stats = TEAM_STATS.get(away, {})
        
        # Calculate projected total
        combined_pace = (home_stats.get('pace', 100) + away_stats.get('pace', 100)) / 2
        combined_ppg = home_stats.get('ppg', 110) + away_stats.get('ppg', 110)
        
        # Adjust for defense
        home_def_adj = (15 - home_stats.get('def_rank', 15)) * 0.3
        away_def_adj = (15 - away_stats.get('def_rank', 15)) * 0.3
        
        projected = combined_ppg - home_def_adj - away_def_adj
        edge = projected - line
        
        rec = "OVER" if edge > 2 else ("UNDER" if edge < -2 else "PASS")
        color = "🟢" if rec == "OVER" else ("🔴" if rec == "UNDER" else "⚪")
        
        with st.expander(f"{color} {away} @ {home} | Line: {line} | Edge: {edge:+.1f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi Line", f"{line}")
            c2.metric("Model Total", f"{projected:.1f}")
            c3.metric("Edge", f"{edge:+.1f} pts")
            
            st.markdown("---")
            st.markdown("**Factor Breakdown**")
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("🏃 Pace", f"{combined_pace:.1f}", f"H:{home_stats.get('pace',100):.1f} A:{away_stats.get('pace',100):.1f}")
            tc2.metric("📊 PPG", f"{combined_ppg:.1f}", f"H:{home_stats.get('ppg',110):.1f} A:{away_stats.get('ppg',110):.1f}")
            tc3.metric("🛡️ Def Ranks", f"{home_def_adj + away_def_adj:+.1f}", f"H:#{home_stats.get('def_rank',15)} A:#{away_stats.get('def_rank',15)}")
            tc4.metric("Recommendation", rec)

with tab_spr:
    st.subheader("Spread Markets")
    
    if not markets['spreads']:
        st.warning("No spread markets found for today.")
    
    for game in markets['spreads']:
        home, away = game['home_team'], game['away_team']
        line = game.get('line', 5)
        
        home_stats = TEAM_STATS.get(home, {})
        away_stats = TEAM_STATS.get(away, {})
        
        # Calculate projected spread
        net_diff = home_stats.get('net_rating', 0) - away_stats.get('net_rating', 0)
        home_court = 3.5
        projected_spread = net_diff + home_court
        
        edge = projected_spread - line
        
        rec = "HOME -" if edge > 2 else ("AWAY +" if edge < -2 else "PASS")
        color = "🟢" if "HOME" in rec else ("🔴" if "AWAY" in rec else "⚪")
        
        with st.expander(f"{color} {away} @ {home} | Line: {line} | Edge: {edge:+.1f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Kalshi Spread", f"{home} -{line}")
            c2.metric("Model Spread", f"{projected_spread:+.1f}")
            c3.metric("Edge", f"{edge:+.1f} pts")
            
            st.markdown("---")
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("📊 Net Ratings", f"{net_diff:+.1f}", f"H:{home_stats.get('net_rating',0):+.1f} A:{away_stats.get('net_rating',0):+.1f}")
            tc2.metric("🏠 Home Court", f"+{home_court}")
            tc3.metric("Recommendation", rec)

# Footer
st.markdown("---")
st.caption("⚠️ DISCLAIMER: For entertainment and educational purposes only. Not financial advice. You may lose money. Only bet what you can afford to lose.")
