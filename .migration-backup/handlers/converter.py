import json
import os
import re
import time

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

SETTINGS_FILE = "user_settings.json"

# Cooldown tracker {user_id: {action: last_ts}}
_cooldowns: dict = {}

# All world timezones (label, offset_minutes)
TIMEZONES = [
    ("UTC-12:00", -720), ("UTC-11:00", -660), ("UTC-10:00", -600),
    ("UTC-9:30",  -570), ("UTC-9:00",  -540), ("UTC-8:00",  -480),
    ("UTC-7:00",  -420), ("UTC-6:00",  -360), ("UTC-5:00",  -300),
    ("UTC-4:00",  -240), ("UTC-3:30",  -210), ("UTC-3:00",  -180),
    ("UTC-2:00",  -120), ("UTC-1:00",   -60), ("UTC+0:00",     0),
    ("UTC+1:00",    60), ("UTC+2:00",   120), ("UTC+3:00",   180),
    ("UTC+3:30",   210), ("UTC+4:00",   240), ("UTC+4:30",   270),
    ("UTC+5:00",   300), ("UTC+5:30",   330), ("UTC+5:45",   345),
    ("UTC+6:00",   360), ("UTC+6:30",   390), ("UTC+7:00",   420),
    ("UTC+8:00",   480), ("UTC+8:45",   525), ("UTC+9:00",   540),
    ("UTC+9:30",   570), ("UTC+10:00",  600), ("UTC+10:30",  630),
    ("UTC+11:00",  660), ("UTC+12:00",  720), ("UTC+12:45",  765),
    ("UTC+13:00",  780), ("UTC+14:00",  840),
]

# ── FSM States ────────────────────────────────────────────────
class ConverterStates(StatesGroup):
    active               = State()   # main panel / waiting for timezone-mode signal
    waiting_swipe_signal = State()   # waiting for signal to swipe
    waiting_format       = State()   # waiting for custom format template


