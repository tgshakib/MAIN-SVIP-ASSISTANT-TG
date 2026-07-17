from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import SUPPORT_USERNAME

router = Router()

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"

# ── Full TradingView pair coverage ─────────────────────────────
KNOWN_PAIRS = {
    # Major Forex
    "EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","NZDUSD","USDCAD",
    # Minor Forex
    "EURGBP","EURJPY","GBPJPY","EURCHF","EURAUD","EURCAD","GBPCHF",
    "GBPAUD","GBPCAD","AUDJPY","CADJPY","CHFJPY","NZDJPY","AUDCAD",
    "AUDCHF","AUDNZD","CADCHF","EURNZD","GBPNZD","NZDCAD","NZDCHF",
    "EURHUF","EURPLN","EURTRY","EURZAR","EURSEK","EURDKK","EURNOK",
    "EURSGD","EURMXN","GBPHUF","GBPSGD","GBPTRY","GBPZAR","GBPMXN",
    "GBPSEK","GBPDKK","GBPNOK","GBPPLN","USDTRY","USDZAR","USDPLN",
    "USDHUF","USDSGD","USDMXN","USDSEK","USDDKK","USDNOK","USDTHB",
    "USDCNH","USDCNY","USDINR","USDRUB","USDCZK","USDHKD","USDPHP",
    "AUDZAR","AUDSGD","CADSGD","CHFSGD","CHFTRY","NZDSGD","NZDCHF",
    "ZARJPY","MXNJPY","SGDJPY","NOKJPY","SEKJPY","DKKJPY","PLNJPY",
    "TRYJPY","HKDJPY","CNHJPY","RUBSEK","CNYSEK",
    # Precious Metals
    "XAUUSD","GOLD","XAGUSD","SILVER","XPTUSD","XPDUSD","XAUEUR",
    "XAUGBP","XAUJPY","XAUCHF","XAUAUD","XAUXAG",
    # Crypto
    "BTCUSD","ETHUSD","BTCEUR","ETHEUR","BTCGBP","ETHGBP",
    "XRPUSD","BNBUSD","SOLUSD","ADAUSD","DOGEUSD","AVAXUSD",
    "LINKUSD","MATICUSD","DOTUSD","LTCUSD","BCHUSD","XLMUSD",
    "UNIUSD","ATOMUSD","ETCUSD","FILUSD","TRXUSD","SHIBUSD",
    "BTCUSDT","ETHUSDT","XRPUSDT","BNBUSDT","SOLUSDT",
    # US Indices
    "US30","US500","NAS100","USTEC","US2000","DJ30","SPX500",
    "NDX100","DXY","VIX",
    # European & Global Indices
    "UK100","GER40","FRA40","ESP35","ITA40","SUI20","NED25",
    "EU50","JPN225","AUS200","HKG33","SIN30","CHINA50",
    "BRAZ35","IND50","RUS50",
    # Commodities / Energy
    "USOUSD","UKOIL","OIL","CRUDE","NATGAS","BRENT","WTI",
    "COFFEE","COCOA","SUGAR","COTTON","WHEAT","CORN","SOYBEAN",
    "COPPER","PLATINUM","PALLADIUM","ALUMINUM","NICKEL","ZINC",
}

_VALID_SUFFIXES = (
    "JPY","USD","EUR","GBP","CHF","AUD","CAD","NZD","SGD","HKD",
    "NOK","SEK","DKK","PLN","HUF","CZK","TRY","ZAR","MXN","CNH",
    "CNY","INR","RUB","THB","PHP","BRL","USDT","BTC","ETH",
)
_VALID_PREFIXES = (
    "EUR","GBP","USD","AUD","NZD","CAD","CHF","JPY","SGD","HKD",
    "NOK","SEK","DKK","PLN","HUF","CZK","TRY","ZAR","MXN","XAU",
    "XAG","XPT","XPD","BTC","ETH","XRP","BNB","SOL","ADA","LTC",
)


def _is_recognized_pair(pair: str) -> bool:
    p = pair.upper().strip()
    if p in KNOWN_PAIRS:
        return True
    if len(p) >= 6:
        for sfx in _VALID_SUFFIXES:
            if p.endswith(sfx) and len(p) > len(sfx):
                return True
        for pfx in _VALID_PREFIXES:
            if p.startswith(pfx) and len(p) > len(pfx):
                return True
    return False


# ── Lot size table ─────────────────────────────────────────────
LOT_TABLE = [
    (0,     100,   0.01, 0.02),
    (101,   300,   0.02, 0.04),
    (301,   500,   0.04, 0.06),
    (501,   700,   0.06, 0.08),
    (701,   900,   0.08, 0.10),
    (901,   2000,  0.10, 0.15),
    (2001,  4000,  0.30, 0.35),
    (4001,  6000,  0.50, 0.55),
    (6001,  8000,  0.70, 0.75),
    (8001,  10000, 0.90, 1.00),
]


