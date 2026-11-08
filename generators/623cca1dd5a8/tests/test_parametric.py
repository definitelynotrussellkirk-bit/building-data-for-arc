"""Prototype-only checks; these do not approve an alternative canonical rule."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/623cca1dd5a8/workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("bbox_thickness_prototype", SOURCE)
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


@pytest.fixture(scope="module")
def executed():
    # Hard-coded cross has a 5x5 bbox. Its center must be erased for both rules.
    cross = [[0, 0, 4, 0, 0], [0, 0, 4, 0, 0], [4, 4, 4, 4, 4],
             [0, 0, 4, 0, 0], [0, 0, 4, 0, 0]]
    narrow = [[7, 0], [7, 0], [7, 7]]
    canon = canonical_pairs("623cca1dd5a8", root=ROOT, labeled_only=True)
    generated = [PROTOTYPE.sample_input(19, i) for i in range(4)]
    inputs = [cross, narrow] + [p["input"] for p in canon] + generated
    labels = {}
    for thickness in PROTOTYPE.THICKNESSES:
        receipt = PROTOTYPE.execute_program(PROTOTYPE.rule_program(thickness, root=ROOT), inputs)
        assert receipt["status"] == "pass", receipt
        labels[thickness] = receipt["test_outputs"]
    return canon, inputs, labels


def test_default_is_exact_canonical_source_and_labels(executed):
    with canonical_path(ROOT).open() as stream:
        source = next(json.loads(line)["program_solution"] for line in stream
                      if json.loads(line).get("task_id") == "623cca1dd5a8")
    assert PROTOTYPE.rule_program(root=ROOT) == source
    canon, _, labels = executed
    assert labels[1][2:2 + len(canon)] == [p["output"] for p in canon]


def test_executed_band_width_and_narrow_coincidence(executed):
    _, _, labels = executed
    assert labels[1][0] == [[4, 4, 4, 4, 4], [4, 0, 0, 0, 4], [4, 0, 0, 0, 4],
                            [4, 0, 0, 0, 4], [4, 4, 4, 4, 4]]
    assert labels[2][0] == [[4, 4, 4, 4, 4], [4, 4, 4, 4, 4], [4, 4, 0, 4, 4],
                            [4, 4, 4, 4, 4], [4, 4, 4, 4, 4]]
    assert labels[1][1] == labels[2][1] == [[7, 7], [7, 7], [7, 7]]


def test_invalid_parameters_are_rejected():
    for invalid in (0, 3, -1, True, False, 1.0, "1", None):
        with pytest.raises(ValueError):
            PROTOTYPE.rule_program(invalid, root=ROOT)


def test_seeded_rule_and_inputs_are_reproducible_and_independent():
    assert {PROTOTYPE.choose_thickness(seed) for seed in range(24)} == {1, 2}
    for seed in range(8):
        assert PROTOTYPE.choose_thickness(seed) == PROTOTYPE.choose_thickness(seed)
        for pair_index in range(4):
            grid = PROTOTYPE.sample_input(seed, pair_index)
            assert grid == PROTOTYPE.sample_input(seed, pair_index)
            assert not PROTOTYPE.validate_input(grid)
        assert PROTOTYPE.choose_thickness(seed, 1) == 1
        assert PROTOTYPE.choose_thickness(seed, 2) == 2


def test_public_projection_omits_all_private_data_and_does_not_alias(executed):
    _, inputs, labels = executed
    for thickness in (1, 2):
        episode = PROTOTYPE.assemble_episode(19, thickness, inputs[-4:], labels[thickness][-4:],
                                             PROTOTYPE.rule_program(thickness, root=ROOT))
        public = PROTOTYPE.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(p) == {"input", "output"} for p in public["train"])
        assert all(set(p) == {"input"} for p in public["test"])
        public["train"][0]["input"][0][0] = 99
        assert episode["train"][0]["input"][0][0] != 99


def test_actual_episode_parameter_rivals_and_every_holdout(executed):
    _, _, labels = executed
    per_setting = {t: labels[t][-4:] for t in (1, 2)}
    for thickness in (1, 2):
        result = PROTOTYPE.parameter_teachability(per_setting, thickness)
        assert result["production"]["identifiable"]
        assert all(r["identifiable"] for r in result["rotations"])
        assert result["rivals"][0]["refuting_pair_indices"] == [0, 1, 2, 3]


def test_narrow_only_episode_is_honestly_ambiguous(executed):
    _, _, labels = executed
    per_setting = {t: [labels[t][1]] * 4 for t in (1, 2)}
    result = PROTOTYPE.parameter_teachability(per_setting, 1)
    assert not result["production"]["identifiable"]
    assert not any(r["identifiable"] for r in result["rotations"])
    assert result["production"]["surviving_parameter_rivals"] == [2]
