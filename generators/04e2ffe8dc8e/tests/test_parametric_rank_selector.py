"""Native parametric regressions for the smallest-green/rank-selector family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "04e2ffe8dc8e"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
SOURCE = HOME / "workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local rank-selector prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_04e2_rank_selector", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


@pytest.fixture(scope="module")
def engine(proto):
    with proto.RacketEngine() as runtime:
        yield runtime


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical(proto):
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get(TASK_ID)
    sources = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert sources == {proto.program({"selection_mode": "smallest_green"})}


def test_rank_selector_uses_key_size_as_input_dependent_intermediate(proto):
    grid = proto.sample_input(19, "train", 0, 16, 18)
    rank = proto.intermediate_value(grid)
    assert rank in (2, 3, 4)
    canonical = proto.transform(grid, {"selection_mode": "smallest_green"})
    ranked = proto.transform(grid, {"selection_mode": "key_rank_green"})
    assert canonical != ranked
    assert proto.selected_green_rank(grid, canonical) == 1
    assert proto.selected_green_rank(grid, ranked) == rank


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_identification_and_four_queries(proto, engine, demos):
    episodes = [
        proto.generate(17, {"selection_mode": mode}, demos, 4)
        for mode in ("smallest_green", "key_rank_green")
    ]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == demos + 4
        certificate = proto.verify_episode(episode, engine=engine)
        assert certificate["survivors"] == [episode["settings"]]
        assert certificate["fit_scope"] == "demonstrations_only"
        assert len(certificate["query_checks"]) == 4



def test_two_demo_lessons_vary_the_input_dependent_rank(proto):
    for seed in range(12):
        episode = proto.generate(seed, {"selection_mode": "key_rank_green"}, 2, 1)
        ranks = [proto.intermediate_value(pair["input"]) for pair in episode["train"]]
        assert len(set(ranks)) == 2

def test_real_racket_labels_include_substantive_30_square(proto, engine):
    for mode in ("smallest_green", "key_rank_green"):
        settings = {"selection_mode": mode}
        episode = proto.generate(23, settings, 3, 4)
        stress = episode["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        assert sum(cell != 0 for row in stress for cell in row) >= 140
        for row0 in (0, 15):
            for col0 in (0, 15):
                assert sum(
                    stress[row][col] != 0
                    for row in range(row0, row0 + 15)
                    for col in range(col0, col0 + 15)
                ) >= 20
        for pair in episode["train"] + episode["test"]:
            assert engine.apply(proto.program(settings), pair["input"]) == pair["output"]


def test_query_prefix_and_public_first_turn_are_count_independent(proto):
    one = proto.generate(31, {"selection_mode": "key_rank_green"}, 2, 1)
    four = proto.generate(31, {"selection_mode": "key_rank_green"}, 6, 4)
    assert one["test"] == four["test"][:1]
    first = {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    comparison = {"train": one["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(comparison)


def test_wrong_intermediate_counterfactual_changes_final_output(proto, engine):
    settings = {"selection_mode": "key_rank_green"}
    episode = proto.generate(7, settings, 3, 4)
    case = next(pair for pair in episode["test"] if proto.intermediate_value(pair["input"]) != 1)
    actual = engine.apply(proto.program(settings), case["input"])
    counterfactual = engine.apply(proto.counterfactual_program(1), case["input"])
    assert actual == case["output"]
    assert actual != counterfactual
    assert proto.selected_green_rank(case["input"], counterfactual) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        {"seed": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"settings": {"selection_mode": "unknown"}},
        {"settings": {"selection_mode": "smallest_green", "extra": 1}},
    ],
)
def test_invalid_requests_fail_closed(proto, mutation):
    kwargs = {
        "seed": 0,
        "settings": {"selection_mode": "smallest_green"},
        "demos": 3,
        "queries": 4,
    }
    kwargs.update(mutation)
    with pytest.raises(ValueError):
        proto.generate(**kwargs)


def test_verifier_rejects_corrupt_labels_duplicate_inputs_and_program(proto, engine):
    episode = proto.generate(11, {"selection_mode": "smallest_green"}, 2, 4)
    corruptions = []
    bad = deepcopy(episode)
    bad["test"][0]["output"][0][0] = 9
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["test"][0] = deepcopy(bad["train"][0])
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["program_solution"] = proto.program({"selection_mode": "key_rank_green"})
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["train"][0]["input"][0][0] = True
    corruptions.append(bad)
    for bad in corruptions:
        with pytest.raises(ValueError):
            proto.verify_episode(bad, engine=engine)
