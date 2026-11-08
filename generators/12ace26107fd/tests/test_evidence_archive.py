"""CPU-only archival fixture tests in portable library and runtime layouts."""
import gzip
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import find_root, load_selected_generator

TASK_ID = "12ace26107fd"
ROOT = find_root(__file__)
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
IDENTITY = f"generators/{TASK_ID}/workspace/evidence_archive.py"
if MANIFEST.is_file():
    entries = [entry for entry in json.loads(MANIFEST.read_text())["files"]
               if entry["library_path"] == IDENTITY]
    entries.sort(key=lambda entry: entry["runtime_path"] == IDENTITY)
    assert entries, "runtime manifest must retain the archive utility workspace"
    TOOL = ROOT / entries[0]["runtime_path"]
else:
    _, selected_source, _ = load_selected_generator(TASK_ID, root=ROOT)
    TOOL = selected_source.parent / "workspace/evidence_archive.py"
assert TOOL.resolve().is_relative_to(ROOT), "archive utility must belong to the selected source tree"


def call(root, *args, ok=True):
    assert TOOL.is_file(), "requested evidence archive CLI is not implemented"
    result = subprocess.run([sys.executable, str(TOOL), "--root", str(root), *args], capture_output=True, text=True)
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
    return result


def put(root, name, raw=b"failure: retained exactly\n" * 100):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def manifest(root):
    return json.loads((root / "checks/ARCHIVE-MANIFEST.json").read_text())


def test_pack_verify_restore_preserves_binary_failures_and_is_idempotent(tmp_path):
    raw = bytes(range(256)) * 40 + b"\x00FAIL\r\n"
    source = put(tmp_path, "checks/failed.bin", raw)
    call(tmp_path, "pack", "checks/failed.bin")
    assert not source.exists()
    row = manifest(tmp_path)["entries"][0]
    assert row["original_path"] == "checks/failed.bin"
    assert row["original_bytes"] == len(raw)
    compressed = (tmp_path / row["compressed_path"]).read_bytes()
    assert compressed[4:8] == b"\x00\x00\x00\x00"
    assert gzip.decompress(compressed) == raw
    call(tmp_path, "verify")
    call(tmp_path, "restore")
    assert source.read_bytes() == raw
    call(tmp_path, "restore")
    assert source.read_bytes() == raw


def test_gzip_is_deterministic_and_second_pack_appends_manifest(tmp_path):
    packed = []
    for name in ("one", "two"):
        root = tmp_path / name
        put(root, "checks/a.log")
        call(root, "pack", "checks/a.log")
        row = manifest(root)["entries"][0]
        packed.append((root / row["compressed_path"]).read_bytes())
    assert packed[0] == packed[1]
    root = tmp_path / "one"
    put(root, "checks/b.log", b"other failure")
    call(root, "pack", "checks/b.log")
    assert len(manifest(root)["entries"]) == 2
    call(root, "restore")
    assert (root / "checks/a.log").is_file()
    assert (root / "checks/b.log").read_bytes() == b"other failure"


def test_corruption_is_detected_before_restore(tmp_path):
    put(tmp_path, "checks/a.log")
    call(tmp_path, "pack", "checks/a.log")
    row = manifest(tmp_path)["entries"][0]
    compressed = tmp_path / row["compressed_path"]
    compressed.write_bytes(compressed.read_bytes() + b"corrupt")
    call(tmp_path, "verify", ok=False)
    call(tmp_path, "restore", ok=False)
    assert not (tmp_path / "checks/a.log").exists()


@pytest.mark.parametrize("bad", ["../outside.log", "/tmp/outside.log", "checks/../outside.log"])
def test_traversal_refusal_preflights_whole_batch(tmp_path, bad):
    source = put(tmp_path, "checks/a.log")
    call(tmp_path, "pack", "checks/a.log", bad, ok=False)
    assert source.is_file()
    assert not (tmp_path / "checks/ARCHIVE-MANIFEST.json").exists()


def test_symlink_file_and_symlink_parent_are_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    put(outside, "a.log")
    root = tmp_path / "WORK"
    root.mkdir()
    (root / "link.log").symlink_to(outside / "a.log")
    (root / "linked").symlink_to(outside, target_is_directory=True)
    call(root, "pack", "link.log", ok=False)
    call(root, "pack", "linked/a.log", ok=False)
    assert (outside / "a.log").is_file()


def test_restore_conflict_does_not_overwrite_or_partially_restore(tmp_path):
    put(tmp_path, "checks/a.log")
    put(tmp_path, "checks/b.log")
    call(tmp_path, "pack", "checks/a.log", "checks/b.log")
    put(tmp_path, "checks/b.log", b"different newer evidence")
    call(tmp_path, "restore", ok=False)
    assert not (tmp_path / "checks/a.log").exists()
    assert (tmp_path / "checks/b.log").read_bytes() == b"different newer evidence"


def test_existing_compressed_conflict_preserves_raw_and_existing_bytes(tmp_path):
    source = put(tmp_path, "checks/a.log")
    compressed = put(tmp_path, "checks/archived/checks/a.log.gz", b"unrelated data")
    call(tmp_path, "pack", "checks/a.log", ok=False)
    assert source.is_file()
    assert compressed.read_bytes() == b"unrelated data"


@pytest.mark.parametrize("mutation", ["path", "size", "hash"])
def test_malicious_or_wrong_manifest_metadata_is_refused(tmp_path, mutation):
    put(tmp_path, "checks/a.log")
    call(tmp_path, "pack", "checks/a.log")
    value = manifest(tmp_path)
    row = value["entries"][0]
    if mutation == "path":
        row["original_path"] = "../outside.log"
    elif mutation == "size":
        row["original_bytes"] = 1
    else:
        row["original_sha256"] = "0" * 64
    (tmp_path / "checks/ARCHIVE-MANIFEST.json").write_text(json.dumps(value))
    call(tmp_path, "verify", ok=False)
    call(tmp_path, "restore", ok=False)
    assert not (tmp_path / "checks/a.log").exists()
