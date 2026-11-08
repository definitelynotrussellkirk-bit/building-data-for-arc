"""Focused tests for the proposed, non-production path-mode prototype."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "db63430eeffa"
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
)


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"].strip()
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _predictions(proto, inputs):
    return {
        mode: [proto.python_mirror(grid, mode) for grid in inputs]
        for mode in proto.ALLOWED_PATH_MODES
    }


def test_parameter_contract_is_small_and_default_program_is_exactly_canonical():
    proto = _prototype()
    assert proto.ALLOWED_PATH_MODES == (
        "both",
        "diagonal_first",
        "straight_first",
    )
    assert proto.DEFAULT_PATH_MODE == "both"
    assert proto.TRAIN_COUNT == 3
    assert proto.QUERY_COUNT == 4
    assert proto.PAIR_COUNT == 7
    assert proto.rule_source("both").strip() == _canonical_source()
    assert len({proto.rule_source(mode) for mode in proto.ALLOWED_PATH_MODES}) == 3


@pytest.mark.parametrize(
    "mode",
    [None, True, False, 0, 1.0, "", "diagonal", "both ", [], {}],
)
def test_unsupported_path_mode_fails_closed(mode):
    proto = _prototype()
    with pytest.raises(ValueError, match="path_mode"):
        proto.rule_source(mode)
    with pytest.raises(ValueError, match="path_mode"):
        proto.python_mirror(proto.sample_inputs(0)[0], mode)


@pytest.mark.parametrize("seed", [None, True, False, 1.0, 1.75, "1"])
def test_seeded_entry_points_require_literal_integers(seed):
    proto = _prototype()
    with pytest.raises(TypeError, match="seed"):
        proto.path_mode_for_seed(seed)
    with pytest.raises(TypeError, match="seed"):
        proto.sample_inputs(seed)
    with pytest.raises(TypeError, match="base_seed"):
        proto.select_seeds(seed)


def test_episode_rule_is_seeded_once_and_inputs_are_rule_independent():
    proto = _prototype()
    for seed in range(20261023, 20261033):
        first = proto.sample_episode(seed)
        second = proto.sample_episode(seed)
        assert first == second
        assert first["parameters"] == {
            "path_mode": proto.path_mode_for_seed(seed)
        }
        assert first["inputs"] == proto.sample_inputs(seed)
        assert first["train_count"] == 3
        assert first["query_count"] == 4
        assert len(first["inputs"]) == 7


def test_every_input_is_distinct_lawful_and_separates_all_three_modes():
    proto = _prototype()
    for seed in proto.select_seeds(20261023)["seeds"]:
        inputs = proto.sample_inputs(seed)
        assert len(inputs) == 7
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 7
        for grid in inputs:
            palette = {cell for row in grid for cell in row}
            endpoints = [
                (row, col)
                for row, values in enumerate(grid)
                for col, cell in enumerate(values)
                if cell == 8
            ]
            assert palette <= {0, 8}
            assert len(endpoints) == 2
            row_gap = abs(endpoints[1][0] - endpoints[0][0])
            col_gap = abs(endpoints[1][1] - endpoints[0][1])
            assert row_gap >= 2 and col_gap >= 2 and row_gap != col_gap
            outputs = [proto.python_mirror(grid, mode) for mode in proto.ALLOWED_PATH_MODES]
            assert len({json.dumps(output) for output in outputs}) == 3


def test_seed_selection_retains_exactly_one_episode_per_setting():
    proto = _prototype()
    selection = proto.select_seeds(20261023)
    assert set(selection["by_path_mode"]) == set(proto.ALLOWED_PATH_MODES)
    assert len(selection["seeds"]) == len(proto.ALLOWED_PATH_MODES)
    assert len(set(selection["seeds"])) == len(proto.ALLOWED_PATH_MODES)
    assert [proto.path_mode_for_seed(seed) for seed in selection["seeds"]] == list(
        proto.ALLOWED_PATH_MODES
    )


def test_three_demonstrations_refute_both_rivals_and_all_four_queries_disagree():
    proto = _prototype()
    for seed in proto.select_seeds(20261023)["seeds"]:
        episode = proto.sample_episode(seed)
        chosen = episode["parameters"]["path_mode"]
        scored = proto.score_episode(_predictions(proto, episode["inputs"]), chosen)
        assert scored["demonstration_pair_indices"] == [0, 1, 2]
        assert scored["query_pair_indices"] == [3, 4, 5, 6]
        assert len(scored["rivals"]) == 2
        for rival in scored["rivals"]:
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["demonstration_mismatches"] == [0, 1, 2]
            assert rival["query_disagreements"] == [3, 4, 5, 6]
            assert rival["all_queries_disagree"] is True


def test_public_challenge_has_three_demos_four_queries_and_no_private_metadata():
    proto = _prototype()
    episode = proto.sample_episode(proto.select_seeds(20261023)["seeds"][0])
    mode = episode["parameters"]["path_mode"]
    pairs = [
        {"input": grid, "output": proto.python_mirror(grid, mode)}
        for grid in episode["inputs"]
    ]
    challenge = proto.public_challenge(pairs)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert proto.public_id(challenge) == public_challenge_id(challenge)
    assert proto.public_bytes(challenge) == public_challenge_bytes(challenge)

    serialized = proto.public_bytes(challenge).decode("utf-8")
    for private_token in (
        "path_mode",
        "both",
        "diagonal_first",
        "straight_first",
        "rule!",
        "seed",
        "parameters",
    ):
        assert private_token not in serialized
