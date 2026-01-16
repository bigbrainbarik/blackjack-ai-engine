import ast
import os
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import confusion_matrix, classification_report

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "blackjack_simulator.csv")
MODEL_PATH = os.path.join(BASE_DIR, "blackjack_nn.pt")
LABEL_PATH = os.path.join(BASE_DIR, "action_labels.pt")

SAMPLE_SIZE = 200_000  # evaluation subset

# -----------------------------
# MODEL DEFINITION
# -----------------------------

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

# -----------------------------
# HELPERS
# -----------------------------

def extract_first_action(actions):
    """
    Safely extract first blackjack action: H, S, P, or D.
    Returns None if invalid.
    """
    if isinstance(actions, str):
        try:
            actions = ast.literal_eval(actions)
        except Exception:
            return None

    if not isinstance(actions, list) or len(actions) == 0:
        return None

    # Flatten nested lists
    while isinstance(actions, list) and len(actions) > 0 and isinstance(actions[0], list):
        actions = actions[0]

    if not actions:
        return None

    first = actions[0]

    if first in ("H", "S", "P", "D"):
        return first

    return None


def compute_hand_total(hand):
    if isinstance(hand, str):
        hand = ast.literal_eval(hand)
    total = sum(hand)
    aces = hand.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

# -----------------------------
# LOAD DATA
# -----------------------------

print("Loading evaluation data...")
df = pd.read_csv(CSV_PATH, nrows=SAMPLE_SIZE)

df["true_action"] = df["actions_taken"].apply(extract_first_action)
df = df.dropna(subset=["true_action"])
df["player_total"] = df["initial_hand"].apply(compute_hand_total)

X = df[
    ["dealer_up", "player_total", "run_count", "true_count", "cards_remaining"]
].values

y_true = df["true_action"].values

# -----------------------------
# LOAD MODEL
# -----------------------------

model = BlackjackNet()
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

labels = torch.load(LABEL_PATH, weights_only=False)

# -----------------------------
# PREDICT
# -----------------------------

with torch.no_grad():
    logits = model(torch.tensor(X, dtype=torch.float32))
    y_pred_idx = torch.argmax(logits, dim=1).numpy()

y_pred = [labels[i] for i in y_pred_idx]

# -----------------------------
# METRICS
# -----------------------------

print("\nClassification Report:")
print(classification_report(y_true, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_true, y_pred))
