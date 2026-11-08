"""Generator for 2d59c1b766d5: fill local chambers from colored gates.

Each input contains two exact rectangular color-8 frames.  A frame encloses
color-5 walls, one colored gate, and zero cells.  The target rule flood-fills
only the zero cells reachable from that frame's gate by four-neighbor motion;
frame borders and gray walls block movement.

Five demonstrations plus one query use a period-three schedule.  The six pairs
contain two examples of every topology, so every query rotation leaves evidence
for all three:

* ``open``: all free interior cells are connected (canonical-like anchor);
* ``sealed``: a solid wall creates a genuinely unreachable chamber;
* ``diagonal``: a stepped wall separates under four-neighbor movement but not
  under eight-neighbor movement.

The latter two profiles refute the strongest shortcuts that fit every canonical
pair: filling every non-wall interior zero, and using eight-neighbor flood fill.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d59c1b766d5"
TASK_ID = GENERATOR_ID
RULE_HASH = "61c97755a0ea"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3

SUMMARY = (
    "Two color-8 rectangular frames contain gray walls and one colored gate. "
    "Flood only gate-reachable zeros with four-neighbor movement. Scheduled "
    "open, sealed, and diagonal-wall profiles make reachability and the "
    "four-neighbor convention identifiable under every query rotation."
)

INVARIANTS = [
    "the canvas is 15..17 by 20..22 and uses only ARC integer colors",
    "there are exactly two disjoint exact rectangular color-8 frames",
    "each frame interior has one gate, 5..7 gray wall cells, and at least one zero",
    "both frames share one observable topology profile: open, sealed, or diagonal",
    "five demonstrations plus one query contain every profile after any holdout",
]

SCHEDULE_PROFILES = ("open", "sealed", "diagonal")
GATE_COLORS = (2, 3, 4, 6, 7, 9)
ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = DIR4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "15..17 (difficulty-weighted)",
        "valid": "15..17",
        "doc": "Exact returned canvas height.",
    },
    "grid_w": {
        "type": "int",
        "default": "20..22 (difficulty-weighted)",
        "valid": "20..22",
        "doc": "Exact returned canvas width.",
    },
    "profile": {
        "type": "enum",
        "default": "period-three open|sealed|diagonal schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": "Exact recoverable interior connectivity topology.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the period-three semantic profile for this lesson position."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, lo, hi in (("grid_h", 15, 17), ("grid_w", 20, 22)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value!r} is outside [{lo}, {hi}]")

    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        if type(value) is not str or value not in SCHEDULE_PROFILES:
            raise ValueError(
                f"profile must be one of {SCHEDULE_PROFILES}, got {value!r}"
            )


def _draw_axis(ctx, name: str, difficulty, domain: tuple[int, ...]) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, domain)
    options = {
        "grid_h": {
            None: domain,
            "easy": (15, 16),
            "medium": domain,
            "hard": (16, 17),
        },
        "grid_w": {
            None: domain,
            "easy": (20, 21),
            "medium": domain,
            "hard": (21, 22),
        },
    }[name][difficulty]
    return ctx.draw_choice(name, options)


def _draw_profile(ctx, seed, sample_index, difficulty) -> str:
    if "profile" in ctx.overrides and ctx.overrides["profile"] is not None:
        return ctx.draw_choice("profile", SCHEDULE_PROFILES)
    return ctx.draw_choice(
        "profile", (schedule_profile(seed, sample_index, difficulty),)
    )


def _neighbors(cell: tuple[int, int], directions):
    r, c = cell
    for dr, dc in directions:
        yield r + dr, c + dc


def _cell_components(cells: Iterable[tuple[int, int]], directions=DIR4):
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        component = {start}
        for cell in queue:
            for nxt in _neighbors(cell, directions):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d4_variants(cells: Iterable[tuple[int, int]]):
    current = tuple(cells)
    variants = set()
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((r, -c) for r, c in current))
        current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _free_profile(height: int, width: int, walls: set[tuple[int, int]]) -> str:
    free = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in walls
    }
    n4 = len(_cell_components(free, DIR4))
    n8 = len(_cell_components(free, DIR8))
    if n4 == 1:
        return "open"
    if n8 == 1:
        return "diagonal"
    return "sealed"


@lru_cache(maxsize=None)
def _wall_candidates(height: int, width: int, profile: str):
    candidates: set[tuple[tuple[int, int], ...]] = set()

    if profile == "open":
        base = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
        for shape in _d4_variants(base):
            sh = 1 + max(r for r, _ in shape)
            sw = 1 + max(c for _, c in shape)
            for top in range(height - sh + 1):
                for left in range(width - sw + 1):
                    walls = tuple(sorted((top + r, left + c) for r, c in shape))
                    if _free_profile(height, width, set(walls)) == profile:
                        candidates.add(walls)

    elif profile == "sealed":
        for col in range(1, width - 1):
            walls = tuple((row, col) for row in range(height))
            if _free_profile(height, width, set(walls)) == profile:
                candidates.add(walls)
        for row in range(1, height - 1):
            walls = tuple((row, col) for col in range(width))
            if _free_profile(height, width, set(walls)) == profile:
                candidates.add(walls)

    elif profile == "diagonal":
        # A one-cell shift creates a diagonal corner: it blocks DIR4 movement,
        # while a DIR8 path can cross at the corner.  Generate both vertical
        # and horizontal spanning versions and both shift directions.
        for split in range(1, height):
            for col in range(width - 1):
                for reverse in (False, True):
                    walls = tuple(
                        (row, col + ((row >= split) ^ reverse))
                        for row in range(height)
                    )
                    if _free_profile(height, width, set(walls)) == profile:
                        candidates.add(tuple(sorted(walls)))
        for split in range(1, width):
            for row in range(height - 1):
                for reverse in (False, True):
                    walls = tuple(
                        (row + ((col >= split) ^ reverse), col)
                        for col in range(width)
                    )
                    if _free_profile(height, width, set(walls)) == profile:
                        candidates.add(tuple(sorted(walls)))
    else:
        raise ValueError(f"unknown profile {profile!r}")

    ordered = tuple(sorted(candidates))
    if not ordered:
        raise RuntimeError(
            f"no {profile!r} wall candidates for interior {height}x{width}"
        )
    return ordered


def _draw_frame(grid, box) -> None:
    r0, c0, r1, c1 = box
    for col in range(c0, c1 + 1):
        grid[r0][col] = 8
        grid[r1][col] = 8
    for row in range(r0, r1 + 1):
        grid[row][c0] = 8
        grid[row][c1] = 8


def _choose_boxes(height: int, width: int, rng):
    frame_h = (rng.choice((7, 8)), rng.choice((7, 8)))
    frame_w = (rng.choice((7, 8, 9)), rng.choice((7, 8, 9)))

    horizontal = []
    for left in range(0, min(4, width - frame_w[0] + 1)):
        for right in range(left + frame_w[0] + 1, width - frame_w[1] + 1):
            gap = right - (left + frame_w[0])
            trailing = width - (right + frame_w[1])
            if 1 <= gap <= 4 and trailing <= 3:
                horizontal.append((left, right))
    if not horizontal:
        raise RuntimeError("no legal two-frame horizontal layout")
    left, right = rng.choice(horizontal)
    top0 = rng.randint(0, height - frame_h[0])
    top1 = rng.randint(0, height - frame_h[1])
    return (
        (top0, left, top0 + frame_h[0] - 1, left + frame_w[0] - 1),
        (top1, right, top1 + frame_h[1] - 1, right + frame_w[1] - 1),
    )


def _populate_frame(grid, box, profile: str, color: int, rng) -> None:
    r0, c0, r1, c1 = box
    interior_h = r1 - r0 - 1
    interior_w = c1 - c0 - 1
    walls = set(rng.choice(_wall_candidates(interior_h, interior_w, profile)))
    for row, col in walls:
        grid[r0 + 1 + row][c0 + 1 + col] = 5

    free = {
        (row, col)
        for row in range(interior_h)
        for col in range(interior_w)
        if (row, col) not in walls
    }
    components = [comp for comp in _cell_components(free, DIR4) if len(comp) >= 2]
    if not components:
        raise RuntimeError("wall topology left no fillable gate component")
    component = rng.choice(sorted(components, key=lambda x: tuple(sorted(x))))
    gate = rng.choice(sorted(component))
    grid[r0 + 1 + gate[0]][c0 + 1 + gate[1]] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, "grid_h", difficulty, (15, 16, 17))
    width = _draw_axis(ctx, "grid_w", difficulty, (20, 21, 22))
    profile = _draw_profile(ctx, seed, sample_index, difficulty)

    layout_rng = ctx.draw_rng("frame_layout")
    boxes = _choose_boxes(height, width, layout_rng)
    colors = ctx.draw_rng("gate_colors").sample(GATE_COLORS, 2)

    grid = full_grid(height, width, 0)
    for box in boxes:
        _draw_frame(grid, box)
    for index, (box, color) in enumerate(zip(boxes, colors)):
        _populate_frame(
            grid,
            box,
            profile,
            color,
            ctx.draw_rng(f"frame_{index}_{profile}"),
        )
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        return [f"grid contains non-ARC value at {bad[0][:2]}: {bad[0][2]!r}"]
    return []


def _frame_boxes(grid):
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    if not cells:
        return [], ["no color-8 frame cells"]
    boxes = []
    errors = []
    for component in _cell_components(cells, DIR4):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3 or component != border:
            errors.append(
                f"color-8 component at {(r0, c0, r1, c1)} is not an exact frame"
            )
        else:
            boxes.append((r0, c0, r1, c1))
    return sorted(boxes), errors


def _frame_info(grid, box):
    r0, c0, r1, c1 = box
    gates = []
    walls = set()
    zeros = set()
    invalid = []
    for row in range(r0 + 1, r1):
        for col in range(c0 + 1, c1):
            value = grid[row][col]
            if value == 0:
                zeros.add((row, col))
            elif value == 5:
                walls.add((row, col))
            elif value in GATE_COLORS:
                gates.append((row, col, value))
            else:
                invalid.append((row, col, value))

    free = zeros | {(r, c) for r, c, _ in gates}
    n4 = len(_cell_components(free, DIR4)) if free else 0
    n8 = len(_cell_components(free, DIR8)) if free else 0
    profile = "open" if n4 == 1 else "diagonal" if n4 > 1 and n8 == 1 else "sealed"
    return {
        "box": box,
        "gates": gates,
        "walls": walls,
        "zeros": zeros,
        "invalid": invalid,
        "n4": n4,
        "n8": n8,
        "profile": profile,
    }


def _analysis(grid):
    errors = _grid_errors(grid)
    if errors:
        return None, errors
    height, width = len(grid), len(grid[0])
    boxes, frame_errors = _frame_boxes(grid)
    errors.extend(frame_errors)
    if len(boxes) != 2:
        errors.append(f"expected exactly 2 exact color-8 frames, found {len(boxes)}")

    infos = [_frame_info(grid, box) for box in boxes]
    covered = set()
    for box in boxes:
        r0, c0, r1, c1 = box
        covered.update(
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        )
    outside = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(width)
        if (r, c) not in covered and grid[r][c] != 0
    ]
    if outside:
        errors.append(f"nonzero cell outside frames at {outside[0][:2]}")

    for info in infos:
        r0, c0, r1, c1 = info["box"]
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if not 7 <= fh <= 8 or not 7 <= fw <= 9:
            errors.append(f"frame {info['box']} must be 7..8 by 7..9")
        if info["invalid"]:
            errors.append(
                f"frame {info['box']} has illegal interior value {info['invalid'][0][2]}"
            )
        if len(info["gates"]) != 1:
            errors.append(
                f"frame {info['box']} must contain exactly one gate, found {len(info['gates'])}"
            )
        if not 5 <= len(info["walls"]) <= 7:
            errors.append(
                f"frame {info['box']} must contain 5..7 gray walls, found {len(info['walls'])}"
            )
        if not info["zeros"]:
            errors.append(f"frame {info['box']} has no zero cell to fill")
        if info["n4"] < 1:
            errors.append(f"frame {info['box']} has no traversable region")
        if len(info["gates"]) == 1:
            gate = info["gates"][0][:2]
            component = next(
                (comp for comp in _cell_components(info["zeros"] | {gate}, DIR4) if gate in comp),
                set(),
            )
            if len(component) < 2:
                errors.append(f"frame {info['box']} gate reaches no zero cell")

    if infos and len({info["profile"] for info in infos}) != 1:
        errors.append("both frames must share the same connectivity profile")
    return {"boxes": boxes, "frames": infos}, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in ALLOWED_DIFFICULTIES:
        return ["difficulty must be easy, medium, hard, or None"]
    _, errors = _analysis(grid)
    return errors


def strict_canonical_like(grid):
    analysis, errors = _analysis(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 15 <= height <= 17:
        errors.append(f"canvas height {height} is outside canonical range 15..17")
    if not 20 <= width <= 22:
        errors.append(f"canvas width {width} is outside canonical range 20..22")
    if analysis is None:
        errors.append("analysis unavailable")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis, errors = _analysis(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    profiles = {info["profile"] for info in analysis["frames"]}
    if len(profiles) != 1:
        raise ValueError("frames do not share one observable profile")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "profile": next(iter(profiles)),
    }


def _flood_output(grid, directions):
    out = deepcopy(grid)
    boxes, _ = _frame_boxes(grid)
    for r0, c0, r1, c1 in boxes:
        gates = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5, 8)
        ]
        if not gates:
            continue
        gate = gates[0]
        color = grid[gate[0]][gate[1]]
        seen = {gate}
        queue = deque([gate])
        while queue:
            cell = queue.popleft()
            for nr, nc in _neighbors(cell, directions):
                if not (r0 < nr < r1 and c0 < nc < c1):
                    continue
                if (nr, nc) in seen or grid[nr][nc] not in (0, color):
                    continue
                seen.add((nr, nc))
                queue.append((nr, nc))
        for row, col in seen:
            out[row][col] = color
    return out


def rule_output(grid):
    """Independent Python mirror of the pinned canonical Racket rule."""
    return _flood_output(grid, DIR4)


def _rival_fill_all_interior(grid):
    out = deepcopy(grid)
    boxes, _ = _frame_boxes(grid)
    for r0, c0, r1, c1 in boxes:
        gates = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5, 8)
        ]
        if not gates:
            continue
        color = grid[gates[0][0]][gates[0][1]]
        for row in range(r0 + 1, r1):
            for col in range(c0 + 1, c1):
                if grid[row][col] == 0:
                    out[row][col] = color
    return out


def _rival_eight_neighbor_flood(grid):
    return _flood_output(grid, DIR8)


def _witness_unreachable_chamber(grid) -> bool:
    return rule_output(grid) != _rival_fill_all_interior(grid)


def _witness_four_neighbor_connectivity(grid) -> bool:
    return rule_output(grid) != _rival_eight_neighbor_flood(grid)


SEMANTIC_WITNESSES = {
    "unreachable_chamber": _witness_unreachable_chamber,
    "four_neighbor_connectivity": _witness_four_neighbor_connectivity,
}
SEMANTIC_RIVALS = {
    "fill_all_interior": _rival_fill_all_interior,
    "eight_neighbor_flood": _rival_eight_neighbor_flood,
}
WITNESS_RIVALS = {
    "unreachable_chamber": ["fill_all_interior"],
    "four_neighbor_connectivity": ["eight_neighbor_flood"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