# ── Settings persistence ──────────────────────────────────────
def _load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_settings(data: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user_settings(user_id: int) -> dict | None:
    return _load_settings().get(str(user_id))


def save_user_settings(user_id: int, from_tz: str, from_min: int,
                       to_tz: str, to_min: int, fmt: str | None = None):
    settings = _load_settings()
    entry = {
        "from_tz": from_tz, "from_min": from_min,
        "to_tz":   to_tz,   "to_min":   to_min,
    }
    if fmt:
        entry["format"] = fmt
    settings[str(user_id)] = entry
    _save_settings(settings)


# ── Cooldown ──────────────────────────────────────────────────
def _check_cooldown(user_id: int, action: str, seconds: int = 3) -> bool:
    now = time.time()
    user_cd = _cooldowns.setdefault(user_id, {})
    if now - user_cd.get(action, 0) < seconds:
        return False
    user_cd[action] = now
    return True


# ── Timezone label encode/decode ──────────────────────────────
def _encode_tz(label: str) -> str:
    return label.replace("+", "p").replace("-", "m").replace(":", "c")

def _decode_tz(safe: str) -> str:
    return safe.replace("p", "+").replace("m", "-").replace("c", ":")

def _tz_minutes(label: str) -> int | None:
    for lbl, mins in TIMEZONES:
        if lbl == label:
            return mins
    return None


# ── Conversion: timezone shift ────────────────────────────────
def _shift_line(line: str, diff_minutes: int) -> str:
    def _shift(m):
        total = int(m.group(1)) * 60 + int(m.group(2)) + diff_minutes
        total = total % (24 * 60)
        if total < 0:
            total += 24 * 60
        return f"{total // 60:02d}:{total % 60:02d}"
    return re.sub(r'\b(\d{1,2}):(\d{2})\b', _shift, line)

def convert_signals(text: str, from_min: int, to_min: int) -> str:
    diff = to_min - from_min
    lines = []
    for line in text.strip().split('\n'):
        if re.search(r'\b\d{1,2}:\d{2}\b', line):
            lines.append(_shift_line(line, diff))
        else:
            lines.append(line)
    return '\n'.join(lines)


# ── Conversion: swipe entry/exit directions ───────────────────
def swipe_signals(text: str) -> str:
    """Swap CALL↔PUT and UP↔DOWN (case-insensitive, outputs uppercase)."""
    result = []
    for line in text.strip().split('\n'):
        line = re.sub(r'\bCALL\b', '__CALL__', line, flags=re.IGNORECASE)
        line = re.sub(r'\bUP\b',   '__UP__',   line, flags=re.IGNORECASE)
        line = re.sub(r'\bPUT\b',  '__PUT__',  line, flags=re.IGNORECASE)
        line = re.sub(r'\bDOWN\b', '__DOWN__', line, flags=re.IGNORECASE)
        line = line.replace('__CALL__', 'PUT')
        line = line.replace('__UP__',   'DOWN')
        line = line.replace('__PUT__',  'CALL')
        line = line.replace('__DOWN__', 'UP')
        result.append(line)
    return '\n'.join(result)


# ── Format template apply ─────────────────────────────────────
def _apply_format(converted_text: str, template: str) -> str:
    sep = ';' if ';' in template else ' '
    result = []
    for line in converted_text.strip().split('\n'):
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue
        time_m  = re.search(r'\b(\d{1,2}:\d{2})\b', stripped)
        dir_m   = re.search(r'\b(CALL|PUT)\b', stripped, re.IGNORECASE)
        pair_m  = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', stripped)
        fmt_line = (template
                    .replace("HH:MM",    time_m.group(1)           if time_m  else "")
                    .replace("CALL/PUT", dir_m.group(1).upper()     if dir_m   else "")
                    .replace("PAIR",     pair_m.group(1)            if pair_m  else "")
                    .replace("TF",       ""))
        result.append(fmt_line.strip(sep) if fmt_line != template else line)
    return '\n'.join(result)


# ── Chat wipe helper ──────────────────────────────────────────
async def _wipe_and_home(callback: CallbackQuery, state: FSMContext):
    """
    Wipe all recent messages (range-based, survives restarts)
    then show a fresh home screen.
    """
    from user_msg_tracker import wipe_chat
    import database as db
    from handlers.user import start_text, _start_keyboard, _is_admin

    await state.clear()
    user    = callback.from_user
    chat_id = callback.message.chat.id
    sub     = db.get_active_subscription(user.id)

    # Range-based wipe — no memory state required
    await wipe_chat(callback.bot, chat_id, callback.message.message_id)

    await callback.bot.send_message(
        chat_id,
        start_text(user.first_name, sub, user.username, is_admin=_is_admin(user.id)),
        parse_mode="Markdown",
        reply_markup=_start_keyboard(sub, user.id),
    )


# ── Keyboards ─────────────────────────────────────────────────
def _converter_panel_kb(from_set: bool, to_set: bool, signal_set: bool) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text="🌍 FROM Timezone", callback_data="conv_from"),
        InlineKeyboardButton(text="🌐 TO Timezone",   callback_data="conv_to"),
    ]]
    confirm_row = []
    if from_set and to_set and signal_set:
        confirm_row.append(InlineKeyboardButton(text="✅ CONFIRM", callback_data="conv_confirm"))
    confirm_row.append(InlineKeyboardButton(text="🔀 SWIPE ENTRY", callback_data="conv_swipe_entry"))
    rows.append(confirm_row)
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _converter_saved_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ CONFIRM",           callback_data="conv_confirm")],
        [
            InlineKeyboardButton(text="🔀 SWIPE ENTRY",    callback_data="conv_swipe_entry"),
            InlineKeyboardButton(text="✏️ CHANGE SETTINGS", callback_data="conv_change"),
        ],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")],
    ])


def _tz_list_kb(which: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for label, _ in TIMEZONES:
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"tz_{which}_{_encode_tz(label)}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Back to Converter", callback_data="conv_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💾 SAVE SETTING", callback_data="conv_save"),
            InlineKeyboardButton(text="📋 COPY",         callback_data="conv_copy"),
        ],
        [
            InlineKeyboardButton(text="🔀 SWIPE",        callback_data="conv_swipe_result"),
            InlineKeyboardButton(text="🧾 FORMAT",       callback_data="conv_format"),
        ],
        [InlineKeyboardButton(text="⬅️ Back to Home",    callback_data="back_main")],
    ])


