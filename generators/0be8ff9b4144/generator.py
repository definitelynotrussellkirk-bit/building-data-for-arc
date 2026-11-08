"""Generator for 21b:m142 — fill header-selected intersections.

Rows below the header whose first cell is green (3) are active. Columns to the
right of the header whose first cell is red (2) are active. Every active
row/column intersection is overwritten with gray (5); headers, the corner, and
all other body cells are preserved.

The four-example schedule contains one strict canonical-style input followed by
three rich inputs. Every rich input simultaneously demonstrates that wrong-color
header cells are inactive, occupied intersections are overwritten, and the
corner is irrelevant. Thus every three-of-four query rotation refutes the three
named shortcuts that fit all labeled canonical examples.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0be8ff9b4144"
VERSION = "5.0.0"
TASK_ID = GENERATOR_ID
RULE_HASH = "138495330232"
SUMMARY = (
    "Green-3 row markers and red-2 column markers paint gray-5 at every "
    "intersection. Rich examples add inactive wrong-color header markers, "
    "pre-existing body content that intersections overwrite, and an irrelevant "
    "noncanonical corner value."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "every generated board has at least one active row and active column",
    "at least one inactive non-corner header position remains on each side",
    "wrong-color header cells are inactive",
    "body content at an active intersection is overwritten; other content survives",
    "the top-left corner is ignored by the rule",
]

HELPFUL_TEXTURES = ("plain", "wrong_marker", "body_content", "corner_var")
SCHEDULE_PROFILES = HELPFUL_TEXTURES
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 0.20

# Negative fixtures are intentionally not exposed as ordinary generator textures.
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_BACKGROUND_VALUES = (0, 1, 4, 6, 7, 9)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_SHAPES = ((7, 8), (8, 9), (8, 10), (9, 10), (10, 11))
_INT_DOMAINS = {
    "grid_h": (5, 16),
    "grid_w": (6, 18),
    "n_top": (1, 6),
    "n_left": (1, 6),
}
_CORNER_BY_TEXTURE = {
    "plain": 8,
    "wrong_marker": 3,
    "body_content": 4,
    "corner_var": 6,
}
_TEXTURE_BY_CORNER = {value: name for name, value in _CORNER_BY_TEXTURE.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted full domain",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted full domain",
        "valid": "6..18",
    },
    "n_top": {
        "type": "int",
        "default": "difficulty-weighted full domain subject to one inactive header cell",
        "valid": "1..6",
    },
    "n_left": {
        "type": "int",
        "default": "difficulty-weighted full domain subject to one inactive header cell",
        "valid": "1..6",
    },
    "background": {
        "type": "int",
        "default": "0 for plain; weighted 0 or nonzero for rich profiles",
        "valid": "0|1|4|6|7|9",
        "doc": "inactive background; excludes active markers 2/3 and paint color 5",
    },
    "texture": {
        "type": "str",
        "default": "sample_index mod 4 teaching schedule",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": (
            "plain is strict canonical-style. Each named rich texture carries all "
            "three semantic contrasts, with its name identifying the emphasized "
            "contrast and a distinct ignored-corner code for exact observation."
        ),
    },
}

# Reserve one inactive header position in both dimensions. Each axis endpoint is
# independently reachable; only impossible dimension/count tuples are rejected.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    *(
        {"grid_h": height, "n_left": count}
        for height in range(5, 17)
        for count in range(1, 7)
        if count > height - 2
    ),
    *(
        {"grid_w": width, "n_top": count}
        for width in range(6, 19)
        for count in range(1, 7)
        if count > width - 2
    ),
]


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the fixed semantic profile for an ordinary sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _mirror(grid):
    """Independent Python statement of the selected Racket authority."""
    height, width = len(grid), len(grid[0])
    active_rows = [row for row in range(1, height) if grid[row][0] == 3]
    active_cols = [col for col in range(1, width) if grid[0][col] == 2]
    out = [row[:] for row in grid]
    for row in active_rows:
        for col in active_cols:
            out[row][col] = 5
    return out


rule_mirror = _mirror


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    for name, (lo, hi) in _INT_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    background = overrides.get("background")
    if background is not None and (
        type(background) is not int or background not in _BACKGROUND_VALUES
    ):
        raise ValueError(
            f"background must be one of {_BACKGROUND_VALUES} as a literal integer"
        )

    texture = overrides.get("texture")
    if texture is not None and (
        type(texture) is not str or texture not in HELPFUL_TEXTURES
    ):
        raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")

    height = overrides.get("grid_h")
    n_left = overrides.get("n_left")
    if height is not None and n_left is not None and n_left > height - 2:
        raise ValueError(
            f"incompatible overrides grid_h={height} and n_left={n_left}: "
            "one inactive left-header cell must remain"
        )
    width = overrides.get("grid_w")
    n_top = overrides.get("n_top")
    if width is not None and n_top is not None and n_top > width - 2:
        raise ValueError(
            f"incompatible overrides grid_w={width} and n_top={n_top}: "
            "one inactive top-header cell must remain"
        )


def _weighted_axis(ctx, label, values, favored):
    values = tuple(values)
    weighted = list(values)
    weighted.extend(value for value in favored for _ in range(8) if value in values)
    return ctx.draw_choice(label, tuple(weighted))


def _band_favorites(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (7, 8, 9),
            "grid_w": (8, 9, 10),
            "n_top": (1, 2),
            "n_left": (1, 2),
        }
    if difficulty == "hard":
        return {
            "grid_h": (10, 11, 12),
            "grid_w": (11, 12, 13),
            "n_top": (3, 4, 5),
            "n_left": (3, 4, 5),
        }
    return {
        "grid_h": (7, 8, 9, 10),
        "grid_w": (8, 9, 10, 11),
        "n_top": (2, 3, 4),
        "n_left": (2, 3, 4),
    }


def _draw_geometry(ctx, overrides, difficulty, texture):
    favorites = _band_favorites(difficulty)
    geometry_overridden = any(
        overrides.get(name) is not None
        for name in ("grid_h", "grid_w", "n_top", "n_left")
    )
    if texture in ("plain", "wrong_marker") and not geometry_overridden:
        # Exact canonical-profile support is deliberate in every difficulty band.
        # The rule itself is scale-invariant; difficulty still broadens the three
        # rich profiles, while the plain residue anchors one observed source scale.
        anchor_h, anchor_w = ctx.draw_rng("canonical_shape").choice(
            _CANONICAL_SHAPES
        )
        height = ctx.draw_choice("grid_h", (anchor_h,))
        width = ctx.draw_choice("grid_w", (anchor_w,))
    else:
        minimum_height = max(5, (overrides.get("n_left") or 0) + 2)
        minimum_width = max(6, (overrides.get("n_top") or 0) + 2)
        height = _weighted_axis(
            ctx, "grid_h", range(minimum_height, 17), favorites["grid_h"]
        )
        width = _weighted_axis(
            ctx, "grid_w", range(minimum_width, 19), favorites["grid_w"]
        )

    n_left = _weighted_axis(
        ctx, "n_left", range(1, min(6, height - 2) + 1), favorites["n_left"]
    )
    n_top = _weighted_axis(
        ctx, "n_top", range(1, min(6, width - 2) + 1), favorites["n_top"]
    )
    return height, width, n_top, n_left


def _choice_excluding(rng, values, *excluded):
    allowed = [value for value in values if value not in set(excluded)]
    if not allowed:
        raise ValueError("no lawful contrast color remains")
    return rng.choice(allowed)


def _add_rich_contrasts(grid, top_cols, left_rows, background, texture, rng):
    """Add all three contrasts while preserving the selected texture identity."""
    height, width = len(grid), len(grid[0])
    free_cols = [col for col in range(1, width) if col not in top_cols]
    free_rows = [row for row in range(1, height) if row not in left_rows]
    if not free_cols or not free_rows:
        raise ValueError("rich profile needs an inactive header position per side")

    wrong_col = rng.choice(free_cols)
    wrong_row = rng.choice(free_rows)
    if texture == "wrong_marker" and background == 0:
        # Keep this rich residue on the exact canonical four-color profile:
        # wrong top markers use 3, wrong left markers use 2, and irrelevant
        # body/corner content uses the already-canonical color 8.
        grid[0][wrong_col] = 3
        grid[wrong_row][0] = 2
        content_values = (8,)
    else:
        grid[0][wrong_col] = _choice_excluding(
            rng, (1, 3, 4, 6, 7, 9), background, 2
        )
        grid[wrong_row][0] = _choice_excluding(
            rng, (1, 2, 4, 6, 7, 9), background, 3
        )
        content_values = tuple(
            value for value in (1, 4, 6, 7, 9) if value != background
        )
    active_cells = [(row, col) for row in left_rows for col in top_cols]
    active_row, active_col = rng.choice(active_cells)
    grid[active_row][active_col] = rng.choice(content_values)

    preserved = [
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if (row not in left_rows or col not in top_cols)
    ]
    rng.shuffle(preserved)
    keep_count = 3 if texture == "body_content" else 1
    for row, col in preserved[:keep_count]:
        grid[row][col] = rng.choice(content_values)

    # The corner is rule-irrelevant. Its stable code makes the texture exactly
    # observable without smuggling any information into the active headers.
    grid[0][0] = _CORNER_BY_TEXTURE[texture]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    texture_options = (
        HELPFUL_TEXTURES if overrides.get("texture") is not None else (scheduled,)
    )
    texture = ctx.draw_choice("texture", texture_options)
    height, width, n_top, n_left = _draw_geometry(
        ctx, overrides, difficulty, texture
    )

    if overrides.get("background") is not None:
        background_options = _BACKGROUND_VALUES
    elif texture in ("plain", "wrong_marker"):
        background_options = (0,)
    else:
        background_options = (0, 0, 1, 4, 6, 7, 9)
    background = ctx.draw_choice("background", background_options)
    rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, background)
    grid[0][0] = _CORNER_BY_TEXTURE[texture]

    top_cols = rng.sample(range(1, width), n_top)
    left_rows = rng.sample(range(1, height), n_left)
    for col in top_cols:
        grid[0][col] = 2
    for row in left_rows:
        grid[row][0] = 3

    if texture != "plain":
        _add_rich_contrasts(
            grid, top_cols, left_rows, background, texture, rng
        )

    return grid


def _background(grid):
    counts = Counter(value for row in grid for value in row)
    return counts.most_common(1)[0][0]


def observe_overrides(grid):
    """Recover every exact declared axis from a generated input."""
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe malformed grid: " + "; ".join(findings))
    corner = grid[0][0]
    if corner not in _TEXTURE_BY_CORNER:
        raise ValueError(f"unrecognized texture corner code {corner}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_top": sum(value == 2 for value in grid[0][1:]),
        "n_left": sum(row[0] == 3 for row in grid[1:]),
        "background": _background(grid),
        "texture": _TEXTURE_BY_CORNER[corner],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or distribution-external inputs; accept authority data."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal integer colors 0..9"]

    height = len(grid)
    messages = []
    if not 5 <= height <= 16:
        messages.append("grid height must be in 5..16")
    if not 6 <= width <= 18:
        messages.append("grid width must be in 6..18")
    if height < 2 or width < 2:
        return messages or ["grid must have header and body cells"]

    background = _background(grid)
    if background not in _BACKGROUND_VALUES:
        messages.append("modal background must exclude marker and paint colors")
    if grid[0][0] not in _TEXTURE_BY_CORNER:
        messages.append("corner must use a declared texture code")

    active_rows = [row for row in range(1, height) if grid[row][0] == 3]
    active_cols = [col for col in range(1, width) if grid[0][col] == 2]
    if not active_rows:
        messages.append("no active row (col-0 == 3)")
    if not active_cols:
        messages.append("no active col (row-0 == 2)")
    if len(active_rows) > 6:
        messages.append("more than six active rows")
    if len(active_cols) > 6:
        messages.append("more than six active columns")
    if active_rows and len(active_rows) == height - 1:
        messages.append("no inactive left-header position")
    if active_cols and len(active_cols) == width - 1:
        messages.append("no inactive top-header position")
    if any(value == 5 for row in grid for value in row):
        messages.append("input already contains output paint color 5")
    return messages


def strict_canonical_like(grid):
    """Accept the canonical-style subpopulation used for support monitoring."""
    messages = self_check(grid)
    if messages:
        return messages
    background = _background(grid)
    if background != 0:
        messages.append("strict profile requires background 0")
    if grid[0][0] != 8:
        messages.append("strict profile requires corner 8")
    if any(value not in (0, 2) for value in grid[0][1:]):
        messages.append("strict profile permits only 0/2 in the top header")
    if any(row[0] not in (0, 3) for row in grid[1:]):
        messages.append("strict profile permits only 0/3 in the left header")
    if any(value != 0 for row in grid[1:] for value in row[1:]):
        messages.append("strict profile requires an empty body")
    return messages


def profile_signature(grid):
    observed = observe_overrides(grid)
    return (
        observed["texture"],
        observed["grid_h"],
        observed["grid_w"],
        observed["n_top"],
        observed["n_left"],
        observed["background"],
    )


def _rival_any_nonbackground_header_activates(grid):
    background = _background(grid)
    rows = [row for row in range(1, len(grid)) if grid[row][0] != background]
    cols = [col for col in range(1, len(grid[0])) if grid[0][col] != background]
    out = [row[:] for row in grid]
    for row in rows:
        for col in cols:
            out[row][col] = 5
    return out


def _rival_preserve_occupied_intersections(grid):
    background = _background(grid)
    rows = [row for row in range(1, len(grid)) if grid[row][0] == 3]
    cols = [col for col in range(1, len(grid[0])) if grid[0][col] == 2]
    out = [row[:] for row in grid]
    for row in rows:
        for col in cols:
            if grid[row][col] == background:
                out[row][col] = 5
    return out


def _rival_corner_8_required(grid):
    if grid[0][0] != 8:
        return [row[:] for row in grid]
    return _mirror(grid)


SEMANTIC_RIVALS = {
    "any_nonbackground_header_activates": _rival_any_nonbackground_header_activates,
    "preserve_occupied_intersections": _rival_preserve_occupied_intersections,
    "corner_8_required": _rival_corner_8_required,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_wrong_header_colors_are_inactive(grid):
    if self_check(grid):
        return False
    background = _background(grid)
    return any(
        value != background and value != 2 for value in grid[0][1:]
    ) and any(row[0] != background and row[0] != 3 for row in grid[1:])


def _witness_active_intersections_overwrite_content(grid):
    if self_check(grid):
        return False
    background = _background(grid)
    rows = [row for row in range(1, len(grid)) if grid[row][0] == 3]
    cols = [col for col in range(1, len(grid[0])) if grid[0][col] == 2]
    return any(grid[row][col] != background for row in rows for col in cols)


def _witness_corner_is_irrelevant(grid):
    return not self_check(grid) and grid[0][0] != 8


SEMANTIC_WITNESSES = {
    "wrong_header_colors_are_inactive": _witness_wrong_header_colors_are_inactive,
    "active_intersections_overwrite_content": _witness_active_intersections_overwrite_content,
    "corner_is_irrelevant": _witness_corner_is_irrelevant,
}
WITNESS_RIVALS = {
    "wrong_header_colors_are_inactive": ["any_nonbackground_header_activates"],
    "active_intersections_overwrite_content": ["preserve_occupied_intersections"],
    "corner_is_irrelevant": ["corner_8_required"],
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query):
    """Reject lessons whose demonstrations leave a declared shortcut alive."""
    reasons = []
    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or not {"input", "output"} <= set(episode):
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{role} input is malformed: {findings[:2]}")
            continue
        if _mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the header-intersection rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"demonstrations do not falsify shortcut {name!r}")
        except Exception as exc:  # defensive reporting for the public hook contract
            reasons.append(f"shortcut {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
