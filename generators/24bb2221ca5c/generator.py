"""Generator for medium_145 — fill each component's enclosed holes.

The official examples are rectangular hollow frames, but the selected Racket
program is topological: for every same-color 4-connected object, fill every
bbox-local zero region that cannot reach that object's bbox border.  The
curriculum therefore preserves frequent canonical rectangles while adding two
auditable controls:

* a paired gap contrast: a missing corner still encloses a hole under
  4-connectivity, while a missing side cell opens an otherwise similar frame;
* a topology-stress scene containing a dense two-cavity object with an
  L-shaped hole and an outward spur, plus a disconnected ring in the same
  color.  Both cavities and both components fill independently, while exterior
  zeros remain unchanged.

Every three consecutive default samples contain a canonical pair, an open
near-miss, and a broad-palette topology stress case.  Those profiles jointly
refute bbox-fill, rectangle-only, largest-only, palette-only, border-skip,
one-hole-only, color-merged, 8-connected-hole, rectangular-hole-only, and
identity shortcuts without changing the authoritative rule.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24bb2221ca5c"
TASK_ID = "24bb2221ca5c"
VERSION = "3.2.0"
RULE_HASH = "514c258ab731"

SUMMARY = (
    "A 0-background grid contains 1-2 closed hollow same-color objects in "
    "one or more colors. Canonical scenes use rectangular frames. One scheduled "
    "contrast pairs a corner-gap frame, whose interior remains 4-connectedly "
    "enclosed, with a side-gap frame whose interior is open. Another scheduled "
    "control uses a dense two-cavity object with an L-shaped hole and one "
    "outward spur plus a disconnected same-color frame. Fill every zero cell "
    "topologically enclosed inside each closed object with that object's color, "
    "preserve all existing nonzero cells, and leave open regions unchanged."
)

INVARIANTS = [
    "background is 0",
    "there are 1-2 closed hollow components and at most one open-frame decoy",
    "disconnected components have a one-cell moat and may reuse a nonzero color",
    "closed components include rectangles, corner-gap 4-connected enclosures, one-spur frames, divider rings, and dense cavity masses",
    "every closed component encloses one or two bbox-local zero regions",
]

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical_pair", "gap_contrast", "topology_stress")
PALETTE_KINDS = ("canonical", "broad")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-aware draw",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-aware draw",
        "valid": "10..14",
    },
    "n_frames": {
        "type": "int",
        "default": "three-profile schedule",
        "valid": "1..2",
    },
    "n_open_decoys": {
        "type": "int",
        "default": "three-profile schedule",
        "valid": "0..1",
    },
    "palette_kind": {
        "type": "str",
        "default": "three-profile schedule",
        "valid": "canonical|broad",
    },
}

_CANONICAL_COLORS = (2, 3, 4, 5, 6, 7, 9)
_OFF_CANONICAL_COLORS = (1, 8)
_ALL_COLORS = tuple(range(1, 10))
# Exact (height, width) profiles with two nonzero colors occur in the official
# examples.  Cycling these anchors gives every difficulty band ample exact
# profile support instead of relying on a low-probability random coincidence.
_CANONICAL_PAIR_DIMS = ((8, 13), (9, 12), (10, 12))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_ALLOWED_OVERRIDES = frozenset(AXES)
Grid = list[list[int]]
Cell = tuple[int, int]
Component = tuple[int, set[Cell]]
SceneEntry = tuple[str, int, set[Cell]]
_CLOSED_KINDS = frozenset(
    {
        "closed_rect",
        "closed_corner_gap",
        "closed_irregular",
        "closed_multi_hole",
        "closed_multi_hole_irregular",
        "closed_cavity_mass",
        "closed_cavity_mass_irregular",
    }
)


def _valid_grid_shape(grid) -> str | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "empty or non-grid input"
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return "ragged grid"
    if len(grid) > 30 or width > 30:
        return f"grid exceeds ARC limit: {len(grid)}x{width}"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid values must be integer ARC colors 0..9"
    return None


def _component_cells(grid: Grid) -> list[Component]:
    """Return same-color 4-connected nonzero components in reading order."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[Component] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: set[Cell] = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                cells.add(current)
                cr, cc = current
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(row0: int, col0: int, row1: int, col1: int) -> set[Cell]:
    return {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }


def _is_rectangular_region(region: set[Cell]) -> bool:
    """Return whether a nonempty cell region exactly fills its own bbox."""
    if not region:
        return False
    row0, col0, row1, col1 = _bbox(region)
    return len(region) == (row1 - row0 + 1) * (col1 - col0 + 1)


def _rectangular_kind(cells: set[Cell]) -> str | None:
    """Classify a complete perimeter or a one-cell gap contrast."""
    if not cells:
        return None
    row0, col0, row1, col1 = _bbox(cells)
    if row1 - row0 + 1 < 3 or col1 - col0 + 1 < 3:
        return None
    border = _perimeter(row0, col0, row1, col1)
    if cells == border:
        return "closed_rect"
    missing = border - cells
    if len(missing) != 1 or not cells < border:
        return None
    mr, mc = next(iter(missing))
    if mr in (row0, row1) and mc in (col0, col1):
        return "closed_corner_gap"
    return "open_rect"