def _swipe_paste_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="conv_panel")]
    ])


def _swipe_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ CONFIRM SWIPE", callback_data="conv_confirm_swipe")],
        [InlineKeyboardButton(text="❌ Cancel",         callback_data="conv_panel")],
    ])


# ── Text builders ─────────────────────────────────────────────
def _panel_text(from_tz: str | None, to_tz: str | None) -> str:
    return (
        "🔄 *Converter Panel*\n\n"
        f"🌍 FROM: *{from_tz or '❌ Not set'}*\n"
        f"🌐 TO:   *{to_tz   or '❌ Not set'}*\n\n"
        "📋 Paste your signal list below 👇\n"
        "_(Select timezones, paste your list, then press ✅ CONFIRM)_"
    )


def _result_text(header: str, converted: str) -> str:
    body = f"{header}\n\n```\n{converted}\n```"
    if len(body) > 4000:
        body = body[:3990] + "\n...(truncated)```"
    return body


# ── Open converter (shared) ───────────────────────────────────
async def _open_converter(event, state: FSMContext, edit: bool):
    user_id  = event.from_user.id
    settings = get_user_settings(user_id)

    if settings:
        from_tz, to_tz = settings["from_tz"], settings["to_tz"]
        await state.update_data(
            from_tz=from_tz, from_min=settings["from_min"],
            to_tz=to_tz,     to_min=settings["to_min"],
            fmt=settings.get("format"),
            signal_text=None, converted_text=None,
        )
        await state.set_state(ConverterStates.active)
        text = (
            "🔄 *Converter Panel*\n\n"
            "✅ *Your saved setting:*\n"
            f"🌍 FROM: *{from_tz}*\n"
            f"🌐 TO:   *{to_tz}*\n\n"
            "📋 Paste your signal list 👇"
        )
        kb = _converter_saved_kb()
    else:
        await state.update_data(
            from_tz=None, from_min=None,
            to_tz=None,   to_min=None,
            fmt=None, signal_text=None, converted_text=None,
        )
        await state.set_state(ConverterStates.active)
        text = _panel_text(None, None)
        kb   = _converter_panel_kb(False, False, False)

    if edit and isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        msg = event.message if isinstance(event, CallbackQuery) else event
        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


# ── /convert and /converter commands ─────────────────────────
@router.message(Command("convert"))
@router.message(Command("converter"))
async def cmd_converter(message: Message, state: FSMContext):
    await state.clear()
    await _open_converter(message, state, edit=False)


# ── Open converter button ─────────────────────────────────────
@router.callback_query(F.data == "open_converter")
async def cb_open_converter(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "open_converter"):
        await callback.answer()
        return
    await state.clear()
    await _open_converter(callback, state, edit=True)
    await callback.answer()


