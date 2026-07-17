from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from datetime import datetime

import database as db
from config import (
    PACKAGES, SUPPORT_USERNAME, FOREX_VIP_PACKAGES, PACKAGE_TIP_HTML,
    PAID_OFFER_TIER3, PAID_OFFER_TIER6,
    FOREX_OFFER_TIER3, FOREX_OFFER_TIER6,
)
from keyboards import (
    join_options_kb, paid_menu_kb, refer_join_kb,
    packages_kb, proceed_payment_kb, forex_join_kb, forex_proceed_payment_kb,
    member_start_kb,
    my_offer_chooser_kb, paid_offer_packages_kb, forex_offer_packages_kb,
)


def _paid_unlocked_tier(user_id: int) -> int:
    n = db.count_approved_payments(user_id, "paid")
    if n >= 6: return 6
    if n >= 3: return 3
    return 0


def _forex_unlocked_tier(user_id: int) -> int:
    n = db.count_approved_payments(user_id, "forex")
    if n >= 6: return 6
    if n >= 3: return 3
    return 0


def _has_offer(user_id: int) -> bool:
    try:
        if user_id == db.get_admin_id():
            return False
    except Exception:
        pass
    return _paid_unlocked_tier(user_id) >= 3 or _forex_unlocked_tier(user_id) >= 3
from user_msg_tracker import wipe_chat as _do_wipe_chat

router = Router()


async def _wipe_chat(callback: CallbackQuery) -> None:
    """Delete all recent messages in this chat (range-based, survives restarts)."""
    await _do_wipe_chat(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
    )

def get_pkg(pkg_id: int):
    return next((p for p in PACKAGES if p["id"] == pkg_id), None)

# ── Start screen text ──────────────────────────────────────
def start_text(first_name: str, sub: dict | None, username: str | None = None, is_admin: bool = False) -> str:
    if is_admin:
        return (
            "☪️ *Assalamu Walaikum BOSS* 👋\n"
            "*Welcome CEO — the TOP G*\n"
            "━━━━━━━━━━━━━\n"
            "💎 *PAID JOIN* — MTG / NON-MTG\n"
            "💹 *FOREX VIP* — GOLDZILA SVIP\n"
            "🔗 *REFER JOIN* — via referral\n"
            "⏳ *CONVERTER* — Timezone tool\n"
            "📟 *MONEY MGMT* — Trade planner\n"
            "━━━━━━━━━━━━━━\n"
            "👇 Choose an option below:"
        )

    display = f"@{username}" if username else f"*{first_name}*"

    if sub:
        end = datetime.fromisoformat(sub["end_date"])
        days_left = max(0, (end - datetime.now()).days)
        status = (
            f"✅ *{sub['package_name']}*\n"
            f"📅 {end.strftime('%d %b %Y')} · ⏳ *{days_left}d left*"
        )
    else:
        status = "❌ *No active subscription*"

    return (
        f"☪️ *Assalamu Walaikum* {display} 👋\n\n"
        f"{status}\n"
        f"━━━━━━━━━━━━━\n"
        f"💎 *PAID JOIN* — MTG / NON-MTG\n"
        f"💹 *FOREX VIP* — GOLDZILA SVIP\n"
        f"🔗 *REFER JOIN* — via referral\n"
        f"⏳ *CONVERTER* — Timezone tool\n"
        f"📟 *MONEY MGMT* — Trade planner\n"
        f"━━━━━━━━━━━━━━\n"
        f"👇 Choose an option below:"
    )

