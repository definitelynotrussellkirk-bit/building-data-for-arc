"""Prototype-only tests for a fixed-per-episode projection edge mode.

These tests do not change or approve the selected canonical rule. Exact Racket
execution is retained separately under ``WORK/checks/parametric/``.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
SPEC = importlib.util.spec_from_file_location("projection_edge_mode_prototype", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)
ROOT = find_root(__file__)


def _canonical_source() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise AssertionError("selected canonical source not found")


def _axis_witness() -> list[list[int]]:
    grid = [[0] * 7 for _ in range(7)]
    for r in range(2, 5):
        for c in range(2, 5):
            grid[r][c] = 8
    grid[3][0] = 1   # horizontal projection
    grid[0][3] = 2   # vertical projection
    grid[0][0] = 3   # diagonal decoy: ignored in both settings
    return grid


def test_parameter_contract_and_default_preserve_canonical_setting():
    assert prototype.ALLOWED_EDGE_MODES == ("near", "far")
    assert prototype.DEFAULT_EDGE_MODE == "near"
    assert prototype.choose_edge_mode(18) == "near"
    assert prototype.choose_edge_mode(19) == "far"
    assert prototype.choose_edge_mode(20) == "near"


def test_near_racket_is_byte_exact_canonical_and_hash_pinned():
    near = prototype.racket_source("near", root=ROOT)
    assert near == _canonical_source()
    assert prototype.normalized_hash(near) == "7288da9bfc7e"


def test_far_racket_and_python_reverse_both_target_axes_only():
    near_source = prototype.racket_source("near", root=ROOT)
    far_source = prototype.racket_source("far", root=ROOT)
    assert far_source != near_source
    assert prototype.normalized_hash(far_source) != prototype.normalized_hash(near_source)

    grid = _axis_witness()
    near = prototype.python_transform(grid, "near")
    far = prototype.python_transform(grid, "far")
    assert near[3][2] == 1 and near[2][3] == 2
    assert far[3][4] == 1 and far[4][3] == 2
    assert near[3][4] == 8 and near[4][3] == 8
    assert far[3][2] == 8 and far[2][3] == 8
    for output in (near, far):
        assert output[3][0] == 1
        assert output[0][3] == 2
        assert output[0][0] == 3


def test_episode_uses_one_mode_and_every_demo_refutes_alternative():
    seeds = {"near": 18, "far": 19}
    for mode, seed in seeds.items():
        episode = prototype.build_episode(root=ROOT, seed=seed)
        assert episode["parameter"] == {"edge_mode": mode}
        assert [pair["sample_index"] for pair in episode["train"]] == [0, 2, 4, 6]
        assert [pair["sample_index"] for pair in episode["test"]] == [8]
        alternative = "far" if mode == "near" else "near"
        for pair in episode["train"]:
            assert pair["output"] == prototype.python_transform(pair["input"], mode)
            assert pair["output"] != prototype.python_transform(pair["input"], alternative)
        query = episode["test"][0]
        assert query["output"] == prototype.python_transform(query["input"], mode)
        assert query["output"] != prototype.python_transform(query["input"], alternative)


def test_public_challenge_hides_parameter_reference_and_query_answer():
    public = prototype.public_challenge(prototype.build_episode(root=ROOT, seed=19))
    payload = json.dumps(public, sort_keys=True)
    assert "parameter" not in public
    assert "edge_mode" not in payload
    assert "racket" not in payload.lower()
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and all("output" not in pair for pair in public["test"])


def test_retained_racket_files_equal_materialized_sources():
    for mode in prototype.ALLOWED_EDGE_MODES:
        path = prototype.rule_path(mode)
        assert path.read_text(encoding="utf-8") == prototype.racket_source(mode, root=ROOT)