def _multi_hole_rect_kind(cells: set[Cell]) -> str | None:
    """Recognize a rectangular perimeter split into two sealed chambers."""
    if not cells:
        return None
    row0, col0, row1, col1 = _bbox(cells)
    height, width = row1 - row0 + 1, col1 - col0 + 1
    if height < 3 or width < 3:
        return None
    border = _perimeter(row0, col0, row1, col1)

    # Vertical divider.  Each side must retain at least one interior column.
    if width >= 5:
        for divider_col in range(col0 + 2, col1 - 1):
            candidate = border | {
                (row, divider_col) for row in range(row0 + 1, row1)
            }
            if cells == candidate:
                return "closed_multi_hole"

    # Horizontal divider.  Each side must retain at least one interior row.
    if height >= 5:
        for divider_row in range(row0 + 2, row1 - 1):
            candidate = border | {
                (divider_row, col) for col in range(col0 + 1, col1)
            }
            if cells == candidate:
                return "closed_multi_hole"
    return None


def _cavity_mass_base_kind(cells: set[Cell]) -> str | None:
    """Recognize a dense rectangular mass with two enclosed cavities.

    At least one cavity must be nonrectangular and at least one interior cell
    must remain colored.  The full outer border is present, so all bbox-local
    zeros are genuine holes rather than exterior pockets.
    """
    if not cells:
        return None
    row0, col0, row1, col1 = _bbox(cells)
    height, width = row1 - row0 + 1, col1 - col0 + 1
    if min(height, width) < 4 or max(height, width) < 5:
        return None
    border = _perimeter(row0, col0, row1, col1)
    if not border <= cells:
        return None
    interior_cells = {
        (row, col)
        for row in range(row0 + 1, row1)
        for col in range(col0 + 1, col1)
        if (row, col) in cells
    }
    if not interior_cells:
        return None
    regions = _component_hole_regions(cells)
    if len(regions) != 2 or all(_is_rectangular_region(region) for region in regions):
        return None
    return "closed_cavity_mass"


def _cavity_mass_kind(cells: set[Cell]) -> str | None:
    direct = _cavity_mass_base_kind(cells)
    if direct is not None:
        return direct
    for spur in cells:
        base = cells - {spur}
        if _cavity_mass_base_kind(base) is None:
            continue
        row0, col0, row1, col1 = _bbox(base)
        sr, sc = spur
        if row0 <= sr <= row1 and col0 <= sc <= col1:
            continue
        neighbors = sum((sr + dr, sc + dc) in base for dr, dc in _DIR4)
        if neighbors == 1:
            return "closed_cavity_mass_irregular"
    return None


def _classify_component(cells: set[Cell]) -> str | None:
    """Classify the deliberately narrow teaching grammar."""
    rectangular = _rectangular_kind(cells)
    if rectangular is not None:
        return rectangular
    multi_hole = _multi_hole_rect_kind(cells)
    if multi_hole is not None:
        return multi_hole
    # A lawful irregular positive is exactly one outward 4-neighbor spur added
    # to an otherwise exact closed rectangle or two-chamber ring.  This gives
    # a clean topological counterexample while remaining easy to audit.
    for spur in cells:
        base = cells - {spur}
        base_kind = _rectangular_kind(base)
        if base_kind != "closed_rect":
            base_kind = _multi_hole_rect_kind(base)
        if base_kind not in {"closed_rect", "closed_multi_hole"}:
            continue
        row0, col0, row1, col1 = _bbox(base)
        sr, sc = spur
        if row0 <= sr <= row1 and col0 <= sc <= col1:
            continue
        if any((sr + dr, sc + dc) in base for dr, dc in _DIR4):
            return (
                "closed_irregular"
                if base_kind == "closed_rect"
                else "closed_multi_hole_irregular"
            )
    return _cavity_mass_kind(cells)


def _component_hole_regions_with_dirs(
    cells: set[Cell], directions: tuple[tuple[int, int], ...]
) -> list[set[Cell]]:
    """Return bbox-local zero regions unable to reach the border via directions."""
    row0, col0, row1, col1 = _bbox(cells)
    zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if (row, col) not in cells
    }
    seen: set[Cell] = set()
    holes: list[set[Cell]] = []
    for start in sorted(zeros):
        if start in seen:
            continue
        region: set[Cell] = set()
        queue = deque([start])
        seen.add(start)
        touches_border = False
        while queue:
            row, col = queue.popleft()
            region.add((row, col))
            touches_border = touches_border or (
                row in (row0, row1) or col in (col0, col1)
            )
            for dr, dc in directions:
                nxt = (row + dr, col + dc)
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes.append(region)
    return holes


def _component_hole_regions(cells: set[Cell]) -> list[set[Cell]]:
    """Return each bbox-local 4-connected zero region that is enclosed."""
    return _component_hole_regions_with_dirs(cells, _DIR4)


def _component_holes(cells: set[Cell]) -> set[Cell]:
    """Return the union of all bbox-local enclosed zero regions."""
    return set().union(*_component_hole_regions(cells)) if cells else set()


