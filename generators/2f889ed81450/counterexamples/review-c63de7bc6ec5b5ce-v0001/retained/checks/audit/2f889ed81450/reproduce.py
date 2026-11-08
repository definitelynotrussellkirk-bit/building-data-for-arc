from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "2f889ed81450"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "audit" / TASK_ID / "reproduction.json"
DIRECTIONS = ((-2, 0), (2, 0), (0, -2), (0, 2))


def canonical_record() -> dict[str, Any]:
    found = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            found.append(row)
    assert len(found) == 1
    return found[0]


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return grid


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def eval_rule(bridge: RacketBridge, program: str, grid: list[list[int]]):
    # These canonical authorities are already bare-bridge-safe body forms.
    # Bind the standard g/h/w convention without importing repository-only
    # source-normalization helpers into the portable audit runtime.
    body = strip_rule_wrapper(program)
    callable_text = (
        "(lambda (g) (let* ((h (rows g)) (w (cols g))) "
        + body
        + "))"
    )
    return bridge.eval_text(f"({callable_text} {grid_literal(grid)})")


def seeds(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def interior_only_rival(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r, c, value in seeds(grid):
        destinations = [(r + dr, c + dc) for dr, dc in DIRECTIONS]
        if all(0 <= rr < h and 0 <= cc < w for rr, cc in destinations):
            for rr, cc in destinations:
                out[rr][cc] = value
    return out


def min_margin(grid: list[list[int]]) -> int | None:
    values = seeds(grid)
    if not values:
        return None
    h, w = len(grid), len(grid[0])
    return min(min(r, c, h - 1 - r, w - 1 - c) for r, c, _ in values)


def min_pair_distance(grid: list[list[int]]) -> int | None:
    values = seeds(grid)
    if len(values) < 2:
        return None
    return min(
        abs(r1 - r2) + abs(c1 - c2)
        for i, (r1, c1, _) in enumerate(values)
        for r2, c2, _ in values[i + 1 :]
    )


generator, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
record = canonical_record()
program = record["program_solution"]

too_close = generator.generate(
    17, 0, difficulty="medium", texture="seeds_too_close"
)
too_close_check = generator.self_check(too_close)

axis_grid = generator.generate(
    20261019,
    0,
    difficulty="medium",
    n_seeds=1,
    n_distinct_colors=1,
    palette_size=1,
)
axis_seed_values = seeds(axis_grid)

ordinary_records = []
with RacketBridge(max_calls_before_restart=128) as bridge:
    too_close_output = eval_rule(bridge, program, too_close)
    for sample_index in range(60):
        grid = generator.generate(20261019, sample_index, difficulty="medium")
        authority = eval_rule(bridge, program, grid)
        rival = interior_only_rival(grid)
        ordinary_records.append(
            {
                "sample_index": sample_index,
                "seed_count": len(seeds(grid)),
                "min_border_margin": min_margin(grid),
                "self_check": generator.self_check(grid),
                "rival_matches_authority": rival == authority,
                "input_sha256": hashlib.sha256(json.dumps(grid).encode()).hexdigest(),
            }
        )

    canonical_pair = record["train"][0]
    canonical_input = normalize_grid(canonical_pair["input"])
    canonical_expected = normalize_grid(canonical_pair["output"])
    canonical_actual = eval_rule(bridge, program, canonical_input)

canonical_rival = interior_only_rival(canonical_input)
result = {
    "schema": "audit-reproduction-v1",
    "task_id": TASK_ID,
    "source": {
        "path": str(Path(source_path).relative_to(ROOT)),
        "sha256": source_sha,
    },
    "authority": {
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    },
    "self_check_accepts_too_close_seeds": {
        "grid": too_close,
        "self_check": too_close_check,
        "accepted": too_close_check == [],
        "min_pair_manhattan_distance": min_pair_distance(too_close),
        "authority_output": too_close_output,
    },
    "declared_axis_override_is_ignored": {
        "call": {
            "seed": 20261019,
            "sample_index": 0,
            "difficulty": "medium",
            "n_seeds": 1,
            "n_distinct_colors": 1,
            "palette_size": 1,
        },
        "grid": axis_grid,
        "self_check": generator.self_check(axis_grid),
        "observed_seed_count": len(axis_seed_values),
        "observed_nonzero_colors": sorted({value for _, _, value in axis_seed_values}),
    },
    "interior_only_rival_census": {
        "seed": 20261019,
        "difficulty": "medium",
        "draws": len(ordinary_records),
        "all_self_check_clean": all(not row["self_check"] for row in ordinary_records),
        "all_min_border_margin_at_least_two": all(
            row["min_border_margin"] is not None and row["min_border_margin"] >= 2
            for row in ordinary_records
        ),
        "rival_matches": sum(row["rival_matches_authority"] for row in ordinary_records),
        "records": ordinary_records,
    },
    "canonical_boundary_witness": {
        "train_pair_index": 0,
        "input": canonical_input,
        "self_check": generator.self_check(canonical_input),
        "min_border_margin": min_margin(canonical_input),
        "expected": canonical_expected,
        "authority_actual": canonical_actual,
        "authority_matches_expected": canonical_actual == canonical_expected,
        "interior_only_rival": canonical_rival,
        "rival_disagrees": canonical_rival != canonical_actual,
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "source_sha256": source_sha,
    "too_close_self_check": too_close_check,
    "too_close_distance": min_pair_distance(too_close),
    "axis_observed_seed_count": len(axis_seed_values),
    "axis_observed_colors": sorted({value for _, _, value in axis_seed_values}),
    "ordinary_rival_matches": sum(row["rival_matches_authority"] for row in ordinary_records),
    "ordinary_draws": len(ordinary_records),
    "canonical_rival_disagrees": canonical_rival != canonical_actual,
    "out": str(OUT),
}, indent=2, sort_keys=True))
