"""Focused tests for the proposed axis-mode prototype.

These tests are intentionally separate from canonical generator approval.  They
exercise a task-local research prototype whose labels are executed by Racket.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import re
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "3f26d45b9f51"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the proposed task-local axis-mode prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_axis_mode_3f26d45b9f51", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=256) as runtime:
        yield runtime


def _manual_lattice():
    """A hand-authored K=7 lattice with independent row and column gaps."""
    size = 20
    divider = 8
    grid = [[0] * size for _ in range(size)]
    for row in range(size):
        if row % 3 == 2:
            grid[row] = [divider] * size
    for col in range(size):
        if col % 3 == 2:
            for row in range(size):
                grid[row][col] = divider

    def marker(cell_row: int, cell_col: int, color: int) -> None:
        for dr in range(2):
            for dc in range(2):
                grid[3 * cell_row + dr][3 * cell_col + dc] = color

    # Color 2 is an L: horizontal endpoints (1,1)-(1,4), vertical endpoints
    # (1,1)-(4,1).  Color 3 supplies an independent horizontal line.
    for cell in ((1, 1), (1, 4), (4, 1)):
        marker(*cell, 2)
    for cell in ((5, 2), (5, 5)):
        marker(*cell, 3)
    return grid


def _coarse_cell(grid, row: int, col: int):
    return [line[3 * col : 3 * col + 2] for line in grid[3 * row : 3 * row + 2]]


def test_canonical_default_is_exact_and_all_labeled_pairs_match_real_racket(prototype, bridge):
    assert prototype.DEFAULT_AXIS_MODE == "both_axes"
    assert prototype.program_for("both_axes") == prototype.canonical_record()["program_solution"]
    assert prototype.program_sha256("both_axes") == hashlib.sha256(
        prototype.program_for("both_axes").encode()
    ).hexdigest()

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.execute_rule(
            prototype.program_for("both_axes"), pair["input"], bridge=bridge
        ) == pair["output"]


@pytest.mark.parametrize(
    "value",
    [True, False, None, 0, "both", "horizontal", "vertical", "BOTH_AXES", [], {}],
)
def test_invalid_axis_modes_fail_visibly(prototype, value):
    with pytest.raises(ValueError, match="axis_mode"):
        prototype.program_for(value)


def test_three_axis_modes_execute_distinct_hand_checked_behaviors(prototype, bridge):
    grid = _manual_lattice()
    before = copy.deepcopy(grid)
    outputs = {
        mode: prototype.execute_rule(prototype.program_for(mode), grid, bridge=bridge)
        for mode in prototype.AXIS_MODES
    }
    assert grid == before
    assert len({prototype.grid_sha256(value) for value in outputs.values()}) == 3

    both = outputs["both_axes"]
    horizontal = outputs["horizontal_only"]
    vertical = outputs["vertical_only"]

    # Horizontal gap at (1,2) is filled by both/horizontal, not vertical.
    assert _coarse_cell(both, 1, 2) == [[2, 2], [2, 2]]
    assert _coarse_cell(horizontal, 1, 2) == [[2, 2], [2, 2]]
    assert _coarse_cell(vertical, 1, 2) == [[0, 0], [0, 0]]

    # Vertical gap at (2,1) is filled by both/vertical, not horizontal.
    assert _coarse_cell(both, 2, 1) == [[2, 2], [2, 2]]
    assert _coarse_cell(horizontal, 2, 1) == [[0, 0], [0, 0]]
    assert _coarse_cell(vertical, 2, 1) == [[2, 2], [2, 2]]


@pytest.mark.parametrize("name,value", [("seed", True), ("demo_count", 0), ("query_count", 0)])
def test_episode_rejects_nonpositive_or_nonexact_integer_controls(prototype, bridge, name, value):
    kwargs = {"seed": 17, "axis_mode": "both_axes", "demo_count": 3, "query_count": 4}
    kwargs[name] = value
    with pytest.raises(ValueError, match=name):
        prototype.make_episode(bridge=bridge, **kwargs)


def test_episode_fixes_one_setting_and_four_queries_are_independently_identifiable(prototype, bridge):
    random.seed(9191)
    before = random.getstate()
    episode = prototype.make_episode(
        seed=17,
        axis_mode="horizontal_only",
        demo_count=3,
        query_count=4,
        bridge=bridge,
    )
    assert random.getstate() == before
    assert prototype.make_episode(
        seed=17,
        axis_mode="horizontal_only",
        demo_count=3,
        query_count=4,
        bridge=bridge,
    ) == episode

    assert episode["status"] == "proposed_unapproved"
    assert episode["parameters"] == {"axis_mode": "horizontal_only"}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({prototype.grid_sha256(pair["input"]) for pair in pairs}) == 7

    selected_program = prototype.program_for("horizontal_only")
    for pair in pairs:
        assert prototype.execute_rule(selected_program, pair["input"], bridge=bridge) == pair["output"]

    analysis = episode["declared_rival_analysis"]
    assert analysis["consistent_settings"] == ["horizontal_only"]
    assert set(analysis["rivals"]) == {"both_axes", "vertical_only"}
    for rival in analysis["rivals"].values():
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]


def test_public_projection_and_identifier_depend_only_on_visible_bytes(prototype, bridge):
    episode = prototype.make_episode(
        seed=23,
        axis_mode="vertical_only",
        demo_count=3,
        query_count=4,
        bridge=bridge,
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert prototype.public_id(episode) == public_challenge_id(public)
    assert prototype.public_bytes(episode) == public_challenge_bytes(public)

    private_only_change = copy.deepcopy(episode)
    private_only_change["parameters"]["axis_mode"] = "both_axes"
    private_only_change["test"][0]["output"][0][0] = (
        private_only_change["test"][0]["output"][0][0] + 1
    ) % 10
    private_only_change["seed"] = 999
    assert prototype.public_bytes(private_only_change) == prototype.public_bytes(episode)
    assert prototype.public_id(private_only_change) == prototype.public_id(episode)

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = (
        visible_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_id(visible_change) != prototype.public_id(episode)

    public["train"][0]["input"][0][0] = 9
    assert public != prototype.public_challenge(episode)


def test_evidence_writer_materializes_all_settings_with_hash_bound_private_rules(
    prototype, bridge, tmp_path
):
    out = tmp_path / "axis-mode-evidence"
    report = prototype.write_evidence(
        seed=31,
        settings=reversed(prototype.AXIS_MODES),
        demo_count=3,
        query_count=4,
        out=out,
        bridge=bridge,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 3,
        "demonstrations": 9,
        "queries": 12,
        "canonical_pairs_checked": 4,
        "declared_rival_ambiguities": 0,
    }
    assert all(row["matches"] for row in report["canonical_default_parity"])
    assert len(report["episodes"]) == 3
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )
    assert {row["axis_mode"] for row in report["episodes"]} == set(prototype.AXIS_MODES)

    public_names = []
    for row in report["episodes"]:
        private_path = out / row["private_path"]
        public_path = out / row["public_path"]
        rule_path = out / row["rule_path"]
        private = json.loads(private_path.read_text())
        public = json.loads(public_path.read_text())
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert public == prototype.public_challenge(private)
        assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == private["program_sha256"]
        assert rule_path.read_text() == private["program"]
        assert "output" not in public["test"][0]
        assert not ({"parameters", "program", "seed", "meta"} & set(public))
        assert public_path.name == f"challenge-{public_challenge_id(public)}.json"
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
        public_names.append(public_path.name)
    assert len(set(public_names)) == 3

    manifest = json.loads((out / "manifest.json").read_text())
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            seed=31,
            settings=prototype.AXIS_MODES,
            demo_count=3,
            query_count=4,
            out=out,
            bridge=bridge,
        )


def test_evidence_writer_rejects_duplicate_visible_payloads_before_creating_output(
    prototype, bridge, tmp_path, monkeypatch
):
    original = prototype.make_episode(
        seed=37,
        axis_mode="both_axes",
        demo_count=3,
        query_count=4,
        bridge=bridge,
    )

    def duplicate_episode(*, axis_mode, **_kwargs):
        private = copy.deepcopy(original)
        private["parameters"]["axis_mode"] = axis_mode
        return private

    monkeypatch.setattr(prototype, "make_episode", duplicate_episode)
    out = tmp_path / "duplicate-visible"
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype.write_evidence(
            seed=37,
            settings=("both_axes", "horizontal_only"),
            demo_count=3,
            query_count=4,
            out=out,
            bridge=bridge,
        )
    assert not out.exists()
