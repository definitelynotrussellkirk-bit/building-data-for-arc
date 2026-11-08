"""Generate four-section shifted-difference sequences for aea4d55345a1."""

from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "aea4d55345a1"
TASK_ID = "aea4d55345a1"
VERSION = "3.1.0"
RULE_HASH = "3af11f1e6cf1"
SUMMARY = (
    "Four equal sections separated by full gray rows show a changing "
    "pattern; predict the next section by shifting the latest cell diff "
    "and carrying a prior row diff when the latest step skipped that row."
)

PUBLIC_PROFILES = (
    "public_grow_bar",
    "public_translate_motif",
    "public_staggered_carry",
)
EXTRAPOLATION_PROFILES = (
    "boundary_growth",
    "motif_translation",
    "staggered_carry",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES
CARRY_PROFILES = ("public_staggered_carry", "staggered_carry")
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across all complete profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INVARIANTS = [
    "exactly four equal sections are separated by three full color-5 rows",
    "the two latest section diffs have a nonzero horizontal displacement",
    "the fifth-section prediction is in bounds and differs from section four",
    "one or two nonzero non-gray colors form growth, translation, or carry",
]

# Default draws follow a period-three semantic curriculum: two carry-capable
# residues followed by one non-carry residue.  Each pool keeps the public-profile
# prior at exactly 25%, so the prior remains stable while every four-pair window
# contains at least two examples that refute the no-carry shortcut.
_CARRY_PROFILE_POOLS = {
    band: (
        "public_staggered_carry",
        "staggered_carry",
        "staggered_carry",
        "staggered_carry",
    )
    for band in ("easy", "medium", "hard")
}
_NON_CARRY_PROFILE_POOLS = {
    "easy": (
        "public_grow_bar",
        "public_translate_motif",
        "boundary_growth",
        "boundary_growth",
        "boundary_growth",
        "boundary_growth",
        "motif_translation",
        "motif_translation",
    ),
    "medium": (
        "public_grow_bar",
        "public_translate_motif",
        "boundary_growth",
        "boundary_growth",
        "boundary_growth",
        "motif_translation",
        "motif_translation",
        "motif_translation",
    ),
    "hard": (
        "public_grow_bar",
        "public_translate_motif",
        "boundary_growth",
        "boundary_growth",
        "motif_translation",
        "motif_translation",
        "motif_translation",
        "motif_translation",
    ),
}


def schedule_requires_carry(sample_index):
    """Whether the default semantic schedule requires a carry witness."""
    return int(sample_index) % LESSON_SCHEDULE_PERIOD in (0, 1)


def _rows(*encoded):
    rows = [[int(value) for value in row] for row in encoded]
    if any(len(row) != 13 for row in rows):
        raise RuntimeError("public row encoding must have width 13")
    return rows


_PUBLIC_CARRY_SECTIONS = (
    _rows(
        "0010001000100",
        "0211011101110",
        "2211111111111",
    ),
    _rows(
        "0020001000100",
        "0221011101110",
        "2221111111111",
    ),
    _rows(
        "0020001000100",
        "0222011101110",
        "2222111111111",
    ),
    _rows(
        "0020001000100",
        "0222011101110",
        "2222211111111",
    ),
)


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _assemble(sections):
    width = len(sections[0][0])
    grid = []
    for index, section in enumerate(sections):
        grid.extend([row[:] for row in section])
        if index < len(sections) - 1:
            grid.append([5] * width)
    return grid


def _build_public_roles(profile):
    if profile == "public_grow_bar":
        sections = []
        for length in (2, 4, 6, 8):
            section = _blank(3, 13)
            for col in range(length):
                section[1][col] = 1
            sections.append(section)
        return sections
    if profile == "public_translate_motif":
        sections = []
        for step in range(4):
            section = _blank(3, 13)
            start = 1 + step
            section[1][start] = 1
            section[1][start + 1] = 1
            section[1][start + 2] = 2
            sections.append(section)
        return sections
    if profile == "public_staggered_carry":
        return [
            [row[:] for row in section]
            for section in _PUBLIC_CARRY_SECTIONS
        ]
    raise KeyError(profile)


_PUBLIC_ROLE_GRIDS = {
    profile: _assemble(_build_public_roles(profile))
    for profile in PUBLIC_PROFILES
}


def _normalize_roles(grid):
    colors = []
    for row in grid:
        for value in row:
            if value not in (0, 5) and value not in colors:
                colors.append(value)
    roles = {0: 0, 5: 5}
    roles.update({color: index + 1 for index, color in enumerate(colors)})
    return tuple(
        tuple(roles.get(value, value) for value in row)
        for row in grid
    )


_PUBLIC_LOOKUP = {
    _normalize_roles(grid): profile
    for profile, grid in _PUBLIC_ROLE_GRIDS.items()
}


def _canonical_answer_profile(grid):
    return _PUBLIC_LOOKUP.get(_normalize_roles(grid))


def _split_sections(grid, *, full_rows=False):
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if full_rows:
        seps = [
            row
            for row, values in enumerate(grid)
            if all(value == 5 for value in values)
        ]
    else:
        seps = [row for row in range(len(grid)) if grid[row][0] == 5]
    if not seps:
        raise ValueError("no separator rows")
    section_height = seps[0]
    starts = [0] + [row + 1 for row in seps]
    sections = [
        [values[:] for values in grid[start : start + section_height]]
        for start in starts
    ]
    if any(len(section) != section_height for section in sections):
        raise ValueError("truncated section")
    return seps, section_height, sections


def _diff(first, second):
    return [
        (row, col, first[row][col], second[row][col])
        for row in range(len(first))
        for col in range(len(first[0]))
        if first[row][col] != second[row][col]
    ]


def solve_python(grid):
    """Input-pure mirror of the authoritative shifted-diff Racket rule."""
    _, section_height, sections = _split_sections(grid)
    if len(sections) < 3:
        raise ValueError("at least three sections are required")
    s_pprev, s_prev, s_last = sections[-3:]
    d_prev = _diff(s_pprev, s_prev)
    d_last = _diff(s_prev, s_last)
    d_last_rows = {row for row, _, _, _ in d_last}
    carry_diffs = [
        diff for diff in d_prev if diff[0] not in d_last_rows
    ]
    col_shift = 0
    if d_prev and d_last:
        col_shift = min(diff[1] for diff in d_last) - min(
            diff[1] for diff in d_prev
        )
    width = len(s_last[0])
    output = _blank(section_height, width)
    for row in range(section_height):
        for col in range(width):
            moved = next(
                (
                    diff
                    for diff in d_last
                    if diff[0] == row and diff[1] + col_shift == col
                ),
                None,
            )
            carried = next(
                (
                    diff
                    for diff in carry_diffs
                    if (
                        diff[0] == row
                        and col > diff[1]
                        and s_last[row][col] == diff[2]
                        and not any(
                            s_last[row][between] == diff[2]
                            for between in range(diff[1] + 1, col)
                        )
                    )
                ),
                None,
            )
            if moved is not None and s_last[row][col] == moved[2]:
                output[row][col] = moved[3]
            elif carried is not None:
                output[row][col] = carried[3]
            else:
                output[row][col] = s_last[row][col]
    return output


def repeat_latest_diff_without_carry(grid):
    """Finite rival: shift only the newest diff and ignore carried rows."""
    _, _section_height, sections = _split_sections(grid)
    if len(sections) < 3:
        raise ValueError("at least three sections are required")
    s_pprev, s_prev, s_last = sections[-3:]
    d_prev = _diff(s_pprev, s_prev)
    d_last = _diff(s_prev, s_last)
    col_shift = (
        min(diff[1] for diff in d_last)
        - min(diff[1] for diff in d_prev)
        if d_prev and d_last
        else 0
    )
    output = [row[:] for row in s_last]
    for row, col, old, new in d_last:
        target = col + col_shift
        if 0 <= target < len(output[0]) and output[row][target] == old:
            output[row][target] = new
    return output


SEMANTIC_RIVALS = {
    "repeat_latest_diff_without_carry": repeat_latest_diff_without_carry,
}
# Canonical examples already refute this partial heuristic; it belongs only
# to generated-lesson assembly and witness checks.
CANONICAL_SHORTCUTS = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "carry_changes_prediction": lambda grid: (
        repeat_latest_diff_without_carry(grid) != solve_python(grid)
    ),
}
WITNESS_RIVALS = {
    "carry_changes_prediction": ["repeat_latest_diff_without_carry"],
}


