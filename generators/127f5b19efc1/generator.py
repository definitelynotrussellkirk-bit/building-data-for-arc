"""Generator for ``hard_30_assemble_transform_panel`` (127f5b19efc1).

A four-cell key strip on the bottom row names, from left to right, the four
panels to draw.  The largest nonzero component above the strip is the colored
template; smaller singleton components are distractors.  Key 1 keeps the
crop, key 2 rotates it clockwise, key 3 rotates it 180 degrees, and key 4
flips it left-to-right.  The four transformed crops are top-left aligned in a
2x2 panel with one blank separator row and column.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "127f5b19efc1"
TASK_ID = "127f5b19efc1"
VERSION = "3.0.0"
RULE_HASH = "692baf483e4b"

SUMMARY = (
    "Place one multicolor connected template above a bottom strip of exactly "
    "four transform keys. Smaller isolated cells may distract from the main "
    "object, so the unique largest component is selected. Read the four keys "
    "left-to-right (repeats are meaningful), apply id/cw90/180/flip-lr, and "
    "top-left align the four crops in a 2x2 gallery separated by zeros."
)

INVARIANTS = [
    "background is 0 and the row above the key strip is blank",
    "the bottom row contains exactly four key cells in colors 1..4, spaced by one zero",
    "the unique largest above-strip component is a 5..10 cell multicolor template",
    "zero to two smaller above-strip components are isolated singleton distractors",
    "the four keyed template transforms are visually distinguishable when their keys differ",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-aware rng",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-aware rng",
        "valid": "11..18",
    },
    "template_cells": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-aware rng",
        "valid": "5..10",
    },
    "key_pattern": {
        "type": "enum",
        "default": "scheduled all_distinct|one_repeat|two_pairs|triple",
        "valid": "all_distinct|one_repeat|two_pairs|triple",
    },
    "distractor_count": {
        "type": "int",
        "default": "scheduled 0..2",
        "valid": "0..2",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled/rng 2..3",
        "valid": "2..3",
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_KEY_PATTERNS = ("all_distinct", "one_repeat", "two_pairs", "triple")
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (
    "canonical_distinct",
    "canonical_repeat",
    "directional_transform",
    "largest_component",
)
MIN_STRICT_FRAC = 0.35

# Exact linked public feature profiles, extracted from all four train inputs and
# the held-out input.  Shape coordinates are deliberately not fixed: the rule
# is about transforming a selected template, not memorizing one bitmap.
_CANONICAL_PROFILES = (
    # h, w, cells, bbox_h, bbox_w, palette, distractors, key_pattern, key_start
    (8, 12, 6, 3, 3, 2, 0, "all_distinct", 1),
    (9, 13, 6, 3, 3, 2, 0, "all_distinct", 2),
    (8, 11, 6, 3, 3, 2, 1, "all_distinct", 1),
    (10, 14, 6, 3, 3, 3, 0, "all_distinct", 4),
    (9, 12, 5, 3, 2, 3, 1, "one_repeat", 2),
)

_BAND_BOUNDS = {
    "easy": {"grid_h": (8, 10), "grid_w": (11, 14), "template_cells": (5, 6)},
    "medium": {"grid_h": (9, 12), "grid_w": (12, 16), "template_cells": (6, 8)},
    "hard": {"grid_h": (10, 14), "grid_w": (14, 18), "template_cells": (8, 10)},
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive instances cover every lesson-critical branch."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, default, default))


def _scheduled_choice(
    ctx, label: str, options: Sequence[str], default: str
) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (default,)))


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid must be a row sequence")
    out: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            raise ValueError("each row must be a sequence")
        converted: list[int] = []
        for value in row:
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            converted.append(value)
        out.append(converted)
    return out


def _components(
    grid: Sequence[Sequence[int]], *, include_bottom: bool = False
) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    row_limit = height if include_bottom else height - 1
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(row_limit):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for dr, dc in _DELTAS:
                    neighbor = current[0] + dr, current[1] + dc
                    nr, nc = neighbor
                    if (
                        0 <= nr < row_limit
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append(sorted(cells))
    return components


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop_component(
    grid: Sequence[Sequence[int]], cells: Iterable[tuple[int, int]]
) -> list[list[int]]:
    top, left, bottom, right = _bbox(cells)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]


def _rotate_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _transform(grid: Sequence[Sequence[int]], key: int) -> list[list[int]]:
    if key == 1:
        return [list(row) for row in grid]
    if key == 2:
        return _rotate_cw(grid)
    if key == 3:
        return _rotate_180(grid)
    if key == 4:
        return _flip_lr(grid)
    raise ValueError(f"invalid transform key: {key}")


def _key_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    return [
        (col, value)
        for col, value in enumerate(grid[-1])
        if value in (1, 2, 3, 4)
    ]


def _key_pattern(keys: Sequence[int]) -> str:
    counts = sorted(Counter(keys).values(), reverse=True)
    if counts == [1, 1, 1, 1]:
        return "all_distinct"
    if counts == [2, 1, 1]:
        return "one_repeat"
    if counts == [2, 2]:
        return "two_pairs"
    if counts == [3, 1]:
        return "triple"
    raise ValueError(f"unsupported key multiplicities: {counts}")


def _analysis(grid: Any) -> tuple[list[list[int]], dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        coerced = _coerce_grid(grid)
    except ValueError as exc:
        return [], {}, [str(exc)]
    if not coerced or not coerced[0]:
        return coerced, {}, ["grid must be nonempty"]
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, {}, ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integers in 0..9")
    height = len(coerced)
    if not 8 <= height <= 14 or not 11 <= width <= 18:
        errors.append("grid dimensions must be within 8..14 by 11..18")
    if height >= 2 and any(value != 0 for value in coerced[-2]):
        errors.append("the row above the key strip must be all zero")

    key_cells = _key_cells(coerced)
    if len(key_cells) != 4:
        errors.append("bottom row must contain exactly four transform keys")
    key_positions = [col for col, _value in key_cells]
    keys = [value for _col, value in key_cells]
    if key_cells and any(
        value != 0 and col not in set(key_positions)
        for col, value in enumerate(coerced[-1])
    ):
        errors.append("bottom row may contain only zero or key colors 1..4")
    if len(key_positions) == 4 and [b - a for a, b in zip(key_positions, key_positions[1:])] != [2, 2, 2]:
        errors.append("the four key cells must be separated by one zero")
    try:
        pattern = _key_pattern(keys) if len(keys) == 4 else None
    except ValueError as exc:
        errors.append(str(exc))
        pattern = None

    components = _components(coerced) if height >= 2 else []
    if not components:
        errors.append("no template component exists above the key strip")
        return coerced, {}, errors
    ordered = sorted(components, key=lambda cells: (-len(cells), cells[0]))
    template = ordered[0]
    distractors = ordered[1:]
    if len(template) not in range(5, 11):
        errors.append("template must contain 5..10 cells")
    if len(ordered) > 3:
        errors.append("at most two distractor components are allowed")
    if distractors and len(distractors[0]) >= len(template):
        errors.append("the template must be the unique largest component")
    if any(len(component) != 1 for component in distractors):
        errors.append("every distractor component must be a singleton")

    top, left, bottom, right = _bbox(template)
    bbox_h = bottom - top + 1
    bbox_w = right - left + 1
    if not 2 <= bbox_h <= 4 or not 2 <= bbox_w <= 4:
        errors.append("template bbox must be between 2x2 and 4x4")
    palette = {coerced[row][col] for row, col in template}
    if not 2 <= len(palette) <= 3:
        errors.append("template must use two or three colors")

    crop = _crop_component(coerced, template)
    transformed = [_transform(crop, key) for key in (1, 2, 3, 4)]
    distinct_transforms = len({repr(item) for item in transformed})
    if distinct_transforms < 4:
        errors.append("all four keyed template transforms must be distinguishable")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "keys": tuple(keys),
        "key_positions": tuple(key_positions),
        "key_start": key_positions[0] if len(key_positions) == 4 else None,
        "key_pattern": pattern,
        "template": tuple(template),
        "template_cells": len(template),
        "template_bbox": (bbox_h, bbox_w),
        "palette_size": len(palette),
        "distractors": tuple(tuple(component) for component in distractors),
        "distractor_count": len(distractors),
        "template_crop": crop,
        "distinct_transforms": distinct_transforms,
    }
    return coerced, facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, and shortcut-hiding input scenes."""
    del difficulty, meta
    _coerced, _facts, errors = _analysis(grid)
    return errors


