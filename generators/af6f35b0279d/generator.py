"""Generator for ``medium_k08`` — crop the corner-selected object.

The first non-zero corner in row-major corner order names a color.  All four
corner cells are cleared, then the tight bounding box of the remaining cells
of that color is returned as a *raw subgrid*.  Consequently a foreign-colored
cell deliberately placed in a hole of the selected object's bounding box is
visible in the answer.

The ordinary curriculum varies every corner, makes the selected object both
smaller and larger than distractors, varies its bbox, and periodically inserts
an in-crop foreign cell.  Those branches refute fixed-corner, largest-object,
fixed-size, and selected-color-mask shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af6f35b0279d"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "5fd8695d776f"

SUMMARY = (
    "Exactly one corner is non-zero and acts only as a color key. Clear all "
    "four corners, find the single connected body object of that key color, "
    "and return the raw subgrid at its tight bounding box. Distractors use "
    "other colors; some samples place one distractor cell in an empty cell "
    "inside the selected bbox, so the foreign cell remains in the output."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular 8..16 grid with zero background and colors 0..9",
    "exactly one non-zero corner marker; the other three corners are zero",
    "the marker color occurs in exactly one connected multi-cell body object",
    "the selected object has a non-solid bbox and never touches a corner",
    "at least one other body color is present outside the selected bbox",
    "selected object is strictly smaller or larger than the largest distractor",
]

CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
RELATIONS = ("target_smaller", "target_larger")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchor every fourth sample; otherwise difficulty-banded",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchor every fourth sample; otherwise difficulty-banded",
        "valid": "8..16",
    },
    "marker_corner": {
        "type": "str",
        "default": "four-sample cycle covering every corner",
        "valid": "|".join(CORNERS),
    },
    "marker_color": {
        "type": "int",
        "default": "rng 1..9",
        "valid": "1..9",
    },
    "n_decoy_colors": {
        "type": "int",
        "default": "four-sample cycle 2,1,3,2",
        "valid": "1..3",
    },
    "target_cells": {
        "type": "int",
        "default": "four-sample cycle 4,5,9,6",
        "valid": "4..9",
    },
    "target_size_relation": {
        "type": "str",
        "default": "alternates target_smaller/target_larger",
        "valid": "|".join(RELATIONS),
    },
    "intrusion": {
        "type": "bool",
        "default": "four-sample cycle false,true,true,false",
        "valid": "false|true",
    },
}

# Every declared boundary combination is constructible; unknown keys are
# rejected before GenCtx is created.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_PROFILES = ((10, 10), (11, 11), (10, 12), (12, 12))
_SCHEDULE = (
    ("top_left", "target_smaller", False, 2),
    ("top_right", "target_larger", True, 1),
    ("bottom_left", "target_smaller", True, 3),
    ("bottom_right", "target_larger", False, 2),
)
SCHEDULE_PROFILES = tuple((c, rel, intr) for c, rel, intr, _ in _SCHEDULE)

_TARGET_TEMPLATES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (1, 0), (1, 1), (1, 2)),
    5: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    6: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    9: ((0, 0), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _transform(cells: list[tuple[int, int]], turn: int, reflect: bool) -> list[tuple[int, int]]:
    pts = list(cells)
    if reflect:
        pts = [(r, -c) for r, c in pts]
    for _ in range(turn % 4):
        pts = [(c, -r) for r, c in pts]
    return _normalize(pts)


def _target_shape(k: int, rng) -> list[tuple[int, int]]:
    return _transform(list(_TARGET_TEMPLATES[k]), rng.randrange(4), bool(rng.getrandbits(1)))


def _compact_shape(k: int, rng) -> list[tuple[int, int]]:
    """Connected compact polyomino with exactly ``k`` cells."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(2000):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        trial = seen | {p}
        height = max(x for x, _ in trial) - min(x for x, _ in trial) + 1
        width = max(y for _, y in trial) - min(y for _, y in trial) + 1
        if height > 4 or width > 4:
            continue
        seen.add(p)
        cells.append(p)
    if len(cells) != k:
        # Deterministic compact fallback, connected in row-major fill order.
        width = min(4, k)
        cells = [(i // width, i % width) for i in range(k)]
    return _transform(cells, rng.randrange(4), bool(rng.getrandbits(1)))


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _corner_positions(h: int, w: int) -> dict[str, tuple[int, int]]:
    return {
        "top_left": (0, 0),
        "top_right": (0, w - 1),
        "bottom_left": (h - 1, 0),
        "bottom_right": (h - 1, w - 1),
    }


def _draw_dimension(ctx, name: str, band: str, sample_index: int, overrides: dict[str, Any]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, 8, 16)
    if sample_index % 4 == 0:
        profile = _CANONICAL_PROFILES[(sample_index // 4) % len(_CANONICAL_PROFILES)]
        value = profile[0 if name == "grid_h" else 1]
        return ctx.draw_choice(name, [value])
    lo, hi = {
        "easy": (8, 11),
        "medium": (10, 14),
        "hard": (12, 16),
    }[band]
    return ctx.draw_int(name, lo, hi)


def _draw_scheduled_choice(ctx, label: str, options: tuple[Any, ...], scheduled: Any, overrides: dict[str, Any]):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, [scheduled])


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, [scheduled])


def _place_shape(
    grid: list[list[int]],
    shape: list[tuple[int, int]],
    color: int,
    rng,
    *,
    forbidden: set[tuple[int, int]] | None = None,
    allowed_origins: list[tuple[int, int]] | None = None,
) -> list[tuple[int, int]] | None:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    origins = allowed_origins or [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    origins = list(origins)
    rng.shuffle(origins)
    forbidden = forbidden or set()
    for r0, c0 in origins:
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        if any(p in forbidden for p in cells):
            continue
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        for r, c in cells:
            grid[r][c] = color
        return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_corner, scheduled_relation, scheduled_intrusion, scheduled_decoys = _SCHEDULE[sample_index % 4]

    h = _draw_dimension(ctx, "grid_h", band, sample_index, overrides)
    w = _draw_dimension(ctx, "grid_w", band, sample_index, overrides)
    corner = _draw_scheduled_choice(ctx, "marker_corner", CORNERS, scheduled_corner, overrides)
    marker_color = ctx.draw_int("marker_color", 1, 9)
    n_decoy_colors = _draw_scheduled_int(
        ctx, "n_decoy_colors", 1, 3, scheduled_decoys, overrides
    )
    target_cells = _draw_scheduled_int(
        ctx, "target_cells", 4, 9, (4, 5, 9, 6)[sample_index % 4], overrides
    )
    relation = _draw_scheduled_choice(
        ctx, "target_size_relation", RELATIONS, scheduled_relation, overrides
    )
    intrusion = bool(
        _draw_scheduled_choice(ctx, "intrusion", (False, True), scheduled_intrusion, overrides)
    )

    palette = list(
        ctx.draw_distinct_colors(
            "decoy_palette", n=n_decoy_colors, exclude={0, marker_color}
        )
    )
    layout_rng = ctx.draw_rng("layout")
    target_rng = ctx.draw_rng("target_shape")
    decoy_rng = ctx.draw_rng("decoy_shapes")

    target_shape = _target_shape(target_cells, target_rng)
    tsh = max(r for r, _ in target_shape) + 1
    tsw = max(c for _, c in target_shape) + 1
    target_origins = [
        (r, c)
        for r in range(1, h - tsh)
        for c in range(1, w - tsw)
    ]

    marker_pos = _corner_positions(h, w)[corner]
    for _attempt in range(160):
        grid = full_grid(h, w, 0)
        grid[marker_pos[0]][marker_pos[1]] = marker_color
        target = _place_shape(
            grid,
            target_shape,
            marker_color,
            layout_rng,
            forbidden=set(_corner_positions(h, w).values()),
            allowed_origins=target_origins,
        )
        if target is None:
            continue
        r0, c0, r1, c1 = _bbox(target)
        target_box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        holes = sorted(target_box - set(target))
        if not holes:
            continue

        # The first distractor is the size-control object.  Others are smaller
        # nuisance objects.  All external distractors stay outside the selected
        # bbox so only the explicit intrusion branch can enter the answer.
        if relation == "target_smaller":
            sizes = [target_cells + 1] + [2 + (i % 2) for i in range(n_decoy_colors - 1)]
        else:
            sizes = [target_cells - 1] + [2 + (i % max(1, target_cells - 3)) for i in range(n_decoy_colors - 1)]
        sizes = [max(2, min(10, size)) for size in sizes]

        ok = True
        for index, (color, size) in enumerate(zip(palette, sizes)):
            shape = _compact_shape(size, decoy_rng)
            forbidden = set(target_box)
            # When this color also supplies the intrusion, keep its external
            # component at least one 4-neighbour step from the target bbox.
            if intrusion and index == 0:
                forbidden |= {
                    (r, c)
                    for r in range(max(0, r0 - 1), min(h, r1 + 2))
                    for c in range(max(0, c0 - 1), min(w, c1 + 2))
                }
            placed = _place_shape(grid, shape, color, layout_rng, forbidden=forbidden)
            if placed is None:
                ok = False
                break
        if not ok:
            continue
        if intrusion:
            rr, cc = holes[layout_rng.randrange(len(holes))]
            grid[rr][cc] = palette[0]

        if not self_check(grid):
            return grid
    raise ValueError(
        "could not construct a lawful corner-selection board for the requested axes"
    )


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(comp)
    return out


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if not (8 <= h <= 16 and 8 <= w <= 16):
        errors.append(f"grid dimensions must be within 8..16, got {h}x{w}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")

    positions = _corner_positions(h, w)
    nonzero = [(name, pos, grid[pos[0]][pos[1]]) for name, pos in positions.items() if grid[pos[0]][pos[1]] != 0]
    if len(nonzero) != 1:
        errors.append(f"expected exactly one non-zero corner marker, found {len(nonzero)}")
        return info, errors
    marker_corner, _, marker_color = nonzero[0]
    clean = [list(row) for row in grid]
    for r, c in positions.values():
        clean[r][c] = 0

    target_components = _components(clean, marker_color)
    if len(target_components) != 1:
        errors.append(
            f"marker color must form exactly one body component, found {len(target_components)}"
        )
        return info, errors
    target = target_components[0]
    if len(target) < 4:
        errors.append(f"selected body object must have at least 4 cells, got {len(target)}")
    r0, c0, r1, c1 = _bbox(target)
    target_box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    if len(target_box) == len(target):
        errors.append("selected object fills its bbox; the crop rule is hidden by a solid block")

    decoy_colors = sorted(
        {value for row in clean for value in row if value not in (0, marker_color)}
    )
    if not decoy_colors:
        errors.append("at least one distractor color is required")
        return info, errors
    external_decoy = any(
        clean[r][c] not in (0, marker_color) and (r, c) not in target_box
        for r in range(h)
        for c in range(w)
    )
    if not external_decoy:
        errors.append("at least one distractor cell must lie outside the selected bbox")

    decoy_component_sizes = [
        len(component)
        for color in decoy_colors
        for component in _components(clean, color)
    ]
    max_decoy = max(decoy_component_sizes, default=0)
    if len(target) < max_decoy:
        relation = "target_smaller"
    elif len(target) > max_decoy:
        relation = "target_larger"
    else:
        # Canonical rows may contain a size tie.  Ties are authority-valid but
        # ordinary generated lessons deliberately avoid them so the size-based
        # shortcut is falsifiable.
        relation = "target_equal"
    intrusion = any(
        clean[r][c] not in (0, marker_color)
        for r, c in target_box
    )
    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "marker_corner": marker_corner,
            "marker_color": marker_color,
            "n_decoy_colors": len(decoy_colors),
            "target_cells": len(target),
            "target_size_relation": relation,
            "intrusion": intrusion,
            "target": tuple(sorted(target)),
            "target_bbox": (r0, c0, r1, c1),
            "clean": clean,
            "decoy_colors": tuple(decoy_colors),
            "max_decoy_component": max_decoy,
        }
    )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    return _analyse(grid)[1]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for tests only; canonical Racket remains the authority."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    clean = [list(row) for row in grid]
    key = None
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if key is None and clean[r][c] != 0:
            key = clean[r][c]
        clean[r][c] = 0
    if key is None:
        raise ValueError("no non-zero corner marker")
    cells = [(r, c) for r in range(h) for c in range(w) if clean[r][c] == key]
    if not cells:
        raise ValueError("marker color has no body cells")
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


def _rival_fixed_top_left(grid: Any) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    key = grid[0][0]
    if key == 0:
        return [[0]]
    clean = [list(row) for row in grid]
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        clean[r][c] = 0
    cells = [(r, c) for r in range(h) for c in range(w) if clean[r][c] == key]
    if not cells:
        return [[0]]
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]



