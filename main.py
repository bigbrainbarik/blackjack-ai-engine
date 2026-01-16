from core.game import Game

game = Game()

while True:
    print("Money:", game.player.money)
    from tools.bet_sizing import calculate_bet

    true_count = game.counter.true_count(len(game.deck.cards))
    bet = calculate_bet(true_count, game.player.money)

    print(f"True Count: {round(true_count, 2)} | Bet: {bet}")
    game.player.place_bet(bet)

    game.deal()
    game.play()

    print("Player:", game.player.hand.total())
    print("Dealer:", game.dealer.hand.total())

    if game.player.money <= 0:
        print("Game Over")
        break
