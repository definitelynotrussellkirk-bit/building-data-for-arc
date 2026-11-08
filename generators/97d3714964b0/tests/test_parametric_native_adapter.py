"""Native promotion contract for the 97d3714964b0 hollow-threshold relay."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "97d3714964b0"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
POLICIES = ("independent", "largest_hollow_threshold")
SETTINGS = tuple({"solid_policy": value} for value in POLICIES)


def _load(path: Path, suffix: str):
    assert path.is_file(), f"required native source is missing: {path.name}"
    source = path.read_bytes()
    name = f"_native_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode() + source).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(HERE / "adapter.py", "adapter")


@pytest.fixture(scope="module")
def prototype():
    return _load(HERE / "prototype.py", "prototype")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode):
    return [*episode["train"], *episode["test"]]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _apply(bridge: RacketBridge, source: str, grid):
    proc = wrap_rule(source)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({proc} {literal})")


def test_promotion_contract_declares_cross_object_policy_and_native_limits():
    assert json.loads((HERE / "promotion.json").read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"solid_policy": ["independent", "largest_hollow_threshold"]},
        "default": {"solid_policy": "independent"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/largest_hollow_threshold.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_alternate_is_distinct(adapter):
    canonical = _canonical_program()
    independent = adapter.program({"solid_policy": "independent"})
    relay = adapter.program({"solid_policy": "largest_hollow_threshold"})
    assert independent == canonical
    assert independent == (HERE / "canonical.rkt").read_text(encoding="utf-8")
    assert relay == (HERE / "largest_hollow_threshold.rkt").read_text(encoding="utf-8")
    assert relay != independent
    assert adapter.program({"solid_policy": "largest_hollow_threshold"}) == relay


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"solid_policy": "largest"}, {"solid_policy": 1},
     {"solid_policy": True}, {"solid_policy": "independent", "extra": 0}],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|solid_policy"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, -1, 1.0, "1", None])
def test_generate_rejects_invalid_seed_scalars(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"solid_policy": "independent"}, 3, 4)


@pytest.mark.parametrize(
    "name,bad",
    [("demos", True), ("demos", 1), ("demos", 7),
     ("queries", False), ("queries", 0), ("queries", 5)],
)
def test_generate_rejects_invalid_counts(adapter, name, bad):
    request = {"seed": 0, "settings": {"solid_policy": "independent"}, "demos": 3, "queries": 4}
    request[name] = bad
    with pytest.raises(ValueError, match=name):
        adapter.generate(**request)


def test_counts_are_independent_prefix_stable_and_deterministic(adapter):
    settings = {"solid_policy": "largest_hollow_threshold"}
    minimum = adapter.generate(23, settings, 2, 1)
    maximum = adapter.generate(23, settings, 6, 4)
    replay = adapter.generate(23, settings, 6, 4)
    assert maximum == replay
    assert set(maximum) == {"train", "test", "program_solution"}
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    assert maximum["program_solution"] == adapter.program(settings)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)}) == 10


def test_same_seed_uses_matched_inputs_across_policies(adapter):
    independent = adapter.generate(91, SETTINGS[0], 3, 4)
    relay = adapter.generate(91, SETTINGS[1], 3, 4)
    assert _inputs(independent) == _inputs(relay)
    assert all(
        a["output"] != b["output"]
        for a, b in zip(independent["train"], relay["train"])
    )


@pytest.mark.parametrize("chosen", POLICIES)
def test_two_demonstrations_identify_the_chosen_policy(prototype, adapter, chosen):
    episode = adapter.generate(0, {"solid_policy": chosen}, 2, 4)
    survivors = [
        rival
        for rival in POLICIES
        if all(
            prototype.native_transform(pair["input"], {"solid_policy": rival}) == pair["output"]
            for pair in episode["train"]
        )
    ]
    assert survivors == [chosen]


def test_every_scene_contains_real_largest_hollow_relay_contrast(prototype, adapter):
    relay = adapter.generate(57, SETTINGS[1], 6, 4)
    independent = adapter.generate(57, SETTINGS[0], 6, 4)
    for relay_pair, independent_pair in zip(_pairs(relay), _pairs(independent)):
        analysis = prototype.analyze_input(relay_pair["input"])
        threshold = analysis["largest_hollow_bbox_area"]
        solid_areas = sorted(obj["bbox_area"] for obj in analysis["objects"] if obj["kind"] == "solid")
        hollow_areas = sorted(obj["bbox_area"] for obj in analysis["objects"] if obj["kind"] == "hollow")
        assert len(hollow_areas) >= 2 and len(solid_areas) >= 2
        assert hollow_areas[-1] == threshold
        assert solid_areas[0] < threshold <= solid_areas[-1]
        assert 7 in {value for row in relay_pair["output"] for value in row}
        assert 7 not in {value for row in independent_pair["output"] for value in row}
        assert relay_pair["output"] != independent_pair["output"]


def test_fourth_query_is_substantive_exact_30x30_relay_stress(prototype, adapter):
    episode = adapter.generate(123, SETTINGS[1], 3, 4)
    pair = episode["test"][3]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    analysis = prototype.analyze_input(pair["input"])
    assert len(analysis["objects"]) == 4
    assert analysis["largest_hollow_bbox_area"] >= 100
    palette = {value for row in pair["output"] for value in row}
    assert {0, 2, 4, 7} <= palette
    changed = sum(
        before != after
        for in_row, out_row in zip(pair["input"], pair["output"])
        for before, after in zip(in_row, out_row)
    )
    assert changed >= 150


@pytest.mark.parametrize("policy", POLICIES)
def test_python_claim_labels_match_protected_racket(adapter, policy):
    episode = adapter.generate(37, {"solid_policy": policy}, 2, 1)
    source = adapter.program({"solid_policy": policy})
    with RacketBridge(timeout=20.0) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for pair in _pairs(episode):
            assert _apply(bridge, source, pair["input"]) == pair["output"]


def test_public_first_turn_masks_policy_program_and_all_query_answers(adapter):
    one = adapter.generate(17, SETTINGS[0], 3, 1)
    four = adapter.generate(17, SETTINGS[0], 3, 4)
    first_turn = {"train": four["train"], "test": [four["test"][0]]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first_turn)
    visible = json.loads(public_challenge_bytes(four))
    assert all(set(pair) == {"input"} for pair in visible["test"])
    text = json.dumps(visible, sort_keys=True)
    assert "solid_policy" not in text
    assert "program_solution" not in text
    assert "largest_hollow_threshold" not in text


def test_dependency_witness_ablates_largest_hollow_area_and_changes_output(prototype):
    witness = prototype.dependency_witness()
    assert witness["settings"] == {"solid_policy": "largest_hollow_threshold"}
    assert witness["ablation"] == "wrong_intermediate"
    assert witness["intermediate_value"]["largest_hollow_bbox_area"] > 0
    assert witness["wrong_intermediate_value"] == {"largest_hollow_bbox_area": 0}
    assert witness["output"] != witness["counterfactual_output"]
    assert witness["output"] == prototype.native_transform(witness["input"], witness["settings"])
    assert witness["counterfactual_output"] == prototype.native_transform(
        witness["input"], {"solid_policy": "independent"}
    )
