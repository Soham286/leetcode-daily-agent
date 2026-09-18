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


def send_email(subject, content):
    sender = clean_setting("GMAIL_ADDRESS")
    password = clean_setting("GMAIL_APP_PASSWORD")
    recipient = clean_setting("RECIPIENT_EMAIL")

    if not sender or not password or not recipient:
        raise ValueError(
            "Missing Gmail settings."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(content)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:
        server.login(sender, password)
        server.send_message(message)

    print(f"Email sent successfully to {recipient}")


def send_daily_email(questions):
    new_count = sum(
        question.get("assignment_type") == "new"
        for question in questions
    )

    review_count = len(questions) - new_count

    lines = [
        "STRIVER SDE DAILY PRACTICE",
        "",
        f"Total questions today: {len(questions)}",
        f"New questions: {new_count}",
        f"Revision questions: {review_count}",
        "Deadline: October 31, 2026",
        ""
    ]

    for number, question in enumerate(
        questions,
        start=1
    ):
        lines.extend([
            f"{number}. {question['title']}",
            f"Topic: {question['topic']}",
            (
                "Type: "
                f"{question.get('assignment_type', 'new').title()}"
            ),
            (
                "Difficulty: "
                f"{question.get('difficulty', 'Unknown')}"
            ),
            f"Link: {question['url']}",
            ""
        ])

    lines.append(
        f"Complete all {len(questions)} questions today."
    )

    send_email(
        "Your Daily Striver SDE Questions",
        "\n".join(lines)
    )


def send_warning_email(
    questions,
    warning_number,
    days_remaining,
    questions_remaining,
    required_daily_pace
):
    pending = [
        question
        for question in questions
        if question.get("status") not in {
            "solved",
            "solved_independently",
            "reviewed",
            "mastered"
        }
    ]

    subject = (
        "DSA Warning 1: Practice still pending"
        if warning_number == 1
        else "DSA Final Warning: Protect your deadline"
    )

    lines = [
        f"Pending questions today: {len(pending)}",
        f"Questions remaining: {questions_remaining}",
        f"Days remaining: {days_remaining}",
        f"Required daily pace: {required_daily_pace}",
        ""
    ]

    for question in pending:
        lines.extend([
            f"- {question['title']}",
            f"  {question['url']}"
        ])

    send_email(subject, "\n".join(lines))


def send_weekly_email(content):
    send_email(
        "Your Weekly Striver SDE Progress Report",
        content
    )
