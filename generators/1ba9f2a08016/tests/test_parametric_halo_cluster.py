"""Contract tests for the episode-level halo-component family."""
from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "1ba9f2a08016"
ROOT = find_root(__file__)
PROTO_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("halo_component_prototype", PROTO_PATH)
assert _SPEC and _SPEC.loader
proto = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(proto)


def _canonical_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    return next(row["program_solution"] for row in rows if row.get("task_id") == TASK_ID)


def test_plain_program_is_exact_canonical_and_alternates_are_distinct():
    assert proto.program_for("plain") == _canonical_source()
    programs = {proto.program_for(policy) for policy in proto.COMPONENT_POLICIES}
    assert len(programs) == len(proto.COMPONENT_POLICIES) == 3


def test_strict_seed_setting_and_count_validation():
    for bad in (True, -1, "1"):
        with pytest.raises(ValueError):
            proto.generate_claims(bad, "plain", 2, 4)
    for bad in (True, 1, 7, "2"):
        with pytest.raises(ValueError):
            proto.generate_claims(0, "plain", bad, 4)
    for bad in (True, 3, 5, "4"):
        with pytest.raises(ValueError):
            proto.generate_claims(0, "plain", 2, bad)
    with pytest.raises(ValueError):
        proto.generate_claims(0, "unknown", 2, 4)


def test_two_demos_identify_all_policies_and_queries_include_substantive_30x30():
    for seed in range(4):
        for chosen in proto.COMPONENT_POLICIES:
            episode = proto.generate_claims(seed, chosen, 2, 4)
            assert episode["program_solution"] == proto.program_for(chosen)
            assert len(episode["train"]) == 2
            assert len(episode["test"]) == 4
            inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
            assert len({json.dumps(grid) for grid in inputs}) == 6
            stress = episode["test"][-1]["input"]
            assert (len(stress), len(stress[0])) == (30, 30)
            assert sum(cell != 0 for row in stress for cell in row) >= 35
            survivors = []
            for candidate in proto.COMPONENT_POLICIES:
                if all(
                    proto.python_mirror(pair["input"], component_policy=candidate) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            assert survivors == [chosen]
            for pair in episode["train"] + episode["test"]:
                facts = proto.scene_facts(pair["input"])
                assert len(facts["components"]) == 3
                assert len({component["size"] for component in facts["components"]}) == 3
                red_counts = [len(component["red_cells"]) for component in facts["components"]]
                largest = proto.select_intermediate(facts, "highlight_largest")
                smallest = proto.select_intermediate(facts, "highlight_smallest")
                # The post-halo selector must not collapse to selecting by the
                # number of red input seeds before Step A.
                assert len(largest["red_cells"]) != max(red_counts)
                assert len(smallest["red_cells"]) != min(red_counts)
                assert proto.python_mirror(pair["input"], component_policy=chosen) == pair["output"]


def test_selected_component_location_and_size_vary_across_seeds():
    signatures = set()
    for seed in range(12):
        episode = proto.generate_claims(seed, "highlight_largest", 2, 4)
        facts = proto.scene_facts(episode["test"][0]["input"])
        selected = proto.select_intermediate(facts, "highlight_largest")
        signatures.add((selected["r1"], selected["c1"], selected["size"], len(selected["magenta_cells"])))
    assert len(signatures) >= 8
