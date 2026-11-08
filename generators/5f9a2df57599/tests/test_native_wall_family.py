"""Focused behavioral contract for the new native wall-family sampler."""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "e8cf01347e8f1013e5af75c1170767e3bac1afd1974dca142f8ff406e41672bd"


def load(name):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"native {name} has not been implemented"
    spec = importlib.util.spec_from_file_location(f"wall_native_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen(grid):
    return tuple(map(tuple, grid))


def components(grid):
    """Independent breadth-first discovery; tests do not trust private metadata."""
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0}
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells, queue = {start}, deque([start])
        while queue:
            r, c = queue.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in pending:
                    pending.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        found.append(cells)
    return found


def test_native_default_preserves_exact_program_and_returns_a_usable_episode():
    adapter = load("adapter")
    episode = adapter.generate(0)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert hashlib.sha256(adapter.program().encode()).hexdigest() == CANONICAL_SHA256
    assert episode["program_solution"] == adapter.program()
    assert adapter.normalize_settings(None) == {"side_boundary_policy": "canvas_edges"}
    assert adapter.program({"side_boundary_policy": "gray_walls"}) != adapter.program()
    json.dumps(episode, allow_nan=False)


def test_counts_select_prefixes_of_one_fixed_matched_distinct_bank():
    adapter = load("adapter")
    full = adapter.generate(17, demos=6, queries=4)
    strict = adapter.generate(17, {"side_boundary_policy": "gray_walls"}, 6, 4)
    assert [p["input"] for split in ("train", "test") for p in full[split]] == [
        p["input"] for split in ("train", "test") for p in strict[split]
    ]
    all_inputs = [frozen(p["input"]) for split in ("train", "test") for p in full[split]]
    assert len(set(all_inputs)) == 10
    for demos, queries in ((2, 1), (2, 4), (3, 1), (3, 4), (6, 1)):
        prefix = adapter.generate(17, demos=demos, queries=queries)
        assert prefix["train"] == full["train"][:demos]
        assert prefix["test"] == full["test"][:queries]
    assert any(a["output"] != b["output"] for a, b in zip(full["train"][:2], strict["train"][:2]))
    full["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, demos=6, queries=4)["train"][0]["input"][0][0] in (0, 5)


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_two_core_demos_contain_small_wall_failures_large_regions_and_boundaries(seed):
    adapter = load("adapter")
    episode = adapter.generate(seed, demos=2)
    large, irregular_selected, small_rejected = False, False, False
    missing_sides = set()
    excluded_left, accepted_right = False, False
    edge_rows = set()
    for pair in episode["train"]:
        grid, output = pair["input"], pair["output"]
        h, w = len(grid), len(grid[0])
        selected_count = 0
        assert any(value == 0 for value in grid[0])
        for cells in components(grid):
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            selected = all(output[r][c] == 4 for r, c in cells)
            selected_count += selected
            rectangle = len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)
            large |= selected and r1 - r0 >= 4 and c1 - c0 >= 4
            irregular_selected |= selected and not rectangle
            if not selected and not rectangle and len(cells) <= 4 and 0 < r0 <= r1 < h - 1:
                small_rejected = True
                sides = {
                    "top": [(r0 - 1, c) for c in range(c0, c1 + 1)],
                    "bottom": [(r1 + 1, c) for c in range(c0, c1 + 1)],
                    "left": [(r, c0 - 1) for r in range(r0, r1 + 1)] if c0 else [],
                    "right": [(r, c1 + 1) for r in range(r0, r1 + 1)] if c1 < w - 1 else [],
                }
                missing_sides.update(side for side, border in sides.items() if any(grid[r][c] == 0 for r, c in border))
            excluded_left |= c0 == c1 == 0 and r0 < r1 and 0 < r0 and r1 < h - 1 and not selected
            accepted_right |= c0 == c1 == w - 1 and r0 < r1 and selected
            if r0 == 0:
                edge_rows.add("top")
                assert not selected
            if r1 == h - 1:
                edge_rows.add("bottom")
                assert not selected
        assert selected_count >= 2
    assert large and irregular_selected and small_rejected
    assert missing_sides == {"top", "bottom", "left", "right"}
    assert excluded_left and accepted_right
    assert edge_rows == {"top", "bottom"}


