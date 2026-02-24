# SundayPrep Automation

SundayPrep is a lightweight Python automation that prepares a weekly church briefing by combining:

- the latest church newsletter from Gmail,
- a Sunday weather snapshot for Abbotsford, BC,
- an LLM-generated summary via Groq,
- and Telegram delivery for fast team access.

## Key Features

- **Automated newsletter retrieval** from Gmail using IMAP.
- **Structured AI summary generation** using a reusable prompt template in `prompt.txt`.
- **Weather context enrichment** from Open-Meteo.
- **Telegram push notifications** using Bot API markdown formatting.
- **Scheduled execution** via GitHub Actions every Sunday (plus manual trigger support).

## How It Works

1. `get_latest_newsletter()` logs into Gmail and fetches the most recent email with subject:
	`Downes Road Weekly Newsletter`.
2. `get_abbotsford_weather()` requests the current forecast window from Open-Meteo.
3. `summarize_with_groq()` injects newsletter + weather context into `prompt.txt` and calls Groq Chat Completions.
4. `send_telegram()` posts the generated briefing to the configured Telegram chat.

## Project Structure

```text
Automations/
├─ main.py                      # Core automation workflow
├─ prompt.txt                   # Prompt template for LLM summarization
├─ requirements.txt             # Python dependencies
└─ .github/workflows/
	└─ sunday_run.yml            # Scheduled and manual GitHub Actions workflow
```

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Gmail account with IMAP enabled
- Gmail app password
- Groq API key
- Telegram bot token and target chat ID

## Installation

From the `Automations` directory:

```bash
pip install -r requirements.txt
```

## Environment Variables

Set the following values before running:

- `GROQ_API_KEY` – Groq API key
- `GMAIL_USER` – Gmail address used for IMAP login
- `GMAIL_PASS` – Gmail app password
- `TELEGRAM_TOKEN` – Telegram bot token
- `TELEGRAM_CHAT_ID` – Telegram chat/channel ID

### PowerShell example

```powershell
$env:GROQ_API_KEY="your-groq-api-key"
$env:GMAIL_USER="your-email@gmail.com"
$env:GMAIL_PASS="your-gmail-app-password"
$env:TELEGRAM_TOKEN="your-bot-token"
$env:TELEGRAM_CHAT_ID="your-chat-id"
```

## Run Locally

```bash
python main.py
```

Expected console flow:

- `🚀 SundayPrep Started...`
- `✅ Telegram notification sent!` (on success)
- `❌ No newsletter found.` (if no matching email is available)

## GitHub Actions Automation

Workflow: `.github/workflows/sunday_run.yml`

- **Schedule:** `30 18 * * 0` (Sundays at 18:30 UTC)
- **Manual run:** supported via `workflow_dispatch`
- **Runner:** `ubuntu-latest`
- **Python:** `3.12`

Configure these GitHub secrets:

- `GROQ_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`

## Prompt Customization

Edit `prompt.txt` to change briefing style, tone, or output format without modifying code.

## Troubleshooting

- **Gmail login fails:** verify IMAP is enabled and app password is correct.
- **No newsletter found:** confirm exact subject line match in inbox.
- **Telegram message fails:** validate bot token, chat ID, and bot permissions.
- **LLM request errors:** verify Groq key and API availability.

## Notes

- This project currently uses the `llama-3.3-70b-versatile` model via Groq.
- Keep all API keys and credentials in environment variables or GitHub Secrets (never commit them).
