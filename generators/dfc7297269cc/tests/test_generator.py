"""Task-local regression suite for dfc7297269cc.

The tests deliberately use an independent oracle from ``workspace`` rather than
production helpers.  They are portable under the source-bound task-test stage.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    active_motifs,
    canonical_pairs,
    changed_cells,
    explicit_counterexamples,
    intended_output,
    load_generator,
    observed,
)

gen = load_generator()


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}"
)
def test_accepts_every_canonical_input_and_matches_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_pins_selected_canonical_rule_hash():
    assert gen.RULE_HASH == "80ec61287499"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 5, "grid_w": 7, "motifs": 4, "n_colors": 4},
        {"grid_h": 14, "grid_w": 16, "motifs": 1, "n_colors": 2},
        {"grid_h": 6, "grid_w": 9, "motifs": 3, "n_colors": 3},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4),
        ("grid_h", 15),
        ("grid_w", 6),
        ("grid_w", 17),
        ("motifs", 0),
        ("motifs", 5),
        ("n_colors", 1),
        ("n_colors", 5),
        ("grid_h", True),
        ("motifs", 2.5),
        ("n_colors", "3"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_and_refutes_all_declared_shortcuts(band):
    shapes = set()
    motif_counts = set()
    color_counts = set()
    unique_inputs = set()
    for index in range(128):
        seed = 10_000 + index * 97
        grid = gen.generate(seed, index * 11 + 3, difficulty=band)
        assert grid == gen.generate(seed, index * 11 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == observed(grid)
        output = intended_output(grid)
        assert len(changed_cells(grid, output)) == len(active_motifs(grid))
        assert output != grid
        for name, rival in RIVALS.items():
            assert rival(deepcopy(grid)) != output, name
            assert gen.SEMANTIC_WITNESSES[name](deepcopy(grid)) is True
            assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) == rival(deepcopy(grid))
        shapes.add((len(grid), len(grid[0])))
        motif_counts.add(len(active_motifs(grid)))
        color_counts.add(len({v for row in grid for v in row if v != 0}))
        unique_inputs.add(repr(grid))
    assert len(shapes) >= 3
    assert motif_counts == {1, 2, 3, 4}
    assert color_counts == {2, 3, 4}
    assert len(unique_inputs) >= 120


def _max_same_color_component(grid):
    seen = set()
    largest = 0
    height, width = len(grid), len(grid[0])
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            size = 0
            while stack:
                row, col = stack.pop()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = row + dr, col + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            largest = max(largest, size)
    return largest


def test_generated_component_scale_includes_the_canonical_singletons():
    sizes = {
        _max_same_color_component(gen.generate(7000 + index, index * 13))
        for index in range(96)
    }
    assert 1 in sizes
    assert max(sizes) <= 2


def _same_color_object_count(grid):
    seen = set()
    count = 0
    height, width = len(grid), len(grid[0])
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            count += 1
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = row + dr, col + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
    return count


def test_generated_object_count_reaches_canonical_scale():
    counts = {
        _same_color_object_count(gen.generate(8100 + index, index * 17))
        for index in range(96)
    }
    assert min(counts) <= 8
    assert max(counts) >= 10


def test_each_canonical_shortcut_fits_all_canonical_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == set(RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs()), name


def test_small_explicit_counterexamples_are_real_and_validator_lawful():
    examples = explicit_counterexamples()
    for name, grid in examples.items():
        assert intended_output(grid) != RIVALS[name](grid)
        # The broad canonical grammar permits these exact local counterexamples.
        assert gen.self_check(grid) == []


def test_validator_rejects_minimal_structure_destroying_impostors():
    baseline = gen.generate(41, 7, grid_h=6, grid_w=9, motifs=2, n_colors=3)
    foreground = next(value for row in baseline for value in row if value != 0)
    height, width = len(baseline), len(baseline[0])
    impostors = {
        "all_background": [[0] * width for _ in range(height)],
        "full_one_color": [[foreground] * width for _ in range(height)],
        "singleton": [
            [foreground if (row, col) == (height // 2, width // 2) else 0
             for col in range(width)]
            for row in range(height)
        ],
        "solid_2x2": [
            [foreground if row < 2 and col < 2 else 0 for col in range(width)]
            for row in range(height)
        ],
        "short_line": [
            [foreground if row == height // 2 and col < 4 else 0 for col in range(width)]
            for row in range(height)
        ],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True, 0, True]], [[-1, 0, -1]], [[10, 0, 10]]],
)
def test_malformed_grid_is_diagnostic_not_an_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_matches_canonical_and_generated_cases_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(36)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
