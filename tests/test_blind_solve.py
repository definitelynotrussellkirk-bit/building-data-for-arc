"""A blind solve of a second, untouched task, recorded apart from the exposed post-repair solve."""
import json
from pathlib import Path
import shutil
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles import review_solve as solves
from arcpuzzles.review_full_draw import blind_contract, draw_audit, draw_main, load_manifest
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return, validate_full_return


def _packet(library, tmp_path, *, blind=True, name="packet"):
    source = Path(__file__).resolve().parents[1]
    if not (library / "src").exists():
        shutil.copytree(source / "src", library / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        q = library / "REVIEW/questions"
        q.mkdir(parents=True)
        (q / "q.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1",
            "id": "q", "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / f"{name}.zip",
                              reviewer_solve=True, blind_solve=blind)
    root = tmp_path / name
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(root)
    draw_main(root, bytes(32))
    return root


@pytest.fixture
def fake_generation(monkeypatch):
    def generate(self, task_id, **options):
        return [{"task_id": task_id, "seed": options["seed"], "program": "PRIVATE_REFERENCE_DO_NOT_COPY",
                 "train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]], "output": [[4]]}],
                 "provenance": {"generator_sha256": self.describe(task_id)["generator_sha256"],
                                "rule_hash": "fixture"}}]
    monkeypatch.setattr(Catalog, "generate", generate)


def _solve(root, kind, intents=("solve",)):
    folder = root / solves.KINDS[kind]["folder"]
    solves.prepare_solve(root, kind)
    (folder / "SOLVE_NOTES.md").write_text(f"{kind}: increment hypothesis\n")
    (folder / "solution.py").write_text("def solve(grid):\n    return [[c + 1 for c in r] for r in grid]\n")
    for intent in intents:
        solves.check_solve(root, note=f"{kind} attempt", intent=intent, kind=kind)
    solves.finish_solve(root, reference_consulted=False, earlier_exposure="no" if kind == "blind" else "yes",
                        reason="Visible examples pass", kind=kind)


def _docs(root, state="complete"):
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (root / name).write_text(name + "\n")
    (root / "RESULTS.json").write_text(json.dumps({"completion_state": state}))


def test_blind_target_is_seeded_distinct_and_first_in_duties(library, tmp_path):
    root = _packet(library, tmp_path)
    main = json.loads((root / "ASSIGNMENT.json").read_text())
    blind = json.loads((root / "BLIND_ASSIGNMENT.json").read_text())
    manifest, packet_id = load_manifest(root)
    assert blind == blind_contract(manifest, packet_id, main)
    assert blind["task_id"] != main["task_id"]
    duties = (root / "DUTIES.md").read_text()
    assert duties.index("Blind solve first") < duties.index("1. Read generator")
    assert f"Task `{blind['task_id']}`" in duties


def test_audit_never_targets_the_blind_task(library, tmp_path):
    root = _packet(library, tmp_path)
    blind_id = json.loads((root / "BLIND_ASSIGNMENT.json").read_text())["task_id"]
    for value in range(8):
        (root / "AUDIT_ASSIGNMENT.json").unlink(missing_ok=True)
        targets = [t["task_id"] for t in draw_audit(root, bytes([value]) * 32)["targets"]]
        assert blind_id not in targets


def test_blind_and_post_repair_records_stay_separate_through_return_and_collect(
        library, tmp_path, fake_generation):
    root = _packet(library, tmp_path)
    _solve(root, "blind", intents=("teaching_negative", "solve"))
    _solve(root, "post_repair")
    _docs(root)
    returned = build_full_return(root, tmp_path / "review_response_blind.zip")
    manifest = json.loads((root / "PACKET-MANIFEST.json").read_text())
    with zipfile.ZipFile(returned["zip"]) as archive:
        names = set(archive.namelist())
        checked = validate_full_return(archive, manifest)
        intake = json.loads(archive.read("INTAKE.json"))
        assert b"PRIVATE_REFERENCE" not in archive.read("solve-blind/challenge.json")
    assert {"BLIND_ASSIGNMENT.json", "solve-blind/attempts/0002/solution.py",
            "solve-blind/source/generator.py", "solve/attempts/0001/solution.py"} <= names
    assert not any(name.startswith(".review/") for name in names)
    assert checked["reviewer_blind_solve"]["earlier_rule_exposure"] == "no"
    assert checked["reviewer_solve"]["earlier_rule_exposure"] == "yes"
    assert intake["reviewer_blind_solve"]["solve_kind"] == "blind_before_repair"
    assert intake["reviewer_blind_solve"]["attempt_intents"] == {
        "solve-blind/attempts/0001/report.json": "teaching_negative",
        "solve-blind/attempts/0002/report.json": "solve"}
    from arcpuzzles.review_full_collect import collect_full_returns
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    assert [r["validation_status"] for r in collected["receipts"]] == ["accepted"], collected["receipts"]


def test_a_swapped_blind_task_is_rejected(library, tmp_path, fake_generation):
    root = _packet(library, tmp_path)
    path = root / "BLIND_ASSIGNMENT.json"
    blind = json.loads(path.read_text())
    main_id = json.loads((root / "ASSIGNMENT.json").read_text())["task_id"]
    manifest, _ = load_manifest(root)
    other = next(t for t in manifest["all_ids"] if t not in {main_id, blind["task_id"]})
    blind.update(task_id=other, generator=manifest["generators"][other])
    path.write_text(json.dumps(blind))
    _solve(root, "blind")
    _solve(root, "post_repair")
    _docs(root)
    with pytest.raises(ValueError, match="differs from the draw"):
        build_full_return(root, tmp_path / "review_response_swapped.zip")


def test_complete_return_needs_the_blind_solve_when_the_packet_requires_it(library, tmp_path, fake_generation):
    root = _packet(library, tmp_path)
    _solve(root, "post_repair")
    _docs(root)
    with pytest.raises(ValueError, match="blind solve"):
        build_full_return(root, tmp_path / "review_response_no_blind.zip")
    _docs(root, state="in_progress")
    build_full_return(root, tmp_path / "review_response_partial.zip")  # unfinished work may still return


def test_legacy_packet_has_no_blind_task_and_rejects_blind_files(library, tmp_path, fake_generation):
    root = _packet(library, tmp_path, blind=False)
    assert not (root / "BLIND_ASSIGNMENT.json").exists()
    assert "Blind solve" not in (root / "DUTIES.md").read_text()
    with pytest.raises(ValueError, match="no blind solve assignment"):
        solves.prepare_solve(root, "blind")
    _solve(root, "post_repair")
    _docs(root)
    build_full_return(root, tmp_path / "review_response_legacy.zip")
    (root / "solve-blind").mkdir()
    (root / "solve-blind/summary.json").write_text("{}")
    with pytest.raises(ValueError, match="no blind solve"):
        build_full_return(root, tmp_path / "review_response_legacy_extra.zip")


def test_blind_command_line_uses_its_own_folder(library, tmp_path, fake_generation, capsys):
    root = _packet(library, tmp_path)
    assert solves.main(root, ["blind", "prepare"]) == 0
    assert (root / "solve-blind/challenge.json").is_file()
    assert not (root / "solve").exists()
    assert "solve_episode.py blind check" in (root / "solve-blind/README.md").read_text()
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "prepared"
    label = "Input: 1 rows × 1 columns. Output: 1 rows × 1 columns."
    assert label in captured.err and captured.err.index(label) < captured.err.index("[1]")
    assert "Output: unknown." in captured.err and "[4]" not in captured.err
    assert label in (root / "solve-blind/README.md").read_text()



def test_audit_draw_and_blind_replay_survive_collect(library, tmp_path, fake_generation):
    from arcpuzzles.review_full_candidate import check_full_candidate
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_solve_tracker import verify_return_solve
    root = _packet(library, tmp_path)
    _solve(root, "blind", intents=("solve",))
    _solve(root, "post_repair")
    audit = draw_audit(root, bytes([3]) * 32)
    (root / "AUDIT.md").write_text("".join(f"## {t['task_id']}\nNo issue found after probing rivals.\n\n"
                                           for t in audit["targets"]))
    _docs(root)
    returned = build_full_return(root, tmp_path / "review_response_audit_blind.zip")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    receipt = next(r for r in collected["receipts"] if r["zip_sha256"] == returned["zip_sha256"])
    assert receipt["validation_status"] == "accepted", receipt
    check_full_candidate(Catalog(library), library / "REVIEW", receipt["assignment_id"], 1)
    replay = verify_return_solve(library / "REVIEW", receipt["assignment_id"], 1)
    blind_id = json.loads((root / "BLIND_ASSIGNMENT.json").read_text())["task_id"]
    assert replay["blind"]["task_id"] == blind_id
    assert replay["blind"]["status"] == "verified"
    assert [a["label"] for a in replay["blind"]["attempts"]] == ["good"]
    assert [a["label"] for a in replay["attempts"]] == ["good"]


def test_tracker_transports_blind_programs_worklogs_and_exposure(library, tmp_path, fake_generation):
    from arcpuzzles.review_full_candidate import check_full_candidate
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_solve_tracker import verify_return_solve, build_solve_tracker
    root = _packet(library, tmp_path)
    _solve(root, 'blind')
    _solve(root, 'post_repair')
    _docs(root)
    returned = build_full_return(root, tmp_path / 'review_response_feed.zip')
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    check_full_candidate(Catalog(library), library / 'REVIEW', receipt['assignment_id'], 1)
    verify_return_solve(library / 'REVIEW', receipt['assignment_id'], 1)
    tracked = build_solve_tracker(library / 'REVIEW', tmp_path / 'tracker')
    assert tracked['counts']['questions'] == 2
    assert tracked['counts']['attempts'] == 2
    assert tracked['counts']['verified_good'] == 2
    with zipfile.ZipFile(tracked['export']) as archive:
        rows = [json.loads(line) for line in archive.read('attempts.jsonl').splitlines()]
        blind = next(row for row in rows if row['solve_kind'] == 'blind_before_repair')
        exposed = next(row for row in rows if row['solve_kind'] == 'post_repair')
        assert blind['earlier_rule_exposure'] == 'no'
        assert exposed['earlier_rule_exposure'] == 'yes'
        assert archive.read(blind['files']['program']['path']).startswith(b'def solve')
        assert b'blind:' in archive.read(blind['files']['work_log']['path'])
        assert 'PRIVATE_REFERENCE' not in archive.read('questions.jsonl').decode()


@pytest.mark.parametrize('blind_drift', [False, True])
def test_blind_replay_survives_main_repair_but_rejects_blind_drift(library, tmp_path, fake_generation, blind_drift):
    from arcpuzzles.review_full_candidate import check_full_candidate
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_solve_tracker import verify_return_solve
    root = _packet(library, tmp_path)
    _solve(root, 'blind')
    main = json.loads((root / 'ASSIGNMENT.json').read_text())
    canonical = root / 'repo/shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in canonical.read_text().splitlines()]
    for row in rows:
        if row['task_id'] == main['task_id']:
            row['written_solution'] += ' repaired explanation'
    canonical.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    _solve(root, 'post_repair')
    _docs(root)
    returned = build_full_return(root, tmp_path / 'review_response_canonical_repair.zip')
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    checked = check_full_candidate(Catalog(library), library / 'REVIEW', receipt['assignment_id'], 1)
    if blind_drift:
        changed = Path(checked['candidate_path']) / 'repo/shared/data/canonical/puzzles.jsonl'
        rows = [json.loads(line) for line in changed.read_text().splitlines()]
        blind_id = json.loads((root / 'BLIND_ASSIGNMENT.json').read_text())['task_id']
        for row in rows:
            if row['task_id'] == blind_id:
                row['written_solution'] += ' unexpected blind drift'
        changed.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    replay = verify_return_solve(library / 'REVIEW', receipt['assignment_id'], 1)
    if blind_drift:
        assert replay['blind']['status'] == 'blocked'
        assert 'unrelated canonical row' in replay['blind']['reason']
        return
    assert replay['blind']['status'] == 'verified', replay['blind']
    assert [a['label'] for a in replay['blind']['attempts']] == ['good']
    assert replay['status'] == 'verified'


def test_timeout_replay_never_verifies_a_wrong_program_label(library, tmp_path, fake_generation, monkeypatch):
    from arcpuzzles.review_full_candidate import check_full_candidate
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles import review_solve_tracker as tracker
    root = _packet(library, tmp_path, blind=False)
    _solve(root, 'post_repair')
    _docs(root)
    returned = build_full_return(root, tmp_path / 'review_response_timeout.zip')
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    check_full_candidate(Catalog(library), library / 'REVIEW', receipt['assignment_id'], 1)
    monkeypatch.setattr(tracker, 'evaluate_program', lambda *a, **k: (
        {'execution_status': 'timeout', 'reported_label': 'bad', 'private_exact': False},
        {'timed_out': True, 'exit_code': -15}))
    replay = tracker.verify_return_solve(library / 'REVIEW', receipt['assignment_id'], 1)
    assert replay['attempts'][0]['label'] == 'unknown'
    exported = tracker.build_solve_tracker(library / 'REVIEW', tmp_path / 'tracker')
    assert exported['counts']['verified_bad'] == 0
    assert exported['counts']['unverified'] == 1


@pytest.mark.parametrize('arguments', [['prepare'], ['blind', 'prepare']])
def test_packet_wrapper_bootstraps_racket_for_both_prepare_commands(monkeypatch, tmp_path, arguments):
    import os
    import runpy
    import sys
    import types
    wrapper = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_full_packet_files/solve_episode.py'
    binary = tmp_path / 'racket/bin/racket'
    calls = []
    setup = types.ModuleType('setup_racket')
    setup.ensure_racket = lambda: (calls.append('setup') or binary)
    monkeypatch.setitem(sys.modules, 'setup_racket', setup)
    monkeypatch.setattr(sys, 'argv', [str(wrapper), *arguments])
    monkeypatch.setattr(sys, 'path', list(sys.path))
    # Register an undo even when the variable starts absent: the wrapper
    # writes it directly, and pytest otherwise leaks this fake executable
    # into later generation/export subprocesses.
    monkeypatch.setenv('RACKET_PATH', '')
    monkeypatch.delenv('RACKET_PATH')
    monkeypatch.setenv('PATH', 'isolated-python-environment')
    monkeypatch.setattr(solves, 'main', lambda root, argv: 0)
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(wrapper), run_name='__main__')
    assert stopped.value.code == 0
    assert calls == ['setup']
    assert os.environ['RACKET_PATH'] == str(binary)
    assert os.environ['PATH'].split(os.pathsep)[0] == str(binary.parent)
