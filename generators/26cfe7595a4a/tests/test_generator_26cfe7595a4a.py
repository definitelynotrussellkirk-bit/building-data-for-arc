from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "generator.py"


def load():
    spec = importlib.util.spec_from_file_location("generator_26_under_test", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def colors(grid):
    return {v for row in grid for v in row if v}


def test_rule_hash_and_validator_match_repaired_domain() -> None:
    gen = load()
    assert gen.RULE_HASH == "a6ccad31118b"
    singleton = [[0] * 8 for _ in range(7)]
    singleton[3][4] = 5
    assert "at least two non-zero cells required" in gen.self_check(singleton)
    border = [[0] * 8 for _ in range(7)]
    border[0][2] = border[1][2] = 5
    assert any("border" in err for err in gen.self_check(border))
    assert gen.self_check(gen.generate(4, 0, difficulty="medium")) == []


def test_every_declared_control_changes_observable_content() -> None:
    gen = load()
    common = dict(grid_h=12, grid_w=13, palette_kind="varied",
                  color_count=3, density="compact", position_bias="near_top")
    small = gen.generate(23, 4, difficulty="medium", motif_size=2, **common)
    large = gen.generate(23, 4, difficulty="medium", motif_size=4, **common)
    sbb, lbb = bbox(small), bbox(large)
    assert (sbb[2] - sbb[0] + 1, sbb[3] - sbb[1] + 1) == (2, 2)
    assert (lbb[2] - lbb[0] + 1, lbb[3] - lbb[1] + 1) == (4, 4)
    one = gen.generate(23, 4, motif_size=4, color_count=1, **{k: v for k, v in common.items() if k != "color_count"})
    three = gen.generate(23, 4, motif_size=4, color_count=3, **{k: v for k, v in common.items() if k != "color_count"})
    assert len(colors(one)) == 1
    assert len(colors(three)) == 3
    sparse = gen.generate(23, 4, motif_size=4, density="sparse", **{k: v for k, v in common.items() if k != "density"})
    dense = gen.generate(23, 4, motif_size=4, density="dense", **{k: v for k, v in common.items() if k != "density"})
    assert sum(v != 0 for row in sparse for v in row) < sum(v != 0 for row in dense for v in row)
    top = gen.generate(23, 4, motif_size=3, position_bias="near_top", **{k: v for k, v in common.items() if k != "position_bias"})
    bottom = gen.generate(23, 4, motif_size=3, position_bias="near_bottom", **{k: v for k, v in common.items() if k != "position_bias"})
    assert bbox(top)[0] < bbox(bottom)[0]


def test_large_boundaries_and_strict_override_rejection() -> None:
    gen = load()
    grid = gen.generate(7, 2, difficulty="hard", grid_h=30, grid_w=30,
                        motif_size=4, palette_kind="cool", color_count=2,
                        density="dense", position_bias="center")
    assert (len(grid), len(grid[0])) == (30, 30)
    assert gen.self_check(grid) == []
    with pytest.raises(ValueError):
        gen.generate(0, 0, invented=3)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, color_count=False)
