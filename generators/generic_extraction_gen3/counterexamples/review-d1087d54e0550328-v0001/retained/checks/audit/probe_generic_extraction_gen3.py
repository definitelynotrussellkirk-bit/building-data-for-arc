#!/usr/bin/env python3
"""Reproduce the fixed output-corner role invariant in generic_extraction_gen3."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    path = repo / "generators/generic_extraction_gen3/generator.py"
    spec = importlib.util.spec_from_file_location("audit_generic_extraction_gen3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pair_count = 0
    fixed = 0
    nonempty = 0
    shape_counts: Counter[str] = Counter()
    program_hashes: set[str] = set()
    examples = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(100):
            seed = 700000 + band_index * 10000 + offset
            task = module.generate_task(seed, difficulty=band)
            program_hashes.add(hashlib.sha256(task["program"].encode()).hexdigest())
            ca, cb = task["meta"]["mapping"].keys()
            db, dd = task["meta"]["mapping"][ca], task["meta"]["mapping"][cb]
            for pair in [*task["train"], *task["test"]]:
                pair_count += 1
                output = pair["output"]
                if output and output[0]:
                    nonempty += 1
                    shape_counts[f"{len(output)}x{len(output[0])}"] += 1
                    corners = [
                        output[0][0], output[0][-1],
                        output[-1][0], output[-1][-1],
                    ]
                    if corners == [db, dd, dd, db]:
                        fixed += 1
                    if len(examples) < 3:
                        examples.append({
                            "band": band,
                            "seed": seed,
                            "input_shape": [len(pair["input"]), len(pair["input"][0])],
                            "output_shape": [len(output), len(output[0])],
                            "mapping": {str(key): value for key, value in task["meta"]["mapping"].items()},
                            "output_corners": corners,
                        })

    report = {
        "schema": "audit-shortcut-probe/1",
        "task_id": "generic_extraction_gen3",
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "command": [
            "python3", "run_with_racket.py", "python3",
            "checks/audit/probe_generic_extraction_gen3.py",
        ],
        "runtime_cwd": str(repo),
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "seeds_per_band": 100,
            "seed_ranges": {
                "easy": "700000..700099",
                "medium": "710000..710099",
                "hard": "720000..720099",
            },
        },
        "counts": {
            "tasks": 300,
            "pairs": pair_count,
            "nonempty_outputs": nonempty,
            "fixed_diagonal_corner_role_outputs": fixed,
            "distinct_program_hashes": len(program_hashes),
        },
        "fixed_corner_fraction": fixed / pair_count,
        "output_shapes": dict(sorted(shape_counts.items())),
        "examples": examples,
        "finding": (
            "Every generated output fixes recolored role db at top-left/bottom-right "
            "and dd at top-right/bottom-left because input window corners are forced "
            "to ca/cb/cb/ca. This supports a corner-role shortcut not required by "
            "remove-color + arbitrary recolor-map + crop."
        ),
        "limitation": (
            "The shortcut agrees on the current generated domain; this is a support "
            "finding, not an incorrect label."
        ),
    }
    destination = repo.parent / "checks/audit/generic_extraction_gen3-corner-probe.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["counts"], sort_keys=True))
    return 0 if fixed == pair_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
