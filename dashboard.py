import html
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from progress_tracker import load_tracker, sync_leetcode_progress


LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")

st.set_page_config(
    page_title="LeetCode Mastery",
    page_icon="⚡",
    layout="wide"
)


st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, #172554 0%, transparent 28%),
            radial-gradient(circle at 90% 5%, #3b0764 0%, transparent 26%),
            linear-gradient(145deg, #020617 0%, #0f172a 55%, #111827 100%);
        color: #f8fafc;
    }

    .block-container {
        max-width: 1300px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, p, label {
        color: #f8fafc !important;
    }

    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(12px);
    }

    [data-testid="stMetricValue"] {
        color: #ffffff;
    }

    .hero {
        padding: 28px;
        border-radius: 24px;
        background:
            linear-gradient(
                135deg,
                rgba(37, 99, 235, 0.32),
                rgba(126, 34, 206, 0.27)
            );
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 24px 55px rgba(0, 0, 0, 0.28);
        margin-bottom: 24px;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        color: #cbd5e1;
        font-size: 1rem;
    }

    .question-card {
        min-height: 265px;
        padding: 22px;
        border-radius: 20px;
        background: rgba(15, 23, 42, 0.88);
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
        margin-bottom: 16px;
    }

    .question-number {
        color: #93c5fd;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .question-title {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 12px 0;
    }

    .question-meta {
        color: #cbd5e1;
        margin: 7px 0;
    }

    .status-pending, .status-solved {
        display: inline-block;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 10px;
    }

    .status-pending {
        color: #fde68a;
        background: rgba(245, 158, 11, 0.17);
    }

    .status-solved {
        color: #86efac;
        background: rgba(34, 197, 94, 0.17);
    }

    .solve-link {
        display: inline-block;
        margin-top: 18px;
        color: #ffffff !important;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        padding: 10px 16px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 700;
    }

    .section-title {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 28px 0 14px;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #0f172a 0%, #172554 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] button {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        border: none;
        color: #ffffff !important;
        font-weight: 700;
    }

    [data-testid="stHeader"] {
        background: rgba(2, 6, 23, 0.82);
    }

    .question-card {
        display: flex;
        flex-direction: column;
        min-height: 285px;
    }

    .solve-link {
        margin-top: auto;
        align-self: flex-start;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_data(ttl=300)
def get_tracker():
    tracker = load_tracker()

    try:
        return sync_leetcode_progress(tracker), None
    except Exception as error:
        return tracker, str(error)


tracker, sync_error = get_tracker()

if st.sidebar.button("Refresh LeetCode progress"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### LeetCode Mastery")
st.sidebar.write("User: **sohambanerjee200**")
st.sidebar.write("Automatic accepted-submission tracking")
st.sidebar.write("Timezone: Los Angeles")

if sync_error:
    st.sidebar.warning(
        "Could not refresh LeetCode. Showing saved tracker data."
    )


all_questions = []

for assignment in tracker.get("assignments", []):
    for question in assignment.get("questions", []):
        row = question.copy()
        row["assignment_date"] = assignment["date"]
        all_questions.append(row)

total = len(all_questions)
solved = sum(q.get("status") == "solved" for q in all_questions)
pending = total - solved
completion = round((solved / total) * 100) if total else 0

today = datetime.now(LOCAL_TIMEZONE).date().isoformat()
today_questions = [
    question
    for question in all_questions
    if question["assignment_date"] == today
]

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">⚡ LeetCode Mastery</div>
        <div class="hero-subtitle">
            Welcome back, Soham. Track consistency, master weak topics,
            and turn daily practice into measurable progress.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

metric_columns = st.columns(4)
metric_columns[0].metric("Questions assigned", total)
metric_columns[1].metric("Solved", solved)
metric_columns[2].metric("Pending", pending)
metric_columns[3].metric("Completion rate", f"{completion}%")

st.markdown(
    '<div class="section-title">Today’s challenge</div>',
    unsafe_allow_html=True
)

if today_questions:
    columns = st.columns(3)

    for index, question in enumerate(today_questions):
        status = question.get("status", "pending")
        safe_title = html.escape(question["title"])
        safe_topic = html.escape(question["topic"])
        safe_difficulty = html.escape(question["difficulty"])
        safe_url = html.escape(question["url"], quote=True)

        with columns[index]:
            st.markdown(
                f"""
                <div class="question-card">
                    <div class="question-number">
                        Challenge {index + 1}
                    </div>
                    <div class="question-title">{safe_title}</div>
                    <div class="question-meta">
                        Difficulty: {safe_difficulty}
                    </div>
                    <div class="question-meta">
                        Topic: {safe_topic}
                    </div>
                    <div class="status-{status}">
                        {status.title()}
                    </div>
                    <br>
                    <a class="solve-link"
                       href="{safe_url}"
                       target="_blank">
                       Solve on LeetCode →
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.info("No questions have been assigned today.")

st.markdown(
    '<div class="section-title">Performance overview</div>',
    unsafe_allow_html=True
)

chart_left, chart_right = st.columns(2)

if all_questions:
    dataframe = pd.DataFrame(all_questions)

    status_counts = (
        dataframe["status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Questions")
    )

    status_chart = px.pie(
        status_counts,
        names="Status",
        values="Questions",
        hole=0.68,
        color="Status",
        color_discrete_map={
            "solved": "#22c55e",
            "pending": "#f59e0b"
        }
    )
    status_chart.update_layout(
        title="Solved versus pending",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark",
        font=dict(color="#f8fafc"),
        title_font=dict(color="#f8fafc"),
        legend_title_text="",
        margin=dict(l=20, r=20, t=55, b=20)
    )

    difficulty_counts = (
        dataframe.groupby(["difficulty", "status"])
        .size()
        .reset_index(name="Questions")
    )

    difficulty_chart = px.bar(
        difficulty_counts,
        x="difficulty",
        y="Questions",
        color="status",
        barmode="group",
        color_discrete_map={
            "solved": "#22c55e",
            "pending": "#8b5cf6"
        },
        labels={"difficulty": "Difficulty", "status": "Status"}
    )
    difficulty_chart.update_layout(
        title="Progress by difficulty",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark",
        font=dict(color="#f8fafc"),
        title_font=dict(color="#f8fafc"),
        legend_title_text="",
        margin=dict(l=20, r=20, t=55, b=20)
    )
    difficulty_chart.update_xaxes(gridcolor="rgba(148,163,184,0.12)")
    difficulty_chart.update_yaxes(gridcolor="rgba(148,163,184,0.12)")

    chart_left.plotly_chart(status_chart, use_container_width=True)
    chart_right.plotly_chart(difficulty_chart, use_container_width=True)

    st.markdown(
        '<div class="section-title">Assignment history</div>',
        unsafe_allow_html=True
    )

    history = dataframe[
        [
            "assignment_date",
            "title",
            "difficulty",
            "topic",
            "status",
            "solved_at"
        ]
    ].copy()

    history.columns = [
        "Assigned",
        "Question",
        "Difficulty",
        "Topic",
        "Status",
        "Solved at"
    ]

    history = history.sort_values("Assigned", ascending=False)

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Your charts will appear after the first assignment is recorded.")

