"""
Multi-seat game orchestrator.

Wraps 1–3 ``Game`` instances that share a **single** ``Deck`` and
``Counter`` — exactly like a real casino table where multiple
box positions draw from the same shoe.

**Does NOT modify ``core/game.py``** — it monkey-patches ``.deck``
and ``.counter`` attributes after construction so the engine itself
is untouched.
"""

from __future__ import annotations
from core.game import Game
from core.deck import Deck
from core.counting import Counter


class MultiSeatManager:
    """
    Manage 1–3 seats at one blackjack table.

    Usage
    -----
    >>> mgr = MultiSeatManager(num_seats=2, num_decks=6, starting_money=1000)
    >>> mgr.deal([100, 100])          # deal both seats with those bets
    >>> while mgr.player_turn:
    ...     seat = mgr.active_seat    # which seat needs action
    ...     game = mgr.active_game    # the Game object for that seat
    ...     mgr.hit()                 # actions route to active seat
    >>> mgr.dealer_play()
    >>> results = mgr.resolve()       # list of per-seat result lists
    """

    def __init__(self, num_seats: int = 1, num_decks: int = 6,
                 starting_money: int = 1000):
        self.num_seats = max(1, min(3, num_seats))
        self.starting_money = starting_money
        self.shared_deck = Deck(num_decks=num_decks)
        self.shared_counter = Counter()

        # Create games — they each get their own Deck/Counter by default,
        # but we immediately replace those references with the shared ones.
        self.games: list[Game] = []
        for _ in range(self.num_seats):
            g = Game(num_decks=num_decks, starting_money=starting_money)
            g.deck = self.shared_deck
            g.counter = self.shared_counter
            self.games.append(g)

        # All seats share one bankroll (via the first game's Player).
        # We'll use self.bankroll property to proxy.
        self._bankroll = starting_money

        # Seat progression
        self.active_seat: int = 0
        self.round_active: bool = False
        self.all_results: list[list[dict]] = []

    # ── Properties ──

    @property
    def bankroll(self) -> int:
        return self._bankroll

    @bankroll.setter
    def bankroll(self, value: int):
        self._bankroll = value
        # Keep every game's player.money in sync
        for g in self.games:
            g.player.money = value

    @property
    def active_game(self) -> Game:
        return self.games[self.active_seat]

    @property
    def player_turn(self) -> bool:
        """True while any seat still has player_turn == True."""
        return any(g.player_turn for g in self.games if g.round_active)

    @property
    def deck(self) -> Deck:
        return self.shared_deck

    @property
    def counter(self) -> Counter:
        return self.shared_counter

    # ── Deal ──

    def deal(self, bets: list[int]):
        """Deal all seats.  ``bets`` must have one entry per seat."""
        if self.shared_deck.needs_shuffle:
            self.shared_deck.reset()
            self.shared_counter.reset()

        self.all_results = []
        self.active_seat = 0

        for i, g in enumerate(self.games):
            g.player.money = self.bankroll
            bet = bets[i] if i < len(bets) else bets[0]
            g.deal(bet)

        # Advance past any seats that already resolved (naturals)
        self._advance_to_next_active()
        self.round_active = True

    # ── Player actions — route to active seat ──

    def hit(self):
        g = self.active_game
        if not g.player_turn:
            return
        g.hit()
        if not g.player_turn:
            self._advance_to_next_active()

    def stand(self):
        g = self.active_game
        if not g.player_turn:
            return
        g.stand()
        if not g.player_turn:
            self._advance_to_next_active()

    def double_down(self):
        g = self.active_game
        if not g.player_turn:
            return
        g.double_down()
        if not g.player_turn:
            self._advance_to_next_active()

    def split(self):
        g = self.active_game
        if not g.player_turn:
            return
        g.split()

    def surrender(self):
        g = self.active_game
        if not g.player_turn:
            return
        g.surrender()
        if not g.player_turn:
            self._advance_to_next_active()

    def take_insurance(self):
        g = self.active_game
        g.take_insurance()

    # ── Dealer ──

    def dealer_play(self):
        """Dealer draws once — shared across all seats (same dealer hand)."""
        # Use first game's dealer logic.  Since they share a deck/counter,
        # any game's dealer_play() will work.  But we need the dealer hand
        # to be shared too.
        primary = self.games[0]
        primary.dealer_play()
        # Copy final dealer hand state to all other seats
        for g in self.games[1:]:
            g.dealer.hand = primary.dealer.hand

    # ── Resolve ──

    def resolve(self) -> list[list[dict]]:
        """Resolve all seats.  Returns list-of-lists of result dicts."""
        self.all_results = []
        net_change = 0
        for g in self.games:
            if g.round_active:
                results = g.resolve()
                for r in results:
                    net_change += r["payout"]
                self.all_results.append(results)
            else:
                self.all_results.append(g.round_results)

        self.bankroll = self.bankroll + net_change
        self.round_active = False
        return self.all_results

    def resolve_surrender(self, seat_idx: int) -> list[dict]:
        """Resolve a surrendered seat."""
        g = self.games[seat_idx]
        results = g.resolve_surrender()
        for r in results:
            self.bankroll += r["payout"]
        return results

    # ── Internal ──

    def _advance_to_next_active(self):
        """Move active_seat to the next seat that still needs player action."""
        for i in range(self.active_seat, self.num_seats):
            if self.games[i].player_turn:
                self.active_seat = i
                return
        # Also check from 0 (shouldn't be needed, but safe)
        for i in range(0, self.active_seat):
            if self.games[i].player_turn:
                self.active_seat = i
                return
        # No seats need action — player turn is over
        self.active_seat = 0

    def reset(self, num_seats: int | None = None, starting_money: int | None = None):
        """Full reset — new shoe, new games."""
        if num_seats is not None:
            self.num_seats = max(1, min(3, num_seats))
        if starting_money is not None:
            self.starting_money = starting_money
        self.shared_deck.reset()
        self.shared_counter.reset()
        self.games = []
        for _ in range(self.num_seats):
            g = Game(num_decks=self.shared_deck.num_decks,
                     starting_money=self.starting_money)
            g.deck = self.shared_deck
            g.counter = self.shared_counter
            self.games.append(g)
        self.bankroll = self.starting_money
        self.active_seat = 0
        self.round_active = False
        self.all_results = []
