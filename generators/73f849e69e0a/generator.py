"""Generator for 73f849e69e0a — compress an icon, stamp it at red markers.

Canonical inputs contain a 6x6 icon made from uniform 2x2 blocks, a full row
of 5s, then a marker field containing only background 0 and red 2.  The rule
reads the 3x3 logical icon at rows/columns 0,2,4 and stamps that icon once for
every red marker in the field.  Color 2 is role-overloaded: it may be both a
real icon color above the separator and the marker color below it.

The teaching schedule alternates canonical-scale anchors with separator-row
contrasts.  Every three-demo window therefore contains a scene that refutes the
canonical-only shortcut "the separator is always row 6" plus scenes where red
is an icon payload color, so marker-vs-payload roles cannot be conflated.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "73f849e69e0a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Updated atomically if the selected commented Racket source is synchronized.
RULE_HASH = "5a8d0a3601e2"

SUMMARY = (
    "A uniform-2x2-block icon occupies the first six rows, followed by one "
    "full separator row of color 5 and a 0/2 marker field. Compress the icon "
    "to its 3x3 stride-2 values. Create a fresh canvas three times the marker "
    "field height and width, then stamp that 3x3 icon at every red(2) marker. "
    "Red may also be an icon color; above the separator it is payload, below "
    "the separator it is a stamp marker."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15

INVARIANTS = [
    "exactly one full row of color 5 separates icon and marker field",
    "the first 6x6 icon area is nine uniform 2x2 blocks",
    "rows between the 6-row icon and a later separator, and top columns after column 5, are zero padding",
    "the marker field contains only 0 and red(2), with at least one red marker",
    "the 3x3 logical icon has at least one nonzero cell; red(2) is legal icon payload",
    "3*marker-field height and 3*marker-field width stay within ARC's 30x30 limit",
]

COUNTER_HYPOTHESES = [
    "assume the separator is always canonical row 6 instead of locating the full row of 5s",
    "treat red(2) above the separator as a marker/background role and drop it from the icon",
    "use only the number of red markers and ignore their positions",
    "stamp only the first red marker rather than every marker",
    "replace the multicolor icon by solid red or by its modal nonzero color",
]

# Exact externally overridable axes.  Explicit overrides use these full ranges
# in every difficulty band; ordinary draws use the four-role lesson schedule.
AXES = {
    "sep_row": {
        "type": "int",
        "default": "schedule 6,7,8,6",
        "valid": "6..8",
        "doc": "Exact full-color-5 separator row index.",
    },
    "bot_h": {
        "type": "int",
        "default": "canonical anchors 6; contrast draws difficulty-aware 5..8",
        "valid": "5..8",
        "doc": "Exact marker-field height; output height is 3*bot_h.",
    },
    "bot_w": {
        "type": "int",
        "default": "canonical anchors 6; contrast draws difficulty-aware 6..8",
        "valid": "6..8",
        "doc": "Exact grid/marker-field width; output width is 3*bot_w.",
    },
    "n_twos": {
        "type": "int",
        "default": "canonical anchors 5..8; contrast draws difficulty-aware 3..12",
        "valid": "3..12",
        "doc": "Exact number of red(2) stamp markers in the marker field.",
    },
}

SCHEDULE_PROFILES = (
    "canonical_anchor_red_payload",
    "separator_row_7_role_contrast",
    "separator_row_8_role_contrast",
    "canonical_anchor_no_red_payload",
)

_ICON_EXTRA_COLORS = (1, 3, 4, 6, 7, 8, 9)


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, lo, hi in (
        ("sep_row", 6, 8),
        ("bot_h", 5, 8),
        ("bot_w", 6, 8),
        ("n_twos", 3, 12),
    ):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or isinstance(value, bool) or not lo <= value <= hi
        ):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _axis_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    """Band/schedule defaults, but explicit overrides are band-independent."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty rectangular sequence"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} must lie within 1..30")
    for row in grid:
        for value in row:
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                return {"errors": errors, "height": height, "width": width}

    sep_rows = [
        r for r, row in enumerate(grid)
        if all(value == 5 for value in row)
    ]
    if len(sep_rows) != 1:
        errors.append(
            f"expected exactly one full color-5 separator row, found {len(sep_rows)}"
        )
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "separator_rows": sep_rows,
        }

    sep = sep_rows[0]
    if sep < 6:
        errors.append("separator must follow at least the six icon rows")
    bot_h = height - sep - 1
    if bot_h < 1:
        errors.append("marker field below separator must be non-empty")
    if width < 6:
        errors.append("grid width must be at least 6 for the 6x6 icon encoding")
    if bot_h > 0 and 3 * bot_h > 30:
        errors.append(f"3*marker-field height exceeds 30: bot_h={bot_h}")
    if 3 * width > 30:
        errors.append(f"3*marker-field width exceeds 30: width={width}")

    # Color 5 has one structural role only.  A stray 5 would make the visual
    # separator cue ambiguous even if it did not form another complete row.
    stray_fives = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5 and r != sep
    ]
    if stray_fives:
        errors.append("color 5 may appear only in the separator row")

    icon = [[0] * 3 for _ in range(3)]
    block_mismatches = []
    if sep >= 6 and width >= 6:
        for dr in range(3):
            for dc in range(3):
                rr, cc = 2 * dr, 2 * dc
                value = grid[rr][cc]
                icon[dr][dc] = value
                for ar in (0, 1):
                    for ac in (0, 1):
                        if grid[rr + ar][cc + ac] != value:
                            block_mismatches.append((dr, dc))
                            break
                    if block_mismatches and block_mismatches[-1] == (dr, dc):
                        break
        if block_mismatches:
            errors.append(
                "first 6x6 icon area must be uniform within every 2x2 block"
            )
        # Width and separator location are allowed to vary, but the extra top
        # area is explicit zero padding.  This makes the sampled 6x6 icon role
        # observable rather than introducing undeclared foreground semantics.
        if any(grid[r][c] != 0 for r in range(min(sep, 6)) for c in range(6, width)):
            errors.append("top columns after the 6x6 icon must be zero padding")
        if sep > 6 and any(grid[r][c] != 0 for r in range(6, sep) for c in range(width)):
            errors.append("rows between the icon and separator must be zero padding")

    icon_nonzero = [value for row in icon for value in row if value != 0]
    if sep >= 6 and width >= 6 and not icon_nonzero:
        errors.append("logical 3x3 icon must contain at least one nonzero cell")

    markers: list[tuple[int, int]] = []
    foreign_bottom: list[tuple[int, int, int]] = []
    if bot_h > 0:
        for br, row in enumerate(grid[sep + 1 :]):
            for bc, value in enumerate(row):
                if value == 2:
                    markers.append((br, bc))
                elif value != 0:
                    foreign_bottom.append((br, bc, value))
        if foreign_bottom:
            errors.append("marker field may contain only background 0 and red(2)")
        if not markers:
            errors.append("marker field must contain at least one red(2) stamp marker")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "sep_row": sep,
        "bot_h": bot_h,
        "bot_w": width,
        "icon": icon,
        "icon_nonzero": icon_nonzero,
        "icon_nonzero_count": len(icon_nonzero),
        "icon_colors": sorted(set(icon_nonzero)),
        "markers": markers,
        "n_twos": len(markers),
        "palette": sorted({value for row in grid for value in row}),
    }


