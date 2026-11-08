"""Generator for arc_additional_puzzle_bank_volume11:E74.

Every isolated red singleton is replaced by a green diagonal X. Larger red
components and unrelated colored objects are distractors and remain unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "98e38c175321"
VERSION = "2.0.0"
TASK_ID = "98e38c175321"
RULE_HASH = "d62cd253ef27"
SUMMARY = (
    "Turn each isolated red singleton into a green diagonal X while preserving "
    "larger red components and unrelated colored objects."
)

INVARIANTS = [
    "background is 0 and red controls are color 2",
    "each target is a 4-connected red component of size one",
    "larger red components are distractors outside every target X footprint",
    "one unrelated non-red object is preserved, including in occlusion cases",
    "generated layouts use one of the five complete canonical semantic profiles",
]

LAYOUT_PROFILES = ("p0", "p1", "p2", "p3", "p4")
PLACEMENT_MODES = ("interior", "edge", "corner", "occluded")
NONRED_COLORS = (4, 6, 7, 8, 9)

AXES = {
    "layout_profile": {
        "type": "enum",
        "default": "rng over five canonical linked profiles",
        "valid": "|".join(LAYOUT_PROFILES),
    },
    "placement_mode": {
        "type": "enum",
        "default": "rng over interior, edge, corner, and occluded",
        "valid": "|".join(PLACEMENT_MODES),
    },
    "nonred_color": {
        "type": "color",
        "default": "rng over canonical nuisance colors",
        "valid": "4|6|7|8|9",
    },
}


@dataclass(frozen=True)
class _Profile:
    h: int
    w: int
    seed_count: int
    red_shape: tuple[tuple[int, int], ...]
    other_shape: tuple[tuple[int, int], ...]


_NONE: tuple[tuple[int, int], ...] = ()
_DOMINO = ((0, 0), (0, 1))
_BAR3 = ((0, 0), (0, 1), (0, 2))
_ELL3 = ((0, 0), (1, 0), (1, 1))
_BAR4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))

# These are the five linked canonical profiles. Position, D4 orientation, and
# the unrelated object's color are nuisance factors; dimensions, target count,
# red-distractor topology, and unrelated-object topology stay linked.
_PROFILES = {
    "p0": _Profile(10, 10, 2, _SQUARE4, _ELL3),
    "p1": _Profile(11, 12, 3, _BAR3, _SQUARE4),
    "p2": _Profile(9, 11, 2, _ELL3, _BAR4),
    "p3": _Profile(12, 12, 4, _NONE, _SQUARE4),
    "p4": _Profile(10, 13, 3, _SQUARE4, _ELL3),
}


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _d4_variants(
    shape: Sequence[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    for swap in (False, True):
        for sign_r in (-1, 1):
            for sign_c in (-1, 1):
                transformed = []
                for r, c in shape:
                    x, y = (c, r) if swap else (r, c)
                    transformed.append((sign_r * x, sign_c * y))
                variants.add(_normalize_shape(transformed))
    return tuple(sorted(variants))


def _canonical_shape(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return min(_d4_variants(tuple(cells)), default=())


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _x_footprint(r: int, c: int, h: int, w: int) -> set[tuple[int, int]]:
    cells = {(r, c)}
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            cells.add((rr, cc))
    return cells


def canonical_profile_signature(grid):
    """Return the task-linked profile, invariant to color and D4 orientation."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    h, w = len(grid), len(grid[0])
    red_components = _components(grid, 2)
    seed_count = sum(len(component) == 1 for component in red_components)
    red_shapes = tuple(
        sorted(
            _canonical_shape(component)
            for component in red_components
            if len(component) > 1
        )
    )
    other_shapes = []
    for color in sorted({value for row in grid for value in row} - {0, 2}):
        other_shapes.extend(
            _canonical_shape(component)
            for component in _components(grid, color)
        )
    return h, w, seed_count, red_shapes, tuple(sorted(other_shapes))


def _profile_signature(profile: _Profile):
    red_shapes = () if not profile.red_shape else (_canonical_shape(profile.red_shape),)
    return (
        profile.h,
        profile.w,
        profile.seed_count,
        red_shapes,
        (_canonical_shape(profile.other_shape),),
    )


_PROFILE_BY_SIGNATURE = {
    _profile_signature(profile): name for name, profile in _PROFILES.items()
}
_CANONICAL_SIGNATURES = frozenset(_PROFILE_BY_SIGNATURE)


def _far_enough(candidate: tuple[int, int], chosen: Sequence[tuple[int, int]]) -> bool:
    r, c = candidate
    return all(max(abs(r - rr), abs(c - cc)) >= 3 for rr, cc in chosen)


def _choose_seeds(
    h: int,
    w: int,
    count: int,
    mode: str,
    rng,
) -> list[tuple[int, int]] | None:
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    edge = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r in (0, h - 1) or c in (0, w - 1))
        and (r, c) not in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    ]
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    first_pool = {
        "interior": interior,
        "occluded": interior,
        "edge": edge,
        "corner": corners,
    }[mode]
    first_pool = first_pool[:]
    rng.shuffle(first_pool)
    for first in first_pool:
        chosen = [first]
        rest = interior[:]
        rng.shuffle(rest)
        for candidate in rest:
            if candidate in chosen or not _far_enough(candidate, chosen):
                continue
            chosen.append(candidate)
            if len(chosen) == count:
                return chosen
        if count == 1:
            return chosen
    return None


