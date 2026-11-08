"""Semantic generator for ``579f1e2dcb4a`` — crop and pack components.

The pinned rule finds every nonzero 4-connected component, crops each component
to its bounding box, sorts the crops by the component's original ``(left, top)``
position, and packs them left-to-right, top-aligned, with one zero column between
adjacent crops.

The five-profile schedule mirrors the canonical dimensions and palettes.  The
palette-6 profiles deliberately include two same-colour components with the same
left edge but different top rows.  That canonical construction teaches both
4-connectivity and the rule's secondary top-row sort key instead of treating the
tie as a degenerate case.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "579f1e2dcb4a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "29c3632de610"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find nonzero 4-connected components, crop them, order by original left "
    "edge then top row, and pack the crops left-to-right with one zero column."
)

INVARIANTS = [
    "background is 0",
    "canonical dimensions and palette counts are preserved",
    "objects are nonzero 4-connected components, even when colors differ",
    "palette-6 scenes expose a same-left tie resolved by top row",
    "output crops are top-aligned and separated by exactly one zero column",
]

COUNTER_HYPOTHESES = [
    "split objects whenever their color changes",
    "merge diagonal contacts using 8-connectivity",
    "order components by top row instead of left edge",
    "order components by color",
    "reverse the left-to-right order",
    "replace sparse crops by solid rectangles",
    "bottom-align crops",
    "omit separator columns",
]

PROFILE_SPECS: dict[str, tuple[int, int, int]] = {
    "canonical_8x13_p6": (8, 13, 6),
    "canonical_9x12_p6": (9, 12, 6),
    "canonical_9x14_p7": (9, 14, 7),
    "canonical_10x15_p6": (10, 15, 6),
    "canonical_11x16_p7": (11, 16, 7),
}
PROFILE_NAMES = tuple(PROFILE_SPECS)
_PROFILE_BY_DIMS = {(height, width): name for name, (height, width, _) in PROFILE_SPECS.items()}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-profile deterministic canonical schedule",
        "valid": "canonical_8x13_p6|canonical_9x12_p6|canonical_9x14_p7|canonical_10x15_p6|canonical_11x16_p7",
    },
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
SCHEDULE_PROFILES = PROFILE_NAMES

# Motifs are (base-color cells, accent-color cells).  Every motif is a tight,
# sparse 4-connected crop and each color region is itself 4-connected.
_SMALL = (
    ((0, 0), (1, 0)),
    ((1, 1),),
)
_MEDIUM = (
    ((0, 0), (0, 1), (1, 1)),
    ((1, 2),),
)
_LARGE = (
    ((0, 0), (1, 0)),
    ((0, 2), (1, 1), (1, 2)),
)
# One color, but two 4-components.  The singleton is diagonal to the upper
# triomino and shares its left edge, exactly exposing 4-vs-8 connectivity and
# the secondary top-row ordering key.
_SPLIT = (
    ((0, 0), (0, 1), (1, 1)),
    ((2, 0),),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in PROFILE_NAMES:
        raise ValueError(
            f"override 'scene_profile'={profile!r} not in {PROFILE_NAMES}"
        )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every five consecutive indexes visit every canonical profile once."""
    del seed, difficulty
    return PROFILE_NAMES[int(sample_index) % len(PROFILE_NAMES)]


