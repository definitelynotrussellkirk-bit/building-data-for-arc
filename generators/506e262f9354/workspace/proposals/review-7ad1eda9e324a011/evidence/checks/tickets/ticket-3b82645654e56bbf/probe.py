#!/usr/bin/env python3
"""One bounded valid/invalid override comparison for ticket-3b82645654e56bbf."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import load_selected_generator

TICKET_ID = "ticket-3b82645654e56bbf"
TASK_ID = "222de43cc4aa"
PINNED_SEED = "e9f16724d227c61059c67b91dc5b343d530473b39fc207dd1cab0e88fbb26690"
EXPECTED_SHA = "0e43a13ef9eb3745adf7a22d5973a2e9b7a0d691666136b25adaf7d0d0b7b04a"
RULE_HASH = "ce9518b81cf8"


def grid_sha256(grid) -> str:
    raw = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()

    module, source, digest = load_selected_generator(TASK_ID, root=REPO)
    seed = int(PINNED_SEED[:16], 16) & 0x7FFFFFFF

    valid_grid = module.generate(seed, 0, difficulty="hard", grid_h=3)
    valid = {
        "arguments": {"seed": seed, "sample_index": 0, "difficulty": "hard", "grid_h": 3},
        "shape": [len(valid_grid), len(valid_grid[0])],
        "grid_sha256": grid_sha256(valid_grid),
        "observed_overrides": module.observe_overrides(valid_grid),
        "self_check_errors": module.self_check(valid_grid, difficulty="hard"),
    }

    invalid = {
        "arguments": {"seed": seed, "sample_index": 0, "difficulty": "hard", "grid_h": 2},
        "raised": False,
        "exception": None,
        "message": None,
    }
    try:
        module.generate(seed, 0, difficulty="hard", grid_h=2)
    except Exception as exc:  # retain exact observed fail-closed behavior
        invalid.update(raised=True, exception=type(exc).__name__, message=str(exc))

    passed = (
        digest == EXPECTED_SHA
        and valid["shape"][0] == 3
        and valid["observed_overrides"].get("grid_h") == 3
        and valid["self_check_errors"] == []
        and invalid["raised"] is True
        and invalid["exception"] in {"TypeError", "ValueError"}
        and "grid_h" in (invalid["message"] or "")
    )
    report = {
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "pinned_seed": PINNED_SEED,
        "derived_integer_seed": seed,
        "source_path": f"repo/{source.relative_to(REPO).as_posix()}",
        "source_sha256": digest,
        "expected_source_sha256": EXPECTED_SHA,
        "rule_hash": RULE_HASH,
        "advertised_boundary": "AXES.grid_h exact integer range 3..8",
        "valid_call": valid,
        "invalid_call": invalid,
        "passed": passed,
        "elapsed_seconds": time.monotonic() - started,
        "scope": "one valid/invalid call comparison; no peer source edits or broader battery",
        "conclusion": (
            "grid_h=3 is honored and observable, while grid_h=2 is rejected before generation"
            if passed else "the advertised grid_h boundary did not reproduce exactly"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
