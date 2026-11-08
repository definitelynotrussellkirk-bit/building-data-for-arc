#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "241567a35764"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    seed = 0
    sample_index = 1
    difficulty = "easy"
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    payload = {
        "schema": "arcpuzzles-audit-generator-witness-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": {},
        "self_check": gen.self_check(grid, difficulty=difficulty),
        "input": grid,
    }
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (out / "generator_witness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "generator_sha256": digest,
        "self_check": payload["self_check"],
        "input": str(out / "input.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
