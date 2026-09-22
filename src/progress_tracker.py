import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from leetcode_api import get_recent_accepted_submissions
from plan_config import DEADLINE, REVIEW_INTERVALS, TIMEZONE


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKER_FILE = PROJECT_ROOT / "data" / "tracker.json"
LOCAL_TIMEZONE = ZoneInfo(TIMEZONE)


def now_local():
    return datetime.now(LOCAL_TIMEZONE)


def today_string():
    return now_local().date().isoformat()


def default_tracker():
    return {
        "version": 2,
        "goal": {
            "sheet": "Striver SDE Sheet",
            "total_questions": 191,
            "deadline": DEADLINE.isoformat()
        },
        "question_progress": {},
        "assignments": [],
        "contests": [],
        "reflections": []
    }


def load_tracker():
    if not TRACKER_FILE.exists():
        return default_tracker()

    try:
        with TRACKER_FILE.open("r", encoding="utf-8-sig") as file:
            tracker = json.load(file)
    except (json.JSONDecodeError, OSError):
        return default_tracker()

    if tracker.get("version") != 2:
        return default_tracker()

    tracker.setdefault("question_progress", {})
    tracker.setdefault("assignments", [])
    tracker.setdefault("contests", [])
    tracker.setdefault("reflections", [])
    return tracker


def save_tracker(tracker):
    with TRACKER_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            tracker,
            file,
            indent=2,
            ensure_ascii=False
        )


def get_question_record(tracker, question_id):
    records = tracker.setdefault("question_progress", {})

    if question_id not in records:
        records[question_id] = {
            "status": "not_started",
            "assigned_count": 0,
            "attempt_count": 0,
            "review_count": 0,
            "hint_used": False,
            "solution_viewed": False,
            "confidence": None,
            "time_minutes": None,
            "mistake": "",
            "pattern": "",
            "first_assigned_at": None,
            "last_assigned_at": None,
            "started_at": None,
            "solved_at": None,
            "last_reviewed_at": None,
            "next_review_on": None,
            "review_interval_index": 0
        }

    return records[question_id]


def get_today_assignment(tracker):
    today = today_string()

    for assignment in tracker["assignments"]:
        if assignment["date"] == today:
            return assignment

    return None


def get_today_questions(tracker, question_bank):
    assignment = get_today_assignment(tracker)

    if not assignment:
        return []

    questions_by_id = {
        question["id"]: question
        for question in question_bank
    }

    results = []

    for assigned_item in assignment["questions"]:
        question = questions_by_id.get(assigned_item["id"])

        if not question:
            continue

        combined = question.copy()
        combined["assignment_type"] = assigned_item["type"]

        record = get_question_record(
            tracker,
            assigned_item["id"]
        )

        combined["status"] = assigned_item.get(
            "status",
            record["status"]
        )
        results.append(combined)

    return results


def record_daily_assignment(tracker, selected_questions):
    timestamp = now_local().isoformat()
    assigned_items = []

    for question in selected_questions:
        question_id = question["id"]
        assignment_type = question.get(
            "assignment_type",
            "new"
        )

        record = get_question_record(
            tracker,
            question_id
        )

        if assignment_type == "new":
            if record["status"] == "not_started":
                record["status"] = "assigned"

            record["assigned_count"] += 1

            if not record["first_assigned_at"]:
                record["first_assigned_at"] = timestamp

            record["last_assigned_at"] = timestamp

        else:
            record["review_count"] += 1
            record["last_assigned_at"] = timestamp

        assigned_items.append({
            "id": question_id,
            "type": assignment_type,
            "status": "pending",
            "assigned_at": timestamp,
            "completed_at": None
        })

    assignment = {
        "date": today_string(),
        "created_at": timestamp,
        "questions": assigned_items,
        "daily_email_sent": False,
        "warning_one_sent": False,
        "warning_two_sent": False
    }

    tracker["assignments"].append(assignment)
    save_tracker(tracker)
    return assignment


def mark_daily_email_sent(tracker):
    assignment = get_today_assignment(tracker)

    if assignment:
        assignment["daily_email_sent"] = True
        assignment["daily_email_sent_at"] = (
            now_local().isoformat()
        )
        save_tracker(tracker)


def mark_started(tracker, question_id):
    record = get_question_record(tracker, question_id)

    if record["status"] in {
        "not_started",
        "assigned"
    }:
        record["status"] = "started"

    if not record["started_at"]:
        record["started_at"] = now_local().isoformat()

    save_tracker(tracker)


