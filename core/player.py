from core.hand import Hand

class Player:
    def __init__(self, money=1000):
        self.money = money
        self.hand = Hand()
        self.bet = 0

    def place_bet(self, amount):
        self.bet = amount


    def win(self):
        self.money += self.bet * 2
        self.bet = 0

    def lose(self):
        self.bet = 0

    def reset(self):
        self.hand = Hand()
