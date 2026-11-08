"""Generator for arc_puzzle_bank_21_set2:S2_M6 — template copies from anchors.

The largest red (2) component is normalized to its bounding-box top-left.
Every blue (1) singleton marks a stamp origin.  The Racket oracle copies the
red offsets in blue while preserving the original input, so an anchor remains
as an extra blue cell when the normalized template omits offset ``(0, 0)``.

The ordinary distribution uses connected four-cell templates with the same
coarse morphology as all canonical examples, varies both origin-present and
origin-absent templates, and occasionally adds a smaller red distractor so the
"largest red component" selection is actually taught.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bbbabb45042b"
TASK_ID = "bbbabb45042b"
RULE_HASH = "6f5eebde1e2e"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A zero-background grid contains one connected four-cell red (2) "
    "template, one to three isolated blue (1) anchor cells, and sometimes "
    "one smaller singleton red distractor.  Normalize the largest red "
    "component by its bounding-box top-left and copy those offsets in blue "
    "at every anchor, preserving the input.  Therefore an anchor is part of "
    "the copied shape when the template contains normalized offset (0, 0), "
    "but remains as an extra marker when that offset is absent."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are blue 1 and red 2",
    "the unique largest red component is a connected four-cell 2x3/3x2 template",
    "an optional second red component is a singleton distractor",
    "there are 1-3 blue singleton anchors and every full template stamp fits in-bounds",
    "template, distractor, anchors, and prospective stamp footprints do not overlap",
]

GRID_DIMS = ("9x11", "10x12", "11x13", "12x14", "13x15", "14x16")
TEMPLATE_KINDS = (
    "vertical_s",
    "t_down",
    "l_bottom",
    "j_bottom",
    "horizontal_s",
    "horizontal_z",
)

# Every shape has four cells, is 4-connected, and occupies a 2x3 or 3x2 bbox.
# The canonical inputs instantiate vertical_s, t_down, and l_bottom.
TEMPLATES: dict[str, tuple[tuple[int, int], ...]] = {
    "vertical_s": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "t_down": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "l_bottom": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "j_bottom": ((0, 1), (1, 1), (2, 0), (2, 1)),
    "horizontal_s": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "horizontal_z": ((0, 0), (0, 1), (1, 1), (1, 2)),
}

AXES = {
    "grid_dims": {
        "type": "str",
        "default": "difficulty-weighted draw",
        "valid": "|".join(GRID_DIMS),
    },
    "template_kind": {
        "type": "str",
        "default": "four-pair lesson schedule",
        "valid": "|".join(TEMPLATE_KINDS),
    },
    "n_anchors": {
        "type": "int",
        "default": "rng 1..3",
        "valid": "1..3",
    },
    "n_red_distractors": {
        "type": "int",
        "default": "one witness in each four-pair lesson",
        "valid": "0..1",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _has_override(ctx, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _scheduled_choice(ctx, label: str, options, scheduled):
    """Record a deterministic lesson schedule while keeping exact overrides live."""
    if _has_override(ctx, label):
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if _has_override(ctx, label):
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (scheduled,)))


def _dims_options(difficulty) -> tuple[str, ...]:
    # All legal values remain present in every band so a globally valid exact
    # override never fails merely because the caller selected a difficulty.
    if difficulty == "easy":
        return (
            "9x11", "9x11", "10x12", "10x12", "11x13",
            "12x14", "13x15", "14x16",
        )
    if difficulty == "hard":
        return (
            "9x11", "10x12", "11x13", "12x14", "13x15",
            "13x15", "14x16", "14x16",
        )
    return (
        "9x11", "10x12", "10x12", "11x13", "11x13",
        "12x14", "12x14", "13x15", "14x16",
    )


def _shape_size(shape) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _translated(shape, r0: int, c0: int) -> set[tuple[int, int]]:
    return {(r0 + dr, c0 + dc) for dr, dc in shape}


def _four_touches(cells: set[tuple[int, int]], other: set[tuple[int, int]]) -> bool:
    return any((r + dr, c + dc) in other for r, c in cells for dr, dc in _CARDINAL)


def _components_of_color(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _kind_for_shape(shape) -> str | None:
    normalized = tuple(sorted(shape))
    for name, candidate in TEMPLATES.items():
        if normalized == tuple(sorted(candidate)):
            return name
    return None


def _anchor_candidates(
    h: int,
    w: int,
    shape,
    red_cells: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], set[tuple[int, int]]]]:
    sh, sw = _shape_size(shape)
    out = []
    for ar in range(h - sh + 1):
        for ac in range(w - sw + 1):
            anchor = (ar, ac)
            footprint = _translated(shape, ar, ac)
            occupied = footprint | {anchor}
            if occupied & red_cells:
                continue
            if _four_touches({anchor}, red_cells):
                continue
            out.append((anchor, footprint))
    return out


def _select_anchors(rng, candidates, n_anchors: int):
    candidates = list(candidates)
    rng.shuffle(candidates)
    chosen: list[tuple[tuple[int, int], set[tuple[int, int]]]] = []
    reserved: set[tuple[int, int]] = set()
    anchors: set[tuple[int, int]] = set()
    for anchor, footprint in candidates:
        occupied = footprint | {anchor}
        if occupied & reserved:
            continue
        if _four_touches({anchor}, anchors):
            continue
        chosen.append((anchor, footprint))
        reserved |= occupied
        anchors.add(anchor)
        if len(chosen) == n_anchors:
            return chosen
    return None


def _find_distractor(
    rng,
    h: int,
    w: int,
    template_cells: set[tuple[int, int]],
    anchor_cells: set[tuple[int, int]],
    reserved: set[tuple[int, int]],
):
    candidates = []
    for r in range(h):
        for c in range(w):
            cell = {(r, c)}
            if (r, c) in reserved:
                continue
            if _four_touches(cell, template_cells | anchor_cells):
                continue
            candidates.append((r, c))
    rng.shuffle(candidates)
    return candidates[0] if candidates else None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    dims_text = ctx.draw_choice("grid_dims", _dims_options(difficulty))
    h, w = (int(part) for part in dims_text.split("x"))

    # Sequential run_one episodes use four consecutive sample indices.  This
    # rotation guarantees both top-left-present and top-left-absent templates
    # in every materialized lesson, while the seed rotates which shape is the
    # query so no fixed query shape leaks through the schedule.
    scheduled_kind = TEMPLATE_KINDS[(seed * 5 + sample_index * 2) % len(TEMPLATE_KINDS)]
    template_kind = _scheduled_choice(
        ctx, "template_kind", TEMPLATE_KINDS, scheduled_kind
    )
    shape = TEMPLATES[template_kind]

    n_anchors = ctx.draw_int("n_anchors", 1, 3)
    scheduled_distractors = 1 if (seed + sample_index) % 4 == 0 else 0
    n_red_distractors = _scheduled_int(
        ctx,
        "n_red_distractors",
        0,
        1,
        scheduled_distractors,
    )

    rng = ctx.draw_rng("layout")
    sh, sw = _shape_size(shape)
    template_origins = [
        (r, c)
        for r in range(h - sh + 1)
        for c in range(w - sw + 1)
    ]
    rng.shuffle(template_origins)

    for tr, tc in template_origins:
        template_cells = _translated(shape, tr, tc)
        candidates = _anchor_candidates(h, w, shape, template_cells)
        selected = _select_anchors(rng, candidates, n_anchors)
        if selected is None:
            continue

        reserved = set(template_cells)
        for anchor, footprint in selected:
            reserved.add(anchor)
            reserved |= footprint

        distractor = None
        if n_red_distractors:
            distractor = _find_distractor(
                rng,
                h,
                w,
                template_cells,
                {anchor for anchor, _footprint in selected},
                reserved,
            )
            if distractor is None:
                continue

        grid = full_grid(h, w, 0)
        for r, c in template_cells:
            grid[r][c] = 2
        if distractor is not None:
            grid[distractor[0]][distractor[1]] = 2
        for (ar, ac), _footprint in selected:
            grid[ar][ac] = 1
        return grid

    # The legal minimum grid has ample capacity for this construction.  A
    # failure therefore indicates a code regression rather than a condition
    # that should be hidden with a shape-changing fallback.
    raise RuntimeError(
        f"unable to place template/anchors for {dims_text}, "
        f"kind={template_kind}, anchors={n_anchors}, "
        f"distractors={n_red_distractors}"
    )


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    red = _components_of_color(grid, 2)
    largest = max(red, key=len) if red else []
    kind = _kind_for_shape(_normalize(largest)) if largest else None
    return {
        "grid_dims": f"{len(grid)}x{len(grid[0])}",
        "template_kind": kind,
        "n_anchors": sum(v == 1 for row in grid for v in row),
        "n_red_distractors": sum(len(comp) == 1 for comp in red),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]

    h, w = len(grid), len(grid[0])
    if f"{h}x{w}" not in GRID_DIMS:
        errors.append(f"unsupported grid dimensions {h}x{w}")

    bad_colors = sorted({v for row in grid for v in row if v not in (0, 1, 2)})
    if bad_colors:
        errors.append(f"unexpected colors outside {{0,1,2}}: {bad_colors}")

    red_components = _components_of_color(grid, 2)
    red_sizes = sorted((len(comp) for comp in red_components), reverse=True)
    if not red_components:
        errors.append("missing red template")
        return errors
    if red_sizes[0] != 4:
        errors.append(f"largest red component must have size 4, got {red_sizes[0]}")
    if len(red_components) not in (1, 2):
        errors.append(f"expected one template plus at most one distractor, got {len(red_components)} red components")
    if any(size != 1 for size in red_sizes[1:]):
        errors.append(f"non-template red components must be singleton distractors, got {red_sizes[1:]}")
    if len(red_sizes) > 1 and red_sizes[0] == red_sizes[1]:
        errors.append("largest red template must be unique")

    template = max(red_components, key=len)
    normalized = _normalize(template)
    template_kind = _kind_for_shape(normalized)
    if template_kind is None:
        errors.append(f"red template is not an allowed connected 2x3/3x2 tetromino: {normalized}")
        return errors

    anchors = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    if not (1 <= len(anchors) <= 3):
        errors.append(f"expected 1-3 blue anchors, got {len(anchors)}")
    blue_components = _components_of_color(grid, 1)
    if any(len(comp) != 1 for comp in blue_components):
        errors.append("every blue anchor must be a 4-connected singleton")

    red_cells = {cell for comp in red_components for cell in comp}
    if _four_touches(anchors, red_cells):
        errors.append("blue anchors must not 4-touch any red component")

    shape = TEMPLATES[template_kind]
    sh, sw = _shape_size(shape)
    reserved: set[tuple[int, int]] = set()
    for ar, ac in sorted(anchors):
        if ar + sh > h or ac + sw > w:
            errors.append(f"anchor {(ar, ac)} cannot fit the full {sh}x{sw} stamp")
            continue
        footprint = _translated(shape, ar, ac)
        occupied = footprint | {(ar, ac)}
        collisions = {
            (r, c)
            for r, c in occupied
            if (r, c) != (ar, ac) and grid[r][c] != 0
        }
        if collisions:
            errors.append(
                f"anchor {(ar, ac)} stamp footprint overlaps foreground at {sorted(collisions)}"
            )
        if occupied & reserved:
            errors.append(f"anchor {(ar, ac)} overlaps another prospective stamp")
        reserved |= occupied

    return errors
