"""Focused tests for the native source-cue stamp-anchor family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "b985d561c63b_parametric_prototype_test")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_byte_exact_and_alternative_is_guarded_source_edit():
    prototype = _prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.program_for("top_left", root=ROOT) == canonical

    alternate = prototype.program_for("hole_corner", root=ROOT)
    assert alternate == prototype.materialize_hole_corner_rule(canonical)
    assert alternate != canonical
    assert (PARAMETRIC / "rules" / "hole_corner_anchor.rkt").read_text() == alternate

    wrong = prototype.fixed_anchor_program("bottom_left", root=ROOT)
    assert wrong != canonical
    assert wrong != alternate
    assert (PARAMETRIC / "rules" / "fixed_bottom_left.rkt").read_text() == wrong

    for bad in (True, 0, None, "bottom_right", "source_hole"):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad, root=ROOT)


def test_adapter_contract_is_thin_and_counts_are_independent():
    prototype = _prototype()
    adapter = _load(ADAPTER_PATH, "b985d561c63b_parametric_adapter_test")
    promotion = json.loads(PROMOTION_PATH.read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/b985d561c63b/workspace/parametric/adapter.py",
        "parameters": {"stamp_anchor": ["top_left", "hole_corner"]},
        "default": {"stamp_anchor": "top_left"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/b985d561c63b/workspace/parametric/rules/hole_corner_anchor.rkt",
            "generators/b985d561c63b/workspace/parametric/rules/fixed_bottom_left.rkt",
        ],
    }
    for setting in prototype.ALLOWED_STAMP_ANCHORS:
        settings = {"stamp_anchor": setting}
        assert adapter.program(settings) == prototype.program_for(setting, root=ROOT)
        episode = adapter.generate(17, settings, demos=2, queries=1)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 1
        assert episode["program_solution"] == adapter.program(settings)

    for bad_settings in ({}, {"stamp_anchor": "top_left", "extra": 1}, {"stamp_anchor": True}):
        with pytest.raises(ValueError):
            adapter.program(bad_settings)


def test_generation_is_deterministic_prefix_stable_and_setting_independent():
    prototype = _prototype()
    for seed in (0, 17, 2**63 - 1):
        small = prototype.generate_episode(seed, stamp_anchor="top_left", demos=2, queries=1)
        large = prototype.generate_episode(seed, stamp_anchor="top_left", demos=6, queries=4)
        assert small == prototype.generate_episode(seed, stamp_anchor="top_left", demos=2, queries=1)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]

        alternate = prototype.generate_episode(seed, stamp_anchor="hole_corner", demos=6, queries=4)
        assert _inputs(large) == _inputs(alternate)
        assert large["program_solution"] != alternate["program_solution"]
        assert all(pair["input"] != other["input"] for i, pair in enumerate(large["train"] + large["test"])
                   for other in (large["train"] + large["test"])[i + 1 :])

    for bad in (True, -1, 2**63, 1.0, "1"):
        with pytest.raises(ValueError):
            prototype.generate_episode(bad, stamp_anchor="top_left")
    for demos in (1, 7, True):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, stamp_anchor="top_left", demos=demos)
    for queries in (0, 5, True):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, stamp_anchor="top_left", queries=queries)


def test_two_demonstrations_identify_each_setting_and_refute_fixed_shortcuts():
    prototype = _prototype()
    rival_corners = ("top_left", "top_right", "bottom_left", "bottom_right")
    for chosen in prototype.ALLOWED_STAMP_ANCHORS:
        episode = prototype.generate_episode(23, stamp_anchor=chosen, demos=2, queries=4)
        demos = episode["train"]

        other = next(value for value in prototype.ALLOWED_STAMP_ANCHORS if value != chosen)
        assert any(
            prototype.apply_python(pair["input"], stamp_anchor=other) != pair["output"]
            for pair in demos
        )

        for corner in rival_corners:
            predictions = [
                prototype.apply_python(
                    pair["input"], stamp_anchor="hole_corner", corner_override=corner
                )
                for pair in demos
            ]
            if chosen == "top_left" and corner == "top_left":
                assert predictions == [pair["output"] for pair in demos]
            else:
                assert any(prediction != pair["output"] for prediction, pair in zip(predictions, demos))

        nonzero_predictions = [
            prototype.apply_python(
                pair["input"], stamp_anchor=chosen, copy_template_zeros=False
            )
            for pair in demos
        ]
        assert any(prediction != pair["output"] for prediction, pair in zip(nonzero_predictions, demos))


def test_racket_labels_match_python_claims_for_full_profiles():
    prototype = _prototype()
    with prototype.RacketBridge(max_calls_before_restart=128) as bridge:
        for seed in (0, 17):
            for setting in prototype.ALLOWED_STAMP_ANCHORS:
                episode = prototype.generate_episode(seed, stamp_anchor=setting, demos=6, queries=4)
                source = prototype.program_for(setting, root=ROOT)
                for pair in episode["train"] + episode["test"]:
                    assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_fourth_query_is_substantive_30x30_boundary_stress():
    prototype = _prototype()
    canonical = prototype.generate_episode(7, stamp_anchor="top_left", demos=3, queries=4)
    alternate = prototype.generate_episode(7, stamp_anchor="hole_corner", demos=3, queries=4)
    grid = canonical["test"][3]["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    features = prototype.input_features(grid)
    assert features["source_shape"] == [5, 5]
    assert features["target_count"] == 4
    assert features["hole_corner"] == "bottom_right"
    assert features["target_cells"] >= 300
    assert features["targets_touching_boundary"] >= 3
    assert canonical["test"][3]["output"] != alternate["test"][3]["output"]


def test_public_projection_omits_private_setting_program_and_query_answers():
    prototype = _prototype()
    episode = prototype.generate_episode(17, stamp_anchor="hole_corner", demos=3, queries=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "hole_corner" not in json.dumps(public)
    assert episode["settings"] == {"stamp_anchor": "hole_corner"}

    changed_private = copy.deepcopy(episode)
    changed_private["settings"] = {"stamp_anchor": "top_left"}
    changed_private["program_solution"] = "private-change"
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
    assert prototype.public_challenge(changed_private) == public
    assert prototype.public_id(changed_private) == prototype.public_id(episode)


def test_self_review_audit_is_racket_labeled_and_keeps_minimal_case(tmp_path):
    audit = _load(PARAMETRIC / "audit.py", "b985d561c63b_parametric_audit_test")
    report = audit.run_audit(seeds=(0,), out=tmp_path / "audit")
    assert report["schema"] == "arcpuzzles-parametric-self-review-v1"
    assert report["status"] == "passed"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["counts"]["jobs"] == 2
    assert report["counts"]["ambiguous_wrong_rivals"] == 0
    case = json.loads((tmp_path / "audit" / "minimal-counterexample.json").read_text())
    assert case["actual_output"] != case["wrong_intermediate_output"]
    assert case["intermediate_value"] == "top_right"
    assert case["ablation"] == "wrong_intermediate"
