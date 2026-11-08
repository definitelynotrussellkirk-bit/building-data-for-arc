from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "08eaba8254b2"
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
    return _load(HOME / "generator.py", "test_08_base")


@pytest.fixture(scope="module")
def proto():
    return _load(PARAMETRIC / "prototype.py", "test_08_parametric")


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
        {"panel_pattern": "bogus"},
        {"grid_w": True},
        {"grid_w": 31},
        {"top_color": "3"},
        {"xor_target": 12},
    )
    for overrides in bad:
        with pytest.raises((TypeError, ValueError)):
            base.generate(1, 0, **overrides)
    # Globally lawful boundary widths stay lawful even outside the hard default band.
    for width in (3, 30):
        grid = base.generate(1, 0, difficulty="hard", grid_w=width, xor_target=3)
        assert (len(grid), len(grid[0])) == (9, width)
        assert base.self_check(grid) == []


def test_base_self_check_accepts_canonical_and_rejects_structural_impostors(base):
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert base.self_check(pair["input"]) == []
    impostor = [[0] * 3 for _ in range(9)]
    impostor[0][0] = 1
    errors = base.self_check(impostor)
    assert errors
    assert any("separator" in error or "bottom" in error for error in errors)


def test_default_program_is_byte_exact_and_variant_is_distinct(proto):
    canonical = _canonical_row()["program_solution"]
    assert proto.program({"projection": "cellwise_xor"}) == canonical
    alternate = proto.program({"projection": "largest_component_bbox"})
    assert alternate != canonical
    assert "obj-bbox" in alternate


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_teaching_and_width_30_query(proto, demos):
    episodes = [
        proto.generate(17, {"projection": setting}, demos=demos, queries=4)
        for setting in ("cellwise_xor", "largest_component_bbox")
    ]
    assert _all_inputs(episodes[0]) == _all_inputs(episodes[1])
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = _all_inputs(episode)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert (len(inputs[-1]), len(inputs[-1][0])) == (9, 30)
        assert proto.certify(episode)["survivors"] == [episode["settings"]]
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def test_protected_racket_matches_python_labels_for_both_settings(proto):
    with RacketBridge(timeout=30) as bridge:
        for setting in ("cellwise_xor", "largest_component_bbox"):
            episode = proto.generate(23, {"projection": setting}, demos=6, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]


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
        proto.generate(0, {"projection": "cellwise_xor"}, **kwargs)
    for settings in ({}, {"projection": "other"}, {"projection": True},
                     {"projection": "cellwise_xor", "extra": 1}):
        with pytest.raises(ValueError):
            proto.program(settings)


def test_public_projection_and_first_query_are_private_data_independent(proto):
    one = proto.generate(31, {"projection": "largest_component_bbox"}, demos=2, queries=1)
    four = proto.generate(31, {"projection": "largest_component_bbox"}, demos=6, queries=4)
    assert one["test"] == four["test"][:1]
    visible = json.loads(public_challenge_bytes(four))
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    changed = copy.deepcopy(four)
    changed["settings"] = {"projection": "cellwise_xor"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(four)


def test_largest_component_tie_break_uses_bbox_top_left_and_matches_racket(proto):
    width = 21
    mask = [[0] * width for _ in range(4)]
    # Component A: size 18, bbox top-left (0, 6), but its first occupied
    # cell in row-major order is (0, 20).
    component_a = {(r, 20) for r in range(4)} | {(3, c) for c in range(6, 20)}
    # Component B: size 18, bbox top-left and first cell both (0, 10).
    component_b = {(r, c) for r in range(2) for c in range(10, 19)}
    assert len(component_a) == len(component_b) == 18
    assert component_a.isdisjoint(component_b)
    for r, c in component_a | component_b:
        mask[r][c] = 1

    grid = [[0] * width for _ in range(9)]
    grid[4] = [8] * width
    for r, c in component_a | component_b:
        grid[r][c] = 2

    settings = {"projection": "largest_component_bbox"}
    expected = [
        [3 if 0 <= r <= 3 and 6 <= c <= 20 and (r in (0, 3) or c in (6, 20)) else 0
         for c in range(width)]
        for r in range(4)
    ]
    assert proto.transform(grid, settings) == expected
    with RacketBridge(timeout=30) as bridge:
        assert proto.execute_rule(proto.program(settings), grid, bridge=bridge) == expected


def _mask_components(mask):
    remaining = {
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value
    }
    components = []
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
        components.append(cells)
    return components


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)



def test_sampler_accepts_the_declared_direct_index_range(proto):
    for split in ("train", "test"):
        grid = proto.sample_input(7, split, 1000, 30)
        assert (len(grid), len(grid[0])) == (9, 30)


def test_sampler_varies_component_reasoning_and_retains_a_tie_query(base, proto):
    episode = proto.generate(17, {"projection": "cellwise_xor"}, demos=6, queries=4)
    signatures = set()
    bbox_shapes = set()
    for pair in episode["train"] + episode["test"]:
        assert base.self_check(pair["input"]) == []
        components = _mask_components(proto.xor_mask(pair["input"]))
        largest_size = max(map(len, components))
        largest = [cells for cells in components if len(cells) == largest_size]
        chosen = min(largest, key=lambda cells: _bbox(cells)[:2])
        r0, c0, r1, c1 = _bbox(chosen)
        signatures.add(tuple(sorted((r - r0, c - c0) for r, c in chosen)))
        bbox_shapes.add((r1 - r0 + 1, c1 - c0 + 1))

    # A fixed plus-sign detector or fixed 3x3 rectangle must not solve the family.
    assert len(signatures) >= 5
    assert len(bbox_shapes) >= 4

    tie_grid = episode["test"][2]["input"]
    tie_components = _mask_components(proto.xor_mask(tie_grid))
    max_size = max(map(len, tie_components))
    tied = sorted((_bbox(cells), cells) for cells in tie_components if len(cells) == max_size)
    assert len(tied) == 2
    selected_bbox = tied[0][0]
    r0, c0, r1, c1 = selected_bbox
    expected = [
        [
            3
            if r0 <= r <= r1
            and c0 <= c <= c1
            and (r in (r0, r1) or c in (c0, c1))
            else 0
            for c in range(len(tie_grid[0]))
        ]
        for r in range(4)
    ]
    settings = {"projection": "largest_component_bbox"}
    assert proto.transform(tie_grid, settings) == expected
    with RacketBridge(timeout=30) as bridge:
        assert proto.execute_rule(proto.program(settings), tie_grid, bridge=bridge) == expected

