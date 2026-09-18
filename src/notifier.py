import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def clean_setting(name):
    value = os.getenv(name, "")
    return "".join(value.split())


def send_daily_email(questions):
    sender = clean_setting("GMAIL_ADDRESS")
    password = clean_setting("GMAIL_APP_PASSWORD")
    recipient = clean_setting("RECIPIENT_EMAIL")

    if not sender or not password or not recipient:
        raise ValueError(
            "Missing Gmail settings. Check the .env file."
        )

    content = [
        "Here are your three random LeetCode questions for today:",
        ""
    ]

    for number, question in enumerate(questions, start=1):
        content.extend([
            f"{number}. {question['title']}",
            f"Difficulty: {question['difficulty']}",
            f"Topic: {question['topic']}",
            f"Link: {question['url']}",
            ""
        ])

    content.append("Complete all three questions today!")

    message = EmailMessage()
    message["Subject"] = "Your Daily LeetCode Questions"
    message["From"] = sender
    message["To"] = recipient
    message.set_content("\n".join(content))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(message)

    print(f"Email sent successfully to {recipient}")
