"""Focused, Racket-backed tests for the proposed frame-color extension."""
from __future__ import annotations

import importlib.util
import json
from functools import lru_cache

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "95524d104174"


@lru_cache(maxsize=1)
def prototype():
    root = find_root(__file__)
    load_selected_generator(TASK_ID, root=root)
    # Task workspaces retain library paths even when selected code is mirrored.
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), "The proposed frame-color prototype must be runnable."
    spec = importlib.util.spec_from_file_location("frame_color_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def test_original_setting_matches_all_selected_canonical_labels(bridge):
    module, root = prototype()
    source = module.instantiate_rule(4, root=root)
    assert source == module.canonical_rule(root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert module.evaluate(bridge, source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("color", [4, 2, 8])
def test_parameter_changes_the_eight_cell_frame_and_preserves_center(bridge, color):
    module, _ = prototype()
    inp = [[0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [3, 3, 1, 3, 3],
           [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]]
    expected = [[0, 0, 1, 0, 0], [0, color, color, color, 0],
                [3, color, 1, color, 3], [0, color, color, color, 0],
                [0, 0, 1, 0, 0]]
    assert module.evaluate(bridge, module.instantiate_rule(color), inp) == expected


@pytest.mark.parametrize("color", [True, False, 4.0, "4", 0, 9])
def test_unsupported_or_noninteger_parameter_values_are_rejected(color):
    module, _ = prototype()
    with pytest.raises(ValueError, match="frame_color"):
        module.instantiate_rule(color)


def test_seed_chooses_one_rule_for_all_demonstrations_and_query(bridge):
    module, _ = prototype()
    for seed, color in enumerate((4, 2, 8)):
        episode = module.make_episode(bridge, seed)
        assert episode["parameters"] == {"frame_color": color}
        assert len(episode["pairs"]) == 4
        for pair in episode["pairs"]:
            new_background_colors = [out for row_in, row_out in
                                     zip(pair["input"], pair["output"])
                                     for before, out in zip(row_in, row_out)
                                     if before == 0 and out != 0]
            assert new_background_colors == [color] * 4


def test_seed_is_repeatable_and_color_override_does_not_change_inputs(bridge):
    module, _ = prototype()
    first = module.make_episode(bridge, 71)
    assert first == module.make_episode(bridge, 71)
    other_color = next(color for color in module.FRAME_COLORS
                       if color != first["parameters"]["frame_color"])
    alternate = module.make_episode(bridge, 71, frame_color=other_color)
    assert [p["input"] for p in first["pairs"]] == [p["input"] for p in alternate["pairs"]]
    assert all(a["output"] != b["output"] for a, b in
               zip(first["pairs"], alternate["pairs"]))


def test_public_projection_contains_only_demonstrations_and_query_input(bridge):
    module, _ = prototype()
    episode = module.make_episode(bridge, 0)
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    public["test"][0]["input"][0][0] = 9
    assert episode["pairs"][3]["input"][0][0] == 0


def test_wrong_parameters_are_refuted_before_every_query_rotation(bridge):
    module, _ = prototype()
    episode = module.make_episode(bridge, 0)
    scores = module.analyze_episode(bridge, episode)
    for score in [scores["production"], *scores["rotations"]]:
        assert score["status"] == "no_ambiguity_found"
        assert len(score["rivals"]) == 2
        for rival in score["rivals"]:
            assert not rival["fits_demonstrations"]
            assert rival["query_differs"]
            assert rival["refuting_demonstration_indices"] == score["demonstration_indices"]
    assert [score["query_index"] for score in scores["rotations"]] == [0, 1, 2, 3]


def test_materialized_files_separate_public_and_private_data(bridge, tmp_path):
    module, _ = prototype()
    out = tmp_path / "evidence"
    report = module.materialize(out, seed=0, bridge=bridge)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "canonical_labels_checked": 4, "canonical_labels_passed": 4,
        "episodes": 3, "demonstrations": 9, "queries": 3,
        "episode_labels": 12, "counterfactual_labels": 24,
        "production_ambiguities": 0, "rotation_ambiguities": 0,
        "query_rotations": 12, "unique_episode_inputs": 12,
    }
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert set(public["test"][0]) == {"input"}
        assert "parameters" in private
        assert "output" in private["pairs"][3]


def test_materialization_refuses_to_overwrite_existing_evidence(bridge, tmp_path):
    module, _ = prototype()
    with pytest.raises(FileExistsError):
        module.materialize(tmp_path, seed=0, bridge=bridge)