def _normalize_colored(
    base: Iterable[tuple[int, int]], accent: Iterable[tuple[int, int]]
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    base_cells = tuple(base)
    accent_cells = tuple(accent)
    cells = base_cells + accent_cells
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return (
        tuple(sorted((row - top, col - left) for row, col in base_cells)),
        tuple(sorted((row - top, col - left) for row, col in accent_cells)),
    )


def _reflect_motif(motif, *, flip_rows: bool, flip_cols: bool):
    base, accent = motif
    cells = base + accent
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1

    def reflect(cell: tuple[int, int]) -> tuple[int, int]:
        row, col = cell
        if flip_rows:
            row = height - 1 - row
        if flip_cols:
            col = width - 1 - col
        return row, col

    return _normalize_colored(map(reflect, base), map(reflect, accent))


def _motif_dims(motif) -> tuple[int, int]:
    cells = motif[0] + motif[1]
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _random_composition(total: int, parts: int, rng) -> list[int]:
    """Deterministically split ``total`` into ``parts`` nonnegative integers."""
    if total < 0 or parts <= 0:
        raise ValueError("invalid composition request")
    remaining = total
    result: list[int] = []
    for slots_left in range(parts, 1, -1):
        value = rng.randint(0, remaining)
        result.append(value)
        remaining -= value
    result.append(remaining)
    rng.shuffle(result)
    return result


def _place_colored(
    grid: list[list[int]],
    motif,
    origin: tuple[int, int],
    colors: tuple[int, int],
) -> None:
    row0, col0 = origin
    for cells, color in zip(motif, colors):
        for dr, dc in cells:
            row, col = row0 + dr, col0 + dc
            if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
                raise AssertionError("motif escaped its canonical profile")
            if grid[row][col] != 0:
                raise AssertionError("motif placement overlap")
            grid[row][col] = color


def _place_split(
    grid: list[list[int]], origin: tuple[int, int], color: int
) -> None:
    row0, col0 = origin
    for cells in _SPLIT:
        for dr, dc in cells:
            row, col = row0 + dr, col0 + dc
            if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
                raise AssertionError("split motif escaped its canonical profile")
            if grid[row][col] != 0:
                raise AssertionError("split motif placement overlap")
            grid[row][col] = color


def _group_tops(height: int, group_heights: list[int], band: str) -> list[int]:
    top = [0, 0, 0]
    middle = [(height - item_height) // 2 for item_height in group_heights]
    bottom = [height - item_height for item_height in group_heights]
    if band == "easy":
        return [bottom[0], top[1], middle[2]]
    if band == "medium":
        return [middle[0], bottom[1], top[2]]
    return [bottom[0], middle[1], top[2]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_overrides(overrides)
    scheduled = schedule_profile(int(seed), int(sample_index), band)
    effective = dict(overrides)
    if effective.get("scene_profile") is None:
        effective["scene_profile"] = scheduled

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    height, width, palette_count = PROFILE_SPECS[profile]
    rng = ctx.draw_rng("layout")

    colors = sorted(rng.sample(range(1, 10), palette_count - 1))
    if palette_count == 7:
        group_colors: list[tuple[int, ...]] = [
            (colors[4], colors[5]),
            (colors[0], colors[1]),
            (colors[2], colors[3]),
        ]
        motifs = [_SMALL, _MEDIUM, _LARGE]
        group_kinds = ["colored", "colored", "colored"]
    else:
        group_colors = [
            (colors[3], colors[4]),
            (colors[0], colors[1]),
            (colors[2],),
        ]
        second = _MEDIUM if rng.randrange(2) == 0 else _LARGE
        motifs = [_SMALL, second, _SPLIT]
        group_kinds = ["colored", "colored", "split"]

    transformed = []
    for index, motif in enumerate(motifs):
        if group_kinds[index] == "split":
            transformed.append(motif)
            continue
        transformed.append(
            _reflect_motif(
                motif,
                flip_rows=bool(rng.randrange(2)),
                flip_cols=bool(rng.randrange(2)),
            )
        )

    group_dims = [
        (3, 2) if kind == "split" else _motif_dims(motif)
        for kind, motif in zip(group_kinds, transformed)
    ]
    total_width = sum(item_width for _, item_width in group_dims) + 2
    margin_left, gap_extra_1, gap_extra_2, _margin_right = _random_composition(
        width - total_width, 4, rng
    )
    lefts = [
        margin_left,
        margin_left + group_dims[0][1] + 1 + gap_extra_1,
        margin_left
        + group_dims[0][1]
        + 1
        + gap_extra_1
        + group_dims[1][1]
        + 1
        + gap_extra_2,
    ]
    tops = _group_tops(height, [item[0] for item in group_dims], band)

    grid = full_grid(height, width, 0)
    for kind, motif, top, left, palette in zip(
        group_kinds, transformed, tops, lefts, group_colors
    ):
        if kind == "split":
            _place_split(grid, (top, left), palette[0])
        else:
            _place_colored(grid, motif, (top, left), (palette[0], palette[1]))

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["scene_profile"] != profile:
        raise ValueError(
            f"internal axis mismatch: requested {profile!r}, "
            f"observed {observed['scene_profile']!r}"
        )
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and Python rule mirror (Racket remains the authority)
# ---------------------------------------------------------------------------


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for row_index, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(char) for char in row]
            except ValueError:
                return None, [f"row {row_index} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {row_index} is not a sequence"]
        if not values:
            return None, ["grid rows must be nonempty"]
        if width is None:
            width = len(values)
        elif len(values) != width:
            return None, ["ragged grid"]
        for col_index, value in enumerate(values):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return None, [
                    f"invalid ARC color at ({row_index},{col_index}): {value!r}"
                ]
        rows.append(values)
    return rows, []


def _component_records(
    grid: list[list[int]],
    *,
    connectivity: int = 4,
    same_color: bool = False,
) -> list[dict[str, Any]]:
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            seed_color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for dr, dc in directions:
                    next_row, next_col = current_row + dr, current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    value = grid[next_row][next_col]
                    if value == 0 or (same_color and value != seed_color):
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [values[left : right + 1] for values in grid[top : bottom + 1]]
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": frozenset(grid[r][c] for r, c in cells),
                    "top": top,
                    "left": left,
                    "bottom": bottom,
                    "right": right,
                    "height": bottom - top + 1,
                    "width": right - left + 1,
                    "size": len(cells),
                    "crop": crop,
                }
            )
    return result


