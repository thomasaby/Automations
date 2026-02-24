# SundayPrep - Church Newsletter Automation

An automated workflow that fetches the latest church newsletter, generates an AI-powered summary of key points, and delivers it to Telegram.

## What It Does

This project automates the Sunday service preparation process by:

1. **Fetching Newsletters**: Connects to Gmail via IMAP to retrieve the latest "Downes Road Weekly Newsletter"
2. **AI Summarization**: Uses Google's Gemini API to extract scripture references and sermon points, condensing the newsletter into 3 concise sentences
3. **Telegram Notifications**: Sends the summary to a Telegram chat, making it easily accessible for quick reference

## Tech Stack

- **Language**: Python 3
- **Email Integration**: `imaplib` (Gmail IMAP protocol)
- **AI Summarization**: [Google GenAI SDK](https://github.com/google/generative-ai-python) with Gemini 1.5 Flash model
- **Notifications**: Telegram Bot API via `requests` library
- **Automation**: GitHub Actions (configured in `.github/workflows/`)

## Setup

### Prerequisites

- Python 3.7+
- Gmail account with app-specific password
- Google Gemini API key
- Telegram bot token and chat ID

### Installation

1. Clone the repository:

```bash
git clone https://github.com/thomasaby/Automations.git
cd Automations
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

```bash
export GMAIL_USER="your-email@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"
export GEMINI_API_KEY="your-gemini-api-key"
export TELEGRAM_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### Running Locally

```bash
python main.py
```

## How It Works

### 1. Newsletter Retrieval (`get_latest_newsletter()`)

- Connects to Gmail using IMAP over SSL
- Searches for emails with subject "Downes Road Weekly Newsletter"
- Extracts and returns the plain text body of the latest email

### 2. Summarization (`summarize_with_gemini()`)

- Sends newsletter content to Google's Gemini API
- Prompts the model to extract scripture references and sermon points
- Returns a 3-sentence summary

### 3. Notification (`send_telegram_notification()`)

- Formats the summary with markdown styling
- Posts the message to Telegram using the Bot API

## GitHub Actions

The workflow in `.github/workflows/sunday_run.yml` automates this script to run on a schedule, fetching and summarizing newsletters automatically.

## License

MIT
