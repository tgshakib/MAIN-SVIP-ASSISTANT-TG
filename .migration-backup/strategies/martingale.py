"""
Mode 5 — MARTINGALE (1-MTG)
Every LOSS doubles the amount.
First WIN → restart at base.
If next calculated amount exceeds stop_loss → session auto-stops (handled externally).
"""


def init_state() -> dict:
    return {"current_multiplier": 1}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    current_multiplier = state.get("current_multiplier", 1)
    stop_loss = config.get("stop_loss", float("inf"))

    if result == "win":
        return base_amount, {"current_multiplier": 1}
    else:
        next_multiplier = current_multiplier * 2
        next_amt = base_amount * next_multiplier
        if next_amt >= stop_loss:
            return next_amt, {"current_multiplier": next_multiplier, "stop_loss_exceeded": True}
        return next_amt, {"current_multiplier": next_multiplier}
