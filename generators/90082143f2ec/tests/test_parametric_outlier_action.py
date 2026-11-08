"""Focused contract for the proposed 90082143f2ec outlier-action prototype."""
from __future__ import annotations

import importlib
import importlib.util
from functools import cache
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK_ID = "90082143f2ec"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "outlier-action prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_outlier_action_90082143f2ec", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rule_is_exact_canonical_and_alternate_is_guarded() -> None:
    """Catch canonical drift, broad replacements, and unbounded settings."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    restored = p.materialize_rule(root=ROOT)
    masked = p.materialize_rule("mask_zero", root=ROOT)

    assert restored == canonical
    assert masked != canonical
    assert p.rule_setting(restored, root=ROOT) == "restore_mode"
    assert p.rule_setting(masked, root=ROOT) == "mask_zero"
    assert masked.count("(if (= v (list-ref col-modes c)) v 0)") == 1
    assert masked.count("(if (= v (list-ref row-modes r)) v 0)") == 1

    with pytest.raises(ValueError, match="outlier_action"):
        p.materialize_rule("keep_noise", root=ROOT)
    with pytest.raises(ValueError, match="outlier_action"):
        p.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(root=ROOT, source=canonical + "\n")


def test_racket_executes_both_actions_and_default_replays_canonical() -> None:
    """Catch a Python-only mirror, reversed actions, or invalid alternate Racket."""
    p = prototype()
    witness = GEN.generate(314159, 0, difficulty="medium")

    with RacketBridge(max_calls_before_restart=128) as bridge:
        restored = p.execute_rule(
            p.materialize_rule("restore_mode", root=ROOT),
            witness,
            bridge=bridge,
            root=ROOT,
        )
        masked = p.execute_rule(
            p.materialize_rule("mask_zero", root=ROOT),
            witness,
            bridge=bridge,
            root=ROOT,
        )

        expected_masked = [
            [value if value == restored[r][c] else 0 for c, value in enumerate(row)]
            for r, row in enumerate(witness)
        ]
        assert restored == GEN.rule_mirror(witness)
        assert masked == expected_masked
        assert masked != restored
        assert any(value == 0 for row in masked for value in row)

        canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        assert len(canonical) == 8
        replayed = p.execute_rule_many(
            p.materialize_rule("restore_mode", root=ROOT),
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=ROOT,
        )
        assert replayed == [pair["output"] for pair in canonical]


def _fingerprint(grid) -> str:
    import json

    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def test_seed_and_count_validation_are_strict_and_paired_seeds_share_inputs() -> None:
    """Catch coercion, unbounded counts, and setting-dependent input sampling."""
    p = prototype()
    assert p.parameter_for_seed(0) == {"outlier_action": "restore_mode"}
    assert p.parameter_for_seed(1) == {"outlier_action": "mask_zero"}
    assert p.parameter_for_seed(2) == {"outlier_action": "restore_mode"}

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
        kwargs = {"demo_count": 3, "query_count": 4, name: value}
        with pytest.raises(ValueError, match=name):
            p.episode_inputs(0, root=ROOT, **kwargs)

    assert p.episode_inputs(0, root=ROOT) == p.episode_inputs(1, root=ROOT)


def test_episode_setting_is_fixed_identifiable_and_has_four_distinct_queries() -> None:
    """Catch per-pair resampling, duplicate inputs, and non-identifying demos."""
    p = prototype()

    episodes = {}
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed, selected, rival in (
            (0, "restore_mode", "mask_zero"),
            (1, "mask_zero", "restore_mode"),
        ):
            public, private = p.generate_episode(
                seed,
                demo_count=3,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            public_again, private_again = p.generate_episode(
                seed,
                demo_count=3,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            assert public == public_again
            assert private == private_again
            assert private["parameter"] == {"outlier_action": selected}
            assert private["demo_count"] == 3
            assert private["query_count"] == 4
            assert len(public["train"]) == 3
            assert len(public["test"]) == 4
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert len(private["query_answers"]) == 4

            visible_inputs = [pair["input"] for pair in public["train"] + public["test"]]
            assert len({_fingerprint(grid) for grid in visible_inputs}) == 7
            assert {
                GEN.semantic_observables(pair["input"])["orientation"]
                for pair in public["train"]
            } == {"vertical", "horizontal"}

            selected_check = private["rival_checks"][selected]
            rival_check = private["rival_checks"][rival]
            assert selected_check["matches_all_demonstrations"] is True
            assert selected_check["demonstration_disagreements"] == []
            assert selected_check["query_disagreements"] == []
            assert rival_check["matches_all_demonstrations"] is False
            assert rival_check["demonstration_disagreements"] == [0, 1, 2]
            assert rival_check["query_disagreements"] == [0, 1, 2, 3]
            assert private["surviving_settings_from_demonstrations"] == [selected]
            episodes[seed] = (public, private)

    # Consecutive seeds form a paired comparison: identical inputs/order, only
    # the episode rule and therefore visible labels differ.
    public0, _ = episodes[0]
    public1, _ = episodes[1]
    assert [pair["input"] for pair in public0["train"] + public0["test"]] == [
        pair["input"] for pair in public1["train"] + public1["test"]
    ]
    assert [pair["output"] for pair in public0["train"]] != [
        pair["output"] for pair in public1["train"]
    ]


def test_evidence_writer_uses_visible_only_sorted_public_ids_and_hides_private_fields(
    tmp_path: Path,
) -> None:
    """Catch hidden metadata leakage, ordinal names, collisions, and partial overwrite."""
    from reviewer_support import public_challenge_bytes, public_challenge_id

    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[0, 1],
        demo_count=3,
        query_count=4,
        root=ROOT,
    )

    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"] == {
        "name": "outlier_action",
        "allowed": ["restore_mode", "mask_zero"],
        "default": "restore_mode",
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["demo_count"] == 3
    assert manifest["query_count"] == 4
    assert [row["public_id"] for row in manifest["episodes"]] == sorted(
        row["public_id"] for row in manifest["episodes"]
    )

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(public_paths) == 2
    assert len(private_paths) == 2
    assert len({path.name for path in public_paths}) == 2

    forbidden = (
        "outlier_action",
        "restore_mode",
        "mask_zero",
        "query_answers",
        '"seed"',
        "program_sha256",
    )
    for path in public_paths:
        raw = path.read_bytes()
        import json

        data = json.loads(raw)
        assert raw == public_challenge_bytes(data)
        assert path.name == f"challenge-{public_challenge_id(data)}.json"
        text = raw.decode("utf-8")
        assert not any(token in text for token in forbidden)
        assert all(set(pair) == {"input"} for pair in data["test"])

    for action in ("restore_mode", "mask_zero"):
        rule_path = out / "private" / "rules" / f"{action}.rkt"
        assert rule_path.read_text(encoding="utf-8") == p.materialize_rule(
            action, root=ROOT
        )

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)
    with pytest.raises(ValueError, match="distinct"):
        p.write_evidence(tmp_path / "duplicate-seeds", seeds=[0, 0], root=ROOT)
