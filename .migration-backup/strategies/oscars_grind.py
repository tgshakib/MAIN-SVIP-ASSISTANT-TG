"""
Mode 6 — OSCAR'S GRIND
Start at 1 unit.
LOSS → same unit size next trade.
WIN  → increase by 1 unit next trade.
When series profit reaches +1 unit (in base_amount) → restart at 1 unit.
Works effectively at 30%+ win rate.
"""


def init_state() -> dict:
    return {"units": 1, "series_profit": 0.0}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    units = state.get("units", 1)
    series_profit = state.get("series_profit", 0.0)
    current_bet = base_amount * units

    if result == "win":
        series_profit += current_bet
        if series_profit >= base_amount:
            return base_amount, {"units": 1, "series_profit": 0.0}
        else:
            new_units = units + 1
            next_bet = base_amount * new_units
            if series_profit + next_bet > base_amount:
                adjusted_units = max(1, round((base_amount - series_profit) / base_amount))
                return base_amount * adjusted_units, {"units": adjusted_units, "series_profit": series_profit}
            return next_bet, {"units": new_units, "series_profit": series_profit}
    else:
        series_profit -= current_bet
        return current_bet, {"units": units, "series_profit": series_profit}