def observe_overrides(grid) -> dict[str, object]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "template_cells": facts["template_cells"],
        "key_pattern": facts["key_pattern"],
        "distractor_count": facts["distractor_count"],
        "palette_size": facts["palette_size"],
    }


def _paste(
    output: list[list[int]], pattern: Sequence[Sequence[int]], top: int, left: int
) -> None:
    for row, values in enumerate(pattern):
        for col, value in enumerate(values):
            if value != 0:
                output[top + row][left + col] = value


def _assemble_from(
    template: Sequence[Sequence[int]], keys: Sequence[int], *, fixed_cell: int | None = None
) -> list[list[int]]:
    transformed = [_transform(template, key) for key in keys]
    if fixed_cell is None:
        cell_h = max(len(item) for item in transformed)
        cell_w = max(len(item[0]) for item in transformed)
    else:
        cell_h = fixed_cell
        cell_w = fixed_cell
    output = full_grid(2 * cell_h + 1, 2 * cell_w + 1, 0)
    positions = ((0, 0), (0, cell_w + 1), (cell_h + 1, 0), (cell_h + 1, cell_w + 1))
    for pattern, (top, left) in zip(transformed, positions):
        clipped = [row[:cell_w] for row in pattern[:cell_h]]
        _paste(output, clipped, top, left)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent mirror for tests; the canonical Racket rule is authoritative."""
    coerced, facts, errors = _analysis(grid)
    if errors:
        raise ValueError("invalid transform-panel scene: " + "; ".join(errors))
    return _assemble_from(facts["template_crop"], facts["keys"])


def _first_component_rule(grid) -> list[list[int]]:
    coerced = _coerce_grid(grid)
    components = sorted(_components(coerced), key=lambda cells: cells[0])
    template = _crop_component(coerced, components[0])
    keys = [value for _col, value in _key_cells(coerced)]
    return _assemble_from(template, keys)


def _fixed_key_order_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    return _assemble_from(facts["template_crop"], (1, 2, 3, 4))


def _identity_only_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    return _assemble_from(facts["template_crop"], (1, 1, 1, 1))


def _ccw_key_two_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    template = facts["template_crop"]
    transformed = []
    for key in facts["keys"]:
        transformed.append(_rotate_ccw(template) if key == 2 else _transform(template, key))
    cell_h = max(len(item) for item in transformed)
    cell_w = max(len(item[0]) for item in transformed)
    output = full_grid(2 * cell_h + 1, 2 * cell_w + 1, 0)
    positions = ((0, 0), (0, cell_w + 1), (cell_h + 1, 0), (cell_h + 1, cell_w + 1))
    for pattern, (top, left) in zip(transformed, positions):
        _paste(output, pattern, top, left)
    return output


def _vertical_flip_key_four_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    template = facts["template_crop"]
    transformed = []
    for key in facts["keys"]:
        transformed.append(_flip_ud(template) if key == 4 else _transform(template, key))
    cell_h = max(len(item) for item in transformed)
    cell_w = max(len(item[0]) for item in transformed)
    output = full_grid(2 * cell_h + 1, 2 * cell_w + 1, 0)
    positions = ((0, 0), (0, cell_w + 1), (cell_h + 1, 0), (cell_h + 1, cell_w + 1))
    for pattern, (top, left) in zip(transformed, positions):
        _paste(output, pattern, top, left)
    return output


def _monochrome_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    template = facts["template_crop"]
    nonzero = [value for row in template for value in row if value != 0]
    color = Counter(nonzero).most_common(1)[0][0]
    mono = [[color if value != 0 else 0 for value in row] for row in template]
    return _assemble_from(mono, facts["keys"])


def _fixed_three_by_three_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    return _assemble_from(facts["template_crop"], facts["keys"], fixed_cell=3)


def _deduplicate_keys_rule(grid) -> list[list[int]]:
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return []
    unique = list(dict.fromkeys(facts["keys"]))
    keys = (unique + [1, 1, 1, 1])[:4]
    return _assemble_from(facts["template_crop"], keys)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_key_order": _fixed_key_order_rule,
    "copy_template_to_every_panel": _identity_only_rule,
    "key_two_rotates_counterclockwise": _ccw_key_two_rule,
    "key_four_flips_up_down": _vertical_flip_key_four_rule,
    "choose_first_component": _first_component_rule,
    "collapse_template_to_modal_color": _monochrome_rule,
    "force_three_by_three_panel_cells": _fixed_three_by_three_rule,
    "deduplicate_repeated_keys": _deduplicate_keys_rule,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "force_three_by_three_panel_cells": _fixed_three_by_three_rule,
}


def _valid_facts(grid) -> dict[str, Any] | None:
    _coerced, facts, errors = _analysis(grid)
    return None if errors else facts


def _differs(grid, rival_name: str) -> bool:
    facts = _valid_facts(grid)
    if facts is None:
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _witness_key_order(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["keys"] != (1, 2, 3, 4) and _differs(grid, "fixed_key_order"))


def _witness_clockwise(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and 2 in facts["keys"] and _differs(grid, "key_two_rotates_counterclockwise"))


def _witness_flip_lr(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and 4 in facts["keys"] and _differs(grid, "key_four_flips_up_down"))


def _witness_largest_component(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["distractor_count"] > 0 and _differs(grid, "choose_first_component"))


def _witness_color_preservation(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["palette_size"] >= 2 and _differs(grid, "collapse_template_to_modal_color"))


def _witness_repeated_keys(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["key_pattern"] != "all_distinct" and _differs(grid, "deduplicate_repeated_keys"))


def _witness_variable_panel_size(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and max(facts["template_bbox"]) != 3 and _differs(grid, "force_three_by_three_panel_cells"))


def _witness_real_transforms(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and _differs(grid, "copy_template_to_every_panel"))


SEMANTIC_WITNESSES = {
    "keys_are_read_left_to_right": _witness_key_order,
    "key_two_is_clockwise": _witness_clockwise,
    "key_four_is_left_right_flip": _witness_flip_lr,
    "largest_component_is_the_template": _witness_largest_component,
    "template_colors_are_preserved": _witness_color_preservation,
    "repeated_keys_repeat_panels": _witness_repeated_keys,
    "panel_cell_size_follows_transformed_crops": _witness_variable_panel_size,
    "keys_apply_real_transforms": _witness_real_transforms,
}

WITNESS_RIVALS = {
    "keys_are_read_left_to_right": ["fixed_key_order"],
    "key_two_is_clockwise": ["key_two_rotates_counterclockwise"],
    "key_four_is_left_right_flip": ["key_four_flips_up_down"],
    "largest_component_is_the_template": ["choose_first_component"],
    "template_colors_are_preserved": ["collapse_template_to_modal_color"],
    "repeated_keys_repeat_panels": ["deduplicate_repeated_keys"],
    "panel_cell_size_follows_transformed_crops": ["force_three_by_three_panel_cells"],
    "keys_apply_real_transforms": ["copy_template_to_every_panel"],
}


def strict_canonical_like(grid) -> list[str]:
    """Match the linked public feature tuples, not independent marginals."""
    _coerced, facts, errors = _analysis(grid)
    if errors:
        return errors
    profile = (
        facts["grid_h"],
        facts["grid_w"],
        facts["template_cells"],
        facts["template_bbox"][0],
        facts["template_bbox"][1],
        facts["palette_size"],
        facts["distractor_count"],
        facts["key_pattern"],
        facts["key_start"],
    )
    if profile not in _CANONICAL_PROFILES:
        return [f"linked feature profile is not public-canonical: {profile!r}"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """A four-demo lesson must eliminate every named shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    profiles: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the transform-panel rule")
            continue
        profiles.add(schedule_profile(0, index))
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True
    for name, killed in refuted.items():
        if not killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _DELTAS:
            neighbor = row + dr, col + dc
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _shape_transforms(shape: Sequence[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = list(shape)
    for _ in range(4):
        variants.add(_normalize_cells(current))
        max_col = max(col for _row, col in current)
        variants.add(_normalize_cells((row, max_col - col) for row, col in current))
        height = max(row for row, _col in current) + 1
        current = [(col, height - 1 - row) for row, col in current]
    return variants


def _random_shape_exact(rng, n_cells: int, bbox_h: int, bbox_w: int) -> tuple[tuple[int, int], ...]:
    if n_cells > bbox_h * bbox_w:
        raise ValueError("template_cells exceeds requested bbox area")
    universe = [(row, col) for row in range(bbox_h) for col in range(bbox_w)]
    for _attempt in range(2000):
        cells = {rng.choice(universe)}
        while len(cells) < n_cells:
            row, col = rng.choice(sorted(cells))
            dr, dc = rng.choice(_DELTAS)
            neighbor = row + dr, col + dc
            if 0 <= neighbor[0] < bbox_h and 0 <= neighbor[1] < bbox_w:
                cells.add(neighbor)
        normalized = _normalize_cells(cells)
        actual_h = max(row for row, _col in normalized) + 1
        actual_w = max(col for _row, col in normalized) + 1
        if actual_h != bbox_h or actual_w != bbox_w:
            continue
        if len(_shape_transforms(normalized)) < 4:
            continue
        return normalized
    # Deterministic fallback for the two public anchor signatures.
    fallbacks = {
        (6, 3, 3): ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
        (5, 3, 2): ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    }
    fallback = fallbacks.get((n_cells, bbox_h, bbox_w))
    if fallback is not None:
        return fallback
    raise RuntimeError(
        f"could not generate connected asymmetric shape: {n_cells=}, {bbox_h=}, {bbox_w=}"
    )


def _choose_bbox(rng, n_cells: int, profile: str) -> tuple[int, int]:
    if profile == "directional_transform":
        options = [(2, 4), (4, 2), (3, 4), (4, 3)]
    elif profile == "largest_component":
        options = [(3, 4), (4, 3), (4, 4)]
    else:
        options = [(3, 3), (3, 2), (2, 3)]
    viable = [
        (h, w)
        for h, w in options
        if n_cells < h * w and n_cells >= h + w - 1
    ]
    if not viable:
        viable = [
            (h, w)
            for h in range(2, 5)
            for w in range(2, 5)
            if n_cells < h * w and n_cells >= h + w - 1
        ]
    if not viable:
        raise ValueError(f"no asymmetric bbox supports {n_cells} cells")
    return rng.choice(viable)


def _make_keys(rng, pattern: str) -> list[int]:
    if pattern == "all_distinct":
        keys = [1, 2, 3, 4]
    elif pattern == "one_repeat":
        repeated = rng.choice([1, 2, 3, 4])
        others = rng.sample([key for key in (1, 2, 3, 4) if key != repeated], 2)
        keys = [repeated, repeated, *others]
    elif pattern == "two_pairs":
        first, second = rng.sample([1, 2, 3, 4], 2)
        keys = [first, first, second, second]
    elif pattern == "triple":
        repeated, other = rng.sample([1, 2, 3, 4], 2)
        keys = [repeated, repeated, repeated, other]
    else:
        raise ValueError(f"unknown key pattern: {pattern}")
    rng.shuffle(keys)
    if pattern != "all_distinct":
        # Repeated keys must be an observable lesson, not an ordering that a
        # first-occurrence/dedup shortcut happens to reproduce exactly.
        for _attempt in range(16):
            deduplicated = (list(dict.fromkeys(keys)) + [1, 1, 1, 1])[:4]
            if keys != deduplicated:
                break
            rng.shuffle(keys)
        else:
            keys = keys[1:] + keys[:1]
    return keys


def _fits_without_touching(
    occupied: set[tuple[int, int]], cells: Iterable[tuple[int, int]]
) -> bool:
    cells = set(cells)
    if occupied & cells:
        return False
    for row, col in cells:
        for dr, dc in _DELTAS:
            if (row + dr, col + dc) in occupied:
                return False
    return True


def _build_scene(
    *,
    height: int,
    width: int,
    n_cells: int,
    key_pattern: str,
    distractor_count: int,
    palette_size: int,
    bbox_h: int,
    bbox_w: int,
    key_start: int | None,
    profile: str,
    rng,
) -> list[list[int]] | None:
    if bbox_h > height - 3 or bbox_w > width:
        return None
    shape = _random_shape_exact(rng, n_cells, bbox_h, bbox_w)
    palette = rng.sample(list(range(1, 10)), palette_size)
    colors = palette[:]
    colors.extend(rng.choice(palette) for _ in range(n_cells - palette_size))
    rng.shuffle(colors)

    # Keep two blank rows below the scene: one explicit separator and the key row.
    max_top = height - 3 - bbox_h
    if max_top < 0:
        return None
    if distractor_count and profile == "largest_component":
        min_top = 2 if max_top >= 2 else max_top
    else:
        min_top = 0
    top = rng.randint(min_top, max_top) if max_top >= min_top else max_top
    left = rng.randint(0, width - bbox_w)
    template_cells = {(top + row, left + col) for row, col in shape}

    grid = full_grid(height, width, 0)
    for (row, col), color in zip(sorted(template_cells), colors):
        grid[row][col] = color
    occupied = set(template_cells)

    candidates = [
        (row, col)
        for row in range(height - 2)
        for col in range(width)
        if _fits_without_touching(occupied, {(row, col)})
    ]
    if distractor_count and profile == "largest_component":
        leading = [cell for cell in candidates if cell < min(template_cells)]
        if not leading:
            return None
        first = rng.choice(leading)
        grid[first[0]][first[1]] = rng.choice(list(range(1, 10)))
        occupied.add(first)
        distractor_count -= 1
    for _ in range(distractor_count):
        candidates = [
            (row, col)
            for row in range(height - 2)
            for col in range(width)
            if _fits_without_touching(occupied, {(row, col)})
        ]
        if not candidates:
            return None
        row, col = rng.choice(candidates)
        grid[row][col] = rng.choice(list(range(1, 10)))
        occupied.add((row, col))

    keys = _make_keys(rng, key_pattern)
    if key_start is None:
        key_start = rng.randint(0, width - 7)
    if not 0 <= key_start <= width - 7:
        return None
    for index, key in enumerate(keys):
        grid[-1][key_start + 2 * index] = key
    return grid


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")


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
    band = difficulty or "medium"
    profile = schedule_profile(seed, sample_index, difficulty)
    has_override = any(overrides.get(label) is not None for label in AXES)
    rng = ctx.draw_rng(f"layout|{band}|{profile}")

    canonical_profile = None
    if not has_override and profile == "canonical_distinct":
        canonical_profile = rng.choice(_CANONICAL_PROFILES[:4])
    elif not has_override and profile == "canonical_repeat":
        canonical_profile = _CANONICAL_PROFILES[4]

    if canonical_profile is not None:
        (
            default_h,
            default_w,
            default_cells,
            bbox_h,
            bbox_w,
            default_palette,
            default_distractors,
            default_pattern,
            key_start,
        ) = canonical_profile
    else:
        bounds = _BAND_BOUNDS[band]
        default_h = rng.randint(*bounds["grid_h"])
        default_w = rng.randint(*bounds["grid_w"])
        default_cells = rng.randint(*bounds["template_cells"])
        default_palette = 2 if profile == "directional_transform" else rng.randint(2, 3)
        default_distractors = 1 if profile == "directional_transform" else 2
        default_pattern = "all_distinct" if profile == "directional_transform" else rng.choice(("two_pairs", "triple"))
        key_start = None
        bbox_h, bbox_w = _choose_bbox(rng, default_cells, profile)

    height = _scheduled_int(ctx, "grid_h", default_h, 8, 14)
    width = _scheduled_int(ctx, "grid_w", default_w, 11, 18)
    n_cells = _scheduled_int(ctx, "template_cells", default_cells, 5, 10)
    key_pattern = _scheduled_choice(ctx, "key_pattern", _KEY_PATTERNS, default_pattern)
    distractor_count = _scheduled_int(ctx, "distractor_count", default_distractors, 0, 2)
    palette_size = _scheduled_int(ctx, "palette_size", default_palette, 2, 3)

    if has_override or n_cells != default_cells:
        bbox_h, bbox_w = _choose_bbox(rng, n_cells, profile)
        key_start = None

    for _attempt in range(512):
        grid = _build_scene(
            height=height,
            width=width,
            n_cells=n_cells,
            key_pattern=key_pattern,
            distractor_count=distractor_count,
            palette_size=palette_size,
            bbox_h=bbox_h,
            bbox_w=bbox_w,
            key_start=key_start,
            profile=profile,
            rng=rng,
        )
        if grid is None:
            continue
        errors = self_check(grid)
        if errors:
            continue
        if observe_overrides(grid) != {
            "grid_h": height,
            "grid_w": width,
            "template_cells": n_cells,
            "key_pattern": key_pattern,
            "distractor_count": distractor_count,
            "palette_size": palette_size,
        }:
            continue
        return grid
    raise RuntimeError(
        "could not construct requested transform-panel scene after 512 attempts: "
        f"{height=}, {width=}, {n_cells=}, {key_pattern=}, "
        f"{distractor_count=}, {palette_size=}, {profile=}"
    )
