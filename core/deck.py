import random

from torch.backends.mkl import verbose

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

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        self.cards.clear()
        for suit in SUITS:
            for rank in RANKS:
                self.cards.append(Card(rank, suit))
        random.shuffle(self.cards)
        if verbose:
            print("Deck shuffled - count reset recommnded")

    def draw(self):
        if not self.cards:
            self.reset()
        return self.cards.pop()


def hand():
    return None