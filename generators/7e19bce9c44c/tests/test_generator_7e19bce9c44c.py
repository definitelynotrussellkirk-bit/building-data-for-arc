"""Focused semantic and contract tests for generator 7e19bce9c44c."""
from __future__ import annotations

import hashlib
import importlib
import itertools
import json
import random
from collections import Counter
from pathlib import Path

import pytest

TASK_ID = "7e19bce9c44c"
ROOT = Path(__file__).resolve().parents[1]
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_path():
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data/canonical/puzzles.jsonl"
        if candidate.exists():
            return candidate
    raise AssertionError("canonical puzzles.jsonl not found in staged tree")


def _canonical_row():
    with _canonical_path().open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in row["train"] + test
    ]


def _same_color_component_count(grid):
    seen = set()
    count = 0
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0 or (row, col) in seen:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _pinned_seed(task_id, band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _bbox_for_cells(cells):
    return (
        min(row for row, _col in cells),
        max(row for row, _col in cells),
        min(col for _row, col in cells),
        max(col for _row, col in cells),
    )


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert digest == GENERATOR.RULE_HASH == "36e37e8e3020"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    expected_observations = [
        (8, 9, 3, 3, 7, 2),
        (9, 10, 3, 4, 7, 2),
        (7, 11, 4, 3, 8, 2),
        (10, 10, 4, 3, 8, 2),
        (9, 12, 3, 4, 7, 2),
    ]
    for pair, expected in zip(pairs, expected_observations):
        source = pair["input"]
        snapshot = [row[:] for row in source]
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot
        observed = GENERATOR.observe_overrides(source)
        assert tuple(observed[axis] for axis in GENERATOR.AXES) == expected


def test_every_boundary_override_combination_is_exact_in_every_band():
    boundaries = {
        "grid_h": (7, 10),
        "grid_w": (9, 12),
        "bbox_h": (3, 4),
        "bbox_w": (3, 4),
        "occupied_cells": (7, 8),
        "n_colors": (2, 3),
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, values in enumerate(itertools.product(*boundaries.values())):
            overrides = dict(zip(boundaries, values))
            grid = GENERATOR.generate(
                20_000 + 1_000 * band_index + case_index,
                7 * case_index + 3,
                difficulty=band,
                **overrides,
            )
            assert GENERATOR.self_check(grid) == []
            assert GENERATOR.observe_overrides(grid) == overrides


def test_official_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            seed = _pinned_seed(TASK_ID, band, index)
            grid = GENERATOR.generate(
                seed,
                seed % 7919 + index,
                difficulty=band,
            )
            exact += _profile(grid) in canonical_profiles
        assert exact > 0, f"{band} has no exact canonical-profile support"


def test_two_most_frequent_colour_shortcut_is_declared_and_refuted():
    rival_name = "two_most_frequent_colours_only"
    rival = GENERATOR.CANONICAL_SHORTCUTS[rival_name]
    assert GENERATOR.SEMANTIC_RIVALS[rival_name] is rival
    assert GENERATOR.WITNESS_RIVALS[
        "least_frequent_colour_bbox_essential"
    ] == [
        rival_name
    ]
    assert rival in GENERATOR.LESSON_COMPETITORS.values()

    # The canonical demonstrations use exactly two nonzero colours, so this
    # rival is observationally indistinguishable there.
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    # Every scheduled discriminative three-colour scene must force every
    # colour to contribute a unique bbox side. Removing any colour therefore
    # changes the intended crop geometry and defeats the rival above.
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in (0, 2, 4, 6):
            grid = GENERATOR.generate(
                910_000 + 1_000 * band_index + sample_index,
                sample_index,
                difficulty=band,
                n_colors=3,
            )
            assert GENERATOR.self_check(grid) == []
            assert GENERATOR.SEMANTIC_WITNESSES[
                "least_frequent_colour_bbox_essential"
            ](grid)
            assert rival(grid) != GENERATOR.rule_mirror(grid)

            cells = [
                (row, col)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value
            ]
            full_bbox = _bbox_for_cells(cells)
            colours = {grid[row][col] for row, col in cells}
            assert len(colours) == 3
            for colour in colours:
                without_colour = [
                    (row, col)
                    for row, col in cells
                    if grid[row][col] != colour
                ]
                assert _bbox_for_cells(without_colour) != full_bbox


def test_medium_three_demo_schedule_refutes_the_declared_shortcut():
    # Exact replay from the semantic gate's first post-repair counterexample.
    seed = 122_751_217_542_644
    start = 11
    pairs = []
    for sample_index in range(start, start + 4):
        grid = GENERATOR.generate(
            seed,
            sample_index,
            difficulty="medium",
        )
        pairs.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
    assert GENERATOR.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_even_default_draws_carry_three_colour_refutations_in_every_band():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grid = GENERATOR.generate(
            930_000 + band_index,
            2,
            difficulty=band,
        )
        assert GENERATOR.observe_overrides(grid)["n_colors"] == 3
        assert GENERATOR.SEMANTIC_WITNESSES[
            "least_frequent_colour_bbox_essential"
        ](grid)


def test_200_per_band_semantic_census_and_disjoint_stability():
    summaries = []
    for seed_base in (100_000, 700_000):
        run = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            axes = Counter()
            components = Counter()
            positions = set()
            inputs = set()
            outputs = set()
            canonical_profiles = 0
            for offset in range(200):
                seed = seed_base + band_index * 10_000 + offset
                grid = GENERATOR.generate(
                    seed,
                    seed * 29 + 11,
                    difficulty=band,
                )
                assert GENERATOR.self_check(grid) == []
                observed = GENERATOR.observe_overrides(grid)
                output = GENERATOR.rule_mirror(grid)
                axes[(
                    observed["bbox_h"],
                    observed["bbox_w"],
                    observed["occupied_cells"],
                    observed["n_colors"],
                )] += 1
                components[_same_color_component_count(grid)] += 1
                analysis, _errors = GENERATOR._analyze(grid)
                positions.add((analysis["top"], analysis["left"]))
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(json.dumps(output, separators=(",", ":")))
                if (
                    (observed["grid_h"], observed["grid_w"], observed["n_colors"] + 1)
                    in {(8, 9, 3), (9, 10, 3), (7, 11, 3), (10, 10, 3), (9, 12, 3)}
                ):
                    canonical_profiles += 1
            assert len(inputs) >= 198
            assert len(outputs) >= 190
            assert len(positions) >= 8
            assert min(components) >= 2
            assert max(components) >= 3
            run[band] = {
                "axis_support": set(axes),
                "unique_inputs": len(inputs),
                "unique_outputs": len(outputs),
                "canonical_profiles": canonical_profiles,
            }
        summaries.append(run)

    for run in summaries:
        assert run["easy"]["axis_support"] == {
            (3, 3, 7, 2),
            (3, 3, 7, 3),
        }
        assert (4, 4, 8, 3) in run["hard"]["axis_support"]
        assert any(
            n_colors == 2 and (bbox_h, bbox_w) != (4, 4)
            for bbox_h, bbox_w, _occupied, n_colors
            in run["hard"]["axis_support"]
        )
        assert len(run["medium"]["axis_support"]) >= 8
        assert run["easy"]["canonical_profiles"] > 0
        assert run["medium"]["canonical_profiles"] > 0
        assert run["hard"]["canonical_profiles"] > 0
    for band in ("easy", "medium", "hard"):
        assert abs(
            summaries[0][band]["unique_outputs"]
            - summaries[1][band]["unique_outputs"]
        ) <= 8


def test_four_targeted_impostors_and_negative_recombination_are_rejected():
    valid = GENERATOR.generate(424_242, 17, difficulty="medium")
    analysis, _errors = GENERATOR._analyze(valid)

    all_zero = [[0 for _ in row] for row in valid]

    single_color = [row[:] for row in valid]
    replacement = next(value for row in valid for value in row if value)
    for row, values in enumerate(single_color):
        for col, value in enumerate(values):
            if value:
                single_color[row][col] = replacement

    touches_border = [row[:] for row in valid]
    crop = GENERATOR.rule_mirror(valid)
    touches_border = [[0 for _ in row] for row in valid]
    for row, values in enumerate(crop):
        for col, value in enumerate(values):
            touches_border[row][col] = value

    filled_bbox = [row[:] for row in valid]
    first_color = next(value for row in valid for value in row if value)
    for row in range(analysis["top"], len(valid) - analysis["bottom_padding"]):
        for col in range(analysis["left"], len(valid[0]) - analysis["right_padding"]):
            if filled_bbox[row][col] == 0:
                filled_bbox[row][col] = first_color

    for name, impostor in {
        "all_zero": all_zero,
        "single_color": single_color,
        "touches_border": touches_border,
        "filled_bbox": filled_bbox,
    }.items():
        assert GENERATOR.self_check(impostor), name

    # The teaching distribution intentionally rejects this single-color
    # recombination, while the broader Racket crop oracle remains executable.
    assert GENERATOR.self_check(single_color)
    assert GENERATOR.rule_mirror(single_color)


def test_determinism_fresh_returns_global_rng_and_invalid_requests():
    random.seed(20260724)
    state = random.getstate()
    first = GENERATOR.generate(73, 109, difficulty="hard")
    assert random.getstate() == state
    second = GENERATOR.generate(73, 109, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GENERATOR.generate(73, 109, difficulty="hard") == second

    with pytest.raises(TypeError, match="unknown override"):
        GENERATOR.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(1, 2, difficulty="nightmare")
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, grid_h=6)
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, n_colors=4)
