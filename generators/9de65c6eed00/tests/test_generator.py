"""Focused regressions for normalized largest-minus-smaller subtraction.

The geometry helpers here intentionally reimplement the selected Racket rule;
they do not call private runner functions or production generator helpers.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "9de65c6eed00"
TASK_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task_under_test", TASK_DIR / "generator.py")
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")
PALETTES = ((2, 3), (5, 7), (3, 5), (8, 4), (6, 1), (9, 2))
PROFILES = {
    0: (
        {(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1)},
        {(0, 0), (0, 1)},
    ),
    1: (
        {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 2)},
        {(0, 0), (0, 1), (1, 0), (2, 0)},
    ),
    2: (
        {(0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)},
        {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)},
    ),
    3: (
        {(0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 2)},
        {(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)},
    ),
}
RIVALS = {"no_normalization", "bbox_subtraction", "smaller_color", "subset_only", "crop_to_large"}


def components(grid):
    """Same-color four-connected nonzero components, measured independently."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            cells = [(sr, sc)]
            seen.add((sr, sc))
            for row, col in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = row + dr, col + dc
                    rr, cc = point
                    if (0 <= rr < height and 0 <= cc < width and point not in seen
                            and grid[rr][cc] == color):
                        seen.add(point)
                        cells.append(point)
            result.append((color, cells))
    return result


def normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return {(row - top, col - left) for row, col in cells}


def bbox_size(cells):
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def intended_output(grid):
    objects = sorted(
        components(grid),
        key=lambda item: (-len(item[1]), min(r for r, _ in item[1]), min(c for _, c in item[1])),
    )
    (large_color, large_raw), (_, small_raw) = objects[:2]
    large, small = normalize(large_raw), normalize(small_raw)
    large_h, large_w = bbox_size(large)
    small_h, small_w = bbox_size(small)
    output = [[0] * max(large_w, small_w) for _ in range(max(large_h, small_h))]
    for row, col in large - small:
        output[row][col] = large_color
    return output


def canonical_signature(cells):
    """Shape signature invariant to joint D4 orientation."""
    cells = normalize(cells)
    variants = []
    for reflect in (False, True):
        current = set(cells)
        if reflect:
            current = {(r, -c) for r, c in current}
            current = normalize(current)
        for _ in range(4):
            current = normalize(current)
            variants.append(tuple(sorted(current)))
            current = {(c, -r) for r, c in current}
    return min(variants)


def profile_of(grid):
    objects = sorted(components(grid), key=lambda item: len(item[1]), reverse=True)
    observed = (canonical_signature(objects[0][1]), canonical_signature(objects[1][1]))
    for profile_id, (large, small) in PROFILES.items():
        expected = (canonical_signature(large), canonical_signature(small))
        if observed == expected:
            return profile_id
    raise AssertionError(f"unknown generated profile: {observed}")


def palette_of(grid):
    objects = sorted(components(grid), key=lambda item: len(item[1]), reverse=True)
    pair = objects[0][0], objects[1][0]
    return PALETTES.index(pair)


def accepts(value):
    return value is True or value == []


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


def test_rule_hash_and_finite_teaching_schedule_are_pinned():
    assert gen.RULE_HASH == "5c7d71fc1b03"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(gen.SCHEDULE_PROFILES) == (0, 1, 2, 3)


@pytest.mark.parametrize("band", BANDS)
def test_every_canonical_input_is_lawful_in_every_band(canonical, band):
    for pair in canonical:
        assert gen.self_check(pair["input"], difficulty=band) == [], pair
        assert accepts(gen.strict_canonical_like(pair["input"])), pair
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile_id", range(4))
@pytest.mark.parametrize("palette_id", range(len(PALETTES)))
def test_exact_profile_and_palette_controls_are_observable(band, profile_id, palette_id):
    options = {"grid_h": 8, "grid_w": 12, "profile_id": profile_id, "palette_id": palette_id}
    grid = gen.generate(319, 17, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band) == []
    assert len(grid) == 8 and len(grid[0]) == 12
    assert profile_of(grid) == profile_id
    assert palette_of(grid) == palette_id
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(319, 17, difficulty=band, **options)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("grid_h,grid_w", ((6, 9), (6, 18), (14, 9), (14, 18)))
def test_extreme_dimensions_are_constructive_in_every_band(band, grid_h, grid_w):
    for profile_id in range(4):
        grid = gen.generate(901, profile_id, difficulty=band, grid_h=grid_h,
                            grid_w=grid_w, profile_id=profile_id, palette_id=0)
        assert gen.self_check(grid, difficulty=band) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": grid_h, "grid_w": grid_w,
            "profile_id": profile_id, "palette_id": 0,
        }


