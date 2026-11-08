from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

TASK_ID = "7944933e200f"
EXPECTED_GENERATOR_SHA256 = "5b2e0eb65c42a9cd61ad2f041463a0db226957cec6b6e8be1213280dbad74473"
SEED = 0
START_SAMPLE_INDEX = 5
DIFFICULTY = "medium"
DEMO_COUNT = 3


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def singleton_minimum_color_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: emit only first minimum-frequency color cell."""
    counts = Counter(value for row in grid for value in row if value != 0)
    minimum = min(counts.values())
    minimum_colors = {color for color, count in counts.items() if count == minimum}
    for row in grid:
        for value in row:
            if value in minimum_colors:
                return [[value]]
    raise ValueError("grid has no nonzero cells")


def main() -> int:
    repo = Path(__file__).resolve().parents[3] / "repo"
    generator_path = repo / "generators" / TASK_ID / "generator.py"
    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise AssertionError((generator_sha, EXPECTED_GENERATOR_SHA256))
    module = load_module(generator_path)

    canonical_path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_row = next(
        json.loads(line)
        for line in canonical_path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    canonical_pairs = canonical_row["train"] + canonical_row.get("test", [])
    canonical_checks = []
    for index, pair in enumerate(canonical_pairs):
        intended = module.rule_mirror(pair["input"])
        rival = singleton_minimum_color_rival(pair["input"])
        canonical_checks.append(
            {
                "pair_index": index,
                "validator_errors": module.self_check(pair["input"]),
                "output_shape": [len(intended), len(intended[0])],
                "rival_fits": rival == pair["output"],
                "python_oracle_matches": intended == pair["output"],
            }
        )
    if not all(item["rival_fits"] and item["python_oracle_matches"] for item in canonical_checks):
        raise AssertionError("rival does not fit every canonical pair")

    grids = [
        module.generate(SEED, START_SAMPLE_INDEX + offset, difficulty=DIFFICULTY)
        for offset in range(DEMO_COUNT + 1)
    ]
    pairs = [{"input": grid, "output": module.rule_mirror(grid)} for grid in grids]
    rival_outputs = [singleton_minimum_color_rival(grid) for grid in grids]
    profiles = [module._analysis(grid)["scene_profile"] for grid in grids]
    selected_sizes = [module._analysis(grid)["facts"]["selected"]["size"] for grid in grids]
    validator_errors = [module.self_check(grid) for grid in grids]
    demo_fits = [rival_outputs[index] == pairs[index]["output"] for index in range(DEMO_COUNT)]
    query_differs = rival_outputs[-1] != pairs[-1]["output"]
    if not all(not errors for errors in validator_errors):
        raise AssertionError(validator_errors)
    if not all(demo_fits) or not query_differs:
        raise AssertionError((demo_fits, query_differs))

    out_dir = Path(__file__).resolve().parent
    (out_dir / "input.json").write_text(json.dumps(pairs[-1]["input"], indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(rival_outputs[-1], indent=2) + "\n")
    (out_dir / "python_oracle.json").write_text(json.dumps(pairs[-1]["output"], indent=2) + "\n")
    report = {
        "task_id": TASK_ID,
        "finding": "generated 3-demo lesson ambiguity for singleton minimum-color shortcut",
        "classification": "reproduced teachability defect",
        "generator_sha256": generator_sha,
        "rule_hash": module.RULE_HASH,
        "generator_version": module.VERSION,
        "rival": {
            "name": "first_minimum_frequency_cell_only",
            "description": "Count each nonzero color globally, scan row-major for the first cell of a minimum-frequency color, and output that one cell; ignore components and bbox crops.",
        },
        "canonical": {
            "pair_count": len(canonical_pairs),
            "all_fit_rival": all(item["rival_fits"] for item in canonical_checks),
            "checks": canonical_checks,
        },
        "generated_window": {
            "seed": SEED,
            "sample_indices": list(range(START_SAMPLE_INDEX, START_SAMPLE_INDEX + DEMO_COUNT + 1)),
            "difficulty": DIFFICULTY,
            "demo_count": DEMO_COUNT,
            "profiles": profiles,
            "selected_object_sizes": selected_sizes,
            "validator_errors": validator_errors,
            "rival_fits_each_demo": demo_fits,
            "rival_changes_query": query_differs,
            "pairs": pairs,
            "rival_outputs": rival_outputs,
        },
        "racket_apply": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                "--input", f"../checks/audit/{TASK_ID}/input.json",
                "--out", f"../checks/audit/{TASK_ID}/racket.json",
            ],
            "status": "run separately; see racket.json",
        },
    }
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": TASK_ID,
        "canonical_pairs": len(canonical_pairs),
        "profiles": profiles,
        "selected_sizes": selected_sizes,
        "demo_fits": demo_fits,
        "query_differs": query_differs,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
