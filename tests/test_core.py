"""Unit tests for core Blackjack modules."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.deck import Card, Deck, SUITS, RANKS
from core.hand import Hand
from core.counting import Counter
from core.player import Player
from core.game import Game, RESULT_WIN, RESULT_LOSE, RESULT_PUSH, RESULT_BUST, RESULT_BLACKJACK


class TestCard(unittest.TestCase):
    def test_face_values(self):
        self.assertEqual(Card("A", "Spades").value, 11)
        self.assertEqual(Card("K", "Hearts").value, 10)
        self.assertEqual(Card("5", "Clubs").value, 5)

    def test_str(self):
        self.assertEqual(str(Card("Q", "Diamonds")), "Q of Diamonds")


class TestHand(unittest.TestCase):
    def test_simple_total(self):
        h = Hand()
        h.add(Card("5", "Hearts"))
        h.add(Card("7", "Clubs"))
        self.assertEqual(h.total(), 12)

    def test_ace_soft(self):
        h = Hand()
        h.add(Card("A", "Spades"))
        h.add(Card("6", "Hearts"))
        self.assertEqual(h.total(), 17)
        self.assertTrue(h.is_soft)

    def test_ace_hard(self):
        h = Hand()
        h.add(Card("A", "Spades"))
        h.add(Card("6", "Hearts"))
        h.add(Card("8", "Clubs"))
        self.assertEqual(h.total(), 15)
        self.assertFalse(h.is_soft)

    def test_two_aces(self):
        h = Hand()
        h.add(Card("A", "Spades"))
        h.add(Card("A", "Hearts"))
        self.assertEqual(h.total(), 12)  # one 11 + one 1

    def test_bust(self):
        h = Hand()
        h.add(Card("K", "Hearts"))
        h.add(Card("Q", "Spades"))
        h.add(Card("5", "Clubs"))
        self.assertTrue(h.bust())

    def test_blackjack(self):
        h = Hand()
        h.add(Card("A", "Spades"))
        h.add(Card("K", "Hearts"))
        self.assertTrue(h.is_blackjack)
        self.assertEqual(h.total(), 21)

    def test_not_blackjack_three_cards(self):
        h = Hand()
        h.add(Card("7", "Spades"))
        h.add(Card("7", "Hearts"))
        h.add(Card("7", "Clubs"))
        self.assertFalse(h.is_blackjack)

    def test_is_pair(self):
        h = Hand()
        h.add(Card("8", "Spades"))
        h.add(Card("8", "Hearts"))
        self.assertTrue(h.is_pair)

    def test_not_pair_different_ranks(self):
        h = Hand()
        h.add(Card("8", "Spades"))
        h.add(Card("9", "Hearts"))
        self.assertFalse(h.is_pair)


class TestDeck(unittest.TestCase):
    def test_default_shoe_size(self):
        d = Deck(num_decks=6)
        self.assertEqual(len(d.cards), 312)

    def test_single_deck(self):
        d = Deck(num_decks=1)
        self.assertEqual(len(d.cards), 52)

    def test_draw_reduces_count(self):
        d = Deck(num_decks=1)
        d.draw()
        self.assertEqual(len(d.cards), 51)

    def test_auto_reshuffle(self):
        d = Deck(num_decks=1)
        for _ in range(52):
            d.draw()
        # Next draw triggers reshuffle
        card = d.draw()
        self.assertIsNotNone(card)
        self.assertEqual(len(d.cards), 51)

    def test_needs_shuffle(self):
        d = Deck(num_decks=1, penetration=0.5)
        for _ in range(26):
            d.draw()
        self.assertTrue(d.needs_shuffle)


class TestCounter(unittest.TestCase):
    def test_low_card(self):
        c = Counter()
        c.update(Card("3", "Hearts"))
        self.assertEqual(c.running_count, 1)

    def test_high_card(self):
        c = Counter()
        c.update(Card("K", "Spades"))
        self.assertEqual(c.running_count, -1)

    def test_neutral(self):
        c = Counter()
        c.update(Card("7", "Diamonds"))
        self.assertEqual(c.running_count, 0)

    def test_true_count(self):
        c = Counter()
        c.running_count = 6
        # 2 decks remaining (104 cards)
        tc = c.true_count(104)
        self.assertAlmostEqual(tc, 3.0)

    def test_reset(self):
        c = Counter()
        c.running_count = 5
        c.reset()
        self.assertEqual(c.running_count, 0)


class TestPlayer(unittest.TestCase):
    def test_initial_money(self):
        p = Player()
        self.assertEqual(p.money, 1000)

    def test_win(self):
        p = Player(money=100)
        p.place_bet(20)
        p.win()
        self.assertEqual(p.money, 120)  # +20 net

    def test_blackjack_win(self):
        p = Player(money=100)
        p.place_bet(20)
        p.win(multiplier=1.5)
        self.assertEqual(p.money, 130)  # +30 net (3:2)

    def test_lose(self):
        p = Player(money=100)
        p.place_bet(20)
        p.lose()
        self.assertEqual(p.money, 80)

    def test_push(self):
        p = Player(money=100)
        p.place_bet(20)
        p.push()
        self.assertEqual(p.money, 100)


class TestGame(unittest.TestCase):
    def test_deal_creates_hands(self):
        g = Game(num_decks=1)
        g.deal(10)
        self.assertEqual(len(g.hands[0].cards), 2)
        self.assertEqual(len(g.dealer.hand.cards), 2)

    def test_hit_adds_card(self):
        g = Game(num_decks=1)
        g.deal(10)
        if g.player_turn:
            initial = len(g.active_hand.cards)
            g.hit()
            self.assertEqual(len(g.active_hand.cards), initial + 1)

    def test_stand_ends_player_turn(self):
        g = Game(num_decks=1)
        g.deal(10)
        if g.player_turn:
            g.stand()
            self.assertFalse(g.player_turn)

    def test_double_down(self):
        g = Game(num_decks=1, starting_money=1000)
        g.deal(50)
        if g.player_turn and g.can_double:
            g.double_down()
            self.assertEqual(g.bets[0], 100)
            self.assertFalse(g.player_turn)

    def test_resolve_returns_results(self):
        g = Game(num_decks=1)
        g.deal(10)
        # Just stand immediately
        while g.player_turn:
            g.stand()
        g.dealer_play()
        results = g.resolve()
        self.assertTrue(len(results) >= 1)
        self.assertIn(results[0]["result"],
                       [RESULT_WIN, RESULT_LOSE, RESULT_PUSH, RESULT_BUST, RESULT_BLACKJACK])

    def test_score_hand_bust(self):
        result, payout = Game._score_hand(
            player_total=25, dealer_total=18,
            player_bj=False, dealer_bj=False, bet=10, player_bust=True
        )
        self.assertEqual(result, RESULT_BUST)
        self.assertEqual(payout, -10)

    def test_score_hand_blackjack(self):
        result, payout = Game._score_hand(
            player_total=21, dealer_total=20,
            player_bj=True, dealer_bj=False, bet=100, player_bust=False
        )
        self.assertEqual(result, RESULT_BLACKJACK)
        self.assertEqual(payout, 150)  # 3:2

    def test_score_hand_push(self):
        result, payout = Game._score_hand(
            player_total=18, dealer_total=18,
            player_bj=False, dealer_bj=False, bet=10, player_bust=False
        )
        self.assertEqual(result, RESULT_PUSH)
        self.assertEqual(payout, 0)

    def test_surrender(self):
        g = Game(num_decks=1, starting_money=1000)
        g.deal(100)
        if g.player_turn and g.can_surrender:
            g.surrender()
            results = g.resolve_surrender()
            self.assertEqual(results[0]["result"], "SURRENDER")
            self.assertEqual(results[0]["payout"], -50)


if __name__ == "__main__":
    unittest.main()
