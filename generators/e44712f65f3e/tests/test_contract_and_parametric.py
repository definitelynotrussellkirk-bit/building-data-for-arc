from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "e44712f65f3e"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required source: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return _load(HOME / "generator.py", "test_e447_base")


@pytest.fixture(scope="module")
def proto():
    return _load(PARAMETRIC / "prototype.py", "test_e447_parametric")


def _canonical_row():
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(TASK_ID)


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_contract_rejects_unknown_invalid_and_coercive_overrides(base):
    bad = (
        {"unknown_axis": 1},
        {"texture": "warm"},
        {"frame_size": True},
        {"frame_size": "4"},
        {"frame_size": 9},
        {"outer_color": 0},
        {"inner_color": "3"},
        {"outer_color": 5, "inner_color": 5},
    )
    for overrides in bad:
        with pytest.raises((TypeError, ValueError)):
            base.generate(1, 0, **overrides)
    # A globally lawful size stays lawful even in a different difficulty band.
    grid = base.generate(
        1, 0, difficulty="hard", frame_size=3, outer_color=2, inner_color=7
    )
    assert base.self_check(grid) == []
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert max(r for r, _ in nonzero) - min(r for r, _ in nonzero) + 1 == 3


def test_base_self_check_accepts_all_canonical_inputs_and_rejects_impostors(base):
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert base.self_check(pair["input"]) == []
    one_color = [[0] * 10 for _ in range(10)]
    for r in range(3, 6):
        for c in range(3, 6):
            one_color[r][c] = 4
    errors = base.self_check(one_color)
    assert errors
    assert any("two nonzero colors" in error for error in errors)
    broken_ring = copy.deepcopy(row["train"][0]["input"])
    broken_ring[3][3] = 7
    assert base.self_check(broken_ring)


def test_default_program_is_byte_exact_and_python_matches_canonical(proto):
    row = _canonical_row()
    canonical = row["program_solution"]
    assert proto.program({"placement": "centered"}) == canonical
    alternate = proto.program({"placement": "nearest_edge"})
    assert alternate != canonical
    assert "top-gap" in alternate and "right-gap" in alternate
    for pair in row["train"] + row["test"]:
        assert proto.transform(pair["input"], {"placement": "centered"}) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_teaching_and_30_by_30_query(proto, demos):
    episodes = [
        proto.generate(17, {"placement": setting}, demos=demos, queries=4)
        for setting in ("centered", "nearest_edge")
    ]
    assert _all_inputs(episodes[0]) == _all_inputs(episodes[1])
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = _all_inputs(episode)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert (len(inputs[-1]), len(inputs[-1][0])) == (30, 30)
        assert proto.certify(episode)["survivors"] == [episode["settings"]]
    assert all(
        a["output"] != b["output"]
        for a, b in zip(episodes[0]["train"], episodes[1]["train"])
    )


def test_protected_racket_matches_python_labels_for_both_settings(proto):
    with RacketBridge(timeout=30) as bridge:
        for setting in ("centered", "nearest_edge"):
            episode = proto.generate(23, {"placement": setting}, demos=6, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(
                    episode["program_solution"], pair["input"], bridge=bridge
                ) == pair["output"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": True, "queries": 4},
        {"demos": 2, "queries": 0},
        {"demos": 2, "queries": 5},
    ],
)
def test_invalid_counts_and_settings_fail_closed(proto, kwargs):
    with pytest.raises(ValueError):
        proto.generate(0, {"placement": "centered"}, **kwargs)
    for settings in (
        {},
        {"placement": "other"},
        {"placement": True},
        {"placement": "centered", "extra": 1},
    ):
        with pytest.raises(ValueError):
            proto.program(settings)


def test_public_projection_and_first_query_are_private_data_independent(proto):
    one = proto.generate(31, {"placement": "nearest_edge"}, demos=2, queries=1)
    four = proto.generate(31, {"placement": "nearest_edge"}, demos=6, queries=4)
    assert one["test"] == four["test"][:1]
    visible = json.loads(public_challenge_bytes(four))
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    changed = copy.deepcopy(four)
    changed["settings"] = {"placement": "centered"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(four)


def _component_bboxes(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    }
    bboxes = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = set()
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        bboxes.append((min(rows), min(cols), max(rows), max(cols)))
    return sorted(bboxes)


def test_sampler_varies_geometry_includes_multiple_frames_and_edge_ties(base, proto):
    geometry_by_slot = [set() for _ in range(10)]
    saw_multiple = False
    for seed in range(8):
        episode = proto.generate(seed, {"placement": "centered"}, demos=6, queries=4)
        for slot, pair in enumerate(episode["train"] + episode["test"]):
            assert base.self_check(pair["input"]) == []
            bboxes = _component_bboxes(pair["input"])
            geometry_by_slot[slot].add(tuple(bboxes))
            saw_multiple |= len(bboxes) > 1

    # Seed must alter geometry, not only colors, on most teaching/query profiles.
    assert sum(len(geometries) > 1 for geometries in geometry_by_slot) >= 8
    assert saw_multiple

    episode = proto.generate(17, {"placement": "nearest_edge"}, demos=6, queries=4)
    selected_edges = set()
    tied_frames = 0
    for pair in episode["train"] + episode["test"]:
        height, width = len(pair["input"]), len(pair["input"][0])
        for r0, c0, r1, c1 in _component_bboxes(pair["input"]):
            gaps = (r0, height - 1 - r1, c0, width - 1 - c1)
            minimum = min(gaps)
            selected_edges.add(min(range(4), key=lambda index: (gaps[index], index)))
            tied_frames += sum(gap == minimum for gap in gaps) > 1
    assert selected_edges == {0, 1, 2, 3}
    assert tied_frames >= 2

