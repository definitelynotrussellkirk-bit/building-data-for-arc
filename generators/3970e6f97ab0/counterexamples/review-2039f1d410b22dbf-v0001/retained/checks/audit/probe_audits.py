#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKET_ROOT / "repo"
OUT_ROOT = PACKET_ROOT / "checks/audit"
EXPECTED = {
    "28268c57c367": "c212d8d564eed0fc9519fb7061152be0e00eb64be1450aceb2644587045c5f63",
    "3970e6f97ab0": "4feb28045863ff797e58b583f967b16c58f2f6f6f31c9128df1b930a19bd291f",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO_ROOT / "generators" / task_id / "generator.py"
    digest = sha(path)
    assert digest == EXPECTED[task_id], (task_id, digest)
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}_{digest[:8]}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, digest


def canonical(task_id: str) -> dict:
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise AssertionError(task_id)


def grid_sha(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def wall_column(grid) -> int:
    h, w = len(grid), len(grid[0])
    walls = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    assert len(walls) == 1, walls
    return walls[0]


def extend_every_nonzero(grid):
    out = [row[:] for row in grid]
    wall = wall_column(grid)
    for r in range(len(grid)):
        for c in range(wall):
            value = grid[r][c]
            if value == 0:
                continue
            for cc in range(c + 1, wall):
                if out[r][cc] == 0:
                    out[r][cc] = value
    return out


def occupancy_or(grid):
    return [[1 if grid[r][c] != 0 or grid[r][c + 7] != 0 else 0
             for c in range(6)] for r in range(len(grid))]


def left_only(grid):
    return [[1 if grid[r][c] != 0 else 0 for c in range(6)]
            for r in range(len(grid))]


def diff_cells(a, b):
    return [[r, c, a[r][c], b[r][c]]
            for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]


def audit_282():
    gen, path, digest = load_generator("28268c57c367")
    row = canonical("28268c57c367")
    racket = json.loads((OUT_ROOT / "28268c57c367/racket.json").read_text())
    query_input = racket["results"][0]["input"]
    actual = racket["results"][0]["output"]
    rival = extend_every_nonzero(query_input)
    assert query_input == row["test"][0]["input"]
    assert actual == row["test"][0]["output"]
    assert rival != actual

    per_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        inputs = set()
        off_wall_fives = 0
        rejected = 0
        for i in range(100):
            grid = gen.generate(282000 + band_index * 10000 + i, i, difficulty=band)
            inputs.add(grid_sha(grid))
            if gen.self_check(grid):
                rejected += 1
            wall = wall_column(grid)
            off_wall_fives += sum(
                grid[r][c] == 5
                for r in range(len(grid))
                for c in range(len(grid[0]))
                if c != wall
            )
        per_band[band] = {
            "draws": 100,
            "unique_inputs": len(inputs),
            "self_check_rejections": rejected,
            "off_wall_color5_cells": off_wall_fives,
        }

    result = {
        "task_id": "28268c57c367",
        "generator_path": str(path.relative_to(PACKET_ROOT)),
        "generator_sha256": digest,
        "executed_rule_hash": racket["executed_rule_hash"],
        "rival": "extend every nonzero cell left of the full-height 5 wall, including isolated 5 cells",
        "canonical_train_fit": sum(
            extend_every_nonzero(pair["input"]) == pair["output"]
            for pair in row["train"]
        ),
        "canonical_train_total": len(row["train"]),
        "counterexample": {
            "source": "canonical held-out input; also accepted by target self_check",
            "input_sha256": racket["results"][0]["input_sha256"],
            "actual_output_sha256": racket["results"][0]["output_sha256"],
            "rival_output_sha256": grid_sha(rival),
            "self_check_errors": gen.self_check(query_input),
            "different_cells_actual_then_rival": diff_cells(actual, rival),
            "input": query_input,
            "actual_racket_output": actual,
            "rival_output": rival,
        },
        "generated_census": {
            "sampler": "100 draws/band; seed=282000+band_index*10000+i; sample_index=i",
            "per_band": per_band,
        },
        "conclusion": (
            "The validator admits isolated off-wall 5 cells, but the generator never emits them "
            "because source colors exclude 5. The canonical training demonstrations do not expose "
            "that 5 is structural and must not cast a ray."
        ),
    }
    (OUT_ROOT / "28268c57c367/analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def audit_397():
    gen, path, digest = load_generator("3970e6f97ab0")
    episode = json.loads((OUT_ROOT / "3970e6f97ab0/episode.jsonl").read_text().splitlines()[0])
    train_matches = [left_only(pair["input"]) == pair["output"] for pair in episode["train"]]
    query = episode["test"][0]
    rival_query = left_only(query["input"])
    assert all(train_matches)
    assert rival_query != query["output"]
    assert query["output"] == occupancy_or(query["input"])

    per_band = {}
    first = None
    for band_index, band in enumerate(("easy", "medium", "hard")):
        ambiguous = 0
        surviving_and_query_differs = 0
        unique_inputs = set()
        rejected = 0
        for lesson_index in range(100):
            seed = 397000 + band_index * 10000 + lesson_index
            grids = [gen.generate(seed, j, difficulty=band) for j in range(4)]
            for grid in grids:
                unique_inputs.add(grid_sha(grid))
                if gen.self_check(grid):
                    rejected += 1
            outputs = [occupancy_or(grid) for grid in grids]
            survives = all(left_only(grids[j]) == outputs[j] for j in range(3))
            if survives:
                ambiguous += 1
                if left_only(grids[3]) != outputs[3]:
                    surviving_and_query_differs += 1
                    if first is None:
                        first = {
                            "band": band,
                            "seed": seed,
                            "sample_indices": [0, 1, 2, 3],
                        }
        per_band[band] = {
            "lessons": 100,
            "pairs": 400,
            "unique_inputs": len(unique_inputs),
            "self_check_rejections": rejected,
            "left_only_fits_all_three_demos": ambiguous,
            "left_only_fits_demos_but_differs_on_query": surviving_and_query_differs,
        }

    result = {
        "task_id": "3970e6f97ab0",
        "generator_path": str(path.relative_to(PACKET_ROOT)),
        "generator_sha256": digest,
        "executed_rule_hash": episode["executed_rule_hash"],
        "rival": "ignore the right panel and output the left panel's nonzero occupancy mask",
        "concrete_generated_lesson": {
            "command_seed": episode["seed"],
            "difficulty": episode["provenance"]["difficulty"],
            "sample_indices": episode["sample_indices"],
            "train_matches": train_matches,
            "query_matches": rival_query == query["output"],
            "query_difference_actual_then_rival": diff_cells(query["output"], rival_query),
            "query_input_sha256": grid_sha(query["input"]),
            "query_actual_output_sha256": grid_sha(query["output"]),
            "query_rival_output_sha256": grid_sha(rival_query),
            "all_self_check_errors": [gen.self_check(pair["input"])
                                      for pair in episode["train"] + episode["test"]],
            "rival_query_output": rival_query,
        },
        "generated_census": {
            "sampler": (
                "100 deterministic 3-demo+1-query blocks/band; "
                "seed=397000+band_index*10000+lesson_index; sample_index=0..3"
            ),
            "per_band": per_band,
            "first_additional_counterexample": first,
        },
        "conclusion": (
            "The same panel_pattern is applied to both panels. For stripes, checker, border, "
            "and diagonal profiles the occupancy masks are identical, so many three-demo "
            "lessons are fully explained by copying only the left panel even when the query "
            "requires a contribution from the right panel."
        ),
    }
    (OUT_ROOT / "3970e6f97ab0/analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    a = audit_282()
    b = audit_397()
    print(json.dumps({
        "28268c57c367": {
            "train_fit": a["canonical_train_fit"],
            "difference_cells": len(a["counterexample"]["different_cells_actual_then_rival"]),
        },
        "3970e6f97ab0": {
            "train_matches": b["concrete_generated_lesson"]["train_matches"],
            "query_difference_cells": len(b["concrete_generated_lesson"]["query_difference_actual_then_rival"]),
            "census": b["generated_census"]["per_band"],
        },
    }, indent=2))
