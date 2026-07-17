import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import mm_database as mmdb
from locale import calculate_base_amount, format_amount, round_amount
from strategies import get_strategy_name, get_init_state, STRATEGY_MAP

router = Router()

FREE_CAPITAL_LIMIT = 50.0
DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━"

MODE_INFO = {
    1:  ("REGULAR",            "LOW",        "1/10",  "50%+"),
    2:  ("1-STEP COMPOUNDING", "LOW-MEDIUM", "2/10",  "45%+"),
    3:  ("2-STEP COMPOUNDING", "MEDIUM",     "3/10",  "40%+"),
    4:  ("3-STEP COMPOUNDING", "MEDIUM-HIGH","4/10",  "38%+"),
    5:  ("MARTINGALE (1-MTG)", "HIGH",       "5/10",  "45%+"),
    6:  ("OSCAR'S GRIND",      "LOW",        "2/10",  "30%+"),
    7:  ("ANTI-MARTINGALE",    "LOW-MEDIUM", "3/10",  "40%+"),
    8:  ("FLAT BET",           "VERY LOW",   "1/10",  "55%+"),
    9:  ("FIBONACCI",          "MEDIUM",     "3/10",  "40%+"),
    10: ("D'ALEMBERT",         "LOW",        "2/10",  "35%+"),
}

MODE_DESC = {
    1:  "Win=next doubles. Loss=stay same until win.",
    2:  "Loss on trade 1 = trade 2 doubles. Restart after trade 2.",
    3:  "2 consecutive losses trigger double. Restart after trade 3.",
    4:  "3 consecutive losses trigger double. Restart after trade 4.",
    5:  "Every loss doubles. First win = restart base.",
    6:  "Loss=same unit. Win=+1 unit. Net+1 profit = restart.",
    7:  "Win=double. Loss=restart base. 3 wins in a row=restart.",
    8:  "Every trade = same base amount. No progression.",
    9:  "Loss=move forward in sequence. Win=2 steps back.",
    10: "Loss=+1 unit. Win=-1 unit. Gentlest system.",
}

RECOMMENDED = {6, 8, 10}


class MMSetupStates(StatesGroup):
    input_capital        = State()
    input_accuracy       = State()
    input_num_trades     = State()
    input_daily_profit   = State()
    input_payout         = State()
    input_total_trades   = State()
    input_wins_needed    = State()
    input_stop_loss      = State()
    input_session_target = State()


def _is_premium(user_id: int) -> bool:
    return mmdb.is_mm_premium(user_id)


# ── Live dashboard helpers ─────────────────────────────────────
def _val(v, fmt: str = "") -> str:
    if v is None:
        return "—"
    if fmt == "$":
        return f"${v:.2f} ✅"
    if fmt == "%":
        return f"{v:.0f}% ✅"
    if fmt == "int":
        return f"{int(v)} ✅"
    return f"{v} ✅"


