from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.ddaee6c28dd7 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        if '"task_id": "ddaee6c28dd7"' not in line:
            continue
        row = json.loads(line)
        return [pair["input"] for pair in row["train"]] + [row["test"]["input"]]
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_pass_structural_self_check():
    inputs = _canonical_inputs()
    assert len(inputs) == 3
    assert [gen.self_check(grid) for grid in inputs] == [[], [], []]


def test_declared_single_axis_boundaries_are_exact_and_observable():
    cases = [
        {"height": 8},
        {"height": 16},
        {"width": 11},
        {"width": 20},
        {"distractor_count": 1},
        {"distractor_count": 4},
        {"winner_w": 4},
        {"winner_w": 8},
        {"winner_h": 1},
        {"winner_h": 4},
        {"winner_color": 1},
        {"winner_color": 9},
        {"winner_profile": "bar"},
        {"winner_profile": "path"},
        {"winner_profile": "frame"},
        {"winner_profile": "solid"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(7000 + index, index, difficulty="easy", **overrides)
        observed = gen.observe_overrides(grid)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        for name, value in overrides.items():
            assert observed[name] == value


def test_incompatible_exact_axes_reject_loudly():
    with pytest.raises(ValueError, match="incompatible overrides"):
        gen.generate(
            1,
            1,
            difficulty="medium",
            winner_profile="bar",
            winner_h=4,
        )
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, texture="warm")
    with pytest.raises(ValueError):
        gen.generate(1, 1, winner_color=8)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(1947)
    before = random.getstate()
    first = gen.generate(12345, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(12345, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    changed = copy.deepcopy(first)
    changed[0][0] = (changed[0][0] + 1) % 10
    assert second != changed


def test_rule_mirror_is_exact_crop_recolor_of_unique_widest_component():
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(90000 + index, index, difficulty=band)
            sig = gen.semantic_signature(grid)
            output = gen.rule_mirror(grid)
            assert len(output) == sig["winner_h"]
            assert len(output[0]) == sig["winner_w"]
            assert {value for row in output for value in row} <= {0, 8}
            assert sum(value == 8 for row in output for value in row) == sig["winner_area"]


def test_declared_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), f"self_check accepted impostor {name}"


def test_ordinary_distribution_rebuts_size_area_color_and_position_shortcuts():
    profiles = set()
    colors = set()
    positions = set()
    output_shapes = set()
    masks = set()
    area_relations = set()
    taller = 0
    border = 0
    total = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(40):
            grid = gen.generate(120000 + band_index * 1000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            sig = gen.semantic_signature(grid)
            profiles.add(sig["winner_profile"])
            colors.add(sig["winner_color"])
            positions.add((band, sig["winner_top_left"]))
            output_shapes.add((sig["winner_h"], sig["winner_w"]))
            masks.add(sig["winner_mask"])
            area_relations.add(sig["area_relation"])
            taller += int(sig["has_taller_distractor"])
            border += int(sig["winner_touches_border"])
            total += 1
    assert profiles == set(gen.WINNER_PROFILES)
    assert len(colors) >= 6
    assert len(positions) >= 30
    assert len(output_shapes) >= 10
    assert len(masks) >= 25
    assert "distractor_larger" in area_relations
    assert "winner_largest" in area_relations
    assert taller >= total // 3
    assert 0 < border < total
