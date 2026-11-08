#!/usr/bin/env python3
"""One minimal valid/invalid override comparison for generator 250a48232c34."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "250a48232c34"
TICKET_ID = "ticket-b3763394f9fce257"
SOURCE = REPO / "generators" / TASK / "generator.py"
SOURCE_SHA256 = "ce145a88a6aac20d9d4bba277674ded55bb3e36e1ff474b91f745b99502494e9"
UNKNOWN_KEY = "n_anchor"  # one-character typo of advertised AXES['n_anchors']
OUT = HERE / "probe.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_grid(grid) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_generator_250a", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def count_anchors(grid) -> int:
    return sum(1 <= value <= 4 for row in grid for value in row)


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(SOURCE) == SOURCE_SHA256
    generator = load_module(SOURCE)
    assert generator.AXES["n_anchors"]["type"] == "int"
    assert generator.AXES["n_anchors"]["valid"] == "1..4"
    assert UNKNOWN_KEY not in generator.AXES

    common = {"seed": 0, "sample_index": 3, "difficulty": "easy", "n_anchors": 2}
    valid = generator.generate(**common)
    invalid_exception = None
    try:
        invalid = generator.generate(**common, **{UNKNOWN_KEY: 999})
    except Exception as exc:  # a correct boundary rejects loudly
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}
        invalid = None

    valid_errors = generator.self_check(valid, difficulty="easy")
    assert valid_errors == []
    valid_hash = sha256_grid(valid)
    invalid_hash = sha256_grid(invalid) if invalid is not None else None
    invalid_errors = generator.self_check(invalid, difficulty="easy") if invalid is not None else None
    unknown_key_accepted = invalid_exception is None
    identical_to_valid = invalid is not None and invalid == valid

    # The advertised override boundary is exact-or-loud. This source silently
    # accepts and ignores a typo of n_anchors, so the invalid call is indistinguishable.
    assert unknown_key_accepted
    assert identical_to_valid
    assert invalid_errors == []
    assert count_anchors(valid) == 2 == count_anchors(invalid)

    report = {
        "schema": "arcpuzzles-api-boundary-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "finding",
        "task_id": TASK,
        "source_sha256": SOURCE_SHA256,
        "advertised_axis": {
            "name": "n_anchors",
            "type": "int",
            "valid": "1..4",
        },
        "valid_call": {
            "kwargs": common,
            "grid_sha256": valid_hash,
            "anchor_count": count_anchors(valid),
            "self_check": valid_errors,
        },
        "invalid_call": {
            "kwargs": {**common, UNKNOWN_KEY: 999},
            "unknown_key": UNKNOWN_KEY,
            "exception": invalid_exception,
            "grid_sha256": invalid_hash,
            "anchor_count": count_anchors(invalid),
            "self_check": invalid_errors,
        },
        "comparison": {
            "unknown_key_accepted": unknown_key_accepted,
            "invalid_output_identical_to_valid": identical_to_valid,
        },
        "finding": (
            "generate() silently accepts the unknown override key 'n_anchor' next to the "
            "advertised 'n_anchors' axis. The invalid call returns the exact valid grid, "
            "so a typo or stale API call reads as success."
        ),
        "suggested_repair": (
            "Reject keys outside AXES before constructing GenCtx, then retain this exact "
            "valid/typo pair as a focused regression."
        ),
        "limitations": [
            "One source-bound valid/invalid comparison only; no full override matrix or peer battery.",
            "This ticket records behavior and makes no peer source edit.",
        ],
        "command": f"python3 review.py run python3 ../checks/tickets/{TICKET_ID}/probe.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "finding", "accepted": True, "identical": True, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
