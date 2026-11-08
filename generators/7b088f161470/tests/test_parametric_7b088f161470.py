from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_id

TASK_ID = "7b088f161470"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_7b088f161470", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _writer_episode(query_value: int) -> dict:
    public = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[query_value]]}],
    }
    rule_source = "(rule! identity)"
    return {
        "public": public,
        "private": {
            "public_id": public_challenge_id(public),
            "rule_source": rule_source,
            "rule_sha256": hashlib.sha256(rule_source.encode("utf-8")).hexdigest(),
        },
    }


def _hand_fixture() -> list[list[int]]:
    return [
        [2] * 8,
        [0, 2, 2, 2, 0, 0, 0, 0],
        [0, 0, 2, 2, 2, 2, 0, 0],
        [0, 2, 2, 2, 2, 2, 0, 0],
        [2, 0, 2, 0, 0, 0, 0, 0],
        [4] * 8,
        [4, 4, 4, 4, 0, 0, 0, 0],
        [0, 0, 4, 4, 4, 4, 4, 0],
        [0, 4, 0, 4, 0, 0, 0, 0],
        [7] * 8,
        [7, 7, 7, 7, 7, 0, 0, 0],
        [0, 0, 0, 7, 7, 7, 7, 7],
        [0, 7, 0, 7, 0, 5, 0, 0],
        [9] * 8,
    ]


EXPECTED = {
    (3, "left"): [[2, 2, 2, 9, 0], [4, 4, 0, 9, 0], [7, 7, 0, 9, 5]],
    (3, "right"): [[2, 2, 2, 9, 0], [0, 4, 4, 9, 0], [0, 7, 7, 9, 5]],
    (4, "left"): [[2, 2, 0, 9, 0], [4, 4, 0, 9, 0], [7, 7, 0, 9, 5]],
    (4, "right"): [[0, 2, 2, 9, 0], [0, 4, 4, 9, 0], [0, 7, 7, 9, 5]],
    (5, "left"): [[2, 0, 0, 9, 0], [4, 0, 0, 9, 5], [7, 7, 0, 9, 0]],
    (5, "right"): [[0, 0, 2, 9, 0], [0, 0, 4, 9, 5], [0, 7, 7, 9, 0]],
}


def test_materialized_rules_execute_hand_derived_outputs() -> None:
    """Wrong threshold, alignment branch, or gray tie handling changes a literal output."""
    prototype = _prototype()
    assert prototype.materialize_rule(3, "left") == prototype.canonical_source()
    with RacketBridge() as bridge:
        actual = {}
        for setting, expected in EXPECTED.items():
            source = prototype.materialize_rule(*setting)
            actual[setting] = prototype.execute_rule(
                source, _hand_fixture(), bridge=bridge
            )
            assert actual[setting] == expected
            assert prototype.apply_python(_hand_fixture(), *setting) == expected
    assert len({json.dumps(value) for value in actual.values()}) == 6


def test_default_rule_executes_every_canonical_pair() -> None:
    """Changing the default away from exact canonical semantics breaks parity."""
    prototype = _prototype()
    source = prototype.materialize_rule(3, "left")
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_every_setting_is_identified_by_demonstrations_only() -> None:
    """A sampler that omits a threshold/alignment witness leaves multiple settings alive."""
    prototype = _prototype()
    with RacketBridge() as bridge:
        for index, setting in enumerate(prototype.SETTINGS):
            episode = prototype.generate_episode(
                8100 + index,
                min_rung_width=setting[0],
                bar_alignment=setting[1],
                n_train=3,
                n_test=4,
                bridge=bridge,
            )
            assert episode["private"]["parameters"] == {
                "min_rung_width": setting[0],
                "bar_alignment": setting[1],
            }
            assert episode["private"]["demo_survivors"] == [
                {"min_rung_width": setting[0], "bar_alignment": setting[1]}
            ]


