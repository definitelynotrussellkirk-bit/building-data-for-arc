"""Focused contract tests for the task-local object-order family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]
WORK = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "c90e481827fb92d38558d0ed96d0d3d54243d1f86a0efd33a8a96951023cc653"


def module(name: str):
    path = WORK / f"{name}.py"
    assert path.is_file(), f"missing native parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"test_e68_{name}_{hash(path)}", path)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def inputs(episode: dict, split: str) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode[split]]


def test_default_program_is_exact_canonical_and_alternate_is_distinct() -> None:
    adapter = module("adapter")
    canonical = adapter.program({"order_policy": "spatial"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    alternate = adapter.program({"order_policy": "largest_first"})
    assert alternate != canonical
    assert alternate.count("(rule!") == 1


def test_independent_counts_matched_settings_and_query_prefix() -> None:
    adapter = module("adapter")
    for seed in (0, 17, 93):
        for demos in (2, 3, 6):
            spatial = adapter.generate(seed, {"order_policy": "spatial"}, demos, 4)
            largest = adapter.generate(seed, {"order_policy": "largest_first"}, demos, 4)
            assert len(spatial["train"]) == demos
            assert len(spatial["test"]) == 4
            assert inputs(spatial, "train") == inputs(largest, "train")
            assert inputs(spatial, "test") == inputs(largest, "test")
            one = adapter.generate(seed, {"order_policy": "spatial"}, demos, 1)
            assert one["train"] == spatial["train"]
            assert one["test"] == spatial["test"][:1]
            all_inputs = inputs(spatial, "train") + inputs(spatial, "test")
            assert len({json.dumps(grid) for grid in all_inputs}) == demos + 4
        two = adapter.generate(seed, {"order_policy": "spatial"}, 2, 4)
        six = adapter.generate(seed, {"order_policy": "spatial"}, 6, 4)
        assert two["train"] == six["train"][:2]
        assert two["test"] == six["test"]


def test_two_demonstrations_identify_both_declared_settings() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    for seed in (0, 17, 93):
        for policy, opposite in (("spatial", "largest_first"), ("largest_first", "spatial")):
            episode = adapter.generate(seed, {"order_policy": policy}, 2, 4)
            assert any(
                prototype.predict(pair["input"], opposite) != pair["output"]
                for pair in episode["train"]
            )
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.predict(pair["input"], policy)


def test_intermediate_is_input_dependent_and_consumed_by_packing() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(17, {"order_policy": "largest_first"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        spatial = prototype.intermediate(grid, {"order_policy": "spatial"})
        largest = prototype.intermediate(grid, {"order_policy": "largest_first"})
        assert spatial["ordered_colors"] != largest["ordered_colors"]
        assert len(spatial["ordered_colors"]) == len(spatial["ordered_areas"])
        assert largest["ordered_areas"] == sorted(largest["ordered_areas"], reverse=True)
        assert prototype.pack_intermediate(largest) == pair["output"]
        assert prototype.pack_intermediate(spatial) != pair["output"]


def test_canonical_claims_match_reviewed_generator_mirror() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    generator = prototype.selected_generator()
    episode = adapter.generate(29, {"order_policy": "spatial"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == generator.rule_mirror(pair["input"])


def test_query_bank_contains_substantive_30_by_30_stress() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(17, {"order_policy": "largest_first"}, 3, 4)
    stress = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30)
    assert len(stress[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 65
    assert {((r >= 15), (c >= 15)) for r, c in nonzero} == {
        (False, False), (False, True), (True, False), (True, True)
    }
    facts = prototype.describe_scene(stress)
    assert facts["object_count"] == 5
    assert facts["max_bbox_height"] >= 6
    assert facts["packed_width"] <= 30


def test_bounded_rival_audit_has_no_harmful_survivor() -> None:
    audit = module("audit")
    report = audit.run_audit(seeds=(0, 17, 93), demos_values=(2, 3, 6))
    assert report["episodes"] == 18
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []


def test_invalid_requests_fail_closed() -> None:
    adapter = module("adapter")
    invalid_settings = ({}, None, {"order_policy": "reverse"}, {"order_policy": True},
                        {"order_policy": "spatial", "extra": 1})
    for settings in invalid_settings:
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in ((True, 2, 4), (-1, 2, 4), (2**63, 2, 4),
                                  (0, 1, 4), (0, 7, 4), (0, True, 4),
                                  (0, 2, 0), (0, 2, 5), (0, 2, True)):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"order_policy": "spatial"}, demos, queries)


def test_generation_is_rng_neutral_deterministic_and_fresh() -> None:
    adapter = module("adapter")
    random.seed(48291)
    before = random.getstate()
    episode = adapter.generate(17, {"order_policy": "largest_first"}, 3, 4)
    saved = copy.deepcopy(episode)
    assert random.getstate() == before
    episode["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, {"order_policy": "largest_first"}, 3, 4) == saved
