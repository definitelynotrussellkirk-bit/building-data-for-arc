import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import hashlib
import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_candidate import check_full_candidate, assess_full_candidate
from test_review_full_collect import _return


def test_v2_check_builds_disposable_source_and_runtime(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    result = check_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"], 1, timeout=2)
    assert result["status"] == "failed_checks"  # minimal fixture lacks inherited battery scripts
    assert f"repo/generators/{contract['task_id']}/generator.py" in result["paths"]
    candidate = Path(result["candidate_path"])
    assert "2.0" in (candidate / f"repo/generators/{contract['task_id']}/generator.py").read_text()
    assert (candidate / "runtime/RUNTIME_MANIFEST.json").is_file()
    assert hashlib.sha256((library / contract['generator']['generator']).read_bytes()).hexdigest() == contract['generator']['generator_sha256']


def test_v2_check_applies_patch_when_candidate_is_inside_parent_checkout(library, tmp_path):
    checkout = Path(__file__).resolve().parents[1]
    scratch = checkout / "var"
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="review-candidate-test-", dir=scratch) as temporary:
        nested_library = Path(temporary) / "library"
        shutil.copytree(library, nested_library)
        contract, _ = _return(nested_library, tmp_path, edit=True)
        collect_full_returns(nested_library / "REVIEW", tmp_path)
        result = check_full_candidate(
            Catalog(nested_library), nested_library / "REVIEW", contract["assignment_id"], 1,
            timeout=2,
        )
        candidate = Path(result["candidate_path"])
        assert "2.0" in (candidate / f"repo/generators/{contract['task_id']}/generator.py").read_text()
        assert hashlib.sha256((nested_library / contract['generator']['generator']).read_bytes()).hexdigest() == contract['generator']['generator_sha256']


def test_failed_or_no_patch_return_remains_assessable(library, tmp_path):
    contract, _ = _return(library, tmp_path, state="blocked")
    collect_full_returns(library / "REVIEW", tmp_path)
    report = assess_full_candidate(library / "REVIEW", contract["assignment_id"], 1)
    assert report["status"] == "no_changes"
    assert Path(report["decision_path"]).read_text().startswith("DECISIONS")
    assert report["question_answer"]["id"] == "q"
    assert Path(report["feedback_path"]).is_file()


def test_v2_assessment_indexes_feedback_ids_in_markdown_headings(library, tmp_path):
    contract, _ = _return(
        library, tmp_path, state="blocked",
        feedback_text="# Feedback\n\n## F1: Show battery progress\n\nF2: Keep source receipts\n",
    )
    collect_full_returns(library / "REVIEW", tmp_path)

    report = assess_full_candidate(library / "REVIEW", contract["assignment_id"], 1)

    assert report["feedback_items"] == [
        {"id": "F1", "text": "Show battery progress"},
        {"id": "F2", "text": "Keep source receipts"},
    ]


@pytest.mark.parametrize("heading", [
    "**F1: Show battery progress.**",
    "## F1. Show battery progress.",
    "- **F1: Show battery progress.**",
    "**F1**: Show battery progress.",
    "## F1 — Show battery progress.",
])
def test_assessment_retains_formatted_feedback_and_its_evidence(library, tmp_path, heading):
    contract, _ = _return(
        library, tmp_path, state="blocked",
        feedback_text=(heading + "\n\nThe wrapper was silent for five minutes.\n"
                       "Flush each completed stage.\n\nF2: Keep source receipts\n"),
    )
    collect_full_returns(library / "REVIEW", tmp_path)

    report = assess_full_candidate(library / "REVIEW", contract["assignment_id"], 1)

    assert report["feedback_items"] == [
        {"id": "F1", "text": "Show battery progress.\n\nThe wrapper was silent for five minutes.\nFlush each completed stage."},
        {"id": "F2", "text": "Keep source receipts"},
    ]


def test_v2_check_records_explicit_lint_override(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    replacement = tmp_path / "lint_generator.py"
    replacement.write_text("# operator checker version\n")

    result = check_full_candidate(
        Catalog(library), library / "REVIEW", contract["assignment_id"], 1,
        timeout=2, lint_override=replacement,
    )

    assert result["checker_override"] == {
        "runtime_path": "scripts/lint_generator.py",
        "source_path": str(replacement.resolve()),
        "sha256": hashlib.sha256(replacement.read_bytes()).hexdigest(),
    }
    assert (Path(result["candidate_path"]) / "runtime/scripts/lint_generator.py").read_bytes() == replacement.read_bytes()
    with pytest.raises(ValueError, match="existing check receipt"):
        check_full_candidate(
            Catalog(library), library / "REVIEW", contract["assignment_id"], 1,
            timeout=2, lint_override=replacement,
        )


def test_feedback_disposition_supports_full_packet_returns(library, tmp_path):
    from arcpuzzles.review_assess import record_feedback
    contract, _ = _return(library, tmp_path, state="blocked",
                         feedback_text="**F1: Show progress.**\n\nKeep the evidence.\n")
    collect_full_returns(library / "REVIEW", tmp_path)

    entry = record_feedback(library / "REVIEW", contract["assignment_id"], 1,
                            "F1", "accepted", "Add a stage heartbeat.")

    assert entry["text"] == "Show progress.\n\nKeep the evidence."
    assert entry["status"] == "accepted"


def test_three_target_check_applies_patch_without_executing_targets(library, tmp_path, monkeypatch):
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    collect_full_returns(library / 'REVIEW', tmp_path)
    def unexpected_runtime(*args, **kwargs):
        raise AssertionError('A three-target patch check must not execute a primary-only battery')
    monkeypatch.setattr('arcpuzzles.review_full_candidate.prepare_runtime', unexpected_runtime)
    result = check_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'], 1)
    assert result['status'] == 'patch_verified_checks_pending'
    assert result['checked_task_ids'] == []
    assert result['independently_checked'] is False
    assert len(result['task_ids']) == 3
    assert result['candidate_file_sha256']
    report = assess_full_candidate(library/'REVIEW', contract['assignment_id'], 1)
    assert report['status'] == 'blocked'
    assert 'target_checks_not_run' in report['blockers']