def semantic_observables(grid: Any) -> dict[str, Any]:
    rows, errors = _coerce_grid(grid)
    if rows is None:
        return {"errors": errors}
    height, width = len(rows), len(rows[0])
    profile = _PROFILE_BY_DIMS.get((height, width))
    return {
        "errors": [],
        "grid": rows,
        "height": height,
        "width": width,
        "palette": frozenset(value for row in rows for value in row),
        "scene_profile": profile,
        "components": _component_records(rows),
    }


def _pack_components(
    components: list[dict[str, Any]],
    order: list[int],
    *,
    gap: int = 1,
    alignment: str = "top",
    solid_bbox: bool = False,
) -> list[list[int]]:
    if not components:
        return [[0]]
    if alignment not in ("top", "bottom"):
        raise ValueError(f"unknown alignment: {alignment}")
    selected = [components[index] for index in order]
    out_height = max(component["height"] for component in selected)
    out_width = sum(component["width"] for component in selected) + gap * (
        len(selected) - 1
    )
    output = full_grid(out_height, out_width, 0)
    left = 0
    for component in selected:
        crop = component["crop"]
        top = 0 if alignment == "top" else out_height - component["height"]
        fill = min(component["colors"])
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                if solid_bbox and value == 0:
                    value = fill
                if value != 0:
                    output[top + row][left + col] = value
        left += component["width"] + gap
    return output


def _valid_components(grid: Any, *, connectivity: int = 4, same_color=False):
    rows, errors = _coerce_grid(grid)
    if rows is None:
        raise ValueError("; ".join(errors))
    return _component_records(
        rows, connectivity=connectivity, same_color=same_color
    )


