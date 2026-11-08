"""Portable regressions for the symmetry-outsider generator curriculum."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "040bfb038c65"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _components(grid, color=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return sorted(result, key=min)


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _d4(cells):
    local = list(_normalize(cells))
    variants = []
    for reflected in (False, True):
        current = [(row, -col) for row, col in local] if reflected else list(local)
        for _ in range(4):
            variants.append(_normalize(current))
            current = [(col, -row) for row, col in current]
    return min(variants)


def _intended(grid):
    components = _components(grid)
    counts = Counter(_d4(cells) for cells in components)
    winners = [cells for cells in components if counts[_d4(cells)] == 1]
    assert len(winners) == 1
    output = deepcopy(grid)
    for row, col in winners[0]:
        output[row][col] = 8
    return output


def _largest_row_major(grid):
    components = _components(grid)
    largest_size = max(map(len, components))
    largest = next(cells for cells in components if len(cells) == largest_size)
    output = deepcopy(grid)
    for row, col in largest:
        output[row][col] = 8
    return output


def _labeled(grid):
    return {"input": grid, "output": _intended(grid)}


def test_rule_pin_canonical_examples_and_selected_authority_are_exact():
    assert GEN.RULE_HASH == "80d289c11e33"
    assert len(PAIRS) == 3
    assert all(GEN.self_check(pair["input"]) == [] for pair in PAIRS)
    assert all(GEN.strict_canonical_like(pair["input"]) == [] for pair in PAIRS)
    assert all(GEN.rule_mirror(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(_largest_row_major(pair["input"]) == pair["output"] for pair in PAIRS)

    selected = json.loads(
        (
            ROOT
            / "shared/data/base/solutions/banks/2f7d84161f6a/H11__040bfb038c65.json"
        ).read_text()
    )
    racket = selected["racket_target"]
    assert racket["target_code"] == racket["raw_code"]


def test_public_axis_and_schedule_contract_is_small_exact_and_constructive():
    assert GEN.AXES == {
        "grid_h": {
            "type": "int",
            "default": "canonical 7",
            "valid": "7..14",
            "doc": "Grid height.",
        },
        "grid_w": {
            "type": "int",
            "default": "canonical 9 or 10",
            "valid": "9..16",
            "doc": "Grid width.",
        },
        "n_majority": {
            "type": "int",
            "default": "2 (easy), 2..3 (medium), 3 (hard)",
            "valid": "2..3",
            "doc": "Copies of the majority D4-shape class (plus one oddball).",
        },
        "texture": {
            "type": "str",
            "default": "3-phase lesson schedule",
            "valid": "smaller_odd|same_size_odd|larger_odd",
            "doc": "Cell-count relation between the oddball and majority objects.",
        },
    }
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "smaller_odd",
        "same_size_odd",
        "larger_odd",
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 14])
@pytest.mark.parametrize("grid_w", [9, 16])
@pytest.mark.parametrize("n_majority", [2, 3])
@pytest.mark.parametrize("texture", ["smaller_odd", "same_size_odd", "larger_odd"])
def test_every_advertised_override_round_trips_in_every_band(
    band, grid_h, grid_w, n_majority, texture
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_majority": n_majority,
        "texture": texture,
    }
    grid = GEN.generate(771, 5, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert _intended(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_majority": "2"},
        {"texture": "plain"},
        {"texture": "all_same_shape"},
    ],
)
def test_invalid_unknown_and_retired_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_is_a_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, sample_index)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_has_canonical_profiles_and_named_counterexamples(band):
    for start in range(6):
        grids = [GEN.generate(12345, index, difficulty=band) for index in range(start, start + 4)]
        assert all(7 <= len(grid) <= 14 and 9 <= len(grid[0]) <= 16 for grid in grids)
        assert all({value for row in grid for value in row} == {0, 4} for grid in grids)
        assert [GEN.schedule_profile(12345, index, band) for index in range(start, start + 4)] == [
            GEN.SCHEDULE_PROFILES[index % 3] for index in range(start, start + 4)
        ]
        assert [GEN.observe_overrides(grid)["texture"] for grid in grids] == [
            GEN.SCHEDULE_PROFILES[index % 3] for index in range(start, start + 4)
        ]
        labeled = [_labeled(grid) for grid in grids]
        for query_index, query in enumerate(labeled):
            demos = [pair for index, pair in enumerate(labeled) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            assert any(
                GEN.LESSON_COMPETITORS["largest_yellow_blob"](pair["input"])
                != pair["output"]
                for pair in demos
            )


def test_default_sampling_reaches_declared_dimension_span_and_canonical_anchor():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(24680 + index, index * 7, difficulty=band) for index in range(240)]
        heights = {len(grid) for grid in grids}
        widths = {len(grid[0]) for grid in grids}
        assert {7, 14} <= heights
        assert {9, 16} <= widths
        assert any(len(grid) == 7 and len(grid[0]) in (9, 10) for grid in grids)


def test_semantic_witness_is_a_real_largest_object_counterexample():
    assert set(GEN.SEMANTIC_RIVALS) == {"largest_yellow_blob"}
    assert GEN.CANONICAL_SHORTCUTS == GEN.SEMANTIC_RIVALS
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS
    for sample_index in (0, 1):
        grid = GEN.generate(882, sample_index)
        expected = _intended(grid)
        assert GEN.SEMANTIC_WITNESSES["oddball_not_largest"](grid)
        assert GEN.SEMANTIC_RIVALS["largest_yellow_blob"](grid) != expected
    grid = GEN.generate(882, 2)
    assert not GEN.SEMANTIC_WITNESSES["oddball_not_largest"](grid)
    assert GEN.SEMANTIC_RIVALS["largest_yellow_blob"](grid) == _intended(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)], [[0] * 9 for _ in range(7)]],
)
def test_malformed_or_out_of_domain_grids_are_diagnostic_not_exceptions(grid):
    assert GEN.self_check(grid)


def test_retained_largest_object_counterexample_is_hash_bound_and_replayable():
    import hashlib

    artifact_path = HOME / "counterexamples/largest-object-shortcut-v3.json"
    payload = json.loads(artifact_path.read_text())
    assert payload["schema"] == "arcpuzzles-generator-counterexample-v1"
    assert payload["task_id"] == TASK_ID
    assert payload["rival"] == "largest_yellow_blob"
    assert payload["generator_sha256"] == hashlib.sha256(
        GENERATOR_PATH.read_bytes()
    ).hexdigest()

    selected_rule = (
        ROOT
        / "shared/data/base/solutions/banks/2f7d84161f6a/H11__040bfb038c65.json"
    )
    assert payload["rule_source_sha256"] == hashlib.sha256(
        selected_rule.read_bytes()
    ).hexdigest()
    assert payload["declared_rule_hash"] == GEN.RULE_HASH
    assert payload["canonical_fit"] == {"matched": 3, "total": 3}

    grid = payload["input"]
    intended = GEN.rule_mirror(grid)
    rival = GEN.LESSON_COMPETITORS[payload["rival"]](grid)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == payload["observed_axes"]
    assert intended == payload["intended_output"]
    assert rival == payload["rival_output"]
    assert intended != rival
    assert payload["intended_changed_cells"] != payload["rival_changed_cells"]


def test_curriculum_probe_rechecks_every_declared_schedule_residue():
    probe_path = HOME / "workspace/probe_curriculum.py"
    spec = spec_from_file_location("task_curriculum_probe", probe_path)
    assert spec and spec.loader
    probe = module_from_spec(spec)
    sys.modules[spec.name] = probe
    spec.loader.exec_module(probe)

    result = probe.evaluate(seed=0, bands=("easy",), starts=GEN.LESSON_SCHEDULE_PERIOD)
    assert result["canonical_shortcut_fit"] == {"matched": 3, "total": 3}
    assert result["lessons_checked"] == 3
    assert result["query_rotations_checked"] == 12
    assert result["ambiguous_rotations"] == []
    assert result["errors"] == []
    assert result["counterexample"]["intended_output"] != result["counterexample"]["rival_output"]
