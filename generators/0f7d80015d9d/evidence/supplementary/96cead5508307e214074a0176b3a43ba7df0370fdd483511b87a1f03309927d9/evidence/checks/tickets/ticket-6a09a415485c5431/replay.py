#!/usr/bin/env python3
"""Bounded replay of the pinned 0f7d80015d9d audit separator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "0f7d80015d9d"
RETURN_ID = "review-bf9d7c5f13da3e98:v0001"
CURRENT_SOURCE_SHA256 = "2bcf9589c3a7c35f27df8976a57635e91cfc05e09bdd2368b7682982a004ea09"
AUDITED_SOURCE_SHA256 = "f576456b685e460e55ddfcd13d3554b45e6b391505bf80e7e4a3a618e23a7e8f"
ASSET_MANIFEST_SHA256 = "68a8904f1b6c392460b03f6fd7d122762e0d4f31200f31b293c48ebc2ce84f81"
AUDIT_INDEX_SHA256 = "a62f4daf0f99ec7353bb89fd59758debb6f02065765e9cd9a29c3c79f855025b"
AUDIT_RECORD_SHA256 = "e6f9db47700da59b06f1e0933703eda4c56c472133b1d71d1f1128de1da3b679"
RULE_HASH = "9744dc525afc"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-bf9d7c5f13da3e98-v0001"
ASSET_MANIFEST = BASE / "audit_assets.json"
AUDIT_INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
CURRENT_SOURCE = REPO / "generators" / TASK / "generator.py"
AUDITED_SOURCE = BASE / "audited_source.py"
AUDITED_RULE = BASE / "audited_rule.jsonl"
RETAINED_EVIDENCE = BASE / "retained" / "checks" / "audit" / TASK / "evidence.json"
OUT = HERE / "replay.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def install_packet_scripts_namespace() -> None:
    qualified = "scripts.comment_solutions"
    if qualified in sys.modules:
        return
    source = REPO / "shared" / "tools" / "comment_solutions.py"
    package = types.ModuleType("scripts")
    package.__path__ = [str(source.parent)]
    sys.modules.setdefault("scripts", package)
    spec = importlib.util.spec_from_file_location(qualified, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_audited_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relative_marker_order(grid):
    """Pinned rival: stamp right iff original red is left of original cyan."""
    out = copy.deepcopy(grid)
    cells = {
        color: [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        for color in (2, 5, 8)
    }
    red, cyan = cells[2][0], cells[8][0]
    bottom = max(row for row, _ in cells[5])
    left = min(col for _, col in cells[5])
    right = max(col for _, col in cells[5])
    destination = right + 1 if red[1] < cyan[1] else left - 1
    out[red[0]][red[1]] = 7
    out[cyan[0]][cyan[1]] = 2
    out[bottom][destination] = 8
    return out


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)

    assert sha256_file(ASSET_MANIFEST) == ASSET_MANIFEST_SHA256
    assert sha256_file(AUDIT_INDEX) == AUDIT_INDEX_SHA256
    assert sha256_file(CURRENT_SOURCE) == CURRENT_SOURCE_SHA256
    assert sha256_file(AUDITED_SOURCE) == AUDITED_SOURCE_SHA256

    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == AUDITED_SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"], (path, actual, row["sha256"])
        verified_assets.append(
            {"path": str(path.relative_to(REPO)), "sha256": actual, "bytes": path.stat().st_size}
        )

    index = json.loads(AUDIT_INDEX.read_text(encoding="utf-8"))
    matching = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(matching) == 1
    audit_record = matching[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == AUDITED_SOURCE_SHA256
    assert audit_record["resolution"] == "needs_triage"

    retained = json.loads(RETAINED_EVIDENCE.read_text(encoding="utf-8"))
    counterexample = retained["counterexample"]
    audited = load_module(AUDITED_SOURCE)
    grid = counterexample["input"]
    validator_errors = audited.self_check(copy.deepcopy(grid))
    strict_errors = audited.strict_canonical_like(copy.deepcopy(grid))
    assert validator_errors == []
    assert strict_errors == []

    rows = [json.loads(line) for line in AUDITED_RULE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1 and rows[0]["task_id"] == TASK
    program = rows[0]["program_solution"]
    assert normalized_rule_hash(program) == RULE_HASH

    install_packet_scripts_namespace()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        runtime = bridge.runtime_identity
        bridge.eval_text(f"(define __audit_rule {wrap_rule(program)})")
        bridge.define_grid("__audit_input", grid)
        actual = bridge.eval_text("(__audit_rule __audit_input)")
    finally:
        bridge.shutdown()

    rival = relative_marker_order(grid)
    assert actual == counterexample["actual_racket_output"]
    assert rival == counterexample["rival_output"]
    assert actual != rival
    assert sha256_json(actual) == counterexample["racket_output_sha256"]
    assert sha256_json(rival) == counterexample["rival_output_sha256"]

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": "ticket-6a09a415485c5431",
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "The retained hand input is accepted by the audited validators and "
            "separates the exact Racket midpoint rule from the marker-order rival."
        ),
        "source_binding": {
            "current_generator_sha256": CURRENT_SOURCE_SHA256,
            "audited_generator_sha256": AUDITED_SOURCE_SHA256,
            "current_differs_from_audited": CURRENT_SOURCE_SHA256 != AUDITED_SOURCE_SHA256,
            "assets_manifest_sha256": ASSET_MANIFEST_SHA256,
            "audit_index_sha256": AUDIT_INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "input_sha256": sha256_json(grid),
            "validator_errors": validator_errors,
            "strict_canonical_errors": strict_errors,
            "observed_axes": audited.observe_overrides(copy.deepcopy(grid)),
            "actual_racket_output_sha256": sha256_json(actual),
            "rival_output_sha256": sha256_json(rival),
            "outputs_differ": True,
            "belongs_to_actual_sampler_support": counterexample["belongs_to_actual_sampler_support"],
            "sampler_exclusion_reason": counterexample["sampler_exclusion_reason"],
        },
        "racket_runtime": runtime,
        "limitations": [
            "This replays one retained separator, not the original 1,024-draw census.",
            "The witness is validator-accepted but outside the audited sampler support.",
            "The current generator has different source bytes; this replay does not assess or clear its audit state.",
        ],
        "command": "python3 review.py run python3 ../checks/tickets/ticket-6a09a415485c5431/replay.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "outputs_differ": True, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
