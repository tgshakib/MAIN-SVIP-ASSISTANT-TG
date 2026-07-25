from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    PACKAGES, FOREX_VIP_PACKAGES, SUPPORT_USERNAME,
    PAID_OFFER_TIER3, PAID_OFFER_TIER6,
    FOREX_OFFER_TIER3, FOREX_OFFER_TIER6,
    MM_PACKAGES,
)

# ── Start / Join Options ───────────────────────────────────
def join_options_kb(is_admin: bool = False, has_offer: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="💎 BIANRY PAID JOIN", callback_data="paid_join"),
            InlineKeyboardButton(text="💹 FOREX VIP JOIN",   callback_data="forex_join"),
        ],
        [
            InlineKeyboardButton(text="🎁 MONTHLY JOIN OFFERS", callback_data="monthly_offers"),
        ],
    ]
    if has_offer:
        rows.append([
            InlineKeyboardButton(text="🎁 MY OFFER", callback_data="my_offer"),
        ])
    rows += [
        [
            InlineKeyboardButton(text="🔗 REFER JOIN",      callback_data="refer_join"),
            InlineKeyboardButton(text="🏢 OFFLINE VIP JOIN", url="https://t.me/OAWHIDSHAKIB"),
        ],
        [
            InlineKeyboardButton(text="🤖 SOFTWARE & AI SIGNAL BOT BUY", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"),
        ],
        [
            InlineKeyboardButton(text="🔄 CONVERTER", callback_data="open_converter"),
        ],
        [
            InlineKeyboardButton(text="💰 MONEY MANAGEMENT", callback_data="open_mm_menu"),
        ],
    ]
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="🛡️ ADMINISTRATION ACCESS", callback_data="admin_panel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ── Paid Join Menu ─────────────────────────────────────────
def paid_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Packages",         callback_data="show_packages"),
            InlineKeyboardButton(text="💬 Support",          url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"),
        ],
        [
            InlineKeyboardButton(text="💳 Pay Now",          callback_data="pay_now"),
            InlineKeyboardButton(text="📊 My Subscription",  callback_data="my_sub"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back",             callback_data="back_main"),
        ],
    ])

# ── FOREX VIP section ─────────────────────────────────────
def forex_join_kb() -> InlineKeyboardMarkup:
    buttons = []
    for p in FOREX_VIP_PACKAGES:
        buttons.append([InlineKeyboardButton(
            text=f"{p['label']}  ·  ${p['price']}",
            callback_data=f"fpkg_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="💬 Support",
        url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Forex: after package selected ─────────────────────────
def forex_proceed_payment_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Proceed to Payment",    callback_data=f"fpay_{pkg_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Forex Plans",   callback_data="forex_join")],
    ])

# ── Forex: payment instructions screen ────────────────────
def forex_payment_instructions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",   callback_data="forex_check_screenshot")],
        [InlineKeyboardButton(text="➡️ More Payment Methods",  callback_data="fpay_p2")],
        [InlineKeyboardButton(text="💬 Support",                url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="❌ Cancel",                 callback_data="back_main")],
    ])

def forex_payment_instructions_page2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",   callback_data="forex_check_screenshot")],
        [InlineKeyboardButton(text="⬅️ Back to Page 1",        callback_data="fpay_p1")],
        [InlineKeyboardButton(text="💬 Support",                url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="❌ Cancel",                 callback_data="back_main")],
    ])

# ── Forex: cancel only ─────────────────────────────────────
def forex_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="back_main")]
    ])

# ── Refer Join ─────────────────────────────────────────────
def refer_join_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 DM @OAWHIDSHAKIB",  url="https://t.me/OAWHIDSHAKIB")],
        [
            InlineKeyboardButton(text="📊 EXNESS",         callback_data="broker_exness"),
            InlineKeyboardButton(text="💹 POCKET OPTION",  callback_data="broker_pocket"),
        ],
        [InlineKeyboardButton(text="📈 QUOTEX",            callback_data="broker_quotex")],
        [InlineKeyboardButton(text="🏦 Others Broker",     url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="⬅️ Back",              callback_data="back_main")],
    ])

# ── Package Selection ──────────────────────────────────────
def packages_kb() -> InlineKeyboardMarkup:
    svip_pkgs  = [p for p in PACKAGES if "SVIP" in p["name"]]
    other_pkgs = [p for p in PACKAGES if "SVIP" not in p["name"]]

    buttons = []
    buttons.append([
        InlineKeyboardButton(text="— 🏆 MTG FUTURE SVIP —", callback_data="noop")
    ])
    for i in range(0, len(svip_pkgs), 2):
        row = []
        for pkg in svip_pkgs[i:i+2]:
            duration = pkg["name"].split("·")[-1].strip()
            row.append(InlineKeyboardButton(
                text=f"{duration}  ·  ${pkg['price']}",
                callback_data=f"pkg_{pkg['id']}"
            ))
        buttons.append(row)

    if other_pkgs:
        buttons.append([
            InlineKeyboardButton(text="— 📈 NON-MTG SIGNAL —", callback_data="noop")
        ])
        for i in range(0, len(other_pkgs), 2):
            row = []
            for pkg in other_pkgs[i:i+2]:
                duration = pkg["name"].split("·")[-1].strip()
                row.append(InlineKeyboardButton(
                    text=f"{duration}  ·  ${pkg['price']}",
                    callback_data=f"pkg_{pkg['id']}"
                ))
            buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_paid")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── After package selected ─────────────────────────────────
