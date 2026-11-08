"""Task-local regression tests for the repaired axis-key reflection sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1e92a4eef51d"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_1e92a4eef51d", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _crop_without_key(grid):
    rest = [list(row) for row in grid]
    rest[0][0] = 0
    cells = [
        (r, c)
        for r, row in enumerate(rest)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert cells
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in rest[r0 : r1 + 1]]


def _oracle(grid):
    crop = _crop_without_key(grid)
    if grid[0][0] == 1:
        return [row[::-1] for row in crop]
    if grid[0][0] == 2:
        return crop[::-1]
    return crop


def _labeled(grid):
    return {"input": deepcopy(grid), "output": _oracle(grid)}


def _canvas_relation(grid):
    h, w = len(grid), len(grid[0])
    return "landscape" if w > h else "portrait" if h > w else "square"


def test_rule_pin_and_all_canonical_pairs_are_accepted_and_exact():
    assert GEN.RULE_HASH == "bf7a0a12ef08"
    assert len(CANONICAL) == 4
    for pair in CANONICAL:
        assert GEN.self_check(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 14,
            "grid_w": 7,
            "key": 1,
            "blob_size": 7,
            "n_distinct_colors": 3,
            "n_components": 2,
            "aspect_relation": "conflict",
        },
        {
            "grid_h": 7,
            "grid_w": 14,
            "key": 2,
            "blob_size": 4,
            "n_distinct_colors": 1,
            "n_components": 1,
            "aspect_relation": "conflict",
        },
    ],
)
def test_every_exact_override_is_visible_in_every_band(band, requested):
    grid = GEN.generate(91, 7, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert _oracle(grid) != _crop_without_key(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_w": 15},
        {"key": 0},
        {"blob_size": 3},
        {"n_distinct_colors": 4},
        {"n_components": 0},
        {"aspect_relation": "square"},
        {"grid_h": True},
        {"key": "1"},
        {"aspect_relation": 1},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_four_profile_schedule_is_rotation_safe_for_declared_competitors():
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.EXAMPLES_NEEDED == 3
    profiles = [GEN.schedule_profile(0, index, "medium") for index in range(4)]
    assert tuple(profiles) == tuple(GEN.SCHEDULE_PROFILES)

    observed = [GEN.observe_overrides(GEN.generate(17, index)) for index in range(4)]
    assert [row["key"] for row in observed] == [1, 2, 1, 2]
    assert [row["aspect_relation"] for row in observed] == [
        "aligned",
        "conflict",
        "conflict",
        "aligned",
    ]
    assert [_canvas_relation(GEN.generate(17, index)) for index in range(4)] == [
        "landscape",
        "landscape",
        "portrait",
        "square",
    ]

    for start in range(4):
        pairs = [_labeled(GEN.generate(31, start + offset)) for offset in range(4)]
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_canonical_canvas_aspect_shortcut_fits_all_public_pairs_but_generated_witnesses_refute_it():
    rival = GEN.CANONICAL_SHORTCUTS["canvas_aspect_axis"]
    assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in CANONICAL)

    for index in (1, 2):
        grid = GEN.generate(708, index)
        assert GEN.SEMANTIC_WITNESSES["canvas_axis_conflict"](grid)
        assert rival(deepcopy(grid)) != _oracle(grid)


def test_crop_aspect_and_fixed_axis_rivals_have_real_generated_counterexamples():
    cases = {
        "always_horizontal": GEN.generate(801, 1),
        "always_vertical": GEN.generate(802, 0),
        "crop_aspect_axis": GEN.generate(803, 1),
    }
    for name, grid in cases.items():
        assert GEN.SEMANTIC_RIVALS[name](deepcopy(grid)) != _oracle(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_covers_canonical_and_broad_features(band):
    observed = []
    grids = []
    body_colors = set()
    for index in range(128):
        grid = GEN.generate(2000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(2000 + index, index, difficulty=band)
        grids.append(grid)
        row = GEN.observe_overrides(grid)
        observed.append(row)
        body_colors.update(
            value
            for r, line in enumerate(grid)
            for c, value in enumerate(line)
            if value != 0 and (r, c) != (0, 0)
        )

    assert {row["key"] for row in observed} == {1, 2}
    assert {row["blob_size"] for row in observed} == {4, 5, 6, 7}
    assert {row["n_distinct_colors"] for row in observed} == {1, 2, 3}
    assert {row["n_components"] for row in observed} == {1, 2}
    assert {row["aspect_relation"] for row in observed} == {"aligned", "conflict"}
    assert len({(row["grid_h"], row["grid_w"]) for row in observed}) >= 12
    assert 2 in body_colors
    assert len({tuple(map(tuple, grid)) for grid in grids}) == len(grids)


def test_self_check_rejects_malformed_or_semantically_empty_inputs():
    bad = [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(7)],
    ]
    for grid in bad:
        assert GEN.self_check(grid)


def test_reference_helpers_do_not_mutate_inputs():
    grid = GEN.generate(44, 9)
    original = deepcopy(grid)
    assert GEN._reference_output(grid) == _oracle(grid)
    for rival in GEN.LESSON_COMPETITORS.values():
        rival(grid)
        assert grid == original


def test_each_difficulty_band_has_a_pinned_exact_canonical_profile_anchor():
    """Mirror the repository profile-floor census that caught band starvation."""
    import hashlib

    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in CANONICAL
    }
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact += profile in canonical_profiles
        assert exact >= 1, f"{band} has no exact canonical-profile anchor"
