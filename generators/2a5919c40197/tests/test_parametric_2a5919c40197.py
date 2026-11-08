"""Focused, portable checks for the task-local parametric row-band adapter.

These checks exercise Python claims and the adapter contract. Native qualification
separately executes the emitted programs and every label through protected Racket.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import importlib.util
from itertools import groupby
import json
from pathlib import Path
import random
import sys

import pytest


# Bind helpers and source to this test's own packet or copied task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402


TASK_ID = "2a5919c40197"
MODES = ("all_uniform", "longest_uniform_run")
ADAPTER_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "adapter.py"
QUERY_SHAPES = [(3, 3), (17, 12), (24, 23), (30, 30)]


def test_parametric_adapter_is_present():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location(f"parametric_test_{TASK_ID}", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = canonical_path(find_root(__file__))
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("the runtime is missing this task's canonical program")


def _uniform_bands(grid: list[list[int]]) -> list[list[int]]:
    """Independent test oracle: group row indices by full-row equality."""
    return [
        [index for index, _row in band]
        for uniform, band in groupby(
            enumerate(grid), key=lambda item: len(set(item[1])) == 1
        )
        if uniform
    ]


def _expected_output(grid: list[list[int]], mode: str) -> list[list[int]]:
    bands = _uniform_bands(grid)
    maximum = max(map(len, bands), default=0)
    kept = {
        index
        for band in bands
        if mode == "all_uniform" or len(band) == maximum
        for index in band
    }
    return [[5 if index in kept else 0] * len(row) for index, row in enumerate(grid)]


def _input_keys(episode: dict) -> list[str]:
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_canonical_setting_preserves_the_exact_authoritative_program(adapter):
    canonical = _canonical_program()
    assert tuple(adapter.MODES) == MODES
    assert adapter.program({"mode": "all_uniform"}).encode("utf-8") == canonical.encode("utf-8")
    alternate = adapter.program({"mode": "longest_uniform_run"})
    assert isinstance(alternate, str) and alternate.startswith("(rule!")
    assert alternate != canonical


def test_literal_row_fixtures_cover_ties_colors_boundaries_and_full_width(adapter):
    # Literal expectations are independent of both solve() and the oracle above.
    fixtures = [
        (
            [
                [1, 1, 1, 1],
                [2, 2, 2, 2],
                [3, 3, 3, 4],
                [4, 4, 4, 4],
                [6, 7, 6, 7],
                [6, 6, 6, 6],
                [7, 7, 7, 7],
                [8, 9, 8, 9],
                [9, 9, 9, 9],
            ],
            [
                [5, 5, 5, 5], [5, 5, 5, 5], [0, 0, 0, 0],
                [5, 5, 5, 5], [0, 0, 0, 0], [5, 5, 5, 5],
                [5, 5, 5, 5], [0, 0, 0, 0], [5, 5, 5, 5],
            ],
            [
                [5, 5, 5, 5], [5, 5, 5, 5], [0, 0, 0, 0],
                [0, 0, 0, 0], [0, 0, 0, 0], [5, 5, 5, 5],
                [5, 5, 5, 5], [0, 0, 0, 0], [0, 0, 0, 0],
            ],
        ),
        (
            [[0, 0, 0], [5, 5, 5], [1, 2, 1], [4, 4, 4], [8, 8, 8]],
            [[5, 5, 5], [5, 5, 5], [0, 0, 0], [5, 5, 5], [5, 5, 5]],
            [[5, 5, 5], [5, 5, 5], [0, 0, 0], [5, 5, 5], [5, 5, 5]],
        ),
        (
            [[1, 1, 1, 1, 2, 1], [3, 3, 3, 3, 3, 3], [4, 4, 4, 6, 4, 4]],
            [[0, 0, 0, 0, 0, 0], [5, 5, 5, 5, 5, 5], [0, 0, 0, 0, 0, 0]],
            [[0, 0, 0, 0, 0, 0], [5, 5, 5, 5, 5, 5], [0, 0, 0, 0, 0, 0]],
        ),
        (
            [[1, 2, 1], [3, 4, 3], [5, 6, 5]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        ),
        (
            [[1, 1, 1], [2, 2, 2], [9, 9, 9]],
            [[5, 5, 5], [5, 5, 5], [5, 5, 5]],
            [[5, 5, 5], [5, 5, 5], [5, 5, 5]],
        ),
    ]
    for source, canonical, longest in fixtures:
        for mode, expected in zip(MODES, (canonical, longest)):
            grid = copy.deepcopy(source)
            actual = adapter.solve(grid, mode)
            assert actual == expected, (mode, source)
            assert grid == source
            assert actual is not grid
            assert all(output_row is not input_row for output_row, input_row in zip(actual, grid))


def test_solve_rejects_malformed_grids_and_accepts_the_largest_boundary(adapter):
    malformed = [
        None, [], [[]], [[1] * 3] * 2, [[1] * 2] * 3,
        [[1] * 3] * 31, [[1] * 31] * 3,
        [[1, 1, 1], [2, 2], [3, 3, 3]],
        [[1, 1, 1], None, [3, 3, 3]],
        [[True, 1, 1], [2, 2, 2], [3, 3, 3]],
        [[1.0, 1, 1], [2, 2, 2], [3, 3, 3]],
        [[-1, 1, 1], [2, 2, 2], [3, 3, 3]],
        [[10, 1, 1], [2, 2, 2], [3, 3, 3]],
    ]
    for mode in MODES:
        for grid in malformed:
            with pytest.raises((TypeError, ValueError)):
                adapter.solve(grid, mode)
        grid = [[index % 10] * 30 for index in range(30)]
        assert adapter.solve(grid, mode) == [[5] * 30 for _ in range(30)]
    with pytest.raises((TypeError, ValueError)):
        adapter.solve([[1, 1, 1], [2, 2, 2], [3, 3, 3]], "unknown")


def test_settings_are_validated_at_both_public_entry_points(adapter):
    bad_settings = [
        None, [], "all_uniform", {}, {"mode": "unknown"},
        {"mode": 1}, {"mode": True}, {"mode": ["all_uniform"]},
        {"mode": "all_uniform", "extra": 1},
    ]
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(17, settings, demos=2, queries=1)


def test_generation_rejects_noninteger_and_out_of_range_requests(adapter):
    valid = {"seed": 17, "settings": {"mode": "all_uniform"}, "demos": 3, "queries": 4}
    invalid = {
        "seed": [-1, 2**63, True, 1.5, "17"],
        "demos": [1, 7, False, 3.0, "3"],
        "queries": [0, 5, True, 1.0, "1"],
    }
    for name, values in invalid.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, name: value})
    # Both permitted seed endpoints remain usable; this is not a large sweep.
    for seed in (0, 2**63 - 1):
        episode = adapter.generate(**{**valid, "seed": seed, "demos": 2, "queries": 1})
        assert len(episode["train"]) == 2 and len(episode["test"]) == 1


def test_generated_episodes_are_complete_novel_and_correct_at_supported_counts(adapter):
    for mode in MODES:
        for seed in (0, 17):
            for demos in (2, 3, 6):
                episode = adapter.generate(seed, {"mode": mode}, demos=demos, queries=4)
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == 4
                assert episode["program_solution"] == adapter.program({"mode": mode})
                keys = _input_keys(episode)
                assert len(set(keys)) == len(keys), (mode, seed, demos)
                for split in ("train", "test"):
                    for pair in episode[split]:
                        assert {"input", "output"} <= pair.keys()
                        grid = pair["input"]
                        assert type(grid) is list and 3 <= len(grid) <= 30
                        assert type(grid[0]) is list and 3 <= len(grid[0]) <= 30
                        width = len(grid[0])
                        assert all(
                            type(row) is list and len(row) == width
                            and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
                            for row in grid
                        )
                        output = pair["output"]
                        assert type(output) is list and len(output) == len(grid)
                        assert all(
                            type(row) is list and len(row) == width
                            and all(type(cell) is int and cell in (0, 5) for cell in row)
                            for row in output
                        )
                        assert output == _expected_output(grid, mode)
                # Each mandatory teaching example separates the two settings.
                for pair in episode["train"][:2]:
                    grid = pair["input"]
                    assert _expected_output(grid, MODES[0]) != _expected_output(grid, MODES[1])


def test_four_query_profiles_include_full_width_witnesses_and_substantive_30x30(adapter):
    for seed in (0, 17):
        episode = adapter.generate(seed, {"mode": "longest_uniform_run"}, demos=3, queries=4)
        grids = [pair["input"] for pair in episode["test"]]
        assert [(len(grid), len(grid[0])) for grid in grids] == QUERY_SHAPES
        assert (len(episode["train"][2]["input"]), len(episode["train"][2]["input"][0])) == (3, 3)
        for grid in grids:
            uniform = [len(set(row)) == 1 for row in grid]
            assert any(uniform) and not all(uniform)
        for grid in grids[1:]:
            assert any(len(set(row[:3])) == 1 and len(set(row)) > 1 for row in grid)
        large = grids[-1]
        for top in (0, 15):
            for left in (0, 15):
                # Meaningful input occupies every quarter of the stress canvas.
                cells = [large[row][column] for row in range(top, top + 15) for column in range(left, left + 15)]
                assert sum(cell not in (0, 5) for cell in cells) > len(cells) // 2


def test_demo_and_query_prefixes_do_not_depend_on_requested_counts(adapter):
    for mode in MODES:
        settings = {"mode": mode}
        full = adapter.generate(17, settings, demos=6, queries=4)
        for demos in (2, 3):
            shorter = adapter.generate(17, settings, demos=demos, queries=4)
            assert shorter["train"] == full["train"][:demos]
            assert shorter["test"] == full["test"]
        for queries in (1, 2, 3):
            shorter = adapter.generate(17, settings, demos=6, queries=queries)
            assert shorter["train"] == full["train"]
            assert shorter["test"] == full["test"][:queries]


@pytest.mark.parametrize("seed", (0, 17))
def test_two_demonstrations_reject_any_fixed_height_ratio_threshold(adapter, seed):
    episode = adapter.generate(seed, {"mode": "longest_uniform_run"}, demos=2, queries=4)
    selected, rejected = [], []
    for pair in episode["train"]:
        grid = pair["input"]
        for band in _uniform_bands(grid):
            ratio = Fraction(len(band), len(grid))
            if pair["output"][band[0]][0] == 5:
                selected.append(ratio)
            else:
                rejected.append(ratio)
    assert selected and rejected, "both positive and negative uniform bands must be taught"
    # A fixed threshold requires every selected ratio to exceed every rejected
    # ratio. Overlap defeats either strict or inclusive threshold variants.
    assert min(selected) <= max(rejected), {
        "seed": seed,
        "selected_ratios": selected,
        "rejected_ratios": rejected,
    }


def test_settings_change_labels_without_changing_sampled_inputs(adapter):
    for seed in (0, 17):
        canonical = adapter.generate(seed, {"mode": MODES[0]}, demos=6, queries=4)
        alternate = adapter.generate(seed, {"mode": MODES[1]}, demos=6, queries=4)
        assert _input_keys(canonical) == _input_keys(alternate)
        assert canonical["train"] != alternate["train"]
        assert canonical["program_solution"] != alternate["program_solution"]
    first = adapter.generate(0, {"mode": MODES[0]}, demos=6, queries=4)
    second = adapter.generate(17, {"mode": MODES[0]}, demos=6, queries=4)
    assert _input_keys(first) != _input_keys(second)


def test_repeated_generation_is_fresh_deterministic_and_global_rng_pure(adapter):
    for mode in MODES:
        settings = {"mode": mode}
        state = random.getstate()
        first = adapter.generate(17, settings, demos=6, queries=4)
        assert random.getstate() == state
        second = adapter.generate(17, settings, demos=6, queries=4)
        assert first == second and first is not second
        assert settings == {"mode": mode}
        for split in ("train", "test"):
            assert first[split] is not second[split]
            for left, right in zip(first[split], second[split]):
                assert left is not right
                for field in ("input", "output"):
                    assert left[field] is not right[field]
                    assert all(a is not b for a, b in zip(left[field], right[field]))
        original = copy.deepcopy(second)
        for split in ("train", "test"):
            for field in ("input", "output"):
                first[split][0][field][0][0] = (first[split][0][field][0][0] + 1) % 10
        assert second == original
        assert adapter.generate(17, settings, demos=6, queries=4) == original