def proceed_payment_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Proceed to Payment",  callback_data=f"pay_{pkg_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Packages",    callback_data="show_packages")],
    ])

# ── Payment instructions screen ────────────────────────────
def payment_instructions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",      callback_data="check_screenshot")],
        [InlineKeyboardButton(text="➡️ More Payment Methods",     callback_data="pay_p2")],
        [InlineKeyboardButton(text="❌ Cancel",                    callback_data="back_paid")],
    ])

def payment_instructions_page2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",      callback_data="check_screenshot")],
        [InlineKeyboardButton(text="⬅️ Back to Page 1",           callback_data="pay_p1")],
        [InlineKeyboardButton(text="❌ Cancel",                    callback_data="back_paid")],
    ])

# ── Waiting for screenshot photo ──────────────────────────
def cancel_only_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="back_paid")]
    ])

# ── Admin: approve / reject ────────────────────────────────
def admin_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🤲 Alhamdulillah Receive Payment",
            callback_data=f"approve_{payment_id}"
        )],
        [InlineKeyboardButton(text="❌ Rejected", callback_data=f"reject_{payment_id}")],
    ])

# ── Admin main panel ───────────────────────────────────────
def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Pending Payments",  callback_data="admin_pending"),
            InlineKeyboardButton(text="👥 Active Members",    callback_data="admin_members"),
        ],
        [
            InlineKeyboardButton(text="📤 Mailing",           callback_data="admin_mailing"),
        ],
        [
            InlineKeyboardButton(text="📊 Stats",             callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="🔑 MM Access Grant",   callback_data="admin_mm_grant"),
        ],
        [
            InlineKeyboardButton(text="🔄 Transfer Admin",    callback_data="admin_transfer"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back",              callback_data="back_main"),
        ],
        [
            InlineKeyboardButton(text="🧹 CLOSE ADMIN PANEL", callback_data="admin_close"),
        ],
    ])

# ── Active members page actions ────────────────────────────
def active_members_actions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Ban / Remove Member",  callback_data="admin_ban_list")],
        [InlineKeyboardButton(text="⬅️ Back to Admin Panel",  callback_data="admin_panel")],
    ])

# ── Ban member: list all active members ────────────────────
def ban_member_list_kb(members: list) -> InlineKeyboardMarkup:
    buttons = []
    for m in members:
        uname = f"@{m['username']}" if m.get("username") else m.get("full_name", "Unknown")
        pkg   = m.get("package_name", "")
        buttons.append([InlineKeyboardButton(
            text=f"🚫 {uname} — {pkg}",
            callback_data=f"banrem_{m['user_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="admin_members")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Ban confirm ────────────────────────────────────────────
def ban_confirm_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes, Remove Now",  callback_data=f"banyes_{user_id}")],
        [InlineKeyboardButton(text="❌ Cancel",           callback_data="admin_ban_list")],
    ])

# ── Transfer confirm ───────────────────────────────────────
def transfer_confirm_kb(new_admin_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes, Transfer Now", callback_data=f"transfer_confirm_{new_admin_id}")],
        [InlineKeyboardButton(text="❌ Cancel",            callback_data="admin_panel")],
    ])

# ── Back to admin panel ────────────────────────────────────
def back_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="admin_panel")]
    ])

# ── Member dashboard (active sub) — 2 buttons only ────────
def member_start_kb(is_forex_sub: bool = False, is_admin: bool = False, has_offer: bool = False) -> InlineKeyboardMarkup:
    renew_data = "renew_forex" if is_forex_sub else "renew_paid"
    first_row = [
        InlineKeyboardButton(text="🔄 Renew",  callback_data=renew_data),
        InlineKeyboardButton(text="📋 MANU",   callback_data="start_refresh"),
    ]
    if has_offer:
        first_row.append(InlineKeyboardButton(text="🎁 MY OFFER", callback_data="my_offer"))
    rows = [first_row]
    rows.append([
        InlineKeyboardButton(text="🔄 CONVERTER", callback_data="open_converter"),
    ])
    rows.append([
        InlineKeyboardButton(text="💰 MONEY MANAGEMENT", callback_data="open_mm_menu"),
    ])
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="🛡️ ADMINISTRATION ACCESS", callback_data="admin_panel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── My Offer: category chooser (when both paid & forex unlocked) ──
def my_offer_chooser_kb(paid_unlocked: bool, forex_unlocked: bool) -> InlineKeyboardMarkup:
    rows = []
    if paid_unlocked:
        rows.append([InlineKeyboardButton(text="💎 PAID VIP — My Offer", callback_data="my_offer_paid")])
    if forex_unlocked:
        rows.append([InlineKeyboardButton(text="💹 FOREX VIP — My Offer", callback_data="my_offer_forex")])
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── My Offer: paid offer packages ─────────────────────────
def paid_offer_packages_kb(tier: int) -> InlineKeyboardMarkup:
    pkgs = PAID_OFFER_TIER6 if tier >= 6 else PAID_OFFER_TIER3
    buttons = []
    for p in pkgs:
        duration = p["name"].split("·")[-1].strip()
        buttons.append([InlineKeyboardButton(
            text=f"{duration}  ·  ${p['price']}",
            callback_data=f"opkg_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def paid_offer_proceed_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Proceed to Payment", callback_data=f"opay_{pkg_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Offers",     callback_data="my_offer_paid")],
    ])


