"""Behavioral contract for the proposed border-policy parametric prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "36275402c6b2"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "border-policy prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_border_policy_36275402c6b2", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _embed_crop(crop: list[list[int]]) -> list[list[int]]:
    """Embed one hand-checked 4x5 crop plus two exterior legend pairs."""
    grid = [[0 for _ in range(11)] for _ in range(9)]
    grid[0][0:2] = [2, 3]
    grid[8][8:10] = [6, 4]
    for row, values in enumerate(crop, start=2):
        grid[row][3:8] = values
    return grid


SIDE_WITNESSES = {
    "top": {
        "input": _embed_crop(
            [
                [8, 8, 3, 8, 8],
                [8, 3, 4, 3, 8],
                [8, 4, 3, 4, 8],
                [8, 8, 8, 8, 8],
            ]
        ),
        "recolour": [
            [8, 8, 2, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 8],
            [8, 8, 8, 8, 8],
        ],
        "preserve": [
            [8, 8, 3, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 8],
            [8, 8, 8, 8, 8],
        ],
    },
    "bottom": {
        "input": _embed_crop(
            [
                [8, 8, 8, 8, 8],
                [8, 3, 4, 3, 8],
                [8, 4, 3, 4, 8],
                [8, 8, 3, 8, 8],
            ]
        ),
        "recolour": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 8],
            [8, 8, 2, 8, 8],
        ],
        "preserve": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 8],
            [8, 8, 3, 8, 8],
        ],
    },
    "left": {
        "input": _embed_crop(
            [
                [8, 8, 8, 8, 8],
                [8, 3, 4, 3, 8],
                [3, 4, 3, 4, 8],
                [8, 8, 8, 8, 8],
            ]
        ),
        "recolour": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [2, 6, 2, 6, 8],
            [8, 8, 8, 8, 8],
        ],
        "preserve": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [3, 6, 2, 6, 8],
            [8, 8, 8, 8, 8],
        ],
    },
    "right": {
        "input": _embed_crop(
            [
                [8, 8, 8, 8, 8],
                [8, 3, 4, 3, 8],
                [8, 4, 3, 4, 3],
                [8, 8, 8, 8, 8],
            ]
        ),
        "recolour": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 2],
            [8, 8, 8, 8, 8],
        ],
        "preserve": [
            [8, 8, 8, 8, 8],
            [8, 2, 6, 2, 8],
            [8, 6, 2, 6, 3],
            [8, 8, 8, 8, 8],
        ],
    },
}


def test_default_is_exact_canonical_and_variant_is_one_guarded_rule_change() -> None:
    """Catches canonical drift, swapped defaults, and broad source rewriting."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    default = p.materialize_rule(root=ROOT)
    preserve = p.materialize_rule("preserve", root=ROOT)

    assert default == canonical
    assert preserve != canonical
    assert p.rule_setting(default, root=ROOT) == "recolour"
    assert p.rule_setting(preserve, root=ROOT) == "preserve"
    assert default.count(p.CANONICAL_BRANCH) == 1
    assert preserve.count(p.PRESERVE_BRANCH) == 1
    assert p.CANONICAL_BRANCH not in preserve

    with pytest.raises(ValueError, match="border_policy"):
        p.materialize_rule("frame_only", root=ROOT)
    with pytest.raises(ValueError, match="border_policy"):
        p.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(root=ROOT, source=canonical + "\n")


def test_racket_executes_both_policies_on_all_four_crop_sides() -> None:
    """Catches wrong border predicates and Python-only answer mirrors."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    grids = [row["input"] for row in SIDE_WITNESSES.values()]
    with RacketBridge() as bridge:
        recoloured = p.execute_rule_many(
            p.materialize_rule("recolour", root=ROOT), grids, bridge=bridge, root=ROOT
        )
        preserved = p.execute_rule_many(
            p.materialize_rule("preserve", root=ROOT), grids, bridge=bridge, root=ROOT
        )

    assert recoloured == [row["recolour"] for row in SIDE_WITNESSES.values()]
    assert preserved == [row["preserve"] for row in SIDE_WITNESSES.values()]


def test_canonical_default_replays_every_labeled_canonical_pair() -> None:
    """Catches a variant implementation that no longer preserves canonical authority."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    with RacketBridge() as bridge:
        actual = p.execute_rule_many(
            p.materialize_rule("recolour", root=ROOT),
            [pair["input"] for pair in pairs],
            bridge=bridge,
            root=ROOT,
        )
    assert actual == [pair["output"] for pair in pairs]


