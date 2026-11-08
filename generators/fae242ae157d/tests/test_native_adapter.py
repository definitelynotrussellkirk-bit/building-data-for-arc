"""Tests-first contracts for the separate native three-object ranking family."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators/fae242ae157d/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PARAMETRIC))
POLICIES = ("area", "nearest_largest", "farthest_largest")
CANONICAL_SHA = "ce7e86577c9974e15935224c415054977e6b7ffb2d2a5d712842ed39b1dff1e4"


def setting(name):
    return {"ranking_policy": name}


@pytest.fixture(scope="module")
def family():
    return importlib.import_module("native_family")


@pytest.fixture(scope="module")
def adapter():
    return importlib.import_module("adapter")


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    with _local_imports(RUNTIME, PARAMETRIC):
        apply_program, identity, bridge = _real_evaluator(RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        rows = [json.loads(line) for line in handle]
    selected = [row for row in rows if row.get("task_id") == "fae242ae157d"]
    assert len(selected) == 1
    return selected[0]


def literal_scene(index):
    """Coordinates/expected role orders authored independently of the family."""
    if index == 0:
        shape = (10, 14)
        anchor = {(r, c) for r in (5, 6, 7) for c in (9, 10, 11)}
        medium = {(1, 1), (2, 1), (3, 1), (4, 1), (4, 2), (4, 3), (4, 4)}
        small = {(5, 6), (6, 6), (6, 7)}
        nearest = "small"
    elif index == 1:
        shape = (10, 14)
        anchor = {(r, c) for r in (6, 7, 8) for c in (9, 10, 11)}
        medium = {(1, 6), (2, 6), (3, 6), (4, 6), (4, 7), (4, 8), (4, 9)}
        small = {(1, 1), (1, 2), (2, 1)}
        nearest = "medium"
    else:
        assert index == 2
        shape = (10, 17)
        anchor = {(r, c) for r in (1, 2, 3, 4) for c in (1, 2, 3, 4)}
        anchor |= {(4, c) for c in (5, 6, 7, 8, 9, 10, 11, 12)}
        medium = {(7, 2), (7, 3), (8, 2), (8, 3)}
        small = {(3, 14), (4, 14), (4, 15)}
        nearest = "small"
    cells = {"anchor": anchor, "medium": medium, "small": small}
    grid = [[0] * shape[1] for _ in range(shape[0])]
    for name, color in (("anchor", 7), ("medium", 5), ("small", 8)):
        for r, c in cells[name]:
            grid[r][c] = color
    expected = {}
    for policy in POLICIES:
        if policy == "area":
            colors = {"anchor": 4, "medium": 3, "small": 2}
        else:
            other = "medium" if nearest == "small" else "small"
            colors = {"anchor": 4, nearest: 2, other: 3}
            if policy == "farthest_largest":
                colors[nearest], colors[other] = 3, 2
        output = [[0] * shape[1] for _ in range(shape[0])]
        for name, positions in cells.items():
            for r, c in positions:
                output[r][c] = colors[name]
        expected[policy] = output
    return grid, cells, expected


def test_default_program_is_byte_exact_canonical_and_adapter_delegates(family, adapter):
    canonical = canonical_row()["program_solution"]
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA
    assert family.program(setting("area")) == canonical
    for policy in POLICIES:
        assert adapter.program(setting(policy)) == family.program(setting(policy))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_literal_anchor_and_distance_semantics(family, racket, index):
    grid, cells, expected = literal_scene(index)
    unchanged = copy.deepcopy(grid)
    assert len(cells["anchor"]) > len(cells["medium"]) > len(cells["small"])
    if index < 2:
        assert len(cells["anchor"]) == 9 and len(cells["medium"]) == 7
        positions = cells["medium"]
        box_height = max(r for r, c in positions) - min(r for r, c in positions) + 1
        box_width = max(c for r, c in positions) - min(c for r, c in positions) + 1
        assert box_height * box_width == 16
    for policy in POLICIES:
        assert family.apply_claim(grid, setting(policy)) == expected[policy]
        assert racket(family.program(setting(policy)), grid) == expected[policy]
    assert grid == unchanged


def cell_distance(left, right):
    return min(abs(r1 - r2) + abs(c1 - c2) for r1, c1 in left for r2, c2 in right)


def components(grid):
    """Independent geometry check; adjacent nonzero colors must not merge objects."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        found, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    found.add(point)
                    stack.append(point)
        groups.append(found)
    return groups


def check_shared_grammar(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width
               and all(type(value) is int and 0 <= value <= 9 for value in row) for row in grid)
    groups = components(grid)
    assert len(groups) == 3
    assert all(len({grid[r][c] for r, c in group}) == 1 for group in groups)
    assert len({len(group) for group in groups}) == 3
    ordered = sorted(groups, key=len)
    assert cell_distance(ordered[0], ordered[2]) != cell_distance(ordered[1], ordered[2])
    return groups


