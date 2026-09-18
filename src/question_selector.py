import json
import random
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = PROJECT_ROOT / "data" / "questions.json"


def load_questions():
    with QUESTIONS_FILE.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def get_slug(question):
    return question["url"].rstrip("/").split("/")[-1]


def select_daily_questions(tracker, number_of_questions=3):
    questions = load_questions()
    solved_slugs = set(tracker.get("known_solved_slugs", []))

    cutoff = date.today() - timedelta(days=7)
    recently_assigned = set()

    for assignment in tracker.get("assignments", []):
        assignment_date = date.fromisoformat(assignment["date"])

        if assignment_date >= cutoff:
            recently_assigned.update(
                question["slug"]
                for question in assignment["questions"]
            )

    available = [
        question
        for question in questions
        if get_slug(question) not in solved_slugs
        and get_slug(question) not in recently_assigned
    ]

    if len(available) < number_of_questions:
        available = [
            question
            for question in questions
            if get_slug(question) not in solved_slugs
        ]

    if len(available) < number_of_questions:
        available = questions.copy()

    return random.sample(available, number_of_questions)