def _get_lots(account: float) -> tuple:
    for (lo, hi, safe_low, safe_high) in LOT_TABLE:
        if lo <= account <= hi:
            safe   = safe_low
            medium = safe_high
            risk   = round(safe_high + (safe_high - safe_low), 2)
            return safe, medium, risk
    safe   = round(account / 10000, 2)
    medium = round(safe * 1.5, 2)
    risk   = round(safe * 2.0, 2)
    return safe, medium, risk


# ── FSM States ────────────────────────────────────────────────
class ForexCalcStates(StatesGroup):
    waiting_pair    = State()
    waiting_account = State()
    waiting_target  = State()


# ── Prompt tracker ────────────────────────────────────────────
async def _save_fx_prompt(state: FSMContext, msg):
    await state.update_data(
        fx_prompt_chat_id=msg.chat.id,
        fx_prompt_msg_id=msg.message_id,
    )


async def _delete_fx_prompt(state: FSMContext, bot):
    data = await state.get_data()
    chat_id = data.get("fx_prompt_chat_id")
    msg_id  = data.get("fx_prompt_msg_id")
    if chat_id and msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        await state.update_data(fx_prompt_chat_id=None, fx_prompt_msg_id=None)


# ── Live dashboard text ────────────────────────────────────────
def _page1_text(pair=None, account=None, target=None) -> str:
    pair_val    = f"`{pair}` ✅"    if pair    else "—"
    account_val = f"${account:.2f} ✅" if account is not None else "—"
    target_val  = f"${target:.2f} ✅" if target  is not None else "—"

    return (
        "📊 *FOREX PIPS CALCULATOR*\n"
        f"`{DIVIDER}`\n"
        "📋 *LIVE SETUP DASHBOARD:*\n"
        f"  📌 Pair:    {pair_val}\n"
        f"  💵 Account: {account_val}\n"
        f"  🎯 Target:  {target_val}\n"
        f"`{DIVIDER}`\n"
        "_Tap each button below to set a value._"
    )


def _page1_kb(pair=None, account=None, target=None) -> InlineKeyboardMarkup:
    pair_lbl    = f"📌 Pair: {pair}"             if pair    else "📌 Pair Name"
    account_lbl = f"💵 Account: ${account:.0f}"  if account is not None else "💵 Account Size"
    target_lbl  = f"🎯 Target: ${target:.0f}"    if target  is not None else "🎯 Target Profit"

    rows = [
        [InlineKeyboardButton(text=pair_lbl,    callback_data="fx_set_pair")],
        [InlineKeyboardButton(text=account_lbl, callback_data="fx_set_account")],
        [InlineKeyboardButton(text=target_lbl,  callback_data="fx_set_target")],
    ]
    if pair and account is not None and target is not None:
        rows.append([InlineKeyboardButton(text="📈 Calculate Now", callback_data="fx_calculate")])
    rows.append([InlineKeyboardButton(text="◀️ Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _show_page1(target_msg, state: FSMContext):
    data    = await state.get_data()
    pair    = data.get("fx_pair")
    account = data.get("fx_account")
    tgt     = data.get("fx_target")
    text    = _page1_text(pair, account, tgt)
    kb      = _page1_kb(pair, account, tgt)
    try:
        await target_msg.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await target_msg.answer(text, parse_mode="Markdown", reply_markup=kb)


# ── Entry point ───────────────────────────────────────────────
@router.callback_query(F.data == "open_forex_calc")
async def open_forex_calc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await _show_page1(callback.message, state)
    await callback.answer()


# ── Set Pair ──────────────────────────────────────────────────
@router.callback_query(F.data == "fx_set_pair")
async def fx_set_pair(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ForexCalcStates.waiting_pair)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
    ])
    prompt = (
        "📌 *Type your Pair name:*\n"
        "_(Forex: EURUSD, GBPJPY, XAUUSD\n"
        "Crypto: BTCUSD, ETHUSD\n"
        "Index: US30, NAS100, GER40\n"
        "Metal: GOLD, SILVER)_"
    )
    try:
        msg = await callback.message.edit_text(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg if msg else callback.message)
    except Exception:
        msg = await callback.message.answer(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg)
    await callback.answer()


@router.message(ForexCalcStates.waiting_pair)
async def fx_receive_pair(message: Message, state: FSMContext):
    pair = message.text.strip().upper() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    await _delete_fx_prompt(state, message.bot)
    if not pair or not _is_recognized_pair(pair):
        await message.answer(
            f"⚠️ *{pair}* — This pair is not available to find.\n\n"
            "You can get help by *CHATGPT* to find the correct pair name.\n\n"
            "_(All TradingView markets supported: Forex, Crypto, Indices, Metals, Energy)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
            ])
        )
        return
    await state.update_data(fx_pair=pair)
    await state.set_state(None)
    await _show_page1(message, state)


