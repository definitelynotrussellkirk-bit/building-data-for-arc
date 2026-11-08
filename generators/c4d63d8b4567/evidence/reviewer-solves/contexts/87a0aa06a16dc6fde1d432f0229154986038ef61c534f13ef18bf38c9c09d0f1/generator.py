"""Semantic generator for ARC task c4d63d8b4567 (Terminal Run Completion).

The authoritative rule scans rows and columns independently.  When a color has
exactly two cells on one row or one column and every cell strictly between them
is zero in the original input, the inclusive span is painted with that color.

The generated curriculum keeps the five public canvas/palette profiles but
varies positions, colors, and span lengths.  A four-sample schedule makes the
otherwise-underdetermined preconditions visible: one scene has clear mixed-axis
pairs, one contains an aligned pair blocked by another color, one contains an
off-axis same-color pair, and one contains several clear horizontal pairs plus
an extra off-axis occurrence of one active color.  Every four consecutive
demonstrations therefore refute the main shortcut rules, including the tempting
assumption that an active color must occur exactly twice in the whole grid.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c4d63d8b4567"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "3c80c97f70dc"  # canonical whitespace-normalized program_solution
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On the original zero-background grid, scan each row and column "
    "independently. When a color occurs exactly twice on that line and every "
    "strictly interior cell is zero, fill the inclusive span with that color. "
    "Leave blocked and off-axis pairs unchanged."
)

INVARIANTS = [
    "zero is background and all nonzero values are ARC colors 1..9",
    "the canvas and number of nonzero colors match one public canonical profile",
    "each nonzero color appears two times, except one scheduled active color "
    "may have one off-axis extra occurrence",
    "aligned pairs are separated by at least one interior cell",
    "at least one aligned pair has an all-zero interior and therefore fires",
    "clear active spans do not cross, avoiding order-dependent output conflicts",
]

SCENE_PROFILES = (
    "p7x8_2",
    "p8x9_2",
    "p7x10_2",
    "p9x9_3",
    "p8x10_2",
)

_PROFILE_DATA = {
    "p7x8_2": (7, 8, 2),
    "p8x9_2": (8, 9, 2),
    "p7x10_2": (7, 10, 2),
    "p9x9_3": (9, 9, 3),
    "p8x10_2": (8, 10, 2),
}
_PROFILE_BY_DIMS = {
    (height, width): name
    for name, (height, width, _count) in _PROFILE_DATA.items()
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "keyed choice among the five public canvas/palette profiles",
        "valid": "p7x8_2|p8x9_2|p7x10_2|p9x9_3|p8x10_2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four semantic profiles; every four-example sliding window sees all."""
    del seed, difficulty
    return int(sample_index) % 4


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} does not have width {width}")
            continue
        for col_index, value in enumerate(row):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append(
                    f"cell ({row_index},{col_index}) has invalid ARC color {value!r}"
                )
    return errors


