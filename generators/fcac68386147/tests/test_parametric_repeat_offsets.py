"""Focused tests for the proposed, non-production repeat-offset prototype."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "fcac68386147"
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "repeat-offset prototype has not been implemented"
    spec = spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _settings(proto):
    return tuple(
        (row_offset, column_offset)
        for row_offset in proto.ALLOWED_REPEAT_OFFSETS
        for column_offset in proto.ALLOWED_REPEAT_OFFSETS
    )


def test_default_rule_is_exact_canonical_and_all_settings_are_distinct():
    proto = _prototype()
    assert proto.ALLOWED_REPEAT_OFFSETS == (0, 1)
    assert proto.DEFAULT_SETTING == (0, 0)
    sources = {
        setting: proto.rule_source(*setting)
        for setting in _settings(proto)
    }
    assert sources[proto.DEFAULT_SETTING] == _canonical_source()
    assert len(set(sources.values())) == 4


@pytest.mark.parametrize("bad", [None, True, False, -1, 2, 1.0, "1", [], {}])
def test_rule_offsets_fail_closed(bad):
    proto = _prototype()
    with pytest.raises(ValueError, match="repeat_offset"):
        proto.rule_source(bad, 0)
    with pytest.raises(ValueError, match="repeat_offset"):
        proto.rule_source(0, bad)


def test_rule_is_selected_once_and_inputs_ignore_the_selected_setting():
    proto = _prototype()
    seed = 20261023
    settings = _settings(proto)
    episodes = [
        proto.sample_episode(seed, demos=3, queries=4, setting=setting)
        for setting in settings
    ]
    assert {tuple(ep["parameters"].values()) for ep in episodes} == set(settings)
    assert all(ep["inputs"] == episodes[0]["inputs"] for ep in episodes[1:])
    assert all(ep["demo_count"] == 3 and ep["query_count"] == 4 for ep in episodes)
    fingerprints = {
        json.dumps(grid, sort_keys=True, separators=(",", ":"))
        for grid in episodes[0]["inputs"]
    }
    assert len(episodes[0]["inputs"]) == 7
    assert len(fingerprints) == 7

    seeded = proto.sample_episode(seed, demos=2, queries=5)
    assert seeded["parameters"] == dict(zip(
        ("row_repeat_offset", "column_repeat_offset"),
        proto.setting_for_seed(seed),
        strict=True,
    ))
    assert seeded["demo_count"] == 2
    assert seeded["query_count"] == 5
    assert len(seeded["inputs"]) == 7


@pytest.mark.parametrize(
    "demos,queries",
    [(0, 4), (3, 0), (9, 1), (1, 9), (8, 9), (True, 4), (3, 4.0)],
)
def test_count_limits_fail_closed(demos, queries):
    proto = _prototype()
    with pytest.raises(ValueError, match="demos|queries|total"):
        proto.sample_episode(0, demos=demos, queries=queries)


def test_every_pair_distinguishes_all_four_settings_and_demos_refute_rivals():
    proto = _prototype()
    episode = proto.sample_episode(17, demos=3, queries=4, setting=(1, 0))
    settings = _settings(proto)
    predictions = {
        setting: [
            proto.python_mirror(grid, *setting)
            for grid in episode["inputs"]
        ]
        for setting in settings
    }
    for pair_index in range(len(episode["inputs"])):
        outputs = {
            json.dumps(predictions[setting][pair_index], separators=(",", ":"))
            for setting in settings
        }
        assert len(outputs) == 4

    score = proto.score_identifiability(
        predictions,
        chosen_setting=(1, 0),
        demo_count=3,
        query_count=4,
    )
    assert score["chosen_setting"] == {
        "row_repeat_offset": 1,
        "column_repeat_offset": 0,
    }
    assert score["all_declared_rivals_refuted"] is True
    assert score["all_queries_distinguish_every_rival"] is True
    assert len(score["rivals"]) == 3
    assert all(row["status"] == "refuted_by_demonstrations" for row in score["rivals"])
    assert all(row["query_disagreements"] == [0, 1, 2, 3] for row in score["rivals"])


def test_python_mirror_preserves_tile_and_changes_only_repeat_counts():
    proto = _prototype()
    grid = [[1, 0, 2], [0, 3, 0], [2, 0, 1]]
    for row_offset, column_offset in _settings(proto):
        output = proto.python_mirror(grid, row_offset, column_offset)
        assert len(output) == 3 * (3 + row_offset)
        assert len(output[0]) == 3 * (3 + column_offset)
        for row in range(len(output)):
            for column in range(len(output[0])):
                assert output[row][column] == grid[row % 3][column % 3]


def test_public_projection_has_four_unlabeled_queries_and_public_only_identity():
    proto = _prototype()
    episode = proto.sample_episode(29, demos=3, queries=4, setting=(1, 1))
    pairs = [
        {
            "input": grid,
            "output": proto.python_mirror(grid, 1, 1),
            "private": {"parameters": episode["parameters"], "program": "secret"},
        }
        for grid in episode["inputs"]
    ]
    challenge = proto.public_challenge(pairs, demos=3, queries=4)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 4
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    visible = public_challenge_bytes(challenge)
    serialized = visible.decode("utf-8")
    assert "row_repeat_offset" not in serialized
    assert "column_repeat_offset" not in serialized
    assert "rule!" not in serialized
    assert "secret" not in serialized
    assert proto.public_identity(challenge) == {
        "sha256": public_challenge_id(challenge),
        "bytes": len(visible),
    }


def test_seed_selection_covers_each_setting_once():
    proto = _prototype()
    selected = proto.select_seeds(20261023)
    assert selected["base_seed"] == 20261023
    assert len(selected["seeds"]) == 4
    assert {
        proto.setting_for_seed(seed)
        for seed in selected["seeds"]
    } == set(_settings(proto))
    assert set(selected["by_setting"]) == {
        "0,0", "0,1", "1,0", "1,1"
    }


def test_evidence_writer_separates_public_and_private_data(tmp_path):
    proto = _prototype()
    program_settings = {
        proto.rule_source(*setting): setting
        for setting in _settings(proto)
    }

    def deterministic_verifier(task, program, *, racket_path=None):
        del racket_path
        setting = program_settings[program]
        return {
            "status": "pass",
            "backend": "test-double",
            "test_outputs": [
                proto.python_mirror(pair["input"], *setting)
                for pair in task["test"]
            ],
        }

    out = tmp_path / "evidence"
    report = proto.run_evidence(
        out,
        base_seed=20261023,
        demos=3,
        queries=4,
        verifier=deterministic_verifier,
        required_backend="test-double",
    )
    assert report["status"] == "pass"
    assert report["summary"] == {
        "settings": 4,
        "episodes": 4,
        "demos_per_episode": 3,
        "queries_per_episode": 4,
        "distinct_inputs_per_episode": 7,
        "racket_or_verifier_outputs_checked": 112,
        "all_declared_rivals_refuted": True,
        "all_queries_distinguish_every_rival": True,
    }
    public_files = sorted((out / "public").glob("*.json"))
    private_files = sorted((out / "private/episodes").glob("*.json"))
    assert len(public_files) == len(private_files) == 4
    for path in public_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert path.stem == public_challenge_id(payload)
        assert path.read_bytes() == public_challenge_bytes(payload)
        serialized = path.read_text(encoding="utf-8")
        assert "repeat_offset" not in serialized
        assert "rule!" not in serialized
        assert all(set(pair) == {"input"} for pair in payload["test"])
