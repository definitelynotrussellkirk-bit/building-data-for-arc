"""Native parametric-family tests for dfc3ce537883."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
DEFAULT = {"followup": "mirror_only"}
ALTERNATE = {"followup": "fill_contacted_frame"}


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing native parametric source: {path.relative_to(ROOT)}"
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    from arcpuzzles import Catalog

    variants = Catalog(ROOT)._variants()["dfc3ce537883"]
    programs = {row["program_solution"] for row in variants}
    assert len(programs) == 1
    return next(iter(programs))


def _hand_scene() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 3, 3, 3],
        [0, 0, 0, 2, 0, 0, 9, 0, 0, 0, 3, 0, 3],
        [0, 0, 0, 2, 0, 0, 9, 0, 0, 0, 3, 3, 3],
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 4, 4, 0, 0],
        [0, 7, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
    ]


def _hand_alternate_output() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 1, 1, 1],
        [0, 0, 0, 2, 0, 0, 9, 0, 0, 2, 1, 1, 1],
        [0, 0, 0, 2, 0, 0, 9, 0, 0, 2, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 0, 4, 4, 4, 0, 0],
        [0, 7, 0, 0, 0, 0, 9, 0, 0, 0, 0, 7, 0],
    ]


def test_promotion_contract_and_default_program_are_exact():
    adapter = _load("dfc3ce_adapter", "adapter.py")
    promotion_path = PARAMETRIC / "promotion.json"
    assert promotion_path.is_file()
    contract = json.loads(promotion_path.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/dfc3ce537883/workspace/parametric/adapter.py",
        "parameters": {"followup": ["mirror_only", "fill_contacted_frame"]},
        "default": DEFAULT,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program(DEFAULT) == _canonical_program()
    assert adapter.program(ALTERNATE) != adapter.program(DEFAULT)


def test_matched_inputs_exact_counts_and_global_uniqueness():
    adapter = _load("dfc3ce_adapter_counts", "adapter.py")
    for demos in range(2, 7):
        canonical = adapter.generate(17, DEFAULT, demos, 4)
        alternate = adapter.generate(17, ALTERNATE, demos, 4)
        assert canonical["program_solution"] == adapter.program(DEFAULT)
        assert alternate["program_solution"] == adapter.program(ALTERNATE)
        assert len(canonical["train"]) == len(alternate["train"]) == demos
        assert len(canonical["test"]) == len(alternate["test"]) == 4
        canonical_inputs = [pair["input"] for pair in canonical["train"] + canonical["test"]]
        alternate_inputs = [pair["input"] for pair in alternate["train"] + alternate["test"]]
        assert canonical_inputs == alternate_inputs
        serialized = [json.dumps(grid, separators=(",", ":")) for grid in canonical_inputs]
        assert len(serialized) == len(set(serialized))


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"followup": "unknown"}, 3, 4),
        ({}, 3, 4),
        (DEFAULT, True, 4),
        (DEFAULT, 1, 4),
        (DEFAULT, 3, 3),
        (DEFAULT, 3, 5),
    ],
)
def test_direct_adapter_rejects_undeclared_settings_and_counts(settings, demos, queries):
    adapter = _load("dfc3ce_adapter_validation", "adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, demos, queries)


def test_alternate_semantics_are_anchored_by_a_hand_checked_scene():
    prototype = _load("dfc3ce_prototype", "prototype.py")
    scene = _hand_scene()
    assert prototype.inspect_contact(scene) == {
        "candidate_color": 3,
        "candidate_cells": 8,
        "bbox": [1, 10, 3, 12],
        "fill_color": 1,
    }
    assert prototype.apply_python(scene, DEFAULT) != _hand_alternate_output()
    assert prototype.apply_python(scene, ALTERNATE) == _hand_alternate_output()


def test_two_demos_leave_only_the_episode_setting_among_declared_rivals():
    adapter = _load("dfc3ce_adapter_teaching", "adapter.py")
    prototype = _load("dfc3ce_prototype_teaching", "prototype.py")
    for chosen in (DEFAULT, ALTERNATE):
        episode = adapter.generate(23, chosen, 2, 4)
        assert prototype.surviving_followups(episode["train"]) == [chosen["followup"]]


def test_query_audit_requires_four_distinct_profiles_and_substantive_30x30_content():
    prototype = _load("dfc3ce_prototype_audit", "prototype.py")
    episode = prototype.make_episode(
        17,
        followup="fill_contacted_frame",
        demos=3,
        queries=4,
    )
    audit = prototype.audit_episode(episode)
    assert audit["query_shapes"] == [[12, 18], [18, 24], [24, 28], [30, 30]]
    assert audit["all_inputs_distinct"] is True
    assert audit["large_query"] == {
        "shape": [30, 30],
        "content_bbox": [0, 2, 29, 23],
        "content_cells": 40,
        "left_content_cells": 20,
        "right_content_cells": 20,
        "palette": [2, 3, 4, 6, 7, 8],
    }


def test_wrong_intermediate_ablation_changes_the_final_output():
    prototype = _load("dfc3ce_prototype_dependency", "prototype.py")
    scene = _hand_scene()
    case = prototype.build_dependency_case(scene)
    assert case["settings"] == ALTERNATE
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"] == {
        "candidate_color": 3,
        "candidate_cells": 8,
        "bbox": [1, 10, 3, 12],
        "fill_color": 1,
    }
    assert case["output"] == _hand_alternate_output()
    assert case["counterfactual_output"] != case["output"]
    assert case["counterfactual_output"][5][8:11] == [1, 1, 1]
    assert case["program"] == prototype.program_for("fill_contacted_frame")
    assert case["counterfactual_program"] == prototype.counterfactual_program()


def test_plausible_shortcuts_are_refuted_by_the_two_visible_demos():
    prototype = _load("dfc3ce_prototype_shortcuts", "prototype.py")
    episode = prototype.make_episode(
        17,
        followup="fill_contacted_frame",
        demos=2,
        queries=4,
    )
    assert prototype.plausible_shortcut_survivors(episode["train"]) == []


def test_first_turn_projection_is_single_query_and_future_query_invariant():
    evidence = _load("dfc3ce_evidence_projection", "evidence_tool.py")
    prototype = _load("dfc3ce_prototype_projection", "prototype.py")
    episode = prototype.make_episode(17, followup="fill_contacted_frame", demos=2, queries=4)
    first = evidence.first_turn_public_bytes(episode)
    projected = json.loads(first)
    assert set(projected) == {"train", "test"}
    assert len(projected["train"]) == 2
    assert len(projected["test"]) == 1
    assert set(projected["test"][0]) == {"input"}

    altered = deepcopy(episode)
    altered["test"][1:] = [
        {"input": [[9]], "output": [[8]]},
        {"input": [[7]], "output": [[6]]},
        {"input": [[5]], "output": [[4]]},
    ]
    altered["future_query_count"] = 999
    assert evidence.first_turn_public_bytes(altered) == first
