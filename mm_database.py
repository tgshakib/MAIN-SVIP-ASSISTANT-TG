import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

DB_PATH = os.environ.get("DB_PATH", "mm_bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_mm_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mm_users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT,
            language        TEXT DEFAULT 'en',
            mm_access_type  TEXT DEFAULT 'free',
            mm_expires_at   TEXT,
            daily_sessions  INTEGER DEFAULT 0,
            daily_date      TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS mm_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            status          TEXT DEFAULT 'active',
            mode_num        INTEGER NOT NULL,
            mode_name       TEXT NOT NULL,
            capital         REAL NOT NULL,
            balance         REAL NOT NULL,
            payout_pct      REAL NOT NULL,
            stop_loss       REAL NOT NULL,
            session_target  REAL NOT NULL,
            daily_target    REAL NOT NULL,
            overall_target  REAL NOT NULL,
            total_trades    INTEGER DEFAULT 0,
            trades_planned  INTEGER DEFAULT 10,
            wins_needed     INTEGER DEFAULT 6,
            cent_account    INTEGER DEFAULT 0,
            base_amount     REAL NOT NULL,
            current_amount  REAL NOT NULL,
            mode_state      TEXT DEFAULT '{}',
            wins            INTEGER DEFAULT 0,
            losses          INTEGER DEFAULT 0,
            trade_number    INTEGER DEFAULT 1,
            profit          REAL DEFAULT 0.0,
            created_at      TEXT DEFAULT (datetime('now')),
            closed_at       TEXT,
            FOREIGN KEY (user_id) REFERENCES mm_users(user_id)
        );

        CREATE TABLE IF NOT EXISTS mm_trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            user_id     INTEGER NOT NULL,
            trade_num   INTEGER NOT NULL,
            result      TEXT NOT NULL,
            amount      REAL NOT NULL,
            profit_loss REAL NOT NULL,
            balance_after REAL NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES mm_sessions(id)
        );
        """)
    print("✅ MM Database initialized.")


# ── Language helpers ────────────────────────────────────────
def get_user_language(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT language FROM mm_users WHERE user_id=?", (user_id,)).fetchone()
        return row["language"] if row else "en"


def set_user_language(user_id: int, lang: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO mm_users (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
        """, (user_id, lang))


# ── MM User helpers ─────────────────────────────────────────
def upsert_mm_user(user_id: int, username: str = ""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO mm_users (user_id, username)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
        """, (user_id, username or ""))


def get_mm_user(user_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM mm_users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_mm_access(user_id: int) -> str:
    """Returns 'free', 'premium', or 'lifetime'."""
    user = get_mm_user(user_id)
    if not user:
        return "free"
    access_type = user.get("mm_access_type", "free")
    if access_type == "free":
        return "free"
    if access_type == "lifetime":
        return "lifetime"
    expires_at = user.get("mm_expires_at")
    if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
        return "premium"
    return "free"


def is_mm_premium(user_id: int) -> bool:
    return get_mm_access(user_id) in ("premium", "lifetime")


def grant_mm_access(user_id: int, duration_str: str) -> Optional[str]:
    """
    Grant MM access. Returns expiry string or None on failure.
    duration_str examples: '7', '14', '1month', '3month', 'lifetime'
    """
    duration_str = duration_str.strip().lower()
    now = datetime.now()

    if duration_str == "lifetime":
        expires_at = None
        access_type = "lifetime"
        expiry_display = "Lifetime ♾️"
    elif duration_str.endswith("month"):
        try:
            months = int(duration_str.replace("month", ""))
            expires_at = (now + timedelta(days=months * 30)).isoformat()
            access_type = "premium"
            expiry_display = (now + timedelta(days=months * 30)).strftime("%d %b %Y %H:%M UTC")
        except ValueError:
            return None
    else:
        try:
            days = int(duration_str)
            expires_at = (now + timedelta(days=days)).isoformat()
            access_type = "premium"
            expiry_display = (now + timedelta(days=days)).strftime("%d %b %Y %H:%M UTC")
        except ValueError:
            return None

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO mm_users (user_id, mm_access_type, mm_expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                mm_access_type=excluded.mm_access_type,
                mm_expires_at=excluded.mm_expires_at
        """, (user_id, access_type, expires_at))

    return expiry_display


def get_user_by_username(username: str) -> Optional[Dict]:
    username = username.lstrip("@").lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM mm_users WHERE LOWER(username)=?", (username,)
        ).fetchone()
        return dict(row) if row else None


# ── Free session counter ────────────────────────────────────
def can_start_free_session(user_id: int) -> bool:
    """Returns True if free user can start a session today."""
    user = get_mm_user(user_id)
    if not user:
        return True
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if user.get("daily_date") != today:
        return True
    return user.get("daily_sessions", 0) < 1


