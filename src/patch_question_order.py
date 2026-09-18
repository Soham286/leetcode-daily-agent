from pathlib import Path


FILE = Path(__file__).resolve().parent / "question_selector.py"
content = FILE.read_text(encoding="utf-8-sig")

start = content.index("def choose_new_questions(")
end = content.index(
    "\ndef choose_review_questions(",
    start
)

replacement = '''def choose_new_questions(
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

'''

updated = (
    content[:start]
    + replacement
    + content[end + 1:]
)

FILE.write_text(updated, encoding="utf-8")

print(
    "Weekday selection changed from random "
    "to the logical Striver Sheet order."
)
