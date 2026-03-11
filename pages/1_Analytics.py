"""
📈 Full Analytics Dashboard
Charts, stats, and round history with CSV export.
Data comes from st.session_state.history (shared via ui/state.py).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ui.state import init_state, DEFAULT_BANKROLL
from ui.themes import get_theme_css, get_theme
from core.game import RESULT_WIN, RESULT_LOSE, RESULT_PUSH, RESULT_BUST, RESULT_BLACKJACK, RESULT_SURRENDER

init_state()
S = st.session_state

st.set_page_config(page_title="Analytics — Blackjack AI", page_icon="📈", layout="wide")
theme_name = S.get("theme", "casino_green")
st.markdown(get_theme_css(theme_name), unsafe_allow_html=True)
t = get_theme(theme_name)

st.title("📈 Session Analytics")

with st.sidebar:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("streamlit_app.py")
    if st.button("📈 Session Analytics", use_container_width=True, key="nav_analytics"):
        st.switch_page("pages/1_Analytics.py")
    if st.button("📖 Tutorial", use_container_width=True, key="nav_tutorial"):
        st.switch_page("pages/2_Tutorial.py")

if not S.history:
    st.info("No hands played yet. Go play some rounds, then come back here!")
    st.stop()

df = pd.DataFrame(S.history)

# ─── Summary Metrics ─────────────────────────────────────────
st.subheader("Overview")
m1, m2, m3, m4, m5, m6 = st.columns(6)
total_hands = len(df)
wins = len(df[df["Result"].isin([RESULT_WIN, RESULT_BLACKJACK])])
losses = len(df[df["Result"].isin([RESULT_LOSE, RESULT_BUST])])
pushes = len(df[df["Result"] == RESULT_PUSH])
net_profit = df["Payout"].sum()
avg_bet = df["Bet"].mean()

m1.metric("Hands Played", total_hands)
m2.metric("Wins", wins)
m3.metric("Losses", losses)
m4.metric("Pushes", pushes)
m5.metric("Net Profit", f"₹{net_profit:+,.0f}")
m6.metric("Avg Bet", f"₹{avg_bet:,.0f}")

# Secondary metrics row
s1, s2, s3, s4 = st.columns(4)
win_rate = (wins / total_hands * 100) if total_hands else 0
biggest_win = df["Payout"].max()
biggest_loss = df["Payout"].min()

# Streak calculation
streak = 0
if len(df) > 0:
    last = df.iloc[-1]["Result"]
    for _, row in df.iloc[::-1].iterrows():
        if row["Result"] == last:
            streak += 1
        else:
            break
    streak_label = f"{streak}{'W' if last in (RESULT_WIN, RESULT_BLACKJACK) else 'L'}"
else:
    streak_label = "—"

s1.metric("Win Rate", f"{win_rate:.1f}%")
s2.metric("Biggest Win", f"₹{biggest_win:+,.0f}")
s3.metric("Biggest Loss", f"₹{biggest_loss:+,.0f}")
s4.metric("Current Streak", streak_label)

st.divider()

# ─── Charts ──────────────────────────────────────────────────
chart_theme = "plotly_dark"
chart_height = 380
chart_margin = dict(l=40, r=20, t=40, b=40)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Bankroll", "Results", "Win Rate", "Actions", "Count vs Outcome", "Bet vs Outcome"
])

# 1. Bankroll over time
with tab1:
    fig = go.Figure()
    _a = t["accent"].lstrip("#")
    _accent_fill = f"rgba({int(_a[0:2],16)},{int(_a[2:4],16)},{int(_a[4:6],16)},0.08)"
    fig.add_trace(go.Scatter(
        y=S.bankroll_history,
        mode="lines+markers",
        line=dict(color=t["accent"], width=3),
        marker=dict(size=4),
        name="Bankroll",
        fill="tozeroy",
        fillcolor=_accent_fill,
    ))
    fig.add_hline(y=DEFAULT_BANKROLL, line_dash="dash", line_color="rgba(255,255,255,0.31)",
                  annotation_text="Starting Bankroll",
                  annotation_font_color="rgba(255,255,255,0.50)")
    fig.update_layout(
        xaxis_title="Round", yaxis_title="Bankroll (₹)",
        template=chart_theme, height=chart_height, margin=chart_margin,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
    )
    st.plotly_chart(fig, use_container_width=True)

# 2. Result distribution — donut
with tab2:
    result_counts = df["Result"].value_counts()
    color_map = {
        RESULT_WIN: t["win"], RESULT_BLACKJACK: t["blackjack"],
        RESULT_LOSE: t["lose"], RESULT_BUST: t["bust"],
        RESULT_PUSH: t["push"], RESULT_SURRENDER: t["surrender"],
    }
    colors = [color_map.get(r, "#888") for r in result_counts.index]
    fig = go.Figure(go.Pie(
        labels=result_counts.index, values=result_counts.values,
        hole=0.55, marker=dict(colors=colors),
        textinfo="label+percent", textfont_size=13,
    ))
    fig.update_layout(
        template=chart_theme, height=chart_height, margin=chart_margin,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#ccc")),
    )
    st.plotly_chart(fig, use_container_width=True)

# 3. Rolling win rate
with tab3:
    window = min(20, max(1, total_hands // 3))
    if total_hands >= 3:
        df_copy = df.copy()
        df_copy["IsWin"] = df_copy["Result"].isin([RESULT_WIN, RESULT_BLACKJACK]).astype(int)
        df_copy["RollingWR"] = df_copy["IsWin"].rolling(window=window, min_periods=1).mean() * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=df_copy["RollingWR"], mode="lines",
            line=dict(color=t["win"], width=2),
            name=f"Rolling {window}-hand Win Rate"
        ))
        fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,0.25)")
        fig.update_layout(
            xaxis_title="Hand #", yaxis_title="Win Rate (%)",
            template=chart_theme, height=chart_height, margin=chart_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Play at least 3 hands to see the rolling win rate.")

# 4. Action frequency
with tab4:
    if S.player_actions:
        from collections import Counter
        action_counts = Counter(S.player_actions)
        action_names = {"H": "Hit", "S": "Stand", "D": "Double", "P": "Split", "SURR": "Surrender"}
        labels = [action_names.get(a, a) for a in action_counts.keys()]
        values = list(action_counts.values())
        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=t["accent"],
            text=values, textposition="auto",
        ))
        fig.update_layout(
            xaxis_title="Action", yaxis_title="Frequency",
            template=chart_theme, height=chart_height, margin=chart_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No player action data yet.")

# 5. True count vs outcome — not tracking TC per hand in history currently
# We'll show bet vs payout scatter instead
with tab5:
    if "Bet" in df.columns and "Payout" in df.columns:
        fig = px.scatter(
            df, x="Bet", y="Payout", color="Result",
            color_discrete_map=color_map,
            opacity=0.7,
        )
        fig.update_layout(
            template=chart_theme, height=chart_height, margin=chart_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
            xaxis_title="Bet Size (₹)", yaxis_title="Payout (₹)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data.")

# 6. Bet size vs outcome grouped bar
with tab6:
    if len(df) >= 3:
        df_copy = df.copy()
        # Bucket bets
        bins = [0, 25, 75, 150, 350, 1000]
        labels_b = ["₹10", "₹50", "₹100", "₹300", "₹500"]
        df_copy["BetBucket"] = pd.cut(df_copy["Bet"], bins=bins, labels=labels_b, include_lowest=True)
        grouped = df_copy.groupby(["BetBucket", "Result"], observed=True).size().reset_index(name="Count")
        fig = px.bar(
            grouped, x="BetBucket", y="Count", color="Result",
            color_discrete_map=color_map,
            barmode="group",
        )
        fig.update_layout(
            template=chart_theme, height=chart_height, margin=chart_margin,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
            xaxis_title="Bet Size", yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Play more hands to see bet-size analysis.")

st.divider()

# ─── Round History Table ─────────────────────────────────────
st.subheader("📋 Round History")

# Filters
fc1, fc2, fc3 = st.columns(3)
with fc1:
    result_filter = st.multiselect(
        "Filter by result:",
        options=[RESULT_WIN, RESULT_LOSE, RESULT_PUSH, RESULT_BUST, RESULT_BLACKJACK, RESULT_SURRENDER],
        default=None,
        key="history_result_filter",
    )
with fc2:
    _max_round = max(S.round_number, 2)
    round_range = st.slider(
        "Round range:",
        min_value=1, max_value=_max_round,
        value=(1, _max_round),
        key="history_round_range",
    )

filtered = df.copy()
if result_filter:
    filtered = filtered[filtered["Result"].isin(result_filter)]
filtered = filtered[(filtered["Round"] >= round_range[0]) & (filtered["Round"] <= round_range[1])]

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Result": st.column_config.TextColumn(width="small"),
        "Bankroll": st.column_config.NumberColumn(format="₹%d"),
        "Bet": st.column_config.NumberColumn(format="₹%d"),
        "Payout": st.column_config.NumberColumn(format="₹%d"),
    },
)

# CSV Export
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download History as CSV",
    data=csv,
    file_name="blackjack_history.csv",
    mime="text/csv",
)
