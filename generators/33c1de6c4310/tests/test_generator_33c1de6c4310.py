from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "33c1de6c4310"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.33c1de6c4310.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def _divider(grid):
    return next(
        c
        for c in range(len(grid[0]))
        if all(row[c] == 9 for row in grid)
    )


def test_rule_hash_and_canonical_pairs():
    canonical = _canonical()
    expected_hash = hashlib.sha256(
        " ".join(canonical["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash
    for pair in canonical["train"] + canonical["test"]:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("texture", GEN.HELPFUL_TEXTURES)
def test_boundary_overrides_are_exact_and_valid(texture):
    grid = GEN.generate(
        1234,
        9,
        difficulty="easy",
        grid_h=5,
        panel_w=4,
        mask_components=4,
        src_colors=8,
        texture=texture,
    )
    assert GEN.self_check(grid) == []
    assert len(grid) == 5
    assert len(grid[0]) == 9
    assert GEN.observe_overrides(grid) == {
        "panel_w": 4,
        "mask_components": 4,
        "src_colors": 8,
    }


def test_determinism_fresh_returns_and_global_rng():
    state = random.getstate()
    kwargs = dict(
        difficulty="hard",
        grid_h=16,
        panel_w=14,
        mask_components=4,
        src_colors=8,
        texture="tall",
    )
    first = GEN.generate(9988, 77, **kwargs)
    second = GEN.generate(9988, 77, **kwargs)
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    saved = copy.deepcopy(second)
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(9988, 77, **kwargs) == saved


def test_self_check_rejects_targeted_impostors():
    grid = GEN.generate(777, 3, difficulty="medium")
    divider = _divider(grid)
    height = len(grid)
    mask = [
        (r, c)
        for r in range(height)
        for c in range(divider)
        if grid[r][c] != 0
    ]

    unequal = [row[:-1] for row in copy.deepcopy(grid)]
    zero_source = copy.deepcopy(grid)
    r, c = mask[0]
    zero_source[r][divider + 1 + c] = 0
    monochrome = copy.deepcopy(grid)
    color = monochrome[0][divider + 1]
    for r in range(height):
        for c in range(divider):
            monochrome[r][divider + 1 + c] = color
    full_mask = copy.deepcopy(grid)
    mask_color = next(
        value for row in full_mask for value in row if value not in (0, 9)
    )
    for r in range(height):
        for c in range(divider):
            full_mask[r][c] = mask_color
    single_cell = copy.deepcopy(grid)
    for r in range(height):
        for c in range(divider):
            single_cell[r][c] = 0
    single_cell[0][0] = mask_color
    second_divider = copy.deepcopy(grid)
    for r in range(height):
        second_divider[r][divider + 1] = 9
    row_major_prefix = copy.deepcopy(grid)
    for r in range(height):
        for c in range(divider):
            row_major_prefix[r][c] = 0
    for flat_index in range(min(divider + 2, height * divider - 2)):
        r, c = divmod(flat_index, divider)
        row_major_prefix[r][c] = mask_color

    impostors = {
        "unequal": unequal,
        "zero_source": zero_source,
        "monochrome": monochrome,
        "full_mask": full_mask,
        "single_cell": single_cell,
        "second_divider": second_divider,
        "row_major_prefix": row_major_prefix,
    }
    for name, impostor in impostors.items():
        assert GEN.self_check(impostor), name


def test_requested_component_and_palette_counts_across_bands():
    for band in ("easy", "medium", "hard"):
        for components in range(1, 5):
            for colors in (2, 5, 8):
                grid = GEN.generate(
                    9000 + components * 10 + colors,
                    5,
                    difficulty=band,
                    mask_components=components,
                    src_colors=colors,
                )
                observed = GEN.observe_overrides(grid)
                assert observed["mask_components"] == components
                assert observed["src_colors"] == colors
                assert GEN.self_check(grid) == []


def test_palette_regression_seed_7_easy_one_component_eight_colors():
    grid = GEN.generate(7, 7, difficulty="easy", mask_components=1, src_colors=8)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["src_colors"] == 8


def test_default_distribution_covers_connected_and_disconnected_masks():
    """Cheap regression for the baseline's all-single-component distribution."""
    counts_by_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = {
            GEN.observe_overrides(
                GEN.generate(30000 + band_index * 1000 + seed, seed, difficulty=band)
            )["mask_components"]
            for seed in range(80)
        }
        counts_by_band[band] = counts

    assert counts_by_band["easy"] == {1, 2}
    assert counts_by_band["medium"] == {2, 3}
    assert counts_by_band["hard"] == {3, 4}
