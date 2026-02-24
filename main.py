import os
import imaplib
import email
from google import genai
import requests

# Configuration from Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")  # Mapped to GMAIL_APP_PASSWORD in YAML
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Connects to Gmail and retrieves the plain text body of the newsletter."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Search for the specific church newsletter subject
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            print("Newsletter not found.")
            return None

        # Fetch the most recent message
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

def summarize_with_gemini(text):
    """Summarizes using the Gemini 3 Flash model (Latest as of Feb 2026)."""
    if not text:
        return "No content to summarize."

    print(f"DEBUG: Sending {len(text)} characters to Gemini 3 API.")
    
    # Initialize the modern SDK client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an assistant for a church member. Analyze this newsletter from Downes Road.
    1. Identify the primary Scripture reference mentioned for this week.
    2. Summarize the main sermon points or theme.
    Output: Provide exactly 3 concise sentences.
    
    Newsletter Content:
    {text}
    """
    
    try:
        # Use 'gemini-3-flash' - the current stable workhorse
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Could not generate AI summary. Check API logs."

def send_telegram_notification(message):
    """Sends the finalized summary to your Telegram phone bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📖 *SundayPrep Summary*:\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload).raise_for_status()
    except Exception as e:
        print(f"Telegram Dispatch Error: {e}")

def main():
    print("Initalizing SundayPrep...")
    content = get_latest_newsletter()
    
    if content:
        print("Generating AI Summary...")
        summary = summarize_with_gemini(content)
        
        print("Sending to Telegram...")
        send_telegram_notification(summary)
        print("Done!")
    else:
        print("Workflow aborted: No content found.")

if __name__ == "__main__":
    main()