import os
import torch
import torch.nn as nn

# ==============================
# PATH SETUP
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "blackjack_nn.pt")
LABEL_PATH = os.path.join(BASE_DIR, "action_labels.pt")

DEVICE = "cpu"

# ==============================
# NEURAL NETWORK DEFINITION
# (MUST MATCH TRAINING)
# ==============================

class BlackjackNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 4)
        )

    def forward(self, x):
        return self.net(x)

# ==============================
# LOAD MODEL + LABELS
# ==============================

model = BlackjackNet().to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()

action_labels = torch.load(LABEL_PATH, weights_only=False)

# ==============================
# PREDICTION FUNCTION
# ==============================

def predict_action(
    dealer_up,
    player_total,
    run_count,
    true_count,
    cards_remaining
):
    """
    Returns one of: 'H', 'S', 'P', 'D'
    """
    features = torch.tensor(
        [[
            dealer_up,
            player_total,
            run_count,
            true_count,
            cards_remaining
        ]],
        dtype=torch.float32
    ).to(DEVICE)

    with torch.no_grad():
        logits = model(features)
        predicted_index = torch.argmax(logits, dim=1).item()

    return action_labels[predicted_index]
