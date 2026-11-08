"""Generator for hard_n03 — rank selection, corner rotation, frame placement.

The input contains a hollow cyan frame, a maroon corner key, orange rank marks
on row 0, and size-distinct colored components.  Count the row-0 orange cells
to choose the rank-th smallest non-reserved component, rotate that component
according to the maroon corner, and center it inside the cyan frame on an
otherwise blank canvas.  Orange objects away from row 0 are distractors and
must not participate in the ranking.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "52b9b0e6b46a"
RULE_HASH = "f3c8be3e0a42"
VERSION = "2.0.0"
TASK_ID = "52b9b0e6b46a"

SUMMARY = (
    "A maroon corner selects one of four rotations; 1-3 orange cells on row 0 "
    "select the rank-th smallest ordinary component, which is centered in the "
    "cyan frame. Optional orange objects away from row 0 are ignored."
)

INVARIANTS = [
    "background is 0 and row 0 contains only the rank marks plus an optional corner key",
    "exactly one color-9 cell occupies a corner and encodes identity/cw/180/ccw",
    "one to three color-7 cells on row 0 encode the selection rank",
    "exactly one complete hollow color-8 rectangular frame is present",
    "ordinary candidate components use distinct colors 1..6 and have distinct areas",
    "the selected component fits the frame interior and every non-identity rotation is visible",
    "an optional non-row-0 orange component is a reserved-color distractor, never a candidate",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted", "valid": "11..16"},
    "grid_w": {"type": "int", "default": "canonical-weighted", "valid": "14..19"},
    "frame_h": {"type": "int", "default": "weighted 5..7", "valid": "5..7"},
    "frame_w": {"type": "int", "default": "weighted 5..8", "valid": "5..8"},
    "corner_code": {"type": "int", "default": "sample_index mod 4", "valid": "0..3"},
    "rank": {"type": "int", "default": "sample_index mod 3 + 1", "valid": "1..3"},
    "frame_side": {"type": "str", "default": "balanced 8-slot schedule", "valid": "left|right"},
    "decoy_mode": {"type": "str", "default": "balanced 8-slot schedule", "valid": "none|orange_object"},
}

_CORNERS = ((0, 0), (0, -1), (-1, -1), (-1, 0))
_DIFFICULTY_SIZES = {
    "easy": (3, 4, 5),
    "medium": (3, 5, 6),
    "hard": (4, 6, 7),
}
_BASE_SHAPES = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    6: ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    7: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    bounds = {
        "grid_h": (11, 16),
        "grid_w": (14, 19),
        "frame_h": (5, 7),
        "frame_w": (5, 8),
        "corner_code": (0, 3),
        "rank": (1, 3),
    }
    for axis, (lo, hi) in bounds.items():
        value = overrides.get(axis)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{axis} must be an integer in [{lo}, {hi}]")
    for axis, legal in {
        "frame_side": {"left", "right"},
        "decoy_mode": {"none", "orange_object"},
    }.items():
        value = overrides.get(axis)
        if value is not None and value not in legal:
            raise ValueError(f"{axis} must be one of {sorted(legal)}")


def _schedule_values(sample_index: int) -> tuple[int, int, str, str]:
    """Four consecutive indexes cover all corners, all ranks, both sides and decoy states.

    The side and decoy patterns invert every four slots.  Therefore the query at
    index s+4 repeats the first demo's corner while changing its rank, side and
    decoy state, which kills cue-correlation shortcuts rather than reinforcing
    them.
    """
    i = int(sample_index)
    code = i % 4
    rank = i % 3 + 1
    block = (i // 4) % 2
    side_bit = (i % 2) ^ block
    base_decoy = (0, 1, 1, 0)[i % 4]
    decoy_bit = base_decoy ^ block
    return code, rank, ("right" if side_bit else "left"), (
        "orange_object" if decoy_bit else "none"
    )


SCHEDULE_PROFILES = tuple(
    f"c{code}-r{rank}-{side}-{'decoy' if decoy == 'orange_object' else 'plain'}"
    for code, rank, side, decoy in (_schedule_values(i) for i in range(24))
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed
    _band(difficulty)
    code, rank, side, decoy = _schedule_values(sample_index)
    return f"c{code}-r{rank}-{side}-{'decoy' if decoy == 'orange_object' else 'plain'}"


def _norm(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot90(cells):
    cells = _norm(cells)
    h = max(r for r, _ in cells) + 1
    return _norm((c, h - 1 - r) for r, c in cells)


def _flip_lr(cells):
    cells = _norm(cells)
    w = max(c for _, c in cells) + 1
    return _norm((r, w - 1 - c) for r, c in cells)


def _variants(cells):
    out = set()
    cur = _norm(cells)
    for _ in range(4):
        out.add(cur)
        out.add(_flip_lr(cur))
        cur = _rot90(cur)
    return tuple(sorted(out))


def _shape_hw(cells) -> tuple[int, int]:
    cells = _norm(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rects_overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _frame_positions(h: int, w: int, fh: int, fw: int, side: str):
    positions = []
    for r0 in range(2, h - fh):
        for c0 in range(1, w - fw):
            center_sum = c0 + (c0 + fw - 1)
            if side == "left" and center_sum >= w - 1:
                continue
            if side == "right" and center_sum <= w - 1:
                continue
            positions.append((r0, c0))
    return positions


def _place_items(g, items, blocked_rects, rng, index=0) -> bool:
    if index == len(items):
        return True
    color, cells, row_min = items[index]
    sh, sw = _shape_hw(cells)
    h, w = len(g), len(g[0])
    candidates = []
    for r0 in range(row_min, h - sh):
        for c0 in range(0, w - sw + 1):
            rect = (r0, c0, r0 + sh - 1, c0 + sw - 1)
            if any(_rects_overlap(rect, other) for other in blocked_rects):
                continue
            candidates.append((r0, c0, rect))
    rng.shuffle(candidates)
    for r0, c0, rect in candidates:
        painted = []
        for dr, dc in cells:
            rr, cc = r0 + dr, c0 + dc
            if g[rr][cc] != 0:
                break
            g[rr][cc] = color
            painted.append((rr, cc))
        else:
            blocked_rects.append(rect)
            if _place_items(g, items, blocked_rects, rng, index + 1):
                return True
            blocked_rects.pop()
        for rr, cc in painted:
            g[rr][cc] = 0
    return False


def _connected_components(grid, colors: set[int] | None = None):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0 or (colors is not None and value not in colors) or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            r2 = max(rr for rr, _ in cells)
            c2 = max(cc for _, cc in cells)
            out.append(
                {
                    "color": value,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (r1, c1, r2, c2),
                    "norm": _norm((rr - r1, cc - c1) for rr, cc in cells),
                }
            )
    return out


def _coerce_grid(grid: Any):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("empty grid")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("grid contains a non-row value")
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        raise ValueError("ragged grid")
    g = [list(row) for row in grid]
    if any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        raise ValueError("grid values must be ARC colors 0..9")
    return g


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        g = _coerce_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}
    h, w = len(g), len(g[0])
    errors: list[str] = []

    nines = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 9]
    corners = ((0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0))
    if len(nines) != 1 or nines[0] not in corners:
        errors.append("exactly one maroon cell must occupy a corner")
        corner_code = None
    else:
        corner_code = corners.index(nines[0])

    rank = sum(value == 7 for value in g[0])
    if rank not in (1, 2, 3):
        errors.append("row 0 must contain one to three orange rank cells")
    if any(value not in (0, 7, 9) for value in g[0]):
        errors.append("row 0 may contain only background, orange rank marks, and the corner key")

    eights = {(r, c) for r in range(h) for c in range(w) if g[r][c] == 8}
    frame_bbox = None
    if not eights:
        errors.append("missing cyan frame")
    else:
        r0 = min(r for r, _ in eights)
        c0 = min(c for _, c in eights)
        r1 = max(r for r, _ in eights)
        c1 = max(c for _, c in eights)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if eights != border:
            errors.append("cyan cells must form exactly one complete hollow rectangle")
        if r1 - r0 + 1 < 5 or c1 - c0 + 1 < 4:
            errors.append("cyan frame is too small")
        if r0 < 1 or c0 < 1 or r1 >= h - 1 or c1 >= w - 1:
            errors.append("cyan frame must have a one-cell canvas margin")
        frame_bbox = (r0, c0, r1, c1)

    all_components = _connected_components(g)
    candidate_components = [obj for obj in all_components if 1 <= obj["color"] <= 6]
    orange_components = [obj for obj in all_components if obj["color"] == 7]
    orange_decoys = [obj for obj in orange_components if all(r != 0 for r, _ in obj["cells"])]
    if any(any(r == 0 for r, _ in obj["cells"]) and any(r != 0 for r, _ in obj["cells"]) for obj in orange_components):
        errors.append("an orange distractor may not connect to the row-0 rank marks")
    if len(orange_decoys) > 1:
        errors.append("at most one non-row-0 orange distractor is allowed")
    if not 2 <= len(candidate_components) <= 4:
        errors.append("expected two to four ordinary candidate components")
    if len({obj["color"] for obj in candidate_components}) != len(candidate_components):
        errors.append("ordinary candidate colors must be distinct")
    if len({obj["size"] for obj in candidate_components}) != len(candidate_components):
        errors.append("ordinary candidate areas must be distinct")

    for obj in candidate_components:
        r0, c0, r1, c1 = obj["bbox"]
        own = set(obj["cells"])
        intruders = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if g[r][c] != 0 and (r, c) not in own
        ]
        if intruders:
            errors.append("a candidate bounding box contains cells from another scene role")
            break
        if frame_bbox and _rects_overlap(obj["bbox"], frame_bbox):
            errors.append("ordinary candidates must lie outside the frame bounding box")
            break

    ordered = sorted(
        candidate_components,
        key=lambda obj: (obj["size"], *obj["bbox"]),
    )
    chosen = None
    transformed = None
    if rank in (1, 2, 3) and len(ordered) >= rank and corner_code is not None:
        chosen = ordered[rank - 1]
        transformed = chosen["norm"]
        for _ in range(corner_code):
            transformed = _rot90(transformed)
        if frame_bbox:
            fh = frame_bbox[2] - frame_bbox[0] + 1
            fw = frame_bbox[3] - frame_bbox[1] + 1
            th, tw = _shape_hw(transformed)
            if th > fh - 2 or tw > fw - 2:
                errors.append("the selected transformed component does not fit the frame interior")
    elif rank in (1, 2, 3) and len(ordered) < rank:
        errors.append("rank requests a candidate that does not exist")

    frame_side = None
    if frame_bbox:
        center_sum = frame_bbox[1] + frame_bbox[3]
        if center_sum < w - 1:
            frame_side = "left"
        elif center_sum > w - 1:
            frame_side = "right"
        else:
            errors.append("frame is centered horizontally, so frame_side is not observable")

    facts = {
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "corner_code": corner_code,
        "rank": rank,
        "frame_bbox": frame_bbox,
        "frame_h": (frame_bbox[2] - frame_bbox[0] + 1) if frame_bbox else None,
        "frame_w": (frame_bbox[3] - frame_bbox[1] + 1) if frame_bbox else None,
        "frame_side": frame_side,
        "decoy_mode": "orange_object" if orange_decoys else "none",
        "orange_decoys": orange_decoys,
        "candidates": ordered,
        "chosen": chosen,
        "transformed": transformed,
    }
    return {"errors": list(dict.fromkeys(errors)), **facts}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    for axis in AXES:
        if axis in requested and requested[axis] is not None:
            observed = analysis.get(axis)
            if observed != requested[axis]:
                errors.append(f"{axis} requested {requested[axis]!r}, observed {observed!r}")
    return list(dict.fromkeys(errors))


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {axis: analysis[axis] for axis in AXES}


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons = []
    if not 11 <= analysis["grid_h"] <= 16 or not 14 <= analysis["grid_w"] <= 19:
        reasons.append("canvas lies outside the canonical-anchored generator envelope")
    if not 5 <= analysis["frame_h"] <= 7 or not 4 <= analysis["frame_w"] <= 8:
        reasons.append("frame lies outside the canonical-anchored envelope")
    if not 2 <= len(analysis["candidates"]) <= 3:
        reasons.append("lawful task scenes contain two or three ranked candidates")
    return reasons


def _draw_border(grid, bbox, color=8):
    r0, c0, r1, c1 = bbox
    for r in range(r0, r1 + 1):
        grid[r][c0] = color
        grid[r][c1] = color
    for c in range(c0, c1 + 1):
        grid[r0][c] = color
        grid[r1][c] = color


def _apply_rule(
    grid: Any,
    *,
    forced_code: int | None = None,
    forced_rank: int | None = None,
    include_orange: bool = False,
    descending: bool = False,
    forced_frame_bbox=None,
):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    g = analysis["grid"]
    code = analysis["corner_code"] if forced_code is None else forced_code
    rank = analysis["rank"] if forced_rank is None else forced_rank
    candidates = list(analysis["candidates"])
    if include_orange:
        candidates.extend(analysis["orange_decoys"])
    candidates.sort(key=lambda obj: (obj["size"], *obj["bbox"]), reverse=descending)
    chosen = candidates[rank - 1]
    r0, c0, r1, c1 = chosen["bbox"]
    raw = [row[c0 : c1 + 1] for row in g[r0 : r1 + 1]]
    for _ in range(code):
        raw = [list(row) for row in zip(*raw[::-1])]

    frame = forced_frame_bbox or analysis["frame_bbox"]
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    _draw_border(out, frame, 8)
    fr0, fc0, fr1, fc1 = frame
    sr = fr0 + 1 + max(0, ((fr1 - fr0 - 1) - len(raw)) // 2)
    sc = fc0 + 1 + max(0, ((fc1 - fc0 - 1) - len(raw[0])) // 2)
    for rr, row in enumerate(raw):
        for cc, value in enumerate(row):
            if value and sr + rr < fr1 and sc + cc < fc1:
                out[sr + rr][sc + cc] = value
    return out


def rule_mirror(grid: Any):
    """Python audit mirror; the canonical Racket rule remains output authority."""
    return _apply_rule(grid)


def semantic_observables(grid: Any) -> dict[str, Any]:
    a = _analyze(grid)
    if a["errors"]:
        return {"errors": list(a["errors"])}
    return {
        **{axis: a[axis] for axis in AXES},
        "candidate_sizes": tuple(obj["size"] for obj in a["candidates"]),
        "winner_color": a["chosen"]["color"],
        "winner_size": a["chosen"]["size"],
        "rotation_visible": a["corner_code"] == 0 or a["transformed"] != a["chosen"]["norm"],
        "marker_scattered": any(
            c2 - c1 > 1
            for c1, c2 in zip(
                [c for c, v in enumerate(a["grid"][0]) if v == 7],
                [c for c, v in enumerate(a["grid"][0]) if v == 7][1:],
            )
        ),
    }


def _witness(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


def _rival_always_smallest(grid):
    return _apply_rule(grid, forced_rank=1)


def _rival_always_largest(grid):
    return _apply_rule(grid, forced_rank=1, descending=True)


def _rival_no_rotation(grid):
    return _apply_rule(grid, forced_code=0)


def _rival_always_clockwise(grid):
    return _apply_rule(grid, forced_code=1)


def _rival_swap_quarter_turns(grid):
    code = _analyze(grid)["corner_code"]
    return _apply_rule(grid, forced_code={0: 0, 1: 3, 2: 2, 3: 1}[code])


def _rival_include_orange(grid):
    return _apply_rule(grid, include_orange=True)


def _rival_canonical_corner_rank(grid):
    code = _analyze(grid)["corner_code"]
    return _apply_rule(grid, forced_rank={0: 2, 1: 3, 2: 2, 3: 1}[code])


def _rival_fixed_side(grid, side: str):
    a = _analyze(grid)
    r0, c0, r1, c1 = a["frame_bbox"]
    mirrored = (r0, a["grid_w"] - 1 - c1, r1, a["grid_w"] - 1 - c0)
    if a["frame_side"] == side:
        return _apply_rule(grid)
    return _apply_rule(grid, forced_frame_bbox=mirrored)


SEMANTIC_RIVALS = {
    "always_smallest": _rival_always_smallest,
    "always_largest": _rival_always_largest,
    "ignore_corner_rotation": _rival_no_rotation,
    "always_clockwise": _rival_always_clockwise,
    "swap_clockwise_counterclockwise": _rival_swap_quarter_turns,
    "include_orange_distractor_in_rank": _rival_include_orange,
    "canonical_corner_implies_rank": _rival_canonical_corner_rank,
    "assume_frame_left": lambda grid: _rival_fixed_side(grid, "left"),
    "assume_frame_right": lambda grid: _rival_fixed_side(grid, "right"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # The four public pairs show one rank per corner. This lookup fits all of
    # them but fails as soon as the same corner is paired with a new rank.
    "canonical_corner_implies_rank": _rival_canonical_corner_rank,
}

SEMANTIC_WITNESSES = {
    "corner_identity": lambda grid: _witness(grid, lambda o: o["corner_code"] == 0),
    "corner_clockwise": lambda grid: _witness(grid, lambda o: o["corner_code"] == 1),
    "corner_180": lambda grid: _witness(grid, lambda o: o["corner_code"] == 2),
    "corner_counterclockwise": lambda grid: _witness(grid, lambda o: o["corner_code"] == 3),
    "rank_1": lambda grid: _witness(grid, lambda o: o["rank"] == 1),
    "rank_2": lambda grid: _witness(grid, lambda o: o["rank"] == 2),
    "rank_3": lambda grid: _witness(grid, lambda o: o["rank"] == 3),
    "orange_reserved_distractor": lambda grid: _witness(grid, lambda o: o["decoy_mode"] == "orange_object"),
    "frame_left": lambda grid: _witness(grid, lambda o: o["frame_side"] == "left"),
    "frame_right": lambda grid: _witness(grid, lambda o: o["frame_side"] == "right"),
}
WITNESS_RIVALS = {
    "corner_identity": ["always_clockwise"],
    "corner_clockwise": ["ignore_corner_rotation", "swap_clockwise_counterclockwise"],
    "corner_180": ["ignore_corner_rotation"],
    "corner_counterclockwise": ["ignore_corner_rotation", "swap_clockwise_counterclockwise"],
    "rank_1": ["always_largest", "canonical_corner_implies_rank"],
    "rank_2": ["always_smallest", "always_largest", "canonical_corner_implies_rank"],
    "rank_3": ["always_smallest", "canonical_corner_implies_rank"],
    "orange_reserved_distractor": ["include_orange_distractor_in_rank"],
    "frame_left": ["assume_frame_right"],
    "frame_right": ["assume_frame_left"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for label, pair in [*( (f"demo {i}", pair) for i, pair in enumerate(demos) ), ("query", query)]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input is unlawful: {'; '.join(errors)}")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{label} output disagrees with the rank/rotation/frame rule")
    if reasons:
        return reasons

    truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != truth:
                reasons.append(f"named competitor {name!r} survives the demos but changes the query")
    return reasons


def mutation_fixtures():
    base = generate(73, 0, difficulty="medium")
    fixtures = []

    no_corner = [row[:] for row in base]
    for r, c in ((0, 0), (0, len(base[0]) - 1), (len(base) - 1, 0), (len(base) - 1, len(base[0]) - 1)):
        if no_corner[r][c] == 9:
            no_corner[r][c] = 0
    fixtures.append(("missing_corner_key", no_corner))

    two_corners = [row[:] for row in base]
    empty_corner = next((r, c) for r, c in ((0, 0), (0, len(base[0]) - 1), (len(base) - 1, len(base[0]) - 1), (len(base) - 1, 0)) if two_corners[r][c] == 0)
    two_corners[empty_corner[0]][empty_corner[1]] = 9
    fixtures.append(("two_corner_keys", two_corners))

    no_rank = [row[:] for row in base]
    no_rank[0] = [0 if value == 7 else value for value in no_rank[0]]
    fixtures.append(("missing_rank_marks", no_rank))

    broken_frame = [row[:] for row in base]
    a = _analyze(base)
    broken_frame[a["frame_bbox"][0]][a["frame_bbox"][1] + 1] = 0
    fixtures.append(("broken_frame", broken_frame))

    duplicate_area = [row[:] for row in base]
    smallest = _analyze(base)["candidates"][0]
    largest = _analyze(base)["candidates"][-1]
    for r, c in largest["cells"]:
        duplicate_area[r][c] = 0
    lr, lc, _, _ = largest["bbox"]
    for dr, dc in smallest["norm"]:
        duplicate_area[lr + dr][lc + dc] = largest["color"]
    fixtures.append(("duplicate_candidate_area", duplicate_area))
    return fixtures


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_overrides(overrides)
    scheduled_code, scheduled_rank, scheduled_side, scheduled_decoy = _schedule_values(sample_index)

    effective = dict(overrides)
    effective.setdefault("corner_code", scheduled_code)
    effective.setdefault("rank", scheduled_rank)
    effective.setdefault("frame_side", scheduled_side)
    effective.setdefault("decoy_mode", scheduled_decoy)

    # Every four-example lesson contains canonical-size anchors, while explicit
    # caller overrides retain precedence and all declared boundaries stay valid.
    slot = int(sample_index) % 4
    if slot == 0:
        effective.setdefault("grid_h", 12)
        effective.setdefault("grid_w", 14)
        effective.setdefault("frame_h", 7)
        effective.setdefault("frame_w", 5)
    elif slot == 1:
        effective.setdefault("grid_h", 11)
        effective.setdefault("grid_w", 15)
        effective.setdefault("frame_h", 7)
        effective.setdefault("frame_w", 5)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_choice("grid_h", (11, 12, 12, 12, 13, 14, 15, 16))
    w = ctx.draw_choice("grid_w", (14, 14, 15, 15, 15, 16, 17, 18, 19))
    fh = ctx.draw_choice("frame_h", (5, 6, 7, 7))
    fw = ctx.draw_choice("frame_w", (5, 5, 6, 7, 8))
    code = ctx.draw_int("corner_code", 0, 3)
    rank = ctx.draw_int("rank", 1, 3)
    side = ctx.draw_choice("frame_side", ("left", "right"))
    decoy_mode = ctx.draw_choice("decoy_mode", ("none", "orange_object"))
    rng = ctx.draw_rng("layout")

    positions = _frame_positions(h, w, fh, fw, side)
    if not positions:
        raise ValueError("frame dimensions cannot realize the requested side")

    sizes = _DIFFICULTY_SIZES[band]
    for _ in range(120):
        g = full_grid(h, w, 0)
        corner_r, corner_c = _CORNERS[code]
        corner_r %= h
        corner_c %= w
        g[corner_r][corner_c] = 9

        available = [c for c in range(w) if not (corner_r == 0 and c == corner_c)]
        if rng.randrange(2) == 0:
            starts = [s for s in range(w - rank + 1) if all(c in available for c in range(s, s + rank))]
            start = rng.choice(starts)
            marker_cols = list(range(start, start + rank))
        else:
            marker_cols = rng.sample(available, rank)
        for c in marker_cols:
            g[0][c] = 7

        r0, c0 = rng.choice(positions)
        frame_bbox = (r0, c0, r0 + fh - 1, c0 + fw - 1)
        draw_frame(g, *frame_bbox, 8)

        colors = rng.sample((1, 2, 3, 4, 5, 6), 3)
        items = []
        for color, size in zip(colors, sizes):
            shape = rng.choice(_variants(_BASE_SHAPES[size]))
            items.append((color, shape, 1))
        if decoy_mode == "orange_object":
            items.append((7, rng.choice(_variants(_BASE_SHAPES[2])), 2))
        # Larger bounding boxes first makes the small backtracking search both
        # faster and more reliable at the narrow override boundaries.
        items.sort(key=lambda item: _shape_hw(item[1])[0] * _shape_hw(item[1])[1], reverse=True)
        if not _place_items(g, items, [frame_bbox], rng):
            continue

        analysis = _analyze(g)
        if analysis["errors"]:
            continue
        expected = {
            "grid_h": h,
            "grid_w": w,
            "frame_h": fh,
            "frame_w": fw,
            "corner_code": code,
            "rank": rank,
            "frame_side": side,
            "decoy_mode": decoy_mode,
        }
        if any(analysis[key] != value for key, value in expected.items()):
            continue
        return g
    raise ValueError("could not realize a lawful rank/rotation/frame scene")
