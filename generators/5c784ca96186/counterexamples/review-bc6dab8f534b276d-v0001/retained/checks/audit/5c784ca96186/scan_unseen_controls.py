#!/usr/bin/env python3
"""Count production-style 3-demo lessons whose query control was never demonstrated."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "5c784ca96186"
HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
GENERATOR = WORK / "repo" / "generators" / TASK / "generator.py"
RUNTIME = WORK / "repo" / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_5c784ca96186", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def control(grid):
    values = [v for row in grid for v in row if v in (1, 3, 4, 6)]
    if len(values) != 1:
        raise ValueError(f"expected one control, found {values}")
    return values[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    gen = load_generator()
    unseen = []
    generation_errors = []
    for seed in range(args.seeds):
        try:
            controls = [control(gen.generate(seed, i)) for i in range(gen.EXAMPLES_NEEDED + 1)]
        except Exception as exc:
            generation_errors.append({"seed": seed, "error": repr(exc)})
            continue
        if controls[-1] not in controls[:-1]:
            unseen.append({"seed": seed, "controls": controls})
    report = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "seed_range": [0, args.seeds - 1],
        "lessons_requested": args.seeds,
        "lessons_generated": args.seeds - len(generation_errors),
        "generation_errors": generation_errors,
        "query_control_unseen_count": len(unseen),
        "query_control_unseen_fraction": len(unseen) / max(1, args.seeds - len(generation_errors)),
        "first_examples": unseen[:10],
        "assembly": "sample indices 0..EXAMPLES_NEEDED, final sample treated as query",
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
