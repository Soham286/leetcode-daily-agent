import math
from collections import Counter
from datetime import date, timedelta

from notifier import send_weekly_email
from plan_config import DEADLINE
from progress_tracker import (
    get_question_record,
    load_tracker,
    save_tracker,
    sync_leetcode_progress
)
from question_selector import load_questions


COMPLETED_STATUSES = {
    "solved",
    "solved_with_help",
    "solved_independently",
    "reviewed",
    "mastered"
}

INDEPENDENT_STATUSES = {
    "solved_independently",
    "reviewed",
    "mastered"
}

CONTEST_TARGET_DATE = date(2026, 10, 10)
CONTEST_MANDATORY_DATE = date(2026, 10, 17)


def calculate_contest_readiness(
    tracker,
    questions_by_id
):
    completed = []

    for question_id, record in tracker[
        "question_progress"
    ].items():
        if (
            question_id in questions_by_id
            and record["status"] in COMPLETED_STATUSES
        ):
            completed.append(record)

    completed_count = len(completed)

    independent_count = sum(
        record["status"] in INDEPENDENT_STATUSES
        for record in completed
    )

    independent_rate = (
        independent_count / completed_count
        if completed_count
        else 0
    )

    recent_assignments = tracker[
        "assignments"
    ][-2:]

    recent_ids = []

    for assignment in recent_assignments:
        for item in assignment["questions"]:
            if item["id"] not in recent_ids:
                recent_ids.append(item["id"])

    recent_ids = recent_ids[-10:]

    recent_completed = sum(
        get_question_record(
            tracker,
            question_id
        )["status"] in COMPLETED_STATUSES
        for question_id in recent_ids
    )

    backlog = sum(
        record["status"] in {
            "assigned",
            "started",
            "attempted",
            "retry"
        }
        for record in tracker[
            "question_progress"
        ].values()
    )

    normal_ready = (
        completed_count >= 75
        and independent_rate >= 0.65
        and recent_completed >= 7
        and backlog < 10
    )

    mandatory_ready = (
        date.today() >= CONTEST_MANDATORY_DATE
    )

    ready = normal_ready or mandatory_ready

    return {
        "ready": ready,
        "completed": completed_count,
        "independent_rate": independent_rate,
        "recent_completed": recent_completed,
        "backlog": backlog
    }


def main():
    question_bank = load_questions()
    questions_by_id = {
        question["id"]: question
        for question in question_bank
    }

    tracker = load_tracker()

    tracker = sync_leetcode_progress(
        tracker,
        question_bank
    )

    today = date.today()
    week_start = today - timedelta(days=6)

    weekly_assignments = [
        assignment
        for assignment in tracker["assignments"]
        if week_start
        <= date.fromisoformat(assignment["date"])
        <= today
    ]

    weekly_ids = []

    for assignment in weekly_assignments:
        for item in assignment["questions"]:
            if item["id"] not in weekly_ids:
                weekly_ids.append(item["id"])

    weekly_completed = []
    weekly_pending = []
    weekly_topics = Counter()

    for question_id in weekly_ids:
        question = questions_by_id.get(question_id)

        if not question:
            continue

        record = get_question_record(
            tracker,
            question_id
        )

        weekly_topics[question["topic"]] += 1

        if record["status"] in COMPLETED_STATUSES:
            weekly_completed.append(question)
        else:
            weekly_pending.append(question)

    weekly_total = len(weekly_ids)

    weekly_rate = (
        round(
            len(weekly_completed)
            / weekly_total
            * 100
        )
        if weekly_total
        else 0
    )

    total_completed = sum(
        record["status"] in COMPLETED_STATUSES
        for record in tracker[
            "question_progress"
        ].values()
    )

    total_mastered = sum(
        record["status"] == "mastered"
        for record in tracker[
            "question_progress"
        ].values()
    )

    total_retry = sum(
        record["status"] == "retry"
        for record in tracker[
            "question_progress"
        ].values()
    )

    remaining = max(191 - total_completed, 0)

    days_remaining = max(
        (DEADLINE - today).days + 1,
        1
    )

    required_pace = math.ceil(
        remaining / days_remaining
    )

    readiness = calculate_contest_readiness(
        tracker,
        questions_by_id
    )

    if readiness["ready"]:
        contest_message = (
            "READY: Participate in the next official "
            "LeetCode contest."
        )
    elif today < CONTEST_TARGET_DATE:
        contest_message = (
            "Not scheduled yet. Target readiness date: "
            "October 10."
        )
    else:
        contest_message = (
            "Continue preparation. Mandatory contest "
            "start date: October 17."
        )

    lines = [
        "WEEKLY STRIVER SDE PROGRESS REPORT",
        "=" * 48,
        "",
        f"Period: {week_start} to {today}",
        "",
        "WEEKLY RESULTS",
        f"Assigned: {weekly_total}",
        f"Completed: {len(weekly_completed)}",
        f"Pending: {len(weekly_pending)}",
        f"Completion rate: {weekly_rate}%",
        "",
        "OVERALL PROGRESS",
        f"Completed: {total_completed}/191",
        f"Remaining: {remaining}",
        f"Mastered: {total_mastered}",
        f"Retry queue: {total_retry}",
        "",
        "OCTOBER 31 DEADLINE",
        f"Days remaining: {days_remaining}",
        f"Required daily pace: {required_pace}",
        "",
        "CONTEST READINESS",
        contest_message,
        (
            "Independent solve rate: "
            f"{readiness['independent_rate']:.0%}"
        ),
        (
            "Recent assignments completed: "
            f"{readiness['recent_completed']}/10"
        ),
        f"Immediate backlog: {readiness['backlog']}",
        "",
        "TOPICS PRACTICED"
    ]

    if weekly_topics:
        for topic, count in weekly_topics.most_common():
            lines.append(f"- {topic}: {count}")
    else:
        lines.append("- No topics recorded")

    lines.extend([
        "",
        "PENDING QUESTIONS"
    ])

    if weekly_pending:
        for question in weekly_pending[:15]:
            lines.append(
                f"- {question['title']} "
                f"({question['topic']})"
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "NEXT WEEK",
        "- Maintain a maximum of five questions daily",
        "- Complete weak and pending questions",
        "- Continue the current sheet topic",
        "- Perform scheduled revision"
    ])

    send_weekly_email("\n".join(lines))
    save_tracker(tracker)

    print("Weekly report sent.")


if __name__ == "__main__":
    main()
