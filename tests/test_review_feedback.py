"""Feedback headings must retain prioritized requests and their evidence."""
import pytest

from arcpuzzles.review_feedback import feedback_items


@pytest.mark.parametrize("heading", [
    "## **F1 (top shared change): Require semantic contracts**",
    "## **F1** (top shared change): Require semantic contracts",
    "## F1 (top shared change): Require semantic contracts",
    "- **F1 (top shared change)**: Require semantic contracts",
])
def test_qualified_feedback_heading_retains_request_and_evidence(heading):
    document = (heading + "\n\nEvidence: checks/lesson.json\n\n"
                "## F2: Improve logs\nKeep this separate.\n")
    assert feedback_items(document) == [
        {"id": "F1", "text": "(top shared change) Require semantic contracts\n\nEvidence: checks/lesson.json"},
        {"id": "F2", "text": "Improve logs\nKeep this separate."},
    ]
