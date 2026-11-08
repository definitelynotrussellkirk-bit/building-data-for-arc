"""Presentation-boundary regression tests; no real generator or private labels opened."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


BUNDLE = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get("CLI_TARGET_SOURCE", str(Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_solve.py")))
REPO_SOURCE = Path(os.environ.get("ARCPUZZLES_REVIEW_SOURCE", str(Path(__file__).resolve().parents[1] / "src")))
sys.path.insert(0, str(REPO_SOURCE))
spec = importlib.util.spec_from_file_location("arcpuzzles.review_solve_optional", SOURCE)
solve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve)
SECRET = "SYNTHETIC_PRIVATE_HYPOTHESIS_DO_NOT_SHOW"
PUBLIC = {"train": [{"input": [[1]], "output": [[1]]}], "test": [{"input": [[2]]}]}


@pytest.fixture
def packet(tmp_path, monkeypatch):
    # Freeze synthetic public examples and synthetic score inputs. This avoids
    # touching real source/authority/labels while exercising real CLI and finish/check.
    def frozen(root, kind="post_repair"):
        return solve._summary(root, kind), {"public": PUBLIC, "test_outputs": [[[2]]]}
    monkeypatch.setattr(solve, "_frozen", frozen)
    for kind, paths in solve.KINDS.items():
        folder = tmp_path / paths["folder"]
        folder.mkdir()
        summary = {"schema": solve.SCHEMA, "assignment_id": "synthetic-assignment",
                   "packet_id": "synthetic-packet", "task_id": "synthetic-task",
                   "status": "attempted", "attempt_count": 1,
                   "generator_hash": "synthetic-source", "instance_hash": "synthetic-instance",
                   "solve_policy": solve.POLICY, "feedback_policy": "visible_only",
                   "generation_provenance": {"lesson_check": {"rivals": {SECRET: {"matched": False}}}},
                   "future_private_field": SECRET, "private_labels_sha256": SECRET,
                   "seed": 123, "config": {"untrusted_future_extension": SECRET}}
        if kind == "blind":
            summary["solve_kind"] = "blind_before_repair"
        solve._write(folder / "summary.json", summary)
        solve._write(folder / "challenge.json", PUBLIC)
        (folder / "SOLVE_NOTES.md").write_text("Synthetic visible-only reasoning\n")
        (folder / "solution.py").write_text("def solve(grid):\n    return grid\n")
    return tmp_path


@pytest.mark.parametrize("kind", ["post_repair", "blind"])
@pytest.mark.parametrize("action", ["prepare", "check", "finish"])
def test_cli_omits_authoring_provenance_and_keeps_visible_feedback(packet, monkeypatch, capsys, kind, action):
    # Removing the projection or admitting unknown fields must fail this test.
    folder = packet / solve.KINDS[kind]["folder"]
    before = (folder / "summary.json").read_bytes()
    if action == "check":
        # The synthetic scorer returns private data; real check_solve masks it.
        monkeypatch.setattr(solve, "evaluate_program", lambda *a, **kw: (
            {"execution_status": "completed", "visible_passed": 1, "visible_total": 1,
             "query_passed": 1, "query_total": 1, "private_exact": True},
            {"exit_code": 0, "timed_out": False, "stdout": "", "stderr": ""}))
    argv = (["blind"] if kind == "blind" else []) + [action]
    if action == "check":
        argv += ["--note", "Synthetic visible hypothesis"]
    elif action == "finish":
        argv += ["--reference-consulted", "no", "--earlier-exposure", "no", "--reason", "Synthetic stop"]
    assert solve.main(packet, argv) == 0
    captured = capsys.readouterr()
    visible = json.loads(captured.out)
    assert SECRET not in captured.out + captured.err
    assert not {"generation_provenance", "future_private_field", "seed", "config",
                "private_labels_sha256", "query_passed", "query_total", "private_exact"} & visible.keys()
    assert visible["assignment_id"] == "synthetic-assignment"
    if action == "prepare":
        assert visible["status"] == "attempted"
        assert captured.err == solve.format_task(PUBLIC) + "\n"
        assert (folder / "summary.json").read_bytes() == before
    elif action == "check":
        assert (visible["visible_passed"], visible["visible_total"]) == (1, 1)
        assert visible["reported_label"] == "unknown"
    else:
        assert visible["status"] == "finished"
        assert visible["stopping_reason"] == "Synthetic stop"
        assert (folder / "FINISHED_NOTES.md").read_bytes() == (folder / "SOLVE_NOTES.md").read_bytes()
    # Authoring evidence must survive presentation and normal summary updates.
    retained = json.loads((folder / "summary.json").read_bytes())
    assert retained["generation_provenance"]["lesson_check"]["rivals"][SECRET] == {"matched": False}
    assert retained["future_private_field"] == SECRET


@pytest.mark.parametrize("kind", ["post_repair", "blind"])
def test_blocked_prepare_masks_provenance_and_preserves_failure_exit(packet, monkeypatch, capsys, kind):
    summary = solve._summary(packet, kind)
    summary.update(status="blocked", stopping_reason="Episode generation blocked: RuntimeError")
    monkeypatch.setattr(solve, "prepare_solve", lambda root, actual_kind: summary)
    assert solve.main(packet, (["blind"] if kind == "blind" else []) + ["prepare"]) == 1
    captured = capsys.readouterr()
    visible = json.loads(captured.out)
    assert SECRET not in captured.out + captured.err
    assert visible["status"] == "blocked"
    assert visible["stopping_reason"] == summary["stopping_reason"]
    assert captured.err == ""


def test_allowlisted_fields_do_not_forward_nested_future_payloads(packet, monkeypatch, capsys):
    summary = solve._summary(packet)
    summary["status"] = {"private_nested_extension": SECRET}
    monkeypatch.setattr(solve, "prepare_solve", lambda *a: summary)
    assert solve.main(packet, ["prepare"]) == 0
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    assert "status" not in json.loads(captured.out)


def test_outer_status_reads_only_lane_state_without_summary_payload(packet, capsys):
    # Outer review.py status is the available status endpoint; solve CLI has no status action.
    outer = Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_workspace_files/review.py"
    outer_spec = importlib.util.spec_from_file_location("arc_optional_outer_status", outer)
    review = importlib.util.module_from_spec(outer_spec)
    outer_spec.loader.exec_module(review)
    review.WORK = packet
    solve._write(packet / "ASSIGNMENT.json", {"assignment_id": "synthetic-assignment", "task_id": "synthetic-repair"})
    solve._write(packet / "BLIND_ASSIGNMENT.json", {"assignment_id": "synthetic-assignment"})
    review.status({"reviewer_solve": {"required": True}})
    out = capsys.readouterr().out
    assert SECRET not in out
    assert "Finish the blind solve" in out
