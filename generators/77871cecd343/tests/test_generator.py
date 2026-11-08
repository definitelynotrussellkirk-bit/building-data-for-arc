"""Task-local regression suite for the cross-reflection input sampler."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    centered_cross_rival,
    intended_output,
    load_generator,
    observed,
    quadrant_offset_rival,
    racket_outputs,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "row_offset",
    "col_offset",
    "source_quadrant",
    "shape_cells",
}


def test_pins_authority_and_advertises_only_observable_axes():
    assert gen.RULE_HASH == "1bad9bf6a465"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=9, grid_w=9, row_offset=-1, col_offset=1, source_quadrant="bottom_right", shape_cells=8),
        dict(grid_h=15, grid_w=15, row_offset=1, col_offset=-1, source_quadrant="top_right", shape_cells=3),
        dict(grid_h=11, grid_w=9, row_offset=0, col_offset=0, source_quadrant="bottom_left", shape_cells=5),
    ],
)
def test_every_exact_override_is_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_h", 16),
        ("grid_w", 8),
        ("grid_w", 16),
        ("row_offset", -2),
        ("row_offset", 2),
        ("col_offset", -2),
        ("col_offset", 2),
        ("source_quadrant", "northwest"),
        ("shape_cells", 2),
        ("shape_cells", 9),
        ("shape_cells", True),
        ("grid_h", 9.0),
    ],
)
def test_rejects_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", "expert", 1])
def test_rejects_unknown_difficulty(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_covers_task_axes_and_is_deterministic(band):
    support = {name: set() for name in EXPECTED_AXES}
    unique = set()
    for index in range(128):
        grid = gen.generate(3100 + index, index, difficulty=band)
        assert grid == gen.generate(3100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        obs = observed(grid)
        for name, value in obs.items():
            support[name].add(value)
        unique.add(tuple(tuple(row) for row in grid))
        out = intended_output(grid)
        assert out != grid
        assert sum(a != b for ra, rb in zip(grid, out) for a, b in zip(ra, rb)) == 3 * obs["shape_cells"]
    assert support["source_quadrant"] == {"top_left", "top_right", "bottom_left", "bottom_right"}
    assert support["row_offset"] == {-1, 0, 1}
    assert support["col_offset"] == {-1, 0, 1}
    assert len(support["grid_h"]) >= 3
    assert len(support["grid_w"]) >= 3
    assert len(support["shape_cells"]) >= 2
    assert len(unique) >= 120


def test_default_schedule_decouples_quadrant_from_cross_offset():
    expected_offsets = {(r, c) for r in (-1, 0, 1) for c in (-1, 0, 1)}
    support = {quadrant: set() for quadrant in (
        "top_left", "top_right", "bottom_left", "bottom_right"
    )}
    for index in range(36):
        grid = gen.generate(8050 + index, index, difficulty="medium")
        obs = observed(grid)
        support[obs["source_quadrant"]].add((obs["row_offset"], obs["col_offset"]))
    assert support == {quadrant: expected_offsets for quadrant in support}


def test_every_four_example_window_refutes_declared_competitors_and_covers_quadrants():
    assert {"assume_centered_cross", "assume_quadrant_offset_schedule"} <= set(gen.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for start in range(36):
            grids = [gen.generate(8100 + start, start + offset, difficulty=band) for offset in range(4)]
            assert {observed(grid)["source_quadrant"] for grid in grids} == {
                "top_left",
                "top_right",
                "bottom_left",
                "bottom_right",
            }
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(grid) != intended_output(grid) for grid in grids)




def test_independent_probe_refutes_quadrant_offset_lookup():
    assert all(quadrant_offset_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = gen.generate(9127, 4, difficulty="medium")
    obs = observed(grid)
    assert obs["source_quadrant"] == "top_left"
    assert (obs["row_offset"], obs["col_offset"]) != (0, 0)
    assert quadrant_offset_rival(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["assume_quadrant_offset_schedule"](grid) == quadrant_offset_rival(grid)

def test_declared_shortcuts_fit_canonical_but_generated_witnesses_refute_them():
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = witness_input()
    assert gen.self_check(grid) == []
    assert centered_cross_rival(grid) != intended_output(grid)
    assert gen.SEMANTIC_WITNESSES["off_center_cross"](grid)
    assert gen.SEMANTIC_RIVALS["assume_centered_cross"](grid) == centered_cross_rival(grid)
    assert gen.WITNESS_RIVALS == {
        "off_center_cross": ["assume_centered_cross"],
        "off_quadrant_schedule": ["assume_quadrant_offset_schedule"],
    }
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "assume_centered_cross", "assume_quadrant_offset_schedule"
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)


@pytest.mark.parametrize(
    "mutation",
    [
        "erase_axis",
        "stray_nine",
        "second_quadrant",
        "disconnect_source",
        "source_on_axis",
        "unknown_color",
        "too_few_cells",
    ],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        4,
        2,
        grid_h=11,
        grid_w=11,
        row_offset=0,
        col_offset=0,
        source_quadrant="top_left",
        shape_cells=5,
    )
    sr, sc = len(grid) // 2, len(grid[0]) // 2
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if mutation == "erase_axis":
        grid[sr][0] = 0
    elif mutation == "stray_nine":
        grid[0][-1] = 9
    elif mutation == "second_quadrant":
        grid[sr + 1][sc + 1] = 1
    elif mutation == "disconnect_source":
        r, c = ones[-1]
        grid[r][c] = 0
        remaining = {(rr, cc) for rr, cc in ones[:-1]}
        candidate = next(
            (rr, cc)
            for rr in range(sr)
            for cc in range(sc)
            if (rr, cc) not in remaining
            and all(abs(rr - ar) + abs(cc - ac) > 1 for ar, ac in remaining)
        )
        grid[candidate[0]][candidate[1]] = 1
    elif mutation == "source_on_axis":
        grid[sr][0] = 1
    elif mutation == "unknown_color":
        grid[0][-1] = 7
    elif mutation == "too_few_cells":
        for r, c in ones[2:]:
            grid[r][c] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_rule_and_rival_are_pure():
    grid = witness_input()
    original = deepcopy(grid)
    intended_output(grid)
    centered_cross_rival(grid)
    gen.SEMANTIC_RIVALS["assume_centered_cross"](grid)
    assert grid == original


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


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(32)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
