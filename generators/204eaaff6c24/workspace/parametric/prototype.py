"""Native parametric family for ARC task 204eaaff6c24.

The canonical setting counts every cell of the sole nonzero color.  The
alternate keeps the same monochrome-bar output grammar but adds a real
input-dependent composition:

1. segment row-major four-connected components and measure the first component;
2. use that anchor size as a cyclic index into the remaining components;
3. count the selected component and encode that count as the output bar.

Inputs are shared across settings and deliberately contain multiple components.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "204eaaff6c24"
MODES = ("all_cells", "anchor_indexed_component")
DEFAULT_MODE = "all_cells"

CANONICAL_PROGRAM = (Path(__file__).with_name("canonical.rkt")).read_text(encoding="utf-8")
INDEXED_PROGRAM = """(rule! (lambda (g)
         (let* ((objs (objects g 0))
                (anchor (first objs))
                (candidates (rest objs))
                (anchor-size (obj-size anchor))
                (target-index (modulo (- anchor-size 1) (length candidates)))
                (target (nth candidates target-index))
                (n (obj-size target))
                (color (obj-color anchor)))
           (encode-bar n n color))))"""
_WRONG_PLUS_ONE_PROGRAM = """(rule! (lambda (g)
         (let* ((objs (objects g 0))
                (anchor (first objs))
                (candidates (rest objs))
                (anchor-size (obj-size anchor))
                (target-index (modulo anchor-size (length candidates)))
                (target (nth candidates target-index))
                (n (obj-size target))
                (color (obj-color anchor)))
           (encode-bar n n color))))"""

# height, width, anchor size, candidate sizes in row-major slot order
_DEMO_SPECS = (
    (14, 16, 1, (2, 5, 3, 7)),
    (15, 17, 3, (6, 2, 5, 4)),
    (16, 18, 2, (4, 7, 3, 6)),
    (18, 20, 4, (2, 8, 5, 3)),
    (21, 23, 1, (9, 4, 6, 2)),
    (24, 26, 3, (4, 8, 6, 5)),
)
_QUERY_SPECS = (
    (14, 16, 2, (4, 7, 3, 6)),
    (18, 20, 4, (2, 8, 5, 3)),
    (24, 26, 3, (9, 4, 6, 2)),
    (30, 30, 4, (2, 3, 4, 5, 6, 1, 5)),
)
_FIVE_SLOTS = ("tl", "tr", "ml", "mr", "bc")
_EIGHT_SLOTS = ("tl", "tc", "tr", "ml", "mc", "mr", "bl", "br")


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"count_mode"}:
        raise ValueError("settings must contain exactly count_mode")
    mode = settings["count_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"count_mode must be one of {MODES}")
    return {"count_mode": mode}


def rule_text(mode: str) -> str:
    if mode == "all_cells":
        return CANONICAL_PROGRAM
    if mode == "anchor_indexed_component":
        return INDEXED_PROGRAM
    raise ValueError(f"unknown count_mode {mode!r}")


def counterfactual_program() -> str:
    return _WRONG_PLUS_ONE_PROGRAM


def _mix(*parts: object) -> int:
    text = ":".join(map(str, (TASK_ID, "anchor-indexed-v1", *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape(size: int, variant: int):
    if type(size) is not int or not 1 <= size <= 15:
        raise ValueError("component size must be in 1..15")
    width = max(2, (size + 3) // 4)
    cells = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    # Dihedral variation, preserving four-connectivity.
    if (variant // 3) % 2:
        cells = [(r, -c) for r, c in cells]
    for _ in range((variant // 7) % 4):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _slot_position(slot: str, height: int, width: int, shape):
    shape_h = 1 + max(r for r, _ in shape)
    shape_w = 1 + max(c for _, c in shape)
    if shape_h > 4 or shape_w > 4 or height < 14 or width < 16:
        raise ValueError("slot geometry expects <=4x4 shapes on >=14x16 grids")
    middle_top = (height - 4) // 2
    top = {
        "tl": 0, "tc": 0, "tr": 0,
        "ml": middle_top, "mc": middle_top, "mr": middle_top,
        "bl": height - shape_h, "bc": height - shape_h, "br": height - shape_h,
    }[slot]
    left = {
        "tl": 0, "ml": 0, "bl": 0,
        "tc": (width - shape_w) // 2,
        "mc": (width - shape_w) // 2,
        "bc": (width - shape_w) // 2,
        "tr": width - shape_w, "mr": width - shape_w, "br": width - shape_w,
    }[slot]
    return top, left


def components4(grid):
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError("expected exactly one nonzero color")
    color = next(iter(colors))
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        components.append(tuple(sorted(cells)))
    return color, sorted(components, key=min)


def analyze(grid) -> dict[str, Any]:
    color, components = components4(grid)
    if len(components) < 2:
        raise ValueError("anchor-indexed family requires at least two components")
    anchor = components[0]
    candidates = components[1:]
    anchor_size = len(anchor)
    target_index = (anchor_size - 1) % len(candidates)
    target = candidates[target_index]
    return {
        "color": color,
        "component_sizes": [len(component) for component in components],
        "anchor_size": anchor_size,
        "candidate_sizes": [len(component) for component in candidates],
        "target_index": target_index,
        "target_size": len(target),
    }


def apply_mode(grid, mode: str):
    info = analyze(grid)
    if mode == "all_cells":
        size = sum(info["component_sizes"])
    elif mode == "anchor_indexed_component":
        size = info["target_size"]
    else:
        raise ValueError(f"unknown count_mode {mode!r}")
    return [[info["color"]] * size]


def apply_wrong_plus_one(grid):
    info = analyze(grid)
    wrong_index = info["anchor_size"] % len(info["candidate_sizes"])
    return [[info["color"]] * info["candidate_sizes"][wrong_index]]


def _build_input(seed: int, split: str, index: int, spec):
    height, width, anchor_size, candidate_sizes = spec
    sizes = (anchor_size, *candidate_sizes)
    slots = _FIVE_SLOTS if len(sizes) == 5 else _EIGHT_SLOTS
    if len(sizes) != len(slots):
        raise ValueError("spec and slot count differ")
    color = 1 + _mix(seed, split, index, "color") % 9
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied = set()
    for component_index, (size, slot) in enumerate(zip(sizes, slots)):
        shape = _shape(size, _mix(seed, split, index, component_index, "shape"))
        top, left = _slot_position(slot, height, width, shape)
        cells = {(top + r, left + c) for r, c in shape}
        if occupied & cells:
            raise ValueError("component overlap")
        # Keep components four-disconnected even when their slot boxes approach.
        if any((r + dr, c + dc) in occupied for r, c in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            raise ValueError("component adjacency")
        occupied.update(cells)
        for r, c in cells:
            grid[r][c] = color
    info = analyze(grid)
    if info["anchor_size"] != anchor_size or sorted(info["candidate_sizes"]) != sorted(candidate_sizes):
        raise ValueError(
            f"constructed component sizes differ: {info['component_sizes']} vs {list(sizes)}"
        )
    return grid


def _pair(seed: int, split: str, index: int, spec, mode: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, count_mode: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    if count_mode not in MODES:
        raise ValueError(f"unknown count_mode {count_mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [
        _pair(seed, "train", index, _DEMO_SPECS[index], count_mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _QUERY_SPECS[index], count_mode)
        for index in range(queries)
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": rule_text(count_mode),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return (
        json.dumps(
            public_turn(episode, query_index),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def public_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    episode = generate_episode(
        seed,
        count_mode="anchor_indexed_component",
        demos=3,
        queries=4,
    )
    pair = episode["test"][0]
    info = analyze(pair["input"])
    return {
        "settings": {"count_mode": "anchor_indexed_component"},
        "input": deepcopy(pair["input"]),
        "program": INDEXED_PROGRAM,
        "output": deepcopy(pair["output"]),
        "counterfactual_program": _WRONG_PLUS_ONE_PROGRAM,
        "counterfactual_output": apply_wrong_plus_one(pair["input"]),
        "intermediate_value": {
            "anchor_size": info["anchor_size"],
            "candidate_sizes": info["candidate_sizes"],
            "correct_target_index": info["target_index"],
            "wrong_target_index": info["anchor_size"] % len(info["candidate_sizes"]),
        },
        "ablation": "wrong_intermediate",
    }