def _authority_order(components: list[dict[str, Any]]) -> list[int]:
    return sorted(
        range(len(components)),
        key=lambda index: (
            components[index]["left"],
            components[index]["top"],
        ),
    )


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure-Python mirror for tests; the pinned Racket rule is authoritative."""
    components = _valid_components(grid)
    return _pack_components(components, _authority_order(components))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors

    profile = facts["scene_profile"]
    if profile is None:
        errors.append(
            f"dimensions are outside canonical profiles: "
            f"{facts['height']}x{facts['width']}"
        )
        return errors
    expected_palette = PROFILE_SPECS[profile][2]
    palette = facts["palette"]
    if 0 not in palette:
        errors.append("background color 0 must be visible")
    if len(palette) != expected_palette:
        errors.append(
            f"profile {profile} requires {expected_palette} visible colors, "
            f"found {len(palette)}"
        )

    components = facts["components"]
    expected_components = 4 if expected_palette == 6 else 3
    if len(components) != expected_components:
        errors.append(
            f"profile {profile} requires {expected_components} nonzero "
            f"4-components, found {len(components)}"
        )
        return errors

    for component in components:
        if not 1 <= len(component["colors"]) <= 2:
            errors.append("each component must use one or two colors")
        if component["height"] > 2 or component["width"] > 3:
            errors.append(
                "component crop exceeds canonical 2x3 morphology: "
                f"{component['height']}x{component['width']}"
            )
        if not 1 <= component["size"] <= 5:
            errors.append(
                f"component has {component['size']} cells; expected 1..5"
            )

    multicolor = [component for component in components if len(component["colors"]) == 2]
    expected_multicolor = expected_palette - 4
    if len(multicolor) != expected_multicolor:
        errors.append(
            f"profile {profile} requires {expected_multicolor} multicolor "
            f"components, found {len(multicolor)}"
        )

    lefts = [component["left"] for component in components]
    if expected_palette == 7:
        if len(set(lefts)) != 3:
            errors.append("palette-7 components must have distinct left edges")
        if sorted(component["size"] for component in components) != [3, 4, 5]:
            errors.append("palette-7 component sizes must be 3, 4, and 5")
    else:
        monochrome = [
            component for component in components if len(component["colors"]) == 1
        ]
        if len(monochrome) != 2:
            errors.append("palette-6 scenes require two monochrome components")
        else:
            mono_colors = [next(iter(component["colors"])) for component in monochrome]
            if len(set(mono_colors)) != 1:
                errors.append(
                    "palette-6 monochrome components must share one color"
                )
            if sorted(component["size"] for component in monochrome) != [1, 3]:
                errors.append(
                    "palette-6 tied monochrome components must have sizes 1 and 3"
                )
            if len({component["left"] for component in monochrome}) != 1:
                errors.append(
                    "palette-6 monochrome components must share a left edge"
                )
            if len({component["top"] for component in monochrome}) != 2:
                errors.append(
                    "palette-6 same-left components must have distinct top rows"
                )
        if len(set(lefts)) != 3:
            errors.append(
                "palette-6 scenes require exactly one duplicated left edge"
            )
        multi_sizes = sorted(component["size"] for component in multicolor)
        if len(multi_sizes) == 2 and (
            multi_sizes[0] != 3 or multi_sizes[1] not in (4, 5)
        ):
            errors.append(
                "palette-6 multicolor component sizes must be 3 and 4-or-5"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked profile check used by the empirical-manifold gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    reasons = self_check(grid)
    if reasons:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(reasons))
    facts = semantic_observables(grid)
    return {"scene_profile": facts["scene_profile"]}


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["height"],
        facts["width"],
        len(facts["palette"]),
        facts["scene_profile"],
        tuple(
            (
                component["left"],
                component["top"],
                component["height"],
                component["width"],
                component["size"],
                tuple(sorted(component["colors"])),
            )
            for component in sorted(
                facts["components"], key=lambda item: (item["left"], item["top"])
            )
        ),
    )


# ---------------------------------------------------------------------------
# Named rivals, witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------


def _rival_monochrome_components(grid):
    components = _valid_components(grid, same_color=True)
    return _pack_components(components, _authority_order(components))


def _rival_eight_connected(grid):
    components = _valid_components(grid, connectivity=8)
    return _pack_components(components, _authority_order(components))


def _rival_top_then_left(grid):
    components = _valid_components(grid)
    order = sorted(
        range(len(components)),
        key=lambda index: (
            components[index]["top"],
            components[index]["left"],
        ),
    )
    return _pack_components(components, order)


def _rival_right_to_left(grid):
    components = _valid_components(grid)
    order = sorted(
        range(len(components)),
        key=lambda index: (
            -components[index]["left"],
            components[index]["top"],
        ),
    )
    return _pack_components(components, order)


def _rival_color_order(grid):
    components = _valid_components(grid)
    order = sorted(
        range(len(components)),
        key=lambda index: (
            min(components[index]["colors"]),
            components[index]["left"],
            components[index]["top"],
        ),
    )
    return _pack_components(components, order)


def _rival_solid_bbox(grid):
    components = _valid_components(grid)
    return _pack_components(
        components, _authority_order(components), solid_bbox=True
    )


def _rival_bottom_align(grid):
    components = _valid_components(grid)
    return _pack_components(
        components, _authority_order(components), alignment="bottom"
    )


def _rival_no_gap(grid):
    components = _valid_components(grid)
    return _pack_components(components, _authority_order(components), gap=0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "monochrome_components": _rival_monochrome_components,
    "eight_connected_components": _rival_eight_connected,
    "top_then_left_order": _rival_top_then_left,
    "right_to_left_order": _rival_right_to_left,
    "color_ascending": _rival_color_order,
    "solid_bbox_crops": _rival_solid_bbox,
    "bottom_align": _rival_bottom_align,
    "omit_gap_columns": _rival_no_gap,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Any]] = {}


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _rival_disagrees(name: str, grid: Any) -> bool:
    return not _grids_equal(rule_mirror(grid), SEMANTIC_RIVALS[name](grid))


def _profile_is(name: str, grid: Any) -> bool:
    return semantic_observables(grid).get("scene_profile") == name


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    **{
        f"profile_{name}": (
            lambda grid, expected=name: _profile_is(expected, grid)
        )
        for name in PROFILE_NAMES
    },
    "multicolor_connectivity_visible": lambda grid: _rival_disagrees(
        "monochrome_components", grid
    ),
    "four_connectivity_visible": lambda grid: _rival_disagrees(
        "eight_connected_components", grid
    ),
    "left_before_top_visible": lambda grid: _rival_disagrees(
        "top_then_left_order", grid
    ),
    "ascending_left_visible": lambda grid: _rival_disagrees(
        "right_to_left_order", grid
    ),
    "color_not_output_order": lambda grid: _rival_disagrees(
        "color_ascending", grid
    ),
    "crop_texture_preserved": lambda grid: _rival_disagrees(
        "solid_bbox_crops", grid
    ),
    "top_alignment_visible": lambda grid: _rival_disagrees(
        "bottom_align", grid
    ),
    "one_column_gaps_visible": lambda grid: _rival_disagrees(
        "omit_gap_columns", grid
    ),
}
BRANCH_WITNESSES = {f"profile_{name}" for name in PROFILE_NAMES}
WITNESS_RIVALS = {
    "multicolor_connectivity_visible": ["monochrome_components"],
    "four_connectivity_visible": ["eight_connected_components"],
    "left_before_top_visible": ["top_then_left_order"],
    "ascending_left_visible": ["right_to_left_order"],
    "color_not_output_order": ["color_ascending"],
    "crop_texture_preserved": ["solid_bbox_crops"],
    "top_alignment_visible": ["bottom_align"],
    "one_column_gaps_visible": ["omit_gap_columns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a declared plausible wrong rule survives its demos."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} outside rule grammar: {exc}")
            continue
        if not _grids_equal(expected, pair.get("output")):
            reasons.append(f"demo {index} output disagrees with pinned rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query outside rule grammar: {exc}")
        return reasons

    if "output" in query and not _grids_equal(query_answer, query["output"]):
        reasons.append("query output disagrees with pinned rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                _grids_equal(competitor(pair["input"]), pair.get("output"))
                for pair in demos
            )
            if survives and not _grids_equal(
                competitor(query["input"]), query_answer
            ):
                reasons.append(
                    f"competitor '{name}' fits every demo but changes the query answer"
                )
        except (KeyError, ValueError) as exc:
            reasons.append(f"competitor '{name}' raised: {exc}")
    return reasons
