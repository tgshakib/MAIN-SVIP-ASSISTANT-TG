"""
Mode 10 — D'ALEMBERT
Start at 1 unit.
LOSS → next amount = current + 1 unit.
WIN  → next amount = current - 1 unit (minimum 1 unit).
Gentle progression. Works effectively at 35%+ win rate.
"""


def init_state() -> dict:
    return {"units": 1}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    units = state.get("units", 1)

    if result == "win":
        new_units = max(1, units - 1)
    else:
        new_units = units + 1

    return base_amount * new_units, {"units": new_units}
