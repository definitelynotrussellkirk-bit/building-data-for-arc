#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "2dacb90452ce"
AUDIT_RETURN_ID = "review-db674f1f2060195b:v0001"
EXPECTED_CURRENT_SOURCE_SHA256 = "b972fe9cc491907d1193818efe9a68c28202c3cb355cf31fc1b0c7dd2779d4c0"
EXPECTED_AUDITED_SOURCE_SHA256 = "59e3240735feef52056bef7408c0a7345856e02a404fc81d77782c694572dd15"
EXPECTED_MANIFEST_SHA256 = "fd501e4d14f40e767b5d02a6eb3f9d15907ea380bd59f221ef8bca335fa2ea90"
EXPECTED_INDEX_SHA256 = "dc224cf489d84721a0b8ee0017037703f156f9cdd9dc14a388ec128e088c1cde"
EXPECTED_AUDIT_RECORD_SHA256 = "7d8e21a8ad3b62c45d237b369979dde208f03949f2f28669e5566fc9e88bd8a9"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audited_2dacb90452ce", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_racket(program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __ticket_rule {wrap_rule(program)})")
        bridge.define_grid("__ticket_input", grid)
        return bridge.eval_text("(__ticket_rule __ticket_input)")
    finally:
        bridge.shutdown()


def main() -> None:
    started = time.monotonic()
    root = Path.cwd()
    task = root / "generators" / TASK_ID
    assets = task / "counterexamples" / "review-db674f1f2060195b-v0001"
    manifest_path = assets / "audit_assets.json"
    index_path = task / "evidence" / "review_index.json"
    audited_source_path = assets / "audited_source.py"
    audited_rule_path = assets / "audited_rule.jsonl"
    retained_path = assets / "retained" / "checks" / "audit-2dacb90452ce-counterexample.json"
    current_source_path = task / "generator.py"

    identities = {
        "manifest_sha256": sha256(manifest_path),
        "index_sha256": sha256(index_path),
        "audited_source_sha256": sha256(audited_source_path),
        "current_source_sha256": sha256(current_source_path),
        "audited_rule_sha256": sha256(audited_rule_path),
        "retained_counterexample_sha256": sha256(retained_path),
    }
    expected_identities = {
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "index_sha256": EXPECTED_INDEX_SHA256,
        "audited_source_sha256": EXPECTED_AUDITED_SOURCE_SHA256,
        "current_source_sha256": EXPECTED_CURRENT_SOURCE_SHA256,
    }
    for key, expected in expected_identities.items():
        if identities[key] != expected:
            raise RuntimeError(f"{key} mismatch: {identities[key]}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("return_id") != AUDIT_RETURN_ID
        or manifest.get("task_id") != TASK_ID
        or manifest.get("audited_generator_sha256") != EXPECTED_AUDITED_SOURCE_SHA256
    ):
        raise RuntimeError("audit asset manifest identity mismatch")
    verified_assets = []
    for row in manifest.get("files", []):
        relative = Path(row["path"])
        asset_path = root / relative
        if relative.is_absolute() or ".." in relative.parts or not asset_path.resolve().is_relative_to(root):
            raise RuntimeError(f"unsafe audit asset path: {relative}")
        actual_sha = sha256(asset_path)
        actual_bytes = asset_path.stat().st_size
        if actual_sha != row["sha256"] or actual_bytes != row["bytes"]:
            raise RuntimeError(f"audit asset identity mismatch: {relative}")
        verified_assets.append(
            {"path": relative.as_posix(), "sha256": actual_sha, "bytes": actual_bytes}
        )

    index = json.loads(index_path.read_text())
    record = next(row for row in index["audits"] if row["return_id"] == AUDIT_RETURN_ID)
    computed_record_sha = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if computed_record_sha != EXPECTED_AUDIT_RECORD_SHA256:
        raise RuntimeError(f"audit record hash mismatch: {computed_record_sha}")

    module = load_module(audited_source_path)
    overrides = {"grid_h": 15, "grid_w": 15, "texture": "tiny_grid"}
    grid = module.generate(17, 0, difficulty="medium", **overrides)
    findings = module.self_check(grid, difficulty="medium")
    rule_row = json.loads(audited_rule_path.read_text().splitlines()[0])
    racket_output = apply_racket(rule_row["program_solution"], grid)
    retained = json.loads(retained_path.read_text())
    reproduced = (
        grid == retained["input_grid"]
        and [len(grid), len(grid[0])] == retained["returned_dimensions"]
        and findings == retained["self_check_findings"]
        and racket_output == retained["actual_racket_output"]
        and retained["requested_dimensions"] == [15, 15]
    )
    result = {
        "schema": "arcpuzzles-ticket-audit-replay-v1",
        "ticket_id": "ticket-b24afeeb35d08a6c",
        "task_id": TASK_ID,
        "consumer": "existing_audit_assessment",
        "audit_return_id": AUDIT_RETURN_ID,
        "identities": identities,
        "verified_assets": verified_assets,
        "audit_record_sha256": computed_record_sha,
        "seed": 17,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": overrides,
        "requested_dimensions": [15, 15],
        "returned_dimensions": [len(grid), len(grid[0])],
        "input_grid": grid,
        "self_check_findings": findings,
        "racket_output": racket_output,
        "reproduced": reproduced,
        "current_source_differs_from_audited_source": identities["current_source_sha256"] != identities["audited_source_sha256"],
        "note": "Reproduction is against the retained audited source; it does not assess or clear the current repaired source.",
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    Path("../checks/tickets/ticket-b24afeeb35d08a6c/result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