# ── Set Account ───────────────────────────────────────────────
@router.callback_query(F.data == "fx_set_account")
async def fx_set_account(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ForexCalcStates.waiting_account)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
    ])
    prompt = "💵 *Type your Account Size* ($):\n_(Example: 100)_"
    try:
        msg = await callback.message.edit_text(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg if msg else callback.message)
    except Exception:
        msg = await callback.message.answer(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg)
    await callback.answer()


@router.message(ForexCalcStates.waiting_account)
async def fx_receive_account(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    await _delete_fx_prompt(state, message.bot)
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer(
            "Please enter a valid account size (positive number).",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
            ])
        )
        return
    await state.update_data(fx_account=value)
    await state.set_state(None)
    await _show_page1(message, state)


# ── Set Target ────────────────────────────────────────────────
@router.callback_query(F.data == "fx_set_target")
async def fx_set_target(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ForexCalcStates.waiting_target)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
    ])
    prompt = "🎯 *Type your Target Profit* ($):\n_(Example: 20)_"
    try:
        msg = await callback.message.edit_text(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg if msg else callback.message)
    except Exception:
        msg = await callback.message.answer(prompt, parse_mode="Markdown", reply_markup=kb)
        await _save_fx_prompt(state, msg)
    await callback.answer()


@router.message(ForexCalcStates.waiting_target)
async def fx_receive_target(message: Message, state: FSMContext):
    data    = await state.get_data()
    account = data.get("fx_account")
    text    = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass
    await _delete_fx_prompt(state, message.bot)
    try:
        value = float(text.replace(",", ""))
        assert value > 0
    except (ValueError, AssertionError):
        await message.answer(
            "Please enter a valid profit target (positive number).",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
            ])
        )
        return
    if account and value > account:
        await message.answer(
            f"Target profit cannot exceed account size.\n"
            f"Your account: `${account:.2f}`\n"
            f"Please enter a smaller target.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Back", callback_data="fx_back_to_page1")]
            ])
        )
        return
    await state.update_data(fx_target=value)
    await state.set_state(None)
    await _show_page1(message, state)


# ── Calculate Now ─────────────────────────────────────────────
@router.callback_query(F.data == "fx_calculate")
async def fx_calculate(callback: CallbackQuery, state: FSMContext):
    data    = await state.get_data()
    pair    = data.get("fx_pair")
    account = data.get("fx_account")
    target  = data.get("fx_target")

    if not pair or account is None or target is None:
        await callback.answer("Please fill all 3 values first.", show_alert=True)
        return

    safe, medium, risk = _get_lots(account)

    note = ""
    if pair.upper() not in KNOWN_PAIRS:
        note = "_Using standard pip value. Verify with your broker._\n"

    text = (
        "📊 *FOREX PIPS CALCULATOR*\n"
        f"`{DIVIDER}`\n"
        f"📌 Pair:    `{pair}`\n"
        f"💵 Account: `${account:.0f}`\n"
        f"🎯 Target:  `${target:.0f}`\n"
        f"`{DIVIDER}`\n"
        "*LOT SIZE SUGGESTIONS*\n\n"
        f"  ✅  *SAFE*    →  `{safe:.2f}`\n"
        f"  ⚠️  *MEDIUM*  →  `{medium:.2f}`\n"
        f"  🔴  *RISK*    →  `{risk:.2f}`\n\n"
        f"`{DIVIDER}`\n"
        f"{note}"
        "_Always go for Safe Lots sizes._\n\n"
        "*JOIN OUR SVIP or BUY ADVANCE AI BOT*\n"
        "_for a more accurate Trading journey._\n"
        f"`{DIVIDER}`"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back",          callback_data="fx_back_to_page1")],
        [InlineKeyboardButton(text="🏠 Home",          callback_data="back_main")],
        [InlineKeyboardButton(text="🔄 New Calculate", callback_data="fx_new_calculate")],
        [InlineKeyboardButton(text="💬 Support",       url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
    ])

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


# ── New Calculate (reset) ─────────────────────────────────────
@router.callback_query(F.data == "fx_new_calculate")
async def fx_new_calculate(callback: CallbackQuery, state: FSMContext):
    await state.update_data(fx_pair=None, fx_account=None, fx_target=None)
    await state.set_state(None)
    text = _page1_text()
    kb   = _page1_kb()
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


# ── Back to page 1 ────────────────────────────────────────────
@router.callback_query(F.data == "fx_back_to_page1")
async def fx_back_to_page1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await _show_page1(callback.message, state)
    await callback.answer()
