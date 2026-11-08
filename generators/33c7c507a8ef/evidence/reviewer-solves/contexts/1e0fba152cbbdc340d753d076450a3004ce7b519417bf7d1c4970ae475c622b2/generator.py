"""Semantic generator for ARC task 33c7c507a8ef.

The top-left cell is a rotation code.  A complete gray rectangular frame holds
an asymmetric colored pattern.  The output is the frame interior only, rotated
by the code: 1 = identity, 2 = clockwise, 3 = 180 degrees, 4 = counter-clockwise.

The default mixture preserves the three complete public input profiles while
also varying frame size, placement, palette, geometry, and whether gray is a
content color.  Every returned grid is structurally validated; malformed
"diagnostic" textures are deliberately not part of the teaching distribution.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "33c7c507a8ef"
VERSION = "4.0.0"
TASK_ID = "33c7c507a8ef"
RULE_HASH = "a03a4d8f590f"
SUMMARY = (
    "Read the color at (0,0) as a rotation code. Find the complete gray (5) "
    "rectangular frame, crop its interior, and return that crop unchanged for "
    "code 1, rotated clockwise for code 2, rotated 180 degrees for code 3, "
    "or rotated counter-clockwise for code 4."
)
EXAMPLES_NEEDED = 7
LESSON_SCHEDULE_PERIOD = 16
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))
MIN_STRICT_FRAC = 0.10
INVARIANTS = [
    "the top-left cell is a code from 1 through 4",
    "all non-code content lies in one complete gray rectangular frame",
    "the frame has a 2..6 by 2..7 interior",
    "the interior uses 2..4 nonzero colors and has at least one zero cell",
    "the interior is asymmetric: its four quarter-turn orientations are distinct",
]

FRAME_COLOR = 5
NON_FRAME_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
TEXTURES = ("canonical_hook", "stair", "bars", "scatter")
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

AXES = {
    "scene_family": {
        "type": "str",
        "default": "scheduled canonical|generalized (3:13); rng with overrides",
        "valid": "canonical|generalized",
        "doc": (
            "canonical selects one complete public linked profile; generalized "
            "varies every rule-relevant nuisance while retaining the same rule"
        ),
    },
    "code": {"type": "int", "default": "seed-shuffled cycle 1..4; rng with overrides", "valid": "1..4"},
    "interior_h": {
        "type": "int",
        "default": "difficulty-aware rng 2..6",
        "valid": "2..6",
    },
    "interior_w": {
        "type": "int",
        "default": "difficulty-aware rng 2..7",
        "valid": "2..7",
    },
    "frame_top": {
        "type": "int",
        "default": "difficulty-aware rng 1..4",
        "valid": "1..4",
    },
    "frame_left": {
        "type": "int",
        "default": "difficulty-aware rng 1..5",
        "valid": "1..5",
    },
    "n_content_colors": {
        "type": "int",
        "default": "rng 2..4 subject to interior area",
        "valid": "2..4",
    },
    "include_frame_color": {
        "type": "bool",
        "default": "alternating per code; rng with overrides",
        "valid": "false|true",
    },
}

# Role-normalized public interiors. F is gray, C is the fixed code color,
# and A/B are other colors in first-occurrence order. The code/content equality
# must be retained: a generic color renaming changes the full public profile.
_PUBLIC_ROLE_PATTERN = (("A", "C", "0"), ("A", "0", "C"))
_PUBLIC_GRAY_ROLE_PATTERN = (("F", "A", "0"), ("F", "0", "A"))
_CANONICAL_SIGNATURES = {
    (5, 6, (1, 1, 4, 5), 2, _PUBLIC_ROLE_PATTERN),
    (5, 6, (1, 1, 4, 5), 4, _PUBLIC_ROLE_PATTERN),
    (5, 6, (1, 1, 4, 5), 3, _PUBLIC_GRAY_ROLE_PATTERN),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rotation_variants(grid):
    return (
        _copy_grid(grid),
        _rotate_cw(grid),
        _rotate_180(grid),
        _rotate_ccw(grid),
    )


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _role_matrix(interior, code):
    labels = {}
    next_label = 0
    result = []
    for row in interior:
        encoded = []
        for value in row:
            if value == 0:
                encoded.append("0")
            elif value == FRAME_COLOR:
                encoded.append("F")
            elif value == code:
                encoded.append("C")
            else:
                if value not in labels:
                    labels[value] = chr(ord("A") + next_label)
                    next_label += 1
                encoded.append(labels[value])
        result.append(tuple(encoded))
    return tuple(result)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular matrix"], "facts": None}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {"errors": ["grid must be rectangular and nonempty"], "facts": None}
    height = len(grid)
    width = next(iter(widths))
    if height > 30 or width > 30:
        errors.append("grid must fit the ARC 30 by 30 limit")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": errors + ["cell values must be integer ARC colors 0..9"], "facts": None}

    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        errors.append("cell (0,0) must be a rotation code from 1 through 4")

    frame_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == FRAME_COLOR
    ]
    if not frame_cells:
        return {"errors": errors + ["a gray frame is required"], "facts": None}
    top = min(row for row, _ in frame_cells)
    left = min(col for _, col in frame_cells)
    bottom = max(row for row, _ in frame_cells)
    right = max(col for _, col in frame_cells)
    if top < 1 or left < 1:
        errors.append("the frame must start below and right of the code cell")
    interior_h = bottom - top - 1
    interior_w = right - left - 1
    if not 2 <= interior_h <= 6:
        errors.append("frame interior height must be 2..6")
    if not 2 <= interior_w <= 7:
        errors.append("frame interior width must be 2..7")

    perimeter = (
        {(top, col) for col in range(left, right + 1)}
        | {(bottom, col) for col in range(left, right + 1)}
        | {(row, left) for row in range(top, bottom + 1)}
        | {(row, right) for row in range(top, bottom + 1)}
    )
    if not all(grid[row][col] == FRAME_COLOR for row, col in perimeter):
        errors.append("the gray bounding rectangle must have a complete one-cell perimeter")

    outside_nonzero = []
    for row in range(height):
        for col in range(width):
            if top <= row <= bottom and left <= col <= right:
                continue
            if (row, col) == (0, 0):
                continue
            if grid[row][col] != 0:
                outside_nonzero.append((row, col, grid[row][col]))
    if outside_nonzero:
        errors.append("all non-code nonzero cells must lie inside the framed rectangle")

    interior = (
        [list(row[left + 1 : right]) for row in grid[top + 1 : bottom]]
        if interior_h > 0 and interior_w > 0
        else []
    )
    nonzero = [value for row in interior for value in row if value != 0]
    colors = set(nonzero)
    if not 2 <= len(colors) <= 4:
        errors.append("the interior must use 2..4 distinct nonzero colors")
    if len(nonzero) < 3:
        errors.append("the interior must contain at least three colored cells")
    if interior and len(nonzero) == interior_h * interior_w:
        errors.append("the interior must retain at least one zero cell")
    variants = _rotation_variants(interior) if interior else ()
    if variants and len({_grid_key(variant) for variant in variants}) != 4:
        errors.append("the interior must distinguish all four quarter-turn orientations")

    facts = {
        "height": height,
        "width": width,
        "code": code,
        "frame_bbox": (top, left, bottom, right),
        "frame_top": top,
        "frame_left": left,
        "interior_h": interior_h,
        "interior_w": interior_w,
        "interior": interior,
        "n_content_colors": len(colors),
        "include_frame_color": FRAME_COLOR in colors,
        "role_matrix": _role_matrix(interior, code),
        "outside_nonzero": tuple(outside_nonzero),
    }
    facts["canonical_signature"] = (
        height,
        width,
        facts["frame_bbox"],
        code,
        facts["role_matrix"],
    )
    facts["scene_family"] = (
        "canonical"
        if facts["canonical_signature"] in _CANONICAL_SIGNATURES
        else "generalized"
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed frames, hidden distractors, and rotation-ambiguous crops."""
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    """Exact Python mirror used only for focused tests and evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    variants = _rotation_variants(facts["interior"])
    return variants[facts["code"] - 1]


def canonical_profile_signature(grid):
    """Return the complete linked public signature, or ``None`` outside it."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    signature = analysis["facts"]["canonical_signature"]
    return signature if signature in _CANONICAL_SIGNATURES else None


