import os
import imaplib
import email
from google import genai
import requests

# Configuration from Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")  # Mapped from GMAIL_APP_PASSWORD in YAML
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Connects to Gmail and retrieves the body of the latest newsletter."""
    try:
        if not GMAIL_USER or not GMAIL_PASS:
            print("Error: Gmail credentials missing from environment.")
            return None

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Search for the specific subject
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            print("No emails found matching the subject.")
            return None

        # Get the latest email ID from the search results
        latest_email_id = messages[0].split()[-1]
        res, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
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
        print(f"Error accessing Gmail: {e}")
    return None

def summarize_with_gemini(text):
    """Uses the modern Google GenAI SDK to summarize."""
    if not text:
        return "No content found in the newsletter."

    print(f"DEBUG: Sending {len(text)} characters to Gemini API.")
    
    # Initialize the modern client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    The following is a church newsletter. Extract the main scripture reference 
    and the primary sermon points. Provide a summary in exactly 3 concise sentences.
    
    Newsletter Content:
    {text}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Error generating summary."

def send_telegram_notification(message):
    """Sends the final summary to the Telegram bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📖 *SundayPrep Summary*:\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"Telegram Error: {e}")

def main():
    print("Fetching newsletter...")
    content = get_latest_newsletter()
    
    if content:
        print("Summarizing with AI...")
        summary = summarize_with_gemini(content)
        
        print("Sending notification...")
        send_telegram_notification(summary)
        print("Done! Check your Telegram.")
    else:
        print("Workflow stopped: No newsletter content found.")

if __name__ == "__main__":
    main()