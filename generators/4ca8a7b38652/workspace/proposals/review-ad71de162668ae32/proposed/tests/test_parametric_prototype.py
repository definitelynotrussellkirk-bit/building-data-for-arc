"""Contracts for the unapproved, task-local scale-offset prototype only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = Path(__file__).resolve().parents[1]
SOURCE = TASK / "workspace/parametric/prototype.py"


def prototype():
    assert SOURCE.is_file(), "requested task-local parametric prototype is absent"
    spec = importlib.util.spec_from_file_location("scale_offset_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prototype_exists():
    prototype()


@pytest.mark.parametrize("bad", [-2, 2, True, 0.0, "0"])
def test_parameter_rejects_values_outside_literal_integer_domain(bad):
    with pytest.raises(ValueError, match="scale_offset"):
        prototype().episode_inputs(seed=17, scale_offset=bad)


@pytest.mark.parametrize("bad", [True, 1.0, "1"])
def test_seed_rejects_nonliteral_integer_values(bad):
    with pytest.raises(ValueError, match="seed"):
        prototype().episode_inputs(seed=bad)


def test_episode_is_reproducible_and_parameter_is_selected_once():
    p = prototype()
    for seed in range(12):
        first = p.episode_inputs(seed=seed)
        assert first == p.episode_inputs(seed=seed)
        offset, inputs = first
        assert offset in {-1, 0, 1}
        assert len(inputs) == 6
        assert p.episode_inputs(seed=seed, scale_offset=offset) == first
    assert {p.episode_inputs(seed=s)[0] for s in range(20)} == {-1, 0, 1}


def test_public_challenge_is_only_demos_and_unanswered_queries():
    p = prototype()
    with p.RacketLabels() as labels:
        public, private = p.build_episode(labels, seed=11, scale_offset=1)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 5 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert private["parameters"] == {"scale_offset": 1}
    assert len(private["query_outputs"]) == 1
    for pair in public["train"] + [{"input": public["test"][0]["input"], "output": private["query_outputs"][0]}]:
        n = len({v for row in pair["input"] for v in row} - {0})
        assert len(pair["output"]) == len(pair["input"]) * (n + 1)


def test_default_source_is_byte_identical_and_executes_canonical_labels():
    p = prototype()
    root = find_root(__file__)
    records = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    selected = next(row["program_solution"] for row in records if row["task_id"] == "4ca8a7b38652")
    assert p.rule_source(0).encode() == selected.encode()
    pairs = canonical_pairs("4ca8a7b38652", root=root)
    with p.RacketLabels() as labels:
        for pair in pairs:
            assert labels.apply(p.rule_source(0), pair["input"]) == pair["output"]


def test_each_setting_is_identified_by_demos_and_same_input_distinguishes_all():
    p = prototype()
    witness = [[0, 1, 0], [2, 0, 1], [0, 2, 0]]
    with p.RacketLabels() as labels:
        outputs = [labels.apply(p.rule_source(offset), witness) for offset in (-1, 0, 1)]
        assert [len(output) for output in outputs] == [3, 6, 9]
        for offset in (-1, 0, 1):
            public, private = p.build_episode(labels, seed=23, scale_offset=offset)
            scores = private["rival_checks"]
            assert scores[f"offset_{offset}"]["status"] == "survived_all"
            assert all(row["status"] == "refuted_by_demos" for name, row in scores.items() if name != f"offset_{offset}")


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_larger_query_keeps_five_3x3_demos_and_output_bound(offset):
    p = prototype()
    with p.RacketLabels() as labels:
        public, private = p.build_episode(labels, seed=7, scale_offset=offset, query_side=6)
    assert all(len(pair["input"]) == len(pair["input"][0]) == 3 for pair in public["train"])
    query = public["test"][0]["input"]
    assert len(query) == len(query[0]) == 6
    output = private["query_outputs"][0]
    assert 1 <= len(output) <= 30 and 1 <= len(output[0]) <= 30


@pytest.mark.parametrize("bad", [0, 7, True, 3.0])
def test_unsupported_query_size_rejected_before_sampling(bad):
    with pytest.raises(ValueError, match="query_side"):
        prototype().episode_inputs(seed=1, query_side=bad)
