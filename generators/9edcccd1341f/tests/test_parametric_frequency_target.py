"""Prototype-only tests for the proposed episode-level frequency target."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9edcccd1341f"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.fixture(scope="module")
def prototype():
    if not PROTOTYPE.is_file():
        pytest.skip("prototype missing; reported by test_prototype_present")
    spec = importlib.util.spec_from_file_location(
        "parametric_9edcccd1341f", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    border = grid[1][0]
    return [
        (row, col, grid[row][col])
        for row in range(2, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] not in (0, border)
    ]


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        max(row for row, _ in cells),
        min(col for _, col in cells),
        max(col for _, col in cells),
    )


def test_prototype_present() -> None:
    assert PROTOTYPE.is_file(), "frequency_target prototype has not been implemented"


def test_default_preserves_exact_canonical_racket(prototype) -> None:
    assert prototype.DEFAULT_FREQUENCY_TARGET == "most_frequent"
    assert prototype.materialize_rule() == prototype.canonical_rule()
    assert prototype.rule_hash(prototype.materialize_rule())[:12] == "d1ac07400a65"


def test_canonical_default_parity_all_pairs(prototype) -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    actual = prototype.execute_rule(
        prototype.materialize_rule(), [pair["input"] for pair in pairs]
    )
    assert actual == [pair["output"] for pair in pairs]
    assert len(pairs) == 10


def test_prototype_inputs_are_lawful_and_have_unique_extrema(prototype) -> None:
    inputs, sample_indices = prototype.build_inputs(
        173, difficulty="medium", start=0, count=5
    )
    assert len(inputs) == len(sample_indices) == 5
    assert sample_indices == sorted(sample_indices)
    for grid in inputs:
        assert GEN.self_check(grid) == []
        cells = _candidate_cells(grid)
        counts = Counter(value for _, _, value in cells)
        assert len(counts) == 2
        assert len(set(counts.values())) == 2
        for color in counts:
            coords = [(row, col) for row, col, value in cells if value == color]
            r1, r2, c1, c2 = _bbox(coords)
            assert r1 < r2 and c1 < c2


def test_same_inputs_distinguish_both_settings(prototype) -> None:
    inputs, _ = prototype.build_inputs(173, difficulty="medium", start=0, count=5)
    outputs = {
        setting: prototype.execute_rule(prototype.materialize_rule(setting), inputs)
        for setting in prototype.FREQUENCY_TARGETS
    }
    assert all(
        most != least
        for most, least in zip(
            outputs["most_frequent"], outputs["least_frequent"]
        )
    )


@pytest.mark.parametrize("setting", ["most_frequent", "least_frequent"])
def test_complete_episode_labels_execute_and_reject_rival(prototype, setting) -> None:
    episode = prototype.build_episode(173, frequency_target=setting)
    challenge = episode["challenge"]
    private = episode["private"]
    assert len(challenge["train"]) == 4
    assert len(challenge["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert set(challenge["test"][0]) == {"input"}
    assert private["parameters"] == {"frequency_target": setting}
    assert private["rival_setting_check"]["rejected_by_demo_indices"] == [0, 1, 2, 3]
    assert private["rival_setting_check"]["query_disagrees"] is True
    inputs = [pair["input"] for pair in challenge["train"] + challenge["test"]]
    labels = [pair["output"] for pair in challenge["train"]] + private["query_outputs"]
    assert labels == prototype.execute_rule(private["racket_text"], inputs)
    public_text = json.dumps(challenge, sort_keys=True)
    assert "frequency_target" not in public_text
    assert "most_frequent" not in public_text
    assert "least_frequent" not in public_text
    assert episode == prototype.build_episode(173, frequency_target=setting)


def test_settings_share_identical_generated_inputs(prototype) -> None:
    first = prototype.build_episode(99, frequency_target="most_frequent")
    second = prototype.build_episode(99, frequency_target="least_frequent")
    for split in ("train", "test"):
        assert [pair["input"] for pair in first["challenge"][split]] == [
            pair["input"] for pair in second["challenge"][split]
        ]
    assert first["private"]["sampling"]["sample_indices"] == second["private"][
        "sampling"
    ]["sample_indices"]


def test_seeded_selection_is_episode_fixed_and_replays(prototype) -> None:
    selected = {prototype.select_frequency_target(seed) for seed in range(32)}
    assert selected == set(prototype.FREQUENCY_TARGETS)
    episode = prototype.build_episode(47, frequency_target=None)
    assert episode["private"]["parameters"]["frequency_target"] == (
        prototype.select_frequency_target(47)
    )
    assert episode == prototype.build_episode(47, frequency_target=None)


@pytest.mark.parametrize("bad", ["median", "", 1, True, None])
def test_invalid_explicit_parameter_rejected(prototype, bad) -> None:
    with pytest.raises(ValueError, match="frequency_target"):
        prototype.materialize_rule(bad)


def test_evidence_refuses_existing_directory(prototype, tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        prototype.write_evidence(tmp_path, seed=173)
    assert list(tmp_path.iterdir()) == []
