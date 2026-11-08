"""Generator for ``choose_the_dihedral_match`` (task 4a3e2293a089).

A color-1 component is the guide shape.  Sort the three other monochrome
components by bounding-box reading order.  The oracle selects the FIRST
component whose shape belongs to the guide's dihedral orbit, transforms that
component into the guide's exact orientation, and returns the tight crop in
the selected component's color.

The first-match tie-break is answer-bearing: three of the four canonical
inputs contain two matching candidates.  Normal draws therefore schedule both
unique-match and tied-match scenes, vary whether a nonmatch precedes the
selected match, and vary whether the selected candidate already has the
guide's orientation.  Four consecutive samples cover every decisive branch.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a3e2293a089"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "045c3413cd7d"

SUMMARY = (
    "A color-1 guide and exactly three colored candidates. Sort candidates "
    "by bbox reading order, choose the first candidate dihedrally equivalent "
    "to the guide, transform it into the guide's orientation, and output its "
    "tight crop in the candidate's color. One or two candidates may match; "
    "when two match, reading order decides."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and the canvas is one canonical 10/11 by 14/15/16 profile",
    "exactly one connected color-1 guide component and exactly three other connected monochrome components",
    "candidate colors are distinct and every motif is spatially separated",
    "one or two candidates are dihedrally equivalent to the guide",
    "the first matching candidate in bbox reading order is the selected source color",
    "the output shape is the guide orientation, not necessarily the selected candidate's input orientation",
]

# Every axis is exact and recoverable from the returned grid.  The default
# schedule is deterministic in sample_index; explicit overrides still receive
# the full declared range.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index schedule over canonical heights",
        "valid": "10..11",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index schedule over canonical widths",
        "valid": "14..16",
    },
    "guide_cells": {
        "type": "int",
        "default": "sample_index schedule 4,5,6,5",
        "valid": "4..6",
    },
    "n_matches": {
        "type": "int",
        "default": "sample_index schedule 1,2,1,2",
        "valid": "1..2",
    },
    "selected_rank": {
        "type": "int",
        "default": "sample_index schedule 0,0,1,1",
        "valid": "0..1",
    },
    "match_orientation": {
        "type": "enum",
        "default": "sample_index schedule different,same,different,different",
        "valid": ["same", "different"],
    },
}

_CANONICAL_PROFILES = ((10, 14), (11, 15), (10, 15), (11, 16))
_GUIDE_SIZE_SCHEDULE = (4, 5, 6, 5)
_MATCH_COUNT_SCHEDULE = (1, 2, 1, 2)
_SELECTED_RANK_SCHEDULE = (0, 0, 1, 1)
_ORIENTATION_SCHEDULE = ("different", "same", "different", "different")


def _normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(c, -r) for r, c in cells]


def _flip_lr(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(r, -c) for r, c in cells]


def _variants(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Unique normalized D4 variants in deterministic order."""
    variants: list[list[tuple[int, int]]] = []
    seen: set[tuple[tuple[int, int], ...]] = set()
    cur = list(cells)
    for reflected in (False, True):
        cur = _flip_lr(cells) if reflected else list(cells)
        for _ in range(4):
            norm = _normalize(cur)
            key = tuple(norm)
            if key not in seen:
                seen.add(key)
                variants.append(norm)
            cur = _rotate_cw(cur)
    return variants


def _orbit_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(tuple(v) for v in _variants(cells))


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


@lru_cache(maxsize=None)
def _shape_classes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All connected 3x3 polyomino classes of ``size`` under D4."""
    by_orbit: dict[
        tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]
    ] = {}
    cells = tuple((r, c) for r in range(3) for c in range(3))
    for combo in combinations(cells, size):
        cell_set = set(combo)
        if not _connected(cell_set):
            continue
        norm = tuple(_normalize(combo))
        key = _orbit_key(norm)
        by_orbit.setdefault(key, norm)
    classes = tuple(sorted(by_orbit.values()))
    if len(classes) < 3:
        raise RuntimeError(f"need at least three D4 classes for size {size}")
    return classes


def _component_bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components_by_color(grid: list[list[int]]) -> list[dict]:
    """Return 4-connected monochrome nonzero components in reading order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and grid[nx][ny] == color
                    ):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            bbox = _component_bbox(cells)
            components.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "norm": _normalize(cells),
                    "bbox": bbox,
                    "size": len(cells),
                    "height": bbox[2] - bbox[0] + 1,
                    "width": bbox[3] - bbox[1] + 1,
                }
            )
    return sorted(components, key=lambda item: item["bbox"][:2])


