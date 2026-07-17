"""
Mode 1 — REGULAR
WIN  → next trade is 2x base. After that win → restart.
LOSS → stay at base until first win, then 2x base, then restart.
"""


def init_state() -> dict:
    return {"phase": "normal"}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    phase = state.get("phase", "normal")

    if phase == "normal":
        if result == "win":
            return base_amount * 2, {"phase": "after_win"}
        else:
            return base_amount, {"phase": "normal"}

    elif phase == "after_win":
        if result == "win":
            return base_amount, {"phase": "normal"}
        else:
            return base_amount, {"phase": "normal"}

    return base_amount, {"phase": "normal"}