def _grouped_cells(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                grouped[value].append((row_index, col_index))
    return dict(grouped)


def _span_record(
    grid: list[list[int]], color: int, cells: list[tuple[int, int]]
) -> dict[str, Any] | None:
    if len(cells) != 2:
        return None
    first, second = cells
    r0, c0 = first
    r1, c1 = second
    if r0 == r1:
        start, end = sorted((c0, c1))
        span = tuple((r0, col) for col in range(start, end + 1))
        orientation = "H"
    elif c0 == c1:
        start, end = sorted((r0, r1))
        span = tuple((row, c0) for row in range(start, end + 1))
        orientation = "V"
    else:
        return {
            "color": color,
            "endpoints": tuple(cells),
            "orientation": "D",
            "role": "off_axis",
            "length": None,
            "span": (),
            "blockers": (),
        }

    interior = span[1:-1]
    blockers = tuple(
        (row, col, grid[row][col])
        for row, col in interior
        if grid[row][col] != 0
    )
    return {
        "color": color,
        "endpoints": tuple(cells),
        "orientation": orientation,
        "role": "blocked" if blockers else "active",
        "length": len(span),
        "span": span,
        "blockers": blockers,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the canonical row-then-column Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    colors = list(dict.fromkeys(value for row in source for value in row if value))

    for row in range(height):
        for color in colors:
            columns = [col for col in range(width) if source[row][col] == color]
            if len(columns) != 2:
                continue
            start, end = min(columns), max(columns)
            if all(source[row][col] == 0 for col in range(start + 1, end)):
                for col in range(start, end + 1):
                    output[row][col] = color

    for col in range(width):
        for color in colors:
            rows = [row for row in range(height) if source[row][col] == color]
            if len(rows) != 2:
                continue
            start, end = min(rows), max(rows)
            if all(source[row][col] == 0 for row in range(start + 1, end)):
                for row in range(start, end + 1):
                    output[row][col] = color
    return output


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    source = [list(row) for row in grid]
    height, width = len(source), len(source[0])
    profile = _PROFILE_BY_DIMS.get((height, width))
    if profile is None:
        errors.append(
            f"canvas {height}x{width} is not one of the five public scene profiles"
        )
        return result

    grouped = _grouped_cells(source)
    expected_colors = _PROFILE_DATA[profile][2]
    if len(grouped) != expected_colors:
        errors.append(
            f"profile {profile} requires {expected_colors} nonzero colors; "
            f"found {len(grouped)}"
        )

    records: list[dict[str, Any]] = []
    repeated: list[dict[str, Any]] = []
    for color, cells in sorted(grouped.items()):
        if len(cells) == 2:
            record = _span_record(source, color, cells)
            if record is None:  # len(cells)==2 makes this defensive only.
                errors.append(f"could not analyze color {color}")
                continue
            record = dict(record, occurrences=2, extra_cells=(), repeated=False)
        elif len(cells) == 3:
            aligned = []
            for first, second in combinations(cells, 2):
                candidate = _span_record(source, color, [first, second])
                if candidate is not None and candidate["orientation"] != "D":
                    aligned.append(candidate)
            if len(aligned) != 1:
                errors.append(
                    f"color {color} appears 3 times but exposes {len(aligned)} "
                    "aligned pairs (expected exactly one)"
                )
                continue
            record = aligned[0]
            if record["role"] != "active":
                errors.append(
                    f"color {color} has an extra occurrence but its unique aligned "
                    "pair is blocked"
                )
                continue
            endpoints = set(record["endpoints"])
            extras = tuple(cell for cell in cells if cell not in endpoints)
            record = dict(
                record, occurrences=3, extra_cells=extras, repeated=True
            )
            repeated.append(record)
        else:
            errors.append(
                f"color {color} appears {len(cells)} times "
                "(expected 2, or one scheduled color may appear 3 times)"
            )
            continue

        if record["orientation"] != "D" and record["length"] < 3:
            errors.append(
                f"color {color} aligned endpoints are adjacent; at least one interior "
                "cell is required"
            )
        records.append(record)

    if len(repeated) > 1:
        errors.append(
            f"scene has {len(repeated)} colors with extra occurrences (expected at most 1)"
        )

    active = [record for record in records if record["role"] == "active"]
    if not active:
        errors.append(
            "scene has no clear aligned pair, so the intended transformation is hidden"
        )

    for left_index, left in enumerate(active):
        left_cells = set(left["span"])
        for right in active[left_index + 1 :]:
            overlap = left_cells.intersection(right["span"])
            if overlap:
                errors.append(
                    "clear active spans cross/overlap at "
                    + ", ".join(map(str, sorted(overlap)[:3]))
                )

    output = rule_mirror(source)
    changed = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] != output[row][col]
    ]
    if not changed:
        errors.append("authoritative rule produces an identity output")

    result.update(
        {
            "profile": profile,
            "grouped": grouped,
            "records": records,
            "active": active,
            "blocked": [record for record in records if record["role"] == "blocked"],
            "off_axis": [record for record in records if record["role"] == "off_axis"],
            "repeated": repeated,
            "output": output,
            "changed": changed,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural gate for the calibrated canonical-profile input grammar."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict semantic census uses the same structural teaching grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the only declared exact axis directly from returned dimensions."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"scene_profile": None}
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return {"scene_profile": None}
    width = len(first)
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"scene_profile": None}
    return {"scene_profile": _PROFILE_BY_DIMS.get((len(grid), width))}


@lru_cache(maxsize=None)
def _all_spans(height: int, width: int, orientation: str):
    spans = []
    if orientation == "H":
        for row in range(height):
            for start in range(width - 2):
                for end in range(start + 2, width):
                    cells = tuple((row, col) for col in range(start, end + 1))
                    spans.append(("H", (row, start), (row, end), cells))
    else:
        for col in range(width):
            for start in range(height - 2):
                for end in range(start + 2, height):
                    cells = tuple((row, col) for row in range(start, end + 1))
                    spans.append(("V", (start, col), (end, col), cells))
    return tuple(spans)


