import random
import logging

logger = logging.getLogger(__name__)

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = VALUES[rank]

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def __str__(self):
        return f"{self.rank} of {self.suit}"


class Deck:
    """Configurable multi-deck shoe with cut-card support."""

    def __init__(self, num_decks=6, penetration=0.75):
        self.num_decks = num_decks
        self.penetration = penetration  # reshuffle when this fraction dealt
        self.cards = []
        self._initial_size = 0
        self.reset()

    def reset(self):
        self.cards.clear()
        for _ in range(self.num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    self.cards.append(Card(rank, suit))
        random.shuffle(self.cards)
        self._initial_size = len(self.cards)
        logger.debug("Shoe shuffled (%d decks, %d cards)", self.num_decks, self._initial_size)

    @property
    def needs_shuffle(self):
        """True when the cut card has been reached."""
        if self._initial_size == 0:
            return True
        dealt_fraction = 1 - len(self.cards) / self._initial_size
        return dealt_fraction >= self.penetration

    def draw(self):
        if not self.cards:
            self.reset()
        return self.cards.pop()