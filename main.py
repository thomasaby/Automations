import os
import imaplib
import email
import requests

# GitHub Models Config
# Note: GitHub token is automatically provided by the workflow
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL_ID = "gemini-3-flash"  # Latest stable Flash model in Feb 2026
ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"

# Gmail & Telegram Config
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Retrieves the plain text body of the latest newsletter from Gmail."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            return None
        latest_id = messages[0].split()[-1]
        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            return part.get_payload(decode=True).decode()
                else:
                    return msg.get_payload(decode=True).decode()
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Gmail Error: {e}")
    return None

def summarize_with_github_models(text):
    """Uses GitHub Models REST API to summarize the content."""
    if not text:
        return "No content found."

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "Extract the scripture and sermon points. Provide a summary in exactly 3 concise sentences."},
            {"role": "user", "content": text}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"GitHub Models Error: {e}")
        return "AI Summary unavailable."

def send_telegram_notification(message):
    """Sends the summary to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"📖 *SundayPrep*:\n\n{message}", "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    print("Fetching newsletter...")
    content = get_latest_newsletter()
    if content:
        print(f"Summarizing with {MODEL_ID}...")
        summary = summarize_with_github_models(content)
        print("Sending to Telegram...")
        send_telegram_notification(summary)
        print("Done!")

if __name__ == "__main__":
    main()