def _translated_shape(
    shape: Sequence[tuple[int, int]],
    anchor_r: int,
    anchor_c: int,
) -> set[tuple[int, int]]:
    return {(anchor_r + r, anchor_c + c) for r, c in shape}


def _shape_fits(cells: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _place_shape_random(
    shape: Sequence[tuple[int, int]],
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]] | None:
    if not shape:
        return set()
    candidates = []
    for oriented in _d4_variants(shape):
        shape_h = max(r for r, _ in oriented) + 1
        shape_w = max(c for _, c in oriented) + 1
        for anchor_r in range(h - shape_h + 1):
            for anchor_c in range(w - shape_w + 1):
                cells = _translated_shape(oriented, anchor_r, anchor_c)
                if not cells & forbidden:
                    candidates.append(cells)
    if not candidates:
        return None
    return rng.choice(candidates)


def _place_occluding_shape(
    shape: Sequence[tuple[int, int]],
    seed: tuple[int, int],
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]] | None:
    sr, sc = seed
    diagonal_targets = [
        (sr + dr, sc + dc)
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        if 0 <= sr + dr < h and 0 <= sc + dc < w
    ]
    candidates = []
    for oriented in _d4_variants(shape):
        for target_r, target_c in diagonal_targets:
            for offset_r, offset_c in oriented:
                cells = _translated_shape(
                    oriented,
                    target_r - offset_r,
                    target_c - offset_c,
                )
                if _shape_fits(cells, h, w) and not cells & forbidden:
                    candidates.append(cells)
    if not candidates:
        return None
    return rng.choice(candidates)


def _build_layout(
    profile: _Profile,
    placement_mode: str,
    nonred_color: int,
    rng,
):
    h, w = profile.h, profile.w
    for _ in range(240):
        seeds = _choose_seeds(h, w, profile.seed_count, placement_mode, rng)
        if seeds is None:
            continue
        seed_cells = set(seeds)
        footprints = set().union(*(_x_footprint(r, c, h, w) for r, c in seeds))

        if placement_mode == "occluded":
            other_cells = _place_occluding_shape(
                profile.other_shape,
                seeds[0],
                h,
                w,
                seed_cells,
                rng,
            )
        else:
            other_cells = _place_shape_random(
                profile.other_shape,
                h,
                w,
                footprints,
                rng,
            )
        if other_cells is None:
            continue

        seed_neighbors = {
            (r + dr, c + dc)
            for r, c in seeds
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= r + dr < h and 0 <= c + dc < w
        }
        red_cells = _place_shape_random(
            profile.red_shape,
            h,
            w,
            footprints | seed_neighbors | other_cells,
            rng,
        )
        if red_cells is None:
            continue

        grid = full_grid(h, w, 0)
        for r, c in seeds:
            grid[r][c] = 2
        for r, c in red_cells:
            grid[r][c] = 2
        for r, c in other_cells:
            grid[r][c] = nonred_color
        return grid
    raise ValueError("could not place the requested linked semantic profile")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_shift = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    placement_shift = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    profile_options = (
        LAYOUT_PROFILES[profile_shift:] + LAYOUT_PROFILES[:profile_shift]
    )
    placement_options = (
        PLACEMENT_MODES[placement_shift:] + PLACEMENT_MODES[:placement_shift]
    )
    layout_profile = ctx.draw_choice("layout_profile", profile_options)
    placement_mode = ctx.draw_choice("placement_mode", placement_options)
    nonred_color = ctx.draw_choice("nonred_color", NONRED_COLORS)
    return _build_layout(
        _PROFILES[layout_profile],
        placement_mode,
        nonred_color,
        ctx.draw_rng("layout"),
    )


def observe_overrides(grid):
    signature = canonical_profile_signature(grid)
    profile = _PROFILE_BY_SIGNATURE.get(signature)
    red_components = _components(grid, 2)
    seeds = [component[0] for component in red_components if len(component) == 1]
    h, w = len(grid), len(grid[0])
    other_colors = sorted({value for row in grid for value in row} - {0, 2})
    other_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    }
    if any(r in (0, h - 1) and c in (0, w - 1) for r, c in seeds):
        placement_mode = "corner"
    elif any(r in (0, h - 1) or c in (0, w - 1) for r, c in seeds):
        placement_mode = "edge"
    elif any(
        cell in other_cells
        for r, c in seeds
        for cell in _x_footprint(r, c, h, w) - {(r, c)}
    ):
        placement_mode = "occluded"
    else:
        placement_mode = "interior"
    return {
        "layout_profile": profile,
        "placement_mode": placement_mode,
        "nonred_color": other_colors[0] if len(other_colors) == 1 else None,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
        return errors
    palette = {value for row in grid for value in row}
    if 0 not in palette or 2 not in palette:
        errors.append("input must contain background 0 and red controls 2")
    if 3 in palette:
        errors.append("green 3 is an output color and must not appear in inputs")
    other_colors = palette - {0, 2}
    if len(other_colors) != 1:
        errors.append("expected exactly one unrelated non-red distractor color")

    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        errors.append("layout is not one of the five linked canonical semantic profiles")

    h, w = len(grid), len(grid[0])
    red_components = _components(grid, 2)
    seeds = [component[0] for component in red_components if len(component) == 1]
    multi_cells = {
        cell for component in red_components if len(component) > 1 for cell in component
    }
    for r, c in seeds:
        if _x_footprint(r, c, h, w) & multi_cells:
            errors.append("larger red distractor overlaps a target X footprint")
            break
    return errors