# ── Back to converter panel ───────────────────────────────────
@router.callback_query(F.data == "conv_panel")
async def cb_conv_panel(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_panel"):
        await callback.answer()
        return
    await state.set_state(ConverterStates.active)
    data    = await state.get_data()
    from_tz = data.get("from_tz")
    to_tz   = data.get("to_tz")
    signal  = data.get("signal_text")
    await callback.message.edit_text(
        _panel_text(from_tz, to_tz),
        parse_mode="Markdown",
        reply_markup=_converter_panel_kb(bool(from_tz), bool(to_tz), bool(signal))
    )
    await callback.answer()


# ── Change settings ───────────────────────────────────────────
@router.callback_query(F.data == "conv_change")
async def cb_conv_change(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_change"):
        await callback.answer()
        return
    await state.update_data(from_tz=None, from_min=None, to_tz=None, to_min=None)
    await state.set_state(ConverterStates.active)
    await callback.message.edit_text(
        _panel_text(None, None),
        parse_mode="Markdown",
        reply_markup=_converter_panel_kb(False, False, False)
    )
    await callback.answer()


# ── FROM timezone ─────────────────────────────────────────────
@router.callback_query(F.data == "conv_from")
async def cb_conv_from(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_from"):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🌍 *Select FROM Timezone:*",
        parse_mode="Markdown",
        reply_markup=_tz_list_kb("from")
    )
    await callback.answer()


# ── TO timezone ───────────────────────────────────────────────
@router.callback_query(F.data == "conv_to")
async def cb_conv_to(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_to"):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🌐 *Select TO Timezone:*",
        parse_mode="Markdown",
        reply_markup=_tz_list_kb("to")
    )
    await callback.answer()


# ── Timezone selected ─────────────────────────────────────────
@router.callback_query(F.data.startswith("tz_"))
async def cb_tz_selected(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "tz_sel"):
        await callback.answer()
        return

    parts    = callback.data.split("_", 2)
    which    = parts[1]
    tz_label = _decode_tz(parts[2])
    tz_mins  = _tz_minutes(tz_label)

    if tz_mins is None:
        await callback.answer("Unknown timezone!", show_alert=True)
        return

    data = await state.get_data()
    if which == "from":
        await state.update_data(from_tz=tz_label, from_min=tz_mins)
        data["from_tz"] = tz_label; data["from_min"] = tz_mins
    else:
        await state.update_data(to_tz=tz_label, to_min=tz_mins)
        data["to_tz"] = tz_label; data["to_min"] = tz_mins

    from_tz = data.get("from_tz")
    to_tz   = data.get("to_tz")
    signal  = data.get("signal_text")

    await callback.message.edit_text(
        _panel_text(from_tz, to_tz),
        parse_mode="Markdown",
        reply_markup=_converter_panel_kb(bool(from_tz), bool(to_tz), bool(signal))
    )
    await callback.answer(f"✅ {which.upper()} → {tz_label}")


# ── Receive signal text (timezone mode) ───────────────────────
@router.message(ConverterStates.active, F.text)
async def receive_signal(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text or text.startswith("/"):
        return

    await state.update_data(signal_text=text)
    data    = await state.get_data()
    from_tz = data.get("from_tz")
    to_tz   = data.get("to_tz")

    if from_tz and to_tz:
        reply = (
            "✅ *Signal list received!*\n\n"
            f"🌍 FROM: *{from_tz}*  →  🌐 TO: *{to_tz}*\n\n"
            "Press ✅ CONFIRM to convert:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ CONFIRM",           callback_data="conv_confirm")],
            [InlineKeyboardButton(text="🔀 SWIPE ENTRY",       callback_data="conv_swipe_entry")],
            [InlineKeyboardButton(text="✏️ CHANGE SETTINGS",  callback_data="conv_change")],
            [InlineKeyboardButton(text="⬅️ Back",             callback_data="back_main")],
        ])
    else:
        reply = (
            "✅ *Signal list received!*\n\n"
            "Now select your FROM and TO timezones:"
        )
        kb = _converter_panel_kb(bool(from_tz), bool(to_tz), True)

    await message.answer(reply, parse_mode="Markdown", reply_markup=kb)


