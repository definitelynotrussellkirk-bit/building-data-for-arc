"""Generator for ARC task 7f03452e81df — Crop the Smallest Object.

The canonical Racket authority sorts same-color 4-connected nonzero components by
``(cell_count, top_row, left_column)`` and returns the original grid's inclusive
bounding-box crop for the first object.  The lesson schedule deliberately
contains counterexamples to common shortcuts: first scan-order object, smallest
bounding-box area, least-frequent color, masking away other cells in the crop,
and incomplete handling of the two tie-break keys.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7f03452e81df"
TASK_ID = "7f03452e81df"
VERSION = "3.1.0"
RULE_HASH = "677cf77c7816"

SUMMARY = (
    "On a zero background, find every same-color 4-connected nonzero object. "
    "Sort components by (cell count ascending, top row ascending, left column "
    "ascending), choose the first, and return the inclusive subgrid bounded by "
    "that object's tight bounding box. Preserve every original cell in that "
    "box, including background and any separate object that lies inside it."
)

INVARIANTS = [
    "grids use one of the three canonical (height, width, palette-size) profiles",
    "ordinary scenes contain three or four separated same-color 4-connected components",
    "the selected object is determined by (cell count, top row, left column)",
    "the output is an original-grid crop, not a mask of only the selected component",
    "five consecutive scheduled examples refute every declared lesson competitor",
]

Grid = list[list[int]]
Cell = tuple[int, int]
Object = dict[str, Any]

SCENE_PROFILES = (
    "canonical_anchor",
    "repeated_sparse",
    "nested_crop",
    "tie_row",
    "tie_col",
)
SCHEDULE_PROFILES = SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = 5
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
CANONICAL_SHAPES = ((8, 10), (9, 11), (10, 12))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "seed-phased five-example semantic schedule",
        "valid": [
            "canonical_anchor",
            "repeated_sparse",
            "nested_crop",
            "tie_row",
            "tie_col",
        ],
        "doc": (
            "canonical_anchor | repeated_sparse (cell count beats bbox area and "
            "color frequency) | nested_crop (preserve other cells in crop) | "
            "tie_row | tie_col"
        ),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# Each construction seed uses exactly three nonzero color slots. Slot zero is the
# intended object in unique-minimum scenes; repeated_sparse deliberately uses
# slot zero for two disconnected components so total color frequency is misleading.
# Generation varies connected shapes, orientation, canvas, and placement. These
# coordinates establish semantic constraints; they are not emitted as a lookup set.
_TEMPLATES: dict[str, tuple[int, int, tuple[tuple[int, tuple[Cell, ...]], ...]]] = {
    "canonical_anchor": (
        8,
        10,
        (
            (0, ((1, 1), (1, 2), (2, 1))),
            (1, ((1, 6), (1, 7), (1, 8), (2, 7), (3, 6), (3, 7))),
            (2, ((5, 4), (5, 5), (5, 6), (5, 7))),
        ),
    ),
    "repeated_sparse": (
        9,
        11,
        (
            (0, ((1, 1), (1, 2), (1, 3), (1, 4),
                 (2, 1), (2, 2), (2, 3), (2, 4))),
            (1, ((1, 6), (1, 7), (1, 8), (1, 9), (1, 10))),
            (2, ((5, 1), (5, 2), (5, 3),
                 (6, 1), (6, 2), (6, 3),
                 (7, 1), (7, 2), (7, 3))),
            (0, ((5, 6), (5, 7), (5, 8), (6, 6))),
        ),
    ),
    "nested_crop": (
        10,
        12,
        (
            (0, ((1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
                 (2, 1), (3, 1), (4, 1), (5, 1), (6, 1))),
            (1, ((3, 3), (3, 4), (3, 5), (3, 6),
                 (4, 3), (4, 4), (4, 5), (4, 6),
                 (5, 3), (5, 4), (5, 5), (5, 6))),
            (2, ((7, 7), (7, 8), (7, 9), (7, 10), (7, 11),
                 (8, 7), (8, 8), (8, 9), (8, 10), (8, 11),
                 (9, 7), (9, 8), (9, 9), (9, 10), (9, 11))),
        ),
    ),
    "tie_row": (
        9,
        11,
        (
            (0, ((1, 7), (1, 8), (1, 9), (2, 9))),
            (1, ((4, 1), (5, 1), (6, 1), (6, 2))),
            (2, ((5, 6), (5, 7), (5, 8),
                 (6, 6),
                 (7, 6), (7, 7), (7, 8))),
        ),
    ),
    "tie_col": (
        10,
        12,
        (
            (0, ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2))),
            (1, ((1, 9), (2, 9), (3, 9), (4, 9), (5, 9))),
            (2, ((7, 4), (7, 5), (7, 6), (7, 7),
                 (8, 4), (8, 5), (8, 6), (8, 7))),
        ),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return a seed-phased period-five profile; any five consecutive draws cover all."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    index = (int(seed) + int(sample_index) + offsets[difficulty]) % len(SCENE_PROFILES)
    return SCENE_PROFILES[index]


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _components(grid: Grid) -> list[Object]:
    """Mirror ``components g 0``: row-major, same-color, 4-connected components."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    out: list[Object] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            color = grid[start_r][start_c]
            queue = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[Cell] = []
            head = 0
            while head < len(queue):
                r, c = queue[head]
                head += 1
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            out.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "cell_set": frozenset(cells),
                    "size": len(cells),
                    "r1": min(rows),
                    "c1": min(cols),
                    "r2": max(rows),
                    "c2": max(cols),
                }
            )
    return out


