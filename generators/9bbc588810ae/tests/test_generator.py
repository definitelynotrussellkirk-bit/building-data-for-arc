from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root

TASK_ID = "9bbc588810ae"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
MODULE_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = load_canonical_pairs(TASK_ID, root=ROOT, variant=0)


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    return PAIRS


def canonical_rule_hash():
    source = canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def nonzero_colors(grid):
    return {value for row in grid for value in row if value not in (0, 9)}


def test_authority_is_pinned_and_python_mirror_matches_all_canonical_pairs():
    assert GEN.RULE_HASH == canonical_rule_hash() == "a63dd2ae1f7a"
    assert len(canonical_pairs()) == 3
    for item in canonical_pairs():
        before = copy.deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == before


def test_override_interface_contains_only_real_observable_axes():
    assert set(GEN.AXES) == {
        "palette_kind", "transform", "match_panel", "query_cells"
    }
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert "r3" not in GEN.AXES["transform"]["valid"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("query_cells", [4, 8])
@pytest.mark.parametrize("match_panel", [0, 2])
def test_boundary_integer_overrides_are_exact_in_every_band(
    band, query_cells, match_panel
):
    grid = GEN.generate(
        271,
        14,
        difficulty=band,
        query_cells=query_cells,
        match_panel=match_panel,
    )
    assert GEN.self_check(grid) == []
    observed = GEN.observe_axes(grid)
    assert observed["query_cells"] == query_cells
    assert observed["match_panel"] == match_panel


@pytest.mark.parametrize("palette_kind", ["default", "warm", "cool", "varied"])
@pytest.mark.parametrize("transform", ["id", "r1", "r2", "fh", "fv", "tr", "atr"])
def test_choice_overrides_are_exact_and_observable(palette_kind, transform):
    grid = GEN.generate(
        918,
        7,
        difficulty="hard",
        palette_kind=palette_kind,
        transform=transform,
        match_panel=1,
        query_cells=7,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_axes(grid) == {
        "palette_kind": palette_kind,
        "transform": transform,
        "match_panel": 1,
        "query_cells": 7,
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"texture": "warm"},
        {"transform": "r3"},
        {"transform": "typo"},
        {"palette_kind": "typo"},
        {"match_panel": -1},
        {"match_panel": 3},
        {"match_panel": True},
        {"query_cells": 3},
        {"query_cells": 9},
        {"query_cells": 4.0},
    ],
)
def test_unknown_retired_and_invalid_overrides_reject_loudly(overrides):
    with pytest.raises((TypeError, ValueError), match="override|axis|transform|palette|panel|cells"):
        GEN.generate(1, 0, **overrides)


def test_default_schedule_supplies_a_bbox_signature_counterexample_every_three_demos():
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.SCHEDULE_PROFILES) == {
        "bbox_lower_color_witness", "bbox_match_low", "permuted_colors"
    }
    for seed in (0, 1, 91, 20261005):
        for start in range(9):
            grids = [GEN.generate(seed, start + offset, difficulty="medium") for offset in range(3)]
            assert any(
                GEN.SEMANTIC_WITNESSES["bbox_count_lowest_color_counterexample"](grid)
                for grid in grids
            )
            demos = [pair(grid) for grid in grids]
            query = pair(GEN.generate(seed + 1000, start + 30, difficulty="medium"))
            assert GEN.lesson_identifiable(demos, query) == []


def test_bbox_count_lowest_color_shortcut_fits_canonical_but_generated_witness_refutes_it():
    name = "bbox_count_lowest_color"
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.LESSON_COMPETITORS
    for item in canonical_pairs():
        assert GEN.CANONICAL_SHORTCUTS[name](item["input"]) == item["output"]

    for seed in range(12):
        grid = GEN.generate(seed, 0, difficulty="hard")
        assert GEN.schedule_profile(seed, 0, "hard") == "bbox_lower_color_witness"
        assert GEN.SEMANTIC_WITNESSES[
            "bbox_count_lowest_color_counterexample"
        ](grid)
        assert GEN.SEMANTIC_RIVALS[name](grid) != GEN.rule_mirror(grid)


def test_generated_distribution_is_lawful_diverse_and_uses_four_distinct_content_colors():
    inputs = set()
    outputs = set()
    observed_transforms = set()
    observed_match_panels = set()
    observed_sizes = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = GEN.generate(seed, seed % 17, difficulty=band)
            assert GEN.self_check(grid) == []
            assert len(grid) == 5 and all(len(row) == 23 for row in grid)
            assert len(nonzero_colors(grid)) == 4
            output = GEN.rule_mirror(grid)
            assert len(output) == 5 and all(len(row) == 5 for row in output)
            assert any(value for row in output for value in row)
            axes = GEN.observe_axes(grid)
            observed_transforms.add(axes["transform"])
            observed_match_panels.add(axes["match_panel"])
            observed_sizes.add(axes["query_cells"])
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))
    assert len(inputs) >= 85
    assert len(outputs) >= 80
    assert observed_transforms == {"id", "r1", "r2", "fh", "fv", "tr", "atr"}
    assert observed_match_panels == {0, 1, 2}
    assert observed_sizes == {4, 5, 6, 7, 8}


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0] * 23] * 4,
        [[0] * 22] * 5,
        [[0] * 23, [0] * 22, [0] * 23, [0] * 23, [0] * 23],
        [[True] * 23 for _ in range(5)],
        [[-1] * 23 for _ in range(5)],
        [[10] * 23 for _ in range(5)],
    ],
)
def test_self_check_reports_malformed_inputs_without_raising_or_mutating(bad):
    before = copy.deepcopy(bad)
    assert GEN.self_check(bad)
    assert bad == before


def test_generation_is_replayable_fresh_and_does_not_touch_global_random_state():
    random.seed(1234)
    state = random.getstate()
    first = GEN.generate(823, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(823, 103, difficulty="hard")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0 if first[0][0] else 8
    assert first != second


def test_every_rotation_of_each_four_pair_window_remains_identifiable():
    """Any one of four consecutive labelled pairs may be held out as query."""
    for band in ("easy", "medium", "hard"):
        for seed in (17, 91):
            for start in range(8):
                labelled = [
                    pair(GEN.generate(seed, start + offset, difficulty=band))
                    for offset in range(4)
                ]
                for query_index in range(4):
                    demos = [
                        item for index, item in enumerate(labelled)
                        if index != query_index
                    ]
                    assert GEN.lesson_identifiable(
                        demos, labelled[query_index]
                    ) == [], (band, seed, start, query_index)
