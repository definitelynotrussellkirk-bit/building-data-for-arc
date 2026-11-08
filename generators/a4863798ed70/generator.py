"""Curriculum generator for cycling icon colors around red frames.

The visible input grammar mirrors the canonical task: a gray rectangular track
connects three to five separate hollow red frames, and each frame contains one
shape in a distinct color.  The authority leaves geometry untouched and gives
each frame the icon color of the next frame in clockwise order.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4863798ed70"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0fa1a0b083d0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Find the separate hollow red(2) square frames, order their centers "
    "clockwise around the shared centroid, and recolor every icon so frame i "
    "receives the icon color from frame i+1. The gray(1) connecting track, "
    "red frames, icon shapes, and all positions stay fixed."
)

INVARIANTS = [
    "background is black 0 and the connecting track is gray 1",
    "there are 3..5 separate equal-size hollow red(2) square frames",
    "frame size is 5x5 or 7x7 and every frame contains exactly one icon color",
    "icon colors are pairwise distinct and excluded from 0, 1, and 2",
    "all non-background cells form one four-connected scene through the gray track",
    "the output changes icon colors only, using the next clockwise frame's color",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# One observable joint axis preserves the linked canonical dimensions, frame
# count, frame size, and palette size.  Splitting these into independent axes
# would advertise many impossible or non-canonical cross-products.
PROFILE_SPECS: dict[str, tuple[int, int, int, int]] = {
    "canonical_3x5_20x22": (20, 22, 3, 5),
    "canonical_4x5_22x21": (22, 21, 4, 5),
    "generalized_5x5_24x25": (24, 25, 5, 5),
    "canonical_3x7_26x26": (26, 26, 3, 7),
    "generalized_4x7_25x24": (25, 24, 4, 7),
    "canonical_5x7_27x27": (27, 27, 5, 7),
    "generalized_4x5_23x24": (23, 24, 4, 5),
}
PROFILE_NAMES = tuple(PROFILE_SPECS)
_PROFILE_BY_FACTS = {facts: name for name, facts in PROFILE_SPECS.items()}
CANONICAL_PROFILES = frozenset(
    {
        "canonical_3x5_20x22",
        "canonical_4x5_22x21",
        "canonical_3x7_26x26",
        "canonical_5x7_27x27",
    }
)

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "seven-slot linked schedule",
        "valid": (
            "canonical_3x5_20x22",
            "canonical_4x5_22x21",
            "generalized_5x5_24x25",
            "canonical_3x7_26x26",
            "generalized_4x7_25x24",
            "canonical_5x7_27x27",
            "generalized_4x5_23x24",
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Four of seven scheduled profiles exactly match the empirical canonical linked
# manifold in every difficulty band.
MIN_STRICT_FRAC = 0.45
SCHEDULE_PROFILES = tuple(range(len(PROFILE_NAMES)))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Expose the deterministic seven-slot curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(
    seed: int,
    sample_index: int,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    value = overrides.get("scene_profile")
    if value is not None and type(value) is not str:
        raise ValueError("scene_profile must be a string")


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components_of_color(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cell = (r + dr, c + dc)
                if cell in remaining:
                    remaining.remove(cell)
                    component.add(cell)
                    stack.append(cell)
        result.append(component)
    return result


def _nonzero_component_count(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cell = (r + dr, c + dc)
                if cell in remaining:
                    remaining.remove(cell)
                    stack.append(cell)
    return count


def _frame_facts(grid: list[list[int]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Independently recover red frames and their icon colors from a grid."""
    errors = _grid_errors(grid)
    if errors:
        return [], errors

    frames: list[dict[str, Any]] = []
    for index, component in enumerate(_components_of_color(grid, 2)):
        rows = [cell[0] for cell in component]
        cols = [cell[1] for cell in component]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        if height != width or height not in (5, 7):
            errors.append(
                f"red component {index} must be a 5x5 or 7x7 square frame; found {height}x{width}"
            )
            continue
        border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if component != border:
            errors.append(f"red component {index} is not an exact hollow square border")
            continue

        interior = [
            (r, c)
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
        ]
        if any(grid[r][c] == 1 for r, c in interior):
            errors.append(f"frame {index} contains gray track cells in its interior")
        icon_colors = {
            grid[r][c]
            for r, c in interior
            if grid[r][c] not in (0, 1, 2)
        }
        if len(icon_colors) != 1:
            errors.append(
                f"frame {index} must contain exactly one non-{{0,1,2}} icon color; found {sorted(icon_colors)}"
            )
            continue
        icon_color = next(iter(icon_colors))
        icon_cells = {(r, c) for r, c in interior if grid[r][c] == icon_color}
        canonical_range = (3, 5) if height == 5 else (8, 10)
        if not canonical_range[0] <= len(icon_cells) <= canonical_range[1]:
            errors.append(
                f"frame {index} icon has {len(icon_cells)} cells; expected {canonical_range[0]}..{canonical_range[1]} for {height}x{height}"
            )
        unexpected = {
            grid[r][c]
            for r, c in interior
            if grid[r][c] not in (0, icon_color)
        }
        if unexpected:
            errors.append(f"frame {index} interior contains unexpected colors {sorted(unexpected)}")
        frames.append(
            {
                "bbox": (r1, c1, r2, c2),
                "size": height,
                "center": ((r1 + r2) / 2.0, (c1 + c2) / 2.0),
                "icon_color": icon_color,
                "icon_cells": icon_cells,
            }
        )
    return frames, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical structural input grammar and reject mutations."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    if not 20 <= h <= 27 or not 20 <= w <= 27:
        errors.append(f"grid dimensions {h}x{w} outside supported 20..27 envelope")

    values = {value for row in grid for value in row}
    if not {0, 1, 2} <= values:
        errors.append("input must contain background 0, gray track 1, and red frames 2")

    frames, frame_errors = _frame_facts(grid)
    errors.extend(frame_errors)
    if not 3 <= len(frames) <= 5:
        errors.append(f"expected 3..5 red frames; found {len(frames)}")
    sizes = {frame["size"] for frame in frames}
    if len(sizes) > 1:
        errors.append(f"all red frames must share one size; found {sorted(sizes)}")

    icon_colors = [frame["icon_color"] for frame in frames]
    if len(icon_colors) != len(set(icon_colors)):
        errors.append("icon colors must be pairwise distinct across frames")

    covered_icon_cells = set().union(*(frame["icon_cells"] for frame in frames)) if frames else set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 1, 2) and (r, c) not in covered_icon_cells:
                errors.append(f"icon color {value} occurs outside its recovered frame at {(r, c)}")
                break
        if errors and errors[-1].startswith("icon color"):
            break

    if _nonzero_component_count(grid) != 1:
        errors.append("all non-background cells must form one four-connected scene")

    if frames:
        cr = sum(frame["center"][0] for frame in frames) / len(frames)
        cc = sum(frame["center"][1] for frame in frames) / len(frames)
        keys = [_clockwise_key(frame["center"], cr, cc) for frame in frames]
        if len(set(keys)) != len(keys):
            errors.append("frame centers must have distinct clockwise ordering keys")
    return errors


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    frames, _ = _frame_facts([list(row) for row in grid])
    facts = (len(grid), len(grid[0]), len(frames), frames[0]["size"])
    profile = _PROFILE_BY_FACTS.get(facts)
    if profile is None:
        raise ValueError(f"no declared scene_profile matches recovered facts {facts}")
    return {"scene_profile": profile}


