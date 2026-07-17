"""
Mode 8 — FLAT BET
Every trade uses the same base amount.
No progression up or down.
Safest mode. Best for consistent win rates.
"""


def init_state() -> dict:
    return {}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    return base_amount, {}