def test_authored_fixtures_are_lawful_and_separate_cell_distance_from_centroid():
    expected_distances = ((6, 2), (2, 12), (3, 2))
    for index in range(3):
        grid, cells, expected = literal_scene(index)
        check_shared_grammar(grid)
        assert (cell_distance(cells["anchor"], cells["medium"]),
                cell_distance(cells["anchor"], cells["small"])) == expected_distances[index]
    _, cells, _ = literal_scene(2)
    centers = {name: (sum(r for r, c in points) / len(points),
                      sum(c for r, c in points) / len(points)) for name, points in cells.items()}
    center_distances = {name: sum(abs(a - b) for a, b in zip(centers["anchor"], centers[name]))
                        for name in ("small", "medium")}
    assert center_distances["small"] > center_distances["medium"]


def test_default_replays_all_four_official_pairs_in_protected_racket(family, racket):
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        expected = racket(family.program(setting("area")), pair["input"])
        assert expected == pair["output"]
        assert family.apply_claim(pair["input"], setting("area")) == expected


@pytest.mark.parametrize("bad", [None, {}, {"ranking_policy": True},
                                 {"ranking_policy": "nearest"},
                                 {"ranking_policy": "area", "extra": 1}])
def test_settings_require_one_exact_declared_key(family, bad):
    grid, _, _ = literal_scene(0)
    for action in (lambda: family.program(bad), lambda: family.generate(0, bad, 3, 1),
                   lambda: family.apply_claim(grid, bad), lambda: family.describe(grid, bad),
                   lambda: family.rivals(bad)):
        with pytest.raises((ValueError, TypeError)):
            action()


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 1.5, "1", None])
def test_seed_validation_is_literal_and_bounded(family, seed):
    with pytest.raises((ValueError, TypeError)):
        family.generate(seed, setting("area"), 3, 1)


@pytest.mark.parametrize("demos,queries", [(2, 1), (7, 1), (True, 1), (3.0, 1),
                                          (3, 0), (3, 5), (3, True), (3, 1.0)])
