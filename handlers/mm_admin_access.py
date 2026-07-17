from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

import database as db
import mm_database as mmdb
from keyboards import admin_panel_kb, mm_access_list_kb, mm_remove_confirm_kb

router = Router()

DIVIDER = "━━━━━━━━━━━━━━"
PER_PAGE = 10


def is_admin(user_id: int) -> bool:
    return user_id == db.get_admin_id()


def get_admin_id() -> int:
    return db.get_admin_id()


class MMGrantStates(StatesGroup):
    waiting_username = State()
    waiting_duration = State()


# ── MM Access Grant ───────────────────────────────────────────
@router.callback_query(F.data == "admin_mm_grant")
async def mm_grant_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(MMGrantStates.waiting_username)
    text = (
        "*MM Access Grant*\n"
        f"`{DIVIDER}`\n\n"
        "Type the username:\n"
        "_(Example: @username)_"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 View MM Access List", callback_data="admin_mm_list")],
        [InlineKeyboardButton(text="◀️ Back to Admin",       callback_data="admin_panel")],
    ])
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.message(MMGrantStates.waiting_username)
async def mm_grant_username(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    username = message.text.strip() if message.text else ""
    if not username:
        await message.answer("Please enter a username.")
        return

    user = mmdb.get_user_by_username(username)
    if not user:
        await message.answer(
            f"User *{username}* not found in the database.\n"
            f"The user must start the bot first.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 View MM Access List", callback_data="admin_mm_list")],
                [InlineKeyboardButton(text="◀️ Back to Admin",       callback_data="admin_panel")],
            ])
        )
        await state.clear()
        return

    await state.update_data(target_user_id=user["user_id"], target_username=username)
    await state.set_state(MMGrantStates.waiting_duration)
    text = (
        "*Type the duration:*\n\n"
        "Examples:\n"
        "`1, 2, 3, 7, 14, 24`  = Days\n"
        "`1month, 2month, 3month` = Months\n"
        "`lifetime` = Permanent ♾️"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin_panel")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)


@router.message(MMGrantStates.waiting_duration)
async def mm_grant_duration(message: Message, state: FSMContext, bot):
    if not is_admin(message.from_user.id):
        return

    duration_str    = message.text.strip().lower() if message.text else ""
    data            = await state.get_data()
    target_user_id  = data.get("target_user_id")
    target_username = data.get("target_username", "Unknown")
    await state.clear()

    if not duration_str or not target_user_id:
        await message.answer("Invalid input. Grant cancelled.")
        return

    expiry_display = mmdb.grant_mm_access(target_user_id, duration_str)
    if expiry_display is None:
        await message.answer(
            "Invalid duration format.\nExamples: `7` (days), `1month`, `lifetime`",
            parse_mode="Markdown",
            reply_markup=admin_panel_kb()
        )
        return

    dur_lower = duration_str.lower()
    if dur_lower == "lifetime":
        duration_label = "Lifetime ♾️"
    elif dur_lower.endswith("month"):
        months = dur_lower.replace("month", "")
        duration_label = f"{months} Month(s)"
    else:
        duration_label = f"{duration_str} Day(s)"

    await message.answer(
        f"✅ MM Access granted to *{target_username}*\n"
        f"Duration: *{duration_label}*\n"
        f"Expires: `{expiry_display}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 View MM Access List", callback_data="admin_mm_list")],
            [InlineKeyboardButton(text="◀️ Back to Admin",       callback_data="admin_panel")],
        ])
    )

    try:
        user_msg = (
            "Your MONEY MANAGEMENT Access is now active!\n"
            f"Plan: {duration_label}\n"
            f"Expires: {expiry_display}\n"
            "Start your session anytime!"
        )
        await bot.send_message(target_user_id, user_msg)
    except Exception as e:
        await message.answer(f"Could not notify user: {e}")


# ── No-op (admin row in list — not removable) ────────────────
@router.callback_query(F.data == "mm_noop")
async def mm_noop(callback: CallbackQuery):
    await callback.answer("Admin access cannot be removed.", show_alert=False)


# ── MM Access List ────────────────────────────────────────────
@router.callback_query(F.data == "admin_mm_list")
async def mm_access_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await _show_mm_list(callback, page=1)
    await callback.answer()


@router.callback_query(F.data.startswith("mm_list_page_"))
async def mm_list_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    page = int(callback.data.split("_")[-1])
    await _show_mm_list(callback, page=page)
    await callback.answer()


async def _show_mm_list(callback: CallbackQuery, page: int):
    admin_id = get_admin_id()
    users, total = mmdb.get_all_mm_access_users(page=page, per_page=PER_PAGE)

    if not users and page == 1:
        text = f"*MM ACCESS LIST*\n`{DIVIDER}`\nNo active MM access users."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin_panel")]
        ])
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
        return

    lines = [f"*MM ACCESS LIST*\nTotal Active: *{total}*\n`{DIVIDER}`"]
    for i, u in enumerate(users, start=(page - 1) * PER_PAGE + 1):
        uname  = f"@{u['username']}" if u.get("username") else f"ID {u['user_id']}"
        uid    = u["user_id"]
        access = u.get("mm_access_type", "free")
        # Admin always shows Lifetime
        if uid == admin_id or access == "lifetime":
            expiry = "Lifetime ♾️"
        elif u.get("mm_expires_at"):
            try:
                expiry = datetime.fromisoformat(u["mm_expires_at"]).strftime("%d %b %Y")
            except Exception:
                expiry = str(u["mm_expires_at"])[:10]
        else:
            expiry = "—"
        lines.append(f"`{i}.` {uname}   _{expiry}_")

    text = "\n".join(lines)
    kb   = mm_access_list_kb(users, page, total, PER_PAGE, admin_id=admin_id)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)


# ── Remove Access ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("mm_remove_"))
async def mm_remove_prompt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    target_uid = int(callback.data.split("_")[-1])
    admin_id   = get_admin_id()

    # Block admin from removing themselves
    if target_uid == admin_id:
        await callback.answer("You cannot remove your own admin access.", show_alert=True)
        return

    user  = mmdb.get_mm_user(target_uid)
    uname = f"@{user['username']}" if user and user.get("username") else f"ID {target_uid}"

    text = f"Remove MM access for *{uname}*?"
    kb   = mm_remove_confirm_kb(target_uid)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mm_confirm_remove_"))
async def mm_confirm_remove(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        return
    target_uid = int(callback.data.split("_")[-1])
    admin_id   = get_admin_id()

    # Double-check: never remove admin
    if target_uid == admin_id:
        await callback.answer("Cannot remove admin access.", show_alert=True)
        return

    user  = mmdb.get_mm_user(target_uid)
    uname = f"@{user['username']}" if user and user.get("username") else f"ID {target_uid}"

    mmdb.remove_mm_access(target_uid)

    try:
        await callback.message.edit_text(
            f"✅ Access removed for *{uname}*.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Back to List", callback_data="admin_mm_list")],
                [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin_panel")],
            ])
        )
    except Exception:
        await callback.message.answer(f"✅ Access removed for {uname}.")

    await callback.answer("Access removed.")

    try:
        await bot.send_message(
            target_uid,
            "Your MONEY MANAGEMENT Access has been removed.\n"
            "Contact support if you think this is a mistake."
        )
    except Exception:
        pass
