import json
import re
from pathlib import Path
from urllib.parse import quote_plus


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = PROJECT_ROOT / "data" / "questions.json"


DIRECT_LINKS = {
    "Inorder Traversal":
        "https://leetcode.com/problems/binary-tree-inorder-traversal/",

    "Preorder Traversal":
        "https://leetcode.com/problems/binary-tree-preorder-traversal/",

    "Postorder Traversal":
        "https://leetcode.com/problems/binary-tree-postorder-traversal/",

    "Morris - Inorder Traversal":
        "https://takeuforward.org/data-structure/morris-inorder-traversal-of-a-binary-tree/",

    "Morris - Preorder Traversal":
        "https://takeuforward.org/data-structure/morris-preorder-traversal-of-a-binary-tree/",

    "Left view of Binary Tree":
        "https://www.geeksforgeeks.org/problems/left-view-of-binary-tree/1",

    "Right view of Binary Tree":
        "https://leetcode.com/problems/binary-tree-right-side-view/",

    "Top view of Binary Tree":
        "https://www.geeksforgeeks.org/problems/top-view-of-binary-tree/1",

    "Bottom view of Binary Tree":
        "https://www.geeksforgeeks.org/problems/bottom-view-of-binary-tree/1",

    "Vertical order traversal":
        "https://leetcode.com/problems/vertical-order-traversal-of-a-binary-tree/",

    "Maximum Width of Binary Tree":
        "https://leetcode.com/problems/maximum-width-of-binary-tree/",

    "Preorder inorder postorder in a single traversal":
        "https://takeuforward.org/data-structure/preorder-inorder-postorder-traversals-in-one-traversal/",

    "Print root to node path":
        "https://takeuforward.org/data-structure/print-root-to-node-path-in-a-binary-tree/",

    "Same Tree":
        "https://leetcode.com/problems/same-tree/",

    "Binary Tree Level Order Traversal":
        "https://leetcode.com/problems/binary-tree-level-order-traversal/",

    "Binary Tree Zigzag Level Order Traversal":
        "https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/",

    "Maximum Depth of Binary Tree":
        "https://leetcode.com/problems/maximum-depth-of-binary-tree/",

    "Balanced Binary Tree":
        "https://leetcode.com/problems/balanced-binary-tree/",

    "Lowest Common Ancestor of a Binary Tree":
        "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/",

    "Diameter of Binary Tree":
        "https://leetcode.com/problems/diameter-of-binary-tree/",

    "Boundary Traversal of Binary Tree":
        "https://www.geeksforgeeks.org/problems/boundary-traversal-of-binary-tree/1",

    "Symmetric Tree":
        "https://leetcode.com/problems/symmetric-tree/",

    "Construct Binary Tree from Preorder and Inorder Traversal":
        "https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/",

    "Construct Binary Tree from Inorder and Postorder Traversal":
        "https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/",

    "Flatten Binary Tree to Linked List":
        "https://leetcode.com/problems/flatten-binary-tree-to-linked-list/",

    "Binary Tree Maximum Path Sum":
        "https://leetcode.com/problems/binary-tree-maximum-path-sum/",

    "Children Sum Property in Binary Tree":
        "https://takeuforward.org/data-structure/check-for-children-sum-property-in-a-binary-tree/",

    "Mirror Tree":
        "https://www.geeksforgeeks.org/problems/mirror-tree/1",

    "Search in a Binary Search Tree":
        "https://leetcode.com/problems/search-in-a-binary-search-tree/",

    "Convert Sorted Array to Binary Search Tree":
        "https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/",

    "Validate Binary Search Tree":
        "https://leetcode.com/problems/validate-binary-search-tree/",

    "Lowest Common Ancestor of a Binary Search Tree":
        "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/",

    "Construct Binary Search Tree from Preorder Traversal":
        "https://leetcode.com/problems/construct-binary-search-tree-from-preorder-traversal/",

    "Populating Next Right Pointers in Each Node":
        "https://leetcode.com/problems/populating-next-right-pointers-in-each-node/",

    "Inorder successor and predecessor in BST":
        "https://www.geeksforgeeks.org/problems/predecessor-and-successor/1",

    "Two Sum IV - Input is a BST":
        "https://leetcode.com/problems/two-sum-iv-input-is-a-bst/",

    "Floor and Ceil in a BST":
        "https://www.google.com/search?q="
        + quote_plus(
            '"Floor and Ceil in a BST" Striver TakeUForward'
        ),

    "Kth Smallest Element in a BST":
        "https://leetcode.com/problems/kth-smallest-element-in-a-bst/",

    "Binary Search Tree Iterator":
        "https://leetcode.com/problems/binary-search-tree-iterator/",

    "Find K-th largest & smallest element in BST":
        "https://www.google.com/search?q="
        + quote_plus(
            '"Find K-th largest and smallest element in BST" '
            "Striver TakeUForward"
        ),

    "Serialize and Deserialize Binary Tree":
        "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/",

    "Maximum Sum BST in Binary Tree":
        "https://leetcode.com/problems/maximum-sum-bst-in-binary-tree/",

    "Kth Largest Element in an Array":
        "https://leetcode.com/problems/kth-largest-element-in-an-array/",

    "Find Median from Data Stream":
        "https://leetcode.com/problems/find-median-from-data-stream/",

    "Kth Largest Element in a Stream":
        "https://leetcode.com/problems/kth-largest-element-in-a-stream/",

    "Flood Fill Algorithm":
        "https://leetcode.com/problems/flood-fill/",

    "Distinct Numbers in Window":
        "https://www.interviewbit.com/problems/distinct-numbers-in-window/"
}


def leetcode_slug(url):
    match = re.search(
        r"leetcode\.com/problems/([^/?#]+)/?",
        url,
        flags=re.IGNORECASE
    )

    return match.group(1) if match else None


def safe_search_url(title):
    query = (
        f'"{title}" '
        "Striver SDE Sheet "
        "site:takeuforward.org OR "
        "site:leetcode.com/problems OR "
        "site:geeksforgeeks.org/problems"
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

    corrected = 0
    removed_unsafe_matches = 0

    for question in questions:
        title = question["title"]
        current_url = question.get("url", "")
        match_score = question.get("link_match_score")

        if title in DIRECT_LINKS:
            new_url = DIRECT_LINKS[title]

            if current_url != new_url:
                corrected += 1

            question["url"] = new_url
            question["leetcode_slug"] = leetcode_slug(
                new_url
            )
            question["link_source"] = "verified_override"
            continue

        safe_exact_match = (
            "leetcode.com/problems/" in current_url
            and match_score == 1.0
        )

        imported_direct_link = (
            "leetcode.com/problems/" in current_url
            and match_score is None
        )

        non_leetcode_direct_link = (
            current_url.startswith("http")
            and "leetcode.com/problemset/" not in current_url
            and match_score is None
        )

        if (
            safe_exact_match
            or imported_direct_link
            or non_leetcode_direct_link
        ):
            question["leetcode_slug"] = leetcode_slug(
                current_url
            )
            question["link_source"] = "exact_or_imported"
            continue

        question["url"] = safe_search_url(title)
        question["leetcode_slug"] = None
        question["difficulty"] = "Unknown"
        question["link_source"] = "safe_search"
        removed_unsafe_matches += 1

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

    print(f"Verified corrections: {corrected}")
    print(
        "Unsafe fuzzy matches removed: "
        f"{removed_unsafe_matches}"
    )
    print(f"Total questions: {len(questions)}")


if __name__ == "__main__":
    main()
