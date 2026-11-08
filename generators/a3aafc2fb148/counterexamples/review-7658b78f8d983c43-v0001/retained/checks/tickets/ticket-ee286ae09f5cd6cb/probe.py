#!/usr/bin/env python3
"""One source-bound valid/invalid override comparison for ticket-ee286ae09f5cd6cb."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator, normalize_grid

TICKET_ID = "ticket-ee286ae09f5cd6cb"
TASK_ID = "a3aafc2fb148"
EXPECTED_SOURCE_SHA256 = "4c2410e8d185cd87ac946f28775c30046545fcd8a384b102c54c98e6705a860a"
TICKET_SEED = "cfb989cf7f04004f257e162cda85e2621703d931c2f7178b686238669444f5a1"


def grid_sha256(grid: Any) -> str:
    body = json.dumps(normalize_grid(grid), separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def call(generator: Any, *, seed: int, fill_density: float) -> dict[str, Any]:
    overrides = {
        "sample_h": 3,
        "sample_w": 3,
        "palette_size": 3,
        "texture": "checkerboard",
        "odd_cell_mode": "all_bg",
        "noise_overlay": 0.0,
        "fill_density": fill_density,
    }
    try:
        grid = normalize_grid(generator.generate(seed, 0, difficulty=None, **overrides))
        errors = list(generator.self_check(grid, difficulty=None, meta={}))
        return {
            "accepted": True,
            "fill_density": fill_density,
            "grid_shape": [len(grid), len(grid[0])],
            "grid_sha256": grid_sha256(grid),
            "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
            "self_check": errors,
            "exception": None,
        }
    except Exception as exc:  # Evidence records actual fail-closed behavior if present.
        return {
            "accepted": False,
            "fill_density": fill_density,
            "grid_shape": None,
            "grid_sha256": None,
            "nonzero_cells": None,
            "self_check": None,
            "exception": {"type": type(exc).__name__, "message": str(exc)},
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {source_sha256}")

    axis = generator.AXES["fill_density"]
    if axis.get("valid") != "0.10..1.0":
        raise SystemExit(f"advertised boundary changed: {axis!r}")

    seed = int(TICKET_SEED[:16], 16)
    valid = call(generator, seed=seed, fill_density=0.10)
    invalid = call(generator, seed=seed, fill_density=0.099)
    invalid_accepted = bool(invalid["accepted"])
    result = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "source_path": source_path.relative_to(root).as_posix(),
        "source_sha256": source_sha256,
        "axis": "fill_density",
        "advertised": axis,
        "comparison": {
            "valid_lower_boundary": valid,
            "invalid_just_below_lower_boundary": invalid,
        },
        "status": "finding" if invalid_accepted else "completed",
        "finding": (
            "fill_density=0.099 is outside the advertised 0.10..1.0 domain but was accepted"
            if invalid_accepted
            else None
        ),
        "conclusion": (
            "The direct float override is converted with float() but is not range-checked; "
            "the invalid call returned a self-check-valid grid."
            if invalid_accepted
            else "The invalid call failed closed at the advertised lower boundary."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
