"""Fault-injection regressions using tiny synthetic packets, never live assignments."""
from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
REPO = Path(os.environ.get("DRAW_REPO", str(HERE.parent))).resolve()
ORIGINAL = REPO / "src/arcpuzzles/review_full_draw.py"
SOURCE = Path(os.environ.get("DRAW_SOURCE", str(REPO / "src/arcpuzzles/review_full_draw.py")))
TASK_A = "111111111111"
TASK_B = "222222222222"
SEED_A = bytes(32)
SEED_B = (1).to_bytes(32, "big")
JOURNAL = ".review/pending-main-draw.json"


def load_draw(source=SOURCE):
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location("arcpuzzles._journal_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def draw():
    return load_draw()


@pytest.fixture
def packet(tmp_path):
    root = tmp_path / "synthetic-packet"
    root.mkdir()
    content = {
        "repo/catalog/runtime_files.json": b"[]",
        "repo/catalog/authority_files.json": b"{}",
        "repo/shared/data/canonical/puzzles.jsonl": b'{"synthetic_fixture":true}\n',
        "repo/REVIEW/questions/q.json": b'{"id":"q","version":1}',
    }
    rows = {}
    for task in (TASK_A, TASK_B):
        content[f"repo/generators/{task}/SUMMARY.md"] = f"Synthetic {task}.\n".encode()
        content[f"repo/generators/{task}/generator.py"] = b"# Inert fixture; never executed.\n"
        rows[task] = {
            "approved": False, "generator": f"generators/{task}/generator.py",
            "generator_sha256": hashlib.sha256(content[f"repo/generators/{task}/generator.py"]).hexdigest(),
            "rule_task_id": task, "rule_hash": "0123456789ab",
        }
    for name, raw in content.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    manifest = {
        "schema": "arcpuzzles-full-packet-v2",
        "main_ids": [TASK_A, TASK_B], "all_ids": [TASK_A, TASK_B],
        "generators": rows,
        "questions": [{"id": "q", "version": 1,
                       "sha256": hashlib.sha256(content["repo/REVIEW/questions/q.json"]).hexdigest()}],
        "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in content.items()},
        "reviewer_solve": {"required": True, "blind": {"required": True}},
    }
    (root / "PACKET-MANIFEST.json").write_bytes(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())
    return root


def inject_partial_copy(monkeypatch, draw, fail_at=2):
    """Keep actual filesystem writes; inject the same errno during one copy."""
    copy = draw.shutil.copy2
    count = 0

    def failing(source, destination, *args, **kwargs):
        nonlocal count
        count += 1
        if count == fail_at:
            Path(destination).write_bytes(Path(source).read_bytes()[:5])
            raise OSError(errno.ENOSPC, "injected partial baseline copy", str(destination))
        return copy(source, destination, *args, **kwargs)

    monkeypatch.setattr(draw.shutil, "copy2", failing)


def read_contract(root):
    return json.loads((root / "ASSIGNMENT.json").read_text())


def assert_complete(root, contract):
    assert contract["task_id"] == TASK_A
    assert contract["seed"] == SEED_A.hex()
    assert read_contract(root) == contract
    assert json.loads((root / "BLIND_ASSIGNMENT.json").read_text())["task_id"] == TASK_B
    assert f"assignment: {TASK_A}" in (root / "DUTIES.md").read_text()
    assert json.loads((root / "RESULTS.json").read_text())["completion_state"] == "in_progress"
    for name, expected in contract["baseline_sha256"].items():
        copied = root / ".review/baseline" / name
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == expected
        assert copied.stat().st_mode & 0o222 == 0
    assert not (root / JOURNAL).exists()


def test_partial_copy_has_durable_original_seed_and_task(draw, packet, monkeypatch):
    # Moving the journal write after copying loses the only recoverable identity.
    monkeypatch.setattr(draw.os, "urandom", lambda n: SEED_A)
    inject_partial_copy(monkeypatch, draw)
    with pytest.raises(OSError) as error:
        draw.draw_main(packet)
    assert error.value.errno == errno.ENOSPC
    assert not (packet / "ASSIGNMENT.json").exists()
    assert (packet / JOURNAL).is_file(), "copy failed before seed/task were journaled"
    pending = json.loads((packet / JOURNAL).read_text())
    assert pending["contract"]["seed"] == SEED_A.hex()
    assert pending["contract"]["task_id"] == TASK_A


def test_retry_does_not_reroll_and_finishes_readonly_partial_baseline(draw, packet, monkeypatch):
    # Using fresh entropy on retry selects TASK_B and changes the original draw.
    with monkeypatch.context() as fault:
        fault.setattr(draw.os, "urandom", lambda n: SEED_A)
        inject_partial_copy(fault, draw)
        with pytest.raises(OSError):
            draw.draw_main(packet)
    monkeypatch.setattr(draw.os, "urandom", lambda n: SEED_B)
    contract = draw.draw_main(packet)
    assert_complete(packet, contract)


def test_pending_draw_rejects_conflicting_explicit_seed(draw, packet, monkeypatch):
    # An explicit new seed must not silently replace a committed pending draw.
    with monkeypatch.context() as fault:
        inject_partial_copy(fault, draw, fail_at=1)
        with pytest.raises(OSError):
            draw.draw_main(packet, seed=SEED_A)
    before = (packet / JOURNAL).read_bytes()
    with pytest.raises(ValueError, match="seed"):
        draw.draw_main(packet, seed=SEED_B)
    assert (packet / JOURNAL).read_bytes() == before
    assert_complete(packet, draw.draw_main(packet, seed=SEED_A))


def test_retry_finishes_outputs_after_assignment_already_exists(draw, packet, monkeypatch):
    # The old early return leaves an assignment without its required blind/duties files.
    with monkeypatch.context() as fault:
        def interrupted(*args):
            raise OSError(errno.ENOSPC, "injected finalization interruption")
        fault.setattr(draw, "blind_contract", interrupted)
        with pytest.raises(OSError):
            draw.draw_main(packet, seed=SEED_A)
    assert (packet / "ASSIGNMENT.json").is_file()
    assert not (packet / "BLIND_ASSIGNMENT.json").exists()
    assignment_before = (packet / "ASSIGNMENT.json").read_bytes()
    assert_complete(packet, draw.draw_main(packet))
    assert (packet / "ASSIGNMENT.json").read_bytes() == assignment_before


def test_changed_manifest_refuses_resume_without_replacing_journal(draw, packet, monkeypatch):
    # A pending draw is bound to the original packet, even if the pool order changes.
    with monkeypatch.context() as fault:
        inject_partial_copy(fault, draw, fail_at=1)
        with pytest.raises(OSError):
            draw.draw_main(packet, seed=SEED_A)
    before = (packet / JOURNAL).read_bytes()
    path = packet / "PACKET-MANIFEST.json"
    manifest = json.loads(path.read_bytes())
    manifest["main_ids"].reverse()
    path.write_bytes(json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())
    with pytest.raises(ValueError, match="packet"):
        draw.draw_main(packet)
    assert (packet / JOURNAL).read_bytes() == before


def test_corrupt_journal_is_a_visible_error_without_reroll(draw, packet, monkeypatch):
    # Falling back to fresh entropy when a journal is damaged destroys provenance.
    review = packet / ".review"
    review.mkdir()
    (packet / JOURNAL).write_text("{truncated")
    monkeypatch.setattr(draw.os, "urandom", lambda n: pytest.fail("unexpected reroll"))
    with pytest.raises(ValueError):
        draw.draw_main(packet)
    assert (packet / JOURNAL).read_text() == "{truncated"
    assert not (packet / "ASSIGNMENT.json").exists()


def test_unjournaled_partial_baseline_requires_explicit_recovery(draw, packet):
    # Installing this change cannot reconstruct a seed lost by the old implementation.
    partial = packet / ".review/baseline/repo/generators" / TASK_A / "SUMMARY.md"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"partial")
    with pytest.raises(ValueError, match="[Uu]njournaled"):
        draw.draw_main(packet, seed=SEED_B)
    assert partial.read_bytes() == b"partial"
    assert not (packet / JOURNAL).exists()


