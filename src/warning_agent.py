import argparse
import math
from datetime import date

from notifier import send_warning_email
from plan_config import DEADLINE
from progress_tracker import (
    get_question_record,
    get_today_assignment,
    get_today_questions,
    load_tracker,
    save_tracker,
    sync_leetcode_progress
)
from question_selector import load_questions


ACTIVE_STATUSES = {
    "started",
    "attempted",
    "solved",
    "solved_with_help",
    "solved_independently",
    "reviewed",
    "mastered",
    "retry"
}


from datetime import date, datetime
from zoneinfo import ZoneInfo


AGENT_START_DATE = date(2026, 9, 22)


def main():
    local_today = datetime.now(
        ZoneInfo("America/Los_Angeles")
    ).date()

    if local_today < AGENT_START_DATE:
        print(
            f"Agent begins on {AGENT_START_DATE.isoformat()}. "
            f"Today is {local_today.isoformat()}, so no email was sent."
        )
        return
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--warning",
        type=int,
        choices=[1, 2],
        required=True
    )

    arguments = parser.parse_args()

    question_bank = load_questions()
    tracker = load_tracker()

    tracker = sync_leetcode_progress(
        tracker,
        question_bank
    )

    assignment = get_today_assignment(tracker)

    if not assignment:
        print("No assignment exists for today.")
        return

    warning_key = (
        "warning_one_sent"
        if arguments.warning == 1
        else "warning_two_sent"
    )

    if assignment.get(warning_key):
        print("Warning already sent.")
        return

    today_questions = get_today_questions(
        tracker,
        question_bank
    )

    activity_detected = any(
        get_question_record(
            tracker,
            question["id"]
        )["status"] in ACTIVE_STATUSES
        for question in today_questions
    )

    if activity_detected:
        print("Activity detected. Warning suppressed.")
        return

    completed_statuses = {
        "solved",
        "solved_with_help",
        "solved_independently",
        "reviewed",
        "mastered"
    }

    completed = sum(
        record["status"] in completed_statuses
        for record in tracker["question_progress"].values()
    )

    remaining = max(191 - completed, 0)

    days_remaining = max(
        (DEADLINE - date.today()).days + 1,
        1
    )

    required_daily_pace = math.ceil(
        remaining / days_remaining
    )

    send_warning_email(
        today_questions,
        arguments.warning,
        days_remaining,
        remaining,
        required_daily_pace
    )

    assignment[warning_key] = True
    assignment[
        f"{warning_key}_at"
    ] = date.today().isoformat()

    save_tracker(tracker)

    print(f"Warning {arguments.warning} sent.")


if __name__ == "__main__":
    main()
