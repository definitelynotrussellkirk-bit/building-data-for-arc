#!/usr/bin/env python3
"""One bounded valid/invalid comparison for the advertised shape_k override."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import time

TICKET_ID = "ticket-e04fb3afba5fdd7c"
TASK_ID = "027805c8ff0f"
PINNED_SOURCE_SHA256 = "cc7cb34ad70900c3f201c5679125e0d51f2163ec4a75c952a2bc816430f4c5a0"
PROBE_SEED_HEX = "8605d77212b9786993de88599f86f14f9f93d157a982bf4c2a377ec06d725745"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> int:
    repo = Path(__file__).resolve().parents[3] / "repo"
    source = repo / "generators" / TASK_ID / "generator.py"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha != PINNED_SOURCE_SHA256:
        raise SystemExit(f"pinned source mismatch: {source_sha}")

    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load pinned generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    seed = int(PROBE_SEED_HEX, 16)
    started = time.monotonic()
    calls = []
    for label, shape_k in (("valid", 3), ("invalid", 999)):
        try:
            grid = module.generate(seed, 0, shape_k=shape_k)
            errors = module.self_check(grid)
            payload = canonical_bytes(grid)
            calls.append({
                "label": label,
                "shape_k": shape_k,
                "status": "returned",
                "grid_sha256": hashlib.sha256(payload).hexdigest(),
                "grid_dimensions": [len(grid), len(grid[0])],
                "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
                "self_check": errors,
            })
        except Exception as exc:  # retain exact observed boundary behavior
            calls.append({
                "label": label,
                "shape_k": shape_k,
                "status": "raised",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            })
    elapsed = time.monotonic() - started
    identical = (
        calls[0].get("status") == "returned"
        and calls[1].get("status") == "returned"
        and calls[0].get("grid_sha256") == calls[1].get("grid_sha256")
    )
    result = {
        "schema": "arcpuzzles-supplementary-probe-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED_HEX,
        "source": {"path": f"repo/generators/{TASK_ID}/generator.py", "sha256": source_sha},
        "advertised_axis": {
            "name": "shape_k",
            "type": module.AXES["shape_k"]["type"],
            "valid": module.AXES["shape_k"]["valid"],
            "doc": module.AXES["shape_k"]["doc"],
        },
        "comparison": calls,
        "same_output_for_valid_and_invalid": identical,
        "elapsed_seconds": round(elapsed, 6),
        "observation": (
            "The advertised shape_k override is not consumed: valid shape_k=3 and "
            "out-of-range shape_k=999 both returned the same self-checking grid."
            if identical else
            "The valid and invalid calls did not return identical successful results; see comparison."
        ),
        "proposed_disposition": "finding" if identical else "completed",
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
