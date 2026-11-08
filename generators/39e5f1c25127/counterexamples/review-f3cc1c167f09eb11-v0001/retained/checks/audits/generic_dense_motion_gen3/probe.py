from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "repo/generators/generic_dense_motion_gen3/generator.py"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("audit_dense_motion_gen3", GENERATOR)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def wall_column(grid, wall_color):
    return next(
        c for c in range(len(grid[0]))
        if all(row[c] == wall_color for row in grid)
    )


def rowwise_rival(grid, wall_color, bg_color):
    """Wrong but plausible: shift each occupied row independently to the wall."""
    h, w = len(grid), len(grid[0])
    wall = wall_column(grid, wall_color)
    out = [[bg_color] * w for _ in range(h)]
    for r in range(h):
        out[r][wall] = wall_color
    for r, row in enumerate(grid):
        left = [(c, value) for c, value in enumerate(row[:wall]) if value != bg_color]
        right = [
            (c, value)
            for c, value in enumerate(row[wall + 1 :], start=wall + 1)
            if value != bg_color
        ]
        if left:
            shift = wall - 1 - max(c for c, _ in left)
            for c, value in left:
                out[r][c + shift] = value
        if right:
            shift = wall + 1 - min(c for c, _ in right)
            for c, value in right:
                out[r][c + shift] = value
    return out


def main():
    task_count = 1000
    pair_count = 0
    matching_pairs = 0
    ambiguous_lessons = []
    self_check_failures = []
    first_case = None

    for offset in range(task_count):
        seed = 100000 + offset
        difficulty = ("easy", "medium", "hard")[offset % 3]
        task = mod.generate_task(seed, difficulty=difficulty)
        errors = mod.self_check_task(task)
        if errors:
            self_check_failures.append({"seed": seed, "difficulty": difficulty, "errors": errors})
        wall_color = task["meta"]["wall_color"]
        bg_color = task["meta"]["bg_color"]
        pairs = task["train"] + task["test"]
        matches = [
            rowwise_rival(pair["input"], wall_color, bg_color) == pair["output"]
            for pair in pairs
        ]
        pair_count += len(matches)
        matching_pairs += sum(matches)
        n_train = len(task["train"])
        if all(matches[:n_train]) and not all(matches[n_train:]):
            record = {
                "seed": seed,
                "difficulty": difficulty,
                "n_train": n_train,
                "n_test": len(task["test"]),
                "pair_matches": matches,
            }
            ambiguous_lessons.append(record)
            if first_case is None:
                first_case = (task, record)

    assert first_case is not None
    task, record = first_case
    query_index = next(
        i for i, matched in enumerate(record["pair_matches"][record["n_train"] :])
        if not matched
    )
    query = task["test"][query_index]
    rival = rowwise_rival(
        query["input"], task["meta"]["wall_color"], task["meta"]["bg_color"]
    )
    mismatch_cells = [
        [r, c, query["output"][r][c], rival[r][c]]
        for r in range(len(rival))
        for c in range(len(rival[0]))
        if query["output"][r][c] != rival[r][c]
    ]

    summary = {
        "generator_sha256": __import__("hashlib").sha256(GENERATOR.read_bytes()).hexdigest(),
        "sampling": {
            "tasks": task_count,
            "seed_formula": "100000 + i",
            "difficulty": "cycles easy, medium, hard",
            "pairs": pair_count,
        },
        "self_check_failures": len(self_check_failures),
        "rowwise_rival": {
            "matching_pairs": matching_pairs,
            "pair_fraction": matching_pairs / pair_count,
            "lessons_where_all_train_fit_but_a_test_differs": len(ambiguous_lessons),
            "first_counterexample": record,
            "first_query_index": query_index,
            "mismatch_cell_count": len(mismatch_cells),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUT / "counterexample_task.json").write_text(json.dumps(task, indent=2) + "\n")
    (OUT / "counterexample_rival_query.json").write_text(json.dumps(rival) + "\n")
    (OUT / "counterexample_mismatches.json").write_text(json.dumps(mismatch_cells, indent=2) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
