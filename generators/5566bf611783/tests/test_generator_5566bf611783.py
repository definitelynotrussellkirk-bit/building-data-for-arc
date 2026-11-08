"""Portable regression tests for the chamber-majority generator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "5566bf611783"
ROOT = find_root(__file__)
gen, GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _regions(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            cells = []
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _majority_output(grid):
    output = [row[:] for row in grid]
    for cells in _regions(grid):
        n2 = sum(grid[r][c] == 2 for r, c in cells)
        n3 = sum(grid[r][c] == 3 for r, c in cells)
        fill = 2 if n2 > n3 else 3 if n3 > n2 else 8
        for r, c in cells:
            if grid[r][c] == 0:
                output[r][c] = fill
    return output


def _counterexample():
    path = GENERATOR_PATH.parent / "counterexamples" / "green_present_dominates.json"
    # The portable runtime selects generator.py from puzzle_generators/, while
    # auxiliary selected-task files can remain under generators/TASK/.
    if not path.is_file():
        path = ROOT / "generators" / TASK_ID / "counterexamples" / path.name
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_five_canonical_inputs_have_official_linked_signatures():
    signatures = {
        gen.canonical_profile_signature(pair["input"])
        for pair in _canonical_pairs()
    }
    assert signatures == gen._CANONICAL_SIGNATURES


def test_default_schedule_reaches_every_official_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        counts = {signature: 0 for signature in gen._CANONICAL_SIGNATURES}
        for sample_index in range(600):
            grid = gen.generate(2718, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            signature = gen.canonical_profile_signature(grid)
            if signature in counts:
                counts[signature] += 1
        assert sum(counts.values()) >= 145, (band, counts)
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_recombined_marker_counts_are_not_official_profile():
    grid = _canonical_pairs()[0]["input"]
    changed = [row[:] for row in grid]
    changed[1][1] = 3
    signature = gen.canonical_profile_signature(changed)
    assert signature is not None
    assert signature not in gen._CANONICAL_SIGNATURES


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_literal_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, 1.75, "1"])
def test_sample_index_requires_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_difficulty_rejects_invalid_scalars(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", True), ("grid_h", 8.0), ("grid_h", "8"),
        ("grid_w", False), ("grid_w", 9.75), ("grid_w", "9"),
        ("div_cols", True), ("div_cols", 2.0), ("div_cols", "2"),
        ("div_rows", False), ("div_rows", 1.0), ("div_rows", "1"),
        ("tie_mode", 1), ("tie_mode", 0), ("tie_mode", "true"),
        ("topology_kind", 1), ("texture", False),
    ],
)
def test_declared_axes_reject_scalar_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, 0, **{axis: value})


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, 0, __override_contract_unknown_axis__=1)


@pytest.mark.parametrize(
    "overrides",
    [
        {"topology_kind": "canonical_cross", "div_cols": 1},
        {"topology_kind": "canonical_cross", "div_rows": 1},
        {"topology_kind": "cols_only", "div_rows": 2},
        {"topology_kind": "segments", "div_rows": 1},
        {"topology_kind": "mixed_grid", "div_rows": 0},
        {"texture": "canonical_cross", "div_cols": 3},
        {"texture": "mixed_grid", "div_rows": 0},
        {"texture": "cols_only", "topology_kind": "mixed_grid"},
    ],
)
def test_declared_incompatible_override_combinations_reject(overrides):
    with pytest.raises(ValueError):
        gen.generate(7, 0, **overrides)


def test_equal_topology_aliases_are_accepted():
    grid = gen.generate(
        7,
        0,
        texture="canonical_cross",
        topology_kind="canonical_cross",
        div_cols=2,
        div_rows=0,
    )
    assert gen.self_check(grid) == []


def test_declared_rival_fits_every_labeled_canonical_pair():
    rival = gen.CANONICAL_SHORTCUTS["green_present_dominates"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"], (
            pair["split"], pair["pair_index"]
        )


def test_exact_counterexample_refutes_canonical_shortcut():
    row = _counterexample()
    grid = row["input"]
    intended = _majority_output(grid)
    rival = gen.SEMANTIC_RIVALS["green_present_dominates"](grid)
    assert gen.self_check(grid) == []
    assert intended == row["intended_output"]
    assert rival == row["rival_output"]
    assert rival != intended
    assert gen.SEMANTIC_WITNESSES["red_majority_with_green"](grid)


def test_discriminator_schedule_covers_every_three_demo_rotation():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    for band in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            lesson = [
                gen.generate(991, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(lesson)):
                demos = [
                    grid for index, grid in enumerate(lesson)
                    if index != query_index
                ]
                assert any(
                    gen.SEMANTIC_WITNESSES["red_majority_with_green"](grid)
                    for grid in demos
                ), (band, start, query_index)


def test_lesson_hook_accepts_scheduled_rotations():
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        grids = [gen.generate(313, start + offset) for offset in range(4)]
        pairs = [
            {"input": grid, "output": _majority_output(grid)}
            for grid in grids
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
