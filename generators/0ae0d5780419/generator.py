"""Generator for ARC task 0ae0d5780419 — panel transform analogy.

Two full-height color-5 columns split the input into three equal-width panels.
Crop each panel to non-background content.  Search transform codes in the fixed
order identity, rotate-cw, rotate-180, transpose, flip-lr, flip-ud; choose the
FIRST code whose exact colored transform maps crop A to crop B, falling back to
identity when none matches.  Apply that code to crop C.

Every consecutive four-example lesson schedules one priority-ambiguous scene,
one color-sensitive scene, one no-match fallback scene, and one unique-match
scene.  This makes the fixed transform order, exact color comparison, and
fallback behavior observable rather than incidental.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ae0d5780419"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2374cac44014"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Two full-height color-5 columns delimit A, B, and C. Crop all three; "
    "take the first exact colored transform in the order identity, rotate-cw, "
    "rotate-180, transpose, flip-lr, flip-ud that maps A to B, or identity if "
    "none matches; apply that code to C. Four scheduled demonstrations expose "
    "priority ambiguity, color-sensitive matching, no-match fallback, and a "
    "unique ordinary transform."
)

INVARIANTS = [
    "exactly two full-height color-5 divider columns split three equal-width panels",
    "A, B, and C each contain non-background content and are cropped before comparison",
    "the first exact colored A-to-B transform wins; no exact match falls back to identity",
    "every four consecutive ordinary samples cover priority, color, fallback, and unique branches",
]

HELPFUL_TEXTURES = ("plain", "multicolor", "no_match")
DEGENERATE_TEXTURES = ("identity",)
LAWFUL_DEGENERATE_TEXTURES = ("identity",)

AXES = {
    "panel_h": {"type": "int", "default": "scheduled/difficulty keyed draw", "valid": "3..8"},
    "panel_n": {"type": "int", "default": "scheduled/difficulty keyed draw", "valid": "3..8"},
    "transform": {"type": "int", "default": "scheduled first-match code", "valid": "1..6"},
    "texture": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "plain|multicolor|no_match",
        "doc": (
            "plain uses one color per crop; multicolor uses a full colored pattern "
            "whose shape-only match selects the wrong code; no_match has no exact "
            "A-to-B transform and therefore realizes transform 1 by fallback"
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "no_match", "transform": None},
]

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_TRANSFORMS = (1, 2, 3, 4, 5, 6)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BAND_BOUNDS = {
    None: ((3, 8), (3, 8)),
    "easy": ((4, 5), (4, 5)),
    "medium": ((4, 7), (4, 7)),
    "hard": ((5, 8), (5, 8)),
}
SCHEDULE_PROFILES = ("priority", "color_sensitive", "no_match", "unique")

# Canonical-derived ambiguity templates.  Their exact match sets are
# respectively {1,3}, {2,6}, and {5,6}; C is generated asymmetric so the later
# code produces a different answer and the first-match order is observable.
_PRIORITY_TEMPLATES = (
    (1, [[1, 1, 0], [0, 1, 0], [0, 1, 1]]),
    (2, [[1, 0, 0], [1, 0, 0], [1, 1, 1]]),
    (5, [[0, 1], [1, 1], [1, 0]]),
)


def _tf(grid, code: int):
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    return [row[:] for row in grid]


def _crop(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [values[left : right + 1] for values in grid[top : bottom + 1]]


def _bbox(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _mask(grid):
    return [[1 if value != 0 else 0 for value in row] for row in grid]


def _split_panels(grid):
    height, width = len(grid), len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    panels = []
    start = 0
    for stop in dividers + [width]:
        if stop > start:
            panels.append([row[start:stop] for row in grid])
        start = stop + 1
    return dividers, panels


def _analyse(grid):
    errors: list[str] = []
    facts: dict = {}
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "facts": facts}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["every row must be a non-empty list"], "facts": facts}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": facts}
    height = len(grid)
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"invalid ARC cell value {value!r}")
                return {"errors": errors, "facts": facts}

    dividers, panels = _split_panels(grid)
    if len(dividers) != 2:
        errors.append(f"expected exactly two full-height color-5 dividers, found {dividers}")
        return {"errors": errors, "facts": facts}
    if len(panels) != 3:
        errors.append(f"expected exactly three non-empty panel slices, found {len(panels)}")
        return {"errors": errors, "facts": facts}
    panel_widths = [len(panel[0]) for panel in panels]
    if len(set(panel_widths)) != 1:
        errors.append(f"panels must have equal widths, found {panel_widths}")
    if panel_widths[0] < 3 or height < 3:
        errors.append(f"panel dimensions must be at least 3x3, got {height}x{panel_widths[0]}")
    divider_set = set(dividers)
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 and col not in divider_set:
                errors.append(f"color 5 is reserved for divider columns; found at {(row, col)}")
                return {"errors": errors, "facts": facts}

    crops = [_crop(panel) for panel in panels]
    for name, crop in zip(("A", "B", "C"), crops):
        if crop is None:
            errors.append(f"panel {name} is empty")
    if errors:
        return {"errors": errors, "facts": facts}

    a, b, c = crops
    exact_matches = [code for code in _TRANSFORMS if _tf(a, code) == b]
    shape_matches = [code for code in _TRANSFORMS if _tf(_mask(a), code) == _mask(b)]
    code = exact_matches[0] if exact_matches else 1
    output = _tf(c, code)
    matching_outputs = {_grid_key(_tf(c, match)) for match in exact_matches}
    object_colors = [
        {value for row in crop for value in row if value != 0}
        for crop in crops
    ]
    if not exact_matches:
        texture = "no_match"
    elif any(len(colors) > 1 for colors in object_colors):
        texture = "multicolor"
    else:
        texture = "plain"

    facts.update(
        {
            "panel_h": height,
            "panel_n": panel_widths[0],
            "dividers": tuple(dividers),
            "panels": panels,
            "crops": crops,
            "bboxes": tuple(_bbox(panel) for panel in panels),
            "exact_matches": tuple(exact_matches),
            "shape_matches": tuple(shape_matches),
            "transform": code,
            "output": output,
            "texture": texture,
            "priority_ambiguous": len(exact_matches) > 1 and len(matching_outputs) > 1,
            "color_sensitive": bool(shape_matches) and shape_matches[0] != code,
            "no_match": not exact_matches,
            "palette": tuple(sorted({value for row in grid for value in row})),
        }
    )
    return {"errors": errors, "facts": facts}


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _mirror(grid):
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["facts"]["output"]]


def _blob(rng, n: int, k: int, colors):
    if not 1 <= k <= n * n:
        raise ValueError(f"blob cell count {k} invalid for side {n}")
    colors = list(colors)
    if not colors or any(color in (0, 5) for color in colors):
        raise ValueError(f"invalid blob colors {colors}")
    grid = [[0] * n for _ in range(n)]
    row, col = rng.randrange(n), rng.randrange(n)
    grid[row][col] = colors[0]
    cells = [(row, col)]
    while len(cells) < k:
        row, col = cells[rng.randrange(len(cells))]
        drow, dcol = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        nr, nc = row + drow, col + dcol
        if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
            grid[nr][nc] = colors[rng.randrange(len(colors))]
            cells.append((nr, nc))
    # Multicolor is an exact observable: guarantee every requested color occurs.
    for index, color in enumerate(colors):
        row, col = cells[index]
        grid[row][col] = color
    return grid


def _unique_blob(rng, n: int, k: int, colors, *, require_non_square=False):
    for _ in range(800):
        blob = _blob(rng, n, k, colors)
        crop = _crop(blob)
        if require_non_square and len(crop) == len(crop[0]):
            continue
        views = {_grid_key(_tf(crop, code)) for code in _TRANSFORMS}
        if len(views) == 6:
            return blob, crop
    raise ValueError("could not generate a six-way-asymmetric crop")


def _unrelated_crop(rng, n: int, colors, a_crop):
    for _ in range(500):
        _, candidate = _unique_blob(
            rng,
            n,
            rng.randint(4, min(n * n, max(4, n + 2))),
            colors,
        )
        if all(_tf(a_crop, code) != candidate for code in _TRANSFORMS):
            return candidate
    raise ValueError("could not generate a no-match B crop")


def _recolor(template, color: int):
    return [[color if value else 0 for value in row] for row in template]


def _embed(crop, panel_h: int, panel_n: int, rng):
    crop_h, crop_w = len(crop), len(crop[0])
    if crop_h > panel_h or crop_w > panel_n:
        raise ValueError(
            f"crop {crop_h}x{crop_w} does not fit panel {panel_h}x{panel_n}"
        )
    panel = [[0] * panel_n for _ in range(panel_h)]
    top = rng.randint(0, panel_h - crop_h)
    left = rng.randint(0, panel_n - crop_w)
    for row in range(crop_h):
        for col in range(crop_w):
            panel[top + row][left + col] = crop[row][col]
    return panel


def _assemble(panel_h: int, panel_n: int, a_crop, b_crop, c_crop, rng):
    panels = [
        _embed(a_crop, panel_h, panel_n, rng),
        _embed(b_crop, panel_h, panel_n, rng),
        _embed(c_crop, panel_h, panel_n, rng),
    ]
    width = 3 * panel_n + 2
    grid = full_grid(panel_h, width, 0)
    d1, d2 = panel_n, 2 * panel_n + 1
    for row in range(panel_h):
        grid[row][d1] = 5
        grid[row][d2] = 5
    offsets = (0, d1 + 1, d2 + 1)
    for panel, offset in zip(panels, offsets):
        for row in range(panel_h):
            for col in range(panel_n):
                if panel[row][col] != 0:
                    grid[row][offset + col] = panel[row][col]
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_dimension(ctx, overrides, name: str, profile: str, band_bounds):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, 3, 8)
    # Priority and fallback slots deliberately anchor the exact canonical 5x17
    # profile in every difficulty band; the other slots carry scale diversity.
    if profile in ("priority", "no_match"):
        return ctx.draw_int(name, 5, 5)
    return ctx.draw_int(name, *band_bounds)


def _ordinary_profile(seed, sample_index, overrides):
    texture_override = overrides.get("texture")
    transform_override = overrides.get("transform")
    if texture_override == "no_match":
        if transform_override is not None:
            raise ValueError(
                "overrides texture='no_match' and transform are incompatible: "
                "no-match scenes realize transform 1 only by fallback"
            )
        return "no_match"
    if texture_override == "multicolor":
        return "color_sensitive"
    if texture_override == "plain" or transform_override is not None:
        return "unique"
    return schedule_profile(seed, sample_index)


def _draw_from_identity(seed, sample_index, difficulty):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={},
    )
    rng = ctx.draw_rng("identity_layout")
    color_a, color_c = rng.sample(list(_COLORS), 2)
    _, a_crop = _unique_blob(rng, 5, rng.randint(4, 7), [color_a])
    _, c_crop = _unique_blob(rng, 5, rng.randint(4, 7), [color_c])
    return _assemble(5, 5, a_crop, a_crop, c_crop, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override(s): {unknown}")

    texture_override = overrides.get("texture")
    if texture_override == "identity":
        extras = sorted(
            name
            for name, value in overrides.items()
            if name != "texture" and value is not None
        )
        if extras:
            raise ValueError(
                f"diagnostic texture 'identity' cannot be combined with {extras}"
            )
        return _draw_from_identity(seed, sample_index, difficulty)
    if texture_override is not None and texture_override not in HELPFUL_TEXTURES:
        raise ValueError(
            f"unknown texture {texture_override!r}; ordinary values are {HELPFUL_TEXTURES}"
        )

    profile = _ordinary_profile(seed, sample_index, overrides)
    profile_texture = {
        "priority": "plain",
        "color_sensitive": "multicolor",
        "no_match": "no_match",
        "unique": "plain",
    }[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if texture_override is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    else:
        texture = ctx.draw_choice("texture", (profile_texture,))

    h_bounds, n_bounds = _BAND_BOUNDS[difficulty]
    panel_h = _draw_dimension(ctx, overrides, "panel_h", profile, h_bounds)
    panel_n = _draw_dimension(ctx, overrides, "panel_n", profile, n_bounds)
    side = min(panel_h, panel_n)
    rng = ctx.draw_rng("layout")

    if overrides.get("transform") is not None:
        code = ctx.draw_int("transform", 1, 6)
    elif profile == "no_match":
        code = ctx.draw_int("transform", 1, 1)
    elif profile == "priority":
        code = ctx.draw_int("transform", _PRIORITY_TEMPLATES[int(seed) % 3][0], _PRIORITY_TEMPLATES[int(seed) % 3][0])
    else:
        scheduled = 2 + (int(seed) % 5)
        code = ctx.draw_int("transform", scheduled, scheduled)

    if profile == "priority":
        expected_code, template = _PRIORITY_TEMPLATES[int(seed) % 3]
        if code != expected_code:
            raise ValueError(f"priority profile expected code {expected_code}, got {code}")
        object_color = rng.choice(_COLORS)
        a_crop = _recolor(template, object_color)
        b_crop = _tf(a_crop, code)
        _, c_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            [object_color],
        )
    elif profile == "color_sensitive":
        colors = rng.sample(list(_COLORS), 2)
        # A full 3x3 mask makes every shape-only transform match; asymmetric
        # colors make exact matching select the scheduled code (>1 ordinarily).
        _, a_crop = _unique_blob(rng, 3, 9, colors)
        b_crop = _tf(a_crop, code)
        c_colors = rng.sample(list(_COLORS), 2)
        _, c_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            c_colors,
        )
    elif profile == "no_match":
        object_color = rng.choice(_COLORS)
        _, a_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            [object_color],
        )
        b_crop = _unrelated_crop(rng, side, [object_color], a_crop)
        _, c_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            [object_color],
        )
    else:
        color_a = rng.choice(_COLORS)
        color_c = rng.choice([color for color in _COLORS if color != color_a])
        _, a_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            [color_a],
            require_non_square=True,
        )
        b_crop = _tf(a_crop, code)
        _, c_crop = _unique_blob(
            rng,
            side,
            rng.randint(4, min(side * side, max(4, side + 2))),
            [color_c],
        )

    grid = _assemble(panel_h, panel_n, a_crop, b_crop, c_crop, rng)
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("generated invalid grid: " + "; ".join(analysis["errors"]))
    observed = analysis["facts"]
    if observed["transform"] != code:
        raise ValueError(
            f"generated transform mismatch: requested {code}, observed {observed['transform']}"
        )
    if observed["texture"] != texture:
        raise ValueError(
            f"generated texture mismatch: requested {texture!r}, observed {observed['texture']!r}"
        )
    return grid


def observe_overrides(grid):
    analysis = _analyse(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "panel_h": int(facts["panel_h"]),
        "panel_n": int(facts["panel_n"]),
        "transform": int(facts["transform"]),
        "texture": str(facts["texture"]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    analysis = _analyse(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and value is not None and observed[axis] != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyse(grid)["facts"]
    if facts["panel_h"] != 5 or facts["panel_n"] != 5:
        errors.append(
            f"canonical panels are 5x5, got {facts['panel_h']}x{facts['panel_n']}"
        )
    if len(facts["palette"]) != 3:
        errors.append(f"canonical palette has 3 colors, got {facts['palette']}")
    return errors


def _rival_last_match(grid):
    facts = _analyse(grid)["facts"]
    matches = facts["exact_matches"]
    code = matches[-1] if matches else 1
    return _tf(facts["crops"][2], code)


def _rival_colorblind(grid):
    facts = _analyse(grid)["facts"]
    matches = facts["shape_matches"]
    code = matches[0] if matches else 1
    return _tf(facts["crops"][2], code)


def _rival_rotate_on_no_match(grid):
    facts = _analyse(grid)["facts"]
    code = facts["transform"] if facts["exact_matches"] else 2
    return _tf(facts["crops"][2], code)


def _rival_transform_padded_c(grid):
    facts = _analyse(grid)["facts"]
    return _tf(facts["panels"][2], facts["transform"])


def _fixed_transform(code: int) -> Callable:
    return lambda grid: _tf(_analyse(grid)["facts"]["crops"][2], code)


SEMANTIC_RIVALS = {
    "last_matching_transform": _rival_last_match,
    "shape_only_matching": _rival_colorblind,
    "rotate_cw_on_no_match": _rival_rotate_on_no_match,
    "transform_padded_c_without_crop": _rival_transform_padded_c,
    "always_transform_1": _fixed_transform(1),
    "always_transform_2": _fixed_transform(2),
}
WITNESS_RIVALS = {
    "priority_first_match": ["last_matching_transform"],
    "color_sensitive_match": ["shape_only_matching"],
    "no_match_identity_fallback": ["rotate_cw_on_no_match"],
    "transform_code_1": ["always_transform_2"],
    "transform_code_2": ["always_transform_1"],
    "transform_code_3": ["always_transform_1"],
    "transform_code_4": ["always_transform_1"],
    "transform_code_5": ["always_transform_1"],
    "transform_code_6": ["always_transform_1"],
    "c_offset_requires_crop": ["transform_padded_c_without_crop"],
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    **{f"always_transform_{code}": _fixed_transform(code) for code in _TRANSFORMS},
}
CANONICAL_SHORTCUTS = {
    "shape_only_matching": _rival_colorblind,
    "rotate_cw_on_no_match": _rival_rotate_on_no_match,
}


def _witness_code(code: int):
    return lambda grid: observe_overrides(grid).get("transform") == code


def _facts_predicate(name: str):
    return lambda grid: bool(_analyse(grid)["facts"].get(name))


def _non_square_crop(grid):
    facts = _analyse(grid)["facts"]
    return any(len(crop) != len(crop[0]) for crop in facts["crops"])


def _c_offset_crop(grid):
    facts = _analyse(grid)["facts"]
    bbox = facts["bboxes"][2]
    return bbox is not None and bbox[:2] != (0, 0)


SEMANTIC_WITNESSES = {
    **{f"transform_code_{code}": _witness_code(code) for code in _TRANSFORMS},
    "priority_first_match": _facts_predicate("priority_ambiguous"),
    "color_sensitive_match": _facts_predicate("color_sensitive"),
    "no_match_identity_fallback": _facts_predicate("no_match"),
    "c_offset_requires_crop": _c_offset_crop,
}


def lesson_identifiable(demos, query):
    try:
        query_input = query["input"]
        query_output = query["output"]
    except (KeyError, TypeError):
        return ["query must contain input and output grids"]
    reasons = []
    if _mirror(query_input) != query_output:
        reasons.append("query output disagrees with the canonical first-match rule")
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            competing_output = competitor(query_input)
        except Exception as exc:  # fail loud; semantic gate records the reason
            return [f"competitor {name!r} raised {type(exc).__name__}: {exc}"]
        if survives and competing_output != query_output:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query"
            )
    return reasons