def _key(obj: Object) -> tuple[int, int, int]:
    return int(obj["size"]), int(obj["r1"]), int(obj["c1"])


def _bbox_area(obj: Object) -> int:
    return (int(obj["r2"]) - int(obj["r1"]) + 1) * (
        int(obj["c2"]) - int(obj["c1"]) + 1
    )


def _crop_bbox(grid: Grid, obj: Object) -> Grid:
    return [
        list(row[int(obj["c1"]): int(obj["c2"]) + 1])
        for row in grid[int(obj["r1"]): int(obj["r2"]) + 1]
    ]


def _chosen(components: Sequence[Object]) -> Object:
    if not components:
        raise ValueError("no nonzero components")
    return min(components, key=_key)


def rule_mirror(grid: Grid) -> Grid:
    """Exact Python mirror of the selected task-local Racket authority."""
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    return _crop_bbox(grid, _chosen(_components(grid)))


def _foreign_cells_in_chosen_bbox(grid: Grid, chosen: Object) -> tuple[Cell, ...]:
    own = chosen["cell_set"]
    return tuple(
        (r, c)
        for r in range(int(chosen["r1"]), int(chosen["r2"]) + 1)
        for c in range(int(chosen["c1"]), int(chosen["c2"]) + 1)
        if grid[r][c] != 0 and (r, c) not in own
    )


def _classify_profile(grid: Grid, components: Sequence[Object], chosen: Object) -> str:
    minimum = int(chosen["size"])
    minima = [obj for obj in components if int(obj["size"]) == minimum]
    if len(minima) > 1:
        return "tie_col" if len({int(obj["r1"]) for obj in minima}) == 1 else "tie_row"
    if _foreign_cells_in_chosen_bbox(grid, chosen):
        return "nested_crop"
    if len({int(obj["color"]) for obj in components}) < len(components):
        return "repeated_sparse"
    return "canonical_anchor"


