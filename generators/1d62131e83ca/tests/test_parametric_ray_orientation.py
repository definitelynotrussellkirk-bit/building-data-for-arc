from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"


def _load_module(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_prototype():
    return _load_module(PROTOTYPE_PATH, "test_parametric_1d62131e83ca")


def _fixture_grid() -> list[list[int]]:
    grid = [[0 for _ in range(8)] for _ in range(8)]
    for row in (2, 3):
        for col in (2, 3):
            grid[row][col] = 1
    for row in (3, 4):
        for col in (4, 5):
            grid[row][col] = 2
    return grid


def _grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_solve_paints_the_hand_derived_ray_orientation_cells():
    proto = _load_prototype()
    grid = _fixture_grid()

    canonical = proto.solve(grid, ray_orientation="nw_se")
    alternative = proto.solve(grid, ray_orientation="ne_sw")

    canonical_new = {
        (row, col, canonical[row][col])
        for row in range(8)
        for col in range(8)
        if canonical[row][col] != grid[row][col]
    }
    alternative_new = {
        (row, col, alternative[row][col])
        for row in range(8)
        for col in range(8)
        if alternative[row][col] != grid[row][col]
    }

    assert canonical_new == {
        (0, 0, 1),
        (1, 1, 1),
        (5, 6, 2),
        (6, 7, 2),
    }
    assert alternative_new == {
        (0, 5, 1),
        (1, 4, 1),
        (5, 3, 2),
        (6, 2, 2),
        (7, 1, 2),
    }
    assert grid == _fixture_grid(), "solve must not mutate its input"


def test_episode_keeps_one_setting_and_four_distinct_setting_sensitive_queries():
    proto = _load_prototype()

    for seed, setting in ((17, "nw_se"), (18, "ne_sw")):
        episode = proto.generate_episode(
            seed,
            difficulty="medium",
            ray_orientation=setting,
            demo_count=3,
            query_count=4,
        )
        replay = proto.generate_episode(
            seed,
            difficulty="medium",
            ray_orientation=setting,
            demo_count=3,
            query_count=4,
        )
        assert replay == episode
        assert episode["parameters"] == {"ray_orientation": setting}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4

        pairs = episode["train"] + episode["test"]
        input_hashes = [_grid_hash(pair["input"]) for pair in pairs]
        assert len(set(input_hashes)) == 7

        rival = "ne_sw" if setting == "nw_se" else "nw_se"
        for pair in pairs:
            assert proto.solve(pair["input"], ray_orientation=setting) == pair["output"]
            assert proto.solve(pair["input"], ray_orientation=rival) != pair["output"]
            assert proto.input_is_valid(pair["input"], ray_orientation=setting)
            assert proto.input_is_valid(pair["input"], ray_orientation=rival)

        if setting == proto.DEFAULT_RAY_ORIENTATION:
            for pair in pairs:
                assert proto.base_canonical_output(pair["input"]) == pair["output"]


def test_public_projection_uses_only_visible_bytes_for_opaque_identity():
    proto = _load_prototype()
    episode = proto.generate_episode(
        23,
        ray_orientation="ne_sw",
        demo_count=3,
        query_count=4,
    )
    public = proto.public_challenge(episode)

    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert proto.public_bytes(episode) == proto.public_bytes(public)
    identity = proto.public_id(episode)
    assert len(identity) == 64
    assert identity == hashlib.sha256(proto.public_bytes(episode)).hexdigest()

    private_only = copy.deepcopy(episode)
    private_only["parameters"]["ray_orientation"] = "nw_se"
    private_only["program"] = "private replacement"
    private_only["meta"]["seed"] = 999999
    private_only["test"][0]["output"] = [[9]]
    assert proto.public_id(private_only) == identity

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = (
        visible_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_change) != identity


def test_invalid_settings_counts_and_setting_specific_collisions_fail_loudly():
    proto = _load_prototype()

    with pytest.raises(ValueError, match="ray_orientation"):
        proto.solve(_fixture_grid(), ray_orientation="sideways")
    for bad in (0, -1, True, 9):
        with pytest.raises(ValueError, match="demo_count"):
            proto.generate_episode(1, demo_count=bad, query_count=4)
        with pytest.raises(ValueError, match="query_count"):
            proto.generate_episode(1, demo_count=3, query_count=bad)

    collision = [[0 for _ in range(8)] for _ in range(8)]
    for row in (4, 5):
        for col in (4, 5):
            collision[row][col] = 1
    for row in (1, 2):
        for col in (1, 2):
            collision[row][col] = 2
    assert not proto.input_is_valid(collision, ray_orientation="nw_se")
    with pytest.raises(ValueError, match="invalid"):
        proto.solve(collision, ray_orientation="nw_se")


def test_verifier_executes_every_label_and_retains_private_public_separation(tmp_path):
    verify_path = TASK_DIR / "workspace" / "parametric" / "verify.py"
    verifier = _load_module(verify_path, "verify_parametric_1d62131e83ca")

    report = verifier.build_report(base_dir=tmp_path)

    assert report["status"] == "proposed_prototype_not_selected"
    assert report["all_racket_exact"]
    assert report["all_rival_racket_python_exact"]
    assert report["all_rivals_refuted_by_every_demo"]
    assert report["all_queries_setting_sensitive"]
    assert report["canonical_default_exact"]
    assert report["all_public_challenges_masked"]
    assert report["all_public_ids_visible_only"]
    assert report["unique_input_count"] == 14
    assert {row["setting"] for row in report["settings"]} == {"nw_se", "ne_sw"}

    public_paths = []
    for row in report["settings"]:
        assert len(row["pairs"]) == 7
        assert sum(pair["split"] == "train" for pair in row["pairs"]) == 3
        assert sum(pair["split"] == "test" for pair in row["pairs"]) == 4
        assert row["all_racket_exact"]
        assert row["rival_refuted_by_every_demo"]
        assert row["rival_changes_every_query"]
        public_path = tmp_path / row["public_episode_path"]
        assert public_path.name == f"challenge-{row['public_id']}.json"
        payload = json.loads(public_path.read_text())
        assert set(payload) == {"train", "test"}
        assert all("output" in pair for pair in payload["train"])
        assert all("output" not in pair for pair in payload["test"])
        public_paths.append(row["public_episode_path"])

    assert public_paths == sorted(public_paths)
    assert (tmp_path / "evidence" / "manifest.json").is_file()


def test_bounded_adversarial_checker_retains_sampler_and_privacy_evidence(tmp_path):
    checker_path = TASK_DIR / "workspace" / "parametric" / "adversarial_check.py"
    checker = _load_module(checker_path, "adversarial_check_1d62131e83ca")
    out_path = tmp_path / "adversarial.json"

    report = checker.build_report(out_path=out_path)

    assert report["status"] == "bounded_no_finding"
    assert report["surfaces"] == [
        "sampler_count_retry_boundaries",
        "public_private_projection_identity",
    ]
    assert report["seed_sweep"]["episodes"] == 24
    assert report["seed_sweep"]["pairs"] == 168
    assert report["seed_sweep"]["globally_distinct_inputs"] > 100
    assert all(report["privacy"].values())
    assert {
        (row["setting"], row["demo_count"], row["query_count"], row["distinct_inputs"])
        for row in report["boundary_counts"]
    } == {
        ("nw_se", 1, 1, 2),
        ("nw_se", 8, 8, 16),
        ("ne_sw", 1, 1, 2),
        ("ne_sw", 8, 8, 16),
    }
    assert json.loads(out_path.read_text()) == report
