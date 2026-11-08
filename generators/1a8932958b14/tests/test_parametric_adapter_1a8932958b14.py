"""Native promotion contract for the payload-axis translation family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys
import types

import pytest

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "1a8932958b14"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
FAMILY_PATH = PARAMETRIC / "family.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
BUILDER_PATH = PARAMETRIC / "build_native_evidence.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing requested parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "task_1a8932958b14_parametric_family_test")


def _all_pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _all_pairs(episode)]


def _digest(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_program_contract_preserves_exact_canonical_default(family):
    variants = Catalog(ROOT)._variants()[TASK_ID]
    canonical = {
        row["program_solution"]
        for row in variants
        if isinstance(row.get("program_solution"), str)
    }
    assert len(canonical) == 1
    assert family.PARAMETER_NAME == "translation_policy"
    assert family.SETTINGS == ("marker_vector", "payload_axis_gate")
    assert family.DEFAULT_SETTINGS == {"translation_policy": "marker_vector"}
    assert {family.program(family.DEFAULT_SETTINGS)} == canonical
    alternate = family.program({"translation_policy": "payload_axis_gate"})
    assert alternate not in canonical
    assert "bbox-of-cells" in alternate
    assert "payload-axis" in alternate.lower()


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_exact_setting_neutral_unique_and_prefix_stable(family, demos, queries):
    before = random.getstate()
    direct = family.generate(17, {"translation_policy": "marker_vector"}, demos, queries)
    gated = family.generate(17, {"translation_policy": "payload_axis_gate"}, demos, queries)
    assert random.getstate() == before

    assert len(direct["train"]) == len(gated["train"]) == demos
    assert len(direct["test"]) == len(gated["test"]) == queries
    assert _inputs(direct) == _inputs(gated)
    assert len({_digest(grid) for grid in _inputs(direct)}) == demos + queries
    assert direct["program_solution"] == family.program({"translation_policy": "marker_vector"})
    assert gated["program_solution"] == family.program({"translation_policy": "payload_axis_gate"})

    longest = family.generate(17, {"translation_policy": "marker_vector"}, 6, 4)
    assert direct["train"] == longest["train"][:demos]
    assert direct["test"] == longest["test"][:queries]

    # Callers cannot mutate a cached/template episode.
    direct["test"][0]["input"][0][0] = 9
    fresh = family.generate(17, {"translation_policy": "marker_vector"}, demos, queries)
    assert fresh["test"][0]["input"][0][0] != 9


@pytest.mark.parametrize("setting", ("marker_vector", "payload_axis_gate"))
@pytest.mark.parametrize("seed", (0, 17, 2**32 + 9))
def test_minimum_lesson_identifies_setting_and_exposes_both_axis_branches(family, setting, seed):
    episode = family.generate(seed, {"translation_policy": setting}, demos=2, queries=4)
    axes = [family.scene_facts(pair["input"])["payload_axis"] for pair in episode["train"]]
    assert axes == ["wide", "tall"]
    assert family.finite_setting_survivors(episode["train"]) == [setting]
    reports = family.audit_shortcuts(episode["train"], selected=setting)
    assert reports
    assert all(row["refuted"] for row in reports), reports
    assert all(row["mismatching_demo_indices"] for row in reports), reports


@pytest.mark.parametrize("setting", ("marker_vector", "payload_axis_gate"))
def test_every_generated_input_is_canonical_lawful_and_labels_match_python_claim(family, setting):
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = family.generate(101, {"translation_policy": setting}, demos=6, queries=4)
    for pair in _all_pairs(episode):
        assert generator.self_check(pair["input"]) == []
        assert pair["output"] == family.transform(pair["input"], setting)
        assert family.transform(pair["input"], "marker_vector") != family.transform(
            pair["input"], "payload_axis_gate"
        )


def test_four_queries_cover_large_fields_boundaries_and_substantive_30x30(family):
    episode = family.generate(101, {"translation_policy": "payload_axis_gate"}, demos=3, queries=4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(18, 22), (22, 18), (26, 30), (30, 30)]
    axes = [family.scene_facts(pair["input"])["payload_axis"] for pair in episode["test"]]
    assert axes == ["wide", "tall", "wide", "tall"]

    facts = family.scene_facts(episode["test"][-1]["input"])
    assert facts["payload_size"] >= 140
    assert facts["palette_size"] >= 3
    assert facts["boundary_contact"] is True
    assert facts["bbox_solid"] is False
    assert facts["canonical_delta"] != facts["gated_delta"]


def test_public_projection_masks_private_material_and_preserves_single_query_prefix(family):
    episode = family.generate(5, {"translation_policy": "payload_axis_gate"}, demos=3, queries=4)
    public = family.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "program_solution" not in _digest(public)

    single = family.public_challenge(
        family.generate(5, {"translation_policy": "payload_axis_gate"}, demos=3, queries=1)
    )
    assert public["train"] == single["train"]
    assert public["test"][:1] == single["test"]

    changed_private = deepcopy(episode)
    changed_private["test"][0]["output"][0][0] = (
        changed_private["test"][0]["output"][0][0] + 1
    ) % 10
    assert family.public_challenge(changed_private) == public
    assert public_challenge_bytes(family.public_challenge(changed_private)) == public_challenge_bytes(public)
    assert public_challenge_id(family.public_challenge(changed_private)) == public_challenge_id(public)


def test_wrong_axis_intermediate_changes_step_b_and_final_output(family):
    episode = family.generate(23, {"translation_policy": "payload_axis_gate"}, demos=2, queries=1)
    wide = episode["train"][0]["input"]
    trace = family.sequential_trace(wide, "payload_axis_gate")
    wrong = family.transform_with_axis(wide, "tall")
    assert trace["step_a"] == "classify payload bounding-box axis"
    assert trace["intermediate"] == "wide"
    assert trace["step_b"] == "choose marker-vector multiplier from payload axis, then translate"
    assert trace["selected_multiplier"] == 2
    assert wrong != episode["train"][0]["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"translation_policy": "marker_vector"}, 2, 4),
        (-1, {"translation_policy": "marker_vector"}, 2, 4),
        (2**63, {"translation_policy": "marker_vector"}, 2, 4),
        (0, {"translation_policy": "marker_vector"}, 1, 4),
        (0, {"translation_policy": "marker_vector"}, 7, 4),
        (0, {"translation_policy": "marker_vector"}, 2, 0),
        (0, {"translation_policy": "marker_vector"}, 2, 5),
        (0, {"translation_policy": "marker_vector"}, 2.0, 4),
        (0, {"translation_policy": "other"}, 2, 4),
        (0, {"mode": "marker_vector"}, 2, 4),
        (0, {"translation_policy": "marker_vector", "extra": 1}, 2, 4),
    ],
)
def test_invalid_requests_fail_before_sampling(family, seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        family.generate(seed, settings, demos, queries)


def test_adapter_uses_exact_adjacent_family_module(monkeypatch):
    foreign = types.ModuleType("family")
    foreign.program = lambda settings: "foreign"
    foreign.generate = lambda *args, **kwargs: {"foreign": True}
    monkeypatch.setitem(sys.modules, "family", foreign)
    adapter = _load(ADAPTER_PATH, "task_1a8932958b14_parametric_adapter_test")
    assert adapter.program({"translation_policy": "marker_vector"}) != "foreign"
    assert len(adapter.generate(7, {"translation_policy": "marker_vector"}, 2, 1)["train"]) == 2


def test_native_worker_executes_both_settings_through_protected_racket():
    assert CONTRACT_PATH.is_file(), "missing promotion contract"
    contract = json.loads(CONTRACT_PATH.read_text())
    jobs = [
        {"seed": 0, "settings": {"translation_policy": "marker_vector"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"translation_policy": "payload_axis_gate"}, "demos": 2, "queries": 4},
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["racket_evaluations"] >= 12
    assert [row["survivors"] for row in result["checks"]] == [
        [{"translation_policy": "marker_vector"}],
        [{"translation_policy": "payload_axis_gate"}],
    ]


def test_forced_wrong_intermediate_program_executes_and_changes_wide_case(family):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = family.generate(
        23, {"translation_policy": "payload_axis_gate"}, demos=2, queries=1
    )["train"][0]["input"]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    correct_source = family.program({"translation_policy": "payload_axis_gate"})
    wrong_source = family.forced_axis_program("tall")
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        correct = bridge.eval_text(f"({wrap_rule(correct_source)} {literal})")
        wrong = bridge.eval_text(f"({wrap_rule(wrong_source)} {literal})")
    assert correct == family.transform(grid, "payload_axis_gate")
    assert wrong == family.transform_with_axis(grid, "tall")
    assert correct != wrong


def test_admission_recipe_selects_qualified_wide_case_and_wrong_intermediate(family):
    builder = _load(BUILDER_PATH, "task_1a8932958b14_native_evidence_builder_test")
    default = family.generate(0, {"translation_policy": "marker_vector"}, demos=3, queries=4)
    gated = family.generate(0, {"translation_policy": "payload_axis_gate"}, demos=3, queries=4)
    execution = {
        "episodes": [
            {"settings": {"translation_policy": "marker_vector"}, **default},
            {"settings": {"translation_policy": "payload_axis_gate"}, **gated},
        ]
    }

    recipe = builder._admission_recipe(execution, family)

    assert recipe["step_a"] == "classify payload bounding-box axis"
    assert recipe["intermediate"] == "payload_axis in {wide, tall}"
    assert recipe["step_b"] == "choose marker-vector multiplier from payload axis, then translate"
    assert "cannot be known until Step A" in recipe["why_b_depends_on_a"]
    assert len(recipe["cases"]) == 1
    case = recipe["cases"][0]
    assert case["episode_index"] == 1
    assert case["split"] == "train"
    selected = gated[case["split"]][case["pair_index"]]
    trace = family.sequential_trace(selected["input"], "payload_axis_gate")
    assert case["intermediate_value"] == trace["intermediate"] == "wide"
    assert case["ablation"] == "wrong_intermediate"
    assert case["counterfactual_program"] == family.forced_axis_program("tall")
    assert family.transform_with_axis(selected["input"], "tall") != selected["output"]
