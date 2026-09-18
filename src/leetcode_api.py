import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

LEETCODE_URL = "https://leetcode.com/graphql"


def get_recent_accepted_submissions(limit=50):
    username = os.getenv("LEETCODE_USERNAME", "").strip()

    if not username:
        raise ValueError("LEETCODE_USERNAME is missing from .env.")

    query = """
    query getUserActivity($username: String!, $limit: Int!) {
      matchedUser(username: $username) {
        username
        profile {
          ranking
        }
      }
      recentAcSubmissionList(username: $username, limit: $limit) {
        id
        title
        titleSlug
        timestamp
      }
    }
    """

    response = requests.post(
        LEETCODE_URL,
        json={
            "query": query,
            "variables": {
                "username": username,
                "limit": limit
            }
        },
        headers={
            "Content-Type": "application/json",
            "Referer": f"https://leetcode.com/u/{username}/",
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()
    result = response.json()

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    data = result.get("data", {})
    profile = data.get("matchedUser")

    if profile is None:
        raise ValueError(
            f"LeetCode profile '{username}' was not found or is private."
        )

    submissions = data.get("recentAcSubmissionList") or []
    return profile, submissions


if __name__ == "__main__":
    try:
        profile, submissions = get_recent_accepted_submissions()

        print(f"Profile verified: {profile['username']}")
        print(f"Ranking: {profile['profile'].get('ranking')}")
        print(f"Recent accepted submissions: {len(submissions)}")

        for submission in submissions[:10]:
            print(
                f"- {submission['title']} "
                f"(https://leetcode.com/problems/"
                f"{submission['titleSlug']}/)"
            )

    except Exception as error:
        print(f"LeetCode check failed: {error}")
