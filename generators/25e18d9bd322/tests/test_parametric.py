"""Behavioral contract for the native nearest-object distance family."""
import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/adapter.py"
TASK = "25e18d9bd322"


def test_native_adapter_exists():
    assert SOURCE.is_file(), "Implement the native nearest-object adapter"


@pytest.fixture(scope="module")
def adapter():
    spec = importlib.util.spec_from_file_location("tested_nearest_adapter", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_default_and_canonical_pairs(adapter):
    with canonical_path(find_root(__file__)).open() as stream:
        canonical = next(r["program_solution"] for r in map(json.loads, stream) if r.get("task_id") == TASK)
    assert adapter.program({"metric": "manhattan"}) == canonical
    assert adapter.program({"metric": "chebyshev"}) != canonical
    for pair in canonical_pairs(TASK, root=find_root(__file__)):
        assert adapter.solve(pair["input"], "manhattan") == pair["output"]


def test_teaching_changes_selected_object_and_keeps_only_its_cells(adapter):
    m = adapter.generate(17, {"metric": "manhattan"}, 2, 4)
    c = adapter.generate(17, {"metric": "chebyshev"}, 2, 4)
    first_m, first_c = m["train"][0]["output"], c["train"][0]["output"]
    a = first_m[0][0]
    assert first_m == [[a, a, a]] + [[a, 0, 0] for _ in range(8)]
    b = first_c[0][-1]
    assert first_c == [[0] * 7 + [b] for _ in range(13)] + [[b] * 8]
    assert first_m != first_c
    second = m["train"][1]["output"]
    assert second == c["train"][1]["output"]
    ink = second[0][-1]
    expected = [[0] * 8 + [ink] for _ in range(7)] + [[ink] * 9]
    expected += [[ink, 0, 0, 0, ink, 0, 0, 0, 0] for _ in range(3)]
    expected += [[ink] * 5 + [0] * 4]
    assert second == expected
    assert second[5][7] == 0  # Original marker lies inside this bbox.
    assert second[9][2] == 0  # Same-color disconnected intruder is removed.


@pytest.mark.parametrize("metric", ["manhattan", "chebyshev"])
def test_complete_key_tie_uses_discovery_order(adapter, metric):
    grid = [[0] * 12 for _ in range(7)]
    grid[0][9] = 9
    a = {(1, c) for c in range(2, 9)} | {(2, 8)} | {(3, c) for c in range(4, 9)}
    b = {(r, 10) for r in range(1, 5)} | {(5, c) for c in range(2, 11)}
    for cells, color in ((a, 7), (b, 2)):
        for r, c in cells:
            grid[r][c] = color
    assert adapter.solve(grid, metric) == [[7] * 7, [0] * 6 + [7], [0, 0] + [7] * 5]


@pytest.mark.parametrize("metric", ["manhattan", "chebyshev"])
def test_minimum_domain_marker_contact(adapter, metric):
    grid = [[9, 3, 0, 0, 0], [0, 3, 0, 0, 0], [0] * 5, [0] * 5, [0, 0, 0, 0, 4]]
    assert adapter.solve(grid, metric) == [[3], [3]]


@pytest.mark.parametrize("metric", ["manhattan", "chebyshev"])
def test_counts_matched_inputs_large_content_and_turn_projection(adapter, metric):
    other = "chebyshev" if metric == "manhattan" else "manhattan"
    for demos in range(2, 7):
        episode = adapter.generate(29, {"metric": metric}, demos, 4)
        matched = adapter.generate(29, {"metric": other}, demos, 4)
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        inputs = [tuple(map(tuple, p["input"])) for split in ("train", "test") for p in episode[split]]
        assert len(inputs) == len(set(inputs))
        for split in ("train", "test"):
            assert [p["input"] for p in episode[split]] == [p["input"] for p in matched[split]]
        for queries in (1, 2, 3):
            shorter = adapter.generate(29, {"metric": metric}, demos, queries)
            assert adapter.public_turn(shorter, 0) == adapter.public_turn(episode, 0)
        big = episode["test"][2]["input"]
        assert len(big) == len(big[0]) == 30
        assert sum(v not in (0, 9) for row in big for v in row) >= 250
        assert sum(v not in (0, 9) for row in big[1:-1] for v in row[1:-1]) >= 150


def test_private_metadata_never_affects_public_bytes(adapter):
    episode = adapter.generate(0, {"metric": "chebyshev"}, 3, 4)
    original = copy.deepcopy(episode)
    turn = adapter.public_turn(episode, 0)
    assert set(turn) == {"train", "test"} and len(turn["test"]) == 1
    assert set(turn["test"][0]) == {"input"}
    altered = copy.deepcopy(episode)
    altered.update(seed=-1, settings={"private": True}, program_solution="private")
    for pair in altered["train"]:
        pair.update(seed=777, settings={"private": True}, program_solution="private")
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(altered)
    assert public_challenge_id(episode) == public_challenge_id(altered)
    assert adapter.public_turn(altered, 0) == turn
    assert episode == original
    with pytest.raises(ValueError):
        adapter.public_turn(episode, True)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, 4.0)])
def test_reject_invalid_counts(adapter, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(0, {"metric": "manhattan"}, demos, queries)


def test_reject_bad_settings_seeds_and_grids(adapter):
    for settings in ({}, {"metric": "euclidean"}, {"metric": True}, {"metric": "manhattan", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.generate(0, settings, 2, 4)
    for seed in (-1, True, 1.0, 2**63):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"metric": "manhattan"}, 2, 4)
    good = adapter.generate(0, {"metric": "manhattan"}, 2, 1)["train"][0]["input"]
    bad = copy.deepcopy(good); bad[0][0] = True
    with pytest.raises(ValueError): adapter.solve(bad)
    bad = [[0] * 5 for _ in range(5)]
    with pytest.raises(ValueError): adapter.solve(bad)
    bad = copy.deepcopy(good); bad[0][0] = 9
    with pytest.raises(ValueError): adapter.solve(bad)


def test_reproducible_fresh_results_without_global_rng_changes(adapter):
    state = random.getstate()
    first = adapter.generate(2**63 - 1, {"metric": "manhattan"}, 2, 4)
    second = adapter.generate(2**63 - 1, {"metric": "manhattan"}, 2, 4)
    assert first == second and random.getstate() == state
    first["train"][0]["input"][0][0] = 9
    assert second == adapter.generate(2**63 - 1, {"metric": "manhattan"}, 2, 4)


@pytest.mark.parametrize("metric", ["manhattan", "chebyshev"])
def test_two_demos_reject_declared_shortcuts(adapter, metric):
    spec = importlib.util.spec_from_file_location("tested_nearest_rivals", SOURCE.with_name("rivals.py"))
    rivals = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rivals)
    for seed in (0, 17, 29, 2**63 - 1):
        rows = rivals.check_episode(adapter.generate(seed, {"metric": metric}, 2, 4))
        assert len(rows) == len(rivals.RIVALS) == 22
        assert not [row["rival"] for row in rows if row["survives_demos"]]
