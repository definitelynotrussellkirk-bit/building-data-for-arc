import json
from pathlib import Path
import zipfile
import stat

import pytest

from arcpuzzles import Catalog, review
from arcpuzzles.review_return import intake


def returned_zip(path, contract, *, extra=None, results=None):
    payload = {"ASSIGNMENT.json": contract, "REVIEW.md": "useful findings\n",
               "FEEDBACK_TO_CODEX.md": "# General feedback\n"}
    payload.update(extra or {})
    payload["RESULTS.json"] = json.dumps(results or {
        "schema": "arcpuzzles-review-results-v1", "assignment_id": json.loads(contract)["assignment_id"],
        "generator_id": json.loads(contract)["task_id"], "completion_state": "complete",
        "changed_components": [], "patches": [], "checks": [], "remaining_failures": [],
        "improvement_claim": "No safe improvement found"})
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in payload.items():
            archive.writestr(name, data)


def assignment(library, tmp_path):
    root = tmp_path / "REVIEW"
    row = review.pick(Catalog(library), task_id="aaaa00000001", review_root=root)
    return root, row, (Path(row["directory"]) / "ASSIGNMENT.json").read_text()


def test_intake_retains_original_and_versions_without_duplicate(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    first = tmp_path / "first.zip"
    returned_zip(first, contract)
    one = intake(root, first)
    assert one["status"] == "accepted"
    assert one["version"] == 1
    assert Path(one["archive_path"]).read_bytes() == first.read_bytes()
    assert Path(one["receipt_path"]).is_file()
    assert intake(root, first)["version"] == 1
    second = tmp_path / "second.zip"
    returned_zip(second, contract, extra={"REVIEW.md": "More findings\n"})
    two = intake(root, second)
    assert two["version"] == 2
    assert Path(one["archive_path"]).read_bytes() == first.read_bytes()


@pytest.mark.parametrize("name", ["../escape", "/absolute", "x/../../escape", "C:/drive", "a\\b"])
def test_unsafe_paths_are_rejected_before_extraction(library, tmp_path, name):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "bad.zip"
    returned_zip(archive, contract, extra={name: "bad"})
    result = intake(root, archive)
    assert result["status"] == "rejected"
    assert Path(result["archive_path"]).read_bytes() == archive.read_bytes()
    assert not Path(result["archive_path"]).parent.joinpath("extracted").exists()
    assert not (tmp_path / "escape").exists()


def test_duplicate_and_case_colliding_members_rejected(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("ASSIGNMENT.json", contract)
        handle.writestr("RESULTS.json", "{}")
        handle.writestr("x.txt", "one")
        handle.writestr("X.txt", "two")
    result = intake(root, archive)
    assert result["status"] == "rejected"
    assert "collision" in result["reason"].lower()


def test_normalized_duplicate_path_is_rejected(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "normalized.zip"
    returned_zip(archive, contract, extra={"notes/a.txt": "one", "notes//a.txt": "two"})
    result = intake(root, archive)
    assert result["status"] == "rejected"
    assert not Path(result["archive_path"]).parent.joinpath("extracted").exists()


def test_symlink_and_oversized_zip_are_retained_without_extraction(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    symlink = tmp_path / "symlink.zip"
    with zipfile.ZipFile(symlink, "w") as handle:
        handle.writestr("ASSIGNMENT.json", contract)
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        handle.writestr(info, "../outside")
    linked = intake(root, symlink)
    assert linked["status"] == "rejected"
    assert not Path(linked["archive_path"]).parent.joinpath("extracted").exists()
    too_big = tmp_path / "oversized.zip"
    returned_zip(too_big, contract, extra={"checks/huge.log": b"x" * (25 * 1024 * 1024 + 1)})
    large = intake(root, too_big)
    assert large["status"] == "rejected"
    assert "limit" in large["reason"]
    assert not Path(large["archive_path"]).parent.joinpath("extracted").exists()


def test_member_count_limit_rejects_archive(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "too-many.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("ASSIGNMENT.json", contract)
        for i in range(256):
            handle.writestr(f"notes/{i:03d}.txt", "x")
    result = intake(root, archive)
    assert result["status"] == "rejected"
    assert "limit" in result["reason"]


def test_wrong_assignment_and_undeclared_patch_rejected(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "wrong.zip"
    wrong = json.loads(contract)
    wrong["generator"]["sha256"] = "0" * 64
    returned_zip(archive, json.dumps(wrong))
    result = intake(root, archive)
    assert result["status"] == "rejected"
    assert "ASSIGNMENT" in result["reason"]
    archive2 = tmp_path / "undeclared.zip"
    returned_zip(archive2, contract, extra={"patches/hidden.patch": "diff"})
    result2 = intake(root, archive2)
    assert result2["status"] == "rejected"
    assert "declare" in result2["reason"].lower()


def test_historical_unknown_return_is_retained_for_mapping(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    archive = tmp_path / "old.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("README.md", "Old reviewer notes")
    result = intake(root, archive)
    assert result["status"] == "mapping_required"
    assert Path(result["archive_path"]).read_bytes() == archive.read_bytes()


def test_malformed_results_and_unfinished_template_are_not_accepted(library, tmp_path):
    root, row, contract = assignment(library, tmp_path)
    bad = tmp_path / "malformed.zip"
    returned_zip(bad, contract, results={"schema": "arcpuzzles-review-results-v1",
        "assignment_id": row["id"], "generator_id": row["task_id"],
        "completion_state": "complete", "patches": "not-a-list", "checks": []})
    assert intake(root, bad)["status"] == "rejected"
    unfinished = tmp_path / "unfinished.zip"
    returned_zip(unfinished, contract, results={"schema": "arcpuzzles-review-results-v1",
        "assignment_id": row["id"], "generator_id": row["task_id"],
        "completion_state": "in_progress", "patches": [], "checks": []})
    assert intake(root, unfinished)["status"] == "partial"