def _active_cells(section):
    return {
        (row, col, value)
        for row in range(len(section))
        for col, value in enumerate(section[row])
        if value != 0
    }


def _translation_shift(sections):
    active = [_active_cells(section) for section in sections]
    if any(not cells for cells in active):
        return None
    lefts = [min(col for _, col, _ in cells) for cells in active]
    shifts = [second - first for first, second in zip(lefts, lefts[1:])]
    if not shifts or len(set(shifts)) != 1 or shifts[0] == 0:
        return None
    shift = shifts[0]
    for step, cells in enumerate(active):
        if cells != {
            (row, col + step * shift, value)
            for row, col, value in active[0]
        }:
            return None
    return shift


def _boundary_growth_increment(sections):
    colors = {
        value
        for section in sections
        for row in section
        for value in row
        if value != 0
    }
    if len(colors) != 1:
        return None
    runs = []
    for section in sections:
        cells = [(row, col) for row, col, _ in _active_cells(section)]
        rows = {row for row, _ in cells}
        if len(rows) != 1:
            return None
        row = next(iter(rows))
        cols = sorted(col for _, col in cells)
        if cols != list(range(cols[0], cols[-1] + 1)):
            return None
        runs.append((row, cols[0], cols[-1], len(cols)))
    if len({run[0] for run in runs}) != 1:
        return None
    width = len(sections[0][0])
    if not (
        all(run[1] == 0 for run in runs)
        or all(run[2] == width - 1 for run in runs)
    ):
        return None
    increments = [
        second[3] - first[3] for first, second in zip(runs, runs[1:])
    ]
    if (
        len(set(increments)) != 1
        or increments[0] <= 0
        or runs[-1][3] + increments[0] > width
    ):
        return None
    return increments[0]