def record_attempt(
    tracker,
    question_id,
    solved=False,
    used_hint=False,
    viewed_solution=False,
    confidence=None,
    time_minutes=None,
    mistake="",
    pattern=""
):
    record = get_question_record(tracker, question_id)
    record["attempt_count"] += 1
    record["hint_used"] = bool(used_hint)
    record["solution_viewed"] = bool(viewed_solution)
    record["confidence"] = confidence
    record["time_minutes"] = time_minutes
    record["mistake"] = mistake
    record["pattern"] = pattern

    if solved:
        if used_hint or viewed_solution:
            record["status"] = "solved_with_help"
        else:
            record["status"] = "solved_independently"

        record["solved_at"] = now_local().isoformat()
        record["review_interval_index"] = 0
        record["next_review_on"] = (
            now_local().date()
            + timedelta(days=REVIEW_INTERVALS[0])
        ).isoformat()
    else:
        record["status"] = "retry"
        record["next_review_on"] = (
            now_local().date()
            + timedelta(days=1)
        ).isoformat()

    save_tracker(tracker)


def record_review(
    tracker,
    question_id,
    successful,
    independent=True
):
    record = get_question_record(tracker, question_id)
    record["review_count"] += 1
    record["last_reviewed_at"] = now_local().isoformat()

    if not successful:
        record["status"] = "retry"
        record["review_interval_index"] = 0
        record["next_review_on"] = (
            now_local().date()
            + timedelta(days=1)
        ).isoformat()
        save_tracker(tracker)
        return

    current_index = record.get(
        "review_interval_index",
        0
    )

    next_index = min(
        current_index + 1,
        len(REVIEW_INTERVALS) - 1
    )

    record["review_interval_index"] = next_index

    if independent and next_index == len(REVIEW_INTERVALS) - 1:
        record["status"] = "mastered"
        record["next_review_on"] = None
    else:
        record["status"] = "reviewed"
        record["next_review_on"] = (
            now_local().date()
            + timedelta(days=REVIEW_INTERVALS[next_index])
        ).isoformat()

    save_tracker(tracker)


def sync_leetcode_progress(tracker, question_bank):
    try:
        _, submissions = get_recent_accepted_submissions(
            limit=50
        )
    except Exception as error:
        print(f"LeetCode synchronization skipped: {error}")
        return tracker

    accepted = {}

    for submission in submissions:
        slug = submission["titleSlug"]
        submission_time = int(submission["timestamp"])

        if (
            slug not in accepted
            or submission_time > accepted[slug]["timestamp"]
        ):
            accepted[slug] = {
                "timestamp": submission_time,
                "submission_id": submission.get("id")
            }

    questions_by_slug = {
        question["leetcode_slug"]: question
        for question in question_bank
        if question.get("leetcode_slug")
    }

    changed = False

    def parse_assignment_time(value):
        if not value:
            return None

        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=LOCAL_TIMEZONE
            )

        return parsed.astimezone(LOCAL_TIMEZONE)

    for slug, submission_data in accepted.items():
        question = questions_by_slug.get(slug)

        if not question:
            continue

        question_id = question["id"]

        accepted_at = datetime.fromtimestamp(
            submission_data["timestamp"],
            tz=timezone.utc
        ).astimezone(LOCAL_TIMEZONE)

        for assignment in tracker.get("assignments", []):
            for assigned_item in assignment.get(
                "questions",
                []
            ):
                if assigned_item.get("id") != question_id:
                    continue

                assigned_at = parse_assignment_time(
                    assigned_item.get("assigned_at")
                    or assignment.get("created_at")
                )

                if not assigned_at:
                    continue

                if accepted_at < assigned_at:
                    continue

                assignment_status = (
                    "reviewed"
                    if assigned_item.get("type") == "review"
                    else "solved"
                )

                previous_completed_at = assigned_item.get(
                    "completed_at"
                )

                if (
                    assigned_item.get("status")
                    != assignment_status
                    or previous_completed_at
                    != accepted_at.isoformat()
                ):
                    assigned_item["status"] = (
                        assignment_status
                    )
                    assigned_item["completed_at"] = (
                        accepted_at.isoformat()
                    )
                    assigned_item["submission_id"] = (
                        submission_data.get("submission_id")
                    )
                    changed = True

        record = get_question_record(
            tracker,
            question_id
        )

        last_assigned = record.get("last_assigned_at")

        if last_assigned:
            assigned_at = parse_assignment_time(
                last_assigned
            )

            if assigned_at and accepted_at < assigned_at:
                continue

        if record["status"] not in {
            "solved",
            "solved_independently",
            "solved_with_help",
            "reviewed",
            "mastered"
        }:
            record["status"] = "solved"
            record["solved_at"] = accepted_at.isoformat()
            record["review_interval_index"] = 0
            record["next_review_on"] = (
                accepted_at.date()
                + timedelta(days=REVIEW_INTERVALS[0])
            ).isoformat()
            changed = True

    if changed:
        save_tracker(tracker)

    return tracker