# ── Package list text (HTML) ───────────────────────────────
def build_packages_text() -> str:
    svip_pkgs  = [p for p in PACKAGES if "SVIP" in p["name"]]
    other_pkgs = [p for p in PACKAGES if "SVIP" not in p["name"]]

    lines = ["💎 <b>Subscription Plans</b>\n"]

    if svip_pkgs:
        lines.append("🏆 <b>MTG Future Signal — SVIP</b>")
        lines.append("━━━━━━━━━━━━━━")
        for p in svip_pkgs:
            duration = p["name"].split("·")[-1].strip()
            original = p["price"] * 4
            lines.append(f"  {duration:<12}  <s>${original}</s> ➜  <b>${p['price']}</b>")
        lines.append("")

    if other_pkgs:
        lines.append("📈 <b>NON-MTG Future Signal</b>")
        lines.append("━━━━━━━━━━━━━━")
        for p in other_pkgs:
            duration = p["name"].split("·")[-1].strip()
            original = p["price"] * 4
            lines.append(f"  {duration:<12}  <s>${original}</s> ➜  <b>${p['price']}</b>")
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━\n",
        "🌐 <b>VIP FUTURE Signal Info</b>",
        "🕐 <b>Timezone:</b> UTC +6:00",
        "📅 <b>Daily Signal Post:</b> 12 PM – 1 PM\n",
        "💡 <b>Different timezone?</b>",
        "Pay an extra <b>$20</b> for <b>custom signals</b> — I'll create a signal list "
        "according to your timezone and send it to your chat every day.",
        "<i>(Please inform admin first, then pay the $20 extra)</i>\n",
        "👇 <b>Tap a plan below to subscribe:</b>",
    ]
    return "\n".join(lines)

# ── FOREX VIP packages text (HTML) ────────────────────────
def build_forex_text() -> str:
    lines = [
        "💹 <b>FOREX VIP JOIN</b>\n",
        "🚀 <b>BOOST YOUR CAPITAL 100x</b>",
        "with our tools and Signals\n",
        "🤑 <b>GOLDZILA SVIP PAID JOIN</b>",
        "<i>(IB change — MOST IF YOUR EXNESS USER)</i>\n",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for p in FOREX_VIP_PACKAGES:
        original = p["price"] * 4
        lines.append(f"  {p['label']:<22}  <s>${original}</s>  ➜  <b>${p['price']}</b>")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        "💳 <b>Payment methods accepted:</b>",
        "₿ Bitcoin  |  🔷 USDT TRC20  |  💛 Binance Pay\n",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "♻️ <b>Lifetime Access available with partner link.</b>\n"
        "To get this please contact 👉 Support",
        "\n👇 Select a plan below to pay:",
    ]
    return "\n".join(lines)

def _is_admin(user_id: int) -> bool:
    try:
        return user_id == db.get_admin_id()
    except Exception:
        return False

def _start_keyboard(sub, user_id: int = 0):
    has_offer = _has_offer(user_id)
    if sub and "FOREX" in sub.get("package_name", ""):
        return member_start_kb(is_forex_sub=True, is_admin=_is_admin(user_id), has_offer=has_offer)
    elif sub:
        return member_start_kb(is_forex_sub=False, is_admin=_is_admin(user_id), has_offer=has_offer)
    return join_options_kb(is_admin=_is_admin(user_id), has_offer=has_offer)

# ── /start ─────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    db.upsert_user(user.id, user.username, user.full_name)
    sub = db.get_active_subscription(user.id)
    await message.answer(
        start_text(user.first_name, sub, user.username, is_admin=_is_admin(user.id)),
        parse_mode="Markdown",
        reply_markup=_start_keyboard(sub, user.id)
    )

# ── Back to start (wipes all tracked messages, sends fresh home) ─
@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user    = callback.from_user
    sub     = db.get_active_subscription(user.id)
    chat_id = callback.message.chat.id
    # Delete all tracked bot messages + the current one
    await _wipe_chat(callback)
    # Send a clean fresh home message
    await callback.bot.send_message(
        chat_id,
        start_text(user.first_name, sub, user.username, is_admin=_is_admin(user.id)),
        parse_mode="Markdown",
        reply_markup=_start_keyboard(sub, user.id)
    )
    await callback.answer()

