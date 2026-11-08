"""Prototype scope: keyed rotation followed by a measured row completion."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
HOME = TASK / "workspace/parametric"


def load(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location("rotation_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return load("prototype")


@pytest.fixture(scope="module")
def adapter():
    return load("adapter")


def canonical():
    return next(json.loads(line) for line in
                (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                if json.loads(line).get("task_id") == "80a3c4f25880")


def scene(mask, key=1, color=6):
    grid = [[0] * (len(mask[0]) + 4) for _ in range(len(mask) + 4)]
    grid[0][0] = key
    for r, row in enumerate(mask):
        for c, cell in enumerate(row):
            grid[r + 2][c + 2] = color if cell == "1" else 0
    return grid


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    with _local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


def test_default_exact_canonical_bytes_and_four_official_pairs(adapter, proto, racket):
    row = canonical()
    settings = {"line_rule": "canonical"}
    assert adapter.program(settings) == row["program_solution"]
    assert (HOME / "canonical.rkt").read_bytes() == row["program_solution"].encode()
    for pair in row["train"] + row["test"]:
        assert racket(adapter.program(settings), pair["input"]) == pair["output"]
        assert proto.apply_claim(pair["input"], settings) == pair["output"]


@pytest.mark.parametrize("rule,expected", [
    ("canonical", ["11000", "01110", "00111", "00011"]),
    ("most_cells", ["11000", "11111", "00111", "00011"]),
    ("least_cells", ["11111", "01110", "00111", "00011"]),
])
def test_hand_counted_rotation_selection_and_topmost_tie(proto, adapter, racket, rule, expected):
    grid = scene(["0011", "0111", "0110", "1100", "1000"])
    before = copy.deepcopy(grid)
    answer = [[6 if x == "1" else 0 for x in row] for row in expected]
    settings = {"line_rule": rule}
    assert proto.apply_claim(grid, settings) == answer
    assert racket(adapter.program(settings), grid) == answer
    assert grid == before
    if rule != "canonical":
        assert racket(proto.rivals(settings)["wrong_order"], grid) != answer


def test_key_is_cleared_even_when_inside_object_bounding_box(proto, adapter, racket):
    grid = [[0] * 8 for _ in range(8)]
    grid[0][0] = 1
    for r, c in ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2)):
        grid[r][c] = 6
    expected = [[6, 0, 0], [6, 0, 0], [6, 6, 6]]
    settings = {"line_rule": "canonical"}
    assert proto.apply_claim(grid, settings) == expected
    assert racket(adapter.program(settings), grid) == expected


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_independent_counts_shared_inputs_freshness_and_rng_purity(adapter, proto, seed):
    random.seed(94941)
    before = random.getstate()
    small = adapter.generate(seed, {"line_rule": "most_cells"}, 3, 1)
    large = adapter.generate(seed, {"line_rule": "most_cells"}, 6, 4)
    four_queries = adapter.generate(seed, {"line_rule": "most_cells"}, 3, 4)
    assert random.getstate() == before
    assert small["train"] == large["train"][:3]
    assert small["test"] == large["test"][:1]
    assert proto.public_turn(small, 0) == proto.public_turn(four_queries, 0)
    assert set(large) == {"train", "test", "program_solution"}
    assert len(large["train"]) == 6 and len(large["test"]) == 4
    reference_inputs = [p["input"] for split in ("train", "test") for p in large[split]]
    assert len({json.dumps(g) for g in reference_inputs}) == 10
    assert {p["input"][0][0] for p in large["train"][:3]} == {1, 2, 3}
    for rule in proto.SETTINGS:
        episode = adapter.generate(seed, {"line_rule": rule}, 6, 4)
        assert [p["input"] for split in ("train", "test") for p in episode[split]] == reference_inputs
    small["train"][0]["input"][0][0] = 9
    assert adapter.generate(seed, {"line_rule": "most_cells"}, 3, 1)["train"] == large["train"][:3]


@pytest.mark.parametrize("rule", ["canonical", "most_cells", "least_cells"])
def test_demonstrations_refute_declared_settings_and_cover_boundary(proto, adapter, rule):
    settings = {"line_rule": rule}
    episode = adapter.generate(17, settings, 3, 4)
    survivors = [candidate for candidate in proto.SETTINGS
                 if all(proto.apply_claim(p["input"], {"line_rule": candidate}) == p["output"]
                        for p in episode["train"])]
    assert survivors == [rule]
    last = episode["test"][-1]
    detail = proto.describe(last["input"], settings)
    assert detail["input_shape"] == [30, 30]
    assert detail["object_shape"] == [30, 30]
    assert detail["output_shape"] == [30, 30]
    assert detail["object_cells"] >= 150
    assert len(last["output"]) == len(last["output"][0]) == 30
    assert not any(last["input"][r][c] for r, c in ((0, 1), (1, 0), (1, 1)))
    assert set(x for row in last["output"] for x in row) <= {0, detail["blob_color"]}
    if rule != "canonical":
        assert detail["added_cells"] > 0


def test_public_turn_has_one_query_no_future_or_private_metadata(proto, adapter):
    episode = adapter.generate(0, {"line_rule": "least_cells"}, 3, 4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(p) == {"input", "output"} for p in visible["train"])
    visible["test"][0]["input"][0][0] = 9
    assert proto.public_turn(episode, 0)["test"][0]["input"][0][0] != 9
    with pytest.raises(ValueError):
        proto.public_turn(episode, True)
    with pytest.raises(ValueError):
        proto.public_turn(episode, 4)


@pytest.mark.parametrize("settings", [{}, {"line_rule": "other"}, {"line_rule": True},
                                     {"line_rule": "canonical", "extra": 1}, None])
def test_invalid_settings_rejected(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
                                               (0, 2, 4), (0, 7, 4), (0, 3.0, 4),
                                               (0, 3, True), (0, 3, 0), (0, 3, 5)])
def test_invalid_count_and_seed_contract_rejected(adapter, seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, {"line_rule": "canonical"}, demos, queries)


@pytest.mark.parametrize("bad", [[[True]], [[1.0]], [[1], [0, 0]], [[10]], [], [[0]*31]])
def test_invalid_typed_grids_rejected(proto, bad):
    with pytest.raises(ValueError):
        proto.apply_claim(bad, {"line_rule": "canonical"})
