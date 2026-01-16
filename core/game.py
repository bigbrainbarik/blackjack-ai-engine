from ml_model.nn_inference import predict_action
from strategy.basic_strategy import suggest_move
from core.deck import Deck
from core.player import Player
from core.counting import Counter

class Game:
    def resolve_round(self):
        player_total = self.player.hand.total()
        dealer_total = self.dealer.hand.total()
        bet = self.player.bet

        # Player bust
        if player_total > 21:
            self.player.money -= bet
            return

        # Dealer bust
        if dealer_total > 21:
            self.player.money += bet
            return

        # Compare totals
        if player_total > dealer_total:
            self.player.money += bet
        elif player_total < dealer_total:
            self.player.money -= bet
        else:
            pass  # push

    def __init__(self, verbose=True, policy="NN"):
        self.deck = Deck()
        self.player = Player()
        self.dealer = Player()
        self.counter = Counter()
        self.verbose = verbose
        self.policy = policy

    def deal(self):
        # RESET HANDS EVERY ROUND
        self.player.reset()
        self.dealer.reset()

        # Deal initial cards
        card = self.deck.draw()
        self.player.hand.add(card)
        self.counter.update(card)

        card = self.deck.draw()
        self.dealer.hand.add(card)
        self.counter.update(card)

        card = self.deck.draw()
        self.player.hand.add(card)
        self.counter.update(card)

        card = self.deck.draw()
        self.dealer.hand.add(card)
        self.counter.update(card)

    def play(self):
        while self.player.hand.total() < 17:
            card = self.deck.draw()
            self.player.hand.add(card)
            self.counter.update(card)

        while True:
            player_total = self.player.hand.total()

            # STOP if bust
            if player_total > 21:
                break

            dealer_card = self.dealer.hand.cards[0].value
            tc = self.counter.true_count(len(self.deck.cards))

            nn_move = predict_action(
                dealer_up=dealer_card,
                player_total=player_total,
                run_count=self.counter.running_count,
                true_count=tc,
                cards_remaining=len(self.deck.cards)
            )

            bs_move = suggest_move(player_total, dealer_card).upper()[0]

            if self.policy == "NN":
                move = nn_move
            else:
                move = bs_move

        p = self.player.hand.total()
        d = self.dealer.hand.total()

        if p > 21:
            self.player.lose()
        elif d > 21 or p > d:
            self.player.win()
        else:
            self.player.lose()
        print("Running Count:", self.counter.running_count)


