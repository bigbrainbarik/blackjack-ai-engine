def calculate_bet(true_count, bankroll):
    """
    Smart bet sizing with minimum bet protection
    """

    # If bankroll too small, go all-in
    if bankroll < 10:
        return bankroll

    # Base bet from count
    if true_count <= 0:
        bet = 10
    elif true_count < 2:
        bet = 50
    elif true_count < 3:
        bet = 100
    elif true_count < 4:
        bet = 300
    else:
        bet = 500

    # Risk control: max 25% of bankroll
    max_bet = max(10, int(bankroll * 0.25))

    return min(bet, max_bet)
