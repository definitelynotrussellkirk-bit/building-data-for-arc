#!/usr/bin/env python3
"""One bounded advertised-API boundary probe for generator 7358813cf026."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from reviewer_support import find_root, load_selected_generator

TASK_ID = "7358813cf026"
EXPECTED_SHA256 = "78e2127b1eed53109573d2f798d7f3bb7c4d335c9d5fcd81bdf64cc032f5a989"
PROBE_SEED_HEX = "6ee8f08a79478c8bfd10a9b769c6e61c775098e2aa95fbccecec8e8b8fb7fb59"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    root = find_root(__file__)
    module, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SHA256:
        raise AssertionError(f"source drift: {digest}")
    seed = int(PROBE_SEED_HEX[:16], 16) % (2**63)
    sample_index = int(PROBE_SEED_HEX[16:24], 16) % (2**31)

    valid_grid = module.generate(seed, sample_index, grid_h=8)
    valid = {
        "call": {"seed": seed, "sample_index": sample_index, "grid_h": 8},
        "accepted": True,
        "observed_height": len(valid_grid),
        "observed_width": len(valid_grid[0]),
        "self_check": module.self_check(valid_grid),
    }
    if valid["observed_height"] != 8:
        raise AssertionError(valid)

    invalid = {
        "call": {"seed": seed, "sample_index": sample_index, "grid_h": 4},
        "advertised_valid": module.AXES["grid_h"]["valid"],
    }
    try:
        module.generate(seed, sample_index, grid_h=4)
    except Exception as exc:
        invalid.update(
            {
                "accepted": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
    else:
        invalid["accepted"] = True

    finding = (
        module.AXES["grid_h"]["valid"] == "4..20"
        and invalid.get("accepted") is False
        and "outside [8, 11]" in invalid.get("error", "")
    )
    result = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": "ticket-22fa45fbe13808da",
        "type": "api_boundary",
        "task_id": TASK_ID,
        "source_path": str(source.relative_to(root)),
        "source_sha256": digest,
        "rule_hash": getattr(module, "RULE_HASH", "a01a7d7e0859"),
        "probe_seed": PROBE_SEED_HEX,
        "elapsed_minutes": round((time.monotonic() - started) / 60, 6),
        "advertised_axis": {"grid_h": module.AXES["grid_h"]},
        "valid_call": valid,
        "advertised_boundary_call": invalid,
        "status": "finding" if finding else "completed",
        "finding": (
            "AXES advertises grid_h=4..20, but the default generation path "
            "accepts grid_h=8 and rejects the advertised lower boundary grid_h=4 "
            "against its narrower draw range [8, 11]."
            if finding
            else None
        ),
        "limits": [
            "One axis and one valid/invalid comparison were probed.",
            "No peer source was modified and no broader battery was run.",
        ],
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
