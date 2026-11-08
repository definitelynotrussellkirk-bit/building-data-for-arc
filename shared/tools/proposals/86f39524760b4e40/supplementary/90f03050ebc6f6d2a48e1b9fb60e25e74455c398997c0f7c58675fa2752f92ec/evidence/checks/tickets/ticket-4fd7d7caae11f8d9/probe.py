#!/usr/bin/env python3
"""One bounded source-bound sparse-recovery support reproduction.

All created files stay beside this script. The retained helper is imported only
after its recorded hash has matched; source files and issued manifests are read.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
REQUEST_ID = "review-9720fbbc5d4ee1d8:v0001:F1"
SEED = "ddeb3a624fed7dadfd797611f3ac156a49e3570048d38d7f00fb443a3a062fe9"
STARTED = time.monotonic()
report = {
    "schema": "bounded-tool-reproduction-v1",
    "ticket_id": "ticket-4fd7d7caae11f8d9",
    "request_id": REQUEST_ID,
    "probe_seed": SEED,
    "execution": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
    "identities": [],
    "scope": "Retained evidence consistency plus one isolated tiny ZIP lifecycle using exact retained helper bytes.",
    "limits": [
        "Original historical ZIP, ENOSPC failure, runtime setup and mount discrepancy were not replayed.",
        "Synthetic archive is a small fixture, not a replacement issued packet.",
        "Package adapter, missing-candidate guard, supplementary ticket retry and full return replay were not executed.",
        "Main-draw seed preservation is tested; supplementary-ticket seed preservation is not inferred from it.",
        "No shared helper adoption, source approval, automatic capacity gate or training admission follows.",
    ],
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def check_file(relative, expected):
    path = WORK / relative
    raw = path.read_bytes()
    actual = digest(raw)
    report["identities"].append({"path": relative, "sha256": actual,
                                 "expected_sha256": expected, "bytes": len(raw),
                                 "matches": actual == expected})
    if actual != expected:
        raise AssertionError(f"Identity mismatch: {relative}")
    return raw


def blocked(call):
    try:
        call()
    except ValueError as exc:
        return {"rejected": True, "exception_type": type(exc).__name__, "message": str(exc)}
    raise AssertionError("Expected ValueError was not raised")


def main():
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("110-second probe limit")))
    signal.alarm(110)
    suggestions = json.loads(check_file("repo/REVIEW/suggestions.json", "2cf732622eeeca12a0b3d2618fd72be588896badeb17ad67a61226d101f1b646"))
    rows = [row for row in suggestions["items"] if row["request_id"] == REQUEST_ID]
    assert len(rows) == 1
    request = rows[0]
    request_sha = digest(canonical(request))
    assert request_sha == "5dcd40afafd838232fd6c39a6fc0e13edf5161bfa0e83cc20dfc3ab17054c980"
    report["request"] = {"canonical_sha256": request_sha, "status": request["status"],
                         "source_sha256": request["source_sha256"], "reason": request["reason"]}
    source = check_file("repo/generators/57bafcdde8c3/generator.py", "dc1725d9eca65b36824a210b2a0f78d84dcae14c457efd5c3d8e46e3790f598b")
    manifest = json.loads(check_file("repo/shared/tools/proposals/86f39524760b4e40/manifest.json", "b58e35115b0c151230db0d43c57f343ebd541e1ce62d76adf86aab9e6b1ba8d3"))
    assets = {}
    for item in manifest["files"]:
        raw = check_file("repo/" + item["path"], item["sha256"])
        assert len(raw) == item["bytes"]
        assets[item["source_member"]] = raw
    recovery = json.loads(assets["checks/storage-recovery.json"])
    observations = [json.loads(line) for line in assets["checks/storage-observations.jsonl"].splitlines()]
    verified = json.loads(assets["checks/original-archive-verification.json"])
    assert [row["stage"] for row in observations] == ["before_extract", "after_extract", "after_setup", "before_package"]
    assert all(row["archive"]["sha256"] == recovery["archive"]["sha256"] for row in observations)
    initial = next(fs for fs in observations[0]["filesystems"] if fs["path"] == recovery["initial_workspace"]["path"])
    assert initial == recovery["initial_workspace"]
    assert verified["files_verified"] + verified["outer_entries_verified"] + 1 == recovery["archive"]["members"]
    report["retained_evidence"] = {
        "status": "hashes_and_selected_consistency_checks_passed",
        "runtime_approved": manifest["runtime_approved"],
        "stages": [row["stage"] for row in observations],
        "initial_workspace": initial,
        "after_setup_scope": recovery["checkpoints"]["after_setup_scope"],
        "archive": recovery["archive"],
        "archive_verification_report": verified,
        "not_run_reported_by_original_author": recovery["not_run"],
        "scope": "Historical assertions retained and checked for consistency; not newly measured historical behavior.",
    }
    helper_relative = recovery["recovery_helper"]["original_path"]
    check_file(helper_relative, recovery["recovery_helper"]["sha256"])
    spec = importlib.util.spec_from_file_location("ticket_sparse_recovery", WORK / helper_relative)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    fixture = HERE / "fixture"
    fixture.mkdir()
    archive = fixture / "minimal-source.zip"
    source_name = "repo/generators/57bafcdde8c3/generator.py"
    entries = {"review.py": b"# synthetic entry; never executed\n", "START-HERE.md": b"Synthetic fixture only.\n"}
    fixture_manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {source_name: digest(source)},
                        "layout": {"workspace": "WORK", "entry_files": {k: digest(v) for k, v in entries.items()}}}
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("WORK/PACKET-MANIFEST.json", canonical(fixture_manifest))
        zf.writestr("WORK/" + source_name, source)
        for name, raw in entries.items():
            zf.writestr(name, raw)
    synthetic_work = fixture / "WORK"
    with helper.Packet(archive) as packet:
        behaviors = {"verify": packet.verify()}
        behaviors["hydrate"] = packet.hydrate(synthetic_work, [source_name])
        assert (synthetic_work / source_name).read_bytes() == source
        behaviors["repeat_hydrate"] = packet.hydrate(synthetic_work, [source_name])
        assert behaviors["repeat_hydrate"]["new_bytes"] == 0
        edited = b"# synthetic local edit; must survive rejection\n"
        (synthetic_work / source_name).write_bytes(edited)
        behaviors["modified_source_hydration"] = blocked(lambda: packet.hydrate(synthetic_work, [source_name]))
        assert (synthetic_work / source_name).read_bytes() == edited
        behaviors["modified_noncandidate_guard"] = packet.unchanged_source(synthetic_work, source_name, digest(source))
        assert behaviors["modified_noncandidate_guard"] is False
        (synthetic_work / source_name).unlink()
        behaviors["missing_noncandidate_guard"] = packet.unchanged_source(synthetic_work, source_name, digest(source))
        assert behaviors["missing_noncandidate_guard"] is True
        assert not (synthetic_work / source_name).exists()
        behaviors["not_in_manifest_hydration"] = blocked(lambda: packet.hydrate(synthetic_work, ["repo/missing.py"]))
        pending = synthetic_work / ".review/pending-main-draw.json"
        pending.parent.mkdir(parents=True)
        pending_raw = canonical({"schema": "arcpuzzles-pending-main-draw-v1", "contract": {"packet_id": packet.packet_id, "seed": SEED}})
        pending.write_bytes(pending_raw)
        committed = helper.commit_seed(synthetic_work, packet.packet_id)
        again = helper.commit_seed(synthetic_work, packet.packet_id)
        behaviors["pending_main_seed"] = {"first": committed.hex(), "retry": again.hex(), "pending_bytes_unchanged": pending.read_bytes() == pending_raw}
        assert committed.hex() == again.hex() == SEED
        assert pending.read_bytes() == pending_raw
    report["probe"] = {"archive_path": str(archive.relative_to(WORK)), "archive_sha256": digest(archive.read_bytes()), "behaviors": behaviors}
    # Source identity is checked again after exercising the helper.
    report["source_identity_unchanged_after_probe"] = all(digest((WORK / row["path"]).read_bytes()) == row["sha256"] for row in report["identities"])
    assert report["source_identity_unchanged_after_probe"]
    report["proposed_disposition"] = {
        "request_id": REQUEST_ID, "status": "accepted", "action": "retain_existing_passive_proposal",
        "reason": "Retained assets and source hashes match. One isolated probe reproduced verified hydration, unchanged-source guards and stable pending main-draw seed adoption. Supported wrapper integration and supplementary-ticket retry remain unimplemented/unverified in this bounded review; no adoption or approval is proposed.",
    }


exit_code = 0
try:
    main()
    report["status"] = "completed"
except Exception as exc:
    exit_code = 1
    report["status"] = "blocked"
    report["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
finally:
    signal.alarm(0)
    report["execution"].update({"elapsed_seconds": time.monotonic() - STARTED, "exit_code": exit_code, "probe_sha256": digest(Path(__file__).read_bytes())})
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "exit_code": exit_code, "elapsed_seconds": report["execution"]["elapsed_seconds"], "result": str(HERE / "result.json")}))
raise SystemExit(exit_code)
