"""Constructive generator for “keep contents matching their frame”.

Every input contains two to four disjoint rectangular frames on background 0.
A frame whose nonzero interior cells all equal the border color is preserved.
If any nonzero interior cell has another color, every nonzero interior cell of
that frame is erased.  The canonical Racket program remains label authority;
the Python mirror and rivals below make the training contract executable.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4dd02f124024"
TASK_ID = GENERATOR_ID
RULE_HASH = "1ded33eac0b5"
VERSION = "2.0.0"
SUMMARY = (
    "Keep nonzero contents when every interior color matches its rectangular "
    "frame; otherwise erase all nonzero contents inside that frame."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

PALETTE_KINDS = ("default", "warm", "cool", "varied")
INTERIOR_STYLES = ("foreign_only", "sparse_mixed", "dense_mixed")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile schedule with canonical support",
        "valid": "9..17",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile schedule with canonical support",
        "valid": "14..20",
    },
    "n_frames": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "palette_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(PALETTE_KINDS),
    },
    "interior_style": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(INTERIOR_STYLES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors",
    "two to four pairwise separated rectangular frames use distinct colors",
    "at least one frame has matching nonzero contents and at least one has mismatching contents",
    "mismatching frames contain a foreign trigger; mixed profiles also contain own-color cells that must be erased",
    "every four-example window contains mixed-content and multiple-mismatch counterexamples",
]

SCHEDULE_PROFILES = (
    "canonical_9x14",
    "mixed_10x15",
    "mixed_9x16",
    "mixed_10x16",
    "extended_12x18",
)
_PROFILE_CONFIG = {
    "canonical_9x14": {
        "grid_h": 9,
        "grid_w": 14,
        "n_frames": 2,
        "palette_kind": "default",
        "interior_style": "foreign_only",
    },
    "mixed_10x15": {
        "grid_h": 10,
        "grid_w": 15,
        "n_frames": 3,
        "palette_kind": "warm",
        "interior_style": "sparse_mixed",
    },
    "mixed_9x16": {
        "grid_h": 9,
        "grid_w": 16,
        "n_frames": 3,
        "palette_kind": "cool",
        "interior_style": "dense_mixed",
    },
    "mixed_10x16": {
        "grid_h": 10,
        "grid_w": 16,
        "n_frames": 3,
        "palette_kind": "varied",
        "interior_style": "sparse_mixed",
    },
    "extended_12x18": {
        "grid_h": 12,
        "grid_w": 18,
        "n_frames": 4,
        "palette_kind": "default",
        "interior_style": "dense_mixed",
    },
}

# The frame-color prefixes are pairwise distinguishable for every legal frame
# count.  The last item is the shared foreign interior color.
_PALETTES = {
    "default": ((2, 7, 4, 5), 9),
    "warm": ((2, 4, 6, 8), 1),
    "cool": ((1, 3, 5, 7), 8),
    "varied": ((9, 4, 7, 2), 6),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile for a default draw."""
    _validate_sample_index(sample_index)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_sample_index(sample_index):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_frames"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    for name in ("palette_kind", "interior_style"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string")


def _draw_int_axis(ctx, name, low, high, preferred):
    # Overrides always retain their full documented domain in every band.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, (preferred,))


def _draw_choice_axis(ctx, name, options, preferred):
    choices = options if ctx.overrides.get(name) is not None else (preferred,)
    return ctx.draw_choice(name, choices)


def _slot_regions(height, width):
    """Four separated regions in reading order, each at least 4x4."""
    separator_row = height // 2
    separator_col = width // 2
    return (
        (0, separator_row - 1, 0, separator_col - 1),
        (0, separator_row - 1, separator_col + 1, width - 1),
        (separator_row + 1, height - 1, 0, separator_col - 1),
        (separator_row + 1, height - 1, separator_col + 1, width - 1),
    )


def _frame_slots(n_frames):
    return (0, 3) if n_frames == 2 else tuple(range(n_frames))


def _choose_frame_rect(rng, region, difficulty):
    r_lo, r_hi, c_lo, c_hi = region
    available_h = r_hi - r_lo + 1
    available_w = c_hi - c_lo + 1
    max_h = min(6, available_h)
    max_w = min(7, available_w)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    if band == "easy":
        frame_h = 4
        frame_w = 4
    elif band == "hard":
        frame_h = rng.randint(max(4, max_h - 1), max_h)
        frame_w = rng.randint(max(4, max_w - 1), max_w)
    else:
        frame_h = rng.randint(4, min(5, max_h))
        frame_w = rng.randint(4, min(6, max_w))
    r0 = rng.randint(r_lo, r_hi - frame_h + 1)
    c0 = rng.randint(c_lo, c_hi - frame_w + 1)
    return r0, c0, r0 + frame_h - 1, c0 + frame_w - 1


def _stamp_border(grid, frame):
    color, r0, c0, r1, c1 = frame
    for col in range(c0, c1 + 1):
        grid[r0][col] = color
        grid[r1][col] = color
    for row in range(r0, r1 + 1):
        grid[row][c0] = color
        grid[row][c1] = color


