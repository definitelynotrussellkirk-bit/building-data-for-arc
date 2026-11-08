"""Focused tests for the task-local component-connectivity prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "a631936f7715"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
VERIFY_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "verify.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "component-connectivity prototype is missing"
    spec = importlib.util.spec_from_file_location("a631936f7715_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    assert stripped.startswith("(rule!") and stripped.endswith(")")
    return stripped[len("(rule!") : -1].strip()


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def test_parameter_is_bounded_and_default_is_exact_canonical_authority():
    proto = _load_prototype()
    assert proto.ALLOWED_CONNECTIVITIES == (4, 8)
    assert proto.DEFAULT_CONNECTIVITY == 4
    assert proto.PARAMETERS == {"component_connectivity": (4, 8)}
    assert proto.program_for(4) == _canonical_program()
    assert proto.program_for(8) != proto.program_for(4)
    assert {proto.choose_connectivity(seed) for seed in range(8)} == {4, 8}
    for invalid in (True, 0, 6, "4", None):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(invalid)


def test_default_setting_preserves_every_canonical_label():
    proto = _load_prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    assert all(proto.apply_python(pair["input"], 4) == pair["output"] for pair in pairs)


def test_each_setting_builds_a_lawful_complete_distinguishing_episode():
    proto = _load_prototype()
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    for connectivity in proto.ALLOWED_CONNECTIVITIES:
        episode = proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=4)
        assert episode["parameters"] == {"component_connectivity": connectivity}
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert episode["program"] == proto.program_for(connectivity)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        visible_inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["train"] + episode["test"]
        ]
        assert len(visible_inputs) == len(set(visible_inputs)) == 7
        assert proto.episode_errors(episode) == []
        rival = 8 if connectivity == 4 else 4
        for pair in episode["train"] + episode["test"]:
            assert generator.self_check(pair["input"]) == []
            assert proto.apply_python(pair["input"], connectivity) == pair["output"]
            assert proto.apply_python(pair["input"], rival) != pair["output"]

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        blob = json.dumps(public, sort_keys=True)
        assert "component_connectivity" not in blob
        assert "program" not in blob


def test_episode_validation_rejects_duplicate_queries_or_demo_reuse():
    proto = _load_prototype()
    episode = proto.build_episode(20261023, connectivity=4, n_train=3, n_test=4)
    episode["test"][0]["input"] = deepcopy(episode["train"][0]["input"])
    episode["test"][0]["output"] = proto.apply_python(episode["test"][0]["input"], 4)
    assert any("duplicate input" in error for error in proto.episode_errors(episode))


def test_public_identity_ignores_private_fields_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(20261023, connectivity=4, n_train=3, n_test=4)
    changed = deepcopy(episode)
    changed["seed"] = 999999
    changed["parameters"] = {"component_connectivity": 8}
    changed["program"] = "private replacement"
    for pair in changed["test"]:
        pair["output"] = [[9]]

    assert proto.public_challenge_bytes(episode) == proto.public_challenge_bytes(changed)
    assert proto.public_challenge_id(episode) == proto.public_challenge_id(changed)


def test_writer_hashes_exact_visible_bytes_sorts_ids_and_keeps_private_data_apart(tmp_path):
    proto = _load_prototype()
    episodes = [
        proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=4)
        for connectivity in proto.ALLOWED_CONNECTIVITIES
    ]
    out = tmp_path / "export"
    manifest = proto.write_batch(list(reversed(episodes)), out)

    ids = [row["public_id"] for row in manifest["episodes"]]
    assert ids == sorted(ids)
    assert manifest["counts"] == {
        "episodes": 2,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
    }
    for row in manifest["episodes"]:
        public_path = out / row["public_path"]
        raw = public_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["public_id"]
        assert public_path.name == f"{row['public_id']}.json"
        public = json.loads(raw)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])

        private = json.loads((out / row["private_episode_path"]).read_text(encoding="utf-8"))
        assert private["parameters"]["component_connectivity"] in (4, 8)
        assert all("output" in pair for pair in private["test"])

    duplicate_out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible public challenge ID"):
        proto.write_batch([episodes[0], deepcopy(episodes[0])], duplicate_out)
    assert not duplicate_out.exists()


def test_verifier_accepts_independent_counts_and_writes_four_query_visible_id_batch(tmp_path):
    report_path = tmp_path / "report.json"
    artifact_dir = tmp_path / "artifacts"
    command = [
        sys.executable,
        str(VERIFY_PATH),
        "--seed",
        "20261023",
        "--train-count",
        "3",
        "--test-count",
        "4",
        "--out",
        str(report_path),
        "--artifact-dir",
        str(artifact_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["counts"] == {
        "settings": 2,
        "train_pairs_per_setting": 3,
        "test_pairs_per_setting": 4,
        "episode_pairs": 14,
        "racket_executions": 28,
        "distinguishing_pairs": 14,
        "identifiable_queries": 8,
    }
    manifest = json.loads(
        (artifact_dir / "private" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["counts"] == {
        "episodes": 2,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
    }
    assert [row["public_id"] for row in manifest["episodes"]] == sorted(
        row["public_id"] for row in manifest["episodes"]
    )
    for row in manifest["episodes"]:
        raw = (artifact_dir / row["public_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["public_id"]


def test_retained_episode_labels_are_executed_by_each_exact_racket_program():
    proto = _load_prototype()
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for connectivity in proto.ALLOWED_CONNECTIVITIES:
            episode = proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=4)
            source = proto.program_for(connectivity)
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(_application(source, pair["input"]))
                assert actual == pair["output"]


@pytest.mark.parametrize("seed", [0, 20261023, -98765])
def test_sampler_covers_finite_support_without_replacement(seed):
    proto = _load_prototype()
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    grids = proto.build_inputs(seed, 1680)
    assert len({json.dumps(grid) for grid in grids}) == 1680
    assert grids == proto.build_inputs(seed, 1680)
    assert {json.dumps(grid) for grid in grids} == {
        json.dumps(grid) for grid in proto.build_inputs(0, 1680)
    }
    for grid in grids:
        assert all(type(cell) is int for row in grid for cell in row)
        assert generator.self_check(grid) == []
        assert proto.apply_python(grid, 4) != proto.apply_python(grid, 8)


def test_sampler_rejects_support_overflow_including_total_episode_count():
    proto = _load_prototype()
    with pytest.raises(ValueError, match="finite support"):
        proto.build_inputs(0, 1681)
    with pytest.raises(ValueError, match="finite support"):
        proto.build_episode(0, n_train=840, n_test=841)


@pytest.mark.parametrize("counts", [(2, 5), (5, 2)])
def test_asymmetric_counts_keep_unique_inputs_and_writer_contract(counts, tmp_path):
    proto = _load_prototype()
    n_train, n_test = counts
    episode = proto.build_episode(20261023, connectivity=4, n_train=n_train, n_test=n_test)
    assert episode["counts"] == {"demonstrations": n_train, "queries": n_test}
    assert proto.episode_errors(episode) == []
    destination = tmp_path / "export"
    manifest = proto.write_batch([episode], destination)
    row = manifest["episodes"][0]
    assert (destination / row["public_path"]).read_bytes() == proto.public_challenge_bytes(episode)
    with pytest.raises(FileExistsError):
        proto.write_batch([episode], destination)
