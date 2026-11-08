"""Semantic generator for ARC task 520fe6e64fb6.

Recolor every 9-cell to 7 and every original 7-cell to background 6.  Treat
the global bounding boxes of all 9s and all 7s as the two blocks.  Equal
minimum columns select the vertical branch; otherwise select the horizontal
branch.  Each between-row (or between-column) containing any zero anywhere
triggers red color 2 across original background cells within the 9-bbox span.
Zeros and all other non-target cells are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "520fe6e64fb6"
TASK_ID = GENERATOR_ID
VERSION = "3.1.1"
RULE_HASH = "82e4ce2077ce"
SUMMARY = "Swap 9/7 roles and paint red connectors across zero-triggered rows or columns between their global bounding boxes."

INVARIANTS = [
    "background is fixed color 6 and zero cells act only as trigger markers",
    "all original 9 cells become 7 and all original 7 cells become 6",
    "equal minimum columns select vertical processing; every other layout selects horizontal processing",
    "a zero anywhere in a between index triggers connector painting within the 9-bbox orthogonal span",
    "only original background-6 connector cells become red 2",
    "zeros and all cells outside the two target colors are preserved",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_PROFILES = (
    "vertical_nines_top", "vertical_sevens_top", "horizontal_nines_left", "horizontal_sevens_left",
    "all_between_triggered", "outside_row_triggers", "outside_col_triggers",
    "unequal_blocks", "irregular_markers", "multiple_components", "off_alignment_fallback",
    "boundary_blocks",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "alternate an irregular teaching refuter with a weighted draw over four public and twelve general profiles",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_INPUTS = {
    "public_train_1": (
        "666666666666", "666666996666", "666666996666", "666600660066",
        "666666666666", "666600660066", "666666666666", "666666666666",
        "666600660066", "666666666666", "666666776666", "666666776666",
    ),
    "public_train_2": (
        "66666666", "66666666", "66606066", "66606066",
        "67666669", "66606066", "66606066", "66666666",
    ),
    "public_train_3": (
        "6666666666666666", "6666666666666666", "6666666666666666", "6666666666666666",
        "6666666666666666", "6060606066066666", "6060606066066666", "6666996666667766",
        "6666996666667766", "6060606066066666", "6060606066066666", "6666666666666666",
        "6666666666666666", "6666666666666666", "6666666666666666", "6666666666666666",
    ),
    "public_test_1": (
        "66666666667777666666666666", "66666666667777666666666666", "66666666667777666666666666",
        "66666666667777666666666666", "66666666666666666666666666", "66666666666666666666666666",
        "66666666006666006666666666", "66666666666666666666666666", "66666666006666006666666666",
        "66666666669999666666666666", "66666666669999666666666666", "66666666009999006666666666",
        "66666666669999666666666666", "66666666006666006666666666", "66666666666666666666666666",
        "66666666006666006666666666", "66666666666666666666666666", "66666666006666006666666666",
        "66666666666666666666666666", "66666666006666006666666666", "66666666666666666666666666",
        "66666666666666666666666666", "66666666666666666666666666", "66666666006666006666666666",
        "66666666666666666666666666", "66666666666666666666666666",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(value) for value in row) for row in mask): profile
    for profile, mask in _PUBLIC_INPUTS.items()
}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _band(difficulty):
    if difficulty is None or difficulty == "medium":
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _dimensions(band):
    return {"easy": (8, 8), "medium": (16, 16), "hard": (26, 26)}[band]


def _blank(height, width):
    return [[6 for _ in range(width)] for _ in range(height)]


def _paint_rect(grid, top, left, rect_h, rect_w, color):
    for row in range(top, top + rect_h):
        for col in range(left, left + rect_w):
            grid[row][col] = color


def _bbox(cells):
    return (
        min(row for row, _ in cells), min(col for _, col in cells),
        max(row for row, _ in cells), max(col for _, col in cells),
    )


def _filled_rect(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return set(cells) == {(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)}


def _component_count(grid, color):
    height, width = len(grid), len(grid[0])
    positions = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == color}
    count = 0
    while positions:
        count += 1
        stack = [positions.pop()]
        while stack:
            row, col = stack.pop()
            for dr, dc in _DIRS:
                neighbor = row + dr, col + dc
                if neighbor in positions:
                    positions.remove(neighbor)
                    stack.append(neighbor)
    return count


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _classify_general(info):
    vertical = info["orientation"] == "vertical"
    aligned_horizontal = info["r9a"] == info["r7a"] and info["r9b"] == info["r7b"]
    if not vertical and not aligned_horizontal:
        return "off_alignment_fallback"
    if info["nine_components"] > 1 or info["seven_components"] > 1:
        return "multiple_components"
    if not info["nines_rect"] or not info["sevens_rect"]:
        return "irregular_markers"
    if info["nine_shape"] != info["seven_shape"]:
        return "unequal_blocks"
    if info["touches_boundary"]:
        return "boundary_blocks"
    if info["outside_only_triggers"] and vertical:
        return "outside_row_triggers"
    if info["outside_only_triggers"]:
        return "outside_col_triggers"
    if info["between_count"] > 0 and info["trigger_count"] == info["between_count"]:
        return "all_between_triggered"
    if vertical and info["r9a"] < info["r7a"]:
        return "vertical_nines_top"
    if vertical:
        return "vertical_sevens_top"
    if info["c9a"] < info["c7a"]:
        return "horizontal_nines_left"
    return "horizontal_sevens_left"


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    nines = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 9]
    sevens = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 7]
    if not nines or not sevens:
        errors.append("at least one 9 cell and one 7 cell are required")
        return result
    r9a, c9a, r9b, c9b = _bbox(nines)
    r7a, c7a, r7b, c7b = _bbox(sevens)
    vertical = c9a == c7a
    orientation = "vertical" if vertical else "horizontal"
    if vertical:
        between = tuple(range(1 + min(r9b, r7b), max(r9a, r7a)))
        triggered = tuple(index for index in between if any(grid[index][col] == 0 for col in range(width)))
        trigger_zeros = tuple((row, col) for row in triggered for col in range(width) if grid[row][col] == 0)
        span = lambda row, col: c9a <= col <= c9b
    else:
        between = tuple(range(1 + min(c9b, c7b), max(c9a, c7a)))
        triggered = tuple(index for index in between if any(grid[row][index] == 0 for row in range(height)))
        trigger_zeros = tuple((row, col) for col in triggered for row in range(height) if grid[row][col] == 0)
        span = lambda row, col: r9a <= row <= r9b

    output = [list(row) for row in grid]
    for row, col in nines:
        output[row][col] = 7
    for row, col in sevens:
        output[row][col] = 6
    connector_cells = []
    if vertical:
        for row in triggered:
            for col in range(c9a, c9b + 1):
                if grid[row][col] == 6:
                    output[row][col] = 2
                    connector_cells.append((row, col))
    else:
        for col in triggered:
            for row in range(r9a, r9b + 1):
                if grid[row][col] == 6:
                    output[row][col] = 2
                    connector_cells.append((row, col))

    nine_shape = (r9b - r9a + 1, c9b - c9a + 1, len(nines))
    seven_shape = (r7b - r7a + 1, c7b - c7a + 1, len(sevens))
    touches_boundary = any(row in (0, height - 1) or col in (0, width - 1) for row, col in nines + sevens)
    info = {
        "r9a": r9a, "c9a": c9a, "r9b": r9b, "c9b": c9b,
        "r7a": r7a, "c7a": c7a, "r7b": r7b, "c7b": c7b,
        "orientation": orientation,
        "between_indices": between,
        "between_count": len(between),
        "triggered_indices": triggered,
        "trigger_count": len(triggered),
        "trigger_zeros": trigger_zeros,
        "outside_only_triggers": bool(trigger_zeros) and all(not span(row, col) for row, col in trigger_zeros),
        "connector_cells": tuple(connector_cells),
        "nine_shape": nine_shape,
        "seven_shape": seven_shape,
        "nines_rect": _filled_rect(nines),
        "sevens_rect": _filled_rect(sevens),
        "nine_components": _component_count(grid, 9),
        "seven_components": _component_count(grid, 7),
        "touches_boundary": touches_boundary,
    }
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature) or _classify_general(info)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared connector lesson")
    if not connector_cells:
        errors.append("lesson must paint at least one red connector cell")
    result.update(info)
    result.update({"errors": errors, "scene_profile": profile, "nines": tuple(nines), "sevens": tuple(sevens), "output": output})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _add_vertical_triggers(grid, rows, c1, c2, rng, *, outside=False):
    width = len(grid[0])
    for row in rows:
        choices = [col for col in range(width) if (col < c1 or col > c2) == outside]
        grid[row][rng.choice(choices)] = 0
        if len(choices) > 2 and rng.random() < 0.6:
            grid[row][rng.choice(choices)] = 0


def _add_horizontal_triggers(grid, cols, r1, r2, rng, *, outside=False):
    height = len(grid)
    for col in cols:
        choices = [row for row in range(height) if (row < r1 or row > r2) == outside]
        grid[rng.choice(choices)][col] = 0
        if len(choices) > 2 and rng.random() < 0.6:
            grid[rng.choice(choices)][col] = 0


def _base_geometry(band):
    height, width = _dimensions(band)
    block_h = {"easy": 2, "medium": 2, "hard": 4}[band]
    block_w = {"easy": 2, "medium": 2, "hard": 4}[band]
    return height, width, block_h, block_w


def _add_inert_distractors(grid, rng, band):
    """Add zeros outside the active between interval without changing the lesson."""
    height, width = len(grid), len(grid[0])
    nines = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 9]
    sevens = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 7]
    r9a, c9a, r9b, c9b = _bbox(nines)
    r7a, c7a, r7b, c7b = _bbox(sevens)
    if c9a == c7a:
        active = set(range(1 + min(r9b, r7b), max(r9a, r7a)))
        choices = [(row, col) for row in range(height) for col in range(width)
                   if row not in active and grid[row][col] == 6]
    else:
        active = set(range(1 + min(c9b, c7b), max(c9a, c7a)))
        choices = [(row, col) for row in range(height) for col in range(width)
                   if col not in active and grid[row][col] == 6]
    rng.shuffle(choices)
    limit = {"easy": 3, "medium": 6, "hard": 10}[band]
    for row, col in choices[:rng.randint(1, min(limit, len(choices)))]:
        grid[row][col] = 0


def _general_grid(rng, profile, band):
    height, width, block_h, block_w = _base_geometry(band)
    grid = _blank(height, width)
    margin = 1 if band == "easy" else 2

    all_vertical = profile == "all_between_triggered" and rng.random() < 0.5
    all_horizontal = profile == "all_between_triggered" and not all_vertical

    if profile in {"vertical_nines_top", "vertical_sevens_top", "outside_row_triggers"} or all_vertical:
        left = rng.randint(margin, width - block_w - margin)
        top, bottom = margin, height - margin - block_h
        nine_top, seven_top = (top, bottom) if profile != "vertical_sevens_top" else (bottom, top)
        _paint_rect(grid, nine_top, left, block_h, block_w, 9)
        _paint_rect(grid, seven_top, left, block_h, block_w, 7)
        between = list(range(top + block_h, bottom))
        if profile == "all_between_triggered":
            selected = between
        else:
            rng.shuffle(between)
            selected = sorted(between[:max(1, len(between) // 3)])
        _add_vertical_triggers(grid, selected, left, left + block_w - 1, rng, outside=profile == "outside_row_triggers")
    elif profile in {"horizontal_nines_left", "horizontal_sevens_left", "outside_col_triggers"} or all_horizontal:
        top = rng.randint(margin, height - block_h - margin)
        left, right = margin, width - margin - block_w
        nine_left, seven_left = (left, right) if profile != "horizontal_sevens_left" else (right, left)
        _paint_rect(grid, top, nine_left, block_h, block_w, 9)
        _paint_rect(grid, top, seven_left, block_h, block_w, 7)
        between = list(range(left + block_w, right))
        if profile == "all_between_triggered":
            selected = between
        else:
            rng.shuffle(between)
            selected = sorted(between[:max(1, len(between) // 3)])
        _add_horizontal_triggers(grid, selected, top, top + block_h - 1, rng, outside=profile == "outside_col_triggers")
    elif profile == "unequal_blocks":
        left = max(1, width // 2 - 2)
        _paint_rect(grid, margin, left, block_h, min(width - left - 1, block_w + 1), 9)
        _paint_rect(grid, height - margin - max(1, block_h - 1), left, max(1, block_h - 1), block_w, 7)
        rows = list(range(margin + block_h, height - margin - max(1, block_h - 1)))
        _add_vertical_triggers(grid, rows[::max(1, len(rows) // 2)], left, left + block_w, rng)
    elif profile == "irregular_markers":
        left = width // 2 - 1
        top, bottom = margin, height - margin - 3
        # Unequal L shapes expose rectangle/size shortcuts and whose span is used.
        for dr, dc in ((0, 0), (1, 0), (1, 1), (1, 2)):
            grid[top + dr][left + dc] = 9
        for dr, dc in ((0, 0), (1, 0), (1, 1)):
            grid[bottom + dr][left + dc] = 7
        rows = list(range(top + 2, bottom))
        # An outside zero leaves the whole 9 span paintable, including the
        # rightmost column beyond the 7 span. Every anchor refutes all rivals.
        _add_vertical_triggers(grid, rows[::max(1, len(rows) // 2)], left, left + 2, rng, outside=True)
    elif profile == "multiple_components":
        left = max(1, width // 2 - 2)
        top, bottom = margin, height - margin - 1
        for col in (left, left + 2):
            grid[top][col] = 9
            grid[bottom][col] = 7
        rows = list(range(top + 1, bottom))
        _add_vertical_triggers(grid, rows[::max(1, len(rows) // 2)], left, left + 2, rng)
    elif profile == "off_alignment_fallback":
        nine_top, nine_left = margin, margin
        seven_top, seven_left = height - margin - block_h, width - margin - block_w
        _paint_rect(grid, nine_top, nine_left, block_h, block_w, 9)
        _paint_rect(grid, seven_top, seven_left, block_h, block_w, 7)
        cols = list(range(nine_left + block_w, seven_left))
        _add_horizontal_triggers(grid, cols[::max(1, len(cols) // 3)], nine_top, nine_top + block_h - 1, rng)
    elif profile == "boundary_blocks":
        left = 0
        _paint_rect(grid, 0, left, block_h, block_w, 9)
        _paint_rect(grid, height - block_h, left, block_h, block_w, 7)
        rows = list(range(block_h, height - block_h))
        _add_vertical_triggers(grid, rows[::max(1, len(rows) // 2)], left, left + block_w - 1, rng)
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    _add_inert_distractors(grid, rng, band)
    return grid


def _public_grid(profile):
    return [[int(value) for value in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a boolean or coerced scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    band = _band(difficulty)
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if "scene_profile" in overrides and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    if requested is not None:
        choices = SCENE_PROFILES
    elif sample_index % 2 == 0:
        choices = ("irregular_markers",)
    else:
        # Half the positions are anchors. Double public weight in payload
        # positions retains about 20% public support over the full stream.
        choices = PUBLIC_PROFILES * 2 + GENERAL_PROFILES
    profile = context.draw_choice("scene_profile", list(choices))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, band)
    if profile == "irregular_markers" and (sample_index // 2) % 2:
        # Consecutive even-index anchors must remain distinct after the
        # production sampler removes duplicate pairs. Opposite marker order
        # guarantees this without relying on random zero/distractor placement.
        # Vertical reflection preserves the branch, spans and every refuter.
        grid = [row[:] for row in reversed(grid)]
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors


def strict_canonical_like(grid):
    """The aligned, equal filled-block manifold; broader inputs remain lawful."""
    info = _analysis(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if not info["nines_rect"] or not info["sevens_rect"]:
        errors.append("canonical blocks are filled rectangles")
    if info["nine_shape"] != info["seven_shape"]:
        errors.append("canonical blocks have equal dimensions and area")
    if info["orientation"] == "horizontal" and (
            info["r9a"] != info["r7a"] or info["r9b"] != info["r7b"]):
        errors.append("canonical horizontal blocks are row-aligned")
    return errors


def _recolor_only(grid):
    return [[7 if value == 9 else 6 if value == 7 else value for value in row] for row in grid]


def rival_equal_filled_rectangles_only(grid):
    info = _analysis(grid)
    if info["nines_rect"] and info["sevens_rect"] and info["nine_shape"] == info["seven_shape"]:
        return rule_mirror(grid)
    return _recolor_only(grid)


def rival_equal_bbox_and_area_only(grid):
    info = _analysis(grid)
    return rule_mirror(grid) if info["nine_shape"] == info["seven_shape"] else _recolor_only(grid)


def rival_seven_span(grid):
    """Use the erased 7 object's span instead of the original 9 object's span."""
    info = _analysis(grid)
    output = _recolor_only(grid)
    if info["orientation"] == "vertical":
        cells = ((r, c) for r in info["triggered_indices"]
                 for c in range(info["c7a"], info["c7b"] + 1))
    else:
        cells = ((r, c) for c in info["triggered_indices"]
                 for r in range(info["r7a"], info["r7b"] + 1))
    for r, c in cells:
        if grid[r][c] == 6:
            output[r][c] = 2
    return output


def rival_span_local_zeros(grid):
    """Ignore a trigger outside the 9 object's orthogonal span."""
    info = _analysis(grid)
    output = _recolor_only(grid)
    for index in info["between_indices"]:
        if info["orientation"] == "vertical":
            cells = [(index, c) for c in range(info["c9a"], info["c9b"] + 1)]
        else:
            cells = [(r, index) for r in range(info["r9a"], info["r9b"] + 1)]
        if any(grid[r][c] == 0 for r, c in cells):
            for r, c in cells:
                if grid[r][c] == 6:
                    output[r][c] = 2
    return output


