"""Generator for ARC task cbe60e2c4b18: intersect two aligned panels.

The input is two equal-size monochrome occupancy masks separated by one full
vertical color-9 divider.  The output is a same-size color-8 mask containing
exactly the coordinates occupied in both panels.  Ordinary draws always include
shared cells and private cells on both sides, so intersection differs from
union, xor, and copying either panel.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels


GENERATOR_ID = "cbe60e2c4b18"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "cd6a6225c112"
SUMMARY = (
    "Split two equal panels at the vertical 9 divider and paint color 8 only "
    "where both aligned panel cells are nonzero."
)

INVARIANTS = [
    "one full-height color-9 column separates two equal-size panels",
    "each panel is monochrome apart from background and may use any lawful color",
    "the aligned supports overlap in at least two cells",
    "each panel support is one 4-connected object with at least one private cell",
    "the output is the same-size color-8 mask of the support intersection",
]

PALETTE_PAIRS = {
    "canonical_23": (2, 3),
    "canonical_24": (2, 4),
    "same_gray": (5, 5),
    "contrast": (6, 1),
    "varied": (4, 7),
    "green_azure": (3, 8),
}
_PALETTE_FROM_PAIR = {pair: name for name, pair in PALETTE_PAIRS.items()}
_OVERLAP_LAYOUTS = ("connected", "disconnected")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty/schedule 5..9", "valid": "5..9"},
    "panel_w": {"type": "int", "default": "difficulty/schedule 5..9", "valid": "5..9"},
    "palette_kind": {
        "type": "str",
        "default": "four-residue teaching schedule with cyclic color variants",
        "valid": "canonical_23|canonical_24|same_gray|contrast|varied|green_azure",
    },
    "shared_count": {"type": "int", "default": "schedule 2..5", "valid": "2..8"},
    "left_only_count": {"type": "int", "default": "schedule 1..4", "valid": "1..6"},
    "right_only_count": {"type": "int", "default": "schedule 1..4", "valid": "1..6"},
    "overlap_layout": {
        "type": "str",
        "default": "alternates connected/disconnected",
        "valid": "connected|disconnected",
    },
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (0, 1, 2, 3)

# Four consecutive draws contain a canonical-profile anchor, both overlap
# topologies, and both same-color and different-color panel pairs.  Within each
# residue, palette variants cycle by schedule round so ordinary generation uses
# every lawful non-divider color without weakening the four-example contract.
_PROFILE_PALETTE_OPTIONS = (
    ("canonical_23",),
    ("same_gray",),
    ("canonical_24", "varied"),
    ("contrast", "green_azure"),
)
_PROFILE_LAYOUTS = ("connected", "disconnected", "connected", "disconnected")

def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic teaching-schedule residue."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height = len(grid)
    width = len(grid[0])
    if not 3 <= height <= 12:
        errors.append(f"panel height must be in 3..12, found {height}")

    divider_cols = [
        col for col in range(width) if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(divider_cols) != 1:
        errors.append(
            f"expected exactly one full-height color-9 divider, found {len(divider_cols)}"
        )
        return {"errors": errors, "height": height, "width": width}

    divider = divider_cols[0]
    if divider == 0 or divider == width - 1 or divider * 2 + 1 != width:
        errors.append("divider must split two equal-width nonempty panels")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "divider": divider,
        }

    panel_width = divider
    if not 3 <= panel_width <= 12:
        errors.append(f"panel width must be in 3..12, found {panel_width}")

    left_values = {
        grid[row][col]
        for row in range(height)
        for col in range(panel_width)
        if grid[row][col] != 0
    }
    right_values = {
        grid[row][col]
        for row in range(height)
        for col in range(divider + 1, width)
        if grid[row][col] != 0
    }
    if len(left_values) != 1:
        errors.append(
            f"left panel must use exactly one nonzero color, found {sorted(left_values)}"
        )
    if len(right_values) != 1:
        errors.append(
            f"right panel must use exactly one nonzero color, found {sorted(right_values)}"
        )
    if 9 in left_values or 9 in right_values:
        errors.append("color 9 is reserved for the divider")

    left = {
        (row, col)
        for row in range(height)
        for col in range(panel_width)
        if grid[row][col] != 0
    }
    right = {
        (row, col - divider - 1)
        for row in range(height)
        for col in range(divider + 1, width)
        if grid[row][col] != 0
    }
    shared = left & right
    left_only = left - shared
    right_only = right - shared

    if len(shared) < 2:
        errors.append(f"expected at least two shared occupied coordinates, found {len(shared)}")
    if not left_only:
        errors.append("left panel needs a private occupied cell")
    if not right_only:
        errors.append("right panel needs a private occupied cell")
    if left and _component_count(left) != 1:
        errors.append("left panel support must be one 4-connected component")
    if right and _component_count(right) != 1:
        errors.append("right panel support must be one 4-connected component")

    left_color = next(iter(left_values)) if len(left_values) == 1 else None
    right_color = next(iter(right_values)) if len(right_values) == 1 else None
    layout = None
    if shared:
        layout = "connected" if _component_count(shared) == 1 else "disconnected"

    return {
        "errors": errors,
        "height": height,
        "panel_width": panel_width,
        "divider": divider,
        "left": left,
        "right": right,
        "shared": shared,
        "left_only": left_only,
        "right_only": right_only,
        "left_color": left_color,
        "right_color": right_color,
        "palette_kind": _PALETTE_FROM_PAIR.get((left_color, right_color)),
        "overlap_layout": layout,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, ambiguous, or unrealized input scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a lawful generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    observed: dict[str, int | str] = {
        "grid_h": analysis["height"],
        "panel_w": analysis["panel_width"],
        "shared_count": len(analysis["shared"]),
        "left_only_count": len(analysis["left_only"]),
        "right_only_count": len(analysis["right_only"]),
        "overlap_layout": analysis["overlap_layout"],
    }
    if analysis["palette_kind"] is not None:
        observed["palette_kind"] = analysis["palette_kind"]
    return observed


def _paint_mask(cells: set[tuple[int, int]], height: int, width: int) -> list[list[int]]:
    output = full_grid(height, width, 0)
    for row, col in cells:
        output[row][col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid intersection scene: " + "; ".join(analysis["errors"]))
    return _paint_mask(analysis["shared"], analysis["height"], analysis["panel_width"])


def strict_canonical_like(grid) -> list[str]:
    """The task-linked lawful manifold used by the semantic gate."""
    return self_check(grid)


def _rival_from_cells(selector: Callable[[dict[str, Any]], set[tuple[int, int]]]):
    def rival(grid):
        analysis = _analysis(grid)
        if analysis["errors"]:
            raise ValueError("invalid grid for rival")
        return _paint_mask(
            selector(analysis), analysis["height"], analysis["panel_width"]
        )

    return rival


_rival_left_panel = _rival_from_cells(lambda a: set(a["left"]))
_rival_right_panel = _rival_from_cells(lambda a: set(a["right"]))
_rival_union = _rival_from_cells(lambda a: set(a["left"] | a["right"]))
_rival_xor = _rival_from_cells(lambda a: set(a["left"] ^ a["right"]))


def _conditional_intersection(grid, predicate: Callable[[dict[str, Any]], bool]):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for rival")
    cells = analysis["shared"] if predicate(analysis) else set()
    return _paint_mask(cells, analysis["height"], analysis["panel_width"])


def _rival_same_colors_only(grid):
    return _conditional_intersection(grid, lambda a: a["left_color"] == a["right_color"])


def _rival_different_colors_only(grid):
    return _conditional_intersection(grid, lambda a: a["left_color"] != a["right_color"])


def _rival_connected_only(grid):
    return _conditional_intersection(grid, lambda a: a["overlap_layout"] == "connected")


def _rival_disconnected_only(grid):
    return _conditional_intersection(
        grid, lambda a: a["overlap_layout"] == "disconnected"
    )


SEMANTIC_RIVALS = {
    "copy_left_panel": _rival_left_panel,
    "copy_right_panel": _rival_right_panel,
    "union": _rival_union,
    "xor": _rival_xor,
    "same_colors_only": _rival_same_colors_only,
    "different_colors_only": _rival_different_colors_only,
    "connected_overlap_only": _rival_connected_only,
    "disconnected_overlap_only": _rival_disconnected_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and predicate(analysis)

    return wrapped


SEMANTIC_WITNESSES = {
    "nonempty_intersection": _witness(lambda a: bool(a["shared"])),
    "left_private_distractor": _witness(lambda a: bool(a["left_only"])),
    "right_private_distractor": _witness(lambda a: bool(a["right_only"])),
    "same_color_panels": _witness(lambda a: a["left_color"] == a["right_color"]),
    "different_color_panels": _witness(lambda a: a["left_color"] != a["right_color"]),
    "connected_overlap": _witness(lambda a: a["overlap_layout"] == "connected"),
    "disconnected_overlap": _witness(
        lambda a: a["overlap_layout"] == "disconnected"
    ),
}

WITNESS_RIVALS = {
    "nonempty_intersection": ["xor"],
    "left_private_distractor": ["copy_left_panel", "union"],
    "right_private_distractor": ["copy_right_panel", "union"],
    "same_color_panels": ["different_colors_only"],
    "different_color_panels": ["same_colors_only"],
    "connected_overlap": ["disconnected_overlap_only"],
    "disconnected_overlap": ["connected_overlap_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every sliding four-demo lesson to determine the query answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        analyses.append(analysis)
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the aligned intersection mask")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")

    if analyses:
        if not any(a["left_color"] == a["right_color"] for a in analyses):
            reasons.append("demonstrations do not refute a different-colors-only rule")
        if not any(a["left_color"] != a["right_color"] for a in analyses):
            reasons.append("demonstrations do not refute a same-colors-only rule")
        if not any(a["overlap_layout"] == "connected" for a in analyses):
            reasons.append("demonstrations do not include connected overlap")
        if not any(a["overlap_layout"] == "disconnected" for a in analyses):
            reasons.append("demonstrations do not include disconnected overlap")

    # A rival that fits every demonstration is harmless only when it gives the
    # same official query answer.  Otherwise the lesson admits two answers.
    if not query_errors:
        official_query = rule_mirror(query["input"])
        for name, competitor in LESSON_COMPETITORS.items():
            try:
                fits_demos = all(
                    competitor(demo["input"]) == demo["output"] for demo in demos
                )
            except (KeyError, TypeError, ValueError):
                continue
            if fits_demos and competitor(query["input"]) != official_query:
                reasons.append(f"competitor {name!r} fits demos but changes query answer")
    return reasons


def _panel(height: int, width: int, cells: set[tuple[int, int]], color: int):
    panel = full_grid(height, width, 0)
    for row, col in cells:
        panel[row][col] = color
    return panel


def _connected_cells(rng, height: int, width: int, count: int) -> set[tuple[int, int]]:
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < count:
        frontier: list[tuple[int, int]] = []
        for row, col in cells:
            for candidate in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    0 <= candidate[0] < height
                    and 0 <= candidate[1] < width
                    and candidate not in cells
                ):
                    frontier.append(candidate)
        if not frontier:
            raise ValueError("could not grow connected overlap support")
        cells.add(rng.choice(frontier))
    return cells


def _grow_private_cells(
    rng,
    height: int,
    width: int,
    shared: set[tuple[int, int]],
    count: int,
    *,
    initial: set[tuple[int, int]] | None = None,
    forbidden: set[tuple[int, int]] | None = None,
) -> set[tuple[int, int]]:
    """Grow exactly ``count`` private cells while keeping one panel connected."""
    private = set(initial or ())
    blocked = set(forbidden or ())
    if len(private) > count:
        raise ValueError("initial private support exceeds requested count")
    while len(private) < count:
        support = shared | private
        candidates: set[tuple[int, int]] = set()
        for row, col in support:
            for candidate in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    0 <= candidate[0] < height
                    and 0 <= candidate[1] < width
                    and candidate not in shared
                    and candidate not in private
                    and candidate not in blocked
                ):
                    candidates.add(candidate)
        if not candidates:
            raise ValueError("could not grow connected private support")
        private.add(rng.choice(sorted(candidates)))
    return private


def _disconnected_supports(
    rng,
    height: int,
    width: int,
    shared_count: int,
    left_count: int,
    right_count: int,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]]]:
    """Build connected panels whose intersection has exactly two components.

    Two diagonal shared seeds in a 2x2 block are connected through opposite
    private corner cells in the two panels.  Both diagonal orientation and
    left/right bridge ownership vary, avoiding a fixed reflected or handed
    shortcut.  Additional shared cells grow onto exactly one shared component,
    so the overlap remains disconnected while both complete panel supports
    remain connected.
    """
    if shared_count < 2 or left_count < 1 or right_count < 1:
        raise ValueError("disconnected overlap needs two shared and one private per panel")

    top = rng.randrange(height - 1)
    left_col = rng.randrange(width - 1)
    northwest = (top, left_col)
    northeast = (top, left_col + 1)
    southwest = (top + 1, left_col)
    southeast = (top + 1, left_col + 1)
    if rng.randrange(2) == 0:
        comp_a, comp_b = {northwest}, {southeast}
        bridge_a, bridge_b = northeast, southwest
    else:
        comp_a, comp_b = {northeast}, {southwest}
        bridge_a, bridge_b = northwest, southeast
    if rng.randrange(2) == 0:
        left_private, right_private = {bridge_a}, {bridge_b}
    else:
        left_private, right_private = {bridge_b}, {bridge_a}

    while len(comp_a) + len(comp_b) < shared_count:
        occupied = comp_a | comp_b | left_private | right_private
        candidates: list[tuple[tuple[int, int], int]] = []
        for row in range(height):
            for col in range(width):
                cell = (row, col)
                if cell in occupied:
                    continue
                neighbors = {
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                }
                touches_a = bool(neighbors & comp_a)
                touches_b = bool(neighbors & comp_b)
                if touches_a ^ touches_b:
                    candidates.append((cell, 0 if touches_a else 1))
        if not candidates:
            raise ValueError("could not grow separated overlap components")
        cell, component = rng.choice(candidates)
        (comp_a if component == 0 else comp_b).add(cell)

    shared = comp_a | comp_b
    left_private = _grow_private_cells(
        rng, height, width, shared, left_count, initial=left_private,
        forbidden=right_private,
    )
    right_private = _grow_private_cells(
        rng, height, width, shared, right_count, initial=right_private,
        forbidden=left_private,
    )
    if _component_count(shared) != 2:
        raise ValueError("disconnected overlap construction collapsed")
    if _component_count(shared | left_private) != 1:
        raise ValueError("left panel construction disconnected")
    if _component_count(shared | right_private) != 1:
        raise ValueError("right panel construction disconnected")
    return shared, left_private, right_private


def _axis_choice(ctx, name: str, ordinary, full, overrides):
    options = full if name in overrides else ordinary
    return ctx.draw_choice(name, tuple(options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket oracle owns the output."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    canonical_anchor = profile == 0

    if difficulty == "easy":
        height_options = (5, 6)
        width_options = (5, 6)
    elif difficulty == "hard":
        height_options = (6, 7, 8, 9)
        width_options = (6, 7, 8, 9)
    else:
        height_options = (5, 6, 7, 8)
        width_options = (5, 6, 7, 8)
    if canonical_anchor:
        height_options = (5,)
        width_options = (5,)

    height = _axis_choice(ctx, "grid_h", height_options, range(5, 10), overrides)
    width = _axis_choice(ctx, "panel_w", width_options, range(5, 10), overrides)
    palette_options = _PROFILE_PALETTE_OPTIONS[profile]
    palette_kind = _axis_choice(
        ctx,
        "palette_kind",
        (palette_options[(sample_index // len(SCHEDULE_PROFILES)) % len(palette_options)],),
        tuple(PALETTE_PAIRS),
        overrides,
    )
    overlap_layout = _axis_choice(
        ctx,
        "overlap_layout",
        (_PROFILE_LAYOUTS[profile],),
        _OVERLAP_LAYOUTS,
        overrides,
    )
    if canonical_anchor:
        shared_options = (4,)
        left_only_options = (2,)
        right_only_options = (1,)
    elif difficulty == "easy":
        shared_options = (2, 3, 4, 5)
        left_only_options = (1, 2, 3)
        right_only_options = (1, 2, 3)
    elif difficulty == "hard":
        shared_options = (2, 3, 4, 5, 6, 7, 8)
        left_only_options = (2, 3, 4, 5, 6)
        right_only_options = (2, 3, 4, 5, 6)
    else:
        shared_options = (2, 3, 4, 5, 6)
        left_only_options = (1, 2, 3, 4, 5)
        right_only_options = (1, 2, 3, 4, 5)
    shared_count = _axis_choice(
        ctx, "shared_count", shared_options, range(2, 9), overrides
    )
    left_only_count = _axis_choice(
        ctx, "left_only_count", left_only_options, range(1, 7), overrides
    )
    right_only_count = _axis_choice(
        ctx, "right_only_count", right_only_options, range(1, 7), overrides
    )

    required = shared_count + left_only_count + right_only_count
    if required > height * width:
        # Unreachable for the declared domain (max 20 cells in min 25-cell
        # panel), retained as a loud guard against future axis edits.
        raise ValueError(
            f"requested supports need {required} cells but panel has {height * width}"
        )

    support_rng = ctx.draw_rng("supports")
    for _attempt in range(100):
        try:
            if overlap_layout == "connected":
                shared = _connected_cells(support_rng, height, width, shared_count)
                left_only = _grow_private_cells(
                    support_rng, height, width, shared, left_only_count
                )
                right_only = _grow_private_cells(
                    support_rng, height, width, shared, right_only_count,
                    forbidden=left_only,
                )
            else:
                shared, left_only, right_only = _disconnected_supports(
                    support_rng, height, width, shared_count,
                    left_only_count, right_only_count,
                )
            break
        except ValueError:
            continue
    else:
        raise ValueError("could not construct connected panel supports")

    left_support = shared | left_only
    right_support = shared | right_only
    left_color, right_color = PALETTE_PAIRS[palette_kind]

    grid = assemble_vertical_panels(
        [
            _panel(height, width, left_support, left_color),
            _panel(height, width, right_support, right_color),
        ]
    )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [list(row) for row in grid]
