import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import mm_database as mmdb
from locale import format_amount, round_amount, get_labels
from strategies import get_next_amount

router = Router()

DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━"


def _count_consecutive_losses(session_id: int) -> int:
    import sqlite3, os
    DB_PATH = os.environ.get("DB_PATH", "mm_bot.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    trades = conn.execute(
        "SELECT result FROM mm_trades WHERE session_id=? ORDER BY trade_num DESC",
        (session_id,)
    ).fetchall()
    conn.close()
    count = 0
    for t in trades:
        if t["result"] == "loss":
            count += 1
        else:
            break
    return count


async def _send_vanish_alert(message, text: str, delay: int = 8):
    try:
        msg = await message.answer(text)
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass
    except Exception:
        pass


def _fresh_trade_keyboard(user_id: int, session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅  WIN", callback_data=f"mm_win_{session_id}"),
            InlineKeyboardButton(text="❌  LOSS", callback_data=f"mm_loss_{session_id}"),
        ],
        [
            InlineKeyboardButton(text="🔒 Close Session", callback_data=f"mm_close_{session_id}"),
            InlineKeyboardButton(text="🔁 New Session",   callback_data="mm_new_session"),
        ],
        [
            InlineKeyboardButton(text="🏠 Back to Home",  callback_data="mm_session_back_confirm"),
        ],
    ])


def _build_trade_card(session: dict, cent: bool, lang: str = "en") -> str:
    trade_num    = session["trade_number"]
    mode_name    = session["mode_name"]
    amount       = session["current_amount"]
    amount_str   = format_amount(amount, cent)
    capital      = session["capital"]
    balance      = session["balance"]
    wins         = session["wins"]
    losses       = session["losses"]
    total_trades = session["total_trades"]
    planned      = session["trades_planned"]
    stop_loss    = session["stop_loss"]
    target       = session["session_target"]

    profit       = round(balance - capital, 2)
    L            = get_labels(lang)

    if profit > 0:
        profit_display = f"+${profit:.2f} ✅"
    elif profit < 0:
        profit_display = f"-${abs(profit):.2f} ❌"
    else:
        profit_display = f"$0.00"

    if total_trades > 0:
        raw_wr = round(wins / total_trades * 100)
        if raw_wr >= 50:
            winrate_display = f"{raw_wr}% ✅"
        else:
            deficit = raw_wr - 50
            winrate_display = f"{deficit}% ⚠️"
    else:
        winrate_display = "—"

    return (
        f"🔢 *{L['trade']} #{trade_num}*  |  `{mode_name}`\n"
        f"`{DIVIDER}`\n"
        f"💰  *{L['enter_amount']}:*\n\n"
        f"        ➤  `${amount_str}`\n\n"
        f"`{DIVIDER}`\n"
        f"💵  {L['capital']}:   `${capital:.2f}`\n"
        f"🏦  {L['balance']}:   `${balance:.2f}`\n"
        f"`{DIVIDER}`\n"
        f"✅ {L['wins']}: `{wins}`    ❌ {L['losses']}: `{losses}`\n"
        f"📊 {L['trades']}: `{total_trades}` / `{planned}`\n"
        f"`{DIVIDER}`\n"
        f"📈  {L['win_rate']}:  *{winrate_display}*\n"
        f"💰  {L['profit']}:   *{profit_display}*\n"
        f"`{DIVIDER}`\n"
        f"🛑  {L['stop_loss']}:  `${stop_loss:.2f}`\n"
        f"🎯  {L['target']}:     `${target:.2f}`\n"
        f"`{DIVIDER}`"
    )


