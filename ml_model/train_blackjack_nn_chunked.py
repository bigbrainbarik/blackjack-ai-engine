import ast
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, TensorDataset
import os

# ==============================
# CONFIGURATION (SAFE DEFAULTS)
# ==============================

CSV_PATH = "blackjack_simulator.csv"   # <-- change if needed
CHUNK_SIZE = 200_000                  # rows per chunk (safe for 16GB RAM)
EPOCHS = 3                            # per chunk (keep small)
BATCH_SIZE = 512
LEARNING_RATE = 0.001

DEVICE = "cpu"  # integrated graphics → CPU only
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = BASE_DIR  # ml_model directory


# ==============================
# HELPER FUNCTIONS
# ==============================

def extract_first_action(actions):
    """
    Always returns a single action character: 'H', 'S', 'P', or 'D'
    Returns None if action is invalid
    """
    # Convert string → list if needed
    if isinstance(actions, str):
        try:
            actions = ast.literal_eval(actions)
        except Exception:
            return None

    # Must be a list and not empty
    if not isinstance(actions, list) or len(actions) == 0:
        return None

    # Flatten nested lists like [['H','S']]
    while isinstance(actions[0], list):
        actions = actions[0]
        if len(actions) == 0:
            return None

    first = actions[0]

    # Ensure final output is a single valid action
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


# ==============================
# NEURAL NETWORK
# ==============================

class BlackjackNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 4)  # H, S, P, D
        )

    def forward(self, x):
        return self.net(x)

model = BlackjackNet().to(DEVICE)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

label_encoder = LabelEncoder()
label_fitted = False

# ==============================
# TRAINING LOOP (CHUNKED)
# ==============================

print("Starting chunked training...")

chunk_number = 0

for chunk in pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE):
    chunk_number += 1
    print(f"\nProcessing chunk {chunk_number}")

    # ------------------------------
    # Feature Engineering
    # ------------------------------

    chunk["first_action"] = chunk["actions_taken"].apply(extract_first_action)
    chunk = chunk.dropna(subset=["first_action"])
    chunk["player_initial_total"] = chunk["initial_hand"].apply(compute_hand_total)

    features = chunk[
        [
            "dealer_up",
            "player_initial_total",
            "run_count",
            "true_count",
            "cards_remaining"
        ]
    ].values

    labels = chunk["first_action"].astype(str).values

    # ------------------------------
    # Encode Labels (once)
    # ------------------------------

    if not label_fitted:
        labels_encoded = label_encoder.fit_transform(labels)
        torch.save(label_encoder.classes_, os.path.join(SAVE_DIR, "action_labels.pt"))
        label_fitted = True
        print("Label encoder fitted:", label_encoder.classes_)
    else:
        labels_encoded = label_encoder.transform(labels)

    # ------------------------------
    # Convert to Torch Tensors
    # ------------------------------

    X = torch.tensor(features, dtype=torch.float32).to(DEVICE)
    y = torch.tensor(labels_encoded, dtype=torch.long).to(DEVICE)

    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # ------------------------------
    # Train on This Chunk
    # ------------------------------

    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            preds = model(xb)
            loss = loss_fn(preds, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Chunk {chunk_number} | Epoch {epoch}/{EPOCHS} | Loss: {total_loss:.4f}")

    # ------------------------------
    # Optional Early Stop
    # ------------------------------

    if chunk_number == 20:
        print("Stopping early after 20 chunks (safe default).")
        break

# ==============================
# SAVE MODEL
# ==============================

torch.save(model.state_dict(), os.path.join(SAVE_DIR, "blackjack_nn.pt"))
print("\nTraining complete. Model saved.")
