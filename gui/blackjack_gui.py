import sys
import os

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

import tkinter as tk
from tkinter import ttk

from strategy.basic_strategy import suggest_move
from core.game import Game
from ml_model.nn_inference import predict_action
from tools.bet_sizing import calculate_bet

# ======================
# INIT GAME
# ======================

game = Game()

# ======================
# GUI WINDOW
# ======================

root = tk.Tk()
root.title("Blackjack AI Engine")
root.geometry("520x420")
root.resizable(False, False)

# ======================
# UI VARIABLES
# ======================

money_var = tk.StringVar()
bet_var = tk.StringVar()
count_var = tk.StringVar()
player_var = tk.StringVar()
dealer_var = tk.StringVar()
decision_var = tk.StringVar()
policy_var = tk.StringVar(value="NN")  # default = Neural Network


# ======================
# FUNCTIONS
# ======================

def play_hand():
    if game.player.money <= 0:
        decision_var.set("GAME OVER")
        return

    game.deal()

    true_count = game.counter.true_count(len(game.deck.cards))
    bet = calculate_bet(true_count, game.player.money)
    game.player.place_bet(bet)

    # Player turn
    while True:
        player_total = game.player.hand.total()
        if player_total > 21:
            break

        dealer_up = game.dealer.hand.cards[0].value

        # Decide move based on selected policy
        if policy_var.get() == "NN":
            move = predict_action(
                dealer_up=dealer_up,
                player_total=player_total,
                run_count=game.counter.running_count,
                true_count=true_count,
                cards_remaining=len(game.deck.cards)
            )
            decision_source = "Neural Net"
        else:
            move = suggest_move(player_total, dealer_up).upper()[0]
            decision_source = "Basic Strategy"

        # Execute move
        if move == "H":
            card = game.deck.draw()
            game.player.hand.add(card)
            game.counter.update(card)
        else:
            break

    # Dealer turn
    while game.dealer.hand.total() < 17:
        card = game.deck.draw()
        game.dealer.hand.add(card)
        game.counter.update(card)

    game.resolve_round()
    update_ui(move, true_count, bet, decision_source)



def update_ui(move, true_count, bet, source):

    money_var.set(f"Money: {game.player.money}")
    bet_var.set(f"Bet: {bet}")
    count_var.set(f"Running Count: {game.counter.running_count} | True Count: {round(true_count, 2)}")
    player_var.set(f"Player Total: {game.player.hand.total()}")
    dealer_var.set(f"Dealer Total: {game.dealer.hand.total()}")
    decision_var.set(f"{source} Decision: {move}")


# ======================
# UI LAYOUT
# ======================

title = ttk.Label(root, text="🂡 Blackjack AI Engine", font=("Arial", 18))
title.pack(pady=10)
policy_frame = ttk.LabelFrame(root, text="Decision Policy")
policy_frame.pack(pady=5)

ttk.Radiobutton(
    policy_frame,
    text="Neural Network",
    variable=policy_var,
    value="NN"
).pack(side="left", padx=10)

ttk.Radiobutton(
    policy_frame,
    text="Basic Strategy",
    variable=policy_var,
    value="BS"
).pack(side="left", padx=10)


ttk.Label(root, textvariable=money_var, font=("Arial", 12)).pack()
ttk.Label(root, textvariable=bet_var, font=("Arial", 12)).pack()
ttk.Label(root, textvariable=count_var, font=("Arial", 11)).pack(pady=5)

ttk.Label(root, textvariable=player_var, font=("Arial", 14)).pack(pady=5)
ttk.Label(root, textvariable=dealer_var, font=("Arial", 14)).pack(pady=5)

ttk.Label(root, textvariable=decision_var, font=("Arial", 12)).pack(pady=10)

ttk.Button(root, text="Play Next Hand", command=play_hand).pack(pady=15)

# ======================
# INITIAL UI STATE
# ======================

money_var.set(f"Money: {game.player.money}")
bet_var.set("Bet: -")
count_var.set("Running Count: 0 | True Count: 0")
player_var.set("Player Total: -")
dealer_var.set("Dealer Total: -")
decision_var.set("Click 'Play Next Hand'")

# ======================
# START GUI
# ======================

root.mainloop()
