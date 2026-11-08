"""Lawful generators for c3fa4749: fill qualifying notches with a rare marker.

A wall cell belongs to a same-color 4-connected component of at least eight
cells.  Remove all wall cells and flood-fill the remaining regions.  A region
is a notch when every adjacent wall cell has the same color.  The marker M is
the globally rarest color present in every notch.  Every notch with at least
three cells is filled with M; one- and two-cell notches still constrain M but
remain unchanged.

The linked three-profile schedule is intentionally lesson-shaped.  Every
consecutive three examples include (1) a short notch that changes which common
color is selected, (2) a one-notch scene, and (3) a genuine global-rarity tie
break.  Thus the demos rule out the previous generator's shortcuts: requiring
multiple edge corridors, ignoring short regions, assuming a unique common
color, or filling every detected region regardless of size.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "f6b13494be37"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "4a6c0f5d3a4a"

SUMMARY = (
    "Square 20/25/30-cell scenes contain one to four isolated mono-color wall "
    "rings. Their non-wall interiors are notches. The globally rarest color "
    "shared by every notch is selected; only notches of size at least three "
    "are filled with it. Linked profiles expose short-notch evidence, a "
    "single-notch case, and a non-unique common-color rarity tie-break."
)

INVARIANTS = [
    "wall cells are exactly cells in same-color 4-components of size at least eight",
    "each generated notch is isolated by one mono-color wall ring",
    "the outside non-wall region touches at least two wall colors and is never a notch",
    "the selected marker is the unique globally rarest color in the all-notch intersection",
    "notches of size one or two constrain marker selection but are left unchanged",
    "every generated input uses all ten ARC colors and has a visible fill operation",
    "the canonical Racket program is the sole output authority",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "20 easy / 25 medium / 30 hard; linked 20/25/30 when unset",
        "valid": "20..30",
        "doc": "Square input height and width.",
    },
    "n_notches": {
        "type": "int",
        "default": "linked schedule 3,1,2",
        "valid": "1..4",
        "doc": "Exact number of one-wall-color non-wall regions.",
    },
    "common_mode": {
        "type": "enum",
        "default": "linked schedule unique,rarest_tiebreak,rarest_tiebreak",
        "valid": ["unique", "rarest_tiebreak"],
        "doc": "Whether all-notch color intersection is singleton or needs global rarity.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"n_notches": 1, "common_mode": "unique"},
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# (notch count, common-mode, canonical default grid size)
# Every cyclic window of length three contains every essential lesson branch.
_PROFILES = (
    (3, "unique", 20),             # short notch changes the selected marker
    (1, "rarest_tiebreak", 25),   # one notch; no >=2 or edge-only shortcut
    (2, "rarest_tiebreak", 30),   # short notch preserved + rarity tie-break
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components_by_color(grid: Sequence[Sequence[int]]):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen:
                continue
            color = grid[r][c]
            seen.add((r, c))
            stack = [(r, c)]
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": tuple(cells)})
    return components


def _analyze(grid) -> dict[str, object]:
    """Pure mirror of the canonical structural rule, plus review observables."""
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    color_components = _components_by_color(grid)
    wall_components = [comp for comp in color_components if len(comp["cells"]) >= 8]
    wall = {cell for comp in wall_components for cell in comp["cells"]}

    seen: set[tuple[int, int]] = set()
    regions = []
    notches = []
    for r in range(h):
        for c in range(w):
            if (r, c) in wall or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            wall_colors: set[int] = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in wall:
                        wall_colors.add(grid[nr][nc])
                    elif (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            record = {
                "cells": tuple(cells),
                "wall_colors": frozenset(wall_colors),
                "colors": frozenset(grid[rr][cc] for rr, cc in cells),
            }
            regions.append(record)
            if len(wall_colors) == 1:
                notches.append(record)

    common: set[int] = set()
    if notches:
        common = set(notches[0]["colors"])
        for notch in notches[1:]:
            common.intersection_update(notch["colors"])

    marker = None
    rarity_tie = False
    if common:
        minimum = min(counts[color] for color in common)
        minima = sorted(color for color in common if counts[color] == minimum)
        marker = minima[0]
        rarity_tie = len(minima) > 1

    fillable = [notch for notch in notches if len(notch["cells"]) >= 3]
    short = [notch for notch in notches if len(notch["cells"]) < 3]
    truth = [list(row) for row in grid]
    if marker is not None:
        for notch in fillable:
            for r, c in notch["cells"]:
                truth[r][c] = marker

    rule_errors: list[str] = []
    if not wall_components:
        rule_errors.append("no same-color component reaches the wall threshold of eight")
    if not notches:
        rule_errors.append("no non-wall region is bounded by exactly one wall color")
    if not common:
        rule_errors.append("notches have no common marker candidate")
    if rarity_tie:
        rule_errors.append("globally rarest common marker is not unique")
    if not fillable:
        rule_errors.append("no notch reaches the fill threshold of three cells")
    if marker is not None and truth == [list(row) for row in grid]:
        rule_errors.append("the qualifying-notch fill is not visible")

    fillable_common: set[int] = set()
    marker_without_short = None
    if fillable:
        fillable_common = set(fillable[0]["colors"])
        for notch in fillable[1:]:
            fillable_common.intersection_update(notch["colors"])
        if fillable_common:
            minimum = min(counts[color] for color in fillable_common)
            minima = sorted(color for color in fillable_common if counts[color] == minimum)
            if len(minima) == 1:
                marker_without_short = minima[0]

    return {
        "errors": rule_errors,
        "height": h,
        "width": w,
        "counts": counts,
        "wall": wall,
        "wall_components": wall_components,
        "regions": regions,
        "notches": notches,
        "common": frozenset(common),
        "marker": marker,
        "rarity_tie": rarity_tie,
        "fillable": fillable,
        "short": short,
        "fillable_common": frozenset(fillable_common),
        "marker_without_short": marker_without_short,
        "truth": truth,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["height"] != analysis["width"]:
        errors.append("canonical inputs are square")
    if analysis["height"] not in (20, 25, 30):
        errors.append("canonical side length must be 20, 25, or 30")
    if len({value for row in grid for value in row}) != 10:
        errors.append("canonical inputs use all ten ARC colors")
    if not 1 <= len(analysis["notches"]) <= 4:
        errors.append("canonical inputs contain one to four notches")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror for tests and reports; Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["truth"]]


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_size": analysis["height"] if analysis["height"] == analysis["width"] else None,
        "n_notches": len(analysis["notches"]),
        "common_mode": "unique" if len(analysis["common"]) == 1 else "rarest_tiebreak",
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    marker = analysis["marker"]
    return {
        **observe_overrides(grid),
        "marker": marker,
        "common_candidate_count": len(analysis["common"]),
        "marker_global_count": analysis["counts"][marker],
        "notch_sizes": sorted(len(notch["cells"]) for notch in analysis["notches"]),
        "fillable_notch_count": len(analysis["fillable"]),
        "short_notch_count": len(analysis["short"]),
        "short_notch_controls_marker": bool(analysis["short"])
        and analysis["marker_without_short"] is not None
        and analysis["marker_without_short"] != marker,
        "short_notches_preserved": all(
            analysis["truth"][r][c] == grid[r][c]
            for notch in analysis["short"]
            for r, c in notch["cells"]
        ),
        "canonical_scale_wall": max(len(comp["cells"]) for comp in analysis["wall_components"]) >= 28,
        "all_ten_colors": len(analysis["counts"]) == 10,
        "visible_transform": analysis["truth"] != [list(row) for row in grid],
    }


def _witness(grid, **expected) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and all(observed.get(key) == value for key, value in expected.items())


SEMANTIC_WITNESSES = {
    "unique_common_marker": lambda grid: _witness(grid, common_mode="unique"),
    "global_rarity_tiebreak": lambda grid: _witness(grid, common_mode="rarest_tiebreak"),
    "single_notch": lambda grid: _witness(grid, n_notches=1),
    "multiple_fillable_notches": lambda grid: semantic_observables(grid).get("fillable_notch_count", 0) >= 2,
    "short_notch_controls_marker": lambda grid: _witness(grid, short_notch_controls_marker=True),
    "short_notch_preserved": lambda grid: semantic_observables(grid).get("short_notch_count", 0) >= 1
    and _witness(grid, short_notches_preserved=True),
    "canonical_scale_wall": lambda grid: _witness(grid, canonical_scale_wall=True),
    "full_palette": lambda grid: _witness(grid, all_ten_colors=True),
    "visible_transform": lambda grid: _witness(grid, visible_transform=True),
}


def _fill_selected(grid, marker: int, *, fill_short: bool = False, largest_only: bool = False):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    selected = list(analysis["notches"] if fill_short else analysis["fillable"])
    if largest_only and selected:
        selected = [max(selected, key=lambda notch: len(notch["cells"]))]
    out = [list(row) for row in grid]
    for notch in selected:
        for r, c in notch["cells"]:
            out[r][c] = marker
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_most_frequent_common(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    marker = max(analysis["common"], key=lambda color: (analysis["counts"][color], color))
    return _fill_selected(grid, marker)


def _rival_ignore_short_notches(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    common = set(analysis["fillable"][0]["colors"])
    for notch in analysis["fillable"][1:]:
        common.intersection_update(notch["colors"])
    marker = min(common, key=lambda color: (analysis["counts"][color], color))
    return _fill_selected(grid, marker)


def _rival_fill_short_notches(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return _fill_selected(grid, analysis["marker"], fill_short=True)


def _rival_require_multiple_notches(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    if len(analysis["notches"]) < 2:
        return [list(row) for row in grid]
    return [row[:] for row in analysis["truth"]]


def _rival_fill_largest_only(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return _fill_selected(grid, analysis["marker"], largest_only=True)


SEMANTIC_RIVALS = {
    "leave the grid unchanged": _rival_identity,
    "choose the globally most frequent common color": _rival_most_frequent_common,
    "ignore one- and two-cell notches when choosing the marker": _rival_ignore_short_notches,
    "fill short notches too": _rival_fill_short_notches,
    "require at least two notches": _rival_require_multiple_notches,
    "fill only the largest qualifying notch": _rival_fill_largest_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "unique_common_marker": ["leave the grid unchanged"],
    "global_rarity_tiebreak": ["choose the globally most frequent common color"],
    "single_notch": ["require at least two notches"],
    "multiple_fillable_notches": ["fill only the largest qualifying notch"],
    "short_notch_controls_marker": ["ignore one- and two-cell notches when choosing the marker"],
    "short_notch_preserved": ["fill short notches too"],
    "canonical_scale_wall": ["leave the grid unchanged"],
    "full_palette": ["leave the grid unchanged"],
    "visible_transform": ["leave the grid unchanged"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return sample_index % len(_PROFILES)


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _wall_ring(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = set(cells)
    ring = set()
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                cell = (r + dr, c + dc)
                if cell not in cells:
                    ring.add(cell)
    return ring


def _band_positions(size: int) -> list[int]:
    # Four disjoint three-row/column bands fit even the 20x20 lower boundary.
    # Larger grids keep the same canonical-scale objects with more free space.
    del size
    return [1, 5, 9, 13]


def _build_scene(size: int, n_notches: int, common_mode: str, rng) -> list[list[int]]:
    colors = list(range(10))
    rng.shuffle(colors)
    wall_colors = colors[:n_notches]
    cursor = n_notches
    guard_color = None
    if n_notches == 1:
        guard_color = colors[cursor]
        cursor += 1
    marker = colors[cursor]
    cursor += 1

    trap = None
    if common_mode == "unique":
        trap = colors[cursor]
        cursor += 1
        background_pool = colors[cursor:]
    else:
        background_pool = colors[cursor:]
    if len(background_pool) < 2:
        raise ValueError("insufficient background colors")
    decoy = background_pool[0]

    # Adjacent background cells always differ, so no background color can
    # accidentally become an eight-cell wall component.  Every pool color is
    # used repeatedly; rings, marker, and trap/guard cover the remaining colors.
    grid = [
        [background_pool[(r + c) % len(background_pool)] for c in range(size)]
        for r in range(size)
    ]

    bands = _band_positions(size)
    rng.shuffle(bands)
    selected_bands = bands[:n_notches]
    short_index = None if n_notches == 1 else rng.randrange(n_notches)
    horizontal = rng.random() < 0.5

    occupied: set[tuple[int, int]] = set()
    for index, (band, wall_color) in enumerate(zip(selected_bands, wall_colors, strict=True)):
        is_short = index == short_index
        length = 2 if is_short else 11 + (index % 3)
        offset = rng.choice((1, size - length - 2))
        if horizontal:
            notch = {(band + 1, offset + 1 + step) for step in range(length)}
        else:
            notch = {(offset + 1 + step, band + 1) for step in range(length)}
        ring = _wall_ring(notch)
        if any(not (0 <= r < size and 0 <= c < size) for r, c in notch | ring):
            raise ValueError("notch shape escaped the grid")
        if occupied.intersection(notch | ring):
            raise ValueError("notch bands overlap")
        occupied.update(notch | ring)
        for r, c in ring:
            grid[r][c] = wall_color

        cells = sorted(notch)
        if is_short:
            values = [marker, decoy if common_mode == "rarest_tiebreak" else background_pool[-1]]
            rng.shuffle(values)
            for (r, c), value in zip(cells, values, strict=True):
                grid[r][c] = value
        else:
            # Alternate background colors along the corridor, then inject each
            # required all-notch candidate exactly once. No interior component
            # can cross the eight-cell wall threshold.
            fillers = background_pool[:-1] if common_mode == "unique" else background_pool
            for position, (r, c) in enumerate(cells):
                grid[r][c] = fillers[position % len(fillers)]
            special = cells[:]
            rng.shuffle(special)
            grid[special[0][0]][special[0][1]] = marker
            grid[special[1][0]][special[1][1]] = decoy if common_mode == "rarest_tiebreak" else trap

    if guard_color is not None:
        # A second eight-cell wall island prevents the outside region from
        # being classified as a notch in the one-notch profile.
        guard_band = next(value for value in bands if value not in selected_bands)
        if horizontal:
            guard = {(guard_band + dr, size // 2 - 2 + dc) for dr in range(2) for dc in range(4)}
        else:
            guard = {(size // 2 - 2 + dc, guard_band + dr) for dr in range(2) for dc in range(4)}
        if occupied.intersection(guard):
            raise ValueError("guard overlaps notch")
        for r, c in guard:
            grid[r][c] = guard_color

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; Racket owns the output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    profile_n, profile_mode, profile_size = _PROFILES[schedule_profile(seed, sample_index, difficulty)]
    default_size = {None: profile_size, "easy": 20, "medium": 25, "hard": 30}[difficulty]
    default_n = profile_n
    default_mode = profile_mode

    explicit_n = overrides.get("n_notches") if overrides.get("n_notches") is not None else None
    explicit_mode = overrides.get("common_mode") if overrides.get("common_mode") is not None else None
    if explicit_n == 1 and explicit_mode == "unique":
        raise ValueError("incompatible overrides: n_notches=1 and common_mode='unique'")
    if explicit_n == 1 and explicit_mode is None:
        default_mode = "rarest_tiebreak"
    if explicit_mode == "unique" and explicit_n is None and default_n == 1:
        default_n = 3

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size = _draw_int_axis(ctx, overrides, "grid_size", default_size, 20, 30)
    n_notches = _draw_int_axis(ctx, overrides, "n_notches", default_n, 1, 4)
    common_mode = _draw_choice_axis(
        ctx,
        overrides,
        "common_mode",
        default_mode,
        ("unique", "rarest_tiebreak"),
    )
    if n_notches == 1 and common_mode == "unique":
        raise ValueError("incompatible overrides: n_notches=1 and common_mode='unique'")

    grid = _build_scene(size, n_notches, common_mode, ctx.draw_rng("scene"))
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_size": size, "n_notches": n_notches, "common_mode": common_mode}
    if observed != expected:
        raise ValueError(f"constructed scene did not realize overrides: {observed!r} != {expected!r}")
    return [row[:] for row in grid]


def lesson_identifiable(demos, query) -> list[str]:
    """Require materialized demos to falsify every named rule shortcut."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the notch-fill rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
