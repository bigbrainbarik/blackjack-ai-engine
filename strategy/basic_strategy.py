# This function tells us whether to HIT or STAND
# based on player's total and dealer's visible card

def suggest_move(player_total, dealer_card):
    """
    player_total: int (sum of player's hand)
    dealer_card: int (dealer visible card value)
    """

    # Always hit on 11 or less
    if player_total <= 11:
        return "hit"

    # Always stand on 17 or more
    if player_total >= 17:
        return "stand"

    # If dealer has strong card (7 to Ace), be aggressive
    if dealer_card >= 7:
        return "hit"

    # Otherwise stand
    return "stand"
