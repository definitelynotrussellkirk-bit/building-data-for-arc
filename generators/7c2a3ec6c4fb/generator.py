"""Generator for ARC task cd3c21df / 7c2a3ec6c4fb.

The input contains several separated colored objects.  Every exact bounding-box
crop occurs twice except one crop, which occurs once.  The output is that lone
crop.  Generated scenes deliberately include at least two repeated pattern
classes and counterexamples to color-signature and geometry-only shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at


Grid = list[list[int]]
Pattern = tuple[tuple[int, ...], ...]

GENERATOR_ID = "7c2a3ec6c4fb"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "38ad2c645d79"

SUMMARY = (
    "Square 0-background scenes contain five, seven, or nine separated colored "
    "objects. Exact bbox-cropped patterns form two to four duplicated pairs plus "
    "one singleton. The singleton may be monochrome or multicolor and shares "
    "coarse size, palette, histogram, or geometry signatures with a repeated "
    "class, so low-complexity uniqueness shortcuts are insufficient. Sparse "
    "scenes use free placement and include canonical-style crops up to length "
    "five. About one third of answers require diagonal connectivity, with a "
    "repeated diagonal class preventing connectivity-only selection. Output the "
    "exact colored crop whose full pattern occurs once."
)

INVARIANTS = [
    "background is 0 on an 11x11, 12x12, or 13x13 square grid",
    "all nonzero objects are 8-connected and occupy disjoint bounding boxes",
    "both orthogonal and diagonal-only answer connectivity have deliberate support",
    "there are two through four repeated exact crop classes, each appearing twice",
    "exactly one exact colored crop appears once",
    "the singleton may use one or two colors and has no exclusive scene color",
    "five-object scenes may contain canonical-style lines of length four or five",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCENE_PROFILES = (
    "square11_c3",
    "square12_c4",
    "square13_c3",
    "square13_c4",
)
PATTERN_PROFILES = (
    "color_swap",
    "shape_shift",
    "mixed_signature",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng canonical morphology profile",
        "valid": "square11_c3|square12_c4|square13_c3|square13_c4",
    },
    "n_pairs": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "pattern_profile": {
        "type": "str",
        "default": "rng exact-pattern counterexample profile",
        "valid": "color_swap|shape_shift|mixed_signature",
    },
}

_PROFILE_SPECS = {
    "square11_c3": (11, 3),
    "square12_c4": (12, 4),
    "square13_c3": (13, 3),
    "square13_c4": (13, 4),
}
_PROFILE_BY_OBSERVABLES = {
    value: name for name, value in _PROFILE_SPECS.items()
}
_KING_DELTAS = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_ORTHOGONAL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Reviewed connected masks. Compact masks fit the dense 3x3 placement zones;
# five-object scenes may also use canonical-style straight crops of length 4 or 5.
# The first class (mutated into the singleton) always has at least four cells.
_SHAPE_MASKS: tuple[tuple[tuple[int, ...], ...], ...] = (
    ((1, 1, 1),),
    ((1, 1, 1, 1),),
    ((1, 1, 1, 1, 1),),
    ((1,), (1,), (1,)),
    ((1,), (1,), (1,), (1,)),
    ((1,), (1,), (1,), (1,), (1,)),
    ((1, 1), (1, 1)),
    ((1, 1, 1), (0, 1, 0)),
    ((1, 0), (1, 1), (1, 0)),
    ((1, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (1, 1, 0)),
    ((1, 1, 1), (1, 0, 0)),
    ((1, 1, 1), (0, 0, 1)),
    ((1, 0, 1), (1, 1, 1)),
    ((1, 1, 1), (1, 0, 1)),
    ((0, 1, 0), (1, 1, 1), (0, 1, 0)),
    ((1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 1, 1), (1, 1, 1)),
    ((1, 1), (1, 1), (1, 1)),
    ((1, 1, 1), (1, 1, 0), (0, 1, 0)),
    ((0, 1, 0), (1, 1, 1), (1, 1, 0)),
    ((1, 1, 1), (1, 0, 1), (0, 1, 0)),
    ((1, 1, 1), (1, 0, 1), (1, 1, 1)),
    # Tight diagonal-bridge masks: one 8-component, several 4-components.
    # Include both handednesses so a diagonal answer is not orientation-specific.
    ((1, 1, 0), (0, 0, 1), (0, 1, 1)),
    ((0, 1, 1), (1, 0, 0), (1, 1, 0)),
    ((1, 1, 0), (0, 0, 1), (1, 1, 0)),
    ((0, 1, 1), (1, 0, 0), (0, 1, 1)),
    ((1, 0, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 0, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 1, 0), (0, 1, 0), (0, 0, 1)),
    ((0, 1, 1), (0, 1, 0), (1, 0, 0)),
)
_COMPACT_SHAPE_MASKS = tuple(
    mask for mask in _SHAPE_MASKS if len(mask) <= 3 and len(mask[0]) <= 3
)
_MUTABLE_MASKS = tuple(
    mask
    for mask in _SHAPE_MASKS
    if sum(sum(row) for row in mask) >= 4
)
_COMPACT_MUTABLE_MASKS = tuple(
    mask for mask in _MUTABLE_MASKS if len(mask) <= 3 and len(mask[0]) <= 3
)
_SHIFTABLE_MASKS = tuple(
    mask
    for mask in _MUTABLE_MASKS
    if any(value == 0 for row in mask for value in row)
)
_COMPACT_SHIFTABLE_MASKS = tuple(
    mask for mask in _SHIFTABLE_MASKS if len(mask) <= 3 and len(mask[0]) <= 3
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    scene_profile = overrides.get("scene_profile")
    if scene_profile is not None and scene_profile not in SCENE_PROFILES:
        raise ValueError(
            "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
        )
    n_pairs = overrides.get("n_pairs")
    if n_pairs is not None and (
        type(n_pairs) is not int or not 2 <= n_pairs <= 4
    ):
        raise ValueError("n_pairs must be an integer in [2, 4]")
    pattern_profile = overrides.get("pattern_profile")
    if pattern_profile is not None and pattern_profile not in PATTERN_PROFILES:
        raise ValueError(
            "pattern_profile must be one of " + ", ".join(PATTERN_PROFILES)
        )


def _mask_cells(mask: tuple[tuple[int, ...], ...]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(mask)
        for col, value in enumerate(values)
        if value
    ]


def _pattern_cells(pattern: Pattern) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value
    ]


def _geometry(pattern: Pattern) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value != 0) for value in row) for row in pattern)


def _color_histogram(pattern: Pattern) -> tuple[tuple[int, int], ...]:
    counts = Counter(
        value for row in pattern for value in row if value != 0
    )
    return tuple(sorted(counts.items()))


def _color_signature(pattern: Pattern) -> frozenset[int]:
    return frozenset(value for row in pattern for value in row if value != 0)


def _cell_count(pattern: Pattern) -> int:
    return sum(value != 0 for row in pattern for value in row)


def _colored_pattern(
    mask: tuple[tuple[int, ...], ...],
    colors: tuple[int, ...],
    rng,
    *,
    force_multicolor: bool = False,
) -> Pattern:
    cells = _mask_cells(mask)
    if not cells:
        raise ValueError("shape mask must contain a cell")
    chosen = tuple(dict.fromkeys(colors))
    if not chosen:
        raise ValueError("at least one color is required")
    if force_multicolor and len(chosen) < 2:
        raise ValueError("force_multicolor requires at least two colors")

    assignments: dict[tuple[int, int], int] = {}
    shuffled = cells[:]
    rng.shuffle(shuffled)
    if force_multicolor:
        # A majority color plus at least one minority cell makes color-swap and
        # histogram-preserving mutations observable and deterministic.
        assignments[shuffled[0]] = chosen[1]
        for cell in shuffled[1:]:
            assignments[cell] = chosen[0]
    else:
        for index, cell in enumerate(shuffled):
            assignments[cell] = chosen[index % len(chosen)]

    return tuple(
        tuple(assignments.get((row, col), 0) for col in range(len(mask[0])))
        for row in range(len(mask))
    )


def _connected4(pattern: Pattern) -> bool:
    cells = {
        (row, col)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _ORTHOGONAL_DELTAS:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _fills_bbox(pattern: Pattern) -> bool:
    occupied = [
        (row, col)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value
    ]
    if not occupied:
        return False
    rows = [row for row, _ in occupied]
    cols = [col for _, col in occupied]
    return (
        min(rows) == 0
        and min(cols) == 0
        and max(rows) == len(pattern) - 1
        and max(cols) == len(pattern[0]) - 1
    )


def _swap_colors_candidate(pattern: Pattern, forbidden: set[Pattern], rng) -> Pattern:
    cells = _pattern_cells(pattern)
    pairs = [
        (left, right)
        for index, left in enumerate(cells)
        for right in cells[index + 1 :]
        if left[2] != right[2]
    ]
    rng.shuffle(pairs)
    for left, right in pairs:
        rows = [list(row) for row in pattern]
        rows[left[0]][left[1]], rows[right[0]][right[1]] = (
            rows[right[0]][right[1]],
            rows[left[0]][left[1]],
        )
        candidate = tuple(tuple(row) for row in rows)
        if candidate not in forbidden:
            return candidate
    raise ValueError("no color-swap mutation is available")


def _shape_shift_candidate(pattern: Pattern, forbidden: set[Pattern], rng) -> Pattern:
    occupied = _pattern_cells(pattern)
    empty = [
        (row, col)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value == 0
    ]
    candidates = [
        (source, target)
        for source in occupied
        for target in empty
    ]
    rng.shuffle(candidates)
    for (source_row, source_col, color), (target_row, target_col) in candidates:
        rows = [list(row) for row in pattern]
        rows[source_row][source_col] = 0
        rows[target_row][target_col] = color
        candidate = tuple(tuple(row) for row in rows)
        if (
            candidate not in forbidden
            and len(_components8(candidate)) == 1
            # Preserve the sampled connectivity stratum. Otherwise shape_shift
            # erases diagonal answers or makes the singleton uniquely diagonal.
            and _connected4(candidate) == _connected4(pattern)
            and _fills_bbox(candidate)
        ):
            return candidate
    raise ValueError("no bbox-preserving shape mutation is available")


def _mixed_signature_candidate(
    pattern: Pattern, forbidden: set[Pattern], rng
) -> Pattern:
    histogram = Counter(
        value for row in pattern for value in row if value
    )
    sources = [color for color, count in histogram.items() if count >= 2]
    candidates = [
        (row, col, old_color, new_color)
        for row, values in enumerate(pattern)
        for col, old_color in enumerate(values)
        if old_color in sources
        for new_color in histogram
        if new_color != old_color
    ]
    rng.shuffle(candidates)
    for row, col, _old_color, new_color in candidates:
        rows = [list(values) for values in pattern]
        rows[row][col] = new_color
        candidate = tuple(tuple(values) for values in rows)
        if (
            candidate not in forbidden
            and _color_signature(candidate) == _color_signature(pattern)
            and _color_histogram(candidate) != _color_histogram(pattern)
        ):
            return candidate
    raise ValueError("no mixed-signature mutation is available")


def _derive_singleton(
    base: Pattern,
    profile: str,
    forbidden: set[Pattern],
    rng,
) -> Pattern:
    if profile == "color_swap":
        return _swap_colors_candidate(base, forbidden, rng)
    if profile == "shape_shift":
        return _shape_shift_candidate(base, forbidden, rng)
    if profile == "mixed_signature":
        return _mixed_signature_candidate(base, forbidden, rng)
    raise ValueError(f"unknown pattern profile: {profile}")


def _pattern_profile_candidates(
    singleton: Pattern,
    repeated_patterns: list[Pattern],
) -> set[str]:
    """Return every profile relation supported by a repeated class.

    Generation rejects ambiguous scenes rather than letting an unrelated class
    shadow the requested provenance when ``observe_overrides`` re-derives it.
    """
    candidates: set[str] = set()
    singleton_geometry = _geometry(singleton)
    singleton_histogram = _color_histogram(singleton)
    singleton_colors = _color_signature(singleton)
    singleton_dimensions = (len(singleton), len(singleton[0]))

    for pattern in repeated_patterns:
        if pattern == singleton:
            continue
        geometry = _geometry(pattern)
        histogram = _color_histogram(pattern)
        colors = _color_signature(pattern)
        dimensions = (len(pattern), len(pattern[0]))
        if geometry == singleton_geometry and histogram == singleton_histogram:
            candidates.add("color_swap")
        if (
            geometry != singleton_geometry
            and histogram == singleton_histogram
            and dimensions == singleton_dimensions
        ):
            candidates.add("shape_shift")
        if (
            geometry == singleton_geometry
            and colors == singleton_colors
            and histogram != singleton_histogram
        ):
            candidates.add("mixed_signature")
    return candidates


def _build_patterns(
    palette: tuple[int, ...],
    n_pairs: int,
    profile: str,
    rng,
    *,
    allow_large: bool = False,
) -> tuple[list[Pattern], Pattern]:
    if len(palette) not in (3, 4):
        raise ValueError("scene palette must contain three or four colors")

    shape_masks = _SHAPE_MASKS if allow_large else _COMPACT_SHAPE_MASKS
    mutable_masks = _MUTABLE_MASKS if allow_large else _COMPACT_MUTABLE_MASKS
    shiftable_masks = (
        _SHIFTABLE_MASKS if allow_large else _COMPACT_SHIFTABLE_MASKS
    )

    # Select once, outside retries: rejection must not silently suppress the
    # harder connectivity stratum. This is a latent draw, not a public override.
    diagonal_base = rng.randrange(3) == 0
    base_pool = shiftable_masks if profile == "shape_shift" else mutable_masks
    base_pool = tuple(mask for mask in base_pool if _connected4(mask) != diagonal_base)

    for _attempt in range(256):
        patterns: list[Pattern] = []

        # Shape-shift scenes sometimes use a monochrome base.  This covers the
        # canonical one-color answers while preserving a repeated same-color
        # class, so color rarity still cannot identify the singleton.
        monochrome_base = profile == "shape_shift" and rng.choice((False, True))
        base_mask = rng.choice(base_pool)
        base_colors = (palette[0],) if monochrome_base else (palette[0], palette[1])
        base = _colored_pattern(
            base_mask,
            base_colors,
            rng,
            force_multicolor=not monochrome_base,
        )
        patterns.append(base)

        for index in range(1, n_pairs):
            # Class 1 carries every palette color not already used by the base.
            # Later classes add morphology/color combinations, but all their
            # colors remain safe because each class is duplicated.
            if index == 1:
                used_by_base = _color_signature(base)
                class_colors = tuple(
                    color for color in palette if color not in used_by_base
                ) or (palette[0],)
                if len(class_colors) == 1:
                    companion = next(
                        color for color in palette if color != class_colors[0]
                    )
                    class_colors = (class_colors[0], companion)
            else:
                count = rng.randint(1, min(3, len(palette)))
                class_colors = tuple(rng.sample(list(palette), count))

            for _inner in range(128):
                mask = rng.choice(shape_masks)
                candidate = _colored_pattern(
                    mask,
                    class_colors,
                    rng,
                    force_multicolor=False,
                )
                if candidate not in patterns:
                    patterns.append(candidate)
                    break
            else:
                break
        if len(patterns) != n_pairs:
            continue

        used = set().union(*(_color_signature(pattern) for pattern in patterns))
        if used != set(palette):
            continue

        forbidden = set(patterns)
        try:
            singleton = _derive_singleton(base, profile, forbidden, rng)
        except ValueError:
            continue
        if singleton in forbidden:
            continue
        if _pattern_profile_candidates(singleton, patterns) != {profile}:
            continue
        return patterns, singleton

    raise RuntimeError("could not construct distinct repeated/singleton patterns")


def _pattern_entries(
    repeated: list[Pattern], singleton: Pattern
) -> list[tuple[str, Pattern]]:
    entries: list[tuple[str, Pattern]] = [("singleton", singleton)]
    for index, pattern in enumerate(repeated):
        entries.extend(((f"pair_{index}", pattern), (f"pair_{index}", pattern)))
    return entries


def _slot_origins(size: int) -> tuple[tuple[int, int], ...]:
    starts = (0, (size - 3) // 2, size - 3)
    return tuple((row, col) for row in starts for col in starts)


def _place_lattice(
    size: int,
    entries: list[tuple[str, Pattern]],
    rng,
) -> Grid:
    shuffled = entries[:]
    rng.shuffle(shuffled)
    slots = list(_slot_origins(size))
    rng.shuffle(slots)
    slots = slots[: len(shuffled)]
    grid = full_grid(size, size, 0)
    for (_label, pattern), (zone_row, zone_col) in zip(shuffled, slots):
        height = len(pattern)
        width = len(pattern[0])
        if height > 3 or width > 3:
            raise ValueError("lattice placement only supports crops up to 3x3")
        row = zone_row + rng.randint(0, 3 - height)
        col = zone_col + rng.randint(0, 3 - width)
        paint_at(grid, row, col, _pattern_cells(pattern))
    return grid


def _place_free(
    size: int,
    entries: list[tuple[str, Pattern]],
    rng,
) -> Grid:
    prepared = [
        (
            label,
            pattern,
            len(pattern),
            len(pattern[0]),
            [(row, col) for row, col, _value in _pattern_cells(pattern)],
        )
        for label, pattern in entries
    ]
    for _attempt in range(256):
        ranked = [(rng.random(), item) for item in prepared]
        ranked.sort(
            key=lambda item: (
                -(item[1][2] * item[1][3]),
                -max(item[1][2], item[1][3]),
                item[0],
            )
        )
        placed_boxes: list[tuple[int, int, int, int]] = []
        blocked_cells: set[tuple[int, int]] = set()
        placements: list[tuple[Pattern, int, int]] = []
        failed = False

        for _rank, (_label, pattern, height, width, relative_cells) in ranked:
            candidates = [
                (row, col)
                for row in range(size - height + 1)
                for col in range(size - width + 1)
            ]
            rng.shuffle(candidates)
            selected = None
            for row, col in candidates:
                bbox = (row, col, row + height - 1, col + width - 1)
                if any(_boxes_overlap(bbox, other) for other in placed_boxes):
                    continue
                cells = {
                    (row + cell_row, col + cell_col)
                    for cell_row, cell_col in relative_cells
                }
                if cells & blocked_cells:
                    continue
                selected = (row, col, bbox, cells)
                break

            if selected is None:
                failed = True
                break

            row, col, bbox, cells = selected
            placed_boxes.append(bbox)
            placements.append((pattern, row, col))
            for cell_row, cell_col in cells:
                blocked_cells.add((cell_row, cell_col))
                for dr, dc in _KING_DELTAS:
                    neighbor = (cell_row + dr, cell_col + dc)
                    if 0 <= neighbor[0] < size and 0 <= neighbor[1] < size:
                        blocked_cells.add(neighbor)

        if failed:
            continue

        grid = full_grid(size, size, 0)
        for pattern, row, col in placements:
            paint_at(grid, row, col, _pattern_cells(pattern))
        return grid

    raise RuntimeError("could not freely place separated disjoint-bbox patterns")


def _place_patterns(
    size: int,
    repeated: list[Pattern],
    singleton: Pattern,
    rng,
) -> Grid:
    entries = _pattern_entries(repeated, singleton)
    if len(entries) <= 7:
        return _place_free(size, entries, rng)
    return _place_lattice(size, entries, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    n_pairs = ctx.draw_int_diff("n_pairs", 2, 4)
    pattern_profile = ctx.draw_choice("pattern_profile", PATTERN_PROFILES)
    size, palette_size = _PROFILE_SPECS[scene_profile]
    palette = ctx.draw_distinct_colors(
        "palette", n=palette_size, exclude={0}
    )
    pattern_rng = ctx.draw_rng("patterns")
    placement_rng = ctx.draw_rng("placement")
    repeated, singleton = _build_patterns(
        palette,
        n_pairs,
        pattern_profile,
        pattern_rng,
        allow_large=n_pairs == 2,
    )
    return _place_patterns(size, repeated, singleton, placement_rng)


def _is_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and all(isinstance(row, (list, tuple)) and bool(row) for row in grid)
        and len({len(row) for row in grid}) == 1
    )


def _components(grid: Grid, deltas) -> list[tuple[tuple[int, int], ...]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in deltas:
                    nxt = (current_row + dr, current_col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return components


def _components8(grid: Grid) -> list[tuple[tuple[int, int], ...]]:
    return _components(grid, _KING_DELTAS)


def _orthogonal_components(grid: Grid) -> Grid:
    """Canonical-perfect rival: use 4-neighbor rather than 8-neighbor objects."""
    if not _is_grid(grid):
        return []
    patterns = [_frozen_crop(grid, _bbox(cells))
                for cells in _components(grid, _ORTHOGONAL_DELTAS)]
    counts = Counter(patterns)
    # Match the reference's first-singleton scan order, not an arbitrary fallback.
    return [list(row) for row in next((p for p in patterns if counts[p] == 1), ())]


def _diagonal_connectivity_counterexample(grid) -> bool:
    analysis = _analyze(grid)
    return bool(not analysis["errors"]
                and not _connected4(analysis["output"])
                and _orthogonal_components(grid) != analysis["output"])


def _bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(grid: Grid, bbox: tuple[int, int, int, int]) -> Grid:
    row0, col0, row1, col1 = bbox
    return [
        list(grid[row][col0 : col1 + 1])
        for row in range(row0, row1 + 1)
    ]


def _frozen_crop(grid: Grid, bbox: tuple[int, int, int, int]) -> Pattern:
    return tuple(tuple(row) for row in _crop(grid, bbox))


def _boxes_overlap(
    left: tuple[int, int, int, int], right: tuple[int, int, int, int]
) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not _is_grid(grid):
        return {"valid": False, "errors": ["grid must be non-empty and rectangular"]}

    normalized = [list(row) for row in grid]
    height = len(normalized)
    width = len(normalized[0])
    if height != width or height not in (11, 12, 13):
        errors.append("grid must be square with side 11, 12, or 13")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in normalized
        for value in row
    ):
        errors.append("cells must be integer ARC colors in 0..9")
        return {"valid": False, "errors": errors}

    counts = Counter(value for row in normalized for value in row)
    if not counts or counts[0] != max(counts.values()):
        errors.append("zero must be a modal background color")
    nonzero_colors = frozenset(value for value in counts if value != 0)
    if len(nonzero_colors) not in (3, 4):
        errors.append("scene must use exactly three or four nonzero colors")

    raw_components = _components8(normalized)
    components: list[dict[str, Any]] = []
    for cells in raw_components:
        bbox = _bbox(cells)
        crop = _frozen_crop(normalized, bbox)
        component_set = set(cells)
        foreign = {
            (row, col)
            for row in range(bbox[0], bbox[2] + 1)
            for col in range(bbox[1], bbox[3] + 1)
            if normalized[row][col] != 0 and (row, col) not in component_set
        }
        if foreign:
            errors.append(
                "component bounding box contains a foreign nonzero cell"
            )
        components.append(
            {
                "cells": cells,
                "bbox": bbox,
                "crop": crop,
                "geometry": _geometry(crop),
                "colors": _color_signature(crop),
                "color_histogram": _color_histogram(crop),
                "cell_count": _cell_count(crop),
            }
        )

    bbox_overlap = any(
        _boxes_overlap(left["bbox"], right["bbox"])
        for index, left in enumerate(components)
        for right in components[index + 1 :]
    )
    if bbox_overlap:
        errors.append("object bounding boxes must not overlap")

    crop_counts = Counter(component["crop"] for component in components)
    singleton_crops = [crop for crop, count in crop_counts.items() if count == 1]
    repeated_crops = [crop for crop, count in crop_counts.items() if count == 2]
    other_multiplicities = [
        count for count in crop_counts.values() if count not in (1, 2)
    ]
    if len(singleton_crops) != 1:
        errors.append(
            f"need exactly one singleton exact crop, got {len(singleton_crops)}"
        )
    if len(repeated_crops) < 2:
        errors.append(
            f"need at least two repeated exact crop classes, got {len(repeated_crops)}"
        )
    if other_multiplicities:
        errors.append(
            "every non-singleton exact crop must appear exactly twice"
        )
    if len(components) not in (5, 7, 9):
        errors.append("scene must contain five, seven, or nine objects")

    singleton_component = None
    if len(singleton_crops) == 1:
        singleton_component = next(
            component
            for component in components
            if component["crop"] == singleton_crops[0]
        )
    other_colors: set[int] = set()
    if singleton_component is not None:
        for component in components:
            if component is not singleton_component:
                other_colors.update(component["colors"])
    singleton_has_exclusive_color = bool(
        singleton_component is not None
        and set(singleton_component["colors"]) - other_colors
    )

    scene_profile = _PROFILE_BY_OBSERVABLES.get(
        (height, len(nonzero_colors))
    )
    pattern_profile = _infer_pattern_profile(
        singleton_component, components, crop_counts
    )
    output = (
        [list(row) for row in singleton_crops[0]]
        if len(singleton_crops) == 1
        else None
    )
    return {
        "valid": not errors,
        "errors": errors,
        "grid": normalized,
        "components": components,
        "component_count": len(components),
        "multiplicities": tuple(sorted(crop_counts.values())),
        "singleton_pattern_classes": len(singleton_crops),
        "repeated_pattern_classes": len(repeated_crops),
        "bbox_overlap": bbox_overlap,
        "singleton": singleton_component,
        "singleton_has_exclusive_color": singleton_has_exclusive_color,
        "scene_profile": scene_profile,
        "pattern_profile": pattern_profile,
        "output": output,
    }


def _infer_pattern_profile(
    singleton: dict[str, Any] | None,
    components: list[dict[str, Any]],
    crop_counts: Counter,
) -> str | None:
    if singleton is None:
        return None
    repeated_patterns = [
        component["crop"]
        for component in components
        if crop_counts[component["crop"]] == 2
    ]
    candidates = _pattern_profile_candidates(
        singleton["crop"],
        repeated_patterns,
    )
    return next(iter(candidates)) if len(candidates) == 1 else None


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid):
    """Return [] exactly for scenes on the task's strict teaching manifold."""
    return self_check(grid)