SEMANTIC_RIVALS = {
    "equal_filled_rectangles_only": rival_equal_filled_rectangles_only,
    "equal_bbox_and_area_only": rival_equal_bbox_and_area_only,
    "seven_span": rival_seven_span,
    "span_local_zeros": rival_span_local_zeros,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The local-zero rival already fails canonical examples; do not claim it fits.
CANONICAL_SHORTCUTS = {name: fn for name, fn in SEMANTIC_RIVALS.items() if name != "span_local_zeros"}
SEMANTIC_WITNESSES = {
    "nonrectangular_refuter": lambda grid: rival_equal_filled_rectangles_only(grid) != rule_mirror(grid),
    "unequal_shape_refuter": lambda grid: rival_equal_bbox_and_area_only(grid) != rule_mirror(grid),
    "nine_span_refuter": lambda grid: rival_seven_span(grid) != rule_mirror(grid),
    "global_zero_refuter": lambda grid: rival_span_local_zeros(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "nonrectangular_refuter": ["equal_filled_rectangles_only"],
    "unequal_shape_refuter": ["equal_bbox_and_area_only"],
    "nine_span_refuter": ["seven_span"],
    "global_zero_refuter": ["span_local_zeros"],
}
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("irregular_refuter", "payload")


def schedule_profile(seed, sample_index, difficulty=None):
    """Report the repeating role, not a nonexistent periodic random layout."""
    return "irregular_refuter" if sample_index % 2 == 0 else "payload"


def lesson_identifiable(demos, query):
    """Finite named-rival check; no claim to exhaust all possible rules."""
    grid = query["input"] if isinstance(query, dict) else query
    expected = query.get("output") if isinstance(query, dict) else None
    if expected is None:
        expected = rule_mirror(grid)
    return [f"{name} fits every demonstration but changes the query answer"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(demo["input"]) == demo["output"] for demo in demos)
            and rival(grid) != expected]
