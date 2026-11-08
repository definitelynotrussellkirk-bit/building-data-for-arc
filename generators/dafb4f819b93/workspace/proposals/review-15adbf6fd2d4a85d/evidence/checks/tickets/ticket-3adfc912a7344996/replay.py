#!/usr/bin/env python3
"""Bounded replay of the pinned 2920da6abe8a degenerate-texture audit."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, RacketBridgeError
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "2920da6abe8a"
TICKET = "ticket-3adfc912a7344996"
RETURN_ID = "review-7ec721b6e52619aa:v0001"
SOURCE_SHA256 = "14e0c877bf47e3d9298955d6f29d591b011ab019cfa9d3498b538e294bb15170"
ASSETS_SHA256 = "9b012e01e8f89484987744eedb4a4d50f2289de3e6127372f3de13a5fb3f82bb"
INDEX_SHA256 = "468cdc8aedaa22e4443802ee75473e9b898609068a3814db07888d9539ce1f55"
AUDIT_RECORD_SHA256 = "9f65281dced8ac621a28e59856599f8d74279cf18df518627d662cbd7ee15176"
RULE_HASH = "6e2213db7e3f"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-7ec721b6e52619aa-v0001"
SOURCE = REPO / "generators" / TASK / "generator.py"
ASSETS = BASE / "audit_assets.json"
INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
RETAINED = BASE / "retained/checks/audit/2920da6abe8a/counterexample.json"
OUT = HERE / "replay.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_2920_generator", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = []
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    rows.append(row)
    programs = {row["program_solution"] for row in rows if isinstance(row.get("program_solution"), str)}
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    program = programs.pop()
    assert normalized_rule_hash(program) == RULE_HASH
    return program


def main() -> int:
    started = time.monotonic()
    if OUT.exists():
        raise FileExistsError(OUT)

    assert sha256_file(SOURCE) == SOURCE_SHA256
    assert sha256_file(ASSETS) == ASSETS_SHA256
    assert sha256_file(INDEX) == INDEX_SHA256

    manifest = json.loads(ASSETS.read_text(encoding="utf-8"))
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"], (path, actual, row["sha256"])
        assert path.stat().st_size == row["bytes"]
        verified_assets.append({"path": path.relative_to(REPO).as_posix(), "bytes": row["bytes"], "sha256": actual})

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    matches = [row for row in index["audits"] if row.get("return_id") == RETURN_ID]
    assert len(matches) == 1
    audit_record = matches[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == SOURCE_SHA256
    assert audit_record["resolution"] == "needs_triage"

    retained = json.loads(RETAINED.read_text(encoding="utf-8"))
    generator = load_generator()
    generated = generator.generate(17, 0, difficulty="easy", texture="no_marker")
    assert generated == retained["input"]
    assert sha256_json(generated) == retained["input_sha256"]
    meta_errors = generator.self_check(copy.deepcopy(generated), difficulty="easy", meta={"texture": "no_marker"})
    domain_errors = generator.self_check(copy.deepcopy(generated), difficulty="easy")
    assert meta_errors == []
    assert domain_errors == ["expected exactly 1 non-zero cell, found 0"]

    program = canonical_program()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=8)
    runtime = bridge.runtime_identity
    authority_error = None
    try:
        bridge.eval_text(f"(define __ticket_rule {wrap_rule(program)})")
        bridge.define_grid("__ticket_input", generated)
        try:
            bridge.eval_text("(__ticket_rule __ticket_input)")
        except RacketBridgeError as exc:
            authority_error = f"{type(exc).__name__}: {exc}"
    finally:
        bridge.shutdown()
    assert authority_error is not None
    assert "list-ref: index #f is not an exact nonnegative integer" in authority_error

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": TICKET,
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "The advertised texture=no_marker override still emits an all-zero 3x3 grid; "
            "the texture-aware validator accepts it, the ordinary task-domain validator rejects it, "
            "and the exact canonical Racket authority raises the retained list-ref error."
        ),
        "source_binding": {
            "generator_sha256": SOURCE_SHA256,
            "assets_manifest_sha256": ASSETS_SHA256,
            "audit_index_sha256": INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "seed": 17,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": {"texture": "no_marker"},
            "input": generated,
            "input_sha256": sha256_json(generated),
            "meta_aware_self_check": meta_errors,
            "ordinary_domain_self_check": domain_errors,
            "authority_error": authority_error,
            "matches_retained_counterexample": True,
        },
        "racket_runtime": runtime,
        "limitations": [
            "This replays one pinned witness only; it does not repeat the retained lint or 14,670-draw override battery.",
            "Reproduction confirms the bounded claim but does not clear or resolve the existing audit.",
        ],
        "command": "python3 review.py run python3 ../checks/tickets/ticket-3adfc912a7344996/replay.py",
        "probe_sha256": sha256_file(Path(__file__)),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "reproduced", "out": str(OUT), "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
