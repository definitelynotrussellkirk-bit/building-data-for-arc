import hashlib
from contextlib import nullcontext
import json
from pathlib import Path
import stat
import subprocess
import zipfile

import pytest

from arcpuzzles import Catalog
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return


def _sample(library, tmp_path, layout=True):
    questions = library / "REVIEW/questions"
    questions.mkdir(parents=True)
    (questions / "q.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1",
        "id": "q", "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    (library / "shared/unrelated.txt").write_text("not a runtime dependency\n")
    source = tmp_path / "source.zip"
    # This fixture tests full original-archive replay versus runtime-only
    # extraction, including deliberately unrelated and case-distinct files.
    # The normal rotating projection intentionally omits those files.
    build_full_packet(Catalog(library), library / "REVIEW", source,
                      workspace_layout=layout, selection_size=None)
    outer = tmp_path / "owner"
    with zipfile.ZipFile(source) as z:
        z.extractall(outer)
    work = outer / "WORK" if layout else outer
    contract = draw_main(work, bytes(32))
    task = contract["task_id"]
    home = work / "repo/generators" / task
    (home / "generator.py").write_text("VERSION = 'reviewed'\n")
    (home / "workspace").mkdir(exist_ok=True)
    (home / "workspace/new.py").write_text("VALUE = 7\n")
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (work / name).write_text(name + "\n")
    (work / "RESULTS.json").write_text(json.dumps({"completion_state": "complete", "stopping_reason": "test"}))
    returned = tmp_path / "returned.zip"
    build_full_return(work, returned)
    return source, returned, work, task


def _replay(source, returned, owner, out, **kwargs):
    from arcpuzzles.review_replay import replay_return
    return replay_return(source, returned, owner, out, **kwargs)


def _rewrite(source, target, changes=None, extra=None):
    with zipfile.ZipFile(source) as z, zipfile.ZipFile(target, "w") as out:
        for info in z.infolist():
            out.writestr(info, (changes or {}).get(info.filename, z.read(info)))
        if extra:
            out.writestr(*extra)
    return target


@pytest.mark.parametrize("layout", [False, True])
@pytest.mark.parametrize("closure", [False, True])
def test_replay_hashes_all_changed_files_and_labels_extraction_scope(library, tmp_path, layout, closure):
    source, returned, owner, task = _sample(library, tmp_path, layout)
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, returned)]
    # A parent Git repository must not cause git apply to report a successful no-op.
    parent = tmp_path / "parent"
    parent.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=parent, check=True)
    result = _replay(source, returned, owner, parent / "replay", runtime_closure=closure)
    work = Path(result["work_root"])
    assert Path(result["git_top_level"]) == work
    assert result["status"] == "patch_replay_passed_tests_pending"
    assert result["tests_run"] is False and result["training_admitted"] is False
    assert result["full_original_packet_extracted"] is not closure
    assert len(result["changed_files"]) == 2
    for row in result["changed_files"]:
        assert row["sha256"] == hashlib.sha256((owner / row["path"]).read_bytes()).hexdigest()
        assert (work / row["path"]).read_bytes() == (owner / row["path"]).read_bytes()
    assert (work / f"repo/generators/{task}/workspace/new.py").is_file()
    assert (work / "repo/shared/unrelated.txt").exists() is not closure
    if closure:
        assert result["extracted_files"] < result["original_files"]
    else:
        assert result["extracted_files"] == result["original_files"]
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, returned)] == hashes
    assert "reviewed" not in (library / f"generators/{task}/generator.py").read_text()
    assert json.loads(Path(result["receipt_path"]).read_text())["status"] == result["status"]


def test_replay_reports_post_patch_hash_mismatch_without_editing_owner(library, tmp_path):
    source, returned, owner, task = _sample(library, tmp_path)
    comparison = owner / f"repo/generators/{task}/workspace/new.py"
    comparison.write_text("DIFFERENT = True\n")
    out = tmp_path / "replay"
    with pytest.raises(ValueError, match="differs from reviewed"):
        _replay(source, returned, owner, out)
    assert comparison.read_text() == "DIFFERENT = True\n"
    assert json.loads((out / "replay.json").read_text())["status"] == "failed"


