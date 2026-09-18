import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from leetcode_api import get_recent_accepted_submissions


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKER_FILE = PROJECT_ROOT / "data" / "tracker.json"
LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")


def current_date():
    return datetime.now(LOCAL_TIMEZONE).date().isoformat()


def question_slug(question):
    return question.get(
        "slug",
        question["url"].rstrip("/").split("/")[-1]
    )


def load_tracker():
    default = {
        "assignments": [],
        "known_solved_slugs": []
    }

    if not TRACKER_FILE.exists():
        return default

    try:
        with TRACKER_FILE.open("r", encoding="utf-8-sig") as file:
            tracker = json.load(file)

        tracker.setdefault("assignments", [])
        tracker.setdefault("known_solved_slugs", [])
        return tracker
    except (json.JSONDecodeError, OSError):
        return default


def save_tracker(tracker):
    with TRACKER_FILE.open("w", encoding="utf-8") as file:
        json.dump(tracker, file, indent=4)


def sync_leetcode_progress(tracker):
    _, submissions = get_recent_accepted_submissions(limit=50)
    accepted = {}

    for submission in submissions:
        slug = submission["titleSlug"]
        submission_time = int(submission["timestamp"])

        if slug not in accepted or submission_time > accepted[slug]:
            accepted[slug] = submission_time

    solved_slugs = set(tracker["known_solved_slugs"])
    solved_slugs.update(accepted.keys())
    tracker["known_solved_slugs"] = sorted(solved_slugs)

    for assignment in tracker["assignments"]:
        for question in assignment["questions"]:
            slug = question["slug"]

            if question["status"] == "solved" or slug not in accepted:
                continue

            assigned_at = datetime.fromisoformat(question["assigned_at"])
            solved_at = datetime.fromtimestamp(
                accepted[slug],
                tz=timezone.utc
            ).astimezone(LOCAL_TIMEZONE)

            if solved_at >= assigned_at:
                question["status"] = "solved"
                question["solved_at"] = solved_at.isoformat()

    save_tracker(tracker)
    return tracker


def get_today_questions(tracker):
    today = current_date()

    for assignment in tracker["assignments"]:
        if assignment["date"] == today:
            return assignment["questions"]

    return []


def record_daily_assignment(tracker, questions):
    assigned_at = datetime.now(LOCAL_TIMEZONE).isoformat()
    tracked_questions = []

    for question in questions:
        tracked_questions.append({
            "id": question["id"],
            "title": question["title"],
            "difficulty": question["difficulty"],
            "topic": question["topic"],
            "url": question["url"],
            "slug": question_slug(question),
            "status": "pending",
            "assigned_at": assigned_at,
            "solved_at": None
        })

    tracker["assignments"].append({
        "date": current_date(),
        "questions": tracked_questions
    })

    save_tracker(tracker)
    return tracked_questions
