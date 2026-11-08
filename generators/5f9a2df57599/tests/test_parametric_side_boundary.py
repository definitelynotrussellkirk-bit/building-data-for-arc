"""Focused tests for the isolated side-boundary policy prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_id,
)

TASK_ID = "5f9a2df57599"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE_PATH.is_file(), "side-boundary prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_side_boundary_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=15, startup_timeout=60) as value:
        yield value


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_policy_selection_is_episode_level_deterministic_and_strict(proto):
    assert proto.SIDE_POLICIES == ("canvas_edges", "gray_walls")
    assert proto.CANONICAL_POLICY == "canvas_edges"
    assert {proto.choose_policy(seed) for seed in range(128)} == set(proto.SIDE_POLICIES)
    for seed in range(16):
        assert proto.choose_policy(seed) == proto.choose_policy(seed)
        for explicit in proto.SIDE_POLICIES:
            assert proto.choose_policy(seed, explicit) == explicit

    for bad_seed in (True, -1, 1.5, "1"):
        with pytest.raises(ValueError):
            proto.choose_policy(bad_seed)
    for bad_policy in ("edge", "strict", 1, False, None):
        if bad_policy is None:
            continue
        with pytest.raises(ValueError):
            proto.choose_policy(0, bad_policy)


def test_materialized_programs_are_source_bound_and_change_only_side_predicates(proto):
    canonical = proto.canonical_record(root=ROOT)["program_solution"]
    canonical_normalized = " ".join(canonical.split())
    default = proto.materialize_program("canvas_edges", root=ROOT)
    strict = proto.materialize_program("gray_walls", root=ROOT)

    assert default == canonical
    assert strict != default
    assert strict.count(proto.LEFT_STRICT_ANCHOR) == 1
    assert strict.count(proto.RIGHT_STRICT_ANCHOR) == 1
    restored = strict.replace(
        proto.LEFT_STRICT_ANCHOR, proto.LEFT_CANONICAL_ANCHOR, 1
    ).replace(proto.RIGHT_STRICT_ANCHOR, proto.RIGHT_CANONICAL_ANCHOR, 1)
    assert restored == canonical_normalized
    assert proto.CANONICAL_RULE_HASH == "5b73d3931a5c"
    assert hashlib.sha256(canonical_normalized.encode()).hexdigest()[:12] == proto.CANONICAL_RULE_HASH


def test_racket_programs_match_independent_python_on_edge_and_interior_scenes(proto, bridge):
    generator, _, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    assert source_hash == proto.GENERATOR_SHA256
    profiles = ("left_n1", "right_n1", "rect_n2", "irregular_n1")
    grids = [
        generator.generate(90_000 + index, 700 + index, difficulty="medium", scene_profile=profile)
        for index, profile in enumerate(profiles)
    ]
    original = deepcopy(grids)
    outputs = {}
    for policy in proto.SIDE_POLICIES:
        program = proto.materialize_program(policy, root=ROOT)
        outputs[policy] = [proto.execute(bridge, program, grid) for grid in grids]
        assert outputs[policy] == [proto.python_apply(grid, policy) for grid in grids]

    assert outputs["canvas_edges"][0] != outputs["gray_walls"][0]
    assert outputs["canvas_edges"][1] != outputs["gray_walls"][1]
    assert outputs["canvas_edges"][2:] == outputs["gray_walls"][2:]
    assert grids == original


def test_episode_has_three_demos_four_distinct_queries_and_identifies_policy(proto, bridge):
    for seed, policy in ((17, "canvas_edges"), (18, "gray_walls")):
        episode = proto.make_episode(seed, policy=policy, bridge=bridge, root=ROOT)
        assert episode["parameters"] == {"side_boundary_policy": policy}
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len({frozen(pair["input"]) for pair in episode["test"]}) == 4
        assert episode["ambiguities"] == []
        matching = [
            row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"
        ]
        refuted = [
            row
            for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["side_boundary_policy"] for row in matching] == [policy]
        assert {row["side_boundary_policy"] for row in refuted} == set(proto.SIDE_POLICIES) - {policy}
        assert all(row["demonstration_mismatch_indices"] for row in refuted)
        assert all(
            pair["output"] == proto.python_apply(pair["input"], policy)
            for pair in episode["train"] + episode["test"]
        )


def test_public_challenge_hides_policy_and_query_answers_without_aliasing(proto, bridge):
    episode = proto.make_episode(17, policy="canvas_edges", bridge=bridge, root=ROOT)
    before = deepcopy(episode)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("side_boundary_policy", "canvas_edges", "gray_walls", "racket_source"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_visible_files_and_retains_four_private_queries(proto, tmp_path):
    out = tmp_path / "side-boundary-evidence"
    report = proto.write_evidence(
        out,
        seed_start=0,
        demo_count=3,
        query_count=4,
        root=ROOT,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 2,
        "episode_settings_exercised": 2,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "train_pairs": 6,
        "query_pairs": 8,
        "canonical_pairs_checked": 4,
        "ambiguous_parameter_rivals": 0,
    }
    assert {row["parameters"]["side_boundary_policy"] for row in report["episodes"]} == set(
        proto.SIDE_POLICIES
    )

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        private = json.loads(private_path.read_text())
        public = json.loads(public_path.read_text())
        assert public_path.name == f"{public_challenge_id(private)}.json"
        assert private_path.name == public_path.name
        assert public == proto.public_challenge(private)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])

    manifest = json.loads((out / "manifest.json").read_text())
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        proto.write_evidence(out, root=ROOT)


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("demo_count", True),
        ("demo_count", 0),
        ("demo_count", 9),
        ("query_count", True),
        ("query_count", 0),
        ("query_count", 9),
    ],
)
def test_invalid_episode_counts_fail_closed(proto, bridge, keyword, value):
    kwargs = {"demo_count": 3, "query_count": 4, keyword: value}
    with pytest.raises(ValueError):
        proto.make_episode(1, bridge=bridge, root=ROOT, **kwargs)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 8 for _ in range(7)],
        [[False] * 8 for _ in range(8)],
        [[4] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(7)] + [[0] * 7],
    ],
)
def test_python_oracle_rejects_malformed_inputs(proto, grid):
    with pytest.raises(ValueError):
        proto.python_apply(grid, "canvas_edges")
