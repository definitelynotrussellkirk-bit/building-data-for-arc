"""Focused regression tests for the fdb8815ba528 generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import RIVALS, canonical_pairs, components, load_generator, observe, oracle

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned():
    assert gen.RULE_HASH == "001f318153f4"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_inputs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_all_exact_axes_are_observable_in_every_band(band):
    requested = {
        "scene_profile": "canonical_7x8",
        "n_blobs": 4,
        "color_relation": "one_repeat",
        "edge_mode": "touching",
        "palette_kind": "mixed",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert observe(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"scene_profile": "unknown"},
        {"n_blobs": 1},
        {"n_blobs": 5},
        {"n_blobs": True},
        {"color_relation": "all_same"},
        {"edge_mode": "center"},
        {"palette_kind": "default"},
    ],
)
def test_invalid_overrides_fail_loudly(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("index", range(24))
def test_default_generation_is_deterministic_valid_and_nontrivial(index):
    grid = gen.generate(9127, index, difficulty=("easy", "medium", "hard")[index % 3])
    assert grid == gen.generate(9127, index, difficulty=("easy", "medium", "hard")[index % 3])
    assert gen.self_check(grid) == []
    out = oracle(grid)
    assert out == gen.rule_mirror(grid)
    assert out != grid
    assert any(a == 0 and b != 0 for row_a, row_b in zip(grid, out) for a, b in zip(row_a, row_b))


@pytest.mark.parametrize("start", range(8))
def test_every_four_consecutive_demos_refute_all_declared_competitors(start):
    demos = []
    for index in range(start, start + 4):
        grid = gen.generate(4301, index, difficulty="medium")
        demos.append({"input": grid, "output": oracle(grid)})
    query_grid = gen.generate(4301, start + 4, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid, "output": oracle(query_grid)}) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_repeated_colour_and_connectivity_counterexamples_are_real():
    grid = gen.generate(
        73,
        3,
        scene_profile="canonical_8x10",
        n_blobs=3,
        color_relation="one_repeat",
        edge_mode="touching",
        palette_kind="low",
    )
    found = components(grid)
    assert len({component["color"] for component in found}) == 2
    expected = oracle(grid)
    for name in ("one_bbox_per_color", "same_color_8_connected", "color_blind_4_connected"):
        assert RIVALS[name](grid) != expected
        assert gen.SEMANTIC_RIVALS[name](grid) == RIVALS[name](grid)


def test_interior_source_cell_is_erased_and_solid_fill_is_wrong():
    grid = gen.generate(
        91,
        3,
        scene_profile="canonical_8x10",
        n_blobs=3,
        color_relation="one_repeat",
        edge_mode="interior",
        palette_kind="mixed",
    )
    expected = oracle(grid)
    assert any(a != 0 and b == 0 for row_a, row_b in zip(grid, expected) for a, b in zip(row_a, row_b))
    assert RIVALS["solid_bbox"](grid) != expected
    assert RIVALS["preserve_source"](grid) != expected


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_rule_and_rivals_do_not_mutate_input():
    grid = gen.generate(100, 3)
    frozen = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == frozen


def test_retained_training_shortcut_counterexample_is_authority_bound():
    import hashlib
    import json

    path = HOME / "counterexamples" / "current-shortcut" / "question_training_shortcut.json"
    evidence = json.loads(path.read_text())
    grid = evidence["input"]
    expected = evidence["expected_output_independent_oracle"]
    assert evidence["canonical_racket"]["matches_independent_oracle"] is True
    assert evidence["canonical_racket"]["executed_rule_hash"] == gen.RULE_HASH
    assert oracle(grid) == expected == gen.rule_mirror(grid)
    assert gen.self_check(grid, meta={"overrides": evidence["overrides"]}) == []
    for name in ("one_bbox_per_color", "same_color_8_connected", "color_blind_4_connected"):
        retained = evidence["rivals"][name]
        assert retained["output"] == RIVALS[name](grid)
        assert retained["output"] != expected
        assert retained["diff_from_expected"]
    assert evidence["generator_sha256"] == hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
