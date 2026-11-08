"""Generator for ARC task 896d5239.

Color-3 markers form one or more V-shaped chevrons on a noisy binary
background.  Each chevron has one apex and marker subsets on both 45-degree
arms; the oracle fills the entire supported triangular wedge with color 8
while preserving the green markers and all cells outside the wedge.

The four unique canonical inputs couple canvas dimensions with complete
multisets of chevron morphologies.  Default generation uses a deterministic
three-slot teaching schedule: two broad lawful anchor profiles jointly cover
all orientations and hard semantic branches, followed by one complete
canonical profile.  Every cyclic three-example lesson therefore refutes the
declared incomplete-rule competitors while retaining a one-third exact
canonical rate.  Binary clutter is regenerated independently so marker
geometry, not fixed background pixels or marker count alone, determines the
answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3977ec54e4a0"
TASK_ID = GENERATOR_ID
VERSION = "4.1.1"
RULE_HASH = "780d64b3096e"

SUMMARY = (
    "A noisy {0,1} grid contains 1..4 disconnected color-3 chevrons.  Each "
    "chevron is an apex plus at least one marker on each of its two diagonal "
    "arms; interior arm markers may be absent and the two arms may be "
    "asymmetric.  For every supported chevron, fill its solid triangular "
    "wedge with color 8, preserving all color-3 markers and all outside "
    "background cells."
)

INVARIANTS = [
    "palette is exactly a noisy binary background {0,1} plus marker color 3",
    "every near-connected marker component decodes as one unambiguous chevron",
    "each chevron has one apex, at least one marker on each arm, and far-depth support",
    "1..4 chevrons are pairwise separated under the oracle's near-marker relation",
    "canvas dimensions stay within 12..22 by 12..22",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band 12..15 easy, 14..18 medium, 17..22 hard; canonical every third sample",
        "valid": "12..22",
    },
    "grid_w": {
        "type": "int",
        "default": "band 12..15 easy, 14..19 medium, 17..22 hard; canonical every third sample",
        "valid": "12..22",
    },
    "chevron_count": {
        "type": "int",
        "default": "teaching anchors use at least 2; canonical every third sample",
        "valid": "1..4",
    },
    "max_depth": {
        "type": "int",
        "default": "teaching anchors include depth 3; canonical every third sample",
        "valid": "1..3",
    },
    "asymmetric_arms": {
        "type": "bool",
        "default": "teaching anchors include exact mask asymmetry; canonical every third sample",
        "valid": "true|false",
    },
}

_ORIENTATIONS = (0, 1, 2, 3)  # down, up, right, left
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("orientation_01", "orientation_23", "canonical")
_H_RANGE = (12, 22)
_W_RANGE = (12, 22)
_COUNT_RANGE = (1, 4)
_DEPTH_RANGE = (1, 3)
_ALLOWED_OVERRIDES = frozenset(AXES)

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"asymmetric_arms": True, "max_depth": 1},
]


@dataclass(frozen=True, order=True)
class Chevron:
    orientation: int
    depth: int
    left_mask: tuple[bool, ...]
    right_mask: tuple[bool, ...]
    apex: tuple[int, int]

    @property
    def descriptor(self) -> tuple[int, int, int, int]:
        return (
            self.orientation,
            self.depth,
            _mask_bits(self.left_mask),
            _mask_bits(self.right_mask),
        )

    @property
    def asymmetric(self) -> bool:
        return self.left_mask != self.right_mask

    @property
    def markers(self) -> frozenset[tuple[int, int]]:
        ar, ac = self.apex
        cells = {self.apex}
        for side, mask in enumerate((self.left_mask, self.right_mask)):
            for k, present in enumerate(mask, 1):
                if present:
                    cells.add(_arm_cell(self.orientation, ar, ac, k, side))
        return frozenset(cells)


def _mask_bits(mask: Iterable[bool]) -> int:
    bits = 0
    for index, present in enumerate(mask):
        if present:
            bits |= 1 << index
    return bits


def _arm_cell(orientation: int, ar: int, ac: int, k: int, side: int) -> tuple[int, int]:
    if orientation == 0:  # down
        return ar + k, ac + (-k if side == 0 else k)
    if orientation == 1:  # up
        return ar - k, ac + (-k if side == 0 else k)
    if orientation == 2:  # right
        return ar + (-k if side == 0 else k), ac + k
    return ar + (-k if side == 0 else k), ac - k


def _near(a: tuple[int, int], b: tuple[int, int]) -> bool:
    dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dr, dc) <= 2 and (dr == dc or dr == 0 or dc == 0)


def _marker_groups(markers: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Graph components under the exact relation used by the Racket rule."""
    remaining = set(markers)
    groups: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        group = []
        while stack:
            current = stack.pop()
            group.append(current)
            neighbors = {cell for cell in remaining if _near(current, cell)}
            remaining.difference_update(neighbors)
            stack.extend(neighbors)
        groups.append(sorted(group))
    return groups


