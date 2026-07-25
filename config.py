import os

# ============================================================
#  CONFIG — Values are loaded from environment variables/secrets
# ============================================================

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", "0"))
GROUP_ID   = int(os.environ.get("GROUP_ID", "0"))

SUPPORT_USERNAME = os.environ.get("SUPPORT_USERNAME", "@JAYITAUTOBO")

PAYMENT_INSTRUCTIONS = os.environ.get("PAYMENT_INSTRUCTIONS", """💛 *Binance Pay* _(Business Official)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🪪  *Pay ID:*
`582355370`

🔷 *Crypto — USDT* _(TRC20 Network)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`TYudgrH88fCWzNqthy6tXQAieeNcCBYmER`

🟡 *Crypto — BTC* _(Bitcoin Network)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`1KgTBewwyvg6wd1F5jy9PKMy3mkvajbaCf`

🔸 *Crypto — BNB* _(BEP20 · Smart Chain)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`0x3dc13af0ff1a7f4585360ab416d35d335afe68e3`
""")

PAYMENT_INSTRUCTIONS_PAGE2 = os.environ.get("PAYMENT_INSTRUCTIONS_PAGE2", """🔵 *Crypto — ETH* _(Ethereum · ERC20)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`0x3dc13af0ff1a7f4585360ab416d35d335afe68e3`

🟣 *Crypto — SOL* _(Solana Network)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`CuG5iW99W8fKCPyT34Zkgyox2aa7hzyK8eRL3CXBvjXC`
""")

# ── MTG / NON-MTG SVIP Packages ────────────────────────────
PACKAGES = [
    # MTG Future Signal Compounding SVIP
    {"id": 1, "name": "🎀 SVIP · 3 Days",    "price": 5,  "days": 3,  "description": "MTG Future Signal Compounding SVIP"},
    {"id": 2, "name": "💠 SVIP · 6 Days",    "price": 10, "days": 6,  "description": "MTG Future Signal Compounding SVIP"},
    {"id": 3, "name": "🏅 SVIP · 14 Days",   "price": 20, "days": 14, "description": "MTG Future Signal Compounding SVIP"},
    {"id": 4, "name": "👑 SVIP · 30 Days",   "price": 52, "days": 30, "description": "MTG Future Signal Compounding SVIP"},
    {"id": 5, "name": "💎 SVIP · 60 Days",   "price": 66, "days": 60, "description": "MTG Future Signal Compounding SVIP"},
    # NON-MTG Future Signal Compounding
    {"id": 6, "name": "💠 NON-MTG · 6 Days",    "price": 15, "days": 6,  "description": "NON-MTG Future Signal Compounding"},
    {"id": 7, "name": "🏅 NON-MTG · 1 Month",   "price": 58, "days": 30, "description": "NON-MTG Future Signal Compounding"},
    {"id": 8, "name": "👑 NON-MTG · 3 Months",  "price": 99, "days": 90, "description": "NON-MTG Future Signal Compounding"},
]

# ── GOLDZILA / FOREX VIP Packages ──────────────────────────
FOREX_VIP_PACKAGES = [
    {"id": 1, "name": "🎯 FOREX SVIP · 10 Days",   "price": 30,  "days": 10,   "label": "10 Days"},
    {"id": 2, "name": "💠 FOREX SVIP · 15 Days",   "price": 48,  "days": 15,   "label": "15 Days"},
    {"id": 3, "name": "🔥 FOREX SVIP · 1 Month",   "price": 119, "days": 30,   "label": "1 Month"},
    {"id": 4, "name": "🏅 FOREX SVIP · 3 Months",  "price": 170, "days": 90,   "label": "3 Months"},
    {"id": 5, "name": "💎 FOREX SVIP · 12 Months", "price": 599, "days": 365,  "label": "12 Months"},
    {"id": 6, "name": "♾️ FOREX SVIP · UNLIMITED", "price": 899, "days": 3650, "label": "UNLIMITED"},
]

FOREX_LIFETIME_NOTE = (
    "━━━━━━━━━━━━\n"
    "♻️ *Lifetime Access available with partner link.*\n"
    "To get this please contact 👉 Support"
)

FOREX_PAYMENT_INSTRUCTIONS = os.environ.get("FOREX_PAYMENT_INSTRUCTIONS", """💛 *Binance Pay* _(Business Official)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🪪  *Pay ID:*
`582355370`

🔷 *Crypto — USDT* _(TRC20 Network)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`TYudgrH88fCWzNqthy6tXQAieeNcCBYmER`

🟡 *Crypto — BTC* _(Bitcoin Network)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`1KgTBewwyvg6wd1F5jy9PKMy3mkvajbaCf`

🔸 *Crypto — BNB* _(BEP20 · Smart Chain)_
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🏷  *Wallet Address:*
`0x3dc13af0ff1a7f4585360ab416d35d335afe68e3`
""")