def _authority_errors(grid: Any) -> tuple[list[str], Grid | None, list[Object], Object | None]:
    """Validate the broad authority-visible grammar, not curriculum scheduling.

    The selected Racket rule is defined on any nonempty object set, but one-object
    and answer-equivalent-minimum scenes hide the selection operation.  Those are
    rejected here because they are lawful oracle inputs but poisonous lessons.
    Profile-specific branch obligations stay in ``_profile_analysis``.
    """
    if not _is_arc_grid(grid):
        return ["expected a nonempty rectangular ARC grid with integer colors 0..9"], None, [], None
    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    errors: list[str] = []
    if not (3 <= h <= 30 and 3 <= w <= 30):
        errors.append(f"expected dimensions in 3..30; found {h}x{w}")

    foreground_colors = {value for row in normalized for value in row if value != 0}
    if len(foreground_colors) < 2:
        errors.append(
            f"expected at least two foreground colors so object selection is visible; "
            f"found {len(foreground_colors)}"
        )

    components = _components(normalized)
    if not (2 <= len(components) <= 8):
        errors.append(f"expected 2..8 same-color components; found {len(components)}")

    # Different colors may be distinct Racket components while edge-touching,
    # but the canonical visual grammar separates every component with zero.
    for r in range(h):
        for c in range(w):
            value = normalized[r][c]
            if value == 0:
                continue
            found_touch = False
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = normalized[nr][nc]
                    if other != 0 and other != value:
                        errors.append(
                            f"different-colored components touch at {(r, c)} and {(nr, nc)}"
                        )
                        found_touch = True
                        break
            if found_touch:
                break
        if errors and errors[-1].startswith("different-colored"):
            break

    chosen = _chosen(components) if components else None
    if chosen is not None:
        official = _crop_bbox(normalized, chosen)
        if len(official) == h and len(official[0]) == w:
            errors.append("selected crop is the whole input, hiding the crop operation")
        minima = [item for item in components if int(item["size"]) == int(chosen["size"])]
        if len(minima) > 1 and all(_crop_bbox(normalized, item) == official for item in minima):
            errors.append("all minimum-size components have answer-equivalent crops")
        if len(components) > 1 and all(
            _crop_bbox(normalized, item) == official for item in components
        ):
            errors.append("every candidate component yields the same crop")
    return errors, normalized, components, chosen


def _strict_profile_errors(grid: Grid, components: Sequence[Object]) -> list[str]:
    errors: list[str] = []
    h, w = len(grid), len(grid[0])
    if (h, w) not in {(8, 10), (9, 11), (10, 12)}:
        errors.append(f"mechanical canonical profile requires 8x10, 9x11, or 10x12; found {h}x{w}")
    palette = {value for row in grid for value in row}
    if len(palette) != 4 or 0 not in palette:
        errors.append(f"mechanical canonical profile requires background plus three colors; found {sorted(palette)}")
    if len(components) not in (3, 4):
        errors.append(f"scheduled curriculum requires 3 or 4 components; found {len(components)}")
    if any(int(item["size"]) < 3 for item in components):
        errors.append("scheduled curriculum components must contain at least three cells")
    return errors

def _profile_errors(grid: Grid, components: Sequence[Object], chosen: Object, profile: str) -> list[str]:
    errors: list[str] = []
    sizes = sorted(int(obj["size"]) for obj in components)
    colors = [int(obj["color"]) for obj in components]
    minima = [obj for obj in components if int(obj["size"]) == int(chosen["size"])]
    foreign = _foreign_cells_in_chosen_bbox(grid, chosen)

    if profile == "canonical_anchor":
        if len(components) != 3 or len(set(colors)) != 3:
            errors.append("canonical_anchor requires three distinct-color components")
        if int(chosen["size"]) != 3 or len(minima) != 1:
            errors.append("canonical_anchor requires a unique three-cell minimum")
        if _bbox_area(chosen) != 4:
            errors.append("canonical_anchor minimum must be an L triomino in a 2x2 box")
        if foreign:
            errors.append("canonical_anchor crop must contain no foreign object cells")
    elif profile == "repeated_sparse":
        if len(components) != 4 or len(set(colors)) != 3 or sizes != [4, 5, 8, 9]:
            errors.append("repeated_sparse requires four components with sizes 4,5,8,9 and one repeated color")
        same_color = [obj for obj in components if obj["color"] == chosen["color"]]
        if len(same_color) != 2:
            errors.append("selected color must occur in two disconnected components")
        if _bbox_area(chosen) != 6:
            errors.append("selected four-cell object must occupy a sparse 2x3 bounding box")
        if not any(_bbox_area(obj) < _bbox_area(chosen) for obj in components if obj is not chosen):
            errors.append("a larger object must have a smaller bounding-box area")
        if components and components[0] is chosen:
            errors.append("selected object must not be the first row-major object")
        if foreign:
            errors.append("repeated_sparse crop must contain no foreign object cells")
    elif profile == "nested_crop":
        if len(components) != 3 or len(set(colors)) != 3 or sizes != [11, 12, 15]:
            errors.append("nested_crop requires distinct-color components of sizes 11,12,15")
        if _bbox_area(chosen) != 36 or not foreign:
            errors.append("nested_crop requires a 6x6 selected box containing a separate object")
    elif profile == "tie_row":
        if len(components) != 3 or len(set(colors)) != 3 or sizes != [4, 4, 7]:
            errors.append("tie_row requires distinct-color components of sizes 4,4,7")
        if len(minima) != 2 or len({int(obj["r1"]) for obj in minima}) != 2:
            errors.append("tie_row requires two minima with different top rows")
        else:
            other = next(obj for obj in minima if obj is not chosen)
            if int(chosen["c1"]) <= int(other["c1"]):
                errors.append("tie_row must make row priority disagree with leftmost priority")
            if _crop_bbox(grid, chosen) == _crop_bbox(grid, other):
                errors.append("tie_row tied components must imply different crops")
        if foreign:
            errors.append("tie_row crop must contain no foreign object cells")
    elif profile == "tie_col":
        if len(components) != 3 or len(set(colors)) != 3 or sizes != [5, 5, 8]:
            errors.append("tie_col requires distinct-color components of sizes 5,5,8")
        if len(minima) != 2 or len({int(obj["r1"]) for obj in minima}) != 1:
            errors.append("tie_col requires two minima sharing the same top row")
        else:
            other = next(obj for obj in minima if obj is not chosen)
            if int(chosen["c1"]) >= int(other["c1"]):
                errors.append("tie_col selected object must be the left minimum")
            if _crop_bbox(grid, chosen) == _crop_bbox(grid, other):
                errors.append("tie_col tied components must imply different crops")
        if foreign:
            errors.append("tie_col crop must contain no foreign object cells")
    else:  # pragma: no cover - protected by the classifier's finite codomain
        errors.append(f"unrecognized scene profile {profile!r}")
    return errors


