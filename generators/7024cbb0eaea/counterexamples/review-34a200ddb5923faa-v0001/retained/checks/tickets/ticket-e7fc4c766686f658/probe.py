#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback

TASK_ID = "7024cbb0eaea"
EXPECTED_SOURCE_SHA256 = "cfb3d91cc4f732e65c3dda1a48d7dc71cc36cd21d03f0a3a8e8b018e5b60a89e"


def run_call(module, **overrides):
    try:
        grid = module.generate(0, 0, difficulty="easy", **overrides)
    except Exception as exc:  # retain exact public API behavior
        return {
            "accepted": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    return {
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    runtime = root / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    from reviewer_support import load_selected_generator  # noqa: PLC0415

    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    source_bytes = source_path.read_bytes()
    exact_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != exact_sha256 or exact_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"source binding mismatch: helper={source_sha256} exact={exact_sha256}"
        )

    accepted = run_call(module, grid_h=7)
    advertised_lower_bound = run_call(module, grid_h=5)
    finding = (
        module.AXES["grid_h"]["valid"] == "5..18"
        and accepted.get("accepted") is True
        and advertised_lower_bound.get("accepted") is False
    )
    payload = {
        "schema": "arcpuzzles-supplementary-api-boundary-v1",
        "ticket_id": "ticket-e7fc4c766686f658",
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": exact_sha256,
        "advertised_axis": module.AXES["grid_h"],
        "comparison": {
            "runtime_accepted_grid_h_7": accepted,
            "advertised_grid_h_5": advertised_lower_bound,
        },
        "finding": finding,
        "summary": (
            "AXES advertises grid_h=5..18, but the easy generator accepts 7 and "
            "rejects the advertised lower bound 5 because draw_int is called with 7..8."
            if finding
            else "No mismatch reproduced at the inspected grid_h boundary."
        ),
        "scope": "Two generate calls at seed=0/sample_index=0/difficulty=easy; no census.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
