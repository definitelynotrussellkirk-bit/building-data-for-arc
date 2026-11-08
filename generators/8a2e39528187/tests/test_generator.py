"""Regression tests for the area-rank curriculum of task 8a2e39528187."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
TASK = "8a2e39528187"


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_8a2e39528187", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_pairs():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                test = row.get("test", [])
                return row["train"] + (test if isinstance(test, list) else [test])
    raise AssertionError("canonical task row is missing")


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "76fcc8e7f591"


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_accepts_every_canonical_input_and_mirrors_canonical_output(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile",
    ["canonical_strict", "tie_break", "touching_colors", "rank_palette"],
)
def test_exact_profile_and_dimension_overrides_are_observable(band, profile):
    grid = GEN.generate(
        1701,
        19,
        difficulty=band,
        grid_h=9,
        grid_w=12,
        lesson_profile=profile,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 9,
        "grid_w": 12,
        "lesson_profile": profile,
    }


@pytest.mark.parametrize("start", range(12))
def test_every_four_example_window_covers_the_semantic_schedule(start):
    profiles = {
        GEN.schedule_profile(9001, start + offset, "medium")
        for offset in range(GEN.EXAMPLES_NEEDED)
    }
    assert profiles == set(GEN.SCHEDULE_PROFILES)

    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(9001, start + offset, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_touching_different_colors_are_distinct_objects_and_refute_color_blind_rival():
    grid = GEN.generate(73, 2, lesson_profile="touching_colors")
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["different_colors_touch"](grid)
    assert GEN.SEMANTIC_RIVALS["color_blind_components"](grid) != GEN.rule_mirror(grid)


def test_equal_area_objects_use_bbox_tie_break_and_refute_reverse_tie_rival():
    grid = GEN.generate(74, 1, lesson_profile="tie_break")
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["equal_area_bbox_tie"](grid)
    assert GEN.SEMANTIC_RIVALS["reverse_bbox_ties"](grid) != GEN.rule_mirror(grid)


def test_rank_palette_input_is_a_distractor_not_an_identity_mapping():
    grid = GEN.generate(75, 3, lesson_profile="rank_palette")
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["rank_palette_distractor"](grid)
    assert GEN.SEMANTIC_RIVALS["numeric_input_color_order"](grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_valid_and_semantically_complete(band):
    profiles = set()
    inputs = set()
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(96):
        grid = GEN.generate(5100 + index, index * 7 + 3, difficulty=band)
        assert grid == GEN.generate(5100 + index, index * 7 + 3, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        observed = GEN.observe_overrides(grid)
        profiles.add(observed["lesson_profile"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(witness(grid))
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert min(witness_hits.values()) > 0
    assert len(inputs) >= 90


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 8},
        {"grid_h": 11},
        {"grid_w": 9},
        {"grid_w": 13},
        {"lesson_profile": "not_a_profile"},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_difficulty_bands_change_the_default_distribution():
    by_band = {
        band: [GEN.generate(8100 + i, i * 5 + 1, difficulty=band) for i in range(24)]
        for band in ("easy", "medium", "hard")
    }
    assert by_band["easy"] != by_band["medium"]
    assert by_band["medium"] != by_band["hard"]
    assert by_band["easy"] != by_band["hard"]
