"""Behavioral regressions for transform inference and source-bound sampling.

Expected transforms use independent NumPy operations and literal canonical
answers. These tests work in both the source library and copied task runtimes.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "1a2afa3c0d4b"
ROOT = find_root(__file__)
SOURCES = [ROOT / "generators" / TASK / "generator.py",
           ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"]
SOURCE = next(p for p in SOURCES if p.is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_transform_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")


def independent_transform(panel, code):
    a = np.array(panel)
    operations = {
        "id": lambda: a.copy(), "r1": lambda: np.rot90(a, -1),
        "r2": lambda: np.rot90(a, 2), "r3": lambda: np.rot90(a, 1),
        "fh": lambda: np.fliplr(a), "fv": lambda: np.flipud(a),
        "tr": lambda: a.T, "atr": lambda: np.rot90(a.T, 2),
    }
    return operations[code]().tolist()


def panels(grid):
    s = len(grid) - 1
    return [[row[k * (s + 1):k * (s + 1) + s] for row in grid[1:]]
            for k in range(3)]


def key(grid):
    return tuple(tuple(row) for row in grid)


def mask(grid):
    return [[int(v != 0) for v in row] for row in grid]


@pytest.mark.parametrize("code", CODES)
def test_transform_coordinates_match_independent_operations(code):
    # A wrong r3/atr branch cannot hide behind the generator's own inverse.
    grid = [[1, 2, 3], [4, 5, 6]]
    assert GEN._xform_grid(grid, code) == independent_transform(grid, code)


@pytest.mark.parametrize("code", CODES)
def test_requested_transform_is_realized_in_b(code):
    grid = GEN.generate(271, 5, panel_side=4, transform=code)
    a, b, _ = panels(grid)
    assert b == independent_transform(a, code)
    matches = [c for c in CODES if independent_transform(a, c) == b]
    assert matches == [code]


def test_random_patterns_do_not_collapse_to_fixed_fallback():
    shapes = {key(mask(panels(GEN.generate(seed, 0, panel_side=4))[0]))
              for seed in range(32)}
    assert len(shapes) >= 12, f"Only {len(shapes)} A support patterns in 32 draws"


def test_canonical_pairs_remain_accepted():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("bad", [[], [[1, 0, 0]], [[1], [0, 0]],
                                 [[True, 0], [0, 0]], [[1.5, 0], [0, 0]]])
def test_validator_rejects_malformed_grids_without_crashing(bad):
    assert GEN.self_check(bad)


def test_validator_rejects_a_body_with_no_exact_a_to_b_transform():
    grid = GEN.generate(8, 2, panel_side=4)
    a, b, _ = panels(grid)
    # Erasing B preserves the old superficial separator/header checks.
    for row in grid[1:]:
        row[5:9] = [0] * 4
    assert any(any(row) for row in a)
    assert GEN.self_check(grid)


def test_negative_metadata_cannot_bypass_missing_header():
    grid = GEN.generate(9, 0, panel_side=4)
    grid[0] = [0] * len(grid[0])
    assert GEN.self_check(grid, meta={"texture": "no_header"})


def test_lawful_header_can_follow_leading_zeros_and_have_color_eight():
    grid = GEN.generate(19, 0, panel_side=4)
    grid[0] = [0] * len(grid[0])
    grid[0][-1] = 8
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_retains_canonical_profile_support(band):
    grids = [GEN.generate(728 + i, i, difficulty=band) for i in range(20)]
    matches = [g for g in grids if (len(g), len(g[0])) == (5, 14)
               and len({v for row in g for v in row}) in (4, 5)]
    assert len(matches) >= 1


@pytest.mark.parametrize("position", ["first", "interior", "last"])
def test_header_position_control_is_observable(position):
    grid = GEN.generate(44, 3, header_position=position, header_color=8)
    col = next(i for i, v in enumerate(grid[0]) if v)
    if position == "first":
        assert col == 0
    elif position == "last":
        assert col == len(grid[0]) - 1
    else:
        assert 0 < col < len(grid[0]) - 1
    assert grid[0][col] == 8
    assert GEN.observe_overrides(grid)["header_position"] == position


def test_color_cue_requires_more_than_binary_occupancy():
    grid = GEN.generate(67, 1, a_mode="color", transform="r3", panel_side=4)
    a, b, c = panels(grid)
    assert mask(a) == mask(b)
    assert len({key(independent_transform(a, t)) for t in CODES}) == 8
    assert mask(independent_transform(c, "r3")) != mask(c)


def test_retained_binary_counterexample_uses_exact_colors():
    # Literal input/output retained in counterexamples/binary-transform.json;
    # the expected output was executed by the unchanged public Racket rule.
    grid = [[7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 8, 1, 1, 1, 8, 3, 0, 0],
            [1, 1, 1, 8, 2, 1, 1, 8, 3, 3, 0],
            [1, 2, 2, 8, 2, 1, 1, 8, 0, 4, 0]]
    expected = [[0, 7, 7], [7, 7, 0], [0, 0, 0]]
    assert GEN.self_check(grid) == []
    a, b, c = panels(grid)
    exact = [code for code in CODES if independent_transform(a, code) == b]
    assert exact == ["r1"]
    assert [[7 if v else 0 for v in row]
            for row in independent_transform(c, exact[0])] == expected
    assert [[7 if v else 0 for v in row] for row in c] != expected


def test_default_witness_headers_refute_last_minimum_and_maximum():
    for band in ("easy", "medium", "hard"):
        for i in (1, 3, 5, 7):
            grid = GEN.generate(104 + i, i, difficulty=band)
            colors = [v for v in grid[0] if v]
            assert len(colors) >= 3
            target = colors[0]
            assert min(colors) < target < max(colors)
            assert target != colors[-1]
            body_colors = {v for row in grid[1:] for v in row}
            assert not set(colors) & body_colors - {8}


def test_default_witness_headers_do_not_encode_target_as_median():
    # A three-color low/target/high header accidentally teaches median color.
    for band in ("easy", "medium", "hard"):
        for i in (1, 3, 5, 7):
            grid = GEN.generate(104 + i, i, difficulty=band)
            colors = sorted(v for v in grid[0] if v)
            target = next(v for v in grid[0] if v)
            assert target not in (colors[(len(colors) - 1) // 2], colors[len(colors) // 2])


def test_default_panels_use_coherent_color_regions():
    # Measure visible fragmentation independently, without importing a sampler
    # helper. Each nonzero color should form one connected region in a panel.
    for band in ("easy", "medium", "hard"):
        for index in range(16):
            grid = GEN.generate(901 + index, index, difficulty=band)
            for panel in panels(grid):
                cells = {(r, c) for r, row in enumerate(panel)
                         for c, value in enumerate(row) if value}
                regions = []
                while cells:
                    start = min(cells)
                    color = panel[start[0]][start[1]]
                    cells.remove(start)
                    todo = [start]
                    while todo:
                        r, c = todo.pop()
                        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                            if neighbor in cells and panel[neighbor[0]][neighbor[1]] == color:
                                cells.remove(neighbor)
                                todo.append(neighbor)
                    regions.append(color)
                assert len(regions) == len(set(regions)), (band, index, regions)


def test_unknown_and_removed_fake_overrides_fail_explicitly():
    for override in ({"typo_axis": 4}, {"palette_kind": "warm"}, {"texture": "cool"}):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **override)


def test_exact_numeric_overrides_reject_lossy_coercions():
    for override in ({"panel_side": 4.5}, {"panel_side": True},
                     {"header_color": 2.5}, {"header_color": False}):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **override)


def test_semantic_rivals_are_refuted_in_every_four_pair_rotation():
    # Each 4-pair window has two color-dependent witnesses, so holding either
    # out leaves a witness. This catches parity/schedule aliasing regressions.
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = []
            for i in range(start, start + 4):
                grid = GEN.generate(101, i, difficulty=band)
                a, b, c = panels(grid)
                code = next(t for t in CODES if independent_transform(a, t) == b)
                color = next(v for v in grid[0] if v)
                output = [[color if v else 0 for v in row]
                          for row in independent_transform(c, code)]
                pairs.append({"input": grid, "output": output})
            for holdout in range(4):
                demos = [p for i, p in enumerate(pairs) if i != holdout]
                query = pairs[holdout]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    survives = all(rival(p["input"]) == p["output"] for p in demos)
                    assert not (survives and rival(query["input"]) != query["output"]), (band, start, holdout, name)
