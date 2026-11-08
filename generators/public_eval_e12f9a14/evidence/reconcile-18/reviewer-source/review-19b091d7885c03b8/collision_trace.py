"""Write a replayable JSON trace for one generated e12f9a14 scene."""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
path = HOME / "generator.py"
spec = importlib.util.spec_from_file_location("_e12_trace_generator", path)
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--sample-index", type=int, required=True)
    parser.add_argument("--rule", choices=g.COLLISION_RULES, default="vector_sum")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    grid = g.sample(args.seed, args.sample_index)
    record = {
        "schema": "ray-merge-trace-v1",
        "task_id": g.TASK_ID,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "collision_rule": args.rule,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "input": grid,
        **g.trace(grid, args.rule),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"events": len(record["events"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
