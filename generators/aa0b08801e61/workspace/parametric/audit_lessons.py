#!/usr/bin/env python3
"""Bounded reusable lesson audit for the symmetry signal-rank family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().with_name("prototype.py")
NAME = "_audit_aa0b_signal_rank_" + hashlib.sha256(str(SOURCE).encode()).hexdigest()
SPEC = importlib.util.spec_from_file_location(NAME, SOURCE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(SOURCE)
PROTOTYPE = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = PROTOTYPE
exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), PROTOTYPE.__dict__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        parser.error("--seeds must be in 1..4096")
    rows = []
    failures = []
    stress_pairs = 0
    for seed in range(args.seeds):
        for mode in PROTOTYPE.MODES:
            for demos in (2, 3, 6):
                row = PROTOTYPE.audit_episode(seed, mode, demos=demos, queries=4)
                rows.append(row)
                stress_pairs += sum(shape == [30, 30] for shape in row["query_shapes"])
                failures.extend({**finding, "seed": seed, "mode": mode, "demos": demos}
                                for finding in row["findings"])
    result = {
        "schema": "arc-parametric-lesson-audit-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "prototype_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seeds": args.seeds,
        "episodes": len(rows),
        "pairs": sum(row["demos"] + row["queries"] for row in rows),
        "settings": list(PROTOTYPE.MODES),
        "demo_counts": [2, 3, 6],
        "query_count": 4,
        "exact_30x30_pairs": stress_pairs,
        "harmful_survivors": failures,
        "status": "passed" if not failures else "failed",
        "limits": "Finite declared settings and twelve named shortcut programs; not universal uniqueness.",
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "episodes", "pairs", "exact_30x30_pairs")}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
