"""Matched-input family varying sequential frame/shape assignment order.

The default is the exact canonical source.  The alternative keeps frame
recognition, fit/orientation preference and centering fixed, but lets frames in
top-left order claim the first unused fitting shape.  Python labels are claims;
native qualification re-executes both Racket programs.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "85e65da9fb15"
HOME = Path(__file__).resolve().parent
MODES = ("shape_first", "frame_first")
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=find_root(__file__)
)


def _read(name: str) -> str:
    return (HOME / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError("assignment_order is not declared")
    return _read("canonical.rkt" if mode == "shape_first" else "frame_first.rkt")


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _derived_seed(seed: int, stream: str, slot: int) -> int:
    raw = hashlib.sha256(f"85e65-parametric-v1:{seed}:{stream}:{slot}".encode()).digest()
    return int.from_bytes(raw[:8], "big") & ((1 << 63) - 1)


_DEMO_SPECS = (
    (1, 14, 16),  # order competition
    (2, 15, 17),  # required rotation
    (0, 16, 18),  # centering slack
    (4, 17, 14),
    (5, 18, 18),
    (3, 13, 17),
)
_QUERY_SPECS = (
    (7, 13, 15),
    (8, 18, 16),
    (6, 17, 18),
)


def _draw_frame(grid, r0: int, c0: int, ih: int, iw: int, color: int) -> None:
    r1, c1 = r0 + ih + 1, c0 + iw + 1
    if not (0 <= r0 < r1 < len(grid) and 0 <= c0 < c1 < len(grid[0])):
        raise RuntimeError("frame escaped canvas")
    cells = {(r0, c) for c in range(c0, c1 + 1)} | {(r1, c) for c in range(c0, c1 + 1)}
    cells |= {(r, c0) for r in range(r0, r1 + 1)} | {(r, c1) for r in range(r0, r1 + 1)}
    if any(grid[r][c] for r, c in cells):
        raise RuntimeError("frame collision")
    for r, c in cells:
        grid[r][c] = color


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells, code: int):
    cells = list(cells)
    if code & 1:
        cells = [(c, -r) for r, c in cells]
    if code & 2:
        cells = [(r, -c) for r, c in cells]
    return _normalize(cells)


def _put_shape(grid, r0: int, c0: int, cells, color: int) -> None:
    placed = {(r0 + r, c0 + c) for r, c in cells}
    if any(not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] for r, c in placed):
        raise RuntimeError("shape collision")
    for r, c in placed:
        grid[r][c] = color


_STRESS_A = _normalize(
    [(0, c) for c in range(5)] + [(1, 0), (1, 4), (2, 1), (2, 2), (2, 3), (3, 2)]
)
_STRESS_B = _normalize(
    [(r, 0) for r in range(5)] + [(4, c) for c in range(1, 5)] + [(1, 1), (3, 3)]
)
_STRESS_C = _normalize([(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)])


def _stress_grid(seed: int) -> list[list[int]]:
    """30x30 competition: canonical fills both frames; frame-first strands B."""
    palette = list(range(1, 9))
    # A deterministic rotation changes colors without altering object roles.
    shift = _derived_seed(seed, "stress-palette", 0) % len(palette)
    palette = palette[shift:] + palette[:shift]
    f1, f2, s1, s2, s3 = palette[:5]
    grid = [[0] * 30 for _ in range(30)]
    # Large frame is first and touches top/left. Tight frame touches bottom/right.
    _draw_frame(grid, 0, 0, 10, 10, f1)       # 10x10 interior
    _draw_frame(grid, 24, 23, 4, 5, f2)       # 4x5 interior
    # First shape fits both and is exact in the later tight frame. Second fits
    # only the large frame, exposing the committed-assignment intermediate.
    _put_shape(grid, 1, 15, _transform(_STRESS_A, shift % 4), s1)
    _put_shape(grid, 14, 0, _transform(_STRESS_B, (shift + 1) % 4), s2)
    # Unmatched distractor exercises deletion and spreads visible content.
    _put_shape(grid, 15, 18, _transform(_STRESS_C, (shift + 2) % 4), s3)
    if GEN.self_check(grid):
        raise RuntimeError(f"stress scene invalid: {GEN.self_check(grid)}")
    if GEN._solve(deepcopy(grid)) == GEN._frame_first(deepcopy(grid)):
        raise RuntimeError("stress scene failed to separate assignment orders")
    return grid


def _production_grid(seed: int, stream: str, slot: int, spec):
    sample_index, h, w = spec
    return GEN.generate(
        _derived_seed(seed, stream, slot), sample_index,
        difficulty="hard", grid_h=h, grid_w=w,
    )


def select_inputs(seed: int, demos: int, queries: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = [
        {"input": _production_grid(seed, "demo", slot, _DEMO_SPECS[slot])}
        for slot in range(demos)
    ]
    test = [
        {"input": (_production_grid(seed, "query", slot, _QUERY_SPECS[slot])
                   if slot < 3 else _stress_grid(seed))}
        for slot in range(queries)
    ]
    return {"train": train, "test": test}


def _frame_first_variant(grid, *, placement="center", allow_rotation=True, exact_only=False, reverse_shapes=False):
    components = GEN._components(grid)
    frames = sorted([obj for obj in components if GEN._is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    solids = sorted([obj for obj in components if not GEN._is_frame(obj)], key=lambda x: (x["r1"], x["c1"]), reverse=reverse_shapes)
    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]
    used: set[int] = set()
    for frame in frames:
        ih, iw = frame["h"] - 2, frame["w"] - 2
        for index, solid in enumerate(solids):
            if index in used:
                continue
            original = GEN._object_grid(solid)
            rotated = GEN._rotate_cw(original)
            oriented = None
            if len(original) <= ih and len(original[0]) <= iw:
                oriented = original
            elif allow_rotation and len(rotated) <= ih and len(rotated[0]) <= iw:
                oriented = rotated
            if oriented is None or (exact_only and (len(oriented), len(oriented[0])) != (ih, iw)):
                continue
            used.add(index)
            if placement == "center":
                r0 = frame["r1"] + 1 + (ih - len(oriented)) // 2
                c0 = frame["c1"] + 1 + (iw - len(oriented[0])) // 2
            elif placement == "top_left":
                r0, c0 = frame["r1"] + 1, frame["c1"] + 1
            else:
                raise ValueError("unknown placement")
            GEN._stamp(out, oriented, r0, c0)
            break
    return out


def output_for(grid, mode: str):
    if mode == "shape_first":
        return GEN._solve(deepcopy(grid))
    if mode == "frame_first":
        return GEN._frame_first(deepcopy(grid))
    raise ValueError("unknown assignment_order")


def _assignments(grid, mode: str):
    """Pixel-derived summary: output frame interior colors in frame order."""
    components = GEN._components(grid)
    frames = sorted([obj for obj in components if GEN._is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    out = output_for(grid, mode)
    rows = []
    for frame in frames:
        colors = sorted({
            out[r][c]
            for r in range(frame["r1"] + 1, frame["r2"])
            for c in range(frame["c1"] + 1, frame["c2"])
            if out[r][c]
        })
        rows.append({"frame_top_left": [frame["r1"], frame["c1"]], "content_colors": colors})
    return rows


def analyze_input(grid):
    components = GEN._components(grid)
    frames = [obj for obj in components if GEN._is_frame(obj)]
    solids = [obj for obj in components if not GEN._is_frame(obj)]
    return {
        "frames": len(frames),
        "solids": len(solids),
        "shape_first_assignments": _assignments(grid, "shape_first"),
        "frame_first_assignments": _assignments(grid, "frame_first"),
        "shape_first_output": output_for(grid, "shape_first"),
        "frame_first_output": output_for(grid, "frame_first"),
    }


def _shortcut_outputs(grid, chosen: str):
    if chosen == "shape_first":
        return {
            "opposite_setting": output_for(grid, "frame_first"),
            "top_left_in_frame": GEN._solve(deepcopy(grid), placement="top_left"),
            "never_rotate": GEN._solve(deepcopy(grid), allow_rotation=False),
            "exact_bbox_only": GEN._solve(deepcopy(grid), exact_only=True),
            "solid_area_order": GEN._solve(deepcopy(grid), solid_order="area"),
        }
    return {
        "opposite_setting": output_for(grid, "shape_first"),
        "top_left_in_frame": _frame_first_variant(grid, placement="top_left"),
        "never_rotate": _frame_first_variant(grid, allow_rotation=False),
        "exact_bbox_only": _frame_first_variant(grid, exact_only=True),
        "reverse_shape_choice": _frame_first_variant(grid, reverse_shapes=True),
    }


def assess_demos(demos, chosen: str):
    if chosen not in MODES:
        raise ValueError("unknown assignment_order")
    setting_survivors = [
        mode for mode in MODES
        if all(output_for(pair["input"], mode) == pair["output"] for pair in demos)
    ]
    names = list(_shortcut_outputs(demos[0]["input"], chosen))
    survivors = [
        name for name in names
        if all(_shortcut_outputs(pair["input"], chosen)[name] == pair["output"] for pair in demos)
    ]
    return {
        "demonstrations": len(demos),
        "setting_survivors": setting_survivors,
        "harmful_shortcut_survivors": survivors,
        "rivals_tested": len(names),
    }


def generate_episode(seed: int, mode: str, demos: int, queries: int):
    if mode not in MODES:
        raise ValueError("unknown assignment_order")
    selected = select_inputs(seed, demos, queries)
    result = {"program_solution": program_for(mode), "train": [], "test": []}
    for split in ("train", "test"):
        result[split] = [
            {"input": deepcopy(row["input"]), "output": output_for(row["input"], mode)}
            for row in selected[split]
        ]
    return result


def causal_case(grid):
    info = analyze_input(grid)
    canonical = output_for(grid, "shape_first")
    counterfactual = output_for(grid, "frame_first")
    return {
        "input": deepcopy(grid),
        "settings": {"assignment_order": "shape_first"},
        "intermediate_value": {
            "shape_first_assignments": info["shape_first_assignments"],
            "frame_first_assignments": info["frame_first_assignments"],
            "changed_final_cells": sum(
                a != b for row_a, row_b in zip(canonical, counterfactual)
                for a, b in zip(row_a, row_b)
            ),
        },
        "program": program_for("shape_first"),
        "output": canonical,
        "counterfactual_program": program_for("frame_first"),
        "counterfactual_output": counterfactual,
        "ablation": "wrong_order",
    }
