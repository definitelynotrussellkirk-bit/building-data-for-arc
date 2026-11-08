"""Generator for ``725513c9d0c9`` — scale the key-adjacent component.

The color-8 marker is cardinally adjacent to exactly one 4-connected
non-background component.  Crop that multicolor component tightly and upscale
it by 2 while preserving every target-cell color and clearing any marker or
distractor that lies inside the target bounding box.

The default four-example schedule deliberately includes: a single-color
canonical profile, a multicolor target with a disconnected same-color decoy, a
generalized middle-sized target, and a cross-profile canvas example.  Palette
roles rotate and the final slot reuses canvas sizes across target morphologies,
so color-rank, dimension-shape, color-only, size-only, bbox-fill, and 8-neighbor
selection shortcuts cannot survive an ordinary lesson.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "725513c9d0c9"
TASK_ID = GENERATOR_ID
VERSION = "3.3.0"
# sha256[:12] of the whitespace-normalized, comment-preserving selected rule.
RULE_HASH = "d635ca555626"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A 0-background grid contains three 4-connected nonzero components and one "
    "color-8 marker. Exactly one component has a cell at Manhattan distance 1 "
    "from the marker; diagonal-only distractors may also be present. The target "
    "component may contain one or two colors. Render only the full multicolor "
    "target into its tight bounding box, clear non-target intruders, and upscale "
    "the crop by 2 while preserving target colors and holes."
)

INVARIANTS = [
    "background is 0 and the only marker color is 8",
    "exactly one non-marker component is 4-adjacent to the marker",
    "components are 4-connected over all nonzero non-8 colors",
    "the selected component is sparse inside its tight bounding box",
    "non-target cells inside that bbox are cleared from the component crop",
    "the output is the exact 2x nearest-neighbor upscale of that isolated crop",
]

# Canonical component shapes, normalized to a top-left origin.  Distractor
# morphology is retained in the profile so the strict linked census is not a
# dimensions-only approximation.
L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
Z4 = ((0, 0), (0, 1), (1, 1), (1, 2))
L3 = ((0, 0), (0, 1), (1, 0))
L5 = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0))
PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
BAR3 = ((0, 0), (0, 1), (0, 2))
U5 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2))
P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2))
BRANCH6 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2))
T5 = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
DOMINO = ((0, 0), (0, 1))
OCTO8 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))

# Each component entry is (shape, tuple of palette-role indexes).  Multiple
# roles make a component multicolor; a reused role creates a disconnected
# same-color decoy, as in the official test example.
_PROFILES: dict[str, dict[str, Any]] = {
    "canon_l4_equal": {
        "dims": (9, 12),
        "components": ((L4, (0,)), (T4, (1,)), (Z4, (2,))),
        "target": 0,
    },
    "canon_z4_diagonal": {
        "dims": (10, 10),
        "components": ((Z4, (0,)), (L3, (1,)), (L5, (2,))),
        "target": 0,
    },
    "canon_l3_small": {
        "dims": (8, 13),
        "components": ((L3, (0,)), (PLUS5, (1,)), (Z4, (2,))),
        "target": 0,
    },
    "canon_l4_multicolor_distractor": {
        "dims": (11, 11),
        "components": ((L4, (0,)), (BAR3, (1,)), (U5, (2, 3))),
        "target": 0,
    },
    "canon_p5_multicolor_target": {
        "dims": (9, 14),
        "components": ((P5, (0, 1)), (T4, (0,)), (Z4, (2,))),
        "target": 0,
    },
    "general_branch6": {
        "dims": (12, 14),
        "components": ((BRANCH6, (0, 1)), (L3, (0,)), (OCTO8, (2,)), (T5, (3,))),
        "target": 0,
    },
    "general_t5": {
        "dims": (14, 16),
        "components": ((T5, (0,)), (DOMINO, (1,)), (OCTO8, (2,)), (BRANCH6, (3,))),
        "target": 0,
    },
}
PROFILE_NAMES = tuple(_PROFILES)
CANONICAL_PROFILE_NAMES = PROFILE_NAMES[:5]
PALETTE_KINDS = ("canonical", "warm", "cool", "varied")
MARKER_SIDES = ("north", "east", "south", "west")
LAYOUT_MODES = ("diagonal_decoy", "clear")

_PALETTES = {
    "canonical": (2, 3, 4, 5),
    "warm": (1, 2, 4, 9),
    "cool": (1, 5, 6, 7),
    "varied": (3, 6, 7, 9),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot semantic schedule",
        "valid": "canon_l4_equal|canon_z4_diagonal|canon_l3_small|canon_l4_multicolor_distractor|canon_p5_multicolor_target|general_branch6|general_t5",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful palette",
        "valid": "canonical|warm|cool|varied",
    },
    "marker_side": {
        "type": "str",
        "default": "rng cardinal side",
        "valid": "north|east|south|west",
    },
    "layout_mode": {
        "type": "str",
        "default": "alternating diagonal decoy / clear",
        "valid": "diagonal_decoy|clear",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_SIDE_TO_MARKER_DELTA = {
    "north": (-1, 0),
    "east": (0, 1),
    "south": (1, 0),
    "west": (0, -1),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    pts = tuple(cells)
    r0 = min(r for r, _ in pts)
    c0 = min(c for _, c in pts)
    return tuple(sorted((r - r0, c - c0) for r, c in pts))


def _transform(cells: Iterable[tuple[int, int]], index: int) -> tuple[tuple[int, int], ...]:
    transformed = []
    for r, c in cells:
        if index == 0:
            rr, cc = r, c
        elif index == 1:
            rr, cc = c, -r
        elif index == 2:
            rr, cc = -r, -c
        elif index == 3:
            rr, cc = -c, r
        elif index == 4:
            rr, cc = r, -c
        elif index == 5:
            rr, cc = -r, c
        elif index == 6:
            rr, cc = c, r
        elif index == 7:
            rr, cc = -c, -r
        else:
            raise ValueError(f"invalid D4 transform {index}")
        transformed.append((rr, cc))
    return _normalize(transformed)


def _d4_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_transform(cells, index) for index in range(8))


def _component_signature(
    shape: Iterable[tuple[int, int]], color_roles: tuple[int, ...]
) -> tuple[tuple[tuple[int, int], ...], int]:
    return (_d4_signature(shape), len(color_roles))


def _profile_signature_from_spec(name: str) -> tuple[Any, ...]:
    profile = _PROFILES[name]
    target = profile["target"]
    component_specs = profile["components"]
    target_sig = _component_signature(*component_specs[target])
    distractors = tuple(sorted(
        (_component_signature(*spec) for i, spec in enumerate(component_specs) if i != target),
        key=repr,
    ))
    color_count = 1 + max(role for _, roles in component_specs for role in roles)
    return (*profile["dims"], color_count + 2, target_sig, distractors)


_PROFILE_SIGNATURES = {
    name: _profile_signature_from_spec(name) for name in PROFILE_NAMES
}
_PROFILE_MORPHOLOGY_SIGNATURES = {
    name: signature[2:] for name, signature in _PROFILE_SIGNATURES.items()
}
_CANONICAL_SIGNATURES = {
    _PROFILE_SIGNATURES[name] for name in CANONICAL_PROFILE_NAMES
}
# One lesson slot reuses these roomy canvases across unrelated morphologies so
# dimensions cannot serve as a target-shape label.  Canonical slots retain the
# exact published dimensions for profile support.
_FLEXIBLE_CANVAS_DIMS = ((12, 14), (14, 16))
_DIMENSION_TARGET_SHAPES = {
    tuple(profile["dims"]): _component_signature(
        *profile["components"][profile["target"]]
    )[0]
    for profile in _PROFILES.values()
}


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (0, 8) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] not in (0, 8)
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(sorted(cells))
    return out


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list grid"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged grid"]}
    if any(not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        errors.append("grid values must be integers in 0..9")
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-8 marker, found {len(markers)}")
        return {"errors": errors, "height": h, "width": w}
    marker = markers[0]
    components = _components(grid)
    cardinal = [
        index
        for index, cells in enumerate(components)
        if any(abs(r - marker[0]) + abs(c - marker[1]) == 1 for r, c in cells)
    ]
    if len(cardinal) != 1:
        errors.append(f"marker is cardinally adjacent to {len(cardinal)} components, expected 1")
        return {
            "errors": errors,
            "height": h,
            "width": w,
            "marker": marker,
            "components": components,
        }
    target_index = cardinal[0]
    target = components[target_index]
    adjacent_target_cells = [
        (r, c) for r, c in target
        if abs(r - marker[0]) + abs(c - marker[1]) == 1
    ]
    if len(adjacent_target_cells) != 1:
        errors.append(
            f"marker touches {len(adjacent_target_cells)} target cells, expected exactly 1"
        )
    rs = [r for r, _ in target]
    cs = [c for _, c in target]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    target_colors = sorted({grid[r][c] for r, c in target})
    diagonal_distractors = [
        index
        for index, cells in enumerate(components)
        if index != target_index
        and any(max(abs(r - marker[0]), abs(c - marker[1])) == 1 for r, c in cells)
    ]
    if adjacent_target_cells:
        ar, ac = adjacent_target_cells[0]
        dr, dc = marker[0] - ar, marker[1] - ac
        marker_side = next(
            side for side, delta in _SIDE_TO_MARKER_DELTA.items() if delta == (dr, dc)
        )
    else:
        marker_side = None
    component_signatures = []
    for cells in components:
        rr0 = min(r for r, _ in cells)
        cc0 = min(c for _, c in cells)
        shape = [(r - rr0, c - cc0) for r, c in cells]
        component_signatures.append(
            (_d4_signature(shape), len({grid[r][c] for r, c in cells}))
        )
    target_sig = component_signatures[target_index]
    distractor_sigs = tuple(sorted(
        (sig for i, sig in enumerate(component_signatures) if i != target_index),
        key=repr,
    ))
    color_count = len({v for row in grid for v in row})
    morphology_signature = (color_count, target_sig, distractor_sigs)
    profile_signature = (h, w, *morphology_signature)
    scene_profile = next(
        (
            name
            for name, signature in _PROFILE_MORPHOLOGY_SIGNATURES.items()
            if signature == morphology_signature
        ),
        None,
    )
    object_colors = frozenset(v for row in grid for v in row if v not in (0, 8))
    palette_kind = next(
        (
            name
            for name, palette in _PALETTES.items()
            if frozenset(palette[: len(object_colors)]) == object_colors
        ),
        None,
    )
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "marker": marker,
        "components": components,
        "target_index": target_index,
        "target": target,
        "target_bbox": (r1, c1, r2, c2),
        "target_colors": target_colors,
        "target_size": len(target),
        "adjacent_target_cells": adjacent_target_cells,
        "diagonal_distractors": diagonal_distractors,
        "marker_side": marker_side,
        "layout_mode": "diagonal_decoy" if diagonal_distractors else "clear",
        "scene_profile": scene_profile,
        "palette_kind": palette_kind,
        "profile_signature": profile_signature,
        "morphology_signature": morphology_signature,
        "component_sizes": [len(cells) for cells in components],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or ambiguous scenes while accepting every official input."""
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    components = analysis["components"]
    if len(components) not in (3, 4):
        errors.append(f"expected 3 or 4 non-marker components, found {len(components)}")
    target = analysis["target"]
    if len(target) < 3:
        errors.append("target component must contain at least 3 cells")
    r1, c1, r2, c2 = analysis["target_bbox"]
    bbox_area = (r2 - r1 + 1) * (c2 - c1 + 1)
    if len(target) == bbox_area:
        errors.append("target component may not be a solid rectangle")
    if len(analysis["target_colors"]) not in (1, 2):
        errors.append("target component must use one or two colors")
    return errors


