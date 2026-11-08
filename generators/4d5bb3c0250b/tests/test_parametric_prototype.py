"""Focused tests for the proposed, unapproved color-cardinality prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
MODULE_PATH = ROOT / "generators/4d5bb3c0250b/workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("parametric_4d5bb3c0250b", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_materialization_is_exact_canonical_and_alternative_is_guarded() -> None:
    proto = _load()
    canonical = proto.canonical_source(root=ROOT)
    assert proto.materialize_rule(1, root=ROOT) == canonical
    alternative = proto.materialize_rule(2, root=ROOT)
    assert alternative != canonical
    assert proto.restore_canonical(alternative) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_SOURCE_SHA256


def test_default_setting_reproduces_every_labeled_canonical_pair(bridge) -> None:
    proto = _load()
    source = proto.materialize_rule(1, root=ROOT)
    for pair in canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True):
        assert proto.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_authored_fixtures_are_lawful_and_distinguish_both_settings(bridge) -> None:
    proto = _load()
    fixtures = proto.fixtures()
    assert len(fixtures) >= 8
    rules = {value: proto.materialize_rule(value, root=ROOT) for value in (1, 2)}
    for row in fixtures:
        outputs = {
            value: proto.execute_rule(source, row["input"], bridge=bridge)
            for value, source in rules.items()
        }
        assert outputs[1] != outputs[2], row["fixture_id"]
        assert proto.validate_fixture(row["input"]) == []


def test_episode_holds_one_setting_across_three_demos_and_four_queries(bridge) -> None:
    proto = _load()
    episodes = [
        proto.make_episode(seed, demo_count=3, query_count=4, root=ROOT, bridge=bridge)
        for seed in range(8)
    ]
    assert {episode["parameters"]["selected_color_count"] for episode in episodes} == {1, 2}
    for episode in episodes:
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in all_inputs}) == 7
        assert episode["ambiguities"] == []
        selected = episode["parameters"]["selected_color_count"]
        matches = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["selected_color_count"] for row in matches] == [selected]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert refuted[0]["query_mismatch_indices"] == [0, 1, 2, 3]


def test_public_export_and_name_depend_only_on_visible_challenge(bridge) -> None:
    proto = _load()
    episode = proto.make_episode(0, demo_count=3, query_count=4, root=ROOT, bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("selected_color_count", "racket", "seed", "parameter"):
        assert forbidden not in serialized
    name = proto.public_filename(episode)
    changed_private = dict(episode, seed=999, parameters={"selected_color_count": 99})
    assert proto.public_filename(changed_private) == name
    assert name.startswith("challenge-") and name.endswith(".json")


def test_evidence_writer_retains_both_settings_and_four_query_labels(tmp_path) -> None:
    proto = _load()
    out = tmp_path / "evidence"
    report = proto.write_evidence(
        range(8),
        out=out,
        demo_count=3,
        query_count=4,
        root=ROOT,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["query_pairs"] == 4 * report["counts"]["episodes"]
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    for episode_row in report["episodes"]:
        public = json.loads((out / episode_row["public_path"]).read_text())
        private = json.loads((out / episode_row["private_path"]).read_text())
        assert public == proto.public_challenge(private)
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize("bad", [True, 0, 3, 1.0, "1", None])
def test_invalid_parameter_values_are_rejected(bad: object) -> None:
    proto = _load()
    with pytest.raises((TypeError, ValueError)):
        proto.materialize_rule(bad, root=ROOT)
