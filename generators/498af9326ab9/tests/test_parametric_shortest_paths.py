"""Behavioral checks for the opt-in any/every shortest-path family."""
from collections import deque
import copy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ADAPTER = HOME / "workspace" / "parametric" / "adapter.py"


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER.is_file(), "The native shortest-path adapter must be implemented"
    spec = importlib.util.spec_from_file_location("tested_shortest_path_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distance(grid, blocked=None):
    start = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    goal = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (r, c), depth = queue.popleft()
        if (r, c) == goal:
            return depth
        for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and grid[nr][nc] != 5 and (nr, nc) != blocked and (nr, nc) not in seen):
                seen.add((nr, nc))
                queue.append(((nr, nc), depth+1))
    return float("inf")


def test_default_program_is_exact_canonical(adapter):
    from reviewer_support import canonical_path, find_root
    with canonical_path(find_root(__file__)).open() as handle:
        canonical = next(row["program_solution"] for row in map(json.loads, handle)
                         if row.get("task_id") == "498af9326ab9")
    assert adapter.program({"path_mode": "any"}) == canonical
    assert adapter.program({"path_mode": "every"}) != canonical


@pytest.mark.parametrize("mode", ["any", "every"])
def test_count_boundaries_matched_inputs_and_query_prefix(adapter, mode):
    settings = {"path_mode": mode}
    for demos in range(2, 7):
        episode = adapter.generate(17, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        all_inputs = [json.dumps(p["input"]) for s in ("train", "test") for p in episode[s]]
        assert len(all_inputs) == len(set(all_inputs))
        assert all(type(v) is int for s in ("train", "test") for p in episode[s]
                   for grid in p.values() for row in grid for v in row)
        single = adapter.generate(17, settings, demos, 1)
        assert single["train"] == episode["train"]
        assert single["test"] == episode["test"][:1]
        other = adapter.generate(17, {"path_mode": "every" if mode == "any" else "any"}, demos, 4)
        for split in ("train", "test"):
            assert [p["input"] for p in episode[split]] == [p["input"] for p in other[split]]
        assert any(a["output"] != b["output"] for a, b in zip(episode["train"], other["train"]))
        assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in episode["test"])


def test_mandatory_cells_match_independent_vertex_deletion_oracle(adapter):
    for seed in (0, 17):
        grid = adapter.generate(seed, {"path_mode": "every"}, 2, 1)["train"][0]["input"]
        output = adapter.solve(grid, "every")
        best = distance(grid)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                expected = 8 if value == 0 and distance(grid, (r, c)) > best else value
                assert output[r][c] == expected


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, 4.0)])
def test_invalid_counts_fail_explicitly(adapter, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(0, {"path_mode": "any"}, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"path_mode": "sometimes"}, {"path_mode": True},
                                      {"path_mode": "any", "leak": 1}])
def test_invalid_settings_fail_explicitly(adapter, settings):
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 3, 4)


def test_seed_and_input_validation_and_no_mutation(adapter):
    for seed in (-1, True, 2**63, 1.0):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"path_mode": "any"}, 3, 4)
    episode = adapter.generate(4, {"path_mode": "any"}, 3, 4)
    before = copy.deepcopy(episode)
    for split in ("train", "test"):
        for pair in episode[split]:
            adapter.solve(pair["input"], "every")
    assert before == episode
    for grid in ([], [[True]], [[1, 0], [2]], [[1, 2]], [[1, 1], [2, 0]]):
        with pytest.raises(ValueError):
            adapter.solve(grid, "every")


def test_public_projection_is_private_metadata_invariant(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = adapter.generate(29, {"path_mode": "any"}, 3, 4)
    first = adapter.public_turn(episode, 0)
    assert len(first["test"]) == 1
    assert set(first) == {"train", "test"}
    assert set(first["test"][0]) == {"input"}
    assert first == adapter.public_turn(adapter.generate(29, {"path_mode": "any"}, 3, 1), 0)
    mutated = copy.deepcopy(episode)
    mutated["seed"] = 111
    mutated["settings"] = {"path_mode": "every"}
    mutated["program_solution"] = "private arbitrary program"
    for pair in mutated["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(mutated)
    assert public_challenge_id(episode) == public_challenge_id(mutated)
    assert adapter.public_turn(mutated, 0) == first
    with pytest.raises(ValueError):
        adapter.public_turn(episode, True)


def test_two_demo_teaching_on_independent_seeds(adapter):
    spec = importlib.util.spec_from_file_location("tested_shortest_path_audit", ADAPTER.with_name("audit.py"))
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    for seed in (0, 1, 2, 3, 17, 29, 71, 127):
        for mode in adapter.MODES:
            episode = adapter.generate(seed, {"path_mode": mode}, 2, 4)
            for name in audit.RIVALS:
                fits = all(audit.rival(p["input"], mode, name) == p["output"] for p in episode["train"])
                if fits:
                    assert all(audit.rival(p["input"], mode, name) == p["output"] for p in episode["test"]), (seed, mode, name)


def test_bounded_sampler_reliability(adapter):
    # 192 independent requests; no assertion of exhaustive seed coverage.
    for seed in range(32):
        for mode in adapter.MODES:
            for demos in (2, 3, 6):
                episode = adapter.generate(seed, {"path_mode": mode}, demos, 4)
                assert len(episode["train"]) == demos and len(episode["test"]) == 4
                signatures = [tuple(map(tuple,p["input"])) for split in ("train","test") for p in episode[split]]
                assert len(signatures) == len(set(signatures))
