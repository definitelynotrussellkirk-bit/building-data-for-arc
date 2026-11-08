"""Portable regressions for the top-row diagonal-ray generator."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "5d13a2fe59fc"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_5d13a2fe59fc", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK, root=find_root(__file__))


def intended_output(grid):
    """Independent mirror of the canonical down-right-ray rule."""
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for start_col, color in enumerate(grid[0]):
        if color == 0:
            continue
        row, col = 0, start_col
        while row < height and col < width:
            out[row][col] = color
            row += 1
            col += 1
    return out


def first_seed_per_color_rival(grid):
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()
    for start_col, color in enumerate(grid[0]):
        if color == 0 or color in seen:
            continue
        seen.add(color)
        row, col = 0, start_col
        while row < height and col < width:
            out[row][col] = color
            row += 1
            col += 1
    return out


def _labeled(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def test_pins_current_canonical_rule_hash():
    assert gen.RULE_HASH == "ba0a11187d3c"


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "controls",
    [
        {"grid_h": 5, "grid_w": 7, "seeds": 2, "color_pattern": "repeat"},
        {"grid_h": 10, "grid_w": 12, "seeds": 5, "color_pattern": "distinct"},
        {"grid_h": 8, "grid_w": 10, "seeds": 4, "color_pattern": "repeat"},
    ],
)
def test_every_documented_override_is_exact_and_observable(band, controls):
    grid = gen.generate(812, 17, difficulty=band, **controls)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == controls


@pytest.mark.parametrize(
    "kwargs",
    [
        {"misspelled": 1},
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 6},
        {"grid_w": 13},
        {"seeds": 1},
        {"seeds": 6},
        {"color_pattern": "monochrome"},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"seeds": "3"},
        {"color_pattern": 1},
    ],
)
def test_unknown_out_of_range_and_wrong_type_controls_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("bad_seed,bad_index", [(True, 0), (1.0, 0), (1, True), (1, -1)])
def test_seed_and_sample_index_are_strict(bad_seed, bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, bad_index)


def test_repeat_control_produces_a_real_shortcut_counterexample():
    grid = gen.generate(
        77,
        5,
        grid_h=6,
        grid_w=8,
        seeds=3,
        color_pattern="repeat",
    )
    colors = [value for value in grid[0] if value]
    counts = Counter(colors)
    assert sorted(counts.values()) == [1, 2]
    assert gen.SEMANTIC_WITNESSES["repeated_color_seeds"](grid) is True
    assert gen.SEMANTIC_RIVALS["first_seed_per_color"](grid) == first_seed_per_color_rival(grid)
    assert first_seed_per_color_rival(grid) != intended_output(grid)


def test_declared_shortcut_fits_every_canonical_demonstration():
    rival = gen.CANONICAL_SHORTCUTS["first_seed_per_color"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_draws_have_two_repeat_witnesses(band):
    for seed in range(8):
        for start in range(3):
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(3)]
            witness_count = sum(gen.SEMANTIC_WITNESSES["repeated_color_seeds"](grid) for grid in grids)
            assert witness_count >= 2, (band, seed, start, witness_count)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_all_four_pair_query_rotations_eliminate_the_named_rival(band):
    for seed in range(5):
        pairs = [_labeled(gen.generate(seed, offset, difficulty=band)) for offset in range(4)]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_validator_rejects_structure_destroying_inputs():
    invalid = [
        None,
        [],
        [[]],
        [[0] * 7 for _ in range(5)],
        [[1, 0, 2, 0, 0, 0, 0], [0, 0, 0, 3, 0, 0, 0]] + [[0] * 7 for _ in range(3)],
        [[True, 0, 2, 0, 0, 0, 0]] + [[0] * 7 for _ in range(4)],
        [[1, 0, 10, 0, 0, 0, 0]] + [[0] * 7 for _ in range(4)],
        [[1, 0, 0, 0, 0, 0, 0]] + [[0] * 7 for _ in range(4)],
    ]
    for grid in invalid:
        assert gen.self_check(grid), grid


def test_generation_is_deterministic_diverse_and_input_pure():
    seen = set()
    patterns = set()
    for index in range(30):
        grid = gen.generate(900 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        before = deepcopy(grid)
        assert grid == gen.generate(900 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        gen.rule_mirror(grid)
        gen.observe_overrides(grid)
        assert grid == before
        seen.add(repr(grid))
        patterns.add(gen.observe_overrides(grid)["color_pattern"])
    assert len(seen) >= 28
    assert patterns == {"distinct", "repeat"}


def test_retained_counterexample_matches_current_source_and_both_rules():
    path = HOME / "counterexamples" / "first_seed_per_color.json"
    record = json.loads(path.read_text())
    source_sha = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    assert record["generator_sha256"] == source_sha
    assert record["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(record["input"]) == []
    assert record["intended_output"] == intended_output(record["input"])
    assert record["rival_output"] == first_seed_per_color_rival(record["input"])
    assert record["intended_output"] != record["rival_output"]
