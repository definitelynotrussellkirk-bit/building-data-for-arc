"""Prototype-only regressions; these do not approve a production rule variant."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "b44c4c938f42"
ROOT = find_root(__file__)
PROTOTYPE = (Path(__file__).resolve().parent.parent /
             "workspace/parametric/prototype.py")
CANONICAL_SHA256 = "c28d990306ed0cc7d8a1c3bb6c9bbb0db4012f9c53124a7b0dc137eca66c4707"
LEFT_FORM = """(shifts (list (list 0 0) (list 0 -1) (list 0 1) (list -1 0) (list 1 0)
                       (list -1 -1) (list -1 1) (list 1 -1) (list 1 1)
                       (list 0 -2) (list 0 2) (list -2 0) (list 2 0)))"""
RIGHT_FORM = """(shifts (list (list 0 0) (list 0 1) (list 0 -1) (list -1 0) (list 1 0)
                       (list -1 1) (list -1 -1) (list 1 1) (list 1 -1)
                       (list 0 2) (list 0 -2) (list -2 0) (list 2 0)))"""


def _prototype():
    # Missing implementation produces an assertion failure in the red phase,
    # rather than an import/collection error.
    assert PROTOTYPE.is_file(), "task-local shift-preference prototype is missing"
    spec = importlib.util.spec_from_file_location("shift_preference_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10) as live:
        yield live


def _canonical_program():
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def test_default_program_preserves_exact_canonical_bytes_and_all_labels(bridge):
    prototype = _prototype()
    sources = prototype.bind_sources(root=ROOT)
    program = prototype.program_for(sources=sources)
    assert program == _canonical_program()
    assert hashlib.sha256(program.encode()).hexdigest() == CANONICAL_SHA256
    assert sources["manifest"]["canonical_rule_hash"] == "10339930cb51"
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert prototype.execute_program(program, pair["input"], bridge=bridge) == pair["output"]


def test_alternative_changes_only_horizontal_shift_preference():
    prototype = _prototype()
    sources = prototype.bind_sources(root=ROOT)
    canonical = prototype.program_for("left_first", sources=sources)
    alternative = prototype.program_for("right_first", sources=sources)
    assert canonical.count(LEFT_FORM) == 1
    assert alternative == canonical.replace(LEFT_FORM, RIGHT_FORM)
    assert alternative != canonical


def test_lawful_collision_witness_separates_settings_in_real_racket(bridge):
    prototype = _prototype()
    sources = prototype.bind_sources(root=ROOT)
    witness = prototype.separating_input()
    assert sources["generator"].self_check(witness) == []
    outputs = {setting: prototype.execute_program(
        prototype.program_for(setting, sources=sources), witness, bridge=bridge)
        for setting in ("left_first", "right_first")}
    expected_left = [[8, 8, 8, 8, 8], [8, 3, 2, 8, 8],
                     [8, 3, 2, 8, 8], [8, 8, 2, 8, 8], [8, 8, 8, 8, 8]]
    expected_right = [[8, 8, 8, 8, 8], [8, 8, 2, 3, 8],
                      [8, 8, 2, 3, 8], [8, 8, 2, 8, 8], [8, 8, 8, 8, 8]]
    assert outputs == {"left_first": expected_left, "right_first": expected_right}


@pytest.mark.parametrize("seed,setting", [(0, "right_first"), (1, "left_first")])
def test_episode_uses_one_seed_selected_setting_and_every_query_rotation_is_identifiable(
        bridge, seed, setting):
    prototype = _prototype()
    episode = prototype.generate_episode(seed, bridge=bridge, root=ROOT)
    private = episode["private"]
    challenge = episode["challenge"]
    assert private["seed"] == seed
    assert private["parameters"] == {"horizontal_shift_preference": setting}
    assert len(private["pairs"]) == 4
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 1
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert challenge["train"] == private["pairs"][:3]
    assert challenge["test"] == [{"input": private["pairs"][3]["input"]}]
    for index, pair in enumerate(private["pairs"]):
        assert pair["output"] == private["rival_outputs"][setting][index]
        assert pair["output"] == prototype.execute_program(
            private["programs"][setting]["text"], pair["input"], bridge=bridge)
        assert (private["rival_outputs"]["left_first"][index] !=
                private["rival_outputs"]["right_first"][index])
    checks = private["identifiability"]
    assert checks["production"]["passed"] is True
    assert len(checks["query_rotations"]) == 4
    assert {row["query_index"] for row in checks["query_rotations"]} == set(range(4))
    assert all(row["passed"] and row["surviving_settings"] == [setting]
               for row in checks["query_rotations"])


def test_episode_replays_without_changing_global_rng_or_aliasing_public_data(bridge):
    prototype = _prototype()
    random.seed(918273)
    before = random.getstate()
    first = prototype.generate_episode(1, bridge=bridge, root=ROOT)
    second = prototype.generate_episode(1, bridge=bridge, root=ROOT)
    assert first == second
    assert random.getstate() == before
    untouched = copy.deepcopy(first["private"]["pairs"])
    first["challenge"]["train"][0]["input"][0][0] = 9
    assert first["private"]["pairs"] == untouched


def test_short_attempt_budget_fails_visibly_instead_of_returning_partial_episode(bridge):
    prototype = _prototype()
    with pytest.raises(RuntimeError, match="attempt budget"):
        prototype.generate_episode(0, bridge=bridge, root=ROOT, max_attempts=1)


@pytest.mark.parametrize("setting", ["up_first", "", 1, None])
def test_unsupported_parameter_values_reject(setting):
    prototype = _prototype()
    with pytest.raises((ValueError, TypeError), match="preference"):
        prototype.program_for(setting, sources=prototype.bind_sources(root=ROOT))


@pytest.mark.parametrize("seed", [True, 0.5, "1"])
def test_seed_must_be_integer_without_coercion(seed):
    prototype = _prototype()
    with pytest.raises((ValueError, TypeError), match="seed"):
        prototype.sample_preference(seed)


def test_source_binding_verification_rejects_changed_expected_bytes():
    prototype = _prototype()
    sources = prototype.bind_sources(root=ROOT)
    generator_file = sources["manifest"]["files"]["generator"]
    assert generator_file["sha256"] == hashlib.sha256(
        (ROOT / generator_file["path"]).read_bytes()).hexdigest()
    changed = dict(sources)
    changed["manifest"] = copy.deepcopy(sources["manifest"])
    changed["manifest"]["files"]["generator"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source binding changed"):
        prototype.verify_source_binding(changed)


def test_evidence_export_keeps_public_challenges_clean_and_binds_every_file(bridge, tmp_path):
    prototype = _prototype()
    out = tmp_path / "evidence"
    result = prototype.write_evidence(out, seeds=[0, 1], bands=["medium"],
                                      bridge=bridge, root=ROOT)
    assert result["status"] == "prototype_verified"
    assert result["counts"] == {"episodes": 2, "pairs": 8, "settings": 2,
                                "production_lessons_passed": 2,
                                "query_rotations_passed": 8,
                                "canonical_pairs_checked": 12,
                                "separating_witnesses": 1}
    assert {row["parameters"]["horizontal_shift_preference"]
            for row in result["episodes"]} == {"left_first", "right_first"}
    for row in result["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    for row in result["episodes"]:
        public = json.loads((out / row["challenge_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(query) == {"input"} for query in public["test"])
    with pytest.raises(FileExistsError):
        prototype.write_evidence(out, seeds=[0, 1], bands=["medium"],
                                  bridge=bridge, root=ROOT)
