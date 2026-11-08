"""Focused tests for the proposed a2ad2da63297 crossing-mode prototype.

The production generator and canonical Racket authority stay untouched.  This
module exercises a separate episode-level prototype whose labels are executed by
the bundled Racket runtime.
"""
from __future__ import annotations

from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a2ad2da63297"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
CANONICAL_SHA256 = "937e30cc1e90881f7f01d4b05e8ec9bbb6a71432bfd75b8e7b744ccc9e2abf1c"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "crossing-mode prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_crossing_mode_a2ad2da63297", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def horizontal_witness() -> list[list[int]]:
    """Two unequal-color pairs around a dominant horizontal barrier."""
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 4, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 6, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def cross_expected() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 6, 0, 3, 0, 0],
        [0, 8, 8, 8, 8, 8, 0],
        [0, 0, 4, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def compress_expected() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 4, 0, 1, 0, 0],
        [0, 8, 8, 8, 8, 8, 0],
        [0, 0, 6, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_default_rule_is_exact_canonical_and_alternate_is_guarded() -> None:
    """Catches authority drift, broad source edits and unbounded settings."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    crossing = p.materialize_rule(root=ROOT)
    compressing = p.materialize_rule("compress_to_barrier", root=ROOT)

    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert crossing == canonical
    assert compressing != canonical
    assert p.rule_setting(crossing, root=ROOT) == "cross_through"
    assert p.rule_setting(compressing, root=ROOT) == "compress_to_barrier"

    for source, destination in p.CROSS_DESTINATIONS:
        assert canonical.count(source) == 1
        assert canonical.count(destination) == 0
        assert compressing.count(source) == 0
        assert compressing.count(destination) == 1

    with pytest.raises(ValueError, match="crossing_mode"):
        p.materialize_rule("bounce_away", root=ROOT)
    with pytest.raises(ValueError, match="crossing_mode"):
        p.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(root=ROOT, source=canonical + "\n")


def test_racket_executes_both_orientations_and_default_replays_canonical() -> None:
    """Catches branch swaps, one-orientation edits and Python-only labels."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    horizontal = horizontal_witness()
    vertical = _transpose(horizontal)
    with RacketBridge(max_calls_before_restart=128) as bridge:
        cross = p.execute_rule_many(
            p.materialize_rule("cross_through", root=ROOT),
            [horizontal, vertical],
            bridge=bridge,
            root=ROOT,
        )
        compress = p.execute_rule_many(
            p.materialize_rule("compress_to_barrier", root=ROOT),
            [horizontal, vertical],
            bridge=bridge,
            root=ROOT,
        )
        assert cross == [cross_expected(), _transpose(cross_expected())]
        assert compress == [compress_expected(), _transpose(compress_expected())]

        canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        assert len(canonical) == 4
        replayed = p.execute_rule_many(
            p.materialize_rule(root=ROOT),
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=ROOT,
        )
        assert replayed == [pair["output"] for pair in canonical]


def test_seed_count_and_input_stream_contracts_are_strict() -> None:
    """Catches bool coercions, per-pair rule drift and setting-dependent inputs."""
    p = prototype()
    assert p.parameter_for_seed(0) == {"crossing_mode": "cross_through"}
    assert p.parameter_for_seed(1) == {"crossing_mode": "compress_to_barrier"}
    assert p.parameter_for_seed(2) == {"crossing_mode": "cross_through"}

    inputs0, roles0 = p.episode_inputs(0, demo_count=2, query_count=4, root=ROOT)
    inputs1, roles1 = p.episode_inputs(1, demo_count=2, query_count=4, root=ROOT)
    assert inputs0 == inputs1
    assert roles0 == roles1
    assert [row["orientation"] for row in roles0[:2]] == ["horizontal", "vertical"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs0}) == 6

    for invalid_seed in (True, -1, 2**63, 1.5, "1"):
        with pytest.raises(ValueError, match="seed"):
            p.parameter_for_seed(invalid_seed)

    for name, value in (
        ("demo_count", 1),
        ("demo_count", 9),
        ("demo_count", True),
        ("query_count", 0),
        ("query_count", 9),
        ("query_count", 4.0),
    ):
        kwargs = {"demo_count": 2, "query_count": 4, name: value}
        with pytest.raises(ValueError, match=name):
            p.episode_inputs(0, root=ROOT, **kwargs)


def test_episode_is_fixed_identifiable_and_has_four_distinct_queries() -> None:
    """Catches query cloning, hidden resampling and demonstrations that fit rivals."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=256) as bridge:
        for seed, selected, rival in (
            (0, "cross_through", "compress_to_barrier"),
            (1, "compress_to_barrier", "cross_through"),
        ):
            public, private = p.generate_episode(
                seed,
                demo_count=2,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            public_again, private_again = p.generate_episode(
                seed,
                demo_count=2,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            assert public == public_again
            assert private == private_again
            assert private["parameter"] == {"crossing_mode": selected}
            assert private["demo_count"] == 2
            assert private["query_count"] == 4
            assert len(public["train"]) == 2
            assert len(public["test"]) == 4
            assert len(private["query_answers"]) == 4
            assert private["racket_python_parity"] is True

            visible_inputs = [pair["input"] for pair in public["train"] + public["test"]]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in visible_inputs}) == 6
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])

            chosen = private["rival_checks"][selected]
            opposite = private["rival_checks"][rival]
            identity = private["rival_checks"]["identity"]
            assert chosen["matches_all_demonstrations"] is True
            assert chosen["demonstration_disagreements"] == []
            assert chosen["query_disagreements"] == []
            assert opposite["matches_all_demonstrations"] is False
            assert opposite["demonstration_disagreements"] == [0, 1]
            assert opposite["query_disagreements"] == [0, 1, 2, 3]
            assert identity["matches_all_demonstrations"] is False
            assert identity["demonstration_disagreements"] == [0, 1]


def test_evidence_writer_uses_visible_only_ids_and_hides_private_fields(
    tmp_path: Path,
) -> None:
    """Catches setting, seed, rule, answer and ordinal leakage into public files."""
    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[0, 1],
        demo_count=2,
        query_count=4,
        root=ROOT,
    )

    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"] == {
        "name": "crossing_mode",
        "allowed": ["cross_through", "compress_to_barrier"],
        "default": "cross_through",
        "input_constraints_dependent": [],
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["demo_count"] == 2
    assert manifest["query_count"] == 4

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(public_paths) == 2
    assert len(private_paths) == 2
    assert len({path.name for path in public_paths}) == 2

    forbidden = (
        "crossing_mode",
        "cross_through",
        "compress_to_barrier",
        "query_answers",
        '"seed"',
        "program_sha256",
        "937e30cc",
    )
    for path in public_paths:
        raw = path.read_bytes()
        data = json.loads(raw)
        assert raw == public_challenge_bytes(data)
        assert path.name == f"challenge-{public_challenge_id(data)}.json"
        text = raw.decode("utf-8")
        assert not any(token in text for token in forbidden)
        assert all(set(pair) == {"input"} for pair in data["test"])

    for setting in ("cross_through", "compress_to_barrier"):
        rule_path = out / "private" / "rules" / f"{setting}.rkt"
        assert rule_path.read_text(encoding="utf-8") == p.materialize_rule(
            setting, root=ROOT
        )

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)
