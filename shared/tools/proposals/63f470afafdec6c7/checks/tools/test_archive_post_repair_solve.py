"""Archival safety checks use temporary public fixtures, never a real solve."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@lru_cache(maxsize=1)
def helper():
    path = Path(__file__).with_name("archive_post_repair_solve.py")
    assert path.is_file(), "The public solve archival helper must exist."
    spec = importlib.util.spec_from_file_location("archive_public_solve", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def work(tmp_path):
    path = tmp_path / "WORK"
    solve = path / "solve"
    (solve / "attempts" / "0001").mkdir(parents=True)
    (solve / "empty-directory").mkdir()
    (solve / "solution.py").write_text("def solve(grid):\n    return grid\n")
    (solve / "summary.json").write_text(json.dumps({"task_id": "public-fixture", "attempts": 1}))
    (solve / "FINISHED_NOTES.md").write_text("Original final work log.\n")
    (solve / "attempts" / "0001" / "solution.py").write_text("def solve(grid):\n    return []\n")
    (solve / "attempts" / "0001" / "SOLVE_NOTES.md").write_text("Actual earlier attempt.\n")
    return path


def files_below(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def test_preview_does_not_create_or_change_any_path(work):
    module = helper()
    before = files_below(work)
    result = module.archive_public_solve(work, "prior-source", "Generator bytes changed")
    assert result["mode"] == "preview"
    assert files_below(work) == before
    assert not (work / "checks").exists()
    assert (work / "solve" / "empty-directory").is_dir()


def test_apply_moves_complete_tree_and_records_verified_hashes(work):
    module = helper()
    original = files_below(work / "solve")
    result = module.archive_public_solve(work, "prior-source", "Generator bytes changed", apply=True)
    container = work / "checks" / "prior-solve" / "prior-source"
    archived = container / "solve"
    assert not (work / "solve").exists()
    assert files_below(archived) == original
    assert (archived / "empty-directory").is_dir()
    receipt = json.loads((container / "ARCHIVE.json").read_text())
    assert receipt == result
    assert receipt["mode"] == "applied"
    assert receipt["before"] == receipt["after"]
    assert receipt["verified"] is True
    assert receipt["file_count"] == 5
    assert receipt["public_summary"] == {"task_id": "public-fixture", "attempts": 1}
    assert receipt["reason"] == "Generator bytes changed"
    for name, contents in original.items():
        assert receipt["before"]["files"][name]["sha256"] == hashlib.sha256(contents).hexdigest()
    assert receipt["attempt_source_hashes"] == {
        "attempts/0001/solution.py": hashlib.sha256(original["attempts/0001/solution.py"]).hexdigest()
    }


def test_cli_defaults_to_preview(work):
    module = helper()
    result = subprocess.run([sys.executable, module.__file__, "--work", str(work),
                             "--archive-name", "cli-preview", "--reason", "A public reason"],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["mode"] == "preview"
    assert (work / "solve").is_dir()
    assert not (work / "checks").exists()


def test_existing_archive_is_never_overwritten(work):
    module = helper()
    container = work / "checks" / "prior-solve" / "existing"
    container.mkdir(parents=True)
    marker = container / "keep.txt"
    marker.write_text("Preexisting evidence")
    before = files_below(work)
    with pytest.raises((ValueError, FileExistsError), match="exist"):
        module.archive_public_solve(work, "existing", "Must retain", apply=True)
    assert files_below(work) == before


@pytest.mark.parametrize("name", [".", "..", "../escape", "a/b", "a\\b", "", "/absolute", "a b", ".hidden"])
def test_unsafe_archive_names_are_rejected_before_mutation(work, name):
    module = helper()
    before = files_below(work)
    with pytest.raises(ValueError, match="archive.name"):
        module.archive_public_solve(work, name, "Invalid name", apply=True)
    assert files_below(work) == before
    assert not (work / "checks").exists()


@pytest.mark.parametrize("kind", ["source", "file", "directory", "broken", "checks_parent"])
def test_symlinks_are_rejected_without_following_them(work, tmp_path, kind):
    module = helper()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "do-not-read.txt"
    secret.write_text("Fixture outside the public source")
    if kind == "source":
        (work / "solve").rename(work / "original-solve")
        (work / "solve").symlink_to(work / "original-solve", target_is_directory=True)
    elif kind == "file":
        (work / "solve" / "linked.txt").symlink_to(secret)
    elif kind == "directory":
        (work / "solve" / "linked-dir").symlink_to(outside, target_is_directory=True)
    elif kind == "broken":
        (work / "solve" / "broken").symlink_to(outside / "absent")
    else:
        (work / "checks").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        module.archive_public_solve(work, "unsafe", "Reject links", apply=True)
    assert (work / "solve").exists()
    assert secret.read_text() == "Fixture outside the public source"
    assert not (outside / "prior-solve").exists()


def test_fifo_is_rejected_without_opening_it(work):
    module = helper()
    os.mkfifo(work / "solve" / "pipe")
    with pytest.raises(ValueError, match="regular"):
        module.archive_public_solve(work, "fifo", "Reject special files", apply=True)
    assert (work / "solve").is_dir()
    assert not (work / "checks").exists()


def test_work_path_must_be_absolute():
    module = helper()
    with pytest.raises(ValueError, match="absolute"):
        module.archive_public_solve("relative/WORK", "name", "reason", apply=True)


def test_missing_source_creates_no_archive(tmp_path):
    module = helper()
    work = tmp_path / "WORK"
    work.mkdir()
    with pytest.raises((ValueError, FileNotFoundError), match="solve"):
        module.archive_public_solve(work, "name", "reason", apply=True)
    assert list(work.iterdir()) == []


def test_failed_rename_removes_only_the_empty_reserved_container(work, monkeypatch):
    module = helper()
    before = files_below(work / "solve")

    def cannot_move(*args, **kwargs):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(module.os, "rename", cannot_move)
    with pytest.raises(OSError, match="simulated rename failure"):
        module.archive_public_solve(work, "failed-move", "Retain original", apply=True)
    assert files_below(work / "solve") == before
    assert not (work / "checks" / "prior-solve" / "failed-move").exists()


def test_private_sibling_is_never_opened(work, monkeypatch):
    module = helper()
    private = work / ".review" / "private"
    private.mkdir(parents=True)
    (private / "labels.json").write_text("Never inspect this fixture")
    real_open = module.os.open

    def refuse_private(path, *args, **kwargs):
        if ".review" in Path(path).parts:
            raise AssertionError("The helper attempted to open private state")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", refuse_private)
    assert module.archive_public_solve(work, "public-only", "Preview public source")["mode"] == "preview"


def test_private_named_subtree_inside_solve_is_rejected(work):
    module = helper()
    (work / "solve" / ".review").mkdir()
    with pytest.raises(ValueError, match="private"):
        module.archive_public_solve(work, "private-tree", "Reject private subtree", apply=True)
    assert not (work / "checks").exists()


def test_blank_reason_is_rejected(work):
    module = helper()
    with pytest.raises(ValueError, match="reason"):
        module.archive_public_solve(work, "no-reason", "   ", apply=True)
