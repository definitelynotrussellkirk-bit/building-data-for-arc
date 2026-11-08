#!/usr/bin/env python3
"""Bounded reproduction of the pinned authority-sync manual-bundle request."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

TICKET_ID = "ticket-6d7f91c2724d383a"
TASK_ID = "86af5978a32a"
REQUEST_ID = "review-061f1fc9b07a6663:v0001:F2"
PROBE_SEED = "02c0a276eab6df1b830b4aaa38c3cce2fc5dc0fe7f636f983e26bd86a65bc8a7"
EXPECTED = {
    "assets_manifest_sha256": "3d57c958a7cd3ac6824def8b6486d9027e2c6ae0d443bb6c86d288379a8cc9c3",
    "request_source_sha256": "6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642",
    "request_sha256": "0fbcaddcd773628ba3fa3aa7667746303e7e35f85d7f6d32e109b97d56cc63b7",
    "generator_sha256": "ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e",
    "canonical_source_sha256": "a6914eb76bfb0d5fbd5a1ed0dc1933807388909461277ac7c0d7b2ac830ca2b5",
    "archival_raw_code_sha256": "b4c6132e218d91908c5c1ddd0fdbd85d114c184b115153f5e24dc2ab9c0b8ecb",
}


def sha_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha_path(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def request_sha(row: dict) -> str:
    return sha_bytes(json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def main() -> int:
    started = time.monotonic()
    here = Path(__file__).resolve()
    work = here.parents[3]
    repo = work / "repo"
    suggestions_path = repo / "REVIEW/suggestions.json"
    manifest_path = repo / "shared/tools/proposals/6003951c195cb0b6/manifest.json"
    manual_path = repo / "shared/tools/proposals/6003951c195cb0b6/checks/authority-manual-review.json"
    retained_log_path = repo / "shared/tools/proposals/6003951c195cb0b6/checks/after-1/checks/86af5978a32a_after_authority_sync.log"
    generator_path = repo / f"generators/{TASK_ID}/generator.py"

    suggestions = json.loads(suggestions_path.read_text(encoding="utf-8"))
    matches = [row for row in suggestions.get("items", []) if row.get("request_id") == REQUEST_ID]
    assert len(matches) == 1
    request = matches[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manual = json.loads(manual_path.read_text(encoding="utf-8"))
    retained_log = retained_log_path.read_text(encoding="utf-8")

    identity_checks = {
        "assets_manifest_hash_matches": sha_path(manifest_path) == EXPECTED["assets_manifest_sha256"],
        "request_source_hash_matches": sha_path(suggestions_path) == EXPECTED["request_source_sha256"],
        "request_hash_matches": request_sha(request) == EXPECTED["request_sha256"],
        "generator_hash_matches": sha_path(generator_path) == EXPECTED["generator_sha256"],
        "manifest_asset_hashes_match": all(
            (repo / row["path"]).is_file() and sha_path(repo / row["path"]) == row["sha256"]
            for row in manifest.get("files", [])
        ),
        "manual_review_canonical_hash_matches": manual.get("canonical_source_sha256") == EXPECTED["canonical_source_sha256"],
        "manual_review_preserves_raw_code": manual.get("archival_raw_code_unchanged") is True,
        "retained_log_reports_execution_parity": "execution-parity: PASS over 3 distinct source text(s)" in retained_log,
    }
    assert all(identity_checks.values()), identity_checks

    mapping = json.loads((repo / "catalog/authority_files.json").read_text(encoding="utf-8"))
    authority_names = sorted(name for name, owner in mapping.items() if owner == TASK_ID)
    assert len(authority_names) == 2
    canonical_rows = []
    for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical_rows.append(row)
    assert len(canonical_rows) == 2
    canonical = canonical_rows[0]["program_solution"]
    assert len({row["program_solution"] for row in canonical_rows}) == 1
    assert sha_bytes(canonical.encode("utf-8")) == EXPECTED["canonical_source_sha256"]

    with tempfile.TemporaryDirectory(prefix="authority-manual-bundle-") as tmp_name:
        library = Path(tmp_name)
        (library / "catalog").mkdir(parents=True)
        (library / "shared/data/canonical").mkdir(parents=True)
        (library / "catalog/puzzles.jsonl").write_text(json.dumps({"id": TASK_ID}) + "\n", encoding="utf-8")
        (library / "catalog/authority_files.json").write_text(
            json.dumps({name: TASK_ID for name in authority_names}), encoding="utf-8"
        )
        (library / "shared/data/canonical/puzzles.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in canonical_rows), encoding="utf-8"
        )

        archival_hashes = []
        for name in authority_names:
            source = repo / "shared" / name
            row = json.loads(source.read_text(encoding="utf-8"))
            raw = row["racket_target"]["raw_code"]
            archival_hashes.append(sha_bytes(raw.encode("utf-8")))
            # Recreate the retained, execution-parity-covered token-different class.
            # The exact historical pre-sync target bytes were not retained in this packet.
            row["racket_target"]["target_code"] = raw
            target = library / "shared" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        assert set(archival_hashes) == {EXPECTED["archival_raw_code_sha256"]}

        out_path = library / "manual-review-proposal.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo / "src") + os.pathsep + env.get("PYTHONPATH", "")
        argv = [
            sys.executable, "-m", "arcpuzzles", "--library", str(library),
            "authority-sync", TASK_ID, "--selected-only", "--out", str(out_path),
        ]
        completed = subprocess.run(
            argv, cwd=repo, env=env, text=True, capture_output=True,
            timeout=120, check=False,
        )
        actual = {
            "argv": ["python3", "-m", "arcpuzzles", "--library", "<temporary-library>",
                     "authority-sync", TASK_ID, "--selected-only", "--out", "<temporary-output>"],
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "output_exists": out_path.exists(),
            "output_bytes": out_path.stat().st_size if out_path.exists() else 0,
        }

    reproduced = (
        actual["exit_code"] != 0
        and "rule tokens differ; semantic changes require manual review" in actual["stderr"]
        and not actual["output_exists"]
    )
    assert reproduced, actual

    report = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "type": "tool_reproduction",
        "status": "completed",
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "request_id": REQUEST_ID,
        "request_status": request.get("status"),
        "identity_checks": identity_checks,
        "retained_evidence": {
            "manifest": manifest_path.relative_to(work).as_posix(),
            "manual_review": manual_path.relative_to(work).as_posix(),
            "authority_sync_log": retained_log_path.relative_to(work).as_posix(),
            "historical_target_source_sha256_before": manual["files"][0]["selected_target_sha256_before"],
            "historical_exact_target_bytes_retained": False,
            "archival_raw_code_sha256": EXPECTED["archival_raw_code_sha256"],
            "execution_parity_scope": "3 distinct source texts on canonical train/test pairs (retained log)",
        },
        "targeted_probe": actual,
        "reproduced_state": {
            "current_cli_refuses_token_different_selected_source": True,
            "current_cli_emits_manual_review_bundle": False,
            "request_feature_present": False,
        },
        "proposed_request_disposition": {
            "decision": "keep_accepted_open",
            "reason": (
                "The current public CLI still raises on an execution-parity-covered token mismatch and emits no "
                "reviewable proposal. The accepted request remains unsatisfied and would remove bespoke JSON surgery "
                "without weakening the explicit reviewer-approval gate."
            ),
            "suggested_acceptance_test": (
                "For a token-different selected target with a retained execution-parity receipt, --out writes a "
                "non-applying, hash-bound target_code-only manual-review bundle while leaving all library bytes unchanged."
            ),
        },
        "limitations": [
            "The packet retains the historical pre-sync target hash but not those exact source bytes.",
            "The probe uses the retained archival raw_code, which is one of the execution-parity-covered token-different source classes, as a reproducible representative.",
            "No shared tooling was modified and no proposal was applied.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "elapsed_minutes": None,
    }
    out = here.with_name("probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": out.relative_to(work).as_posix(), "reproduced_state": report["reproduced_state"], "proposed_disposition": report["proposed_request_disposition"]["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
