# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

REFERENCE_THRESHOLD = 235.5  # Single reference line (can be replaced with live Kalshi line later)

cs1, cs2, cs3 = st.columns([1, 1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 12, 18, 24, 30], index=2, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")
cs3.markdown(f"**Line: {REFERENCE_THRESHOLD}**")

cush_data = []

for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    
    # HARD GATE: Skip if below minimum minutes
    if mins < 6:
        continue
    if mins < cush_min:
        continue
    
    total = g['total']
    pace = total / mins
    remaining_min = max(48 - mins, 1)
    
    # Project remaining points (NOT full-game linear)
    projected_final = round(total + pace * remaining_min)
    
    # Cushion against ONE line only
    if cush_side == "NO":
        cushion = REFERENCE_THRESHOLD - projected_final
    else:
        cushion = projected_final - REFERENCE_THRESHOLD
    
    # HARD GATE: Skip if cushion < 6
    if cushion < 6:
        continue
    
    # SCORING (max 10)
    # Cushion strength (0-4)
    if cushion >= 20:
        cushion_pts = 4
    elif cushion >= 12:
        cushion_pts = 3
    elif cushion >= 6:
        cushion_pts = 2
    elif cushion >= 2:
        cushion_pts = 1
    else:
        cushion_pts = 0
    
    # Time reliability (0-3)
    if mins >= 30:
        time_pts = 3
    elif mins >= 24:
        time_pts = 2
    elif mins >= 18:
        time_pts = 1
    else:
        time_pts = 0
    
    # Pace alignment (0-3)
    if cush_side == "NO":
        if pace < 4.6:
            pace_pts = 3
        elif pace < 4.9:
            pace_pts = 1
        else:
            pace_pts = 0
    else:
        if pace > 5.1:
            pace_pts = 3
        elif pace > 4.8:
            pace_pts = 1
        else:
            pace_pts = 0
    
    edge_score = cushion_pts + time_pts + pace_pts
    
    # Pace label for display
    if pace < 4.6:
        pace_label = "🟢 SLOW"
    elif pace < 4.9:
        pace_label = "🟡 AVG"
    elif pace < 5.1:
        pace_label = "🟠 FAST"
    else:
        pace_label = "🔴 SHOT"
    
    cush_data.append({
        "game": gk,
        "total": total,
        "mins": mins,
        "pace": pace,
        "pace_label": pace_label,
        "projected": projected_final,
        "cushion": cushion,
        "edge_score": edge_score,
        "cushion_pts": cushion_pts,
        "time_pts": time_pts,
        "pace_pts": pace_pts
    })

# Sort by edge score descending
cush_data.sort(key=lambda x: x['edge_score'], reverse=True)

if cush_data:
    # Header
    hcols = st.columns([2.5, 1, 1, 1.5, 1.5, 1])
    hcols[0].markdown("**Game**")
    hcols[1].markdown("**Current**")
    hcols[2].markdown("**Proj**")
    hcols[3].markdown(f"**Cushion vs {REFERENCE_THRESHOLD}**")
    hcols[4].markdown("**Pace**")
    hcols[5].markdown("**Score**")
    
    for cd in cush_data:
        rcols = st.columns([2.5, 1, 1, 1.5, 1.5, 1])
        
        gk = cd['game']
        g = games.get(gk, {})
        status = "FINAL" if g.get('status_type') == "STATUS_FINAL" else f"Q{g.get('period', 0)} {g.get('clock', '')}"
        
        rcols[0].markdown(f"**{gk.replace('@', ' @ ')}**<br><span style='color:#888;font-size:0.8em'>{status} | {cd['mins']:.0f}m</span>", unsafe_allow_html=True)
        rcols[1].write(f"{cd['total']} pts")
        rcols[2].write(f"{cd['projected']}")
        
        # Cushion display
        cush = cd['cushion']
        if cush >= 20:
            cush_color = "#00ff00"
            cush_icon = "🟢"
        elif cush >= 12:
            cush_color = "#88ff00"
            cush_icon = "🟢"
        elif cush >= 6:
            cush_color = "#ffff00"
            cush_icon = "🟡"
        else:
            cush_color = "#ff8800"
            cush_icon = "🟠"
        rcols[3].markdown(f"<span style='color:{cush_color};font-weight:bold'>+{cush:.0f}</span> {cush_icon}", unsafe_allow_html=True)
        
        # Pace display
        rcols[4].markdown(f"{cd['pace_label']}<br><span style='color:#aaa;font-size:0.85em'>{cd['pace']:.2f}/m</span>", unsafe_allow_html=True)
        
        # Score display
        score = cd['edge_score']
        if score >= 8:
            score_color = "#00ff00"
            score_tier = "🟢"
        elif score >= 6:
            score_color = "#ffff00"
            score_tier = "🟡"
        elif score >= 4:
            score_color = "#ff8800"
            score_tier = "🟠"
        else:
            score_color = "#ff0000"
            score_tier = "🔴"
        rcols[5].markdown(f"<span style='color:{score_color};font-weight:bold'>{score}/10</span> {score_tier}", unsafe_allow_html=True)
        
        # Expandable breakdown
        with st.expander(f"📊 Score breakdown: {gk.replace('@', ' @ ')}", expanded=False):
            st.markdown(f"""
            - **Cushion pts:** {cd['cushion_pts']}/4 (cushion = +{cd['cushion']:.0f})
            - **Time pts:** {cd['time_pts']}/3 ({cd['mins']:.0f} min played)
            - **Pace pts:** {cd['pace_pts']}/3 ({cd['pace']:.2f}/min {'< 4.6 ✓' if cush_side == 'NO' and cd['pace'] < 4.6 else '> 5.1 ✓' if cush_side == 'YES' and cd['pace'] > 5.1 else ''})
            - **Total:** {score}/10
            """)
    
    st.caption(f"📊 {len(cush_data)} games pass filters | Line: {REFERENCE_THRESHOLD} | Min: {cush_min}m | Side: {cush_side} | Cushion ≥ 6 required")
else:
    st.info(f"⚪ No games pass filters (need {cush_min}+ min AND +6 cushion vs {REFERENCE_THRESHOLD} for {cush_side})")
