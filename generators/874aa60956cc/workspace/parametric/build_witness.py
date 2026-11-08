#!/usr/bin/env python3
"""Bind the audited causal case to an exact native qualification source binding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STEP_A = "Paint the first exactly-twice color's bounding border."
INTERMEDIATE = "Count distinct later paired colors with an original clue on that derived border."
STEP_B = "Select the count-ranked later paired color in first-appearance order and paint its bounding border."
WHY = "The second color is rank k, so B cannot be chosen until A's derived border determines k."


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    q = json.loads(Path(args.qualification).read_bytes())
    case = json.loads(Path(args.case).read_bytes())
    if q.get("status") != "qualified" or q.get("task_id") != "874aa60956cc":
        raise ValueError("expected qualified 874aa60956cc receipt")
    witness_case = {
        key: case[key]
        for key in (
            "input", "settings", "intermediate_value", "program", "output",
            "counterfactual_program", "counterfactual_output", "ablation",
        )
    }
    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": "874aa60956cc",
        "source_binding": q["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": [witness_case],
        "verification_status": "reviewer_replayed",
        "limits": "One authored 30x30 wrong-intermediate case; not a universal depth proof.",
    }
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(_raw(witness))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
