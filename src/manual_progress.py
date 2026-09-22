import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKER_FILE = PROJECT_ROOT / "data" / "tracker.json"
TIMEZONE = ZoneInfo("America/Los_Angeles")

VALID_STATUSES = {
    "started",
    "attempted",
    "solved_independently",
    "solved_with_help",
    "retry",
    "reviewed",
    "mastered",
}

COMPLETED_STATUSES = {
    "solved",
    "solved_independently",
    "solved_with_help",
    "reviewed",
    "mastered",
}

REVIEW_INTERVALS = [1, 3, 7, 14]


def boolean_value(value):
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def optional_integer(value):
    value = str(value or "").strip()

    if not value or value == "0":
        return None

    return int(value)


def main():
    question_id = os.environ.get(
        "MANUAL_QUESTION_ID",
        "",
    ).strip()

    status = os.environ.get(
        "MANUAL_STATUS",
        "",
    ).strip()

    confidence = optional_integer(
        os.environ.get("MANUAL_CONFIDENCE")
    )

    time_minutes = optional_integer(
        os.environ.get("MANUAL_TIME_MINUTES")
    )

    mistake = os.environ.get(
        "MANUAL_MISTAKE",
        "",
    ).strip()

    pattern = os.environ.get(
        "MANUAL_PATTERN",
        "",
    ).strip()

    hint_used = boolean_value(
        os.environ.get("MANUAL_HINT_USED")
    )

    solution_viewed = boolean_value(
        os.environ.get("MANUAL_SOLUTION_VIEWED")
    )

    if not question_id:
        raise ValueError("Question ID is required.")

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Unsupported status: {status}"
        )

    if confidence is not None and confidence not in range(1, 6):
        raise ValueError("Confidence must be from 1 to 5.")

    with TRACKER_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        tracker = json.load(file)

    questions = tracker.setdefault("questions", {})

    if question_id not in questions:
        raise ValueError(
            f"Question ID {question_id} was not found."
        )

    state = questions[question_id]
    now = datetime.now(TIMEZONE)
    today = now.date()

    previous_status = state.get(
        "status",
        "not_started",
    )

    state["status"] = status

    if status == "started":
        state["started_at"] = (
            state.get("started_at")
            or now.isoformat()
        )

    if status in {"attempted", "retry"}:
        state["attempt_count"] = (
            int(state.get("attempt_count", 0)) + 1
        )

        state["started_at"] = (
            state.get("started_at")
            or now.isoformat()
        )

    if status in {
        "solved_independently",
        "solved_with_help",
        "mastered",
    }:
        state["solved_at"] = (
            state.get("solved_at")
            or now.isoformat()
        )

        state["started_at"] = (
            state.get("started_at")
            or now.isoformat()
        )

        if status == "mastered":
            state["next_review_on"] = None
        else:
            state["review_interval_index"] = 0
            state["next_review_on"] = (
                today + timedelta(days=REVIEW_INTERVALS[0])
            ).isoformat()

    if status == "reviewed":
        interval_index = int(
            state.get("review_interval_index", 0)
        )

        interval_index = min(
            interval_index + 1,
            len(REVIEW_INTERVALS) - 1,
        )

        state["review_interval_index"] = interval_index
        state["review_count"] = (
            int(state.get("review_count", 0)) + 1
        )
        state["last_reviewed_at"] = now.isoformat()
        state["next_review_on"] = (
            today
            + timedelta(
                days=REVIEW_INTERVALS[interval_index]
            )
        ).isoformat()

    if confidence is not None:
        state["confidence"] = confidence

    if time_minutes is not None:
        state["time_minutes"] = time_minutes

    if mistake:
        state["mistake"] = mistake

    if pattern:
        state["pattern"] = pattern

    state["hint_used"] = hint_used
    state["solution_viewed"] = solution_viewed

    completed_statuses = {
        "solved",
        "solved_independently",
        "solved_with_help",
        "reviewed",
        "mastered",
    }

    for assignment in reversed(
        tracker.get("assignments", [])
    ):
        matched_assignment = False

        for assigned_item in assignment.get(
            "questions",
            []
        ):
            if assigned_item.get("id") != question_id:
                continue

            assigned_item["status"] = status

            if status in completed_statuses:
                assigned_item["completed_at"] = (
                    now.isoformat()
                )

            matched_assignment = True
            break

        if matched_assignment:
            break

    tracker.setdefault("reflections", []).append(
        {
            "question_id": question_id,
            "recorded_at": now.isoformat(),
            "previous_status": previous_status,
            "new_status": status,
            "confidence": confidence,
            "time_minutes": time_minutes,
            "mistake": mistake,
            "pattern": pattern,
            "hint_used": hint_used,
            "solution_viewed": solution_viewed,
            "source": "manual_github_action",
        }
    )

    with TRACKER_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            tracker,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    print(
        f"Updated {question_id}: "
        f"{previous_status} -> {status}"
    )


if __name__ == "__main__":
    main()
