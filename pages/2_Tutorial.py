"""
📖 Interactive Blackjack Tutorial
Covers rules, actions, basic strategy, card counting, NN AI, and bet sizing
with a mini "Try It" quiz at the end.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from ui.state import init_state
from ui.themes import get_theme_css
from gui.card_renderer import render_card, render_card_back

init_state()
S = st.session_state

st.set_page_config(page_title="Tutorial — Blackjack AI", page_icon="📖", layout="wide")
st.markdown(get_theme_css(S.get("theme", "casino_green")), unsafe_allow_html=True)

st.title("📖 How to Play Blackjack")
st.caption("An interactive guide to the game, strategy systems, and the AI engine")

with st.sidebar:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("streamlit_app.py")
    if st.button("🎯 Strategy Advisor", use_container_width=True, key="nav_advisor"):
        st.switch_page("pages/3_Strategy_Advisor.py")
    if st.button("📈 Session Analytics", use_container_width=True, key="nav_analytics"):
        st.switch_page("pages/1_Analytics.py")
    if st.button("📖 Tutorial", use_container_width=True, key="nav_tutorial"):
        st.switch_page("pages/2_Tutorial.py")

# ─── Section 1: Rules ────────────────────────────────────────
with st.expander("1 · Rules of Blackjack", expanded=True):
    st.markdown("""
### Objective
Beat the dealer by getting a hand total **closer to 21** without going over.