def _decode_group(group: Iterable[tuple[int, int]]) -> Chevron | None:
    points = frozenset(group)
    if len(points) < 3:
        return None
    if len(_marker_groups(points)) != 1:
        return None
    span = max(
        max(r for r, _ in points) - min(r for r, _ in points),
        max(c for _, c in points) - min(c for _, c in points),
    )
    candidates: list[Chevron] = []
    for apex in points:
        ar, ac = apex
        for orientation in _ORIENTATIONS:
            for depth in range(1, span + 1):
                left = tuple(
                    _arm_cell(orientation, ar, ac, k, 0) in points
                    for k in range(1, depth + 1)
                )
                right = tuple(
                    _arm_cell(orientation, ar, ac, k, 1) in points
                    for k in range(1, depth + 1)
                )
                if not any(left) or not any(right):
                    continue
                if not (left[-1] or right[-1]):
                    continue
                support = {apex}
                for side, mask in enumerate((left, right)):
                    for k, present in enumerate(mask, 1):
                        if present:
                            support.add(_arm_cell(orientation, ar, ac, k, side))
                if support != points:
                    continue
                candidates.append(Chevron(orientation, depth, left, right, apex))
    unique = {candidate for candidate in candidates}
    return next(iter(unique)) if len(unique) == 1 else None


