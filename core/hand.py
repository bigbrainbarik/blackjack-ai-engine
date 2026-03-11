class Hand:
    def __init__(self):
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def total(self):
        total = 0
        aces = 0
        for card in self.cards:
            total += card.value
            if card.rank == "A":
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def bust(self):
        return self.total() > 21

    @property
    def is_soft(self):
        """True when at least one ace is still counted as 11."""
        total = 0
        aces = 0
        for card in self.cards:
            total += card.value
            if card.rank == "A":
                aces += 1
        reduced = 0
        while total > 21 and aces:
            total -= 10
            aces -= 1
            reduced += 1
        return aces > 0  # unreduced aces remain → soft hand

    @property
    def is_pair(self):
        """True when the hand has exactly 2 cards of the same value (e.g. 10-J, K-Q)."""
        return len(self.cards) == 2 and self.cards[0].value == self.cards[1].value

    @property
    def is_blackjack(self):
        """Natural blackjack: exactly 2 cards totalling 21."""
        return len(self.cards) == 2 and self.total() == 21

    def __repr__(self):
        return " | ".join(str(c) for c in self.cards)