def test_process_death_during_copy_resumes_original_draw(packet):
    # OS process death must release the lock and preserve the journal without cleanup code.
    script = r'''
import importlib.util, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("arcpuzzles._draw_worker", sys.argv[2])
draw = importlib.util.module_from_spec(spec); spec.loader.exec_module(draw)
draw.os.urandom = lambda n: int(sys.argv[4]).to_bytes(32, "big")
if sys.argv[5] == "die":
    copy = draw.shutil.copy2
    def dying(source, destination, *args, **kwargs):
        copy(source, destination, *args, **kwargs)
        os._exit(73)
    draw.shutil.copy2 = dying
draw.draw_main(Path(sys.argv[3]))
'''
    common = [sys.executable, "-B", "-c", script, str(REPO / "src"), str(SOURCE), str(packet)]
    first = subprocess.run([*common, "0", "die"], capture_output=True, text=True, timeout=20)
    assert first.returncode == 73, first.stderr
    assert (packet / JOURNAL).is_file(), "hard exit lost the selected draw"
    second = subprocess.run([*common, "1", "resume"], capture_output=True, text=True, timeout=20)
    assert second.returncode == 0, second.stderr
    assert_complete(packet, read_contract(packet))


def test_completed_draw_remains_idempotent_after_source_edits(draw, packet, monkeypatch):
    # Reviewers may legitimately edit selected source after a completed draw.
    expected = draw.draw_main(packet, seed=SEED_A)
    source = packet / "repo/generators" / TASK_A / "generator.py"
    source.write_text("# Reviewer repair.\n")
    monkeypatch.setattr(draw.os, "urandom", lambda n: pytest.fail("completed draw rerolled"))
    assert draw.draw_main(packet) == expected