def semantic_observables(grid) -> dict:
    """Recover exact axes and task-linked cue/role facts from an input grid."""
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    markers = analysis["markers"]
    return {
        "sep_row": analysis["sep_row"],
        "bot_h": analysis["bot_h"],
        "bot_w": analysis["bot_w"],
        "n_twos": analysis["n_twos"],
        "icon_nonzero_count": analysis["icon_nonzero_count"],
        "icon_color_count": len(analysis["icon_colors"]),
        "icon_contains_red": 2 in analysis["icon_colors"],
        "marker_row_count": len({r for r, _ in markers}),
        "marker_col_count": len({c for _, c in markers}),
        "palette_size": len(analysis["palette"]),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural input grammar; canonical inputs all satisfy it."""
    del difficulty, meta
    return list(_grid_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, allowing harmless icon-color renaming."""
    analysis = _grid_analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["sep_row"], analysis["bot_h"], analysis["bot_w"]) != (6, 6, 6):
        reasons.append("canonical profile is six icon rows + separator + 6x6 marker field")
    if len(analysis["palette"]) not in (5, 6):
        reasons.append("canonical input palette size is 5 or 6")
    if not 4 <= analysis["icon_nonzero_count"] <= 7:
        reasons.append("canonical logical icon has 4..7 nonzero cells")
    if not 5 <= analysis["n_twos"] <= 12:
        reasons.append("canonical marker field contains 5..12 red markers")
    return reasons