def semantic_observables(grid):
    """Expose task-linked structure used by focused tests and semantic gates."""
    return _analyze(grid)


def observe_overrides(grid):
    """Recover every declared control from a generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe overrides: " + "; ".join(analysis["errors"])
        )
    return {
        "scene_profile": analysis["scene_profile"],
        "n_pairs": analysis["repeated_pattern_classes"],
        "pattern_profile": analysis["pattern_profile"],
    }


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("off-contract grid: " + "; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def _signature_shortcut(
    grid,
    signature: Callable[[dict[str, Any]], Any],
) -> Grid:
    analysis = _analyze(grid)
    components = analysis.get("components") or []
    if not components:
        return []
    signatures = [signature(component) for component in components]
    unique = [
        component
        for component, value in zip(components, signatures)
        if signatures.count(value) == 1
    ]
    target = unique[0] if len(unique) == 1 else components[0]
    return [list(row) for row in target["crop"]]


def _unique_color_signature(grid):
    return _signature_shortcut(grid, lambda component: component["colors"])


def _unique_geometry_signature(grid):
    return _signature_shortcut(grid, lambda component: component["geometry"])


def _unique_color_histogram(grid):
    return _signature_shortcut(
        grid, lambda component: component["color_histogram"]
    )


def _unique_geometry_and_colors(grid):
    return _signature_shortcut(
        grid,
        lambda component: (component["geometry"], component["colors"]),
    )


def _unique_bbox_and_histogram(grid):
    return _signature_shortcut(
        grid,
        lambda component: (
            (len(component["crop"]), len(component["crop"][0])),
            component["color_histogram"],
        ),
    )


def _shared_color_counterexample(grid) -> bool:
    analysis = _analyze(grid)
    return bool(
        not analysis["errors"]
        and not analysis["singleton_has_exclusive_color"]
        and _unique_color_signature(grid) != analysis["output"]
    )


def _same_geometry_counterexample(grid) -> bool:
    analysis = _analyze(grid)
    singleton = analysis.get("singleton")
    if analysis["errors"] or singleton is None:
        return False
    repeated_same_geometry = any(
        component["crop"] != singleton["crop"]
        and component["geometry"] == singleton["geometry"]
        for component in analysis["components"]
    )
    return bool(
        repeated_same_geometry
        and _unique_geometry_signature(grid) != analysis["output"]
    )


def _shared_signature_counterexample(
    grid,
    signature: Callable[[dict[str, Any]], Any],
    rival: Callable[[Grid], Grid],
) -> bool:
    analysis = _analyze(grid)
    singleton = analysis.get("singleton")
    if analysis["errors"] or singleton is None:
        return False
    singleton_signature = signature(singleton)
    shared = any(
        component["crop"] != singleton["crop"]
        and signature(component) == singleton_signature
        for component in analysis["components"]
    )
    return bool(shared and rival(grid) != analysis["output"])


def _shared_color_histogram_counterexample(grid) -> bool:
    return _shared_signature_counterexample(
        grid,
        lambda component: component["color_histogram"],
        _unique_color_histogram,
    )


def _shared_geometry_color_counterexample(grid) -> bool:
    return _shared_signature_counterexample(
        grid,
        lambda component: (component["geometry"], component["colors"]),
        _unique_geometry_and_colors,
    )


def _shared_bbox_histogram_counterexample(grid) -> bool:
    return _shared_signature_counterexample(
        grid,
        lambda component: (
            (len(component["crop"]), len(component["crop"][0])),
            component["color_histogram"],
        ),
        _unique_bbox_and_histogram,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "orthogonal_components": _orthogonal_components,
    "unique_color_signature": _unique_color_signature,
    "unique_geometry_signature": _unique_geometry_signature,
    "unique_color_histogram": _unique_color_histogram,
    "unique_geometry_and_colors": _unique_geometry_and_colors,
    "unique_bbox_and_histogram": _unique_bbox_and_histogram,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "orthogonal_components": _orthogonal_components,
    "unique_color_signature": _unique_color_signature,
    "unique_color_histogram": _unique_color_histogram,
    "unique_geometry_and_colors": _unique_geometry_and_colors,
    "unique_bbox_and_histogram": _unique_bbox_and_histogram,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "diagonal_connectivity_counterexample": _diagonal_connectivity_counterexample,
    "shared_color_signature_counterexample": _shared_color_counterexample,
    "same_geometry_different_colors": _same_geometry_counterexample,
    "shared_color_histogram_counterexample": _shared_color_histogram_counterexample,
    "shared_geometry_color_counterexample": _shared_geometry_color_counterexample,
    "shared_bbox_histogram_counterexample": _shared_bbox_histogram_counterexample,
}
WITNESS_RIVALS = {
    "diagonal_connectivity_counterexample": ["orthogonal_components"],
    "shared_color_signature_counterexample": ["unique_color_signature"],
    "same_geometry_different_colors": ["unique_geometry_signature"],
    "shared_color_histogram_counterexample": ["unique_color_histogram"],
    "shared_geometry_color_counterexample": ["unique_geometry_and_colors"],
    "shared_bbox_histogram_counterexample": ["unique_bbox_and_histogram"],
}
MIN_STRICT_FRAC = 0.95
