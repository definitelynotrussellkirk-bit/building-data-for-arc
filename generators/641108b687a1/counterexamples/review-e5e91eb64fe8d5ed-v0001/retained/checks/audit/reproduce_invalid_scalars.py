#!/usr/bin/env python3
"""Reproduce accepted malformed generator call scalars in one selected source tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import load_selected_generator  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    generator, source, source_sha = load_selected_generator(args.task_id, root=REPO)
    probes = []
    for label, seed, sample_index in (
        ("bool_seed", True, 0),
        ("negative_sample_index", 991, -1),
    ):
        try:
            grid = generator.generate(seed, sample_index, difficulty="medium")
        except Exception as exc:  # A rejecting generator is recorded, not hidden.
            probes.append(
                {
                    "probe": label,
                    "status": "rejected",
                    "exception": type(exc).__name__,
                    "message": str(exc),
                }
            )
            continue
        encoded = json.dumps(grid, separators=(",", ":")).encode()
        probes.append(
            {
                "probe": label,
                "arguments": {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": "medium",
                },
                "status": "accepted_invalid_scalar",
                "grid_sha256": hashlib.sha256(encoded).hexdigest(),
                "shape": [len(grid), len(grid[0])],
                "self_check": generator.self_check(grid),
            }
        )

    report = {
        "schema": "audit-invalid-call-scalars-v1",
        "task_id": args.task_id,
        "source": str(source.relative_to(REPO)),
        "source_sha256": source_sha,
        "probes": probes,
        "command": {
            "cwd": str(WORK),
            "argv": [
                "python3",
                "checks/audit/reproduce_invalid_scalars.py",
                args.task_id,
                "--out",
                args.out,
            ],
        },
    }
    output = Path(args.out)
    if not output.is_absolute():
        output = WORK / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