def _decode_grid(grid: list[list[int]]) -> tuple[list[Chevron], list[str]]:
    errors: list[str] = []
    if not grid or not grid[0]:
        return [], ["grid is empty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return [], ["grid is not rectangular"]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    chevrons: list[Chevron] = []
    for index, group in enumerate(_marker_groups(markers)):
        decoded = _decode_group(group)
        if decoded is None:
            errors.append(
                f"marker component {index} is not one unambiguous supported chevron"
            )
        else:
            chevrons.append(decoded)
    return chevrons, errors


def canonical_profile_signature(grid: list[list[int]]):
    """Complete linked profile, quotienting only marker translation/background."""
    chevrons, errors = _decode_grid(grid)
    if errors:
        return None
    return (
        len(grid),
        len(grid[0]),
        tuple(sorted(chevron.descriptor for chevron in chevrons)),
    )


# Exact marker coordinates from the four unique canonical inputs.  The focused
# regression test derives signatures from every canonical row and proves these
# profiles are complete; duplicate source rows collapse to the same four values.
_CANONICAL_PROFILES = (
    (
        15,
        12,
        ((12, 4), (14, 2), (14, 6),
         (2, 6), (3, 5), (4, 4), (5, 3), (6, 4), (7, 5), (8, 6)),
    ),
    (
        13,
        12,
        ((8, 5), (9, 4), (9, 6), (10, 3), (11, 2),
         (2, 4), (3, 3), (3, 5), (4, 2), (4, 6)),
    ),
    (
        15,
        16,
        ((8, 8), (9, 7), (10, 6), (11, 5), (12, 6), (14, 8),
         (8, 12), (9, 13), (9, 15), (10, 14),
         (2, 5), (3, 4), (3, 6), (4, 3)),
    ),
    (
        15,
        18,
        ((9, 9), (10, 8), (11, 7), (12, 6), (13, 7),
         (9, 1), (10, 2), (11, 3), (12, 2),
         (3, 13), (3, 17), (4, 14), (4, 16), (5, 15),
         (1, 3), (3, 1), (3, 5)),
    ),
)


def _profile_grid(profile) -> list[list[int]]:
    h, w, markers = profile
    grid = full_grid(h, w, 0)
    for r, c in markers:
        grid[r][c] = 3
    return grid


_CANONICAL_SIGNATURES = frozenset(
    canonical_profile_signature(_profile_grid(profile))
    for profile in _CANONICAL_PROFILES
)
assert None not in _CANONICAL_SIGNATURES


def _draw_axis_int(ctx, overrides, label, global_bounds, default_bounds):
    lo, hi = global_bounds if overrides.get(label) is not None else default_bounds
    return ctx.draw_int(label, lo, hi)


def _record_bool(ctx, overrides, label: str, default: bool) -> bool:
    if overrides.get(label) is not None:
        return bool(ctx.draw_choice(label, (False, True)))
    return bool(ctx.draw_choice(label, (default,)))


def _binary_background(h: int, w: int, rng) -> list[list[int]]:
    one_probability = rng.uniform(0.38, 0.62)
    grid = [
        [1 if rng.random() < one_probability else 0 for _ in range(w)]
        for _ in range(h)
    ]
    # Structural checker requires both nuisance colors.  This repair is local
    # to the background and never touches marker geometry.
    grid[0][0] = 0
    grid[0][1] = 1
    return grid


def _legal_masks(depth: int) -> list[tuple[bool, ...]]:
    """Nonempty arm masks connected to the apex under the oracle relation."""
    masks = []
    for bits in range(1, 1 << depth):
        selected = [k for k in range(1, depth + 1) if bits & (1 << (k - 1))]
        chain = [0, *selected]
        if all(b - a <= 2 for a, b in zip(chain, chain[1:])):
            masks.append(tuple(bool(bits & (1 << i)) for i in range(depth)))
    return masks


def _make_masks(depth: int, asymmetric: bool, rng) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    if asymmetric and depth < 2:
        raise ValueError("asymmetric_arms=true requires max_depth >= 2")
    legal = _legal_masks(depth)
    pairs = [
        (left, right)
        for left in legal
        for right in legal
        if (left[-1] or right[-1])
        and ((left != right) == asymmetric)
    ]
    if not pairs:
        raise ValueError("no connected arm masks satisfy the requested geometry")
    return rng.choice(pairs)


def _candidate_apices(h: int, w: int, descriptor, rng):
    orientation, depth, left_mask, right_mask = descriptor
    candidates = []
    for ar in range(h):
        for ac in range(w):
            cells = {(ar, ac)}
            valid = True
            for side, mask in enumerate((left_mask, right_mask)):
                for k, present in enumerate(mask, 1):
                    if not present:
                        continue
                    r, c = _arm_cell(orientation, ar, ac, k, side)
                    if not (0 <= r < h and 0 <= c < w):
                        valid = False
                        break
                    cells.add((r, c))
                if not valid:
                    break
            if valid:
                candidates.append((ar, ac, frozenset(cells)))
    rng.shuffle(candidates)
    return candidates


def _place_descriptors(
    h: int,
    w: int,
    descriptors,
    rng,
    *,
    accept_complete=None,
) -> list[Chevron]:
    candidate_lists = [
        _candidate_apices(h, w, descriptor, rng)
        for descriptor in descriptors
    ]
    order = sorted(range(len(descriptors)), key=lambda i: len(candidate_lists[i]))
    placed: list[Chevron | None] = [None] * len(descriptors)
    occupied: set[tuple[int, int]] = set()

    def separated(cells) -> bool:
        return all(
            not _near(cell, existing)
            for cell in cells
            for existing in occupied
        )

    def search(position: int) -> bool:
        if position == len(order):
            completed = [item for item in placed if item is not None]
            return accept_complete is None or bool(accept_complete(completed))
        index = order[position]
        orientation, depth, left_mask, right_mask = descriptors[index]
        for ar, ac, cells in candidate_lists[index]:
            if not separated(cells):
                continue
            chevron = Chevron(
                orientation,
                depth,
                tuple(left_mask),
                tuple(right_mask),
                (ar, ac),
            )
            # Reject rare geometries that decode differently from construction.
            if _decode_group(cells) != chevron:
                continue
            placed[index] = chevron
            occupied.update(cells)
            if search(position + 1):
                return True
            occupied.difference_update(cells)
            placed[index] = None
        return False

    if not search(0):
        raise ValueError(
            "requested chevron_count/max_depth cannot be placed on the requested canvas"
        )
    return [item for item in placed if item is not None]


def _general_chevrons(h: int, w: int, count: int, max_depth: int, asymmetric: bool, rng):
    descriptors = []
    for index in range(count):
        depth = max_depth if index == 0 else rng.randint(1, max_depth)
        wants_asymmetry = asymmetric and index == 0
        left, right = _make_masks(depth, wants_asymmetry, rng)
        descriptors.append((rng.choice(_ORIENTATIONS), depth, left, right))
    return _place_descriptors(h, w, descriptors, rng)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the declared three-slot lesson profile.

    The schedule intentionally depends only on the lesson position.  A seed
    still controls all within-profile variation, but no seed can accidentally
    erase one of the three pedagogical obligations from a cyclic window.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _wedge_cells(chevron: Chevron, *, depth: int | None = None) -> set[tuple[int, int]]:
    """Return the solid supported wedge, independent of background texture."""
    d = chevron.depth if depth is None else depth
    ar, ac = chevron.apex
    cells: set[tuple[int, int]] = set()
    for offset in range(d + 1):
        if chevron.orientation == 0:
            r = ar + offset
            cells.update((r, c) for c in range(ac - offset, ac + offset + 1))
        elif chevron.orientation == 1:
            r = ar - offset
            cells.update((r, c) for c in range(ac - offset, ac + offset + 1))
        elif chevron.orientation == 2:
            c = ac + offset
            cells.update((r, c) for r in range(ar - offset, ar + offset + 1))
        else:
            c = ac - offset
            cells.update((r, c) for r in range(ar - offset, ar + offset + 1))
    return cells


def _teaching_support_is_exclusive(chevrons: list[Chevron]) -> bool:
    """Ensure each required anchor changes pixels no other wedge can explain.

    The first two descriptors are the scheduled orientations.  Merely placing
    their marker components separately is insufficient: one wedge can fully
    cover the other's painted cells, allowing an orientation-omission rival to
    survive.  The first (depth-three asymmetric) anchor additionally needs an
    exclusive outer-shell pixel so the depth-capped rival is visibly refuted.
    """
    if len(chevrons) < 2:
        return False
    markers = set().union(*(item.markers for item in chevrons))
    wedges = [_wedge_cells(item) for item in chevrons]
    for index in (0, 1):
        covered_elsewhere = set().union(
            *(wedge for other, wedge in enumerate(wedges) if other != index)
        )
        exclusive_paint = wedges[index] - markers - covered_elsewhere
        if not exclusive_paint:
            return False

    first_outer_shell = _wedge_cells(chevrons[0]) - _wedge_cells(
        chevrons[0], depth=2
    )
    covered_elsewhere = set().union(*wedges[1:])
    return bool(first_outer_shell - markers - covered_elsewhere)


def _teaching_chevrons(
    h: int,
    w: int,
    count: int,
    required_orientations: tuple[int, int],
    rng,
) -> list[Chevron]:
    """Build one anchor with depth, asymmetry, sparsity, and multiplicity."""
    if count < 2:
        raise ValueError("a teaching anchor requires at least two chevrons")

    # The first descriptor jointly refutes depth-capped, symmetric-only, and
    # complete-arm-only rivals.  Exact inequality at depth three guarantees at
    # least one absent interior marker without relying on marker counts.
    first_left, first_right = _make_masks(3, True, rng)
    descriptors = [
        (required_orientations[0], 3, first_left, first_right),
    ]

    second_depth = rng.randint(1, 3)
    second_left, second_right = _make_masks(second_depth, False, rng)
    descriptors.append(
        (required_orientations[1], second_depth, second_left, second_right)
    )

    for _ in range(2, count):
        depth = rng.randint(1, 3)
        left, right = _make_masks(depth, False, rng)
        descriptors.append((rng.choice(_ORIENTATIONS), depth, left, right))
    return _place_descriptors(
        h,
        w,
        descriptors,
        rng,
        accept_complete=_teaching_support_is_exclusive,
    )


def _difficulty_config(difficulty):
    if difficulty == "easy":
        return (12, 15), (12, 15), (1, 2), (1, 2), 0.20
    if difficulty == "hard":
        return (17, 22), (17, 22), (3, 4), (2, 3), 0.80
    return (14, 18), (14, 19), (2, 3), (2, 3), 0.55


def _validate_override_keys(overrides) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    h_bounds, w_bounds, count_bounds, depth_bounds, asymmetry_p = (
        _difficulty_config(difficulty)
    )

    # Explicit controls bypass the lesson schedule.  This keeps every declared
    # axis exact and independently testable instead of silently replacing a
    # caller's requested geometry with a scheduled profile.
    if overrides:
        h = _draw_axis_int(ctx, overrides, "grid_h", _H_RANGE, h_bounds)
        w = _draw_axis_int(ctx, overrides, "grid_w", _W_RANGE, w_bounds)
        count = _draw_axis_int(
            ctx, overrides, "chevron_count", _COUNT_RANGE, count_bounds
        )
        if (
            overrides.get("asymmetric_arms") is True
            and overrides.get("max_depth") == 1
        ):
            raise ValueError(
                "incompatible overrides: asymmetric_arms=true requires max_depth >= 2"
            )
        effective_depth_bounds = depth_bounds
        if overrides.get("asymmetric_arms") is True and "max_depth" not in overrides:
            effective_depth_bounds = (max(2, depth_bounds[0]), depth_bounds[1])
        max_depth = _draw_axis_int(
            ctx, overrides, "max_depth", _DEPTH_RANGE, effective_depth_bounds
        )
        asymmetric = _record_bool(
            ctx,
            overrides,
            "asymmetric_arms",
            max_depth >= 2 and rng.random() < asymmetry_p,
        )
        chevrons = _general_chevrons(h, w, count, max_depth, asymmetric, rng)
        grid = _binary_background(h, w, rng)
        for chevron in chevrons:
            for r, c in chevron.markers:
                grid[r][c] = 3
        return grid

    profile_name = schedule_profile(seed, sample_index, difficulty)
    if profile_name == "canonical":
        profile = rng.choice(_CANONICAL_PROFILES)
        h, w, marker_cells = profile
        signature = canonical_profile_signature(_profile_grid(profile))
        assert signature is not None
        descriptors = signature[2]
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("chevron_count", len(descriptors), len(descriptors))
        max_depth = max(descriptor[1] for descriptor in descriptors)
        ctx.draw_int("max_depth", max_depth, max_depth)
        asymmetry = any(
            descriptor[2] != descriptor[3]
            for descriptor in descriptors
        )
        ctx.draw_choice("asymmetric_arms", (asymmetry,))
        grid = _binary_background(h, w, rng)
        for r, c in marker_cells:
            grid[r][c] = 3
        return grid

    h = ctx.draw_int("grid_h", *h_bounds)
    w = ctx.draw_int("grid_w", *w_bounds)
    # Easy previously allowed one component, but a teaching anchor must expose
    # the multiple-component branch.  This remains inside the declared 1..4
    # global grammar and does not affect exact override generation.
    anchor_count_bounds = (max(2, count_bounds[0]), count_bounds[1])
    count = ctx.draw_int("chevron_count", *anchor_count_bounds)
    ctx.draw_int("max_depth", 3, 3)
    ctx.draw_choice("asymmetric_arms", (True,))
    required = (0, 1) if profile_name == "orientation_01" else (2, 3)
    chevrons = _teaching_chevrons(h, w, count, required, rng)
    grid = _binary_background(h, w, rng)
    for chevron in chevrons:
        for r, c in chevron.markers:
            grid[r][c] = 3
    return grid


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid alone."""
    chevrons, errors = _decode_grid(grid)
    if errors:
        return {
            "grid_h": len(grid),
            "grid_w": len(grid[0]) if grid else 0,
        }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "chevron_count": len(chevrons),
        "max_depth": max(chevron.depth for chevron in chevrons),
        "asymmetric_arms": any(chevron.asymmetric for chevron in chevrons),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the authority-level input grammar; reject shortcut impostors."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), width
    if not (_H_RANGE[0] <= h <= _H_RANGE[1]):
        errors.append(f"height {h} outside {_H_RANGE[0]}..{_H_RANGE[1]}")
    if not (_W_RANGE[0] <= w <= _W_RANGE[1]):
        errors.append(f"width {w} outside {_W_RANGE[0]}..{_W_RANGE[1]}")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 3}:
        errors.append(f"input palette {sorted(palette)} is not a subset of {{0,1,3}}")
    if 0 not in palette or 1 not in palette:
        errors.append("binary nuisance background must contain both colors 0 and 1")
    if 3 not in palette:
        errors.append("no color-3 marker found")

    chevrons, decode_errors = _decode_grid(grid)
    errors.extend(decode_errors)
    if not decode_errors:
        if not (_COUNT_RANGE[0] <= len(chevrons) <= _COUNT_RANGE[1]):
            errors.append(
                f"chevron count {len(chevrons)} outside {_COUNT_RANGE[0]}..{_COUNT_RANGE[1]}"
            )
        if chevrons:
            max_depth = max(chevron.depth for chevron in chevrons)
            if not (_DEPTH_RANGE[0] <= max_depth <= _DEPTH_RANGE[1]):
                errors.append(
                    f"maximum chevron depth {max_depth} outside {_DEPTH_RANGE[0]}..{_DEPTH_RANGE[1]}"
                )
    return errors

# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks
# ---------------------------------------------------------------------------

MIN_STRICT_FRAC = 0.20


def strict_canonical_like(grid) -> list[str]:
    """Recognize one complete linked official profile, not loose marginals."""
    signature = canonical_profile_signature(grid)
    if signature is None:
        return ["marker components do not decode as the canonical chevron grammar"]
    if signature not in _CANONICAL_SIGNATURES:
        return ["dimension plus complete oriented chevron-morphology multiset is not official"]
    palette = {value for row in grid for value in row}
    if palette != {0, 1, 3}:
        return ["canonical-like input palette must be exactly {0,1,3}"]
    return []


def _lawful_chevrons(grid) -> list[Chevron] | None:
    if self_check(grid):
        return None
    chevrons, errors = _decode_grid(grid)
    return None if errors else chevrons


def _has_orientation(grid, orientation: int) -> bool:
    chevrons = _lawful_chevrons(grid)
    return chevrons is not None and any(c.orientation == orientation for c in chevrons)


SEMANTIC_WITNESSES = {
    "down_chevron": lambda grid: _has_orientation(grid, 0),
    "up_chevron": lambda grid: _has_orientation(grid, 1),
    "right_chevron": lambda grid: _has_orientation(grid, 2),
    "left_chevron": lambda grid: _has_orientation(grid, 3),
    "depth_three": lambda grid: (
        (chevrons := _lawful_chevrons(grid)) is not None
        and any(c.depth == 3 for c in chevrons)
    ),
    "asymmetric_arms": lambda grid: (
        (chevrons := _lawful_chevrons(grid)) is not None
        and any(c.asymmetric for c in chevrons)
    ),
    "multiple_chevrons": lambda grid: (
        (chevrons := _lawful_chevrons(grid)) is not None
        and len(chevrons) >= 2
    ),
    "missing_interior_arm_markers": lambda grid: (
        (chevrons := _lawful_chevrons(grid)) is not None
        and any(
            (not all(c.left_mask)) or (not all(c.right_mask))
            for c in chevrons
        )
    ),
}

def _inside_at_depth(chevron: Chevron, depth: int, r: int, c: int) -> bool:
    ar, ac = chevron.apex
    d = depth
    if chevron.orientation == 0:
        return ar <= r <= ar + d and abs(c - ac) <= r - ar
    if chevron.orientation == 1:
        return ar - d <= r <= ar and abs(c - ac) <= ar - r
    if chevron.orientation == 2:
        return ac <= c <= ac + d and abs(r - ar) <= c - ac
    return ac - d <= c <= ac and abs(r - ar) <= ac - c


def _inside(chevron: Chevron, r: int, c: int) -> bool:
    return _inside_at_depth(chevron, chevron.depth, r, c)


def rule_mirror(grid):
    """Independent Python mirror for focused tests; Racket remains authority."""
    chevrons, errors = _decode_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 3 and any(_inside(chevron, r, c) for chevron in chevrons):
                out[r][c] = 8
    return out


def _rival_output(grid, keep, *, depth_cap: int | None = None):
    """Render a deliberately incomplete but executable pedagogical rival."""
    chevrons, errors = _decode_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    active = [
        (chevron, min(chevron.depth, depth_cap) if depth_cap else chevron.depth)
        for index, chevron in enumerate(sorted(chevrons))
        if keep(chevron, index)
    ]
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 3 and any(
                _inside_at_depth(chevron, depth, r, c)
                for chevron, depth in active
            ):
                out[r][c] = 8
    return out


def _omit_down(grid):
    return _rival_output(grid, lambda chevron, _index: chevron.orientation != 0)


def _omit_up(grid):
    return _rival_output(grid, lambda chevron, _index: chevron.orientation != 1)


def _omit_right(grid):
    return _rival_output(grid, lambda chevron, _index: chevron.orientation != 2)


def _omit_left(grid):
    return _rival_output(grid, lambda chevron, _index: chevron.orientation != 3)


def _cap_depth_two(grid):
    return _rival_output(grid, lambda _chevron, _index: True, depth_cap=2)


def _symmetric_only(grid):
    return _rival_output(grid, lambda chevron, _index: not chevron.asymmetric)


def _first_component_only(grid):
    return _rival_output(grid, lambda _chevron, index: index == 0)


def _complete_arms_only(grid):
    return _rival_output(
        grid,
        lambda chevron, _index: (
            all(chevron.left_mask) and all(chevron.right_mask)
        ),
    )


SEMANTIC_RIVALS = {
    "omit_down": _omit_down,
    "omit_up": _omit_up,
    "omit_right": _omit_right,
    "omit_left": _omit_left,
    "cap_depth_two": _cap_depth_two,
    "symmetric_only": _symmetric_only,
    "first_component_only": _first_component_only,
    "complete_arms_only": _complete_arms_only,
}

WITNESS_RIVALS = {
    "down_chevron": ["omit_down"],
    "up_chevron": ["omit_up"],
    "right_chevron": ["omit_right"],
    "left_chevron": ["omit_left"],
    "depth_three": ["cap_depth_two"],
    "asymmetric_arms": ["symmetric_only"],
    "multiple_chevrons": ["first_component_only"],
    "missing_interior_arm_markers": ["complete_arms_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}
