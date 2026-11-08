"""Semantic generator for ARC task 62757098b2dd (source slug e9ac8c9e).

For every solid gray rectangle, four colored cells sit diagonally one cell
outside its corners.  The output erases those marker cells and fills the
rectangle's top-left, top-right, bottom-left, and bottom-right quadrants with
the corresponding marker colors.  Each rectangle is processed independently.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "62757098b2dd"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"  # honest exact axes, structural grammar, and semantic schedule
# sha256[:12] of whitespace-normalized canonical program_solution.
RULE_HASH = "6d0daea2c755"

SUMMARY = (
    "For each solid gray(5) rectangle, read the four distinct colored markers "
    "one cell diagonally outside its bounding-box corners. Erase those markers "
    "and fill the rectangle's four local quadrants with the top-left, top-right, "
    "bottom-left, and bottom-right marker colors. Process every rectangle "
    "independently; for odd dimensions the extra row or column belongs to the "
    "bottom or right half."
)

INVARIANTS = [
    "literal color 0 is background",
    "there are one to three 4-connected gray(5) components",
    "every gray component exactly fills a rectangular bounding box",
    "each rectangle has four distinct non-{0,5} markers at its diagonal outer corners",
    "marker cells are unambiguous, in bounds, and are the only non-{0,5} cells",
    "rectangles and their marker cells do not overlap",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical_2x2",
    "odd_both",
    "canonical_multi",
    "canonical_6x6_border",
    "canonical_4x4",
    "odd_height",
    "multi_mixed",
    "odd_width",
)
SCHEDULE_PROFILES = SCENE_PROFILES

PALETTE_PROFILES = ("primary", "cool", "warm", "broad")
# Single-object profiles use four colors; multi-object profiles use six colors
# while retaining four distinct markers around every rectangle.
_SINGLE_PALETTES: dict[str, tuple[int, ...]] = {
    "primary": (1, 2, 3, 4),
    "cool": (1, 6, 7, 8),
    "warm": (2, 4, 6, 9),
    "broad": (1, 7, 8, 9),
}
_MULTI_PALETTES: dict[str, tuple[int, ...]] = {
    "primary": (1, 2, 3, 4, 6, 7),
    "cool": (1, 3, 6, 7, 8, 9),
    "warm": (2, 3, 4, 6, 8, 9),
    "broad": (1, 2, 4, 7, 8, 9),
}
_SINGLE_PALETTE_BY_SET = {
    frozenset(colors): name for name, colors in _SINGLE_PALETTES.items()
}
_MULTI_PALETTE_BY_SET = {
    frozenset(colors): name for name, colors in _MULTI_PALETTES.items()
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "eight-slot semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_profile": {
        "type": "str",
        "default": "deterministic keyed draw",
        "valid": "|".join(PALETTE_PROFILES),
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band_name(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = max(0.0, min(1.0, float(difficulty)))
        return "easy" if value < 0.34 else "medium" if value < 0.67 else "hard"
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile {profile!r}")
    palette = overrides.get("palette_profile")
    if palette is not None and palette not in PALETTE_PROFILES:
        raise ValueError(f"unknown palette_profile {palette!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    bad = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    return [f"cells must be ARC integer colors 0..9; found {bad[:4]}"] if bad else []


def _gray_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: min(cells))


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    errors = _valid_grid(grid)
    result: dict[str, Any] = {"errors": errors, "rectangles": []}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    components = _gray_components(grid)
    if not 1 <= len(components) <= 3:
        errors.append(f"expected one to three gray rectangles; got {len(components)}")

    rectangles: list[dict[str, Any]] = []
    expected_markers: list[tuple[int, int]] = []
    for index, cells in enumerate(components):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        prefix = f"gray component {index + 1}"
        if len(cells) != height * width:
            errors.append(f"{prefix} must fill its rectangular bounding box")
        if height < 2 or width < 2:
            errors.append(f"{prefix} must be at least 2x2")
        marker_cells = (
            (r1 - 1, c1 - 1),
            (r1 - 1, c2 + 1),
            (r2 + 1, c1 - 1),
            (r2 + 1, c2 + 1),
        )
        if any(not (0 <= r < h and 0 <= c < w) for r, c in marker_cells):
            errors.append(f"{prefix} has an out-of-bounds corner marker")
            marker_colors: tuple[int, ...] = ()
        else:
            marker_colors = tuple(grid[r][c] for r, c in marker_cells)
            if any(color in (0, 5) for color in marker_colors):
                errors.append(f"{prefix} requires four non-{{0,5}} corner markers")
            if len(set(marker_colors)) != 4:
                errors.append(f"{prefix} corner marker colors must be distinct")
            expected_markers.extend(marker_cells)
        rectangles.append(
            {
                "bbox": (r1, c1, r2, c2),
                "height": height,
                "width": width,
                "cells": cells,
                "marker_cells": marker_cells,
                "marker_colors": marker_colors,
            }
        )

    if len(set(expected_markers)) != len(expected_markers):
        errors.append("two rectangles reuse the same marker cell")
    expected_set = set(expected_markers)
    actual_marker_set = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 5)
    }
    missing = expected_set - actual_marker_set
    extras = actual_marker_set - expected_set
    if missing:
        errors.append(f"missing {len(missing)} required corner marker cell(s)")
    if extras:
        errors.append(f"found {len(extras)} orphan non-{{0,5}} cell(s)")

    gray_set = {cell for rect in rectangles for cell in rect["cells"]}
    if expected_set & gray_set:
        errors.append("a marker cell overlaps a gray rectangle")

    result.update(
        {
            "rectangles": rectangles,
            "marker_cells": expected_set,
            "marker_colors": {grid[r][c] for r, c in expected_set if (r, c) in actual_marker_set},
            "errors": errors,
        }
    )
    return result


def _apply_rule(grid: list[list[int]], *, keep_markers: bool = False,
                ceil_split: bool = False, first_only: bool = False) -> list[list[int]]:
    facts = _facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = [list(row) for row in grid]
    rectangles = facts["rectangles"][:1] if first_only else facts["rectangles"]
    for rect in rectangles:
        r1, c1, r2, c2 = rect["bbox"]
        height, width = rect["height"], rect["width"]
        tl, tr, bl, br = rect["marker_colors"]
        if not keep_markers:
            for r, c in rect["marker_cells"]:
                output[r][c] = 0
        mid_r = r1 + ((height + 1) // 2 if ceil_split else height // 2)
        mid_c = c1 + ((width + 1) // 2 if ceil_split else width // 2)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r < mid_r and c < mid_c:
                    color = tl
                elif r < mid_r and c >= mid_c:
                    color = tr
                elif r >= mid_r and c < mid_c:
                    color = bl
                else:
                    color = br
                output[r][c] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python audit mirror; the canonical Racket program remains output authority."""
    return _apply_rule(grid)


