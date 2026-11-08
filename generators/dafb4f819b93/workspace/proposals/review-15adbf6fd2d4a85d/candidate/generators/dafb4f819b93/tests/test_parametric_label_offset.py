"""Focused tests for the proposed, unapproved label-offset prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_id


ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators/dafb4f819b93/workspace/parametric/prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "parametric_dafb4f819b93", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rewrite_json_and_refresh_manifest(out, path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    relative = path.relative_to(out).as_posix()
    body = path.read_bytes()
    manifest["files"][relative] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


@pytest.fixture(scope="module")
def prototype():
    assert PROTOTYPE_PATH.is_file(), "prototype.py must be retained"
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=64) as runtime:
        yield runtime


def test_prototype_file_is_retained():
    assert PROTOTYPE_PATH.is_file(), "prototype.py must be retained"


def test_default_rule_is_exact_canonical_and_offset_one_is_guarded(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(0, root=ROOT) == canonical
    assert canonical.count(prototype.CANONICAL_DECISION) == 1

    shifted = prototype.materialize_rule(1, root=ROOT)
    assert shifted != canonical
    assert shifted.count(prototype.OFFSET_ONE_DECISION) == 1
    assert (
        shifted.replace(
            prototype.OFFSET_ONE_DECISION,
            prototype.CANONICAL_DECISION,
            1,
        )
        == canonical
    )
    assert prototype.rule_setting(canonical, root=ROOT) == 0
    assert prototype.rule_setting(shifted, root=ROOT) == 1


@pytest.mark.parametrize("value", [True, False, -1, 2, 1.0, "1", None])
def test_invalid_label_offset_is_rejected(prototype, value):
    with pytest.raises(ValueError, match="label_offset"):
        prototype.materialize_rule(value, root=ROOT)


def test_default_racket_rule_reproduces_every_labeled_canonical_pair(
    prototype, bridge
):
    source = prototype.materialize_rule(0, root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    outputs = prototype.execute_rule_many(
        source,
        [pair["input"] for pair in pairs],
        bridge=bridge,
        root=ROOT,
    )
    assert outputs == [pair["output"] for pair in pairs]


def test_two_offsets_produce_distinct_racket_outputs_on_lawful_witness(
    prototype, bridge
):
    witness = prototype.distinguishing_input(root=ROOT)
    outputs = {
        offset: prototype.execute_rule(
            prototype.materialize_rule(offset, root=ROOT),
            witness,
            bridge=bridge,
            root=ROOT,
        )
        for offset in prototype.ALLOWED_LABEL_OFFSETS
    }
    assert outputs[0] != outputs[1]
    for output in outputs.values():
        assert [row[-1] for row in output] == [row[-1] for row in witness]
        assert output[-1] == witness[-1]


@pytest.mark.parametrize("seed, expected", [(1, 0), (0, 1)])
def test_episode_fixes_one_offset_and_has_distinct_three_demo_four_query_pairs(
    prototype, bridge, seed, expected
):
    episode = prototype.make_episode(
        seed,
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert episode["parameters"] == {"label_offset": expected}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    visible_inputs = [
        json.dumps(pair["input"], separators=(",", ":")) for pair in pairs
    ]
    assert len(set(visible_inputs)) == 7
    assert all(pair["label_offset"] == expected for pair in pairs)
    assert episode["ambiguities"] == []

    selected = [
        row
        for row in episode["parameter_rivals"]
        if row["label_offset"] == expected
    ]
    rival = [
        row
        for row in episode["parameter_rivals"]
        if row["label_offset"] != expected
    ]
    assert selected[0]["status"] == "selected_setting"
    assert rival[0]["status"] == "refuted_by_demonstrations"
    assert rival[0]["demonstration_mismatch_indices"] == [0, 1, 2]
    assert rival[0]["query_mismatch_indices"] == [0, 1, 2, 3]


def test_public_projection_and_identifier_ignore_private_metadata_and_query_answers(
    prototype, bridge
):
    episode = prototype.make_episode(
        1, n_train=3, n_test=4, root=ROOT, bridge=bridge
    )
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in (
        "label_offset",
        "racket",
        "parameters",
        "seed",
        "query_output",
    ):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)
    assert filename == f"challenge-{public_challenge_id(public)}.json"

    changed_private = copy.deepcopy(episode)
    changed_private["seed"] = 999
    changed_private["parameters"] = {"label_offset": 1}
    changed_private["test"][0]["output"] = [[9]]
    assert (
        prototype.public_filename(prototype.public_challenge(changed_private))
        == filename
    )

    changed_visible = copy.deepcopy(public)
    changed_visible["test"][0]["input"][0][0] = 9
    assert prototype.public_filename(changed_visible) != filename


def test_materialized_tree_is_hash_bound_sorted_and_self_verifying(
    prototype, bridge, tmp_path
):
    out = tmp_path / "label-offset-evidence"
    report = prototype.materialize(
        out,
        seeds=(1, 0),
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["demonstrations"] == 6
    assert report["counts"]["queries"] == 8
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == 4
    assert {row["parameters"]["label_offset"] for row in report["episodes"]} == {0, 1}

    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    assert len(public_ids) == len(set(public_ids))
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
        assert Path(row["public_path"]).name == prototype.public_filename(public)

    manifest = json.loads((out / "manifest.json").read_text())
    for relative, meta in manifest["files"].items():
        body = (out / relative).read_bytes()
        assert len(body) == meta["bytes"]
        assert hashlib.sha256(body).hexdigest() == meta["sha256"]

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass", verification
    with pytest.raises(FileExistsError):
        prototype.materialize(
            out,
            seeds=(1, 0),
            n_train=3,
            n_test=4,
            root=ROOT,
            bridge=bridge,
        )


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError, match="seed"):
        prototype.parameters_for_seed(seed)


@pytest.mark.parametrize(
    "n_train, n_test",
    [(0, 4), (3, 0), (17, 1), (1, 17), (True, 4), (3, 4.0)],
)
def test_invalid_pair_counts_are_rejected(prototype, n_train, n_test):
    with pytest.raises(ValueError, match="count"):
        prototype.episode_inputs(
            0, n_train=n_train, n_test=n_test, root=ROOT
        )


def test_verifier_rejects_stale_selected_generator_binding(
    prototype, bridge, tmp_path
):
    out = tmp_path / "stale-generator-binding"
    report = prototype.materialize(
        out,
        seeds=(1, 0),
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    private_path = out / report["episodes"][0]["private_path"]
    private = json.loads(private_path.read_text())
    private["train"][0]["input_provenance"]["selected_generator_sha256"] = "0" * 64
    _rewrite_json_and_refresh_manifest(out, private_path, private)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("selected generator" in error for error in verification["errors"])


def test_verifier_rejects_unmanifested_file(prototype, bridge, tmp_path):
    out = tmp_path / "unmanifested-file"
    prototype.materialize(
        out, seeds=(1, 0), n_train=3, n_test=4, root=ROOT, bridge=bridge
    )
    (out / "unexpected.json").write_text("{}\n")

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("manifest inventory" in error for error in verification["errors"])


def test_verifier_rejects_falsified_pair_hash_metadata(
    prototype, bridge, tmp_path
):
    out = tmp_path / "pair-hash-metadata"
    report = prototype.materialize(
        out, seeds=(1, 0), n_train=3, n_test=4, root=ROOT, bridge=bridge
    )
    private_path = out / report["episodes"][0]["private_path"]
    private = json.loads(private_path.read_text())
    private["train"][0]["input_sha256"] = "0" * 64
    _rewrite_json_and_refresh_manifest(out, private_path, private)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("input hash mismatch" in error for error in verification["errors"])


def test_verifier_rejects_falsified_report_counts(prototype, bridge, tmp_path):
    out = tmp_path / "report-counts"
    prototype.materialize(
        out, seeds=(1, 0), n_train=3, n_test=4, root=ROOT, bridge=bridge
    )
    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["counts"]["queries"] += 1
    _rewrite_json_and_refresh_manifest(out, report_path, report)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("report counts mismatch" in error for error in verification["errors"])


def test_verifier_rejects_falsified_distinguishing_witness(
    prototype, bridge, tmp_path
):
    out = tmp_path / "distinguishing-witness"
    report = prototype.materialize(
        out, seeds=(1, 0), n_train=3, n_test=4, root=ROOT, bridge=bridge
    )
    witness_path = out / report["distinguishing_witness"]
    witness = json.loads(witness_path.read_text())
    witness["outputs"]["1"][0][0] = (witness["outputs"]["1"][0][0] + 1) % 10
    witness["output_sha256"]["1"] = hashlib.sha256(
        json.dumps(
            witness["outputs"]["1"], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    _rewrite_json_and_refresh_manifest(out, witness_path, witness)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any(
        "distinguishing witness mismatch" in error
        for error in verification["errors"]
    )