# ── 📋 MANU button (member dashboard) ──────────────────────
@router.callback_query(F.data == "start_refresh")
async def start_refresh(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = callback.from_user
    sub  = db.get_active_subscription(user.id)
    await _wipe_chat(callback)
    await callback.bot.send_message(
        callback.message.chat.id,
        start_text(user.first_name, sub, user.username, is_admin=_is_admin(user.id)),
        parse_mode="Markdown",
        reply_markup=join_options_kb(is_admin=_is_admin(user.id), has_offer=_has_offer(user.id)),
    )
    await callback.answer()

# ── Broker: EXNESS ─────────────────────────────────────────
@router.callback_query(F.data == "broker_exness")
async def broker_exness(callback: CallbackQuery, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
    caption = (
        "🚀 <b>Time to level up!</b> With our <b>Advance AI Bot strategy</b>, "
        "we are catching <b>MASSIVE moves</b> on Gold (XAUUSD).\n\n"
        "🔹 <b>Small Risk</b>  💰  <b>Big Reward</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 <b>Join the Broker I use — EXNESS</b>\n"
        "<b>CREATE NEW ACCOUNT CLICK HERE 👈</b>\n\n"
        "It offers <b>1:Unlimited Leverage</b> + <b>Tightest Spreads</b> and much more ..\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "• If you're serious about profit or want to pass your funded account,\n"
        "it's time to join <b>GOLDZILA SVIP</b> or buy our <b>AI NOW!</b>\n\n"
        "🤖 USE AI assistant <b>@Managementtg_Bot</b>\n"
        "👑 Join our <b>VIP Autocratic</b>"
    )
    photo = FSInputFile("attached_assets/ChatGPT_Image_Jun_9,_2026,_07_16_31_PM_1781023203348.png")
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 CREATE NEW ACCOUNT — EXNESS 👈", url="https://one.exnessonelink.com/a/9w89qlwcf2")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")],
        ])
    )
    await callback.answer()

# ── Broker: POCKET OPTION ───────────────────────────────────
@router.callback_query(F.data == "broker_pocket")
async def broker_pocket(callback: CallbackQuery, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
    caption = (
        "🔥 <b>WELCOME50</b> – <b>Get a 50% Bonus on Your First Deposit!</b> 🔥\n\n"
        "No time to analyze the markets all day? Join our <b>SVIP trading community</b> "
        "or buy <b>TRADING AI</b> and trade with confidence.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>50% Deposit Bonus Link Available</b>\n"
        "💵 <b>Minimum Deposit:</b> $10\n"
        "🏷️ <b>Promo Code:</b> <code>WELCOME50</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ <b>Create Your Pocket Option Account 👇</b>\n\n"
        "🌍 <b>Global Registration Link</b> also available below\n\n"
        "🚀 <b>Don't miss this opportunity to boost your trading capital and start your journey today!</b>"
    )
    photo = FSInputFile("attached_assets/ChatGPT_Image_Jun_9,_2026,_06_53_59_PM_1781023499405.png")
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ CREATE ACCOUNT + 50% BONUS 👈", url="https://goo.su/a7Kioo")],
            [InlineKeyboardButton(text="🌍 Global Registration Link", url="https://po-ru4.click/smart/r44rfMYgy7uvhR")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")],
        ])
    )
    await callback.answer()

