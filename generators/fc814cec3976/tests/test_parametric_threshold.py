"""Bounded proposed min_reds extension; these are not canonical repair tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "missing runnable min_reds prototype"
    spec = importlib.util.spec_from_file_location("fc814cec3976_min_reds", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_preserves_exact_canonical_default():
    proto = load_prototype()
    canonical = proto.canonical_program(find_root(__file__))
    assert proto.MIN_REDS_VALUES == (1, 2, 3)
    assert proto.DEFAULT_MIN_REDS == 1
    assert proto.instantiate(canonical) == canonical
    assert [proto.choose_min_reds(seed) for seed in (4, 0, 1)] == [1, 2, 3]
    for value in proto.MIN_REDS_VALUES:
        program = proto.instantiate(canonical, value)
        assert proto.retained_rule_path(value).read_text() == program
        if value != 1:
            assert program.replace(
                f"(>= (length covered-twos) {value})", "(not (empty? covered-twos))"
            ) == canonical


@pytest.mark.parametrize("value", [None, True, False, 0, 4, 2.0, "2"])
def test_threshold_rejects_values_outside_the_declared_integer_domain(value):
    proto = load_prototype()
    with pytest.raises(ValueError, match="min_reds"):
        proto.instantiate(proto.canonical_program(find_root(__file__)), value)


def test_rule_template_drift_is_not_silently_accepted():
    proto = load_prototype()
    canonical = proto.canonical_program(find_root(__file__))
    drifted = canonical.replace("(not (empty? covered-twos))", "#t")
    with pytest.raises(ValueError, match="predicate"):
        proto.instantiate(drifted, 2)


def test_seeded_episode_keeps_one_parameter_and_independent_input_draws():
    proto = load_prototype()
    before = random.getstate()
    first = proto.episode_spec(4)
    assert first == proto.episode_spec(4)
    assert before == random.getstate()
    assert first["parameters"] == {"min_reds": 1}
    assert len(first["inputs"]) == 4
    assert len({json.dumps(grid) for grid in first["inputs"]}) == 4
    assert all(set(row) == {"pair_index", "motifs", "input_sha256"}
               for row in first["input_provenance"])
    assert first["inputs"] != proto.episode_spec(0)["inputs"]


def test_public_projection_whitelists_only_examples_and_query_inputs():
    proto = load_prototype()
    private = {
        "seed": 4, "parameters": {"min_reds": 1}, "program": "hidden",
        "program_sha256": "hidden", "rivals": ["hidden"],
        "train": [{"input": [[2]], "output": [[7]]}],
        "test": [{"input": [[5]], "output": [[4]]}],
    }
    public = proto.public_challenge(private)
    assert public == {
        "train": [{"input": [[2]], "output": [[7]]}],
        "test": [{"input": [[5]]}],
    }
    public["train"][0]["input"][0][0] = 9
    assert private["train"][0]["input"] == [[2]]


def test_overlap_trace_keeps_count_priority_ties_and_reused_red_rejection():
    proto = load_prototype()
    grid = [[5, 2, 2, 2, 2], [5, 5, 5, 5, 5], [5, 5, 2, 5, 5]]
    before = copy.deepcopy(grid)
    for value in proto.MIN_REDS_VALUES:
        trace = proto.candidate_trace(grid, value)
        assert [candidate["top_left"] for candidate in trace["eligible"]] == [
            [0, 1], [0, 2], [0, 0]
        ]
        assert [candidate["red_count"] for candidate in trace["eligible"]] == [4, 4, 3]
        assert trace["selected"] == [[0, 1]]
        assert len(trace["rejected"]) == 2
        assert all(candidate["reused_reds"] for candidate in trace["rejected"])
    assert grid == before


@pytest.mark.parametrize("value", [1, 2, 3])
def test_racket_rule_retains_first_selected_gray_overlap_and_eligibility(value):
    proto = load_prototype()
    canonical = proto.canonical_program(find_root(__file__))
    shared_gray = [[2, 5, 5, 2], [2, 5, 5, 2], [2, 5, 5, 2]]
    gray_only = [[5, 5, 5], [5, 5, 5], [5, 5, 5]]
    red_center = [[2, 2, 2], [2, 2, 2], [2, 2, 2]]
    blocked = [[0, 2, 2], [2, 5, 2], [2, 2, 2]]
    one_red = [[2, 5, 5], [5, 5, 5], [5, 5, 5]]
    two_reds = [[2, 2, 5], [5, 5, 5], [5, 5, 5]]
    inputs = [shared_gray, gray_only, red_center, blocked, one_red, two_reds]
    original = copy.deepcopy(inputs)
    receipt = proto.execute_program(proto.instantiate(canonical, value), inputs)
    assert receipt["backend"] == "racket" and receipt["status"] == "pass"
    assert receipt["test_outputs"] == [
        [[2, 7, 7, 2], [2, 4, 7, 2], [2, 7, 7, 2]],
        gray_only, red_center, blocked,
        [[2, 7, 7], [7, 4, 7], [7, 7, 7]] if value == 1 else one_red,
        [[2, 2, 7], [7, 4, 7], [7, 7, 7]] if value <= 2 else two_reds,
    ]
    assert inputs == original


def test_rival_audit_reports_an_ambiguous_demonstration_set():
    proto = load_prototype()
    outputs = {
        1: [[[7]], [[7]], [[4]]],
        2: [[[7]], [[7]], [[5]]],
        3: [[[7]], [[7]], [[5]]],
    }
    report = proto.parameter_rival_check(outputs, chosen=1, query_index=2)
    assert report["identifiable"] is False
    assert report["query_determined"] is False
    assert report["surviving_settings"] == [1, 2, 3]
    assert [row["status"] for row in report["rivals"]] == [
        "chosen", "undistinguished", "undistinguished"
    ]


def test_materialized_evidence_executes_all_rivals_and_query_roles(tmp_path):
    proto = load_prototype()
    destination = tmp_path / "threshold-evidence"
    report = proto.materialize(destination)
    assert report["status"] == "prototype"
    assert report["evidence_status"] == "pass"
    assert report["default_program_exact"] is True
    assert report["settings_seen"] == [1, 2, 3]
    assert report["episode_count"] == 3
    assert report["episode_label_count"] == 12
    assert report["parameter_rival_label_count"] == 24
    assert report["witness_output_count"] == 3
    assert report["canonical_unique_pair_count"] == 4
    assert report["racket_test_output_count"] == 43
    assert report["query_role_check_count"] == 12
    assert report["declared_setting_comparison_count"] == 36
    assert report["identifiable_query_roles"] == 12
    assert report["prototype_input_count_with_rejected_overlap"] == 12

    for index, seed in enumerate((4, 0, 1)):
        private = json.loads((destination / "private" / f"episode-{index}.json").read_text())
        public = json.loads((destination / "public" / f"episode-{index}.json").read_text())
        assert private["seed"] == seed
        assert private["parameters"] == {"min_reds": index + 1}
        assert len(private["train"]) == 3 and len(private["test"]) == 1
        assert public == proto.public_challenge(private)
        assert private["label_authority"] == "Racket execution"
        program_path = destination / private["program_path"]
        assert hashlib.sha256(program_path.read_bytes()).hexdigest() == private["program_sha256"]
        assert program_path.read_text() == private["program"]
        for role in private["query_roles"]:
            assert role["surviving_settings"] == [index + 1]
            assert role["identifiable"] and role["query_determined"]
            for rival in role["rivals"]:
                if rival["min_reds"] != index + 1:
                    assert rival["demo_differences"]
                    assert rival["query_differs"]
        assert all(trace["rejected"] for trace in private["input_traces"])

    witness = json.loads((destination / "private" / "cross-setting-witness.json").read_text())
    assert witness["outputs_pairwise_distinct"] is True
    assert set(witness["outputs"]) == {"1", "2", "3"}
    assert all(row["matches"] for row in report["canonical_checks"])
    with pytest.raises(FileExistsError):
        proto.materialize(destination)


# Native promotion contract -------------------------------------------------


def test_native_program_contract_preserves_all_retained_sources_and_rejects_bad_settings():
    """Catches source drift or a permissive setting parser in the native API."""
    proto = load_prototype()
    canonical = proto.canonical_program(find_root(__file__))
    for value in proto.MIN_REDS_VALUES:
        settings = {"min_reds": value}
        assert proto.program(settings) == proto.retained_rule_path(value).read_text()
    assert proto.program({"min_reds": 1}) == canonical

    bad_settings = [
        None,
        {},
        {"min_reds": 1, "extra": 2},
        {"min_reds": True},
        {"min_reds": 2.0},
        {"min_reds": "2"},
        {"min_reds": 0},
        {"min_reds": 4},
    ]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            proto.program(settings)


def test_native_generate_uses_matched_inputs_and_every_scene_identifies_all_settings():
    """Catches setting leakage into inputs and demonstration ambiguity."""
    proto = load_prototype()
    episodes = {
        value: proto.generate(23, {"min_reds": value}, demos=2, queries=4)
        for value in proto.MIN_REDS_VALUES
    }
    serialized_inputs = {}
    for value, episode in episodes.items():
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == proto.retained_rule_path(value).read_text()
        pairs = episode["train"] + episode["test"]
        signatures = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(signatures) == len(set(signatures))
        serialized_inputs[value] = signatures
    assert len({tuple(signatures) for signatures in serialized_inputs.values()}) == 1

    for pair_index in range(6):
        outputs = {
            json.dumps((episodes[value]["train"] + episodes[value]["test"])[pair_index]["output"])
            for value in proto.MIN_REDS_VALUES
        }
        assert len(outputs) == len(proto.MIN_REDS_VALUES)


def test_native_demo_and_query_streams_are_independent_and_prefix_stable():
    """Catches count-dependent resampling that changes unrelated episode pairs."""
    proto = load_prototype()
    settings = {"min_reds": 2}
    small = proto.generate(91, settings, demos=2, queries=1)
    more_demos = proto.generate(91, settings, demos=6, queries=1)
    more_queries = proto.generate(91, settings, demos=2, queries=4)
    assert small["train"] == more_demos["train"][:2]
    assert small["test"] == more_demos["test"]
    assert small["train"] == more_queries["train"]
    assert small["test"] == more_queries["test"][:1]


@pytest.mark.parametrize(
    ("seed", "demos", "queries"),
    [
        (True, 2, 1),
        (-1, 2, 1),
        (0, 1, 1),
        (0, 7, 1),
        (0, True, 1),
        (0, 2.0, 1),
        (0, 2, 0),
        (0, 2, 5),
        (0, 2, True),
        (0, 2, 1.0),
    ],
)
def test_native_generate_rejects_nonexact_or_out_of_range_counts(seed, demos, queries):
    """Catches bool/float coercion and requests outside the declared finite limits."""
    proto = load_prototype()
    with pytest.raises(ValueError):
        proto.generate(seed, {"min_reds": 1}, demos=demos, queries=queries)


def test_python_claim_and_skip_greedy_ablation_have_hand_checked_outputs():
    """Catches a wrong greedy-selection implementation or wrong first-hit precedence."""
    proto = load_prototype()
    grid = [[5, 2, 2, 2, 2], [5, 5, 5, 5, 5], [5, 5, 2, 5, 5]]
    expected = [[5, 2, 2, 2, 2], [5, 7, 4, 7, 5], [5, 7, 2, 7, 5]]
    skipped = [[7, 2, 2, 2, 2], [7, 7, 4, 7, 7], [7, 7, 2, 7, 7]]
    before = copy.deepcopy(grid)
    for value in proto.MIN_REDS_VALUES:
        assert proto.apply_python(grid, value) == expected
        assert proto.skip_greedy_output(grid, value) == skipped
    assert grid == before


def test_native_fourth_query_is_substantive_30_by_30_and_needs_greedy_selection():
    """Catches a token large-grid case or one whose overlap stage is irrelevant."""
    proto = load_prototype()
    episode = proto.generate(5, {"min_reds": 1}, demos=2, queries=4)
    grid = episode["test"][3]["input"]
    assert [len(grid), len(grid[0])] == [30, 30]
    assert sum(value != 0 for row in grid for value in row) >= 180
    trace = proto.candidate_trace(grid, 1)
    assert len(trace["eligible"]) >= 20
    assert trace["rejected"]
    assert trace["selected_gray_overlaps"]
    for value in proto.MIN_REDS_VALUES:
        assert proto.apply_python(grid, value) != proto.skip_greedy_output(grid, value)


def test_native_claim_labels_match_all_three_protected_racket_programs():
    """Catches divergence between Python claim labels and exact Racket semantics."""
    proto = load_prototype()
    for value in proto.MIN_REDS_VALUES:
        episode = proto.generate(17, {"min_reds": value}, demos=2, queries=4)
        pairs = episode["train"] + episode["test"]
        receipt = proto.execute_program(episode["program_solution"], [pair["input"] for pair in pairs])
        assert receipt["test_outputs"] == [pair["output"] for pair in pairs]