def test_compact_and_substantive_30_square_inputs_are_present_and_procedural():
    adapter = load("adapter")
    first = adapter.generate(0)
    second = adapter.generate(17)
    shapes = {(len(p["input"]), len(p["input"][0])) for split in ("train", "test") for p in first[split]}
    assert (8, 8) in shapes and (30, 30) in shapes
    assert first["test"] != second["test"]
    for episode in (first, second):
        stress = next(p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30)
        grid, output = stress["input"], stress["output"]
        assert 150 <= sum(value == 5 for row in grid for value in row) <= 650
        assert sum(value == 4 for row in output for value in row) >= 100
        for r0 in (0, 15):
            for c0 in (0, 15):
                assert sum(output[r][c] == 4 for r in range(r0, r0 + 15) for c in range(c0, c0 + 15)) >= 10
        assert len(components(grid)) >= 10
        assert any(value == 0 for value in grid[0])


def test_compact_first_queries_exceed_four_shapes_and_keep_positive_negative_contrast():
    adapter = load("adapter")
    seeds = [*range(16), 17]
    inputs = []
    for seed in seeds:
        for policy in ("canvas_edges", "gray_walls"):
            pair = adapter.generate(seed, {"side_boundary_policy": policy})["test"][0]
            grid, output = pair["input"], pair["output"]
            assert len(grid) == len(grid[0]) == 8
            regions = components(grid)
            assert any(all(output[r][c] == 4 for r, c in cells) for cells in regions)
            assert any(all(output[r][c] == 0 for r, c in cells) for cells in regions)
            if policy == "canvas_edges":
                inputs.append(frozen(grid))
    assert len(set(inputs)) > 4
    assert inputs[0] != inputs[-1]


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("policy", ["canvas_edges", "gray_walls"])
def test_same_three_cell_l_shape_is_both_selected_and_rejected_by_first_two_demos(seed, policy):
    adapter = load("adapter")
    shapes = {"selected": set(), "rejected": set()}
    for pair in adapter.generate(seed, {"side_boundary_policy": policy}, demos=2)["train"]:
        grid, output = pair["input"], pair["output"]
        for cells in components(grid):
            if len(cells) != 3:
                continue
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            if (r1 - r0, c1 - c0) != (1, 1):
                continue
            if not (0 < r0 and r1 < len(grid) - 1 and 0 < c0 and c1 < len(grid[0]) - 1):
                continue
            key = "selected" if all(output[r][c] == 4 for r, c in cells) else "rejected"
            shapes[key].add(tuple(sorted((r - r0, c - c0) for r, c in cells)))
    assert shapes["selected"] & shapes["rejected"], "L shape alone must not substitute for bbox-wall facts"


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 1.0}, {"seed": "0"}, {"seed": 2**63},
    {"demos": True}, {"demos": 1}, {"demos": 7}, {"demos": 3.0},
    {"queries": False}, {"queries": 0}, {"queries": 5}, {"queries": "4"},
    {"settings": {}}, {"settings": []}, {"settings": "canvas_edges"},
    {"settings": {"side_boundary_policy": True}},
    {"settings": {"side_boundary_policy": 0}},
    {"settings": {"side_boundary_policy": "canvas_edges", "extra": 1}},
])
def test_invalid_requests_fail_before_building_an_episode(kwargs):
    adapter = load("adapter")
    request = {"seed": 0, **kwargs}
    with pytest.raises(ValueError):
        adapter.generate(**request)


def test_claims_match_protected_racket_on_core_compact_and_stress_inputs():
    from arc_repl.racket_bridge import RacketBridge

    adapter, prototype = load("adapter"), load("prototype")
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for policy in ("canvas_edges", "gray_walls"):
            episode = adapter.generate(17, {"side_boundary_policy": policy})
            for pair in episode["train"][:2] + [episode["test"][0], episode["test"][-1]]:
                assert prototype.execute(bridge, episode["program_solution"], pair["input"]) == pair["output"]
