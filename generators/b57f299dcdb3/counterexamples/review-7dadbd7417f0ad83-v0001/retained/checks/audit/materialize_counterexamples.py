from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
OUT_ROOT = Path(__file__).resolve().parent


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def aea_no_carry(gen, grid):
    _seps, _height, sections = gen._split_sections(grid)
    s_pprev, s_prev, s_last = sections[-3:]
    d_prev = gen._diff(s_pprev, s_prev)
    d_last = gen._diff(s_prev, s_last)
    shift = (
        min(diff[1] for diff in d_last) - min(diff[1] for diff in d_prev)
        if d_prev and d_last
        else 0
    )
    output = [row[:] for row in s_last]
    for row, col, old, new in d_last:
        target = col + shift
        if 0 <= target < len(output[0]) and output[row][target] == old:
            output[row][target] = new
    return output


def materialize_b57() -> None:
    task_id = "b57f299dcdb3"
    gen, _path, source_sha256 = load_selected_generator(task_id, root=ROOT)
    seed = 1_000_004
    sample_index = 4
    difficulty = "easy"
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    analysis = gen._analyze(grid)
    background = analysis["background"]
    centers = gen._plus_centers(grid, background)
    eligible = [
        color
        for color in {value for row in grid for value in row}
        if color not in (0, 4, background)
    ]
    counts = Counter(
        value for row in grid for value in row if value in eligible
    )
    prediction = max(counts, key=counts.get)
    rival_output = [[prediction]]
    intended_output = gen.solve_python(grid)
    payload = {
        "schema": "arcpuzzles-audit-counterexample-input-v1",
        "task_id": task_id,
        "generator_sha256": source_sha256,
        "recipe": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
        },
        "generator_domain_errors": gen.self_check(grid, difficulty=difficulty),
        "observed": {
            "scene_profile": analysis["scene_profile"],
            "background": background,
            "plus_center_colors": [color for _r, _c, color in centers],
            "eligible_global_counts": dict(sorted(counts.items())),
        },
        "rival": {
            "name": "global_most_frequent_eligible_role",
            "description": (
                "Return the globally most frequent eligible non-background, "
                "non-yellow role color without locating yellow-centered pluses."
            ),
            "output": rival_output,
        },
        "python_mirror_output": intended_output,
        "input": grid,
    }
    directory = OUT_ROOT / f"{task_id}-counterexample"
    write_json(directory / "input.json", grid)
    write_json(directory / "rival.json", payload)


def materialize_aea() -> None:
    task_id = "aea4d55345a1"
    gen, _path, source_sha256 = load_selected_generator(task_id, root=ROOT)
    seed = 2_000_004
    sample_index = 4
    difficulty = "easy"
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    analysis = gen._analyze(grid)
    rival_output = aea_no_carry(gen, grid)
    intended_output = gen.solve_python(grid)
    payload = {
        "schema": "arcpuzzles-audit-counterexample-input-v1",
        "task_id": task_id,
        "generator_sha256": source_sha256,
        "recipe": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
        },
        "generator_domain_errors": gen.self_check(grid, difficulty=difficulty),
        "observed": {
            "scene_profile": analysis["scene_profile"],
            "section_height": analysis["section_height"],
            "width": analysis["width"],
            "col_shift": analysis["col_shift"],
            "carry_row_count": analysis["carry_row_count"],
        },
        "rival": {
            "name": "repeat_latest_diff_without_carry",
            "description": (
                "Shift only the most recent section diff and ignore prior-row "
                "diffs that the intended rule carries forward."
            ),
            "output": rival_output,
        },
        "python_mirror_output": intended_output,
        "input": grid,
    }
    directory = OUT_ROOT / f"{task_id}-counterexample"
    write_json(directory / "input.json", grid)
    write_json(directory / "rival.json", payload)


def main() -> None:
    materialize_b57()
    materialize_aea()
    print("materialized audit counterexamples")


if __name__ == "__main__":
    main()
