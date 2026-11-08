from __future__ import annotations

import copy
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.36343a80035c.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID)]


def test_canonical_inputs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._true_output(pair["input"]) == pair["output"]


def test_canonical_same_color_vertical_sandwich_shortcut_fits_all_pairs():
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen._same_color_vertical_sandwich_output(pair["input"]) == pair["output"]


def test_each_scheduled_profile_refutes_named_shortcuts():
    for sample_index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(731, sample_index, difficulty="medium")
        assert gen.observe_overrides(grid)["scene_profile"] == profile
        answer = gen._true_output(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if name in gen.ANCHOR_COMPATIBLE_RIVALS and sample_index == 0:
                continue  # These new rivals are killed by the other lesson slots.
            assert rival(grid) != answer, (profile, name)


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    for profile in gen.SCENE_PROFILES:
        for palette_kind in gen.PALETTE_KINDS:
            grid = gen.generate(
                91,
                0,
                difficulty="hard",
                grid_h=14,
                grid_w=9,
                scene_profile=profile,
                palette_kind=palette_kind,
            )
            assert (len(grid), len(grid[0])) == (14, 9)
            assert gen.observe_overrides(grid) == {
                "scene_profile": profile,
                "palette_kind": palette_kind,
            }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="x")


def test_self_check_rejects_four_structural_impostors():
    all_zero = [[0] * 9 for _ in range(9)]
    solid = [[0] * 9 for _ in range(9)]
    for r in range(2, 5):
        for c in range(2, 5):
            solid[r][c] = 4
    open_frame = [[0] * 9 for _ in range(9)]
    gen._draw_frame(open_frame, 2, 2, 4, 4, 4)
    open_frame[3][2] = 0
    isolated_wall = [[0] * 9 for _ in range(9)]
    isolated_wall[4][4] = 7

    for impostor in (all_zero, solid, open_frame, isolated_wall):
        assert gen.self_check(impostor), impostor


def test_generation_is_deterministic_fresh_and_preserves_global_rng():
    random.seed(20260727)
    before = random.getstate()
    first = gen.generate(44, 3, difficulty="hard")
    after = random.getstate()
    second = gen.generate(44, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after


def test_self_check_is_input_pure():
    for grid in _canonical_inputs() + [gen.generate(12, i) for i in range(4)]:
        frozen = copy.deepcopy(grid)
        gen.self_check(grid)
        assert grid == frozen


def _eight_neighbor_output(grid):
    """Independent deliberately wrong 8-neighbor border-reachability probe."""
    h, w = len(grid), len(grid[0])
    outside = {(r, c) for r in range(h) for c in range(w)
               if grid[r][c] == 0 and (r in (0, h - 1) or c in (0, w - 1))}
    pending = list(outside)
    while pending:
        r, c = pending.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0
                        and (nr, nc) not in outside):
                    outside.add((nr, nc))
                    pending.append((nr, nc))
    return [[8 if grid[r][c] == 0 and (r, c) not in outside else 0
             for c in range(w)] for r in range(h)]


def _is_rectangle(region):
    rows, cols = zip(*region)
    return len(region) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


@pytest.mark.parametrize('sample_index', [1, 2, 3])
def test_non_anchor_profiles_teach_nonrectangular_holes(sample_index):
    for seed in range(8):
        grid = gen.generate(seed, sample_index, difficulty='hard')
        assert any(not _is_rectangle(region) for region in gen._hole_regions(grid)), (
            seed, sample_index, 'every hole is rectangular')


@pytest.mark.parametrize('sample_index', range(4))
def test_every_profile_distinguishes_four_from_eight_connectivity(sample_index):
    for seed in range(8):
        grid = gen.generate(seed, sample_index, difficulty='medium')
        assert _eight_neighbor_output(grid) != gen._true_output(grid), (seed, sample_index)


def test_multiple_nonrectangular_tetromino_shapes_are_sampled():
    shapes = set()
    for seed in range(40):
        grid = gen.generate(seed, 2, difficulty='hard')
        for region in gen._hole_regions(grid):
            if len(region) != 4:
                continue
            variants = []
            for swap in (False, True):
                for sr in (-1, 1):
                    for sc in (-1, 1):
                        cells = [(sr * (c if swap else r), sc * (r if swap else c))
                                 for r, c in region]
                        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
                        variants.append(tuple(sorted((r-r0, c-c0) for r, c in cells)))
            shapes.add(min(variants))
    assert len(shapes) >= 3, shapes
