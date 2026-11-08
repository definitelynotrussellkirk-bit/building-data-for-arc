"""Task-local regression tests for b71c45e9a3c0.

The oracle and observations live in workspace/reference_probe.py and do not call
production helpers, so a shared implementation bug cannot make these tests pass.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "b71c45e9a3c0"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    bbox_key_output,
    canonical_pairs as probe_canonical_pairs,
    load_generator,
    observed,
    one_key_output,
    top_row_key_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_independent_oracle_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert bbox_key_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 9,
            "grid_w": 9,
            "n_groups": 4,
            "n_gap_shapes": 2,
            "palette_kind": "low",
            "shape_profile": "extended",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_groups": 2,
            "n_gap_shapes": 1,
            "palette_kind": "high",
            "shape_profile": "compact",
        },
        {
            "grid_h": 11,
            "grid_w": 12,
            "n_groups": 3,
            "n_gap_shapes": 1,
            "palette_kind": "mixed",
            "shape_profile": "mixed",
        },
    ],
)
def test_every_advertised_override_is_exact_in_every_band(band, options):
    grid = gen.generate(71, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_w", 15),
        ("n_groups", 1),
        ("n_groups", 5),
        ("n_gap_shapes", 0),
        ("n_gap_shapes", 3),
        ("palette_kind", "unknown"),
        ("shape_profile", "unknown"),
        ("grid_h", True),
        ("n_groups", 3.0),
        ("n_gap_shapes", "1"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_constructive_boundary_never_silently_drops_a_group(band):
    options = {
        "grid_h": 9,
        "grid_w": 9,
        "n_groups": 4,
        "n_gap_shapes": 2,
        "palette_kind": "mixed",
        "shape_profile": "mixed",
    }
    for index in range(96):
        grid = gen.generate(20_000 + index, index * 7, difficulty=band, **options)
        assert gen.self_check(grid) == []
        assert observed(grid) == options


@pytest.mark.parametrize(
    "profile,expected",
    [
        ("compact", lambda heights: all(height <= 2 for height in heights)),
        ("extended", lambda heights: all(height == 3 for height in heights)),
        (
            "mixed",
            lambda heights: any(height <= 2 for height in heights)
            and any(height == 3 for height in heights),
        ),
    ],
)
def test_shape_profile_changes_realized_geometry(profile, expected):
    grid = gen.generate(
        81,
        4,
        grid_h=11,
        grid_w=11,
        n_groups=4,
        n_gap_shapes=2,
        palette_kind="mixed",
        shape_profile=profile,
    )
    components = []
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    while unseen:
        stack = [unseen.pop()]
        cells = set(stack)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(cells)
    heights = [max(r for r, _ in cells) - min(r for r, _ in cells) + 1 for cells in components]
    assert expected(heights)


def test_declared_witnesses_refute_independently_implemented_rivals():
    grid = gen.generate(
        812,
        3,
        grid_h=11,
        grid_w=12,
        n_groups=3,
        n_gap_shapes=2,
        palette_kind="mixed",
        shape_profile="mixed",
    )
    expected = bbox_key_output(grid)
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["empty_bbox_corner"](grid)
    assert gen.SEMANTIC_WITNESSES["multiple_key_colors"](grid)
    assert top_row_key_output(grid) != expected
    assert one_key_output(grid) != expected
    assert gen.SEMANTIC_RIVALS["above_topmost_occupied"](grid) == top_row_key_output(grid)
    assert gen.SEMANTIC_RIVALS["one_key_for_all"](grid) == one_key_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_each_band_retains_substantial_canonical_profile_support(band):
    hits = 0
    for index in range(64):
        grid = gen.generate(70_000 + index, index * 11, difficulty=band)
        obs = observed(grid)
        hits += obs["grid_h"] == 11 and obs["grid_w"] in (10, 11, 12) and obs["n_groups"] == 3
    assert hits >= 16, f"only {hits}/64 canonical size/palette profiles in {band!r}"


def test_every_query_rotation_is_supported_by_the_declared_lesson_contract():
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(500, index * 11, difficulty=("easy", "medium", "hard", None)[index % 4])
        pairs.append({"input": grid, "output": bbox_key_output(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_generator_is_deterministic_and_python_hash_seed_independent():
    expected = gen.generate(319, 17, difficulty="hard")
    assert expected == gen.generate(319, 17, difficulty="hard")
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(319,17,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]])
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_portable_canonical_helper_sees_all_four_labeled_pairs():
    assert len(probe_canonical_pairs()) == 4

def test_default_layouts_include_objects_not_flush_to_outer_corners():
    """Reject the shortcut that every object's bbox is pinned to two outer edges."""
    saw_free_vertical_and_horizontal_margin = False
    for index in range(96):
        grid = gen.generate(880_000 + index, index * 19, difficulty="hard")
        for component in __import__("reference_probe").color3_components(grid):
            top, left, bottom, right = __import__("reference_probe").bbox(component)
            vertically_interior = top > 1 and bottom < len(grid) - 1
            horizontally_interior = left > 0 and right < len(grid[0]) - 1
            if vertically_interior and horizontally_interior:
                saw_free_vertical_and_horizontal_margin = True
                break
        if saw_free_vertical_and_horizontal_margin:
            break
    assert saw_free_vertical_and_horizontal_margin