def test_episode_counts_queries_reproducibility_and_setting_stability() -> None:
    """Changing counts must not resample the hidden rule or silently clone queries."""
    prototype = _prototype()
    with RacketBridge() as bridge:
        first = prototype.generate_episode(991, n_train=2, n_test=4, bridge=bridge)
        again = prototype.generate_episode(991, n_train=2, n_test=4, bridge=bridge)
        resized = prototype.generate_episode(991, n_train=5, n_test=1, bridge=bridge)
    assert first == again
    assert first["private"]["parameters"] == resized["private"]["parameters"]
    assert len(first["public"]["train"]) == 2
    assert len(first["public"]["test"]) == 4
    visible_inputs = [
        pair["input"] for pair in first["public"]["train"] + first["public"]["test"]
    ]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in visible_inputs}
    assert len(keys) == 6
    assert all("output" not in pair for pair in first["public"]["test"])
    assert len(first["private"]["query_outputs"]) == 4


def test_public_payload_and_filename_depend_only_on_visible_bytes(tmp_path: Path) -> None:
    """Leaking settings, seed, rule text, or query labels makes the public export unsafe."""
    prototype = _prototype()
    with RacketBridge() as bridge:
        episode = prototype.generate_episode(
            1207,
            min_rung_width=4,
            bar_alignment="right",
            n_train=3,
            n_test=4,
            bridge=bridge,
        )
    public_id = public_challenge_id(episode["public"])
    assert episode["private"]["public_id"] == public_id
    paths = prototype.write_episode(episode, tmp_path, index=0)
    assert paths["public"].name == f"challenge-{public_id}.json"
    public = json.loads(paths["public"].read_text())
    private = json.loads(paths["private"].read_text())
    rule_bytes = paths["rule"].read_bytes()
    assert public == episode["public"]
    assert private["parameters"] == episode["private"]["parameters"]
    assert rule_bytes == private["rule_source"].encode("utf-8")
    assert hashlib.sha256(rule_bytes).hexdigest() == private["rule_sha256"]
    public_text = paths["public"].read_text()
    for forbidden in (
        "seed",
        "min_rung_width",
        "bar_alignment",
        "rule_source",
        "query_outputs",
    ):
        assert forbidden not in public_text
    changed = copy.deepcopy(episode)
    changed["private"]["seed"] += 1
    changed["private"]["parameters"]["min_rung_width"] = 5
    changed["private"]["query_outputs"][0][0][0] ^= 1
    assert public_challenge_id(changed["public"]) == public_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"min_rung_width": 2}, "min_rung_width"),
        ({"min_rung_width": True}, "min_rung_width"),
        ({"bar_alignment": "center"}, "bar_alignment"),
        ({"seed": True}, "seed"),
        ({"n_train": 0}, "n_train"),
        ({"n_test": 0}, "n_test"),
        ({"n_train": True}, "n_train"),
        ({"n_test": 129}, "n_test"),
    ],
)
def test_invalid_episode_arguments_fail_loudly(kwargs: dict, message: str) -> None:
    """Invalid settings/counts must raise instead of producing partial evidence."""
    prototype = _prototype()
    base = {"seed": 1, "n_train": 3, "n_test": 4}
    base.update(kwargs)
    with pytest.raises(ValueError, match=message):
        prototype.generate_episode(**base)


def test_existing_rule_artifact_must_match_its_content_hash(tmp_path: Path) -> None:
    """A stale or corrupted rule file must not be silently reused as evidence."""
    prototype = _prototype()
    first = _writer_episode(1)
    second = _writer_episode(2)
    assert first["private"]["rule_sha256"] == second["private"]["rule_sha256"]
    assert first["private"]["public_id"] != second["private"]["public_id"]
    paths = prototype.write_episode(first, tmp_path, index=0)
    paths["rule"].write_bytes(b"corrupted rule evidence")
    with pytest.raises(ValueError, match="existing rule artifact"):
        prototype.write_episode(second, tmp_path, index=1)


def test_writer_rejects_private_rule_hash_mismatch(tmp_path: Path) -> None:
    """A tampered private rule hash must not select a misleading artifact name."""
    prototype = _prototype()
    episode = _writer_episode(1)
    episode["private"]["rule_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="rule_sha256"):
        prototype.write_episode(episode, tmp_path, index=0)

