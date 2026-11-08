import io
import hashlib
import json
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main, draw_audit
from arcpuzzles.review_full_return import build_full_return, validate_full_return


def test_patch_headers_are_distinguished_from_source_lines_inside_hunks():
    from arcpuzzles.review_full_return import _patch_paths
    path = "repo/generators/aaaa00000003/generator.py"
    contract = {"task_id": "aaaa00000003", "baseline_sha256": {}}
    patch = (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
             "@@ -1 +1 @@\n--- removed docstring separator\n+++ added docstring separator\n")
    assert _patch_paths(patch, contract) == [path]


@pytest.mark.parametrize("header", ["--- a/repo/shared/rogue.py", "+++ b/repo/shared/rogue.py",
                                   "--- x/repo/generators/aaaa00000003/generator.py"])
def test_real_patch_headers_cannot_escape_or_spoof_the_selected_file(header):
    from arcpuzzles.review_full_return import _patch_paths
    path = "repo/generators/aaaa00000003/generator.py"
    contract = {"task_id": "aaaa00000003", "baseline_sha256": {}}
    before = header if header.startswith("---") else f"--- a/{path}"
    after = header if header.startswith("+++") else f"+++ b/{path}"
    patch = f"diff --git a/{path} b/{path}\n{before}\n{after}\n@@ -1 +1 @@\n-old\n+new\n"
    with pytest.raises(ValueError, match="Patch header"):
        _patch_paths(patch, contract)


