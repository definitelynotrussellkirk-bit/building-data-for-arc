"""Small real-file checks for the reusable replay helper, without generator or solve labels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import sys
import zipfile

import pytest


HELPER = Path(__file__).resolve().parents[1] / "workspace" / "replay_return.py"
SPEC = importlib.util.spec_from_file_location("task_replay_return", HELPER)
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def original_zip(path, files, *, added=None, manifest_files=None):
    hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    manifest = {"schema": replay.SCHEMA, "files": hashes if manifest_files is None else manifest_files}
    with zipfile.ZipFile(path, "w") as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
        archive.writestr(replay.MANIFEST, json.dumps(manifest).encode())
        if added is not None:
            name, raw, mode = added
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, raw)
    return manifest


def test_original_files_and_identity_are_verified(tmp_path):
    original = tmp_path / "original.zip"
    manifest = original_zip(original, {"repo/example.txt": b"baseline\n"})
    report = {}
    replay.extract_original(original, tmp_path / "fresh", report)
    assert (tmp_path / "fresh/repo/example.txt").read_bytes() == b"baseline\n"
    assert report["original"]["all_manifest_files_verified"] is True
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    assert report["original"]["packet_id"] == hashlib.sha256(canonical).hexdigest()


def test_original_changed_bytes_fail_hash_verification(tmp_path):
    original = tmp_path / "original.zip"
    original_zip(original, {"repo/example.txt": b"changed\n"},
                 manifest_files={"repo/example.txt": hashlib.sha256(b"baseline\n").hexdigest()})
    report = {}
    with pytest.raises(replay.ReplayError, match="hash differs"):
        replay.extract_original(original, tmp_path / "fresh", report)
    assert report["original"]["all_manifest_files_verified"] is False


@pytest.mark.parametrize("name,mode", [
    ("../escaped.txt", stat.S_IFREG | 0o644),
    ("repo/link", stat.S_IFLNK | 0o777),
    ("REPO/EXAMPLE.TXT", stat.S_IFREG | 0o644),
])
def test_unsafe_original_members_are_rejected_before_extraction(tmp_path, name, mode):
    original = tmp_path / "original.zip"
    original_zip(original, {"repo/example.txt": b"safe\n"}, added=(name, b"bad\n", mode))
    with pytest.raises(replay.ReplayError):
        replay.extract_original(original, tmp_path / "fresh", {})
    assert not (tmp_path / "fresh").exists()
    assert not (tmp_path / "escaped.txt").exists()


def test_original_extra_member_is_rejected(tmp_path):
    original = tmp_path / "original.zip"
    original_zip(original, {"repo/example.txt": b"safe\n"},
                 added=("repo/unlisted.txt", b"extra\n", stat.S_IFREG | 0o644))
    with pytest.raises(replay.ReplayError, match="inventory differs"):
        replay.extract_original(original, tmp_path / "fresh", {})


def test_real_git_patch_routes_from_packet_root_without_repository(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("Git is required for the real patch routing check")
    source = tmp_path / "repo/generators/example/generator.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    patch = ("diff --git a/repo/generators/example/generator.py b/repo/generators/example/generator.py\n"
             "--- a/repo/generators/example/generator.py\n"
             "+++ b/repo/generators/example/generator.py\n"
             "@@ -1 +1 @@\n-value = 1\n+value = 2\n").encode()
    report = {}
    replay.apply_return_patch(tmp_path, patch, ["repo/generators/example/generator.py"], report, 10)
    assert source.read_text() == "value = 2\n"
    assert [row["exit_code"] for row in report["verification_commands"]] == [0, 0, 0]
    assert all(row["actual_cwd"] == str(tmp_path) for row in report["verification_commands"])
    assert report["patch"]["sha256"] == hashlib.sha256(patch).hexdigest()


def test_git_paths_reject_an_extra_quoted_diff_before_applying(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("Git is required for the real patch routing check")
    source = tmp_path / "repo/shared/tool.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    patch = ('diff --git "a/repo/shared/tool.py" "b/repo/shared/tool.py"\n'
             '--- "a/repo/shared/tool.py"\n'
             '+++ "b/repo/shared/tool.py"\n'
             '@@ -1 +1 @@\n-value = 1\n+value = 2\n').encode()
    with pytest.raises(replay.ReplayError, match="paths differ"):
        replay.apply_return_patch(tmp_path, patch, ["repo/generators/example/generator.py"], {}, 10)
    assert source.read_text() == "value = 1\n"


@pytest.mark.parametrize("change", ["modify", "add"])
def test_post_patch_invariant_rejects_unlisted_source_changes(tmp_path, change):
    source = tmp_path / "repo/shared/tool.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original\n")
    manifest = {"files": {"repo/shared/tool.py": hashlib.sha256(source.read_bytes()).hexdigest()}}
    if change == "modify":
        source.write_bytes(b"changed\n")
    else:
        (source.parent / "extra.py").write_bytes(b"extra\n")
    with pytest.raises(replay.ReplayError, match="outside validated paths|Undeclared file"):
        replay.verify_patched_source(tmp_path, manifest, [], {})


@pytest.mark.parametrize("wrong", ["solve", "expected"])
def test_generator_must_match_solve_and_optional_expected_hash(tmp_path, wrong):
    source = tmp_path / "repo/generators/example/generator.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source bytes\n")
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    validated = {"task_id": "example", "solve_status": "finished",
                 "solve_generator_sha256": actual, "solve_source_sha256": actual}
    expected = actual
    if wrong == "solve":
        validated["solve_generator_sha256"] = "0" * 64
    else:
        expected = "0" * 64
    with pytest.raises(replay.ReplayError, match="does not match"):
        replay.bind_generator(tmp_path, validated, expected, {})


def test_test_command_uses_wrapper_and_repo_relative_selected_tests():
    assert replay.focused_test_argv("example") == [
        sys.executable, "run_with_racket.py", sys.executable, "-m", "pytest", "-q",
        "generators/example/tests"]


def test_failing_command_retains_real_output_and_exit_status(tmp_path):
    report = {}
    with pytest.raises(replay.ReplayError, match="status 7"):
        replay.run_command("deliberate_failure", [sys.executable, "-c", "print('witness'); raise SystemExit(7)"],
                           tmp_path, report, 10)
    assert report["verification_commands"][0]["exit_code"] == 7
    assert report["verification_commands"][0]["stdout"] == "witness\n"


def test_existing_output_is_preserved_and_failure_report_is_written(tmp_path):
    original = tmp_path / "original.zip"
    original_zip(original, {"repo/example.txt": b"safe\n"})
    returned = tmp_path / "return.zip"
    returned.write_bytes(b"not reached")
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep me\n")
    report = tmp_path / "report.json"
    status = replay.main(["--original", str(original), "--return", str(returned),
                          "--out", str(out), "--report", str(report)])
    assert status == 1
    evidence = json.loads(report.read_text())
    assert evidence["completion_state"] == "blocked"
    assert "already exists" in evidence["error"]
    assert sentinel.read_text() == "keep me\n"
    assert evidence["verification_commands"] == []


def test_existing_report_is_never_overwritten(tmp_path):
    report = tmp_path / "report.json"
    report.write_text("preserve this\n")
    status = replay.main(["--original", str(tmp_path / "unused.zip"), "--return", str(tmp_path / "unused-return.zip"),
                          "--out", str(tmp_path / "fresh"), "--report", str(report)])
    assert status == 2
    assert report.read_text() == "preserve this\n"
