"""Focused checks for the proposed overlap-precedence rule prototype.

These tests keep the approved production generator and canonical rule untouched.
They exercise a separate episode-level prototype whose labels are produced by the
bundled Racket runtime.
"""
from __future__ import annotations

from functools import cache
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

TASK_ID = "0ae119475d57"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "overlap-precedence prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_overlap_precedence_0ae119475d57", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distinguishing_input() -> list[list[int]]:
    """Literal lawful scene with overlap, top-only, bottom-only and blank cells."""
    return [
        [1, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [5, 5, 5, 5],
        [2, 0, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]


def test_default_rule_is_exact_canonical_and_variant_is_guarded() -> None:
    """Catches default drift, broad source replacement and unbounded settings."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    lower = p.materialize_rule(root=ROOT)
    upper = p.materialize_rule("upper_wins", root=ROOT)

    assert lower == canonical
    assert upper != canonical
    assert lower.count("(if (!= bot 0) bot top)") == 1
    assert upper.count("(if (!= top 0) top bot)") == 1
    assert p.rule_setting(lower, root=ROOT) == "lower_wins"
    assert p.rule_setting(upper, root=ROOT) == "upper_wins"

    with pytest.raises(ValueError, match="overlap_precedence"):
        p.materialize_rule("separator_wins", root=ROOT)
    with pytest.raises(ValueError, match="overlap_precedence"):
        p.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(root=ROOT, source=canonical + "\n")


def test_racket_executes_both_settings_and_default_replays_canonical() -> None:
    """Catches a Python-only mirror or the two precedence branches being swapped."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    witness = distinguishing_input()
    expected_lower = [
        [2, 1, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    expected_upper = [
        [1, 1, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]

    with RacketBridge() as bridge:
        actual = p.execute_rule_many(
            p.materialize_rule("lower_wins", root=ROOT),
            [witness],
            bridge=bridge,
            root=ROOT,
        )[0]
        alternate = p.execute_rule_many(
            p.materialize_rule("upper_wins", root=ROOT),
            [witness],
            bridge=bridge,
            root=ROOT,
        )[0]
        assert actual == expected_lower
        assert alternate == expected_upper

        canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        assert len(canonical) == 4
        replayed = p.execute_rule_many(
            p.materialize_rule("lower_wins", root=ROOT),
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=ROOT,
        )
        assert replayed == [pair["output"] for pair in canonical]


def test_seed_and_count_validation_are_strict() -> None:
    """Catches bool/float coercions, unbounded counts and per-call setting drift."""
    p = prototype()
    assert p.parameter_for_seed(0) == {"overlap_precedence": "lower_wins"}
    assert p.parameter_for_seed(1) == {"overlap_precedence": "upper_wins"}
    assert p.parameter_for_seed(2) == {"overlap_precedence": "lower_wins"}

    for invalid_seed in (True, -1, 2**63, 1.5, "1"):
        with pytest.raises(ValueError, match="seed"):
            p.parameter_for_seed(invalid_seed)

    for name, value in (
        ("demo_count", 0),
        ("demo_count", 9),
        ("demo_count", True),
        ("query_count", 0),
        ("query_count", 9),
        ("query_count", 4.0),
    ):
        kwargs = {"demo_count": 2, "query_count": 4, name: value}
        with pytest.raises(ValueError, match=name):
            p.episode_inputs(0, root=ROOT, **kwargs)


def test_episode_setting_is_fixed_identifiable_and_has_four_distinct_queries() -> None:
    """Catches per-pair resampling, duplicate inputs and non-identifying demos."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed, selected, rival in (
            (0, "lower_wins", "upper_wins"),
            (1, "upper_wins", "lower_wins"),
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
            assert private["parameter"] == {"overlap_precedence": selected}
            assert private["demo_count"] == 2
            assert private["query_count"] == 4
            assert len(public["train"]) == 2
            assert len(public["test"]) == 4
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert len(private["query_answers"]) == 4

            visible_inputs = [pair["input"] for pair in public["train"] + public["test"]]
            fingerprints = {
                json.dumps(grid, sort_keys=True, separators=(",", ":"))
                for grid in visible_inputs
            }
            assert len(fingerprints) == 6

            selected_check = private["rival_checks"][selected]
            rival_check = private["rival_checks"][rival]
            assert selected_check["matches_all_demonstrations"] is True
            assert selected_check["demonstration_disagreements"] == []
            assert selected_check["query_disagreements"] == []
            assert rival_check["matches_all_demonstrations"] is False
            assert rival_check["demonstration_disagreements"] == [0, 1]
            assert rival_check["query_disagreements"] == [0, 1, 2, 3]


def test_evidence_writer_uses_visible_only_public_ids_and_hides_private_fields(
    tmp_path: Path,
) -> None:
    """Catches private setting/seed/answer leakage and ordinal public names."""
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
        "name": "overlap_precedence",
        "allowed": ["lower_wins", "upper_wins"],
        "default": "lower_wins",
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
        "overlap_precedence",
        "lower_wins",
        "upper_wins",
        "query_answers",
        '"seed"',
        "program_sha256",
    )
    for path in public_paths:
        raw = path.read_bytes()
        data = json.loads(raw)
        assert raw == public_challenge_bytes(data)
        assert path.name == f"challenge-{public_challenge_id(data)}.json"
        text = raw.decode("utf-8")
        assert not any(token in text for token in forbidden)
        assert all(set(pair) == {"input"} for pair in data["test"])

    for setting in ("lower_wins", "upper_wins"):
        rule_path = out / "private" / "rules" / f"{setting}.rkt"
        assert rule_path.read_text(encoding="utf-8") == p.materialize_rule(
            setting, root=ROOT
        )

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)
