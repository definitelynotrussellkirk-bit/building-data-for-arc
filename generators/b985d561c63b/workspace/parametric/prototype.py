"""Task-local native authoring implementation for b985d561c63b.

The canonical setting stamps the complete colored-source bounding box at the
upper-left of each gray target, byte-for-byte using the selected canonical
Racket rule.  The alternate setting adds a real input-dependent dependency:
first locate the source crop's unique zero-valued corner, then use that corner
as the alignment corner for every larger gray target before copying the full
crop (including the zero).

Python outputs are deterministic authoring claims.  Native qualification
re-executes every label through the protected Racket runtime.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_id,
)


TASK_ID = "b985d561c63b"
VERSION = "native-hole-corner-anchor-v1"
ALLOWED_STAMP_ANCHORS = ("top_left", "hole_corner")
DEFAULT_STAMP_ANCHOR = "top_left"
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
CANONICAL_RULE_HASH = "c86839f15a5d"
CANONICAL_SHA256 = "d28ede61a9c78ba345f33b47b9db17b0ea2334f382d7c6f17c8a1ec9cb6ef51a"
HERE = Path(__file__).resolve().parent

_CANONICAL_RESULT_SITE = """                  (result (make-hash)))"""
_HOLE_RESULT_SITE = """                  (hole-cells
                    (for*/list ((r (range tr1 (+ tr2 1)))
                                (c (range tc1 (+ tc2 1)))
                                #:when (= (at g r c) 0))
                      (list r c)))
                  (hole (first hole-cells))
                  (anchor-bottom? (>= (* 2 (- (first hole) tr1)) th))
                  (anchor-right? (>= (* 2 (- (second hole) tc1)) tw))
                  (result (make-hash)))"""
_CANONICAL_ANCHOR_SITE = """               (let ((rmin (min-of first region))
                     (cmin (min-of second region)))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ rmin dr))
                             (nc (+ cmin dc)))"""
_HOLE_ANCHOR_SITE = """               (let* ((rmin (min-of first region))
                      (cmin (min-of second region))
                      (rmax (max-of first region))
                      (cmax (max-of second region))
                      (target-r0
                        (if anchor-bottom? (+ 1 (- rmax th)) rmin))
                      (target-c0
                        (if anchor-right? (+ 1 (- cmax tw)) cmin)))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ target-r0 dr))
                             (nc (+ target-c0 dc)))"""

# Profiles are deliberately prefix-stable.  The first two demonstrations use
# different non-top-left cue corners, so either declared setting is identified
# with the minimum supported context.  The fourth query is a dense 30x30 case.
_DEMO_PROFILES = (
    {
        "canvas": (10, 12), "source_shape": (3, 3), "hole_corner": "top_right",
        "target_shape": (4, 5), "source": (1, 1), "targets": ((0, 7), (6, 0)),
        "palette_size": 2,
    },
    {
        "canvas": (13, 14), "source_shape": (4, 3), "hole_corner": "bottom_left",
        "target_shape": (6, 5), "source": (0, 0), "targets": ((0, 9), (7, 4)),
        "palette_size": 3,
    },
    {
        "canvas": (15, 16), "source_shape": (3, 4), "hole_corner": "bottom_right",
        "target_shape": (5, 6), "source": (0, 0),
        "targets": ((0, 10), (6, 0), (10, 10)), "palette_size": 2,
    },
    {
        "canvas": (18, 19), "source_shape": (5, 4), "hole_corner": "top_right",
        "target_shape": (6, 6), "source": (0, 0),
        "targets": ((0, 13), (7, 0), (12, 13)), "palette_size": 3,
    },
    {
        "canvas": (21, 22), "source_shape": (4, 5), "hole_corner": "bottom_left",
        "target_shape": (6, 7), "source": (0, 0),
        "targets": ((0, 15), (7, 0), (15, 15)), "palette_size": 2,
    },
    {
        "canvas": (24, 25), "source_shape": (5, 5), "hole_corner": "bottom_right",
        "target_shape": (7, 7), "source": (0, 0),
        "targets": ((0, 18), (8, 0), (17, 0), (17, 18)), "palette_size": 3,
    },
)
_QUERY_PROFILES = (
    {
        "canvas": (11, 13), "source_shape": (3, 4), "hole_corner": "top_left",
        "target_shape": (4, 6), "source": (0, 0), "targets": ((0, 7), (7, 3)),
        "palette_size": 2,
    },
    {
        "canvas": (16, 17), "source_shape": (4, 4), "hole_corner": "top_right",
        "target_shape": (6, 6), "source": (0, 0),
        "targets": ((0, 11), (7, 0), (10, 11)), "palette_size": 3,
    },
    {
        "canvas": (23, 24), "source_shape": (5, 4), "hole_corner": "bottom_left",
        "target_shape": (7, 7), "source": (0, 0),
        "targets": ((0, 17), (8, 0), (16, 0), (16, 17)), "palette_size": 2,
    },
    {
        "canvas": (30, 30), "source_shape": (5, 5), "hole_corner": "bottom_right",
        "target_shape": (9, 9), "source": (0, 0),
        "targets": ((0, 21), (10, 0), (21, 0), (21, 21)), "palette_size": 3,
    },
)


def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_stamp_anchor(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_STAMP_ANCHORS:
        raise ValueError(f"stamp_anchor must be one of {ALLOWED_STAMP_ANCHORS}")
    return value


def _validate_corner(value: Any) -> str:
    if type(value) is not str or value not in CORNERS:
        raise ValueError(f"corner must be one of {CORNERS}")
    return value


def validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"stamp_anchor"}:
        raise ValueError("settings must contain exactly stamp_anchor")
    return {"stamp_anchor": _validate_stamp_anchor(settings["stamp_anchor"])}


def _checked_canonical(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA-256 differs from the pinned authority")
    if source.count(_CANONICAL_RESULT_SITE) != 1:
        raise ValueError("canonical source has an unexpected result binding")
    if source.count(_CANONICAL_ANCHOR_SITE) != 1:
        raise ValueError("canonical source has an unexpected stamp site")
    return source


def canonical_source(*, root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    rows: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                value = row.get("program_solution")
                if type(value) is not str:
                    raise ValueError("canonical task row has no exact program_solution")
                rows.add(value)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(rows)}")
    return _checked_canonical(next(iter(rows)))


def materialize_hole_corner_rule(source: str) -> str:
    source = _checked_canonical(source)
    alternate = source.replace(_CANONICAL_RESULT_SITE, _HOLE_RESULT_SITE, 1)
    alternate = alternate.replace(_CANONICAL_ANCHOR_SITE, _HOLE_ANCHOR_SITE, 1)
    if alternate.count(_HOLE_RESULT_SITE) != 1 or alternate.count(_HOLE_ANCHOR_SITE) != 1:
        raise AssertionError("hole-corner source edit was not unique")
    return alternate


def _fixed_anchor_site(corner: str) -> str:
    corner = _validate_corner(corner)
    bottom = corner.startswith("bottom")
    right = corner.endswith("right")
    row_origin = "(+ 1 (- rmax th))" if bottom else "rmin"
    col_origin = "(+ 1 (- cmax tw))" if right else "cmin"
    return f"""               (let* ((rmin (min-of first region))
                      (cmin (min-of second region))
                      (rmax (max-of first region))
                      (cmax (max-of second region))
                      (target-r0 {row_origin})
                      (target-c0 {col_origin}))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ target-r0 dr))
                             (nc (+ target-c0 dc)))"""


def fixed_anchor_program(corner: Any, *, root: Path | None = None, source: str | None = None) -> str:
    corner = _validate_corner(corner)
    canonical = canonical_source(root=root) if source is None else _checked_canonical(source)
    if corner == "top_left":
        return canonical
    result = canonical.replace(_CANONICAL_ANCHOR_SITE, _fixed_anchor_site(corner), 1)
    if result == canonical:
        raise AssertionError("fixed-anchor source edit did not change the canonical program")
    return result


def program_for(stamp_anchor: Any = DEFAULT_STAMP_ANCHOR, *, root: Path | None = None) -> str:
    stamp_anchor = _validate_stamp_anchor(stamp_anchor)
    canonical = canonical_source(root=root)
    if stamp_anchor == DEFAULT_STAMP_ANCHOR:
        return canonical
    expected = materialize_hole_corner_rule(canonical)
    path = HERE / "rules" / "hole_corner_anchor.rkt"
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        raise ValueError("hole-corner Racket resource differs from the guarded canonical edit")
    return actual


def program(settings: Any) -> str:
    normalized = validate_settings(settings)
    return program_for(normalized["stamp_anchor"])


def rule_callable(source: Any) -> str:
    if type(source) is not str or not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("expected one complete rule! source")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None) -> list[list[int]]:
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _components(points: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(points)
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: _bbox(cells))


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _normalize_grid(grid: Any) -> list[list[int]]:
    value = normalize_grid(grid)
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact ARC colors")
    return value


def _corner_for_relative(row: int, col: int, height: int, width: int) -> str:
    if (row, col) == (0, 0):
        return "top_left"
    if (row, col) == (0, width - 1):
        return "top_right"
    if (row, col) == (height - 1, 0):
        return "bottom_left"
    if (row, col) == (height - 1, width - 1):
        return "bottom_right"
    raise ValueError("the unique source zero must occupy a bounding-box corner")


def _analyze(grid: Any) -> dict[str, Any]:
    grid = _normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    source = [
        (row, col)
        for row, values in enumerate(grid)
        for col, cell in enumerate(values)
        if cell not in (0, 5)
    ]
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, cell in enumerate(values)
        if cell == 5
    ]
    if not source or not gray:
        raise ValueError("input needs a colored source and at least one gray target")
    source_box = _bbox(source)
    sr0, sc0, sr1, sc1 = source_box
    source_h, source_w = sr1 - sr0, sc1 - sc0
    holes = [
        (row, col)
        for row in range(sr0, sr1)
        for col in range(sc0, sc1)
        if grid[row][col] == 0
    ]
    if len(holes) != 1:
        raise ValueError("source bounding box must contain exactly one zero cue")
    hole_row, hole_col = holes[0]
    hole_relative = (hole_row - sr0, hole_col - sc0)
    hole_corner = _corner_for_relative(*hole_relative, source_h, source_w)

    targets: list[dict[str, Any]] = []
    for cells in _components(gray):
        box = _bbox(cells)
        r0, c0, r1, c1 = box
        target_h, target_w = r1 - r0, c1 - c0
        if len(cells) != target_h * target_w:
            raise ValueError("every gray target must be a solid rectangle")
        if target_h < source_h or target_w < source_w:
            raise ValueError("every gray target must contain the source crop")
        targets.append({"cells": cells, "bbox": box, "shape": (target_h, target_w)})
    return {
        "grid": grid,
        "height": height,
        "width": width,
        "source_cells": source,
        "source_bbox": source_box,
        "source_shape": (source_h, source_w),
        "hole": holes[0],
        "hole_relative": hole_relative,
        "hole_corner": hole_corner,
        "targets": targets,
    }


def hole_corner_intermediate(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    return {
        "corner": analysis["hole_corner"],
        "source_bbox": list(analysis["source_bbox"]),
        "hole_cell": list(analysis["hole"]),
        "hole_relative": list(analysis["hole_relative"]),
    }


def _target_origin(box: tuple[int, int, int, int], source_shape: tuple[int, int], corner: str) -> tuple[int, int]:
    r0, c0, r1, c1 = box
    source_h, source_w = source_shape
    top = corner.startswith("top")
    left = corner.endswith("left")
    return (r0 if top else r1 - source_h, c0 if left else c1 - source_w)


def apply_python(
    grid: Any,
    *,
    stamp_anchor: Any = DEFAULT_STAMP_ANCHOR,
    corner_override: Any | None = None,
    copy_template_zeros: Any = True,
) -> list[list[int]]:
    stamp_anchor = _validate_stamp_anchor(stamp_anchor)
    if type(copy_template_zeros) is not bool:
        raise ValueError("copy_template_zeros must be a literal bool")
    if corner_override is not None:
        if stamp_anchor != "hole_corner":
            raise ValueError("corner_override is only valid for hole_corner")
        corner_override = _validate_corner(corner_override)
    analysis = _analyze(grid)
    source_r0, source_c0, _, _ = analysis["source_bbox"]
    source_h, source_w = analysis["source_shape"]
    corner = (
        "top_left"
        if stamp_anchor == "top_left"
        else corner_override or analysis["hole_corner"]
    )
    output = copy.deepcopy(analysis["grid"])
    for target in analysis["targets"]:
        target_r0, target_c0 = _target_origin(target["bbox"], analysis["source_shape"], corner)
        for dr in range(source_h):
            for dc in range(source_w):
                value = analysis["grid"][source_r0 + dr][source_c0 + dc]
                if value == 0 and not copy_template_zeros:
                    continue
                output[target_r0 + dr][target_c0 + dc] = value
    return output


def input_features(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    touching = 0
    target_cells = 0
    shapes: list[list[int]] = []
    for target in analysis["targets"]:
        r0, c0, r1, c1 = target["bbox"]
        if r0 == 0 or c0 == 0 or r1 == analysis["height"] or c1 == analysis["width"]:
            touching += 1
        target_cells += len(target["cells"])
        shapes.append(list(target["shape"]))
    return {
        "grid_shape": [analysis["height"], analysis["width"]],
        "source_shape": list(analysis["source_shape"]),
        "source_bbox": list(analysis["source_bbox"]),
        "hole_corner": analysis["hole_corner"],
        "hole_relative": list(analysis["hole_relative"]),
        "target_count": len(analysis["targets"]),
        "target_shapes": shapes,
        "target_cells": target_cells,
        "targets_touching_boundary": touching,
    }


def _seeded_rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _corner_offset(corner: str, height: int, width: int) -> tuple[int, int]:
    corner = _validate_corner(corner)
    return (
        0 if corner.startswith("top") else height - 1,
        0 if corner.endswith("left") else width - 1,
    )


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    profile = profiles[index]
    height, width = profile["canvas"]
    source_h, source_w = profile["source_shape"]
    target_h, target_w = profile["target_shape"]
    grid = [[0] * width for _ in range(height)]
    rng = _seeded_rng(seed, split, index)
    palette = rng.sample((1, 2, 3, 4, 6, 7, 8, 9), profile["palette_size"])
    cells = [(r, c) for r in range(source_h) for c in range(source_w)]
    hole = _corner_offset(profile["hole_corner"], source_h, source_w)
    cells.remove(hole)
    rng.shuffle(cells)
    source_r0, source_c0 = profile["source"]
    for position, (dr, dc) in enumerate(cells):
        grid[source_r0 + dr][source_c0 + dc] = palette[position % len(palette)]
    for target_r0, target_c0 in profile["targets"]:
        for dr in range(target_h):
            for dc in range(target_w):
                if grid[target_r0 + dr][target_c0 + dc] != 0:
                    raise AssertionError("profile objects overlap")
                grid[target_r0 + dr][target_c0 + dc] = 5
    features = input_features(grid)
    if features["hole_corner"] != profile["hole_corner"]:
        raise AssertionError("profile cue corner changed during construction")
    return grid


def generate_episode(
    seed: Any,
    *,
    stamp_anchor: Any = DEFAULT_STAMP_ANCHOR,
    demos: Any = 3,
    queries: Any = 4,
    root: Path | None = None,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    stamp_anchor = _validate_stamp_anchor(stamp_anchor)
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demos):
        grid = _build_input(seed, "demo", index)
        train.append({"input": grid, "output": apply_python(grid, stamp_anchor=stamp_anchor)})
    for index in range(queries):
        grid = _build_input(seed, "query", index)
        test.append({"input": grid, "output": apply_python(grid, stamp_anchor=stamp_anchor)})
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(stamp_anchor, root=root),
        "settings": {"stamp_anchor": stamp_anchor},
        "prototype_version": VERSION,
    }


def public_challenge(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_id(episode: Any) -> str:
    return public_challenge_id(public_challenge(episode))
