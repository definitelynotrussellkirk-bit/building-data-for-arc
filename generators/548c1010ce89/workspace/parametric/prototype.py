#!/usr/bin/env python3
"""Proposed episode-level paint-color parameter for ARC task 548c1010ce89.

Production remains pinned to the canonical red-2 rule.  This task-local
prototype selects paint color 2 or 6 once per episode, uses the repaired
three-demonstration lesson structure, exposes four distinct queries, and obtains
selected and rival predictions from exact Racket programs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "548c1010ce89"
ROOT = find_root(__file__)
PAINT_COLORS = (2, 6)
DEFAULT_PAINT_COLOR = 2
AXIS_MODES = ("both", "rows", "columns")
STATUS = "proposed prototype; not production-approved"
DEMO_PROFILES = ("rows_and_cols_sparse", "columns_only", "rows_only")
QUERY_PROFILES = (
    "single_empty_row",
    "single_empty_col",
    "boundary_empty_lines",
    "adjacent_empty_lines",
)
_CANONICAL_COND = "(cond ((row-empty? r) 2) ((col-empty? c) 2) (else v))"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_record(root: Path | str = ROOT) -> dict[str, Any]:
    records = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            records.append(row)
    if not records:
        raise ValueError(f"canonical task not found: {TASK_ID}")
    programs = {row["program_solution"] for row in records}
    if len(programs) != 1:
        raise ValueError("canonical task variants disagree on program_solution")
    return records[0]


def _validate_paint_color(paint_color: int) -> int:
    if type(paint_color) is not int or paint_color not in PAINT_COLORS:
        raise ValueError(f"paint_color must be one of {PAINT_COLORS}")
    return paint_color


def _validate_axis_mode(axis_mode: str) -> str:
    if type(axis_mode) is not str or axis_mode not in AXIS_MODES:
        raise ValueError(f"axis_mode must be one of {AXIS_MODES}")
    return axis_mode


def _episode_input_seed(seed: int) -> int:
    """Return the deterministic generator seed shared by one color pair."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python integer")
    return (seed // len(PAINT_COLORS)) ^ 0x548C1010


def program_for(
    paint_color: int = DEFAULT_PAINT_COLOR,
    axis_mode: str = "both",
    *,
    root: Path | str = ROOT,
) -> str:
    """Return the exact canonical program or a one-condition/literal variant."""
    paint_color = _validate_paint_color(paint_color)
    axis_mode = _validate_axis_mode(axis_mode)
    canonical = canonical_record(root)["program_solution"]
    if canonical.count(_CANONICAL_COND) != 1:
        raise ValueError("canonical empty-line condition changed; prototype needs review")
    if axis_mode == "both" and paint_color == DEFAULT_PAINT_COLOR:
        return canonical
    if axis_mode == "both":
        replacement = (
            f"(cond ((row-empty? r) {paint_color}) "
            f"((col-empty? c) {paint_color}) (else v))"
        )
    elif axis_mode == "rows":
        replacement = f"(cond ((row-empty? r) {paint_color}) (else v))"
    else:
        replacement = f"(cond ((col-empty? c) {paint_color}) (else v))"
    return canonical.replace(_CANONICAL_COND, replacement, 1)


def _callable_text(program: str) -> str:
    """Return the callable lambda inside the canonical ``rule!`` wrapper."""
    return strip_rule_wrapper(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def episode_inputs(seed: int, *, root: Path | str = ROOT) -> tuple[list[list[int]], ...]:
    """Return three demos plus four queries; paired color settings share inputs."""
    generator, _, _ = load_selected_generator(TASK_ID, root=Path(root))
    input_seed = _episode_input_seed(seed)
    profiles = DEMO_PROFILES + QUERY_PROFILES
    grids = tuple(
        generator.generate(
            input_seed,
            sample_index,
            difficulty="medium",
            scene_profile=profile,
        )
        for sample_index, profile in enumerate(profiles)
    )
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(set(serialized)) != len(grids):
        raise ValueError("episode inputs must be distinct")
    return grids


def _selected_color(seed: int, paint_color: int | None) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python integer")
    if paint_color is None:
        return PAINT_COLORS[seed % len(PAINT_COLORS)]
    return _validate_paint_color(paint_color)


def generate_episode(
    seed: int,
    bridge: RacketBridge,
    *,
    paint_color: int | None = None,
    root: Path | str = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one fixed-setting episode and evaluator-only Racket evidence."""
    root = Path(root)
    selected = _selected_color(seed, paint_color)
    other = next(color for color in PAINT_COLORS if color != selected)
    grids = episode_inputs(seed, root=root)
    selected_program = program_for(selected, "both", root=root)
    selected_outputs = [execute(bridge, selected_program, grid) for grid in grids]

    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(grids[: len(DEMO_PROFILES)], selected_outputs[: len(DEMO_PROFILES)])
        ],
        "test": [{"input": grid} for grid in grids[len(DEMO_PROFILES) :]],
    }

    rival_programs = {
        f"other_color_{other}": program_for(other, "both", root=root),
        "rows_only": program_for(selected, "rows", root=root),
        "columns_only": program_for(selected, "columns", root=root),
    }
    rivals: dict[str, Any] = {}
    surviving: list[str] = []
    other_color_query_differences: list[bool] | None = None
    for name, program in rival_programs.items():
        predictions = [execute(bridge, program, grid) for grid in grids]
        demo_mismatches = [
            index
            for index, (prediction, truth) in enumerate(
                zip(predictions[: len(DEMO_PROFILES)], selected_outputs[: len(DEMO_PROFILES)])
            )
            if prediction != truth
        ]
        query_mismatches = [
            index
            for index, (prediction, truth) in enumerate(
                zip(predictions[len(DEMO_PROFILES) :], selected_outputs[len(DEMO_PROFILES) :])
            )
            if prediction != truth
        ]
        rivals[name] = {
            "program": program,
            "program_sha256": sha256_bytes(program.encode()),
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "demonstration_predictions": predictions[: len(DEMO_PROFILES)],
            "query_predictions": predictions[len(DEMO_PROFILES) :],
        }
        if not demo_mismatches:
            surviving.append(name)
        if name.startswith("other_color_"):
            other_color_query_differences = [
                prediction != truth
                for prediction, truth in zip(
                    predictions[len(DEMO_PROFILES) :],
                    selected_outputs[len(DEMO_PROFILES) :],
                )
            ]

    if surviving:
        raise ValueError(f"declared rivals survive demonstrations: {surviving}")
    if other_color_query_differences is None or not all(other_color_query_differences):
        raise ValueError("every query must distinguish the declared paint colors")

    private = {
        "schema": "548c1010ce89-parametric-paint-color-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"paint_color": selected},
        "input_seed": _episode_input_seed(seed),
        "program": selected_program,
        "program_sha256": sha256_bytes(selected_program.encode()),
        "demo_profiles": list(DEMO_PROFILES),
        "query_profiles": list(QUERY_PROFILES),
        "query_answers": selected_outputs[len(DEMO_PROFILES) :],
        "rivals": rivals,
        "surviving_declared_rivals": surviving,
        "query_outputs_differ_from_other_color": other_color_query_differences,
        "input_sha256": [
            sha256_bytes(json.dumps(grid, separators=(",", ":")).encode()) for grid in grids
        ],
    }
    return public, private


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Materialize source-bound public/private episodes and exact Racket programs."""
    out = Path(out)
    root = Path(root)
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("seeds must contain at least one episode seed")
    if any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("seeds must be non-negative Python integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be unique")
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    (out / "rules").mkdir()

    all_programs = {
        f"paint-{color}-both": program_for(color, "both", root=root)
        for color in PAINT_COLORS
    }
    for color in PAINT_COLORS:
        all_programs[f"paint-{color}-rows"] = program_for(color, "rows", root=root)
        all_programs[f"paint-{color}-columns"] = program_for(color, "columns", root=root)
    for name, program in all_programs.items():
        (out / "rules" / f"{name}.rkt").write_text(program, encoding="utf-8")

    episode_rows = []
    public_ids: set[str] = set()
    private_episodes = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            public, private = generate_episode(seed, bridge, root=root)
            public_id = public_challenge_id(public)
            if public_id in public_ids:
                raise ValueError(f"duplicate visible payload: {public_id}")
            public_ids.add(public_id)
            public_path = Path("public") / f"challenge-{public_id}.json"
            private_path = Path("private") / f"episode-{seed:03d}.json"
            (out / public_path).write_bytes(public_challenge_bytes(public))
            private["public_id"] = public_id
            private["public_sha256"] = sha256_bytes((out / public_path).read_bytes())
            _write_json(out / private_path, private)
            private_episodes.append(private)
            episode_rows.append(
                {
                    "seed": seed,
                    "paint_color": private["parameters"]["paint_color"],
                    "public_id": public_id,
                    "public_path": str(public_path),
                    "private_path": str(private_path),
                }
            )

        default_program = program_for(DEFAULT_PAINT_COLOR, "both", root=root)
        canonical_checks = []
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root, labeled_only=True)):
            actual = execute(bridge, default_program, pair["input"])
            if actual != pair["output"]:
                raise ValueError(f"default program failed canonical pair {index}")
            canonical_checks.append({"pair_index": index, "output_sha256": sha256_bytes(
                json.dumps(actual, separators=(",", ":")).encode()
            )})
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

    input_groups: dict[int, list[dict[str, Any]]] = {}
    for episode in private_episodes:
        input_groups.setdefault(episode["input_seed"], []).append(episode)

    complete_group_rows = []
    incomplete_group_rows = []
    for input_seed, group in sorted(input_groups.items()):
        input_hashes = {tuple(episode["input_sha256"]) for episode in group}
        if len(input_hashes) != 1:
            raise ValueError(f"input group {input_seed} does not share inputs")
        colors = sorted({episode["parameters"]["paint_color"] for episode in group})
        row = {
            "input_seed": input_seed,
            "episode_seeds": sorted(episode["seed"] for episode in group),
            "paint_colors": colors,
            "input_sha256": list(next(iter(input_hashes))),
        }
        if set(colors) == set(PAINT_COLORS):
            complete_group_rows.append(row)
        else:
            incomplete_group_rows.append(row)

    shared_inputs = bool(complete_group_rows) and not incomplete_group_rows
    settings = sorted({episode["parameters"]["paint_color"] for episode in private_episodes})
    episode_rows.sort(key=lambda row: row["public_id"])
    _, generator_source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_record(root)["program_solution"]
    prototype_source = Path(__file__).resolve()
    report = {
        "schema": "548c1010ce89-parametric-paint-color-report-v1",
        "status": "prototype_passed",
        "prototype_status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "paint_color",
            "allowed": list(PAINT_COLORS),
            "default": DEFAULT_PAINT_COLOR,
        },
        "pairs_per_episode": {"train": len(DEMO_PROFILES), "test": len(QUERY_PROFILES)},
        "settings_covered": settings,
        "shared_inputs_across_settings": shared_inputs,
        "input_groups_checked": len(complete_group_rows),
        "input_groups": complete_group_rows,
        "canonical_default_exact": default_program == canonical,
        "canonical_pairs_checked": len(canonical_checks),
        "episodes": episode_rows,
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": sha256_bytes(prototype_source.read_bytes()),
        "program_sha256": {
            name: sha256_bytes(program.encode()) for name, program in all_programs.items()
        },
        "racket_runtime": runtime_identity,
        "limitations": [
            "prototype only; production remains pinned to paint color 2",
            "bounded evidence covers two declared colors and the listed episode seeds",
            "declared rivals are the other paint color and the two single-axis rules",
            "finite demonstrations do not prove uniqueness against arbitrary programs",
        ],
    }
    if set(settings) != set(PAINT_COLORS):
        report["status"] = "prototype_partial"
        report["missing_settings"] = sorted(set(PAINT_COLORS) - set(settings))
    if incomplete_group_rows:
        report["status"] = "prototype_partial"
        report["incomplete_input_groups"] = incomplete_group_rows
    _write_json(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    args = parser.parse_args(argv)
    report = write_evidence(args.out, seeds=tuple(args.seeds), root=ROOT)
    print(json.dumps({
        "status": report["status"],
        "settings_covered": report["settings_covered"],
        "episodes": len(report["episodes"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
