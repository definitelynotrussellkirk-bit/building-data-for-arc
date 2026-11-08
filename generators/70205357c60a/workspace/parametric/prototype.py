#!/usr/bin/env python3
"""Episode-level cardinal-neighbor threshold prototype for 70205357c60a.

This is task-local authoring evidence, not a production parametric-rule API.
The selected canonical generator and its fixed rule remain unchanged.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "70205357c60a"
ALLOWED_THRESHOLDS = (4, 3)
DEFAULT_THRESHOLD = 4
CANONICAL_PREDICATE = "(if (and (= 1 l) (= 1 ri) (= 1 u) (= 1 d)) 2 5)"
THREE_NEIGHBOR_PREDICATE = "(if (>= (+ l ri u d) 3) 2 5)"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

_FIXTURE_SPECS = (
    {"difficulty": "easy", "scene_profile": "solid_rectangles", "grid_h": 14, "grid_w": 16, "n_components": 3},
    {"difficulty": "medium", "scene_profile": "single_notches", "grid_h": 15, "grid_w": 17, "n_components": 3},
    {"difficulty": "hard", "scene_profile": "deep_notches", "grid_h": 16, "grid_w": 18, "n_components": 3},
    {"difficulty": "medium", "scene_profile": "solid_rectangles", "grid_h": 13, "grid_w": 15, "n_components": 2},
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_sha256(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(program: str) -> str:
    return sha256_bytes(" ".join(program.split()).encode())[:12]


def canonical_program(root: str | Path) -> str:
    programs: set[str] = set()
    rows = 0
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            rows += 1
            program = row.get("program_solution")
            if not isinstance(program, str) or not program:
                raise ValueError("canonical row has no Racket program")
            programs.add(program)
    if rows == 0:
        raise ValueError(f"no canonical row for {TASK_ID}")
    if len(programs) != 1:
        raise ValueError(f"canonical variants disagree for {TASK_ID}")
    return programs.pop()


def _validate_threshold(threshold: int) -> None:
    if type(threshold) is not int:
        raise TypeError("min_cardinal_neighbors must be an exact integer")
    if threshold not in ALLOWED_THRESHOLDS:
        raise ValueError(f"min_cardinal_neighbors must be one of {ALLOWED_THRESHOLDS}")


def render_program(canonical: str, threshold: int = DEFAULT_THRESHOLD) -> str:
    """Instantiate exact Racket text for one fixed episode-level setting."""
    _validate_threshold(threshold)
    if not canonical.startswith("(rule!") or not canonical.endswith(")"):
        raise ValueError("canonical program is not wrapped with rule!")
    if canonical.count(CANONICAL_PREDICATE) != 1:
        raise ValueError("canonical cardinal-neighbor predicate did not match pinned rule")
    if threshold == DEFAULT_THRESHOLD:
        return canonical
    return canonical.replace(CANONICAL_PREDICATE, THREE_NEIGHBOR_PREDICATE, 1)


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute exact instantiated Racket bytes with the input bound to ``g``."""
    if not program.startswith("(rule!") or not program.endswith(")"):
        raise ValueError("expected rule! wrapper")
    bridge.define_grid("g", grid)
    body = program[len("(rule!") : -1].strip()
    output = bridge.eval_text(f"({body} g)")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def select_threshold(seed: int) -> int:
    """Choose one hidden rule setting deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return ALLOWED_THRESHOLDS[seed % len(ALLOWED_THRESHOLDS)]


def neighbor_count_histogram(grid: list[list[int]]) -> dict[int, int]:
    """Count color-5 cells by their number of cardinal color-5 neighbours."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    histogram: dict[int, int] = {}
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            count = sum(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == 5
                for dr, dc in DIR4
            )
            histogram[count] = histogram.get(count, 0) + 1
    return histogram


def _fixture_records(seed: int, *, root: str | Path) -> list[dict[str, Any]]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    generator, _source, _digest = load_selected_generator(TASK_ID, root=root)
    records: list[dict[str, Any]] = []
    for index, spec in enumerate(_FIXTURE_SPECS):
        accepted = None
        for attempt in range(64):
            draw_seed = seed * 1009 + index * 97 + attempt
            sample_index = seed * 1013 + index
            controls = {name: value for name, value in spec.items() if name != "difficulty"}
            grid = generator.generate(
                draw_seed,
                sample_index,
                difficulty=spec["difficulty"],
                **controls,
            )
            findings = generator.self_check(
                grid,
                difficulty=spec["difficulty"],
                meta={"overrides": controls},
            )
            histogram = neighbor_count_histogram(grid)
            if not findings and histogram.get(3, 0) and histogram.get(4, 0):
                accepted = {
                    "grid": grid,
                    "draw_seed": draw_seed,
                    "sample_index": sample_index,
                    "controls": dict(spec),
                    "neighbor_count_histogram": {str(k): v for k, v in sorted(histogram.items())},
                }
                break
        if accepted is None:
            raise ValueError(f"could not materialize distinguishing fixture {index}")
        records.append(accepted)
    return records


