#!/usr/bin/env python3
"""Reproduce rotation ambiguity and override-contract weakness for 78143e5d7ed1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "78143e5d7ed1"
GENERATOR = Path("generators") / TASK / "generator.py"
OUT = Path("../checks/audit") / TASK
SEED = 0
START_INDEX = 0
DIFFICULTY = "medium"
QUERY_POSITION = 1


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rival_without_height(module, grid):
    components = module._extract_components(grid)
    ordered = sorted(
        components,
        key=lambda obj: (obj.area, obj.width, obj.color),
    )
    return module._pack_components(grid, ordered)


def main() -> None:
    module = load_generator()
    OUT.mkdir(parents=True, exist_ok=True)

    pairs = []
    for offset in range(5):
        sample_index = START_INDEX + offset
        grid = module.generate(SEED, sample_index, difficulty=DIFFICULTY)
        expected = module._solve_grid(grid)
        pairs.append(
            {
                "seed": SEED,
                "sample_index": sample_index,
                "difficulty": DIFFICULTY,
                "profile": module._profile(module._extract_components(grid)),
                "input": grid,
                "output": expected,
                "rival_without_height": rival_without_height(module, grid),
                "self_check": module.self_check(grid),
            }
        )

    query = pairs[QUERY_POSITION]
    demos = [pair for index, pair in enumerate(pairs) if index != QUERY_POSITION]
    demo_fit = [
        pair["rival_without_height"] == pair["output"]
        for pair in demos
    ]
    query_differs = query["rival_without_height"] != query["output"]

    unknown_override = {"accepted": False, "exception": None}
    try:
        module.generate(SEED, 0, difficulty=DIFFICULTY, typo_axis=123)
        unknown_override["accepted"] = True
    except Exception as exc:  # noqa: BLE001 - evidence records exact behavior
        unknown_override["exception"] = f"{type(exc).__name__}: {exc}"

    summary = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK,
        "generator_path": str(GENERATOR),
        "generator_sha256": sha256(GENERATOR),
        "declared_rule_hash": module.RULE_HASH,
        "version": module.VERSION,
        "seed": SEED,
        "start_index": START_INDEX,
        "difficulty": DIFFICULTY,
        "lesson_size": 5,
        "demonstration_count": 4,
        "query_position": QUERY_POSITION,
        "profiles": [pair["profile"] for pair in pairs],
        "rival": {
            "name": "omit_height_key",
            "sort_key": ["area", "width", "color"],
            "fits_all_demonstrations": all(demo_fit),
            "demonstration_fit_vector": demo_fit,
            "changes_query_answer": query_differs,
        },
        "query_self_check": query["self_check"],
        "query_belongs_to_documented_generator_domain": query["self_check"] == [],
        "unknown_override_probe": unknown_override,
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/78143e5d7ed1/reproduce.py",
        ],
        "effective_cwd": "WORK/repo",
    }
    if not all(demo_fit) or not query_differs:
        raise AssertionError(summary)
    if query["self_check"]:
        raise AssertionError(summary)
    if not unknown_override["accepted"]:
        raise AssertionError(summary)

    (OUT / "probe.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "lesson.json").write_text(json.dumps({
        "task_id": TASK,
        "query_position": QUERY_POSITION,
        "pairs": pairs,
    }, indent=2) + "\n")
    (OUT / "input.json").write_text(json.dumps(query["input"], indent=2) + "\n")
    (OUT / "mirror_expected.json").write_text(json.dumps(query["output"], indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(query["rival_without_height"], indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
