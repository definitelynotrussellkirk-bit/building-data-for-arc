"""Focused tests for the proposed gated-XOR episode parameters.

These tests exercise only the separate task-local prototype. They do not alter
or approve the selected production generator or canonical Racket authority.
"""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path
import re
import shutil

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b38782448e7b"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_SETTINGS = (
    ("different", "overwrite"),
    ("different", "preserve"),
    ("same", "overwrite"),
    ("same", "preserve"),
)


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "gated-XOR parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("b38782448e7b_parametric", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    """Share one protected Racket process; startup security checks are expensive."""
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=1024) as instance:
        yield instance


def test_default_program_is_exact_canonical_and_settings_are_bounded():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.SETTINGS == EXPECTED_SETTINGS
    assert p.program_for(root=ROOT) == canonical
    assert p.program_for("different", "overwrite", root=ROOT) == canonical
    assert p.program_for("different", "preserve", root=ROOT) != canonical
    assert p.program_for("same", "overwrite", root=ROOT) != canonical
    assert p.program_for("same", "preserve", root=ROOT) != canonical

    for invalid in ("equal", "", 1, True, None):
        with pytest.raises(ValueError, match="gate_mode"):
            p.program_for(invalid, "overwrite", root=ROOT)
    for invalid in ("paint", "", 1, True, None):
        with pytest.raises(ValueError, match="third_color_mode"):
            p.program_for("different", invalid, root=ROOT)


def test_all_four_programs_execute_in_racket_and_preserve_the_intended_cells(bridge):
    p = prototype()

    grid = p.prototype_input(11, 0, root=ROOT)
    generator, _, _ = p.load_base_generator(root=ROOT)
    analysis = generator._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["markers"] and analysis["decoys"]

    outputs = {
        setting: p.execute(bridge, p.program_for(*setting, root=ROOT), grid)
        for setting in EXPECTED_SETTINGS
    }

    # Every declared setting changes this shared input, so a demonstration can
    # distinguish all four without relying on hidden metadata.
    assert len({p.grid_sha256(output) for output in outputs.values()}) == 4

    marker_col = analysis["markers"][0]
    marker = grid[0][marker_col]
    bg = analysis["bg"]
    assert grid[1][marker_col] not in (bg, marker)  # explicit third-colour witness
    assert outputs[("different", "overwrite")][1][marker_col] == marker
    assert outputs[("different", "preserve")][1][marker_col] == grid[1][marker_col]
    assert outputs[("different", "preserve")][2][marker_col] == bg
    assert outputs[("different", "preserve")][3][marker_col] == marker

    decoy_col = analysis["decoys"][0]
    decoy = grid[0][decoy_col]
    assert grid[2][decoy_col] not in (bg, decoy)
    assert outputs[("same", "overwrite")][2][decoy_col] == decoy
    assert outputs[("same", "preserve")][2][decoy_col] == grid[2][decoy_col]
    assert outputs[("same", "preserve")][1][decoy_col] == bg
    assert outputs[("same", "preserve")][3][decoy_col] == decoy


def test_default_program_replays_every_canonical_labeled_pair(bridge):
    p = prototype()

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    for pair in pairs:
        assert p.execute(bridge, p.program_for(root=ROOT), pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,expected",
    [
        (0, ("different", "overwrite")),
        (1, ("different", "preserve")),
        (2, ("same", "overwrite")),
        (3, ("same", "preserve")),
        (8, ("different", "overwrite")),
    ],
)
def test_episode_selects_one_setting_and_three_demos_identify_four_queries(seed, expected, bridge):
    p = prototype()

    public, private = p.generate_episode(seed, bridge, root=ROOT)
    public_again, private_again = p.generate_episode(seed, bridge, root=ROOT)

    assert public == public_again
    assert private == private_again
    assert private["parameter"] == {
        "gate_mode": expected[0],
        "third_color_mode": expected[1],
    }
    assert private["selection_scope"] == "once_per_episode"
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(private["query_answers"]) == 4
    assert len(set(private["input_sha256"])) == 7

    selected_key = p.setting_key(expected)
    assert set(private["rival_checks"]) == {p.setting_key(s) for s in EXPECTED_SETTINGS}
    assert private["rival_checks"][selected_key]["matches_all_demonstrations"] is True
    for key, check in private["rival_checks"].items():
        if key == selected_key:
            continue
        assert check["matches_all_demonstrations"] is False
        assert check["distinguishing_demo_indices"] == [0, 1, 2]
        assert check["query_diff_indices"] == [0, 1, 2, 3]


def test_episode_validation_fails_closed_for_bad_counts_seeds_and_settings(bridge):
    p = prototype()

    for kwargs in (
            {"demonstration_count": 0},
            {"query_count": 0},
            {"demonstration_count": True},
            {"query_count": 1.0},
            {"demonstration_count": 17, "query_count": 16},
    ):
        with pytest.raises(ValueError):
            p.generate_episode(0, bridge, root=ROOT, **kwargs)
    for seed in (-1, True, 1.0, "1"):
        with pytest.raises(ValueError, match="seed"):
            p.generate_episode(seed, bridge, root=ROOT)
    with pytest.raises(ValueError, match="setting"):
        p.generate_episode(0, bridge, setting=("different", "paint"), root=ROOT)


def test_public_batch_uses_only_visible_bytes_and_rejects_duplicates(tmp_path, bridge):
    p = prototype()

    public0, private0 = p.generate_episode(0, bridge, root=ROOT)
    public1, _ = p.generate_episode(1, bridge, root=ROOT)

    rows = p.write_public_batch([public1, public0], tmp_path / "public")
    assert [row["public_id"] for row in rows] == sorted(
        [public_challenge_id(public0), public_challenge_id(public1)]
    )
    for row in rows:
        path = Path(row["path"])
        payload = json.loads(path.read_text())
        assert path.name == f"challenge-{row['public_id']}.json"
        assert re.fullmatch(r"[0-9a-f]{64}", row["public_id"])
        assert path.read_bytes() == public_challenge_bytes(payload)
        text = path.read_text()
        for forbidden in (
            "gate_mode",
            "third_color_mode",
            "parameter_seed",
            "query_answers",
            "rival_checks",
            "(rule!",
        ):
            assert forbidden not in text
        assert all(set(pair) == {"input"} for pair in payload["test"])

    # Hidden metadata does not participate in the public identity.
    public0_copy = json.loads(json.dumps(public0))
    assert public_challenge_id(public0_copy) == public_challenge_id(public0)
    assert private0["parameter"] not in public0.values()
    with pytest.raises(ValueError, match="duplicate public payload"):
        p.write_public_batch([public0, public0_copy], tmp_path / "duplicate")


def test_evidence_round_trip_reexecutes_and_tampering_is_rejected(tmp_path, bridge):
    p = prototype()
    manifest = p.write_evidence(
        tmp_path,
        seeds=[0, 1, 2, 3],
        demonstration_count=3,
        query_count=4,
        root=ROOT,
        bridge=bridge,
    )
    assert manifest["status"] == p.STATUS
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["settings"] == [
        {"gate_mode": gate, "third_color_mode": third}
        for gate, third in EXPECTED_SETTINGS
    ]
    assert len(manifest["episodes"]) == 4
    assert len(list((tmp_path / "public").glob("challenge-*.json"))) == 4
    assert len(list((tmp_path / "private" / "episodes").glob("*.json"))) == 4

    receipt = p.verify_evidence(tmp_path, root=ROOT, bridge=bridge)
    assert receipt["status"] == "pass"
    assert receipt["episode_count"] == 4
    assert receipt["racket_execution_count"] >= 4 * 7 * 4
    assert receipt["canonical_pair_count"] == 6

    public_path = next((tmp_path / "public").glob("challenge-*.json"))
    public_path.write_bytes(public_path.read_bytes().replace(b"\n", b" \n", 1))
    with pytest.raises(ValueError, match="public bytes"):
        p.verify_evidence(tmp_path, root=ROOT, bridge=bridge)


def test_evidence_verifier_rejects_manifest_inventory_tampering(tmp_path, bridge):
    """Dropping, duplicating, redirecting, or relabeling an episode must fail closed."""
    p = prototype()
    pristine = tmp_path / "pristine"
    p.write_evidence(
        pristine,
        seeds=[0],
        demonstration_count=1,
        query_count=1,
        root=ROOT,
        bridge=bridge,
    )

    def load_manifest(evidence_dir):
        path = evidence_dir / "manifest.json"
        return path, json.loads(path.read_text())

    def store_manifest(path, manifest):
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    omitted = tmp_path / "omitted"
    shutil.copytree(pristine, omitted)
    manifest_path, manifest = load_manifest(omitted)
    manifest["episodes"] = []
    store_manifest(manifest_path, manifest)
    with pytest.raises(ValueError, match="evidence manifest episode inventory"):
        p.verify_evidence(omitted, root=ROOT, bridge=bridge)

    duplicated = tmp_path / "duplicated"
    shutil.copytree(pristine, duplicated)
    manifest_path, manifest = load_manifest(duplicated)
    manifest["episodes"].append(dict(manifest["episodes"][0]))
    store_manifest(manifest_path, manifest)
    with pytest.raises(ValueError, match="evidence manifest episode inventory"):
        p.verify_evidence(duplicated, root=ROOT, bridge=bridge)

    redirected = tmp_path / "redirected"
    shutil.copytree(pristine, redirected)
    manifest_path, manifest = load_manifest(redirected)
    public_name = Path(manifest["episodes"][0]["public_path"]).name
    outside_public = tmp_path / "outside" / public_name
    outside_public.parent.mkdir()
    shutil.copy2(redirected / manifest["episodes"][0]["public_path"], outside_public)
    manifest["episodes"][0]["public_path"] = f"../outside/{public_name}"
    store_manifest(manifest_path, manifest)
    with pytest.raises(ValueError, match="evidence manifest episode inventory"):
        p.verify_evidence(redirected, root=ROOT, bridge=bridge)

    relabeled = tmp_path / "relabeled"
    shutil.copytree(pristine, relabeled)
    manifest_path, manifest = load_manifest(relabeled)
    manifest["episodes"][0]["parameter"] = {
        "gate_mode": "same",
        "third_color_mode": "preserve",
    }
    store_manifest(manifest_path, manifest)
    with pytest.raises(ValueError, match="evidence manifest episode metadata"):
        p.verify_evidence(relabeled, root=ROOT, bridge=bridge)
