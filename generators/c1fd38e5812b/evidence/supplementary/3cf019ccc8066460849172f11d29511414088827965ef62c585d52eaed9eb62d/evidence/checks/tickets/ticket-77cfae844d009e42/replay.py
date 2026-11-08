#!/usr/bin/env python3
"""Replay one retained audit witness against the pinned source and live Racket authority."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "c1fd38e5812b"
RETURN_ID = "review-18970a2504c4bc81:v0001"
EXPECTED_SOURCE_SHA256 = "836fa3a06d55f5a6450ccf989f8187695e6f45d8ef81f0a6a384a853a73409af"
EXPECTED_RULE_HASH = "0805714fcf25"
ASSET_MANIFEST_REL = Path(
    "generators/c1fd38e5812b/counterexamples/review-18970a2504c4bc81-v0001/audit_assets.json"
)
EXPECTED_ASSET_MANIFEST_SHA256 = "314aee543ac71bfffb92241c4476b90034785ab37a689f500de814a474d21d13"
AUDIT_INDEX_REL = Path("generators/c1fd38e5812b/evidence/review_index.json")
EXPECTED_AUDIT_INDEX_SHA256 = "46c4d85be4606fa00d1c4180b58bf609a239166394e575ecea236a3aa18bfedc"
EXPECTED_AUDIT_RECORD_SHA256 = "6a6cd71e8eb3abedbec7ce9afba9d5eceb968af7185b60ee58245be79fd2222e"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def fail(message: str) -> None:
    raise AssertionError(message)


def starts(values: list[int]) -> list[int]:
    return [0] + [index for index in range(1, len(values)) if values[index] != values[index - 1]]


def rival(grid: list[list[int]]) -> list[list[int]]:
    row_starts = starts([row[0] for row in grid])
    row_spans = [b - a for a, b in zip(row_starts, row_starts[1:] + [len(grid)])]
    if len(set(row_spans)) == 1:
        first_width = next(
            (col for col in range(1, len(grid[0])) if grid[0][col] != grid[0][col - 1]),
            len(grid[0]),
        )
        col_starts = list(range(0, len(grid[0]), first_width))
    else:
        col_starts = starts(grid[0])
    return [[grid[row][col] for col in col_starts] for row in row_starts]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: replay.py RESULT.json")
    result_path = Path(sys.argv[1]).resolve()
    evidence_dir = result_path.parent
    evidence_dir.mkdir(parents=True, exist_ok=True)
    repo = Path.cwd().resolve()

    generator, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        fail(f"peer source differs: {source_sha256}")

    asset_manifest_path = repo / ASSET_MANIFEST_REL
    if sha256_path(asset_manifest_path) != EXPECTED_ASSET_MANIFEST_SHA256:
        fail("retained asset manifest differs")
    asset_manifest = json.loads(asset_manifest_path.read_text())
    if asset_manifest.get("audited_generator_sha256") != EXPECTED_SOURCE_SHA256:
        fail("asset manifest source identity differs")
    if asset_manifest.get("return_id") != RETURN_ID:
        fail("asset manifest return identity differs")

    retained: dict[str, Path] = {}
    for row in asset_manifest["files"]:
        path = repo / row["path"]
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha256_path(path) != row["sha256"]:
            fail(f"retained asset differs: {row['path']}")
        retained[Path(row["path"]).name] = path

    audit_index_path = repo / AUDIT_INDEX_REL
    if sha256_path(audit_index_path) != EXPECTED_AUDIT_INDEX_SHA256:
        fail("audit index differs")
    audit_index = json.loads(audit_index_path.read_text())
    audit_record = next(row for row in audit_index["audits"] if row.get("return_id") == RETURN_ID)
    if stable_sha256(audit_record) != EXPECTED_AUDIT_RECORD_SHA256:
        fail("pinned audit record differs")
    if audit_record.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        fail("audit record source identity differs")
    if audit_record.get("assets_manifest_sha256") != EXPECTED_ASSET_MANIFEST_SHA256:
        fail("audit record asset identity differs")

    probe = json.loads(retained["probe-preapply.json"].read_text())
    retained_finding = json.loads(retained["finding.json"].read_text())
    grid = json.loads(retained["input.json"].read_text())
    if probe.get("generator_sha256") != EXPECTED_SOURCE_SHA256:
        fail("probe source identity differs")
    if retained_finding.get("generator_sha256") != EXPECTED_SOURCE_SHA256:
        fail("finding source identity differs")

    current_errors = generator.self_check(grid)
    current_overrides = generator.observe_overrides(grid)
    current_python_output = generator.solve_python(grid)
    rival_output = rival(grid)
    if current_errors != []:
        fail(f"witness no longer accepted: {current_errors}")
    if current_overrides != {"scene_profile": "interior_merges"}:
        fail(f"witness classification changed: {current_overrides}")
    if current_python_output != probe["python_authority_mirror"]:
        fail("current Python mirror differs from retained authority mirror")
    if rival_output != probe["rival_output"]:
        fail("recomputed rival differs from retained rival")
    if current_python_output == rival_output:
        fail("witness no longer separates authority and rival")

    replay_input = evidence_dir / "input.json"
    replay_input.write_bytes(retained["input.json"].read_bytes())
    racket_path = evidence_dir / "racket-replay.json"
    stdout_path = evidence_dir / "racket-stdout.log"
    stderr_path = evidence_dir / "racket-stderr.log"
    input_arg = os.path.relpath(replay_input, repo)
    output_arg = os.path.relpath(racket_path, repo)
    argv = [
        sys.executable,
        "-m",
        "arcpuzzles",
        "apply",
        TASK_ID,
        "--input",
        input_arg,
        "--check-generator-domain",
        "--out",
        output_arg,
    ]
    completed = subprocess.run(
        argv,
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    stdout_path.write_text(completed.stdout)
    stderr_path.write_text(completed.stderr)
    if completed.returncode != 0:
        fail(f"live Racket replay failed with exit {completed.returncode}")

    racket = json.loads(racket_path.read_text())
    if racket.get("generator_sha256") != EXPECTED_SOURCE_SHA256:
        fail("live Racket source identity differs")
    if racket.get("catalog_rule_hash") != EXPECTED_RULE_HASH:
        fail("catalog rule hash differs")
    if racket.get("executed_rule_hash") != EXPECTED_RULE_HASH:
        fail("executed rule hash differs")
    if racket.get("rule_hash_matches_catalog") is not True:
        fail("executed rule no longer matches catalog")
    rows = racket.get("results", [])
    if len(rows) != 1 or rows[0].get("error") is not None:
        fail("live Racket replay did not produce one clean result")
    row = rows[0]
    if row.get("generator_domain") != {"status": "valid", "errors": []}:
        fail("live authority no longer accepts the witness")
    if row.get("output") != current_python_output:
        fail("live Racket output differs from the current Python authority mirror")
    if row.get("output") == rival_output:
        fail("live Racket output no longer separates the rival")

    result = {
        "schema": "arcpuzzles-ticket-audit-replay-v1",
        "ticket_id": "ticket-77cfae844d009e42",
        "task_id": TASK_ID,
        "audit_return_id": RETURN_ID,
        "source_path": str(source_path.relative_to(repo)),
        "source_sha256": source_sha256,
        "rule_hash": EXPECTED_RULE_HASH,
        "assets_manifest_path": str(ASSET_MANIFEST_REL),
        "assets_manifest_sha256": EXPECTED_ASSET_MANIFEST_SHA256,
        "audit_index_path": str(AUDIT_INDEX_REL),
        "audit_index_sha256": EXPECTED_AUDIT_INDEX_SHA256,
        "audit_record_sha256": EXPECTED_AUDIT_RECORD_SHA256,
        "retained_assets_verified": len(asset_manifest["files"]),
        "witness_shape": [len(grid), len(grid[0])],
        "row_spans": probe["construction"]["row_spans"],
        "column_spans": probe["construction"]["col_spans"],
        "generator_domain_valid": True,
        "current_python_matches_retained": True,
        "live_racket_matches_current_python": True,
        "rival_differs": True,
        "replay_status": "reproduced",
        "audit_resolution_changed": False,
        "scope_limit": "One exact accepted witness; prior 48-draw census was not repeated and the audit was not cleared.",
        "racket_command": {
            "cwd": "repo",
            "argv": ["python3", "-m", "arcpuzzles", "apply", TASK_ID, "--input", input_arg,
                     "--check-generator-domain", "--out", output_arg],
            "exit_code": completed.returncode,
        },
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
