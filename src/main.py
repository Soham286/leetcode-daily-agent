from notifier import send_daily_email
from progress_tracker import (
    get_today_questions,
    load_tracker,
    record_daily_assignment,
    sync_leetcode_progress
)
from question_selector import select_daily_questions


def main():
    tracker = load_tracker()
    tracker = sync_leetcode_progress(tracker)

    questions = get_today_questions(tracker)

    if questions:
        print("Using today's existing assignment.")
    else:
        questions = select_daily_questions(tracker)
        questions = record_daily_assignment(tracker, questions)

    print()
    print("Your Daily LeetCode Practice")
    print("=" * 45)

    for number, question in enumerate(questions, start=1):
        print()
        print(f"{number}. {question['title']}")
        print(f"   Difficulty: {question['difficulty']}")
        print(f"   Topic: {question['topic']}")
        print(f"   Status: {question.get('status', 'pending')}")
        print(f"   Link: {question['url']}")

    print()
    send_daily_email(questions)


if __name__ == "__main__":
    main()