def _profile_analysis(grid: Any) -> dict[str, Any]:
    errors, normalized, components, chosen = _authority_errors(grid)
    if normalized is None or chosen is None:
        return {"errors": errors, "profile": None, "components": components, "chosen": chosen}
    errors.extend(_strict_profile_errors(normalized, components))
    profile = _classify_profile(normalized, components, chosen)
    errors.extend(_profile_errors(normalized, components, chosen, profile))
    return {
        "errors": errors,
        "grid": normalized,
        "profile": profile,
        "components": components,
        "chosen": chosen,
    }

def self_check(grid: Any, *, difficulty: str | None = None, meta: Any = None) -> list[str]:
    del meta
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    return list(_authority_errors(grid)[0])


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked strict support at canonical dimensions/palette, independent of schedule."""
    errors, normalized, components, _ = _authority_errors(grid)
    if normalized is not None:
        errors.extend(_strict_profile_errors(normalized, components))
    return errors


def observe_overrides(grid: Any) -> dict[str, str]:
    analysis = _profile_analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": str(analysis["profile"])}


def semantic_observables(grid: Any) -> dict[str, Any]:
    analysis = _profile_analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    components: list[Object] = analysis["components"]
    chosen: Object = analysis["chosen"]
    color_counts = Counter(value for row in analysis["grid"] for value in row if value != 0)
    least_color = min(color_counts, key=lambda color: (color_counts[color], color))
    target_index = next(index for index, obj in enumerate(components) if obj is chosen)
    return {
        "scene_profile": analysis["profile"],
        "target_index": target_index,
        "target_bbox_area": _bbox_area(chosen),
        "target_color": int(chosen["color"]),
        "least_frequent_color": least_color,
        "repeated_target_color": sum(obj["color"] == chosen["color"] for obj in components) > 1,
        "larger_smaller_bbox": any(
            int(obj["size"]) > int(chosen["size"]) and _bbox_area(obj) < _bbox_area(chosen)
            for obj in components
        ),
        "foreign_cells_in_crop": bool(_foreign_cells_in_chosen_bbox(analysis["grid"], chosen)),
    }


def _obs(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and bool(predicate(observed))


def _rival_first_object(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    components = _components(grid)
    if not components:
        raise ValueError("no components")
    return _crop_bbox(grid, components[0])


def _rival_smallest_bbox_area(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    components = _components(grid)
    if not components:
        raise ValueError("no components")
    chosen = min(components, key=lambda obj: (_bbox_area(obj), int(obj["r1"]), int(obj["c1"])))
    return _crop_bbox(grid, chosen)


def _rival_least_frequent_color(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("no nonzero colors")
    color = min(counts, key=lambda value: (counts[value], value))
    components = [obj for obj in _components(grid) if int(obj["color"]) == color]
    return _crop_bbox(grid, components[0])


def _rival_selected_object_mask(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    chosen = _chosen(_components(grid))
    h = int(chosen["r2"]) - int(chosen["r1"]) + 1
    w = int(chosen["c2"]) - int(chosen["c1"]) + 1
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in chosen["cells"]:
        out[r - int(chosen["r1"])][c - int(chosen["c1"])] = grid[r][c]
    return out


def _rival_leftmost_minimum(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    components = _components(grid)
    minimum = min(int(obj["size"]) for obj in components)
    minima = [obj for obj in components if int(obj["size"]) == minimum]
    return _crop_bbox(grid, min(minima, key=lambda obj: (int(obj["c1"]), int(obj["r1"]))))


def _rival_rightmost_minimum(grid: Grid) -> Grid:
    if not _is_arc_grid(grid):
        raise ValueError("not a rectangular ARC grid")
    components = _components(grid)
    minimum = min(int(obj["size"]) for obj in components)
    minima = [obj for obj in components if int(obj["size"]) == minimum]
    return _crop_bbox(grid, min(minima, key=lambda obj: (-int(obj["c1"]), int(obj["r1"]))))


SEMANTIC_RIVALS = {
    "first_object": _rival_first_object,
    "smallest_bbox_area": _rival_smallest_bbox_area,
    "least_frequent_color": _rival_least_frequent_color,
    "selected_object_mask": _rival_selected_object_mask,
    "leftmost_minimum": _rival_leftmost_minimum,
    "rightmost_minimum": _rival_rightmost_minimum,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every declared shortcut reproduces all three canonical pairs, so generated
# counterexamples are necessary to make the rule identifiable.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "target_not_first_scan": lambda grid: _obs(grid, lambda o: o["target_index"] > 0),
    "cell_count_beats_bbox_area": lambda grid: _obs(grid, lambda o: o["larger_smaller_bbox"]),
    "component_count_beats_color_frequency": lambda grid: _obs(
        grid,
        lambda o: o["repeated_target_color"] and o["least_frequent_color"] != o["target_color"],
    ),
    "crop_preserves_foreign_cells": lambda grid: _obs(grid, lambda o: o["foreign_cells_in_crop"]),
    "row_tiebreak_precedes_column": lambda grid: _obs(grid, lambda o: o["scene_profile"] == "tie_row"),
    "column_tiebreak_after_row": lambda grid: _obs(grid, lambda o: o["scene_profile"] == "tie_col"),
}
WITNESS_RIVALS = {
    "target_not_first_scan": ["first_object"],
    "cell_count_beats_bbox_area": ["smallest_bbox_area"],
    "component_count_beats_color_frequency": ["least_frequent_color"],
    "crop_preserves_foreign_cells": ["selected_object_mask"],
    "row_tiebreak_precedes_column": ["leftmost_minimum"],
    "column_tiebreak_after_row": ["rightmost_minimum"],
}


def lesson_identifiable(demos: Sequence[dict[str, Grid]], query: dict[str, Grid]) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need {EXAMPLES_NEEDED} demonstrations; received {len(demos)}")

    for index, demo in enumerate(demos):
        grid = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        truth = rule_mirror(grid)
        if demo.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with crop-smallest authority")

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append("query input is unlawful: " + "; ".join(query_errors))
    elif query.get("output") is not None and query.get("output") != rule_mirror(query_grid):
        reasons.append("query output disagrees with crop-smallest authority")

    # Teaching is a property of the labelled evidence. A lawful scene need not
    # match the generator's exact-control observer or a fixed size signature.
    if not reasons:
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"demonstrations fail to refute competitor {name!r}")
    return reasons


def _build_scene(profile: str, colors: Sequence[int]) -> Grid:
    h, w, components = _TEMPLATES[profile]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for slot, cells in components:
        color = int(colors[slot])
        for r, c in cells:
            if grid[r][c] != 0:
                raise AssertionError(f"template overlap at {(r, c)}")
            grid[r][c] = color
    return grid


def _vary_shape(cells: Sequence[Cell], rng: Any) -> tuple[Cell, ...]:
    """Grow a connected polyomino with the seed's cell count and tight box."""
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    original = tuple(sorted((r - min_r, c - min_c) for r, c in cells))
    height = max(r for r, _ in original) + 1
    width = max(c for _, c in original) + 1
    for _ in range(24):
        shape = {(rng.randrange(height), rng.randrange(width))}
        while len(shape) < len(original):
            frontier = sorted({
                (nr, nc)
                for r, c in shape
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in shape
            })
            shape.add(rng.choice(frontier))
        if (min(r for r, _ in shape) == 0 and max(r for r, _ in shape) == height - 1
                and min(c for _, c in shape) == 0 and max(c for _, c in shape) == width - 1):
            return tuple(sorted(shape))
    # Bounded shape proposal; the original shape is connected and still receives
    # independently randomized orientation, position, and canvas below.
    return original


