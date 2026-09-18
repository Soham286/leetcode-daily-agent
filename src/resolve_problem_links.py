import json
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote_plus

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = PROJECT_ROOT / "data" / "questions.json"
LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

MANUAL_ALIASES = {
    "preorder traversal": "binary-tree-preorder-traversal",
    "inorder traversal": "binary-tree-inorder-traversal",
    "postorder traversal": "binary-tree-postorder-traversal",
    "level order traversal": "binary-tree-level-order-traversal",
    "maximum depth of binary tree": "maximum-depth-of-binary-tree",
    "same tree": "same-tree",
    "symmetric tree": "symmetric-tree",
    "diameter of binary tree": "diameter-of-binary-tree",
    "balanced binary tree": "balanced-binary-tree",
    "binary tree maximum path sum": "binary-tree-maximum-path-sum",
    "vertical order traversal": "vertical-order-traversal-of-a-binary-tree",
    "maximum width of binary tree": "maximum-width-of-binary-tree",
    "serialize and deserialize binary tree": "serialize-and-deserialize-binary-tree",
    "flatten binary tree to linked list": "flatten-binary-tree-to-linked-list",
    "search in a binary search tree": "search-in-a-binary-search-tree",
    "validate binary search tree": "validate-binary-search-tree",
    "binary search tree iterator": "binary-search-tree-iterator",
    "kth smallest element in a bst": "kth-smallest-element-in-a-bst",
    "two sum iv - input is a bst": "two-sum-iv-input-is-a-bst",
    "lowest common ancestor of a binary tree": "lowest-common-ancestor-of-a-binary-tree",
    "lowest common ancestor of a binary search tree": "lowest-common-ancestor-of-a-binary-search-tree",
    "construct binary tree from preorder and inorder traversal": "construct-binary-tree-from-preorder-and-inorder-traversal",
    "construct binary tree from inorder and postorder traversal": "construct-binary-tree-from-inorder-and-postorder-traversal",
    "convert sorted array to binary search tree": "convert-sorted-array-to-binary-search-tree",
    "populating next right pointers in each node": "populating-next-right-pointers-in-each-node",
    "binary tree zigzag level order traversal": "binary-tree-zigzag-level-order-traversal"
}


def normalize_title(title):
    title = title.lower()
    title = title.replace("&", " and ")
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return " ".join(title.split())


def fetch_leetcode_questions():
    query = """
    query problemsetQuestionList(
      $categorySlug: String,
      $limit: Int,
      $skip: Int,
      $filters: QuestionListFilterInput
    ) {
      problemsetQuestionList: questionList(
        categorySlug: $categorySlug,
        limit: $limit,
        skip: $skip,
        filters: $filters
      ) {
        total: totalNum
        questions: data {
          title
          titleSlug
          difficulty
          isPaidOnly
        }
      }
    }
    """

    all_questions = []
    limit = 500
    skip = 0
    total = None

    while total is None or skip < total:
        response = requests.post(
            LEETCODE_GRAPHQL,
            json={
                "query": query,
                "variables": {
                    "categorySlug": "",
                    "limit": limit,
                    "skip": skip,
                    "filters": {}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com/problemset/",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=60
        )

        response.raise_for_status()
        payload = response.json()

        if payload.get("errors"):
            raise RuntimeError(payload["errors"])

        result = payload["data"]["problemsetQuestionList"]
        batch = result["questions"] or []
        total = result["total"]

        if not batch:
            break

        all_questions.extend(batch)
        skip += len(batch)

        print(
            f"Downloaded {len(all_questions)}/{total} "
            "LeetCode problems"
        )

        time.sleep(0.25)

    return all_questions


def title_score(sheet_title, leetcode_title):
    left = normalize_title(sheet_title)
    right = normalize_title(leetcode_title)

    if left == right:
        return 1.0

    sequence_score = SequenceMatcher(
        None,
        left,
        right
    ).ratio()

    left_tokens = set(left.split())
    right_tokens = set(right.split())

    if not left_tokens or not right_tokens:
        token_score = 0.0
    else:
        token_score = len(
            left_tokens & right_tokens
        ) / len(left_tokens | right_tokens)

    if left in right or right in left:
        containment_score = 0.9
    else:
        containment_score = 0.0

    return max(
        sequence_score,
        token_score,
        containment_score
    )


def find_best_match(title, leetcode_questions):
    normalized = normalize_title(title)

    if normalized in MANUAL_ALIASES:
        alias = MANUAL_ALIASES[normalized]

        for question in leetcode_questions:
            if question["titleSlug"] == alias:
                return question, 1.0

        return {
            "title": title,
            "titleSlug": alias,
            "difficulty": "Unknown",
            "isPaidOnly": False
        }, 1.0

    best_question = None
    best_score = 0.0

    for candidate in leetcode_questions:
        score = title_score(
            title,
            candidate["title"]
        )

        if score > best_score:
            best_question = candidate
            best_score = score

    if best_score >= 0.72:
        return best_question, best_score

    return None, best_score


def fallback_search_url(title):
    query = (
        f'"{title}" '
        "Striver DSA problem "
        "site:takeuforward.org OR "
        "site:geeksforgeeks.org"
    )

    return (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )


def main():
    with QUESTIONS_FILE.open(
        "r",
        encoding="utf-8-sig"
    ) as file:
        questions = json.load(file)

    leetcode_questions = fetch_leetcode_questions()

    resolved = 0
    fallback = 0

    for index, question in enumerate(
        questions,
        start=1
    ):
        current_url = question.get("url", "")

        if (
            "leetcode.com/problems/" in current_url
            and "problemset/?search=" not in current_url
        ):
            resolved += 1
            continue

        match, score = find_best_match(
            question["title"],
            leetcode_questions
        )

        if match:
            slug = match["titleSlug"]

            question["url"] = (
                f"https://leetcode.com/problems/{slug}/"
            )
            question["leetcode_slug"] = slug
            question["difficulty"] = match.get(
                "difficulty",
                question.get("difficulty", "Unknown")
            )
            question["paid_only"] = match.get(
                "isPaidOnly",
                False
            )
            question["link_match_score"] = round(
                score,
                3
            )

            resolved += 1
        else:
            question["url"] = fallback_search_url(
                question["title"]
            )
            question["leetcode_slug"] = None
            question["link_match_score"] = round(
                score,
                3
            )

            fallback += 1

        print(
            f"{index:03d}/191 "
            f"{question['title']} -> "
            f"{question['url']}"
        )

    with QUESTIONS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            questions,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(f"Direct LeetCode links: {resolved}")
    print(f"Fallback searches: {fallback}")
    print(f"Total: {len(questions)}")


if __name__ == "__main__":
    main()
