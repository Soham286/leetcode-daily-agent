from notifier import send_daily_email
from progress_tracker import (
    get_today_questions,
    load_tracker,
    mark_daily_email_sent,
    record_daily_assignment,
    save_tracker,
    sync_leetcode_progress
)
from question_selector import (
    load_questions,
    select_daily_questions
)


def main():
    question_bank = load_questions()
    tracker = load_tracker()

    tracker = sync_leetcode_progress(
        tracker,
        question_bank
    )

    questions = get_today_questions(
        tracker,
        question_bank
    )

    if not questions:
        selected = select_daily_questions(tracker)

        record_daily_assignment(
            tracker,
            selected
        )

        tracker = load_tracker()

        questions = get_today_questions(
            tracker,
            question_bank
        )

    print()
    print("Striver SDE Daily Practice")
    print("=" * 50)

    for number, question in enumerate(
        questions,
        start=1
    ):
        print()
        print(f"{number}. {question['title']}")
        print(f"   Topic: {question['topic']}")
        print(
            f"   Type: "
            f"{question.get('assignment_type', 'new')}"
        )
        print(
            f"   Status: "
            f"{question.get('status', 'assigned')}"
        )
        print(f"   Link: {question['url']}")

    print()

    send_daily_email(questions)

    tracker = load_tracker()
    mark_daily_email_sent(tracker)


if __name__ == "__main__":
    main()
