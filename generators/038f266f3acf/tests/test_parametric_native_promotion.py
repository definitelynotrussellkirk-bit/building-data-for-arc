"""Native promotion contract for the marker-derived beam-width family."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root


TASK_ID = "038f266f3acf"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
VERIFY_CAUSAL = PARAMETRIC / "verify_causal.py"
AUDIT_NATIVE = PARAMETRIC / "audit_native.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "_beam_width_native_test", ADAPTER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _dimensions(grid):
    return len(grid), len(grid[0])


def test_native_contract_declares_two_settings_and_exact_four_queries():
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/038f266f3acf/workspace/parametric/adapter.py",
        "parameters": {"wing_multiplier": [1, 2]},
        "default": {"wing_multiplier": 1},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_adapter_program_preserves_exact_canonical_default_and_changes_only_wing_scale():
    # A generic cached module must not replace the adjacent exact prototype.
    fake = types.ModuleType("beam_width")
    fake.materialize_program = lambda *_args, **_kwargs: "WRONG CACHED MODULE"
    previous = sys.modules.get("beam_width")
    sys.modules["beam_width"] = fake
    try:
        adapter = _load_adapter()
    finally:
        if previous is None:
            sys.modules.pop("beam_width", None)
        else:
            sys.modules["beam_width"] = previous

    canonical = _canonical_program()
    assert adapter.program({"wing_multiplier": 1}) == canonical
    assert adapter.program({"wing_multiplier": 2}) == canonical.replace(
        "(range 1 (+ half 1))",
        "(range 1 (+ (* 2 half) 1))",
    )
    for bad in (
        None,
        {},
        {"wing_multiplier": True},
        {"wing_multiplier": 1.0},
        {"wing_multiplier": "1"},
        {"wing_multiplier": 0},
        {"wing_multiplier": 3},
        {"wing_multiplier": 1, "extra": 0},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def test_adapter_generation_is_matched_deterministic_and_needs_no_nested_racket(monkeypatch):
    adapter = _load_adapter()

    class ForbiddenRacketOracle:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("native adapter generation must not start nested Racket")

    monkeypatch.setattr(adapter._prototype, "RacketOracle", ForbiddenRacketOracle)
    first = adapter.generate(17, {"wing_multiplier": 1}, 2, 4)
    again = adapter.generate(17, {"wing_multiplier": 1}, 2, 4)
    alternate = adapter.generate(17, {"wing_multiplier": 2}, 2, 4)

    assert first == again
    assert set(first) == {"train", "test", "program_solution"}
    assert (len(first["train"]), len(first["test"])) == (2, 4)
    assert _inputs(first) == _inputs(alternate)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            first["train"] + first["test"],
            alternate["train"] + alternate["test"],
        )
    )
    identities = {json.dumps(grid, separators=(",", ":")) for grid in _inputs(first)}
    assert len(identities) == 6
    assert (30, 30) in {_dimensions(pair["input"]) for pair in first["test"]}


def test_demo_count_is_prefix_stable_and_does_not_change_four_queries():
    adapter = _load_adapter()
    short = adapter.generate(91, {"wing_multiplier": 2}, 2, 4)
    long = adapter.generate(91, {"wing_multiplier": 2}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]
    assert (len(long["train"]), len(long["test"])) == (6, 4)


def test_adapter_rejects_counts_and_seed_outside_native_contract():
    adapter = _load_adapter()
    for demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"wing_multiplier": 1}, demos, 4)
    for queries in (True, 1, 3, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"wing_multiplier": 1}, 2, queries)
    for seed in (True, -1, 2**63, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"wing_multiplier": 1}, 2, 4)



def _load_causal():
    spec = importlib.util.spec_from_file_location(
        "_beam_width_causal_test", VERIFY_CAUSAL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setting_key(settings):
    return json.dumps(settings, sort_keys=True, separators=(",", ":"))


def test_causal_recipe_selects_max_size_case_per_setting_and_binds_program_hash():
    adapter = _load_adapter()
    causal = _load_causal()
    episodes = []
    programs = {}
    for multiplier in (1, 2):
        settings = {"wing_multiplier": multiplier}
        generated = adapter.generate(17, settings, 2, 4)
        program = generated["program_solution"]
        programs[_setting_key(settings)] = hashlib.sha256(program.encode()).hexdigest()
        episodes.append({
            "settings": settings,
            "program": program,
            "train": generated["train"],
            "test": generated["test"],
        })
    recipe = causal.make_recipe({"programs": programs}, {"episodes": episodes})

    assert set(recipe) == {
        "step_a", "intermediate", "step_b", "why_b_depends_on_a", "cases"
    }
    assert len(recipe["cases"]) == 2
    assert {case["episode_index"] for case in recipe["cases"]} == {0, 1}
    assert all(case["split"] == "test" for case in recipe["cases"])
    assert all(case["pair_index"] == 3 for case in recipe["cases"])
    assert all(case["ablation"] == "wrong_intermediate" for case in recipe["cases"])
    assert all(case["intermediate_value"]["source_depths"] == [5, 6]
               for case in recipe["cases"])
    assert all(case["intermediate_value"]["wrong_depth_cap"] == 4
               for case in recipe["cases"])

    for episode, case in zip(episodes, recipe["cases"]):
        grid = episode["test"][case["pair_index"]]["input"]
        multiplier = episode["settings"]["wing_multiplier"]
        counterfactual = adapter._prototype.simulate(grid, multiplier, cap_depth=4)
        assert counterfactual != episode["test"][case["pair_index"]]["output"]
        assert case["counterfactual_program"] == adapter._prototype.materialize_program(
            multiplier, cap_depth=4
        )


def test_causal_recipe_rejects_unqualified_program_and_deduplicates_settings():
    adapter = _load_adapter()
    causal = _load_causal()
    settings = {"wing_multiplier": 1}
    generated = adapter.generate(4, settings, 2, 4)
    episode = {
        "settings": settings,
        "program": generated["program_solution"],
        "train": generated["train"],
        "test": generated["test"],
    }
    with pytest.raises(ValueError, match="qualified program"):
        causal.make_recipe({"programs": {}}, {"episodes": [episode]})
    qualified = {"programs": {
        _setting_key(settings): hashlib.sha256(
            generated["program_solution"].encode()
        ).hexdigest()
    }}
    duplicate = json.loads(json.dumps(episode))
    recipe = causal.make_recipe(qualified, {"episodes": [episode, duplicate]})
    assert len(recipe["cases"]) == 1
    duplicate["program"] = adapter.program({"wing_multiplier": 2})
    with pytest.raises(ValueError, match="qualified program"):
        causal.make_recipe(qualified, {"episodes": [episode, duplicate]})



def _load_audit():
    spec = importlib.util.spec_from_file_location(
        "_beam_width_audit_test", AUDIT_NATIVE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_audit_checks_matched_settings_and_supported_count_edges():
    audit = _load_audit()
    receipt = audit.audit_matrix(seeds=[0, 1], demo_counts=[2, 6])
    assert receipt["schema"] == "038f266f3acf-native-audit-v1"
    assert receipt["status"] == "passed"
    assert receipt["summary"] == {
        "seeds": 2,
        "demo_counts": 2,
        "settings": 2,
        "episodes": 8,
        "pairs": 64,
        "failures": 0,
    }
    assert len(receipt["records"]) == 4
    assert all(record["matched_input_streams"] for record in receipt["records"])
    assert all(record["all_outputs_disagree"] for record in receipt["records"])
    assert all(record["query_shapes"][-1] == [30, 30]
               for record in receipt["records"])