def _ordered_spans(
    height: int, width: int, orientation: str, target_length: int, rng
):
    spans = list(_all_spans(height, width, orientation))
    rng.shuffle(spans)
    spans.sort(key=lambda span: abs(len(span[3]) - target_length))
    return spans


def _pick_extra_active(
    height: int,
    width: int,
    target_length: int,
    forbidden: set[tuple[int, int]],
    rng,
):
    orientations = ["H", "V"]
    rng.shuffle(orientations)
    for orientation in orientations:
        for span in _ordered_spans(height, width, orientation, target_length, rng):
            if forbidden.isdisjoint(span[3]):
                return span
    return None


def _construct_mixed_active(height: int, width: int, count: int, target: int, rng):
    horizontal = _ordered_spans(height, width, "H", target, rng)
    vertical = _ordered_spans(height, width, "V", target, rng)
    for first in horizontal:
        first_cells = set(first[3])
        for second in vertical:
            if not first_cells.isdisjoint(second[3]):
                continue
            selected = [first, second]
            forbidden = first_cells.union(second[3])
            if count == 3:
                extra = _pick_extra_active(height, width, target, forbidden, rng)
                if extra is None:
                    continue
                selected.append(extra)
            return [("active", span) for span in selected]
    raise RuntimeError("could not construct mixed clear-pair profile")


def _construct_horizontal_active(height: int, width: int, count: int, target: int, rng):
    candidates = _ordered_spans(height, width, "H", target, rng)

    def search(start: int, chosen: list[Any], forbidden: set[tuple[int, int]]):
        if len(chosen) == count:
            return list(chosen)
        for index in range(start, len(candidates)):
            span = candidates[index]
            if forbidden.isdisjoint(span[3]):
                chosen.append(span)
                found = search(index + 1, chosen, forbidden.union(span[3]))
                if found is not None:
                    return found
                chosen.pop()
        return None

    selected = search(0, [], set())
    if selected is None:
        raise RuntimeError("could not construct all-horizontal clear-pair profile")
    return [("active", span) for span in selected]


def _construct_repeated_horizontal_active(
    height: int, width: int, count: int, target: int, rng
):
    """Clear horizontal pairs, with one color carrying an off-axis singleton."""
    ordinary_roles = _construct_horizontal_active(height, width, count, target, rng)
    spans = [span for _role, span in ordinary_roles]
    repeated_span = spans[0]
    forbidden = {cell for span in spans for cell in span[3]}
    endpoint_columns = {repeated_span[1][1], repeated_span[2][1]}
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
        and row != repeated_span[1][0]
        and col not in endpoint_columns
    ]
    rng.shuffle(candidates)
    if not candidates:
        raise RuntimeError("could not place repeated-color off-axis occurrence")
    return [
        ("active_repeated", (repeated_span, candidates[0])),
        *[("active", span) for span in spans[1:]],
    ]


def _construct_blocked(height: int, width: int, count: int, target: int, rng):
    orientations = ["H", "V"]
    rng.shuffle(orientations)
    for active_orientation in orientations:
        blocked_orientation = "V" if active_orientation == "H" else "H"
        for active in _ordered_spans(height, width, active_orientation, target, rng):
            endpoints = [active[1], active[2]]
            rng.shuffle(endpoints)
            for blocker_cell in endpoints:
                blocked_options = _ordered_spans(
                    height, width, blocked_orientation, target, rng
                )
                for blocked in blocked_options:
                    # A length>=4 blocked span has at least one empty interior
                    # cell in addition to the blocker. This makes the
                    # "fill through blockers" rival observably wrong instead
                    # of answer-equivalent on a length-3 A-X-A pattern.
                    if len(blocked[3]) < 4:
                        continue
                    if blocker_cell not in blocked[3][1:-1]:
                        continue
                    if set(active[3]).intersection(blocked[3]) != {blocker_cell}:
                        continue
                    roles = [("active", active), ("blocked", blocked)]
                    if count == 3:
                        forbidden = set(active[3]).union(blocked[3])
                        extra = _pick_extra_active(
                            height, width, target, forbidden, rng
                        )
                        if extra is None:
                            continue
                        roles.append(("active", extra))
                    return roles
    raise RuntimeError("could not construct blocked-pair profile")


