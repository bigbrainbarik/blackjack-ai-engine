class Counter:
    def __init__(self):
        self.running_count = 0

    def update(self, card):
        """
        Updates running count using Hi-Lo system
        """
        if card.rank in ["2", "3", "4", "5", "6"]:
            self.running_count += 1
        elif card.rank in ["10", "J", "Q", "K", "A"]:
            self.running_count -= 1
        # 7,8,9 do nothing

    def reset(self):
        self.running_count = 0

    def true_count(self, cards_remaining):
        decks_remaining = max(1, cards_remaining / 52)
        return self.running_count / decks_remaining