def paid_offer_payment_instructions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",  callback_data="ocheck_screenshot")],
        [InlineKeyboardButton(text="➡️ More Payment Methods", callback_data="opay_p2")],
        [InlineKeyboardButton(text="❌ Cancel",                callback_data="my_offer_paid")],
    ])

def paid_offer_payment_instructions_page2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",  callback_data="ocheck_screenshot")],
        [InlineKeyboardButton(text="⬅️ Back to Page 1",       callback_data="opay_p1")],
        [InlineKeyboardButton(text="❌ Cancel",                callback_data="my_offer_paid")],
    ])


def paid_offer_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="my_offer_paid")]
    ])


# ── My Offer: forex offer packages ────────────────────────
def forex_offer_packages_kb(tier: int) -> InlineKeyboardMarkup:
    pkgs = FOREX_OFFER_TIER6 if tier >= 6 else FOREX_OFFER_TIER3
    buttons = []
    for p in pkgs:
        buttons.append([InlineKeyboardButton(
            text=f"{p['label']}  ·  ${p['price']}",
            callback_data=f"ofpkg_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="💬 Support", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Back",    callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def forex_offer_proceed_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Proceed to Payment", callback_data=f"ofpay_{pkg_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Offers",     callback_data="my_offer_forex")],
    ])


def forex_offer_payment_instructions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",  callback_data="ofcheck_screenshot")],
        [InlineKeyboardButton(text="➡️ More Payment Methods", callback_data="ofpay_p2")],
        [InlineKeyboardButton(text="💬 Support",               url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="❌ Cancel",                callback_data="my_offer_forex")],
    ])

def forex_offer_payment_instructions_page2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 CHECK MY SCREENSHOT",  callback_data="ofcheck_screenshot")],
        [InlineKeyboardButton(text="⬅️ Back to Page 1",       callback_data="ofpay_p1")],
        [InlineKeyboardButton(text="💬 Support",               url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="❌ Cancel",                callback_data="my_offer_forex")],
    ])


def forex_offer_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="my_offer_forex")]
    ])

# ── MM Buy Access Plans ────────────────────────────────────
def mm_buy_access_kb() -> InlineKeyboardMarkup:
    rows = []
    for pkg in MM_PACKAGES:
        rows.append([InlineKeyboardButton(
            text=f"{pkg['label']}  |  ${pkg['price']}  — PAY",
            callback_data=f"mm_pay_{pkg['id']}"
        )])
    rows.append([InlineKeyboardButton(
        text="Support (Free Access)",
        url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    )])
    rows.append([InlineKeyboardButton(text="Back", callback_data="open_mm_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mm_payment_instructions_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK MY SCREENSHOT", callback_data=f"mm_check_ss_{pkg_id}")],
        [InlineKeyboardButton(text="Support", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="Back", callback_data="mm_buy_access")],
    ])


def mm_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data="mm_buy_access")]
    ])


def mm_access_list_kb(users: list, page: int, total: int, per_page: int = 10, admin_id: int = None) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        uid   = u["user_id"]
        uname = f"@{u['username']}" if u.get("username") else f"ID {uid}"
        if uid == admin_id:
            rows.append([InlineKeyboardButton(
                text=f"🔒 {uname} — Admin",
                callback_data="mm_noop"
            )])
        else:
            rows.append([InlineKeyboardButton(
                text=f"❌ Remove {uname}",
                callback_data=f"mm_remove_{uid}"
            )])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"mm_list_page_{page - 1}"))
    total_pages = (total + per_page - 1) // per_page
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"mm_list_page_{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mm_remove_confirm_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Confirm Remove", callback_data=f"mm_confirm_remove_{user_id}")],
        [InlineKeyboardButton(text="Cancel", callback_data="admin_mm_list")],
    ])


# ── Aliases ────────────────────────────────────────────────
def cancel_kb() -> InlineKeyboardMarkup:
    return cancel_only_kb()

def main_menu_kb() -> InlineKeyboardMarkup:
    return paid_menu_kb()
