from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

import mm_database as mmdb
from config import SUPPORT_USERNAME
from keyboards import mm_buy_access_kb

router = Router()

D  = "━━━━━━━━━━━━━━━━━━━━━━"
DS = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"


def _mm_menu_kb_full(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️  BINARY START SESSION",    callback_data="mm_start_session")],
        [InlineKeyboardButton(text="📊  FOREX PIPS CALCULATOR",   callback_data="open_forex_calc")],
        [InlineKeyboardButton(text="🛒  Buy Access",              callback_data="mm_buy_access")],
        [InlineKeyboardButton(text="💬  Support",                 url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="🌐  Language",               callback_data="mm_set_language")],
        [InlineKeyboardButton(text="◀️  Back",                   callback_data="back_main")],
    ])


def _mm_menu_kb_expired() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒  Buy Access", callback_data="mm_buy_access")],
        [InlineKeyboardButton(text="🏠  Home",       callback_data="back_main")],
    ])


def _build_mm_menu_text(user_id: int) -> tuple:
    access = mmdb.get_mm_access(user_id)
    user   = mmdb.get_mm_user(user_id)

    if access == "lifetime":
        text = (
            f"💰 *MONEY MANAGEMENT*\n"
            f"`{D}`\n"
            f"🏆  *Status:*    `PREMIUM ♾️ LIFETIME`\n"
            f"⏳  *Expires:*   `Never — Lifetime`\n"
            f"`{D}`\n"
            f"✅  _Full access to all features_"
        )
        return text, _mm_menu_kb_full(user_id)

    if access == "premium":
        expires = "—"
        if user and user.get("mm_expires_at"):
            try:
                expires = datetime.fromisoformat(user["mm_expires_at"]).strftime("%d %b %Y")
            except Exception:
                expires = str(user["mm_expires_at"])[:10]
        text = (
            f"💰 *MONEY MANAGEMENT*\n"
            f"`{D}`\n"
            f"✅  *Status:*    `PREMIUM ACTIVE`\n"
            f"📅  *Expires:*   `{expires}`\n"
            f"`{D}`\n"
            f"🚀  _Unlimited sessions — No capital limit_"
        )
        return text, _mm_menu_kb_full(user_id)

    # Free user — check daily limit
    today_used = 0
    if user:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if user.get("daily_date") == today:
            today_used = user.get("daily_sessions", 0)

    if today_used >= 1:
        text = (
            f"💰 *MONEY MANAGEMENT*\n"
            f"`{D}`\n"
            f"🔓  *Status:*   `FREE`\n\n"
            f"⚠️  *Today's free session has been used.*\n\n"
            f"`{DS}`\n"
            f"🔄  _New free session resets tomorrow_\n"
            f"⬆️  _Upgrade for unlimited sessions_\n"
            f"`{D}`"
        )
        return text, _mm_menu_kb_expired()

    text = (
        f"💰 *MONEY MANAGEMENT*\n"
        f"`{D}`\n"
        f"🔓  *Status:*   `FREE`\n"
        f"📊  *Today:*    `{today_used} of 1` session used\n"
        f"`{D}`\n\n"
        f"🆓 *FREE PLAN INCLUDES:*\n"
        f"  ▸ `1 session per day`\n"
        f"  ▸ `Maximum capital $50`\n"
        f"  ▸ `All 10 trading modes`\n"
        f"  ▸ `Basic dashboard`\n"
        f"  ▸ `FOREX PIPS CALCULATOR`\n\n"
        f"`{DS}`\n\n"
        f"👑 *PREMIUM PLAN INCLUDES:*\n"
        f"  ▸ `Unlimited sessions daily`\n"
        f"  ▸ `No capital limit`\n"
        f"  ▸ `Priority AI tracking`\n"
        f"  ▸ `Full dashboard stats`\n"
        f"  ▸ `New Session anytime`\n"
        f"  ▸ `Multi-session support`\n"
        f"  ▸ `FOREX PIPS CALCULATOR`\n\n"
        f"`{D}`"
    )
    return text, _mm_menu_kb_full(user_id)


@router.callback_query(F.data == "open_mm_menu")
async def open_mm_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    mmdb.upsert_mm_user(user_id, callback.from_user.username or "")

    text, kb = _build_mm_menu_text(user_id)

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data == "mm_buy_access")
async def mm_buy_access(callback: CallbackQuery):
    text = (
        f"💰 *MM ACCESS — PLANS & PRICING*\n"
        f"`{D}`\n\n"
        f"  📦  `13 Days`    ➜  *$6*\n"
        f"  📦  `25 Days`    ➜  *$10*\n"
        f"  📦  `1 Month`    ➜  *$15*\n"
        f"  📦  `2 Months`   ➜  *$25*\n"
        f"  📦  `4 Months`   ➜  *$60*\n"
        f"  ♾️  `Lifetime`   ➜  *$100*\n\n"
        f"`{D}`\n"
        f"🎁  *SVIP / AI Bot Users = FREE ACCESS*\n"
        f"👉  _DM Admin to claim your free access._\n"
        f"`{DS}`\n"
        f"⬇️  _Select a plan below to continue_"
    )

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=mm_buy_access_kb())
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=mm_buy_access_kb())
    await callback.answer()