def fixture_inputs(seed: int, *, root: str | Path | None = None) -> list[list[list[int]]]:
    resolved = Path(root) if root is not None else find_root(__file__)
    return [record["grid"] for record in _fixture_records(seed, root=resolved)]


def _build_episode(
    seed: int,
    threshold: int,
    canonical: str,
    bridge: RacketBridge,
    *,
    root: str | Path,
) -> dict[str, Any]:
    programs = {value: render_program(canonical, value) for value in ALLOWED_THRESHOLDS}
    rival_threshold = next(value for value in ALLOWED_THRESHOLDS if value != threshold)
    generator, _source, generator_digest = load_selected_generator(TASK_ID, root=root)
    records = _fixture_records(seed, root=root)

    pairs: list[dict[str, Any]] = []
    rival_outputs: list[list[list[int]]] = []
    difference_counts: list[int] = []
    for record in records:
        grid = record["grid"]
        chosen = execute(bridge, programs[threshold], grid)
        rival = execute(bridge, programs[rival_threshold], grid)
        pairs.append({"input": grid, "output": chosen})
        rival_outputs.append(rival)
        difference_counts.append(
            sum(
                chosen[row][col] != rival[row][col]
                for row in range(len(grid))
                for col in range(len(grid[0]))
            )
        )

    demo_differences = [index for index, count in enumerate(difference_counts[:3]) if count > 0]
    query_differs = difference_counts[3] > 0
    if demo_differences != [0, 1, 2] or not query_differs:
        raise ValueError("controlled episode failed to distinguish threshold settings")

    return {
        "schema": "70205357c60a-parametric-neighbor-threshold-episode-v1",
        "status": "proposed_prototype",
        "seed": seed,
        "parameters": {"min_cardinal_neighbors": threshold},
        "setting_selected_once": True,
        "program": programs[threshold],
        "program_sha256": sha256_bytes(programs[threshold].encode()),
        "program_normalized_hash": normalized_rule_hash(programs[threshold]),
        "generator_sha256": generator_digest,
        "train": pairs[:3],
        "test": pairs[3:],
        "input_controls": [
            {name: value for name, value in record.items() if name != "grid"}
            for record in records
        ],
        "selected_generator_self_check": all(generator.self_check(record["grid"]) == [] for record in records),
        "rival": {
            "min_cardinal_neighbors": rival_threshold,
            "status": "distinguished",
            "program_sha256": sha256_bytes(programs[rival_threshold].encode()),
            "program_normalized_hash": normalized_rule_hash(programs[rival_threshold]),
            "demo_differences": demo_differences,
            "query_differs": query_differs,
            "differing_cell_counts": {"train": difference_counts[:3], "test": difference_counts[3:]},
            "outputs": {"train": rival_outputs[:3], "test": rival_outputs[3:]},
        },
        "label_authority": "included protected Racket bridge executing the exact instantiated program text",
    }


