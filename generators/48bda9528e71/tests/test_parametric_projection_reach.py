"""Focused tests for the proposed projection-reach rule prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir())
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id

TASK_ID = "48bda9528e71"
PROTOTYPE_PATH = HERE.parents[1] / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"prototype missing: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "test_parametric_projection_reach_subject", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _occupied(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 8}


def test_parameter_contract_and_invalid_controls():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "projection_reach"
    assert proto.SETTINGS == ("one_step", "to_boundary")
    assert proto.DEFAULT_SETTING == "one_step"
    assert proto.PUBLIC_PARENT_TASK_ID == "142ca369"

    for invalid in (None, True, 1, "edge", "one-step"):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(invalid)

    for invalid in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            proto.generate_episode(invalid)

    for keyword in ("n_train", "n_test"):
        for invalid in (True, 0, -1, 1.5, "4"):
            with pytest.raises((TypeError, ValueError)):
                proto.generate_episode(0, **{keyword: invalid})


def test_default_setting_matches_every_official_output():
    proto = _load_prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 6
    for pair in pairs:
        assert proto.apply_python(pair["input"], "one_step") == pair["output"]
    assert any(
        proto.apply_python(pair["input"], "to_boundary") != pair["output"]
        for pair in pairs
    )


def test_to_boundary_projects_each_extent_ray_and_erases_source_shape():
    proto = _load_prototype()
    grid = [
        [4, 4, 4, 4, 8],
        [4, 2, 4, 4, 8],
        [4, 4, 8, 8, 8],
        [4, 4, 8, 8, 8],
        [8, 8, 8, 8, 8],
    ]
    out = proto.apply_python(grid, "to_boundary")
    cells = _occupied(grid)
    rare = 2
    expected = [[8 for _ in row] for row in grid]
    for row in {r for r, _ in cells}:
        cols = [c for r, c in cells if r == row]
        for col in range(0, min(cols)):
            expected[row][col] = rare
        for col in range(max(cols) + 1, len(grid[0])):
            expected[row][col] = rare
    for col in {c for _, c in cells}:
        rows = [r for r, c in cells if c == col]
        for row in range(0, min(rows)):
            expected[row][col] = rare
        for row in range(max(rows) + 1, len(grid)):
            expected[row][col] = rare
    assert out == expected
    assert all(out[r][c] == 8 for r, c in cells)
    assert out != proto.apply_python(grid, "one_step")


@pytest.mark.parametrize("setting,seed", [("one_step", 10), ("to_boundary", 11)])
def test_episode_keeps_one_setting_and_exposes_separate_demo_query_counts(setting, seed):
    proto = _load_prototype()
    episode = proto.generate_episode(
        seed,
        projection_reach=setting,
        difficulty="hard",
        n_train=3,
        n_test=4,
    )
    assert episode["parameters"] == {"projection_reach": setting}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = [*episode["train"], *episode["test"]]
    assert len({_grid_hash(pair["input"]) for pair in pairs}) == 7
    rival = next(value for value in proto.SETTINGS if value != setting)
    for pair in pairs:
        assert pair["output"] == proto.apply_python(pair["input"], setting)
        assert pair["output"] != proto.apply_python(pair["input"], rival)
    assert episode["program"] == proto.program_for(setting)
    assert episode["meta"]["selection_scope"] == "once_per_episode"
    assert episode["meta"]["n_train"] == 3
    assert episode["meta"]["n_test"] == 4


def test_public_projection_and_identifier_depend_only_on_visible_bytes():
    proto = _load_prototype()
    episode = proto.generate_episode(
        17, projection_reach="to_boundary", n_train=2, n_test=4
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert proto.public_bytes(episode) == public_challenge_bytes(public)
    assert proto.public_id(episode) == public_challenge_id(public)
    assert proto.public_filename(episode) == f"challenge-{proto.public_id(episode)}.json"
    filename = proto.public_filename(episode)
    assert "to_boundary" not in filename and "17" not in filename

    private_change = deepcopy(episode)
    private_change["parameters"]["projection_reach"] = "one_step"
    private_change["meta"]["seed"] = 999
    private_change["test"][0]["output"][0][0] = (
        private_change["test"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_id(private_change) == proto.public_id(episode)

    visible_change = deepcopy(episode)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_change) != proto.public_id(episode)
