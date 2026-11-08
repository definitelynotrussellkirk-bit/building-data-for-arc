#!/usr/bin/env python3
"""Bounded adversarial/Racket probe for the match-mode parametric family.

The probe targets the concrete shortcuts found during review: fixed-row answers,
color-mask matching, treating wildcard zero as literal background, and omitting
part of the orientation intermediate.  It also crosses semantic and nuisance
controls, covers the base generator's declared observable surface, and retains
minimum/maximum lesson and 30x30 boundary checks.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Iterable

_HOME = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load("parametric_860cbb625ca0_probe_prototype", _HOME / "prototype.py")
base_generator = _load("generator_860cbb625ca0_probe", _HOME.parent.parent / "generator.py")


def _positive_rows(output):
    return [index for index, value in enumerate(output[0]) if value]


def _base_surface_probe():
    cases = 0
    case_index = 0
    density_counts = {"sparse": 1, "medium": 2, "dense": 3}
    for h in (6, 8, 12, 16):
        candidate_lengths = [len(list(range(parity, h - 2, 2))) for parity in (0, 1)]
        max_rows = min(6, max(length - 1 for length in candidate_lengths))
        for total_w in (9, 18, 30):
            board_w = total_w - 4
            column_capacity = len(list(range(0, board_w - 2, 4)))
            densities = [
                name for name, count in density_counts.items() if count <= column_capacity
            ]
            for n_rows in sorted({1, max_rows}):
                supports_scattered = any(
                    length >= (3 if n_rows == 1 else n_rows + 1)
                    for length in candidate_lengths
                )
                biases = ("top", "bottom", "scattered") if supports_scattered else ("top", "bottom")
                for bias in biases:
                    for density in densities:
                        for n_colors in (1, 2):
                            palette_kind = base_generator.PALETTE_KINDS[
                                case_index % len(base_generator.PALETTE_KINDS)
                            ]
                            grid = base_generator.generate(
                                1000 + case_index,
                                case_index % 11,
                                grid_h=h,
                                grid_w=total_w,
                                n_match_rows=n_rows,
                                palette_kind=palette_kind,
                                n_distinct_colors=n_colors,
                                position_bias=bias,
                                density=density,
                            )
                            observed = base_generator.observe_overrides(grid)
                            expected = {
                                "grid_h": h,
                                "grid_w": total_w,
                                "palette_kind": palette_kind,
                                "n_match_rows": n_rows,
                                "palette_size": n_colors,
                                "position_bias": bias,
                                "n_distinct_colors": n_colors,
                                "density": density,
                            }
                            if observed != expected:
                                raise AssertionError(
                                    f"base override observability drift: expected={expected}, actual={observed}"
                                )
                            if base_generator.self_check(grid):
                                raise AssertionError("base self_check rejected an explicit valid draw")
                            output = prototype.python_mirror(grid, match_mode="exact")
                            rows = _positive_rows(output)
                            if len(rows) != n_rows:
                                raise AssertionError("base match-row count drifted")
                            if any(output[0][row] != density_counts[density] for row in rows):
                                raise AssertionError("base density count drifted")
                            cases += 1
                            case_index += 1

    rejection_calls = (
        lambda: base_generator.generate(
            11,
            0,
            grid_h=6,
            grid_w=16,
            n_match_rows=1,
            palette_kind="default",
            n_distinct_colors=1,
            position_bias="scattered",
            density="sparse",
        ),
        lambda: base_generator.generate(11, 0, grid_h=True),
        lambda: base_generator.generate(11, 0, grid_w=9, density="dense"),
        lambda: base_generator.generate(
            11, 0, palette_size=1, n_distinct_colors=2
        ),
        lambda: base_generator.generate(11, 0, unknown_axis=1),
    )
    rejections = 0
    for call in rejection_calls:
        try:
            call()
        except (TypeError, ValueError):
            rejections += 1
        else:
            raise AssertionError("base generator accepted an invalid or unobservable control")
    return cases, rejections


def _fixed_anchor_orientation_counterfactual(sample):
    """Change one exact stamp to 180 degrees without moving its rectangle."""
    grid = sample["grid"]
    template, board = prototype.split_input(grid)
    placements = [
        row for row in sample["semantic_placements"] if row["variant_index"] == 0
    ]
    if not placements:
        raise AssertionError("sample has no exact placement to cross")
    selected = placements[0]
    rotated = prototype.variants_for(template, "rotations")[2]
    if selected["shape"] != [len(rotated), len(rotated[0])]:
        raise AssertionError("counterfactual must preserve the selected stamp shape")
    changed_board = [row[:] for row in board]
    r0, c0 = selected["row"], selected["col"]
    for dr in range(selected["shape"][0]):
        for dc in range(selected["shape"][1]):
            changed_board[r0 + dr][c0 + dc] = 0
    prototype.paste_grid(changed_board, rotated, r0, c0)
    return prototype.compose_input(template, changed_board)


def run_probe(*, seeds=(0, 1, 2), demo_counts=(2, 3, 6), bridge=None):
    seeds = list(seeds)
    demo_counts = list(demo_counts)
    if not seeds:
        raise ValueError("seeds must be nonempty")
    if not demo_counts:
        raise ValueError("demo_counts must be nonempty")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    if len(set(demo_counts)) != len(demo_counts):
        raise ValueError("demo_counts must be distinct")

    owns_bridge = bridge is None
    active = prototype.RacketBridge() if owns_bridge else bridge
    episodes_checked = 0
    pairs_checked = 0
    parameter_rivals_checked = 0
    shortcut_rivals_checked = 0
    shortcut_rivals_refuted = 0
    shortcut_error_refutations = 0
    minimum_lesson_episodes = 0
    stress_cases_checked = 0
    palette_invariance_checks = 0
    crossed_control_checks = 0
    max_shape = [0, 0]
    profile_hashes = set()
    try:
        for seed in seeds:
            prototype._validate_seed(seed)
            for demos in demo_counts:
                prototype._validate_counts(demos, 4)
                family = prototype.make_episode_family(
                    seed,
                    demos=demos,
                    queries=4,
                    bridge=active,
                )
                for mode in prototype.ALLOWED_MODES:
                    episode = family[mode]
                    if episode["ambiguities"]:
                        raise AssertionError(f"ambiguous rivals for {seed=} {demos=} {mode=}")
                    if len(episode["test"]) != 4:
                        raise AssertionError("query count drifted")
                    query_hashes = {
                        prototype.grid_sha256(pair["input"]) for pair in episode["test"]
                    }
                    if len(query_hashes) != 4:
                        raise AssertionError("query inputs are not distinct")
                    for rival in episode["parameter_rivals"]:
                        parameter_rivals_checked += 1
                        if rival["status"] != "refuted_by_demonstrations":
                            raise AssertionError("declared parameter rival survived demonstrations")
                    diagnostics = episode["shortcut_rivals"]
                    if diagnostics != prototype.rival_diagnostics(episode):
                        raise AssertionError("persisted shortcut diagnostics drifted")
                    for row in diagnostics:
                        shortcut_rivals_checked += 1
                        shortcut_error_refutations += len(row["demonstration_error_records"])
                        if row["status"] != "refuted_by_demonstrations":
                            raise AssertionError(
                                f"shortcut survived {seed=} {demos=} {mode=}: {row['name']}"
                            )
                        shortcut_rivals_refuted += 1
                    if demos == 2:
                        minimum_lesson_episodes += 1
                    for pair in episode["train"] + episode["test"]:
                        pairs_checked += 1
                        h, w = len(pair["input"]), len(pair["input"][0])
                        max_shape = [max(max_shape[0], h), max(max_shape[1], w)]
                        expected = prototype.python_mirror(
                            pair["input"], match_mode=mode
                        )
                        if pair["output"] != expected:
                            raise AssertionError("stored label disagrees with mirror")
                        profile_hashes.add(prototype.grid_sha256(expected))
                    stress = episode["test"][-1]["input"]
                    if [len(stress), len(stress[0])] != [30, 30]:
                        raise AssertionError("last query is not the 30x30 boundary case")
                    _, stress_board = prototype.split_input(stress)
                    occupied = [
                        (r, c)
                        for r, row in enumerate(stress_board)
                        for c, value in enumerate(row)
                        if value
                    ]
                    rows = {r for r, _ in occupied}
                    cols = {c for _, c in occupied}
                    if not (
                        len(occupied) >= 70
                        and min(rows) == 0
                        and max(rows) == len(stress_board) - 1
                        and min(cols) == 0
                        and max(cols) == len(stress_board[0]) - 1
                    ):
                        raise AssertionError("30x30 stress case lost substantive boundary spread")
                    stress_cases_checked += 1
                    episodes_checked += 1

            # Nuisance crossing: a palette bijection preserves every orientation
            # record and final output, verified through protected Racket.
            invariant_sample = prototype._build_input(seed, 1, 7, "medium")
            recolored = prototype.recolor_input(
                invariant_sample["grid"], salt=7000 + seed
            )
            if recolored == invariant_sample["grid"]:
                raise AssertionError("palette crossing failed to change visible colors")
            for mode in prototype.ALLOWED_MODES:
                before_records = prototype.match_records(
                    invariant_sample["grid"], match_mode=mode
                )
                after_records = prototype.match_records(recolored, match_mode=mode)
                if after_records != before_records:
                    raise AssertionError("palette nuisance changed the intended intermediate")
                expected = prototype.python_mirror(
                    invariant_sample["grid"], match_mode=mode
                )
                if prototype.python_mirror(recolored, match_mode=mode) != expected:
                    raise AssertionError("palette nuisance changed Python output")
                actual = prototype.execute_rule(
                    prototype.program_for(mode), recolored, bridge=active
                )
                if actual != expected:
                    raise AssertionError("palette nuisance changed protected-Racket output")
                palette_invariance_checks += 1

            # Semantic crossing: keep canvas, anchor and rectangle fixed while
            # swapping one exact orientation to 180 degrees.
            semantic_sample = prototype._build_input(seed, 0, 7, "medium")
            crossed = _fixed_anchor_orientation_counterfactual(semantic_sample)
            if [len(crossed), len(crossed[0])] != semantic_sample["shape"]:
                raise AssertionError("semantic crossing changed dimensions")
            before_exact = prototype.python_mirror(
                semantic_sample["grid"], match_mode="exact"
            )
            after_exact = prototype.python_mirror(crossed, match_mode="exact")
            if before_exact == after_exact:
                raise AssertionError("fixed-anchor semantic crossing did not change exact output")
            actual = prototype.execute_rule(
                prototype.program_for("exact"), crossed, bridge=active
            )
            if actual != after_exact:
                raise AssertionError("crossed semantic case failed protected-Racket parity")
            crossed_control_checks += 1
    finally:
        if owns_bridge:
            active.shutdown()

    base_cases, base_rejections = _base_surface_probe()
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "base_generator_version": base_generator.VERSION,
        "modes": list(prototype.ALLOWED_MODES),
        "seeds": seeds,
        "demo_counts": demo_counts,
        "episodes_checked": episodes_checked,
        "pairs_checked": pairs_checked,
        "parameter_rivals_checked": parameter_rivals_checked,
        "shortcut_rivals_checked": shortcut_rivals_checked,
        "shortcut_rivals_refuted": shortcut_rivals_refuted,
        "shortcut_error_refutations": shortcut_error_refutations,
        "minimum_lesson_episodes": minimum_lesson_episodes,
        "palette_invariance_checks": palette_invariance_checks,
        "crossed_control_checks": crossed_control_checks,
        "stress_cases_checked": stress_cases_checked,
        "base_generator_cases": base_cases,
        "base_generator_rejections": base_rejections,
        "distinct_output_profiles": len(profile_hashes),
        "queries_per_episode": 4,
        "max_input_shape": max_shape,
        "finite_scope": (
            "Bounded seeds/counts and named rivals only; this is not a proof of "
            "uniqueness against arbitrary programs."
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_probe(seeds=args.seeds, demo_counts=args.demo_counts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
