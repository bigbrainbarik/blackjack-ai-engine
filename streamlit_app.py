"""
Blackjack AI Engine — Streamlit UI  (v2)
Play manually with live AI advisory from a Neural Network and Basic Strategy.
Supports: Hit, Stand, Double Down, Split, Surrender, Insurance, Natural Blackjack.
Multi-seat (1-3), switchable themes, animated cards, sound effects, ₹ currency.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import streamlit.components.v1 as components
import base64

from core.game import Game, RESULT_WIN, RESULT_LOSE, RESULT_PUSH, RESULT_BUST, RESULT_BLACKJACK, RESULT_SURRENDER
from core.hand import Hand
from strategy.basic_strategy import suggest_move
from ml_model.nn_inference import predict_action_with_confidence
from tools.bet_sizing import calculate_bet
from gui.card_renderer import render_card, render_card_back
from gui.chip_renderer import render_chip, decompose_bet, decompose_bet_grouped, render_chip_stack

from ui.state import init_state, DEFAULT_BANKROLL, DEFAULT_DECKS
from ui.themes import get_theme_css, get_theme, THEMES
from ui.animations import animated_cards_html, get_animation_css, _b64_img, chip_stack_html
from ui.effects import get_effect_for_result, confetti_html
from ui.sounds import sound_html
from ui.multi_seat import MultiSeatManager

# ──────────────────────────────────────
# Page config
# ──────────────────────────────────────
st.set_page_config(page_title="Blackjack AI Engine", page_icon="🂡", layout="wide")

# ──────────────────────────────────────
# Session-state initialisation
# ──────────────────────────────────────
init_state()

# Additional game-page specific defaults
_extra_defaults = {
    "mgr": None,          # MultiSeatManager — created lazily
    "phase": "idle",      # idle | betting | playing | result
    "pending_sound": None,
    "pending_effect": None,
}
for k, v in _extra_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

S = st.session_state

def _ensure_mgr() -> MultiSeatManager:
    """Lazy-init the multi-seat manager, re-use across rounds."""
    if S.mgr is None:
        S.mgr = MultiSeatManager(
            num_seats=S.num_seats,
            num_decks=DEFAULT_DECKS,
            starting_money=DEFAULT_BANKROLL,
        )
    elif S.mgr.num_seats != S.num_seats and S.phase in ("idle", "betting"):
        money = S.mgr.bankroll
        S.mgr = MultiSeatManager(
            num_seats=S.num_seats,
            num_decks=DEFAULT_DECKS,
            starting_money=money,
        )
    return S.mgr

MGR = _ensure_mgr()
G: Game = MGR.active_game  # shorthand for current seat's game

# ──────────────────────────────────────
# Inject Theme CSS
# ──────────────────────────────────────
theme_name = S.get("theme", "casino_green")
st.markdown(get_theme_css(theme_name), unsafe_allow_html=True)
t = get_theme(theme_name)

# ──────────────────────────────────────
# Helpers
# ──────────────────────────────────────
ACTION_NAMES = {"H": "Hit", "S": "Stand", "D": "Double Down", "P": "Split"}

def _fmt(amount: int) -> str:
    """Format amount as ₹ with commas."""
    return f"₹{amount:,}"

def _get_advice_for_game(game: Game):
    """Return (nn_action, nn_confidence, bs_action, bs_raw) for a game."""
    hand = game.active_hand
    player_total = hand.total()
    dealer_up = game.dealer.hand.cards[0].value
    tc = game.counter.true_count(len(game.deck.cards))
    nn_action, nn_conf = predict_action_with_confidence(
        dealer_up=dealer_up,
        player_total=player_total,
        run_count=game.counter.running_count,
        true_count=tc,
        cards_remaining=len(game.deck.cards),
    )
    bs_raw = suggest_move(player_total, dealer_up)
    bs_action = bs_raw.upper()[0]
    return nn_action, nn_conf, bs_action, bs_raw

def _hand_label(hand: Hand) -> str:
    kind = "Soft" if hand.is_soft else "Hard"
    return f"{kind} {hand.total()}"

def _play_sound(event: str):
    """Queue a sound to be played."""
    S.pending_sound = event

def _show_animated_cards(hand: Hand, hide_second: bool = False,
                         label: str = "", shake: bool = False):
    """Render a hand of cards as animated HTML."""
    cards = hand.cards
    if not cards:
        st.write("—")
        return

    card_images = []
    for i, card in enumerate(cards):
        if hide_second and i == 1:
            card_images.append(render_card_back())
        else:
            card_images.append(render_card(card.rank, card.suit))

    flip_idx = 1 if (hide_second is False and len(cards) >= 2
                     and hasattr(S, '_was_hidden') and S._was_hidden) else None

    total_text = ""
    if not hide_second:
        total_text = f"<strong>{_hand_label(hand)}</strong>"
        if hand.bust():
            total_text += " — 💥 Bust!"
        elif hand.is_blackjack and len(hand.cards) == 2:
            total_text += " — 🂡 Blackjack!"

    cw = 60 if MGR.num_seats >= 3 else (80 if MGR.num_seats == 2 else 100)
    html = get_animation_css() + animated_cards_html(
        card_images=card_images,
        card_width=cw,
        stagger_ms=120,
        flip_index=flip_idx,
        back_image=render_card_back() if flip_idx is not None else None,
        shake=shake,
        label=label,
        total_text=total_text,
    )
    card_h = int(cw * 1.4)
    iframe_h = card_h + 85  # single row + label + total text
    components.html(html, height=iframe_h, scrolling=False)

def _show_chip_stack(amount: int):
    """Display a visual chip stack for the given bet."""
    if amount <= 0:
        return
    groups = decompose_bet_grouped(amount)
    chip_imgs = [(d, count, render_chip(d)) for d, count in groups]
    html = chip_stack_html(chip_imgs, label=_fmt(amount))
    components.html(html, height=80, scrolling=False)

# ──────────────────────────────────────
# Game-flow callbacks
# ──────────────────────────────────────

def cb_start_betting():
    S.phase = "betting"

def cb_deal():
    if S.game_over:
        return
    mgr = _ensure_mgr()
    bets = []
    for i in range(mgr.num_seats):
        override = S.bet_overrides[i]
        if override and override > 0:
            bets.append(min(override, mgr.bankroll))
        else:
            tc = mgr.counter.true_count(len(mgr.deck.cards))
            bets.append(calculate_bet(tc, mgr.bankroll))
        S.seat_bets[i] = bets[-1]

    S.current_bet = sum(bets)
    S.surrendered = False
    S.player_actions = []
    S.round_results = []
    S.pending_effect = None
    mgr.deal(bets)
    S.round_number += 1
    S.phase = "playing"
    _play_sound("card_deal")

    # If all naturals resolved immediately
    if not mgr.player_turn:
        mgr.dealer_play()
        _finish_round()

def cb_hit():
    S.player_actions.append("H")
    mgr = _ensure_mgr()
    mgr.hit()
    _play_sound("card_deal")
    if not mgr.player_turn:
        mgr.dealer_play()
        _finish_round()

def cb_stand():
    S.player_actions.append("S")
    mgr = _ensure_mgr()
    mgr.stand()
    if not mgr.player_turn:
        mgr.dealer_play()
        _finish_round()

def cb_double():
    S.player_actions.append("D")
    mgr = _ensure_mgr()
    mgr.double_down()
    _play_sound("chip_place")
    if not mgr.player_turn:
        mgr.dealer_play()
        _finish_round()

def cb_split():
    S.player_actions.append("P")
    mgr = _ensure_mgr()
    mgr.split()
    _play_sound("card_deal")

def cb_surrender():
    S.player_actions.append("SURR")
    mgr = _ensure_mgr()
    surrendered_seat = mgr.active_seat  # capture before advance
    mgr.surrender()
    S.surrendered = True
    if not mgr.player_turn:
        _finish_round_surrender(surrendered_seat)

def cb_insurance():
    mgr = _ensure_mgr()
    mgr.take_insurance()
    _play_sound("chip_place")

def _finish_round():
    mgr = _ensure_mgr()
    all_results = mgr.resolve()
    flat = [r for seat_results in all_results for r in seat_results]
    S.round_results = flat
    _record_history(flat, mgr.bankroll)
    S.phase = "result"

    # Pick effect from first result
    if flat:
        S.pending_effect = flat[0]["result"]
        if flat[0]["result"] in (RESULT_WIN, RESULT_BLACKJACK):
            _play_sound("blackjack" if flat[0]["result"] == RESULT_BLACKJACK else "win")
        elif flat[0]["result"] in (RESULT_BUST, RESULT_LOSE):
            _play_sound("bust" if flat[0]["result"] == RESULT_BUST else "lose")

def _finish_round_surrender(seat_idx: int = 0):
    mgr = _ensure_mgr()
    results = mgr.resolve_surrender(seat_idx)
    S.round_results = results
    _record_history(results, mgr.bankroll)
    S.phase = "result"
    S.pending_effect = "SURRENDER"

def _record_history(results, bankroll):
    for r in results:
        S.history.append({
            "Round": S.round_number,
            "Hand": r["hand_idx"] + 1,
            "Player": r["player_total"],
            "Dealer": r["dealer_total"],
            "Bet": r["bet"],
            "Result": r["result"],
            "Payout": r["payout"],
            "Bankroll": bankroll,
        })
    S.bankroll_history.append(bankroll)
    if bankroll <= 0:
        S.game_over = True

def cb_reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()

def cb_next_round():
    S.phase = "idle"
    S.round_results = []
    S.pending_effect = None
    S.pending_sound = None
    S.bet_overrides = [None, None, None]


# ──────────────────────────────────────
# Result HTML
# ──────────────────────────────────────
_RESULT_HTML = {
    RESULT_WIN:       '<p class="result-win">🎉 You Win!</p>',
    RESULT_LOSE:      '<p class="result-lose">😞 Dealer Wins</p>',
    RESULT_PUSH:      '<p class="result-push">🤝 Push</p>',
    RESULT_BUST:      '<p class="result-bust">💥 Bust!</p>',
    RESULT_BLACKJACK: '<p class="result-blackjack">🂡 Blackjack! (3:2)</p>',
    RESULT_SURRENDER: '<p class="result-surrender">🏳️ Surrendered (half bet returned)</p>',
}

# ──────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────

with st.sidebar:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("streamlit_app.py")
    if st.button("🎯 Strategy Advisor", use_container_width=True, key="nav_advisor"):
        st.switch_page("pages/3_Strategy_Advisor.py")
    if st.button("📈 Session Analytics", use_container_width=True, key="nav_analytics"):
        st.switch_page("pages/1_Analytics.py")
    if st.button("📖 Tutorial", use_container_width=True, key="nav_tutorial"):
        st.switch_page("pages/2_Tutorial.py")
    st.divider()
    st.header("🤖 AI Advisory Panel")
    st.divider()

    active_game = MGR.active_game
    if active_game.round_active and active_game.player_turn:
        nn_action, nn_conf, bs_action, bs_raw = _get_advice_for_game(active_game)

        st.subheader("Neural Network")
        st.info(f"**Recommendation:** {ACTION_NAMES.get(nn_action, nn_action)}")
        sorted_conf = sorted(nn_conf.items(), key=lambda x: x[1], reverse=True)
        for label, prob in sorted_conf:
            st.progress(prob, text=f"{ACTION_NAMES.get(label, label)}: {prob*100:.1f}%")

        st.subheader("Basic Strategy")
        st.info(f"**Recommendation:** {ACTION_NAMES.get(bs_action, bs_action)}")
        player_total = active_game.active_hand.total()
        dealer_card = active_game.dealer.hand.cards[0].value
        if player_total <= 11:
            st.caption("Player total ≤ 11 → always hit")
        elif player_total >= 17:
            st.caption("Player total ≥ 17 → always stand")
        elif dealer_card >= 7:
            st.caption(f"Dealer shows strong card ({dealer_card}) → hit")
        else:
            st.caption(f"Dealer shows weak card ({dealer_card}) → stand")

        if MGR.num_seats > 1:
            st.caption(f"Advising for **Seat {MGR.active_seat + 1}**")
    else:
        st.write("Deal a hand to see AI advice.")

    st.divider()
    st.subheader("📊 Card Counting")
    tc = MGR.counter.true_count(len(MGR.deck.cards))
    c1, c2 = st.columns(2)
    c1.metric("Running Count", MGR.counter.running_count)
    c2.metric("True Count", f"{tc:+.2f}")
    st.metric("Cards Remaining", f"{len(MGR.deck.cards)} / {MGR.deck.num_decks * 52}")

    st.divider()
    st.subheader("💰 Bet Sizing")
    if any(g.round_active for g in MGR.games):
        st.metric("Current Bet", _fmt(S.current_bet))
    else:
        next_tc = MGR.counter.true_count(len(MGR.deck.cards))
        suggested = calculate_bet(next_tc, MGR.bankroll) if MGR.bankroll > 0 else 0
        st.metric("Next Suggested Bet", _fmt(suggested))

    with st.expander("Bet Sizing Guide"):
        st.markdown("""
