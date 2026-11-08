"""Generator for ``Transform Code Tiling`` (task d7a79f2f335e).

The input is always the canonical 2x5 layout: a 2x2 template, one black
separator column, and a 2x2 matrix of transform commands.  The output is a
4x4 tiling in which command 1 keeps the template, 2 rotates clockwise,
3 rotates 180 degrees, and 4 rotates counter-clockwise.

The former generator declared eight mostly dead or unobservable axes, emitted
non-canonical 3x3 panels, sampled commands 5..7 that never appear in the task,
and could materialize lessons whose demonstrations did not identify the
command mapping.  This version exposes one exact *linked* profile axis.  Four
profiles are the empirical canonical manifold; a fifth fully-asymmetric
profile is a controlled generalization that strengthens transform evidence.
Every three consecutive examples include an asymmetric all-command anchor.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers import L_TROMINOES, SQUARE_2X2, random_palette
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7a79f2f335e"
TASK_ID = "d7a79f2f335e"
VERSION = "3.0.0"
RULE_HASH = "3bcb3322c1c7"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "A 2x2 template sits left of one black separator column; a 2x2 command "
    "matrix sits on the right. Commands 1/2/3/4 tile the template unchanged/"
    "clockwise/180-degrees/counter-clockwise into a 4x4 output."
)
INVARIANTS = [
    "input shape is exactly 2x5 and background is 0",
    "column 2 is the unique all-zero separator",
    "the left 2x2 template has a full 2x2 crop and a declared linked profile",
    "the right 2x2 command matrix uses only codes 1..4",
    "every three-example schedule window contains an asymmetric all-code anchor",
]

PROFILE_L_MONO_ALL = "l_mono_all"
PROFILE_DIAG_MONO_ALL = "diag_mono_all"
PROFILE_L_TWO_ALL = "l_two_all"
PROFILE_L_TWO_REPEAT = "l_two_repeat"
PROFILE_FOUR_COLOR_ALL = "four_color_all"
PROFILE_NAMES = (
    PROFILE_L_MONO_ALL,
    PROFILE_DIAG_MONO_ALL,
    PROFILE_L_TWO_ALL,
    PROFILE_L_TWO_REPEAT,
    PROFILE_FOUR_COLOR_ALL,
)

AXES = {
    "profile": {
        "type": "str",
        "default": (
            "four-slot lesson schedule: asymmetric anchor / repeated-command "
            "control / varied canonical-or-generalized profile / asymmetric anchor"
        ),
        "valid": "|".join(PROFILE_NAMES),
    },
}

# Schedule slots are reported to the semantic gate.  Slots 0 and 3 are both
# anchors, so every sliding window of EXAMPLES_NEEDED=3 contains one.
SCHEDULE_PROFILES = (0, 1, 2, 3)

# Coarse semantic signatures, quotienting L orientation, diagonal orientation,
# concrete colors, and command-cell order.  These preserve exactly the linked
# facts visible in the five canonical inputs.
_CANONICAL_SIGNATURES = frozenset(
    {
        ("l3", "mono", "all_rotations"),
        ("diag2", "mono", "all_rotations"),
        ("l3", "two_color", "all_rotations"),
        ("l3", "two_color", "repeat_identity"),
    }
)
_PROFILE_BY_SIGNATURE = {
    ("l3", "mono", "all_rotations"): PROFILE_L_MONO_ALL,
    ("diag2", "mono", "all_rotations"): PROFILE_DIAG_MONO_ALL,
    ("l3", "two_color", "all_rotations"): PROFILE_L_TWO_ALL,
    ("l3", "two_color", "repeat_identity"): PROFILE_L_TWO_REPEAT,
    ("full4", "four_color", "all_rotations"): PROFILE_FOUR_COLOR_ALL,
}

_FIXED_POSITION_CODES = ((1, 2), (3, 4))
_ALL_ROTATION_ORDERS = tuple(
    order
    for order in (
        (2, 4, 1, 3),
        (3, 1, 4, 2),
        (4, 2, 3, 1),
        (2, 3, 4, 1),
        (4, 1, 2, 3),
        (3, 4, 1, 2),
    )
    if order != (1, 2, 3, 4)
)
_REPEAT_ORDERS = (
    (1, 4, 1, 2),
    (2, 1, 4, 1),
    (4, 1, 2, 1),
    (1, 2, 1, 4),
)


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Return the deterministic four-slot lesson schedule class."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _transform(template, code: int):
    if code == 1:
        return [row[:] for row in template]
    if code == 2:
        return _rotate_cw(template)
    if code == 3:
        return _rotate_180(template)
    if code == 4:
        return _rotate_ccw(template)
    raise ValueError(f"unsupported command {code}; expected 1..4")


def _parts(grid):
    """Return (template, codes) for the exact 2x5 grammar, else ``None``."""
    if not isinstance(grid, list) or len(grid) != 2:
        return None
    if any(not isinstance(row, list) or len(row) != 5 for row in grid):
        return None
    return ([row[:2] for row in grid], [row[3:] for row in grid])


def _template_signature(template):
    cells = [(r, c) for r in range(2) for c in range(2) if template[r][c] != 0]
    colors = [template[r][c] for r, c in cells]
    color_counts = sorted(Counter(colors).values())
    occupied = frozenset(cells)

    if len(cells) == 3 and occupied in {frozenset(shape) for shape in L_TROMINOES}:
        shape_class = "l3"
    elif len(cells) == 2 and occupied in {
        frozenset({(0, 0), (1, 1)}),
        frozenset({(0, 1), (1, 0)}),
    }:
        shape_class = "diag2"
    elif len(cells) == 4:
        shape_class = "full4"
    else:
        return None

    if len(set(colors)) == 1:
        color_class = "mono"
    elif len(set(colors)) == 2 and color_counts == [1, 2]:
        color_class = "two_color"
    elif len(set(colors)) == 4 and color_counts == [1, 1, 1, 1]:
        color_class = "four_color"
    else:
        return None
    return shape_class, color_class


def profile_signature(grid):
    """Return the complete linked semantic signature, or ``None``.

    This deliberately couples template morphology/color multiplicity to the
    command multiset.  Recombining canonical marginals into an unseen pair is
    therefore rejected instead of being mislabeled as an exact profile.
    """
    split = _parts(grid)
    if split is None:
        return None
    template, codes = split
    template_sig = _template_signature(template)
    if template_sig is None:
        return None
    code_values = sorted(value for row in codes for value in row)
    if code_values == [1, 2, 3, 4]:
        code_class = "all_rotations"
    elif code_values == [1, 1, 2, 4]:
        code_class = "repeat_identity"
    else:
        return None
    return (*template_sig, code_class)


def _profile_name(grid):
    return _PROFILE_BY_SIGNATURE.get(profile_signature(grid))


def observe_overrides(grid) -> dict[str, str]:
    profile = _profile_name(grid)
    if profile is None:
        raise ValueError("returned grid does not realize a declared profile")
    return {"profile": profile}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or len(grid) != 2:
        return ["input must be a 2-row list"]
    if any(not isinstance(row, list) or len(row) != 5 for row in grid):
        return ["input must be rectangular with shape 2x5"]

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (not isinstance(value, int) or isinstance(value, bool)
                    or not 0 <= value <= 9):
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9")

    zero_cols = [c for c in range(5) if all(grid[r][c] == 0 for r in range(2))]
    if zero_cols != [2]:
        errors.append(f"column 2 must be the unique all-zero separator, got {zero_cols}")

    template, codes = _parts(grid)
    if any(all(template[r][c] == 0 for c in range(2)) for r in range(2)):
        errors.append("template crop does not touch both rows")
    if any(all(template[r][c] == 0 for r in range(2)) for c in range(2)):
        errors.append("template crop does not touch both columns")
    bad_codes = [value for row in codes for value in row if value not in (1, 2, 3, 4)]
    if bad_codes:
        errors.append(f"command matrix contains values outside 1..4: {bad_codes}")

    signature = profile_signature(grid)
    if signature not in _PROFILE_BY_SIGNATURE:
        errors.append(
            "template morphology/color multiplicity and command multiset do not "
            "form a declared linked profile"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked profile {signature!r} is outside the empirical canonical manifold"]
    return []


def _draw_profile(ctx, sample_index: int, difficulty, overrides) -> str:
    if "profile" in overrides and overrides["profile"] is not None:
        return ctx.draw_choice("profile", list(PROFILE_NAMES))

    slot = schedule_profile(0, sample_index, difficulty)
    if slot in (0, 3):
        return ctx.draw_choice("profile", [PROFILE_L_TWO_ALL])
    if slot == 1:
        return ctx.draw_choice("profile", [PROFILE_L_TWO_REPEAT])

    # Slot 2 supplies morphology controls and one controlled generalization.
    if difficulty == "easy":
        pool = [
            PROFILE_DIAG_MONO_ALL,
            PROFILE_DIAG_MONO_ALL,
            PROFILE_L_MONO_ALL,
            PROFILE_FOUR_COLOR_ALL,
        ]
    elif difficulty == "hard":
        pool = [
            PROFILE_FOUR_COLOR_ALL,
            PROFILE_FOUR_COLOR_ALL,
            PROFILE_DIAG_MONO_ALL,
            PROFILE_L_MONO_ALL,
        ]
    else:
        pool = [PROFILE_DIAG_MONO_ALL, PROFILE_L_MONO_ALL, PROFILE_FOUR_COLOR_ALL]
    return ctx.draw_choice("profile", pool)


def _draw_template(profile: str, rng, difficulty):
    # Easy keeps role colors separate from commands; later bands sometimes
    # overlap them, matching the canonical examples where template colors may
    # also be command symbols.
    if difficulty == "easy":
        color_pool = list(range(5, 10))
    else:
        color_pool = list(range(1, 10))

    if profile in (PROFILE_L_MONO_ALL, PROFILE_L_TWO_ALL, PROFILE_L_TWO_REPEAT):
        cells = list(rng.choice(L_TROMINOES))
    elif profile == PROFILE_DIAG_MONO_ALL:
        cells = list(rng.choice((((0, 0), (1, 1)), ((0, 1), (1, 0)))))
    elif profile == PROFILE_FOUR_COLOR_ALL:
        cells = list(SQUARE_2X2)
    else:  # guarded by _draw_profile / draw_choice
        raise ValueError(f"unknown profile {profile!r}")

    template = full_grid(2, 2, 0)
    if profile in (PROFILE_L_MONO_ALL, PROFILE_DIAG_MONO_ALL):
        color = rng.choice(color_pool)
        for r, c in cells:
            template[r][c] = color
    elif profile in (PROFILE_L_TWO_ALL, PROFILE_L_TWO_REPEAT):
        c0, c1 = random_palette(rng, 2, bg=0)
        singleton = rng.choice(cells)
        for r, c in cells:
            template[r][c] = c1 if (r, c) == singleton else c0
    else:
        colors = list(random_palette(rng, 4, bg=0))
        rng.shuffle(colors)
        for (r, c), color in zip(cells, colors):
            template[r][c] = color
    return template


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, sample_index, difficulty, overrides)
    rng = ctx.draw_rng("layout")
    template = _draw_template(profile, rng, difficulty)

    if profile == PROFILE_L_TWO_REPEAT:
        flat_codes = list(rng.choice(_REPEAT_ORDERS))
    else:
        flat_codes = list(rng.choice(_ALL_ROTATION_ORDERS))

    grid = full_grid(2, 5, 0)
    for r in range(2):
        for c in range(2):
            grid[r][c] = template[r][c]
            grid[r][3 + c] = flat_codes[2 * r + c]
    return grid


def _render(template, codes, mapper: Callable[[int, int, int], int]):
    out = full_grid(4, 4, 0)
    for rr in range(2):
        for cc in range(2):
            transformed = _transform(template, mapper(codes[rr][cc], rr, cc))
            for r in range(2):
                for c in range(2):
                    out[2 * rr + r][2 * cc + c] = transformed[r][c]
    return out


def rule_mirror(grid):
    split = _parts(grid)
    if split is None:
        raise ValueError("rule_mirror requires the exact 2x5 input grammar")
    template, codes = split
    return _render(template, codes, lambda code, _r, _c: code)


def _rival_all_identity(grid):
    template, codes = _parts(grid)
    return _render(template, codes, lambda _code, _r, _c: 1)


def _rival_swap_quarter_turns(grid):
    template, codes = _parts(grid)
    swap = {1: 1, 2: 4, 3: 3, 4: 2}
    return _render(template, codes, lambda code, _r, _c: swap[code])


def _rival_ignore_command_values(grid):
    template, codes = _parts(grid)
    return _render(template, codes, lambda _code, r, c: _FIXED_POSITION_CODES[r][c])


def _rival_solid_bbox(grid):
    template, codes = _parts(grid)
    color = next(value for row in template for value in row if value != 0)
    return full_grid(4, 4, color)


SEMANTIC_RIVALS = {
    "all_commands_are_identity": _rival_all_identity,
    "swap_clockwise_and_counterclockwise": _rival_swap_quarter_turns,
    "command_meaning_is_fixed_by_cell_position": _rival_ignore_command_values,
    "tile_solid_template_bounding_boxes": _rival_solid_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rotation_orbit_size(grid) -> int:
    template, _ = _parts(grid)
    forms = {
        tuple(tuple(row) for row in _transform(template, code))
        for code in (1, 2, 3, 4)
    }
    return len(forms)


def _rival_differs(grid, rival) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "canonical_linked_profile": lambda grid: (
        strict_canonical_like(grid) == []
        and _rival_differs(grid, _rival_solid_bbox)
    ),
    "four_rotation_mapping_decisive": lambda grid: (
        _rotation_orbit_size(grid) == 4
        and sorted(value for row in _parts(grid)[1] for value in row) == [1, 2, 3, 4]
        and _rival_differs(grid, _rival_swap_quarter_turns)
    ),
    "command_values_not_cell_positions": lambda grid: (
        _rival_differs(grid, _rival_ignore_command_values)
    ),
    "repeated_command_control": lambda grid: (
        _profile_name(grid) == PROFILE_L_TWO_REPEAT
        and _rival_differs(grid, _rival_ignore_command_values)
    ),
    "diagonal_symmetry_control": lambda grid: (
        _profile_name(grid) == PROFILE_DIAG_MONO_ALL
        and _rival_differs(grid, _rival_solid_bbox)
    ),
    "fully_asymmetric_generalization": lambda grid: (
        _profile_name(grid) == PROFILE_FOUR_COLOR_ALL
        and _rival_differs(grid, _rival_all_identity)
    ),
}
WITNESS_RIVALS = {
    "canonical_linked_profile": ["tile_solid_template_bounding_boxes"],
    "four_rotation_mapping_decisive": [
        "all_commands_are_identity",
        "swap_clockwise_and_counterclockwise",
    ],
    "command_values_not_cell_positions": ["command_meaning_is_fixed_by_cell_position"],
    "repeated_command_control": ["command_meaning_is_fixed_by_cell_position"],
    "diagonal_symmetry_control": ["tile_solid_template_bounding_boxes"],
    "fully_asymmetric_generalization": ["all_commands_are_identity"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named shortcut compatible with the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the command-transform rule")
    if reasons:
        return reasons

    decisive_demo = any(
        _rotation_orbit_size(demo["input"]) == 4
        and sorted(value for row in _parts(demo["input"])[1] for value in row)
        == [1, 2, 3, 4]
        for demo in demos
    )
    if not decisive_demo:
        reasons.append(
            "demonstrations contain no asymmetric template exposing all four rotation codes"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute shortcut {name!r}")
    return reasons


def mutation_fixtures():
    """Named malformed scenes that structural self_check must reject."""
    valid = generate(17, 0, difficulty="medium")

    no_separator = [row[:] for row in valid]
    no_separator[0][2] = 8
    no_separator[1][2] = 8

    empty_template = [row[:] for row in valid]
    for r in range(2):
        for c in range(2):
            empty_template[r][c] = 0

    bad_command = [row[:] for row in valid]
    bad_command[0][3] = 7

    ambiguous_full_mono = [row[:] for row in valid]
    for r in range(2):
        for c in range(2):
            ambiguous_full_mono[r][c] = 8

    # Canonical marginals recombined into an unseen linked profile: the L-mono
    # template is canonical and the repeated-command multiset is canonical, but
    # their combination never appears in the five official inputs.
    recombined = [
        [8, 0, 0, 1, 4],
        [8, 8, 0, 1, 2],
    ]

    extra_separator = [row[:] for row in valid]
    extra_separator[0][0] = 0
    extra_separator[1][0] = 0

    return [
        ("no_separator", no_separator),
        ("empty_template", empty_template),
        ("command_outside_1_to_4", bad_command),
        ("fully_symmetric_template", ambiguous_full_mono),
        ("negative_linked_recombination", recombined),
        ("second_zero_column", extra_separator),
    ]