def _rival_fixed_bottom_right(grid: Any) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    key = grid[h - 1][w - 1]
    if key == 0:
        return [[0]]
    clean = [list(row) for row in grid]
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        clean[r][c] = 0
    cells = [(r, c) for r in range(h) for c in range(w) if clean[r][c] == key]
    if not cells:
        return [[0]]
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


def _rival_smallest_body_object(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    clean = info["clean"]
    components: list[list[tuple[int, int]]] = []
    for color in sorted({v for row in clean for v in row if v != 0}):
        components.extend(_components(clean, color))
    winner = min(components, key=len)
    r0, c0, r1, c1 = _bbox(winner)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


def _rival_fixed_3x3(grid: Any) -> list[list[int]]:
    actual = rule_mirror(grid)
    return [
        [actual[r][c] if r < len(actual) and c < len(actual[0]) else 0 for c in range(3)]
        for r in range(3)
    ]

def _rival_selected_color_mask(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    key = info["marker_color"]
    return [[value if value == key else 0 for value in row] for row in rule_mirror(grid)]


def _rival_largest_body_object(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    clean = info["clean"]
    components: list[list[tuple[int, int]]] = []
    for color in sorted({v for row in clean for v in row if v != 0}):
        components.extend(_components(clean, color))
    winner = max(components, key=len)
    r0, c0, r1, c1 = _bbox(winner)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


def _rival_crop_all_nonzero(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    clean = info["clean"]
    cells = [(r, c) for r, row in enumerate(clean) for c, value in enumerate(row) if value != 0]
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_top_left_key": _rival_fixed_top_left,
    "fixed_bottom_right_key": _rival_fixed_bottom_right,
    "selected_color_mask_only": _rival_selected_color_mask,
    "largest_body_object": _rival_largest_body_object,
    "smallest_body_object": _rival_smallest_body_object,
    "fixed_3x3_output": _rival_fixed_3x3,
    "crop_all_nonzero_body": _rival_crop_all_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All four canonical pairs contain no foreign cell inside the selected bbox,
    # so only generated intrusion witnesses can falsify this shortcut.
    "selected_color_mask_only": _rival_selected_color_mask,
}


def _witness_corner(name: str):
    def predicate(grid):
        info, errors = _analyse(grid)
        return not errors and info["marker_corner"] == name
    return predicate


def _witness_relation(name: str):
    def predicate(grid):
        info, errors = _analyse(grid)
        return not errors and info["target_size_relation"] == name
    return predicate


def _witness_intrusion(grid):
    info, errors = _analyse(grid)
    return not errors and info["intrusion"]


def _witness_decoys_outside(grid):
    info, errors = _analyse(grid)
    if errors:
        return False
    r0, c0, r1, c1 = info["target_bbox"]
    return any(
        info["clean"][r][c] not in (0, info["marker_color"])
        and not (r0 <= r <= r1 and c0 <= c <= c1)
        for r in range(info["grid_h"])
        for c in range(info["grid_w"])
    )


def _witness_non_3x3(grid):
    info, errors = _analyse(grid)
    if errors:
        return False
    r0, c0, r1, c1 = info["target_bbox"]
    return (r1 - r0 + 1, c1 - c0 + 1) != (3, 3)


SEMANTIC_WITNESSES = {
    "marker_top_left": _witness_corner("top_left"),
    "marker_top_right": _witness_corner("top_right"),
    "marker_bottom_left": _witness_corner("bottom_left"),
    "marker_bottom_right": _witness_corner("bottom_right"),
    "target_smaller_than_distractor": _witness_relation("target_smaller"),
    "target_larger_than_distractor": _witness_relation("target_larger"),
    "foreign_cell_survives_raw_crop": _witness_intrusion,
    "distractors_outside_selected_bbox": _witness_decoys_outside,
    "output_bbox_not_fixed_3x3": _witness_non_3x3,
}
WITNESS_RIVALS = {
    "marker_top_left": ["fixed_bottom_right_key"],
    "marker_top_right": ["fixed_top_left_key"],
    "marker_bottom_left": ["fixed_top_left_key"],
    "marker_bottom_right": ["fixed_top_left_key"],
    "target_smaller_than_distractor": ["largest_body_object"],
    "target_larger_than_distractor": ["smallest_body_object"],
    "foreign_cell_survives_raw_crop": ["selected_color_mask_only"],
    "distractors_outside_selected_bbox": ["crop_all_nonzero_body"],
    "output_bbox_not_fixed_3x3": ["fixed_3x3_output"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    corner, relation, intrusion, _ = _SCHEDULE[sample_index % 4]
    return corner, relation, intrusion


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    corners: set[str] = set()
    relations: set[str] = set()
    intrusion_seen = False
    output_shapes: set[tuple[int, int]] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not the raw selected-color bbox crop")
        corners.add(info["marker_corner"])
        relations.add(info["target_size_relation"])
        intrusion_seen |= bool(info["intrusion"])
        output_shapes.add((len(expected), len(expected[0])))
    if corners != set(CORNERS):
        reasons.append(f"demonstrations do not cover every marker corner: {sorted(corners)}")
    if relations != set(RELATIONS):
        reasons.append(f"demonstrations do not cover both size relations: {sorted(relations)}")
    if not intrusion_seen:
        reasons.append("demonstrations lack a foreign-cell raw-crop witness")
    if len(output_shapes) < 2:
        reasons.append("demonstrations do not vary the selected bbox shape")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, qerrors = _analyse(query["input"])
        if qerrors:
            reasons.append(f"query malformed: {qerrors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative transform")
    return reasons


def make_degenerate(name: str) -> list[list[int]]:
    """Deterministic malformed fixtures for focused mutation tests."""
    grid = full_grid(9, 9, 0)
    if name == "no_corner_marker":
        for r, c in ((2, 2), (3, 2), (3, 3), (3, 4)):
            grid[r][c] = 4
        grid[6][6] = 6
        return grid
    if name == "no_match":
        grid[0][0] = 4
        for r, c in ((5, 5), (5, 6), (6, 5)):
            grid[r][c] = 6
        return grid
    if name == "multiple_matches":
        grid[0][0] = 4
        for r, c in ((2, 2), (2, 3), (3, 2), (6, 6), (6, 7), (7, 6)):
            grid[r][c] = 4
        grid[4][5] = 6
        return grid
    raise ValueError(f"unknown degenerate fixture: {name!r}")