def _analyze(grid: list[list[int]]) -> dict:
    components = _components_by_color(grid)
    guides = [component for component in components if component["color"] == 1]
    candidates = sorted(
        [component for component in components if component["color"] != 1],
        key=lambda item: item["bbox"][:2],
    )
    guide = guides[0] if len(guides) == 1 else None
    matches: list[int] = []
    if guide is not None:
        guide_orbit = _orbit_key(guide["norm"])
        matches = [
            index
            for index, candidate in enumerate(candidates)
            if _orbit_key(candidate["norm"]) == guide_orbit
        ]
    return {
        "components": components,
        "guides": guides,
        "guide": guide,
        "candidates": candidates,
        "matches": matches,
    }


def _scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], value: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (value,))


def _stamp(
    grid: list[list[int]],
    shape: Iterable[tuple[int, int]],
    color: int,
    slot_top: int,
    slot_left: int,
    rng,
) -> None:
    shape = _normalize(shape)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    # Every motif fits a 3x3 slot. Keep the row fixed so the two lower
    # candidates have an unambiguous left-to-right reading order; horizontal
    # jitter avoids one fixed absolute placement without changing rank.
    top = slot_top
    left = slot_left + rng.randint(0, 3 - width)
    for r, c in shape:
        grid[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    phase = sample_index % 4
    profile_h, profile_w = _CANONICAL_PROFILES[phase]
    h = _scheduled_int(ctx, "grid_h", 10, 11, profile_h)
    w = _scheduled_int(ctx, "grid_w", 14, 16, profile_w)
    guide_cells = _scheduled_int(
        ctx, "guide_cells", 4, 6, _GUIDE_SIZE_SCHEDULE[phase]
    )
    n_matches = _scheduled_int(
        ctx, "n_matches", 1, 2, _MATCH_COUNT_SCHEDULE[phase]
    )
    selected_rank = _scheduled_int(
        ctx, "selected_rank", 0, 1, _SELECTED_RANK_SCHEDULE[phase]
    )
    orientation = _scheduled_choice(
        ctx,
        "match_orientation",
        ("same", "different"),
        _ORIENTATION_SCHEDULE[phase],
    )

    layout_rng = ctx.draw_rng("layout")
    shape_rng = ctx.draw_rng("shape")
    color_rng = ctx.draw_rng("colors")

    classes = list(_shape_classes(guide_cells))
    eligible_guides = [shape for shape in classes if len(_variants(shape)) >= 2]
    # Difficulty changes the selected shape class while preserving the exact
    # semantic schedule. This keeps the three bands behaviorally distinct
    # without turning difficulty into a hidden answer-bearing axis.
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 1)
    guide_index = (shape_rng.randrange(len(eligible_guides)) + band_offset) % len(eligible_guides)
    guide = list(eligible_guides[guide_index])
    guide_orbit = _orbit_key(guide)
    distractor_classes = [shape for shape in classes if _orbit_key(shape) != guide_orbit]
    shape_rng.shuffle(distractor_classes)

    selected_variants = _variants(guide)
    if orientation == "same":
        selected_shape = list(guide)
    else:
        different = [variant for variant in selected_variants if variant != guide]
        if not different:
            raise ValueError("selected guide class has no different orientation")
        selected_shape = list(shape_rng.choice(different))

    match_ranks = {selected_rank}
    if n_matches == 2:
        # Phase 1 mirrors two canonical rows (second match immediately after
        # the selected one); phase 3 places a nonmatch before the selected and
        # the second match after it.
        extra_rank = 1 if selected_rank == 0 else 2
        match_ranks.add(extra_rank)

    candidate_shapes: list[list[tuple[int, int]]] = []
    distractor_index = 0
    for rank in range(3):
        if rank == selected_rank:
            candidate_shapes.append(selected_shape)
        elif rank in match_ranks:
            variants = [variant for variant in selected_variants if variant != selected_shape]
            candidate_shapes.append(list(shape_rng.choice(variants or selected_variants)))
        else:
            candidate_shapes.append(list(distractor_classes[distractor_index]))
            distractor_index += 1

    colors = color_rng.sample([2, 3, 4, 5, 6, 7, 8], 3)
    grid = full_grid(h, w, 0)
    slots = (
        (1, 1),
        (1, w - 4),
        (h - 4, 1),
        (h - 4, w - 4),
    )
    _stamp(grid, guide, 1, *slots[0], layout_rng)
    for shape, color, slot in zip(candidate_shapes, colors, slots[1:]):
        _stamp(grid, shape, color, *slot, layout_rng)
    return grid


