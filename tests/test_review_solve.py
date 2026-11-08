import hashlib
import json
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return, validate_full_return
from arcpuzzles import review_solve as solves


def packet(library, tmp_path):
    from pathlib import Path
    import shutil
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(source / "src", library / "src",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    q = library / "REVIEW/questions"
    q.mkdir(parents=True)
    (q / "q.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1",
        "id": "q", "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "request.zip",
                              reviewer_solve=True)
    root = tmp_path / "packet"
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(root)
    draw_main(root, bytes(32))
    return root


@pytest.mark.parametrize("declaration,expected", [
    ("EXAMPLES_NEEDED = 4", 4),
    ("EXAMPLES_NEEDED: int = 5", 5),
    ("EXAMPLES_NEEDED = 2", 3),
])
def test_preparation_honors_declared_lesson_budget(library, tmp_path, monkeypatch,
                                                  declaration, expected):
    root = packet(library, tmp_path)
    source = root / "repo/generators/aaaa00000003/generator.py"
    source.write_text(source.read_text() + "\n" + declaration + "\n")
    calls = []
    def generate(self, task_id, **options):
        calls.append(options)
        return [{"train": [{"input": [[1]], "output": [[2]]}] * options["n_train"],
                 "test": [{"input": [[3]], "output": [[4]]}] * options["n_test"],
                 "provenance": {"generator_sha256": self.describe(task_id)["generator_sha256"]}}]
    monkeypatch.setattr(Catalog, "generate", generate)
    summary = solves.prepare_solve(root)
    assert summary["status"] == "prepared"
    assert summary["config"]["n_train"] == calls[0]["n_train"] == expected
    assert len(json.loads((root / "solve/challenge.json").read_text())["train"]) == expected


@pytest.mark.parametrize("declaration", ["EXAMPLES_NEEDED = True",
    "EXAMPLES_NEEDED = 0", "EXAMPLES_NEEDED = 1000000",
    "EXAMPLES_NEEDED = get_count()"])
def test_invalid_lesson_budget_is_blocked_before_generation(library, tmp_path,
                                                           monkeypatch, declaration):
    root = packet(library, tmp_path)
    source = root / "repo/generators/aaaa00000003/generator.py"
    source.write_text(source.read_text() + "\n" + declaration + "\n")
    monkeypatch.setattr(Catalog, "generate", lambda *a, **k: pytest.fail("must not generate"))
    assert solves.prepare_solve(root)["status"] == "blocked"


@pytest.fixture
def prepared(library, tmp_path, monkeypatch):
    root = packet(library, tmp_path)
    def generate(self, task_id, **options):
        return [{"task_id": task_id, "seed": options["seed"],
            "program": "PRIVATE_REFERENCE_DO_NOT_COPY",
            "train": [{"input": [[1]], "output": [[2]]}],
            "test": [{"input": [[3]], "output": [[4]]}],
            "provenance": {"generator_sha256": self.describe(task_id)["generator_sha256"],
                           "rule_hash": "fixture"}}]
    monkeypatch.setattr(Catalog, "generate", generate)
    solves.prepare_solve(root)
    (root / "solve/SOLVE_NOTES.md").write_text("Hypothesis: increment every color.\n")
    return root


def test_public_challenge_is_answer_free_and_content_hashed(prepared):
    public = json.loads((prepared / "solve/challenge.json").read_text())
    assert set(public) == {"train", "test"}
    assert public["test"] == [{"input": [[3]]}]
    summary = json.loads((prepared / "solve/summary.json").read_text())
    assert summary["instance_hash"] == solves.instance_hash(public)
    assert summary["generator_hash"] == hashlib.sha256(
        (prepared / "repo/generators/aaaa00000003/generator.py").read_bytes()).hexdigest()
    assert "PRIVATE_REFERENCE" not in "".join(p.read_text() for p in (prepared / "solve").rglob("*.json"))
    assert "DO NOT consult" in (prepared / "solve/README.md").read_text()
    original = (prepared / "solve/challenge.json").read_bytes()
    solves.prepare_solve(prepared)
    assert (prepared / "solve/challenge.json").read_bytes() == original


def test_wrong_then_correct_keeps_both_sources_notes_and_scores(prepared):
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    return grid\n")
    first = solves.check_solve(prepared, source, note="Test identity hypothesis")
    source.write_text("def solve(grid):\n    return [[c + 1 for c in row] for row in grid]\n")
    second = solves.check_solve(prepared, source, note="Visible mismatch suggests increment")
    assert first["reported_label"] == "bad"
    assert second["reported_label"] == "unknown"
    assert first["program_hash"] != second["program_hash"]
    assert (prepared / "solve/attempts/0001/solution.py").read_text().endswith("return grid\n")
    assert (prepared / "solve/attempts/0002/SOLVE_NOTES.md").is_file()
    assert not any(key in second for key in ("private_exact", "query_passed", "query_total"))
    assert second["visible_passed"] == second["visible_total"]
    private = json.loads((prepared / ".review/solve-private/scores/0002.json").read_text())
    assert private["private_exact"] is True
    assert not any(key in second for key in ("test_outputs", "expected", "labels", "program"))
    solves.finish_solve(prepared, reference_consulted=False, earlier_exposure="yes",
                        reason="Both visible and query checks passed")
    summary = json.loads((prepared / "solve/summary.json").read_text())
    assert summary["reference_consulted_during_solve"] is False
    assert summary["earlier_rule_exposure"] == "yes"
    assert summary["attempt_count"] == 2


def test_solve_attempt_intent_is_explicit_and_survives_return(prepared, tmp_path, library):
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (prepared / name).write_text("Evidence\n")
    (prepared / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    return grid\n")
    first = solves.check_solve(prepared, note="Deliberate rival for a teaching probe",
                               intent="teaching_negative")
    source.write_text("def solve(grid):\n    return [[c + 1 for c in row] for row in grid]\n")
    second = solves.check_solve(prepared, note="Actual solution attempt")
    assert first["attempt_intent"] == "teaching_negative"
    assert second["attempt_intent"] == "solve"
    solves.finish_solve(prepared, reference_consulted=False, earlier_exposure="yes", reason="Done")
    returned = build_full_return(prepared, tmp_path / "review_response_intent.zip")
    with zipfile.ZipFile(returned["zip"]) as archive:
        manifest = json.loads((prepared / "PACKET-MANIFEST.json").read_text())
        validate_full_return(archive, manifest)
        report = json.loads(archive.read("solve/attempts/0001/report.json"))
        assert report["attempt_intent"] == "teaching_negative"
        intake = json.loads(archive.read("INTAKE.json"))
        assert intake["reviewer_solve"]["attempt_intents"] == {
            "solve/attempts/0001/report.json": "teaching_negative",
            "solve/attempts/0002/report.json": "solve"}
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_solve_tracker import build_solve_tracker
    collect_full_returns(library / "REVIEW", tmp_path)
    build_solve_tracker(library / "REVIEW", library / "var/review/solves")
    rows = [json.loads(line) for line in (library / "var/review/solves/attempts.jsonl").read_text().splitlines()]
    assert [r["attempt_intent"] for r in rows] == ["teaching_negative", "solve"]
    assert all(r["label"] == "unknown" and r["training_admitted"] is False for r in rows)


def test_invalid_attempt_intent_is_rejected_before_execution(prepared):
    with pytest.raises(ValueError, match="intent"):
        solves.check_solve(prepared, note="Invalid metadata", intent="accidental_guess")
    assert not (prepared / "solve/attempts/0001").exists()


def test_hash_changes_only_with_public_content():
    public = {"train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]]}]}
    reordered = {"test": public["test"], "train": public["train"]}
    assert solves.instance_hash(public) == solves.instance_hash(reordered)
    changed = {"train": public["train"], "test": [{"input": [[4]]}]}
    assert solves.instance_hash(public) != solves.instance_hash(changed)


def test_finish_freezes_final_notes_without_rewriting_revision(prepared):
    (prepared / "solve/solution.py").write_text("def solve(grid):\n    return grid\n")
    solves.check_solve(prepared, note="First recorded hypothesis")
    revision = prepared / "solve/attempts/0001/SOLVE_NOTES.md"
    original_revision = revision.read_bytes()
    final_notes = b"Final result and why I stopped.\n"
    (prepared / "solve/SOLVE_NOTES.md").write_bytes(final_notes)
    summary = solves.finish_solve(prepared, reference_consulted=False,
                                 earlier_exposure="yes", reason="Stopped")
    assert summary["final_notes_path"] == "solve/FINISHED_NOTES.md"
    assert summary["final_notes_sha256"] == hashlib.sha256(final_notes).hexdigest()
    assert (prepared / summary["final_notes_path"]).read_bytes() == final_notes
    assert revision.read_bytes() == original_revision
    (prepared / "solve/SOLVE_NOTES.md").write_text("Later edits are not the frozen finish.\n")
    assert (prepared / summary["final_notes_path"]).read_bytes() == final_notes
    with pytest.raises(ValueError, match="finished"):
        solves.finish_solve(prepared, reference_consulted=False,
                            earlier_exposure="yes", reason="Rewrite")


def test_validator_rejects_tampered_final_notes(prepared):
    (prepared / "solve/solution.py").write_text("def solve(grid):\n    return grid\n")
    solves.check_solve(prepared, note="Retained revision")
    solves.finish_solve(prepared, reference_consulted=False,
                        earlier_exposure="yes", reason="Finished")
    notes = prepared / "solve/FINISHED_NOTES.md"
    notes.write_text("Changed after finish\n")
    source = prepared / "solve/source/generator.py"
    source.parent.mkdir()
    source.write_bytes((prepared / ".review/solve-private/generator.py").read_bytes())
    names = {str(p.relative_to(prepared)) for p in (prepared / "solve").rglob("*") if p.is_file()}
    contract = json.loads((prepared / "ASSIGNMENT.json").read_text())
    with pytest.raises(ValueError, match="final notes"):
        solves.validate_solve_payload(lambda name: (prepared/name).read_bytes(),
                                      names, contract, complete=True)


def test_visible_fit_does_not_reveal_private_query_failure(prepared):
    (prepared / "solve/solution.py").write_text("def solve(grid):\n    return [[2]]\n")
    report = solves.check_solve(prepared, note="A constant output fits the demonstration")
    assert report["visible_passed"] == report["visible_total"] == 1
    assert report["reported_label"] == "unknown"
    assert not {"private_exact", "query_passed", "query_total"} & set(report)
    private = json.loads((prepared / ".review/solve-private/scores/0001.json").read_text())
    assert private["private_exact"] is False


def test_source_drift_and_public_tampering_are_rejected(prepared):
    (prepared / "repo/generators/aaaa00000003/generator.py").write_text("changed again\n")
    with pytest.raises(ValueError, match="source changed"):
        solves.check_solve(prepared, prepared / "solve/solution.py", note="probe")


def test_execution_failure_is_retained_without_overwriting(prepared):
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    raise ValueError('failed hypothesis')\n")
    report = solves.check_solve(prepared, source, note="Probe exception")
    assert report["reported_label"] == "bad"
    assert report["execution_status"] == "error"
    assert (prepared / "solve/attempts/0001/report.json").is_file()


def test_new_returns_require_solve_record_and_include_every_revision(prepared, tmp_path):
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (prepared / name).write_text(name + "\n")
    (prepared / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    return grid\n")
    solves.check_solve(prepared, source, note="Initial attempt")
    solves.finish_solve(prepared, reference_consulted=False, earlier_exposure="unknown", reason="Stopped wrong")
    returned = build_full_return(prepared, tmp_path / "review_response_solve.zip")
    with zipfile.ZipFile(returned["zip"]) as archive:
        checked = validate_full_return(archive, json.loads((prepared / "PACKET-MANIFEST.json").read_text()))
        assert checked["reviewer_solve"]["attempt_count"] == 1
        assert "solve/attempts/0001/solution.py" in archive.namelist()
        assert "solve/SOLVE_NOTES.md" in archive.namelist()
        assert not any(name.startswith(".review/") for name in archive.namelist())
        assert b"PRIVATE_REFERENCE" not in archive.read("solve/challenge.json")


def test_complete_return_cannot_omit_solve(library, tmp_path):
    root = packet(library, tmp_path)
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (root / name).write_text(name + "\n")
    (root / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    with pytest.raises(ValueError, match="solve"):
        build_full_return(root, tmp_path / "review_response_no_solve.zip")


def test_tracker_retains_wrong_and_good_as_unverified_until_replay(prepared, library, tmp_path):
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_solve_tracker import build_solve_tracker, verify_return_solve
    from arcpuzzles.review_full_candidate import check_full_candidate
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (prepared / name).write_text("Evidence\n")
    (prepared / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    return grid\n")
    solves.check_solve(prepared, source, note="Try identity")
    source.write_text("def solve(grid):\n    return [[c + 1 for c in row] for row in grid]\n")
    solves.check_solve(prepared, source, note="Try increment after visible mismatch")
    solves.finish_solve(prepared, reference_consulted=False, earlier_exposure="yes", reason="Solved")
    returned = build_full_return(prepared, tmp_path / "review_response_tracker.zip")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    receipt = next(r for r in collected["receipts"] if r["zip_sha256"] == returned["zip_sha256"])
    tracker = build_solve_tracker(library / "REVIEW", library / "var/review/solves")
    rows = [json.loads(line) for line in (library / "var/review/solves/attempts.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert [r["label"] for r in rows] == ["unknown", "unknown"]
    assert {r["reported_label"] for r in rows} == {"unknown", "bad"}
    assert all(r["training_admitted"] is False for r in rows)
    assert tracker["counts"]["questions"] == 1
    assert "Reviewer solves" in (library / "var/review/solves/index.html").read_text()
    checked = check_full_candidate(Catalog(library), library / "REVIEW", receipt["assignment_id"], 1)
    assert checked["status"] == "no_changes"
    verified = verify_return_solve(library / "REVIEW", receipt["assignment_id"], 1)
    assert [r["label"] for r in verified["attempts"]] == ["bad", "good"]
    build_solve_tracker(library / "REVIEW", library / "var/review/solves")
    rows = [json.loads(line) for line in (library / "var/review/solves/attempts.jsonl").read_text().splitlines()]
    assert [r["label"] for r in rows] == ["bad", "good"]
    with zipfile.ZipFile(library / "var/review/solves/export/reviewer-solves.zip") as exported:
        assert "manifest.json" in exported.namelist()
        assert not any("labels" in p for p in exported.namelist())


def test_return_rejects_changed_revision_bytes(prepared, tmp_path):
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (prepared / name).write_text("Evidence\n")
    (prepared / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    solves.check_solve(prepared, note="Try initial stub")
    solves.finish_solve(prepared, reference_consulted=False, earlier_exposure="unknown", reason="Stopped")
    (prepared / "solve/attempts/0001/solution.py").write_text("def solve(grid): return grid\n")
    with pytest.raises(ValueError, match="revision hash"):
        build_full_return(prepared, tmp_path / "review_response_tampered.zip")


def test_generation_failure_can_return_blocked_without_private_rule(library, tmp_path, monkeypatch):
    root = packet(library, tmp_path)
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_RULE_FAILURE")
    monkeypatch.setattr(Catalog, "generate", fail)
    summary = solves.prepare_solve(root)
    assert summary["status"] == "blocked"
    assert "PRIVATE_RULE" not in json.dumps(summary)
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (root / name).write_text("Blocked by generation\n")
    (root / "RESULTS.json").write_text(json.dumps({"completion_state": "blocked"}))
    result = build_full_return(root, tmp_path / "review_response_blocked.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        assert all(b"PRIVATE_RULE" not in archive.read(p) for p in archive.namelist())


def test_timeout_retains_a_failed_revision(prepared):
    source = prepared / "solve/solution.py"
    source.write_text("def solve(grid):\n    while True:\n        pass\n")
    report = solves.check_solve(prepared, source, note="Bounded probe", timeout=0.1)
    assert report["execution_status"] == "timeout"
    assert report["reported_label"] == "bad"
    assert json.loads((prepared / "solve/attempts/0001/execution.json").read_text())["timed_out"] is True


def test_invalid_timeout_does_not_leave_an_unrecorded_revision(prepared):
    with pytest.raises(ValueError, match="timeout"):
        solves.check_solve(prepared, note="Invalid configuration", timeout=0)
    assert not (prepared / "solve/attempts/0001").exists()


def test_duties_solve_preparation_runs_from_packet_root(library, tmp_path):
    import re
    import shlex
    import sys
    from arcpuzzles.runtime import run_process
    root = packet(library, tmp_path)
    duties = (root / "DUTIES.md").read_text()
    command = re.search(r"`([^`]*solve_episode.py prepare)`", duties)[1]
    args = shlex.split(command)
    args[0] = sys.executable
    result = run_process(args, root, timeout=30)
    # The tiny fixture cannot generate, but the command must reach the solve tool
    # and retain a blocked record, rather than failing to locate its script.
    assert (root / "solve/summary.json").is_file(), result["stderr"]


def test_prepare_automatically_presents_visible_dimensions_before_grids(prepared, capsys):
    original = (prepared / 'solve/challenge.json').read_bytes()
    text = (prepared / 'solve/README.md').read_text()
    label = 'Input: 1 rows × 1 columns. Output: 1 rows × 1 columns.'
    assert label in text and text.index(label) < text.index('[1]')
    assert 'Output: unknown.' in text and '[4]' not in text
    assert solves.main(prepared, ['prepare']) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)['status'] == 'prepared'
    assert label in captured.err and captured.err.index(label) < captured.err.index('[1]')
    assert 'Output: unknown.' in captured.err and '[4]' not in captured.err
    assert (prepared / 'solve/challenge.json').read_bytes() == original


def test_grid_command_works_from_relocated_packet_without_catalog_or_racket(prepared, tmp_path):
    import os
    import subprocess
    import sys
    moved = tmp_path / 'relocated-review'
    prepared.rename(moved)
    env = {**os.environ, 'PYTHONPATH': str(moved / 'repo/src'), 'RACKET_PATH': '/not-installed'}
    run = subprocess.run([sys.executable, '-S', '-m', 'arcpuzzles', '--library', '/missing-library',
                          'grid', str(moved / 'solve/challenge.json')],
                         cwd=tmp_path, env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert 'Input: 1 rows × 1 columns. Output: 1 rows × 1 columns.' in run.stdout
    assert 'Output: unknown.' in run.stdout
    assert '[4]' not in run.stdout and 'PRIVATE_REFERENCE' not in run.stdout