def _components_have_moats(components: list[Component]) -> bool:
    for index, (_, left) in enumerate(components):
        for _, right in components[index + 1 :]:
            if any(
                abs(lr - rr) <= 1 and abs(lc - rc) <= 1
                for lr, lc in left
                for rr, rc in right
            ):
                return False
    return True


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    """Recover each non-dimensional exact axis from a materialized grid."""
    components = _component_cells(grid)
    kinds = [_classify_component(cells) for _, cells in components]
    colors = {color for color, _ in components}
    palette_kind = (
        "canonical"
        if colors and colors <= set(_CANONICAL_COLORS)
        else "broad"
        if colors and bool(colors & set(_OFF_CANONICAL_COLORS))
        else "invalid"
    )
    return {
        "n_frames": sum(kind in _CLOSED_KINDS for kind in kinds),
        "n_open_decoys": sum(kind == "open_rect" for kind in kinds),
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lawful lesson grammar and all official inputs."""
    del difficulty, meta
    shape_error = _valid_grid_shape(grid)
    if shape_error:
        return [shape_error]
    errors: list[str] = []
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    components = _component_cells(grid)
    if not components:
        errors.append("no nonzero components")
        return errors
    kinds: list[str | None] = []
    for color, cells in components:
        kind = _classify_component(cells)
        kinds.append(kind)
        if kind is None:
            errors.append(
                f"color-{color} component is outside the closed-cavity and "
                "one-gap teaching grammar"
            )
            continue
        hole_regions = _component_hole_regions(cells)
        if kind in _CLOSED_KINDS and not hole_regions:
            errors.append(f"color-{color} closed component has no enclosed zero hole")
        if kind in {
            "closed_multi_hole",
            "closed_multi_hole_irregular",
            "closed_cavity_mass",
            "closed_cavity_mass_irregular",
        } and len(hole_regions) != 2:
            errors.append(
                f"color-{color} two-cavity component has {len(hole_regions)} holes"
            )
        if kind in {
            "closed_rect",
            "closed_corner_gap",
            "closed_irregular",
        } and len(hole_regions) != 1:
            errors.append(
                f"color-{color} single-chamber component has {len(hole_regions)} holes"
            )
        if kind in {"closed_cavity_mass", "closed_cavity_mass_irregular"} and not any(
            not _is_rectangular_region(region) for region in hole_regions
        ):
            errors.append(f"color-{color} cavity mass lacks a nonrectangular hole")
        if kind == "open_rect" and hole_regions:
            errors.append(f"color-{color} open decoy unexpectedly encloses zero cells")

    n_closed = sum(kind in _CLOSED_KINDS for kind in kinds)
    n_open = sum(kind == "open_rect" for kind in kinds)
    if not 1 <= n_closed <= 2:
        errors.append(f"expected 1-2 closed hollow components, found {n_closed}")
    if not 0 <= n_open <= 1:
        errors.append(f"expected 0-1 open decoys, found {n_open}")
    if len(components) != n_closed + n_open:
        errors.append("unclassified nonzero component present")
    if not _components_have_moats(components):
        errors.append("components must be separated by a one-cell moat")
    return errors


def _lawful_scene(grid) -> list[SceneEntry] | None:
    if self_check(grid):
        return None
    return [
        (_classify_component(cells), color, cells)
        for color, cells in _component_cells(grid)
    ]


def strict_canonical_like(grid) -> list[str]:
    """Semantic-gate hook for the official rectangular task neighborhood."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    reasons: list[str] = []
    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 11 and 10 <= width <= 13):
        reasons.append(
            f"dimensions {height}x{width} outside canonical envelope 8..11 x 10..13"
        )
    observed = observe_overrides(grid)
    if observed["palette_kind"] != "canonical":
        reasons.append("official inputs use only the observed canonical color set")
    if observed["n_open_decoys"] != 0:
        reasons.append("official inputs contain no open-frame decoy")
    scene = _lawful_scene(grid)
    if scene is not None and len({color for _, color, _ in scene}) != len(scene):
        reasons.append("official inputs use a distinct color for each component")
    if scene is not None and any(kind != "closed_rect" for kind, _, _ in scene):
        reasons.append("official inputs use exact rectangular closed frames")
    return reasons


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected bbox-local Racket hole fill."""
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        for row, col in _component_holes(cells):
            out[row][col] = color
    return out


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _fill_component_bboxes(grid: Grid) -> Grid:
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        row0, col0, row1, col1 = _bbox(cells)
        for row in range(row0 + 1, row1):
            for col in range(col0 + 1, col1):
                if out[row][col] == 0:
                    out[row][col] = color
    return out


def _fill_selected_holes(grid: Grid, predicate) -> Grid:
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        kind = _classify_component(cells)
        holes = _component_holes(cells)
        if holes and predicate(kind, color, cells, holes):
            for row, col in holes:
                out[row][col] = color
    return out


def _fill_largest_closed_only(grid: Grid) -> Grid:
    candidates = []
    for color, cells in _component_cells(grid):
        holes = _component_holes(cells)
        if holes:
            candidates.append((len(cells), color, holes))
    out = [list(row) for row in grid]
    if not candidates:
        return out
    _, color, holes = max(
        candidates,
        key=lambda item: (item[0], -min(item[2])[0], -min(item[2])[1]),
    )
    for row, col in holes:
        out[row][col] = color
    return out


def _fill_one_hole_per_component(grid: Grid) -> Grid:
    """Plausible shortcut: fill only the largest hole in each component."""
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        regions = _component_hole_regions(cells)
        if not regions:
            continue
        chosen = max(regions, key=lambda region: (len(region), tuple(sorted(region))))
        for row, col in chosen:
            out[row][col] = color
    return out


def _fill_eight_connected_holes(grid: Grid) -> Grid:
    """Plausible shortcut: use diagonal connectivity for background holes."""
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        for region in _component_hole_regions_with_dirs(cells, _DIR8):
            for row, col in region:
                out[row][col] = color
    return out


def _fill_rectangular_holes_only(grid: Grid) -> Grid:
    """Plausible shortcut: fill only hole regions that are rectangles."""
    out = [list(row) for row in grid]
    for color, cells in _component_cells(grid):
        for region in _component_hole_regions(cells):
            if not _is_rectangular_region(region):
                continue
            for row, col in region:
                out[row][col] = color
    return out


def _merge_same_color_bboxes(grid: Grid) -> Grid:
    """Plausible shortcut: treat all cells of one color as one bbox object."""
    out = [list(row) for row in grid]
    by_color: dict[int, set[Cell]] = {}
    for color, cells in _component_cells(grid):
        by_color.setdefault(color, set()).update(cells)
    for color, cells in by_color.items():
        row0, col0, row1, col1 = _bbox(cells)
        for row in range(row0 + 1, row1):
            for col in range(col0 + 1, col1):
                if out[row][col] == 0:
                    out[row][col] = color
    return out


def _fill_rectangular_frames_only(grid: Grid) -> Grid:
    return _fill_selected_holes(
        grid, lambda kind, _color, _cells, _holes: kind == "closed_rect"
    )


def _fill_canonical_colors_only(grid: Grid) -> Grid:
    return _fill_selected_holes(
        grid,
        lambda _kind, color, _cells, _holes: color in _CANONICAL_COLORS,
    )


def _touches_canvas_border(grid: Grid, cells: set[Cell]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in cells
    )


def _skip_border_touching_closed_frames(grid: Grid) -> Grid:
    return _fill_selected_holes(
        grid,
        lambda _kind, _color, cells, _holes: not _touches_canvas_border(grid, cells),
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity_no_fill": _identity,
    "fill_every_component_bbox": _fill_component_bboxes,
    "fill_largest_closed_only": _fill_largest_closed_only,
    "rectangular_frames_only": _fill_rectangular_frames_only,
    "canonical_colors_only": _fill_canonical_colors_only,
    "skip_border_touching_closed_frames": _skip_border_touching_closed_frames,
    "fill_one_hole_per_component": _fill_one_hole_per_component,
    "merge_same_color_bboxes": _merge_same_color_bboxes,
    "eight_connected_holes": _fill_eight_connected_holes,
    "rectangular_holes_only": _fill_rectangular_holes_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "fill_every_component_bbox",
        "rectangular_frames_only",
        "canonical_colors_only",
        "eight_connected_holes",
        "rectangular_holes_only",
    )
}


def _witness(predicate):
    def check(grid):
        scene = _lawful_scene(grid)
        return scene is not None and predicate(scene)

    return check


def _closed_entries(scene: list[SceneEntry]) -> list[SceneEntry]:
    return [
        entry
        for entry in scene
        if entry[0] in _CLOSED_KINDS
    ]


SEMANTIC_WITNESSES = {
    "enclosed_hole_fills": _witness(lambda scene: bool(_closed_entries(scene))),
    "two_closed_objects_fill": _witness(
        lambda scene: len(_closed_entries(scene)) == 2
    ),
    "open_gap_decoy_stays_zero": _witness(
        lambda scene: any(kind == "open_rect" for kind, _, _ in scene)
    ),
    "irregular_closed_object_fills": _witness(
        lambda scene: any(
            kind in {
                "closed_irregular",
                "closed_multi_hole",
                "closed_multi_hole_irregular",
                "closed_cavity_mass",
                "closed_cavity_mass_irregular",
            }
            for kind, _, _ in scene
        )
    ),
    "broad_palette_still_fills": _witness(
        lambda scene: any(
            color in _OFF_CANONICAL_COLORS
            for kind, color, _ in scene
            if kind in _CLOSED_KINDS
        )
    ),
    "closed_object_may_touch_canvas_border": lambda grid: (
        (scene := _lawful_scene(grid)) is not None
        and any(
            _touches_canvas_border(grid, cells)
            for kind, _, cells in scene
            if kind in _CLOSED_KINDS
        )
    ),
    "component_may_have_multiple_holes": _witness(
        lambda scene: any(
            len(_component_hole_regions(cells)) >= 2
            for kind, _, cells in scene
            if kind in _CLOSED_KINDS
        )
    ),
    "same_color_components_stay_separate": _witness(
        lambda scene: len({color for _, color, _ in scene}) < len(scene)
    ),
    "corner_gap_still_encloses": _witness(
        lambda scene: any(kind == "closed_corner_gap" for kind, _, _ in scene)
    ),
    "nonrectangular_hole_fills": _witness(
        lambda scene: any(
            any(
                not _is_rectangular_region(region)
                for region in _component_hole_regions(cells)
            )
            for kind, _, cells in scene
            if kind in _CLOSED_KINDS
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
    "component_may_have_multiple_holes": ["fill_one_hole_per_component"],
    "same_color_components_stay_separate": ["merge_same_color_bboxes"],
    "corner_gap_still_encloses": ["eight_connected_holes"],
    "nonrectangular_hole_fills": ["rectangular_holes_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return no reasons only when the demonstrations eliminate all rivals."""
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
            reasons.append(f"demo {index} outside teaching grammar: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with enclosed-hole filling")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query outside teaching grammar: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with enclosed-hole filling")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every three consecutive samples contain all decisive lesson profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _split_slots(
    height: int,
    width: int,
    count: int,
    rng,
    *,
    required_slot_predicate=None,
) -> list[tuple[int, int, int, int]]:
    """Partition a canvas into 1-3 rectangles separated by one blank row/col."""
    if count == 1:
        return [(0, 0, height - 1, width - 1)]

    layouts: list[list[tuple[int, int, int, int]]] = []
    if count == 2:
        if width >= 7:
            left_width = (width - 1) // 2
            right_col = left_width + 1
            layouts.append(
                [
                    (0, 0, height - 1, left_width - 1),
                    (0, right_col, height - 1, width - 1),
                ]
            )
        if height >= 7:
            top_height = (height - 1) // 2
            bottom_row = top_height + 1
            layouts.append(
                [
                    (0, 0, top_height - 1, width - 1),
                    (bottom_row, 0, height - 1, width - 1),
                ]
            )
    elif count == 3:
        if width >= 11:
            base = (width - 2) // 3
            remainder = width - 2 - 3 * base
            widths = [base + (1 if index < remainder else 0) for index in range(3)]
            col = 0
            slots = []
            for slot_width in widths:
                slots.append((0, col, height - 1, col + slot_width - 1))
                col += slot_width + 1
            if all(slot[3] - slot[1] + 1 >= 3 for slot in slots):
                layouts.append(slots)
        if height >= 7 and width >= 7:
            top_height = (height - 1) // 2
            bottom_row = top_height + 1
            left_width = (width - 1) // 2
            right_col = left_width + 1
            layouts.extend(
                [
                    [
                        (0, 0, top_height - 1, left_width - 1),
                        (0, right_col, top_height - 1, width - 1),
                        (bottom_row, 0, height - 1, width - 1),
                    ],
                    [
                        (0, 0, top_height - 1, width - 1),
                        (bottom_row, 0, height - 1, left_width - 1),
                        (bottom_row, right_col, height - 1, width - 1),
                    ],
                ]
            )
    if required_slot_predicate is not None:
        layouts = [
            layout
            for layout in layouts
            if any(required_slot_predicate(slot) for slot in layout)
        ]
    if not layouts:
        raise ValueError(f"cannot place {count} moat-separated frames in {height}x{width}")
    return rng.choice(layouts)


