"""Contract tests for the episode-level rank-policy family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "e0680a673043"
ROOT = find_root(__file__)
PROTO_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("e068_rank_prototype", PROTO_PATH)
assert _SPEC and _SPEC.loader
proto = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(proto)


def _canonical_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    return next(row["program_solution"] for row in rows if row.get("task_id") == TASK_ID)


def test_default_program_is_exact_canonical_and_variants_are_distinct():
    assert proto.program_for("size_desc") == _canonical_source()
    programs = {proto.program_for(policy) for policy in proto.RANK_POLICIES}
    assert len(programs) == len(proto.RANK_POLICIES) == 3


def test_strict_parameter_seed_and_count_validation():
    for bad in (True, -1, "1"):
        with pytest.raises(ValueError):
            proto.generate_claims(bad, "size_desc", 2, 4)
    for bad in (True, 1, 7, "2"):
        with pytest.raises(ValueError):
            proto.generate_claims(0, "size_desc", bad, 4)
    for bad in (True, 3, 5, "4"):
        with pytest.raises(ValueError):
            proto.generate_claims(0, "size_desc", 2, bad)
    with pytest.raises(ValueError):
        proto.generate_claims(0, "unknown", 2, 4)


def test_two_demos_identify_each_policy_and_four_queries_are_distinct_with_30x30_stress():
    for seed in range(4):
        for chosen in proto.RANK_POLICIES:
            episode = proto.generate_claims(seed, chosen, 2, 4)
            assert episode["program_solution"] == proto.program_for(chosen)
            assert len(episode["train"]) == 2
            assert len(episode["test"]) == 4
            inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
            assert len({json.dumps(grid) for grid in inputs}) == 6
            assert len(episode["test"][-1]["input"]) == 30
            assert len(episode["test"][-1]["input"][0]) == 30
            assert sum(cell != 0 for row in episode["test"][-1]["input"] for cell in row) >= 75
            survivors = []
            for candidate in proto.RANK_POLICIES:
                if all(
                    proto.python_mirror(pair["input"], rank_policy=candidate) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            assert survivors == [chosen]
            for pair in episode["train"] + episode["test"]:
                assert proto.python_mirror(pair["input"], rank_policy=chosen) == pair["output"]


def test_selected_object_locations_move_across_seeds_and_policy_is_not_a_fixed_lane():
    signatures = set()
    for seed in range(12):
        episode = proto.generate_claims(seed, "color_asc", 2, 4)
        facts = proto.scene_facts(episode["test"][0]["input"])
        selected = proto.select_intermediate(facts, "color_asc")
        signatures.add((selected["r1"], selected["c1"], selected["size"], selected["color"]))
    assert len(signatures) >= 8
