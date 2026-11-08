"""Focused semantic regressions for generator 6c88f7697696."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK_ID = "6c88f7697696"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs.extend(row.get("train", []))
                test = row.get("test", [])
                pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def test_canonical_inputs_are_owned_and_rule_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
    # The official test is the documented compatibility exception: transpose
    # and anti-transpose both explain A→B, but authority order selects transpose.
    observed = GEN.semantic_observables(pairs[-1]["input"])
    assert observed["canonical_ambiguity_exception"] is True
    assert observed["transform_candidate_count"] == 2
    assert observed["transform"] == "tr"
    assert GEN.TRANSFORM_PRECEDENCE[-2:] == ("tr", "atr")


def test_all_transform_implementations_are_distinct_on_asymmetric_grid():
    grid = [[1, 2, 0], [0, 3, 0], [4, 0, 5]]
    variants = {code: GEN._freeze(GEN._transform_grid(grid, code)) for code in GEN._TRANSFORM_ORDER}
    assert len(set(variants.values())) == 8
    assert variants["r3"] != variants["tr"]
    assert variants["atr"] != variants["tr"]


def test_exact_boundary_overrides_are_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for transform in GEN.TRANSFORMS:
            grid = GEN.generate(
                17,
                23,
                difficulty=band,
                transform=transform,
                source_color_count=3,
                a_cells=3,
                c_cells=7,
            )
            assert GEN.observe_overrides(grid) == {
                "transform": transform,
                "source_color_count": 3,
                "a_cells": 3,
                "c_cells": 7,
            }
            assert GEN.self_check(grid) == []


def test_default_schedule_covers_all_semantic_branches_per_band():
    for band in ("easy", "medium", "hard"):
        transforms = set()
        source_counts = set()
        palette_relations = set()
        distinct = set()
        for sample_index in range(42):
            grid = GEN.generate(101 + sample_index, sample_index, difficulty=band)
            observed = GEN.semantic_observables(grid)
            transforms.add(observed["transform"])
            source_counts.add(observed["source_color_count"])
            palette_relations.add(observed["palette_relation"])
            assert observed["transform_candidate_count"] == 1
            assert observed["a_orbit_size"] == 8
            assert observed["c_orbit_size"] == 8
            assert observed["transform_visible"]
            assert observed["recolor_visible"]
            distinct.add(GEN._freeze(grid))
        assert transforms == set(GEN.TRANSFORMS)
        assert source_counts == {1, 2, 3}
        assert palette_relations == {"disjoint", "permuted"}
        assert len(distinct) >= 40


def test_materialized_two_demo_schedule_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(0, 28, 3):
            demos = []
            for sample_index in (start, start + 1):
                grid = GEN.generate(31337, sample_index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(31337, start + 2, difficulty=band)
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []

    first = GEN.generate(9, 0, transform="fh", source_color_count=2)
    second = GEN.generate(10, 1, transform="fh", source_color_count=3)
    query_grid = GEN.generate(11, 2, transform="r1")
    reasons = GEN.lesson_identifiable(
        [
            {"input": first, "output": GEN.rule_mirror(first)},
            {"input": second, "output": GEN.rule_mirror(second)},
        ],
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    )
    assert any("fixed-transform shortcut" in reason for reason in reasons)


def test_self_check_rejects_targeted_structural_and_semantic_impostors():
    base = GEN.generate(41, 0, transform="r1", source_color_count=3, a_cells=5, c_cells=6)

    broken_divider = copy.deepcopy(base)
    broken_divider[1][3] = 0

    panel_eight = copy.deepcopy(base)
    panel_eight[0][0] = 8

    missing_query_color = copy.deepcopy(base)
    a, _, c = GEN._split_panels(missing_query_color)
    remove = next(value for row in c for value in row if value)
    for r in range(3):
        for col in range(8, 11):
            if missing_query_color[r][col] == remove:
                missing_query_color[r][col] = 0

    identity_transform = copy.deepcopy(base)
    a, _, _ = GEN._split_panels(identity_transform)
    for r in range(3):
        for c in range(3):
            identity_transform[r][4 + c] = a[r][c]

    ambiguous_a = [[0] * 11 for _ in range(3)]
    for r in range(3):
        ambiguous_a[r][3] = ambiguous_a[r][7] = 8
    # A support is diagonal-symmetric; B is its transpose with recolor.
    for r, c in ((0, 0), (1, 1), (2, 2)):
        ambiguous_a[r][c] = 1
        ambiguous_a[r][4 + c] = 2
        ambiguous_a[r][8 + ((c + 1) % 3)] = 1

    same_orbit_query = copy.deepcopy(base)
    a, _, _ = GEN._split_panels(same_orbit_query)
    for r in range(3):
        for c in range(3):
            same_orbit_query[r][8 + c] = a[r][c]

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    boolean_cell = copy.deepcopy(base)
    boolean_cell[0][0] = True

    for mutation in (
        broken_divider,
        panel_eight,
        missing_query_color,
        identity_transform,
        ambiguous_a,
        same_orbit_query,
        ragged,
        boolean_cell,
    ):
        assert GEN.self_check(mutation), mutation


def test_named_rivals_disagree_with_every_generated_truth():
    for sample_index in range(28):
        grid = GEN.generate(9191, sample_index)
        truth = GEN.rule_mirror(grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != truth


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 9
    assert GEN.generate(97, 103, difficulty="hard") == second


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="warm")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, source_color_count=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, a_cells=8)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, transform="id")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_rule_hash_matches_selected_canonical_authority():
    programs = set()
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    selected = next(iter(programs))
    expected = hashlib.sha256(" ".join(selected.split()).encode()).hexdigest()[:12]
    assert "Transpose" in selected
    assert "deliberately precedes anti-transpose" in selected
    assert selected.index("'transpose") < selected.index("'anti-transpose")
    assert GEN.RULE_HASH == expected == "09a64aa644b8"

    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/f7fa4dfa2903/H141__6c88f7697696.json"
        ).read_text(encoding="utf-8")
    )
    assert base["racket_target"]["target_code"] == selected