| True Count | Base Bet |
|:----------:|:--------:|
| ≤ 0        | ₹10      |
| 1 – 1.99   | ₹50      |
| 2 – 2.99   | ₹100     |
| 3 – 3.99   | ₹300     |
| 4+         | ₹500     |

*Max bet capped at available bankroll.*
""")

    st.divider()
    st.subheader("⚙️ Settings")
    with st.expander("Game Settings"):
        # Theme selector
        theme_options = list(THEMES.keys())
        theme_labels = [THEMES[k]["name"] for k in theme_options]
        current_idx = theme_options.index(S.theme) if S.theme in theme_options else 0
        new_theme = st.radio("Theme", theme_options, index=current_idx,
                             format_func=lambda x: THEMES[x]["name"],
                             key="theme_radio", horizontal=True)
        if new_theme != S.theme:
            S.theme = new_theme
            st.rerun()

        # Seats
        new_seats = st.slider("Number of seats", 1, 3, S.num_seats, key="seats_slider")
        if new_seats != S.num_seats and S.phase == "idle":
            S.num_seats = new_seats
            S.mgr = None  # force re-creation
            st.rerun()

        # Decks
        current_decks = MGR.deck.num_decks
        new_decks = st.slider("Number of decks", 1, 8, current_decks, key="deck_slider")
        if new_decks != current_decks and S.phase == "idle":
            MGR.shared_deck.num_decks = new_decks
            MGR.shared_deck.reset()
            MGR.shared_counter.reset()

        # Sound
        S.sound_enabled = st.toggle("Sound Effects", value=S.sound_enabled, key="sound_toggle")
        if S.sound_enabled:
            S.sound_volume = st.slider("Volume", 0.0, 1.0, S.sound_volume,
                                       step=0.1, key="volume_slider")

        st.caption("Theme & seat changes apply between rounds.")

    with st.expander("Quick Reference"):
        st.markdown("""
