"""Task-local regressions; runnable from source or a relocated runtime."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
# Source checkout and staged legacy layout, without predecessor imports.
for parent in HOME.parents:
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT / "shared/runtime"))
        CANONICAL = ROOT / "shared/data/canonical/puzzles.jsonl"
        break
    if (parent / "puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT))
        CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
        break
else:
    raise RuntimeError("No independent runtime found")
spec = importlib.util.spec_from_file_location("reviewed_5ccdbe078da6", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def groups(grid):
    out = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                out.setdefault(color, []).append((r, c))
    return out


def kind(cells):
    (r, c), (s, d) = sorted(cells)
    return "horizontal" if r == s else "vertical" if c == d else "down_right" if c < d else "down_left"


def canonical_pairs():
    for line in CANONICAL.open():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row["train"] + row["test"]
    raise AssertionError("Task missing")


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 0]], [[True, 0], [0, 1]],
    [[10, 0], [0, 10]], [[-1, 0], [0, -1]], [[1.0, 0], [0, 1.0]],
    [[0]*4 for _ in range(4)], [[1, 0], [0, 0]], [[1, 1], [1, 0]]])
def test_bad_grids_rejected_without_crashing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(4, 5), (10, 12)])
def test_dimension_and_pair_overrides_all_bands(band, shape):
    h, w = shape
    for count in (1, 2, 3):
        grid = gen.generate(9, 11, difficulty=band, grid_h=h, grid_w=w, n_pairs=count)
        assert (len(grid), len(grid[0])) == shape
        assert len(groups(grid)) == count
        assert not gen.self_check(grid)


@pytest.mark.parametrize("pair_kind", ["horizontal", "vertical", "down_right", "down_left"])
def test_pair_kind_is_real(pair_kind):
    for seed in range(12):
        grid = gen.generate(seed, 7, pair_kind=pair_kind, n_pairs=3)
        assert {kind(cells) for cells in groups(grid).values()} == {pair_kind}
        assert not gen.self_check(grid)


def test_unknown_and_removed_fake_axes_rejected():
    for key in ("typo_axis", "palette_size", "n_distinct_colors", "position_bias", "density", "texture"):
        with pytest.raises(TypeError, match=key):
            gen.generate(0, 0, **{key: 1})


@pytest.mark.parametrize("overrides", [{"grid_h": 3}, {"grid_h": 11}, {"grid_w": 4},
    {"grid_w": 13}, {"n_pairs": 0}, {"n_pairs": 4}, {"n_pairs": True},
    {"grid_h": 5.5}, {"grid_w": "7"}, {"pair_kind": "diagonalish"}, {"palette_kind": "bad"}])
def test_invalid_override_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(0, 0, **overrides)


def test_palette_kind_changes_support():
    palettes = {"default": set(range(1,10)), "warm": {2,4,6,9}, "cool": {1,3,5,8}, "varied": {1,2,7,8,9}}
    for name, support in palettes.items():
        for seed in range(20):
            assert set(groups(gen.generate(seed, 3, palette_kind=name))) <= support


def test_rule_mirror_matches_all_canonical_pairs():
    for pair in canonical_pairs():
        assert not gen.self_check(pair["input"])
        assert not gen.strict_canonical_like(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_reading_order_overwrites_even_original_markers():
    grid = [[0]*5 for _ in range(4)]
    grid[0][0] = grid[3][2] = 2
    grid[1][1] = grid[3][4] = 8
    output = gen.rule_mirror(grid)
    assert output[3][2] == 8
    assert output[1][2] == 8
    assert gen.rival_numeric_descending(grid)[3][2] == 2
    assert gen.rival_keep_markers(grid)[3][2] == 2


def test_nonpair_colors_preserved_by_mirror_but_not_training_domain():
    grid = [[0]*6 for _ in range(5)]
    grid[0][0] = grid[3][3] = 2
    grid[1][3] = 4
    result = gen.rule_mirror(grid)
    assert result[1][3] == 4
    assert gen.self_check(grid)


def test_default_support_and_determinism():
    found = set()
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    seen = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(100):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert grid == gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert not gen.self_check(grid)
            original = copy.deepcopy(grid)
            assert gen.rule_mirror(grid) != grid
            assert grid == original
            found.update(kind(cells) for cells in groups(grid).values())
            seen.add(json.dumps(grid))
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    hits[name] += 1
                    assert any(gen.SEMANTIC_RIVALS[r](grid) != gen.rule_mirror(grid)
                               for r in gen.WITNESS_RIVALS[name])
    assert found == {"horizontal", "vertical", "down_right", "down_left"}
    assert len(seen) >= 290
    assert all(hits.values()), hits


def test_canonical_shortcut_really_fits_demonstrations():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