# ── 🔄 Renew → PAID JOIN ───────────────────────────────────
@router.callback_query(F.data == "renew_paid")
async def renew_paid(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _wipe_chat(callback)
    await callback.bot.send_message(
        callback.message.chat.id,
        "💎 *PAID JOIN*\n\nChoose what you'd like to do below:",
        parse_mode="Markdown",
        reply_markup=paid_menu_kb(),
    )
    await callback.answer()

# ── 🔄 Renew → FOREX VIP JOIN ──────────────────────────────
@router.callback_query(F.data == "renew_forex")
async def renew_forex(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _wipe_chat(callback)
    await callback.bot.send_message(
        callback.message.chat.id,
        build_forex_text(),
        parse_mode="HTML",
        reply_markup=forex_join_kb(),
    )
    await callback.answer()

# ── PAID JOIN ──────────────────────────────────────────────
@router.callback_query(F.data == "paid_join")
async def paid_join(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 *PAID JOIN*\n\n"
        "Choose what you'd like to do below:",
        parse_mode="Markdown",
        reply_markup=paid_menu_kb()
    )
    await callback.answer()

# ── Back to paid menu ──────────────────────────────────────
@router.callback_query(F.data == "back_paid")
async def back_paid(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "💎 *PAID JOIN*\n\n"
        "Choose what you'd like to do below:",
        parse_mode="Markdown",
        reply_markup=paid_menu_kb()
    )
    await callback.answer()

# ── FOREX VIP JOIN ─────────────────────────────────────────
@router.callback_query(F.data == "forex_join")
async def forex_join(callback: CallbackQuery):
    await callback.message.edit_text(
        build_forex_text(),
        parse_mode="HTML",
        reply_markup=forex_join_kb()
    )
    await callback.answer()

# ── 🎁 MY OFFER ───────────────────────────────────────────
def _paid_offer_text(tier: int) -> str:
    pkgs = PAID_OFFER_TIER6 if tier >= 6 else PAID_OFFER_TIER3
    badge = "🏆 <b>LIFETIME LOYALTY OFFER</b>" if tier >= 6 else "🎁 <b>LOYALTY OFFER</b>"
    lines = [
        badge,
        "💎 <b>PAID VIP — Your Personal Pricing</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for p in pkgs:
        duration = p["name"].split("·")[-1].strip()
        lines.append(f"  {duration:<14}  <b>${p['price']}</b>")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "👇 Tap a plan to subscribe:",
    ]
    return "\n".join(lines)


def _forex_offer_text(tier: int) -> str:
    pkgs = FOREX_OFFER_TIER6 if tier >= 6 else FOREX_OFFER_TIER3
    badge = "🏆 <b>LIFETIME LOYALTY OFFER</b>" if tier >= 6 else "🎁 <b>LOYALTY OFFER</b>"
    lines = [
        badge,
        "💹 <b>FOREX VIP — Your Personal Pricing</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for p in pkgs:
        lines.append(f"  {p['label']:<14}  <b>${p['price']}</b>")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "👇 Tap a plan to subscribe:",
    ]
    return "\n".join(lines)


@router.callback_query(F.data == "my_offer")
async def my_offer_entry(callback: CallbackQuery):
    uid = callback.from_user.id
    paid_tier  = _paid_unlocked_tier(uid)
    forex_tier = _forex_unlocked_tier(uid)

    if paid_tier == 0 and forex_tier == 0:
        await callback.answer("You haven't unlocked My Offer yet.", show_alert=True)
        return

    # Only one category unlocked → jump straight in
    if paid_tier > 0 and forex_tier == 0:
        await callback.message.edit_text(
            _paid_offer_text(paid_tier),
            parse_mode="HTML",
            reply_markup=paid_offer_packages_kb(paid_tier)
        )
        await callback.answer()
        return
    if forex_tier > 0 and paid_tier == 0:
        await callback.message.edit_text(
            _forex_offer_text(forex_tier),
            parse_mode="HTML",
            reply_markup=forex_offer_packages_kb(forex_tier)
        )
        await callback.answer()
        return

    # Both unlocked → choose category
    await callback.message.edit_text(
        "🎁 <b>My Offer</b>\n\nYou've unlocked loyalty pricing in both categories.\n"
        "Choose which one you'd like to view:",
        parse_mode="HTML",
        reply_markup=my_offer_chooser_kb(paid_tier > 0, forex_tier > 0)
    )
    await callback.answer()


@router.callback_query(F.data == "my_offer_paid")
async def my_offer_paid(callback: CallbackQuery):
    tier = _paid_unlocked_tier(callback.from_user.id)
    if tier == 0:
        await callback.answer("Not unlocked yet.", show_alert=True)
        return
    await callback.message.edit_text(
        _paid_offer_text(tier),
        parse_mode="HTML",
        reply_markup=paid_offer_packages_kb(tier)
    )
    await callback.answer()


@router.callback_query(F.data == "my_offer_forex")
async def my_offer_forex(callback: CallbackQuery):
    tier = _forex_unlocked_tier(callback.from_user.id)
    if tier == 0:
        await callback.answer("Not unlocked yet.", show_alert=True)
        return
    await callback.message.edit_text(
        _forex_offer_text(tier),
        parse_mode="HTML",
        reply_markup=forex_offer_packages_kb(tier)
    )
    await callback.answer()


# ── 🎁 MONTHLY JOIN OFFERS ────────────────────────────────
@router.callback_query(F.data == "monthly_offers")
async def monthly_offers(callback: CallbackQuery):
    text = (
        "<b>Exclusive Lifetime discount Benefits for ACTIVE Members!</b>\n\n"
        "<b>Join our VIP program three times or more using our bot, and unlock "
        "incredible discounts on your monthly membership package for life!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b><u>FOR BINARY TRADERS</u></b> 🎯\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>• Join VIP 3 Times: Unlock VIP at just $45 per month</b>\n\n"
        "<b>(originally $52/month).</b>\n\n"
        "<b>• Join VIP 6 Times: Unlock VIP at just $30 per month. lifetime</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💹 <b><u>FOR FOREX TRADERS</u></b> 💹\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>• Join VIP 3 Times: Unlock VIP at just $90 per month Lifetime</b>\n\n"
        "<b>(originally $199/1month).</b>\n\n"
        "<b>• Join VIP 6 Times: Unlock VIP at just $68 per month. ( Lifetime)</b>\n\n"
        "<b>Take advantage of this amazing offer and secure your lifetime Discount today!</b>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Contact Admin", url="https://t.me/OAWHIDSHAKIB")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

# ── REFER JOIN ─────────────────────────────────────────────
@router.callback_query(F.data == "refer_join")
async def refer_join(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔗 *REFER JOIN*\n\n"
        "To join via referral, contact our admin directly:\n\n"
        "👤 *@OAWHIDSHAKIB*\n\n"
        "Send a DM and mention you want to join via referral.",
        parse_mode="Markdown",
        reply_markup=refer_join_kb()
    )
    await callback.answer()

# ── Show packages ──────────────────────────────────────────
@router.callback_query(F.data == "show_packages")
@router.callback_query(F.data == "renew")
async def show_packages(callback: CallbackQuery):
    await callback.message.edit_text(
        build_packages_text(),
        parse_mode="HTML",
        reply_markup=packages_kb()
    )
    await callback.answer()

# ── Package selected ───────────────────────────────────────
@router.callback_query(F.data.startswith("pkg_"))
async def package_selected(callback: CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split("_")[1])
    pkg    = get_pkg(pkg_id)
    if not pkg:
        await callback.answer("Package not found!", show_alert=True)
        return

    await state.update_data(selected_pkg_id=pkg_id)
    original = pkg["price"] * 4

    text = (
        f"✅ <b>You selected:</b>\n\n"
        f"📦 {pkg['name']}\n"
        f"💰 Amount: <s>${original}</s>  <b>${pkg['price']}</b>\n"
        f"⏱ Duration: <b>{pkg['description']}</b>\n\n"
        f"Click below to proceed to payment."
    )

    if pkg["days"] < 30:
        text += f"\n\n{PACKAGE_TIP_HTML}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=proceed_payment_kb(pkg_id)
    )
    await callback.answer()

# ── My subscription ────────────────────────────────────────
@router.callback_query(F.data == "my_sub")
async def my_subscription(callback: CallbackQuery):
    sub = db.get_active_subscription(callback.from_user.id)
    if sub:
        end       = datetime.fromisoformat(sub["end_date"])
        start     = datetime.fromisoformat(sub["start_date"])
        days_left = max(0, (end - datetime.now()).days)
        text = (
            f"📊 *Your Subscription*\n\n"
            f"📦 Package: *{sub['package_name']}*\n"
            f"📅 Started: {start.strftime('%d %b %Y')}\n"
            f"📅 Expires: *{end.strftime('%d %b %Y')}*\n"
            f"⏳ Remaining: *{days_left} days*\n\n"
            f"{'🟢 Status: Active' if days_left > 0 else '🔴 Status: Expiring today!'}"
        )
    else:
        text = (
            "❌ *No Active Subscription*\n\n"
            "You don't have an active subscription.\n"
            "Choose a package to get started! 👇"
        )

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=paid_menu_kb())
    await callback.answer()

# ── No-op (section header buttons) ─────────────────────────
@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()
