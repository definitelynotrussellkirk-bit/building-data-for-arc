from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import zipfile

import pytest

from arcpuzzles import Catalog
from arcpuzzles import review
from arcpuzzles.runtime import prepare_runtime, run_process


def test_check_after_phase_uses_after_policy_and_receipt(library, tmp_path, monkeypatch):
    from arcpuzzles import runtime

    commands = []

    def fake_run(command, root, timeout, **options):
        commands.append(command)
        checks = root / "checks"
        checks.mkdir()
        (checks / "aaaa00000001_after_battery_summary.json").write_text('{"phase":"after"}')
        return {"command": command, "exit_code": 0, "timed_out": False, "stdout": "", "stderr": ""}

    monkeypatch.setattr(runtime, "run_process", fake_run)
    result = runtime.check(Catalog(library), "aaaa00000001", full_battery=True,
                           phase="after", output=tmp_path / "after")
    assert commands == [["bash", "scripts/run_generator_battery.sh", "aaaa00000001", "after", "--fresh", "--keep-going",
                         "--time-budget", "310"]]
    assert result["phase"] == "after"
    assert result["battery_summary"] == {"phase": "after"}
    assert (tmp_path / "after/checks/aaaa00000001_after_battery_summary.json").is_file()


def test_runtime_copies_current_sources_without_links(library, tmp_path):
    target = tmp_path / "runtime"
    receipt = prepare_runtime(Catalog(library), target, "aaaa00000001")
    path = target / "puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    assert path.read_text() == "VERSION = '1.0.0'\n"
    assert not path.is_symlink()
    path.write_text("# draft\n")
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '1.0.0'\n"
    assert len(receipt["files"]) == 1
    with pytest.raises(FileExistsError):
        prepare_runtime(Catalog(library), target)


def test_runtime_rejects_traversal(library, tmp_path):
    mapping = library / "catalog/runtime_files.json"
    mapping.write_text(json.dumps([{"path": "generators/aaaa00000001/generator.py", "target": "../escape.py"}]))
    with pytest.raises(ValueError, match="Invalid"):
        prepare_runtime(Catalog(library), tmp_path / "runtime")
    assert not (tmp_path / "escape.py").exists()


def test_review_claims_are_exclusive_and_closing_does_not_approve(library, tmp_path):
    catalog = Catalog(library)
    root = tmp_path / "REVIEW"
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(review.pick, catalog, seed=7, approved=True, review_root=root) for _ in range(2)]
        chosen = [future.result() for future in futures]
    assert len({r["task_id"] for r in chosen}) == 2
    with pytest.raises(ValueError, match="unclaimed"):
        review.pick(catalog, seed=7, approved=True, review_root=root)
    first = chosen[0]
    folder = Path(first["directory"])
    assert (folder / "REQUEST.md").is_file()
    assert (folder / "workspace/RUNTIME_MANIFEST.json").is_file()
    archive = review.pack(root, first["id"], tmp_path / "request.zip")
    with zipfile.ZipFile(archive) as handle:
        assert "REQUEST.md" in handle.namelist()
        assert "baseline/generator.py" in handle.namelist()
    review.finish(root, first["id"], status="cancelled", note="Fixture review only; no return")
    again = review.pick(catalog, seed=7, approved=True, review_root=root)
    assert again["task_id"] == first["task_id"]
    assert catalog.describe("aaaa00000003")["train_safety"] == "unverified"


def test_failed_preparation_leaves_a_visible_record_and_releases_claim(library, tmp_path):
    catalog = Catalog(library)
    mapping = library / "catalog/runtime_files.json"
    mapping.write_text(json.dumps([{"path": "missing.py", "target": "missing.py"}]))
    root = tmp_path / "REVIEW"
    with pytest.raises(FileNotFoundError):
        review.pick(catalog, task_id="aaaa00000001", review_root=root)
    records = review.assignments(root)
    assert records[0]["status"] == "preparation_failed"
    assert "missing.py" in records[0]["error"]


def test_process_failure_and_timeout_are_visible(tmp_path):
    failed = run_process([sys.executable, "-c", "raise SystemExit(9)"], tmp_path)
    assert failed["exit_code"] == 9
    timed = run_process([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, timeout=0.05)
    assert timed["timed_out"] and timed["exit_code"] != 0


def test_process_progress_arrives_before_exit_and_retains_both_streams(tmp_path):
    chunks = []
    def progress(chunk):
        chunks.append(chunk)
        (tmp_path / "ack").touch()
    code = ("import pathlib,sys,time; print('RUN α',flush=True); "
            "print('warning β',file=sys.stderr,flush=True); "
            "deadline=time.monotonic()+3\n"
            "while not pathlib.Path('ack').exists() and time.monotonic()<deadline: time.sleep(.01)\n"
            "sys.exit(0 if pathlib.Path('ack').exists() else 19)")
    result = run_process([sys.executable, "-c", code], tmp_path, on_output=progress)
    assert result["exit_code"] == 0
    assert result["stdout"] == "RUN α\n"
    assert result["stderr"] == "warning β\n"
    assert "RUN α\n" in "".join(chunks) and "warning β\n" in "".join(chunks)


def test_streaming_timeout_retains_progress_and_stops_child(tmp_path):
    chunks = []
    # This child needs only the standard library. Site hooks can consume the
    # entire 0.2-second deadline before our progress/cleanup fixture starts.
    result = run_process([sys.executable, "-S", "-c",
        "import time; print('RUN unfinished',flush=True); time.sleep(30)"],
        tmp_path, timeout=.2, on_output=chunks.append)
    assert result["timed_out"] and result["exit_code"] != 0
    assert result["stdout"] == "RUN unfinished\n" == "".join(chunks)


def test_checkpoint_ignores_disappearing_transient_lock_files(tmp_path, monkeypatch):
    from arcpuzzles import runtime
    root, output = tmp_path / "runtime", tmp_path / "output"
    lock = root / "checks/.lock_fixture_before/pid"
    lock.parent.mkdir(parents=True)
    lock.write_text("1234")
    report = root / "checks/fixture_before_lint.json"
    report.write_text('{"status":"PASS"}')
    output.mkdir()
    original_read = Path.read_bytes

    def disappearing(path):
        if path == lock:
            path.unlink()
            raise FileNotFoundError(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", disappearing)
    result = {"task_id": "fixture", "phase": "before"}
    runtime._save_check_checkpoint(root, output, result)
    assert result["evidence_sha256"] == {"checks/fixture_before_lint.json": runtime.sha256(report)}
    assert not (output / "checks/.lock_fixture_before").exists()


def test_checkpoint_does_not_hide_missing_durable_evidence(tmp_path, monkeypatch):
    from arcpuzzles import runtime
    root, output = tmp_path / "runtime", tmp_path / "output"
    report = root / "checks/fixture_before_lint.json"
    report.parent.mkdir(parents=True)
    report.write_text('{"status":"PASS"}')
    output.mkdir()
    original_read = Path.read_bytes

    def disappearing(path):
        if path == report:
            path.unlink()
            raise FileNotFoundError(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", disappearing)
    with pytest.raises(FileNotFoundError):
        runtime._save_check_checkpoint(root, output, {"task_id": "fixture", "phase": "before"})
