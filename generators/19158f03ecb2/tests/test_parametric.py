"""Prototype-only tests; alternative rules remain outside canonical selection."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/19158f03ecb2/workspace/parametric/prototype.py"


def _load_prototype():
    assert SOURCE.exists(), "mirror-side parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("mirror_side_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def executed(prototype):
    witness = [[1, 2, 3], [4, 5, 6]]
    canonical = canonical_pairs("19158f03ecb2", root=ROOT, labeled_only=True)
    generated = [prototype.sample_input(23, i) for i in range(4)]
    inputs = [witness] + [pair["input"] for pair in canonical] + generated
    labels = {}
    for side in prototype.MIRROR_SIDES:
        receipt = prototype.execute_program(prototype.rule_program(side, root=ROOT), inputs)
        assert receipt["status"] == "pass", receipt
        labels[side] = receipt["test_outputs"]
    return witness, canonical, generated, labels


def test_default_is_byte_exact_canonical_source_and_labels(prototype, executed):
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        source = next(
            row["program_solution"]
            for row in map(json.loads, stream)
            if row.get("task_id") == "19158f03ecb2"
        )
    assert prototype.DEFAULT_MIRROR_SIDE == "right"
    assert prototype.rule_program(root=ROOT) == source

    _, canonical, _, labels = executed
    assert labels["right"][1 : 1 + len(canonical)] == [pair["output"] for pair in canonical]


def test_executed_left_and_right_programs_are_distinct(prototype, executed):
    _, _, _, labels = executed
    assert labels["right"][0] == [[1, 2, 3, 3, 2, 1], [4, 5, 6, 6, 5, 4]]
    assert labels["left"][0] == [[3, 2, 1, 1, 2, 3], [6, 5, 4, 4, 5, 6]]
    assert labels["right"][0] != labels["left"][0]


def test_invalid_parameter_values_are_rejected(prototype):
    for invalid in (None, "up", "RIGHT", 0, 1, True, False, 1.0):
        with pytest.raises(ValueError):
            prototype.rule_program(invalid, root=ROOT)


def test_seeded_hidden_rule_and_inputs_are_reproducible_and_independent(prototype):
    assert {prototype.choose_mirror_side(seed) for seed in range(32)} == {"left", "right"}
    for seed in range(8):
        for pair_index in range(4):
            grid = prototype.sample_input(seed, pair_index)
            assert grid == prototype.sample_input(seed, pair_index)
            assert prototype.validate_input(grid) == []
        # Forcing the episode rule never changes input streams.
        right_inputs = [prototype.sample_input(seed, i) for i in range(4)]
        left_inputs = [prototype.sample_input(seed, i) for i in range(4)]
        assert right_inputs == left_inputs


def test_public_projection_omits_hidden_rule_and_query_answer(prototype, executed):
    _, _, generated, labels = executed
    for side in prototype.MIRROR_SIDES:
        episode = prototype.assemble_episode(
            23,
            side,
            generated,
            labels[side][-4:],
            prototype.rule_program(side, root=ROOT),
        )
        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "mirror_side" not in serialized and "program" not in serialized and "seed" not in serialized
        public["train"][0]["input"][0][0] = 99
        assert episode["train"][0]["input"][0][0] != 99


def test_actual_parameter_rivals_are_refuted_for_every_holdout(prototype, executed):
    _, _, _, labels = executed
    per_setting = {side: labels[side][-4:] for side in prototype.MIRROR_SIDES}
    for selected in prototype.MIRROR_SIDES:
        result = prototype.parameter_teachability(per_setting, selected)
        assert result["production"]["identifiable"]
        assert all(rotation["identifiable"] for rotation in result["rotations"])
        assert result["rivals"][0]["refuting_pair_indices"] == [0, 1, 2, 3]