def _draw(library, tmp_path):
    (library / "README.md").write_text("fixture docs\n")
    q = library / "REVIEW/questions"
    q.mkdir(parents=True)
    (q / "q.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1", "id": "q",
        "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "request.zip")
    packet = tmp_path / "packet"
    packet.mkdir()
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(packet)
    draw_main(packet, (2).to_bytes(32, "big"))
    return packet


def _docs(packet):
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (packet / name).write_text(name + "\n")
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": "complete", "stopping_reason": "done"}))


def test_return_declares_every_artifact_and_echoes_contract(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    audit = draw_audit(packet, bytes(32))
    (packet / "AUDIT.md").write_text("".join(
        f"## {row['task_id']}\npossible shortcut\n\n" for row in audit["targets"]))
    (packet / "repo/generators/aaaa00000003/generator.py").write_text("VERSION = 'better'\n")
    result = build_full_return(packet, tmp_path / "review_response_test.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        manifest = json.loads((packet / "PACKET-MANIFEST.json").read_text())
        checked = validate_full_return(archive, manifest)
        assert checked["completion_state"] == "complete"
        assert checked["audit_targets"] == [row["task_id"] for row in audit["targets"]]
        assert archive.read("ASSIGNMENT.json") == (packet / "ASSIGNMENT.json").read_bytes()
        data = json.loads(archive.read("RESULTS.json"))
        declared = {item["path"] for item in data["artifacts"]}
        assert declared == set(archive.namelist()) - {"ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "RESULTS.json"}
        assert "AUDIT.md" in declared
        assert "patches/source.patch" in declared


def test_two_audit_return_requires_a_section_for_each_target(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    audit = draw_audit(packet, bytes(32))
    (packet / "AUDIT.md").write_text(f"## {audit['targets'][0]['task_id']}\nFinding\n")
    with pytest.raises(ValueError, match="audit target section"):
        build_full_return(packet, tmp_path / "missing-audit.zip")


def test_legacy_single_audit_return_remains_readable(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    manifest = json.loads((packet / "PACKET-MANIFEST.json").read_text())
    target = manifest["all_ids"][0]
    (packet / "AUDIT_ASSIGNMENT.json").write_text(json.dumps({
        "schema": "arcpuzzles-full-audit-v2",
        "packet_id": json.loads((packet / "ASSIGNMENT.json").read_text())["packet_id"],
        "seed": bytes(32).hex(), "task_id": target,
        "generator_sha256": manifest["generators"][target]["generator_sha256"]}))
    (packet / "AUDIT.md").write_text("Legacy freeform finding\n")
    result = build_full_return(packet, tmp_path / "legacy-audit.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        assert validate_full_return(archive, manifest)["audit_targets"] == [target]


def test_return_ignores_generated_python_bytecode_in_selected_workspace(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    cache = packet / "repo/generators/aaaa00000003/workspace/__pycache__/probe.cpython-312.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"compiled cache")
    result = build_full_return(packet, tmp_path / "with-cache.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        assert not any("__pycache__" in name for name in archive.namelist())


def test_return_rejects_shared_edits_and_nonassigned_rule_rows(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    shared = packet / "repo/shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in shared.read_text().splitlines()]
    rows[0]["program_solution"] = "(wrong)"
    shared.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError):
        build_full_return(packet, tmp_path / "bad.zip")
    shared.write_bytes((packet / ".review/baseline/repo/shared/data/canonical/puzzles.jsonl").read_bytes())
    (packet / "repo/README.md").write_text("changed")
    with pytest.raises(ValueError):
        build_full_return(packet, tmp_path / "bad.zip")
    (packet / "repo/README.md").write_text("fixture docs\n")
    rogue = packet / "repo/shared/rogue.py"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text("surprise\n")
    with pytest.raises(ValueError):
        build_full_return(packet, tmp_path / "bad.zip")


def test_no_change_partial_return_keeps_decisions_without_directory_members(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": "blocked", "stopping_reason": "missing example"}))
    result = build_full_return(packet, tmp_path / "review_response_partial.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        assert all(not info.is_dir() for info in archive.infolist())
        checked = validate_full_return(archive, json.loads((packet / "PACKET-MANIFEST.json").read_text()))
        assert checked["completion_state"] == "blocked"
        assert "DECISIONS.md" in archive.namelist()
        assert not any(name.startswith("patches/") for name in archive.namelist())


def test_return_rejects_modified_frozen_baseline(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    baseline = packet / ".review/baseline/repo/generators/aaaa00000003/generator.py"
    baseline.chmod(0o644)
    baseline.write_text("fabricated baseline\n")
    with pytest.raises(ValueError, match="baseline"):
        build_full_return(packet, tmp_path / "review_response_bad.zip")


def test_return_builds_hash_bound_intake_summary_with_feedback_and_commands(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    (packet / "FEEDBACK_TO_CODEX.md").write_text("**F1: Show progress.**\n\nEvidence: checks/after.json\n")
    command = {"cwd": "repo", "argv": ["python3", "-m", "pytest", "-q"],
               "evidence_paths": ["checks/after.json"], "exit_code": 0}
    (packet / "checks").mkdir()
    (packet / "checks/after.json").write_text('{"passed": true}\n')
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": "complete",
        "stopping_reason": "done", "verification_commands": [command]}))
    (packet / "repo/generators/aaaa00000003/generator.py").write_text("VERSION = 'better'\n")

    result = build_full_return(packet, tmp_path / "summary.zip")

    with zipfile.ZipFile(result["zip"]) as archive:
        summary = json.loads(archive.read("INTAKE.json"))
        assert summary["assignment_id"] == json.loads(archive.read("ASSIGNMENT.json"))["assignment_id"]
        assert summary["changed_paths"] == ["repo/generators/aaaa00000003/generator.py"]
        assert summary["components"] == ["generator"]
        assert summary["feedback_items"] == [{"id": "F1", "text": "Show progress.\n\nEvidence: checks/after.json"}]
        assert summary["verification_commands"] == [command]
        assert summary["evidence_sha256"]["checks/after.json"] == hashlib.sha256(archive.read("checks/after.json")).hexdigest()
        assert summary["training_admitted"] is False


def test_intake_summary_cannot_contradict_hash_bound_source(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    result = build_full_return(packet, tmp_path / "summary.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    summary = json.loads(payload["INTAKE.json"])
    summary["task_id"] = "another-task"
    payload["INTAKE.json"] = json.dumps(summary).encode()
    results = json.loads(payload["RESULTS.json"])
    next(row for row in results["artifacts"] if row["path"] == "INTAKE.json")["sha256"] = hashlib.sha256(payload["INTAKE.json"]).hexdigest()
    payload["RESULTS.json"] = json.dumps(results).encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, raw in payload.items(): archive.writestr(name, raw)
    with zipfile.ZipFile(stream) as archive, pytest.raises(ValueError, match="intake summary"):
        validate_full_return(archive, json.loads((packet / "PACKET-MANIFEST.json").read_text()))


@pytest.mark.parametrize("tamper_task", [False, True])
def test_legacy_qualified_heading_summary_preserves_source_checks(library, tmp_path, tamper_task):
    from arcpuzzles.review_feedback import feedback_items
    packet = _draw(library, tmp_path)
    _docs(packet)
    feedback = ("## **F1 (top shared change): Require semantic contracts**\n"
                "Evidence: an accepted witness.\n\n## F2: Improve logs\nKeep this separate.\n")
    (packet / "FEEDBACK_TO_CODEX.md").write_text(feedback)
    result = build_full_return(packet, tmp_path / "qualified.zip")
    with zipfile.ZipFile(result["zip"]) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    summary = json.loads(payload["INTAKE.json"])
    assert [row["id"] for row in summary["feedback_items"]] == ["F1", "F2"]
    # Older builders skipped qualified headings; keep their exact receipt meaning.
    summary["feedback_items"] = [{"id": "F2", "text": "Improve logs\nKeep this separate."}]
    if tamper_task:
        summary["task_id"] = "another-task"
    payload["INTAKE.json"] = json.dumps(summary).encode()
    results = json.loads(payload["RESULTS.json"])
    next(row for row in results["artifacts"] if row["path"] == "INTAKE.json")["sha256"] = hashlib.sha256(payload["INTAKE.json"]).hexdigest()
    payload["RESULTS.json"] = json.dumps(results).encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, raw in payload.items():
            archive.writestr(name, raw)
    manifest = json.loads((packet / "PACKET-MANIFEST.json").read_text())
    with zipfile.ZipFile(stream) as archive:
        if tamper_task:
            with pytest.raises(ValueError, match="intake summary"):
                validate_full_return(archive, manifest)
        else:
            validate_full_return(archive, manifest)
            assert [row["id"] for row in feedback_items(archive.read("FEEDBACK_TO_CODEX.md").decode())] == ["F1", "F2"]


def test_verification_commands_require_explicit_packet_directory(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": "complete",
        "verification_commands": [{"cwd": "../sibling", "argv": ["python3", "probe.py"]}]}))
    with pytest.raises(ValueError, match="verification command"):
        build_full_return(packet, tmp_path / "bad-command.zip")


def test_missing_verification_evidence_names_exact_command_and_path(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    (packet / "RESULTS.json").write_text(json.dumps({
        "verification_commands": [{"cwd": "repo", "argv": ["python3", "probe.py"],
                                   "evidence_paths": ["checks/missing.json"]}]}))
    with pytest.raises(ValueError) as error:
        build_full_return(packet, tmp_path / "missing-evidence.zip")
    assert "verification_commands[0].evidence_paths[0]" in str(error.value)
    assert "checks/missing.json" in str(error.value)
    assert not (tmp_path / "missing-evidence.zip").exists()


def test_oversized_return_reports_budget_groups_before_creating_zip(library, tmp_path, monkeypatch):
    from arcpuzzles import review_return
    packet = _draw(library, tmp_path)
    _docs(packet)
    checks = packet / "checks" / "superseded"
    checks.mkdir(parents=True)
    for index in range(10):
        (checks / f"{index}.log").write_bytes(b"x")
    monkeypatch.setattr(review_return, "MAX_MEMBERS", 10)
    monkeypatch.setattr(review_return, "MAX_EXPANDED", 100)
    output = tmp_path / "oversized.zip"
    with pytest.raises(ValueError) as error:
        build_full_return(packet, output)
    message = str(error.value)
    assert "members=17/10" in message
    assert "expanded_bytes=" in message and "/100" in message
    assert "checks/superseded: members=10" in message
    assert not output.exists()