def _classify_scene(sections, answer_profile):
    if answer_profile is not None:
        return answer_profile
    if _boundary_growth_increment(sections) is not None:
        return "boundary_growth"
    if _translation_shift(sections) is not None:
        return "motif_translation"
    d_prev = _diff(sections[-3], sections[-2])
    d_last = _diff(sections[-2], sections[-1])
    if {row for row, _, _, _ in d_prev} - {
        row for row, _, _, _ in d_last
    }:
        return "staggered_carry"
    return None


def _analyze(grid):
    reasons = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}
    height = len(grid)
    if not 11 <= width <= 18:
        reasons.append("width_range")
    seps = [
        row
        for row, values in enumerate(grid)
        if all(value == 5 for value in values)
    ]
    if len(seps) != 3:
        reasons.append("separator_count")
    section_height = seps[0] if seps else 0
    if not 3 <= section_height <= 5:
        reasons.append("section_height")
    if (
        seps
        != [
            section_height,
            2 * section_height + 1,
            3 * section_height + 2,
        ]
        or height != 4 * section_height + 3
    ):
        reasons.append("section_geometry")
    if any(
        grid[row][col] == 5
        for row in range(height)
        if row not in seps
        for col in range(width)
    ):
        reasons.append("gray_inside_section")
    colors = {value for row in grid for value in row}
    active_colors = sorted(colors - {0, 5})
    if 0 not in colors:
        reasons.append("missing_background")
    if not 1 <= len(active_colors) <= 2:
        reasons.append("active_color_count")
    if (
        len(seps) != 3
        or section_height < 1
        or height != 4 * section_height + 3
    ):
        return {
            "strict": False,
            "reasons": sorted(set(reasons)),
        }
    starts = (
        0,
        section_height + 1,
        2 * section_height + 2,
        3 * section_height + 3,
    )
    sections = [
        [row[:] for row in grid[start : start + section_height]]
        for start in starts
    ]
    if any(not _active_cells(section) for section in sections):
        reasons.append("four_nonempty_sections")
    d_prev = _diff(sections[-3], sections[-2])
    d_last = _diff(sections[-2], sections[-1])
    if not d_prev or not d_last:
        reasons.append("empty_recent_diff")
        col_shift = 0
    else:
        col_shift = min(diff[1] for diff in d_last) - min(
            diff[1] for diff in d_prev
        )
        if col_shift == 0 or abs(col_shift) > 2:
            reasons.append("diff_column_shift")
    d_last_rows = {row for row, _, _, _ in d_last}
    carry_rows = {
        row for row, _, _, _ in d_prev if row not in d_last_rows
    }
    try:
        output = solve_python(grid)
    except Exception as exc:
        reasons.append(f"oracle:{type(exc).__name__}")
        output = sections[-1]
    if output == sections[-1]:
        reasons.append("identity_prediction")
    answer_profile = _canonical_answer_profile(grid)
    scene_profile = _classify_scene(sections, answer_profile)
    if scene_profile is None:
        reasons.append("unclassified_sequence")
    active_count = sum(
        value not in (0, 5)
        for section in sections
        for row in section
        for value in row
    )
    active_density = active_count / (4 * section_height * width)
    if not 0.01 <= active_density <= 0.75:
        reasons.append("active_density")
    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "section_height": section_height,
        "active_colors": tuple(active_colors),
        "active_color_count": len(active_colors),
        "active_count": active_count,
        "active_density": active_density,
        "d_prev_size": len(d_prev),
        "d_last_size": len(d_last),
        "col_shift": col_shift,
        "carry_row_count": len(carry_rows),
        "canonical_answer_profile": answer_profile,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete four-section lesson from the returned grid."""
    return _analyze(grid)["reasons"]


def lesson_identifiable(demos, query):
    """Reject invalid labels and lessons where the no-carry rival survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside grammar: {errors[0]}")
            continue
        if solve_python(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output does not match shifted-diff rule")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name} fits every demonstration")
    return sorted(set(reasons))


