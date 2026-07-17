import asyncio
from collections import defaultdict
from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.methods import TelegramMethod, Response
from aiogram.methods.base import TelegramType

import database as db

_USER_MSG_IDS: dict[int, list[int]] = defaultdict(list)


def add_id(chat_id: int, message_id: int) -> None:
    _USER_MSG_IDS[int(chat_id)].append(int(message_id))


def pop_all(chat_id: int) -> list[int]:
    ids = list(_USER_MSG_IDS.get(int(chat_id), []))
    _USER_MSG_IDS[int(chat_id)] = []
    return ids


async def wipe_chat(bot: Bot, chat_id: int, anchor_id: int, lookback: int = 50) -> None:
    """
    Delete anchor_id and up to `lookback` messages before it using ID range,
    plus any IDs tracked in the in-memory store.

    This is range-based and does NOT rely on in-memory state, so it works
    correctly even after a bot restart. Silently ignores all failures
    (user messages, already-deleted messages, permission errors, etc.).
    """
    tracked = pop_all(chat_id)

    # Build a deduplicated set of message IDs to attempt deletion:
    # tracked IDs (may be empty after restart) + range around anchor
    ids: set[int] = set(tracked)
    for mid in range(anchor_id + 5, max(anchor_id - lookback, 1), -1):
        ids.add(mid)

    async def _try_delete(mid: int) -> None:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass

    # Delete in parallel, batched to avoid flooding Telegram
    id_list = list(ids)
    for i in range(0, len(id_list), 20):
        batch = id_list[i:i + 20]
        await asyncio.gather(*[_try_delete(m) for m in batch])


class UserOutgoingTracker(BaseRequestMiddleware):
    """Tracks every outgoing bot message in non-admin private chats so they can be cleaned later."""

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        result = await make_request(bot, method)
        try:
            chat_id = getattr(method, "chat_id", None)
            if chat_id is None:
                return result
            try:
                admin_id = db.get_admin_id()
            except Exception:
                admin_id = 0
            if int(chat_id) == int(admin_id):
                return result
            mid = getattr(result, "message_id", None)
            if mid:
                add_id(chat_id, mid)
            elif isinstance(result, list):
                for m in result:
                    mid = getattr(m, "message_id", None)
                    if mid:
                        add_id(chat_id, mid)
        except Exception:
            pass
        return result
