"""Write a parsed, setting-comparison record for one generated decoder board."""
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
spec = importlib.util.spec_from_file_location("_decoder_inspect_generator", path)
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--sample-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    grid = g.sample(args.seed, args.sample_index)
    info = g.analyse(grid)
    record = {
        "schema": "keyed-decoder-inspection-v1",
        "task_id": g.TASK_ID,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "input": grid,
        "analysis": info,
        "outputs": {mode: g.solve(grid, mode) for mode in g.BINDING_MODES},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tile_size": info["tile_size"], "tokens": sum(v != 0 for row in info["tokens"] for v in row), "out": str(args.out)}))


if __name__ == "__main__":
    main()
