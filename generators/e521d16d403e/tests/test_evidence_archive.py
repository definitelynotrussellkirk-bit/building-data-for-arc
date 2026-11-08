"""Synthetic round trips and destructive-edge guards for evidence compression."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "workspace" / "compact_evidence.py"
SPEC = importlib.util.spec_from_file_location("evidence_archive_checker_tests", SOURCE)
ARCHIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARCHIVE)


def fixture(root, name="payload.json", content=b"evidence\n" * 100):
    path = root / "checks" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path, "checks/" + name


def test_binary_and_empty_roundtrip_with_idempotent_compression(tmp_path):
    root = tmp_path / "packet"
    expected = {"binary file.json": bytes(range(256)) * 9, "empty.json": b""}
    paths = [fixture(root, name, content)[1] for name, content in expected.items()]
    ARCHIVE.compress(root, paths)
    manifest = root / ARCHIVE.MANIFEST
    first_manifest = manifest.read_bytes()
    ARCHIVE.compress(root, paths)
    assert manifest.read_bytes() == first_manifest
    assert ARCHIVE.verify(root)["verified_archives"] == 2
    destination = tmp_path / "restored"
    ARCHIVE.restore(root, destination)
    for name, content in expected.items():
        assert (destination / "checks" / name).read_bytes() == content
        assert not (root / "checks" / name).exists()
        assert (root / "checks" / (name + ".gz")).is_file()
    with pytest.raises(FileExistsError):
        ARCHIVE.restore(root, destination)


def test_gzip_is_independent_of_source_name_and_timestamp(tmp_path):
    results = []
    for number, name in enumerate(("first.json", "second.json")):
        root = tmp_path / str(number)
        original, relative = fixture(root, name)
        ARCHIVE.compress(root, [relative])
        results.append(original.with_name(name + ".gz").read_bytes())
    assert results[0] == results[1]
    assert results[0][4:8] == b"\x00\x00\x00\x00"


def test_untracked_archive_collision_preserves_both_files(tmp_path):
    original, relative = fixture(tmp_path)
    archive = original.with_suffix(".json.gz")
    archive.write_bytes(b"pre-existing bytes")
    with pytest.raises(FileExistsError, match="collision"):
        ARCHIVE.compress(tmp_path, [relative])
    assert original.read_bytes() == b"evidence\n" * 100
    assert archive.read_bytes() == b"pre-existing bytes"
    assert not (tmp_path / ARCHIVE.MANIFEST).exists()


@pytest.mark.parametrize("invalid", ["checks/../outside.json", "/absolute.json", "outside.json",
                                     "checks/summary.json", "checks/RUNTIME_MANIFEST.json",
                                     "checks/part\\outside.json"])
def test_entire_selection_is_preflighted_before_mutation(tmp_path, invalid):
    original, relative = fixture(tmp_path)
    with pytest.raises((ValueError, FileNotFoundError)):
        ARCHIVE.compress(tmp_path, [relative, invalid])
    assert original.exists()
    assert not original.with_suffix(".json.gz").exists()


def test_leaf_and_ancestor_symlinks_are_refused(tmp_path):
    root = tmp_path / "packet"
    original, relative = fixture(root)
    (root / "checks/link.json").symlink_to(original)
    (root / "checks/directory").symlink_to(root / "checks", target_is_directory=True)
    for candidate in ("checks/link.json", "checks/directory/payload.json"):
        with pytest.raises(ValueError, match="Symlink"):
            ARCHIVE.compress(root, [candidate])
    assert original.exists()


def test_failed_manifest_commit_never_removes_original(tmp_path, monkeypatch):
    original, relative = fixture(tmp_path)
    def fail(*args):
        raise OSError("simulated manifest failure")
    monkeypatch.setattr(ARCHIVE, "write_manifest", fail)
    with pytest.raises(OSError, match="manifest failure"):
        ARCHIVE.compress(tmp_path, [relative])
    assert original.exists()
    assert gzip.decompress(original.with_suffix(".json.gz").read_bytes()) == original.read_bytes()


def test_original_modified_after_manifest_commit_is_preserved(tmp_path, monkeypatch):
    original, relative = fixture(tmp_path)
    commit = ARCHIVE.write_manifest
    def edit_after_commit(root, data):
        commit(root, data)
        original.write_bytes(b"new evidence still being written")
    monkeypatch.setattr(ARCHIVE, "write_manifest", edit_after_commit)
    with pytest.raises(ValueError, match="changed before removal"):
        ARCHIVE.compress(tmp_path, [relative])
    assert original.read_bytes() == b"new evidence still being written"
    assert ARCHIVE.verify(tmp_path)["verified_archives"] == 1


def test_corrupt_archive_cannot_produce_a_restoration_directory(tmp_path):
    root = tmp_path / "packet"
    original, relative = fixture(root)
    ARCHIVE.compress(root, [relative])
    original.with_suffix(".json.gz").write_bytes(b"corrupted")
    destination = tmp_path / "restored"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        ARCHIVE.restore(root, destination)
    assert not destination.exists()


def test_extra_gzip_member_cannot_exceed_declared_restored_size(tmp_path):
    root = tmp_path / "packet"
    original, relative = fixture(root)
    ARCHIVE.compress(root, [relative])
    archive = original.with_suffix(".json.gz")
    archive.write_bytes(archive.read_bytes() + gzip.compress(b"unexpected extra bytes", mtime=0))
    manifest = root / ARCHIVE.MANIFEST
    data = json.loads(manifest.read_text())
    data["entries"][0]["compressed_size"] = archive.stat().st_size
    data["entries"][0]["compressed_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="byte limit"):
        ARCHIVE.restore(root, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