@pytest.mark.parametrize("key,value", [
    ("grid_h", 5), ("grid_h", 15), ("grid_w", 8), ("grid_w", 19),
    ("profile_id", -1), ("profile_id", 4), ("palette_id", -1), ("palette_id", 6),
    ("grid_h", True), ("grid_w", 10.5), ("profile_id", "1"), ("palette_id", False),
    ("small_size", 3), ("large_size", 7), ("palette_kind", "warm"),
    ("palette_size", 2), ("position_bias", "two_separated_objects"),
    ("n_distinct_colors", 2), ("density", "sparse"), ("texture", "default"),
    ("unknown_axis", 1),
])
def test_invalid_and_retired_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_none_overrides_retain_default_draw_behavior():
    explicit_none = gen.generate(77, 11, grid_h=None, grid_w=None,
                                 profile_id=None, palette_id=None)
    assert explicit_none == gen.generate(77, 11)


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(6)],
    [[0] * 9 for _ in range(6)], [[10] * 9 for _ in range(6)],
    [[1, 1], [0, 0]], ["000000000"] * 6,
])
def test_malformed_or_out_of_domain_inputs_return_reasons_not_exceptions(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


def test_default_schedule_hits_all_profiles_and_canonical_dimensions_in_every_band():
    for band in BANDS:
        grids = [gen.generate(418, index, difficulty=band) for index in range(20)]
        assert {profile_of(grid) for grid in grids} == set(range(4))
        dims = {(len(grid), len(grid[0])) for grid in grids}
        assert {(6, 9), (6, 10), (6, 11)} <= dims
        assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)


def test_declared_witnesses_and_rivals_are_real_counterexamples():
    assert RIVALS == set(gen.SEMANTIC_RIVALS)
    assert RIVALS == set(gen.LESSON_COMPETITORS)
    for profile_id in range(4):
        grid = gen.generate(271, profile_id, grid_h=8, grid_w=12,
                            profile_id=profile_id, palette_id=profile_id)
        expected = intended_output(grid)
        original = deepcopy(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            got = rival(grid)
            assert grid == original, f"{name} mutated its input"
            assert got == rival(deepcopy(grid)), f"{name} is nondeterministic"
            if any(gen.WITNESS_RIVALS.get(w) == [name] and predicate(grid)
                   for w, predicate in gen.SEMANTIC_WITNESSES.items()):
                assert got != expected, (profile_id, name)


def test_every_three_demonstration_rotation_refutes_all_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            grids = [gen.generate(761, start + offset, difficulty=band) for offset in range(4)]
            expected = [intended_output(grid) for grid in grids]
            for query in range(4):
                demos = [index for index in range(4) if index != query]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    predictions = [rival(grid) for grid in grids]
                    assert any(predictions[index] != expected[index] for index in demos), (
                        band, start, query, name,
                    )


def test_generated_outputs_match_real_racket_authority():
    grids = [gen.generate(151, index, difficulty=band)
             for band in ("easy", "medium", "hard") for index in range(8)]
    applied = Catalog().apply(TASK, grids, timeout=120)
    assert applied["rule_hash_matches_catalog"]
    assert all(item["valid_output"] and item["error"] is None for item in applied["results"])
    assert [item["output"] for item in applied["results"]] == [intended_output(grid) for grid in grids]


def test_three_object_authority_disagreement_remains_outside_selected_domain():
    # Preserve the prior audit's deliberate two-object domain boundary.
    fixture = [[0] * 9 for _ in range(6)]
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)):
        fixture[r][c] = 2
    for r, c in ((3, 5), (3, 6), (4, 5)):
        fixture[r][c] = 3
    fixture[5][8] = 4
    assert any("exactly two" in reason for reason in gen.self_check(fixture))


def test_semantic_probe_reads_public_apply_rule_hash_field():
    path = TASK_DIR / "workspace/probe_semantics.py"
    spec = importlib.util.spec_from_file_location("semantic_probe_under_test", path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)
    assert probe.executed_rule_hash({"executed_rule_hash": "abc123"}) == "abc123"


def test_retained_crop_canvas_counterexample_is_source_bound():
    import hashlib
    import json

    path = TASK_DIR / "counterexamples/crop_to_large.json"
    witness = json.loads(path.read_text())
    source_hash = hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()
    assert witness["generator_sha256"] == source_hash
    assert witness["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(witness["input"]) == []
    assert gen.CANONICAL_SHORTCUTS[witness["rival"]](witness["input"]) == witness["rival_output"]
    assert intended_output(witness["input"]) == witness["racket_output"]
    assert witness["racket_output"] != witness["rival_output"]