def _rect_in_slot(
    slot: tuple[int, int, int, int],
    rng,
    *,
    canvas_shape: tuple[int, int] | None = None,
    force_canvas_border: bool = False,
) -> tuple[int, int, int, int]:
    row0, col0, row1, col1 = slot
    slot_height = row1 - row0 + 1
    slot_width = col1 - col0 + 1
    if slot_height < 3 or slot_width < 3:
        raise ValueError(f"slot {slot} is too small for a hollow frame")

    frame_height = rng.randint(3, min(7, slot_height))
    frame_width = rng.randint(3, min(7, slot_width))
    row_room = slot_height - frame_height
    col_room = slot_width - frame_width
    draw_row = row0 + rng.randint(0, row_room)
    draw_col = col0 + rng.randint(0, col_room)

    if force_canvas_border:
        if canvas_shape is None:
            raise ValueError("canvas_shape required for border-forced frame")
        height, width = canvas_shape
        anchors = []
        if row0 == 0:
            anchors.append((0, draw_col))
        if row1 == height - 1:
            anchors.append((height - frame_height, draw_col))
        if col0 == 0:
            anchors.append((draw_row, 0))
        if col1 == width - 1:
            anchors.append((draw_row, width - frame_width))
        if not anchors:
            raise ValueError(f"slot {slot} cannot touch the canvas border")
        draw_row, draw_col = rng.choice(anchors)
    return (
        draw_row,
        draw_col,
        draw_row + frame_height - 1,
        draw_col + frame_width - 1,
    )


