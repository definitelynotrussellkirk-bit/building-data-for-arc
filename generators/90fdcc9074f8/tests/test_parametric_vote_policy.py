"""Regressions for the three-panel vote-policy family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR = HOME / "generator.py"


def load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load(GENERATOR, "_test_90_generator")


@pytest.fixture(scope="module")
def prototype():
    return load(PROTOTYPE, "_test_90_parametric")


def inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_existing_base_draws_are_valid_majority_repair_inputs(generator):
    for seed in (0, 17, 43):
        for index in range(3):
            grid = generator.generate(seed, index, difficulty="medium")
            assert generator.self_check(grid) == []


def test_default_program_is_exact_canonical_and_matched_inputs_identify_vote_policy(prototype):
    from arcpuzzles import Catalog

    catalog = Catalog(ROOT)
    row = catalog.describe("90fdcc9074f8")
    canonical = {v["program_solution"] for v in catalog._variants()[row["rule_task_id"]]}
    assert canonical == {prototype.program({"vote_policy": "majority"})}

    majority = prototype.generate(17, {"vote_policy": "majority"}, demos=2, queries=4)
    unanimous = prototype.generate(17, {"vote_policy": "unanimous"}, demos=2, queries=4)
    assert inputs(majority) == inputs(unanimous)
    assert len({json.dumps(grid) for grid in inputs(majority)}) == 6
    assert majority["train"][0]["output"] != unanimous["train"][0]["output"]
    assert prototype.check_teaching(majority["train"], majority["settings"])["survivors"] == ["majority"]
    assert prototype.check_teaching(unanimous["train"], unanimous["settings"])["survivors"] == ["unanimous"]


@pytest.mark.parametrize("demos", [2, 6])
def test_demo_boundaries_and_query_prefix(prototype, demos):
    four = prototype.generate(29, {"vote_policy": "majority"}, demos=demos, queries=4)
    one = prototype.generate(29, {"vote_policy": "majority"}, demos=demos, queries=1)
    assert len(four["train"]) == demos
    assert len(four["test"]) == 4
    assert one["test"] == four["test"][:1]


def test_substantive_30x29_query_exercises_vote_then_depth(prototype):
    episode = prototype.generate(31, {"vote_policy": "unanimous"}, demos=3, queries=4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 29)
    analysis = prototype.analyze(stress)
    assert analysis["majority_cells"] >= 100
    assert analysis["unanimous_cells"] >= 60
    assert analysis["majority_cells"] > analysis["unanimous_cells"]
    assert max(max(row) for row in episode["test"][-1]["output"]) >= 3


def test_bounded_shortcut_audit_rejects_panel_union_and_skip_depth(prototype):
    report = prototype.audit(41)
    assert report["status"] == "passed"
    for setting in ("majority", "unanimous"):
        assert report["settings"][setting]["survivors"] == [setting]
        assert all(row["rejected"] for row in report["settings"][setting]["rivals"].values())


def test_python_labels_match_protected_racket_for_both_settings(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def apply(bridge, source, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")

    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["protected"] is True
        for setting in ("majority", "unanimous"):
            episode = prototype.generate(41, {"vote_policy": setting}, demos=2, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert apply(bridge, episode["program_solution"], pair["input"]) == pair["output"]


def test_invalid_contract_tampered_labels_and_public_projection(prototype):
    from reviewer_support import public_challenge_bytes

    for kwargs in ({"demos": 1, "queries": 4}, {"demos": 7, "queries": 4}, {"demos": 3, "queries": 0}, {"demos": 3, "queries": 5}):
        with pytest.raises(ValueError):
            prototype.generate(0, {"vote_policy": "majority"}, **kwargs)
    with pytest.raises(ValueError):
        prototype.program({"vote_policy": "plurality"})
    episode = prototype.generate(7, {"vote_policy": "majority"}, demos=2, queries=4)
    visible = public_challenge_bytes(episode)
    changed = deepcopy(episode)
    changed["settings"] = {"vote_policy": "unanimous"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == visible
    bad = deepcopy(episode)
    bad["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError):
        prototype.verify_episode(bad)