def _band_dimensions(band, rng):
    if band == "easy":
        return 3, rng.randint(11, 13)
    if band == "hard":
        return rng.randint(3, 5), rng.randint(14, 18)
    return rng.randint(3, 4), rng.randint(12, 16)


def _boundary_growth(band, rng, color):
    section_height, width = _band_dimensions(band, rng)
    increment = rng.choice((1, 2))
    max_start = width - 4 * increment
    start_length = rng.randint(1, min(4, max_start))
    row = rng.randrange(section_height)
    grow_left_to_right = bool(rng.randrange(2))
    sections = []
    for step in range(4):
        length = start_length + step * increment
        section = _blank(section_height, width)
        start = 0 if grow_left_to_right else width - length
        for col in range(start, start + length):
            section[row][col] = color
        sections.append(section)
    return sections


def _motif_translation(band, rng, colors):
    section_height, width = _band_dimensions(band, rng)
    variant = rng.choice(("line", "elbow", "spaced"))
    if variant == "line":
        motif_width = rng.randint(3, min(5, width - 4))
        row = rng.randrange(section_height)
        motif = [
            (row, col, colors[col % len(colors)])
            for col in range(motif_width)
        ]
    elif variant == "elbow" and section_height >= 2:
        motif_width = 3
        top = rng.randrange(section_height - 1)
        motif = (
            (top, 0, colors[0]),
            (top, 1, colors[0]),
            (top + 1, 1, colors[-1]),
            (top + 1, 2, colors[-1]),
        )
    else:
        motif_width = 4
        row = rng.randrange(section_height)
        motif = (
            (row, 0, colors[0]),
            (row, 2, colors[-1]),
            (row, 3, colors[0]),
        )
    feasible = [
        shift
        for shift in (-2, -1, 1, 2)
        if motif_width + 4 * abs(shift) <= width
    ]
    shift = rng.choice(feasible)
    if shift > 0:
        start = rng.randint(0, width - motif_width - 4 * shift)
    else:
        start = rng.randint(-4 * shift, width - motif_width)
    sections = []
    for step in range(4):
        section = _blank(section_height, width)
        offset = start + step * shift
        for row, col, color in motif:
            section[row][col + offset] = color
        sections.append(section)
    return sections