# ── Tip shown for non-monthly packages (HTML) ──────────────
PACKAGE_TIP_HTML = (
    "💡 <b>Tips:</b>\n\n"
    "❒ নিজের account কে ভালো একটা boost up ভালো একটা রিজাল্ট দেখতে চাইলে, "
    "আমি personally suggested করবো ১/২মাসের জন্যে SVIP join করেন। "
    "সাথে আমি প্রতেকদিন কত ডলার profit করে market থেকে বের হইয়া যাবেন তার একটা "
    "DAILY target sheet দিয়া দিবো এবং ওইটা follow করলে মাস শেষে ৭০০/৮০০$+ profit "
    "থাকবে ইনশাল্লাহ। 💯💞\n\n"
    "〔 English 〕\n"
    "❒ NEED GOOD RESULT — BOOST YOUR Capital? I will personally suggest to join "
    "SVIP for 1/2 month. Also, I will give you a DAILY target sheet of how many "
    "dollars profit you will get out of the market every day and if you follow that, "
    "you will have 700/800$+ profit at the end of the month, in sha Allah. 💯💞"
)

# ── Loyalty Offer Packages (unlocked after 3 / 6 approved buys) ─
PAID_OFFER_TIER3 = [
    {"id": 101, "name": "🎁 OFFER · 1 Month",  "price": 45,  "days": 30, "description": "Loyalty Offer (3+ joins)"},
    {"id": 102, "name": "🎁 OFFER · 2 Months", "price": 53,  "days": 60, "description": "Loyalty Offer (3+ joins)"},
    {"id": 103, "name": "🎁 OFFER · 3 Months", "price": 110, "days": 90, "description": "Loyalty Offer (3+ joins)"},
]
PAID_OFFER_TIER6 = [
    {"id": 104, "name": "🏆 LIFETIME OFFER · 1 Month", "price": 30,  "days": 30, "description": "Lifetime Loyalty Offer (6+ joins)"},
    {"id": 102, "name": "🎁 OFFER · 2 Months",        "price": 53,  "days": 60, "description": "Loyalty Offer"},
    {"id": 103, "name": "🎁 OFFER · 3 Months",        "price": 110, "days": 90, "description": "Loyalty Offer"},
]

FOREX_OFFER_TIER3 = [
    {"id": 201, "name": "🎁 FOREX OFFER · 1 Month",  "price": 90,  "days": 30,  "label": "1 Month"},
    {"id": 202, "name": "🎁 FOREX OFFER · 2 Months", "price": 119, "days": 60,  "label": "2 Months"},
    {"id": 203, "name": "🎁 FOREX OFFER · 4 Months", "price": 150, "days": 120, "label": "4 Months"},
    {"id": 204, "name": "🎁 FOREX OFFER · 6 Months", "price": 200, "days": 180, "label": "6 Months"},
]
FOREX_OFFER_TIER6 = [
    {"id": 205, "name": "🏆 FOREX LIFETIME OFFER · 1 Month", "price": 68,  "days": 30,  "label": "1 Month"},
    {"id": 202, "name": "🎁 FOREX OFFER · 2 Months",         "price": 119, "days": 60,  "label": "2 Months"},
    {"id": 203, "name": "🎁 FOREX OFFER · 4 Months",         "price": 150, "days": 120, "label": "4 Months"},
    {"id": 204, "name": "🎁 FOREX OFFER · 6 Months",         "price": 200, "days": 180, "label": "6 Months"},
]

# ── Scheduler reminder windows (handled internally in scheduler.py) ─
REMINDER_DAYS_BEFORE = [7, 5, 3]

# ── MM Access Packages ──────────────────────────────────────
MM_PACKAGES = [
    {"id": 301, "name": "MM Access · 13 Days",  "price": 6,   "days": 13,  "label": "13 Days"},
    {"id": 302, "name": "MM Access · 25 Days",  "price": 10,  "days": 25,  "label": "25 Days"},
    {"id": 303, "name": "MM Access · 1 Month",  "price": 15,  "days": 30,  "label": "1 Month"},
    {"id": 304, "name": "MM Access · 2 Months", "price": 25,  "days": 60,  "label": "2 Months"},
    {"id": 305, "name": "MM Access · 4 Months", "price": 60,  "days": 120, "label": "4 Months"},
    {"id": 306, "name": "MM Access · Lifetime", "price": 100, "days": 0,   "label": "Lifetime"},
]
