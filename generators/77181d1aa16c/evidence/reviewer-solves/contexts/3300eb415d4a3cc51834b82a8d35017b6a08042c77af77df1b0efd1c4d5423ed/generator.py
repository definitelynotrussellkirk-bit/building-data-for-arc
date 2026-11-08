"""Generator for ARC task 77181d1aa16c.

The largest all-nonzero rectangle is a two-colour source pattern.  It occupies
one block of a 2-by-2 local frame.  The source is reflected horizontally,
vertically, and both ways into the other blocks.  Sparse indicator cells in a
target block map source-pattern roles to that block's output colours; a missing
role is erased.  When several indicators name the same block/role, the first in
row-major order wins, matching the selected Racket authority.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "77181d1aa16c"
TASK_ID = GENERATOR_ID
RULE_HASH = "76ff7f3a7ec0"
VERSION = "4.0.0"
SUMMARY = (
    "Find the largest all-nonzero two-colour rectangle. Keep it in place and "
    "mirror it into a local 2x2 frame. In each of the other three blocks, "
    "indicator positions identify source roles and indicator colours provide "
    "that block's recolouring; absent roles become 0 and the first duplicate "
    "indicator in row-major order wins."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 6
SCHEDULE_PROFILES = (0, 1, 2, 3, 4, 5)

INVARIANTS = [
    "the selected largest all-nonzero rectangle is 3..5 by 3..5 and uses exactly two colours with a strict majority",
    "the complete reflected 2x2 frame fits inside the grid with 0..2 cells of margin on each side",
    "all non-source nonzero cells are lawful indicators inside target blocks 1, 2, or 3",
    "each target block has at least one indicator; generated profiles have one missing role and one conflicting duplicate",
    "generated source patterns are asymmetric, so reflection cannot be replaced by direct tiling",
]

AXES = {
    "pattern_h": {"type": "int", "default": "scheduled 3|4|5", "valid": "3..5"},
    "pattern_w": {"type": "int", "default": "scheduled 3|4|5", "valid": "3..5"},
    "top_margin": {"type": "int", "default": "scheduled 0|1|2", "valid": "0..2"},
    "bottom_margin": {"type": "int", "default": "scheduled 0|1|2", "valid": "0..2"},
    "left_margin": {"type": "int", "default": "scheduled 0|1|2", "valid": "0..2"},
    "right_margin": {"type": "int", "default": "scheduled 0|1|2", "valid": "0..2"},
    "indicator_profile": {
        "type": "int",
        "default": "scheduled 0|1|2|3; each chooses a missing role and a conflicting duplicate",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_AXIS_BOUNDS = {
    "pattern_h": (3, 5),
    "pattern_w": (3, 5),
    "top_margin": (0, 2),
    "bottom_margin": (0, 2),
    "left_margin": (0, 2),
    "right_margin": (0, 2),
    "indicator_profile": (0, 3),
}

# pattern_h, pattern_w, top, bottom, left, right, indicator_profile
# Profile 0 exactly preserves the canonical 10x10 / 4x4 / one-cell-margin
# geometry.  The other profiles break fixed-origin and square-only shortcuts.
_GEOMETRY_PROFILES = {
    0: (4, 4, 1, 1, 1, 1, 0),
    1: (3, 4, 2, 2, 1, 1, 1),
    2: (4, 3, 1, 1, 2, 2, 2),
    3: (5, 4, 1, 0, 2, 1, 3),
    4: (4, 5, 0, 2, 1, 0, 2),
    5: (3, 3, 2, 1, 0, 2, 3),
}

# (missing descriptor, duplicated descriptor), where a descriptor is
# (target block, semantic role name).  Every duplicate uses two different
# colours, so first-vs-last precedence is observable in every generated grid.
_INDICATOR_PROFILES = {
    0: ((3, "minor"), (1, "major")),
    1: ((2, "major"), (3, "minor")),
    2: ((1, "minor"), (2, "major")),
    3: ((3, "major"), (1, "minor")),
}
_EXPECTED_DESCRIPTORS = tuple(
    (block, role) for block in (1, 2, 3) for role in ("major", "minor")
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the finite semantic/geometry schedule state."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool/float/string/None)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _scheduled_int(ctx, name, scheduled):
    lo, hi = _AXIS_BOUNDS[name]
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _is_asymmetric(pattern):
    reversed_columns = [row[::-1] for row in pattern]
    reversed_rows = pattern[::-1]
    half_turn = [row[::-1] for row in pattern[::-1]]
    return (
        pattern != reversed_columns
        and pattern != reversed_rows
        and pattern != half_turn
    )


def _make_pattern(ctx, height, width, major, minor, difficulty):
    """Construct a strict-majority pattern with safe cells for both roles."""
    rng = ctx.draw_rng("source_pattern")
    all_cells = [(row, col) for row in range(height) for col in range(width)]
    safe_core = {
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
    }
    maximum = (height * width - 1) // 2
    band = difficulty or "medium"
    if band == "easy":
        counts = list(range(2, min(maximum, 3) + 1))
    elif band == "hard":
        counts = list(range(max(2, maximum - 2), maximum + 1))
    else:
        counts = list(range(2, maximum + 1))

    for _ in range(256):
        n_minor = rng.choice(counts)
        minor_cells = set(rng.sample(all_cells, n_minor))
        if len(minor_cells & safe_core) < 2:
            continue
        if len(safe_core - minor_cells) < 2:
            continue
        pattern = [
            [minor if (row, col) in minor_cells else major for col in range(width)]
            for row in range(height)
        ]
        if _is_asymmetric(pattern):
            return pattern

    # Total deterministic fallback for every 3..5 x 3..5 shape.
    minor_cells = {(0, 0), (1, 1)}
    pattern = [
        [minor if (row, col) in minor_cells else major for col in range(width)]
        for row in range(height)
    ]
    if not _is_asymmetric(pattern):  # defensive; unreachable for the domain
        raise RuntimeError("could not construct an asymmetric two-colour pattern")
    return pattern


def _block_position(top, left, ph, pw, block, source_row, source_col):
    if block == 1:
        return top + source_row, left + 2 * pw - 1 - source_col
    if block == 2:
        return top + 2 * ph - 1 - source_row, left + source_col
    if block == 3:
        return top + 2 * ph - 1 - source_row, left + 2 * pw - 1 - source_col
    raise ValueError(f"target block must be 1, 2, or 3, got {block}")


def _indicator_candidates(pattern, top, left, block, role_value):
    """Use the inner (ph-1)x(pw-1) source core to avoid extending the source rect."""
    ph, pw = len(pattern), len(pattern[0])
    candidates = [
        _block_position(top, left, ph, pw, block, row, col)
        for row in range(ph - 1)
        for col in range(pw - 1)
        if pattern[row][col] == role_value
    ]
    return sorted(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic lawful input with exact observable controls."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _GEOMETRY_PROFILES[profile]
    names = (
        "pattern_h",
        "pattern_w",
        "top_margin",
        "bottom_margin",
        "left_margin",
        "right_margin",
        "indicator_profile",
    )
    values = {
        name: _scheduled_int(ctx, name, scheduled)
        for name, scheduled in zip(names, defaults)
    }
    ph, pw = values["pattern_h"], values["pattern_w"]
    top, left = values["top_margin"], values["left_margin"]
    height = top + 2 * ph + values["bottom_margin"]
    width = left + 2 * pw + values["right_margin"]

    palette = ctx.draw_distinct_colors("palette", n=8, exclude={0})
    major, minor = palette[:2]
    pattern = _make_pattern(ctx, ph, pw, major, minor, difficulty)
    grid = full_grid(height, width, 0)
    for row in range(ph):
        for col in range(pw):
            grid[top + row][left + col] = pattern[row][col]

    missing, duplicate = _INDICATOR_PROFILES[values["indicator_profile"]]
    present = [descriptor for descriptor in _EXPECTED_DESCRIPTORS if descriptor != missing]
    mapping_colors = dict(zip(present, palette[2:7]))
    duplicate_color = palette[7]
    role_values = {"major": major, "minor": minor}
    placement_rng = ctx.draw_rng("indicator_positions")

    for descriptor in present:
        block, role_name = descriptor
        candidates = _indicator_candidates(
            pattern, top, left, block, role_values[role_name]
        )
        if len(candidates) < (2 if descriptor == duplicate else 1):
            raise RuntimeError(f"insufficient safe indicator positions for {descriptor}")
        position = candidates[0] if descriptor == duplicate else placement_rng.choice(candidates)
        grid[position[0]][position[1]] = mapping_colors[descriptor]
        if descriptor == duplicate:
            decoy = candidates[-1]
            grid[decoy[0]][decoy[1]] = duplicate_color

    expected_rect = (top, left, top + ph - 1, left + pw - 1)
    if _largest_nonzero_rect(grid) != expected_rect:
        raise RuntimeError("indicator placement changed the selected source rectangle")
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer colours 0..9 (not bool)"]
    return []


def _largest_nonzero_rect(grid):
    """Exhaustive selected-rule rectangle scan, including its first-max tie order."""
    height, width = len(grid), len(grid[0])
    zeros = [[0] * (width + 1) for _ in range(height + 1)]
    for row in range(height):
        for col in range(width):
            zeros[row + 1][col + 1] = (
                zeros[row][col + 1]
                + zeros[row + 1][col]
                - zeros[row][col]
                + int(grid[row][col] == 0)
            )
    best = (0, 0, 0, 0, 0)
    for top in range(height):
        for bottom in range(top, height):
            for left in range(width):
                for right in range(left, width):
                    area = (bottom - top + 1) * (right - left + 1)
                    holes = (
                        zeros[bottom + 1][right + 1]
                        - zeros[top][right + 1]
                        - zeros[bottom + 1][left]
                        + zeros[top][left]
                    )
                    if area > best[0] and holes == 0:
                        best = (area, top, left, bottom, right)
    return best[1:]


def _block_key(top, left, ph, pw, row, col):
    return 2 * int(row >= top + ph) + int(col >= left + pw)


def _role_at(pattern, top, left, row, col, *, mirror=True):
    ph, pw = len(pattern), len(pattern[0])
    lower = row >= top + ph
    rightward = col >= left + pw
    local_row = row - (top + ph if lower else top)
    local_col = col - (left + pw if rightward else left)
    if not (0 <= local_row < ph and 0 <= local_col < pw):
        return None
    source_row = ph - 1 - local_row if lower and mirror else local_row
    source_col = pw - 1 - local_col if rightward and mirror else local_col
    return pattern[source_row][source_col]


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    top, left, bottom, right = _largest_nonzero_rect(grid)
    ph, pw = bottom - top + 1, right - left + 1
    pattern = [row[left : right + 1] for row in grid[top : bottom + 1]]
    counts = Counter(value for row in pattern for value in row)

    if not 3 <= ph <= 5:
        errors.append(f"source pattern height must be 3..5, got {ph}")
    if not 3 <= pw <= 5:
        errors.append(f"source pattern width must be 3..5, got {pw}")
    if 0 in counts:
        errors.append("selected source rectangle contains background 0")
    if len(counts) != 2:
        errors.append(f"source pattern must use exactly two colours, got {len(counts)}")

    ranked = [color for color, _ in sorted(counts.items(), key=lambda item: -item[1])]
    major = ranked[0] if ranked else None
    minor = ranked[1] if len(ranked) > 1 else None
    if major is not None and minor is not None and counts[major] <= counts[minor]:
        errors.append("source pattern must have a strict majority colour")
    if major is not None and minor is not None:
        safe = [
            pattern[row][col]
            for row in range(max(0, ph - 1))
            for col in range(max(0, pw - 1))
        ]
        if safe.count(major) < 2 or safe.count(minor) < 2:
            errors.append("each source role needs at least two cells in the safe inner core")

    bottom_margin = height - (top + 2 * ph)
    right_margin = width - (left + 2 * pw)
    margins = {
        "top_margin": top,
        "bottom_margin": bottom_margin,
        "left_margin": left,
        "right_margin": right_margin,
    }
    if bottom_margin < 0 or right_margin < 0:
        errors.append("the complete reflected 2x2 frame does not fit inside the grid")
    for name, value in margins.items():
        if not 0 <= value <= 2:
            errors.append(f"{name} must be 0..2, got {value}")

    groups: Counter[tuple[int, int | None]] = Counter()
    group_colors: dict[tuple[int, int | None], list[int]] = {}
    indicators = []
    if pattern:
        for row, values in enumerate(grid):
            for col, value in enumerate(values):
                if value == 0 or (top <= row <= bottom and left <= col <= right):
                    continue
                block = _block_key(top, left, ph, pw, row, col)
                role = _role_at(pattern, top, left, row, col)
                indicators.append((row, col, block, role, value))
                if role is None:
                    errors.append(f"indicator at {(row, col)} lies outside the reflected frame")
                    continue
                if block == 0:
                    errors.append(f"indicator at {(row, col)} lies in source block 0")
                    continue
                descriptor = (block, role)
                groups[descriptor] += 1
                group_colors.setdefault(descriptor, []).append(value)

    if not 5 <= len(indicators) <= 8:
        errors.append(f"expected 5..8 indicator cells, got {len(indicators)}")
    for block in (1, 2, 3):
        if not any(key[0] == block and count for key, count in groups.items()):
            errors.append(f"target block {block} has no indicator")
    for descriptor, count in groups.items():
        if count > 2:
            errors.append(f"indicator descriptor {descriptor} occurs {count} times; maximum is 2")

    indicator_profile = None
    if major is not None and minor is not None:
        role_names = {major: "major", minor: "minor"}
        named_counts = {
            (block, role_names[role]): count
            for (block, role), count in groups.items()
            if role in role_names
        }
        missing = [descriptor for descriptor in _EXPECTED_DESCRIPTORS if named_counts.get(descriptor, 0) == 0]
        duplicated = [descriptor for descriptor in _EXPECTED_DESCRIPTORS if named_counts.get(descriptor, 0) == 2]
        if len(missing) == 1 and len(duplicated) == 1:
            for profile, pair in _INDICATOR_PROFILES.items():
                if pair == (missing[0], duplicated[0]):
                    indicator_profile = profile
                    break

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "rect": (top, left, bottom, right),
        "pattern_h": ph,
        "pattern_w": pw,
        "pattern": pattern,
        "counts": counts,
        "major": major,
        "minor": minor,
        "margins": margins,
        "indicators": indicators,
        "groups": groups,
        "group_colors": group_colors,
        "indicator_profile": indicator_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    candidate = nested if isinstance(nested, dict) else meta
    return {name: value for name, value in candidate.items() if name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concrete violations of the selected-rule input manifold."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if requested != observed.get(name):
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact axis directly from a generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["indicator_profile"] is None:
        return {}
    return {
        "pattern_h": analysis["pattern_h"],
        "pattern_w": analysis["pattern_w"],
        **analysis["margins"],
        "indicator_profile": analysis["indicator_profile"],
    }


def _render_model(
    grid,
    *,
    rect=None,
    last_indicator=False,
    mirror=True,
    carry_missing=False,
):
    """Pure Python model used for the test oracle and explicit rival rules."""
    height, width = len(grid), len(grid[0])
    if rect is None:
        rect = _largest_nonzero_rect(grid)
    top, left, bottom, right = rect
    ph, pw = bottom - top + 1, right - left + 1
    if top < 0 or left < 0 or bottom >= height or right >= width:
        return [[0] * width for _ in range(height)]
    pattern = [row[left : right + 1] for row in grid[top : bottom + 1]]
    counts = Counter(value for row in pattern for value in row if value != 0)
    roles = [color for color, _ in sorted(counts.items(), key=lambda item: -item[1])[:2]]
    if len(roles) < 2:
        return [[0] * width for _ in range(height)]

    mappings = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (top <= row <= bottom and left <= col <= right):
                continue
            role = _role_at(pattern, top, left, row, col, mirror=mirror)
            if role not in roles:
                continue
            descriptor = (_block_key(top, left, ph, pw, row, col), role)
            if last_indicator or descriptor not in mappings:
                mappings[descriptor] = value

    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            role = _role_at(pattern, top, left, row, col, mirror=mirror)
            if role not in roles:
                continue
            block = _block_key(top, left, ph, pw, row, col)
            if block == 0:
                output[row][col] = role
            elif (block, role) in mappings:
                output[row][col] = mappings[(block, role)]
            elif carry_missing:
                output[row][col] = role
    return output


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid kaleidoscope input: " + "; ".join(errors))
    return _render_model(grid)


def strict_canonical_like(grid) -> list[str]:
    """Lawful manifold containing all canonical and generated inputs."""
    return list(self_check(grid))


def _rival_last_indicator_wins(grid):
    return _render_model(grid, last_indicator=True)


def _rival_fixed_canonical_source(grid):
    return _render_model(grid, rect=(1, 1, 4, 4))


def _rival_force_square_source(grid):
    top, left, bottom, right = _largest_nonzero_rect(grid)
    side = min(bottom - top + 1, right - left + 1)
    return _render_model(grid, rect=(top, left, top + side - 1, left + side - 1))


def _rival_copy_without_mirroring(grid):
    return _render_model(grid, mirror=False)


def _rival_carry_source_when_missing(grid):
    return _render_model(grid, carry_missing=True)


def _witness_conflicting_duplicate(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    return any(len(colors) == 2 and colors[0] != colors[1] for colors in analysis["group_colors"].values())


def _witness_missing_role(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    expected = {
        (block, role)
        for block in (1, 2, 3)
        for role in (analysis["major"], analysis["minor"])
    }
    return any(descriptor not in analysis["groups"] for descriptor in expected)


def _witness_asymmetric_pattern(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and _is_asymmetric(analysis["pattern"])


def _witness_noncanonical_source(grid):
    """A moved/resized source that actually separates the fixed-frame shortcut."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["rect"] == (1, 1, 4, 4):
        return False
    return _rival_fixed_canonical_source(grid) != _render_model(grid)


