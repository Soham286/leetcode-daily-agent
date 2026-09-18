from datetime import date


TIMEZONE = "America/Los_Angeles"
DEADLINE = date(2026, 10, 31)

WEEKDAY_NEW_QUESTIONS = 5
WEEKDAY_REVIEW_QUESTIONS = 0

WEEKEND_NEW_QUESTIONS = 3
WEEKEND_REVIEW_QUESTIONS = 2

WARNING_ONE_HOUR = 18
WARNING_TWO_HOUR = 22

DAILY_EMAIL_HOUR = 8
WEEKLY_REPORT_DAY = 6
WEEKLY_REPORT_HOUR = 20

REVIEW_INTERVALS = [1, 3, 7, 14]

MASTERY_STATES = [
    "not_started",
    "assigned",
    "started",
    "attempted",
    "solved",
    "solved_with_help",
    "solved_independently",
    "reviewed",
    "mastered",
    "retry"
]
