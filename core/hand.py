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