**Hit** — Draw a card  
**Stand** — Keep your hand  
**Double** — Double bet + 1 card  
**Split** — Split pairs into 2 hands  
**Surrender** — Forfeit half bet  
**Insurance** — Side bet vs dealer Ace  
""")

# ──────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────

st.title("🂡 Blackjack AI Engine")

# ── Top metrics ──
m1, m2, m3, m4 = st.columns(4)
m1.metric("Bankroll", _fmt(MGR.bankroll))
m2.metric("Round", S.round_number)
wins = sum(1 for r in S.history if r["Result"] in (RESULT_WIN, RESULT_BLACKJACK))
total_rounds = S.round_number
m3.metric("Win Rate", f"{wins / total_rounds * 100:.1f}%" if total_rounds else "—")
streak = 0
if S.history:
    last_result = S.history[-1]["Result"]
    for r in reversed(S.history):
        if r["Result"] == last_result:
            streak += 1
        else:
            break
    streak_char = "W" if last_result in (RESULT_WIN, RESULT_BLACKJACK) else "L"
    m4.metric("Streak", f"{streak}{streak_char}")
else:
    m4.metric("Streak", "—")

st.divider()

# ── Sound playback (hidden component) ──
if S.pending_sound and S.sound_enabled:
    components.html(sound_html(S.pending_sound, S.sound_enabled, S.sound_volume),
                    height=0, scrolling=False)
    S.pending_sound = None

# ── Effect overlay ──
if S.pending_effect:
    effect_html = get_effect_for_result(S.pending_effect)
    if effect_html:
        components.html(effect_html, height=0, scrolling=False)

# ──────────────────────────────────────
# GAME OVER
# ──────────────────────────────────────
if S.game_over:
    st.markdown("## 💀 Game Over — Bankroll depleted!")
    if S.round_results:
        for r in S.round_results:
            st.markdown(_RESULT_HTML.get(r["result"], ""), unsafe_allow_html=True)
    st.button("🔄 New Game", on_click=cb_reset, type="primary", key="btn_reset")

# ──────────────────────────────────────
# IDLE / BETTING PHASE
# ──────────────────────────────────────
elif S.phase in ("idle", "betting"):

    # Show previous round results if any
    if S.round_results and S.phase == "idle":
        with st.container():
            table_cols = st.columns([1] + [1] * MGR.num_seats)
            with table_cols[0]:
                dealer_hand = MGR.games[0].dealer.hand
                _show_animated_cards(dealer_hand, label="Dealer", shake=False)
            for si, game in enumerate(MGR.games):
                with table_cols[si + 1]:
                    seat_label = f"Seat {si+1}" if MGR.num_seats > 1 else "Player"
                    for hi, hand in enumerate(game.hands):
                        lbl = f"{seat_label} — Hand {hi+1}" if len(game.hands) > 1 else seat_label
                        _show_animated_cards(hand, label=lbl, shake=hand.bust())

            for r in S.round_results:
                st.markdown(_RESULT_HTML.get(r["result"], ""), unsafe_allow_html=True)
                if r["payout"] > 0:
                    st.write(f"Won **{_fmt(r['payout'])}**")
                elif r["payout"] < 0:
                    st.write(f"Lost **{_fmt(abs(r['payout']))}**")
                else:
                    st.write("Bet returned.")

    # Betting phase
    st.markdown("### 🎰 Place Your Bets")
    tc = MGR.counter.true_count(len(MGR.deck.cards))
    ai_bet = calculate_bet(tc, MGR.bankroll) if MGR.bankroll > 0 else 0

    bet_cols = st.columns(max(MGR.num_seats, 1))
    for i in range(MGR.num_seats):
        with bet_cols[i]:
            seat_label = f"Seat {i+1}" if MGR.num_seats > 1 else "Your Bet"
            st.markdown(f"**{seat_label}**")
            st.caption(f"AI suggests: {_fmt(ai_bet)}")

            max_per_seat = max(10, MGR.bankroll // MGR.num_seats)
            bet_val = st.number_input(
                f"Bet (₹)",
                min_value=10,
                max_value=max_per_seat,
                value=min(ai_bet, max_per_seat),
                step=10,
                key=f"bet_input_{i}",
                label_visibility="collapsed",
            )
            S.bet_overrides[i] = bet_val

            # Show chip stack preview
            _show_chip_stack(bet_val)

    _, center_deal, _ = st.columns([1, 1, 1])
    with center_deal:
        st.button("🃏 Deal", on_click=cb_deal, type="primary",
                  use_container_width=True, key="btn_deal")

# ──────────────────────────────────────
# PLAYING PHASE
# ──────────────────────────────────────
elif S.phase == "playing":
    mgr = _ensure_mgr()
    active_game = mgr.active_game

    # Side-by-side layout: dealer | player seat(s)
    table_cols = st.columns([1] + [1] * mgr.num_seats)

    # ── Dealer column ──
    with table_cols[0]:
        dealer_hand = mgr.games[0].dealer.hand
        hide_hole = any(g.player_turn for g in mgr.games)

        if hide_hole:
            card_images = [render_card(dealer_hand.cards[0].rank, dealer_hand.cards[0].suit)]
            if len(dealer_hand.cards) > 1:
                card_images.append(render_card_back())
            cw = 60 if mgr.num_seats >= 3 else (80 if mgr.num_seats == 2 else 100)
            html = get_animation_css() + animated_cards_html(card_images, card_width=cw, stagger_ms=120,
                                       label="Dealer", total_text=f"Showing: {dealer_hand.cards[0]}")
            card_h = int(cw * 1.4)
            components.html(html, height=card_h + 70, scrolling=False)
        else:
            _show_animated_cards(dealer_hand, label="Dealer")

    # ── Player seat columns ──
    for si in range(mgr.num_seats):
        game = mgr.games[si]
        with table_cols[si + 1]:
            is_active = (si == mgr.active_seat and game.player_turn)
            seat_label = f"Seat {si+1}" if mgr.num_seats > 1 else "Player"
            if is_active:
                seat_label += " 👈"

            for hi, hand in enumerate(game.hands):
                lbl = f"{seat_label} — Hand {hi+1}" if len(game.hands) > 1 else seat_label
                if len(game.hands) > 1:
                    active_h = (hi == game.active_hand_idx and game.player_turn)
                    if active_h:
                        lbl += " 👈"

                _show_animated_cards(hand, label=lbl, shake=hand.bust())

            bet_total = sum(game.bets)
            st.markdown(f"<p style='text-align:center;color:#ccc;font-size:0.9rem;'>"
                        f"Bet: {_fmt(bet_total)}</p>", unsafe_allow_html=True)

    # ── Action buttons (for active seat) ──
    if mgr.player_turn:
        ag = mgr.active_game

        # Insurance prompt
        if ag.can_insure:
            st.info(f"Dealer shows **Ace**. Insurance costs {_fmt(ag.bets[0] // 2)}.")
            st.button("🛡️ Take Insurance", on_click=cb_insurance, key="btn_insurance")
            st.divider()

        btn_cols = st.columns([1, 1, 1, 1, 1.3])
        with btn_cols[0]:
            st.button("🃏 Hit", on_click=cb_hit, type="primary",
                      use_container_width=True, key="btn_hit")
        with btn_cols[1]:
            st.button("✋ Stand", on_click=cb_stand, type="primary",
                      use_container_width=True, key="btn_stand")
        with btn_cols[2]:
            st.button("⏫ Double", on_click=cb_double, type="primary",
                      disabled=not ag.can_double,
                      use_container_width=True, key="btn_double")
        with btn_cols[3]:
            st.button("✂️ Split", on_click=cb_split, type="primary",
                      disabled=not ag.can_split,
                      use_container_width=True, key="btn_split")
        with btn_cols[4]:
            st.button("🏳️ Surrender", on_click=cb_surrender, type="primary",
                      disabled=not ag.can_surrender,
                      use_container_width=True, key="btn_surrender")

# ──────────────────────────────────────
# RESULT PHASE
# ──────────────────────────────────────
elif S.phase == "result":
    mgr = _ensure_mgr()

    # Side-by-side: dealer | player seat(s)
    table_cols = st.columns([1] + [1] * mgr.num_seats)

    with table_cols[0]:
        dealer_hand = mgr.games[0].dealer.hand
        _show_animated_cards(dealer_hand, label="Dealer")

    for si in range(mgr.num_seats):
        game = mgr.games[si]
        with table_cols[si + 1]:
            seat_label = f"Seat {si+1}" if mgr.num_seats > 1 else "Player"
            for hi, hand in enumerate(game.hands):
                lbl = f"{seat_label} — Hand {hi+1}" if len(game.hands) > 1 else seat_label
                _show_animated_cards(hand, label=lbl, shake=hand.bust())

    # Results
    for r in S.round_results:
        st.markdown(_RESULT_HTML.get(r["result"], ""), unsafe_allow_html=True)
        if r["payout"] > 0:
            st.write(f"Won **{_fmt(r['payout'])}**")
        elif r["payout"] < 0:
            st.write(f"Lost **{_fmt(abs(r['payout']))}**")
        else:
            st.write("Bet returned.")

    _, center_next, _ = st.columns([1, 1, 1])
    with center_next:
        st.button("🃏 Next Round", on_click=cb_next_round, type="primary",
                  use_container_width=True, key="btn_next")

# ──────────────────────────────────────
# Footer link to analytics
# ──────────────────────────────────────
if S.history and S.phase != "playing":
    st.divider()
    col_stats = st.columns([1, 1, 1])
    with col_stats[0]:
        total_hands = len(S.history)
        st.metric("Hands Played", total_hands)
    with col_stats[1]:
        net = MGR.bankroll - DEFAULT_BANKROLL
        st.metric("Net Profit", _fmt(net))
    with col_stats[2]:
        if st.button("📈 View Full Analytics", key="footer_analytics_main"):
            st.switch_page("pages/1_Analytics.py")
