"""Generator for medium_i14 — fill each enclosed object hole with its color.

The official examples happen to use rectangular frames, but the title,
written solution, topology/holes skill tags, and selected Racket program all
state the more general rule: fill zero cells enclosed by each hollow
same-color object.  The curriculum therefore keeps canonical rectangles while
also using two conservative controls:

* a one-gap open rectangle, whose interior leaks and must remain unchanged;
* an exact closed rectangle with one outward spur, whose hole still fills.

Together they distinguish topological hole filling from bbox filling and from
the rectangle-only shortcut without admitting arbitrary, hard-to-audit shapes.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56f043832ecb"
TASK_ID = "56f043832ecb"
VERSION = "4.0.0"
RULE_HASH = "29fbeb2dce83"

SUMMARY = (
    "A 0-background grid contains 1-2 hollow same-color objects in distinct "
    "colors: canonical rectangular frames and, in one scheduled profile, an "
    "exact rectangular frame with one outward spur. It may also contain one "
    "visually similar rectangle with a single non-corner wall gap. Fill every "
    "zero cell topologically enclosed by each hollow object with that object's "
    "color; preserve existing cells and leave the open decoy unchanged."
)

INVARIANTS = [
    "background is 0 and every non-zero component has one distinct color",
    "there are exactly 1-2 closed hollow components: rectangles or one-spur rectangles",
    "there are 0-1 one-gap open rectangular perimeter decoys",
    "every closed component has at least one bbox-local enclosed zero cell",
    "all components are at least 3x3 and are separated by a one-cell moat",
]

PALETTE_KINDS = ("canonical", "broad")

# Any EXAMPLES_NEEDED consecutive sample indices include a canonical two-frame
# scene, an open-decoy scene, and an irregular broad-palette scene.  This
# refutes the declared shortcut family in every lesson window.
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical_pair", "open_decoy", "irregular_broad")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over the canonical neighborhood",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over the canonical neighborhood",
        "valid": "8..12",
    },
    "n_frames": {
        "type": "int",
        "default": "three-profile schedule; canonical_pair anchors two frames",
        "valid": "1..2",
    },
    "n_open_decoys": {
        "type": "int",
        "default": "three-profile schedule; open_decoy anchors one decoy",
        "valid": "0..1",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled canonical/broad choice",
        "valid": "canonical|broad",
    },
}

_CANONICAL_COLORS = (2, 3, 4, 6, 7)
_BROAD_COLORS = (1, 5, 8, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_OVERRIDES = frozenset(AXES)


def _component_cells(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    """Return same-color 4-connected non-zero components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells: set[tuple[int, int]] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(r0: int, c0: int, r1: int, c1: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _rectangular_kind(cells: set[tuple[int, int]]) -> str | None:
    """Classify an exact closed or one-gap rectangular perimeter."""
    if not cells:
        return None
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return None
    border = _perimeter(r0, c0, r1, c1)
    if cells == border:
        return "closed_rect"
    missing = border - cells
    if len(missing) != 1 or not cells < border:
        return None
    mr, mc = next(iter(missing))
    # A missing corner changes the bbox and is not the intended open-frame cue.
    if mr in (r0, r1) and mc in (c0, c1):
        return None
    return "open_rect"


def _classify_component(cells: set[tuple[int, int]]) -> str | None:
    """Classify the exact supported shape families.

    ``closed_irregular`` is deliberately narrow: removing exactly one cell
    must leave a closed rectangular perimeter, and that removed cell must be
    an outward 4-connected spur.  This rejects arbitrary blobs and interior
    contamination while supplying a clean counterexample to rectangle-only
    reasoning.
    """
    rectangular = _rectangular_kind(cells)
    if rectangular is not None:
        return rectangular
    for spur in cells:
        base = cells - {spur}
        if _rectangular_kind(base) != "closed_rect":
            continue
        r0, c0, r1, c1 = _bbox(base)
        sr, sc = spur
        if r0 <= sr <= r1 and c0 <= sc <= c1:
            continue
        if any((sr + dr, sc + dc) in base for dr, dc in _DIR4):
            return "closed_irregular"
    return None


def _component_holes(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """Return bbox-local zero cells not reachable from the bbox border.

    This is the Python mirror of the selected Racket program's flood-fill
    criterion.  A one-gap frame has no such cells; a spurred closed frame has
    the same enclosed hole as its rectangular base even though its bbox is
    larger.
    """
    r0, c0, r1, c1 = _bbox(cells)
    zeros = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cells
    }
    exterior = {
        (r, c)
        for r, c in zeros
        if r in (r0, r1) or c in (c0, c1)
    }
    queue = deque(exterior)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            nxt = (r + dr, c + dc)
            if nxt in zeros and nxt not in exterior:
                exterior.add(nxt)
                queue.append(nxt)
    return zeros - exterior


def _component_moats_clear(
    components: list[tuple[int, set[tuple[int, int]]]],
) -> bool:
    for i, (_, left) in enumerate(components):
        for _, right in components[i + 1 :]:
            if any(
                abs(lr - rr) <= 1 and abs(lc - rc) <= 1
                for lr, lc in left
                for rr, rc in right
            ):
                return False
    return True


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact semantic axis from the materialized grid."""
    components = _component_cells(grid)
    kinds = [_classify_component(cells) for _, cells in components]
    colors = {color for color, _ in components}
    if colors and colors <= set(_CANONICAL_COLORS):
        palette_kind = "canonical"
    elif colors and colors <= set(_BROAD_COLORS):
        palette_kind = "broad"
    else:
        palette_kind = "mixed_or_invalid"
    return {
        "n_frames": sum(
            kind in {"closed_rect", "closed_irregular"} for kind in kinds
        ),
        "n_open_decoys": sum(kind == "open_rect" for kind in kinds),
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar, not merely palette/shape."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    components = _component_cells(grid)
    if not components:
        errors.append("no non-zero frame components")
        return errors
    colors = [color for color, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("each component must use a distinct color")

    kinds: list[str | None] = []
    for color, cells in components:
        kind = _classify_component(cells)
        kinds.append(kind)
        if kind is None:
            errors.append(
                f"color-{color} component is not an exact closed rectangle, "
                "one-spur closed rectangle, or one-gap open rectangle"
            )
            continue
        holes = _component_holes(cells)
        if kind in {"closed_rect", "closed_irregular"} and not holes:
            errors.append(f"color-{color} closed component has no enclosed zero hole")
        if kind == "open_rect" and holes:
            errors.append(f"color-{color} open decoy unexpectedly encloses zero cells")

    n_closed = sum(
        kind in {"closed_rect", "closed_irregular"} for kind in kinds
    )
    n_open = sum(kind == "open_rect" for kind in kinds)
    if not 1 <= n_closed <= 2:
        errors.append(f"expected 1-2 closed frames, found {n_closed}")
    if not 0 <= n_open <= 1:
        errors.append(f"expected 0-1 open decoys, found {n_open}")
    if len(components) != n_closed + n_open:
        errors.append("unclassified non-zero component present")
    if not _component_moats_clear(components):
        errors.append("frame components must be separated by a one-cell moat")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Semantic-gate hook: canonical-like for THIS task.

    The four official inputs are 7-8 rows by 8-11 columns, contain only
    CLOSED hollow rectangular frames (no open decoy) in the canonical
    palette {2, 3, 4, 6, 7}.  Returns [] for such scenes, else reasons.
    Pure.
    """
    errors = self_check(grid)
    if errors:
        return list(errors)
    reasons = []
    height, width = len(grid), len(grid[0])
    if not (7 <= height <= 8 and 8 <= width <= 11):
        reasons.append(
            f"dimensions {height}x{width} outside the canonical 7..8 x 8..11 envelope"
        )
    observed = observe_overrides(grid)
    if observed["palette_kind"] != "canonical":
        reasons.append(
            f"palette is {observed['palette_kind']!r}; canonical scenes use only "
            f"colors {_CANONICAL_COLORS}"
        )
    if observed["n_open_decoys"] != 0:
        reasons.append("canonical scenes contain no one-gap open frame")
    scene = _lawful_scene(grid)
    if scene is not None and any(kind != "closed_rect" for kind, _, _ in scene):
        reasons.append("canonical scenes use rectangular closed frames only")
    return reasons


def _lawful_scene(grid) -> list[tuple[str, int, set[tuple[int, int]]]] | None:
    """[(kind, color, cells)] for a self_check-clean grid, else None.  Pure."""
    if self_check(grid):
        return None
    return [
        (_classify_component(cells), color, cells)
        for color, cells in _component_cells(grid)
    ]


def _witness(predicate):
    def check(grid):
        scene = _lawful_scene(grid)
        return scene is not None and predicate(scene)

    return check


def _touches_border(grid, cells: set[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        r in (0, height - 1) or c in (0, width - 1) for r, c in cells
    )


def _closed_entries(scene):
    return [
        entry
        for entry in scene
        if entry[0] in {"closed_rect", "closed_irregular"}
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the authoritative bbox-local hole fill for Python-side probes."""
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        for row, col in _component_holes(cells):
            out[row][col] = color
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _fill_component_bboxes(grid):
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        r0, c0, r1, c1 = _bbox(cells)
        for row in range(r0 + 1, r1):
            for col in range(c0 + 1, c1):
                if out[row][col] == 0:
                    out[row][col] = color
    return out


def _fill_selected_holes(grid, predicate):
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        kind = _classify_component(cells)
        holes = _component_holes(cells)
        if holes and predicate(kind, color, cells, holes):
            for row, col in holes:
                out[row][col] = color
    return out


def _fill_largest_closed_only(grid):
    candidates = []
    for color, cells in _component_cells(grid):
        holes = _component_holes(cells)
        if holes:
            candidates.append((len(cells), color, cells, holes))
    out = [list(row) for row in grid]
    if not candidates:
        return out
    _, color, _, holes = max(
        candidates,
        key=lambda item: (item[0], -min(item[3])[0], -min(item[3])[1]),
    )
    for row, col in holes:
        out[row][col] = color
    return out


def _fill_rectangular_frames_only(grid):
    return _fill_selected_holes(
        grid, lambda kind, _color, _cells, _holes: kind == "closed_rect"
    )


def _fill_canonical_colors_only(grid):
    return _fill_selected_holes(
        grid, lambda _kind, color, _cells, _holes: color in _CANONICAL_COLORS
    )


def _skip_border_touching_closed_frames(grid):
    return _fill_selected_holes(
        grid,
        lambda _kind, _color, cells, _holes: not _touches_border(grid, cells),
    )


SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "identity_no_fill": _identity,
    "fill_every_component_bbox": _fill_component_bboxes,
    "fill_largest_closed_only": _fill_largest_closed_only,
    "rectangular_frames_only": _fill_rectangular_frames_only,
    "canonical_colors_only": _fill_canonical_colors_only,
    "skip_border_touching_closed_frames": _skip_border_touching_closed_frames,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "fill_every_component_bbox",
        "rectangular_frames_only",
        "canonical_colors_only",
    )
}


# Every witness below has a concrete named rival.  The semantic gate executes
# both functions on the same generated grid; a merely frequent branch is not
# credited unless its rival really disagrees with the authoritative Racket
# output.
SEMANTIC_WITNESSES = {
    "enclosed_hole_fills": _witness(lambda scene: bool(_closed_entries(scene))),
    "two_closed_objects_fill": _witness(
        lambda scene: len(_closed_entries(scene)) == 2
    ),
    "open_gap_decoy_stays_zero": _witness(
        lambda scene: any(kind == "open_rect" for kind, _, _ in scene)
    ),
    "irregular_closed_object_fills": _witness(
        lambda scene: any(kind == "closed_irregular" for kind, _, _ in scene)
    ),
    "broad_palette_still_fills": _witness(
        lambda scene: {color for _, color, _ in scene} <= set(_BROAD_COLORS)
    ),
    "closed_object_may_touch_canvas_border": lambda grid: (
        (scene := _lawful_scene(grid)) is not None
        and any(
            _touches_border(grid, cells)
            for kind, _, cells in scene
            if kind in {"closed_rect", "closed_irregular"}
        )
    ),
}

WITNESS_RIVALS = {
    "enclosed_hole_fills": ["identity_no_fill"],
    "two_closed_objects_fill": ["fill_largest_closed_only"],
    "open_gap_decoy_stays_zero": ["fill_every_component_bbox"],
    "irregular_closed_object_fills": ["rectangular_frames_only"],
    "broad_palette_still_fills": ["canonical_colors_only"],
    "closed_object_may_touch_canvas_border": [
        "skip_border_touching_closed_frames"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return [] only when demonstrations refute every declared competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with enclosed-hole filling")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with enclosed-hole filling")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def _split_slots(
    height: int, width: int, count: int, rng
) -> list[tuple[int, int, int, int]]:
    """Partition the grid into 1-3 moat-separated slots."""
    if count == 1:
        return [(0, 0, height - 1, width - 1)]

    layouts: list[list[tuple[int, int, int, int]]] = []
    if count == 2:
        if width >= 7:
            left_w = (width - 1) // 2
            right_c = left_w + 1
            layouts.append(
                [
                    (0, 0, height - 1, left_w - 1),
                    (0, right_c, height - 1, width - 1),
                ]
            )
        if height >= 7:
            top_h = (height - 1) // 2
            bottom_r = top_h + 1
            layouts.append(
                [
                    (0, 0, top_h - 1, width - 1),
                    (bottom_r, 0, height - 1, width - 1),
                ]
            )
    elif count == 3:
        if width >= 11:
            base = (width - 2) // 3
            rem = width - 2 - 3 * base
            widths = [base + (1 if i < rem else 0) for i in range(3)]
            c = 0
            slots = []
            for slot_w in widths:
                slots.append((0, c, height - 1, c + slot_w - 1))
                c += slot_w + 1
            layouts.append(slots)
        if height >= 7 and width >= 7:
            top_h = (height - 1) // 2
            bottom_r = top_h + 1
            left_w = (width - 1) // 2
            right_c = left_w + 1
            layouts.append(
                [
                    (0, 0, top_h - 1, left_w - 1),
                    (0, right_c, top_h - 1, width - 1),
                    (bottom_r, 0, height - 1, width - 1),
                ]
            )
            layouts.append(
                [
                    (0, 0, top_h - 1, width - 1),
                    (bottom_r, 0, height - 1, left_w - 1),
                    (bottom_r, right_c, height - 1, width - 1),
                ]
            )
    if not layouts:
        raise ValueError(
            f"cannot place {count} moat-separated 3x3 frames in {height}x{width}"
        )
    return rng.choice(layouts)


def _rect_in_slot(
    slot: tuple[int, int, int, int],
    rng,
    *,
    canvas_shape: tuple[int, int] | None = None,
    force_canvas_border: bool = False,
) -> tuple[int, int, int, int]:
    sr0, sc0, sr1, sc1 = slot
    slot_h, slot_w = sr1 - sr0 + 1, sc1 - sc0 + 1
    if slot_h < 3 or slot_w < 3:
        raise ValueError(f"slot {slot} is too small for a hollow frame")

    # Leave a canonical-style outer margin when the slot can afford it.  The
    # rectangle otherwise expands to keep the transformed hole conspicuous.
    max_h = slot_h - 2 if slot_h >= 5 else slot_h
    max_w = slot_w - 2 if slot_w >= 5 else slot_w
    min_h = max(3, max_h - 1)
    min_w = max(3, max_w - 1)
    frame_h = rng.randint(min_h, max_h)
    frame_w = rng.randint(min_w, max_w)
    row_room = slot_h - frame_h
    col_room = slot_w - frame_w
    r0 = sr0 + rng.randint(0, row_room)
    c0 = sc0 + rng.randint(0, col_room)

    if force_canvas_border:
        if canvas_shape is None:
            raise ValueError("canvas_shape is required when force_canvas_border=True")
        height, width = canvas_shape
        anchors = []
        if sr0 == 0:
            anchors.append((0, c0))
        if sr1 == height - 1:
            anchors.append((height - frame_h, c0))
        if sc0 == 0:
            anchors.append((r0, 0))
        if sc1 == width - 1:
            anchors.append((r0, width - frame_w))
        if not anchors:
            raise ValueError(f"slot {slot} cannot touch the canvas border")
        r0, c0 = rng.choice(anchors)
    return r0, c0, r0 + frame_h - 1, c0 + frame_w - 1


def _draw_perimeter(
    grid: list[list[int]],
    rect: tuple[int, int, int, int],
    color: int,
    *,
    open_gap: bool,
    rng,
) -> None:
    r0, c0, r1, c1 = rect
    cells = sorted(_perimeter(r0, c0, r1, c1))
    if open_gap:
        eligible = [
            (r, c)
            for r, c in cells
            if not (r in (r0, r1) and c in (c0, c1))
        ]
        gap = rng.choice(eligible)
    else:
        gap = None
    for r, c in cells:
        if (r, c) != gap:
            grid[r][c] = color


def _slot_supports_spur(slot: tuple[int, int, int, int]) -> bool:
    r0, c0, r1, c1 = slot
    height, width = r1 - r0 + 1, c1 - c0 + 1
    return (height >= 3 and width >= 4) or (height >= 4 and width >= 3)


def _draw_spurred_frame(
    grid: list[list[int]],
    slot: tuple[int, int, int, int],
    color: int,
    *,
    rng,
) -> None:
    """Draw an exact rectangular perimeter plus one outward side spur."""
    sr0, sc0, sr1, sc1 = slot
    slot_h, slot_w = sr1 - sr0 + 1, sc1 - sc0 + 1
    orientations = []
    if slot_w >= 4:
        orientations.extend(("left", "right"))
    if slot_h >= 4:
        orientations.extend(("up", "down"))
    if not orientations:
        raise ValueError(f"slot {slot} cannot contain a spurred frame")
    orientation = rng.choice(orientations)

    if orientation in {"left", "right"}:
        frame_h = rng.randint(3, slot_h)
        frame_w = rng.randint(3, slot_w - 1)
        r0 = sr0 + rng.randint(0, slot_h - frame_h)
        if orientation == "left":
            c0 = sc0 + 1 + rng.randint(0, slot_w - frame_w - 1)
            spur = (r0 + frame_h // 2, c0 - 1)
        else:
            c0 = sc0 + rng.randint(0, slot_w - frame_w - 1)
            spur = (r0 + frame_h // 2, c0 + frame_w)
    else:
        frame_h = rng.randint(3, slot_h - 1)
        frame_w = rng.randint(3, slot_w)
        c0 = sc0 + rng.randint(0, slot_w - frame_w)
        if orientation == "up":
            r0 = sr0 + 1 + rng.randint(0, slot_h - frame_h - 1)
            spur = (r0 - 1, c0 + frame_w // 2)
        else:
            r0 = sr0 + rng.randint(0, slot_h - frame_h - 1)
            spur = (r0 + frame_h, c0 + frame_w // 2)

    rect = (r0, c0, r0 + frame_h - 1, c0 + frame_w - 1)
    _draw_perimeter(grid, rect, color, open_gap=False, rng=rng)
    grid[spur[0]][spur[1]] = color


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every three consecutive ordinary samples contain all decisive profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_dimension(ctx, overrides, label, default_low, default_high, valid_low, valid_high):
    if label in overrides:
        return ctx.draw_int(label, valid_low, valid_high)
    return ctx.draw_int(label, default_low, default_high)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile = schedule_profile(seed, sample_index, difficulty)
    context_overrides = dict(overrides)
    defaults = {
        "canonical_pair": {
            "n_frames": 2,
            "n_open_decoys": 0,
            "palette_kind": "canonical",
        },
        "open_decoy": {
            "n_frames": 1,
            "n_open_decoys": 1,
            "palette_kind": "canonical",
        },
        "irregular_broad": {
            "n_frames": 1,
            "n_open_decoys": 0,
            "palette_kind": "broad",
        },
    }[profile]
    for name, value in defaults.items():
        context_overrides.setdefault(name, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=context_overrides,
    )

    # One third of every band is an exact canonical-profile anchor, including
    # hard.  Other profiles retain the wider neighborhood.
    if profile == "canonical_pair":
        height = _draw_dimension(ctx, overrides, "grid_h", 7, 8, 7, 10)
        width = _draw_dimension(ctx, overrides, "grid_w", 8, 11, 8, 12)
    else:
        if difficulty == "easy":
            h_range, w_range = (7, 8), (8, 10)
        elif difficulty == "hard":
            h_range, w_range = (9, 10), (10, 12)
        else:
            h_range, w_range = (8, 10), (9, 12)
        height = _draw_dimension(ctx, overrides, "grid_h", *h_range, 7, 10)
        width = _draw_dimension(ctx, overrides, "grid_w", *w_range, 8, 12)

    n_frames = ctx.draw_int("n_frames", 1, 2)
    n_open = ctx.draw_int("n_open_decoys", 0, 1)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    total = n_frames + n_open
    layout_rng = ctx.draw_rng("layout")
    slots = _split_slots(height, width, total, layout_rng)
    layout_rng.shuffle(slots)

    pool = _CANONICAL_COLORS if palette_kind == "canonical" else _BROAD_COLORS
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(pool), total)

    kinds = ["closed_rect"] * n_frames + ["open_rect"] * n_open
    if profile == "irregular_broad" and n_frames:
        kinds[0] = "closed_irregular"
    layout_rng.shuffle(kinds)

    if "closed_irregular" in kinds:
        irregular_index = kinds.index("closed_irregular")
        capable_index = next(
            (index for index, candidate in enumerate(slots) if _slot_supports_spur(candidate)),
            None,
        )
        if capable_index is None:
            raise ValueError(
                f"cannot place irregular closed frame in {height}x{width} with {total} components"
            )
        slots[irregular_index], slots[capable_index] = (
            slots[capable_index],
            slots[irregular_index],
        )

    grid = full_grid(height, width, 0)
    forced_border = False
    for index, (component_slot, kind, color) in enumerate(zip(slots, kinds, colors)):
        shape_rng = ctx.draw_rng(f"shape_{index}")
        if kind == "closed_irregular":
            _draw_spurred_frame(grid, component_slot, color, rng=shape_rng)
            continue
        force_border = profile == "canonical_pair" and not forced_border and kind == "closed_rect"
        rect = _rect_in_slot(
            component_slot,
            shape_rng,
            canvas_shape=(height, width),
            force_canvas_border=force_border,
        )
        forced_border = forced_border or force_border
        _draw_perimeter(
            grid,
            rect,
            color,
            open_gap=(kind == "open_rect"),
            rng=ctx.draw_rng(f"gap_{index}"),
        )

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    return grid
