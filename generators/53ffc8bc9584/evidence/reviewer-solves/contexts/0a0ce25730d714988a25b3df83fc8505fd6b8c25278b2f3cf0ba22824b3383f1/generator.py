"""Generator for ``arc_additional_puzzles_21_set2:E10``.

The selected rule scans the *original* grid.  In every 2x2 window containing
exactly three yellow (4) cells and one black (0) cell, the black missing corner
becomes maroon (9).  All other cells remain unchanged.

Ordinary lessons cycle through four scene families, with a seed-dependent phase
so a fixed query position tests every family across a batch.  The isolated family stays
on the demonstrated ARC manifold.  The other three families are deliberate
counterexamples to plausible shortcuts: treating only isolated L-components,
ignoring the yellow color, or filling black cells using cardinal neighbours
without checking the required yellow diagonal.  The sandwich family includes
both opposite and perpendicular two-neighbour near misses.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "53ffc8bc9584"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "fbd60dec4738"
SUMMARY = (
    "Scan every original 2x2 window.  Replace its black corner with maroon "
    "exactly when the other three cells are yellow; leave all other cells "
    "unchanged."
)
INVARIANTS = [
    "7..11 by 7..11 rectangular grid with black background",
    "exactly two or three distinct black cells satisfy a three-yellow 2x2 window",
    "all four missing-corner orientations are scheduled across each four-demo lesson",
    "four consecutive samples cover isolated, linked, sandwich, and colored-decoy scenes",
    "consecutive episode seeds rotate the family at the default query position",
    "the Racket rule, not the Python mirror, remains the output authority",
]

SCENE_FAMILIES = ("isolated", "linked", "sandwich", "colored")
DECOY_COLORS = (2, 3, 6, 8)
CORNER_NAMES = ("tl", "tr", "bl", "br")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = SCENE_FAMILIES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "7..9 square for isolated; difficulty-banded otherwise",
        "valid": "7..11",
    },
    "grid_w": {
        "type": "int",
        "default": "7..9 square for isolated; difficulty-banded otherwise",
        "valid": "7..11",
    },
    "n_targets": {
        "type": "int",
        "default": "2 easy; 2..3 medium; 3 hard",
        "valid": "2..3",
    },
    "scene_family": {
        "type": "str",
        "default": "sample_index cycle with seed-dependent phase",
        "valid": "|".join(SCENE_FAMILIES),
    },
}

# Every declared boundary combination is constructible; declaring the empty
# list opts this generator into the strict incompatibility policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Grid = list[list[int]]
Cell = tuple[int, int]


# ---------------------------------------------------------------------------
# Rule and scene analysis
# ---------------------------------------------------------------------------


def _rectangular_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, ["grid must be rectangular"]
    return h, w, []


def _trigger_windows(grid: Any) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    windows: list[dict[str, Any]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            vals = [grid[rr][cc] for rr, cc in coords]
            if vals.count(4) != 3 or vals.count(0) != 1:
                continue
            missing_index = vals.index(0)
            mr, mc = coords[missing_index]
            windows.append(
                {
                    "top_left": (r, c),
                    "target": (mr, mc),
                    "corner": CORNER_NAMES[missing_index],
                }
            )
    return windows


def _components(grid: Any, color: int) -> list[set[Cell]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    out: list[set[Cell]] = []
    while unseen:
        start = unseen.pop()
        comp = {start}
        queue: deque[Cell] = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        out.append(comp)
    return out


def _component_signature(component: Iterable[Cell]) -> tuple[int, int, frozenset[Cell]]:
    cells = set(component)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    normalized = frozenset((r - min_r, c - min_c) for r, c in cells)
    return max_r - min_r + 1, max_c - min_c + 1, normalized


def _is_l_component(component: Iterable[Cell]) -> bool:
    h, w, normalized = _component_signature(component)
    return h == 2 and w == 2 and len(normalized) == 3


_LINKED_SIGNATURES = {
    # Three yellows on one row and two on the opposite corners.  The missing
    # middle cell belongs to two overlapping trigger windows.
    (2, 3, frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)})),
    (2, 3, frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)})),
    (3, 2, frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)})),
    (3, 2, frozenset({(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)})),
}


def _is_linked_component(component: Iterable[Cell]) -> bool:
    return _component_signature(component) in _LINKED_SIGNATURES


def _l_missing_cell(component: Iterable[Cell]) -> Cell:
    cells = set(component)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    for dr in (0, 1):
        for dc in (0, 1):
            cell = (min_r + dr, min_c + dc)
            if cell not in cells:
                return cell
    raise ValueError("component is not a 3-cell 2x2 L")


def _sandwich_centers(
    grid: Any, targets: set[Cell], singleton_cells: set[Cell]
) -> tuple[set[Cell], set[Cell]]:
    h, w = len(grid), len(grid[0])
    centers: set[Cell] = set()
    supporting_cells: set[Cell] = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in targets:
                continue
            horizontal = {(r, c - 1), (r, c + 1)} if 0 < c < w - 1 else set()
            if horizontal and horizontal <= singleton_cells:
                centers.add((r, c))
                supporting_cells.update(horizontal)
            vertical = {(r - 1, c), (r + 1, c)} if 0 < r < h - 1 else set()
            if vertical and vertical <= singleton_cells:
                centers.add((r, c))
                supporting_cells.update(vertical)
    return centers, supporting_cells


def _perpendicular_centers(
    grid: Any, targets: set[Cell], singleton_cells: set[Cell]
) -> tuple[set[Cell], set[Cell]]:
    """Find non-trigger corners supported by two perpendicular yellow singletons."""
    h, w = len(grid), len(grid[0])
    centers: set[Cell] = set()
    supporting_cells: set[Cell] = set()
    directions = ((-1, 0), (0, 1), (1, 0), (0, -1))
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in targets:
                continue
            for index, (dr, dc) in enumerate(directions):
                er, ec = directions[(index + 1) % 4]
                pair = {(r + dr, c + dc), (r + er, c + ec)}
                if pair <= singleton_cells:
                    centers.add((r, c))
                    supporting_cells.update(pair)
    return centers, supporting_cells


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _rectangular_grid(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors

    if not (7 <= h <= 11 and 7 <= w <= 11):
        errors.append(f"grid dimensions must both be 7..11, got {h}x{w}")

    allowed = {0, 4, *DECOY_COLORS}
    # Validate before hashing or sorting cells: malformed external grids can
    # contain strings, None, lists or dictionaries, and self_check must return
    # diagnostics rather than crash while trying to construct its palette.
    bad = sorted({
        repr(value)
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or value not in allowed
    })
    if bad:
        errors.append(f"input palette contains unsupported values: {', '.join(bad)}")
        return info, errors

    windows = _trigger_windows(grid)
    targets = {entry["target"] for entry in windows}
    info.update(
        {
            "trigger_windows": tuple(windows),
            "targets": tuple(sorted(targets)),
            "n_targets": len(targets),
            "target_orientations": tuple(sorted({entry["corner"] for entry in windows})),
            "palette": tuple(sorted({value for row in grid for value in row})),
            "edge_target": any(r in (0, h - 1) or c in (0, w - 1) for r, c in targets),
        }
    )
    if not (2 <= len(targets) <= 3):
        errors.append(f"expected exactly 2..3 distinct completion targets, got {len(targets)}")

    yellow_components = _components(grid, 4)
    l_components = [component for component in yellow_components if _is_l_component(component)]
    linked_components = [component for component in yellow_components if _is_linked_component(component)]
    singleton_components = [component for component in yellow_components if len(component) == 1]
    malformed_yellow = [
        component
        for component in yellow_components
        if component not in l_components
        and component not in linked_components
        and component not in singleton_components
    ]
    if malformed_yellow:
        errors.append(
            "yellow cells contain a component that is neither an isolated L, "
            "the linked five-cell motif, nor a sandwich singleton"
        )

    colored_components: list[tuple[int, set[Cell]]] = []
    for color in DECOY_COLORS:
        for component in _components(grid, color):
            colored_components.append((color, component))
            if not _is_l_component(component):
                errors.append(f"color-{color} distractor must be a 3-cell 2x2 L")

    singleton_cells = {cell for component in singleton_components for cell in component}
    sandwich_centers, sandwich_cells = _sandwich_centers(grid, targets, singleton_cells)
    perpendicular_centers, perpendicular_cells = _perpendicular_centers(grid, targets, singleton_cells)
    info["perpendicular_near_misses"] = tuple(sorted(perpendicular_centers))
    uncovered_singletons = [
        component
        for component in singleton_components
        if next(iter(component)) not in sandwich_cells | perpendicular_cells
    ]
    if uncovered_singletons:
        errors.append("yellow singleton is not part of a non-trigger neighbour motif")

    special_flags = {
        "colored": bool(colored_components),
        "linked": bool(linked_components),
        "sandwich": bool(sandwich_centers),
    }
    active_special = [name for name, active in special_flags.items() if active]
    if len(active_special) > 1:
        errors.append(f"scene mixes incompatible special families: {active_special}")
        family = "mixed"
    elif active_special:
        family = active_special[0]
    else:
        family = "isolated"
    info["scene_family"] = family

    if family == "isolated":
        if len(l_components) != len(targets) or len(yellow_components) != len(l_components):
            errors.append("isolated scenes must contain only one L-component per target")
    elif family == "linked":
        if len(linked_components) != 1:
            errors.append("linked scenes must contain exactly one linked five-cell component")
        if singleton_components or colored_components or sandwich_centers:
            errors.append("linked scenes may otherwise contain only isolated yellow Ls")
        if len(l_components) + 1 != len(targets):
            errors.append("linked scene target count must equal isolated Ls plus the linked target")
    elif family == "sandwich":
        if len(sandwich_centers) != 1 or len(singleton_components) not in (2, 3):
            errors.append("sandwich scenes require one opposite-pair center and two or three yellow singletons")
        if len(singleton_components) == 3 and not perpendicular_centers:
            errors.append("the third sandwich singleton must expose a perpendicular near miss")
        if linked_components or colored_components:
            errors.append("sandwich scenes may otherwise contain only isolated yellow Ls")
        if len(l_components) != len(targets):
            errors.append("sandwich distractor must not change the true completion count")
    elif family == "colored":
        if len(colored_components) != 1:
            errors.append("colored scenes must contain exactly one non-yellow L distractor")
        if linked_components or singleton_components or sandwich_centers:
            errors.append("colored scenes may otherwise contain only isolated yellow Ls")
        if len(l_components) != len(targets):
            errors.append("colored distractor must not change the yellow completion count")

    # Every isolated yellow L must expose exactly its bbox's missing corner as a
    # true target.  This rejects extra/missing pixels that accidentally preserve
    # only the aggregate target count.
    for component in l_components:
        missing = _l_missing_cell(component)
        if missing not in targets:
            errors.append(f"isolated yellow L at {sorted(component)} does not expose its missing corner")

    return info, sorted(set(errors))


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {axis: info[axis] for axis in AXES}


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if info["scene_family"] != "isolated":
        reasons.append("canonical-like scenes use isolated yellow L-components only")
    if info["grid_h"] != info["grid_w"] or info["grid_h"] not in (7, 8, 9):
        reasons.append("canonical-like dimensions are square 7x7, 8x8, or 9x9")
    if set(info["palette"]) != {0, 4}:
        reasons.append("canonical-like input palette is exactly black and yellow")
    if len(info["target_orientations"]) < 2:
        reasons.append("canonical-like scenes show at least two missing-corner orientations")
    if info["edge_target"]:
        reasons.append("canonical targets are interior rather than boundary cells")
    return reasons


def rule_mirror(grid: Any) -> Grid:
    """Pure Python mirror used only by tests and semantic diagnostics."""
    h, w, errors = _rectangular_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    targets = {entry["target"] for entry in _trigger_windows(grid)}
    for r, c in targets:
        if not (0 <= r < h and 0 <= c < w):
            raise AssertionError("internal target outside grid")
        out[r][c] = 9
    return out


# ---------------------------------------------------------------------------
# Deterministic construction
# ---------------------------------------------------------------------------


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del difficulty
    return SCENE_FAMILIES[(sample_index + seed) % len(SCENE_FAMILIES)]


def _axis_choice(ctx, overrides: dict[str, Any], name: str, value: Any, domain: list[Any]) -> Any:
    if name in overrides:
        if all(isinstance(option, int) and not isinstance(option, bool) for option in domain):
            return ctx.draw_int(name, min(domain), max(domain))
        return ctx.draw_choice(name, domain)
    return ctx.draw_choice(name, [value])


def _default_dimensions(family: str, band: str, sample_index: int) -> tuple[int, int]:
    if family == "isolated":
        size = 7 + ((sample_index // len(SCENE_FAMILIES)) % 3)
        return size, size
    options = {
        "easy": ((7, 8), (8, 7), (8, 8)),
        "medium": ((8, 9), (9, 8), (9, 10), (10, 9)),
        "hard": ((9, 10), (10, 9), (10, 11), (11, 10)),
    }[band]
    return options[(sample_index // len(SCENE_FAMILIES)) % len(options)]


def _default_target_count(band: str, sample_index: int) -> int:
    if band == "easy":
        return 2
    if band == "hard":
        return 3
    return 2 + ((sample_index // len(SCENE_FAMILIES)) % 2)


def _l_motif(missing_index: int, color: int = 4) -> dict[str, Any]:
    cells = [
        (r, c, color)
        for r in (0, 1)
        for c in (0, 1)
        if 2 * r + c != missing_index
    ]
    return {
        "name": "yellow_l" if color == 4 else "colored_l",
        "h": 2,
        "w": 2,
        "cells": cells,
        "targets": [(missing_index // 2, missing_index % 2)] if color == 4 else [],
    }


def _linked_motif(variant: int) -> dict[str, Any]:
    variants = (
        (2, 3, {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)}, (1, 1)),
        (2, 3, {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}, (0, 1)),
        (3, 2, {(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)}, (1, 1)),
        (3, 2, {(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)}, (1, 0)),
    )
    mh, mw, cells, target = variants[variant % len(variants)]
    return {
        "name": "linked",
        "h": mh,
        "w": mw,
        "cells": [(r, c, 4) for r, c in sorted(cells)],
        "targets": [target],
    }


def _sandwich_motif(variant: int) -> dict[str, Any]:
    # Each black near-miss has yellow cardinal neighbours but lacks the
    # diagonal required to complete an L.  The top center also has opposite
    # yellow neighbours, preserving the previous family's teaching contrast.
    h, w = 2, 3
    cells = {(0, 0), (0, 2), (1, 1)}
    for _ in range(variant % 4):
        cells = {(c, h - 1 - r) for r, c in cells}
        h, w = w, h
    return {"name": "sandwich", "h": h, "w": w,
            "cells": [(r, c, 4) for r, c in sorted(cells)], "targets": []}


def _footprint(top: int, left: int, motif: dict[str, Any]) -> set[Cell]:
    return {
        (top + dr, left + dc)
        for dr in range(motif["h"])
        for dc in range(motif["w"])
    }


def _far_from(existing: set[Cell], candidate: set[Cell]) -> bool:
    return all(
        max(abs(r - rr), abs(c - cc)) > 1
        for r, c in candidate
        for rr, cc in existing
    )


def _placement_candidates(
    motif: dict[str, Any],
    h: int,
    w: int,
    *,
    margin: int,
    require_edge_target: bool,
    rng,
) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for top in range(margin, h - motif["h"] - margin + 1):
        for left in range(margin, w - motif["w"] - margin + 1):
            if require_edge_target:
                absolute_targets = [
                    (top + dr, left + dc) for dr, dc in motif["targets"]
                ]
                if not any(r in (0, h - 1) or c in (0, w - 1) for r, c in absolute_targets):
                    continue
            candidates.append((top, left))
    rng.shuffle(candidates)
    return candidates


def _place_motifs(
    h: int,
    w: int,
    motifs: list[dict[str, Any]],
    *,
    strict_margin: bool,
    edge_target_index: int | None,
    rng,
) -> Grid | None:
    grid = full_grid(h, w, 0)

    def visit(index: int, occupied_footprint: set[Cell]) -> bool:
        if index == len(motifs):
            return True
        motif = motifs[index]
        candidates = _placement_candidates(
            motif,
            h,
            w,
            margin=1 if strict_margin else 0,
            require_edge_target=index == edge_target_index,
            rng=rng,
        )
        for top, left in candidates:
            footprint = _footprint(top, left, motif)
            if occupied_footprint and not _far_from(occupied_footprint, footprint):
                continue
            for dr, dc, color in motif["cells"]:
                grid[top + dr][left + dc] = color
            if visit(index + 1, occupied_footprint | footprint):
                return True
            for dr, dc, _ in motif["cells"]:
                grid[top + dr][left + dc] = 0
        return False

    return grid if visit(0, set()) else None


def _build_motifs(
    family: str,
    n_targets: int,
    sample_index: int,
    decoy_color: int,
) -> tuple[list[dict[str, Any]], int | None]:
    orientation_start = sample_index % 4
    motifs: list[dict[str, Any]] = []
    edge_target_index: int | None = None

    if family == "linked":
        motifs.append(_linked_motif((sample_index // len(SCENE_FAMILIES)) % 4))
        edge_target_index = 0
        isolated_needed = n_targets - 1
    elif family == "sandwich":
        motifs.append(_sandwich_motif((sample_index // len(SCENE_FAMILIES)) % 4))
        isolated_needed = n_targets
        edge_target_index = 1
    elif family == "colored":
        motifs.append(_l_motif((orientation_start + 2) % 4, decoy_color))
        isolated_needed = n_targets
        edge_target_index = 1
    else:
        isolated_needed = n_targets

    for offset in range(isolated_needed):
        motifs.append(_l_motif((orientation_start + offset) % 4))
    return motifs, edge_target_index


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_targets"):
        if name in overrides and (isinstance(overrides[name], bool) or not isinstance(overrides[name], int)):
            raise ValueError(f"{name} must be an exact integer, got {overrides[name]!r}")
    if "scene_family" in overrides and overrides["scene_family"] not in SCENE_FAMILIES:
        raise ValueError(f"unknown scene_family: {overrides['scene_family']!r}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    default_family = schedule_profile(seed, sample_index, difficulty=band)
    family = _axis_choice(ctx, overrides, "scene_family", default_family, list(SCENE_FAMILIES))
    default_h, default_w = _default_dimensions(family, band, sample_index)
    h = _axis_choice(ctx, overrides, "grid_h", default_h, list(range(7, 12)))
    w = _axis_choice(ctx, overrides, "grid_w", default_w, list(range(7, 12)))
    n_targets = _axis_choice(
        ctx,
        overrides,
        "n_targets",
        _default_target_count(band, sample_index),
        [2, 3],
    )
    rng = ctx.draw_rng("layout")
    decoy_color = rng.choice(DECOY_COLORS)

    # A few motif-orientation retries are cheaper and safer than silently
    # changing an exact requested axis.  Returned-grid analysis must recover
    # the requested family and target count exactly.
    for attempt in range(32):
        motifs, edge_target_index = _build_motifs(
            family,
            n_targets,
            sample_index + 4 * attempt,
            decoy_color,
        )
        grid = _place_motifs(
            h,
            w,
            motifs,
            strict_margin=family == "isolated",
            edge_target_index=edge_target_index,
            rng=rng,
        )
        if grid is None:
            continue
        info, errors = _analyse(grid)
        if not errors and info["scene_family"] == family and info["n_targets"] == n_targets:
            return grid
    raise ValueError(
        f"could not construct exact scene_family={family!r}, n_targets={n_targets}, "
        f"grid={h}x{w}"
    )


# ---------------------------------------------------------------------------
# Rival rules and lesson-level semantic contract
# ---------------------------------------------------------------------------


def _rival_isolated_components_only(grid: Any) -> Grid:
    out = [list(row) for row in grid]
    for component in _components(grid, 4):
        if _is_l_component(component):
            r, c = _l_missing_cell(component)
            out[r][c] = 9
    return out


def _rival_color_blind_equal_l(grid: Any) -> Grid:
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            vals = [grid[rr][cc] for rr, cc in coords]
            nonzero = [value for value in vals if value != 0]
            if vals.count(0) == 1 and len(nonzero) == 3 and len(set(nonzero)) == 1:
                mr, mc = coords[vals.index(0)]
                out[mr][mc] = 9
    return out


def _rival_two_cardinal_yellows(grid: Any) -> Grid:
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            neighbours = sum(
                1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 4
            )
            if neighbours >= 2:
                out[r][c] = 9
    return out


def _rival_perpendicular_yellows(grid: Any) -> Grid:
    """Plausible shortcut: require a cardinal corner but ignore its diagonal."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    directions = ((-1, 0), (0, 1), (1, 0), (0, -1))
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            yellow = [
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 4
                for dr, dc in directions
            ]
            if any(yellow[index] and yellow[(index + 1) % 4] for index in range(4)):
                out[r][c] = 9
    return out


