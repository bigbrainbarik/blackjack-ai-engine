# 🂡 Blackjack AI Engine

A feature-rich Blackjack web app built with **Streamlit**, combining a full game engine with AI-powered decision advisory. Play manually while a Neural Network and Basic Strategy advisor guide your decisions in real time.

---

## 🚀 Features

- **Multi-seat gameplay** — Play 1–3 seats simultaneously, each with independent hands and bets
- **AI Advisory** — Live recommendations from a trained Neural Network and Basic Strategy engine
- **Card Counting** — Hi-Lo system with running count, true count, and cards-remaining display
- **Dynamic Bet Sizing** — Automatic bet suggestions based on the true count (₹10–₹500)
- **Pillow-rendered Cards** — Custom playing cards (150×210px) and chip stacks with animations
- **3 Themes** — Casino Green, Dark Neon, and Minimalist Dark
- **Sound Effects** — Procedural Web Audio sounds for deal, hit, win, lose, and chip actions
- **Analytics Dashboard** — Bankroll chart, win-rate trends, action frequency, bet-vs-payout scatter, round history with CSV export
- **Interactive Tutorial** — Learn rules, strategy, card counting, and test yourself with quizzes
- **Full Action Set** — Hit, Stand, Double Down, Split, Surrender, Insurance

---

## 🧠 Neural Network

| | |
|---|---|
| **Framework** | PyTorch |
| **Architecture** | 5 → 64 → 64 → 4 (fully connected) |
| **Inputs** | Dealer up-card, player total, running count, true count, cards remaining |
| **Outputs** | Hit, Stand, Double, Split |
| **Accuracy** | ~92% |

The model runs inference locally via `ml_model/blackjack_nn.pt` — no external API calls.

---

## 🖥️ Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/<your-username>/Blackjack.git
cd Blackjack
pip install -r requirements.txt
```

### Run

```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501` with three pages: **Game**, **Analytics**, and **Tutorial**.

---

## 📁 Project Structure

```
Blackjack/
├── streamlit_app.py          # Main game interface (Streamlit)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Streamlit theme & server config
├── core/                     # Game engine
│   ├── game.py               # State-machine game logic
│   ├── hand.py               # Hand (total, bust, blackjack)
│   ├── deck.py               # Multi-deck shoe with auto-reshuffle
│   ├── counting.py           # Hi-Lo card counting
│   └── player.py             # Player bankroll management
├── ml_model/                 # Neural network
│   ├── nn_inference.py       # BlackjackNet model + prediction
│   ├── blackjack_nn.pt       # Trained model weights
│   └── action_labels.pt      # Action label mappings
├── strategy/
│   └── basic_strategy.py     # Rule-based basic strategy
├── tools/
│   └── bet_sizing.py         # True-count-based bet sizing
├── ui/                       # UI components
│   ├── themes.py             # 3 CSS themes + nav hiding
│   ├── animations.py         # Card/chip animation HTML/CSS/JS
│   ├── multi_seat.py         # Multi-seat manager (1–3 seats)
│   ├── sounds.py             # Web Audio procedural sounds
│   ├── effects.py            # Confetti, glow, flash effects
│   └── state.py              # Session state defaults
├── gui/                      # Renderers
│   ├── card_renderer.py      # Pillow card image generation
│   └── chip_renderer.py      # Pillow chip image generation
├── pages/                    # Streamlit multipage
│   ├── 1_Analytics.py        # Session analytics dashboard
│   └── 2_Tutorial.py         # Interactive tutorial & quiz
└── tests/
    └── test_core.py          # 35 unit tests (pytest)
```

---

## 🧪 Testing

```bash
python -m pytest tests/test_core.py -v
```

35 tests covering Card, Hand, Deck, Counter, Player, and Game classes.

---

## 🛠️ Tech Stack

- **Streamlit 1.55** — Web UI framework
- **PyTorch** — Neural network inference
- **Pillow** — Card and chip image rendering
- **Plotly** — Interactive analytics charts
- **Pandas** — Data handling for analytics
- **Web Audio API** — Procedural sound effects (no audio files)

---

## 📄 License

This project is for educational purposes.
