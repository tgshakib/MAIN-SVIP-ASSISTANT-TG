"""
Mode 2 — 1-STEP COMPOUNDING
Trade 1: Base Amount
  WIN  → restart at base
  LOSS → Trade 2: 2x Base
Trade 2: 2x Base — WIN or LOSS → always restart at base
"""


def init_state() -> dict:
    return {"step": 1}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    step = state.get("step", 1)

    if step == 1:
        if result == "win":
            return base_amount, {"step": 1}
        else:
            return base_amount * 2, {"step": 2}

    elif step == 2:
        return base_amount, {"step": 1}

    return base_amount, {"step": 1}