def generate_episode(
    seed: int,
    *,
    min_cardinal_neighbors: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    threshold = select_threshold(seed) if min_cardinal_neighbors is None else min_cardinal_neighbors
    _validate_threshold(threshold)
    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, threshold, canonical, bridge, root=root)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, threshold, canonical, owned_bridge, root=root)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(output: str | Path, *, seed: int = 7020) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is not accepted)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    test_path = Path(__file__).parents[2] / "tests" / "test_parametric_neighbor_threshold.py"
    source_paths = [Path(__file__), test_path, Path(__file__).with_name("README.md")]
    source_hashes = {
        str(path.relative_to(root)): sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    canonical = canonical_program(root)
    programs = {value: render_program(canonical, value) for value in ALLOWED_THRESHOLDS}
    _generator, _source, generator_digest = load_selected_generator(TASK_ID, root=root)

    with RacketBridge() as bridge:
        episodes = [generate_episode(seed + offset, bridge=bridge) for offset in range(2)]
        observed = {episode["parameters"]["min_cardinal_neighbors"] for episode in episodes}
        if observed != set(ALLOWED_THRESHOLDS):
            raise ValueError(f"retained seeds did not cover both thresholds: {observed}")

        witness_input = fixture_inputs(seed, root=root)[0]
        witness_outputs = {
            value: execute(bridge, program, witness_input)
            for value, program in programs.items()
        }
        canonical_checks = []
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root)):
            actual = execute(bridge, canonical, pair["input"])
            canonical_checks.append(
                {
                    "pair_index": index,
                    "input_sha256": json_sha256(pair["input"]),
                    "expected_output_sha256": json_sha256(pair["output"]),
                    "actual_output_sha256": json_sha256(actual),
                    "matches": actual == pair["output"],
                }
            )
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        episode["prototype_source_sha256"] = source_hashes
        _write_json(output / "public" / f"episode-{index}.json", public_challenge(episode))
        _write_json(output / "private" / f"episode-{index}.json", episode)
    for value, program in programs.items():
        path = output / "private" / f"program-threshold-{value}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")

    differing_cells = [
        {
            "row": row,
            "col": col,
            "threshold_4": witness_outputs[4][row][col],
            "threshold_3": witness_outputs[3][row][col],
        }
        for row in range(len(witness_input))
        for col in range(len(witness_input[0]))
        if witness_outputs[4][row][col] != witness_outputs[3][row][col]
    ]
    _write_json(
        output / "private" / "setting-difference-witness.json",
        {
            "input": witness_input,
            "neighbor_count_histogram": neighbor_count_histogram(witness_input),
            "outputs": {str(value): output_grid for value, output_grid in witness_outputs.items()},
            "different": bool(differing_cells),
            "differing_cell_count": len(differing_cells),
            "differing_cells": differing_cells,
        },
    )
    _write_json(
        output / "private" / "canonical-default-check.json",
        {
            "canonical_program_sha256": sha256_bytes(canonical.encode()),
            "canonical_normalized_rule_hash": normalized_rule_hash(canonical),
            "generator_sha256": generator_digest,
            "all_match": all(row["matches"] for row in canonical_checks),
            "pairs": canonical_checks,
        },
    )

    episode_parameters = {
        str(episode["parameters"]["min_cardinal_neighbors"]): {
            "episode_index": index,
            "seed": episode["seed"],
            "program_sha256": episode["program_sha256"],
            "program_normalized_hash": episode["program_normalized_hash"],
        }
        for index, episode in enumerate(episodes)
    }
    report = {
        "schema": "70205357c60a-parametric-neighbor-threshold-report-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "min_cardinal_neighbors",
            "allowed_values": list(ALLOWED_THRESHOLDS),
            "default": DEFAULT_THRESHOLD,
            "meaning": "recolor a 5 to 2 when at least this many cardinal neighbours are 5",
        },
        "episode_parameters": episode_parameters,
        "setting_selection": "ALLOWED_THRESHOLDS[seed mod 2], once per episode",
        "reasoning_invariants": [
            "inspect each color-5 cell independently",
            "count only in-bounds up/down/left/right color-5 neighbours",
            "recolor qualifying cells to 2 and preserve all other cells",
        ],
        "input_constraints": [
            "selected generator's lawful 0/5 separated-component grammar",
            "every controlled pair contains both exact-3 and exact-4 cardinal-neighbour witnesses",
        ],
        "default_program_exact_canonical": programs[4] == canonical,
        "canonical_program_sha256": sha256_bytes(canonical.encode()),
        "canonical_normalized_rule_hash": normalized_rule_hash(canonical),
        "program_hashes": {
            str(value): {"sha256": sha256_bytes(program.encode()), "normalized": normalized_rule_hash(program)}
            for value, program in programs.items()
        },
        "generator_sha256": generator_digest,
        "canonical_pairs_checked": len(canonical_checks),
        "canonical_pairs_all_match": all(row["matches"] for row in canonical_checks),
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2] for episode in episodes
        ),
        "all_queries_distinguish_other_declared_setting": all(
            episode["rival"]["query_differs"] for episode in episodes
        ),
        "witness_differing_cell_count": len(differing_cells),
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only thresholds 4 (canonical) and 3 (proposed) are instantiated.",
            "Threshold 3 changes boundary behavior but preserves the original local-neighborhood reasoning structure and palette.",
            "Evidence covers two retained seeds and four controlled inputs per episode.",
            "Inputs without exact-3 witnesses cannot distinguish these two settings.",
            "Only the declared opposite threshold is checked as a rival; finite evidence does not prove unique induction against all rules.",
            "This task-local prototype has no production API, approval, or training-admission claim.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7020)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.out, seed=args.seed)
    print(json.dumps({
        "status": report["status"],
        "task_id": report["task_id"],
        "complete_episodes": report["complete_episodes"],
        "episode_parameters": report["episode_parameters"],
        "out": str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