def _scene_profile(facts: dict[str, Any], grid: list[list[int]]) -> str | None:
    if facts["errors"]:
        return None
    dims = (len(grid), len(grid[0]))
    sizes = sorted((rect["height"], rect["width"]) for rect in facts["rectangles"])
    if dims == (10, 10) and sizes == [(2, 2)]:
        return "canonical_2x2"
    if dims == (10, 10) and sizes == [(4, 4)]:
        return "canonical_4x4"
    if dims == (10, 10) and sizes == [(6, 6)]:
        marker_cells = facts["rectangles"][0]["marker_cells"]
        if any(r in (0, 9) or c in (0, 9) for r, c in marker_cells):
            return "canonical_6x6_border"
    if dims == (15, 15) and sizes == [(2, 2), (4, 4), (6, 6)]:
        return "canonical_multi"
    if sizes == [(5, 4)]:
        return "odd_height"
    if sizes == [(4, 5)]:
        return "odd_width"
    if sizes == [(5, 5)]:
        return "odd_both"
    if sizes == [(3, 4), (4, 3), (5, 5)]:
        return "multi_mixed"
    return None


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    facts = _facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    scene = _scene_profile(facts, grid)
    if scene is None:
        raise ValueError("grid does not match a declared scene_profile")
    colors = frozenset(facts["marker_colors"])
    if len(facts["rectangles"]) == 1:
        palette = _SINGLE_PALETTE_BY_SET.get(colors)
    else:
        palette = _MULTI_PALETTE_BY_SET.get(colors)
    if palette is None:
        raise ValueError(f"marker palette {sorted(colors)} is not a declared profile")
    return {"scene_profile": scene, "palette_profile": palette}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _facts(grid)
    errors = list(facts["errors"])
    if not errors:
        scene = _scene_profile(facts, grid)
        if scene is None:
            errors.append("scene does not match any declared teaching profile")
        if rule_mirror(grid) == [list(row) for row in grid]:
            errors.append("quadrant-fill rule is an identity on this scene")
    requested = ((meta or {}).get("overrides") or {})
    if requested and not errors:
        observed = observe_overrides(grid)
        for name in _ALLOWED_OVERRIDES:
            if name in requested and requested[name] is not None and observed.get(name) != requested[name]:
                errors.append(
                    f"{name} drifted from requested {requested[name]!r} to {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked input grammar shared by canonical and generated scenes."""
    return self_check(grid)


def _blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _expanded_box(spec: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    r1, c1, height, width = spec
    return r1 - 1, c1 - 1, r1 + height, c1 + width


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _place_sizes(h: int, w: int, sizes: Iterable[tuple[int, int]], rng) -> list[tuple[int, int, int, int]]:
    specs: list[tuple[int, int, int, int]] = []
    for height, width in sizes:
        candidates = [
            (r1, c1, height, width)
            for r1 in range(1, h - height)
            for c1 in range(1, w - width)
        ]
        rng.shuffle(candidates)
        chosen = next(
            (
                candidate
                for candidate in candidates
                if all(
                    not _boxes_overlap(_expanded_box(candidate), _expanded_box(existing))
                    for existing in specs
                )
            ),
            None,
        )
        if chosen is None:
            raise RuntimeError(f"could not place rectangle {height}x{width} on {h}x{w}")
        specs.append(chosen)
    return specs


def _profile_layout(profile: str, band: str, rng) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    if profile == "canonical_2x2":
        h = w = 10
        specs = _place_sizes(h, w, [(2, 2)], rng)
    elif profile == "canonical_4x4":
        h = w = 10
        specs = _place_sizes(h, w, [(4, 4)], rng)
    elif profile == "canonical_6x6_border":
        h = w = 10
        r1 = rng.choice((1, 3))
        c1 = rng.choice((1, 3))
        specs = [(r1, c1, 6, 6)]
    elif profile == "canonical_multi":
        h = w = 15
        specs = [(1, 1, 6, 6), (4, 11, 2, 2), (10, 6, 4, 4)]
    elif profile == "odd_height":
        h, w = {"easy": (11, 11), "medium": (13, 14), "hard": (17, 18)}[band]
        specs = _place_sizes(h, w, [(5, 4)], rng)
    elif profile == "odd_width":
        h, w = {"easy": (11, 11), "medium": (14, 13), "hard": (18, 17)}[band]
        specs = _place_sizes(h, w, [(4, 5)], rng)
    elif profile == "odd_both":
        side = {"easy": 11, "medium": 13, "hard": 17}[band]
        h = w = side
        specs = _place_sizes(h, w, [(5, 5)], rng)
    elif profile == "multi_mixed":
        side = {"easy": 16, "medium": 19, "hard": 23}[band]
        h = w = side
        # Fixed separated anchors avoid a greedy-placement tail while D4 and
        # marker permutations still diversify the scene deterministically.
        specs = [
            (1, 1, 3, 4),
            (1, side - 4, 4, 3),
            (side - 6, (side - 5) // 2, 5, 5),
        ]
    else:  # pragma: no cover - validated before dispatch
        raise ValueError(profile)
    return h, w, specs


def _marker_sets(palette_profile: str, count: int) -> list[list[int]]:
    if count == 1:
        return [list(_SINGLE_PALETTES[palette_profile])]
    colors = list(_MULTI_PALETTES[palette_profile])
    patterns = ((0, 1, 2, 3), (2, 3, 4, 5), (0, 1, 4, 5))
    return [[colors[index] for index in patterns[i % len(patterns)]] for i in range(count)]


def _transform(grid: list[list[int]], name: str) -> list[list[int]]:
    if name == "identity":
        return [list(row) for row in grid]
    if name == "rotate_90":
        return [list(row) for row in zip(*grid[::-1])]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_270":
        return _transform(_transform(_transform(grid, "rotate_90"), "rotate_90"), "rotate_90")
    if name == "reflect_horizontal":
        return [list(row) for row in reversed(grid)]
    if name == "reflect_vertical":
        return [list(reversed(row)) for row in grid]
    if name == "reflect_main_diagonal":
        return [list(row) for row in zip(*grid)]
    if name == "reflect_anti_diagonal":
        return _transform(_transform(_transform(grid, "rotate_180"), "reflect_main_diagonal"), "identity")
    raise ValueError(name)


_D4 = (
    "identity",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "reflect_horizontal",
    "reflect_vertical",
    "reflect_main_diagonal",
    "reflect_anti_diagonal",
)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band_name(difficulty)
    effective = dict(overrides)
    effective.setdefault("scene_profile", schedule_profile(seed, sample_index, difficulty))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)
    layout_rng = ctx.draw_rng("layout")
    role_rng = ctx.draw_rng("marker_roles")
    h, w, specs = _profile_layout(profile, band, layout_rng)
    grid = _blank(h, w)
    color_sets = _marker_sets(palette_profile, len(specs))
    for (r1, c1, height, width), colors in zip(specs, color_sets):
        for r in range(r1, r1 + height):
            for c in range(c1, c1 + width):
                grid[r][c] = 5
        role_rng.shuffle(colors)
        r2, c2 = r1 + height - 1, c1 + width - 1
        marker_cells = (
            (r1 - 1, c1 - 1),
            (r1 - 1, c2 + 1),
            (r2 + 1, c1 - 1),
            (r2 + 1, c2 + 1),
        )
        for (r, c), color in zip(marker_cells, colors):
            grid[r][c] = color

    # Square profiles are diversified across all D4 orientations.  Odd-height
    # and odd-width profiles use only transforms that preserve their exact axis
    # identity; full D4 remains lawful as an external augmentation.
    if profile in {"odd_height", "odd_width"}:
        orientations = ("identity", "rotate_180", "reflect_horizontal", "reflect_vertical")
    else:
        orientations = _D4
    grid = _transform(grid, layout_rng.choice(orientations))
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": effective})
    if errors:  # fail loud: never emit a malformed teaching example
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


def _has_odd_dimension(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return any(rect["height"] % 2 or rect["width"] % 2 for rect in facts["rectangles"])


def _has_multiple_rectangles(grid: list[list[int]]) -> bool:
    return len(_facts(grid)["rectangles"]) >= 2


def _has_border_marker(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    h, w = len(grid), len(grid[0])
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in facts.get("marker_cells", ()))


def _has_non_4x4_rectangle(grid: list[list[int]]) -> bool:
    return any((rect["height"], rect["width"]) != (4, 4) for rect in _facts(grid)["rectangles"])


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "marker_erasure": lambda grid: bool(_facts(grid).get("marker_cells")),
    "odd_dimension_split": _has_odd_dimension,
    "multiple_rectangles": _has_multiple_rectangles,
}


def _rival_keep_markers(grid: list[list[int]]) -> list[list[int]]:
    return _apply_rule(grid, keep_markers=True)


def _rival_ceil_split(grid: list[list[int]]) -> list[list[int]]:
    return _apply_rule(grid, ceil_split=True)


def _rival_first_rectangle_only(grid: list[list[int]]) -> list[list[int]]:
    return _apply_rule(grid, first_only=True)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "keep_markers": _rival_keep_markers,
    "ceil_split": _rival_ceil_split,
    "first_rectangle_only": _rival_first_rectangle_only,
}
WITNESS_RIVALS = {
    "marker_erasure": ["keep_markers"],
    "odd_dimension_split": ["ceil_split"],
    "multiple_rectangles": ["first_rectangle_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"ceil_split": _rival_ceil_split}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    try:
        query_input = query["input"]
        if self_check(query_input):
            reasons.append("query input is outside the teaching grammar")
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"competitor {name!r} fits every demonstration")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reasons.append(f"lesson analysis failed: {type(exc).__name__}: {exc}")
    return sorted(set(reasons))


def mutation_impostors(grid: list[list[int]]) -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes for the focused regression test and audit."""
    facts = _facts(grid)
    if facts["errors"]:
        raise ValueError("canonical mutation source must be valid")
    first = facts["rectangles"][0]
    marker_cells = list(first["marker_cells"])
    impostors: list[tuple[str, list[list[int]]]] = []

    missing = [list(row) for row in grid]
    r, c = marker_cells[0]
    missing[r][c] = 0
    impostors.append(("missing_corner_marker", missing))

    duplicate = [list(row) for row in grid]
    r0, c0 = marker_cells[0]
    r1, c1 = marker_cells[1]
    duplicate[r1][c1] = duplicate[r0][c0]
    impostors.append(("duplicate_marker_color", duplicate))

    nonrect = [list(row) for row in grid]
    rr, cc, _r2, _c2 = first["bbox"]
    nonrect[rr][cc] = 0
    impostors.append(("nonrectangular_gray_component", nonrect))

    orphan = [list(row) for row in grid]
    used = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color != 5 and color not in used)
    location = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and (r, c) not in facts["marker_cells"]
    )
    orphan[location[0]][location[1]] = replacement
    impostors.append(("orphan_absent_feature_marker", orphan))

    shifted = [list(row) for row in grid]
    r, c = marker_cells[2]
    color = shifted[r][c]
    shifted[r][c] = 0
    target = next(
        (rr, cc)
        for rr in range(len(grid))
        for cc in range(len(grid[0]))
        if shifted[rr][cc] == 0 and (rr, cc) not in facts["marker_cells"]
    )
    shifted[target[0]][target[1]] = color
    impostors.append(("shifted_corner_marker", shifted))
    return impostors
