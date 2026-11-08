"""Generator for ARC task H72 / 12a886996b14: translation analogy.

The red (2) and green (3) objects are two placements of one marker template.
Their bounding-box top-lefts define a translation vector.  Apply that vector to
all yellow (4) cells on a fresh zero background; omit the marker objects and the
original yellow object.

One canonical demonstration contains a useful complication: yellow covers two
cells of the red source marker.  The green target marker reveals the complete
hidden template.  This generator models that case directly instead of reducing
red and green to unrelated singleton cells.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12a886996b14"
TASK_ID = "12a886996b14"
VERSION = "3.0.0"
RULE_HASH = "8de52d1da0e7"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains matching red (2) source and green (3) "
    "target marker shapes plus one connected yellow (4) object.  The yellow "
    "object may partially occlude the red source marker; the complete green "
    "marker reveals the hidden source template.  Translate every yellow cell "
    "by the vector from the red marker bounding-box top-left to the green "
    "marker bounding-box top-left, placing only the translated yellow object "
    "on a fresh blank grid."
)

INVARIANTS = [
    "red and green encode the same connected marker template, modulo yellow occlusion of red",
    "the red-bbox to green-bbox translation vector is nonzero",
    "all yellow cells form one nonempty 4-connected object",
    "every translated yellow cell remains in bounds",
    "the output is blank except for the translated yellow object",
]

_DIRECTIONS = (
    "up_left",
    "up",
    "up_right",
    "left",
    "right",
    "down_left",
    "down",
    "down_right",
)
_OCCLUSIONS = ("none", "partial")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped with canonical-scale schedule anchors",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped with canonical-scale schedule anchors",
        "valid": "12..16",
    },
    "marker_size": {
        "type": "int",
        "default": "difficulty-shaped; canonical anchors use 3..5",
        "valid": "3..6",
    },
    "yellow_size": {
        "type": "int",
        "default": "difficulty-shaped; canonical anchors use 4..8",
        "valid": "3..8",
    },
    "occlusion": {
        "type": "str",
        "default": "six-slot schedule with two partial cases in every three-slot window",
        "valid": "none|partial",
    },
    "vector_direction": {
        "type": "str",
        "default": "six-slot schedule with two upward cases in every three-slot window",
        "valid": "up_left|up|up_right|left|right|down_left|down|down_right",
    },
}

# Opt into the strict exact-override contract.  Every declared value can be
# combined with every value of the other axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The canonical data only moves yellow downward.  Any three consecutive draws
# contain two upward examples, so every two-demo query rotation retains an
# explicit counterexample to that public-only correlation.  The same schedule
# protects the source-occlusion branch.
_DIRECTION_SCHEDULE = (
    "down_right",
    "up_left",
    "up_right",
    "down_left",
    "up",
    "up_right",
)
_OCCLUSION_SCHEDULE = (
    "none",
    "partial",
    "partial",
    "none",
    "partial",
    "partial",
)
_CANONICAL_ANCHOR_SLOTS = frozenset((0, 3))
SCHEDULE_PROFILES = tuple(range(len(_DIRECTION_SCHEDULE)))
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SIZE_BANDS = {
    None: ((9, 14), (12, 16), (3, 6), (3, 8)),
    "easy": ((9, 11), (12, 14), (3, 4), (3, 5)),
    "medium": ((9, 13), (12, 15), (3, 5), (4, 7)),
    "hard": ((10, 14), (13, 16), (4, 6), (5, 8)),
}

_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
    7: ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    8: (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
}


@dataclass(frozen=True)
class _Scene:
    h: int
    w: int
    red: frozenset[tuple[int, int]]
    green: frozenset[tuple[int, int]]
    yellow: frozenset[tuple[int, int]]
    red_anchor: tuple[int, int]
    green_anchor: tuple[int, int]
    source_template: frozenset[tuple[int, int]]

    @property
    def delta(self) -> tuple[int, int]:
        return (
            self.green_anchor[0] - self.red_anchor[0],
            self.green_anchor[1] - self.red_anchor[1],
        )

    @property
    def occluded_marker_cells(self) -> frozenset[tuple[int, int]]:
        return frozenset(self.source_template & self.yellow)

    @property
    def occlusion(self) -> str:
        return "partial" if self.occluded_marker_cells else "none"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the finite pedagogical schedule slot."""
    del seed, difficulty
    return int(sample_index) % LESSON_SCHEDULE_PERIOD


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _SIZE_BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "marker_size", "yellow_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("occlusion", "vector_direction"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _bbox_top_left(cells: set[tuple[int, int]] | frozenset[tuple[int, int]]) -> tuple[int, int]:
    return min(r for r, _ in cells), min(c for _, c in cells)


