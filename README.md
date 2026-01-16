# 🂡 Blackjack AI Engine

A complete Blackjack simulation engine that combines:

- Basic Strategy
- Neural Network–based decision making
- Card counting (Hi-Lo)
- Dynamic bet sizing
- Strategy comparison framework
- Interactive GUI

This project demonstrates how machine learning can be applied to decision-making under uncertainty using a controlled simulation environment.

---

## 🚀 Features

- Full Blackjack game engine (player, dealer, deck, rules)
- Hi-Lo card counting system
- Neural Network trained on millions of simulated hands
- Dynamic bet sizing using true count
- Switchable strategy:
  - Basic Strategy
  - Neural Network
- Tkinter GUI for interactive play
- Evaluation scripts for policy comparison
- Clean, modular Python architecture

---

## 🧠 Neural Network Overview

- **Framework:** PyTorch
- **Input features:**
  - Dealer up-card
  - Player hand total
  - Running count
  - True count
  - Cards remaining
- **Output actions:**
  - H → Hit
  - S → Stand
  - D → Double
  - P → Split
- **Evaluation accuracy:** ~92%

---

## 🖥️ GUI Usage

Run the GUI to play step-by-step Blackjack hands:

```bash
python gui/blackjack_gui.py
