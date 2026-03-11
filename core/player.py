from core.hand import Hand


class Player:
    def __init__(self, money=1000):
        self.money = money
        self.hand = Hand()
        self.bet = 0

    def place_bet(self, amount):
        self.bet = amount

    def win(self, multiplier=1):
        """Add winnings. multiplier=1 for normal win, 1.5 for blackjack 3:2."""
        self.money += int(self.bet * multiplier)
        self.bet = 0

    def lose(self):
        self.money -= self.bet
        self.bet = 0

    def push(self):
        self.bet = 0

    def reset(self):
        self.hand = Hand()