def _pick_icon(role: int, rng) -> list[list[int]]:
    """Return a nontrivial 3x3 logical icon; roles 0/1/2 carry red payload."""
    if role == 0:
        # Canonical exact palette size 5: {0,2,5} + two payload colors.
        colors = [2, *rng.sample(_ICON_EXTRA_COLORS, 2)]
    elif role == 3:
        # Canonical exact palette size 6 without red in the icon.
        colors = list(rng.sample(_ICON_EXTRA_COLORS, 3))
    elif role == 1:
        colors = [2, *rng.sample(_ICON_EXTRA_COLORS, 3)]
    else:
        colors = [2, *rng.sample(_ICON_EXTRA_COLORS, 2)]

    count = rng.randint(max(5, len(colors)), 7)
    positions = rng.sample(range(9), count)
    rng.shuffle(colors)
    icon = [[0] * 3 for _ in range(3)]
    for index, flat in enumerate(positions):
        r, c = divmod(flat, 3)
        icon[r][c] = colors[index % len(colors)]
    # Every chosen payload color must be visible.  The cycling assignment above
    # guarantees this because count >= len(colors).
    return icon


def _pick_markers(bot_h: int, bot_w: int, n_twos: int, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(bot_h) for c in range(bot_w)]
    first_n = set(cells[:n_twos])
    for _ in range(128):
        chosen = rng.sample(cells, n_twos)
        rows = {r for r, _ in chosen}
        cols = {c for _, c in chosen}
        if len(rows) >= 2 and len(cols) >= 2 and set(chosen) != first_n:
            return chosen
    raise ValueError("could not construct a position-informative marker field")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    role = sample_index % len(SCHEDULE_PROFILES)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # anchor / both-controls / both-controls / anchor: every length-3 window
    # includes a noncanonical separator row, while half of all draws remain at
    # exact canonical dimensions and palette profile.
    scheduled_sep = (6, 7, 8, 6)[role]
    sep_row = _axis_int(ctx, overrides, "sep_row", scheduled_sep, scheduled_sep, 6, 8)

    if role in (0, 3):
        bot_h_lo = bot_h_hi = 6
        bot_w_lo = bot_w_hi = 6
        n_lo, n_hi = 5, 8
    elif difficulty == "easy":
        bot_h_lo, bot_h_hi = 5, 6
        bot_w_lo, bot_w_hi = 6, 7
        n_lo, n_hi = 3, 6
    elif difficulty == "hard":
        bot_h_lo, bot_h_hi = 7, 8
        bot_w_lo, bot_w_hi = 7, 8
        n_lo, n_hi = 8, 12
    else:
        bot_h_lo, bot_h_hi = 6, 7
        bot_w_lo, bot_w_hi = 6, 7
        n_lo, n_hi = 5, 9

    bot_h = _axis_int(ctx, overrides, "bot_h", bot_h_lo, bot_h_hi, 5, 8)
    bot_w = _axis_int(ctx, overrides, "bot_w", bot_w_lo, bot_w_hi, 6, 8)
    n_twos = _axis_int(ctx, overrides, "n_twos", n_lo, n_hi, 3, 12)
    rng = ctx.draw_rng("layout")

    height = sep_row + 1 + bot_h
    grid = full_grid(height, bot_w, 0)
    icon = _pick_icon(role, rng)

    # Encode each logical icon cell as a uniform 2x2 visual block.
    for dr in range(3):
        for dc in range(3):
            value = icon[dr][dc]
            for ar in (0, 1):
                for ac in (0, 1):
                    grid[2 * dr + ar][2 * dc + ac] = value

    for c in range(bot_w):
        grid[sep_row][c] = 5

    markers = _pick_markers(bot_h, bot_w, n_twos, rng)
    for br, bc in markers:
        grid[sep_row + 1 + br][bc] = 2

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))

    # Curriculum-only semantic obligations belong here, not in self_check.
    facts = semantic_observables(grid)
    if facts["icon_nonzero_count"] < 5 or facts["icon_color_count"] < 2:
        raise AssertionError("generated icon is not a decisive multicolor pattern")
    if role in (0, 1, 2) and not facts["icon_contains_red"]:
        raise AssertionError("scheduled red-payload witness did not fire")
    if not overrides and role in (0, 3) and strict_canonical_like(grid):
        raise AssertionError("canonical anchor fell outside strict canonical manifold")
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket rule for focused evidence."""
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid lesson: " + "; ".join(analysis["errors"]))
    bot_h = analysis["bot_h"]
    bot_w = analysis["bot_w"]
    icon = analysis["icon"]
    output = full_grid(3 * bot_h, 3 * bot_w, 0)
    for br, bc in analysis["markers"]:
        for dr in range(3):
            for dc in range(3):
                value = icon[dr][dc]
                if value != 0:
                    output[3 * br + dr][3 * bc + dc] = value
    return output


def _rival_fixed_separator_6(grid):
    """Canonical-only shortcut: pretend the marker field always starts row 7."""
    if not grid or not grid[0] or len(grid) <= 7:
        return []
    bot_start = 7
    bot_h = len(grid) - bot_start
    bot_w = len(grid[0])
    icon = [[grid[2 * r][2 * c] for c in range(3)] for r in range(3)]
    output = full_grid(3 * bot_h, 3 * bot_w, 0)
    for br in range(bot_h):
        for bc in range(bot_w):
            if grid[bot_start + br][bc] != 2:
                continue
            for dr in range(3):
                for dc in range(3):
                    value = icon[dr][dc]
                    if value:
                        output[3 * br + dr][3 * bc + dc] = value
    return output


def _rival_ignore_red_icon_payload(grid):
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return rule_mirror(grid)
    output = full_grid(3 * analysis["bot_h"], 3 * analysis["bot_w"], 0)
    for br, bc in analysis["markers"]:
        for dr in range(3):
            for dc in range(3):
                value = analysis["icon"][dr][dc]
                if value not in (0, 2):
                    output[3 * br + dr][3 * bc + dc] = value
    return output


def _rival_first_marker_only(grid):
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return rule_mirror(grid)
    output = full_grid(3 * analysis["bot_h"], 3 * analysis["bot_w"], 0)
    if analysis["markers"]:
        br, bc = analysis["markers"][0]
        for dr in range(3):
            for dc in range(3):
                value = analysis["icon"][dr][dc]
                if value:
                    output[3 * br + dr][3 * bc + dc] = value
    return output


def _rival_marker_count_only(grid):
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return rule_mirror(grid)
    output = full_grid(3 * analysis["bot_h"], 3 * analysis["bot_w"], 0)
    all_cells = [
        (r, c)
        for r in range(analysis["bot_h"])
        for c in range(analysis["bot_w"])
    ]
    for br, bc in all_cells[: analysis["n_twos"]]:
        for dr in range(3):
            for dc in range(3):
                value = analysis["icon"][dr][dc]
                if value:
                    output[3 * br + dr][3 * bc + dc] = value
    return output


def _rival_modal_icon_color(grid):
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return rule_mirror(grid)
    output = full_grid(3 * analysis["bot_h"], 3 * analysis["bot_w"], 0)
    nonzero = analysis["icon_nonzero"]
    modal = Counter(nonzero).most_common(1)[0][0]
    for br, bc in analysis["markers"]:
        for dr in range(3):
            for dc in range(3):
                if analysis["icon"][dr][dc] != 0:
                    output[3 * br + dr][3 * bc + dc] = modal
    return output


def _rival_solid_red_blocks(grid):
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return rule_mirror(grid)
    output = full_grid(3 * analysis["bot_h"], 3 * analysis["bot_w"], 0)
    for br, bc in analysis["markers"]:
        for dr in range(3):
            for dc in range(3):
                output[3 * br + dr][3 * bc + dc] = 2
    return output


def _witness_canonical_anchor(grid) -> bool:
    return strict_canonical_like(grid) == [] and _rival_solid_red_blocks(grid) != rule_mirror(grid)


def _witness_separator_location(grid) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and analysis["sep_row"] != 6
        and _rival_fixed_separator_6(grid) != rule_mirror(grid)
    )


def _witness_red_icon_payload(grid) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and 2 in analysis["icon_colors"]
        and _rival_ignore_red_icon_payload(grid) != rule_mirror(grid)
    )


def _witness_marker_positions(grid) -> bool:
    analysis = _grid_analysis(grid)
    return not analysis["errors"] and _rival_marker_count_only(grid) != rule_mirror(grid)


def _witness_every_marker(grid) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and analysis["n_twos"] >= 2
        and _rival_first_marker_only(grid) != rule_mirror(grid)
    )


def _witness_icon_pattern(grid) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and len(analysis["icon_colors"]) >= 2
        and 0 in {value for row in analysis["icon"] for value in row}
        and _rival_modal_icon_color(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canonical_scale_anchor": _witness_canonical_anchor,
    "separator_row_must_be_located": _witness_separator_location,
    "red_can_be_icon_payload": _witness_red_icon_payload,
    "marker_positions_control_stamp_positions": _witness_marker_positions,
    "every_marker_is_stamped": _witness_every_marker,
    "multicolor_icon_pattern_is_copied": _witness_icon_pattern,
}

SEMANTIC_RIVALS = {
    "fixed_separator_row_6": _rival_fixed_separator_6,
    "ignore_red_icon_payload": _rival_ignore_red_icon_payload,
    "first_marker_only": _rival_first_marker_only,
    "marker_count_only": _rival_marker_count_only,
    "modal_icon_color": _rival_modal_icon_color,
    "solid_red_marker_blocks": _rival_solid_red_blocks,
}

WITNESS_RIVALS = {
    "canonical_scale_anchor": ["solid_red_marker_blocks"],
    "separator_row_must_be_located": ["fixed_separator_row_6"],
    "red_can_be_icon_payload": ["ignore_red_icon_payload"],
    "marker_positions_control_stamp_positions": ["marker_count_only"],
    "every_marker_is_stamped": ["first_marker_only"],
    "multicolor_icon_pattern_is_copied": ["modal_icon_color"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# All canonical scenes use separator row 6, so canonical alone cannot refute
# this shortcut.  The schedule's row-7/row-8 scenes are the required generated
# killing witnesses.
CANONICAL_SHORTCUTS = {"fixed_separator_row_6": _rival_fixed_separator_6}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return reasons


def mutation_fixtures():
    """Structural mutations that must be rejected by self_check."""
    fixtures = []

    no_separator = generate(1101, 0)
    sep = semantic_observables(no_separator)["sep_row"]
    no_separator[sep] = [0] * len(no_separator[0])
    fixtures.append(("missing_separator", no_separator))

    duplicate_separator = generate(1102, 1)
    duplicate_separator[-1] = [5] * len(duplicate_separator[0])
    fixtures.append(("duplicate_separator", duplicate_separator))

    broken_icon_block = generate(1103, 2)
    replacement = 9 if broken_icon_block[0][0] != 9 else 8
    broken_icon_block[1][1] = replacement
    fixtures.append(("nonuniform_2x2_icon_block", broken_icon_block))

    foreign_bottom_color = generate(1104, 3)
    facts = semantic_observables(foreign_bottom_color)
    sep = facts["sep_row"]
    marker = _grid_analysis(foreign_bottom_color)["markers"][0]
    foreign_bottom_color[sep + 1 + marker[0]][marker[1]] = 9
    fixtures.append(("foreign_bottom_color", foreign_bottom_color))

    noisy_top_padding = generate(1105, 1, bot_w=7)
    noisy_top_padding[0][6] = 1
    fixtures.append(("nonzero_top_padding", noisy_top_padding))

    no_markers = generate(1106, 2)
    analysis = _grid_analysis(no_markers)
    sep = analysis["sep_row"]
    for br, bc in analysis["markers"]:
        no_markers[sep + 1 + br][bc] = 0
    fixtures.append(("no_markers", no_markers))

    return fixtures


def negative_recombination_fixture(grid=None):
    """Replace one red marker by a novel absent color; oracle remains defined."""
    source = copy.deepcopy(grid if grid is not None else generate(2201, 1))
    analysis = _grid_analysis(source)
    if analysis["errors"]:
        raise ValueError("source must be a valid lesson")
    used = {value for row in source for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    br, bc = analysis["markers"][0]
    source[analysis["sep_row"] + 1 + br][bc] = replacement
    return source
