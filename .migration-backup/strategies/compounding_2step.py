"""
Mode 3 — 2-STEP COMPOUNDING
Trade 1: Base
  WIN  → restart
  LOSS → Trade 2: 2x Base
Trade 2: 2x Base
  WIN  → restart
  LOSS → Trade 3: 4x Base
Trade 3: 4x Base — WIN or LOSS → always restart
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
        if result == "win":
            return base_amount, {"step": 1}
        else:
            return base_amount * 4, {"step": 3}

    elif step == 3:
        return base_amount, {"step": 1}

    return base_amount, {"step": 1}