def _different_color_touching(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < h and nc < w:
                    other = grid[nr][nc]
                    if other != 0 and other != value:
                        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural checker for both canonical inputs and generated lessons."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    h, w = len(grid), width
    errors: list[str] = []
    if not (10 <= h <= 11 and 14 <= w <= 16):
        errors.append(f"canvas {h}x{w} outside canonical envelope 10..11 x 14..16")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    analysis = _analyze(grid)
    guides = analysis["guides"]
    candidates = analysis["candidates"]
    if len(guides) != 1:
        errors.append(f"expected exactly one color-1 guide component, found {len(guides)}")
        return errors
    guide = guides[0]
    if not 4 <= guide["size"] <= 6:
        errors.append(f"guide size {guide['size']} outside 4..6 cells")
    if guide["height"] > 3 or guide["width"] > 3:
        errors.append("guide bbox must fit within 3x3")

    if len(candidates) != 3:
        errors.append(f"expected exactly three candidate components, found {len(candidates)}")
    candidate_colors = [candidate["color"] for candidate in candidates]
    if len(set(candidate_colors)) != len(candidate_colors):
        errors.append("candidate components must use three distinct colors")
    for candidate in candidates:
        if not 3 <= candidate["size"] <= 6:
            errors.append(
                f"candidate color {candidate['color']} size {candidate['size']} outside 3..6"
            )
        if candidate["height"] > 3 or candidate["width"] > 3:
            errors.append(f"candidate color {candidate['color']} bbox exceeds 3x3")

    if _different_color_touching(grid):
        errors.append("different-colored motifs must not touch orthogonally")

    matches = analysis["matches"]
    if not 1 <= len(matches) <= 2:
        errors.append(f"expected one or two dihedral-matching candidates, found {len(matches)}")
    elif matches[0] > 1:
        errors.append(
            f"first matching candidate rank {matches[0]} is outside the supported 0..1 range"
        )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic AXES value from the returned grid."""
    analysis = _analyze(grid)
    guide = analysis["guide"]
    matches = analysis["matches"]
    candidates = analysis["candidates"]
    if guide is None or not matches:
        return {}
    selected_rank = matches[0]
    selected = candidates[selected_rank]
    orientation = "same" if selected["norm"] == guide["norm"] else "different"
    return {
        "guide_cells": guide["size"],
        "n_matches": len(matches),
        "selected_rank": selected_rank,
        "match_orientation": orientation,
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, stricter than ``self_check``."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in _CANONICAL_PROFILES:
        return [f"dimensions {h}x{w} are not one of the four canonical profiles"]
    analysis = _analyze(grid)
    guide = analysis["guide"]
    candidates = analysis["candidates"]
    reasons: list[str] = []
    if guide["size"] != 5:
        reasons.append(f"canonical guide size is 5, found {guide['size']}")
    if len({value for row in grid for value in row}) != 5:
        reasons.append("canonical palette has exactly background, guide, and three candidate colors")
    gr1, gc1, _, _ = guide["bbox"]
    if gr1 > 2 or gc1 > 3:
        reasons.append("guide is not in the canonical upper-left role")
    if candidates:
        cr1, cc1, _, _ = candidates[0]["bbox"]
        if cr1 > 3 or cc1 < 7:
            reasons.append("first candidate is not in the canonical upper-right role")
    if len(candidates) == 3 and any(candidate["bbox"][0] < 5 for candidate in candidates[1:]):
        reasons.append("lower candidate row is not separated from the upper roles")
    return reasons


MIN_STRICT_FRAC = 0.45


def _witness_unique_match(grid) -> bool:
    return len(_analyze(grid)["matches"]) == 1


def _witness_tied_match(grid) -> bool:
    return len(_analyze(grid)["matches"]) == 2


def _witness_nonmatch_before_selected(grid) -> bool:
    analysis = _analyze(grid)
    return bool(analysis["matches"] and analysis["matches"][0] == 1)


def _witness_orientation_same(grid) -> bool:
    return observe_overrides(grid).get("match_orientation") == "same"


def _witness_orientation_changed(grid) -> bool:
    return observe_overrides(grid).get("match_orientation") == "different"


def _witness_count_only_rebuttal(grid) -> bool:
    analysis = _analyze(grid)
    guide = analysis["guide"]
    if guide is None:
        return False
    match_set = set(analysis["matches"])
    return any(
        index not in match_set and candidate["size"] == guide["size"]
        for index, candidate in enumerate(analysis["candidates"])
    )


def _witness_guide_size(size: int):
    return lambda grid: (
        (_analyze(grid)["guide"] is not None)
        and _analyze(grid)["guide"]["size"] == size
    )


SEMANTIC_WITNESSES = {
    "unique_match": _witness_unique_match,
    "tied_match_reading_order": _witness_tied_match,
    "nonmatch_before_selected": _witness_nonmatch_before_selected,
    "selected_already_oriented": _witness_orientation_same,
    "selected_requires_transform": _witness_orientation_changed,
    "same_size_nonmatch_refutes_count_only": _witness_count_only_rebuttal,
    "guide_size_4": _witness_guide_size(4),
    "guide_size_5": _witness_guide_size(5),
    "guide_size_6": _witness_guide_size(6),
}


def _paint_normalized(cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    norm = _normalize(cells)
    h = max(r for r, _ in norm) + 1
    w = max(c for _, c in norm) + 1
    out = full_grid(h, w, 0)
    for r, c in norm:
        out[r][c] = color
    return out


def _rule_mirror(grid):
    """Pure test/semantic hook mirror; the Racket oracle remains authority."""
    analysis = _analyze(grid)
    if analysis["guide"] is None or not analysis["matches"]:
        return None
    selected = analysis["candidates"][analysis["matches"][0]]
    return _paint_normalized(analysis["guide"]["norm"], selected["color"])


def _competitor_keep_candidate_orientation(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None or not analysis["matches"]:
        return None
    selected = analysis["candidates"][analysis["matches"][0]]
    return _paint_normalized(selected["norm"], selected["color"])


def _competitor_last_match(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None or not analysis["matches"]:
        return None
    selected = analysis["candidates"][analysis["matches"][-1]]
    return _paint_normalized(analysis["guide"]["norm"], selected["color"])


def _competitor_candidate_rank(grid, rank: int):
    analysis = _analyze(grid)
    if analysis["guide"] is None or len(analysis["candidates"]) <= rank:
        return None
    selected = analysis["candidates"][rank]
    return _paint_normalized(analysis["guide"]["norm"], selected["color"])


def _competitor_copy_guide(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None:
        return None
    return _paint_normalized(analysis["guide"]["norm"], 1)


def _competitor_exact_orientation_only(grid):
    analysis = _analyze(grid)
    guide = analysis["guide"]
    if guide is None:
        return None
    exact = [
        candidate
        for candidate in analysis["candidates"]
        if candidate["norm"] == guide["norm"]
    ]
    if not exact:
        return None
    return _paint_normalized(guide["norm"], exact[0]["color"])


_LESSON_COMPETITORS = {
    "crop the selected candidate without reorienting it": _competitor_keep_candidate_orientation,
    "choose the last matching candidate instead of the first": _competitor_last_match,
    "always use candidate rank 0": lambda grid: _competitor_candidate_rank(grid, 0),
    "always use candidate rank 1": lambda grid: _competitor_candidate_rank(grid, 1),
    "copy the color-1 guide": _competitor_copy_guide,
    "match only exact orientation, not the dihedral orbit": _competitor_exact_orientation_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named plausible rival alive."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        mirrored = _rule_mirror(demo["input"])
        if mirrored != demo["output"]:
            reasons.append(
                f"demo {index} output disagrees with first-dihedral-match/reorient rule"
            )
    for name, competitor in _LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule '{name}' fits every demo but changes the query answer"
                )
    return reasons
