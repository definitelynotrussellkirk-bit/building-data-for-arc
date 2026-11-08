#!/usr/bin/env python3
"""One bounded advertised grid_h override comparison for a2b78ff2c2e0."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path

TICKET_ID = "ticket-907fcb279b40e160"
TASK_ID = "a2b78ff2c2e0"
PROBE_SEED_HEX = "9ff884a6044136146bd3a1010032a9e6ed3d2499abae3be2b4ac8f3c7e02d8e0"
EXPECTED_SOURCE_SHA256 = "d944c42ab24f35e0148815995509d3e8663b3bd0b854d784e52bee6e8328a121"
EXPECTED_RULE_HASH = "428dc8ceec14"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"
OUT = Path(__file__).resolve().with_name("result.json")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_rule_hash() -> str:
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row.get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return hashlib.sha256(" ".join(programs.pop().split()).encode()).hexdigest()[:12]


def main() -> int:
    source_sha = file_sha(SOURCE)
    assert source_sha == EXPECTED_SOURCE_SHA256
    rule_hash = canonical_rule_hash()
    assert rule_hash == EXPECTED_RULE_HASH
    generator = load_generator()
    seed = int(PROBE_SEED_HEX, 16)

    valid_arguments = {"seed": seed, "sample_index": 0, "difficulty": None, "grid_h": 5}
    valid_grid = generator.generate(**valid_arguments)
    valid_errors = generator.self_check(valid_grid, difficulty=None)
    assert len(valid_grid) == 5
    assert valid_errors == []

    invalid_arguments = {"seed": seed, "sample_index": 0, "difficulty": None, "grid_h": 4}
    invalid_exception = None
    try:
        generator.generate(**invalid_arguments)
    except Exception as exc:  # evidence records exact fail-closed behavior
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}
    assert invalid_exception is not None
    assert invalid_exception["type"] == "ValueError"
    assert "outside [5, 8]" in invalid_exception["message"]

    report = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "status": "completed",
        "consumer": "target_current_audit",
        "scope": "One advertised grid_h valid/invalid override comparison; no broader API battery.",
        "task_id": TASK_ID,
        "source_path": f"repo/generators/{TASK_ID}/generator.py",
        "source_sha256": source_sha,
        "rule_hash": rule_hash,
        "probe_seed_hex": PROBE_SEED_HEX,
        "advertised_boundary": generator.AXES["grid_h"],
        "valid_call": {
            "arguments": valid_arguments,
            "shape": [len(valid_grid), len(valid_grid[0])],
            "grid_sha256": grid_sha(valid_grid),
            "self_check_errors": valid_errors,
        },
        "invalid_call": {
            "arguments": invalid_arguments,
            "exception": invalid_exception,
        },
        "summary": "The selected lower grid_h boundary failed closed as advertised: grid_h=5 produced a valid five-row puzzle, while grid_h=4 raised ValueError under the generator's default [5, 8] draw band.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "valid_shape": report["valid_call"]["shape"], "invalid_exception": invalid_exception["type"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
