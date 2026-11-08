#!/usr/bin/env python3
"""One advertised-boundary comparison for 7284e86d3539.grid_h."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TICKET_ID = "ticket-758bcb4bd10a4f58"
TASK_ID = "7284e86d3539"
PINNED_SHA256 = "68512e94c82664f0504c1192832bfdb13e7a6848179458ccb34f32a38c86a275"
PINNED_RULE_HASH = "f64d7e09c9f4"
PROBE_SEED_HEX = "562c238c6672e32590bb50e30dc89418a2c5469619ff37190193f358586c3fb1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha_json(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> int:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha256 != PINNED_SHA256:
        raise RuntimeError(f"source drift: {source_sha256} != {PINNED_SHA256}")
    declared = generator.AXES["grid_h"]
    if declared.get("valid") != "6":
        raise RuntimeError(f"unexpected declared grid_h contract: {declared}")

    numeric_seed = int(PROBE_SEED_HEX[:16], 16)
    common = {
        "seed": numeric_seed,
        "sample_index": 0,
        "difficulty": "medium",
    }
    valid_grid = generator.generate(**common, grid_h=6)
    metadata_invalid_grid = generator.generate(**common, grid_h=7)
    valid_check = generator.self_check(valid_grid)
    metadata_invalid_check = generator.self_check(metadata_invalid_grid)

    finding = (
        len(valid_grid) == 6
        and len(metadata_invalid_grid) == 7
        and not valid_check
        and not metadata_invalid_check
    )
    report = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "status": "finding" if finding else "completed",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed_hex": PROBE_SEED_HEX,
        "numeric_seed": numeric_seed,
        "sample_index": 0,
        "difficulty": "medium",
        "source": {
            "path": str(Path(source_path).relative_to(ROOT)),
            "sha256": source_sha256,
            "version": generator.VERSION,
            "rule_hash": PINNED_RULE_HASH,
        },
        "axis": "grid_h",
        "advertised_contract": declared,
        "valid_call": {
            "override": 6,
            "accepted": True,
            "observed_dimensions": [len(valid_grid), len(valid_grid[0])],
            "self_check": valid_check,
            "grid_sha256": sha_json(valid_grid),
        },
        "metadata_invalid_call": {
            "override": 7,
            "accepted": True,
            "observed_dimensions": [
                len(metadata_invalid_grid),
                len(metadata_invalid_grid[0]),
            ],
            "self_check": metadata_invalid_check,
            "grid_sha256": sha_json(metadata_invalid_grid),
        },
        "finding": (
            "AXES advertises grid_h valid=6, but generate(..., difficulty='medium', "
            "grid_h=7) accepts the override, returns a 7-row grid, and self_check "
            "accepts it. The metadata/API boundary is therefore not enforced."
            if finding
            else None
        ),
        "suggested_repair": (
            "Align AXES with the intended variable-size contract, or enforce grid_h=6 "
            "with an exact override gate; add a boundary test for 6 versus 7."
            if finding
            else None
        ),
        "limitations": [
            "One valid/metadata-invalid comparison was executed; other axes were not audited.",
            "No claim is made about semantic rule correctness or output packing.",
        ],
    }
    out = HERE / "boundary.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "declared_valid": declared.get("valid"),
                "valid_dimensions": report["valid_call"]["observed_dimensions"],
                "metadata_invalid_dimensions": report["metadata_invalid_call"]["observed_dimensions"],
                "metadata_invalid_self_check": metadata_invalid_check,
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
