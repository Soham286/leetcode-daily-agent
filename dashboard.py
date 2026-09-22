import html
import json
import math
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
QUESTIONS_FILE = PROJECT_ROOT / "data" / "questions.json"
TRACKER_FILE = PROJECT_ROOT / "data" / "tracker.json"

sys.path.insert(0, str(SRC_DIR))

from progress_tracker import load_tracker


TIMEZONE = ZoneInfo("America/Los_Angeles")
DEADLINE = date(2026, 10, 31)
TOTAL_SHEET_QUESTIONS = 191

COMPLETED_STATUSES = {
    "solved",
    "solved_with_help",
    "solved_independently",
    "reviewed",
    "mastered",
}

ACTIVE_STATUSES = {
    "assigned",
    "started",
    "attempted",
    "retry",
}

STATUS_LABELS = {
    "not_started": "Not started",
    "assigned": "Assigned",
    "started": "Started",
    "attempted": "Attempted",
    "solved": "Solved",
    "solved_with_help": "Solved with help",
    "solved_independently": "Solved independently",
    "reviewed": "Reviewed",
    "mastered": "Mastered",
    "retry": "Retry needed",
}

STATUS_COLORS = {
    "Not started": "#334155",
    "Assigned": "#f59e0b",
    "Started": "#38bdf8",
    "Attempted": "#a78bfa",
    "Solved": "#22c55e",
    "Solved with help": "#84cc16",
    "Solved independently": "#10b981",
    "Reviewed": "#14b8a6",
    "Mastered": "#06b6d4",
    "Retry needed": "#ef4444",
}


def load_catalog():
    with QUESTIONS_FILE.open("r", encoding="utf-8-sig") as file:
        raw = json.load(file)

    if isinstance(raw, dict):
        questions = raw.get("questions", list(raw.values()))
    else:
        questions = raw

    return {
        str(question.get("id", question.get("slug", index))): question
        for index, question in enumerate(questions, start=1)
        if isinstance(question, dict)
    }


def question_value(question, *keys, default=""):
    for key in keys:
        value = question.get(key)
        if value not in (None, ""):
            return value
    return default


def safe_text(value):
    return html.escape(str(value or ""))


def format_status(status):
    return STATUS_LABELS.get(status, str(status).replace("_", " ").title())


def status_class(status):
    if status in COMPLETED_STATUSES:
        return "status-completed"
    if status == "retry":
        return "status-retry"
    if status in {"started", "attempted"}:
        return "status-active"
    return "status-pending"


def get_question_details(question_id, catalog):
    question = catalog.get(str(question_id), {})
    return {
        "id": str(question_id),
        "title": question_value(
            question,
            "title",
            "name",
            "problem",
            "problem_name",
            default=str(question_id),
        ),
        "topic": question_value(
            question,
            "topic",
            "section",
            "category",
            default="General",
        ),
        "difficulty": question_value(
            question,
            "difficulty",
            "level",
            default="Unknown",
        ),
        "url": question_value(
            question,
            "url",
            "link",
            "leetcode_url",
            default="https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2/",
        ),
    }


def assignment_for_date(assignments, target_date):
    target = target_date.isoformat()
    return next(
        (
            assignment
            for assignment in reversed(assignments)
            if assignment.get("date") == target
        ),
        None,
    )


def build_history(assignments, catalog, states):
    rows = []

    for assignment in assignments:
        for item in assignment.get("questions", []):
            question_id = (
                item.get("id")
                if isinstance(item, dict)
                else str(item)
            )
            assignment_type = (
                item.get("type", "new")
                if isinstance(item, dict)
                else "new"
            )

            details = get_question_details(question_id, catalog)
            state = states.get(str(question_id), {})
            status = (
                item.get(
                    "status",
                    state.get("status", "not_started")
                )
                if isinstance(item, dict)
                else state.get("status", "not_started")
            )

            rows.append(
                {
                    "Date": assignment.get("date", ""),
                    "Question": details["title"],
                    "Topic": details["topic"],
                    "Difficulty": details["difficulty"],
                    "Type": assignment_type.title(),
                    "Status": format_status(status),
                    "URL": details["url"],
                }
            )

    return pd.DataFrame(rows)


def calculate_streak(assignments, states, today):
    assignment_dates = {}

    for assignment in assignments:
        try:
            assignment_date = date.fromisoformat(assignment["date"])
        except (KeyError, TypeError, ValueError):
            continue

        question_ids = [
            str(item.get("id") if isinstance(item, dict) else item)
            for item in assignment.get("questions", [])
        ]

        if question_ids:
            assignment_dates[assignment_date] = all(
                states.get(question_id, {}).get("status")
                in COMPLETED_STATUSES
                for question_id in question_ids
            )

    streak = 0
    current_date = today

    if current_date in assignment_dates and not assignment_dates[current_date]:
        current_date -= timedelta(days=1)

    while assignment_dates.get(current_date, False):
        streak += 1
        current_date -= timedelta(days=1)

    return streak


