from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_694d3ee0b12a", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _canonical_row():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "694d3ee0b12a":
                return row
    raise AssertionError("canonical task not found")


def _pairs(row):
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _seven_components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == 7
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(component)
    return result


def _frame_bbox(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _is_exact_7x7_frame(component):
    r0, c0, r1, c1 = _frame_bbox(component)
    border = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }
    return (r1 - r0 + 1, c1 - c0 + 1) == (7, 7) and set(component) == border


def test_canonical_inputs_are_accepted_by_the_generator_contract():
    for pair in _pairs(_canonical_row()):
        assert gen.self_check(pair["input"]) == []


def test_default_schedule_emits_two_and_three_independent_canonical_frames():
    observed_counts = []
    for sample_index in range(8):
        grid = gen.generate(12345, sample_index, difficulty="medium")
        components = _seven_components(grid)
        observed_counts.append(len(components))
        assert len(components) in (2, 3)
        assert all(_is_exact_7x7_frame(component) for component in components)
        assert gen.self_check(grid) == []
    assert set(observed_counts) == {2, 3}


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert getattr(gen, "RULE_HASH", None) == "c13ecc4348dc"
    assert callable(getattr(gen, "strict_canonical_like", None))
    assert callable(getattr(gen, "rule_mirror", None))
    for pair in _pairs(_canonical_row()):
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_declared_bottom_right_shortcut_fits_canonical_but_generated_inputs_refute_it():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    rivals = getattr(gen, "SEMANTIC_RIVALS", None)
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", None)
    claims = getattr(gen, "WITNESS_RIVALS", None)
    assert isinstance(shortcuts, dict) and "fixed_bottom_right_key" in shortcuts
    assert isinstance(rivals, dict) and "fixed_bottom_right_key" in rivals
    assert isinstance(witnesses, dict) and witnesses
    assert isinstance(claims, dict) and claims

    shortcut = shortcuts["fixed_bottom_right_key"]
    for pair in _pairs(_canonical_row()):
        assert shortcut(pair["input"]) == pair["output"]

    for profile in gen.SCHEDULE_PROFILES:
        for seed in range(4):
            grid = gen.generate(seed, seed, difficulty="medium", scene_profile=profile)
            answer = gen.rule_mirror(grid)
            assert shortcut(grid) != answer
            assert all(witness(grid) for witness in witnesses.values())


def test_profile_schedule_overrides_and_observer_are_exact():
    assert callable(getattr(gen, "observe_overrides", None))
    for band in ("easy", "medium", "hard"):
        observed = []
        for sample_index in range(12):
            expected = gen.schedule_profile(77, sample_index, difficulty=band)
            grid = gen.generate(77, sample_index, difficulty=band)
            actual = gen.observe_overrides(grid)
            assert actual == {"scene_profile": expected}
            observed.append(actual["scene_profile"])
        assert set(observed) == set(gen._PROFILE_SCHEDULES[band])

    for profile in gen.SCHEDULE_PROFILES:
        grid = gen.generate(91, 0, scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}

    for kwargs in ({"unknown_axis": 1}, {"scene_profile": "not_a_profile"}):
        try:
            gen.generate(1, 0, **kwargs)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"override should reject: {kwargs}")


def test_mutation_fixtures_are_rejected_without_mutating_inputs():
    assert callable(getattr(gen, "mutation_fixtures", None))
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, fixture in fixtures:
        snapshot = copy.deepcopy(fixture)
        assert gen.self_check(fixture), name
        assert fixture == snapshot


def test_generated_two_demo_lessons_are_identifiable_against_declared_competitors():
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 2
    assert callable(getattr(gen, "lesson_identifiable", None))
    demos = []
    for sample_index in range(2):
        grid = gen.generate(404, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(404, 2, difficulty="hard")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    assert gen.lesson_identifiable(demos[:1], query)