SEMANTIC_RIVALS = {
    "isolated_components_only": _rival_isolated_components_only,
    "color_blind_equal_l": _rival_color_blind_equal_l,
    "two_cardinal_yellows": _rival_two_cardinal_yellows,
    "perpendicular_yellows": _rival_perpendicular_yellows,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _family_witness(expected: str):
    def witness(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["scene_family"] == expected

    return witness


def _perpendicular_witness(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["perpendicular_near_misses"])


SEMANTIC_WITNESSES = {
    "linked_windows_refute_component_only": _family_witness("linked"),
    "sandwich_refutes_two_neighbor_fill": _family_witness("sandwich"),
    "colored_l_refutes_color_blind_fill": _family_witness("colored"),
    "missing_diagonal_refutes_perpendicular_fill": _perpendicular_witness,
}
WITNESS_RIVALS = {
    "linked_windows_refute_component_only": ["isolated_components_only"],
    "sandwich_refutes_two_neighbor_fill": ["two_cardinal_yellows"],
    "colored_l_refutes_color_blind_fill": ["color_blind_equal_l"],
    "missing_diagonal_refutes_perpendicular_fill": ["perpendicular_yellows"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    families: set[str] = set()
    orientations: set[str] = set()
    saw_edge_target = False
    saw_interior_target = False

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
            reasons.append(f"demo {index} output does not match the original-window rule")
        families.add(info["scene_family"])
        orientations.update(info["target_orientations"])
        saw_edge_target |= bool(info["edge_target"])
        saw_interior_target |= not bool(info["edge_target"])

    if families != set(SCENE_FAMILIES):
        reasons.append(f"demonstrations must cover all four scene families, got {sorted(families)}")
    if orientations != set(CORNER_NAMES):
        reasons.append(f"demonstrations must cover all four missing corners, got {sorted(orientations)}")
    if not saw_edge_target or not saw_interior_target:
        reasons.append("demonstrations must include both boundary and interior completion targets")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and competitor(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"declared competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyse(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the original-window rule")
    return sorted(set(reasons))