def _normalize(cells: set[tuple[int, int]] | frozenset[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    top, left = _bbox_top_left(cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _is_connected(cells: set[tuple[int, int]] | frozenset[tuple[int, int]]) -> bool:
    if not cells:
        return False
    unseen = set(cells)
    seed = min(unseen)
    unseen.remove(seed)
    stack = [seed]
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor in unseen:
                unseen.remove(neighbor)
                stack.append(neighbor)
    return not unseen


def _sign(value: int) -> int:
    return 0 if value == 0 else (1 if value > 0 else -1)


def _direction(dr: int, dc: int) -> str:
    names = {
        (-1, -1): "up_left",
        (-1, 0): "up",
        (-1, 1): "up_right",
        (0, -1): "left",
        (0, 1): "right",
        (1, -1): "down_left",
        (1, 0): "down",
        (1, 1): "down_right",
    }
    key = _sign(dr), _sign(dc)
    if key not in names:
        raise ValueError(f"zero or unsupported vector ({dr}, {dc})")
    return names[key]


def _translate(cells: set[tuple[int, int]] | frozenset[tuple[int, int]], dr: int, dc: int):
    return {(r + dr, c + dc) for r, c in cells}


def _analyze(grid: Any) -> tuple[_Scene | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return None, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be nonempty and rectangular"]
    h, w = len(grid), width
    if h > 30 or w > 30:
        errors.append(f"ARC grid dimensions must be <=30, got {h}x{w}")
    if any(type(value) is not int for row in grid for value in row):
        errors.append("grid values must be integers")
        return None, errors
    bad_colors = sorted({value for row in grid for value in row if value not in (0, 2, 3, 4)})
    if bad_colors:
        errors.append(f"unexpected task color(s): {bad_colors}")
        return None, errors

    red = frozenset(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 2
    )
    green = frozenset(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 3
    )
    yellow = frozenset(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 4
    )
    if not red:
        errors.append("expected a nonempty red source marker")
    if not green:
        errors.append("expected a nonempty green target marker")
    if not yellow:
        errors.append("expected a nonempty yellow object")
    if errors:
        return None, errors

    if not _is_connected(green):
        errors.append("green target marker must be 4-connected")
    if not _is_connected(yellow):
        errors.append("yellow cells must form one 4-connected object")

    red_anchor = _bbox_top_left(red)
    green_anchor = _bbox_top_left(green)
    dr = green_anchor[0] - red_anchor[0]
    dc = green_anchor[1] - red_anchor[1]
    if dr == 0 and dc == 0:
        errors.append("red and green bounding boxes must define a nonzero vector")

    green_shape = _normalize(green)
    source_template = frozenset(
        (red_anchor[0] + rr, red_anchor[1] + cc) for rr, cc in green_shape
    )
    if any(not (0 <= r < h and 0 <= c < w) for r, c in source_template):
        errors.append("green marker shape cannot be reconstructed at the red source anchor")
    extra_red = red - source_template
    if extra_red:
        errors.append("visible red cells do not match the green marker template")
    missing_source = source_template - red
    uncovered_missing = missing_source - yellow
    if uncovered_missing:
        errors.append("red marker differs from green without yellow occlusion explaining the missing cells")
    if len(red) > len(green):
        errors.append("red source marker has more visible cells than the green template")

    shifted_yellow = _translate(yellow, dr, dc)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in shifted_yellow):
        errors.append("red-to-green vector shifts at least one yellow cell out of bounds")

    if errors:
        return None, errors
    return (
        _Scene(
            h=h,
            w=w,
            red=red,
            green=green,
            yellow=yellow,
            red_anchor=red_anchor,
            green_anchor=green_anchor,
            source_template=source_template,
        ),
        [],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked input grammar, including source occlusion."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Validate the canonical-scale manifold used by this generator."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return errors
    strict_errors: list[str] = []
    if not 9 <= scene.h <= 14:
        strict_errors.append(f"grid height {scene.h} is outside canonical-scale range 9..14")
    if not 12 <= scene.w <= 16:
        strict_errors.append(f"grid width {scene.w} is outside canonical-scale range 12..16")
    if not 3 <= len(scene.green) <= 6:
        strict_errors.append(f"marker size {len(scene.green)} is outside 3..6")
    if not 3 <= len(scene.yellow) <= 8:
        strict_errors.append(f"yellow size {len(scene.yellow)} is outside 3..8")
    return strict_errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; the canonical Racket program is authority."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        raise ValueError("rule_mirror expects a lawful scene: " + "; ".join(errors))
    dr, dc = scene.delta
    output = full_grid(scene.h, scene.w, 0)
    for row, col in scene.yellow:
        output[row + dr][col + dc] = 4
    return output


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every exact declared axis from a lawful generated grid."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        raise ValueError("cannot observe exact axes from malformed grid: " + "; ".join(errors))
    dr, dc = scene.delta
    return {
        "grid_h": scene.h,
        "grid_w": scene.w,
        "marker_size": len(scene.green),
        "yellow_size": len(scene.yellow),
        "occlusion": scene.occlusion,
        "vector_direction": _direction(dr, dc),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return {"valid": False, "errors": errors}
    dr, dc = scene.delta
    rows = [r for r, _ in scene.yellow]
    cols = [c for _, c in scene.yellow]
    bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return {
        "valid": True,
        **observe_overrides(grid),
        "delta": (dr, dc),
        "vector_linf": max(abs(dr), abs(dc)),
        "occluded_marker_cells": len(scene.occluded_marker_cells),
        "yellow_bbox_area": bbox_area,
        "yellow_is_bbox_solid": bbox_area == len(scene.yellow),
        "red_visible_size": len(scene.red),
        "source_anchor": scene.red_anchor,
        "target_anchor": scene.green_anchor,
    }


def _blank_like(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return []
    return full_grid(len(grid), len(grid[0]), 0)


def _translate_yellow_with(grid, dr: int, dc: int) -> list[list[int]]:
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    out = full_grid(scene.h, scene.w, 0)
    for row, col in scene.yellow:
        nr, nc = row + dr, col + dc
        if 0 <= nr < scene.h and 0 <= nc < scene.w:
            out[nr][nc] = 4
    return out


def _always_down(grid: list[list[int]]) -> list[list[int]]:
    """Public-only shortcut: preserve horizontal displacement, force dr >= 0."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    dr, dc = scene.delta
    return _translate_yellow_with(grid, abs(dr), dc)


def _equal_visible_markers_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival that refuses to infer red cells hidden by yellow."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    if _normalize(scene.red) != _normalize(scene.green):
        return full_grid(scene.h, scene.w, 0)
    return rule_mirror(grid)


def _translate_filled_yellow_bbox(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival that treats yellow as its solid bounding rectangle."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    dr, dc = scene.delta
    min_r = min(r for r, _ in scene.yellow)
    max_r = max(r for r, _ in scene.yellow)
    min_c = min(c for _, c in scene.yellow)
    max_c = max(c for _, c in scene.yellow)
    out = full_grid(scene.h, scene.w, 0)
    for row in range(min_r, max_r + 1):
        for col in range(min_c, max_c + 1):
            nr, nc = row + dr, col + dc
            if 0 <= nr < scene.h and 0 <= nc < scene.w:
                out[nr][nc] = 4
    return out


def _witness_upward_translation(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("delta", (0, 0))[0] < 0)


def _witness_partial_source_occlusion(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("occlusion") == "partial")


def _witness_irregular_yellow(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and not profile.get("yellow_is_bbox_solid"))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "upward_translation": _witness_upward_translation,
    "partial_source_occlusion": _witness_partial_source_occlusion,
    "irregular_yellow_object": _witness_irregular_yellow,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "always_down": _always_down,
    "equal_visible_markers_only": _equal_visible_markers_only,
    "translate_filled_yellow_bbox": _translate_filled_yellow_bbox,
}

WITNESS_RIVALS = {
    "upward_translation": ["always_down"],
    "partial_source_occlusion": ["equal_visible_markers_only"],
    "irregular_yellow_object": ["translate_filled_yellow_bbox"],
}

# Every canonical labeled pair moves downward, so this rival genuinely matches
# the public evidence.  Scheduled upward examples supply explicit disproof.
CANONICAL_SHORTCUTS = {"always_down": _always_down}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared rival fits all demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not lawful: {errors[0]}")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"{role} input cannot be mirrored: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"{role} output disagrees with the yellow-translation rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def _random_irregular_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Draw a compact connected non-rectangular polyomino containing (0, 0)."""
    for _attempt in range(128):
        cells = {(0, 0)}
        for _step in range(512):
            if len(cells) >= size:
                break
            frontier = set()
            for row, col in cells:
                for dr, dc in _CARDINAL:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in cells:
                        frontier.add((nr, nc))
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        if len(cells) != size or (0, 0) not in cells:
            continue
        shape = tuple(sorted(cells))
        sh, sw = _shape_dims(shape)
        if sh >= 2 and sw >= 2 and sh * sw > size:
            return shape
    return _FALLBACK_SHAPES[size]


def _vector_candidates(direction: str, h: int, w: int, rng) -> list[tuple[int, int]]:
    row_magnitudes = list(range(2, min(5, h - 1) + 1))
    col_magnitudes = list(range(2, min(6, w - 1) + 1))
    diagonals = [(r, c) for r in row_magnitudes for c in col_magnitudes]
    rng.shuffle(diagonals)
    # Canonical-scale vectors first when they are available, without excluding
    # other magnitudes or directions.
    canonical = {(2, 4), (3, 4), (4, 5), (3, 6), (4, 6)}
    diagonals.sort(key=lambda pair: (pair not in canonical, pair[0] + pair[1]))
    rng.shuffle(row_magnitudes)
    rng.shuffle(col_magnitudes)

    if direction == "up_left":
        return [(-r, -c) for r, c in diagonals]
    if direction == "up":
        return [(-r, 0) for r in row_magnitudes]
    if direction == "up_right":
        return [(-r, c) for r, c in diagonals]
    if direction == "left":
        return [(0, -c) for c in col_magnitudes]
    if direction == "right":
        return [(0, c) for c in col_magnitudes]
    if direction == "down_left":
        return [(r, -c) for r, c in diagonals]
    if direction == "down":
        return [(r, 0) for r in row_magnitudes]
    if direction == "down_right":
        return [(r, c) for r, c in diagonals]
    raise ValueError(f"unknown vector_direction {direction!r}")


def _shape_at(shape: tuple[tuple[int, int], ...], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _in_bounds(cells: set[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _place_scene(
    *,
    h: int,
    w: int,
    marker_shape: tuple[tuple[int, int], ...],
    yellow_shape: tuple[tuple[int, int], ...],
    direction: str,
    occlusion: str,
    rng,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]]]:
    mh, mw = _shape_dims(marker_shape)
    yh, yw = _shape_dims(yellow_shape)
    vectors = _vector_candidates(direction, h, w, rng)
    if not vectors:
        raise ValueError(f"grid {h}x{w} cannot realize {direction}")

    for dr, dc in vectors:
        source_anchors = [
            (row, col)
            for row in range(0, h - mh + 1)
            for col in range(0, w - mw + 1)
            if 0 <= row + dr <= h - mh and 0 <= col + dc <= w - mw
        ]
        rng.shuffle(source_anchors)
        for source_top, source_left in source_anchors:
            source = _shape_at(marker_shape, source_top, source_left)
            target = _shape_at(marker_shape, source_top + dr, source_left + dc)
            if source & target:
                continue

            if occlusion == "partial":
                yellow_anchors = {
                    (mr - yr, mc - yc)
                    for mr, mc in source
                    for yr, yc in yellow_shape
                }
                yellow_anchors = list(yellow_anchors)
            else:
                yellow_anchors = [
                    (row, col)
                    for row in range(0, h - yh + 1)
                    for col in range(0, w - yw + 1)
                ]
            rng.shuffle(yellow_anchors)

            for yellow_top, yellow_left in yellow_anchors:
                yellow = _shape_at(yellow_shape, yellow_top, yellow_left)
                if not _in_bounds(yellow, h, w):
                    continue
                if not _in_bounds(_translate(yellow, dr, dc), h, w):
                    continue
                if yellow & target:
                    continue
                overlap = yellow & source
                if occlusion == "none":
                    if overlap:
                        continue
                else:
                    if not overlap or overlap == source:
                        continue
                    if (source_top, source_left) in yellow:
                        continue
                    if not (yellow - source):
                        continue
                return source, target, yellow
    raise ValueError("no lawful marker/yellow placement for requested exact axes")


def _draw_int_axis(ctx, name: str, lo: int, hi: int, scheduled: int | None = None) -> int:
    if ctx.overrides.get(name) is not None:
        valid_ranges = {
            "grid_h": (9, 14),
            "grid_w": (12, 16),
            "marker_size": (3, 6),
            "yellow_size": (3, 8),
        }
        full_lo, full_hi = valid_ranges[name]
        return ctx.draw_int(name, full_lo, full_hi)
    if scheduled is not None:
        valid_ranges = {
            "grid_h": (9, 14),
            "grid_w": (12, 16),
            "marker_size": (3, 6),
            "yellow_size": (3, 8),
        }
        full_lo, full_hi = valid_ranges[name]
        if not full_lo <= scheduled <= full_hi:
            raise ValueError(
                f"scheduled {name}={scheduled} outside [{full_lo}, {full_hi}]"
            )
        return int(ctx.draw_choice(name, (scheduled,)))
    return ctx.draw_int(name, lo, hi)


def _draw_choice_axis(ctx, name: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def mutation_fixtures():
    """Task-linked destructive examples that structural validation must reject."""
    base = generate(
        203101,
        0,
        grid_h=10,
        grid_w=14,
        marker_size=5,
        yellow_size=6,
        occlusion="none",
        vector_direction="down_right",
    )

    def clone():
        return [row[:] for row in base]

    missing_red = clone()
    for row in range(len(missing_red)):
        for col in range(len(missing_red[0])):
            if missing_red[row][col] == 2:
                missing_red[row][col] = 0

    missing_green = clone()
    for row in range(len(missing_green)):
        for col in range(len(missing_green[0])):
            if missing_green[row][col] == 3:
                missing_green[row][col] = 0

    wrong_green = clone()
    gr, gc = next(
        (r, c)
        for r, values in enumerate(wrong_green)
        for c, value in enumerate(values)
        if value == 3
    )
    wrong_green[gr][gc] = 0

    disconnected_yellow = clone()
    for row in range(len(disconnected_yellow)):
        for col in range(len(disconnected_yellow[0])):
            if disconnected_yellow[row][col] == 4:
                disconnected_yellow[row][col] = 0
    disconnected_yellow[0][0] = 4
    disconnected_yellow[0][1] = 4
    disconnected_yellow[-1][-1] = 4

    out_of_bounds = clone()
    for row in range(len(out_of_bounds)):
        for col in range(len(out_of_bounds[0])):
            if out_of_bounds[row][col] == 4:
                out_of_bounds[row][col] = 0
    out_of_bounds[-1][-1] = 4
    out_of_bounds[-1][-2] = 4
    out_of_bounds[-2][-1] = 4

    unknown_color = clone()
    unknown_color[0][0] = 9

    return [
        ("missing_red_source_marker", missing_red),
        ("missing_green_target_marker", missing_green),
        ("green_no_longer_matches_source_template", wrong_green),
        ("disconnected_yellow_object", disconnected_yellow),
        ("translated_yellow_leaves_grid", out_of_bounds),
        ("unexpected_task_color", unknown_color),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    anchor = slot in _CANONICAL_ANCHOR_SLOTS
    (h_band, w_band, marker_band, yellow_band) = _SIZE_BANDS[difficulty]

    anchor_rng = ctx.draw_rng("canonical_anchor_axes")
    scheduled_h = anchor_rng.choice((9, 10, 11)) if anchor else None
    scheduled_w = anchor_rng.choice((12, 13, 14, 15)) if anchor else None
    scheduled_marker = anchor_rng.choice((3, 4, 5)) if anchor else None
    scheduled_yellow = anchor_rng.choice((4, 5, 8)) if anchor else None

    h = _draw_int_axis(ctx, "grid_h", *h_band, scheduled_h)
    w = _draw_int_axis(ctx, "grid_w", *w_band, scheduled_w)
    marker_size = _draw_int_axis(ctx, "marker_size", *marker_band, scheduled_marker)
    yellow_size = _draw_int_axis(ctx, "yellow_size", *yellow_band, scheduled_yellow)
    occlusion = _draw_choice_axis(
        ctx,
        "occlusion",
        _OCCLUSIONS,
        _OCCLUSION_SCHEDULE[slot],
    )
    vector_direction = _draw_choice_axis(
        ctx,
        "vector_direction",
        _DIRECTIONS,
        _DIRECTION_SCHEDULE[slot],
    )

    marker_rng = ctx.draw_rng("marker_shape")
    yellow_rng = ctx.draw_rng("yellow_shape")
    layout_rng = ctx.draw_rng("layout")
    last_error: Exception | None = None

    for _attempt in range(128):
        marker_shape = _random_irregular_shape(marker_rng, marker_size)
        yellow_shape = _random_irregular_shape(yellow_rng, yellow_size)
        try:
            source, target, yellow = _place_scene(
                h=h,
                w=w,
                marker_shape=marker_shape,
                yellow_shape=yellow_shape,
                direction=vector_direction,
                occlusion=occlusion,
                rng=layout_rng,
            )
        except ValueError as exc:
            last_error = exc
            continue

        grid = full_grid(h, w, 0)
        for row, col in source:
            grid[row][col] = 2
        for row, col in target:
            grid[row][col] = 3
        for row, col in yellow:
            grid[row][col] = 4

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            last_error = ValueError("; ".join(errors))
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": h,
            "grid_w": w,
            "marker_size": marker_size,
            "yellow_size": yellow_size,
            "occlusion": occlusion,
            "vector_direction": vector_direction,
        }
        if observed != expected:
            raise AssertionError(f"exact-axis round trip failed: {expected=} {observed=}")
        return grid

    raise ValueError(f"could not realize requested exact axes: {last_error}")