### Card Values
| Card | Value |
|------|-------|
| 2–10 | Face value |
| J, Q, K | 10 |
| Ace | 11 (or 1 if you'd bust) |

### Natural Blackjack
If your first two cards total **21** (an Ace + a 10-value card), that's a
**Natural Blackjack** — pays **3:2** (₹150 on a ₹100 bet).

### Dealer Rules
The dealer **must** hit until reaching **17 or higher**, then stands.
""")
    st.divider()
    st.markdown("**Example hand:**")
    cols = st.columns(5)
    example_cards = [("A", "Spades"), ("K", "Hearts")]
    for i, (r, s) in enumerate(example_cards):
        with cols[i]:
            st.image(render_card(r, s), width=90)
    st.success("Ace + King = **21** → Natural Blackjack! 🎉")

# ─── Section 2: Actions ──────────────────────────────────────
with st.expander("2 · Player Actions"):
    actions = [
        ("🃏 Hit", "Draw one more card. You can hit as many times as you like until you stand or bust."),
        ("✋ Stand", "Keep your current hand — end your turn."),
        ("⏫ Double Down", "Double your bet, receive **exactly one** more card, then automatically stand. Only allowed on your first two cards."),
        ("✂️ Split", "If your first two cards are a **pair** (same rank), split them into two separate hands. Each gets one new card and a bet equal to the original."),
        ("🏳️ Surrender", "Give up your hand and lose only **half** your bet. Only allowed on your first two cards before any other action."),
        ("🛡️ Insurance", "When the dealer shows an **Ace**, you can place a side bet (half your original bet). Pays **2:1** if the dealer has Blackjack."),
    ]
    for title, desc in actions:
        st.markdown(f"**{title}**")
        st.markdown(desc)
        st.write("")

# ─── Section 3: Basic Strategy ───────────────────────────────
with st.expander("3 · Basic Strategy"):
    st.markdown("""
Basic Strategy is a **mathematically optimal** set of decisions for every
possible hand combination.  Our simplified version uses these rules:

| Your Total | Dealer Shows | Action |
|:----------:|:------------:|:------:|
| ≤ 11 | Any | **Hit** |
| 12 – 16 | 2 – 6 (weak) | **Stand** |
| 12 – 16 | 7 – A (strong) | **Hit** |
| ≥ 17 | Any | **Stand** |

> 💡 The full casino basic-strategy chart has **550+ decisions** covering
> soft hands, pairs, double opportunities, and surrender spots.  Our
> simplified version captures the most impactful rules.
""")

# ─── Section 4: Card Counting ────────────────────────────────
with st.expander("4 · Card Counting (Hi-Lo)"):
    st.markdown("""
### The Hi-Lo System

Card counting tracks the balance of high vs low cards remaining in the shoe.

| Cards | Count Change |
|:-----:|:------------:|
| 2, 3, 4, 5, 6 | **+1** (low cards removed → good for you) |
| 7, 8, 9 | **0** (neutral) |
| 10, J, Q, K, A | **-1** (high cards removed → bad for you) |

### Running Count → True Count

$$\\text{True Count} = \\frac{\\text{Running Count}}{\\text{Decks Remaining}}$$

A **positive** true count means the remaining shoe is rich in high cards
(10s and Aces) — **favourable** for the player.

### Example Walkthrough

Imagine these cards have been dealt from a 6-deck shoe:  
**5, K, 3, 7, Q, 2, 8, A**

| Card | Change | Running Count |
|:----:|:------:|:-------------:|
| 5 | +1 | +1 |
| K | −1 | 0 |
| 3 | +1 | +1 |
| 7 | 0 | +1 |
| Q | −1 | 0 |
| 2 | +1 | +1 |
| 8 | 0 | +1 |
| A | −1 | 0 |

With ~5.85 decks remaining: **True Count = 0 / 5.85 ≈ 0.00** (neutral shoe).
""")

# ─── Section 5: Neural Network ───────────────────────────────
with st.expander("5 · Neural Network AI"):
    st.markdown("""
### Architecture

Our NN is a **3-layer fully connected** network trained on millions of
simulated hands:

```
Input (5 features) → 64 neurons → ReLU → 64 neurons → ReLU → 4 outputs
```

### What the NN sees

| # | Feature | Range |
|:-:|---------|-------|
| 1 | Dealer's face-up card value | 2 – 11 |
| 2 | Your hand total | 4 – 21 |
| 3 | Running count | −∞ to +∞ |
| 4 | True count | decimal |
| 5 | Cards remaining in shoe | 52 – 312 |

### What it predicts

Four action probabilities via **softmax**:

**H** (Hit) · **S** (Stand) · **D** (Double) · **P** (Split)

The sidebar shows **confidence bars** so you can see how certain the NN
is about each action.

### Accuracy

The model achieves approximately **92% accuracy** on held-out test data,
meaning it agrees with optimal play 92 out of 100 times.
""")

# ─── Section 6: Bet Sizing ───────────────────────────────────
with st.expander("6 · Bet Sizing by True Count"):
    st.markdown("""
The AI automatically adjusts bet size based on the true count:

| True Count | Bet Amount |
|:----------:|:----------:|
| ≤ 0 | ₹10 (minimum — unfavourable shoe) |
| 1.0 – 1.99 | ₹50 |
| 2.0 – 2.99 | ₹100 |
| 3.0 – 3.99 | ₹300 |
| ≥ 4.0 | ₹500 (maximum — very hot shoe) |

The bet is also capped at your available bankroll.

> 🎯 **Key principle:** Bet more when the shoe favours you (high true count),
> bet minimum when it doesn't.
""")

# ─── Section 7: Try It ───────────────────────────────────────
with st.expander("7 · Try It! — Test Your Knowledge", expanded=False):
    st.markdown("### What would you do?")

    # Scenario 1
    st.markdown("**Scenario:** You have **Hard 15** (8 + 7). Dealer shows **10**.")
    cols = st.columns(4)
    with cols[0]:
        st.image(render_card("8", "Clubs"), width=80)
    with cols[1]:
        st.image(render_card("7", "Hearts"), width=80)
    with cols[2]:
        st.write("vs")
    with cols[3]:
        st.image(render_card("10", "Spades"), width=80)

    answer1 = st.radio(
        "Your decision:",
        ["Hit", "Stand", "Double Down", "Surrender"],
        key="quiz_1",
        index=None,
    )
    if answer1:
        if answer1 == "Hit":
            st.success("✅ Correct! With Hard 15 vs dealer 10, basic strategy says **Hit**. "
                       "The dealer has a strong showing and is likely to make 17+.")
        elif answer1 == "Surrender":
            st.info("🤔 Good instinct! Full basic strategy actually recommends **Surrender** "
                    "for 15 vs 10 if available, otherwise **Hit**.")
        else:
            st.error("❌ Not quite. Against a dealer 10, standing on 15 loses more often. "
                     "The optimal play is **Hit** (or Surrender if allowed).")

    st.divider()

    # Scenario 2
    st.markdown("**Scenario:** You have **A + 6** (Soft 17). Dealer shows **5**.")
    cols2 = st.columns(4)
    with cols2[0]:
        st.image(render_card("A", "Hearts"), width=80)
    with cols2[1]:
        st.image(render_card("6", "Diamonds"), width=80)
    with cols2[2]:
        st.write("vs")
    with cols2[3]:
        st.image(render_card("5", "Clubs"), width=80)

    answer2 = st.radio(
        "Your decision:",
        ["Hit", "Stand", "Double Down", "Surrender"],
        key="quiz_2",
        index=None,
    )
    if answer2:
        if answer2 == "Double Down":
            st.success("✅ Perfect! Soft 17 vs dealer 5 is a **Double Down** spot. "
                       "The dealer is weak and you can't bust with one card on soft 17.")
        elif answer2 == "Hit":
            st.info("🤔 Not bad — hitting is the second-best play. But **Double Down** "
                    "is optimal here because the dealer is weak and you can improve risk-free.")
        else:
            st.error("❌ With Soft 17, you have room to improve. Against a weak dealer card "
                     "like 5, the optimal play is **Double Down**.")

    st.divider()

    # Scenario 3
    st.markdown("**Scenario:** True Count is **+4.5**. You have ₹800 bankroll. How much to bet?")
    bet_answer = st.number_input("Your bet (₹):", min_value=10, max_value=800,
                                 value=10, step=10, key="quiz_3")
    if st.button("Check Answer", key="quiz_3_check"):
        if bet_answer >= 400:
            st.success(f"✅ Great! With TC ≥ 4, the AI bets ₹500 (the max). "
                       f"You chose ₹{bet_answer} — aggressive betting in a hot shoe is correct.")
        elif bet_answer >= 200:
            st.info(f"🤔 ₹{bet_answer} is reasonable, but with TC +4.5 the shoe is "
                    f"**very** favourable. The AI would bet ₹500.")
        else:
            st.error(f"❌ With True Count +4.5, this is the best betting opportunity. "
                     f"The AI would bet ₹500, not ₹{bet_answer}.")
