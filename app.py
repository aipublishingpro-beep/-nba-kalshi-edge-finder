# Main output - EXPLICIT TEAM NAME
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
        
        conf = result['confidence']
        conf_color = "#00ff00" if conf == 'HIGH' else ("#ffff00" if conf == 'MEDIUM' else "#888888")
        
        # BIG RECOMMENDATION BOX AT TOP
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
