"""Racket-backed contract tests for the proposed floor-acceptance extension."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "52ac31926856"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "155890c61ab00ef4a460914d2de683ae25a4b20761bb7adfae92fb324688857d"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "floor-acceptance prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_52ac31926856_floor_acceptance", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_default_rule_are_exact():
    """Catches a drifted canonical default or a variant that edits more than the predicate."""
    proto = _prototype()
    canonical = proto.canonical_rule(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert proto.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert tuple(proto.FLOOR_ACCEPTANCE_VALUES) == ("whole_section", "under_drop")
    assert proto.DEFAULT_FLOOR_ACCEPTANCE == "whole_section"
    assert proto.instantiate_rule("whole_section", root=ROOT) == canonical
    alternative = proto.instantiate_rule("under_drop", root=ROOT)
    assert alternative != canonical
    assert proto.restore_canonical(alternative, root=ROOT) == canonical
    assert proto.choose_floor_acceptance(0) == "whole_section"
    assert proto.choose_floor_acceptance(1) == "under_drop"


@pytest.mark.parametrize("bad", [True, False, 1.0, "0", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(bad):
    """Catches bool/coercion acceptance and negative episode seeds."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        proto.choose_floor_acceptance(bad)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("demo_count", 0),
        ("query_count", 0),
        ("demo_count", True),
        ("query_count", 1.5),
        ("query_count", 13),
    ],
)
def test_episode_counts_are_bounded_plain_integers(name, bad):
    """Catches silently truncated, empty, bool, or unbounded episode sizes."""
    proto = _prototype()
    kwargs = {name: bad}
    with pytest.raises((TypeError, ValueError), match=name):
        proto.generate_inputs(0, **kwargs)


@pytest.mark.parametrize("bad", ["solid", "", 0, None, True])
def test_floor_acceptance_rejects_undeclared_settings(bad):
    """Catches accidental acceptance of arbitrary hidden rule strings."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="floor_acceptance"):
        proto.instantiate_rule(bad, root=ROOT)


def test_inputs_are_distinct_lawful_setting_independent_and_distinguishing():
    """Catches cloned pairs, parameter-conditioned inputs, or missing off-column witnesses."""
    proto = _prototype()
    first = proto.generate_inputs(23, demo_count=3, query_count=4)
    second = proto.generate_inputs(23, demo_count=3, query_count=4)
    assert first == second
    assert len(first) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 7
    assert all(proto.GEN.self_check(grid) == [] for grid in first)

    analyses = [proto.GEN._analyze(grid) for grid in first]
    assert all(analysis["landing"] in {"second", "bottom"} for analysis in analyses)
    assert all(
        any(
            item["candidate"]
            and not item["floor_solid"]
            and item["blue_floor_solid"]
            and item["off_column_gap"]
            for item in analysis["containers"]
        )
        for analysis in analyses
    )

    with RacketBridge() as bridge:
        canonical = proto.make_episode(
            bridge,
            23,
            floor_acceptance="whole_section",
            demo_count=3,
            query_count=4,
        )
        alternative = proto.make_episode(
            bridge,
            23,
            floor_acceptance="under_drop",
            demo_count=3,
            query_count=4,
        )
    assert [pair["input"] for pair in canonical["pairs"]] == [
        pair["input"] for pair in alternative["pairs"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["pairs"], alternative["pairs"], strict=True)
    )


def test_real_racket_labels_cover_canonical_and_four_queries_per_setting():
    """Catches Python-only labels or demonstrations that fail to identify the chosen setting."""
    proto = _prototype()
    with RacketBridge() as bridge:
        canonical_program = proto.instantiate_rule("whole_section", root=ROOT)
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert proto.evaluate(bridge, canonical_program, pair["input"]) == pair["output"]

        episodes = [
            proto.make_episode(bridge, seed, demo_count=3, query_count=4)
            for seed in (0, 1)
        ]
        assert {
            episode["parameters"]["floor_acceptance"] for episode in episodes
        } == set(proto.FLOOR_ACCEPTANCE_VALUES)
        for episode in episodes:
            analysis = proto.analyze_episode(bridge, episode)
            assert len(episode["pairs"]) == 7
            assert episode["demo_count"] == 3
            assert episode["query_count"] == 4
            assert analysis["status"] == "no_ambiguity_found"
            assert len(analysis["queries"]) == 4
            assert all(row["status"] == "no_ambiguity_found" for row in analysis["queries"])
            assert all(
                row["rivals"][0]["refuting_demonstration_indices"]
                for row in analysis["queries"]
            )
            assert all(row["rivals"][0]["query_differs"] for row in analysis["queries"])


def test_public_projection_and_name_hide_private_episode_state():
    """Catches private metadata/query-label leakage or non-visible filename inputs."""
    proto = _prototype()
    with RacketBridge() as bridge:
        episode = proto.make_episode(bridge, 0, demo_count=3, query_count=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("floor_acceptance", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized

    name = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
    assert name == f"challenge-{public_challenge_id(public)}.json"
    assert proto.public_bytes(episode) == public_challenge_bytes(public)

    hidden_changed = deepcopy(episode)
    hidden_changed["seed"] = 999
    hidden_changed["parameters"] = {"floor_acceptance": "under_drop"}
    hidden_changed["racket_program"] = "private replacement"
    for pair in hidden_changed["pairs"][hidden_changed["demo_count"] :]:
        pair["output"] = [[9]]
    assert proto.public_filename(hidden_changed) == name
    assert proto.public_bytes(hidden_changed) == proto.public_bytes(episode)

    visible_changed = deepcopy(episode)
    visible_changed["pairs"][0]["output"][0][0] = 9
    assert proto.public_filename(visible_changed) != name


def test_materialized_tree_has_two_complete_four_query_episodes(tmp_path):
    """Catches incomplete evidence, stale receipts, replay drift, or missing setting coverage."""
    proto = _prototype()
    out = tmp_path / "floor-acceptance"
    report = proto.materialize(out, seed=0, demo_count=3, query_count=4)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_passed"] == 6
    assert report["counts"]["demonstrations"] == 6
    assert report["counts"]["queries"] == 8
    assert report["counts"]["query_ambiguities"] == 0
    assert report["counts"]["settings_seen"] == list(proto.FLOOR_ACCEPTANCE_VALUES)

    report_public_paths = [episode["public_path"] for episode in report["episodes"]]
    assert report_public_paths == sorted(report_public_paths)
    assert len(report_public_paths) == len(set(report_public_paths)) == 2

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    for path in public_paths:
        challenge = json.loads(path.read_text())
        assert path.name == proto.public_filename(challenge)
        assert path.read_bytes() == public_challenge_bytes(challenge)
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert len(list((out / "private" / "rules").glob("*.rkt"))) == 2
    assert proto.verify_tree(out, root=ROOT)["status"] == "pass"

    with pytest.raises(FileExistsError):
        proto.materialize(out, seed=0, demo_count=3, query_count=4)

def test_materialized_batch_rejects_duplicate_visible_payloads(tmp_path, monkeypatch):
    """Catches silent overwrite when two private episodes project to one public challenge."""
    proto = _prototype()
    with RacketBridge() as bridge:
        repeated = proto.make_episode(bridge, 0, demo_count=3, query_count=4)

    def repeat_episode(*args, **kwargs):
        return deepcopy(repeated)

    monkeypatch.setattr(proto, "make_episode", repeat_episode)
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        proto.materialize(
            tmp_path / "duplicate-public",
            seed=0,
            demo_count=3,
            query_count=4,
        )