def _orient_group(group: Sequence[tuple[int, int, int]], rng: Any) -> list[tuple[int, int, int]]:
    """Apply one square symmetry, preserving relative placement inside a group."""
    turns, reflect = rng.randrange(4), rng.randrange(2)
    transformed = []
    for slot, r, c in group:
        if reflect:
            c = -c
        for _ in range(turns):
            r, c = c, -r
        transformed.append((slot, r, c))
    min_r = min(r for _, r, _ in transformed)
    min_c = min(c for _, _, c in transformed)
    return sorted((slot, r - min_r, c - min_c) for slot, r, c in transformed)


def _varied_scene(profile: str, colors: Sequence[int], shape: tuple[int, int], rng: Any) -> Grid:
    """Place varied components with bounded search and recheck every obligation."""
    height, width = shape
    components = _TEMPLATES[profile][2]
    for _ in range(128):
        if profile == "nested_crop":
            # Moving these two components together preserves the important
            # foreign-cell crop witness and their zero separation.
            nested = [(slot, r, c) for slot, cells in components[:2] for r, c in cells]
            slot, cells = components[2]
            groups = [_orient_group(nested, rng), _orient_group(
                [(slot, r, c) for r, c in _vary_shape(cells, rng)], rng)]
        else:
            groups = [_orient_group(
                [(slot, r, c) for r, c in _vary_shape(cells, rng)], rng)
                for slot, cells in components]
        extents = [(max(r for _, r, _ in group) + 1,
                    max(c for _, _, c in group) + 1) for group in groups]
        if any(h > height or w > width for h, w in extents):
            continue
        common_row = (rng.randrange(height - max(extents[0][0], extents[1][0]) + 1)
                      if profile == "tie_col" else None)
        grid = [[0] * width for _ in range(height)]
        occupied: set[Cell] = set()
        # Place large groups first; the nested group's internal overlap is
        # intentional, while distinct groups may neither overlap nor touch.
        order = sorted(range(len(groups)), key=lambda i: -(extents[i][0] * extents[i][1]))
        for index in order:
            h, w = extents[index]
            for _ in range(40):
                top = common_row if profile == "tie_col" and index < 2 else rng.randrange(height - h + 1)
                left = rng.randrange(width - w + 1)
                placed = [(slot, r + top, c + left) for slot, r, c in groups[index]]
                if any((nr, nc) in occupied
                       for _, r, c in placed
                       for nr, nc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))):
                    continue
                for slot, r, c in placed:
                    grid[r][c] = int(colors[slot])
                    occupied.add((r, c))
                break
            else:
                break
        else:
            analysis = _profile_analysis(grid)
            if not analysis["errors"] and analysis["profile"] == profile:
                return grid
    raise RuntimeError(f"could not place lawful {profile!r} components on {height}x{width}")


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: Any) -> Grid:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    scheduled = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(tuple(range(1, 10)), 3)
    # Repeated profile positions five indices apart use different canonical
    # canvases. In an unrejected five-demo lesson the query cannot be an exact
    # palette substitution of its same-profile demonstration. Geometry varies
    # independently too; the public lesson census checks the accepted sampler.
    shape_index = (int(seed) // len(SCENE_PROFILES) + sample_index // len(SCENE_PROFILES)) % len(CANONICAL_SHAPES)
    grid = _varied_scene(profile, colors, CANONICAL_SHAPES[shape_index], ctx.draw_rng("geometry"))
    errors = _profile_analysis(grid)["errors"]
    if errors:  # Loud internal invariant: ordinary generation never emits poison.
        raise AssertionError(f"generated invalid {profile!r} scene: {'; '.join(errors)}")
    return grid