st.set_page_config(
    page_title="Striver DSA Mastery",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 5%, rgba(37,99,235,.25), transparent 25%),
            radial-gradient(circle at 92% 8%, rgba(126,34,206,.25), transparent 25%),
            linear-gradient(145deg, #020617 0%, #0f172a 58%, #111827 100%);
        color: #f8fafc;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.7rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, p, label {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] {
        background: rgba(2, 6, 23, .96);
        border-right: 1px solid rgba(148, 163, 184, .15);
    }

    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, .84);
        border: 1px solid rgba(148, 163, 184, .18);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 16px 38px rgba(0,0,0,.22);
    }

    [data-testid="stMetricValue"] {
        color: #ffffff;
    }

    .hero {
        padding: 30px;
        border-radius: 25px;
        background:
            linear-gradient(
                135deg,
                rgba(37, 99, 235, .38),
                rgba(126, 34, 206, .36)
            );
        border: 1px solid rgba(255,255,255,.14);
        box-shadow: 0 24px 60px rgba(0,0,0,.3);
        margin-bottom: 24px;
    }

    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: #cbd5e1;
        font-size: 1rem;
    }

    .question-card {
        min-height: 295px;
        padding: 22px;
        border-radius: 20px;
        background: rgba(15,23,42,.88);
        border: 1px solid rgba(148,163,184,.18);
        box-shadow: 0 18px 42px rgba(0,0,0,.24);
        margin-bottom: 12px;
    }

    .question-number {
        color: #93c5fd;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .09em;
        text-transform: uppercase;
    }

    .question-title {
        color: #ffffff;
        font-size: 1.15rem;
        line-height: 1.45;
        font-weight: 750;
        margin: 13px 0;
        min-height: 53px;
    }

    .question-meta {
        color: #cbd5e1;
        font-size: .9rem;
        margin: 7px 0;
    }

    .status-completed,
    .status-pending,
    .status-active,
    .status-retry {
        display: inline-block;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: .76rem;
        font-weight: 700;
        margin-top: 10px;
    }

    .status-completed {
        background: rgba(34,197,94,.2);
        color: #86efac;
    }

    .status-pending {
        background: rgba(245,158,11,.18);
        color: #fcd34d;
    }

    .status-active {
        background: rgba(56,189,248,.18);
        color: #7dd3fc;
    }

    .status-retry {
        background: rgba(239,68,68,.18);
        color: #fca5a5;
    }

    .section-card {
        padding: 22px;
        border-radius: 20px;
        background: rgba(15,23,42,.73);
        border: 1px solid rgba(148,163,184,.15);
        margin: 10px 0 20px;
    }

    .readiness-ready {
        color: #86efac;
        font-weight: 800;
    }

    .readiness-building {
        color: #fcd34d;
        font-weight: 800;
    }

    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #2563eb, #9333ea);
    }

    .stButton > button,
    .stLinkButton > a {
        border-radius: 11px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tracker = load_tracker()
catalog = load_catalog()

states = tracker.get("questions", {})
assignments = tracker.get("assignments", [])
contests = tracker.get("contests", [])
reflections = tracker.get("reflections", [])

now = datetime.now(TIMEZONE)
today = now.date()
today_assignment = assignment_for_date(assignments, today)

completed_ids = {
    question_id
    for question_id, state in states.items()
    if state.get("status") in COMPLETED_STATUSES
}

independent_ids = {
    question_id
    for question_id, state in states.items()
    if state.get("status") in {"solved_independently", "mastered"}
}

assigned_ids = {
    str(item.get("id") if isinstance(item, dict) else item)
    for assignment in assignments
    for item in assignment.get("questions", [])
}

pending_ids = {
    question_id
    for question_id in assigned_ids
    if states.get(question_id, {}).get("status", "not_started")
    not in COMPLETED_STATUSES
}

review_due_ids = {
    question_id
    for question_id, state in states.items()
    if state.get("next_review_on")
    and state.get("next_review_on") <= today.isoformat()
    and state.get("status") in COMPLETED_STATUSES
}

completed_count = len(completed_ids)
remaining_count = max(TOTAL_SHEET_QUESTIONS - completed_count, 0)
completion_rate = completed_count / TOTAL_SHEET_QUESTIONS
independent_rate = (
    len(independent_ids) / completed_count
    if completed_count
    else 0
)

days_remaining = max((DEADLINE - today).days, 0)
required_weekly_pace = (
    math.ceil((remaining_count / max(days_remaining, 1)) * 7)
    if remaining_count
    else 0
)

streak = calculate_streak(assignments, states, today)

history_df = build_history(assignments, catalog, states)

recent_history = history_df.tail(10) if not history_df.empty else history_df
recent_completed = (
    int(recent_history["Status"].isin(
        [format_status(status) for status in COMPLETED_STATUSES]
    ).sum())
    if not recent_history.empty
    else 0
)

contest_checks = {
    "75 sheet questions completed": completed_count >= 75,
    "65% solved independently": independent_rate >= 0.65,
    "7 of the latest 10 completed": recent_completed >= 7,
    "Backlog below 10": len(pending_ids) < 10,
}

contest_score = sum(contest_checks.values())
contest_ready = contest_score == len(contest_checks)

with st.sidebar:
    st.markdown("## ⚡ DSA Command Center")
    st.caption("Striver SDE Sheet · 191 problems")
    st.markdown("---")

    st.markdown("**LeetCode profile**")
    st.code("sohambanerjee200")

    st.markdown("**Schedule**")
    st.write("Weekdays: 5 new questions")
    st.write("Weekends: 3 new + 2 revisions")
    st.write("Maximum: 5 questions/day")

    st.markdown("**Deadline**")
    st.write(DEADLINE.strftime("%B %d, %Y"))
    st.progress(min(completion_rate, 1.0))
    st.caption(f"{completed_count} of {TOTAL_SHEET_QUESTIONS} completed")

    st.markdown("---")

    if st.button("🔄 Reload tracker", use_container_width=True):
        st.rerun()

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">⚡ Striver DSA Mastery</div>
        <div class="hero-subtitle">
            Welcome back, Soham. Complete the full 191-question Striver SDE
            Sheet by October 31 while building revision strength and contest readiness.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_columns = st.columns(6)

with metric_columns[0]:
    st.metric("Completed", completed_count, f"{completion_rate:.0%}")

with metric_columns[1]:
    st.metric("Remaining", remaining_count)

with metric_columns[2]:
    st.metric("Current backlog", len(pending_ids))

with metric_columns[3]:
    st.metric("Reviews due", len(review_due_ids))

with metric_columns[4]:
    st.metric("Day streak", f"{streak} 🔥")

with metric_columns[5]:
    st.metric("Weekly pace needed", required_weekly_pace)

st.markdown("## Today’s mission")

if not today_assignment:
    st.info(
        "No questions have been assigned for today yet. "
        "The daily workflow will create today’s assignment."
    )
else:
    today_items = today_assignment.get("questions", [])
    columns = st.columns(min(len(today_items), 5))

    for index, item in enumerate(today_items):
        question_id = (
            str(item.get("id"))
            if isinstance(item, dict)
            else str(item)
        )
        assignment_type = (
            item.get("type", "new")
            if isinstance(item, dict)
            else "new"
        )

        details = get_question_details(question_id, catalog)
        state = states.get(question_id, {})
        status = (
            item.get(
                "status",
                state.get("status", "assigned")
            )
            if isinstance(item, dict)
            else state.get("status", "assigned")
        )

        with columns[index % len(columns)]:
            st.markdown(
                f"""
                <div class="question-card">
                    <div class="question-number">
                        Challenge {index + 1} · {safe_text(assignment_type)}
                    </div>
                    <div class="question-title">
                        {safe_text(details["title"])}
                    </div>
                    <div class="question-meta">
                        <b>Topic:</b> {safe_text(details["topic"])}
                    </div>
                    <div class="question-meta">
                        <b>Difficulty:</b> {safe_text(details["difficulty"])}
                    </div>
                    <div class="{status_class(status)}">
                        {safe_text(format_status(status))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.link_button(
                "Open problem ↗",
                details["url"],
                use_container_width=True,
            )

st.markdown("## Deadline progress")

deadline_columns = st.columns([2, 1])

with deadline_columns[0]:
    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )
    st.write(
        f"**{completed_count} completed · {remaining_count} remaining · "
        f"{days_remaining} days left**"
    )
    st.progress(min(completion_rate, 1.0))
    st.caption(
        f"Maintain approximately {required_weekly_pace} completed questions "
        "per week to finish by October 31."
    )
    st.markdown("</div>", unsafe_allow_html=True)

with deadline_columns[1]:
    projected_days = (
        math.ceil(remaining_count / 5)
        if remaining_count
        else 0
    )
    st.metric(
        "Minimum practice days",
        projected_days,
        "at 5 per day",
    )

st.markdown("## Performance overview")

chart_columns = st.columns(2)

status_counts = Counter(
    format_status(state.get("status", "not_started"))
    for state in states.values()
)

status_df = pd.DataFrame(
    {
        "Status": list(status_counts.keys()),
        "Questions": list(status_counts.values()),
    }
)

with chart_columns[0]:
    status_figure = px.pie(
        status_df,
        names="Status",
        values="Questions",
        hole=0.68,
        title="Sheet status",
        color="Status",
        color_discrete_map=STATUS_COLORS,
    )
    status_figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        legend_title_text="",
        margin=dict(l=15, r=15, t=55, b=15),
    )
    st.plotly_chart(status_figure, use_container_width=True)

topic_rows = []

for question_id, question in catalog.items():
    state = states.get(question_id, {})
    topic_rows.append(
        {
            "Topic": question_value(
                question,
                "topic",
                "section",
                "category",
                default="General",
            ),
            "Completed": int(
                state.get("status") in COMPLETED_STATUSES
            ),
        }
    )

topic_df = pd.DataFrame(topic_rows)

with chart_columns[1]:
    if not topic_df.empty:
        topic_summary = (
            topic_df.groupby("Topic", as_index=False)
            .agg(
                Completed=("Completed", "sum"),
                Total=("Completed", "size"),
            )
        )
        topic_summary["Progress"] = (
            topic_summary["Completed"]
            / topic_summary["Total"]
            * 100
        )
        topic_summary = topic_summary.sort_values(
            "Progress",
            ascending=True,
        ).tail(12)

        topic_figure = px.bar(
            topic_summary,
            x="Progress",
            y="Topic",
            orientation="h",
            title="Progress by topic",
            color="Progress",
            color_continuous_scale=["#1e3a8a", "#2563eb", "#a855f7"],
            text=topic_summary["Progress"].map(lambda value: f"{value:.0f}%"),
        )
        topic_figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            coloraxis_showscale=False,
            xaxis_title="Completion %",
            yaxis_title="",
            margin=dict(l=15, r=15, t=55, b=15),
        )
        st.plotly_chart(topic_figure, use_container_width=True)

st.markdown("## Contest readiness")

readiness_columns = st.columns([1, 2])

with readiness_columns[0]:
    readiness_percentage = int(
        contest_score / len(contest_checks) * 100
    )

    if contest_ready:
        readiness_message = (
            '<span class="readiness-ready">Ready for a live contest</span>'
        )
    else:
        readiness_message = (
            '<span class="readiness-building">Building contest readiness</span>'
        )

    st.markdown(
        f"""
        <div class="section-card">
            <h2>{readiness_percentage}%</h2>
            {readiness_message}
            <p>{contest_score} of {len(contest_checks)} readiness conditions met</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with readiness_columns[1]:
    for label, passed in contest_checks.items():
        icon = "✅" if passed else "⏳"
        st.write(f"{icon} {label}")

    st.caption(
        "We will recommend your first live LeetCode contest once all four "
        "conditions are satisfied."
    )

st.markdown("## Revision queue")

if not review_due_ids:
    st.success("No revisions are currently overdue.")
else:
    review_rows = []

    for question_id in sorted(review_due_ids):
        details = get_question_details(question_id, catalog)
        state = states.get(question_id, {})

        review_rows.append(
            {
                "Question": details["title"],
                "Topic": details["topic"],
                "Next review": state.get("next_review_on", ""),
                "Reviews completed": state.get("review_count", 0),
                "Confidence": state.get("confidence") or "Not recorded",
            }
        )

    st.dataframe(
        pd.DataFrame(review_rows),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("## Assignment history")

if history_df.empty:
    st.info("Assignment history will appear after the first daily run.")
else:
    filter_columns = st.columns(3)

    with filter_columns[0]:
        topic_options = ["All"] + sorted(
            history_df["Topic"].dropna().unique().tolist()
        )
        selected_topic = st.selectbox("Topic", topic_options)

    with filter_columns[1]:
        status_options = ["All"] + sorted(
            history_df["Status"].dropna().unique().tolist()
        )
        selected_status = st.selectbox("Status", status_options)

    with filter_columns[2]:
        type_options = ["All"] + sorted(
            history_df["Type"].dropna().unique().tolist()
        )
        selected_type = st.selectbox("Assignment type", type_options)

    filtered_history = history_df.copy()

    if selected_topic != "All":
        filtered_history = filtered_history[
            filtered_history["Topic"] == selected_topic
        ]

    if selected_status != "All":
        filtered_history = filtered_history[
            filtered_history["Status"] == selected_status
        ]

    if selected_type != "All":
        filtered_history = filtered_history[
            filtered_history["Type"] == selected_type
        ]

    st.dataframe(
        filtered_history.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn(
                "Problem link",
                display_text="Open ↗",
            )
        },
    )

st.markdown("---")
st.caption(
    f"Last refreshed: {now.strftime('%B %d, %Y at %I:%M %p %Z')} · "
    f"Contests recorded: {len(contests)} · Reflections recorded: {len(reflections)}"
)