def test_signed_seed_contract_and_paired_inputs_are_preserved() -> None:
    """Catches nonnegative-only validation and setting-dependent input sampling."""
    p = prototype()

    assert p.parameter_for_seed(-2) == {"border_policy": "recolour"}
    assert p.parameter_for_seed(-1) == {"border_policy": "preserve"}
    assert p.parameter_for_seed(0) == {"border_policy": "recolour"}
    assert p.parameter_for_seed(1) == {"border_policy": "preserve"}
    assert p.episode_inputs(-2, root=ROOT) == p.episode_inputs(-1, root=ROOT)
    assert p.episode_inputs(0, root=ROOT) == p.episode_inputs(1, root=ROOT)

    for invalid in (True, 1.0, "1", None, -(2**63) - 1, 2**63):
        with pytest.raises(ValueError, match="seed"):
            p.parameter_for_seed(invalid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demo_count": 0},
        {"demo_count": 9},
        {"demo_count": True},
        {"query_count": 0},
        {"query_count": 9},
        {"query_count": 4.0},
    ],
)
def test_episode_counts_are_independent_and_strict(kwargs: dict[str, object]) -> None:
    """Catches coercion, zero queries, and unbounded evidence generation."""
    p = prototype()
    with pytest.raises(ValueError, match=next(iter(kwargs))):
        p.episode_inputs(0, root=ROOT, **kwargs)


def test_episode_setting_is_fixed_identifiable_and_queries_are_distinct() -> None:
    """Catches per-pair resampling, duplicate inputs, and underidentified demos."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    with RacketBridge(max_calls_before_restart=128) as bridge:
        recolour_public, recolour_private = p.generate_episode(0, bridge=bridge, root=ROOT)
        preserve_public, preserve_private = p.generate_episode(1, bridge=bridge, root=ROOT)

    assert recolour_private["parameter"] == {"border_policy": "recolour"}
    assert preserve_private["parameter"] == {"border_policy": "preserve"}
    assert recolour_private["demo_count"] == preserve_private["demo_count"] == 3
    assert recolour_private["query_count"] == preserve_private["query_count"] == 4
    assert len(recolour_public["train"]) == len(preserve_public["train"]) == 3
    assert len(recolour_public["test"]) == len(preserve_public["test"]) == 4

    recolour_inputs = [pair["input"] for pair in recolour_public["train"] + recolour_public["test"]]
    preserve_inputs = [pair["input"] for pair in preserve_public["train"] + preserve_public["test"]]
    assert recolour_inputs == preserve_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in recolour_inputs}) == 7
    assert all(generator.SEMANTIC_WITNESSES["border_source_recoloured"](grid) for grid in recolour_inputs)

    for private, selected, rival in (
        (recolour_private, "recolour", "preserve"),
        (preserve_private, "preserve", "recolour"),
    ):
        assert private["surviving_settings_from_demonstrations"] == [selected]
        assert private["rival_checks"][selected]["matches_all_demonstrations"] is True
        assert private["rival_checks"][selected]["demonstration_disagreements"] == []
        assert private["rival_checks"][selected]["query_disagreements"] == []
        assert private["rival_checks"][rival]["matches_all_demonstrations"] is False
        assert private["rival_checks"][rival]["demonstration_disagreements"] == [0, 1, 2]
        assert private["rival_checks"][rival]["query_disagreements"] == [0, 1, 2, 3]
        assert len(private["query_answers"]) == 4


def test_evidence_writer_is_content_addressed_and_keeps_private_data_private(
    tmp_path: Path,
) -> None:
    """Catches public leakage, ordinal names, incomplete evidence, and overwrite."""
    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[1, 0, -1, -2],
        demo_count=3,
        query_count=4,
        root=ROOT,
    )

    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"] == {
        "name": "border_policy",
        "allowed": ["recolour", "preserve"],
        "default": "recolour",
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["demo_count"] == 3
    assert manifest["query_count"] == 4
    assert len(manifest["episodes"]) == 4
    public_ids = [row["public_id"] for row in manifest["episodes"]]
    assert public_ids == sorted(public_ids)

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(public_paths) == len(private_paths) == 4
    assert len({path.name for path in public_paths}) == 4

    forbidden = (
        "border_policy",
        "recolour",
        "preserve",
        "query_answers",
        '"seed"',
        "program_sha256",
        "source_sha256",
    )
    for path in public_paths:
        raw = path.read_bytes()
        data = json.loads(raw)
        assert raw == public_challenge_bytes(data)
        assert path.name == f"challenge-{public_challenge_id(data)}.json"
        assert all(set(pair) == {"input"} for pair in data["test"])
        text = raw.decode("utf-8")
        assert not any(token in text for token in forbidden)

    for setting in ("recolour", "preserve"):
        rule_path = out / "private" / "rules" / f"{setting}.rkt"
        assert rule_path.read_text(encoding="utf-8") == p.materialize_rule(
            setting, root=ROOT
        )

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)
    with pytest.raises(ValueError, match="distinct"):
        p.write_evidence(tmp_path / "duplicate", seeds=[0, 0], root=ROOT)
