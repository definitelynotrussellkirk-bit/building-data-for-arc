from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_28c998e193d9", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)

PROFILES = (
    "pair_one_bent",
    "triple_one_bent",
    "pair_two_bent",
    "triple_two_bent",
)


def _canonical_row():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "28c998e193d9":
                return row
    raise AssertionError("canonical task not found")


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and grid[point[0]][point[1]] != 0
                        and point not in seen
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(cells)
    return result


def _empty_like(grid):
    return [[0 for _ in row] for row in grid]


def _bbox_fill(grid):
    output = _empty_like(grid)
    for cells in _components(grid):
        r1 = min(row for row, _ in cells)
        r2 = max(row for row, _ in cells)
        c1 = min(col for _, col in cells)
        c2 = max(col for _, col in cells)
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = 8
    return output


def _global_row_close(grid):
    output = _empty_like(grid)
    for row in range(len(grid)):
        cols = [col for col, value in enumerate(grid[row]) if value != 0]
        if cols:
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = 8
    return output


def _recolor_only(grid):
    return [[8 if value else 0 for value in row] for row in grid]


def _vertical_close(grid):
    output = _empty_like(grid)
    for cells in _components(grid):
        for col in {col for _, col in cells}:
            rows = [row for row, cc in cells if cc == col]
            for row in range(min(rows), max(rows) + 1):
                output[row][col] = 8
    return output


def test_canonical_inputs_are_accepted_and_python_mirror_matches_every_output():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    assert gen.RULE_HASH == "b18cc934f1d8"
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_bent_component_is_closed_row_by_row_not_by_whole_bbox():
    source = [
        [2, 2, 2, 2, 2],
        [2, 0, 0, 0, 2],
        [2, 0, 0, 2, 2],
        [2, 0, 0, 2, 0],
        [2, 2, 0, 2, 0],
        [0, 2, 0, 2, 0],
    ]
    expected = [
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 0],
        [8, 8, 8, 8, 0],
        [0, 8, 8, 8, 0],
    ]
    assert gen.rule_mirror(source) == expected
    assert expected != _bbox_fill(source)


def test_every_declared_profile_emits_shortcut_counterexamples():
    for profile in PROFILES:
        for seed in range(20):
            grid = gen.generate(seed, seed % 7, difficulty="medium", scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            answer = gen.rule_mirror(grid)
            assert answer != _bbox_fill(grid)
            assert answer != _global_row_close(grid)
            assert answer != _recolor_only(grid)
            assert answer != _vertical_close(grid)
            assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())


def test_default_schedule_covers_every_profile_in_each_band_and_stays_on_canonical_scale():
    for band in ("easy", "medium", "hard"):
        observed = []
        for sample_index in range(8):
            expected = gen.schedule_profile(123, sample_index, difficulty=band)
            grid = gen.generate(123, sample_index, difficulty=band)
            observed.append(gen.observe_overrides(grid)["scene_profile"])
            assert observed[-1] == expected
            assert (len(grid), len(grid[0])) in {(8, 14), (9, 15)}
        assert set(observed) == set(PROFILES)


def test_override_contract_rejects_unknown_and_invalid_values():
    for kwargs in ({"unknown_axis": 1}, {"scene_profile": "not_a_profile"}):
        try:
            gen.generate(1, 0, **kwargs)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"override should reject: {kwargs}")


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(17, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(17, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(17, 4, difficulty="hard") == second


def test_lesson_identifiability_for_generated_two_demo_curriculum():
    demos = []
    for index in range(2):
        grid = gen.generate(44, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(44, 2, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


def test_mutation_fixtures_are_rejected_without_mutating_inputs():
    for name, fixture in gen.mutation_fixtures():
        snapshot = copy.deepcopy(fixture)
        assert gen.self_check(fixture), name
        assert fixture == snapshot