def _staggered_carry(band, rng, base_color, accent_color):
    section_height, width = _band_dimensions(band, rng)
    active_count = rng.randint(2, section_height)
    active_rows = sorted(rng.sample(range(section_height), active_count))
    carry_count = rng.randint(1, active_count - 1)
    carry_rows = set(rng.sample(active_rows, carry_count))
    frontier = rng.randint(2, min(4, width - 5))
    sections = [_blank(section_height, width) for _ in range(4)]

    for row in range(section_height):
        if row not in active_rows:
            for section in sections:
                for col in range((row + 1) % 3, width, 4):
                    section[row][col] = base_color
            continue
        base_positions = set(range(frontier + 3))
        if row in carry_rows:
            base_positions.discard(frontier + 1)
        for col in range(frontier + 4, width):
            if (col + row) % 3 == 0:
                base_positions.add(col)
        base_positions.update((frontier - 1, frontier, frontier + 2))
        if row not in carry_rows:
            base_positions.add(frontier + 1)
        accent_steps = (
            {col for col in base_positions if col <= frontier - 2},
            {col for col in base_positions if col <= frontier - 1},
            {col for col in base_positions if col <= frontier},
            {
                col
                for col in base_positions
                if col <= (
                    frontier if row in carry_rows else frontier + 1
                )
            },
        )
        for index, section in enumerate(sections):
            for col in base_positions:
                section[row][col] = base_color
            for col in accent_steps[index]:
                section[row][col] = accent_color
    return sections


def _draw_palette(profile, rng):
    available = [1, 2, 3, 4, 6, 7, 8, 9]
    if profile in ("public_grow_bar", "boundary_growth"):
        choices = (
            [color for color in available if color != 1]
            if profile == "public_grow_bar"
            else available
        )
        return (rng.choice(choices),)
    while True:
        first = rng.choice(available)
        second = rng.choice([color for color in available if color != first])
        if (
            profile
            not in ("public_translate_motif", "public_staggered_carry")
            or (first, second) != (2, 3)
        ):
            return first, second


def _recolor_roles(sections, colors):
    mapping = {0: 0, 1: colors[0]}
    if len(colors) > 1:
        mapping[2] = colors[1]
    return [
        [
            [mapping[value] for value in row]
            for row in section
        ]
        for section in sections
    ]


def observe_overrides(grid):
    """Recover the one declared semantic control from the returned grid."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    return {"scene_profile": analysis["scene_profile"]}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _CARRY_PROFILE_POOLS else "medium"
    if "scene_profile" in overrides:
        profile_options = SCENE_PROFILES
    elif schedule_requires_carry(sample_index):
        profile_options = _CARRY_PROFILE_POOLS[band]
    else:
        profile_options = _NON_CARRY_PROFILE_POOLS[band]
    profile = ctx.draw_choice("scene_profile", profile_options)
    scene_rng = ctx.draw_rng("scene")
    palette_rng = ctx.draw_rng("palette")
    colors = _draw_palette(profile, palette_rng)

    if profile in PUBLIC_PROFILES:
        roles = _build_public_roles(profile)
        sections = _recolor_roles(roles, colors)
    elif profile == "boundary_growth":
        sections = _boundary_growth(band, scene_rng, colors[0])
    elif profile == "motif_translation":
        sections = _motif_translation(band, scene_rng, colors)
    elif profile == "staggered_carry":
        sections = _staggered_carry(
            band,
            scene_rng,
            colors[0],
            colors[1],
        )
    else:
        raise RuntimeError(f"unhandled scene profile {profile!r}")

    if (
        profile in EXTRAPOLATION_PROFILES
        and _canonical_answer_profile(_assemble(sections)) is not None
    ):
        # Keep the declared scene_profile exactly observable even when a
        # random extrapolation lands on one complete public morphology.
        sections = [
            section[1:] + section[:1]
            for section in sections
        ]
    grid = _assemble(sections)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(
            f"constructed invalid {profile!r} scene: {errors}"
        )
    return [row[:] for row in grid]
