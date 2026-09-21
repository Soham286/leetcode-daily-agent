import json
import random
from datetime import date
from pathlib import Path

from plan_config import (
    WEEKDAY_NEW_QUESTIONS,
    WEEKDAY_REVIEW_QUESTIONS,
    WEEKEND_NEW_QUESTIONS,
    WEEKEND_REVIEW_QUESTIONS
)
from progress_tracker import get_question_record


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = PROJECT_ROOT / "data" / "questions.json"


def load_questions():
    with QUESTIONS_FILE.open(
        "r",
        encoding="utf-8-sig"
    ) as file:
        return json.load(file)


def daily_targets():
    weekday = date.today().weekday()

    if weekday < 5:
        return (
            WEEKDAY_NEW_QUESTIONS,
            WEEKDAY_REVIEW_QUESTIONS
        )

    return (
        WEEKEND_NEW_QUESTIONS,
        WEEKEND_REVIEW_QUESTIONS
    )


def choose_new_questions(
    tracker,
    question_bank,
    count
):
    available = []

    for question in question_bank:
        record = get_question_record(
            tracker,
            question["id"]
        )

        if record["status"] == "not_started":
            available.append(question)

    available.sort(
        key=lambda question: (
            question.get("curriculum_rank", 999),
            question.get("curriculum_order", 999),
            question.get("sheet_order", 999)
        )
    )

    selected = available[:count]

    for question in selected:
        question["assignment_type"] = "new"

    return selected

def choose_review_questions(
    tracker,
    question_bank,
    count
):
    today = date.today()
    questions_by_id = {
        question["id"]: question
        for question in question_bank
    }

    due = []
    weak = []
    recent = []

    for question_id, record in tracker.get(
        "question_progress",
        {}
    ).items():
        question = questions_by_id.get(question_id)

        if not question:
            continue

        next_review = record.get("next_review_on")

        if next_review:
            try:
                if date.fromisoformat(next_review) <= today:
                    due.append(question)
                    continue
            except ValueError:
                pass

        if record["status"] in {
            "retry",
            "solved_with_help",
            "attempted",
            "started",
            "assigned"
        }:
            weak.append(question)
            continue

        if record["status"] in {
            "solved",
            "solved_independently",
            "reviewed"
        }:
            recent.append(question)

    candidates = due + weak + recent
    unique_candidates = []
    seen_ids = set()

    for question in candidates:
        if question["id"] in seen_ids:
            continue

        seen_ids.add(question["id"])
        unique_candidates.append(question)

    if len(unique_candidates) <= count:
        selected = unique_candidates
    else:
        selected = random.sample(
            unique_candidates,
            count
        )

    for question in selected:
        question["assignment_type"] = "review"

    return selected



def is_supported_platform(question):
    url = str(
        question.get("url")
        or question.get("link")
        or question.get("leetcode_url")
        or ""
    ).lower()

    return (
        "leetcode.com/" in url
        or "geeksforgeeks.org/" in url
    )


def select_daily_questions(tracker):
    question_bank = [
        question
        for question in load_questions()
        if is_supported_platform(question)
    ]
    new_target, review_target = daily_targets()

    new_questions = choose_new_questions(
        tracker,
        question_bank,
        new_target
    )

    review_questions = choose_review_questions(
        tracker,
        question_bank,
        review_target
    )

    selected_ids = {
        question["id"]
        for question in new_questions + review_questions
    }

    missing = (
        new_target
        + review_target
        - len(new_questions)
        - len(review_questions)
    )

    if missing > 0:
        additional = []

        for question in question_bank:
            if question["id"] in selected_ids:
                continue

            record = get_question_record(
                tracker,
                question["id"]
            )

            if record["status"] == "not_started":
                question["assignment_type"] = "new"
                additional.append(question)

            if len(additional) == missing:
                break

        new_questions.extend(additional)

    return new_questions + review_questions
