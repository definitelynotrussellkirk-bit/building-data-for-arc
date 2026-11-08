from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "f112ec4615da"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "priority prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("f112ec4615da_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_default_are_exact():
    proto = _prototype()
    assert tuple(proto.PRIORITY_SETTINGS) == ("canonical", "reverse")
    assert proto.DEFAULT_PRIORITY == "canonical"
    assert proto.instantiate_rule("canonical") == proto.canonical_rule()
    assert proto.instantiate_rule("reverse") != proto.canonical_rule()
    assert proto.choose_priority(0) == "canonical"
    assert proto.choose_priority(1) == "reverse"
    for bad in (True, 1.5, "0"):
        with pytest.raises((TypeError, ValueError)):
            proto.choose_priority(bad)
    for bad in (True, 0, "sideways"):
        with pytest.raises((TypeError, ValueError)):
            proto.instantiate_rule(bad)


def test_inputs_do_not_depend_on_the_hidden_setting():
    proto = _prototype()
    first = proto.generate_inputs(23)
    second = proto.generate_inputs(23)
    assert first == second
    assert len(first) == 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 4
    assert all(proto.GEN.self_check(grid) == [] for grid in first)


def test_real_racket_labels_distinguish_settings_and_all_query_rotations():
    proto = _prototype()
    with RacketBridge() as bridge:
        for seed in (0, 1):
            episode = proto.make_episode(bridge, seed)
            analysis = proto.analyze_episode(bridge, episode)
            expected_setting = proto.choose_priority(seed)
            assert episode["parameters"] == {"priority_order": expected_setting}
            assert analysis["production"]["status"] == "no_ambiguity_found"
            assert all(row["status"] == "no_ambiguity_found" for row in analysis["rotations"])
            assert all(
                rival["refuting_demonstration_indices"]
                for rival in analysis["production"]["rivals"]
            )

        canonical = proto.instantiate_rule("canonical")
        reverse = proto.instantiate_rule("reverse")
        witness = proto.generate_inputs(7)[0]
        assert proto.evaluate(bridge, canonical, witness) != proto.evaluate(bridge, reverse, witness)

        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert proto.evaluate(bridge, canonical, pair["input"]) == pair["output"]


def test_materialized_public_files_hide_parameters_code_and_query_answers(tmp_path):
    proto = _prototype()
    out = tmp_path / "evidence"
    report = proto.materialize(out, seed=0)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_passed"] == 7
    assert report["counts"]["production_ambiguities"] == 0
    assert report["counts"]["rotation_ambiguities"] == 0

    for path in sorted((out / "public").glob("*.json")):
        challenge = json.loads(path.read_text(encoding="utf-8"))
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 3
        assert challenge["test"] and set(challenge["test"][0]) == {"input"}
        text = path.read_text(encoding="utf-8")
        assert "priority_order" not in text
        assert "racket" not in text.lower()

    with pytest.raises(FileExistsError):
        proto.materialize(out, seed=0)