def _interior_positions(frame):
    _, r0, c0, r1, c1 = frame
    return [(row, col) for row in range(r0 + 1, r1) for col in range(c0 + 1, c1)]


def _stamp_contents(grid, frame, kind, style, foreign_color, rng, difficulty):
    color = frame[0]
    interior = _interior_positions(frame)
    if kind == "match":
        upper = max(1, len(interior) // (3 if difficulty == "easy" else 2))
        count = rng.randint(1, upper)
        for row, col in rng.sample(interior, count):
            grid[row][col] = color
        return

    if style == "foreign_only":
        # One or two isolated cells cannot accidentally form another frame.
        count = rng.randint(1, min(2, len(interior)))
        for row, col in rng.sample(interior, count):
            grid[row][col] = foreign_color
        return

    positions = rng.sample(interior, len(interior))
    if style == "sparse_mixed":
        # Exactly one own-color cell and one foreign trigger leave a sparse,
        # unambiguous witness without creating a nested uniform-border frame.
        grid[positions[0][0]][positions[0][1]] = color
        grid[positions[1][0]][positions[1][1]] = foreign_color
        return

    if style == "dense_mixed":
        # A full checkerboard is dense but has no monochrome edge of length 3,
        # so the Racket scanner sees the intended outer frame and no accidental
        # interior frame that could consume the trigger before the outer scan.
        phase = rng.randrange(2)
        for row, col in interior:
            grid[row][col] = color if (row + col + phase) % 2 == 0 else foreign_color
        return

    raise ValueError(f"unknown interior_style {style!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_sample_index(sample_index)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILE_CONFIG[schedule_profile(seed, sample_index, difficulty)]
    height = _draw_int_axis(ctx, "grid_h", 9, 17, profile["grid_h"])
    width = _draw_int_axis(ctx, "grid_w", 14, 20, profile["grid_w"])
    n_frames = _draw_int_axis(ctx, "n_frames", 2, 4, profile["n_frames"])
    palette_kind = _draw_choice_axis(
        ctx, "palette_kind", PALETTE_KINDS, profile["palette_kind"]
    )
    interior_style = _draw_choice_axis(
        ctx, "interior_style", INTERIOR_STYLES, profile["interior_style"]
    )

    frame_palette, foreign_color = _PALETTES[palette_kind]
    grid = full_grid(height, width, 0)
    band_key = difficulty if difficulty is not None else "none"
    rng = ctx.draw_rng(f"geometry:{band_key}")
    regions = _slot_regions(height, width)
    mismatch_indices = {0} | ({2} if n_frames >= 3 else set())
    for frame_index, slot_index in enumerate(_frame_slots(n_frames)):
        r0, c0, r1, c1 = _choose_frame_rect(rng, regions[slot_index], difficulty)
        frame = (frame_palette[frame_index], r0, c0, r1, c1)
        _stamp_border(grid, frame)
        kind = "mismatch" if frame_index in mismatch_indices else "match"
        _stamp_contents(
            grid,
            frame,
            kind,
            interior_style,
            foreign_color,
            rng,
            difficulty,
        )
    return grid


def _well_formed_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return False
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return False
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return False
    return all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


def _scan_frames(grid):
    """Enumerate exactly the uniform-border rectangles scanned by the Racket rule."""
    if not _well_formed_grid(grid):
        return []
    height, width = len(grid), len(grid[0])
    frames = []
    for r0 in range(0, height - 2):
        for c0 in range(0, width - 2):
            color = grid[r0][c0]
            if color == 0:
                continue
            for r1 in range(r0 + 2, height):
                for c1 in range(c0 + 2, width):
                    if all(
                        grid[r0][col] == color and grid[r1][col] == color
                        for col in range(c0, c1 + 1)
                    ) and all(
                        grid[row][c0] == color and grid[row][c1] == color
                        for row in range(r0, r1 + 1)
                    ):
                        frames.append((color, r0, c0, r1, c1))
    return frames


def find_frames(grid):
    """Return maximal same-color rectangular frames in reading order.

    Dense matching interiors can themselves contain many uniform-border
    subrectangles.  Filtering same-color contained candidates recovers the
    semantic outer frames without changing the exact Racket mirror.
    """
    candidates = _scan_frames(grid)
    maximal = []
    for frame in candidates:
        color, r0, c0, r1, c1 = frame
        contained = any(
            other[0] == color
            and other != frame
            and other[1] <= r0
            and other[2] <= c0
            and other[3] >= r1
            and other[4] >= c1
            for other in candidates
        )
        if not contained:
            maximal.append(frame)
    return sorted(maximal, key=lambda item: (item[1], item[2], item[3], item[4], item[0]))


def frame_kind(grid, frame):
    color = frame[0]
    values = [grid[row][col] for row, col in _interior_positions(frame) if grid[row][col] != 0]
    if not values:
        return "empty"
    return "match" if set(values) == {color} else "mismatch"


def solve_reference_shape(grid):
    """Independent Python mirror of the canonical Racket scan/application order."""
    output = deepcopy(grid)
    for frame in _scan_frames(grid):
        color = frame[0]
        cells = [
            (row, col)
            for row, col in _interior_positions(frame)
            if output[row][col] != 0
        ]
        colors = {output[row][col] for row, col in cells}
        if cells and (len(colors) != 1 or next(iter(colors)) != color):
            for row, col in cells:
                output[row][col] = 0
    return output


# Alias used in some retained task-local probes.
rule_mirror = solve_reference_shape


def observe_overrides(grid):
    """Recover every advertised control from pixels, independently of GenCtx."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed task grid: " + "; ".join(errors))
    frames = find_frames(grid)
    frame_colors = {frame[0] for frame in frames}
    palette_matches = [
        name
        for name, (colors, _) in _PALETTES.items()
        if frame_colors == set(colors[: len(frames)])
    ]
    if len(palette_matches) != 1:
        raise ValueError(f"palette kind is not uniquely observable: {palette_matches}")

    mismatch_frames = [frame for frame in frames if frame_kind(grid, frame) == "mismatch"]
    has_own = []
    has_zero = []
    for frame in mismatch_frames:
        color = frame[0]
        all_values = [grid[row][col] for row, col in _interior_positions(frame)]
        nonzero = [value for value in all_values if value != 0]
        has_own.append(color in nonzero)
        has_zero.append(0 in all_values)
    if not any(has_own):
        style = "foreign_only"
    elif all(has_own) and all(has_zero):
        style = "sparse_mixed"
    elif all(has_own) and not any(has_zero):
        style = "dense_mixed"
    else:
        raise ValueError("interior style is not uniquely observable")

    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(frames),
        "palette_kind": palette_matches[0],
        "interior_style": style,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    height = len(grid)
    errors = []
    if not 9 <= height <= 17 or not 14 <= width <= 20:
        errors.append("grid dimensions must be 9..17 by 14..20")
    frames = find_frames(grid)
    if not 2 <= len(frames) <= 4:
        errors.append("expected two to four maximal rectangular frames")
    if len({frame[0] for frame in frames}) != len(frames):
        errors.append("maximal frame colors must be distinct")
    kinds = [frame_kind(grid, frame) for frame in frames]
    if "match" not in kinds:
        errors.append("expected at least one matching nonempty frame interior")
    if "mismatch" not in kinds:
        errors.append("expected at least one mismatching nonempty frame interior")
    if "empty" in kinds:
        errors.append("frame interiors must contain at least one nonzero cell")
    return errors


def strict_canonical_like(grid):
    """Selected lawful manifold; includes every labeled canonical input."""
    return self_check(grid)


def _erase_all_interiors(grid):
    output = deepcopy(grid)
    for frame in find_frames(grid):
        for row, col in _interior_positions(frame):
            if output[row][col] != 0:
                output[row][col] = 0
    return output


def _identity(grid):
    return deepcopy(grid)


def _erase_only_foreign(grid):
    output = deepcopy(grid)
    for frame in find_frames(grid):
        color = frame[0]
        for row, col in _interior_positions(frame):
            if output[row][col] not in (0, color):
                output[row][col] = 0
    return output


def _first_mismatch_only(grid):
    output = deepcopy(grid)
    for frame in find_frames(grid):
        if frame_kind(grid, frame) == "mismatch":
            for row, col in _interior_positions(frame):
                if output[row][col] != 0:
                    output[row][col] = 0
            break
    return output


def _match_and_mismatch(grid):
    kinds = {frame_kind(grid, frame) for frame in find_frames(grid)}
    return "match" in kinds and "mismatch" in kinds


def _mixed_mismatch(grid):
    for frame in find_frames(grid):
        if frame_kind(grid, frame) != "mismatch":
            continue
        color = frame[0]
        values = [grid[row][col] for row, col in _interior_positions(frame)]
        if color in values and any(value not in (0, color) for value in values):
            return True
    return False


def _multiple_mismatches(grid):
    return sum(frame_kind(grid, frame) == "mismatch" for frame in find_frames(grid)) >= 2


SEMANTIC_RIVALS = {
    "identity": _identity,
    "erase_all_interiors": _erase_all_interiors,
    "erase_only_foreign": _erase_only_foreign,
    "first_mismatch_only": _first_mismatch_only,
}
SEMANTIC_WITNESSES = {
    "matching_and_mismatching_frames": _match_and_mismatch,
    "mixed_mismatch_erases_own_color": _mixed_mismatch,
    "multiple_mismatching_frames": _multiple_mismatches,
}
WITNESS_RIVALS = {
    "matching_and_mismatching_frames": ["identity", "erase_all_interiors"],
    "mixed_mismatch_erases_own_color": ["erase_only_foreign"],
    "multiple_mismatching_frames": ["first_mismatch_only"],
}
CANONICAL_SHORTCUTS = {
    "erase_only_foreign": _erase_only_foreign,
    "first_mismatch_only": _first_mismatch_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite named-rival check; not a proof against arbitrary hypotheses."""
    return [
        f"{name} fits all demonstrations but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
