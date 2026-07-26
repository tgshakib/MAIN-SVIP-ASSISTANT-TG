# 𝐒ꪜip Assistant™ — Telegram Bot

A multilingual binary trading money management Telegram bot.

---

## ⚡ Quick Deploy

### Railway
1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables (see below)
4. Deploy — done ✅

### Render
1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Background Worker
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add environment variables → Deploy ✅

### Koyeb
1. Push to GitHub
2. Go to [koyeb.com](https://koyeb.com) → Create App → GitHub
3. Builder: Buildpack, Run command: `python bot.py`
4. Add environment variables → Deploy ✅

### VPS / Any Linux Server
```bash
git clone <your-repo>
cd <your-repo>
pip install -r requirements.txt
# Set environment variables, then:
python bot.py
```

---

## 🔑 Required Environment Variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `ADMIN_ID` | Your Telegram user ID (numeric) |
| `GROUP_ID` | Your Telegram group/channel ID |
| `SESSION_SECRET` | Any random secret string |

---

## 📁 Project Structure

```
bot.py              — Entry point
config.py           — All configuration & payment addresses
keyboards.py        — All Telegram inline keyboards
handlers/           — All bot command & callback handlers
strategies/         — MM strategy logic
locales/            — 20-language translation files
scheduler.py        — Subscription reminder scheduler
database.py         — SQLite database helpers
```

---

## 🐍 Python Version
Requires Python 3.11+
