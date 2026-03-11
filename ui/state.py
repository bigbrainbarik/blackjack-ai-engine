"""
Shared session-state initialisation used by every Streamlit page.

Importing and calling ``init_state()`` at the top of each page ensures
the Game object, history lists and UI flags are always available in
``st.session_state`` regardless of which page the user lands on first.
"""

import streamlit as st
from core.game import Game


DEFAULT_DECKS = 6
DEFAULT_BANKROLL = 1000


def init_state():
    """Populate session_state with defaults if they don't already exist."""
    defaults = {
        "game": Game(num_decks=DEFAULT_DECKS, starting_money=DEFAULT_BANKROLL),
        "round_results": [],
        "current_bet": 0,
        "round_number": 0,
        "history": [],
        "bankroll_history": [DEFAULT_BANKROLL],
        "game_over": False,
        "surrendered": False,
        "nn_advice_cache": {},
        "player_actions": [],
        # Theme: "casino_green" | "dark_neon" | "minimalist_dark"
        "theme": "casino_green",
        # Multi-seat
        "num_seats": 1,
        "seat_bets": [0, 0, 0],
        # Betting phase
        "betting_phase": False,
        "bet_overrides": [None, None, None],
        # Sound
        "sound_enabled": True,
        "sound_volume": 0.5,
        # Tutorial progress
        "tutorial_step": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