def _witness_rectangular_source(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["pattern_h"] != analysis["pattern_w"]


SEMANTIC_WITNESSES = {
    "conflicting_duplicate_indicator": _witness_conflicting_duplicate,
    "missing_role_mapping": _witness_missing_role,
    "asymmetric_source_pattern": _witness_asymmetric_pattern,
    "noncanonical_source_frame": _witness_noncanonical_source,
    "rectangular_source_pattern": _witness_rectangular_source,
}
SEMANTIC_RIVALS = {
    "last_indicator_wins": _rival_last_indicator_wins,
    "fixed_canonical_source": _rival_fixed_canonical_source,
    "force_square_source": _rival_force_square_source,
    "copy_without_mirroring": _rival_copy_without_mirroring,
    "carry_source_when_mapping_missing": _rival_carry_source_when_missing,
}
WITNESS_RIVALS = {
    "conflicting_duplicate_indicator": ["last_indicator_wins"],
    "missing_role_mapping": ["carry_source_when_mapping_missing"],
    "asymmetric_source_pattern": ["copy_without_mirroring"],
    "noncanonical_source_frame": ["fixed_canonical_source"],
    "rectangular_source_pattern": ["force_square_source"],
}
CANONICAL_SHORTCUTS = {
    "fixed_canonical_source": _rival_fixed_canonical_source,
    "force_square_source": _rival_force_square_source,
    "last_indicator_wins": _rival_last_indicator_wins,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared deterministic rival."""
    del query
    if not isinstance(demos, list) or not demos:
        return ["lesson needs at least one demonstration"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        refuted = False
        for pair in demos:
            try:
                grid = pair["input"]
                if rival(grid) != rule_mirror(grid):
                    refuted = True
                    break
            except Exception as exc:
                reasons.append(f"{name} could not be checked: {type(exc).__name__}: {exc}")
                refuted = True
                break
        if not refuted:
            reasons.append(f"all demonstrations are consistent with rival {name}")
    return reasons