async def send_trade_dashboard(message_or_obj, user_id: int, session_id: int):
    """Send the trade dashboard as a new message."""
    import sqlite3, json, os
    DB_PATH = os.environ.get("DB_PATH", "mm_bot.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM mm_sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return
    session = dict(row)
    session["mode_state"] = json.loads(session.get("mode_state") or "{}")

    cent = bool(session.get("cent_account", 0))
    lang = mmdb.get_user_language(user_id)
    text = _build_trade_card(session, cent, lang)
    kb   = _fresh_trade_keyboard(user_id, session_id)

    if isinstance(message_or_obj, Message):
        await message_or_obj.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message_or_obj.answer(text, reply_markup=kb, parse_mode="Markdown")


async def _handle_trade_result(callback: CallbackQuery, result: str):
    user_id    = callback.from_user.id
    lang       = mmdb.get_user_language(user_id)
    L          = get_labels(lang)
    parts      = callback.data.split("_")
    session_id = int(parts[-1])

    import sqlite3, json, os
    DB_PATH = os.environ.get("DB_PATH", "mm_bot.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM mm_sessions WHERE id=? AND status='active'", (session_id,)).fetchone()
    conn.close()

    if not row:
        await callback.answer("Session not found.", show_alert=True)
        return

    session      = dict(row)
    session["mode_state"] = json.loads(session.get("mode_state") or "{}")

    cent          = bool(session.get("cent_account", 0))
    current_amt   = session["current_amount"]
    payout_pct    = session["payout_pct"]
    stop_loss     = session["stop_loss"]
    session_target = session["session_target"]
    mode_num      = session["mode_num"]

    if result == "win":
        trade_pl = round(current_amt * (payout_pct / 100), 2)
    else:
        trade_pl = -current_amt

    new_balance     = round(session["balance"] + trade_pl, 2)
    new_wins        = session["wins"] + (1 if result == "win" else 0)
    new_losses      = session["losses"] + (1 if result == "loss" else 0)
    new_trade_num   = session["trade_number"] + 1
    current_profit  = round(new_balance - session["capital"], 2)

    config = {"stop_loss": stop_loss, "payout_pct": payout_pct}
    next_amt, new_state = get_next_amount(
        mode_num, result, session["base_amount"], session["mode_state"], config
    )
    next_amt = max(1.0, next_amt)
    next_amt = round_amount(next_amt, cent)

    mmdb.update_session_after_trade(
        session_id, result, current_amt, trade_pl,
        new_balance, next_amt, new_state,
        new_wins, new_losses, new_trade_num
    )

    await callback.answer("✅ WIN recorded!" if result == "win" else "❌ LOSS recorded!")

    try:
        await callback.message.delete()
    except Exception:
        pass

    # Check stop conditions
    if current_profit <= -stop_loss:
        mmdb.close_session(session_id)
        wins_f   = new_wins
        losses_f = new_losses
        total_f  = new_wins + new_losses
        raw_wr   = round((wins_f / total_f * 100) if total_f > 0 else 0)
        if raw_wr >= 50:
            wr_display = f"{raw_wr}% ✅"
        else:
            wr_display = f"{raw_wr - 50}% ⚠️"
        loss_display = f"-${abs(current_profit):.2f} ❌"
        text = (
            f"🛑 *{L['stop_loss_reached']}*\n"
            f"{L['closed_safety']}\n"
            f"`{DIVIDER}`\n"
            f"Total Loss:    *{loss_display}*\n"
            f"Total Trades:  `{total_f}`\n"
            f"✅ {L['wins']}: `{wins_f}`   ❌ {L['losses']}: `{losses_f}`\n"
            f"{L['win_rate']}:      *{wr_display}*\n"
            f"`{DIVIDER}`\n"
            f"{L['smarter_risk']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁 New Session", callback_data="mm_new_session"),
                InlineKeyboardButton(text="🏠 Home",        callback_data="back_main"),
            ]
        ])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        return

    if result == "win" and current_profit >= session_target:
        mmdb.close_session(session_id)
        wins_f   = new_wins
        losses_f = new_losses
        total_f  = new_wins + new_losses
        raw_wr   = round((wins_f / total_f * 100) if total_f > 0 else 0)
        if raw_wr >= 50:
            wr_display = f"{raw_wr}% ✅"
        else:
            wr_display = f"{raw_wr - 50}% ⚠️"
        profit_display = f"+${current_profit:.2f} ✅"
        text = (
            f"🎉 *{L['congratulations']}!*\n"
            "Your session target is reached!\n"
            f"`{DIVIDER}`\n"
            f"Final Profit:  *{profit_display}*\n"
            f"Total Trades:  `{total_f}`\n"
            f"✅ {L['wins']}: `{wins_f}`   ❌ {L['losses']}: `{losses_f}`\n"
            f"{L['win_rate']}:      *{wr_display}*\n"
            f"`{DIVIDER}`\n"
            "Want to improve your trading?\n"
            "Try our AI Bot, SVIP Signals or\n"
            "Premium Software.\n"
            "DM Support Team for details."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁 New Session", callback_data="mm_new_session"),
                InlineKeyboardButton(text="🏠 Home",        callback_data="back_main"),
            ]
        ])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        return

    if mode_num == 5 and new_state.get("stop_loss_exceeded"):
        mmdb.close_session(session_id)
        text = (
            f"🛑 *{L['stop_loss_reached']}*\n"
            "Next Martingale amount would exceed\n"
            "your stop loss. Session closed.\n"
            f"`{DIVIDER}`\n"
            f"{L['smarter_risk']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁 New Session", callback_data="mm_new_session"),
                InlineKeyboardButton(text="🏠 Home",        callback_data="back_main"),
            ]
        ])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        return

    # Count consecutive losses and send alerts
    consec = _count_consecutive_losses(session_id)

    # Re-read session and send fresh trade card
    conn2 = sqlite3.connect(DB_PATH)
    conn2.row_factory = sqlite3.Row
    row2  = conn2.execute("SELECT * FROM mm_sessions WHERE id=?", (session_id,)).fetchone()
    conn2.close()
    if not row2:
        return
    session2 = dict(row2)
    session2["mode_state"] = json.loads(session2.get("mode_state") or "{}")

    text = _build_trade_card(session2, cent, lang)
    kb   = _fresh_trade_keyboard(user_id, session_id)
    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")

    # Send consecutive loss warnings AFTER the trade card
    if consec >= 7:
        asyncio.create_task(_send_vanish_alert(
            callback.message,
            "⛔ STOP TRADING FOR TODAY ❌\n\n7 losses in a row detected.\nTake a full break and return tomorrow.",
            delay=8
        ))
    elif consec >= 5:
        asyncio.create_task(_send_vanish_alert(
            callback.message,
            "⚠️ WINRATE not good\nAvoided trading for 1/2hr\nTrade later again.",
            delay=8
        ))


