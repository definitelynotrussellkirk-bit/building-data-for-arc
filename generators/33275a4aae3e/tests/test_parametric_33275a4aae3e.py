"""Prototype-only tests; canonical generator repair coverage is separate."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "33275a4aae3e"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@pytest.fixture(scope="module")
def prototype():
    spec = importlib.util.spec_from_file_location("parametric_33275a4aae3e", PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(PROTOTYPE_PATH.read_bytes(), str(PROTOTYPE_PATH), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def evaluator(prototype):
    with prototype.RacketEvaluator() as engine:
        assert engine.runtime_identity["backend"] == "racket"
        assert engine.runtime_identity["protected"] is True
        yield engine


def framed_area(area: int) -> list[list[int]]:
    """Broad semantic control, not a claimed generated-network input."""
    grid = [[0] * (area + 4) for _ in range(5)]
    for col in range(1, area + 3):
        grid[1][col] = grid[3][col] = 8
    grid[2][1] = grid[2][area + 2] = 8
    grid[0][0], grid[0][1] = 2, 3
    return grid


def test_bounded_parameter_and_exact_canonical_default(prototype):
    assert prototype.PARAMETER_VALUES == (1, 32, 40)
    assert prototype.DEFAULT_MIN_ENCLOSED_AREA == 1
    assert prototype.materialize_racket() == prototype.CANONICAL_RACKET
    for value in (True, False, 1.0, "32", 0, 16, 41, -1):
        with pytest.raises(ValueError, match="min_enclosed_area"):
            prototype.materialize_racket(value)
        with pytest.raises(ValueError, match="min_enclosed_area"):
            prototype.select_parameter(17, value)


def test_seed_selection_is_deterministic_and_local(prototype):
    random.seed(702)
    before = random.getstate()
    values = [prototype.select_parameter(seed) for seed in range(30)]
    assert values == [prototype.select_parameter(seed) for seed in range(30)]
    assert set(values) == set(prototype.PARAMETER_VALUES)
    assert random.getstate() == before
    assert prototype.select_parameter(17, 40) == 40
    for seed in (True, 1.0, "17"):
        with pytest.raises(ValueError, match="seed"):
            prototype.select_parameter(seed)


@pytest.mark.parametrize("area", [31, 32, 39, 40])
@pytest.mark.parametrize("threshold", [1, 32, 40])
def test_exact_threshold_endpoints_and_foreground_preservation(
    prototype, evaluator, area, threshold
):
    grid = framed_area(area)
    before = copy.deepcopy(grid)
    actual = evaluator.evaluate(prototype.materialize_racket(threshold), grid)
    assert actual == prototype.solve_python(grid, threshold)
    assert all(actual[2][col] == (2 if area >= threshold else 3)
               for col in range(2, area + 2))
    assert actual[0][0:2] == [2, 3]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                assert actual[row][col] == value
    assert actual[4] == [3] * len(grid[0])
    assert grid == before


def test_diagonal_background_contact_is_still_four_connected_enclosure(
    prototype, evaluator
):
    grid = [[0, 8, 0], [8, 0, 8], [0, 8, 0]]
    for threshold in prototype.PARAMETER_VALUES:
        actual = evaluator.evaluate(prototype.materialize_racket(threshold), grid)
        assert actual == prototype.solve_python(grid, threshold)
        assert actual[1][1] == (2 if threshold == 1 else 3)
        assert actual[0][0] == 3


def test_default_racket_matches_all_canonical_positive_controls(prototype, evaluator):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        actual = evaluator.evaluate(prototype.materialize_racket(), pair["input"])
        assert actual == pair["output"]
        assert actual == prototype.solve_python(pair["input"])


@pytest.mark.parametrize("threshold", [1, 32, 40])
def test_every_selected_scene_profile_with_every_parameter(prototype, evaluator, threshold):
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    for profile in generator.SCENE_PROFILES:
        grid = generator.generate(17, 0, scene_profile=profile)
        assert generator.self_check(grid) == []
        actual = evaluator.evaluate(prototype.materialize_racket(threshold), grid)
        assert actual == prototype.solve_python(grid, threshold), (profile, threshold)
        if threshold == 1:
            assert actual == generator.solve_python(grid), profile


@pytest.fixture(scope="module")
def explicit_episodes(prototype, evaluator):
    return {
        threshold: prototype.build_episode(
            17, min_enclosed_area=threshold, evaluator=evaluator, root=ROOT
        )
        for threshold in prototype.PARAMETER_VALUES
    }


def test_complete_episodes_fix_the_parameter_and_distinguish_every_rival(
    prototype, explicit_episodes
):
    generator, _, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    inputs = []
    for threshold, episode in explicit_episodes.items():
        assert episode["parameters"] == {"min_enclosed_area": threshold}
        assert episode["generator_sha256"] == source_hash
        assert len(episode["pairs"]) == 4
        assert [pair["split"] for pair in episode["pairs"]] == [
            "train", "train", "train", "test"
        ]
        assert episode["rival_check"]["all_declared_rivals_refuted"] is True
        assert len(episode["rival_check"]["rivals"]) == 2
        assert all(row["status"] == "refuted_by_demonstration"
                   for row in episode["rival_check"]["rivals"])
        assert len(episode["query_rotations"]) == 4
        assert all(row["all_declared_rivals_refuted"]
                   for row in episode["query_rotations"])
        current_inputs = []
        for pair in episode["pairs"]:
            assert not generator.self_check(pair["input"])
            assert pair["output"] == prototype.solve_python(pair["input"], threshold)
            assert pair["input_sha256"] == prototype.hash_json(pair["input"])
            assert pair["output_sha256"] == prototype.hash_json(pair["output"])
            assert pair["input"] == generator.generate(17, pair["sample_index"])
            current_inputs.append(pair["input"])
        inputs.append(current_inputs)
    assert inputs[0] == inputs[1] == inputs[2]
    for pair_index in (0, 2):
        outputs = {
            prototype.hash_json(episode["pairs"][pair_index]["output"])
            for episode in explicit_episodes.values()
        }
        assert len(outputs) == 3


def test_balanced_threshold_and_connectivity_support_survives_every_rotation(
    prototype, explicit_episodes
):
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    roles = ["threshold_witness", "connectivity_witness"] * 2
    for threshold, episode in explicit_episodes.items():
        assert episode["sampling"]["roles"] == roles
        for index in (1, 3):
            pair = episode["pairs"][index]
            observed = generator.observe_overrides(pair["input"])["scene_profile"]
            assert observed in generator.CONNECTIVITY_PROFILES
            assert generator.SEMANTIC_WITNESSES["nonrectangular_enclosure"](pair["input"])
            assert generator.SEMANTIC_WITNESSES["diagonal_seal"](pair["input"])
        for rotation in episode["query_rotations"]:
            assert {roles[index] for index in rotation["demonstration_indices"]} == set(roles)
            assert rotation["all_declared_rivals_refuted"]
        semantic = {row["name"]: row for row in episode["semantic_rival_check"]["rivals"]}
        assert semantic["complete_rectangle_fill_at_threshold"]["status"] == "refuted_by_demonstration"
        expected_eight = "refuted_by_demonstration" if threshold == 1 else "survived_all"
        assert semantic["eight_connected_enclosure_at_threshold"]["status"] == expected_eight
        assert all(not row["ambiguous"] for row in episode["semantic_query_rotations"])


def test_public_challenge_omits_private_fields_and_is_fresh(prototype, explicit_episodes):
    episode = explicit_episodes[32]
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    original = copy.deepcopy(episode)
    challenge["train"][0]["input"][0][0] = 9
    assert episode == original


def test_episode_is_reproducible_and_seed_selected_parameter_is_fixed(
    prototype, evaluator, explicit_episodes
):
    repeated = prototype.build_episode(
        17, min_enclosed_area=32, evaluator=evaluator, root=ROOT
    )
    assert repeated == explicit_episodes[32]
    automatic = prototype.build_episode(17, evaluator=evaluator, root=ROOT)
    selected = prototype.select_parameter(17)
    assert automatic["parameters"] == {"min_enclosed_area": selected}
    assert automatic["pairs"] == explicit_episodes[selected]["pairs"]


def test_bounded_sampling_fails_visibly(prototype, evaluator):
    with pytest.raises(prototype.EpisodeSelectionError) as failure:
        prototype.build_episode(17, evaluator=evaluator, root=ROOT, max_draws=1)
    assert failure.value.receipt["status"] == "selection_budget_exhausted"
    assert failure.value.receipt["attempted_candidates"] == 1
    assert failure.value.receipt["accepted_pairs"] < 4


def test_export_records_programs_sources_labels_and_opaque_public_files(
    prototype, evaluator, tmp_path
):
    destination = tmp_path / "evidence"
    report = prototype.export_evidence(destination, seeds=[17], root=ROOT,
                                       evaluator=evaluator)
    assert report["status"] == "pass"
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["parameter_rival_checks"] == 6
    assert report["counts"]["query_rotations"] == 12
    assert report["counts"]["ambiguous_episodes"] == 0
    assert report["counts"]["ambiguous_rotations"] == 0
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    assert report["counts"]["profile_parameter_checks"] == 3 * len(generator.SCENE_PROFILES)
    assert report["counts"]["profile_parameter_checks_passed"] == 3 * len(generator.SCENE_PROFILES)
    for row in report["sources"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    retained = json.loads((destination / "private_evidence.json").read_text())
    assert retained == report
    public = sorted((destination / "public").glob("*.challenge.json"))
    assert [path.name for path in public] == [
        "episode-0000.challenge.json", "episode-0001.challenge.json",
        "episode-0002.challenge.json",
    ]
    for threshold in prototype.PARAMETER_VALUES:
        program_path = destination / "programs" / f"min-area-{threshold}.rkt"
        assert program_path.read_text() == prototype.materialize_racket(threshold)
    with pytest.raises(FileExistsError):
        prototype.export_evidence(destination, seeds=[17], root=ROOT,
                                  evaluator=evaluator)


def test_export_claims_directory_before_runtime_startup(prototype, monkeypatch, tmp_path):
    def unavailable():
        raise RuntimeError("deliberate unavailable Racket control")

    monkeypatch.setattr(prototype, "RacketEvaluator", unavailable)
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "failure.json"
    sentinel.write_text("prior evidence\n")
    with pytest.raises(FileExistsError):
        prototype.export_evidence(existing, seeds=[17], root=ROOT)
    assert sentinel.read_text() == "prior evidence\n"

    fresh = tmp_path / "fresh"
    with pytest.raises(RuntimeError, match="unavailable Racket"):
        prototype.export_evidence(fresh, seeds=[17], root=ROOT)
    partial = json.loads((fresh / "private_evidence.json").read_text())
    assert partial["status"] == "fail"
    assert partial["sources"]
    assert partial["episodes"] == []
    assert (fresh / "failure.json").is_file()


def test_later_failure_preserves_completed_episode_provenance(
    prototype, evaluator, monkeypatch, tmp_path
):
    original = prototype.build_episode
    calls = []

    def fail_second(*args, **kwargs):
        calls.append(kwargs.get("min_enclosed_area"))
        if len(calls) == 2:
            raise prototype.EpisodeSelectionError({"status": "deliberate_later_failure"})
        return original(*args, **kwargs)

    monkeypatch.setattr(prototype, "build_episode", fail_second)
    destination = tmp_path / "partial"
    with pytest.raises(prototype.EpisodeSelectionError):
        prototype.export_evidence(destination, seeds=[17], root=ROOT, evaluator=evaluator)
    partial = json.loads((destination / "private_evidence.json").read_text())
    assert partial["status"] == "fail"
    assert len(partial["episodes"]) == 1
    assert partial["episodes"][0]["parameters"] == {"min_enclosed_area": 1}
    assert partial["episodes"][0]["seed"] == 17
    assert partial["sources"]
    assert partial["runtime"]["backend"] == "racket"
    assert len(partial["programs"]) == 3
    assert (destination / "public/episode-0000.challenge.json").is_file()
    assert (destination / "failure.json").is_file()
