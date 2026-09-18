import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote, quote_plus


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "questions.json"

REFERENCE_REPOSITORY = (
    "https://github.com/tazheeb-shamsi/strivers-sde-sheet.git"
)

OFFICIAL_SHEET = (
    "https://takeuforward.org/dsa/"
    "strivers-sde-sheet-top-coding-interview-problems"
)

PLATFORM_PATTERN = re.compile(
    r"https?://[^\s\"'<>)]+",
    re.IGNORECASE
)

SUPPORTED_PLATFORMS = (
    "leetcode.com/problems/",
    "geeksforgeeks.org/",
    "interviewbit.com/",
    "codingninjas.com/",
    "naukri.com/code360/",
    "takeuforward.org/"
)

TOPIC_PRIORITY = {
    "Binary Trees - I": 1,
    "Binary Trees - II": 2,
    "Binary Trees - III": 3,
    "Binary Search Trees - I": 4,
    "Binary Search Trees - II": 5,
    "Binary Trees (Miscellaneous)": 6,
    "Arrays - I": 7,
    "Arrays - II": 8,
    "Arrays - III": 9,
    "Arrays - IV": 10,
    "Strings - I": 11,
    "Strings - II": 12,
    "Linked List - I": 13,
    "Linked List - II": 14,
    "Linked List & Arrays": 15,
    "Recursion": 16,
    "Recursion & Backtracking": 17,
    "Greedy Algorithms": 18,
    "Binary Search": 19,
    "Heaps": 20,
    "Stacks and Queues - I": 21,
    "Stacks and Queues - II": 22,
    "Graphs - I": 23,
    "Graphs - II": 24,
    "Dynamic Programming - I": 25,
    "Dynamic Programming - II": 26,
    "Trie": 27
}


def find_readme(repository):
    for candidate in repository.iterdir():
        if candidate.is_file() and candidate.name.lower() == "readme.md":
            return candidate

    raise FileNotFoundError("Reference repository README was not found.")


def clean_markdown(text):
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = text.replace("`", "")
    return text.strip()


def resolve_solution_file(readme, link):
    link = unquote(link.split("#")[0].strip())

    if not link:
        return None

    if "/blob/" in link:
        relative = link.split("/blob/", 1)[1]
        relative = relative.split("/", 1)[1]
        candidate = readme.parent / relative
    elif link.startswith("http"):
        return None
    else:
        candidate = (readme.parent / link).resolve()

    return candidate if candidate.exists() and candidate.is_file() else None


def extract_problem_url(solution_file):
    if solution_file is None:
        return None

    try:
        content = solution_file.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except OSError:
        return None

    urls = PLATFORM_PATTERN.findall(content)

    cleaned_urls = []
    for url in urls:
        cleaned = url.rstrip(".,;:)]}")
        if any(platform in cleaned.lower() for platform in SUPPORTED_PLATFORMS):
            cleaned_urls.append(cleaned)

    leetcode_urls = [
        url for url in cleaned_urls
        if "leetcode.com/problems/" in url.lower()
    ]

    if leetcode_urls:
        return leetcode_urls[0]

    return cleaned_urls[0] if cleaned_urls else None


def get_leetcode_slug(url):
    if not url or "leetcode.com/problems/" not in url.lower():
        return None

    match = re.search(
        r"leetcode\.com/problems/([^/?#]+)",
        url,
        flags=re.IGNORECASE
    )

    return match.group(1) if match else None


def parse_sheet(readme):
    lines = readme.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()

    questions = []
    current_topic = None
    inside_problem_set = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower() == "## problem set":
            inside_problem_set = True
            continue

        if inside_problem_set and stripped.startswith("## "):
            break

        if not inside_problem_set:
            continue

        heading = re.match(r"^###\s+(.+?)\s*$", stripped)
        if heading:
            current_topic = clean_markdown(heading.group(1))
            continue

        if not current_topic or not stripped.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in stripped.strip("|").split("|")
        ]

        if len(cells) < 2:
            continue

        first_cell = cells[0].strip()

        if not first_cell:
            continue

        if first_cell.lower() == "problem":
            continue

        if set(first_cell.replace(":", "").strip()) <= {"-"}:
            continue

        title = clean_markdown(first_cell)

        if not title or title.lower() == "problem":
            continue

        solution_match = re.search(r"\(([^)]+)\)", cells[1])
        solution_link = (
            solution_match.group(1)
            if solution_match
            else ""
        )

        solution_file = resolve_solution_file(
            readme,
            solution_link
        )

        problem_url = extract_problem_url(solution_file)

        if not problem_url:
            problem_url = (
                "https://leetcode.com/problemset/"
                f"?search={quote_plus(title)}"
            )

        questions.append({
            "id": f"sde-{len(questions) + 1:03d}",
            "sheet_order": len(questions) + 1,
            "curriculum_rank": TOPIC_PRIORITY.get(
                current_topic,
                999
            ),
            "title": title,
            "topic": current_topic,
            "difficulty": "Unknown",
            "url": problem_url,
            "leetcode_slug": get_leetcode_slug(problem_url),
            "sheet": "Striver SDE Sheet",
            "official_sheet_url": OFFICIAL_SHEET,
            "target_status": "not_started",
            "deadline": "2026-10-31"
        })

    return questions


def validate_questions(questions):
    if len(questions) != 191:
        raise RuntimeError(
            "Expected 191 questions but parsed "
            f"{len(questions)}. Existing question bank was not replaced."
        )

    titles = [question["title"] for question in questions]

    if len(titles) != len(set(titles)):
        duplicates = sorted({
            title
            for title in titles
            if titles.count(title) > 1
        })

        print(
            "Warning: repeated titles found:",
            ", ".join(duplicates)
        )

    required_topics = {
        "Binary Trees - I",
        "Binary Trees - II",
        "Binary Trees - III",
        "Binary Search Trees - I",
        "Binary Search Trees - II",
        "Arrays - I",
        "Linked List - I",
        "Graphs - I",
        "Dynamic Programming - I",
        "Trie"
    }

    available_topics = {
        question["topic"]
        for question in questions
    }

    missing_topics = required_topics - available_topics

    if missing_topics:
        raise RuntimeError(
            "Required topics are missing: "
            + ", ".join(sorted(missing_topics))
        )


def main():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory) / "striver-sheet"

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                REFERENCE_REPOSITORY,
                str(repository)
            ],
            check=True
        )

        readme = find_readme(repository)
        questions = parse_sheet(readme)
        validate_questions(questions)

    questions.sort(
        key=lambda question: (
            question["curriculum_rank"],
            question["sheet_order"]
        )
    )

    for curriculum_order, question in enumerate(
        questions,
        start=1
    ):
        question["curriculum_order"] = curriculum_order

    OUTPUT_FILE.write_text(
        json.dumps(
            questions,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    topics = {}

    for question in questions:
        topics[question["topic"]] = (
            topics.get(question["topic"], 0) + 1
        )

    print()
    print(f"Imported questions: {len(questions)}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    print("Topic counts:")

    for topic, count in sorted(
        topics.items(),
        key=lambda item: TOPIC_PRIORITY.get(item[0], 999)
    ):
        print(f"- {topic}: {count}")


if __name__ == "__main__":
    main()