def strict_canonical_like(grid) -> list[str]:
    """Match the exact linked dimension/count/frame-size canonical manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    try:
        profile = observe_overrides(grid)["scene_profile"]
    except ValueError as exc:
        return [str(exc)]
    if profile not in CANONICAL_PROFILES:
        reasons.append("linked dimensions, frame count, and frame size are outside canonical profiles")
    return reasons


def _clockwise_key(center: tuple[float, float], centroid_r: float, centroid_c: float) -> float:
    """Mirror the Racket authority's quadrant-plus-slope sort exactly."""
    dr = center[0] - centroid_r
    dc = center[1] - centroid_c
    if dr < 0 and dc >= 0:
        quadrant = 0
    elif dr >= 0 and dc > 0:
        quadrant = 1
    elif dr > 0 and dc <= 0:
        quadrant = 2
    else:
        quadrant = 3
    slope = -99999.0 if dc == 0 else dr / dc
    return quadrant * 100000.0 + slope


def _ordered_frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    frames, errors = _frame_facts(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    cr = sum(frame["center"][0] for frame in frames) / len(frames)
    cc = sum(frame["center"][1] for frame in frames) / len(frames)
    return sorted(frames, key=lambda frame: _clockwise_key(frame["center"], cr, cc))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror only; the Racket rule remains output authority."""
    ordered = _ordered_frames(grid)
    colors = [frame["icon_color"] for frame in ordered]
    mapping = {color: colors[(index + 1) % len(colors)] for index, color in enumerate(colors)}
    return [[mapping.get(value, value) for value in row] for row in grid]


def _rival_reverse_cycle(grid: list[list[int]]) -> list[list[int]]:
    ordered = _ordered_frames(grid)
    colors = [frame["icon_color"] for frame in ordered]
    mapping = {color: colors[(index - 1) % len(colors)] for index, color in enumerate(colors)}
    return [[mapping.get(value, value) for value in row] for row in grid]


def _rival_reading_order_cycle(grid: list[list[int]]) -> list[list[int]]:
    frames, errors = _frame_facts(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    ordered = sorted(frames, key=lambda frame: (frame["bbox"][0], frame["bbox"][1]))
    colors = [frame["icon_color"] for frame in ordered]
    mapping = {color: colors[(index + 1) % len(colors)] for index, color in enumerate(colors)}
    return [[mapping.get(value, value) for value in row] for row in grid]


def _rival_rotate_shapes(grid: list[list[int]]) -> list[list[int]]:
    """Plausible but wrong: move each icon mask instead of only its color."""
    ordered = _ordered_frames(grid)
    out = [row[:] for row in grid]
    masks: list[set[tuple[int, int]]] = []
    for frame in ordered:
        r1, c1, _, _ = frame["bbox"]
        masks.append({(r - r1, c - c1) for r, c in frame["icon_cells"]})
        for r, c in frame["icon_cells"]:
            out[r][c] = 0
    for index, frame in enumerate(ordered):
        r1, c1, _, _ = frame["bbox"]
        color = ordered[(index + 1) % len(ordered)]["icon_color"]
        for dr, dc in masks[(index + 1) % len(masks)]:
            out[r1 + dr][c1 + dc] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reverse_clockwise_direction": _rival_reverse_cycle,
    "reading_order_cycle": _rival_reading_order_cycle,
    "move_icon_shapes": _rival_rotate_shapes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    return lambda grid: not self_check(grid) and rule_mirror(grid) != rival(grid)


def _witness_frame_count(count: int):
    def witness(grid) -> bool:
        if self_check(grid):
            return False
        frames, _ = _frame_facts([list(row) for row in grid])
        return len(frames) == count

    return witness


def _witness_frame_size(size: int):
    def witness(grid) -> bool:
        if self_check(grid):
            return False
        frames, _ = _frame_facts([list(row) for row in grid])
        return bool(frames) and frames[0]["size"] == size

    return witness


SEMANTIC_WITNESSES = {
    "direction_not_reverse": _differs_from(_rival_reverse_cycle),
    "geometry_not_reading_order": _differs_from(_rival_reading_order_cycle),
    "colors_not_shapes_move": _differs_from(_rival_rotate_shapes),
}

WITNESS_RIVALS = {
    "direction_not_reverse": ["reverse_clockwise_direction"],
    "geometry_not_reading_order": ["reading_order_cycle"],
    "colors_not_shapes_move": ["move_icon_shapes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid demonstrations that eliminate every named rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is malformed: {'; '.join(errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the clockwise color cycle")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append("query is malformed: " + "; ".join(errors))
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the clockwise color cycle")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons


def _profile_positions(h: int, w: int, count: int, size: int, variant: int) -> list[tuple[int, int]]:
    """Place frames on the four sides of one rectangular track."""
    center_c = (w - size) // 2
    center_r = (h - size) // 2
    shift = (-1, 0, 1)[variant % 3]

    top = (0, max(1, min(w - size - 1, center_c + shift)))
    right = (max(1, min(h - size - 1, center_r - shift)), w - size)
    bottom = (h - size, max(1, min(w - size - 1, center_c - shift)))
    left = (max(1, min(h - size - 1, center_r + shift)), 0)
    if count == 3:
        return [top, right, bottom]
    if count == 4:
        return [top, right, bottom, left]

    top_left_c = 2 + (variant % 2)
    top_right_c = w - size - 2 - ((variant + 1) % 2)
    return [
        (0, top_right_c),
        right,
        bottom,
        left,
        (0, top_left_c),
    ]


def _draw_track(grid: list[list[int]], size: int) -> None:
    h, w = len(grid), len(grid[0])
    half = size // 2
    top, bottom = half, h - half - 1
    left, right = half, w - half - 1
    for c in range(left, right + 1):
        grid[top][c] = 1
        grid[bottom][c] = 1
    for r in range(top, bottom + 1):
        grid[r][left] = 1
        grid[r][right] = 1


def _draw_frame(grid: list[list[int]], r1: int, c1: int, size: int) -> None:
    r2, c2 = r1 + size - 1, c1 + size - 1
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if r in (r1, r2) or c in (c1, c2):
                grid[r][c] = 2
            else:
                grid[r][c] = 0


def _icon_target(size: int, difficulty: Any, index: int) -> int:
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    if size == 5:
        table = {
            "easy": (3, 4),
            "medium": (4, 5),
            "hard": (5, 4),
        }
    else:
        table = {
            "easy": (8, 9),
            "medium": (9, 10),
            "hard": (10, 9),
        }
    return table[band][index % 2]


def _icon_mask(inner: int, target: int, rng, style: int) -> set[tuple[int, int]]:
    cells = [(r, c) for r in range(inner) for c in range(inner)]
    boundary = [
        (r, c)
        for r, c in cells
        if r in (0, inner - 1) or c in (0, inner - 1)
    ]
    anchor = boundary[rng.randrange(len(boundary))]

    def connected_growth(count: int) -> set[tuple[int, int]]:
        selected = {anchor}
        while len(selected) < count:
            frontier = {
                (r + dr, c + dc)
                for r, c in selected
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= r + dr < inner and 0 <= c + dc < inner
            } - selected
            options = sorted(frontier)
            selected.add(options[rng.randrange(len(options))])
        return selected

    if style % 3 == 0:
        # Connected growth starts against the red border, so the whole icon is
        # part of the canonical single non-background scene.
        return connected_growth(target)
    if style % 3 == 1:
        # Sparse canonical icons may have several components, but every
        # component touches the red frame.  Sampling the interior perimeter
        # reproduces that property without floating pixels.
        choices = boundary[:]
        rng.shuffle(choices)
        return set(choices[:target])

    # A compact branch plus one border-attached satellite gives a third
    # morphology while preserving scene connectivity through the red frame.
    selected = connected_growth(max(1, target - 1))
    choices = [cell for cell in boundary if cell not in selected]
    if choices:
        selected.add(choices[rng.randrange(len(choices))])
    while len(selected) < target:
        options = [cell for cell in boundary if cell not in selected]
        selected.add(options[rng.randrange(len(options))])
    return selected


def _add_track_spurs(
    grid: list[list[int]],
    frame_boxes: list[tuple[int, int, int, int]],
    count: int,
    rng,
) -> None:
    if count <= 0:
        return
    h, w = len(grid), len(grid[0])

    def inside_frame(r: int, c: int) -> bool:
        return any(r1 <= r <= r2 and c1 <= c <= c2 for r1, c1, r2, c2 in frame_boxes)

    candidates: list[tuple[int, int, int, int]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0 and not inside_frame(rr, cc):
                    candidates.append((rr, cc, dr, dc))
    rng.shuffle(candidates)
    used: set[tuple[int, int]] = set()
    for r, c, dr, dc in candidates:
        if len(used) >= count:
            break
        if (r, c) in used:
            continue
        grid[r][c] = 1
        used.add((r, c))
        rr, cc = r + dr, c + dc
        if (
            len(used) < count
            and 0 <= rr < h
            and 0 <= cc < w
            and grid[rr][cc] == 0
            and not inside_frame(rr, cc)
        ):
            grid[rr][cc] = 1
            used.add((rr, cc))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic authority-valid input; Racket owns output."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = PROFILE_NAMES[schedule_profile(seed, sample_index, difficulty)]
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    h, w, frame_count, frame_size = PROFILE_SPECS[profile]

    grid = full_grid(h, w, 0)
    _draw_track(grid, frame_size)
    variant_rng = ctx.draw_rng("layout_variant")
    variant = variant_rng.randrange(3)
    positions = _profile_positions(h, w, frame_count, frame_size, variant)
    boxes: list[tuple[int, int, int, int]] = []
    for r, c in positions:
        _draw_frame(grid, r, c, frame_size)
        boxes.append((r, c, r + frame_size - 1, c + frame_size - 1))

    icon_colors = ctx.draw_distinct_colors(
        "icon_colors",
        n=frame_count,
        exclude={0, 1, 2},
    )
    inner = frame_size - 2
    for index, ((r1, c1, _, _), color) in enumerate(zip(boxes, icon_colors)):
        target = _icon_target(frame_size, difficulty, index)
        shape_rng = ctx.draw_rng(f"icon_shape_{index}")
        style_rng = ctx.draw_rng(f"icon_style_{index}")
        mask = _icon_mask(inner, target, shape_rng, style_rng.randrange(3))
        for dr, dc in mask:
            grid[r1 + 1 + dr][c1 + 1 + dc] = color

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    spur_cells = {"easy": 0, "medium": 2, "hard": 4}[band]
    _add_track_spurs(grid, boxes, spur_cells, ctx.draw_rng("track_spurs"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid generator instance: " + "; ".join(errors))
    return [row[:] for row in grid]
