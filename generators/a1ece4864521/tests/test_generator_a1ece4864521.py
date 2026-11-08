from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generator_a1ece4864521_under_test", HOME / "generator.py")
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _repeat(tile, height=15, width=15):
    return [[tile[r % 5][c % 5] for c in range(width)] for r in range(height)]


def test_canonical_like_repeated_and_binary_anomalies_are_valid():
    grid = _repeat(gen._TILE)
    # The selected ARC task contains repeated colors and 8-valued anomalies
    # replacing inferred zeros in the same modulo-5 class.
    for row, col, value in ((0, 0, 8), (0, 5, 8), (5, 0, 4), (5, 5, 4)):
        grid[row][col] = value
    snapshot = copy.deepcopy(grid)
    assert gen.self_check(grid) == []
    output = gen.rule_mirror(grid)
    assert grid == snapshot
    assert output != grid
    assert len(output) == len(grid) and len(output[0]) == len(grid[0])


def test_declared_controls_are_exact_and_unknown_overrides_reject():
    grid = gen.generate(
        914,
        7,
        difficulty="hard",
        height=30,
        width=30,
        zero_count=13,
        anomaly_count=7,
        anomaly_mode="mixed",
    )
    facts = gen._analyze(grid)
    assert facts["errors"] == []
    assert facts["height"] == 30
    assert facts["width"] == 30
    assert facts["zero_count"] == 13
    assert facts["anomaly_count"] == 7
    assert facts["anomaly_mode"] == "mixed"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)


def test_generation_is_deterministic_fresh_pure_and_varies_the_inferred_tile():
    before = random.getstate()
    first = gen.generate(771, 19, difficulty="medium")
    assert random.getstate() == before
    second = gen.generate(771, 19, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert gen.self_check(first) == []
    frozen = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(771, 19, difficulty="medium") == frozen

    tiles = set()
    for seed in range(24):
        grid = gen.generate(seed, seed + 3, difficulty="medium")
        facts = gen._analyze(grid)
        assert facts["errors"] == []
        tiles.add(tuple(tuple(row) for row in facts["tile"]))
    assert len(tiles) >= 16


def test_rule_mirror_matches_analyzed_clean_then_fill_semantics():
    for mode in ("colored", "binary", "mixed"):
        grid = gen.generate(
            300 + len(mode),
            8,
            difficulty="hard",
            anomaly_mode=mode,
            anomaly_count=6 if mode == "mixed" else 5,
        )
        facts = gen._analyze(grid)
        assert facts["errors"] == []
        output = gen.rule_mirror(grid)
        assert len(output) == facts["height"]
        assert len(output[0]) == facts["width"]
        # Every non-clean output color is attributable to a row-major anomaly.
        allowed = {0, 8, *(a[2] for a in facts["anomalies"] if a[2] not in (0, 8))}
        assert set(cell for row in output for cell in row) <= allowed
