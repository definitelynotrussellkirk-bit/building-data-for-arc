"""Focused tests for the proposed episode-level ray-relation prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK_ID = "c5a69e7cd8c8"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "cd162c43ed682af8c42df94bcb1c099d019115b65f32e70077f02d447664267d"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "ray-relation prototype must be runnable"
    spec = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=256) as instance:
        yield instance


def _distinguishing_input() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 8, 3, 8, 0, 0],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def _rewrite_json_and_refresh_manifest(out: Path, relative: str, value) -> None:
    path = out / relative
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    body = path.read_bytes()
    manifest["files"][relative] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_default_rule_is_exact_pinned_canonical_source(prototype, bridge):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert prototype.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert prototype.DEFAULT_RAY_RELATION == "opposite_opening"
    assert prototype.materialize_rule("opposite_opening", source=canonical) == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]


def test_two_settings_paint_opposite_literal_rays(prototype, bridge):
    grid = _distinguishing_input()
    canonical = prototype.materialize_rule("opposite_opening", root=ROOT)
    through = prototype.materialize_rule("through_opening", root=ROOT)

    expected_opposite = copy.deepcopy(grid)
    expected_opposite[5][3] = 3
    expected_opposite[6][3] = 3
    expected_through = copy.deepcopy(grid)
    expected_through[0][3] = 3
    expected_through[1][3] = 3
    expected_through[2][3] = 3

    assert prototype.execute_rule(canonical, grid, bridge=bridge) == expected_opposite
    assert prototype.execute_rule(through, grid, bridge=bridge) == expected_through


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, "opposite", "through", "left"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises(ValueError, match="ray_relation"):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.parameters_for_seed(bad)


def test_two_consecutive_seeds_cover_identifiable_four_query_episodes(prototype, bridge):
    episodes = [
        prototype.make_episode(seed, n_train=3, n_test=4, root=ROOT, bridge=bridge)
        for seed in (0, 1)
    ]
    assert {row["parameters"]["ray_relation"] for row in episodes} == set(
        prototype.RAY_RELATIONS
    )
    for episode in episodes:
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["pairs"]) == 7
        inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["pairs"]
        ]
        assert len(set(inputs)) == 7
        assert all(
            pair["ray_relation"] == episode["parameters"]["ray_relation"]
            for pair in episode["pairs"]
        )
        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["status"] == "no_ambiguity_found"
        assert analysis["rival_fits_demonstrations"] is False
        assert len(analysis["queries"]) == 4
        assert all(row["rival_query_differs"] for row in analysis["queries"])


def test_shared_input_seed_isolates_parameter_effect(prototype, bridge):
    opposite = prototype.make_episode(
        0,
        input_seed=17,
        ray_relation="opposite_opening",
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    through = prototype.make_episode(
        1,
        input_seed=17,
        ray_relation="through_opening",
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert [pair["input"] for pair in opposite["pairs"]] == [
        pair["input"] for pair in through["pairs"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(opposite["pairs"], through["pairs"])
    )


def test_public_projection_and_name_ignore_private_metadata_and_query_answers(
    prototype, bridge
):
    episode = prototype.make_episode(0, n_train=3, n_test=4, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("ray_relation", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)
    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["parameters"] = {"ray_relation": "through_opening"}
    changed["test"][0]["output"] = [[9]]
    assert prototype.public_filename(prototype.public_challenge(changed)) == filename


def test_materialized_tree_is_self_verifying_and_has_four_queries_per_setting(
    prototype, bridge, tmp_path
):
    out = tmp_path / "ray-relation-evidence"
    report = prototype.materialize(
        out,
        seed=17,
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "episodes": 2,
        "demonstrations": 6,
        "queries": 8,
    }
    assert {row["parameters"]["ray_relation"] for row in report["episodes"]} == set(
        prototype.RAY_RELATIONS
    )
    assert len({row["public_id"] for row in report["episodes"]}) == 2

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    for path in public_paths:
        payload = json.loads(path.read_text())
        assert prototype.public_filename(payload) == path.name
        assert len(payload["train"]) == 3
        assert len(payload["test"]) == 4
        assert all(set(pair) == {"input"} for pair in payload["test"])


def test_public_files_are_the_exact_bytes_bound_by_their_content_ids(
    prototype, bridge, tmp_path
):
    out = tmp_path / "exact-public-bytes"
    prototype.materialize(
        out,
        seed=19,
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )

    for path in sorted((out / "public").glob("challenge-*.json")):
        payload = json.loads(path.read_text())
        expected = public_challenge_bytes(payload)
        assert path.read_bytes() == expected
        assert path.stem == f"challenge-{hashlib.sha256(expected).hexdigest()}"


def test_materialize_rejects_public_id_collisions_before_writing_files(
    prototype, bridge, tmp_path, monkeypatch
):
    out = tmp_path / "forced-public-id-collision"
    monkeypatch.setattr(
        prototype,
        "public_filename",
        lambda _public: f"challenge-{'0' * 64}.json",
    )

    with pytest.raises(ValueError, match="public ID collision"):
        prototype.materialize(
            out,
            seed=23,
            n_train=3,
            n_test=4,
            root=ROOT,
            bridge=bridge,
        )

    assert not [path for path in out.rglob("*") if path.is_file()]


def test_materialized_tree_supports_independent_nondefault_counts(
    prototype, bridge, tmp_path
):
    out = tmp_path / "nondefault-counts"
    report = prototype.materialize(
        out,
        seed=4,
        n_train=2,
        n_test=5,
        root=ROOT,
        bridge=bridge,
    )
    assert report["counts"] == {
        "episodes": 2,
        "demonstrations": 4,
        "queries": 10,
    }
    assert prototype.verify_tree(out, root=ROOT, bridge=bridge)["status"] == "pass"


def test_verify_tree_rejects_stale_prototype_source_binding(
    prototype, bridge, tmp_path
):
    out = tmp_path / "stale-source-binding"
    prototype.materialize(out, seed=8, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["prototype_source_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    body = report_path.read_bytes()
    manifest["files"]["report.json"] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("prototype source" in error for error in verification["errors"]), verification


def test_verify_tree_rejects_hidden_pairs_unrelated_to_public_episode(
    prototype, bridge, tmp_path
):
    out = tmp_path / "mismatched-hidden-pairs"
    prototype.materialize(out, seed=37, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    report = json.loads((out / "report.json").read_text())
    row = report["episodes"][0]
    private_path = out / row["private_path"]
    private = json.loads(private_path.read_text())
    relation = private["episode"]["parameters"]["ray_relation"]
    replacement = prototype.make_episode(
        101,
        input_seed=103,
        ray_relation=relation,
        n_train=3,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    replacement_analysis = prototype.analyze_episode(
        replacement, root=ROOT, bridge=bridge
    )
    private["episode"]["pairs"] = replacement["pairs"]
    private["analysis"] = replacement_analysis
    _rewrite_json_and_refresh_manifest(
        out, row["private_path"], private
    )

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any(
        "train/test do not match pairs" in error for error in verification["errors"]
    ), verification


def test_verify_tree_rejects_duplicate_episode_coverage(
    prototype, bridge, tmp_path
):
    out = tmp_path / "duplicate-episode-coverage"
    prototype.materialize(out, seed=41, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["episodes"][1] = copy.deepcopy(report["episodes"][0])
    _rewrite_json_and_refresh_manifest(out, "report.json", report)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("episode coverage" in error for error in verification["errors"]), verification


def test_verify_tree_rejects_report_paths_outside_evidence_root(
    prototype, bridge, tmp_path
):
    out = tmp_path / "escaped-report-path"
    prototype.materialize(out, seed=43, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    report = json.loads((out / "report.json").read_text())
    row = report["episodes"][0]
    original = out / row["public_path"]
    escaped = out.parent / original.name
    escaped.write_bytes(original.read_bytes())
    row["public_path"] = f"../{escaped.name}"
    _rewrite_json_and_refresh_manifest(out, "report.json", report)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any(
        "path must stay inside evidence root" in error
        for error in verification["errors"]
    ), verification


@pytest.mark.parametrize(
    ("case", "error_fragment"),
    [
        ("manifest_schema", "manifest schema"),
        ("report_schema", "report schema"),
        ("task_id", "task ID"),
        ("approved", "approval status"),
        ("prototype_status", "prototype status"),
        ("prototype_path", "prototype path"),
        ("parameters", "parameter contract"),
        ("counts", "report counts"),
        ("rule_sha256", "rule hashes"),
    ],
)
def test_verify_tree_rejects_tampered_report_contract(
    prototype, bridge, tmp_path, case, error_fragment
):
    out = tmp_path / f"tampered-report-{case}"
    prototype.materialize(out, seed=47, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    if case == "manifest_schema":
        manifest_path = out / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema"] = "wrong-manifest-schema"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    else:
        report = json.loads((out / "report.json").read_text())
        if case == "report_schema":
            report["schema"] = "wrong-report-schema"
        elif case == "task_id":
            report["task_id"] = "wrong-task"
        elif case == "approved":
            report["approved"] = True
        elif case == "prototype_status":
            report["prototype_status"] = "approved"
        elif case == "prototype_path":
            report["prototype_path"] = "elsewhere.py"
        elif case == "parameters":
            report["parameters"]["ray_relation"]["default"] = "through_opening"
        elif case == "counts":
            report["counts"] = {"episodes": 999, "demonstrations": 999, "queries": 999}
        elif case == "rule_sha256":
            report["rule_sha256"]["opposite_opening"] = "0" * 64
        else:  # pragma: no cover - parametrization is closed above
            raise AssertionError(case)
        _rewrite_json_and_refresh_manifest(out, "report.json", report)

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any(error_fragment in error for error in verification["errors"]), verification


def test_verify_tree_rejects_reformatted_public_bytes_even_with_fresh_manifest(
    prototype, bridge, tmp_path
):
    out = tmp_path / "reformatted-public-bytes"
    prototype.materialize(out, seed=29, n_train=3, n_test=4, root=ROOT, bridge=bridge)

    public_path = sorted((out / "public").glob("challenge-*.json"))[0]
    payload = json.loads(public_path.read_text())
    public_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    body = public_path.read_bytes()
    relative = public_path.relative_to(out).as_posix()
    manifest["files"][relative] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("public file bytes" in error for error in verification["errors"]), verification