@router.callback_query(F.data.startswith("mm_win_"))
async def mm_win(callback: CallbackQuery):
    await _handle_trade_result(callback, "win")


@router.callback_query(F.data.startswith("mm_loss_"))
async def mm_loss(callback: CallbackQuery):
    await _handle_trade_result(callback, "loss")


@router.callback_query(F.data == "mm_session_back_confirm")
async def mm_session_back_confirm(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, Leave", callback_data="back_main"),
            InlineKeyboardButton(text="Cancel",     callback_data="mm_session_cancel_back"),
        ]
    ])
    await callback.answer()
    await callback.message.answer(
        "This will close your active session. Continue?\n"
        "(Your session data will be lost)",
        reply_markup=kb
    )


@router.callback_query(F.data == "mm_session_cancel_back")
async def mm_session_cancel_back(callback: CallbackQuery):
    await callback.answer("Continuing session.")
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("mm_close_all_"))
async def mm_close_all(callback: CallbackQuery):
    user_id = callback.from_user.id
    mmdb.close_all_sessions(user_id)
    await callback.answer("All sessions closed.")
    await callback.message.answer("All sessions have been closed.")


@router.callback_query(F.data.startswith("mm_close_"))
async def mm_close_session(callback: CallbackQuery):
    user_id  = callback.from_user.id
    lang     = mmdb.get_user_language(user_id)
    L        = get_labels(lang)
    parts    = callback.data.split("_")
    session_id = int(parts[-1])

    import sqlite3, json, os
    DB_PATH = os.environ.get("DB_PATH", "mm_bot.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM mm_sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()

    if row:
        session = dict(row)
        mmdb.close_session(session_id)
        profit = round(session["balance"] - session["capital"], 2)
        total_trades = session["total_trades"]
        raw_wr = round((session["wins"] / total_trades * 100) if total_trades > 0 else 0)

        if profit > 0:
            profit_display = f"+${profit:.2f} ✅"
        elif profit < 0:
            profit_display = f"-${abs(profit):.2f} ❌"
        else:
            profit_display = "$0.00"

        if total_trades > 0:
            if raw_wr >= 50:
                wr_display = f"{raw_wr}% ✅"
            else:
                wr_display = f"{raw_wr - 50}% ⚠️"
        else:
            wr_display = "—"

        text = (
            f"*{L['session_closed']}*\n"
            f"`{DIVIDER}`\n"
            f"Mode:    `{session['mode_name']}`\n"
            f"Trades:  `{total_trades}`\n"
            f"✅ {L['wins']}: `{session['wins']}`   ❌ {L['losses']}: `{session['losses']}`\n"
            f"📈 {L['win_rate']}:  *{wr_display}*\n"
            f"💰 {L['profit']}:   *{profit_display}*"
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Home", callback_data="back_main")]
        ])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.answer("Session not found.")

    await callback.answer("Session closed.")


@router.callback_query(F.data == "mm_new_session")
async def mm_new_session(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not mmdb.is_mm_premium(user_id):
        if not mmdb.can_start_free_session(user_id):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Buy Access", callback_data="mm_buy_access")],
                [InlineKeyboardButton(text="🏠 Home",       callback_data="back_main")],
            ])
            await callback.message.answer(
                "Your free session for today has been used.\n"
                "Upgrade to start unlimited sessions.\n\n"
                "_A new free session will be available tomorrow._",
                reply_markup=kb,
                parse_mode="Markdown"
            )
            await callback.answer()
            return

    await state.clear()
    from handlers.mm_setup import MMSetupStates, _p1_text, _p1_kb
    data = {}
    text = _p1_text(data)
    kb   = _p1_kb(data, user_id)
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()
