from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"
CANONICAL_SHA256 = "fc2471b9a0fe8f3bf1318728a845cb54408e2d80744b6da6deca664a681cdbaa"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "review_ead22faa41ef_parametric", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_preserves_exact_default_and_restores_variants():
    prototype = load_prototype()
    canonical = prototype.canonical_rule()

    assert prototype.TASK_ID == "ead22faa41ef"
    assert prototype.SURVIVOR_ROLES == ("green3", "red2")
    assert prototype.DEFAULT_SURVIVOR_ROLE == "green3"
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.instantiate_rule() == canonical
    assert prototype.instantiate_rule("green3") == canonical

    alternative = prototype.instantiate_rule("red2")
    assert alternative != canonical
    assert prototype.restore_canonical(canonical) == canonical
    assert prototype.restore_canonical(alternative) == canonical


@pytest.mark.parametrize("bad_seed", [-1, True, 1.5, "1"])
def test_seed_validation_rejects_negative_and_non_plain_integers(bad_seed):
    prototype = load_prototype()
    error = ValueError if bad_seed == -1 else TypeError
    with pytest.raises(error):
        prototype.generate_inputs(bad_seed)


@pytest.mark.parametrize("name,value", [("demo_count", 0), ("query_count", 13)])
def test_count_validation_is_bounded(name, value):
    prototype = load_prototype()
    kwargs = {name: value}
    with pytest.raises(ValueError):
        prototype.generate_inputs(0, **kwargs)


def test_input_generation_is_setting_independent_distinct_and_witness_bearing():
    prototype = load_prototype()
    first = prototype.generate_inputs(7, demo_count=3, query_count=4)
    second = prototype.generate_inputs(7, demo_count=3, query_count=4)

    assert first == second
    assert len(first) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 7
    for grid in first:
        assert prototype.GEN.self_check(grid) == []
        features = prototype.GEN._scene_features(grid)
        assert len(features["paired3"]) >= 1
        assert features["counts"][3] - len(features["paired3"]) >= 1
        assert features["counts"][2] - len(features["paired2"]) >= 1


def test_real_racket_episodes_refute_declared_rivals_for_all_four_queries():
    prototype = load_prototype()
    with RacketBridge() as bridge:
        for role in prototype.SURVIVOR_ROLES:
            episode = prototype.make_episode(
                bridge,
                11,
                survivor_role=role,
                demo_count=3,
                query_count=4,
            )
            analysis = prototype.analyze_episode(bridge, episode)

            assert episode["parameters"] == {"survivor_role": role}
            assert len(episode["pairs"]) == 7
            assert analysis["status"] == "no_ambiguity_found"
            assert len(analysis["queries"]) == 4
            for row in analysis["queries"]:
                assert row["status"] == "no_ambiguity_found"
                assert {rival["kind"] for rival in row["rivals"]} == {
                    "alternate_parameter",
                    "global_replacement",
                }
                assert all(not rival["fits_demonstrations"] for rival in row["rivals"])
                assert all(rival["query_differs"] for rival in row["rivals"])


def test_public_projection_and_opaque_name_depend_only_on_visible_bytes():
    prototype = load_prototype()
    with RacketBridge() as bridge:
        episode = prototype.make_episode(
            bridge,
            3,
            survivor_role="green3",
            demo_count=3,
            query_count=4,
        )

    challenge = prototype.public_challenge(episode)
    name = prototype.public_filename(challenge)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
    assert name == f"challenge-{public_challenge_id(challenge)}.json"
    assert public_challenge_bytes(challenge).endswith(b"\n")
    assert all(set(pair) == {"input"} for pair in challenge["test"])

    hidden_change = deepcopy(episode)
    hidden_change["seed"] += 100
    hidden_change["parameters"]["survivor_role"] = "red2"
    hidden_change["racket_program"] = "private-change"
    hidden_change["pairs"][-1]["output"][0][0] ^= 1
    hidden_challenge = prototype.public_challenge(hidden_change)
    assert prototype.public_filename(hidden_challenge) == name

    visible_change = deepcopy(challenge)
    visible_change["train"][0]["output"][0][0] ^= 1
    assert prototype.public_filename(visible_change) != name


def test_materialized_tree_replays_all_labels_and_receipts(tmp_path):
    prototype = load_prototype()
    out = tmp_path / "survivor-role-evidence"
    report = prototype.materialize(
        out,
        seed=20,
        demo_count=3,
        query_count=4,
    )
    verified = prototype.verify_tree(out)

    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "canonical_labels": 4,
        "canonical_labels_passed": 4,
        "episodes": 2,
        "demonstrations": 6,
        "queries": 8,
        "episode_labels": 14,
        "query_ambiguities": 0,
        "settings_seen": ["green3", "red2"],
    }
    assert verified["status"] == "pass", verified["errors"]
    assert verified["counts"]["canonical_labels_checked"] == 4
    assert verified["counts"]["episode_labels_checked"] == 14
    assert verified["counts"]["public_files_checked"] == 2


def test_materialize_sorts_public_writes_independently_of_private_role_order(
    monkeypatch, tmp_path
):
    prototype = load_prototype()
    monkeypatch.setattr(prototype, "SURVIVOR_ROLES", ("red2", "green3"))
    out = tmp_path / "reversed-private-order"
    public_writes: list[str] = []
    original_write_bytes = Path.write_bytes

    def observe_write_bytes(path: Path, payload: bytes) -> int:
        if path.parent == out / "public" and path.suffix == ".json":
            public_writes.append(path.name)
        return original_write_bytes(path, payload)

    monkeypatch.setattr(Path, "write_bytes", observe_write_bytes)
    report = prototype.materialize(
        out,
        seed=2,
        demo_count=3,
        query_count=4,
    )

    assert public_writes == sorted(public_writes)
    assert [
        row["parameters"]["survivor_role"] for row in report["episodes"]
    ] == ["red2", "green3"]
    assert [row["private_path"] for row in report["episodes"]] == [
        "private/episode-001.json",
        "private/episode-002.json",
    ]


def test_materialize_rejects_duplicate_visible_batch_before_destination_creation(
    monkeypatch, tmp_path
):
    prototype = load_prototype()
    original_public_challenge = prototype.public_challenge
    first_challenge: list[dict] = []

    def duplicate_public_challenge(episode):
        challenge = original_public_challenge(episode)
        if not first_challenge:
            first_challenge.append(deepcopy(challenge))
        return deepcopy(first_challenge[0])

    monkeypatch.setattr(prototype, "public_challenge", duplicate_public_challenge)
    out = tmp_path / "duplicate-visible-batch"

    with pytest.raises(ValueError, match="duplicate visible challenge"):
        prototype.materialize(
            out,
            seed=0,
            demo_count=3,
            query_count=4,
        )

    assert not out.exists()