def observe_overrides(grid):
    """Recover every exact semantic axis from the returned grid itself."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "scene_family": facts["scene_family"],
        "code": facts["code"],
        "interior_h": facts["interior_h"],
        "interior_w": facts["interior_w"],
        "frame_top": facts["frame_top"],
        "frame_left": facts["frame_left"],
        "n_content_colors": facts["n_content_colors"],
        "include_frame_color": facts["include_frame_color"],
    }


def _canonical_compatible(overrides):
    checks = {
        "code": lambda value: value in (2, 3, 4),
        "interior_h": lambda value: value == 2,
        "interior_w": lambda value: value == 3,
        "frame_top": lambda value: value == 1,
        "frame_left": lambda value: value == 1,
        "n_content_colors": lambda value: value == 2,
    }
    for name, predicate in checks.items():
        if name in overrides and not predicate(overrides[name]):
            return False
    if overrides.get("scene_family") == "generalized":
        return False
    code = overrides.get("code")
    include_gray = overrides.get("include_frame_color")
    if code is not None and include_gray is not None:
        return bool(include_gray) == (int(code) == 3)
    return True


def _content_colors(rng, count, include_frame_color):
    if include_frame_color:
        return [FRAME_COLOR, *rng.sample(list(NON_FRAME_COLORS), count - 1)]
    return rng.sample(list(NON_FRAME_COLORS), count)


def _public_profile_colors(rng, code, include_frame_color):
    other = rng.choice([color for color in NON_FRAME_COLORS if color != code])
    return [FRAME_COLOR, other] if include_frame_color else [other, code]


def _candidate_positions(height, width, texture, rng):
    all_positions = [(row, col) for row in range(height) for col in range(width)]
    if texture == "canonical_hook":
        preferred = [
            (0, 0),
            (min(1, height - 1), 0),
            (0, min(1, width - 1)),
            (height - 1, width - 1),
        ]
    elif texture == "stair":
        preferred = []
        for index in range(max(height, width)):
            preferred.append((index % height, index % width))
            preferred.append((index % height, (index + 1) % width))
    elif texture == "bars":
        preferred = (
            [(row, 0) for row in range(height)]
            + [(height - 1, col) for col in range(width)]
            + [(0, width - 1)]
        )
    else:
        preferred = all_positions[:]
        rng.shuffle(preferred)

    ordered = []
    seen = set()
    for position in preferred:
        if position not in seen:
            seen.add(position)
            ordered.append(position)
    remainder = [position for position in all_positions if position not in seen]
    rng.shuffle(remainder)
    return ordered + remainder


def _build_pattern(height, width, colors, texture, rng):
    area = height * width
    max_marks = area - 1
    min_marks = max(3, len(colors))
    target_high = min(max_marks, max(min_marks, (area * 2) // 3))
    target = rng.randint(min_marks, target_high)

    for attempt in range(320):
        positions = _candidate_positions(height, width, texture, rng)
        if attempt:
            rng.shuffle(positions)
        selected = positions[:target]
        interior = full_grid(height, width, 0)
        assignments = list(colors)
        while len(assignments) < target:
            assignments.append(rng.choice(colors))
        if (
            texture == "canonical_hook"
            and target >= 4
            and len(colors) >= 2
            and attempt == 0
        ):
            assignments[:4] = [colors[0], colors[0], colors[1], colors[1]]
        else:
            rng.shuffle(assignments)
        for (row, col), value in zip(selected, assignments):
            interior[row][col] = value
        if len({value for row in interior for value in row if value}) != len(colors):
            continue
        if len({_grid_key(variant) for variant in _rotation_variants(interior)}) == 4:
            return interior
    raise RuntimeError("could not construct a rotation-distinguishing interior")


def _build_canonical(ctx, *, planned_code=None):
    code_options = (2, 3, 4) if planned_code is None else (planned_code,)
    if "include_frame_color" in ctx.overrides and "code" not in ctx.overrides:
        code_options = (3,) if bool(ctx.overrides["include_frame_color"]) else (2, 4)
    code = ctx.draw_choice("code", code_options)
    include_frame_color = ctx.draw_choice("include_frame_color", (code == 3,))
    interior_h = ctx.draw_int("interior_h", 2, 2)
    interior_w = ctx.draw_int("interior_w", 3, 3)
    frame_top = ctx.draw_int("frame_top", 1, 1)
    frame_left = ctx.draw_int("frame_left", 1, 1)
    n_content_colors = ctx.draw_int("n_content_colors", 2, 2)
    ctx.draw_choice("texture", ("canonical_hook",))

    rng = ctx.draw_rng("canonical_palette")
    # Public codes 2/4 echo the second content role; code 3 is separate from
    # the gray and non-gray content roles. All three inputs have four colors.
    first, second = _public_profile_colors(rng, code, include_frame_color)
    interior = [
        [first, second, 0],
        [first, 0, second],
    ]
    grid = full_grid(5, 6, 0)
    grid[0][0] = code
    draw_frame(grid, frame_top, frame_left, 4, 5, FRAME_COLOR)
    for row in range(interior_h):
        for col in range(interior_w):
            grid[frame_top + 1 + row][frame_left + 1 + col] = interior[row][col]
    return grid


def _generalized_dimensions(ctx):
    requested_colors = ctx.overrides.get("n_content_colors")
    requested_h = ctx.overrides.get("interior_h")
    requested_w = ctx.overrides.get("interior_w")
    if requested_colors is not None and int(requested_colors) == 4:
        if requested_h is not None and requested_w is not None:
            if int(requested_h) * int(requested_w) < 5:
                raise ValueError(
                    "n_content_colors=4 needs an interior with at least five cells"
                )
        min_h = 3 if requested_w is not None and int(requested_w) == 2 else 2
        height = ctx.draw_int_diff("interior_h", min_h, 6)
        min_w = 3 if height == 2 else 2
        width = ctx.draw_int_diff("interior_w", min_w, 7)
    else:
        height = ctx.draw_int_diff("interior_h", 2, 6)
        width = ctx.draw_int_diff("interior_w", 2, 7)
    return height, width


def _build_generalized(ctx, *, planned_code=None, planned_gray=None, compact=False):
    code = (ctx.draw_int("code", 1, 4) if planned_code is None
            else ctx.draw_choice("code", (planned_code,)))
    if compact:
        interior_h = ctx.draw_int("interior_h", 2, 2)
        interior_w = ctx.draw_int("interior_w", 3, 3)
        frame_top = ctx.draw_int("frame_top", 1, 1)
        frame_left = ctx.draw_int("frame_left", 1, 1)
    else:
        interior_h, interior_w = _generalized_dimensions(ctx)
        frame_top = ctx.draw_int_diff("frame_top", 1, 4)
        frame_left = ctx.draw_int_diff("frame_left", 1, 5)
        # The expanded half of each default lesson must refute a fixed crop.
        # Explicit controls retain their full lawful support.
        if (planned_code is not None
                and (interior_h, interior_w, frame_top, frame_left) == (2, 3, 1, 1)):
            frame_top = ctx.draw_int("frame_top", 2, 2)
    max_colors = min(4, interior_h * interior_w - 1)
    n_content_colors = ctx.draw_int("n_content_colors", 2, 2 if compact else max_colors)
    gray_options = (False, True) if planned_gray is None else (planned_gray,)
    include_frame_color = ctx.draw_choice("include_frame_color", gray_options)
    pattern_rng = ctx.draw_rng("pattern")
    texture = pattern_rng.choice(TEXTURES)

    margin_rng = ctx.draw_rng("margins")
    band = "medium" if ctx.difficulty in (None, "default") else ctx.difficulty
    margin_high = {"easy": 2, "medium": 3, "hard": 5}[band]
    # Compact generalized scenes share the 5x6/four-color public envelope,
    # while their interior role patterns are kept outside the exact prior.
    bottom_margin = 0 if compact else margin_rng.randint(1, margin_high)
    right_margin = 0 if compact else margin_rng.randint(1, margin_high)
    height = frame_top + interior_h + 2 + bottom_margin
    width = frame_left + interior_w + 2 + right_margin
    if height > 30 or width > 30:
        raise RuntimeError("internal dimension construction exceeded ARC limits")

    palette_rng = ctx.draw_rng("palette")
    colors = (_public_profile_colors(palette_rng, code, include_frame_color) if compact
              else _content_colors(palette_rng, n_content_colors, include_frame_color))
    for _ in range(320):
        interior = _build_pattern(interior_h, interior_w, colors, texture, pattern_rng)
        signature = (height, width, (frame_top, frame_left,
                     frame_top + interior_h + 1, frame_left + interior_w + 1),
                     code, _role_matrix(interior, code))
        if not compact or signature not in _CANONICAL_SIGNATURES:
            break
    else:
        raise RuntimeError("could not construct a noncanonical compact pattern")
    grid = full_grid(height, width, 0)
    grid[0][0] = code
    bottom = frame_top + interior_h + 1
    right = frame_left + interior_w + 1
    draw_frame(grid, frame_top, frame_left, bottom, right, FRAME_COLOR)
    for row in range(interior_h):
        for col in range(interior_w):
            grid[frame_top + 1 + row][frame_left + 1 + col] = interior[row][col]
    return grid


# The key is (position of code 1, position of code 3) in the shuffled code order.
# Each complement has ten compact slots, retains the three canonical anchors,
# and crosses gray/non-gray content for every code within compact scenes.
# Every cyclic eight-slot window has at least two expanded slots and at least
# two compact gray/non-3 slots. Thus a single query holdout cannot remove the
# only refutation of either the fixed-crop or compact-gray half-turn rival.
# The retained exhaustive schedule probe and public-draw tests verify these
# constraints independently; generation needs no runtime search.
_EXPANDED_SCHEDULE_SLOTS = {
    (0, 1): (0, 2, 3, 7, 9, 13),
    (0, 2): (0, 2, 6, 7, 9, 13),
    (0, 3): (0, 2, 3, 7, 9, 13),
    (1, 0): (1, 2, 7, 8, 12, 13),
    (1, 2): (1, 2, 7, 8, 13, 14),
    (1, 3): (1, 2, 7, 8, 11, 13),
    (2, 0): (1, 2, 7, 8, 12, 13),
    (2, 1): (1, 2, 7, 8, 11, 13),
    (2, 3): (1, 2, 7, 8, 11, 13),
    (3, 0): (1, 2, 7, 8, 12, 13),
    (3, 1): (1, 2, 6, 8, 13, 15),
    (3, 2): (1, 2, 6, 8, 13, 15),
}


def _lesson_plan(seed, sample_index):
    rng = stable_rng(seed, TASK_ID + ":lesson_schedule", VERSION)
    order = [1, 2, 3, 4]
    rng.shuffle(order)
    slot = (sample_index + rng.randrange(LESSON_SCHEDULE_PERIOD)) % LESSON_SCHEDULE_PERIOD
    block, position = divmod(slot, 4)
    code = order[position]
    # Each code appears twice in every eight consecutive draws, once with
    # gray content and once without. Thus all eight inputs are distinct.
    gray = bool((block % 2) ^ (position % 2) ^ (code == 3))
    family = "canonical" if block == position and code != 1 else "generalized"
    compact = slot not in _EXPANDED_SCHEDULE_SLOTS[(order.index(1), order.index(3))]
    return slot, code, gray, family, compact


def schedule_profile(seed, sample_index, difficulty=None):
    """Default semantic schedule repeats every 16 indices at each fixed seed."""
    return _lesson_plan(seed, sample_index)[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if value < 0:
            raise ValueError(f"{name} must be nonnegative")
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    # GenCtx treats None as an omitted override; normalize before compatibility
    # checks as well. Reject lossy int()/bool() coercions at the public boundary.
    overrides = {name: value for name, value in overrides.items() if value is not None}
    for name, value in overrides.items():
        expected = str if name == "scene_family" else bool if name == "include_frame_color" else int
        if type(value) is not expected:
            raise TypeError(f"{name} must be {expected.__name__}, got {type(value).__name__}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    plan = _lesson_plan(seed, sample_index) if not overrides else None
    canonical_allowed = _canonical_compatible(overrides)
    explicit_family = overrides.get("scene_family")
    if explicit_family == "canonical" and not canonical_allowed:
        raise ValueError("scene_family='canonical' conflicts with another override")
    if plan is not None:
        family_options = (plan[3],)
    elif explicit_family == "generalized" or not canonical_allowed:
        family_options = ("generalized",)
    else:
        family_options = (
            "canonical",
            "canonical",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        )
    family = ctx.draw_choice("scene_family", family_options)
    planned_code = plan[1] if plan is not None else None
    if family == "canonical":
        grid = _build_canonical(ctx, planned_code=planned_code)
    else:
        grid = _build_generalized(ctx, planned_code=planned_code,
                                  planned_gray=plan[2] if plan is not None else None,
                                  compact=plan[4] if plan is not None else False)

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise RuntimeError("internal construction error: " + "; ".join(analysis["errors"]))
    if analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal family provenance mismatch: wanted "
            f"{family}, observed {analysis['facts']['scene_family']}"
        )
    return grid


def strict_canonical_like(grid):
    return [] if canonical_profile_signature(grid) is not None else ["outside the linked public profile"]


def lesson_identifiable(demos, query):
    """Check code meanings in the rotation hypothesis class, from demos only.

    Rival checks separately test frame extraction and misleading color cues.
    Query outputs are deliberately never read by this coverage hook.
    """
    allowed = {code: set(range(4)) for code in (1, 2, 3, 4)}
    for pair in demos:
        analysis = _analyze(pair['input'])
        if analysis['errors']:
            return ['invalid demonstration: ' + '; '.join(analysis['errors'])]
        facts = analysis['facts']
        matches = {i for i, output in enumerate(_rotation_variants(facts['interior']))
                   if output == pair['output']}
        allowed[facts['code']] &= matches
        if not allowed[facts['code']]:
            return [f"inconsistent demonstrated meaning for code {facts['code']}"]
    analysis = _analyze(query['input'])
    if analysis['errors']:
        return ['invalid query: ' + '; '.join(analysis['errors'])]
    code = analysis['facts']['code']
    return [] if len(allowed[code]) == 1 else [f"query code {code} has no demonstrated rotation meaning"]


def _make_code_rival(code, wrong_rotation):
    def rival(grid):
        facts = _analyze(grid)['facts']
        rotation = wrong_rotation if facts['code'] == code else facts['code'] - 1
        return _rotation_variants(facts['interior'])[rotation]
    return rival


def _fixed_public_crop(grid):
    inner = [list(row[2:5]) for row in grid[2:4]]
    return _rotation_variants(inner)[grid[0][0] - 1]


def _gray_implies_half_turn(grid):
    facts = _analyze(grid)['facts']
    rotation = 2 if facts['include_frame_color'] else facts['code'] - 1
    return _rotation_variants(facts['interior'])[rotation]


def _compact_gray_implies_half_turn(grid):
    if len(grid) == 5 and len(grid[0]) == 6:
        return _gray_implies_half_turn(grid)
    return rule_mirror(grid)


def _erase_gray_content(grid):
    return [[0 if value == FRAME_COLOR else value for value in row]
            for row in rule_mirror(grid)]


_ROTATION_NAMES = ('identity', 'clockwise', 'half_turn', 'counterclockwise')
SEMANTIC_RIVALS = {
    f'code_{code}_as_{name}': _make_code_rival(code, rotation)
    for code in (1, 2, 3, 4)
    for rotation, name in enumerate(_ROTATION_NAMES)
    if rotation != code - 1
}
SEMANTIC_RIVALS.update({
    'fixed_public_crop': _fixed_public_crop,
    'gray_implies_half_turn': _gray_implies_half_turn,
    'compact_gray_implies_half_turn': _compact_gray_implies_half_turn,
    'erase_gray_content': _erase_gray_content,
})
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: rival for name, rival in SEMANTIC_RIVALS.items()
    if name.startswith('code_1_') or name in (
        'fixed_public_crop', 'gray_implies_half_turn', 'compact_gray_implies_half_turn')
}
SEMANTIC_WITNESSES = {
    f'code_{code}': (lambda grid, code=code: grid[0][0] == code)
    for code in (1, 2, 3, 4)
}
SEMANTIC_WITNESSES.update({
    'fixed_public_crop': lambda grid: _fixed_public_crop(grid) != rule_mirror(grid),
    'gray_implies_half_turn': lambda grid: (
        _analyze(grid)['facts']['include_frame_color'] and grid[0][0] != 3),
    'compact_gray_implies_half_turn': lambda grid: (
        _compact_gray_implies_half_turn(grid) != rule_mirror(grid)),
    'erase_gray_content': lambda grid: _analyze(grid)['facts']['include_frame_color'],
})
WITNESS_RIVALS = {
    f'code_{code}': [name for name in SEMANTIC_RIVALS if name.startswith(f'code_{code}_')]
    for code in (1, 2, 3, 4)
}
WITNESS_RIVALS.update({name: [name] for name in (
    'fixed_public_crop', 'gray_implies_half_turn',
    'compact_gray_implies_half_turn', 'erase_gray_content')})