# ── CONFIRM: timezone conversion ──────────────────────────────
@router.callback_query(F.data == "conv_confirm")
async def cb_conv_confirm(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_confirm"):
        await callback.answer()
        return

    data        = await state.get_data()
    signal_text = data.get("signal_text")
    from_tz     = data.get("from_tz")
    from_min    = data.get("from_min")
    to_tz       = data.get("to_tz")
    to_min      = data.get("to_min")

    if not signal_text:
        await callback.answer("❌ Please paste your signal list first!", show_alert=True)
        return
    if not from_tz or not to_tz:
        await callback.answer("❌ Please select both FROM and TO timezones!", show_alert=True)
        return

    converted = convert_signals(signal_text, from_min, to_min)
    await state.update_data(converted_text=converted)

    header = f"✅ *Converted Signal List*\n🌍 FROM: *{from_tz}*  →  🌐 TO: *{to_tz}*"
    await callback.message.edit_text(
        _result_text(header, converted),
        parse_mode="Markdown",
        reply_markup=_result_kb()
    )
    await callback.answer("✅ Converted!")


# ════════════════════════════════════════════════════════════
#  SWIPE ENTRY FLOW
# ════════════════════════════════════════════════════════════

@router.callback_query(F.data == "conv_swipe_entry")
async def cb_conv_swipe_entry(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_swipe_entry"):
        await callback.answer()
        return
    await state.set_state(ConverterStates.waiting_swipe_signal)
    await callback.message.edit_text(
        "🔀 *Swipe Entry Mode*\n\n"
        "📋 Paste your signal list below 👇\n\n"
        "_(CALL ↔ PUT  |  UP ↔ DOWN will be swapped)_",
        parse_mode="Markdown",
        reply_markup=_swipe_paste_kb()
    )
    await callback.answer()


@router.message(ConverterStates.waiting_swipe_signal, F.text)
async def receive_swipe_signal(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text or text.startswith("/"):
        return
    await state.update_data(swipe_signal_text=text)
    preview = text[:300] + ("..." if len(text) > 300 else "")
    await message.answer(
        f"✅ *Signal list received!*\n\n"
        f"```\n{preview}\n```\n\n"
        f"Press ✅ CONFIRM SWIPE to swap directions:",
        parse_mode="Markdown",
        reply_markup=_swipe_confirm_kb()
    )


@router.callback_query(F.data == "conv_confirm_swipe")
async def cb_conv_confirm_swipe(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_confirm_swipe"):
        await callback.answer()
        return

    data  = await state.get_data()
    raw   = data.get("swipe_signal_text", "")
    if not raw:
        await callback.answer("❌ No signal list found. Please paste again.", show_alert=True)
        return

    swiped = swipe_signals(raw)
    await state.update_data(converted_text=swiped)
    await state.set_state(ConverterStates.active)

    header = "🔀 *Swipe Entry Result*\n_(CALL↔PUT  |  UP↔DOWN swapped)_"
    await callback.message.edit_text(
        _result_text(header, swiped),
        parse_mode="Markdown",
        reply_markup=_result_kb()
    )
    await callback.answer("🔀 Swiped!")


# ── SWIPE button in results (swap directions in current result) ─
@router.callback_query(F.data == "conv_swipe_result")
async def cb_conv_swipe_result(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_swipe_result"):
        await callback.answer()
        return

    data      = await state.get_data()
    converted = data.get("converted_text", "")
    if not converted:
        await callback.answer("❌ No result to swipe.", show_alert=True)
        return

    swiped = swipe_signals(converted)
    await state.update_data(converted_text=swiped)

    from_tz = data.get("from_tz")
    to_tz   = data.get("to_tz")
    if from_tz and to_tz:
        header = f"🔀 *Swiped Result*\n🌍 FROM: *{from_tz}*  →  🌐 TO: *{to_tz}*"
    else:
        header = "🔀 *Swipe Entry Result* _(directions swapped again)_"

    await callback.message.edit_text(
        _result_text(header, swiped),
        parse_mode="Markdown",
        reply_markup=_result_kb()
    )
    await callback.answer("🔀 Directions swiped!")


# ── COPY button (wipe old messages, then show copy text + home) ─
@router.callback_query(F.data == "conv_copy")
async def cb_conv_copy(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_copy"):
        await callback.answer()
        return

    from user_msg_tracker import wipe_chat
    import database as db
    from handlers.user import start_text, _start_keyboard, _is_admin

    data      = await state.get_data()
    converted = data.get("converted_text", "")
    user      = callback.from_user
    chat_id   = callback.message.chat.id
    anchor    = callback.message.message_id
    sub       = db.get_active_subscription(user.id)

    await state.clear()
    await callback.answer()

    # 1. WIPE all old messages first (so the chat is clean)
    await wipe_chat(callback.bot, chat_id, anchor)

    # 2. Send copyable text (appears AFTER wipe — user can now tap to copy)
    await callback.bot.send_message(
        chat_id,
        f"📋 *Tap the text below to copy:*\n\n`{converted}`",
        parse_mode="Markdown",
    )

    # 3. Send fresh home screen below
    await callback.bot.send_message(
        chat_id,
        start_text(user.first_name, sub, user.username, is_admin=_is_admin(user.id)),
        parse_mode="Markdown",
        reply_markup=_start_keyboard(sub, user.id),
    )


# ── SAVE SETTING ──────────────────────────────────────────────
@router.callback_query(F.data == "conv_save")
async def cb_conv_save(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_save"):
        await callback.answer()
        return

    data     = await state.get_data()
    from_tz  = data.get("from_tz")
    from_min = data.get("from_min")
    to_tz    = data.get("to_tz")
    to_min   = data.get("to_min")
    fmt      = data.get("fmt")

    if not from_tz or not to_tz:
        await callback.answer("❌ Timezone settings not available to save!", show_alert=True)
        return

    save_user_settings(callback.from_user.id, from_tz, from_min, to_tz, to_min, fmt)

    await callback.message.edit_text(
        "✅ *Settings Saved!*\n\n"
        f"🌍 FROM: *{from_tz}*\n"
        f"🌐 TO:   *{to_tz}*\n\n"
        "Next time you open CONVERTER your settings will load automatically.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ CHANGE SETTINGS", callback_data="conv_change")],
            [InlineKeyboardButton(text="⬅️ Back to Home",    callback_data="back_main")],
        ])
    )
    await callback.answer("✅ Settings saved!")


# ── FORMAT button ─────────────────────────────────────────────
@router.callback_query(F.data == "conv_format")
async def cb_conv_format(callback: CallbackQuery, state: FSMContext):
    if not _check_cooldown(callback.from_user.id, "conv_format"):
        await callback.answer()
        return
    await state.set_state(ConverterStates.waiting_format)
    await callback.message.answer(
        "🧾 *Format Template*\n\n"
        "Send me your preferred format template.\n"
        "Example: `TF;PAIR;HH:MM;CALL/PUT`\n\n"
        "Your converted list will be reformatted using that template.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="conv_cancel_format")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "conv_cancel_format")
async def cb_cancel_format(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ConverterStates.active)
    data      = await state.get_data()
    converted = data.get("converted_text", "")
    from_tz   = data.get("from_tz", "")
    to_tz     = data.get("to_tz", "")
    if from_tz and to_tz:
        header = f"✅ *Converted Signal List*\n🌍 FROM: *{from_tz}*  →  🌐 TO: *{to_tz}*"
    else:
        header = "🔀 *Swipe Entry Result*"
    await callback.message.edit_text(
        _result_text(header, converted),
        parse_mode="Markdown",
        reply_markup=_result_kb()
    )
    await callback.answer()


@router.message(ConverterStates.waiting_format, F.text)
async def receive_format_template(message: Message, state: FSMContext):
    template = message.text.strip()
    await state.set_state(ConverterStates.active)

    data      = await state.get_data()
    converted = data.get("converted_text", "")
    from_tz   = data.get("from_tz", "")
    to_tz     = data.get("to_tz", "")

    reformatted = _apply_format(converted, template)
    await state.update_data(converted_text=reformatted, fmt=template)

    user_settings = get_user_settings(message.from_user.id)
    if user_settings:
        save_user_settings(
            message.from_user.id,
            user_settings["from_tz"], user_settings["from_min"],
            user_settings["to_tz"],   user_settings["to_min"],
            template
        )

    if from_tz and to_tz:
        header = f"🧾 *Reformatted*  |  Format: `{template}`\n🌍 FROM: *{from_tz}*  →  🌐 TO: *{to_tz}*"
    else:
        header = f"🧾 *Reformatted*  |  Format: `{template}`"

    body = f"{header}\n\n```\n{reformatted}\n```"
    if len(body) > 4000:
        body = body[:3990] + "\n...(truncated)```"

    await message.answer(body, parse_mode="Markdown", reply_markup=_result_kb())
