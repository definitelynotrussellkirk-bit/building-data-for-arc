from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "8d37d130fec1"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("_candidate_choice_prototype_test", HERE / "prototype.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_alternate_is_complete_rule():
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    first = MODULE.program({"candidate_choice": "first"})
    last = MODULE.program({"candidate_choice": "last"})
    assert first == canonical
    assert last.startswith("(rule!")
    assert last != first
    assert "(last (sort-by candidates" in last
    assert last.count("(rule!") == 1


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_labels_distinctness_and_matched_inputs(seed, demos, queries):
    first = MODULE.generate(seed, {"candidate_choice": "first"}, demos, queries)
    last = MODULE.generate(seed, {"candidate_choice": "last"}, demos, queries)
    assert len(first["train"]) == len(last["train"]) == demos
    assert len(first["test"]) == len(last["test"]) == queries
    assert _inputs(first) == _inputs(last)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(first)}) == demos + queries
    for setting, episode in (("first", first), ("last", last)):
        assert episode["program_solution"] == MODULE.program({"candidate_choice": setting})
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == MODULE.solve(pair["input"], {"candidate_choice": setting})
            facts = MODULE.analyze(pair["input"])
            assert facts["errors"] == []
            assert len(facts["candidate_indices"]) == 2
            assert facts["candidate_masks"][0] != facts["candidate_masks"][1]


def test_prefix_stability_and_first_turn_identity():
    short_demo = MODULE.generate(29, {"candidate_choice": "last"}, 2, 4)
    long_demo = MODULE.generate(29, {"candidate_choice": "last"}, 6, 4)
    assert short_demo["train"] == long_demo["train"][:2]
    assert short_demo["test"] == long_demo["test"]

    one_query = MODULE.generate(29, {"candidate_choice": "last"}, 3, 1)
    four_queries = MODULE.generate(29, {"candidate_choice": "last"}, 3, 4)
    assert one_query["train"] == four_queries["train"]
    assert one_query["test"] == four_queries["test"][:1]
    assert MODULE.visible_turn(one_query, 0) == MODULE.visible_turn(four_queries, 0)


def test_constructive_curriculum_and_substantive_query_sizes():
    episode = MODULE.generate(41, {"candidate_choice": "first"}, 3, 4)
    query_shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert query_shapes == [(14, 18), (18, 23), (24, 28), (30, 30)]
    q4 = episode["test"][3]["input"]
    assert sum(cell != 8 for row in q4 for cell in row) >= 100

    first_two = [MODULE.analyze(p["input"]) for p in episode["train"][:2]]
    assert first_two[0]["candidate_indices"] != first_two[1]["candidate_indices"]
    assert first_two[0]["candidate_areas"][0] > first_two[0]["candidate_areas"][1]
    assert first_two[1]["candidate_areas"][0] < first_two[1]["candidate_areas"][1]
    assert first_two[0]["candidate_colors"][0] < first_two[0]["candidate_colors"][1]
    assert first_two[1]["candidate_colors"][0] > first_two[1]["candidate_colors"][1]


@pytest.mark.parametrize("setting", ["first", "last"])
def test_finite_teaching_audit_has_no_harmful_survivor(setting):
    for seed in (0, 17, 41):
        episode = MODULE.generate(seed, {"candidate_choice": setting}, 3, 4)
        report = MODULE.teaching_report(episode, {"candidate_choice": setting})
        assert report["accepted"], report
        assert report["query_conflicts"] == []
        assert report["declared_survivors"] == [setting]


def test_public_projection_reveals_one_query_and_no_private_fields():
    episode = MODULE.generate(5, {"candidate_choice": "last"}, 3, 4)
    for index in range(4):
        turn = MODULE.visible_turn(episode, index)
        assert set(turn) == {"train", "test"}
        assert len(turn["train"]) == 3
        assert len(turn["test"]) == 1
        assert set(turn["test"][0]) == {"input"}
        serialized = json.dumps(turn, sort_keys=True)
        for forbidden in ("candidate_choice", "program_solution", "private_sampler", "output"):
            if forbidden == "output":
                assert '"test": [{"input"' in serialized or '"test":[{"input"' in serialized
            else:
                assert forbidden not in serialized


@pytest.mark.parametrize(
    "args",
    [
        (True, {"candidate_choice": "first"}, 3, 4),
        (-1, {"candidate_choice": "first"}, 3, 4),
        (0, {"candidate_choice": "first"}, 1, 4),
        (0, {"candidate_choice": "first"}, 7, 4),
        (0, {"candidate_choice": "first"}, 3, 0),
        (0, {"candidate_choice": "first"}, 3, 5),
        (0, {"candidate_choice": "middle"}, 3, 4),
        (0, {"candidate_choice": "first", "extra": 1}, 3, 4),
    ],
)
def test_invalid_requests_are_rejected(args):
    with pytest.raises(ValueError):
        MODULE.generate(*args)
