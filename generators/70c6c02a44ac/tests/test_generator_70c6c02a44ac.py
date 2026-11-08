"""Focused regression tests for glyph-broadcast generator 70c6c02a44ac."""
from __future__ import annotations

import importlib
import itertools
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.70c6c02a44ac.generator"
)
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = (
    ROOT
    / "data/base/solutions/banks/3c7b85b8eeb1/E41__70c6c02a44ac.json"
)
AXIS_NAMES = (
    "grid_h",
    "grid_w",
    "shape_family",
    "n_anchors",
    "source_band",
    "anchor_mode",
)


def _canonical_pairs():
    record = json.loads(AUTHORITY.read_text())
    pairs = list(record["visible_context"]["train"])
    for test_input, expected in zip(
        record["visible_context"]["test_inputs"],
        record["verification"]["expected_test_outputs"],
    ):
        pairs.append({"input": test_input["input"], "output": expected})
    return pairs


def _pair(seed: int, sample_index: int, band: str = "medium"):
    grid = MODULE.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": MODULE._solve_grid(grid)}


def test_canonical_pairs_are_accepted_and_solved_including_clipped_copy():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    profiles = []
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE._solve_grid(pair["input"]) == pair["output"]
        profiles.append(MODULE._analyze_grid(pair["input"])[0]["edge_profile"])
    assert profiles.count("clipped") == 1
    assert profiles.count("inside") == 4


def test_every_exact_axis_override_is_observable_in_both_edge_profiles():
    values = itertools.product(
        range(8, 11),
        range(10, 13),
        MODULE.SHAPE_FAMILIES,
        range(2, 4),
        MODULE.SOURCE_BANDS,
        MODULE.ANCHOR_MODES,
    )
    checked = 0
    for checked, axis_values in enumerate(values, start=1):
        overrides = dict(zip(AXIS_NAMES, axis_values))
        for sample_index in (0, 1):  # clipped then inside for the 3-step schedule
            grid = MODULE.generate(
                100_000 + checked,
                sample_index,
                difficulty="easy",
                **overrides,
            )
            assert MODULE.self_check(grid) == []
            assert MODULE.observe_overrides(grid) == overrides
            info = MODULE._analyze_grid(grid)[0]
            assert info["edge_profile"] == MODULE.schedule_profile(
                0, sample_index
            )
    assert checked == 720


def test_unknown_and_out_of_range_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="outside"):
        MODULE.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="not in options"):
        MODULE.generate(1, 0, anchor_mode="hidden")


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(99173)
    state = random.getstate()
    first = MODULE.generate(84, 5, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(84, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    replay = MODULE.generate(84, 5, difficulty="hard")
    assert replay == second


def test_self_check_rejects_targeted_rule_hiding_mutations():
    base = MODULE.generate(
        77,
        1,
        difficulty="medium",
        shape_family="hook6",
        n_anchors=3,
        source_band="top",
        anchor_mode="separate",
    )
    assert MODULE.self_check(base) == []

    no_source = deepcopy(base)
    for row in no_source:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    assert any("missing red" in reason for reason in MODULE.self_check(no_source))

    one_anchor = deepcopy(base)
    kept = False
    for row in one_anchor:
        for c, value in enumerate(row):
            if value == 3:
                if kept:
                    row[c] = 0
                else:
                    kept = True
    assert any("expected 2 or 3" in reason for reason in MODULE.self_check(one_anchor))

    unsupported_color = deepcopy(base)
    unsupported_color[-1][-1] = 8
    assert any("unsupported color" in reason for reason in MODULE.self_check(unsupported_color))

    solid_bbox = deepcopy(base)
    info = MODULE._analyze_grid(base)[0]
    rows = [r for r, _ in info["source_cells"]]
    cols = [c for _, c in info["source_cells"]]
    for r in range(min(rows), max(rows) + 1):
        for c in range(min(cols), max(cols) + 1):
            solid_bbox[r][c] = 2
    findings = MODULE.self_check(solid_bbox)
    assert any("solid rectangular" in reason for reason in findings)

    source_at_origin = deepcopy(base)
    for row in source_at_origin:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    for dr, dc in MODULE.SHAPES["hook6"]:
        source_at_origin[dr][dc] = 2
    findings = MODULE.self_check(source_at_origin)
    assert any("grid origin" in reason for reason in findings)


def test_each_anchor_contributes_a_unique_visible_output_cell():
    for sample_index in range(18):
        grid = MODULE.generate(500 + sample_index, sample_index, difficulty="hard")
        info = MODULE._analyze_grid(grid)[0]
        for index, cells in enumerate(info["projected"]):
            others = set().union(
                *(other for j, other in enumerate(info["projected"]) if j != index)
            )
            assert cells - others


def test_three_consecutive_demos_refute_every_named_competitor():
    for start in range(0, 15):
        demos = [_pair(3301, start + offset) for offset in range(3)]
        query = _pair(3301, start + 3)
        assert MODULE.lesson_identifiable(demos, query) == []
        for name, rival in MODULE.LESSON_COMPETITORS.items():
            assert any(
                rival(demo["input"]) != demo["output"] for demo in demos
            ), name


def test_rule_hash_matches_assigned_canonical_authority():
    assert MODULE.RULE_HASH == "53ceb2a607c4"