def _draw_perimeter(
    grid: Grid,
    rect: tuple[int, int, int, int],
    color: int,
    *,
    gap_kind: str | None,
    rng,
) -> None:
    row0, col0, row1, col1 = rect
    cells = sorted(_perimeter(row0, col0, row1, col1))
    gap = None
    if gap_kind == "side":
        eligible = [
            (row, col)
            for row, col in cells
            if not (row in (row0, row1) and col in (col0, col1))
        ]
        gap = rng.choice(eligible)
    elif gap_kind == "corner":
        gap = rng.choice(
            [(row0, col0), (row0, col1), (row1, col0), (row1, col1)]
        )
    elif gap_kind is not None:
        raise ValueError(f"unknown perimeter gap kind: {gap_kind}")
    for row, col in cells:
        if (row, col) != gap:
            grid[row][col] = color


def _slot_supports_spur(slot: tuple[int, int, int, int]) -> bool:
    row0, col0, row1, col1 = slot
    height, width = row1 - row0 + 1, col1 - col0 + 1
    return (height >= 3 and width >= 4) or (height >= 4 and width >= 3)


def _slot_supports_multi_hole_spur(slot: tuple[int, int, int, int]) -> bool:
    row0, col0, row1, col1 = slot
    height, width = row1 - row0 + 1, col1 - col0 + 1
    return any(
        (
            width >= 6 and height >= 3,  # vertical divider, left/right spur
            width >= 5 and height >= 4,  # vertical divider, up/down spur
            width >= 4 and height >= 5,  # horizontal divider, left/right spur
            width >= 3 and height >= 6,  # horizontal divider, up/down spur
        )
    )


