"""
🎯 Custom Strategy Advisor
Enter your own card combination and get AI recommendations
from both the Neural Network and Basic Strategy engines.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import base64
from ui.state import init_state
from ui.themes import get_theme_css, get_theme
from gui.card_renderer import render_card
from core.deck import VALUES
from ml_model.nn_inference import predict_action_with_confidence
from strategy.basic_strategy import suggest_move

init_state()
S = st.session_state

st.set_page_config(page_title="Strategy Advisor — Blackjack AI", page_icon="🎯", layout="wide")
theme_name = S.get("theme", "casino_green")
st.markdown(get_theme_css(theme_name), unsafe_allow_html=True)
t = get_theme(theme_name)

ACTION_NAMES = {"H": "Hit", "S": "Stand", "D": "Double Down", "P": "Split"}
ACTION_ICONS = {"H": "👊", "S": "🤚", "D": "⬇️", "P": "✂️"}

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]

st.title("🎯 Custom Strategy Advisor")
st.caption("Enter any card combination and get AI-powered recommendations")

# ─── Sidebar Navigation ──────────────────────────────────────
with st.sidebar:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("streamlit_app.py")
    if st.button("📈 Session Analytics", use_container_width=True, key="nav_analytics"):
        st.switch_page("pages/1_Analytics.py")
    if st.button("📖 Tutorial", use_container_width=True, key="nav_tutorial"):
        st.switch_page("pages/2_Tutorial.py")
    if st.button("🎯 Strategy Advisor", use_container_width=True, key="nav_advisor"):
        st.switch_page("pages/3_Strategy_Advisor.py")
    st.divider()
    st.markdown("""
    **How to use:**
    1. Select the dealer's face-up card
    2. Add your player cards (2 or more)
    3. Optionally adjust counting parameters
    4. Click **Analyze** to get recommendations
    """)


def calc_hand_total(card_ranks):
    """Calculate hand total from a list of card ranks, handling aces."""
    total = 0
    aces = 0
    for rank in card_ranks:
        total += VALUES[rank]
        if rank == "A":
            aces += 1
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def render_card_html(rank, suit):
    """Render a card as an inline base64 image."""
    png_bytes = render_card(rank, suit)
    b64 = base64.b64encode(png_bytes).decode()
    return f'<img src="data:image/png;base64,{b64}" style="height:120px; margin:2px; border-radius:8px; box-shadow:2px 2px 6px rgba(0,0,0,0.3);">'


# ─── Card Input Section ──────────────────────────────────────
st.subheader("🃏 Card Setup")

col_dealer, col_player = st.columns(2)

with col_dealer:
    st.markdown("#### Dealer's Hand")
    num_dealer_cards = st.slider("Number of cards", min_value=1, max_value=8, value=1, key="num_dealer_cards")

    dealer_cards = []
    d_card_cols = st.columns(min(num_dealer_cards, 4))
    for i in range(num_dealer_cards):
        col_idx = i % min(num_dealer_cards, 4)
        with d_card_cols[col_idx]:
            r = st.selectbox(f"Card {i+1} Rank", RANKS, index=8 if i == 0 else min(i, len(RANKS)-1), key=f"d_rank_{i}")
            s = st.selectbox(f"Card {i+1} Suit", SUITS, index=(3 + i) % 4, key=f"d_suit_{i}")
            dealer_cards.append((r, s))

    # Preview dealer cards
    dealer_html = "".join(render_card_html(r, s) for r, s in dealer_cards)
    st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{dealer_html}</div>', unsafe_allow_html=True)

with col_player:
    st.markdown("#### Your Hand")
    num_cards = st.slider("Number of cards", min_value=2, max_value=8, value=2, key="num_player_cards")

    player_cards = []
    card_cols = st.columns(min(num_cards, 4))
    for i in range(num_cards):
        col_idx = i % min(num_cards, 4)
        with card_cols[col_idx]:
            r = st.selectbox(f"Card {i+1} Rank", RANKS, index=min(i, len(RANKS)-1), key=f"p_rank_{i}")
            s = st.selectbox(f"Card {i+1} Suit", SUITS, index=i % 4, key=f"p_suit_{i}")
            player_cards.append((r, s))

    # Preview player cards
    cards_html = "".join(render_card_html(r, s) for r, s in player_cards)
    st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{cards_html}</div>', unsafe_allow_html=True)

# ─── Bet & Counting Parameters ───────────────────────────────
st.subheader("💰 Bet & Counting Parameters")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)

with p_col1:
    bet_amount = st.number_input("Bet Amount (₹)", min_value=10, max_value=10000, value=100, step=10, key="custom_bet")
with p_col2:
    running_count = st.number_input("Running Count", min_value=-50, max_value=50, value=0, step=1, key="custom_rc")
with p_col3:
    true_count = st.number_input("True Count", min_value=-20.0, max_value=20.0, value=0.0, step=0.5, key="custom_tc")
with p_col4:
    cards_remaining = st.number_input("Cards Remaining", min_value=10, max_value=416, value=312, step=1, key="custom_cards_rem")

# ─── Analyze Button ──────────────────────────────────────────
st.divider()

if st.button("🔍 Analyze", use_container_width=True, type="primary"):
    player_ranks = [r for r, s in player_cards]
    player_total = calc_hand_total(player_ranks)
    dealer_ranks = [r for r, s in dealer_cards]
    dealer_total = calc_hand_total(dealer_ranks)
    dealer_value = VALUES[dealer_cards[0][0]]  # face-up card value
    dealer_rank_display = dealer_cards[0][0]
    is_pair = len(player_cards) == 2 and VALUES[player_cards[0][0]] == VALUES[player_cards[1][0]]
    is_soft = any(r == "A" for r, s in player_cards) and calc_hand_total(player_ranks) != sum(VALUES[r] for r, s in player_cards)
    is_blackjack = len(player_cards) == 2 and player_total == 21
    is_bust = player_total > 21

    # ─── Hand Summary ────────────────────────────────────
    st.subheader("📊 Analysis Results")

    summary_cols = st.columns(5)
    with summary_cols[0]:
        hand_type = "Blackjack! 🎉" if is_blackjack else ("Bust 💥" if is_bust else ("Soft" if is_soft else "Hard"))
        st.metric("Hand Type", hand_type)
    with summary_cols[1]:
        st.metric("Player Total", player_total)
    with summary_cols[2]:
        st.metric("Dealer Total", dealer_total)
    with summary_cols[3]:
        st.metric("Dealer Face-Up", f"{dealer_rank_display} ({dealer_value})")
    with summary_cols[4]:
        st.metric("Bet", f"₹{bet_amount}")

    if is_blackjack:
        st.success("🎉 **Natural Blackjack!** You win 3:2 — no action needed.")
        payout = int(bet_amount * 1.5)
        st.info(f"**Payout:** ₹{payout} (on a ₹{bet_amount} bet)")

    elif is_bust:
        st.error("💥 **Bust!** Your hand exceeds 21. You lose your bet.")

    else:
        # ─── Neural Network Recommendation ───────────────
        nn_action, nn_conf = predict_action_with_confidence(
            dealer_up=dealer_value,
            player_total=player_total,
            run_count=running_count,
            true_count=true_count,
            cards_remaining=cards_remaining,
        )

        # ─── Basic Strategy Recommendation ───────────────
        bs_raw = suggest_move(player_total, dealer_value)
        bs_action = bs_raw.upper()[0]

        rec_col1, rec_col2 = st.columns(2)

        with rec_col1:
            st.markdown("### 🧠 Neural Network")
            nn_name = ACTION_NAMES.get(nn_action, nn_action)
            nn_icon = ACTION_ICONS.get(nn_action, "")
            st.success(f"**Recommendation:** {nn_icon} {nn_name}")

            st.markdown("**Confidence Breakdown:**")
            # Sort by probability descending
            sorted_conf = sorted(nn_conf.items(), key=lambda x: x[1], reverse=True)
            for label, prob in sorted_conf:
                name = ACTION_NAMES.get(label, label)
                icon = ACTION_ICONS.get(label, "")
                st.progress(prob, text=f"{icon} {name}: {prob*100:.1f}%")

        with rec_col2:
            st.markdown("### 📘 Basic Strategy")
            bs_name = ACTION_NAMES.get(bs_action, bs_action)
            bs_icon = ACTION_ICONS.get(bs_action, "")
            st.success(f"**Recommendation:** {bs_icon} {bs_name}")

            st.markdown("**Reasoning:**")
            if player_total <= 11:
                st.info("Your total is **11 or less** — always hit, you can't bust.")
            elif player_total >= 17:
                st.info("Your total is **17 or higher** — always stand, risk of busting is too high.")
            elif dealer_value >= 7:
                st.info(f"Dealer shows **{dealer_rank_display}** (strong card, 7+) — hit to improve your hand.")
            else:
                st.info(f"Dealer shows **{dealer_rank_display}** (weak card, 2–6) — stand and let the dealer risk busting.")

            if is_pair:
                st.warning("🃏 **Pair detected!** Splitting may be an option. The Neural Network considers split in its analysis.")

        # ─── Agreement Check ─────────────────────────────
        st.divider()
        if nn_action == bs_action:
            st.success(f"✅ **Both strategies agree:** {ACTION_ICONS.get(nn_action, '')} {ACTION_NAMES.get(nn_action, nn_action)}")
        else:
            st.warning(
                f"⚠️ **Strategies disagree:** "
                f"Neural Network says **{ACTION_NAMES.get(nn_action, nn_action)}**, "
                f"Basic Strategy says **{ACTION_NAMES.get(bs_action, bs_action)}**. "
                f"The NN factors in card counting data, which may lead to different advice."
            )

        # ─── Contextual Tips ─────────────────────────────
        st.divider()
        st.subheader("💡 Contextual Tips")
        tips = []
        if true_count >= 2:
            tips.append("📈 **Positive count** — The deck is rich in high cards. Consider increasing your bet.")
        elif true_count <= -2:
            tips.append("📉 **Negative count** — The deck is rich in low cards. Consider decreasing your bet.")
        if is_soft:
            tips.append("🔄 **Soft hand** — Your Ace gives flexibility. You can safely take another card without busting.")
        if is_pair:
            tips.append("✂️ **Pair hand** — Consider whether splitting gives you a strategic advantage.")
        if player_total in [10, 11]:
            tips.append("⬇️ **Strong double-down position** — Totals of 10 or 11 are ideal for doubling.")
        if dealer_value in [5, 6]:
            tips.append("🎯 **Dealer weakness** — Dealer showing 5 or 6 is the weakest position. Play conservatively.")
        if not tips:
            tips.append("👍 Standard situation — follow the recommended strategy.")
        for tip in tips:
            st.markdown(tip)
