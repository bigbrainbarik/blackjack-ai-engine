"""
Blackjack game engine — state-machine design.

All game logic lives here. UIs (Streamlit, Tkinter, CLI) call these methods
without reimplementing rules.  The trained NN model and basic-strategy module
are *not* modified — they are called for advisory only via the UI layer.
"""

from __future__ import annotations

from core.deck import Deck
from core.player import Player
from core.hand import Hand
from core.counting import Counter


# ── Round-result constants ────────────────────────────────────────

RESULT_WIN = "WIN"
RESULT_LOSE = "LOSE"
RESULT_PUSH = "PUSH"
RESULT_BUST = "BUST"
RESULT_BLACKJACK = "BLACKJACK"
RESULT_SURRENDER = "SURRENDER"


class Game:
    """
    Single-player Blackjack game engine.

    Typical flow
    ------------
    1. ``deal()``       → deals initial 4 cards
    2. Check ``player_blackjack`` / ``dealer_blackjack`` / ``can_insure``
    3. Optionally ``take_insurance()``
    4. Player actions: ``hit()``, ``stand()``, ``double_down()``,
       ``split()``, ``surrender()``
    5. Once ``player_turn`` is False → ``dealer_play()``
    6. ``resolve()``    → returns list of result dicts (one per hand)
    """

    def __init__(self, num_decks: int = 6, starting_money: int = 1000):
        self.deck = Deck(num_decks=num_decks)
        self.player = Player(money=starting_money)
        self.dealer = Player()
        self.counter = Counter()

        # Round state
        self.hands: list[Hand] = []       # player hands (usually 1; 2 after split)
        self.bets: list[int] = []         # bet per hand
        self.active_hand_idx: int = 0     # which hand the player is currently playing
        self.player_turn: bool = False
        self.round_active: bool = False
        self.insurance_bet: int = 0
        self.round_results: list[dict] = []

    # ── Properties ────────────────────────────────────────────────

    @property
    def active_hand(self) -> Hand:
        return self.hands[self.active_hand_idx]

    @property
    def player_blackjack(self) -> bool:
        return len(self.hands) == 1 and self.hands[0].is_blackjack

    @property
    def dealer_blackjack(self) -> bool:
        return self.dealer.hand.is_blackjack

    @property
    def can_hit(self) -> bool:
        return self.player_turn and not self.active_hand.bust()

    @property
    def can_double(self) -> bool:
        """Double only on first two cards of a hand, if bankroll allows."""
        h = self.active_hand
        return (self.player_turn
                and len(h.cards) == 2
                and self.player.money >= self.bets[self.active_hand_idx])

    @property
    def can_split(self) -> bool:
        """Split only first two cards when they share a rank, max 2 hands."""
        h = self.active_hand
        return (self.player_turn
                and len(self.hands) == 1
                and h.is_pair
                and self.player.money >= self.bets[self.active_hand_idx])

    @property
    def can_surrender(self) -> bool:
        """Late surrender: only on initial two cards, no splits active."""
        h = self.active_hand
        return (self.player_turn
                and len(h.cards) == 2
                and len(self.hands) == 1
                and self.active_hand_idx == 0)

    @property
    def can_insure(self) -> bool:
        """Insurance offered when dealer shows Ace, before any player action."""
        return (self.player_turn
                and len(self.active_hand.cards) == 2
                and len(self.hands) == 1
                and self.dealer.hand.cards[0].rank == "A"
                and self.insurance_bet == 0)

    # ── Deal ──────────────────────────────────────────────────────

    def deal(self, bet: int):
        """Start a new round: reset, place bet, deal 4 cards."""
        # Reshuffle if cut card reached
        if self.deck.needs_shuffle:
            self.deck.reset()
            self.counter.reset()

        self.player.reset()
        self.dealer.reset()

        hand = Hand()
        self.hands = [hand]
        self.player.hand = hand
        self.bets = [bet]
        self.active_hand_idx = 0
        self.player_turn = True
        self.round_active = True
        self.insurance_bet = 0
        self.round_results = []

        # Deal: player, dealer, player, dealer
        for target_hand in [hand, self.dealer.hand, hand, self.dealer.hand]:
            card = self.deck.draw()
            target_hand.add(card)
            self.counter.update(card)

        # Auto-resolve naturals
        if self.player_blackjack and self.dealer_blackjack:
            self.player_turn = False
        elif self.player_blackjack:
            self.player_turn = False
        elif self.dealer_blackjack:
            self.player_turn = False

    # ── Player actions ────────────────────────────────────────────

    def hit(self):
        """Draw one card for the active hand."""
        if not self.can_hit:
            return
        card = self.deck.draw()
        self.active_hand.add(card)
        self.counter.update(card)

        if self.active_hand.bust() or self.active_hand.total() == 21:
            self._advance_hand()

    def stand(self):
        """End the current hand."""
        if not self.player_turn:
            return
        self._advance_hand()

    def double_down(self):
        """Double the bet, take exactly one card, then stand."""
        if not self.can_double:
            return
        self.bets[self.active_hand_idx] *= 2
        card = self.deck.draw()
        self.active_hand.add(card)
        self.counter.update(card)
        self._advance_hand()

    def split(self):
        """Split the active hand into two hands."""
        if not self.can_split:
            return
        original = self.active_hand
        card1 = original.cards[0]
        card2 = original.cards[1]

        h1 = Hand()
        h1.add(card1)
        h2 = Hand()
        h2.add(card2)

        # Deal one new card to each
        new1 = self.deck.draw()
        h1.add(new1)
        self.counter.update(new1)

        new2 = self.deck.draw()
        h2.add(new2)
        self.counter.update(new2)

        self.hands = [h1, h2]
        self.bets = [self.bets[0], self.bets[0]]
        self.active_hand_idx = 0
        self.player.hand = h1  # point to first hand for convenience

    def surrender(self):
        """Forfeit half the bet and end the round."""
        if not self.can_surrender:
            return
        self.player_turn = False

    def take_insurance(self):
        """Place an insurance side-bet (half the original bet)."""
        if not self.can_insure:
            return
        self.insurance_bet = self.bets[0] // 2

    # ── Dealer play ───────────────────────────────────────────────

    def dealer_play(self):
        """Dealer draws to 17 (stands on soft 17). Call after player_turn is False."""
        # Skip if all player hands busted
        if all(h.bust() for h in self.hands):
            return
        while self.dealer.hand.total() < 17:
            card = self.deck.draw()
            self.dealer.hand.add(card)
            self.counter.update(card)

    # ── Resolve ───────────────────────────────────────────────────

    def resolve(self) -> list[dict]:
        """
        Resolve the round.  Returns a list of result dicts — one per player hand:
        ``{ "hand_idx", "player_total", "dealer_total", "bet", "result", "payout" }``

        Payout is the **net** change to bankroll (positive = profit, negative = loss).
        """
        dealer_total = self.dealer.hand.total()
        dealer_bj = self.dealer_blackjack
        results = []

        # Insurance payout
        if self.insurance_bet > 0:
            if dealer_bj:
                self.player.money += self.insurance_bet * 2  # pays 2:1
            else:
                self.player.money -= self.insurance_bet

        for i, hand in enumerate(self.hands):
            bet = self.bets[i]
            player_total = hand.total()
            player_bj = hand.is_blackjack and len(self.hands) == 1

            # Surrender
            if self.can_surrender is False and i == 0 and not self.player_turn and len(hand.cards) == 2 and len(self.hands) == 1:
                pass  # not a surrender round (surrender handled via explicit flag)

            result, payout = self._score_hand(
                player_total, dealer_total, player_bj, dealer_bj, bet, hand.bust()
            )

            self.player.money += payout
            results.append({
                "hand_idx": i,
                "player_total": player_total,
                "dealer_total": dealer_total,
                "bet": bet,
                "result": result,
                "payout": payout,
            })

        # Check if this was a surrender (override)
        if not self.player_turn and len(self.hands) == 1 and len(self.hands[0].cards) == 2:
            # We need a flag — handled via the _surrendered marker
            pass

        self.round_active = False
        self.round_results = results
        return results

    def resolve_surrender(self) -> list[dict]:
        """Resolve a surrendered round — lose half the bet."""
        bet = self.bets[0]
        payout = -(bet // 2)
        self.player.money += payout
        result = [{
            "hand_idx": 0,
            "player_total": self.hands[0].total(),
            "dealer_total": self.dealer.hand.total(),
            "bet": bet,
            "result": RESULT_SURRENDER,
            "payout": payout,
        }]
        self.round_active = False
        self.round_results = result
        return result

    @staticmethod
    def _score_hand(player_total, dealer_total, player_bj, dealer_bj, bet, player_bust):
        """Return (result_str, net_payout) for one hand."""
        if player_bust:
            return RESULT_BUST, -bet

        if player_bj and dealer_bj:
            return RESULT_PUSH, 0

        if player_bj:
            return RESULT_BLACKJACK, int(bet * 1.5)  # 3:2 payout

        if dealer_bj:
            return RESULT_LOSE, -bet

        if dealer_total > 21:
            return RESULT_WIN, bet

        if player_total > dealer_total:
            return RESULT_WIN, bet

        if player_total < dealer_total:
            return RESULT_LOSE, -bet

        return RESULT_PUSH, 0

    # ── Internal helpers ──────────────────────────────────────────

    def _advance_hand(self):
        """Move to the next split hand, or end the player turn."""
        if self.active_hand_idx < len(self.hands) - 1:
            self.active_hand_idx += 1
            self.player.hand = self.hands[self.active_hand_idx]
        else:
            self.player_turn = False


