"""Task-local regression tests for a287e878de99.

The small oracle and topology probes below are independent of production code.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a287e878de99"
HERE = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_under_test", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    result: list[set[tuple[int, int]]] = []
    while cells:
        start = min(cells)
        todo = [start]
        component = {start}
        cells.remove(start)
        while todo:
            r, c = todo.pop()
            for dr, dc in _NEIGHBORS4:
                neighbor = (r + dr, c + dc)
                if neighbor in cells:
                    cells.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        result.append(component)
    return result


def _degree(cell: tuple[int, int], component: set[tuple[int, int]]) -> int:
    r, c = cell
    return sum((r + dr, c + dc) in component for dr, dc in _NEIGHBORS4)


def endpoint_output(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    output = [[0] * width for _ in range(height)]
    for component in _components(grid):
        for r, c in component:
            if _degree((r, c), component) == 1:
                output[r][c] = 5
    return output


def _scene_kind(grid: list[list[int]]) -> str:
    components = _components(grid)
    if any(sum(_degree(cell, comp) for cell in comp) // 2 >= len(comp) for comp in components):
        return "cycle"
    if any(any(_degree(cell, comp) >= 3 for cell in comp) for comp in components):
        return "branch"
    if any(len(comp) == 1 for comp in components):
        return "singleton"
    return "path"


def _signature(grid: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_contract_is_rule_pinned_and_only_real_axes_are_advertised():
    assert gen.RULE_HASH == "d7cc9d995b63"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "component_count", "scene_pattern"}
    assert gen.AXES["scene_pattern"]["valid"] == "path|branch|cycle|singleton"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 4
    assert tuple(gen.SCHEDULE_PROFILES) == ("path", "branch", "cycle", "singleton")


def test_canonical_pairs_are_accepted_and_python_oracle_matches_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert endpoint_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_overrides_are_constructive_and_observable_in_every_band():
    cases = (
        (7, 8, 2),
        (7, 8, 5),
        (9, 13, 4),
        (15, 17, 5),
    )
    for band in (None, "easy", "medium", "hard"):
        for scene in gen.SCHEDULE_PROFILES:
            for index, (height, width, count) in enumerate(cases):
                grid = gen.generate(
                    7100 + index,
                    index,
                    difficulty=band,
                    grid_h=height,
                    grid_w=width,
                    component_count=count,
                    scene_pattern=scene,
                )
                assert gen.self_check(grid, difficulty=band) == []
                assert gen.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                    "component_count": count,
                    "scene_pattern": scene,
                }
                assert _scene_kind(grid) == scene
                assert endpoint_output(grid) != grid


def test_invalid_overrides_and_difficulties_fail_loudly():
    bad_calls = (
        {"mystery_axis": 1},
        {"grid_h": 6},
        {"grid_h": 16},
        {"grid_w": 7},
        {"grid_w": 18},
        {"component_count": 1},
        {"component_count": 6},
        {"scene_pattern": "plain"},
        {"grid_h": True},
        {"grid_w": "9"},
        {"component_count": 3.0},
        {"scene_pattern": 3},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_four_example_schedule_covers_every_profile_and_anchors_canonical_shape():
    expected = set(gen.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            assert {
                gen.schedule_profile(99, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            } == expected

        anchors = [
            gen.generate(8000 + index, index, difficulty=band)
            for index in range(0, 20, 4)
        ]
        for grid in anchors:
            observed = gen.observe_overrides(grid)
            assert observed == {
                "grid_h": 7,
                "grid_w": 8,
                "component_count": 2,
                "scene_pattern": "path",
            }
            assert sorted(map(len, _components(grid))) == [2, 5]


def test_default_distribution_is_deterministic_nonidentity_and_varied():
    for band in ("easy", "medium", "hard"):
        scenes, shapes, signatures = set(), set(), set()
        for index in range(64):
            grid = gen.generate(12000 + index, index, difficulty=band)
            assert grid == gen.generate(12000 + index, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert endpoint_output(grid) == gen.rule_mirror(grid)
            assert endpoint_output(grid) != grid
            observed = gen.observe_overrides(grid)
            scenes.add(observed["scene_pattern"])
            shapes.add((len(grid), len(grid[0])))
            signatures.add(_signature(grid))
        assert scenes == set(gen.SCHEDULE_PROFILES)
        assert len(shapes) >= 8
        assert len(signatures) >= 60


def test_named_shortcuts_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "two_extrema_per_component",
        "nonbranching_components_only",
        "degree_at_most_one",
    }
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_generated_witnesses_are_real_counterexamples_to_named_rivals():
    for scene in ("branch", "cycle", "singleton"):
        grid = gen.generate(
            424242,
            7,
            grid_h=9,
            grid_w=12,
            component_count=3,
            scene_pattern=scene,
        )
        truth = endpoint_output(grid)
        fired = [name for name, predicate in gen.SEMANTIC_WITNESSES.items() if predicate(grid)]
        assert fired, scene
        for witness in fired:
            rivals = gen.WITNESS_RIVALS[witness]
            assert rivals
            for rival_name in rivals:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth, (scene, witness, rival_name)


def test_every_four_demo_window_refutes_all_lesson_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(919191, index, difficulty=band)
                pairs.append({"input": grid, "output": endpoint_output(grid)})
            demos, query = pairs[:-1], pairs[-1]
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert not all(competitor(pair["input"]) == pair["output"] for pair in demos), (
                    band,
                    start,
                    name,
                )


def test_self_check_rejects_non_teaching_and_malformed_impostors():
    blank = [[0] * 8 for _ in range(7)]
    pair_only = [row[:] for row in blank]
    pair_only[2][2] = pair_only[2][3] = 5
    short_line = [row[:] for row in blank]
    for col in range(4):
        short_line[3][col] = 5
    singleton_only = [row[:] for row in blank]
    singleton_only[2][2] = 5
    cycle_only = [row[:] for row in blank]
    for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)):
        cycle_only[r][c] = 5
    wrong_color = [row[:] for row in blank]
    wrong_color[1][1] = 8
    ragged = [[0, 5, 0], [0, 0], [0, 5, 0]]

    for name, grid in (
        ("blank", blank),
        ("pair_only", pair_only),
        ("short_line", short_line),
        ("singleton_only", singleton_only),
        ("cycle_only", cycle_only),
        ("wrong_color", wrong_color),
        ("ragged", ragged),
    ):
        assert gen.self_check(grid), name


def test_regression_easy_seed_14_is_not_identity():
    grid = gen.generate(14, 14, difficulty="easy")
    assert endpoint_output(grid) != grid
    assert gen.rule_mirror(grid) != grid


def test_retained_strongest_shortcut_counterexample():
    path = HERE / "counterexamples" / "two_extrema_branch_singleton.json"
    payload = json.loads(path.read_text())
    grid = payload["input"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == payload["canonical_output"]
    rival = gen.CANONICAL_SHORTCUTS[payload["rival"]]
    assert rival(grid) == payload["rival_output"]
    assert payload["canonical_output"] != payload["rival_output"]