def _construct_off_axis(height: int, width: int, count: int, target: int, rng):
    orientations = ["H", "V"]
    rng.shuffle(orientations)
    for active_orientation in orientations:
        for active in _ordered_spans(height, width, active_orientation, target, rng):
            active_spans = [active]
            forbidden = set(active[3])
            if count == 3:
                extra = _pick_extra_active(height, width, target, forbidden, rng)
                if extra is None:
                    continue
                active_spans.append(extra)
                forbidden.update(extra[3])

            free = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if (row, col) not in forbidden
            ]
            rng.shuffle(free)
            off_axis = None
            for index, first in enumerate(free):
                for second in free[index + 1 :]:
                    if first[0] != second[0] and first[1] != second[1]:
                        off_axis = ("D", first, second, ())
                        break
                if off_axis is not None:
                    break
            if off_axis is None:
                continue
            roles = [("active", active_spans[0]), ("off_axis", off_axis)]
            if count == 3:
                roles.append(("active", active_spans[1]))
            return roles
    raise RuntimeError("could not construct off-axis-pair profile")


def _paint_endpoints(
    height: int,
    width: int,
    colors: Iterable[int],
    roles: list[tuple[str, Any]],
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for color, (role, payload) in zip(colors, roles):
        if role == "active_repeated":
            span, extra = payload
            cells = (span[1], span[2], extra)
        else:
            span = payload
            cells = (span[1], span[2])
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructor attempted to overlap endpoint cells")
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    height, width, color_count = _PROFILE_DATA[scene_profile]

    # These are nuisance draws rather than public axes.  draw_int_diff makes
    # easy/medium/hard genuinely different without claiming a non-observable
    # difficulty axis in AXES.
    layout_code = ctx.draw_int_diff("layout_code", 0, 1_000_000)
    target_span = ctx.draw_int_diff("span_target", 3, max(height, width))
    rng = ctx.draw_rng(f"layout:{layout_code}")
    colors = ctx.draw_distinct_colors("colors", n=color_count, exclude={0})

    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == 0:
        roles = _construct_mixed_active(height, width, color_count, target_span, rng)
    elif profile == 1:
        roles = _construct_blocked(height, width, color_count, target_span, rng)
    elif profile == 2:
        roles = _construct_off_axis(height, width, color_count, target_span, rng)
    else:
        roles = _construct_repeated_horizontal_active(
            height, width, color_count, target_span, rng
        )

    grid = _paint_endpoints(height, width, colors, roles)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid training scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["scene_profile"] != scene_profile:
        raise AssertionError("constructed scene lost its exact scene_profile axis")
    return grid


# ---------------------------------------------------------------------------
# Semantic rivals and witnesses.  These are deliberately simple plausible
# wrong rules, not alternate authorities.
# ---------------------------------------------------------------------------


def _rival_horizontal_only(grid):
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    width = len(source[0])
    colors = list(dict.fromkeys(value for row in source for value in row if value))
    for row in range(len(source)):
        for color in colors:
            columns = [col for col in range(width) if source[row][col] == color]
            if len(columns) == 2:
                start, end = min(columns), max(columns)
                if all(source[row][col] == 0 for col in range(start + 1, end)):
                    for col in range(start, end + 1):
                        output[row][col] = color
    return output


def _rival_vertical_only(grid):
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    colors = list(dict.fromkeys(value for row in source for value in row if value))
    for col in range(width):
        for color in colors:
            rows = [row for row in range(height) if source[row][col] == color]
            if len(rows) == 2:
                start, end = min(rows), max(rows)
                if all(source[row][col] == 0 for row in range(start + 1, end)):
                    for row in range(start, end + 1):
                        output[row][col] = color
    return output


def _rival_ignore_blockers(grid):
    """Wrong rule: fill zero cells between aligned endpoints even past blockers."""
    source = [list(row) for row in grid]
    output = rule_mirror(source)
    for color, cells in sorted(_grouped_cells(source).items()):
        if len(cells) != 2:
            continue
        record = _span_record(source, color, cells)
        if record is None or record["orientation"] == "D":
            continue
        for row, col in record["span"]:
            if source[row][col] == 0:
                output[row][col] = color
    return output


def _rival_connect_off_axis(grid):
    source = [list(row) for row in grid]
    output = rule_mirror(source)
    for color, cells in sorted(_grouped_cells(source).items()):
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        if r0 == r1 or c0 == c1:
            continue
        step_c = 1 if c1 >= c0 else -1
        for col in range(c0, c1 + step_c, step_c):
            output[r0][col] = color
        step_r = 1 if r1 >= r0 else -1
        for row in range(r0, r1 + step_r, step_r):
            output[row][c1] = color
    return output


def _rival_global_exactly_two(grid):
    """Wrong rule: an active color must occur exactly twice in the whole grid."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    eligible = [
        color
        for color, cells in sorted(_grouped_cells(source).items())
        if len(cells) == 2
    ]

    for row in range(height):
        for color in eligible:
            columns = [col for col in range(width) if source[row][col] == color]
            if len(columns) != 2:
                continue
            start, end = min(columns), max(columns)
            if all(source[row][col] == 0 for col in range(start + 1, end)):
                for col in range(start, end + 1):
                    output[row][col] = color

    for col in range(width):
        for color in eligible:
            rows = [row for row in range(height) if source[row][col] == color]
            if len(rows) != 2:
                continue
            start, end = min(rows), max(rows)
            if all(source[row][col] == 0 for row in range(start + 1, end)):
                for row in range(start, end + 1):
                    output[row][col] = color
    return output


def _rival_first_active_only(grid):
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    analysis = _analyze(source)
    active = sorted(analysis.get("active") or [], key=lambda record: record["color"])
    if active:
        record = active[0]
        for row, col in record["span"]:
            output[row][col] = record["color"]
    return output


def _witness_role(grid, role: str) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        record["role"] == role for record in analysis.get("records") or []
    )


def _witness_orientation(grid, orientation: str) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        record["role"] == "active" and record["orientation"] == orientation
        for record in analysis.get("records") or []
    )


def _witness_multiple_active(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and len(analysis.get("active") or []) >= 2


def _witness_repeated_color(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis.get("repeated"))


SEMANTIC_WITNESSES = {
    "horizontal_active": lambda grid: _witness_orientation(grid, "H"),
    "vertical_active": lambda grid: _witness_orientation(grid, "V"),
    "blocked_pair": lambda grid: _witness_role(grid, "blocked"),
    "off_axis_pair": lambda grid: _witness_role(grid, "off_axis"),
    "multiple_active_pairs": _witness_multiple_active,
    "repeated_color": _witness_repeated_color,
}

SEMANTIC_RIVALS = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "ignore_blockers": _rival_ignore_blockers,
    "connect_off_axis": _rival_connect_off_axis,
    "first_active_only": _rival_first_active_only,
    "global_exactly_two": _rival_global_exactly_two,
}

WITNESS_RIVALS = {
    "horizontal_active": ["vertical_only"],
    "vertical_active": ["horizontal_only"],
    "blocked_pair": ["ignore_blockers"],
    "off_axis_pair": ["connect_off_axis"],
    "multiple_active_pairs": ["first_active_only"],
    "repeated_color": ["global_exactly_two"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Every plausible named rival must be falsified by the demonstrations."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(pair["input"]) == pair["output"] for pair in demos):
            continue
        if competitor(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demo but changes the query answer")
        else:
            reasons.append(f"{name} survives every demo and the query")
    return reasons


def mutation_fixtures():
    """Named near-misses that the structural checker must reject."""
    blank = full_grid(7, 8, 0)

    singleton = full_grid(7, 8, 0)
    singleton[1][1] = 2
    singleton[4][1] = 2
    singleton[2][5] = 4

    ambiguous_repeated_color = full_grid(7, 8, 0)
    for row, col in ((1, 1), (1, 4), (5, 1)):
        ambiguous_repeated_color[row][col] = 2
    ambiguous_repeated_color[2][6] = 4
    ambiguous_repeated_color[5][6] = 4

    adjacent_pair = full_grid(7, 8, 0)
    adjacent_pair[1][1] = adjacent_pair[1][2] = 2
    adjacent_pair[2][6] = adjacent_pair[5][6] = 4

    crossing_active = full_grid(7, 8, 0)
    crossing_active[3][1] = crossing_active[3][6] = 2
    crossing_active[1][4] = crossing_active[5][4] = 4

    no_active = full_grid(7, 8, 0)
    no_active[1][1] = no_active[3][3] = 2
    no_active[1][6] = no_active[5][7] = 4

    invalid_color = full_grid(7, 8, 0)
    invalid_color[1][1] = invalid_color[1][4] = 2
    invalid_color[2][6] = 10
    invalid_color[5][6] = 10

    return [
        ("blank_rule_hiding_scene", blank),
        ("singleton_color", singleton),
        ("ambiguous_repeated_color", ambiguous_repeated_color),
        ("adjacent_aligned_pair", adjacent_pair),
        ("crossing_clear_spans", crossing_active),
        ("no_clear_aligned_pair", no_active),
        ("invalid_arc_color", invalid_color),
    ]
