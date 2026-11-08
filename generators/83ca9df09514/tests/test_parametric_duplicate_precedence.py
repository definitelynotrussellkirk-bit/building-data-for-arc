"""Focused checks for the proposed duplicate-key precedence prototype.

The selected production generator and canonical authority remain untouched.  The
prototype varies only which conflicting sparse key aligned to one template color
wins: the canonical rightmost key or an alternate leftmost key.
"""
from __future__ import annotations

from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "83ca9df09514"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "duplicate-precedence prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_duplicate_precedence_83ca9df09514", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def conflict_witness() -> list[list[int]]:
    """Literal input whose two keys for template color 1 disagree."""
    return [
        [1, 2, 1, 2, 1, 2],
        [0, 0, 0, 0, 0, 0],
        [3, 4, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]


def test_default_rule_is_exact_canonical_and_variant_is_guarded() -> None:
    """Catches default drift, broad source replacement, and unbounded settings."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    right = p.materialize_rule(root=ROOT)
    left = p.materialize_rule("leftmost_wins", root=ROOT)

    assert right == canonical
    assert left != canonical
    assert p.rule_setting(right, root=ROOT) == "rightmost_wins"
    assert p.rule_setting(left, root=ROOT) == "leftmost_wins"

    with pytest.raises(ValueError, match="duplicate_precedence"):
        p.materialize_rule("last_nonzero_wins", root=ROOT)
    with pytest.raises(ValueError, match="duplicate_precedence"):
        p.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(root=ROOT, source=canonical + "\n")
    with pytest.raises(ValueError, match="recognized"):
        p.rule_setting(left + "\n", root=ROOT)


def test_racket_executes_both_settings_and_default_replays_canonical() -> None:
    """Catches a Python-only oracle, reversed labels, and canonical incompatibility."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    expected_right = [
        [1, 2, 1, 2, 1, 2],
        [0, 0, 0, 0, 0, 0],
        [5, 4, 5, 4, 5, 4],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    expected_left = [
        [1, 2, 1, 2, 1, 2],
        [0, 0, 0, 0, 0, 0],
        [3, 4, 3, 4, 3, 4],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]

    with RacketBridge(max_calls_before_restart=64) as bridge:
        actual_right = p.execute_rule(
            p.materialize_rule("rightmost_wins", root=ROOT),
            conflict_witness(),
            bridge=bridge,
            root=ROOT,
        )
        actual_left = p.execute_rule(
            p.materialize_rule("leftmost_wins", root=ROOT),
            conflict_witness(),
            bridge=bridge,
            root=ROOT,
        )
        assert actual_right == expected_right
        assert actual_left == expected_left

        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        replayed = p.execute_rule_many(
            p.materialize_rule(root=ROOT),
            [pair["input"] for pair in pairs],
            bridge=bridge,
            root=ROOT,
        )
        assert replayed == [pair["output"] for pair in pairs]


def _visible_inputs(public: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in public["train"] + public["test"]]


def _fingerprint(grid: list[list[int]]) -> str:
    import json

    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def test_seed_and_count_validation_are_strict() -> None:
    """Catches bool/float coercion, negative seeds, and unbounded lesson sizes."""
    p = prototype()
    assert p.parameter_for_seed(0) == {"duplicate_precedence": "rightmost_wins"}
    assert p.parameter_for_seed(1) == {"duplicate_precedence": "leftmost_wins"}
    assert p.parameter_for_seed(2) == {"duplicate_precedence": "rightmost_wins"}

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


def test_paired_seeds_share_distinct_conflict_inputs() -> None:
    """Catches parameter-dependent sampling, duplicate queries, and inert conflicts."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    inputs_right = p.episode_inputs(0, demo_count=2, query_count=4, root=ROOT)
    inputs_left = p.episode_inputs(1, demo_count=2, query_count=4, root=ROOT)
    assert inputs_right == inputs_left
    assert len(inputs_right) == 6
    assert len({_fingerprint(grid) for grid in inputs_right}) == 6

    with RacketBridge(max_calls_before_restart=128) as bridge:
        right = p.execute_rule_many(
            p.materialize_rule("rightmost_wins", root=ROOT),
            inputs_right,
            bridge=bridge,
            root=ROOT,
        )
        left = p.execute_rule_many(
            p.materialize_rule("leftmost_wins", root=ROOT),
            inputs_right,
            bridge=bridge,
            root=ROOT,
        )
    assert [a != b for a, b in zip(right, left, strict=True)] == [True] * 6


def test_episode_setting_is_fixed_identifiable_and_has_four_distinct_queries() -> None:
    """Catches per-pair resampling, weak demos, leaked answers, and query cloning."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    episodes = {}
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed, selected, rival in (
            (0, "rightmost_wins", "leftmost_wins"),
            (1, "leftmost_wins", "rightmost_wins"),
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
            assert private["parameter"] == {"duplicate_precedence": selected}
            assert private["demo_count"] == 2
            assert private["query_count"] == 4
            assert len(public["train"]) == 2
            assert len(public["test"]) == 4
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert len(private["query_answers"]) == 4
            assert len({_fingerprint(grid) for grid in _visible_inputs(public)}) == 6

            selected_check = private["rival_checks"][selected]
            rival_check = private["rival_checks"][rival]
            assert selected_check["matches_all_demonstrations"] is True
            assert selected_check["demonstration_disagreements"] == []
            assert selected_check["query_disagreements"] == []
            assert rival_check["matches_all_demonstrations"] is False
            assert rival_check["demonstration_disagreements"] == [0, 1]
            assert rival_check["query_disagreements"] == [0, 1, 2, 3]
            assert private["surviving_settings_from_demonstrations"] == [selected]
            episodes[seed] = (public, private)

    assert _visible_inputs(episodes[0][0]) == _visible_inputs(episodes[1][0])
    assert [pair["output"] for pair in episodes[0][0]["train"]] != [
        pair["output"] for pair in episodes[1][0]["train"]
    ]
    assert episodes[0][1]["query_answers"] != episodes[1][1]["query_answers"]


def test_evidence_writer_uses_visible_only_public_ids_and_hides_private_fields(
    tmp_path: Path,
) -> None:
    """Catches private setting/seed/answers leakage and ordinal public filenames."""
    import json

    from reviewer_support import public_challenge_bytes, public_challenge_id

    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[1, 0],
        demo_count=2,
        query_count=4,
        root=ROOT,
    )

    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"] == {
        "name": "duplicate_precedence",
        "allowed": ["rightmost_wins", "leftmost_wins"],
        "default": "rightmost_wins",
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["demo_count"] == 2
    assert manifest["query_count"] == 4
    assert len(manifest["episodes"]) == 2
    assert [row["public_id"] for row in manifest["episodes"]] == sorted(
        row["public_id"] for row in manifest["episodes"]
    )

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(public_paths) == 2
    assert len(private_paths) == 2
    assert len({path.name for path in public_paths}) == 2

    forbidden = (
        "duplicate_precedence",
        "rightmost_wins",
        "leftmost_wins",
        "query_answers",
        '"seed"',
        "program_sha256",
    )
    public_payloads = []
    for path in public_paths:
        raw = path.read_bytes()
        data = json.loads(raw)
        public_payloads.append(data)
        assert raw == public_challenge_bytes(data)
        assert path.name == f"challenge-{public_challenge_id(data)}.json"
        text = raw.decode("utf-8")
        assert not any(token in text for token in forbidden)
        assert all(set(pair) == {"input", "output"} for pair in data["train"])
        assert all(set(pair) == {"input"} for pair in data["test"])

    assert _visible_inputs(public_payloads[0]) == _visible_inputs(public_payloads[1])
    assert [pair["output"] for pair in public_payloads[0]["train"]] != [
        pair["output"] for pair in public_payloads[1]["train"]
    ]

    for setting in ("rightmost_wins", "leftmost_wins"):
        rule_path = out / "private" / "rules" / f"{setting}.rkt"
        assert rule_path.read_text(encoding="utf-8") == p.materialize_rule(
            setting, root=ROOT
        )

    canonical_check = json.loads(
        (out / "private" / "canonical-default-check.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(canonical_check) == 10
    assert {(row["variant"], row["split"], row["pair_index"]) for row in canonical_check} == {
        (0, "train", 0), (0, "train", 1), (0, "train", 2),
        (0, "train", 3), (0, "test", 0),
        (1, "train", 0), (1, "train", 1), (1, "train", 2),
        (1, "train", 3), (1, "train", 4),
    }
    assert all(row["matched"] is True for row in canonical_check)

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)
    with pytest.raises(ValueError, match="distinct"):
        p.write_evidence(tmp_path / "duplicate", seeds=[0, 0], root=ROOT)
