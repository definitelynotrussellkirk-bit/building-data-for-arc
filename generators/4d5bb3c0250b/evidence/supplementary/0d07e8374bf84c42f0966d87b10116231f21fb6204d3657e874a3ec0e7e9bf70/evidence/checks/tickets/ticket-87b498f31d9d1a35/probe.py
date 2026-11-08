#!/usr/bin/env python3
"""Minimal valid/invalid API-boundary probe for 4d5bb3c0250b."""
from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = next(parent / "repo" for parent in HERE.parents if (parent / "repo" / "shared" / "runtime").is_dir())
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "4d5bb3c0250b"
TICKET_ID = "ticket-87b498f31d9d1a35"
PINNED_GENERATOR_SHA256 = "268443a7bf130a55f9d1d6aca5767e0e820edc8bcef4de01d490867bd5be7c54"
PINNED_RULE_HASH = "0bc50653fe24"
SEED_HEX = "cdbe5511ac4ee515ee75d2736e9948f92ac71d63922212c155981b62e457f200"


def main() -> int:
    module, source, digest = load_selected_generator(TASK_ID, root=REPO)
    if digest != PINNED_GENERATOR_SHA256:
        raise RuntimeError(f"generator changed: {digest}")
    seed = int(SEED_HEX[:16], 16) % (2**31)
    sample_index = 0

    valid_grid = module.generate(
        seed,
        sample_index,
        difficulty="medium",
        target_at_border=False,
    )
    observed = module.observe_overrides(valid_grid)
    valid_errors = module.self_check(valid_grid, difficulty="medium")

    invalid_exception = None
    try:
        module.generate(
            seed,
            sample_index,
            difficulty="medium",
            target_at_border=0,
        )
    except Exception as exc:  # report the actual boundary behavior
        invalid_exception = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    passed = (
        valid_errors == []
        and observed.get("target_at_border") is False
        and invalid_exception == {
            "type": "TypeError",
            "message": "target_at_border must be a literal bool",
        }
    )
    report = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "status": "completed" if passed else "unknown",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "source": {
            "path": str(source.relative_to(REPO)),
            "sha256": digest,
            "pinned_sha256": PINNED_GENERATOR_SHA256,
        },
        "rule_hash": PINNED_RULE_HASH,
        "probe": {
            "seed_hex": SEED_HEX,
            "seed_int": seed,
            "sample_index": sample_index,
            "difficulty": "medium",
            "axis": "target_at_border",
        },
        "valid_call": {
            "override": False,
            "accepted": True,
            "observed_overrides": observed,
            "self_check": valid_errors,
            "grid_shape": [len(valid_grid), len(valid_grid[0])],
        },
        "invalid_call": {
            "override": 0,
            "accepted": invalid_exception is None,
            "exception": invalid_exception,
        },
        "conclusion": (
            "The advertised bool axis accepts literal False and rejects integer 0 before generation, "
            "so Python's bool/int coercion does not cross this API boundary."
            if passed
            else "The observed behavior did not match the advertised literal-bool boundary."
        ),
    }
    out = HERE.with_name("report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "valid_observed": observed.get("target_at_border"),
        "invalid_exception": invalid_exception,
        "report": str(out),
    }, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
