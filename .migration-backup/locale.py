import json
import os
import math
from functools import lru_cache
import mm_database as mmdb

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")
VALID_LANGS = {
    "bn", "en", "hi", "ar", "es", "fr", "pt", "ru", "tr", "id",
    "zh", "ja", "ko", "de", "it", "tl", "vi", "th", "ur", "ha"
}


@lru_cache(maxsize=30)
def _load_locale(lang: str) -> dict:
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    if not os.path.exists(path):
        path = os.path.join(LOCALES_DIR, "en.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def t(user_id: int, key: str, **kwargs) -> str:
    """Get translated string for user's language."""
    lang = mmdb.get_user_language(user_id)
    data = _load_locale(lang)
    if key not in data:
        data = _load_locale("en")
    text = data.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def t_lang(lang: str, key: str, **kwargs) -> str:
    """Get translated string for a specific language code."""
    data = _load_locale(lang)
    if key not in data:
        data = _load_locale("en")
    text = data.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def round_amount(amount: float, cent_account: bool) -> float:
    """Apply cent or standard rounding to a trade amount."""
    if cent_account:
        return round(amount, 2)
    decimal_part = amount - math.floor(amount)
    if decimal_part < 0.50:
        return float(math.floor(amount))
    else:
        return float(math.ceil(amount))


def format_amount(amount: float, cent_account: bool) -> str:
    """Format amount for display."""
    rounded = round_amount(amount, cent_account)
    if cent_account:
        return f"{rounded:.2f}"
    return f"{rounded:.2f}"


def calculate_base_amount(capital: float, accuracy: float, payout: float,
                           stop_loss: float, mode_num: int) -> float:
    """Calculate the base trade amount using Kelly Criterion with safety caps."""
    win_rate = accuracy / 100
    loss_rate = 1 - win_rate
    payout_rate = payout / 100

    # Modified Kelly Criterion
    if payout_rate > 0:
        kelly = (win_rate * payout_rate - loss_rate) / payout_rate
    else:
        kelly = 0.02
    kelly = max(0.01, min(kelly, 0.05))

    base = capital * kelly

    # Mode-specific safety caps to avoid blowing stop_loss
    safety_divisors = {
        1: 4,    # Regular — same until win, then 2x
        2: 3,    # 1-step: 1+2=3x worst
        3: 7,    # 2-step: 1+2+4=7x worst
        4: 15,   # 3-step: 1+2+4+8=15x worst
        5: 7,    # Martingale: 3 doublings = 1+2+4=7x
        6: 3,    # Oscar's Grind (slow increase)
        7: 1,    # Anti-martingale (grows on wins, safe capital)
        8: 1,    # Flat bet (no progression)
        9: 8,    # Fibonacci: fib[5]=8
        10: 5,   # D'Alembert: gentle increase
    }
    divisor = safety_divisors.get(mode_num, 3)
    safe_max = stop_loss / max(divisor, 1)
    base = min(base, safe_max)

    return max(0.10, base)


# ── Per-language trade UI labels ─────────────────────────────
_LABELS_EN = {
    "enter_amount":       "ENTER THIS AMOUNT",
    "capital":            "Capital",
    "balance":            "Balance",
    "wins":               "Wins",
    "losses":             "Losses",
    "trades":             "Trades",
    "win_rate":           "Win Rate",
    "profit":             "Profit",
    "stop_loss":          "Stop Loss",
    "target":             "Target",
    "trade":              "TRADE",
    "stop_loss_reached":  "STOP LOSS REACHED",
    "congratulations":    "CONGRATULATIONS",
    "session_closed":     "Session Closed",
    "closed_safety":      "Session closed for your safety.",
    "smarter_risk":       "Smarter risk management — DM Support.",
}

_LABELS = {
    "ar": {
        "enter_amount":       "أدخل هذا المبلغ",
        "capital":            "رأس المال",
        "balance":            "الرصيد",
        "wins":               "انتصارات",
        "losses":             "خسائر",
        "trades":             "صفقات",
        "win_rate":           "نسبة الفوز",
        "profit":             "الربح",
        "stop_loss":          "وقف الخسارة",
        "target":             "الهدف",
        "trade":              "صفقة",
        "stop_loss_reached":  "🛑 وقف الخسارة مُفعَّل",
        "congratulations":    "🎉 تهانينا",
        "session_closed":     "🔒 الجلسة مغلقة",
        "closed_safety":      "تم إغلاق الجلسة لحمايتك.",
        "smarter_risk":       "راسل فريق الدعم للحصول على مساعدة.",
    },
    "bn": {
        "enter_amount":       "এই পরিমাণ লিখুন",
        "capital":            "মূলধন",
        "balance":            "ব্যালেন্স",
        "wins":               "জয়",
        "losses":             "হার",
        "trades":             "ট্রেড",
        "win_rate":           "জয়ের হার",
        "profit":             "মুনাফা",
        "stop_loss":          "স্টপ লস",
        "target":             "লক্ষ্য",
        "trade":              "ট্রেড",
        "stop_loss_reached":  "🛑 স্টপ লস হিট হয়েছে",
        "congratulations":    "🎉 অভিনন্দন",
        "session_closed":     "🔒 সেশন বন্ধ",
        "closed_safety":      "আপনার সুরক্ষায় সেশন বন্ধ করা হয়েছে।",
        "smarter_risk":       "সাপোর্ট টিমকে DM করুন।",
    },
    "de": {
        "enter_amount":       "DIESEN BETRAG EINGEBEN",
        "capital":            "Kapital",
        "balance":            "Guthaben",
        "wins":               "Gewinne",
        "losses":             "Verluste",
        "trades":             "Trades",
        "win_rate":           "Gewinnrate",
        "profit":             "Gewinn",
        "stop_loss":          "Stop-Loss",
        "target":             "Ziel",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP-LOSS ERREICHT",
        "congratulations":    "🎉 HERZLICHEN GLÜCKWUNSCH",
        "session_closed":     "🔒 Sitzung geschlossen",
        "closed_safety":      "Sitzung zu Ihrem Schutz geschlossen.",
        "smarter_risk":       "Support-Team kontaktieren.",
    },
    "es": {
        "enter_amount":       "INGRESAR ESTE MONTO",
        "capital":            "Capital",
        "balance":            "Saldo",
        "wins":               "Ganancias",
        "losses":             "Pérdidas",
        "trades":             "Trades",
        "win_rate":           "Tasa de acierto",
        "profit":             "Ganancia",
        "stop_loss":          "Stop Loss",
        "target":             "Objetivo",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS ALCANZADO",
        "congratulations":    "🎉 FELICITACIONES",
        "session_closed":     "🔒 Sesión cerrada",
        "closed_safety":      "Sesión cerrada por tu seguridad.",
        "smarter_risk":       "Contacta al equipo de soporte.",
    },
    "fr": {
        "enter_amount":       "SAISIR CE MONTANT",
        "capital":            "Capital",
        "balance":            "Solde",
        "wins":               "Gains",
        "losses":             "Pertes",
        "trades":             "Trades",
        "win_rate":           "Taux de réussite",
        "profit":             "Profit",
        "stop_loss":          "Stop Loss",
        "target":             "Objectif",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS ATTEINT",
        "congratulations":    "🎉 FÉLICITATIONS",
        "session_closed":     "🔒 Session fermée",
        "closed_safety":      "Session fermée pour votre sécurité.",
        "smarter_risk":       "Contactez le support.",
    },
    "ha": {
        "enter_amount":       "SHIGAR DA ADADIN KUƊI",
        "capital":            "Jari",
        "balance":            "Ma'auni",
        "wins":               "Nasara",
        "losses":             "Asara",
        "trades":             "Ciniki",
        "win_rate":           "Adadin nasara",
        "profit":             "Riba",
        "stop_loss":          "Tsayawa Loss",
        "target":             "Manufa",
        "trade":              "CINIKI",
        "stop_loss_reached":  "🛑 STOP LOSS YA ISO",
        "congratulations":    "🎉 TAYA MURNA",
        "session_closed":     "🔒 Zama ya ƙare",
        "closed_safety":      "Zama ya ƙare don kare ku.",
        "smarter_risk":       "Tuntuɓi ƙungiyar tallafi.",
    },
    "hi": {
        "enter_amount":       "यह राशि डालें",
        "capital":            "पूंजी",
        "balance":            "शेष",
        "wins":               "जीत",
        "losses":             "हार",
        "trades":             "ट्रेड",
        "win_rate":           "जीत दर",
        "profit":             "लाभ",
        "stop_loss":          "स्टॉप लॉस",
        "target":             "लक्ष्य",
        "trade":              "ट्रेड",
        "stop_loss_reached":  "🛑 स्टॉप लॉस हिट हुआ",
        "congratulations":    "🎉 बधाई हो",
        "session_closed":     "🔒 सत्र बंद",
        "closed_safety":      "सुरक्षा के लिए सत्र बंद किया गया।",
        "smarter_risk":       "सपोर्ट टीम को DM करें।",
    },
    "id": {
        "enter_amount":       "MASUKKAN JUMLAH INI",
        "capital":            "Modal",
        "balance":            "Saldo",
        "wins":               "Menang",
        "losses":             "Kalah",
        "trades":             "Trade",
        "win_rate":           "Tingkat menang",
        "profit":             "Profit",
        "stop_loss":          "Stop Loss",
        "target":             "Target",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS TERCAPAI",
        "congratulations":    "🎉 SELAMAT",
        "session_closed":     "🔒 Sesi ditutup",
        "closed_safety":      "Sesi ditutup untuk keamanan Anda.",
        "smarter_risk":       "Hubungi tim dukungan.",
    },
    "it": {
        "enter_amount":       "INSERIRE QUESTO IMPORTO",
        "capital":            "Capitale",
        "balance":            "Saldo",
        "wins":               "Vincite",
        "losses":             "Perdite",
        "trades":             "Trade",
        "win_rate":           "Tasso di vincita",
        "profit":             "Profitto",
        "stop_loss":          "Stop Loss",
        "target":             "Obiettivo",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS RAGGIUNTO",
        "congratulations":    "🎉 CONGRATULAZIONI",
        "session_closed":     "🔒 Sessione chiusa",
        "closed_safety":      "Sessione chiusa per la tua sicurezza.",
        "smarter_risk":       "Contatta il team di supporto.",
    },
    "ja": {
        "enter_amount":       "この金額を入力",
        "capital":            "資本金",
        "balance":            "残高",
        "wins":               "勝利",
        "losses":             "敗北",
        "trades":             "取引",
        "win_rate":           "勝率",
        "profit":             "利益",
        "stop_loss":          "損切り",
        "target":             "目標",
        "trade":              "取引",
        "stop_loss_reached":  "🛑 ストップロス到達",
        "congratulations":    "🎉 おめでとう",
        "session_closed":     "🔒 セッション終了",
        "closed_safety":      "安全のためセッションを終了しました。",
        "smarter_risk":       "サポートチームにDMしてください。",
    },
    "ko": {
        "enter_amount":       "이 금액을 입력",
        "capital":            "자본",
        "balance":            "잔액",
        "wins":               "승리",
        "losses":             "손실",
        "trades":             "거래",
        "win_rate":           "승률",
        "profit":             "수익",
        "stop_loss":          "손절매",
        "target":             "목표",
        "trade":              "거래",
        "stop_loss_reached":  "🛑 손절매 도달",
        "congratulations":    "🎉 축하합니다",
        "session_closed":     "🔒 세션 종료",
        "closed_safety":      "안전을 위해 세션이 종료되었습니다.",
        "smarter_risk":       "지원팀에 DM하세요.",
    },
    "pt": {
        "enter_amount":       "INSERIR ESTE VALOR",
        "capital":            "Capital",
        "balance":            "Saldo",
        "wins":               "Ganhos",
        "losses":             "Perdas",
        "trades":             "Trades",
        "win_rate":           "Taxa de acerto",
        "profit":             "Lucro",
        "stop_loss":          "Stop Loss",
        "target":             "Meta",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS ATINGIDO",
        "congratulations":    "🎉 PARABÉNS",
        "session_closed":     "🔒 Sessão encerrada",
        "closed_safety":      "Sessão encerrada para sua segurança.",
        "smarter_risk":       "Entre em contato com o suporte.",
    },
    "ru": {
        "enter_amount":       "ВВЕДИТЕ СУММУ",
        "capital":            "Капитал",
        "balance":            "Баланс",
        "wins":               "Победы",
        "losses":             "Поражения",
        "trades":             "Сделки",
        "win_rate":           "% побед",
        "profit":             "Прибыль",
        "stop_loss":          "Стоп-лосс",
        "target":             "Цель",
        "trade":              "СДЕЛКА",
        "stop_loss_reached":  "🛑 СТОП-ЛОСС ДОСТИГНУТ",
        "congratulations":    "🎉 ПОЗДРАВЛЯЕМ",
        "session_closed":     "🔒 Сессия закрыта",
        "closed_safety":      "Сессия закрыта для вашей защиты.",
        "smarter_risk":       "Напишите команде поддержки.",
    },
    "th": {
        "enter_amount":       "ใส่จำนวนเงินนี้",
        "capital":            "ทุน",
        "balance":            "ยอดเงิน",
        "wins":               "ชนะ",
        "losses":             "แพ้",
        "trades":             "เทรด",
        "win_rate":           "อัตราชนะ",
        "profit":             "กำไร",
        "stop_loss":          "สตอปลอส",
        "target":             "เป้าหมาย",
        "trade":              "เทรด",
        "stop_loss_reached":  "🛑 สตอปลอสถูกกระตุ้น",
        "congratulations":    "🎉 ยินดีด้วย",
        "session_closed":     "🔒 ปิดเซสชันแล้ว",
        "closed_safety":      "ปิดเซสชันเพื่อความปลอดภัยของคุณ",
        "smarter_risk":       "ติดต่อทีมสนับสนุน",
    },
    "tl": {
        "enter_amount":       "ILAGAY ANG HALAGANG ITO",
        "capital":            "Kapital",
        "balance":            "Balanse",
        "wins":               "Panalo",
        "losses":             "Talo",
        "trades":             "Trades",
        "win_rate":           "Antas ng panalo",
        "profit":             "Kita",
        "stop_loss":          "Stop Loss",
        "target":             "Target",
        "trade":              "TRADE",
        "stop_loss_reached":  "🛑 STOP LOSS NAABOT",
        "congratulations":    "🎉 BINABATI KITA",
        "session_closed":     "🔒 Sarado ang sesyon",
        "closed_safety":      "Sarado ang sesyon para sa iyong kaligtasan.",
        "smarter_risk":       "Makipag-ugnayan sa support.",
    },
    "tr": {
        "enter_amount":       "BU MİKTARI GİR",
        "capital":            "Sermaye",
        "balance":            "Bakiye",
        "wins":               "Kazançlar",
        "losses":             "Kayıplar",
        "trades":             "İşlemler",
        "win_rate":           "Kazanma oranı",
        "profit":             "Kâr",
        "stop_loss":          "Zarar Durdur",
        "target":             "Hedef",
        "trade":              "İŞLEM",
        "stop_loss_reached":  "🛑 ZARAR DURDUR DEVREDE",
        "congratulations":    "🎉 TEBRİKLER",
        "session_closed":     "🔒 Oturum kapatıldı",
        "closed_safety":      "Güvenliğiniz için oturum kapatıldı.",
        "smarter_risk":       "Destek ekibiyle iletişime geçin.",
    },
    "ur": {
        "enter_amount":       "یہ رقم درج کریں",
        "capital":            "سرمایہ",
        "balance":            "بیلنس",
        "wins":               "جیت",
        "losses":             "ہار",
        "trades":             "ٹریڈ",
        "win_rate":           "جیت کی شرح",
        "profit":             "منافع",
        "stop_loss":          "سٹاپ لاس",
        "target":             "ہدف",
        "trade":              "ٹریڈ",
        "stop_loss_reached":  "🛑 سٹاپ لاس فعال ہوا",
        "congratulations":    "🎉 مبارکباد",
        "session_closed":     "🔒 سیشن بند",
        "closed_safety":      "آپ کی حفاظت کے لیے سیشن بند کیا گیا۔",
        "smarter_risk":       "سپورٹ ٹیم کو DM کریں۔",
    },
    "vi": {
        "enter_amount":       "NHẬP SỐ TIỀN NÀY",
        "capital":            "Vốn",
        "balance":            "Số dư",
        "wins":               "Thắng",
        "losses":             "Thua",
        "trades":             "Lệnh",
        "win_rate":           "Tỷ lệ thắng",
        "profit":             "Lợi nhuận",
        "stop_loss":          "Cắt lỗ",
        "target":             "Mục tiêu",
        "trade":              "LỆNH",
        "stop_loss_reached":  "🛑 CẮT LỖ ĐÃ KÍCH HOẠT",
        "congratulations":    "🎉 CHÚC MỪNG",
        "session_closed":     "🔒 Phiên đã đóng",
        "closed_safety":      "Phiên đã đóng để bảo vệ bạn.",
        "smarter_risk":       "Liên hệ đội hỗ trợ.",
    },
    "zh": {
        "enter_amount":       "输入此金额",
        "capital":            "资本",
        "balance":            "余额",
        "wins":               "盈利",
        "losses":             "亏损",
        "trades":             "交易",
        "win_rate":           "胜率",
        "profit":             "利润",
        "stop_loss":          "止损",
        "target":             "目标",
        "trade":              "交易",
        "stop_loss_reached":  "🛑 止损已触发",
        "congratulations":    "🎉 恭喜",
        "session_closed":     "🔒 交易结束",
        "closed_safety":      "为保护您的账户，交易已关闭。",
        "smarter_risk":       "联系客服团队。",
    },
}


def get_labels(lang: str) -> dict:
    """Return translated UI labels for the given language, falling back to English."""
    base = dict(_LABELS_EN)
    if lang and lang != "en" and lang in _LABELS:
        base.update(_LABELS[lang])
    return base
