"""Semantic generator for ARC task 235a1d06b9d3.

The background is the value at input cell (2, 1).  The output copies input
rows zero and one, then adds a third row that contains the background wherever
row zero has background and magenta 6 everywhere else.

Published inputs use a binary signal row and an alternating left-column cue
below it.  Five linked profiles retain every complete public input morphology;
general profiles vary cue/signal relationships and canvas boundaries while
preserving that demonstrated structure.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "235a1d06b9d3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0df093c037e1"
SUMMARY = (
    "Copy rows 0 and 1, then derive row 2 by mapping row-0 background cells "
    "to the background at (2,1) and every non-background cell to color 6."
)

INVARIANTS = [
    "height >= 3 and width >= 5, so background cell (2,1) exists",
    "row 0 contains one signal color and the background at least twice each",
    "row 1 is copied verbatim and the demonstrated cue stripe alternates in column 0",
    "derived row 2 depends only on row 0 versus the background value",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "same_signal_zero",
    "same_signal_color",
    "distinct_cue_zero",
    "distinct_cue_color",
    "magenta_cue_zero",
    "magenta_cue_color",
    "magenta_signal_zero",
    "magenta_signal_color",
    "minimal_height",
    "tall_stripe",
    "wide_stripe",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng; five linked public profiles in sixteen",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_ROWS = {
    "public_train_1": (
        "07070707",
        "70000000",
        "00000000",
        "70000000",
        "00000000",
        "70000000",
    ),
    "public_train_2": (
        "2121221211",
        "7222222222",
        "2222222222",
        "7222222222",
        "2222222222",
        "7222222222",
        "2222222222",
        "7222222222",
        "2222222222",
        "7222222222",
    ),
    "public_train_3": (
        "1114111441441",
        "6444444444444",
        "4444444444444",
        "6444444444444",
        "4444444444444",
        "6444444444444",
        "4444444444444",
        "6444444444444",
        "4444444444444",
        "6444444444444",
        "4444444444444",
        "6444444444444",
    ),
    "public_train_4": (
        "49499449994",
        "79999999999",
        "99999999999",
        "79999999999",
        "99999999999",
        "79999999999",
        "99999999999",
        "79999999999",
    ),
    "public_test_1": (
        "81818",
        "41111",
        "11111",
    ),
}


def _public_literal(profile):
    """Return a fresh published input grid; outputs are never stored here."""
    return [[int(cell) for cell in row] for row in _PUBLIC_ROWS[profile]]


def _morphology_signature(grid):
    height = len(grid)
    width = len(grid[0])
    background = grid[2][1]
    signals = [value for value in grid[0] if value != background]
    if not signals or len(set(signals)) != 1:
        return None
    signal = signals[0]
    cue = grid[1][0]
    encoded = []
    for row in grid:
        encoded_row = []
        for value in row:
            if value == background:
                encoded_row.append(0)
            elif value == signal:
                encoded_row.append(1)
            elif value == 6:
                encoded_row.append(2)
            elif value == cue:
                encoded_row.append(3)
            else:
                encoded_row.append(9)
        encoded.append(tuple(encoded_row))
    return (
        height,
        width,
        background == 0,
        signal == 6,
        "same" if cue == signal else "six" if cue == 6 else "distinct",
        sum(value != background for value in grid[0]),
        # Signal positions are the per-column payload and may be permuted; the
        # complete ignored-row/cue morphology remains linked to the profile.
        tuple(encoded[1:]),
    )


_PUBLIC_SIGNATURES = {
    _morphology_signature(_public_literal(profile)): profile
    for profile in PUBLIC_PROFILES
}
if len(_PUBLIC_SIGNATURES) != len(PUBLIC_PROFILES):
    raise RuntimeError("public profile signatures collide")


def canonical_profile_signature(grid):
    if (
        not isinstance(grid, (list, tuple))
        or len(grid) < 3
        or not isinstance(grid[0], (list, tuple))
        or len(grid[0]) < 2
        or any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid)
    ):
        return None
    try:
        return _PUBLIC_SIGNATURES.get(_morphology_signature(grid))
    except (IndexError, TypeError, ValueError):
        return None


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
        if errors:
            break
    if height < 3:
        errors.append(f"need at least 3 rows, got {height}")
    if width < 5:
        errors.append(f"need at least 5 columns, got {width}")
    if errors:
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "scene_profile": None,
        }

    background = grid[2][1]
    if background == 6:
        errors.append("background color 6 collapses the demonstrated marker contrast")
    non_background = [value for value in grid[0] if value != background]
    if len(non_background) < 2:
        errors.append("row 0 needs at least two signal cells")
    if width - len(non_background) < 2:
        errors.append("row 0 needs at least two background cells")
    signal_colors = set(non_background)
    signal = next(iter(signal_colors)) if len(signal_colors) == 1 else None
    if signal is None:
        errors.append(f"row 0 needs exactly one signal color, got {sorted(signal_colors)}")

    cue = grid[1][0]
    if cue == background:
        errors.append("left-column cue must differ from the background")
    for row in range(1, height):
        expected_left = cue if row % 2 == 1 else background
        if grid[row][0] != expected_left:
            errors.append(f"row {row} has the wrong alternating column-0 cue")
            break
        if any(value != background for value in grid[row][1:]):
            errors.append(f"row {row} has non-background content outside the cue column")
            break

    profile = canonical_profile_signature(grid) if not errors else None
    cue_relation = None
    if not errors and profile is None:
        if signal == 6:
            cue_relation = "magenta_signal"
        elif cue == 6:
            cue_relation = "magenta_cue"
        elif cue == signal:
            cue_relation = "same_signal"
        else:
            cue_relation = "distinct_cue"
        if height == 3:
            profile = "minimal_height"
        elif height >= 15:
            profile = "tall_stripe"
        elif width >= 16:
            profile = "wide_stripe"
        else:
            profile = f"{cue_relation}_{'zero' if background == 0 else 'color'}"
    elif not errors:
        if signal == 6:
            cue_relation = "magenta_signal"
        elif cue == 6:
            cue_relation = "magenta_cue"
        elif cue == signal:
            cue_relation = "same_signal"
        else:
            cue_relation = "distinct_cue"

    if profile not in SCENE_PROFILES and not errors:
        errors.append(f"unrecognized scene profile {profile!r}")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "background": background,
        "signal": signal,
        "cue": cue,
        "cue_relation": cue_relation,
        "signal_count": len(non_background),
        "background_count": width - len(non_background),
        "scene_profile": profile,
    }


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical Racket rule."""
    if len(grid) < 3 or len(grid[0]) < 2:
        raise ValueError("rule requires at least a 3x2 grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("rule requires a rectangular grid")
    background = grid[2][1]
    return [
        list(grid[0]),
        list(grid[1]),
        [background if value == background else 6 for value in grid[0]],
    ]


def _choose_color(rng, *, exclude=()):
    choices = [color for color in range(10) if color not in set(exclude)]
    return rng.choice(choices)


def _binary_mask(rng, width):
    pattern = rng.choice(("random", "alternating", "blocks", "sparse"))
    if pattern == "alternating":
        mask = [(col + rng.randrange(2)) % 2 for col in range(width)]
    elif pattern == "blocks":
        block = rng.randint(1, max(1, width // 3))
        phase = rng.randrange(2)
        mask = [((col // block) + phase) % 2 for col in range(width)]
    elif pattern == "sparse":
        mask = [1] * width
        step = rng.randint(2, max(2, width // 2))
        for col in range(rng.randrange(step), width, step):
            mask[col] = 0
    else:
        mask = [rng.randrange(2) for _ in range(width)]
    if sum(mask) < 2:
        mask[0] = mask[-1] = 1
    if width - sum(mask) < 2:
        mask[0] = mask[-1] = 0
    return mask


def _normal_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(4, 7), rng.randint(6, 10)
    if difficulty == "hard":
        return rng.randint(9, 14), rng.randint(11, 15)
    return rng.randint(6, 12), rng.randint(8, 15)


def _colors_for_profile(rng, profile):
    wants_zero = profile.endswith("_zero")
    background = 0 if wants_zero else _choose_color(rng, exclude={0, 6})
    if profile.startswith("magenta_signal"):
        signal = 6
        cue = _choose_color(rng, exclude={background, 6})
    else:
        signal = _choose_color(rng, exclude={background, 6})
        if profile.startswith("same_signal"):
            cue = signal
        elif profile.startswith("magenta_cue"):
            cue = 6
        else:
            cue = _choose_color(rng, exclude={background, signal, 6})
    return background, signal, cue


def _construct_grid(rng, height, width, background, signal, cue):
    mask = _binary_mask(rng, width)
    grid = [[background for _ in range(width)] for _ in range(height)]
    grid[0] = [signal if bit else background for bit in mask]
    for row in range(1, height, 2):
        grid[row][0] = cue
    return grid


def _general_grid(rng, difficulty, profile):
    if profile == "minimal_height":
        height, width = 3, rng.randint(5, 12)
        colors_profile = "distinct_cue_color"
    elif profile == "tall_stripe":
        height, width = rng.randint(15, 22), rng.randint(7, 14)
        colors_profile = rng.choice(("same_signal_zero", "distinct_cue_color"))
    elif profile == "wide_stripe":
        height, width = rng.randint(5, 14), rng.randint(16, 24)
        colors_profile = rng.choice(("magenta_cue_color", "distinct_cue_zero"))
    else:
        height, width = _normal_dimensions(rng, difficulty)
        colors_profile = profile
    background, signal, cue = _colors_for_profile(rng, colors_profile)
    for _ in range(100):
        grid = _construct_grid(rng, height, width, background, signal, cue)
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"failed to synthesize {profile}")


def _generate_public(rng, profile):
    literal = _public_literal(profile)
    background = literal[2][1]
    signal = next(value for value in literal[0] if value != background)
    cue = literal[1][0]
    new_background = 0 if background == 0 else _choose_color(rng, exclude={0, 6})
    new_signal = _choose_color(rng, exclude={new_background, 6})
    if cue == signal:
        new_cue = new_signal
    elif cue == 6:
        new_cue = 6
    else:
        new_cue = _choose_color(rng, exclude={new_background, new_signal, 6})
    mapping = {background: new_background, signal: new_signal, cue: new_cue}
    recolored = [[mapping.get(value, value) for value in row] for row in literal]
    # The rule is column-wise and the cue stripe carries no horizontal anchor;
    # signal-column placement is a nuisance while its count stays profile-linked.
    rng.shuffle(recolored[0])
    return recolored


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    rng = context.draw_rng("scene")
    grid = (
        _generate_public(rng, profile)
        if profile in PUBLIC_PROFILES
        else _general_grid(rng, difficulty, profile)
    )
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed grids and nearest signal/cue/profile impostors."""
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
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    if not errors:
        output = rule_mirror(grid)
        if len(output) != 3 or any(len(row) != info["width"] for row in output):
            errors.append("rule mirror must emit exactly 3 x width")
        if output[:2] != [list(grid[0]), list(grid[1])]:
            errors.append("rule mirror failed to copy the first two rows")
        expected = [
            info["background"] if value == info["background"] else 6
            for value in grid[0]
        ]
        if output[2] != expected:
            errors.append("rule mirror derived the wrong marker row")
    return errors
