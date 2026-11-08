"""Independent behavior checks for the separate native pivot-rotation family.

The small oracle below discovers the ray/component and rotates coordinates
directly. It imports neither the generator mirror nor implementation internals.
Actual labels returned by the native adapter are compared with that oracle;
native qualification independently replays them through protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from collections import deque
from pathlib import Path

import pytest

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = TASK_DIR.parents[1]
NATIVE_PATH = TASK_DIR / "workspace/parametric/native.py"
SPEC = importlib.util.spec_from_file_location("native_66387591ebe6_under_test", NATIVE_PATH)
assert SPEC and SPEC.loader
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


def _scene(grid):
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    assert len(pivots) == 1
    payload = {(r, c): value for r, row in enumerate(grid) for c, value in enumerate(row)
               if value not in (0, 9) and (r, c) != (0, 0)}
    return grid[0][0], pivots[0], payload


def _hit_component(grid):
    key, pivot, payload = _scene(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[key]
    r, c = pivot
    hit = None
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            break
        if (r, c) in payload:
            hit = (r, c)
            break
    if hit is None:
        return None
    color = payload[hit]
    seen = {hit}
    todo = deque([hit])
    while todo:
        r, c = todo.popleft()
        for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if p not in seen and payload.get(p) == color:
                seen.add(p)
                todo.append(p)
    return seen


def _rotated_position(point, pivot, turns):
    dr, dc = point[0] - pivot[0], point[1] - pivot[1]
    for _ in range(turns % 4):
        dr, dc = dc, -dr
    return pivot[0] + dr, pivot[1] + dc


def _oracle(grid, turn_source):
    key, pivot, payload = _scene(grid)
    component = _hit_component(grid)
    turns = key - 1
    if turn_source == "hit_size":
        turns = 0 if component is None else (len(component) - 1) % 4
    output = [[0] * len(grid[0]) for _ in grid]
    output[0][0] = key
    output[pivot[0]][pivot[1]] = 9
    for point, color in payload.items():
        r, c = _rotated_position(point, pivot, turns)
        assert 0 <= r < len(grid) and 0 <= c < len(grid[0])
        assert (r, c) not in ((0, 0), pivot)
        output[r][c] = color
    return output


@pytest.fixture(scope="module", params=[0, 17], ids=["seed0", "seed17"])
def episodes(request):
    seed = request.param
    return seed, {mode: native.generate(seed, {"turn_source": mode}, demos=5, queries=4)
                  for mode in ("key", "hit_size")}


def test_default_program_is_exact_selected_canonical_bytes():
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    programs = {row["program_solution"] for line in ledger.read_text().splitlines()
                if (row := json.loads(line)).get("task_id") == "66387591ebe6"}
    assert programs == {native.program({"turn_source": "key"})}
    assert hashlib.sha256(next(iter(programs)).encode()).hexdigest() == (
        "60007e76f2188c327bb9fde3962cc36c3b0573e38d45735fa937fcddceb27673"
    )
    assert native.program({"turn_source": "hit_size"}) not in programs


class _DictSubclass(dict):
    pass


@pytest.mark.parametrize("settings", [None, {}, "key", {"turn_source": True},
    {"turn_source": "unknown"}, {"turn_source": "key", "extra": 1},
    _DictSubclass(turn_source="key")])
def test_settings_are_an_exact_declared_dictionary(settings):
    with pytest.raises(ValueError):
        native.program(settings)
    with pytest.raises(ValueError):
        native.generate(0, settings)


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 0.0, "0", None])
def test_recipe_seed_is_exact_bounded_integer(seed):
    with pytest.raises(ValueError):
        native.sample_inputs(seed)
    with pytest.raises(ValueError):
        native.generate(seed, {"turn_source": "key"})


@pytest.mark.parametrize("demos", [4, 7, True, 5.0, "5", None])
def test_demo_count_rejects_unsupported_and_coercible_values(demos):
    with pytest.raises(ValueError):
        native.sample_inputs(0, demos=demos)
    with pytest.raises(ValueError):
        native.generate(0, {"turn_source": "key"}, demos=demos)


@pytest.mark.parametrize("queries", [0, 5, True, 1.0, "1", None])
def test_query_count_rejects_unsupported_and_coercible_values(queries):
    with pytest.raises(ValueError):
        native.sample_inputs(0, queries=queries)
    with pytest.raises(ValueError):
        native.generate(0, {"turn_source": "key"}, queries=queries)


@pytest.mark.parametrize("seed", [0, 17])
def test_teaching_schedule_covers_keys_and_component_branches(seed):
    train, test = native.sample_inputs(seed, demos=6, queries=4)
    assert len(train) == 6 and len(test) == 4
    assert [grid[0][0] for grid in train] == [1, 2, 3, 4, 1, 2]
    assert [None if (cells := _hit_component(grid)) is None else len(cells)
            for grid in train] == [2, 1, 4, None, 7, 6]
    assert [len(grid) for grid in test] == [9, 17, 23, 30]
    assert [grid[0][0] for grid in test] == [4, 3, 2, 1]
    assert [None if (cells := _hit_component(grid)) is None else len(cells)
            for grid in test] == [1, 6, None, 7]
    hit_colors = set()
    for grid in train:
        component = _hit_component(grid)
        if component:
            r, c = next(iter(component))
            hit_colors.add(grid[r][c])
    assert len(hit_colors) == 1, "repeat color while changing component size and key"
    all_grids = train + test
    assert len({json.dumps(grid) for grid in all_grids}) == len(all_grids)
    for grid in all_grids:
        assert 9 <= len(grid) <= 30
        assert all(type(row) is list and len(row) == len(grid) for row in grid)
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_are_prefix_stable_and_sampling_is_deterministic_fresh_and_rng_pure(seed):
    before = random.getstate()
    all_train, all_test = native.sample_inputs(seed, demos=6, queries=4)
    train, test = native.sample_inputs(seed, demos=5, queries=1)
    assert random.getstate() == before
    assert train == all_train[:5] and test == all_test[:1]
    train[0][0][0] = 0
    assert native.sample_inputs(seed, demos=5, queries=1) == (all_train[:5], all_test[:1])


@pytest.mark.parametrize("seed", [0, 17])
def test_every_admitted_cell_is_rotation_safe_for_all_four_turns(seed):
    train, test = native.sample_inputs(seed, demos=6, queries=4)
    for grid in train + test:
        _, pivot, payload = _scene(grid)
        assert pivot != (0, 0) and payload
        for turns in range(4):
            destinations = {_rotated_position(point, pivot, turns) for point in payload}
            assert len(destinations) == len(payload)
            assert not (destinations & {(0, 0), pivot})
            assert all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in destinations)


def test_large_query_contains_substantive_payload_spread():
    _, tests = native.sample_inputs(17)
    grid = tests[-1]
    _, _, payload = _scene(grid)
    assert len(grid) == len(grid[0]) == 30
    assert len(payload) >= 40
    assert max(r for r, _ in payload) - min(r for r, _ in payload) >= 24
    assert max(c for _, c in payload) - min(c for _, c in payload) >= 24
    assert len(_hit_component(grid)) == 7


def test_native_labels_match_independent_coordinate_and_component_oracle(episodes):
    seed, generated = episodes
    sampled = native.sample_inputs(seed, demos=5, queries=4)
    for mode, episode in generated.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert episode["program_solution"] == native.program({"turn_source": mode})
        assert [p["input"] for p in episode["train"]] == sampled[0]
        assert [p["input"] for p in episode["test"]] == sampled[1]
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == _oracle(pair["input"], mode)
    key, hit = generated["key"], generated["hit_size"]
    assert key["train"][0]["output"] == key["train"][0]["input"]
    assert hit["train"][0]["output"] != key["train"][0]["output"]
    assert hit["train"][1]["output"] == hit["train"][1]["input"]
    assert hit["train"][3]["output"] == hit["train"][3]["input"], "no selected object means no action"
    assert hit["train"][3]["output"] != key["train"][3]["output"]
    for episode in generated.values():
        first, second = episode["train"][:2]
        assert len(first["input"]) == len(second["input"]) == 9
        first_turns = {t for t in range(4) if _rotation_for_test(first["input"], t) == first["output"]}
        second_turns = {t for t in range(4) if _rotation_for_test(second["input"], t) == second["output"]}
        assert first_turns and second_turns and first_turns.isdisjoint(second_turns)


def _rotation_for_test(grid, turns):
    key, pivot, payload = _scene(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    output[0][0], output[pivot[0]][pivot[1]] = key, 9
    for point, color in payload.items():
        r, c = _rotated_position(point, pivot, turns)
        output[r][c] = color
    return output


def test_public_projection_ignores_hidden_metadata_and_query_answers(episodes):
    _, generated = episodes
    episode = generated["hit_size"]
    visible = public_challenge_bytes(episode)
    altered = copy.deepcopy(episode)
    altered["settings"] = {"turn_source": "key"}
    altered["seed"] = 999
    altered["program_solution"] = "not the executed program"
    altered["future_query_count"] = 200
    for pair in altered["test"]:
        pair["output"] = [[0] * len(pair["input"][0]) for _ in pair["input"]]
    assert public_challenge_bytes(altered) == visible
    assert public_challenge_id(altered) == hashlib.sha256(visible).hexdigest()
    public = json.loads(visible)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_single_query_first_turn_equals_four_query_first_turn():
    full = native.generate(0, {"turn_source": "hit_size"}, demos=5, queries=4)
    single = native.generate(0, {"turn_source": "hit_size"}, demos=5, queries=1)
    first_turn = {"train": full["train"], "test": full["test"][:1]}
    assert public_challenge_bytes(single) == public_challenge_bytes(first_turn)
    assert public_challenge_id(single) == public_challenge_id(first_turn)


def test_optional_sixth_demo_is_a_real_independently_labeled_example():
    episode = native.generate(17, {"turn_source": "hit_size"}, demos=6, queries=1)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 1
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == _oracle(pair["input"], "hit_size")
