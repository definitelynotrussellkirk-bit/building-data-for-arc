"""Behavioral checks for the separate, opt-in diagonal-count family."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("diagonal_count_adapter_tests", HOME / "workspace/parametric/adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)
FIXED = {"ink_rule": "fixed_yellow"}
PARITY = {"ink_rule": "target_parity"}


def test_default_program_preserves_exact_canonical_bytes():
    root = HOME.parents[1]
    rows = (json.loads(line) for line in (root / "shared/data/canonical/puzzles.jsonl").open())
    canonical = next(row["program_solution"] for row in rows if row["task_id"] == HOME.name)
    assert ADAPTER.program(FIXED) == canonical
    assert ADAPTER.program(PARITY) != canonical


def test_remote_target_changes_existing_center_without_local_change():
    first = [[0] * 9 for _ in range(4)]
    for i in range(3):
        first[i][i] = 5
    second = [row[:] for row in first]
    for i in range(3):
        second[i][6 + i] = 5
    assert ADAPTER.solve(first, PARITY)[1][1] == 2
    assert ADAPTER.solve(second, PARITY)[1][1] == 4
    assert [row[:4] for row in first] == [row[:4] for row in second]
    assert ADAPTER.solve(first, FIXED)[1][1] == 4
    assert first[1][1] == 5


def test_whole_component_and_gray_color_are_required():
    grid = [[0] * 15 for _ in range(6)]
    for i in range(3):
        grid[i][i] = 5
        grid[i][12 + i] = 6
    for i in range(5):
        grid[i][6 + i] = 5
    expected = [row[:] for row in grid]
    expected[1][1] = 2
    assert ADAPTER.solve(grid, PARITY) == expected


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_supported_demo_counts_teach_both_settings_and_query_shortcuts(demos):
    matched = []
    for settings in (FIXED, PARITY):
        episode = ADAPTER.generate(17, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        inputs = [json.dumps(pair["input"]) for pair in pairs]
        assert len(set(inputs)) == len(inputs)
        assert not ADAPTER.lesson_report(episode, settings)["surviving_query_disagreements"]
        matched.append(inputs)
        if demos == 2:
            assert {len(ADAPTER.target_components(p["input"])) for p in episode["test"]} <= {3, 4}
    assert matched[0] == matched[1]


def test_first_turn_and_demo_prefix_do_not_depend_on_query_count():
    from reviewer_support import public_challenge_bytes
    one = ADAPTER.generate(33, PARITY, 3, 1)
    four = ADAPTER.generate(33, PARITY, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]
    four["test"] = four["test"][:1]
    assert public_challenge_bytes(one) == public_challenge_bytes(four)


def test_generation_is_deterministic_fresh_and_rng_pure():
    state = random.getstate()
    first = ADAPTER.generate(0, PARITY, 3, 4)
    assert random.getstate() == state
    second = ADAPTER.generate(0, PARITY, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert ADAPTER.generate(0, PARITY, 3, 4) == second


def test_large_query_uses_full_canvas_and_distant_targets():
    grid = ADAPTER.generate(7, PARITY, 3, 4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(cells) >= 75
    assert {r // 15 for r, c in cells} == {0, 1}
    assert {c // 15 for r, c in cells} == {0, 1}
    assert min(r for r, c in cells) == min(c for r, c in cells) == 0
    assert max(r for r, c in cells) == max(c for r, c in cells) == 29
    targets = ADAPTER.target_components(grid)
    assert len(targets) == 8
    assert max(r for obj in targets for r, c in obj) - min(r for obj in targets for r, c in obj) >= 18


def test_lesson_check_rejects_clean_only_color_blind_shortcut():
    demo = [[0] * 9 for _ in range(4)]
    query = [[0] * 9 for _ in range(4)]
    for i in range(3):
        demo[i][i] = query[i][i] = 5
        query[i][6 + i] = 6
    episode = {"train": [{"input": demo, "output": ADAPTER.solve(demo, FIXED)}],
               "test": [{"input": query, "output": ADAPTER.solve(query, FIXED)}]}
    report = ADAPTER.lesson_report(episode, FIXED)
    assert "paint_all_color_triples" in report["surviving_query_disagreements"]


@pytest.mark.parametrize("demos", [2, 3])
def test_demos_refute_counting_all_objects_with_either_ink_mapping(demos):
    episode = ADAPTER.generate(0, PARITY, demos, 4)
    for inverse in (False, True):
        fits = []
        for pair in episode["train"]:
            grid = pair["input"]
            all_objects = sum(len(ADAPTER._BASE._components8_of_color(grid, color))
                              for color in range(1, 10))
            red = (all_objects % 2 == 1) != inverse
            wrong = [row[:] for row in grid]
            for obj in ADAPTER.target_components(grid):
                r, c = sorted(obj)[1]
                wrong[r][c] = 2 if red else 4
            fits.append(wrong == pair["output"])
        assert not all(fits), (demos, inverse, fits)


@pytest.mark.parametrize("settings", [{}, {"ink_rule": True}, {"ink_rule": "other"}, {"ink_rule": "fixed_yellow", "extra": 1}])
def test_invalid_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, 3, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True)])
def test_count_boundaries_reject_invalid_requests(demos, queries):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, PARITY, demos, queries)


def test_strict_grid_and_seed_types():
    with pytest.raises(ValueError):
        ADAPTER.solve([[True]], PARITY)
    with pytest.raises(ValueError):
        ADAPTER.generate(True, PARITY, 3, 4)
