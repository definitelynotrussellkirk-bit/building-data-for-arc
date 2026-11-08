from __future__ import annotations

from scripts import check_task_authority_sync as authority
from scripts.check_task_authority_sync import source_digests, strip_racket_comments


def test_comment_stripping_preserves_quoted_semicolons() -> None:
    source = '(rule! (display "a;b")) ; outside comment\n(+ 1 2)'
    assert strip_racket_comments(source) == (
        '(rule! (display "a;b")) \n(+ 1 2)'
    )


def test_digests_separate_exact_whitespace_and_comment_agreement() -> None:
    compact = "(rule! (+ 1 2))"
    spaced = "(rule!   (+ 1 2)) ; explanation"
    compact_digests = source_digests(compact)
    spaced_digests = source_digests(spaced)

    assert compact_digests["exact_sha256"] != spaced_digests["exact_sha256"]
    assert (
        compact_digests["comment_stripped_normalized_sha256"]
        == spaced_digests["comment_stripped_normalized_sha256"]
    )


def test_audit_labels_selected_sync_with_archival_divergence(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        authority,
        "_canonical_sources",
        lambda _task_id: [
            {
                "location": "canonical.jsonl:1",
                "field": "program_solution",
                "role": "canonical_program_solution",
                "canonicalization_status": "canonical",
                "source": "(rule! g)",
            }
        ],
    )
    monkeypatch.setattr(
        authority,
        "_base_sources",
        lambda _task_id: [
            {
                "location": "base.json",
                "field": "raw_code",
                "role": "archival_or_executable_raw",
                "canonicalization_status": "preserved_executable_source",
                "code_form": "rule_body_or_callable",
                "target_status": "verified_racket_available",
                "source": "(rule! (identity g))",
            },
            {
                "location": "base.json",
                "field": "target_code",
                "role": "selected_task_rule",
                "canonicalization_status": "preserved_executable_source",
                "code_form": "rule_body_or_callable",
                "target_status": "verified_racket_available",
                "source": "(rule! g)",
            },
        ],
    )

    result = authority.audit_task("fixture")

    assert result["status"] == "selected_synchronized_archival_divergent"
    assert result["selected_authority_count"] == 2
    assert result["archival_authority_count"] == 1
    assert result["archival_divergent"] == ["base.json#raw_code"]
    assert {
        row["role"] for row in result["authorities"]
    } == {
        "canonical_program_solution",
        "archival_or_executable_raw",
        "selected_task_rule",
    }
