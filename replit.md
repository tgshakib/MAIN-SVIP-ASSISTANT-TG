# Money Management Telegram Bot

A multilingual Telegram bot for binary trading money management. Handles VIP subscriptions, multiple money-management strategies (Martingale, Fibonacci, D'Alembert, Oscar's Grind, etc.), admin controls, scheduled reminders, forex calculator, and 20+ language support.

## Run & Operate

- `python bot.py` — start the Telegram bot (run via "Start application" workflow)
- Bot reads all config from environment variables / secrets — no hardcoded credentials

## Required Secrets

Set these in Replit Secrets before running:

- `BOT_TOKEN` — Telegram bot token from @BotFather
- `ADMIN_ID` — Telegram user ID of the admin
- `GROUP_ID` — Telegram group/channel ID for VIP members

## Optional Env Vars (have defaults)

- `SUPPORT_USERNAME` — support contact handle (default: `@JAYITAUTOBO`)
- `PAYMENT_INSTRUCTIONS` — payment details shown to users
- `FOREX_PAYMENT_INSTRUCTIONS` — forex payment details

## Stack

- Python 3.11
- aiogram 3.13 (async Telegram bot framework)
- aiosqlite for async SQLite access
- SQLite databases: `subscriptions.db` (SVIP/Forex subs) and `mm_bot.db` (MM access)
- Locales: 20 languages in `locales/`
- Strategies: 10 MM strategies in `strategies/`

## Where things live

- `bot.py` — entry point, registers all routers and starts polling
- `config.py` — all config loaded from env vars
- `database.py` — subscriptions/payments DB (subscriptions.db)
- `mm_database.py` — money management DB (mm_bot.db)
- `scheduler.py` — background renewal reminder scheduler
- `keyboards.py` — all aiogram inline keyboards
- `locale.py` — i18n helper, reads from `locales/*.json`
- `handlers/` — one router per feature area
- `strategies/` — MM strategy calculation modules

## Architecture decisions

- All secrets are environment variables — never hardcoded.
- Two separate SQLite databases: `subscriptions.db` for SVIP/Forex and `mm_bot.db` for MM access, keeping concerns separated.
- aiogram 3.x router pattern — each handler file registers its own Router.

## User preferences

_Populate as you build._

## Gotchas

- Do not run `pnpm dev` at workspace root — this is a Python bot, not a Node app.
- The `locales/` directory path is relative to `locale.py`; both must stay at the same level.
- `admin_msg_ids.json` and `user_settings.json` are runtime state files — commit with caution.
