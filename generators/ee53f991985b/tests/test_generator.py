"""Portable regressions for the ee53f991985b teaching/distribution repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "ee53f991985b"
RULE_HASH = "638445812e80"
ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = ("easy", "medium", "hard")


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    groups = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            groups.append((color, set(cells)))
    return groups


def bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def is_outline(cells):
    row1, col1, row2, col2 = bbox(cells)
    border = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    return cells == border


def oracle(grid, *, fill_every_bbox=False):
    output = deepcopy(grid)
    for color, cells in components(grid):
        if fill_every_bbox or is_outline(cells):
            row1, col1, row2, col2 = bbox(cells)
            for row in range(row1, row2 + 1):
                for col in range(col1, col2 + 1):
                    output[row][col] = color
    return output


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def labeled(grid):
    return {"input": deepcopy(grid), "output": oracle(grid)}


def test_public_contract_is_small_truthful_and_rule_pinned():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == RULE_HASH
    assert gen.RULE_HASH == Catalog(ROOT).describe(TASK_ID)["rule_hash"]
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert callable(gen.observe_overrides)
    assert callable(gen.rule_mirror)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.lesson_identifiable)
    assert set(gen.SEMANTIC_RIVALS) == {"fill_every_component_bbox"}
    assert set(gen.CANONICAL_SHORTCUTS) == {"fill_every_component_bbox"}


@pytest.mark.parametrize("pair", PAIRS, ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    frozen = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == frozen


@pytest.mark.parametrize("band", (None, *BANDS))
@pytest.mark.parametrize("requested", ((7, 10), (10, 12), (24, 28)))
def test_exact_dimension_controls_round_trip_in_every_band(band, requested):
    height, width = requested
    grid = gen.generate(1701, 23, difficulty=band, grid_h=height, grid_w=width)
    assert gen.observe_overrides(grid) == {"grid_h": height, "grid_w": width}
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["broken_frame"](grid) is True
    assert grid == gen.generate(1701, 23, difficulty=band, grid_h=height, grid_w=width)


def test_unknown_removed_and_invalid_controls_fail_closed():
    for key, value in (
        ("typo_axis", 1),
        ("n_frames", 2),
        ("n_neg", 1),
        ("palette_kind", "warm"),
        ("texture", "broken_frame"),
    ):
        with pytest.raises((TypeError, ValueError), match=key):
            gen.generate(0, 0, **{key: value})
    for key, value in (
        ("grid_h", True),
        ("grid_h", 6),
        ("grid_h", 25),
        ("grid_w", 9),
        ("grid_w", 29),
        ("grid_w", 12.0),
    ):
        with pytest.raises((TypeError, ValueError), match=key):
            gen.generate(0, 0, **{key: value})


def test_profile_floor_population_has_exact_and_envelope_support_in_every_band():
    canonical_profiles = {profile(pair["input"]) for pair in PAIRS}
    heights = [item[0] for item in canonical_profiles]
    widths = [item[1] for item in canonical_profiles]
    palettes = [item[2] for item in canonical_profiles]
    envelope = (
        (min(heights), max(heights)),
        (min(widths), max(widths)),
        (min(palettes), max(palettes)),
    )
    total_exact = 0
    total_envelope = 0
    for band in BANDS:
        band_exact = 0
        for index in range(20):
            seed = pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            current = profile(grid)
            band_exact += current in canonical_profiles
            total_envelope += (
                envelope[0][0] <= current[0] <= envelope[0][1]
                and envelope[1][0] <= current[1] <= envelope[1][1]
                and envelope[2][0] <= current[2] <= envelope[2][1]
            )
        assert band_exact >= 1
        total_exact += band_exact
    assert total_exact >= 3
    assert total_envelope >= 15


def test_broken_frame_counterexample_refutes_bbox_shortcut():
    fixture_path = ROOT / "generators" / TASK_ID / "counterexamples" / "broken-frame-shortcut.json"
    fixture = json.loads(fixture_path.read_text())
    grid = fixture["input"]
    intended = oracle(grid)
    shortcut = oracle(grid, fill_every_bbox=True)
    assert fixture["generator_sha256"] == SOURCE_SHA256
    assert fixture["rule_hash"] == RULE_HASH
    assert fixture["intended_output"] == intended
    assert fixture["rival_output"] == shortcut
    assert gen.self_check(grid) == []
    assert intended != shortcut
    assert gen.rule_mirror(grid) == intended
    assert gen.SEMANTIC_RIVALS["fill_every_component_bbox"](grid) == shortcut
    assert gen.SEMANTIC_WITNESSES["broken_frame"](grid) is True


def test_declared_shortcut_fits_every_canonical_pair_but_not_generated_inputs():
    rival = gen.CANONICAL_SHORTCUTS["fill_every_component_bbox"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for band in BANDS:
        for index in range(24):
            grid = gen.generate(9000 + index, 7 * index + 3, difficulty=band)
            assert gen.SEMANTIC_WITNESSES["broken_frame"](grid) is True
            assert rival(grid) != oracle(grid)


@pytest.mark.parametrize("band", BANDS)
def test_every_consecutive_lesson_and_rotation_refutes_declared_competitor(band):
    for start in range(12):
        pairs = [labeled(gen.generate(1200 + start, start + offset, difficulty=band))
                 for offset in range(gen.EXAMPLES_NEEDED + 1)]
        for held_out in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []
