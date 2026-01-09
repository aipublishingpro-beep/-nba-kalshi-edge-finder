# ========== LEFT SIDEBAR - 12 SAUCES WITH HOVER TOOLTIPS ==========

st.sidebar.title("Settings")

# Color Key
st.sidebar.markdown("### Color Key")
st.sidebar.markdown("🟢 = BUY YES")
st.sidebar.markdown("🔴 = BUY NO")

st.sidebar.markdown("---")

# CORE FACTORS (6)
st.sidebar.markdown("### Core Factors")

w_rest = st.sidebar.slider(
    "Rest Days", 0.0, 2.0, 1.0, 0.1, key="w_rest",
    help="Days since last game. Back-to-backs (0-1 days) hurt performance. 2+ days rest = fresh legs. Bigger rest advantage = bigger edge."
)

w_def = st.sidebar.slider(
    "Defense Rating", 0.0, 2.0, 1.0, 0.1, key="w_def",
    help="Defensive efficiency ranking (1-30). Elite defenses (#1-5) force bad shots and turnovers. Poor defenses (#25-30) give up easy buckets."
)

w_inj = st.sidebar.slider(
    "Injuries", 0.0, 2.0, 1.0, 0.1, key="w_inj",
    help="Count of injured players per team. Star injuries (All-NBA) hurt more than bench players. More injuries = weaker team."
)

w_pace = st.sidebar.slider(
    "Pace", 0.0, 2.0, 1.0, 0.1, key="w_pace",
    help="Possessions per game. Fast teams (100+) push tempo and score more. Slow teams (96-98) grind it out. Pace mismatches create edges."
)

w_net = st.sidebar.slider(
    "Net Rating", 0.0, 2.0, 1.0, 0.1, key="w_net",
    help="Points scored minus points allowed per 100 possessions. THE core quality metric. +10 = elite, 0 = average, -10 = tanking."
)

w_travel = st.sidebar.slider(
    "Travel Distance", 0.0, 2.0, 1.0, 0.1, key="w_travel",
    help="Miles traveled by away team. Long flights (1500+ mi) cause fatigue. Cross-country trips + time zone changes = sluggish starts."
)

st.sidebar.markdown("---")

# ADVANCED FACTORS (6)
st.sidebar.markdown("### Advanced Factors")

w_splits = st.sidebar.slider(
    "Home/Away Splits", 0.0, 2.0, 1.0, 0.1, key="w_splits",
    help="Home vs away win percentages. Some teams dominate at home but struggle on road. Big splits = exploit home/away matchups."
)

w_div = st.sidebar.slider(
    "Divisional Rivalry", 0.0, 2.0, 1.0, 0.1, key="w_div",
    help="Same-division matchups are more competitive. Teams know each other's tendencies. Rivalries = extra intensity and closer games."
)

w_refs = st.sidebar.slider(
    "Ref Bias (Home)", 0.0, 2.0, 1.0, 0.1, key="w_refs",
    help="Home teams get ~2 more FTA/game on average. Some ref crews favor home crowds more. Higher weight = favor home team edge."
)

w_ft = st.sidebar.slider(
    "Free Throw Rate", 0.0, 2.0, 1.0, 0.1, key="w_ft",
    help="Free throw attempts per field goal attempt. Teams that attack the rim get to the line more. Free points = easy offense."
)

w_reb = st.sidebar.slider(
    "Rebounding", 0.0, 2.0, 1.0, 0.1, key="w_reb",
    help="Total rebound rate. Offensive rebounds = second-chance points. Defensive rebounds = end opponent possessions. Board control = game control."
)

w_three = st.sidebar.slider(
    "Three-Point Pct", 0.0, 2.0, 1.0, 0.1, key="w_three",
    help="Three-point shooting percentage. Hot shooting nights swing games. Teams shooting 38%+ from three are dangerous. Volume + accuracy = blowouts."
)

st.sidebar.markdown("---")

# Kelly Settings
st.sidebar.markdown("### Kelly Settings")
bankroll = st.sidebar.number_input("Bankroll ($)", value=1000, min_value=100, step=100)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05, 
    help="What fraction of Kelly to bet. Full Kelly (1.0) is aggressive. Quarter Kelly (0.25) is conservative. Most pros use 0.25-0.5.")
min_edge = st.sidebar.slider("Min Edge %", 0.0, 20.0, 5.0, 0.5,
    help="Minimum edge percentage to show a bet. Higher = fewer but stronger bets. Lower = more bets including marginal ones.")

# Pack weights into dict for easy passing
weights = {
    'rest': w_rest,
    'defense': w_def,
    'injuries': w_inj,
    'pace': w_pace,
    'net_rating': w_net,
    'travel': w_travel,
    'splits': w_splits,
    'divisional': w_div,
    'refs': w_refs,
    'ft_rate': w_ft,
    'rebounding': w_reb,
    'three_pct': w_three
}