def test_journal_publish_failure_stops_before_any_baseline_copy(draw, packet, monkeypatch):
    # A journal write that cannot commit must never permit baseline side effects.
    replace = draw.os.replace

    def fail_journal(source, destination):
        if Path(destination).name == "pending-main-draw.json":
            raise OSError(errno.ENOSPC, "injected journal publication failure")
        return replace(source, destination)

    monkeypatch.setattr(draw.os, "replace", fail_journal)
    with pytest.raises(OSError) as error:
        draw.draw_main(packet, seed=SEED_A)
    assert error.value.errno == errno.ENOSPC
    assert not (packet / JOURNAL).exists()
    assert not (packet / ".review/baseline").exists()
    assert not (packet / "ASSIGNMENT.json").exists()


def test_changed_copy_is_not_published_and_original_draw_can_resume(draw, packet, monkeypatch):
    # A source change between initial verification and copying must not freeze bad bytes.
    with monkeypatch.context() as fault:
        copy = draw.shutil.copy2

        def corrupting(source, destination, *args, **kwargs):
            result = copy(source, destination, *args, **kwargs)
            Path(destination).write_bytes(b"different bytes")
            return result

        fault.setattr(draw.shutil, "copy2", corrupting)
        with pytest.raises(ValueError, match="changed"):
            draw.draw_main(packet, seed=SEED_A)
    assert not (packet / "ASSIGNMENT.json").exists()
    assert_complete(packet, draw.draw_main(packet))


def test_preexisting_results_are_preserved(draw, packet):
    # Resumable finalization must keep the original do-not-overwrite RESULTS convention.
    raw = b'{"completion_state":"in_progress","author_note":"keep this"}\n'
    (packet / "RESULTS.json").write_bytes(raw)
    draw.draw_main(packet, seed=SEED_A)
    assert (packet / "RESULTS.json").read_bytes() == raw
