from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import mm_database as mmdb
from locale import _load_locale, VALID_LANGS

router = Router()

LANGUAGES = [
    ("en", "🇬🇧 English"),
    ("ar", "🇸🇦 العربية"),
    ("bn", "🇧🇩 বাংলা"),
    ("zh", "🇨🇳 中文"),
    ("de", "🇩🇪 Deutsch"),
    ("es", "🇪🇸 Español"),
    ("fr", "🇫🇷 Français"),
    ("ha", "🌍 Hausa"),
    ("hi", "🇮🇳 हिंदी"),
    ("id", "🇮🇩 Indonesia"),
    ("it", "🇮🇹 Italiano"),
    ("ja", "🇯🇵 日本語"),
    ("ko", "🇰🇷 한국어"),
    ("pt", "🇧🇷 Português"),
    ("ru", "🇷🇺 Русский"),
    ("th", "🇹🇭 ภาษาไทย"),
    ("tl", "🇵🇭 Filipino"),
    ("tr", "🇹🇷 Türkçe"),
    ("ur", "🇵🇰 اردو"),
    ("vi", "🇻🇳 Tiếng Việt"),
]

D = "━━━━━━━━━━━━━━━━━━━━"


def _lang_kb(current: str) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(LANGUAGES), 2):
        row = []
        for code, name in LANGUAGES[i:i + 2]:
            mark = " ✅" if code == current else ""
            row.append(InlineKeyboardButton(
                text=f"{name}{mark}",
                callback_data=f"mm_lang_{code}"
            ))
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text="◀️ Back",       callback_data="open_mm_menu"),
        InlineKeyboardButton(text="🔄 Reset (EN)", callback_data="mm_lang_reset"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "mm_set_language")
async def mm_language_panel(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    mmdb.upsert_mm_user(user_id, callback.from_user.username or "")
    await state.clear()
    current = mmdb.get_user_language(user_id)
    text = (
        "🌐 *Select Your Language*\n"
        f"`{D}`\n"
        "_Tap your language —_ ✅ _= currently active_\n"
        "_Session text: 90% your language, 10% English._\n"
        f"`{D}`"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=_lang_kb(current))
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=_lang_kb(current))
    await callback.answer()


@router.callback_query(F.data == "mm_lang_reset")
async def mm_lang_reset(callback: CallbackQuery):
    user_id = callback.from_user.id
    mmdb.set_user_language(user_id, "en")
    await callback.answer("✅ Language reset to English")
    text = (
        "🌐 *Select Your Language*\n"
        f"`{D}`\n"
        "✅ *Language reset to English*\n"
        f"`{D}`"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=_lang_kb("en"))
    except Exception:
        pass


@router.callback_query(F.data.startswith("mm_lang_"))
async def mm_lang_select(callback: CallbackQuery):
    user_id = callback.from_user.id
    code = callback.data[8:]
    if code not in VALID_LANGS:
        await callback.answer("Invalid selection.", show_alert=True)
        return

    mmdb.set_user_language(user_id, code)
    locale_data = _load_locale(code)
    lang_name = locale_data.get("lang_name", code.upper())

    await callback.answer(f"✅ {lang_name}")
    text = (
        "🌐 *Select Your Language*\n"
        f"`{D}`\n"
        f"✅ *{lang_name}* selected\n"
        "_Session text will now show in your language._\n"
        f"`{D}`"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=_lang_kb(code))
    except Exception:
        pass