def _slot_supports_cavity_mass_spur(slot: tuple[int, int, int, int]) -> bool:
    """Whether a slot can hold a 4x5/5x4 cavity mass plus one outward spur."""
    row0, col0, row1, col1 = slot
    height, width = row1 - row0 + 1, col1 - col0 + 1
    required_shapes = ((4, 6), (5, 5), (5, 5), (6, 4))
    return any(height >= needed_h and width >= needed_w for needed_h, needed_w in required_shapes)


def _draw_spurred_frame(
    grid: Grid,
    slot: tuple[int, int, int, int],
    color: int,
    *,
    rng,
) -> None:
    """Draw an exact rectangular perimeter plus one outward side spur."""
    row0, col0, row1, col1 = slot
    slot_height = row1 - row0 + 1
    slot_width = col1 - col0 + 1
    orientations = []
    if slot_width >= 4:
        orientations.extend(("left", "right"))
    if slot_height >= 4:
        orientations.extend(("up", "down"))
    if not orientations:
        raise ValueError(f"slot {slot} cannot contain a spurred frame")
    orientation = rng.choice(orientations)

    if orientation in {"left", "right"}:
        frame_height = rng.randint(3, min(7, slot_height))
        frame_width = rng.randint(3, min(7, slot_width - 1))
        draw_row = row0 + rng.randint(0, slot_height - frame_height)
        if orientation == "left":
            draw_col = col0 + 1 + rng.randint(0, slot_width - frame_width - 1)
            spur = (draw_row + frame_height // 2, draw_col - 1)
        else:
            draw_col = col0 + rng.randint(0, slot_width - frame_width - 1)
            spur = (draw_row + frame_height // 2, draw_col + frame_width)
    else:
        frame_height = rng.randint(3, min(7, slot_height - 1))
        frame_width = rng.randint(3, min(7, slot_width))
        draw_col = col0 + rng.randint(0, slot_width - frame_width)
        if orientation == "up":
            draw_row = row0 + 1 + rng.randint(0, slot_height - frame_height - 1)
            spur = (draw_row - 1, draw_col + frame_width // 2)
        else:
            draw_row = row0 + rng.randint(0, slot_height - frame_height - 1)
            spur = (draw_row + frame_height, draw_col + frame_width // 2)

    rect = (
        draw_row,
        draw_col,
        draw_row + frame_height - 1,
        draw_col + frame_width - 1,
    )
    _draw_perimeter(grid, rect, color, gap_kind=None, rng=rng)
    grid[spur[0]][spur[1]] = color


def _draw_multi_hole_spurred_frame(
    grid: Grid,
    slot: tuple[int, int, int, int],
    color: int,
    *,
    rng,
) -> None:
    """Draw a two-chamber rectangular ring plus one outward connected spur."""
    row0, col0, row1, col1 = slot
    slot_height = row1 - row0 + 1
    slot_width = col1 - col0 + 1
    options: list[tuple[str, str]] = []
    if slot_width >= 6 and slot_height >= 3:
        options.extend(("vertical", side) for side in ("left", "right"))
    if slot_width >= 5 and slot_height >= 4:
        options.extend(("vertical", side) for side in ("up", "down"))
    if slot_width >= 4 and slot_height >= 5:
        options.extend(("horizontal", side) for side in ("left", "right"))
    if slot_width >= 3 and slot_height >= 6:
        options.extend(("horizontal", side) for side in ("up", "down"))
    if not options:
        raise ValueError(f"slot {slot} cannot contain a multi-hole spurred frame")

    divider_orientation, spur_side = rng.choice(options)
    min_height = 3 if divider_orientation == "vertical" else 5
    min_width = 5 if divider_orientation == "vertical" else 3
    max_height = slot_height - (1 if spur_side in {"up", "down"} else 0)
    max_width = slot_width - (1 if spur_side in {"left", "right"} else 0)
    frame_height = rng.randint(min_height, min(7, max_height))
    frame_width = rng.randint(min_width, min(9, max_width))

    if spur_side == "up":
        draw_row = row0 + 1 + rng.randint(0, slot_height - frame_height - 1)
        draw_col = col0 + rng.randint(0, slot_width - frame_width)
    elif spur_side == "down":
        draw_row = row0 + rng.randint(0, slot_height - frame_height - 1)
        draw_col = col0 + rng.randint(0, slot_width - frame_width)
    elif spur_side == "left":
        draw_row = row0 + rng.randint(0, slot_height - frame_height)
        draw_col = col0 + 1 + rng.randint(0, slot_width - frame_width - 1)
    else:
        draw_row = row0 + rng.randint(0, slot_height - frame_height)
        draw_col = col0 + rng.randint(0, slot_width - frame_width - 1)

    draw_row1 = draw_row + frame_height - 1
    draw_col1 = draw_col + frame_width - 1
    for row, col in _perimeter(draw_row, draw_col, draw_row1, draw_col1):
        grid[row][col] = color

    if divider_orientation == "vertical":
        divider_col = draw_col + rng.randint(2, frame_width - 3)
        for row in range(draw_row + 1, draw_row1):
            grid[row][divider_col] = color
    else:
        divider_row = draw_row + rng.randint(2, frame_height - 3)
        for col in range(draw_col + 1, draw_col1):
            grid[divider_row][col] = color

    if spur_side == "up":
        spur = (draw_row - 1, draw_col + rng.randint(1, frame_width - 2))
    elif spur_side == "down":
        spur = (draw_row1 + 1, draw_col + rng.randint(1, frame_width - 2))
    elif spur_side == "left":
        spur = (draw_row + rng.randint(1, frame_height - 2), draw_col - 1)
    else:
        spur = (draw_row + rng.randint(1, frame_height - 2), draw_col1 + 1)
    grid[spur[0]][spur[1]] = color


def _draw_cavity_mass_spurred_frame(
    grid: Grid,
    slot: tuple[int, int, int, int],
    color: int,
    *,
    rng,
) -> None:
    """Draw a dense two-cavity mass with one L-hole and one outward spur."""
    row0, col0, row1, col1 = slot
    slot_height = row1 - row0 + 1
    slot_width = col1 - col0 + 1
    options: list[tuple[bool, str, int, int]] = []
    for transpose, (base_height, base_width) in (
        (False, (4, 5)),
        (True, (5, 4)),
    ):
        for spur_side in ("left", "right", "up", "down"):
            needed_height = base_height + (spur_side in {"up", "down"})
            needed_width = base_width + (spur_side in {"left", "right"})
            if slot_height >= needed_height and slot_width >= needed_width:
                options.append((transpose, spur_side, base_height, base_width))
    if not options:
        raise ValueError(f"slot {slot} cannot contain a cavity-mass spur profile")

    transpose, spur_side, base_height, base_width = rng.choice(options)
    if spur_side == "up":
        draw_row = row0 + 1 + rng.randint(0, slot_height - base_height - 1)
        draw_col = col0 + rng.randint(0, slot_width - base_width)
    elif spur_side == "down":
        draw_row = row0 + rng.randint(0, slot_height - base_height - 1)
        draw_col = col0 + rng.randint(0, slot_width - base_width)
    elif spur_side == "left":
        draw_row = row0 + rng.randint(0, slot_height - base_height)
        draw_col = col0 + 1 + rng.randint(0, slot_width - base_width - 1)
    else:
        draw_row = row0 + rng.randint(0, slot_height - base_height)
        draw_col = col0 + rng.randint(0, slot_width - base_width - 1)

    for row in range(draw_row, draw_row + base_height):
        for col in range(draw_col, draw_col + base_width):
            grid[row][col] = color

    # Canonical 4x5 local cavities: one singleton and one L-shaped region.
    hole_cells = {(1, 1), (1, 3), (2, 2), (2, 3)}
    reflect_rows = bool(rng.randrange(2))
    reflect_cols = bool(rng.randrange(2))
    transformed: set[Cell] = set()
    for local_row, local_col in hole_cells:
        if transpose:
            local_row, local_col = local_col, local_row
        if reflect_rows:
            local_row = base_height - 1 - local_row
        if reflect_cols:
            local_col = base_width - 1 - local_col
        transformed.add((local_row, local_col))
    for local_row, local_col in transformed:
        grid[draw_row + local_row][draw_col + local_col] = 0

    if spur_side == "up":
        spur = (draw_row - 1, draw_col + rng.randint(1, base_width - 2))
    elif spur_side == "down":
        spur = (
            draw_row + base_height,
            draw_col + rng.randint(1, base_width - 2),
        )
    elif spur_side == "left":
        spur = (draw_row + rng.randint(1, base_height - 2), draw_col - 1)
    else:
        spur = (
            draw_row + rng.randint(1, base_height - 2),
            draw_col + base_width,
        )
    grid[spur[0]][spur[1]] = color


def _draw_dimension(
    ctx,
    explicit_overrides,
    label: str,
    default_low: int,
    default_high: int,
) -> int:
    if label in explicit_overrides:
        valid_low, valid_high = ((8, 13) if label == "grid_h" else (10, 14))
        return ctx.draw_int(label, valid_low, valid_high)
    return ctx.draw_int(label, default_low, default_high)


def _choose_colors(
    kinds: list[str], palette_kind: str, rng, *, repeat_closed: bool = False
) -> list[int]:
    count = len(kinds)
    closed_indices = [index for index, kind in enumerate(kinds) if kind in _CLOSED_KINDS]
    if repeat_closed and len(closed_indices) >= 2:
        pool = _CANONICAL_COLORS if palette_kind == "canonical" else _OFF_CANONICAL_COLORS
        shared = rng.choice(pool)
        colors: list[int | None] = [None] * count
        for index in closed_indices:
            colors[index] = shared
        remaining_indices = [index for index, value in enumerate(colors) if value is None]
        remaining_pool = [
            color
            for color in (
                _CANONICAL_COLORS if palette_kind == "canonical" else _ALL_COLORS
            )
            if color != shared
        ]
        for index, color in zip(
            remaining_indices, rng.sample(remaining_pool, len(remaining_indices))
        ):
            colors[index] = color
        return [int(color) for color in colors]
    if palette_kind == "canonical":
        return rng.sample(list(_CANONICAL_COLORS), count)
    closed_index = next(
        index
        for index, kind in enumerate(kinds)
        if kind in _CLOSED_KINDS
    )
    off_color = rng.choice(_OFF_CANONICAL_COLORS)
    remaining = [color for color in _ALL_COLORS if color != off_color]
    colors = rng.sample(remaining, count - 1)
    colors.insert(closed_index, off_color)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile = schedule_profile(seed, sample_index, difficulty)
    profile_defaults = {
        "canonical_pair": {
            "n_frames": 2,
            "n_open_decoys": 0,
            "palette_kind": "canonical",
        },
        "gap_contrast": {
            "n_frames": 1,
            "n_open_decoys": 1,
            "palette_kind": "canonical",
        },
        "topology_stress": {
            "n_frames": 2,
            "n_open_decoys": 0,
            "palette_kind": "broad",
        },
    }[profile]
    context_overrides = dict(overrides)
    for name, value in profile_defaults.items():
        context_overrides.setdefault(name, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=context_overrides,
    )

    if profile == "canonical_pair":
        canonical_index = (int(sample_index) // EXAMPLES_NEEDED) % len(_CANONICAL_PAIR_DIMS)
        scheduled_height, scheduled_width = _CANONICAL_PAIR_DIMS[canonical_index]
        height = _draw_dimension(
            ctx, overrides, "grid_h", scheduled_height, scheduled_height
        )
        width = _draw_dimension(
            ctx, overrides, "grid_w", scheduled_width, scheduled_width
        )
    else:
        if difficulty == "easy":
            height_range, width_range = (8, 9), (10, 12)
        elif difficulty == "hard":
            height_range, width_range = (11, 13), (13, 14)
        else:
            height_range, width_range = (9, 11), (11, 13)
        height = _draw_dimension(ctx, overrides, "grid_h", *height_range)
        width = _draw_dimension(ctx, overrides, "grid_w", *width_range)

    n_frames = ctx.draw_int("n_frames", 1, 2)
    n_open = ctx.draw_int("n_open_decoys", 0, 1)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    count = n_frames + n_open
    layout_rng = ctx.draw_rng("layout")
    slots = _split_slots(
        height,
        width,
        count,
        layout_rng,
        required_slot_predicate=(
            _slot_supports_cavity_mass_spur
            if profile == "topology_stress" and n_frames
            else None
        ),
    )
    layout_rng.shuffle(slots)

    kinds = ["closed_rect"] * n_frames + ["open_rect"] * n_open
    if profile == "gap_contrast" and n_frames:
        kinds[0] = "closed_corner_gap"
    if profile == "topology_stress" and n_frames:
        kinds[0] = "closed_cavity_mass_irregular"
    layout_rng.shuffle(kinds)

    if "closed_cavity_mass_irregular" in kinds:
        irregular_index = kinds.index("closed_cavity_mass_irregular")
        capable_index = next(
            (
                index
                for index, candidate in enumerate(slots)
                if _slot_supports_cavity_mass_spur(candidate)
            ),
            None,
        )
        if capable_index is None:
            raise ValueError(
                f"cannot place topology-stress frame in {height}x{width} with {count} components"
            )
        slots[irregular_index], slots[capable_index] = (
            slots[capable_index],
            slots[irregular_index],
        )

    colors = _choose_colors(
        kinds,
        palette_kind,
        ctx.draw_rng("colors"),
        repeat_closed=(profile == "topology_stress"),
    )
    grid = full_grid(height, width, 0)
    forced_border = False
    for index, (slot, kind, color) in enumerate(zip(slots, kinds, colors)):
        shape_rng = ctx.draw_rng(f"shape_{index}")
        if kind == "closed_irregular":
            _draw_spurred_frame(grid, slot, color, rng=shape_rng)
            continue
        if kind == "closed_multi_hole_irregular":
            _draw_multi_hole_spurred_frame(grid, slot, color, rng=shape_rng)
            continue
        if kind == "closed_cavity_mass_irregular":
            _draw_cavity_mass_spurred_frame(grid, slot, color, rng=shape_rng)
            continue
        force_border = (
            profile == "canonical_pair"
            and not forced_border
            and kind == "closed_rect"
        )
        rect = _rect_in_slot(
            slot,
            shape_rng,
            canvas_shape=(height, width),
            force_canvas_border=force_border,
        )
        forced_border = forced_border or force_border
        _draw_perimeter(
            grid,
            rect,
            color,
            gap_kind=(
                "side"
                if kind == "open_rect"
                else "corner"
                if kind == "closed_corner_gap"
                else None
            ),
            rng=ctx.draw_rng(f"gap_{index}"),
        )

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    return grid
