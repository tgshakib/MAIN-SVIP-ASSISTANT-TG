"""
Mode 9 — FIBONACCI
Sequence: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144...
LOSS → move 1 step forward in sequence (increase amount).
WIN  → move 2 steps backward (decrease amount, minimum step 0).
Restart when back to step 0.
Works effectively at 40%+ win rate.
"""

FIB_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]


def _fib(index: int) -> int:
    if index < len(FIB_SEQUENCE):
        return FIB_SEQUENCE[index]
    a, b = FIB_SEQUENCE[-2], FIB_SEQUENCE[-1]
    for _ in range(index - len(FIB_SEQUENCE) + 1):
        a, b = b, a + b
    return b


def init_state() -> dict:
    return {"fib_index": 0}


def next_amount(result: str, base_amount: float, state: dict, config: dict) -> tuple:
    fib_index = state.get("fib_index", 0)

    if result == "win":
        new_index = max(0, fib_index - 2)
    else:
        new_index = fib_index + 1

    next_amt = base_amount * _fib(new_index)
    return next_amt, {"fib_index": new_index}
