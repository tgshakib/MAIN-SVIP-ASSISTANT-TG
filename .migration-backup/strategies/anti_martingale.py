"""
Mode 7 — ANTI-MARTINGALE
WIN  → double the amount next trade.
LOSS → restart at base amount.
After 3 consecutive wins → restart at base amount.
Grows on winning streaks, protects capital on losing streaks.
"""


def init_state() -> dict:
    return {"current_amount": None, "consecutive_wins": 0}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    current_amount = state.get("current_amount") or base_amount
    consecutive_wins = state.get("consecutive_wins", 0)

    if result == "win":
        consecutive_wins += 1
        if consecutive_wins >= 3:
            return base_amount, {"current_amount": base_amount, "consecutive_wins": 0}
        next_amt = current_amount * 2
        return next_amt, {"current_amount": next_amt, "consecutive_wins": consecutive_wins}
    else:
        return base_amount, {"current_amount": base_amount, "consecutive_wins": 0}