# ── Page 1 panel ──────────────────────────────────────────────
def _p1_kb(data: dict, user_id: int) -> InlineKeyboardMarkup:
    cap  = data.get("setup_capital")
    acc  = data.get("setup_accuracy")
    nt   = data.get("setup_num_trades")
    dp   = data.get("setup_daily_profit")
    ca   = data.get("setup_cent_account", False)
    po   = data.get("setup_payout")

    cap_lbl = f"💰 Capital: ${cap:.2f}" if cap is not None else "💰 Capital: Tap to set"
    acc_lbl = f"📊 Accuracy: {acc:.0f}%" if acc is not None else "📊 Accuracy: Tap to set"
    nt_lbl  = f"🔢 Trades: {nt}" if nt is not None else "🔢 Trades: Tap to set (optional)"
    dp_lbl  = f"🎯 Profit: ${dp:.2f}" if dp is not None else "🎯 Daily Profit: Tap to set"
    ca_lbl  = f"🏦 Broker support Cent: {'Yes ✅' if ca else 'No  —'}"
    po_lbl  = f"💹 Payout: {po:.0f}%" if po is not None else "💹 Payout %: Tap to set"

    required_filled = all(v is not None for v in [cap, acc, dp, po])

    rows = [
        [InlineKeyboardButton(text=cap_lbl, callback_data="mm_input_capital"),
         InlineKeyboardButton(text=acc_lbl, callback_data="mm_input_accuracy")],
        [InlineKeyboardButton(text=nt_lbl,  callback_data="mm_input_num_trades")],
        [InlineKeyboardButton(text=dp_lbl,  callback_data="mm_input_daily_profit"),
         InlineKeyboardButton(text=po_lbl,  callback_data="mm_input_payout")],
        [InlineKeyboardButton(text=ca_lbl,  callback_data="mm_toggle_cent")],
    ]
    if required_filled:
        rows.append([InlineKeyboardButton(text="▶️  Continue → Page 2", callback_data="mm_page2")])
    rows.append([InlineKeyboardButton(text="◀️  Back to Menu", callback_data="mm_back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _p1_text(data: dict) -> str:
    cap = data.get("setup_capital")
    acc = data.get("setup_accuracy")
    nt  = data.get("setup_num_trades")
    dp  = data.get("setup_daily_profit")
    ca  = data.get("setup_cent_account", False)
    po  = data.get("setup_payout")

    cent_lbl = "Yes ✅" if ca else "No —"
    nt_lbl   = f"{int(nt)} ✅" if nt is not None else "— (optional)"

    return (
        "*SESSION SETUP — Page 1 of 2*\n"
        f"`{DIVIDER}`\n"
        "📋 *LIVE SETUP DASHBOARD:*\n"
        f"  💰 Capital:   {_val(cap, '$')}\n"
        f"  📊 Accuracy:  {_val(acc, '%')}\n"
        f"  🔢 Trades:    {nt_lbl}\n"
        f"  🎯 Profit:    {_val(dp, '$')}\n"
        f"  💹 Payout:    {_val(po, '%')}\n"
        f"  🏦 Cent:      {cent_lbl}\n"
        f"`{DIVIDER}`\n"
        "_Tap each button below to set a value._"
    )


# ── Page 2 panel ──────────────────────────────────────────────
def _p2_kb(data: dict) -> InlineKeyboardMarkup:
    wn  = data.get("setup_wins_needed")
    sl  = data.get("setup_stop_loss")
    st  = data.get("setup_session_target")
    mn  = data.get("setup_mode_num")

    wn_lbl = f"🏆 Wins Needed: {wn}"         if wn is not None else "🏆 Wins Needed: Tap to set"
    sl_lbl = f"🛑 Stop Loss: ${sl:.2f}"       if sl is not None else "🛑 Stop Loss $: Tap to set"
    st_lbl = f"🎯 Target: ${st:.2f}"          if st is not None else "🎯 Session Target: Tap to set"
    if mn is not None:
        rec = " ⭐" if mn in RECOMMENDED else ""
        mn_lbl = f"🎮 Mode: {MODE_INFO[mn][0]}{rec}"
    else:
        mn_lbl = "🎮 Trading Mode: Tap to choose"

    all_filled = all(v is not None for v in [wn, sl, st, mn])

    if all_filled:
        rows = [
            [InlineKeyboardButton(text="🚀  START TRADING", callback_data="mm_confirm_start")],
            [InlineKeyboardButton(text="◀️  Back to Page 1", callback_data="mm_page1")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=rows)

    rows = [
        [InlineKeyboardButton(text=wn_lbl, callback_data="mm_input_wins_needed")],
        [InlineKeyboardButton(text=sl_lbl, callback_data="mm_input_stop_loss"),
         InlineKeyboardButton(text=st_lbl, callback_data="mm_input_session_target")],
        [InlineKeyboardButton(text=mn_lbl, callback_data="mm_select_mode")],
    ]
    rows.append([
        InlineKeyboardButton(text="◀️  Page 1", callback_data="mm_page1"),
        InlineKeyboardButton(text="🏠 Menu",    callback_data="mm_back_to_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _p2_text(data: dict = None) -> str:
    if data is None:
        data = {}
    # P1 values
    cap = data.get("setup_capital")
    acc = data.get("setup_accuracy")
    nt  = data.get("setup_num_trades")
    dp  = data.get("setup_daily_profit")
    ca  = data.get("setup_cent_account", False)
    po  = data.get("setup_payout")
    # P2 values
    wn  = data.get("setup_wins_needed")
    sl  = data.get("setup_stop_loss")
    st  = data.get("setup_session_target")
    mn  = data.get("setup_mode_num")

    all_filled = all(v is not None for v in [wn, sl, st, mn])

    cent_lbl = "Yes ✅" if ca else "No —"
    nt_lbl   = f"{int(nt)} ✅" if nt is not None else "— (optional)"

    if mn is not None:
        rec = " ⭐" if mn in RECOMMENDED else ""
        mode_display = f"{MODE_INFO[mn][0]}{rec} ✅"
    else:
        mode_display = "—"

    status_line = "✅ *All set! Tap START TRADING.*" if all_filled else "_Tap buttons below to set values._"

    return (
        "*SESSION SETUP — Page 2 of 2*\n"
        f"`{DIVIDER}`\n"
        "📋 *FULL SETUP DASHBOARD:*\n"
        f"`{DIVIDER}`\n"
        "*Page 1:*\n"
        f"  💰 Capital:  {_val(cap, '$')}\n"
        f"  📊 Accuracy: {_val(acc, '%')}\n"
        f"  🔢 Trades:   {nt_lbl}\n"
        f"  🎯 Profit:   {_val(dp, '$')}\n"
        f"  💹 Payout:   {_val(po, '%')}\n"
        f"  🏦 Cent:     {cent_lbl}\n"
        f"`{DIVIDER}`\n"
        "*Page 2:*\n"
        f"  🏆 Wins:     {_val(wn, 'int')}\n"
        f"  🛑 Loss:     {_val(sl, '$')}\n"
        f"  🎯 Target:   {_val(st, '$')}\n"
        f"  🎮 Mode:     {mode_display}\n"
        f"`{DIVIDER}`\n"
        f"{status_line}"
    )


# ── Mode selection panel ──────────────────────────────────────
def _mode_select_kb(selected: int = None) -> InlineKeyboardMarkup:
    rows = []
    for i in range(1, 11, 2):
        row = []
        for num in [i, i + 1]:
            if num > 10:
                break
            name  = MODE_INFO[num][0]
            rec   = " ⭐" if num in RECOMMENDED else ""
            tick  = " ✅" if num == selected else ""
            short = name[:12] if len(name) > 12 else name
            row.append(InlineKeyboardButton(
                text=f"{num}. {short}{rec}{tick}",
                callback_data=f"mm_mode_{num}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️  Back", callback_data="mm_page2")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _mode_select_text() -> str:
    lines = [
        "*SELECT TRADING MODE*",
        f"`{DIVIDER}`",
        "",
    ]
    for num in range(1, 11):
        name, risk, rank, winrate = MODE_INFO[num]
        desc = MODE_DESC[num]
        rec  = "  ⭐ Recommended" if num in RECOMMENDED else ""
        lines.append(f"*{num}. {name}*{rec}")
        lines.append(f"   _{desc}_")
        lines.append(f"   Risk: `{risk}`  |  Rank: `{rank}`  |  Win: `{winrate}`")
        lines.append("")
    return "\n".join(lines)


# ── Prompt message tracker ────────────────────────────────────
async def _save_prompt(state: FSMContext, msg):
    """Save the prompt message's chat_id and message_id so we can delete it later."""
    await state.update_data(
        mm_prompt_chat_id=msg.chat.id,
        mm_prompt_msg_id=msg.message_id,
    )


async def _delete_prompt(state: FSMContext, bot):
    """Delete the saved prompt message."""
    data = await state.get_data()
    chat_id = data.get("mm_prompt_chat_id")
    msg_id  = data.get("mm_prompt_msg_id")
    if chat_id and msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        await state.update_data(mm_prompt_chat_id=None, mm_prompt_msg_id=None)


# ── START SESSION ─────────────────────────────────────────────
@router.callback_query(F.data == "mm_start_session")
async def mm_start_session(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    mmdb.upsert_mm_user(user_id, callback.from_user.username or "")

    if not _is_premium(user_id):
        if not mmdb.can_start_free_session(user_id):
            text = (
                "*ACCESS REQUIRED*\n"
                f"`{DIVIDER}`\n"
                "Your free session for today\n"
                "has been used.\n\n"
                "Upgrade to continue trading\n"
                "with unlimited sessions.\n\n"
                "_A new free session resets tomorrow._"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Buy Access", callback_data="mm_buy_access")],
                [InlineKeyboardButton(text="🏠 Home",       callback_data="back_main")],
            ])
            try:
                await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
            await callback.answer()
            return

    await state.clear()
    data = {}
    text = _p1_text(data)
    kb   = _p1_kb(data, user_id)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


# ── Navigation ────────────────────────────────────────────────
@router.callback_query(F.data == "mm_back_to_menu")
async def mm_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.mm_menu import open_mm_menu
    await open_mm_menu(callback)


@router.callback_query(F.data == "mm_page1")
async def mm_go_page1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    text = _p1_text(data)
    kb   = _p1_kb(data, callback.from_user.id)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "mm_page2")
async def mm_go_page2(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    text = _p2_text(data)
    kb   = _p2_kb(data)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


# ── Cent Account Toggle ────────────────────────────────────────
@router.callback_query(F.data == "mm_toggle_cent")
async def mm_toggle_cent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("setup_cent_account", False)
    await state.update_data(setup_cent_account=not current)
    data = await state.get_data()
    text = _p1_text(data)
    kb   = _p1_kb(data, callback.from_user.id)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        pass
    await callback.answer("Broker support Cent: " + ("Yes ✅" if not current else "No"))


# ── Mode Selection ────────────────────────────────────────────
@router.callback_query(F.data == "mm_select_mode")
async def mm_select_mode(callback: CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    selected = data.get("setup_mode_num")
    text     = _mode_select_text()
    kb       = _mode_select_kb(selected)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mm_mode_"))
async def mm_mode_selected(callback: CallbackQuery, state: FSMContext):
    mode_num = int(callback.data.split("_")[-1])
    await state.update_data(setup_mode_num=mode_num)
    data = await state.get_data()
    text = _p2_text(data)
    kb   = _p2_kb(data)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer(f"Mode selected: {MODE_INFO[mode_num][0]}")


# ── Input prompts ─────────────────────────────────────────────
async def _ask(callback: CallbackQuery, state: FSMContext, new_state, prompt: str, back_cb: str):
    await state.set_state(new_state)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️  Back", callback_data=back_cb)]
    ])
    try:
        msg = await callback.message.edit_text(prompt, parse_mode="Markdown", reply_markup=kb)
        if msg:
            await _save_prompt(state, msg)
        else:
            await _save_prompt(state, callback.message)
    except Exception:
        msg = await callback.message.answer(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_prompt(state, msg)
    await callback.answer()


@router.callback_query(F.data == "mm_input_capital")
async def ask_capital(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_capital,
               "*Enter your Trading Capital* ($):\n_(Example: 100)_", "mm_page1")


@router.callback_query(F.data == "mm_input_accuracy")
async def ask_accuracy(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_accuracy,
               "*Enter your Trading Accuracy* (%):\n_(Example: 65)_", "mm_page1")


@router.callback_query(F.data == "mm_input_num_trades")
async def ask_num_trades(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_num_trades,
               "*How many trades this session?*\n_(Type a number, or type: *skip*)_", "mm_page1")


@router.callback_query(F.data == "mm_input_daily_profit")
async def ask_daily_profit(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_daily_profit,
               "*How much profit do you want today?* ($)\n_(Example: 20)_", "mm_page1")


@router.callback_query(F.data == "mm_input_payout")
async def ask_payout(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_payout,
               "*Enter broker Market Payout* (%):\n_(Example: 80)_", "mm_page1")


@router.callback_query(F.data == "mm_input_total_trades")
async def ask_total_trades(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_total_trades,
               "*Total trades planned this session?*\n_(Example: 10)_", "mm_page2")


@router.callback_query(F.data == "mm_input_wins_needed")
async def ask_wins_needed(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_wins_needed,
               "*How many wins do you need?*\n_(Example: 6)_", "mm_page2")


@router.callback_query(F.data == "mm_input_stop_loss")
async def ask_stop_loss(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_stop_loss,
               "*Max loss before session auto-stops?* ($)\n_(Example: 15)_", "mm_page2")


@router.callback_query(F.data == "mm_input_session_target")
async def ask_session_target(callback: CallbackQuery, state: FSMContext):
    await _ask(callback, state, MMSetupStates.input_session_target,
               "*Profit amount to auto-close session?* ($)\n_(Example: 20)_", "mm_page2")


# ── Text input handlers ───────────────────────────────────────

async def _back_to_p1(message: Message, state: FSMContext):
    await _delete_prompt(state, message.bot)
    await state.set_state(None)
    data = await state.get_data()
    cap = data.get("setup_capital")
    acc = data.get("setup_accuracy")
    dp  = data.get("setup_daily_profit")
    po  = data.get("setup_payout")
    required_filled = all(v is not None for v in [cap, acc, dp, po])
    if required_filled:
        await message.answer(_p2_text(data), parse_mode="Markdown", reply_markup=_p2_kb(data))
    else:
        await message.answer(_p1_text(data), parse_mode="Markdown",
                             reply_markup=_p1_kb(data, message.from_user.id))


async def _back_to_p2(message: Message, state: FSMContext):
    await _delete_prompt(state, message.bot)
    await state.set_state(None)
    data = await state.get_data()
    await message.answer(_p2_text(data), parse_mode="Markdown", reply_markup=_p2_kb(data))


@router.message(MMSetupStates.input_capital)
async def recv_capital(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a valid amount greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
        return
    if not _is_premium(user_id) and value > FREE_CAPITAL_LIMIT:
        await message.answer(f"Free Access allows maximum ${FREE_CAPITAL_LIMIT:.0f} capital.\n"
                             f"Please enter ${FREE_CAPITAL_LIMIT:.0f} or less.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
        return
    await state.update_data(setup_capital=value)
    await _back_to_p1(message, state)


@router.message(MMSetupStates.input_accuracy)
async def recv_accuracy(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text)
        assert 1 <= value <= 100
    except (ValueError, AssertionError):
        await message.answer("Please enter a number between 1 and 100.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
        return
    await state.update_data(setup_accuracy=value)
    await _back_to_p1(message, state)


@router.message(MMSetupStates.input_num_trades)
async def recv_num_trades(message: Message, state: FSMContext):
    text = message.text.strip().lower() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    if text == "skip":
        await state.update_data(setup_num_trades=None)
    else:
        try:
            value = int(text)
            assert value > 0
            # sync to setup_total_trades so P2 / launch session can use it
            await state.update_data(setup_num_trades=value, setup_total_trades=value)
        except (ValueError, AssertionError):
            await message.answer("Please enter a whole number or type: skip",
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
            return
    await _back_to_p1(message, state)


@router.message(MMSetupStates.input_daily_profit)
async def recv_daily_profit(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a valid amount greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
        return
    await state.update_data(setup_daily_profit=value)
    await _back_to_p1(message, state)


@router.message(MMSetupStates.input_payout)
async def recv_payout(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text)
        assert 1 <= value <= 200
    except (ValueError, AssertionError):
        await message.answer("Please enter a valid payout % (1 to 200).",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page1")]]))
        return
    await state.update_data(setup_payout=value)
    await _back_to_p1(message, state)


@router.message(MMSetupStates.input_total_trades)
async def recv_total_trades(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = int(text)
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a whole number greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page2")]]))
        return
    await state.update_data(setup_total_trades=value)
    await _back_to_p2(message, state)


@router.message(MMSetupStates.input_wins_needed)
async def recv_wins_needed(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = int(text)
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a whole number greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page2")]]))
        return
    await state.update_data(setup_wins_needed=value)
    await _back_to_p2(message, state)


@router.message(MMSetupStates.input_stop_loss)
async def recv_stop_loss(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a valid amount greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page2")]]))
        return
    await state.update_data(setup_stop_loss=value)
    await _back_to_p2(message, state)


@router.message(MMSetupStates.input_session_target)
async def recv_session_target(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer("Please enter a valid amount greater than 0.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="◀️ Back", callback_data="mm_page2")]]))
        return
    await state.update_data(setup_session_target=value)
    await _back_to_p2(message, state)


# ── CONFIRM: show summary before launching ────────────────────
@router.callback_query(F.data == "mm_confirm_start")
async def mm_confirm_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    capital        = data.get("setup_capital", 100)
    accuracy       = data.get("setup_accuracy", 50)
    payout         = data.get("setup_payout", 80)
    stop_loss      = data.get("setup_stop_loss", 15)
    session_target = data.get("setup_session_target", 20)
    cent_account   = data.get("setup_cent_account", False)
    mode_num       = data.get("setup_mode_num", 1)
    mode_name      = get_strategy_name(mode_num)

    base_amount = calculate_base_amount(capital, accuracy, payout, stop_loss, mode_num)
    base_amount = max(1.0, base_amount)
    base_amount = round_amount(base_amount, cent_account)

    adjusted_note = ""
    raw = calculate_base_amount(capital, accuracy, payout, stop_loss, mode_num)
    if raw < 1.0:
        adjusted_note = "\n_Base Trade Amount adjusted to minimum $1.00_"

    await state.update_data(setup_base_amount=base_amount)

    win_profit = round(base_amount * (payout / 100), 2)

    confirm_text = (
        "*Session Setup Complete*\n"
        f"`{DIVIDER}`\n"
        f"🎮 Mode:       *{mode_name}*\n"
        f"💹 Payout:     `{payout:.0f}%`\n"
        f"🛑 Stop Loss:  `${stop_loss:.2f}`\n"
        f"🎯 Target:     `${session_target:.2f}`\n"
        f"💰 Base Amt:   `${base_amount:.2f}`{adjusted_note}\n"
        f"`{DIVIDER}`\n"
        f"Trade  1:  `${base_amount:.2f}`\n"
        f"✅ WIN  →  `+${win_profit:.2f}`\n"
        f"❌ LOSS →  `-${base_amount:.2f}`\n"
        f"`{DIVIDER}`"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Start Trading", callback_data="mm_do_start")],
        [InlineKeyboardButton(text="◀️ Back",          callback_data="mm_page2")],
    ])

    try:
        await callback.message.edit_text(confirm_text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "mm_do_start")
async def mm_do_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await _launch_session(callback.message, callback.from_user.id, data)
    await callback.answer()


# ── LAUNCH SESSION ────────────────────────────────────────────
async def _launch_session(message, user_id: int, data: dict):
    capital      = data.get("setup_capital", 100)
    accuracy     = data.get("setup_accuracy", 50)
    payout       = data.get("setup_payout", 80)
    stop_loss    = data.get("setup_stop_loss", 15)
    cent_account = data.get("setup_cent_account", False)
    mode_num     = data.get("setup_mode_num", 1)
    mode_name    = get_strategy_name(mode_num)
    init_state   = get_init_state(mode_num)

    base_amount = data.get("setup_base_amount") or \
                  calculate_base_amount(capital, accuracy, payout, stop_loss, mode_num)
    base_amount = max(1.0, base_amount)
    base_amount = round_amount(base_amount, cent_account)

    session_target = data.get("setup_session_target", 20)

    session_data = {
        "mode_num":       mode_num,
        "mode_name":      mode_name,
        "capital":        capital,
        "payout_pct":     payout,
        "stop_loss":      stop_loss,
        "session_target": session_target,
        "daily_target":   data.get("setup_daily_profit", 20),
        "overall_target": session_target,
        "trades_planned": data.get("setup_total_trades") or data.get("setup_num_trades") or 10,
        "wins_needed":    data.get("setup_wins_needed", 6),
        "cent_account":   cent_account,
        "base_amount":    base_amount,
        "current_amount": base_amount,
        "mode_state":     init_state,
    }

    session_id = mmdb.create_session(user_id, session_data)

    if not _is_premium(user_id):
        mmdb.increment_free_session(user_id)

    from handlers.mm_session import send_trade_dashboard
    await send_trade_dashboard(message, user_id, session_id)
