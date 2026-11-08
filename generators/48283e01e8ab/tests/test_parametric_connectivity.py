"""Behavioral checks for the unapproved connectivity prototype, not production."""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "48283e01e8ab"
ROOT = find_root(__file__)


def _prototype():
    source = ROOT / "generators" / TASK_ID / "workspace/parametric/connectivity.py"
    spec = importlib.util.spec_from_file_location("connectivity_prototype", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagonal_contacts_change_component_membership():
    prototype = _prototype()
    grid = [[6, 6, 7], [7, 7, 6]]
    before = copy.deepcopy(grid)
    with prototype.RacketLabeler(root=ROOT) as labeler:
        assert labeler.apply(grid, 4) == [[9, 9, 7], [7, 7, 6]]
        assert labeler.apply(grid, 8) == [[4, 4, 7], [7, 7, 4]]
    assert grid == before


def test_default_racket_matches_every_usable_canonical_label():
    prototype = _prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    with prototype.RacketLabeler(root=ROOT) as labeler:
        for pair in pairs:
            assert labeler.apply(pair["input"]) == pair["output"]


def test_size_table_axis_aligned_straightness_and_foreign_preservation():
    prototype = _prototype()
    with prototype.RacketLabeler(root=ROOT) as labeler:
        for connectivity in prototype.CONNECTIVITY_VALUES:
            for size, color in ((1, 6), (2, 9), (3, 2), (4, 8), (5, 3), (6, 5), (7, 6), (8, 6)):
                grid = [[1] + [6] * size + [8], [9] + [7] * size + [0]]
                expected = [[1] + [color] * size + [8], [9] + [7] * size + [0]]
                assert labeler.apply(grid, connectivity) == expected
        diagonal = [[6, 7, 7], [7, 6, 7], [7, 7, 6]]
        assert labeler.apply(diagonal, 8) == [[4, 7, 7], [7, 4, 7], [7, 7, 4]]
        assert labeler.apply(diagonal, 4) == diagonal
        bend = [[6, 6], [7, 6]]
        assert labeler.apply(bend, 4) == labeler.apply(bend, 8) == [[4, 4], [7, 4]]


def test_every_emitted_scene_is_canonical_lawful_and_separates_the_settings():
    prototype = _prototype()
    canonical, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    with prototype.RacketLabeler(root=ROOT) as labeler:
        for band in prototype.DIFFICULTIES:
            for index, profile in enumerate(prototype.SCENE_PROFILES):
                grid = prototype.make_input(37, index, profile=profile, difficulty=band)
                assert canonical.self_check(grid, difficulty=band) == []
                assert labeler.apply(grid, 4) != labeler.apply(grid, 8)


def test_episode_parameter_is_fixed_and_all_holdouts_identify_it():
    prototype = _prototype()
    with prototype.RacketLabeler(root=ROOT) as labeler:
        episodes = [prototype.generate_episode(83, connectivity=value, labeler=labeler)
                    for value in prototype.CONNECTIVITY_VALUES]
        left_inputs = [pair["input"] for pair in episodes[0]["pairs"]]
        right_inputs = [pair["input"] for pair in episodes[1]["pairs"]]
        assert left_inputs == right_inputs
        for episode, connectivity in zip(episodes, prototype.CONNECTIVITY_VALUES):
            assert episode["parameters"] == {"connectivity": connectivity}
            assert len(episode["pairs"]) == 4
            assert episode["production_query_index"] == 3
            for pair in episode["pairs"]:
                assert pair["output"] == labeler.apply(pair["input"], connectivity)
            evidence = prototype.parameter_identifiability(episode, labeler=labeler)
            assert evidence["production"]["status"] == "identified"
            assert len(evidence["holdouts"]) == 4
            for holdout in evidence["holdouts"]:
                assert holdout["status"] == "identified"
                assert holdout["surviving_settings"] == [connectivity]
                assert holdout["rivals"][0]["refuting_demo_indices"]


def test_parameter_check_reports_ambiguous_demonstrations():
    prototype = _prototype()
    with prototype.RacketLabeler(root=ROOT) as labeler:
        inputs = [[[6, 6, 7]], [[7, 6, 6]], [[6, 6, 7], [7, 7, 6]]]
        episode = {"parameters": {"connectivity": 4}, "production_query_index": 2,
                   "pairs": [{"input": grid, "output": labeler.apply(grid, 4)} for grid in inputs]}
        evidence = prototype.parameter_identifiability(episode, labeler=labeler)
        assert evidence["production"]["status"] == "ambiguous"
        assert evidence["production"]["surviving_settings"] == [4, 8]
        assert evidence["production"]["rivals"][0]["query_differs"] is True
        assert evidence["production"]["rivals"][0]["refuting_demo_indices"] == []


def test_public_challenge_contains_only_visible_grids():
    prototype = _prototype()
    with prototype.RacketLabeler(root=ROOT) as labeler:
        episode = prototype.generate_episode(101, connectivity=8, labeler=labeler)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert public["test"][0]["input"] == episode["pairs"][3]["input"]
    public["train"][0]["input"][0][0] = -1
    assert episode["pairs"][0]["input"][0][0] != -1


def test_seeded_parameter_selection_and_inputs_are_deterministic_and_local():
    prototype = _prototype()
    random.seed(712)
    before = random.getstate()
    selections = [prototype.choose_connectivity(seed) for seed in range(20)]
    assert set(selections) == {4, 8}
    assert selections == [prototype.choose_connectivity(seed) for seed in range(20)]
    first = prototype.make_input(3, 1, profile="all_classes_contact")
    assert first == prototype.make_input(3, 1, profile="all_classes_contact")
    assert first is not prototype.make_input(3, 1, profile="all_classes_contact")
    assert before == random.getstate()


@pytest.mark.parametrize("invalid", [True, False, 0, 3, 6, "4", 4.0, None])
def test_parameter_domain_is_bounded_integers(invalid):
    prototype = _prototype()
    with pytest.raises(ValueError):
        prototype.materialize_program(invalid, root=ROOT)


@pytest.mark.parametrize("seeds,difficulties", [([], ["easy"]), ([0], [])])
def test_empty_evidence_population_is_rejected(tmp_path, seeds, difficulties):
    prototype = _prototype()
    with pytest.raises(ValueError, match="nonempty"):
        prototype.run_evidence(tmp_path / "empty", seeds=seeds, difficulties=difficulties)
