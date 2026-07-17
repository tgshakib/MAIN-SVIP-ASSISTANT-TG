import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter

import database as db
from keyboards import back_admin_kb

logger = logging.getLogger(__name__)
router = Router()

BATCH_SIZE   = 25    # messages per batch
BATCH_DELAY  = 1.0   # seconds between batches
RETRY_DELAY  = 5     # seconds to wait after a flood error (on top of retry_after)

# ── FSM ─────────────────────────────────────────────────────
class MailingStates(StatesGroup):
    waiting_message = State()
    confirming      = State()

# ── Stored pending broadcast (keyed by admin user_id) ───────
_pending: dict[int, Message] = {}

def _is_admin(user_id: int) -> bool:
    return user_id == db.get_admin_id()

# ── Mailing confirm keyboard ─────────────────────────────────
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def mailing_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Send Mailing", callback_data="mailing_send")],
        [InlineKeyboardButton(text="❌ Cancel",        callback_data="mailing_cancel")],
    ])

# ── 1. Admin presses "📤 Mailing" ───────────────────────────
@router.callback_query(F.data == "admin_mailing")
async def admin_mailing_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(MailingStates.waiting_message)
    await callback.message.edit_text(
        "📤 <b>Broadcast / Mailing</b>\n\n"
        "Send or forward the message you want to broadcast to <b>all users</b>.\n\n"
        "Accepted: text, photo, video, document, animation, voice, audio, forwarded messages.",
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )
    await callback.answer()

# ── 2. Admin sends/forwards the broadcast content ───────────
@router.message(MailingStates.waiting_message)
async def mailing_receive_message(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    _pending[message.from_user.id] = message
    await state.set_state(MailingStates.confirming)

    total = len(db.get_all_user_ids())
    await message.answer(
        f"📋 <b>Preview received.</b>\n\n"
        f"Ready to send this mailing to <b>{total} users</b>.\n\n"
        f"Confirm?",
        parse_mode="HTML",
        reply_markup=mailing_confirm_kb()
    )

# ── 3. Admin confirms → broadcast ───────────────────────────
@router.callback_query(F.data == "mailing_send")
async def mailing_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not _is_admin(callback.from_user.id):
        return

    src_msg = _pending.pop(callback.from_user.id, None)
    if not src_msg:
        await callback.answer("⚠️ No message found. Please start over.", show_alert=True)
        await state.clear()
        return

    await state.clear()
    user_ids = db.get_all_user_ids()
    total     = len(user_ids)
    sent      = 0
    failed    = 0

    # Live progress message
    progress_msg = await callback.message.edit_text(
        f"📤 <b>Broadcasting…</b>\n\n"
        f"✅ Sent: 0\n❌ Failed: 0\n⏳ Remaining: {total}",
        parse_mode="HTML"
    )
    await callback.answer()

    for i, uid in enumerate(user_ids):
        try:
            await _copy_message(bot, uid, src_msg)
            sent += 1
        except TelegramRetryAfter as e:
            # Flood control — wait and retry once
            await asyncio.sleep(e.retry_after + RETRY_DELAY)
            try:
                await _copy_message(bot, uid, src_msg)
                sent += 1
            except Exception:
                failed += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            # User blocked bot or chat not found — skip silently
            failed += 1
        except Exception as exc:
            logger.error("Mailing error for uid=%s: %s", uid, exc)
            failed += 1

        # Update progress every 25 messages
        if (i + 1) % BATCH_SIZE == 0:
            remaining = total - (i + 1)
            try:
                await progress_msg.edit_text(
                    f"📤 <b>Broadcasting…</b>\n\n"
                    f"✅ Sent: {sent}\n❌ Failed: {failed}\n⏳ Remaining: {remaining}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            await asyncio.sleep(BATCH_DELAY)

    success_rate = round((sent / total * 100), 1) if total else 0

    await progress_msg.edit_text(
        f"📊 <b>Mailing Completed</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"✅ Delivered: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📈 Success Rate: <b>{success_rate}%</b>",
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )

# ── 4. Admin cancels ────────────────────────────────────────
@router.callback_query(F.data == "mailing_cancel")
async def mailing_cancel(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return
    _pending.pop(callback.from_user.id, None)
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Mailing cancelled.</b>",
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )
    await callback.answer("Cancelled.")

# ── Helper: copy any message type to a target user ──────────
async def _copy_message(bot: Bot, chat_id: int, msg: Message):
    """Copy the admin's message to chat_id, preserving all content types."""
    # Use copyMessage API — preserves formatting, media, captions
    await bot.copy_message(
        chat_id=chat_id,
        from_chat_id=msg.chat.id,
        message_id=msg.message_id
    )
