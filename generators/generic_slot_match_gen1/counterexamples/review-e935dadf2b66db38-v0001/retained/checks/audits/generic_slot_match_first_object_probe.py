#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "repo/generators/generic_slot_match_gen1/generator.py"
OUT = ROOT / "checks/audits/generic_slot_match_gen1_first_object.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("generic_slot_match_audit", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_matching_object_rival(gen, grid):
    """Use the first reading-order matching scattered object's color, not the mode."""
    bg = Counter(value for row in grid for value in row if value != 0).most_common(1)[0][0]
    objects = gen._components(grid, bg)
    template = objects[0]
    for obj in objects[1:]:
        if len(obj[1]) > len(template[1]):
            template = obj
    template_color, template_cells = template
    r1 = min(r for r, _ in template_cells)
    c1 = min(c for _, c in template_cells)
    r2 = max(r for r, _ in template_cells)
    c2 = max(c for _, c in template_cells)
    subgrid = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
    slots = [
        component
        for color, component in gen._components(subgrid, template_color)
        if color == bg
    ]

    def outside_template(component):
        rr1 = min(r for r, _ in component)
        cc1 = min(c for _, c in component)
        rr2 = max(r for r, _ in component)
        cc2 = max(c for _, c in component)
        return not (rr1 >= r1 and rr2 <= r2 and cc1 >= c1 and cc2 <= c2)

    scattered = [
        (color, component)
        for color, component in objects
        if outside_template(component)
    ]
    output = [row[:] for row in subgrid]
    for slot in slots:
        candidates = [
            (color, component)
            for color, component in scattered
            if gen._same_class(component, slot)
        ]
        chosen = candidates[0][0]
        for row, col in slot:
            output[row][col] = chosen
    return output


def main() -> int:
    gen = load_generator()
    bands = {}
    first_examples = {}
    for band in ("easy", "medium", "hard"):
        pair_total = 0
        pair_matches = 0
        train_survivors = 0
        test_failures_after_train_survival = 0
        first_example = None
        for seed in range(1000):
            task = gen.generate_task(seed, difficulty=band)
            train_rows = []
            train_survives = True
            for pair in task["train"]:
                rival = first_matching_object_rival(gen, pair["input"])
                matches = rival == pair["output"]
                pair_total += 1
                pair_matches += int(matches)
                train_survives = train_survives and matches
                train_rows.append({"matches": matches, "rival_output": rival})
            if not train_survives:
                continue
            train_survivors += 1
            test_rows = []
            test_disagrees = False
            for pair in task["test"]:
                rival = first_matching_object_rival(gen, pair["input"])
                matches = rival == pair["output"]
                test_disagrees = test_disagrees or not matches
                test_rows.append({"matches": matches, "rival_output": rival})
            if test_disagrees:
                test_failures_after_train_survival += 1
                if first_example is None:
                    first_example = {
                        "seed": seed,
                        "difficulty": band,
                        "train": [
                            {
                                "input": pair["input"],
                                "official_output": pair["output"],
                                **train_rows[index],
                            }
                            for index, pair in enumerate(task["train"])
                        ],
                        "test": [
                            {
                                "input": pair["input"],
                                "official_output": pair["output"],
                                **test_rows[index],
                            }
                            for index, pair in enumerate(task["test"])
                        ],
                    }
        bands[band] = {
            "tasks": 1000,
            "seed_range": "0..999",
            "training_pairs": pair_total,
            "pair_matches": pair_matches,
            "pair_match_rate": pair_matches / pair_total,
            "train_survivor_tasks": train_survivors,
            "train_survivor_rate": train_survivors / 1000,
            "test_disagreement_after_train_survival": test_failures_after_train_survival,
            "conditional_test_disagreement_rate": (
                test_failures_after_train_survival / train_survivors
                if train_survivors else 0.0
            ),
        }
        first_examples[band] = first_example

    report = {
        "schema": "generic-slot-match-first-object-audit-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "rival": (
            "For each slot class, choose the color of the first matching scattered "
            "object in reading order instead of counting the modal color."
        ),
        "sampler": {
            "difficulties": ["easy", "medium", "hard"],
            "seeds_per_band": 1000,
            "seed_range": "0..999",
            "task_sampler": "generate_task(seed, difficulty=band)",
        },
        "bands": bands,
        "first_counterexamples": first_examples,
        "claim_limit": (
            "This is a finite generated-task ambiguity census. Racket parity for "
            "the generator's official outputs is recorded separately."
        ),
        "command": [
            "env", "PYTHONPATH=repo/src:repo/shared/runtime", "python3",
            "checks/audits/generic_slot_match_first_object_probe.py"
        ],
        "cwd": "packet_root",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"bands": bands, "out": str(OUT)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