def test_replay_preserves_distinct_case_sensitive_source_paths(library, tmp_path):
    (library / "shared/Manifest.json").write_text("upper")
    (library / "shared/manifest.json").write_text("lower")
    if (library / "shared/Manifest.json").read_text() != "upper":
        pytest.skip("Fixture requires a case-sensitive filesystem")
    source, returned, owner, _ = _sample(library, tmp_path)
    result = _replay(source, returned, owner, tmp_path / "replay")
    work = Path(result["work_root"])
    assert (work / "repo/shared/Manifest.json").read_text() == "upper"
    assert (work / "repo/shared/manifest.json").read_text() == "lower"


@pytest.mark.parametrize("bad", ["hash", "extra", "symlink", "traversal", "duplicate"])
def test_replay_rejects_bad_original_archive(library, tmp_path, bad):
    source, returned, owner, task = _sample(library, tmp_path)
    changes = {f"WORK/repo/generators/{task}/generator.py": b"tampered\n"} if bad == "hash" else None
    extra = None
    if bad in {"extra", "traversal", "duplicate"}:
        name = {"extra": "WORK/unlisted.txt", "traversal": "../escaped.txt", "duplicate": "WORK/PACKET-MANIFEST.json"}[bad]
        extra = (name, b"unexpected")
    if bad == "symlink":
        info = zipfile.ZipInfo("WORK/link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        extra = (info, b"/tmp/elsewhere")
    with pytest.warns(UserWarning) if bad == "duplicate" else nullcontext():
        changed = _rewrite(source, tmp_path / "bad.zip", changes, extra)
    with pytest.raises(ValueError):
        _replay(changed, returned, owner, tmp_path / "replay")
    assert not (tmp_path / "escaped.txt").exists()


def test_replay_rejects_unvalidated_return_patch(library, tmp_path):
    source, returned, owner, _ = _sample(library, tmp_path)
    changed = _rewrite(returned, tmp_path / "bad-return.zip", {"patches/source.patch": b"unsafe patch\n"})
    with pytest.raises(ValueError):
        _replay(source, changed, owner, tmp_path / "replay")
    assert not (tmp_path / "replay").exists()


@pytest.mark.parametrize("destination", ["existing", "symlink", "inside_owner"])
def test_replay_does_not_overwrite_or_follow_output_paths(library, tmp_path, destination):
    source, returned, owner, _ = _sample(library, tmp_path)
    out = tmp_path / "replay"
    if destination == "existing":
        out.mkdir()
        (out / "keep").write_text("keep")
    elif destination == "symlink":
        link = tmp_path / "link"
        link.symlink_to(owner, target_is_directory=True)
        out = link / "replay"
    else:
        out = owner / "replay"
    with pytest.raises((ValueError, FileExistsError)):
        _replay(source, returned, owner, out)
    if destination == "existing":
        assert (out / "keep").read_text() == "keep"


def test_replay_ignores_inherited_git_directory(library, tmp_path, monkeypatch):
    source, returned, owner, _ = _sample(library, tmp_path)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=foreign, check=True)
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    result = _replay(source, returned, owner, tmp_path / "replay")
    assert Path(result["git_top_level"]) == Path(result["work_root"])


def test_replay_cli_is_available(library, tmp_path, capsys):
    from arcpuzzles.cli import main
    source, returned, owner, _ = _sample(library, tmp_path)
    assert main(["--library", str(library), "review", "replay-return",
        "--source-zip", str(source), "--return-zip", str(returned),
        "--compare-work", str(owner), "--out", str(tmp_path / "replay"),
        "--runtime-closure"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "patch_replay_passed_tests_pending"


def test_three_target_replay_extracts_all_task_closures(library, tmp_path):
    from test_review_full_collect import _return
    contract, result = _return(library, tmp_path, edit=True, repair_target_count=3)
    returned = tmp_path/'review_response_0.zip'
    work = tmp_path/'packet-0'
    report = _replay(tmp_path/'request-0.zip', returned, work, tmp_path/'replayed', runtime_closure=True)
    assert len(report['task_ids']) == 3
    assert len(report['changed_files']) == 3
    assert set(report['generator_sha256_by_task']) == set(report['task_ids'])
    for row in contract['repair_targets']:
        assert (Path(report['work_root'])/'repo'/row['generator']['generator']).is_file()
    assert report['tests_run'] is False