def _scheduled_choice(ctx, label: str, full_options: tuple[str, ...], defaults: tuple[str, ...]) -> str:
    options = full_options if label in ctx.overrides else defaults
    return ctx.draw_choice(label, options)


def _profile_defaults(sample_index: int, difficulty: Any) -> tuple[str, ...]:
    residue = sample_index % 4
    if residue == 0:
        return CANONICAL_PROFILE_NAMES[:4]
    if residue == 1:
        return ("canon_p5_multicolor_target",)
    if residue == 2:
        # This generalized middle-sized target has a deep concavity that can
        # hold the marker while touching exactly one target cell. Pinning it in
        # one residue makes every four-example sliding window refute a raw-bbox
        # crop without weakening the canonical anchors in the other slots.
        return ("general_t5",)
    return (*CANONICAL_PROFILE_NAMES, "general_branch6")


def _paint_component(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    colors: tuple[int, ...],
) -> None:
    ordered = sorted(cells)
    for index, (r, c) in enumerate(ordered):
        color_index = min(index * len(colors) // len(ordered), len(colors) - 1)
        grid[r][c] = colors[color_index]


def _translate(shape: Iterable[tuple[int, int]], top: int, left: int) -> list[tuple[int, int]]:
    return [(top + r, left + c) for r, c in shape]


def _in_bounds(cells: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _cardinal_neighbors(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))


def _can_place_component(
    cells: list[tuple[int, int]],
    *,
    occupied: set[tuple[int, int]],
    marker: tuple[int, int],
    h: int,
    w: int,
    clear_marker_diagonals: bool,
) -> bool:
    cellset = set(cells)
    if not _in_bounds(cells, h, w) or marker in cellset or cellset & occupied:
        return False
    for cell in cells:
        if any(neighbor in occupied for neighbor in _cardinal_neighbors(cell)):
            return False
        if abs(cell[0] - marker[0]) + abs(cell[1] - marker[1]) == 1:
            return False
        if clear_marker_diagonals and max(abs(cell[0] - marker[0]), abs(cell[1] - marker[1])) <= 1:
            return False
    return True


def _place_target(
    rng,
    shape: tuple[tuple[int, int], ...],
    marker_side: str,
    h: int,
    w: int,
    *,
    require_bbox_intruder: bool,
) -> tuple[list[tuple[int, int]], tuple[int, int]] | None:
    marker_delta = _SIDE_TO_MARKER_DELTA[marker_side]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    placements = [
        (top, left)
        for top in range(1, h - sh)
        for left in range(1, w - sw)
    ]
    rng.shuffle(placements)
    for top, left in placements:
        cells = _translate(shape, top, left)
        cellset = set(cells)
        anchors = []
        for r, c in cells:
            marker = (r + marker_delta[0], c + marker_delta[1])
            if not (0 <= marker[0] < h and 0 <= marker[1] < w) or marker in cellset:
                continue
            if require_bbox_intruder and not (
                top <= marker[0] < top + sh and left <= marker[1] < left + sw
            ):
                continue
            touches = [cell for cell in cells if abs(cell[0] - marker[0]) + abs(cell[1] - marker[1]) == 1]
            if len(touches) == 1:
                anchors.append(marker)
        if anchors:
            return cells, rng.choice(anchors)
    return None


def _place_diagonal_decoy(
    rng,
    shape: tuple[tuple[int, int], ...],
    *,
    marker: tuple[int, int],
    target_cells: set[tuple[int, int]],
    marker_side: str,
    occupied: set[tuple[int, int]],
    h: int,
    w: int,
) -> list[tuple[int, int]] | None:
    # The decoy sits diagonally on the side opposite the cardinal target, so it
    # is not edge-connected to the target but a Chebyshev selector still sees it.
    marker_delta = _SIDE_TO_MARKER_DELTA[marker_side]
    target_dir = (-marker_delta[0], -marker_delta[1])
    opposite = (-target_dir[0], -target_dir[1])
    perpendiculars = ((opposite[1], -opposite[0]), (-opposite[1], opposite[0]))
    anchors = [
        (marker[0] + opposite[0] + pr, marker[1] + opposite[1] + pc)
        for pr, pc in perpendiculars
    ]
    variants = [_transform(shape, index) for index in range(8)]
    rng.shuffle(anchors)
    rng.shuffle(variants)
    for anchor in anchors:
        for variant in variants:
            local = list(variant)
            rng.shuffle(local)
            for ar, ac in local:
                cells = [(anchor[0] + r - ar, anchor[1] + c - ac) for r, c in variant]
                if not _can_place_component(
                    cells,
                    occupied=occupied,
                    marker=marker,
                    h=h,
                    w=w,
                    clear_marker_diagonals=False,
                ):
                    continue
                if not any(max(abs(r - marker[0]), abs(c - marker[1])) == 1 for r, c in cells):
                    continue
                if any(any(neighbor in target_cells for neighbor in _cardinal_neighbors(cell)) for cell in cells):
                    continue
                return cells
    return None


def _place_random_component(
    rng,
    shape: tuple[tuple[int, int], ...],
    *,
    occupied: set[tuple[int, int]],
    marker: tuple[int, int],
    h: int,
    w: int,
    clear_marker_diagonals: bool,
) -> list[tuple[int, int]] | None:
    variants = [_transform(shape, index) for index in range(8)]
    candidates = []
    for variant in variants:
        sh = max(r for r, _ in variant) + 1
        sw = max(c for _, c in variant) + 1
        for top in range(h - sh + 1):
            for left in range(w - sw + 1):
                candidates.append(_translate(variant, top, left))
    rng.shuffle(candidates)
    for cells in candidates:
        if _can_place_component(
            cells,
            occupied=occupied,
            marker=marker,
            h=h,
            w=w,
            clear_marker_diagonals=clear_marker_diagonals,
        ):
            return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = _scheduled_choice(
        ctx,
        "scene_profile",
        PROFILE_NAMES,
        _profile_defaults(sample_index, difficulty),
    )
    palette_kind = _scheduled_choice(ctx, "palette_kind", PALETTE_KINDS, PALETTE_KINDS)
    marker_side = _scheduled_choice(ctx, "marker_side", MARKER_SIDES, MARKER_SIDES)
    default_layout = ("diagonal_decoy",) if sample_index % 2 == 0 else ("clear",)
    layout_mode = _scheduled_choice(ctx, "layout_mode", LAYOUT_MODES, default_layout)

    profile = _PROFILES[profile_name]
    canonical_dims = profile["dims"]
    component_specs = profile["components"]
    target_index = profile["target"]
    needed_colors = 1 + max(role for _, roles in component_specs for role in roles)
    base_palette = _PALETTES[palette_kind][:needed_colors]
    # Component roles must not leak through numeric color rank.  Rotating the
    # role-to-color assignment by sample index guarantees that every ordinary
    # four-example window contains a target whose colors are not lexicographically
    # smallest, while preserving the requested palette set exactly.
    role_offset = sample_index % needed_colors
    palette = base_palette[role_offset:] + base_palette[:role_offset]
    rng = ctx.draw_rng(f"layout:{difficulty or 'none'}")
    if sample_index % 4 == 3:
        canvas_options = tuple(
            dims for dims in _FLEXIBLE_CANVAS_DIMS if dims != canonical_dims
        )
        h, w = rng.choice(canvas_options)
    else:
        h, w = canonical_dims

    # Residue 2 uses general_t5 and places the marker inside a target concavity.
    # Every four-example sliding window contains that residue, refuting the
    # tempting raw-bounding-box crop. Explicit profile overrides remain lawful.
    require_bbox_intruder = (
        sample_index % 4 == 2 and profile_name == "general_t5"
    )

    for attempt in range(80):
        grid = full_grid(h, w, 0)
        orientation = rng.randrange(8)
        target_shape, target_roles = component_specs[target_index]
        transformed_target = _transform(target_shape, orientation)
        placed = _place_target(
            rng,
            transformed_target,
            marker_side,
            h,
            w,
            require_bbox_intruder=require_bbox_intruder,
        )
        if placed is None:
            continue
        target_cells, marker = placed
        occupied = set(target_cells)
        placed_components: dict[int, list[tuple[int, int]]] = {target_index: target_cells}

        distractor_indexes = [i for i in range(len(component_specs)) if i != target_index]
        if layout_mode == "diagonal_decoy":
            decoy_index = distractor_indexes[0]
            decoy_shape, _ = component_specs[decoy_index]
            decoy_cells = _place_diagonal_decoy(
                rng,
                decoy_shape,
                marker=marker,
                target_cells=set(target_cells),
                marker_side=marker_side,
                occupied=occupied,
                h=h,
                w=w,
            )
            if decoy_cells is None:
                continue
            placed_components[decoy_index] = decoy_cells
            occupied.update(decoy_cells)
            remaining = distractor_indexes[1:]
        else:
            remaining = distractor_indexes

        failed = False
        for index in remaining:
            shape, _ = component_specs[index]
            cells = _place_random_component(
                rng,
                shape,
                occupied=occupied,
                marker=marker,
                h=h,
                w=w,
                clear_marker_diagonals=True,
            )
            if cells is None:
                failed = True
                break
            placed_components[index] = cells
            occupied.update(cells)
        if failed:
            continue

        for index, (shape, roles) in enumerate(component_specs):
            colors = tuple(palette[role] for role in roles)
            _paint_component(grid, placed_components[index], colors)
        grid[marker[0]][marker[1]] = 8
        findings = self_check(grid, difficulty=difficulty)
        if not findings:
            return grid
    raise ValueError(
        f"could not place profile={profile_name} side={marker_side} layout={layout_mode}"
    )


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    return {
        "scene_profile": analysis["scene_profile"],
        "palette_kind": analysis["palette_kind"],
        "marker_side": analysis["marker_side"],
        "layout_mode": analysis["layout_mode"],
    }


def canonical_profile_signature(grid) -> tuple[Any, ...] | None:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    return analysis["profile_signature"]


def strict_canonical_like(grid) -> list[str]:
    signature = canonical_profile_signature(grid)
    if signature is None:
        return ["grid is not a lawful key-adjacent-component scene"]
    if signature not in _CANONICAL_SIGNATURES:
        return ["linked dimensions/palette/target/distractor morphology is not canonical"]
    return []


def _crop_target(grid: list[list[int]], analysis: dict[str, Any]) -> list[list[int]]:
    """Render only the selected component into its tight bounding box."""
    r1, c1, r2, c2 = analysis["target_bbox"]
    target = set(analysis["target"])
    return [
        [grid[r][c] if (r, c) in target else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def _raw_bbox_crop(grid: list[list[int]], analysis: dict[str, Any]) -> list[list[int]]:
    """Incorrect shortcut: crop the raw scene, including bbox intruders."""
    r1, c1, r2, c2 = analysis["target_bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _upscale2(grid: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(2)]
        out.extend([expanded[:], expanded[:]])
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return _upscale2(_crop_target(grid, analysis))


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    target_index = analysis["target_index"]
    sizes = analysis["component_sizes"]
    target_size = sizes[target_index]
    target_colors = set(analysis["target_colors"])
    distractor_colors = {
        grid[r][c]
        for index, cells in enumerate(analysis["components"])
        if index != target_index
        for r, c in cells
    }
    r1, c1, r2, c2 = analysis["target_bbox"]
    bbox_area = (r2 - r1 + 1) * (c2 - c1 + 1)
    target_cells = set(analysis["target"])
    bbox_intruders = [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if (r, c) not in target_cells and grid[r][c] != 0
    ]
    return {
        **observe_overrides(grid),
        "canonical_profile": analysis["profile_signature"] in _CANONICAL_SIGNATURES,
        "multicolor_target": len(target_colors) > 1,
        "target_color_reused": bool(target_colors & distractor_colors),
        "diagonal_decoy": bool(analysis["diagonal_distractors"]),
        "sparse_target": target_size < bbox_area,
        "bbox_intruder": bool(bbox_intruders),
        "bbox_intruder_cells": bbox_intruders,
        "target_middle_sized": min(sizes) < target_size < max(sizes),
        "target_shape": _d4_signature(
            [(r - r1, c - c1) for r, c in analysis["target"]]
        ),
    }


def _valid_obs(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


def _component_crop(grid, cells: list[tuple[int, int]]) -> list[list[int]]:
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _isolated_component_crop(grid, cells: list[tuple[int, int]]) -> list[list[int]]:
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    selected = set(cells)
    return [
        [grid[r][c] if (r, c) in selected else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def _rival_diagonal_preferred(grid):
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    if a["diagonal_distractors"]:
        cells = a["components"][a["diagonal_distractors"][0]]
        return _upscale2(_component_crop(grid, cells))
    return rule_mirror(grid)


def _rival_same_color_component(grid):
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    ar, ac = a["adjacent_target_cells"][0]
    color = grid[ar][ac]
    cells = [cell for cell in a["target"] if grid[cell[0]][cell[1]] == color]
    # Keep only the same-color connected region containing the adjacent cell.
    seen = {(ar, ac)}
    stack = [(ar, ac)]
    while stack:
        r, c = stack.pop()
        for nr, nc in _cardinal_neighbors((r, c)):
            if (nr, nc) in cells and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return _upscale2(_component_crop(grid, sorted(seen)))


def _rival_global_color(grid):
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    ar, ac = a["adjacent_target_cells"][0]
    color = grid[ar][ac]
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    return _upscale2(_component_crop(grid, cells))


def _rival_largest(grid):
    a = _analyze(grid)
    cells = max(a["components"], key=len)
    return _upscale2(_component_crop(grid, cells))


def _rival_smallest(grid):
    a = _analyze(grid)
    cells = min(a["components"], key=len)
    return _upscale2(_component_crop(grid, cells))


def _rival_bbox_fill(grid):
    a = _analyze(grid)
    crop = _crop_target(grid, a)
    color = next(value for row in crop for value in row if value != 0)
    return _upscale2([[color if value == 0 else value for value in row] for row in crop])


def _rival_no_upscale(grid):
    a = _analyze(grid)
    return _crop_target(grid, a)


def _rival_raw_bbox_crop(grid):
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    return _upscale2(_raw_bbox_crop(grid, a))


def _rival_fixed_l4(grid):
    a = _analyze(grid)
    color = grid[a["target"][0][0]][a["target"][0][1]]
    shape = [list(row) for row in ((color, 0), (color, 0), (color, color))]
    return _upscale2(shape)


def _rival_palette_rank_selector(grid):
    """Ignore the marker and select by numeric palette rank instead."""
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    components = a["components"]
    selected_index = min(
        range(len(components)),
        key=lambda index: (
            min(grid[r][c] for r, c in components[index]),
            -len({grid[r][c] for r, c in components[index]}),
            min(components[index]),
        ),
    )
    return _upscale2(_isolated_component_crop(grid, components[selected_index]))


def _rival_dimension_shape_lookup(grid):
    """Ignore the marker and look up a target morphology from canvas size."""
    a = _analyze(grid)
    if a.get("errors"):
        raise ValueError("; ".join(a["errors"]))
    expected_shape = _DIMENSION_TARGET_SHAPES.get((a["height"], a["width"]))
    if expected_shape is None:
        return [[0]]
    for cells in a["components"]:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        shape = _d4_signature([(r - r0, c - c0) for r, c in cells])
        if shape == expected_shape:
            return _upscale2(_isolated_component_crop(grid, cells))
    return [[0]]


SEMANTIC_RIVALS = {
    "diagonal_preferred": _rival_diagonal_preferred,
    "same_color_only": _rival_same_color_component,
    "global_color_crop": _rival_global_color,
    "largest_component": _rival_largest,
    "smallest_component": _rival_smallest,
    "bbox_fill": _rival_bbox_fill,
    "no_upscale": _rival_no_upscale,
    "raw_bbox_crop": _rival_raw_bbox_crop,
    "fixed_l4": _rival_fixed_l4,
    "palette_rank_selector": _rival_palette_rank_selector,
    "dimension_shape_lookup": _rival_dimension_shape_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "diagonal_decoy": lambda grid: _valid_obs(grid, lambda obs: obs["diagonal_decoy"]),
    "multicolor_target": lambda grid: _valid_obs(grid, lambda obs: obs["multicolor_target"]),
    "disconnected_target_color_reuse": lambda grid: _valid_obs(grid, lambda obs: obs["target_color_reused"]),
    "target_middle_sized": lambda grid: _valid_obs(grid, lambda obs: obs["target_middle_sized"]),
    "sparse_target": lambda grid: _valid_obs(grid, lambda obs: obs["sparse_target"]),
    "bbox_intruder": lambda grid: _valid_obs(grid, lambda obs: obs["bbox_intruder"]),
    "non_l4_target": lambda grid: _valid_obs(grid, lambda obs: obs["target_shape"] != _d4_signature(L4)),
    "target_not_palette_rank_selected": lambda grid: (
        not self_check(grid)
        and _rival_palette_rank_selector(grid) != rule_mirror(grid)
    ),
    "target_not_dimension_shape_selected": lambda grid: (
        not self_check(grid)
        and _rival_dimension_shape_lookup(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "diagonal_decoy": ["diagonal_preferred"],
    "multicolor_target": ["same_color_only"],
    "disconnected_target_color_reuse": ["global_color_crop"],
    "target_middle_sized": ["largest_component", "smallest_component"],
    "sparse_target": ["bbox_fill", "no_upscale"],
    "bbox_intruder": ["raw_bbox_crop"],
    "non_l4_target": ["fixed_l4"],
    "target_not_palette_rank_selected": ["palette_rank_selector"],
    "target_not_dimension_shape_selected": ["dimension_shape_lookup"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        grid = pair.get("input") if isinstance(pair, dict) else None
        findings = self_check(grid)
        if findings:
            reasons.append(f"pair {index} input is unlawful: {'; '.join(findings)}")
            continue
        expected = rule_mirror(grid)
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output disagrees with the cardinal-component rule")
    if reasons:
        return reasons
    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos do not refute competitor {name!r}, which changes the query answer"
                )
    return reasons


def _draw_from_degenerate(name: str) -> list[list[int]]:
    """Focused invalid fixtures for mutation tests; never part of AXES.valid."""
    grid = full_grid(9, 12, 0)
    if name == "no_key":
        grid[2][2] = grid[2][3] = grid[3][2] = 4
    elif name == "key_isolated":
        grid[2][2] = grid[2][3] = grid[3][2] = 4
        grid[6][8] = 8
    elif name == "key_adj_multiple":
        grid[4][4] = 4
        grid[4][6] = 6
        grid[4][5] = 8
    elif name == "solid_target":
        grid[4][4] = grid[4][5] = grid[5][4] = grid[5][5] = 4
        grid[3][4] = 8
        grid[1][1] = grid[1][2] = grid[2][1] = 5
        grid[7][8] = grid[7][9] = grid[6][9] = 6
    else:
        raise ValueError(f"unknown degenerate fixture {name!r}")
    return grid
