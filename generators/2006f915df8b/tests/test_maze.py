"""Behavioral regression tests for the shortest-corridor sampler."""
from collections import deque
from copy import deepcopy
import importlib
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "2006f915df8b"
candidate = Path(os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py"))
if candidate.is_file():
    spec = importlib.util.spec_from_file_location("maze_under_test", candidate)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
else:
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")

PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def shortest(grid):
    """Independent distance/path-count oracle; never used for emitted labels."""
    start, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    goal, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    queue = deque([start])
    distance, ways, parent = {start: 0}, {start: 1}, {}
    while queue:
        r, c = queue.popleft()
        for dr, dc in DELTAS:
            nxt = r + dr, c + dc
            nr, nc = nxt
            if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])) or grid[nr][nc] == 5:
                continue
            nd = distance[r, c] + 1
            if nxt not in distance:
                distance[nxt], ways[nxt], parent[nxt] = nd, ways[r, c], (r, c)
                queue.append(nxt)
            elif distance[nxt] == nd:
                ways[nxt] += ways[r, c]
    if goal not in distance:
        return None, 0, deepcopy(grid)
    out, at = deepcopy(grid), goal
    while at != start:
        r, c = at
        if out[r][c] == 0:
            out[r][c] = 8
        at = parent[at]
    return distance[goal], ways[goal], out


def cycle_rank(grid):
    vertices = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 5}
    edges = sum((r + dr, c + dc) in vertices for r, c in vertices for dr, dc in ((1, 0), (0, 1)))
    components, remaining = 0, set(vertices)
    while remaining:
        components += 1
        queue = [remaining.pop()]
        for r, c in queue:
            for dr, dc in DELTAS:
                at = r + dr, c + dc
                if at in remaining:
                    remaining.remove(at)
                    queue.append(at)
    return edges - len(vertices) + components


def test_pins_the_unchanged_canonical_authority():
    assert getattr(gen, "RULE_HASH", None) == "24791e9d8fc8"


def test_declared_canonical_shortcut_fits_every_canonical_pair():
    assert "goal_greedy" in gen.CANONICAL_SHORTCUTS
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_none_overrides_replay_the_omitted_defaults(band):
    for seed in (0, 7, 91):
        for index in range(4):
            expected = gen.generate(seed, index, difficulty=band)
            assert gen.generate(seed, index, difficulty=band, grid_h=None, grid_w=None) == expected


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(7, 8), (12, 14), (11, 12)])
def test_exact_dimensions_keep_the_full_domain_in_every_band(band, shape):
    h, w = shape
    grid = gen.generate(37, 2, difficulty=band, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == shape
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}


@pytest.mark.parametrize("key,value", [
    ("grid_h", True), ("grid_h", 8.0), ("grid_h", "8"),
    ("grid_h", 6), ("grid_h", 13), ("grid_w", 7), ("grid_w", 15),
    ("typo", 1), ("palette_kind", "warm"), ("palette_size", 3),
    ("anchor_corner", True), ("asymmetry_force", True),
    ("position_bias", "varied"), ("n_distinct_colors", 3), ("texture", "cool"),
])
def test_bad_and_retired_controls_raise(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("pair", PAIRS, ids=[f"{p['split']}{p['pair_index']}" for p in PAIRS])
def test_canonical_inputs_remain_valid_including_tied_paths(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert shortest(pair["input"])[0] >= 3


def test_canonical_ties_are_not_rejected_as_sampler_invalidity():
    assert shortest(PAIRS[0]["input"])[1] == 3
    assert shortest(PAIRS[-1]["input"])[1] == 3
    assert gen.self_check(PAIRS[0]["input"]) == []


@pytest.mark.parametrize("grid", [None, [], [[]], [[5], [5, 5]], [[2, 0, False, 3]], [[2, 0, 0.0, 3]]])
def test_malformed_grids_return_actionable_reasons(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_size_floor_and_full_palette_are_in_each_band(band):
    grids = [gen.generate(2100 + i, i, difficulty=band) for i in range(20)]
    assert any((len(g), len(g[0])) in {(11, 12), (11, 11), (12, 11), (10, 12)} for g in grids)
    assert all({v for row in g for v in row} == {0, 2, 3, 5} for g in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_witness_draws_refute_all_declared_rivals(band):
    rivals = gen.LESSON_COMPETITORS
    assert len([name for name in rivals if name.startswith("dfs_")]) == 24
    assert {"flood_open", "fewest_turns", "goal_greedy"} <= set(rivals)
    for index in range(0, 32, 2):
        grid = gen.generate(6100 + index, index, difficulty=band)
        distance, ways, answer = shortest(grid)
        assert ways == 1 and distance >= 7
        assert cycle_rank(grid) >= 2
        assert all(rival(grid) != answer for rival in rivals.values())


def test_random_slots_include_trees_and_free_endpoint_positions():
    grids = [gen.generate(9700 + i, i, difficulty="medium") for i in range(1, 64, 2)]
    assert any(cycle_rank(g) == 0 for g in grids)
    assert any(cycle_rank(g) > 0 for g in grids)
    positions = []
    for grid in grids:
        assert gen.self_check(grid) == []
        assert shortest(grid)[1] == 1
        s, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
        t, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
        positions.append((s, t))
    assert any(s[1] > t[1] for s, t in positions)
    assert any(s[0] < t[0] for s, t in positions)
    assert any(s[0] > t[0] for s, t in positions)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_cyclic_start_and_query_position_has_refuting_demonstrations(band):
    for seed in (0, 17, 99):
        for start in range(4):
            pairs = []
            for index in range(start, start + 4):
                grid = gen.generate(seed, index, difficulty=band)
                assert shortest(grid)[1] == 1
                pairs.append({"input": grid, "output": shortest(grid)[2]})
            for query in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if all(rival(p["input"]) == p["output"] for p in demos):
                        assert rival(pairs[query]["input"]) == pairs[query]["output"], name


def test_replay_is_deterministic_and_returns_independent_grids():
    first = gen.generate(314159, 2, difficulty="hard")
    expected = deepcopy(first)
    first[0][0] = 9
    assert gen.generate(314159, 2, difficulty="hard") == expected


def test_rejected_duplicate_keeps_every_query_rotation_teachable():
    # The prior repair emitted the same witness at indices 2 and 4 for this
    # seed. Production accepted [1,2,3,5]; holding out index 2 exposed a rival.
    pairs, seen, index = [], set(), 1
    while len(pairs) < 4 and index < 32:
        grid = gen.generate(6484, index, difficulty="easy", grid_h=7, grid_w=8)
        key = tuple(tuple(row) for row in grid)
        if key not in seen:
            seen.add(key)
            pairs.append({"input": grid, "output": shortest(grid)[2]})
        index += 1
    assert len(pairs) == 4
    for query in range(4):
        demos = [pair for i, pair in enumerate(pairs) if i != query]
        for name, rival in gen.LESSON_COMPETITORS.items():
            if all(rival(p["input"]) == p["output"] for p in demos):
                assert rival(pairs[query]["input"]) == pairs[query]["output"], name
