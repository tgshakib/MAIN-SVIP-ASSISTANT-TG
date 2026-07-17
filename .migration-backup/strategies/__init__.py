from strategies.regular import init_state as regular_init, next_amount as regular_next
from strategies.compounding_1step import init_state as comp1_init, next_amount as comp1_next
from strategies.compounding_2step import init_state as comp2_init, next_amount as comp2_next
from strategies.compounding_3step import init_state as comp3_init, next_amount as comp3_next
from strategies.martingale import init_state as mtg_init, next_amount as mtg_next
from strategies.oscars_grind import init_state as oscar_init, next_amount as oscar_next
from strategies.anti_martingale import init_state as antimtg_init, next_amount as antimtg_next
from strategies.flat_bet import init_state as flat_init, next_amount as flat_next
from strategies.fibonacci import init_state as fib_init, next_amount as fib_next
from strategies.dalembert import init_state as dal_init, next_amount as dal_next

STRATEGY_MAP = {
    1: ("Regular",             regular_init,  regular_next),
    2: ("1-Step Compounding",  comp1_init,    comp1_next),
    3: ("2-Step Compounding",  comp2_init,    comp2_next),
    4: ("3-Step Compounding",  comp3_init,    comp3_next),
    5: ("Martingale (1-MTG)",  mtg_init,      mtg_next),
    6: ("Oscar's Grind",       oscar_init,    oscar_next),
    7: ("Anti-Martingale",     antimtg_init,  antimtg_next),
    8: ("Flat Bet",            flat_init,     flat_next),
    9: ("Fibonacci",           fib_init,      fib_next),
    10: ("D'Alembert",         dal_init,      dal_next),
}


def get_strategy_name(mode: int) -> str:
    return STRATEGY_MAP.get(mode, (f"Mode {mode}", None, None))[0]


def get_init_state(mode: int) -> dict:
    entry = STRATEGY_MAP.get(mode)
    if entry:
        return entry[1]()
    return {}


def get_next_amount(mode: int, result: str, base_amount: float, state: dict, config: dict) -> tuple:
    entry = STRATEGY_MAP.get(mode)
    if entry:
        return entry[2](result, base_amount, state, config)
    return base_amount, state