def increment_free_session(user_id: int):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_conn() as conn:
        user = get_mm_user(user_id)
        if user and user.get("daily_date") == today:
            conn.execute(
                "UPDATE mm_users SET daily_sessions=daily_sessions+1 WHERE user_id=?",
                (user_id,)
            )
        else:
            conn.execute(
                "UPDATE mm_users SET daily_sessions=1, daily_date=? WHERE user_id=?",
                (today, user_id)
            )


def reset_free_sessions():
    """Called by scheduler at midnight UTC."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_conn() as conn:
        conn.execute(
            "UPDATE mm_users SET daily_sessions=0, daily_date=? WHERE mm_access_type='free'",
            (today,)
        )
    print("✅ Free session counters reset.")


def grant_admin_lifetime_access(admin_ids: list):
    """Grant lifetime MM access to all admin IDs. Called on bot startup."""
    for admin_id in admin_ids:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO mm_users (user_id, username, mm_access_type, mm_expires_at)
                VALUES (?, 'admin', 'lifetime', NULL)
                ON CONFLICT(user_id) DO UPDATE SET
                    mm_access_type='lifetime',
                    mm_expires_at=NULL
            """, (admin_id,))
    print(f"✅ Admin lifetime MM access granted to {len(admin_ids)} admin(s).")


def get_all_mm_access_users(page: int = 1, per_page: int = 10) -> tuple:
    """Returns (list of users with active MM access, total_count)."""
    offset = (page - 1) * per_page
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM mm_users WHERE mm_access_type != 'free'"
        ).fetchone()[0]
        rows = conn.execute("""
            SELECT * FROM mm_users
            WHERE mm_access_type != 'free'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset)).fetchall()
        return [dict(r) for r in rows], total


def remove_mm_access(user_id: int):
    """Remove MM access from a user, setting them back to free."""
    with get_conn() as conn:
        conn.execute("""
            UPDATE mm_users SET mm_access_type='free', mm_expires_at=NULL
            WHERE user_id=?
        """, (user_id,))


# ── Session helpers ─────────────────────────────────────────
def create_session(user_id: int, data: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO mm_sessions (
                user_id, mode_num, mode_name, capital, balance,
                payout_pct, stop_loss, session_target, daily_target,
                overall_target, total_trades, trades_planned, wins_needed,
                cent_account, base_amount, current_amount, mode_state
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            data["mode_num"],
            data["mode_name"],
            data["capital"],
            data["capital"],
            data["payout_pct"],
            data["stop_loss"],
            data["session_target"],
            data["daily_target"],
            data["overall_target"],
            0,
            data.get("trades_planned", 10),
            data.get("wins_needed", 6),
            1 if data.get("cent_account") else 0,
            data["base_amount"],
            data["current_amount"],
            json.dumps(data.get("mode_state", {}))
        ))
        return cur.lastrowid


def get_active_session(user_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM mm_sessions
            WHERE user_id=? AND status='active'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,)).fetchone()
        if row:
            d = dict(row)
            d["mode_state"] = json.loads(d.get("mode_state") or "{}")
            return d
        return None


def get_all_active_sessions(user_id: int) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM mm_sessions
            WHERE user_id=? AND status='active'
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["mode_state"] = json.loads(d.get("mode_state") or "{}")
            result.append(d)
        return result


def update_session_after_trade(session_id: int, result: str, amount: float,
                                profit_loss: float, new_balance: float,
                                new_amount: float, new_state: dict,
                                wins: int, losses: int, trade_number: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE mm_sessions SET
                balance=?, current_amount=?, mode_state=?,
                wins=?, losses=?, trade_number=?,
                profit=balance-capital,
                total_trades=total_trades+1
            WHERE id=?
        """, (
            new_balance, new_amount, json.dumps(new_state),
            wins, losses, trade_number, session_id
        ))
        conn.execute("""
            INSERT INTO mm_trades (session_id, user_id, trade_num, result, amount, profit_loss, balance_after)
            SELECT id, user_id, ?, ?, ?, ?, ?
            FROM mm_sessions WHERE id=?
        """, (trade_number - 1, result, amount, profit_loss, new_balance, session_id))


def close_session(session_id: int):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute("""
            UPDATE mm_sessions SET status='closed', closed_at=?,
            profit=balance-capital
            WHERE id=?
        """, (now, session_id))


def close_all_sessions(user_id: int):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute("""
            UPDATE mm_sessions SET status='closed', closed_at=?,
            profit=balance-capital
            WHERE user_id=? AND status='active'
        """, (now, user_id))


# Initialize on import
init_mm_db()
