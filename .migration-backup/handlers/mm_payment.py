import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
import mm_database as mmdb
from config import MM_PACKAGES, PAYMENT_INSTRUCTIONS, ADMIN_ID
from keyboards import mm_cancel_kb, mm_payment_instructions_kb

router = Router()

D  = "━━━━━━━━━━━━━━━━━━━━━━"
DS = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"


def get_mm_pkg(pkg_id: int):
    return next((p for p in MM_PACKAGES if p["id"] == pkg_id), None)


class MMPaymentStates(StatesGroup):
    waiting_screenshot = State()
    waiting_broker_name = State()


# ── PAY button tapped ────────────────────────────────────────
@router.callback_query(F.data.startswith("mm_pay_"))
async def mm_pay_selected(callback: CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split("_")[-1])
    pkg    = get_mm_pkg(pkg_id)
    if not pkg:
        await callback.answer("Package not found!", show_alert=True)
        return

    await state.update_data(mm_pkg_id=pkg_id)

    text = (
        f"💳 *MM ACCESS — PAYMENT*\n"
        f"`{D}`\n\n"
        f"📦  *Plan:*    `{pkg['label']}`\n"
        f"💰  *Amount:*  `${pkg['price']}`   ⬅️ *PAY THIS*\n\n"
        f"`{D}`\n"
        f"📋 *PAYMENT METHODS:*\n\n"
        f"{PAYMENT_INSTRUCTIONS}\n"
        f"`{D}`\n"
        f"⚠️  _Send exact amount shown above._\n"
        f"📸  _Screenshot required as proof._"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown",
                                         reply_markup=mm_payment_instructions_kb(pkg_id))
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown",
                                      reply_markup=mm_payment_instructions_kb(pkg_id))
    await callback.answer()


# ── CHECK MY SCREENSHOT ──────────────────────────────────────
@router.callback_query(F.data.startswith("mm_check_ss_"))
async def mm_check_screenshot(callback: CallbackQuery, state: FSMContext):
    data   = await state.get_data()
    pkg_id = data.get("mm_pkg_id") or int(callback.data.split("_")[-1])
    pkg    = get_mm_pkg(pkg_id) if pkg_id else None
    if not pkg:
        await callback.answer("Session expired. Please start again.", show_alert=True)
        return

    payment_id = db.create_payment(
        callback.from_user.id, pkg["id"], pkg["name"], pkg["price"]
    )
    await state.update_data(mm_payment_id=payment_id, mm_pkg_id=pkg_id)
    await state.set_state(MMPaymentStates.waiting_screenshot)

    text = (
        f"📸 *SEND PAYMENT SCREENSHOT*\n"
        f"`{D}`\n\n"
        f"✅  *Plan:*    `{pkg['label']}`\n"
        f"💵  *Amount:*  `${pkg['price']}`\n\n"
        f"`{DS}`\n"
        f"📌 *Instructions:*\n\n"
        f"  1️⃣  Complete your payment\n"
        f"  2️⃣  Take a *screenshot* of confirmation\n"
        f"  3️⃣  Send the screenshot *as a photo* below\n\n"
        f"`{D}`\n"
        f"⬇️  _Send your screenshot now_"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=mm_cancel_kb())
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=mm_cancel_kb())
    await callback.answer()


# ── Receive screenshot photo ─────────────────────────────────
@router.message(MMPaymentStates.waiting_screenshot, F.photo)
async def mm_receive_screenshot(message: Message, state: FSMContext):
    data       = await state.get_data()
    payment_id = data.get("mm_payment_id")

    if not payment_id:
        await message.answer(
            "⚠️ *Session expired.*\nPlease start again.",
            parse_mode="Markdown",
            reply_markup=mm_cancel_kb()
        )
        await state.clear()
        return

    file_id = message.photo[-1].file_id
    db.attach_screenshot(payment_id, file_id)
    await state.update_data(mm_file_id=file_id)
    await state.set_state(MMPaymentStates.waiting_broker_name)

    await message.answer(
        f"✅ *Screenshot Received!*\n"
        f"`{D}`\n\n"
        f"🏦 *One more step:*\n\n"
        f"Please type your *broker's name* and send it.\n\n"
        f"_Example: Quotex, IQ Option, Pocket Option_\n\n"
        f"`{D}`\n"
        f"⬇️  _Type broker name below_",
        parse_mode="Markdown",
        reply_markup=mm_cancel_kb()
    )