def test_demo_query_bounds_are_independent_and_strict(family, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        family.generate(0, setting("area"), demos, queries)


def test_malformed_grids_and_shared_grammar_violations_are_rejected(family):
    valid, cells, _ = literal_scene(0)
    malformed = [[], [[]], tuple(valid), [tuple(row) for row in valid],
                 valid[:-1] + [[0]], "not-a-grid", valid + [[0] * len(valid[0]) for _ in range(21)]]
    for value in (True, -1, 10, 1.0, "7"):
        grid = copy.deepcopy(valid)
        r, c = next(iter(cells["anchor"]))
        grid[r][c] = value
        malformed.append(grid)
    two_objects = copy.deepcopy(valid)
    for r, c in cells["small"]:
        two_objects[r][c] = 0
    malformed.append(two_objects)
    four_objects = copy.deepcopy(valid)
    four_objects[0][0] = 6
    malformed.append(four_objects)
    tied_areas = [[0] * 12 for _ in range(10)]
    tied_areas[1][1] = 7
    tied_areas[1][4] = 8
    tied_areas[5][8] = tied_areas[6][8] = 9
    malformed.append(tied_areas)
    tied_distances = [[0] * 12 for _ in range(10)]
    tied_distances[2][5] = 7
    tied_distances[4][3] = tied_distances[5][3] = 8
    tied_distances[4][5] = tied_distances[5][5] = tied_distances[6][5] = 9
    malformed.append(tied_distances)
    for grid in malformed:
        for policy in POLICIES:
            with pytest.raises((ValueError, TypeError)):
                family.apply_claim(grid, setting(policy))
            with pytest.raises((ValueError, TypeError)):
                family.describe(grid, setting(policy))


def test_claims_are_input_pure_and_return_fresh_outputs(family):
    grid, _, expected = literal_scene(1)
    unchanged = copy.deepcopy(grid)
    for policy in POLICIES:
        result = family.apply_claim(grid, setting(policy))
        result[0][0] = 9
        assert family.apply_claim(grid, setting(policy)) == expected[policy]
        description = family.describe(grid, setting(policy))
        assert isinstance(description, dict)
        json.dumps(description)
        assert grid == unchanged


def test_full_banks_are_deterministic_matched_and_have_independent_prefixes(family, adapter):
    before_rng = random.getstate()
    reference = None
    for policy in POLICIES:
        selected = setting(policy)
        full = family.generate(7, selected, 6, 4)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert full == family.generate(7, selected, 6, 4)
        for demos, queries in ((3, 1), (3, 4), (6, 1), (4, 2), (5, 3)):
            smaller = family.generate(7, selected, demos, queries)
            assert smaller["train"] == full["train"][:demos]
            assert smaller["test"] == full["test"][:queries]
        inputs = [pair["input"] for pair in full["train"] + full["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == 10
        if reference is None:
            reference = copy.deepcopy(inputs)
        else:
            assert inputs == reference
        for grid in inputs:
            check_shared_grammar(grid)
        assert adapter.generate(7, selected, 3, 1) == family.generate(7, selected, 3, 1)
        untouched = copy.deepcopy(full)
        full["train"][0]["input"][0][0] = 9 - full["train"][0]["input"][0][0]
        full["test"][0]["output"][0][0] = 9 - full["test"][0]["output"][0][0]
        assert family.generate(7, selected, 6, 4) == untouched
    assert random.getstate() == before_rng
    assert len(family.generate(2**63 - 1, setting("area"), 3, 1)["train"]) == 3


def test_three_demonstrations_identify_policy_without_query_answers(family):
    episodes = {policy: family.generate(0, setting(policy), 3, 4) for policy in POLICIES}
    for selected, episode in episodes.items():
        for candidate in POLICIES:
            fits = all(family.apply_claim(pair["input"], setting(candidate)) == pair["output"]
                       for pair in episode["train"])
            assert fits == (candidate == selected)


@pytest.mark.parametrize("policy", ["nearest_largest", "farthest_largest"])
def test_three_demos_refute_top_left_distance_rival(family, racket, policy):
    """Strengthen demo support against one finite rival, without query answers."""
    selected = setting(policy)
    episode = family.generate(0, selected, 3, 1)
    intended = family.program(selected)
    rival = family.rivals(selected)["distance_top_left"]
    agreements = []
    for pair in episode["train"]:
        actual = racket(intended, pair["input"])
        assert pair["output"] == actual
        agreements.append(racket(rival, pair["input"]) == actual)
    assert not all(agreements), (
        f"distance_top_left survives all three {policy} demonstrations: {agreements}; "
        "this is a finite demonstration-support check, not a query-error claim"
    )


def test_episode_labels_and_substantive_boundary_stress_match_protected_racket(family, racket):
    for policy in POLICIES:
        selected = setting(policy)
        episode = family.generate(0, selected, 3, 4)
        stress = episode["test"][3]["input"]
        assert len(stress) == len(stress[0]) == 30
        assert sum(value != 0 for row in stress for value in row) >= 200
        assert any(stress[0]) and any(stress[-1])
        assert any(row[0] for row in stress) and any(row[-1] for row in stress)
        for pair in episode["train"] + episode["test"]:
            check_shared_grammar(pair["input"])
            expected = racket(family.program(selected), pair["input"])
            assert pair["output"] == expected
            assert family.apply_claim(pair["input"], selected) == expected
            assert len(expected) == len(pair["input"])
            assert len(expected[0]) == len(pair["input"][0])


def test_rivals_are_complete_executable_racket_sources(family, racket):
    grid, _, _ = literal_scene(0)
    seen = set()
    for policy in POLICIES:
        rivals = family.rivals(setting(policy))
        assert isinstance(rivals, dict) and rivals
        assert all(type(name) is str and name for name in rivals)
        for program in rivals.values():
            assert type(program) is str and program.strip()
            if program in seen:
                continue
            seen.add(program)
            result = racket(program, grid)
            assert type(result) is list and 1 <= len(result) <= 30
            assert type(result[0]) is list and 1 <= len(result[0]) <= 30
            assert all(type(row) is list and len(row) == len(result[0])
                       and all(type(value) is int and 0 <= value <= 9 for value in row)
                       for row in result)


def test_public_projection_hides_private_data_answers_and_future_queries(family):
    selected = setting("nearest_largest")
    episode = family.generate(0, selected, 3, 4)
    unchanged = copy.deepcopy(episode)
    for index in range(4):
        public = family.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert public["train"] == [{"input": pair["input"], "output": pair["output"]}
                                   for pair in episode["train"]]
        assert public["test"] == [{"input": episode["test"][index]["input"]}]
    first = family.public_turn(episode, 0)
    assert first == family.public_turn(family.generate(0, selected, 3, 1), 0)
    tainted = copy.deepcopy(episode)
    tainted.update(seed=999, settings=setting("farthest_largest"), program="hidden-program-marker")
    tainted["test"][0]["output"] = [[9]]
    tainted["test"][1]["input"] = [[8]]
    assert family.public_turn(tainted, 0) == first
    first["train"][0]["input"][0][0] = 9 - first["train"][0]["input"][0][0]
    first["train"][0]["output"][0][0] = 9 - first["train"][0]["output"][0][0]
    first["test"][0]["input"][0][0] = 9 - first["test"][0]["input"][0][0]
    assert episode == unchanged
    for bad in (-1, 4, True, 0.0, None):
        with pytest.raises((ValueError, TypeError, IndexError)):
            family.public_turn(episode, bad)
