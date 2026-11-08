"""Bounded, live-Racket regressions for actual parent-choice teaching holes."""
from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import find_root


ROOT = find_root(__file__)
AUDIT_PATH = ROOT / "generators/f59691ac00f3/workspace/parametric/self_audit.py"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("parent_choice_self_audit", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def evaluator(audit):
    with audit.protected_evaluator(ROOT) as result:
        yield result


@pytest.mark.parametrize("seed,expected", [(0, [True] * 4), (1, [True, False, False, False])])
def test_original_visible_lesson_has_a_depth_cap_counterexample(audit, evaluator, seed, expected):
    execute, identity = evaluator
    # The task-test runner deliberately omits historical evidence archives.
    # Recreate the exact legacy lesson from its deterministic sampler instead
    # of depending on files that do not belong to the executable test closure.
    episode = audit._normalize_episode(audit._prototype.make_episode(seed, root=ROOT), ROOT)
    report = audit.audit_episode(episode, execute=execute, racket=identity, root=ROOT)
    cap = next(row for row in report["rivals"] if row["name"] == "depth_cap")
    assert report["status"] == "counterexample_found"
    assert cap["fits_all_demonstrations"] is True
    assert cap["query_differs"] == expected
    assert cap["counterexample"] is True
    assert cap["replay_case"]["train"] == episode["train"]
    assert cap["replay_case"]["query"]["output"] != cap["replay_case"]["counterfactual_output"]


@pytest.mark.parametrize("policy", ["right", "left"])
def test_support_hole_rejects_endpoint_shortcut_without_rejecting_binary_equivalence(
    audit, evaluator, policy
):
    execute, _ = evaluator
    program = audit.selected_program(policy, root=ROOT)
    candidates = {row["name"]: row for row in audit.rival_programs(program, depth_cap=4)}
    grid = [[2, 7, 7, 7, 5, 7, 2, 7, 5], *[[7] * 9 for _ in range(4)]]
    correct = execute(program, grid)
    endpoint_only = execute(candidates["endpoint_support_only"]["program"], grid)
    equivalent = execute(candidates["equivalent_complement"]["program"], grid)
    assert correct[2][2] == 7
    assert endpoint_only[2][2] in (2, 5)
    assert equivalent == correct
    assert candidates["equivalent_complement"]["answer_equivalent"] is True


@pytest.mark.parametrize("policy", ["right", "left"])
def test_native_teaching_repairs_depth_and_internal_support_ambiguity(audit, evaluator, policy):
    execute, identity = evaluator
    path = AUDIT_PATH.with_name("adapter.py")
    spec = importlib.util.spec_from_file_location("parent_choice_audit_native_adapter", path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    settings = {"different_parent": policy}
    episode = {**adapter.generate(0, settings, 2, 4), "seed": 0, "settings": settings}
    report = audit.audit_episode(episode, execute=execute, racket=identity, root=ROOT)
    rivals = {row["name"]: row for row in report["rivals"]}
    assert report["status"] == "no_counterexample_found"
    assert report["max_demonstration_depth"] == 14
    assert rivals["depth_cap"]["fits_all_demonstrations"] is True
    assert rivals["depth_cap"]["query_differs"] == [False] * 4
    assert rivals["endpoint_support_only"]["refuting_demonstration_index"] == 1
    assert all(rivals[name]["fits_all_demonstrations"] is False for name in (
        "opposite_setting", "frozen_input_parents", "omit_opposite_support_gate",
        "endpoint_support_only",
    ))
    assert rivals["equivalent_complement"]["query_differs"] == [False] * 4
