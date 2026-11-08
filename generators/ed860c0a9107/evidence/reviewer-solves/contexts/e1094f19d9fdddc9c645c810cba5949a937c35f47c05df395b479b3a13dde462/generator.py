"""Generator for ARC task ed860c0a9107.

The input contains two to four equal-sized rectangular containers.  Background
is the nonzero color at (0, 0); zero is transparent inside a container.  The
selected Racket rule aligns the container bounding boxes and, at each local
cell, returns the first visible color in row-major container order.

This sampler deliberately includes a true overlap on every generated input so
that the canonical-fitting ``last visible`` shortcut is refuted by ordinary
lessons rather than only by an exceptional diagnostic fixture.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ed860c0a9107"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "8e6a03efc456"
SUMMARY = (
    "Place 2-4 equal solid rectangles of transparent zero and colored payload "
    "on a nonzero background. Align their bounding boxes and overlay them in "
    "row-major object order, taking the first nonzero payload at every local "
    "coordinate. Every generated scene contains a distinct-color overlap that "
    "makes first-object priority observable."
)
INVARIANTS = [
    "background is the nonzero cell at (0,0); zero is transparent",
    "2-4 separated 8-connected containers are solid rectangles of zero/payload cells",
    "all container bounding boxes have the same 2..5 height and width",
    "every container has at least one zero and one colored payload cell",
    "every generated scene has a local overlap whose first and last visible colors differ",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "14..22 with a deterministic 16x16 canonical-scale lane",
        "valid": "14..22",
    },
    "grid_w": {
        "type": "int",
        "default": "14..22 with a deterministic 16x16 canonical-scale lane",
        "valid": "14..22",
    },
    "n_containers": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
    },
    "box_h": {
        "type": "int",
        "default": "difficulty-weighted 2..5",
        "valid": "2..5",
    },
    "box_w": {
        "type": "int",
        "default": "difficulty-weighted 2..5",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
_DOMAINS = {
    "grid_h": tuple(range(14, 23)),
    "grid_w": tuple(range(14, 23)),
    "n_containers": (2, 3, 4),
    "box_h": (2, 3, 4, 5),
    "box_w": (2, 3, 4, 5),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _draw_axis(ctx, overrides, name, *, forced=None, favored=()):
    """Draw an exact observable axis without narrowing its override domain."""
    domain = _DOMAINS[name]
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, domain)
    if forced is not None:
        return ctx.draw_choice(name, (forced,))
    return ctx.draw_choice(name, domain + tuple(favored))


def _curriculum_profile(sample_index):
    # Every four consecutive sample indexes contain exact 16x16 scenes with
    # canonical palette sizes 4, 5, and 6, plus one broader scene.  The profile
    # floor uses consecutive indexes, so every difficulty band is anchored.
    return ("canonical-4", "canonical-5", "canonical-6", "broad")[
        int(sample_index) % 4
    ]


def _positions(n_containers, h, w, box_h, box_w, rng):
    """Choose row-major corner slots; all legal axis combinations fit exactly."""
    slots = (
        (1, 1),
        (1, w - box_w - 1),
        (h - box_h - 1, 1),
        (h - box_h - 1, w - box_w - 1),
    )
    choices = tuple(combinations(slots, n_containers))
    return sorted(rng.choice(choices))


def _payload_patterns(n_containers, box_h, box_w, fills, density, rng):
    """Build aligned patterns with a guaranteed first-vs-last conflict."""
    area = box_h * box_w
    total = n_containers * area
    patterns = [
        [[0 for _ in range(box_w)] for _ in range(box_h)]
        for _ in range(n_containers)
    ]

    conflict_index = rng.randrange(area)
    conflict = divmod(conflict_index, box_w)

    # Reserve one transparent cell per container, distinct from the overlap.
    protected_zero = set()
    for obj_index in range(n_containers):
        zero_index = (conflict_index + 1 + obj_index) % area
        while zero_index == conflict_index:
            zero_index = (zero_index + 1) % area
        protected_zero.add((obj_index, *divmod(zero_index, box_w)))

    assigned = set()
    cr, cc = conflict
    patterns[0][cr][cc] = fills[0]
    assigned.add((0, cr, cc))
    for obj_index in range(1, n_containers):
        # The last visible color is guaranteed to differ from the first.
        patterns[obj_index][cr][cc] = fills[1]
        assigned.add((obj_index, cr, cc))

    available = [
        (obj_index, row, col)
        for obj_index in range(n_containers)
        for row in range(box_h)
        for col in range(box_w)
        if (obj_index, row, col) not in assigned
        and (obj_index, row, col) not in protected_zero
    ]
    rng.shuffle(available)

    # Make the chosen palette observable from pixels, not only RNG provenance.
    for color in fills[2:]:
        obj_index, row, col = available.pop()
        patterns[obj_index][row][col] = color
        assigned.add((obj_index, row, col))

    max_colored = total - n_containers  # one protected transparent cell each
    target = min(max_colored, max(len(assigned), round(total * density)))
    while len(assigned) < target:
        obj_index, row, col = available.pop()
        patterns[obj_index][row][col] = rng.choice(fills)
        assigned.add((obj_index, row, col))

    return patterns


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or float)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _curriculum_profile(sample_index)
    canonical_lane = profile.startswith("canonical-")
    h = _draw_axis(
        ctx, overrides, "grid_h", forced=16 if canonical_lane else None,
        favored=(16, 16, 16),
    )
    w = _draw_axis(
        ctx, overrides, "grid_w", forced=16 if canonical_lane else None,
        favored=(16, 16, 16),
    )

    band = "medium" if difficulty in (None, "default") else difficulty
    n_favored = {
        "easy": (2, 2, 2, 3),
        "medium": (2, 3, 3, 4),
        "hard": (3, 4, 4, 4),
    }[band]
    size_favored = {
        "easy": (2, 3, 3),
        "medium": (3, 4, 4),
        "hard": (4, 5, 5),
    }[band]
    n_containers = _draw_axis(
        ctx, overrides, "n_containers", favored=n_favored
    )
    box_h = _draw_axis(ctx, overrides, "box_h", favored=size_favored)
    box_w = _draw_axis(ctx, overrides, "box_w", favored=size_favored)

    if canonical_lane:
        # Total grid palette includes transparent zero, so 3/4/5 nonzero
        # colors produce the canonical palette profiles 4/5/6.
        n_nonzero_colors = int(profile.rsplit("-", 1)[1]) - 1
    else:
        n_nonzero_colors = ctx.draw_rng("palette_size").choice((3, 4, 5, 6, 7))
    palette = ctx.draw_distinct_colors(
        "palette", n=n_nonzero_colors, exclude={0}
    )
    bg, fills = palette[0], list(palette[1:])

    density_range = {
        "easy": (0.28, 0.42),
        "medium": (0.42, 0.62),
        "hard": (0.62, 0.82),
    }[band]
    density = ctx.draw_rng("payload_density").uniform(*density_range)
    placement_rng = ctx.draw_rng("placement")
    payload_rng = ctx.draw_rng("payload")
    positions = _positions(
        n_containers, h, w, box_h, box_w, placement_rng
    )
    patterns = _payload_patterns(
        n_containers, box_h, box_w, fills, density, payload_rng
    )

    grid = full_grid(h, w, bg)
    for (top, left), pattern in zip(positions, patterns):
        for row in range(box_h):
            for col in range(box_w):
                grid[top + row][left + col] = pattern[row][col]

    analysis = _analyze(grid)
    requested = {
        "grid_h": h,
        "grid_w": w,
        "n_containers": n_containers,
        "box_h": box_h,
        "box_w": box_w,
    }
    if analysis["errors"]:
        raise RuntimeError(
            "internal construction error: " + "; ".join(analysis["errors"])
        )
    if observe_overrides(grid) != requested:
        raise RuntimeError("internal construction error: exact controls drifted")
    if not _priority_overlap(grid):
        raise RuntimeError("internal construction error: priority witness missing")
    return grid


def _components8_non_bg(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_row in range(h):
        for start_col in range(w):
            if grid[start_row][start_col] == bg or (start_row, start_col) in seen:
                continue
            queue = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.pop()
                cells.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != bg
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["expected a nonempty rectangular grid"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid rows must be nonempty lists or tuples"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["ragged grid"], "facts": None}
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    height = len(grid)
    if not 14 <= height <= 22 or not 14 <= width <= 22:
        errors.append(f"grid dimensions must be within 14..22, got {height}x{width}")

    bg = grid[0][0]
    if bg == 0:
        errors.append("background cue at (0,0) must be nonzero")
    components = _components8_non_bg(grid, bg)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 separated containers, found {len(components)}")

    boxes = []
    for cells in components:
        top, left, bottom, right = _bbox(cells)
        box_h, box_w = bottom - top + 1, right - left + 1
        boxes.append((top, left, bottom, right))
        if not 2 <= box_h <= 5 or not 2 <= box_w <= 5:
            errors.append(f"container bbox must be 2..5 per side, got {box_h}x{box_w}")
        expected = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        }
        if set(cells) != expected:
            errors.append("container bbox is not a solid non-background rectangle")
        values = [grid[row][col] for row, col in cells]
        if 0 not in values:
            errors.append("each container must include a transparent zero cell")
        if not any(value not in (0, bg) for value in values):
            errors.append("each container must include a colored payload cell")
        if top == 0 or left == 0 or bottom == height - 1 or right == width - 1:
            errors.append("containers must leave the outer background border intact")

    shapes = {(bottom - top + 1, right - left + 1) for top, left, bottom, right in boxes}
    if boxes and len(shapes) != 1:
        errors.append(f"container bounding boxes must be equal-sized, got {sorted(shapes)}")
    payload_colors = {
        value
        for row in grid
        for value in row
        if value not in (0, bg)
    }
    if len(payload_colors) < 2:
        errors.append("at least two distinct payload colors are required")

    facts = None
    if not errors:
        ordered_boxes = sorted(boxes)
        box_h, box_w = next(iter(shapes))
        facts = {
            "height": height,
            "width": width,
            "bg": bg,
            "boxes": ordered_boxes,
            "box_h": box_h,
            "box_w": box_w,
            "n_containers": len(ordered_boxes),
            "payload_colors": payload_colors,
        }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_containers": facts["n_containers"],
        "box_h": facts["box_h"],
        "box_w": facts["box_w"],
    }


def _overlay(grid, *, take_last):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    bg = facts["bg"]
    boxes = facts["boxes"]
    output = []
    for local_row in range(facts["box_h"]):
        row = []
        for local_col in range(facts["box_w"]):
            visible = []
            for top, left, _bottom, _right in boxes:
                value = grid[top + local_row][left + local_col]
                if value not in (0, bg):
                    visible.append(value)
            row.append((visible[-1] if take_last else visible[0]) if visible else 0)
        output.append(row)
    return output


def rule_mirror(grid):
    """Python mirror for focused tests; the Racket source remains label authority."""
    return _overlay(grid, take_last=False)


def _last_visible(grid):
    """Canonical-fitting rival: reverse the selected first-visible priority."""
    return _overlay(grid, take_last=True)


def _priority_overlap(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    facts = analysis["facts"]
    bg = facts["bg"]
    for local_row in range(facts["box_h"]):
        for local_col in range(facts["box_w"]):
            values = []
            for top, left, _bottom, _right in facts["boxes"]:
                value = grid[top + local_row][left + local_col]
                if value not in (0, bg):
                    values.append(value)
            if len(values) >= 2 and values[0] != values[-1]:
                return True
    return False


def lesson_identifiable(demos, query):
    del query  # Identifiability is established by labeled demonstrations.
    if not demos:
        return ["no labeled demonstrations"]
    for pair in demos:
        try:
            if _last_visible(pair["input"]) != pair["output"]:
                return []
        except (KeyError, TypeError, ValueError) as exc:
            return [f"invalid demonstration: {exc}"]
    return ["demonstrations do not distinguish first-visible from last-visible priority"]


SEMANTIC_WITNESSES = {"priority_overlap": _priority_overlap}
SEMANTIC_RIVALS = {"last_visible": _last_visible}
WITNESS_RIVALS = {"priority_overlap": ["last_visible"]}
CANONICAL_SHORTCUTS = {"last_visible": _last_visible}
LESSON_COMPETITORS = {"last_visible": _last_visible}
