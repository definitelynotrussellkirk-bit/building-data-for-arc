"""Focused tests for the separate selection-mode rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root


TASK_ID = "9bd5d9c04dd8"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load():
    assert PROTOTYPE_PATH.is_file(), "selection-mode prototype is missing"
    spec = importlib.util.spec_from_file_location("selection_mode_prototype", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_program_identity():
    proto = _load()
    assert proto.SELECTION_MODES == ("most", "fewest")
    assert proto.CANONICAL_DEFAULT == "most"
    assert proto.PARAMETER_SPEC["selection_mode"]["chosen_once_per_episode"] is True
    canonical = proto.program_for("most", root=ROOT)
    alternative = proto.program_for("fewest", root=ROOT)
    assert canonical != alternative
    assert "(best-n -1)" in canonical
    assert "(if (> ones best-n)" in canonical
    assert "(best-n 10)" in alternative
    assert "(if (< ones best-n)" in alternative


def test_parameter_choice_is_deterministic_and_both_values_have_seed_support():
    proto = _load()
    observed = {proto.choose_parameters(seed)["selection_mode"] for seed in range(32)}
    assert observed == set(proto.SELECTION_MODES)
    for seed in range(8):
        assert proto.choose_parameters(seed) == proto.choose_parameters(seed)


def test_racket_verified_episode_teaches_selected_setting_and_hides_query_answer():
    proto = _load()
    evidence = proto.materialize_episode(0, difficulty="easy", root=ROOT)
    assert evidence["racket_verified"] is True
    assert len(evidence["public"]["train"]) == proto.N_TRAIN
    assert len(evidence["public"]["test"]) == proto.N_TEST
    assert all("output" not in pair for pair in evidence["public"]["test"])
    assert "parameter" not in evidence["public"]
    assert evidence["demonstration_difference_indices"] == list(range(proto.N_TRAIN))
    assert evidence["query_difference_indices"] == [0]
    assert all(pair["settings_disagree"] for pair in evidence["private"]["train"])
    assert all(pair["settings_disagree"] for pair in evidence["private"]["test"])


@pytest.mark.parametrize("bad", [True, 0, 1.0, "maximum", None])
def test_program_rejects_unsupported_or_coerced_parameter_values(bad):
    proto = _load()
    with pytest.raises(ValueError):
        proto.program_for(bad, root=ROOT)


def test_default_evidence_seeds_cover_both_parameter_settings():
    proto = _load()
    observed = {
        proto.choose_parameters(seed)["selection_mode"]
        for seed in proto.DEFAULT_EVIDENCE_SEEDS
    }
    assert observed == set(proto.SELECTION_MODES)


def _shape(grid):
    return len(grid), len(grid[0])


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_native_api_preserves_exact_default_and_rejects_malformed_settings():
    """Catches a native adapter that reformats the canonical rule or coerces settings."""
    proto = _load()
    canonical = proto.program_for("most", root=ROOT)
    assert proto.program({"selection_mode": "most"}) == canonical
    assert proto.program({"selection_mode": "fewest"}) != canonical
    for bad in (
        {},
        {"selection_mode": "most", "extra": 1},
        {"selection_mode": "maximum"},
        {"selection_mode": 1},
        {"selection_mode": True},
    ):
        with pytest.raises(ValueError):
            proto.program(bad)


def test_native_generation_supports_independent_counts_and_setting_matched_inputs():
    """Catches count coupling or a hidden-setting leak into the input sampler."""
    proto = _load()
    most = proto.generate(23, {"selection_mode": "most"}, demos=2, queries=4)
    fewest = proto.generate(23, {"selection_mode": "fewest"}, demos=2, queries=4)
    assert len(most["train"]) == len(fewest["train"]) == 2
    assert len(most["test"]) == len(fewest["test"]) == 4
    assert _all_inputs(most) == _all_inputs(fewest)
    assert most["program_solution"] == proto.program({"selection_mode": "most"})
    assert fewest["program_solution"] == proto.program({"selection_mode": "fewest"})
    assert all(
        left["output"] != right["output"]
        for left, right in zip(most["train"] + most["test"], fewest["train"] + fewest["test"], strict=True)
    )


def test_native_demo_and_query_streams_are_stable_and_all_inputs_are_distinct():
    """Catches demo-count-dependent queries, query-count-dependent demos, and duplicate scenes."""
    proto = _load()
    setting = {"selection_mode": "most"}
    short_demos = proto.generate(31, setting, demos=2, queries=4)
    long_demos = proto.generate(31, setting, demos=6, queries=4)
    short_queries = proto.generate(31, setting, demos=2, queries=1)
    assert [pair["input"] for pair in short_demos["test"]] == [
        pair["input"] for pair in long_demos["test"]
    ]
    assert [pair["input"] for pair in short_demos["train"]] == [
        pair["input"] for pair in short_queries["train"]
    ]
    inputs = _all_inputs(long_demos)
    assert len(inputs) == len({json.dumps(grid, separators=(",", ":")) for grid in inputs})


def test_native_count_validation_is_strict():
    """Catches bool/coercion acceptance and requests outside the declared 2..6/1..4 limits."""
    proto = _load()
    setting = {"selection_mode": "most"}
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, 4.0)):
        with pytest.raises(ValueError):
            proto.generate(0, setting, demos=demos, queries=queries)
    with pytest.raises(ValueError):
        proto.generate(True, setting, demos=2, queries=4)


def test_four_query_episode_has_substantive_30x30_stress_and_nontrivial_candidates():
    """Catches a nominally large but empty/padded stress scene."""
    proto = _load()
    episode = proto.generate(5, {"selection_mode": "fewest"}, demos=3, queries=4)
    large = [pair["input"] for pair in episode["test"] if _shape(pair["input"]) == (30, 30)]
    assert len(large) == 1
    report = proto.analyze(large[0])
    assert len(report["candidates"]) >= 6
    assert report["nonzero_cells"] >= 70
    assert len({candidate["ones"] for candidate in report["candidates"]}) == len(report["candidates"])


def test_every_scene_rejects_the_first_candidate_bypass_for_both_settings():
    """Catches a sampler where fixed row-major cropping solves the claimed selector stage."""
    proto = _load()
    for mode in proto.SELECTION_MODES:
        episode = proto.generate(17, {"selection_mode": mode}, demos=2, queries=4)
        assert all(
            proto.first_candidate_output(pair["input"]) != pair["output"]
            for pair in episode["train"] + episode["test"]
        )


def test_native_claim_labels_match_racket_for_all_pairs_and_settings():
    """Catches drift between the Python claim generator and exact Racket programs."""
    proto = _load()
    for mode in proto.SELECTION_MODES:
        episode = proto.generate(9, {"selection_mode": mode}, demos=2, queries=4)
        pairs = episode["train"] + episode["test"]
        executed = proto._racket_outputs(proto.program({"selection_mode": mode}), [p["input"] for p in pairs])
        assert executed == [pair["output"] for pair in pairs]
