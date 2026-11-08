"""Independent repair regressions for ARC task c59d7541b22e."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "c59d7541b22e"
ROOT = find_root(__file__)
HOME = next(path for path in (
    ROOT / "generators" / TASK,
    ROOT / "puzzle_generators" / "per_puzzle" / TASK,
) if (path / "generator.py").is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_c59d7541b22e", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def oracle(grid):
    """One simultaneous pass over the original input, independent of generator helpers."""
    out = deepcopy(grid)
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            cells = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            values = [grid[rr][cc] for rr, cc in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                rr, cc = next(point for point, value in zip(cells, values) if value == 0)
                out[rr][cc] = nonzero[0]
    return out


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        todo = [start]
        cells = {start}
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = r + dr, c + dc
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append((color, cells))
    return result


def bbox_rival(grid):
    out = deepcopy(grid)
    for color, cells in components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                out[r][c] = color
    return out


def iterative_rival(grid):
    out = deepcopy(grid)
    while True:
        nxt = oracle(out)
        if nxt == out:
            return out
        out = nxt


def authority_hash():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
    assert len(programs) == 1
    return hashlib.sha256(" ".join(next(iter(programs)).split()).encode()).hexdigest()[:12]


def labeled(grid):
    return {"input": grid, "output": oracle(grid)}


def test_authority_pin_canonical_acceptance_and_independent_oracle():
    assert GEN.RULE_HASH == authority_hash() == "014f3ef40cee"
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_canonical_shortcuts_really_fit_every_official_pair():
    shortcuts = GEN.CANONICAL_SHORTCUTS
    assert {"component_bounding_boxes", "iterate_until_stable"} <= set(shortcuts)
    for name, rival in shortcuts.items():
        for pair in canonical_pairs(TASK, root=ROOT):
            original = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == original


def test_exact_counterexample_separates_one_pass_rule_from_strongest_shortcuts():
    grid = [
        [2, 2, 2],
        [2, 0, 0],
    ]
    expected = [
        [2, 2, 2],
        [2, 2, 0],
    ]
    overfilled = [
        [2, 2, 2],
        [2, 2, 2],
    ]
    assert oracle(grid) == expected
    assert bbox_rival(grid) == overfilled
    assert iterative_rival(grid) == overfilled
    assert GEN.CANONICAL_SHORTCUTS["component_bounding_boxes"](grid) == overfilled
    assert GEN.CANONICAL_SHORTCUTS["iterate_until_stable"](grid) == overfilled


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_is_deterministic_lawful_and_semantically_useful(difficulty):
    seen = set()
    for seed in range(6):
        for sample_index in range(6):
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            assert grid == GEN.generate(seed, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert oracle(grid) != grid
            observed = GEN.observe_overrides(grid)
            expected_profile = GEN.schedule_profile(seed, sample_index, difficulty)
            assert observed["profile"] == expected_profile
            if expected_profile == "canonical":
                assert (len(grid), len(grid[0])) in {(7, 7), (8, 8)}
            else:
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert rival(deepcopy(grid)) != oracle(grid), (name, difficulty, seed, sample_index)
            seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) >= 24


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical", "witness"])
@pytest.mark.parametrize("h,w", [(7, 7), (7, 16), (14, 7), (14, 16), (9, 11)])
def test_exact_axes_are_honored_and_observable(difficulty, profile, h, w):
    requested = {"grid_h": h, "grid_w": w, "profile": profile}
    grid = GEN.generate(19, 23, difficulty=difficulty, **requested)
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("overrides", [
    {"misspelled": 1}, {"grid_h": True}, {"grid_w": 9.5},
    {"grid_h": 6}, {"grid_h": 15}, {"grid_w": 6}, {"grid_w": 17},
    {"profile": "typo"}, {"profile": 1},
])
def test_unknown_or_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("bad", [
    None, "000", [], [[]], [[0], [0, 2]], [[True]], [[-1]], [[10]],
    [[0] * 7 for _ in range(7)],
    [[4] * 7 for _ in range(7)],
    [[0, 0, 0], [0, 4, 4], [0, 0, 0]],
    [[0, 0, 0], [0, 4, 4], [0, 4, 4]],
])
def test_validator_rejects_malformed_identity_or_nonlesson_inputs(bad):
    assert GEN.self_check(bad)


def test_every_rotated_lesson_refutes_declared_competitors():
    n = GEN.EXAMPLES_NEEDED
    assert n >= 3
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(4):
                grids = [GEN.generate(seed, start + j, difficulty=difficulty) for j in range(n + 1)]
                pairs = [labeled(grid) for grid in grids]
                for query_index in range(n + 1):
                    demos = [pair for j, pair in enumerate(pairs) if j != query_index]
                    query = pairs[query_index]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        difficulty, seed, start, query_index,
                    )
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), (
                            difficulty, seed, start, query_index, name,
                        )


def test_declared_semantic_witnesses_fire_on_forced_witness_profile():
    for seed in range(8):
        grid = GEN.generate(seed, seed + 5, profile="witness")
        assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())


def test_generation_is_global_random_pure_and_rows_are_not_aliased():
    random.seed(1234567)
    state = random.getstate()
    first = GEN.generate(91, 17)
    second = GEN.generate(91, 17)
    assert random.getstate() == state
    assert first == second and first is not second
    assert len({id(row) for row in first}) == len(first)
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_default_probe_path_exercises_declared_span_and_noninert_difficulty():
    draws = {
        band: [GEN.generate(seed, seed, difficulty=band) for seed in range(1, 9)]
        for band in ("easy", "medium", "hard")
    }
    assert any(
        draws["easy"][index] != draws["medium"][index]
        or draws["medium"][index] != draws["hard"][index]
        for index in range(8)
    )
    heights = [len(grid) for grids in draws.values() for grid in grids]
    widths = [len(grid[0]) for grids in draws.values() for grid in grids]
    assert max(heights) - min(heights) + 1 >= 3
    assert max(widths) - min(widths) + 1 >= 4


def test_each_semantic_witness_names_the_rival_it_refutes():
    assert GEN.WITNESS_RIVALS == {name: [name] for name in GEN.SEMANTIC_RIVALS}
