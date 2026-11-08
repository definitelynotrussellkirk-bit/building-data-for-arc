"""Racket-backed contract tests for the proposed lower-band-order extension."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "3a0af56db83e"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "bc82cba9a8627be7135eaf112cc05518bb9db9ababda3c3c1a497c47c906d0d0"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "lower-band-order prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_3a0af56db83e", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_default_rule_are_exact():
    proto = _prototype()
    canonical = proto.canonical_rule(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert proto.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert tuple(proto.LOWER_BAND_ORDERS) == ("band3_then_band2", "band2_then_band3")
    assert proto.DEFAULT_LOWER_BAND_ORDER == "band3_then_band2"
    assert proto.instantiate_rule("band3_then_band2", root=ROOT) == canonical
    alternative = proto.instantiate_rule("band2_then_band3", root=ROOT)
    assert alternative != canonical
    assert proto.restore_canonical(alternative) == canonical
    assert proto.choose_lower_band_order(0) == "band3_then_band2"
    assert proto.choose_lower_band_order(1) == "band2_then_band3"


@pytest.mark.parametrize("bad", [True, False, 1.0, "0", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(bad):
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        proto.choose_lower_band_order(bad)


@pytest.mark.parametrize("name,bad", [("demo_count", 0), ("query_count", 0), ("demo_count", True), ("query_count", 1.5), ("query_count", 13)])
def test_episode_counts_are_bounded_plain_integers(name, bad):
    proto = _prototype()
    kwargs = {name: bad}
    with pytest.raises((TypeError, ValueError), match=name):
        proto.generate_inputs(0, **kwargs)


def test_inputs_are_distinct_lawful_and_independent_of_hidden_setting():
    proto = _prototype()
    first = proto.generate_inputs(23, demo_count=2, query_count=4)
    second = proto.generate_inputs(23, demo_count=2, query_count=4)
    assert first == second
    assert len(first) == 6
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 6
    assert all(proto.GEN.self_check(grid) == [] for grid in first)
    with RacketBridge() as bridge:
        canonical = proto.make_episode(
            bridge,
            23,
            lower_band_order="band3_then_band2",
            demo_count=2,
            query_count=4,
        )
        alternative = proto.make_episode(
            bridge,
            23,
            lower_band_order="band2_then_band3",
            demo_count=2,
            query_count=4,
        )
    assert [pair["input"] for pair in canonical["pairs"]] == [
        pair["input"] for pair in alternative["pairs"]
    ]


def test_real_racket_labels_cover_canonical_and_four_queries_per_setting():
    proto = _prototype()
    with RacketBridge() as bridge:
        canonical_program = proto.instantiate_rule("band3_then_band2", root=ROOT)
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert proto.evaluate(bridge, canonical_program, pair["input"]) == pair["output"]

        episodes = [
            proto.make_episode(bridge, seed, demo_count=2, query_count=4)
            for seed in (0, 1)
        ]
        assert {episode["parameters"]["lower_band_order"] for episode in episodes} == set(
            proto.LOWER_BAND_ORDERS
        )
        for episode in episodes:
            analysis = proto.analyze_episode(bridge, episode)
            assert len(episode["pairs"]) == 6
            assert episode["demo_count"] == 2
            assert episode["query_count"] == 4
            assert analysis["status"] == "no_ambiguity_found"
            assert len(analysis["queries"]) == 4
            assert all(row["status"] == "no_ambiguity_found" for row in analysis["queries"])
            assert all(row["rivals"][0]["refuting_demonstration_indices"] for row in analysis["queries"])
            assert all(row["rivals"][0]["query_differs"] for row in analysis["queries"])


def test_public_projection_and_name_hide_private_episode_state():
    proto = _prototype()
    with RacketBridge() as bridge:
        episode = proto.make_episode(bridge, 0, demo_count=2, query_count=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 2
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("lower_band_order", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized

    name = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
    hidden_changed = deepcopy(episode)
    hidden_changed["seed"] = 999
    hidden_changed["parameters"] = {"lower_band_order": "band2_then_band3"}
    hidden_changed["racket_program"] = "private replacement"
    for pair in hidden_changed["pairs"][hidden_changed["demo_count"] :]:
        pair["output"] = [[9]]
    assert proto.public_filename(hidden_changed) == name
    visible_changed = deepcopy(episode)
    visible_changed["pairs"][0]["output"][0][0] = 9
    assert proto.public_filename(visible_changed) != name


def test_materialized_tree_emits_public_files_in_visible_name_order(tmp_path, monkeypatch):
    """A private seed/setting schedule must not determine public creation order."""
    proto = _prototype()
    observed_public_writes = []
    real_write_json = proto.write_json

    def record_public_write(path, value):
        path = Path(path)
        if path.parent.name == "public":
            observed_public_writes.append(path.name)
        real_write_json(path, value)

    monkeypatch.setattr(proto, "write_json", record_public_write)
    out = tmp_path / "lower-band-order"
    proto.materialize(out, seed=0, demo_count=2, query_count=4)
    assert len(observed_public_writes) == 2
    assert observed_public_writes == sorted(observed_public_writes)


def test_materialized_tree_rejects_duplicate_visible_public_ids(tmp_path, monkeypatch):
    """A duplicate visible payload/id must fail explicitly before public emission."""
    proto = _prototype()
    monkeypatch.setattr(
        proto,
        "public_filename",
        lambda _challenge: "challenge-duplicate-visible-id.json",
    )

    with pytest.raises(ValueError, match="duplicate visible public challenge id"):
        proto.materialize(
            tmp_path / "lower-band-order",
            seed=0,
            demo_count=2,
            query_count=4,
        )


def test_materialized_tree_has_two_complete_four_query_episodes(tmp_path):
    proto = _prototype()
    out = tmp_path / "lower-band-order"
    report = proto.materialize(out, seed=0, demo_count=2, query_count=4)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_passed"] == 7
    assert report["counts"]["demonstrations"] == 4
    assert report["counts"]["queries"] == 8
    assert report["counts"]["query_ambiguities"] == 0
    assert report["counts"]["settings_seen"] == list(proto.LOWER_BAND_ORDERS)

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    for path in public_paths:
        challenge = json.loads(path.read_text())
        assert path.name == proto.public_filename(challenge)
        assert len(challenge["train"]) == 2
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert len(list((out / "private" / "rules").glob("*.rkt"))) == 2
    assert proto.verify_tree(out, root=ROOT)["status"] == "pass"

    with pytest.raises(FileExistsError):
        proto.materialize(out, seed=0, demo_count=2, query_count=4)