# ── Receive broker name ──────────────────────────────────────
@router.message(MMPaymentStates.waiting_broker_name, F.text)
async def mm_receive_broker_name(message: Message, state: FSMContext, bot):
    data        = await state.get_data()
    payment_id  = data.get("mm_payment_id")
    pkg_id      = data.get("mm_pkg_id")
    file_id     = data.get("mm_file_id")
    broker_name = message.text.strip()

    if not payment_id:
        await message.answer("⚠️ Session expired. Please start again.")
        await state.clear()
        return

    pkg  = get_mm_pkg(pkg_id)
    user = message.from_user
    db.attach_broker_name(payment_id, broker_name)
    await state.clear()

    pending = await message.answer(
        f"⏳ *Submitting your payment...*\n"
        f"`{DS}`\n"
        f"_Please wait a moment..._",
        parse_mode="Markdown"
    )
    await asyncio.sleep(2)
    await pending.edit_text(
        f"🕐 *PAYMENT UNDER REVIEW*\n"
        f"`{D}`\n\n"
        f"📦  *Plan:*    `{pkg['label'] if pkg else 'Unknown'}`\n"
        f"💰  *Amount:*  `${pkg['price'] if pkg else '?'}`\n"
        f"🏦  *Broker:*  `{broker_name}`\n\n"
        f"`{D}`\n"
        f"✅  *Screenshot received*\n"
        f"✅  *Broker name recorded*\n"
        f"🔄  *Waiting for admin approval*\n\n"
        f"`{DS}`\n"
        f"⏱  *Review time:*  `5 – 30 minutes`\n"
        f"_during working hours_\n\n"
        f"🔔  *You will be notified* once your\n"
        f"    *MM Access is activated!*\n\n"
        f"`{D}`\n"
        f"💬  _Contact support if no reply in 30 min._",
        parse_mode="Markdown"
    )

    from keyboards import admin_payment_kb
    caption = (
        f"🔔 MM ACCESS — PAYMENT REQUEST\n"
        f"{D}\n\n"
        f"👤  User:    {user.full_name} (@{user.username or 'N/A'})\n"
        f"🆔  ID:      {user.id}\n"
        f"📦  Plan:    {pkg['name'] if pkg else 'Unknown'}\n"
        f"💰  Amount:  ${pkg['price'] if pkg else '?'}\n"
        f"🏦  Broker:  {broker_name}\n\n"
        f"{D}\n"
        f"⬇️  Choose an action below:"
    )
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=caption,
        reply_markup=admin_payment_kb(payment_id)
    )


# ── Wrong file type when screenshot expected ─────────────────
@router.message(MMPaymentStates.waiting_screenshot)
async def mm_wrong_file_type(message: Message):
    await message.answer(
        f"❌ *Wrong file type!*\n"
        f"`{DS}`\n\n"
        f"📸  Please send your payment screenshot\n"
        f"    as a *photo*, not as a document or file.\n\n"
        f"_Tap the 📎 icon → choose Photo_",
        parse_mode="Markdown",
        reply_markup=mm_cancel_kb()
    )


# ── Wrong type when broker name expected ─────────────────────
@router.message(MMPaymentStates.waiting_broker_name)
async def mm_wrong_broker_input(message: Message):
    await message.answer(
        f"❌ *Invalid input*\n"
        f"`{DS}`\n\n"
        f"🏦  Please *type* your broker's name\n"
        f"    as a text message.\n\n"
        f"_Example: Quotex, IQ Option, Pocket Option_",
        parse_mode="Markdown",
        reply_markup=mm_cancel_kb()
    )
