"""Focused contract tests for the isolated cyclic rank-offset prototype."""
from __future__ import annotations

import copy
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
    load_selected_generator,
    public_challenge_bytes,
)


TASK_ID = "9a94379ed070"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"
CANONICAL_SHA256 = "57b79c20b9ed9bf5ad1ca8b4b2547a7ef6d598e6bd06677f674870bafc4a9130"
GEN, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "cyclic rank-offset prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_rank_offset_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=128) as instance:
        yield instance


def test_parameter_contract_default_authority_and_validation(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.PARAMETER_SPEC == {
        "name": "rank_offset",
        "values": (0, 1),
        "default": 0,
        "meaning": (
            "paint cyan when micro-rank equals macro-rank plus rank_offset "
            "modulo the active motif-cell count"
        ),
    }
    assert prototype.materialize_rule(0, root=ROOT) == canonical
    alternative = prototype.materialize_rule(1, root=ROOT)
    assert alternative != canonical
    assert "active-count (length tile-cells)" in alternative
    assert "(remainder (+ macro-rank 1) active-count)" in alternative

    assert prototype.parameters_for_seed(0) == {"rank_offset": 0}
    assert prototype.parameters_for_seed(1) == {"rank_offset": 1}
    assert prototype.parameters_for_seed(100) == {"rank_offset": 0}

    for bad in (-1, 2, True, 0.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="rank_offset"):
            prototype.materialize_rule(bad, root=ROOT)
    for bad in (-1, True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="seed"):
            prototype.parameters_for_seed(bad)
    for kwargs in ({"n_train": 0}, {"n_test": 13}, {"n_train": True}):
        with pytest.raises((TypeError, ValueError), match="n_(train|test)"):
            prototype.make_episode(7, root=ROOT, **kwargs)


def test_racket_python_parity_on_canonical_pairs_and_wraparound_witness(
    prototype, bridge
):
    canonical = prototype.materialize_rule(0, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair[
            "output"
        ]
        assert prototype.apply_python(pair["input"], 0, root=ROOT) == pair["output"]

    witness = GEN.generate(
        20261023,
        0,
        difficulty="hard",
        tile_size=3,
        tile_color=6,
        stripe_orientation="row",
        stripe_index=1,
        texture="sparse",
    )
    facts = GEN.semantic_observables(witness)
    positions = list(facts["motif_positions"])
    assert len(positions) > 1
    last_macro = positions[-1]
    first_micro = positions[0]
    q = facts["tile_size"]
    row = last_macro[0] * (q + 1) + first_micro[0]
    col = last_macro[1] * (q + 1) + first_micro[1]

    canonical_output = prototype.apply_python(witness, 0, root=ROOT)
    alternative_source = prototype.materialize_rule(1, root=ROOT)
    alternative_output = prototype.execute_rule(
        alternative_source, witness, bridge=bridge
    )
    assert alternative_output == prototype.apply_python(witness, 1, root=ROOT)
    assert canonical_output[row][col] == 2
    assert alternative_output[row][col] == 8
    assert alternative_output != canonical_output


@pytest.mark.parametrize("rank_offset", [0, 1])
def test_four_query_episode_is_fixed_distinct_identifiable_and_deterministic(
    prototype, bridge, rank_offset
):
    episode = prototype.make_episode(
        31,
        rank_offset=rank_offset,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    replay = prototype.make_episode(
        31,
        rank_offset=rank_offset,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert episode == replay
    assert episode["status"] == "proposed_unapproved"
    assert episode["approved"] is False
    assert episode["parameters"] == {"rank_offset": rank_offset}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert len(episode["pairs"]) == 6
    assert all(pair["rank_offset"] == rank_offset for pair in episode["pairs"])

    inputs = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["pairs"]
    ]
    assert len(inputs) == len(set(inputs)) == 6
    assert {pair["tile_size"] for pair in episode["pairs"]} == {3, 4, 5}

    analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
    assert analysis["status"] == "no_ambiguity_found"
    assert analysis["python_parity"] is True
    assert analysis["racket_replay"] is True
    assert analysis["rival_fits_demonstrations"] is False
    assert analysis["demonstrations_refuting_rival"] == 2
    assert len(analysis["queries"]) == 4
    assert all(row["rival_query_differs"] for row in analysis["queries"])


def test_public_projection_and_id_exclude_private_fields_and_query_answers(
    prototype, bridge
):
    episode = prototype.make_episode(
        41, rank_offset=1, n_train=2, n_test=4, root=ROOT, bridge=bridge
    )
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "rank_offset",
        "rule!",
        "parameters",
        "program_sha256",
        "seed",
        "output_sha256",
    ):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)

    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["parameters"] = {"rank_offset": 0}
    changed["test"][0]["output"] = [[9]]
    changed["test"][0]["output_sha256"] = "private-change"
    changed_public = prototype.public_challenge(changed)
    assert changed_public == public
    assert prototype.public_filename(changed_public) == filename
    assert public_challenge_bytes(changed_public) == public_challenge_bytes(public)


def test_materialized_tree_verifies_and_rejects_public_tampering(
    prototype, bridge, tmp_path
):
    out = tmp_path / "rank-offset-evidence"
    report = prototype.materialize(
        out,
        seed=31,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["passed"] is True
    assert report["canonical_authority_changed"] is False
    assert report["default_program_byte_identical"] is True
    expected_prototype_source = {
        "path": PROTOTYPE_PATH.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
    }
    assert report["prototype_source"] == expected_prototype_source
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["prototype_source"] == expected_prototype_source
    for private_path in sorted((out / "private").glob("rank-offset-*.json")):
        episode = json.loads(private_path.read_text())
        assert episode["prototype_source"] == expected_prototype_source
    assert report["counts"] == {
        "settings": 2,
        "episodes": 2,
        "demonstrations": 4,
        "queries": 8,
        "episode_pairs": 12,
        "distinct_input_payloads": 6,
        "racket_labels": 12,
        "canonical_pairs": 8,
        "canonical_pairs_passed": 8,
        "identifiable_episodes": 2,
        "queries_refuting_rival": 8,
    }
    assert report["setting_difference_witness"]["different_cell_count"] > 0
    assert report["setting_difference_witness"]["wraparound_verified"] is True

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    assert verification["counts"] == report["counts"]
    assert verification["prototype_source"] == expected_prototype_source

    manifest_path = out / "manifest.json"
    retained_manifest = json.loads(manifest_path.read_text())
    stale_manifest = copy.deepcopy(retained_manifest)
    stale_manifest["prototype_source"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(stale_manifest, sort_keys=True))
    with pytest.raises(ValueError, match="prototype source"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)
    manifest_path.write_text(json.dumps(retained_manifest, sort_keys=True))
    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    assert all(len(json.loads(path.read_text())["test"]) == 4 for path in public_paths)

    payload = json.loads(public_paths[0].read_text())
    payload["test"][0]["input"][0][0] = (
        payload["test"][0]["input"][0][0] + 1
    ) % 10
    public_paths[0].write_text(json.dumps(payload, sort_keys=True))
    with pytest.raises(ValueError, match="hash|public"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)


def test_verifier_rejects_symlinked_retained_files(prototype, bridge, tmp_path):
    out = tmp_path / "rank-offset-evidence"
    prototype.materialize(
        out,
        seed=31,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    retained = next((out / "public").glob("challenge-*.json"))
    external = tmp_path / "outside-evidence.json"
    external.write_bytes(retained.read_bytes())
    retained.unlink()
    retained.symlink_to(external)

    with pytest.raises(ValueError, match="symlink"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)


def test_verifier_rejects_manifest_entries_outside_inventory(
    prototype, bridge, tmp_path
):
    out = tmp_path / "rank-offset-evidence"
    prototype.materialize(
        out,
        seed=31,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    retained = out / "programs" / "rank-offset-0.rkt"
    external = tmp_path / "outside-program.rkt"
    external.write_bytes(retained.read_bytes())
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"]["0"]["program"] = "../outside-program.rkt"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))

    with pytest.raises(ValueError, match="entry path"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)


def _rewrite_retained_json(out, relative, payload):
    retained_path = out / relative
    retained_path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    )
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][relative] = hashlib.sha256(retained_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    )


def test_verifier_rejects_private_seed_drift_after_manifest_rehash(
    prototype, bridge, tmp_path
):
    out = tmp_path / "rank-offset-evidence"
    prototype.materialize(
        out, seed=31, n_train=2, n_test=4, root=ROOT, bridge=bridge
    )
    manifest = json.loads((out / "manifest.json").read_text())
    private_rel = manifest["entries"]["0"]["private_episode"]
    episode = json.loads((out / private_rel).read_text())
    episode["seed"] += 1
    _rewrite_retained_json(out, private_rel, episode)

    with pytest.raises(ValueError, match="seed"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)


def test_verifier_rejects_train_pairs_split_brain_after_manifest_rehash(
    prototype, bridge, tmp_path
):
    out = tmp_path / "rank-offset-evidence"
    prototype.materialize(
        out, seed=31, n_train=2, n_test=4, root=ROOT, bridge=bridge
    )
    manifest = json.loads((out / "manifest.json").read_text())
    private_rel = manifest["entries"]["0"]["private_episode"]
    episode = json.loads((out / private_rel).read_text())
    episode["train"][0]["output_sha256"] = "0" * 64
    _rewrite_retained_json(out, private_rel, episode)

    with pytest.raises(ValueError, match="train/test|split"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)
