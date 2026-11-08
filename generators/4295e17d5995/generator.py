"""Generator for ``4295e17d5995`` — matching-wall rigid-body slides.

A color-7 background is bounded by two distinct full-height colored walls.
Every interior 8-connected object has one of the wall colors.  Objects move
horizontally toward the wall of the same color, keep their exact shape, and
stop when any cell would hit the wall or an object already settled closer to
that wall.

The six-profile curriculum deliberately includes crossed starting sides and
same-color queues.  Those cases distinguish the true color-to-wall rule from
plausible shortcuts such as moving to the nearest wall or sliding every object
independently through already-settled objects.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4295e17d5995"
TASK_ID = "4295e17d5995"
VERSION = "2.0.0"
RULE_HASH = "11d057876362"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "On a color-7 grid, distinct colored left/right walls attract every "
    "8-connected object of their own color. Objects slide horizontally as "
    "rigid bodies, closest-to-wall first, and stop against the wall or an "
    "already-settled object."
)

INVARIANTS = [
    "the background is color 7",
    "the left and right borders are distinct non-7 full-height walls",
    "every interior non-background cell has one of the two wall colors",
    "interior objects are maximal same-color 8-connected components",
    "both wall colors occur in at least one interior object",
]

PALETTE_KINDS = ("warm", "cool", "primary", "broad")
PALETTE_BY_KIND = {
    "warm": (2, 4),
    "cool": (8, 9),
    "primary": (1, 6),
    "broad": (3, 5),
}

SCHEDULE_PROFILES = (
    "canonical_crossed",
    "canonical_stacked",
    "crossed",
    "stacked",
    "edge_rows",
    "scattered",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-shaped",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-shaped",
        "valid": "9..18",
    },
    "left_objects": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "1..4",
    },
    "right_objects": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "|".join(PALETTE_KINDS),
    },
}

_CARDINAL_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

_SHAPES = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the six-slot deterministic lesson schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_exact_or_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Accept every declared override while pinning a scheduled default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _profile_defaults(profile: str, difficulty: Any) -> tuple[int, int, int, int]:
    if profile == "canonical_crossed":
        return 9, 9, 2, 3
    if profile == "canonical_stacked":
        return 10, 10, 3, 3
    band = difficulty if isinstance(difficulty, str) else "medium"
    if band == "easy":
        dims = (9, 11)
        counts = (2, 2)
    elif band == "hard":
        dims = (15, 17)
        counts = (4, 4)
    else:
        dims = (12, 14)
        counts = (3, 3)
    if profile == "edge_rows":
        counts = (2, 3)
    elif profile == "scattered":
        counts = (3, 2)
    return dims[0], dims[1], counts[0], counts[1]


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _normalize_shape(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variant(shape: tuple[tuple[int, int], ...], turns: int, mirror: bool) -> tuple[tuple[int, int], ...]:
    cells: list[tuple[int, int]] = []
    for row, col in shape:
        if mirror:
            col = -col
        for _ in range(turns):
            row, col = col, -row
        cells.append((row, col))
    return _normalize_shape(cells)


def _candidate_columns(profile: str, color_role: str, width: int) -> list[int]:
    middle = width // 2
    left_band = list(range(2, max(3, middle)))
    right_band = list(range(min(width - 3, middle), width - 2))
    all_cols = list(range(2, width - 2))
    if profile in ("canonical_crossed", "crossed"):
        return right_band if color_role == "left" else left_band
    if profile in ("canonical_stacked", "stacked"):
        # Objects queue along their travel direction while sharing row bands.
        return all_cols if color_role == "left" else list(reversed(all_cols))
    if profile == "edge_rows":
        return all_cols
    return left_band if color_role == "left" else right_band


def _can_place(cells: set[tuple[int, int]], occupied: set[tuple[int, int]], h: int, w: int) -> bool:
    if any(not (0 <= r < h and 1 <= c < w - 1) for r, c in cells):
        return False
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr, dc in _CARDINAL_8 + ((0, 0),)
    )


def _place_family(
    grid: list[list[int]],
    *,
    color: int,
    role: str,
    count: int,
    profile: str,
    rng,
    occupied: set[tuple[int, int]],
) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    components: list[set[tuple[int, int]]] = []
    columns = _candidate_columns(profile, role, w)
    if not columns:
        columns = list(range(2, w - 2))

    for index in range(count):
        # Keep one multi-cell object per color. Remaining shapes vary from
        # singleton through seven-cell polyominoes, matching canonical sizes.
        if index == 0:
            shape_choices = _SHAPES[2:7]
        elif profile in ("canonical_stacked", "stacked"):
            shape_choices = _SHAPES[:6]
        else:
            shape_choices = _SHAPES

        placed: set[tuple[int, int]] | None = None
        for attempt in range(320):
            shape = rng.choice(shape_choices)
            shape = _shape_variant(shape, rng.randrange(4), bool(rng.randrange(2)))
            sh, sw = _shape_dims(shape)
            legal_cols = [c for c in columns if c + sw <= w - 1]
            if not legal_cols:
                continue

            if profile == "edge_rows" and index == 0:
                row0 = 0 if role == "left" else h - sh
            elif profile in ("canonical_stacked", "stacked"):
                # Constrain both first objects to central rows; later objects
                # frequently overlap those rows but remain 8-disconnected.
                center = max(0, (h - sh) // 2)
                row0 = max(0, min(h - sh, center + rng.choice((-1, 0, 1))))
            else:
                row0 = rng.randint(0, h - sh)

            col0 = rng.choice(legal_cols)
            cells = {(row0 + r, col0 + c) for r, c in shape}
            if _can_place(cells, occupied, h, w):
                placed = cells
                break

        if placed is None:
            # Guaranteed exact-count fallback on a two-cell lattice. It never
            # silently drops an overridden count.
            lattice = [
                (r, c)
                for r in range(0, h, 2)
                for c in range(2, w - 2, 2)
            ]
            if profile in ("canonical_crossed", "crossed"):
                lattice.sort(key=lambda rc: rc[1], reverse=(role == "left"))
            for row, col in lattice:
                cells = {(row, col)}
                if _can_place(cells, occupied, h, w):
                    placed = cells
                    break
        if placed is None:
            raise ValueError(
                f"could not place exact {role}-wall object count {count} on {h}x{w}"
            )

        occupied.update(placed)
        components.append(placed)
        for row, col in placed:
            grid[row][col] = color
    return components


def _place_exact_fallback(
    grid: list[list[int]],
    *,
    left_color: int,
    right_color: int,
    n_left: int,
    n_right: int,
    profile: str,
) -> None:
    """Construct every legal count combination on the minimum 9x9 canvas.

    Random shape placement is intentionally ambitious, but exact override
    support cannot depend on luck or on which color was placed first.  This
    compact row-lattice construction is a total fallback for all declared
    dimensions/counts: each color gets a vertical domino plus up to three
    singleton objects separated by blank rows.
    """
    h, w = len(grid), len(grid[0])
    for row in range(h):
        for col in range(1, w - 1):
            grid[row][col] = 7

    if profile in ("canonical_crossed", "crossed"):
        left_col, right_col = w - 3, 2
    elif profile in ("canonical_stacked", "stacked"):
        left_col, right_col = 3, w - 4
    elif profile == "edge_rows":
        left_col, right_col = 2, w - 3
    else:
        left_col, right_col = 3, w - 4

    # Width is at least nine, so these columns are always distinct and interior.
    if left_col == right_col:
        right_col = w - 3 if left_col != w - 3 else 2

    rows = (0, 3, 5, 7)
    for color, col, count in (
        (left_color, left_col, n_left),
        (right_color, right_col, n_right),
    ):
        grid[0][col] = color
        grid[1][col] = color
        for index in range(1, count):
            grid[rows[index]][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_left, default_right = _profile_defaults(profile, difficulty)
    h = _draw_exact_or_default(ctx, "grid_h", 9, 16, default_h)
    w = _draw_exact_or_default(ctx, "grid_w", 9, 18, default_w)
    n_left = _draw_exact_or_default(ctx, "left_objects", 1, 4, default_left)
    n_right = _draw_exact_or_default(ctx, "right_objects", 1, 4, default_right)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    left_color, right_color = PALETTE_BY_KIND[palette_kind]

    grid = full_grid(h, w, 7)
    for row in range(h):
        grid[row][0] = left_color
        grid[row][w - 1] = right_color

    occupied: set[tuple[int, int]] = set()
    rng = ctx.draw_rng("object_geometry")
    try:
        _place_family(
            grid,
            color=left_color,
            role="left",
            count=n_left,
            profile=profile,
            rng=rng,
            occupied=occupied,
        )
        _place_family(
            grid,
            color=right_color,
            role="right",
            count=n_right,
            profile=profile,
            rng=rng,
            occupied=occupied,
        )
    except ValueError:
        _place_exact_fallback(
            grid,
            left_color=left_color,
            right_color=right_color,
            n_left=n_left,
            n_right=n_right,
            profile=profile,
        )
    return grid


def _components_for_color(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for row in range(h):
        for col in range(1, w - 1):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _CARDINAL_8:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 1 <= nc < w - 1
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    left_color, right_color = grid[0][0], grid[0][-1]
    left = _components_for_color(grid, left_color)
    right = _components_for_color(grid, right_color)
    return {
        "errors": [],
        "height": h,
        "width": w,
        "left_color": left_color,
        "right_color": right_color,
        "left": left,
        "right": right,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if width < 3 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and at least three columns wide"]
    if any(not isinstance(value, int) or not (0 <= value <= 9) for row in grid for value in row):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    height = len(grid)
    left_color, right_color = grid[0][0], grid[0][-1]
    if left_color == right_color or 7 in (left_color, right_color):
        errors.append("left/right walls must be distinct non-background colors")
    if any(grid[row][0] != left_color for row in range(height)):
        errors.append("left wall is not full-height and constant")
    if any(grid[row][-1] != right_color for row in range(height)):
        errors.append("right wall is not full-height and constant")
    legal = {7, left_color, right_color}
    if any(grid[row][col] not in legal for row in range(height) for col in range(1, width - 1)):
        errors.append("interior contains a foreign color")
    if not any(grid[row][col] == left_color for row in range(height) for col in range(1, width - 1)):
        errors.append("missing a left-wall-colored interior object")
    if not any(grid[row][col] == right_color for row in range(height) for col in range(1, width - 1)):
        errors.append("missing a right-wall-colored interior object")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    info = _analyze(grid)
    if info.get("errors"):
        return {}
    palette_kind = next(
        (
            name
            for name, pair in PALETTE_BY_KIND.items()
            if pair == (info["left_color"], info["right_color"])
        ),
        None,
    )
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "left_objects": len(info["left"]),
        "right_objects": len(info["right"]),
        "palette_kind": palette_kind,
    }


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    info = _analyze(grid)
    if info.get("errors"):
        raise ValueError("; ".join(info["errors"]))
    h, w = info["height"], info["width"]
    out = full_grid(h, w, 7)
    for row in range(h):
        out[row][0] = info["left_color"]
        out[row][-1] = info["right_color"]

    for color, direction, components in (
        (info["left_color"], -1, info["left"]),
        (info["right_color"], 1, info["right"]),
    ):
        ordered = sorted(
            components,
            key=lambda cells: (
                min(col for _, col in cells)
                if direction == -1
                else -max(col for _, col in cells)
            ),
        )
        for cells in ordered:
            shifts: list[int] = []
            for row, col in cells:
                cursor = col
                while 0 <= cursor + direction < w and out[row][cursor + direction] == 7:
                    cursor += direction
                shifts.append(abs(cursor - col))
            shift = min(shifts)
            for row, col in cells:
                out[row][col + direction * shift] = color
    return out


def _independent_no_blocking(grid):
    """Wrong rival: every object ignores objects that settled before it."""
    info = _analyze(grid)
    if info.get("errors"):
        raise ValueError("; ".join(info["errors"]))
    h, w = info["height"], info["width"]
    out = full_grid(h, w, 7)
    for row in range(h):
        out[row][0] = info["left_color"]
        out[row][-1] = info["right_color"]
    for color, direction, components in (
        (info["left_color"], -1, info["left"]),
        (info["right_color"], 1, info["right"]),
    ):
        for cells in components:
            shift = min(
                col - 1 if direction == -1 else (w - 2) - col
                for _, col in cells
            )
            for row, col in cells:
                out[row][col + direction * shift] = color
    return out


def _nearest_wall(grid):
    """Wrong rival: direction is chosen from starting position, not color."""
    info = _analyze(grid)
    if info.get("errors"):
        raise ValueError("; ".join(info["errors"]))
    h, w = info["height"], info["width"]
    out = full_grid(h, w, 7)
    for row in range(h):
        out[row][0] = info["left_color"]
        out[row][-1] = info["right_color"]
    all_components = [
        (info["left_color"], cells) for cells in info["left"]
    ] + [
        (info["right_color"], cells) for cells in info["right"]
    ]
    all_components.sort(key=lambda item: min(c for _, c in item[1]))
    for color, cells in all_components:
        center = sum(c for _, c in cells) / len(cells)
        direction = -1 if center < (w - 1) / 2 else 1
        shift = min(
            col - 1 if direction == -1 else (w - 2) - col
            for _, col in cells
        )
        for row, col in cells:
            out[row][col + direction * shift] = color
    return out


def _no_slide(grid):
    return [list(row) for row in grid]


def strict_canonical_like(grid) -> list[str]:
    info = _analyze(grid)
    if info.get("errors"):
        return list(info["errors"])
    reasons: list[str] = []
    if (info["height"], info["width"]) not in ((9, 9), (10, 10)):
        reasons.append("canonical canvases are 9x9 or 10x10")
    if not (2 <= len(info["left"]) <= 3 and 2 <= len(info["right"]) <= 3):
        reasons.append("canonical inputs use two or three objects of each wall color")
    if any(not (1 <= len(cells) <= 7) for cells in info["left"] + info["right"]):
        reasons.append("canonical object sizes are one through seven cells")
    return reasons


def _crossed_color_witness(grid) -> bool:
    info = _analyze(grid)
    if info.get("errors"):
        return False
    midpoint = (info["width"] - 1) / 2
    return (
        any(sum(c for _, c in cells) / len(cells) > midpoint for cells in info["left"])
        and any(sum(c for _, c in cells) / len(cells) < midpoint for cells in info["right"])
        and _nearest_wall(grid) != rule_mirror(grid)
    )


def _blocking_witness(grid) -> bool:
    info = _analyze(grid)
    if info.get("errors"):
        return False
    return _independent_no_blocking(grid) != rule_mirror(grid)


def _motion_witness(grid) -> bool:
    return _no_slide(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "color_not_nearest_wall": _crossed_color_witness,
    "settled_objects_block_followers": _blocking_witness,
    "nonzero_rigid_motion": _motion_witness,
}

SEMANTIC_RIVALS = {
    "nearest_wall": _nearest_wall,
    "independent_no_blocking": _independent_no_blocking,
    "no_slide": _no_slide,
}

WITNESS_RIVALS = {
    "color_not_nearest_wall": ["nearest_wall"],
    "settled_objects_block_followers": ["independent_no_blocking"],
    "nonzero_rigid_motion": ["no_slide"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 0.25


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the matching-wall rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(f"demos do not falsify shortcut {name!r}")
    return reasons
