"""Focused regressions for the exact-length yellow-bar generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap: packet tree and staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "2da4094bc0e1"
ROOT = find_root(__file__)
DEFAULT_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_SOURCE.is_file():
    DEFAULT_SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_SOURCE))
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _runs(grid):
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            color = row[col]
            start = col
            while col < len(row) and row[col] == color:
                col += 1
            if color != 0:
                yield color, row_index, start, col - start


def _cap_runs(grid, *, color_specific: bool, exact: bool = True):
    out = deepcopy(grid)
    width = len(grid[0])
    for color, row, start, length in _runs(grid):
        if color_specific and color != 4:
            continue
        if (length == 3) if exact else (color == 4 and length >= 3):
            if start > 0 and grid[row][start - 1] == 0:
                out[row][start - 1] = 6
            stop = start + length
            if stop < width and grid[row][stop] == 0:
                out[row][stop] = 6
    return out


def _pair(grid):
    return {"input": deepcopy(grid), "output": _cap_runs(grid, color_specific=True)}


def test_metadata_and_contract_are_truthful():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "5f2c21d44ce7"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_bars",
        "n_wrong_bars",
        "n_color_decoys",
        "decoy_color",
        "palette_size",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == {"color_agnostic_exact3"}
    assert set(GEN.SEMANTIC_RIVALS) == {
        "color_agnostic_exact3",
        "yellow_at_least3",
    }


def test_all_labeled_canonical_pairs_match_authority_and_shortcut():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert _cap_runs(source, color_specific=True) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        # The canonical demonstrations do not contain a same-colour non-yellow
        # horizontal run of exactly three, so this plausible rival survives all.
        assert GEN.CANONICAL_SHORTCUTS["color_agnostic_exact3"](source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 8,
            "grid_w": 7,
            "n_bars": 1,
            "n_wrong_bars": 1,
            "n_color_decoys": 1,
            "decoy_color": 5,
            "palette_size": 3,
        },
        {
            "grid_h": 10,
            "grid_w": 13,
            "n_bars": 2,
            "n_wrong_bars": 2,
            "n_color_decoys": 1,
            "decoy_color": 7,
            "palette_size": 4,
        },
        {
            "grid_h": 14,
            "grid_w": 16,
            "n_bars": 3,
            "n_wrong_bars": 3,
            "n_color_decoys": 2,
            "decoy_color": 9,
            "palette_size": 4,
        },
    ],
)
def test_exact_overrides_are_constructive_observable_and_semantic(difficulty, requested):
    grid = GEN.generate(9127, 31, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    truth = GEN.rule_mirror(grid)
    assert truth == _cap_runs(grid, color_specific=True)
    assert GEN.SEMANTIC_WITNESSES["color_specificity"](grid)
    assert GEN.SEMANTIC_WITNESSES["exact_length"](grid)
    assert GEN.SEMANTIC_RIVALS["color_agnostic_exact3"](grid) != truth
    assert GEN.SEMANTIC_RIVALS["yellow_at_least3"](grid) != truth


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 17},
        {"n_bars": 0},
        {"n_bars": 4},
        {"n_wrong_bars": 0},
        {"n_wrong_bars": 4},
        {"n_color_decoys": 0},
        {"n_color_decoys": 3},
        {"decoy_color": 4},
        {"decoy_color": 6},
        {"palette_size": 2},
        {"palette_size": 5},
        {"grid_h": True},
        {"n_bars": 2.0},
        {"decoy_color": "7"},
    ],
)
def test_invalid_unknown_and_coerced_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def _pinned_profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_default_distribution_reaches_both_canonical_palette_sizes():
    palette_sizes = {
        len({cell for row in GEN.generate(6100, index) for cell in row})
        for index in range(80)
    }
    assert palette_sizes == {3, 4}


def test_hard_band_has_pinned_exact_canonical_profile_support():
    canonical_profiles = {(10, 13, 3), (10, 14, 4), (11, 13, 4), (11, 14, 4)}
    observed = set()
    for index in range(20):
        seed = _pinned_profile_seed("hard", index)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty="hard")
        observed.add((len(grid), len(grid[0]), len({cell for row in grid for cell in row})))
    assert observed & canonical_profiles


def test_default_distribution_always_teaches_both_discriminators():
    shapes = set()
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for index in range(40):
            grid = GEN.generate(4000 + band_index, index, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.SEMANTIC_WITNESSES["color_specificity"](grid)
            assert GEN.SEMANTIC_WITNESSES["exact_length"](grid)
            assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS["color_agnostic_exact3"](grid)
            assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS["yellow_at_least3"](grid)
            shapes.add((len(grid), len(grid[0])))
    assert {(10, 13), (11, 14)} & shapes
    assert len(shapes) >= 12


def test_lesson_hook_requires_demonstrated_counterexamples():
    grids = [GEN.generate(7000, index, difficulty="medium") for index in range(4)]
    pairs = [_pair(grid) for grid in grids]
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []

    # Removing color-decoy evidence lets the color-agnostic rival survive.
    stripped = []
    for pair in pairs[:3]:
        grid = deepcopy(pair["input"])
        for color, row, start, length in list(_runs(grid)):
            if color not in (4, 6) and length == 3:
                for col in range(start, start + length):
                    grid[row][col] = 0
        stripped.append(_pair(grid))
    reasons = GEN.lesson_identifiable(stripped, pairs[3])
    assert any("color_agnostic_exact3" in reason for reason in reasons)


def test_validator_rejects_malformed_and_missing_rule_support():
    valid = GEN.generate(77, 4)
    fixtures = [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(8)]]
    no_target = deepcopy(valid)
    for color, row, start, length in list(_runs(no_target)):
        if color == 4 and length == 3:
            no_target[row][start] = 0
    fixtures.append(no_target)
    for grid in fixtures:
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = GEN.generate(991, 37, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(991, 37, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_retained_color_agnostic_counterexample_is_replayable_and_exact():
    path = SOURCE.parent / "counterexamples" / "color_agnostic_exact3.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == TASK_ID
    assert record["generator_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    generated = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
        **record["overrides"],
    )
    assert generated == record["input"]
    assert GEN.rule_mirror(generated) == record["intended_output"]
    assert GEN.SEMANTIC_RIVALS["color_agnostic_exact3"](generated) == record["rival_output"]
    differing = [
        [row, col]
        for row in range(len(generated))
        for col in range(len(generated[0]))
        if record["intended_output"][row][col] != record["rival_output"][row][col]
    ]
    assert differing == record["differing_cells"] == [[4, 1], [4, 5]]
    assert record["executed_rule_hash"] == GEN.RULE_HASH
