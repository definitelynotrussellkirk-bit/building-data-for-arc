"""Generator for ARC task d5178d26d905 (template/reference row mapping).

A full gray (5) column separates two panels.  The 0/4 panel is a spatial
reference: its sparsest positive-yellow row marks the output line columns and
its denser yellow rows mark ordered special rows.  The colored template's most
common row supplies line colors; its other rows supply ordered fill/retention
variants.  The output repaints the reference geometry with that template.

The three-sample schedule deliberately includes two counterexamples absent
from every canonical demonstration: a third special row and a reference width
other than seven.  Those examples rule out two especially plausible shortcuts
while retaining canonical-scale examples in every lesson window.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5178d26d905"
TASK_ID = GENERATOR_ID
RULE_HASH = "70d9964daef1"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Use a 0/4 reference panel for output positions and ordered special rows, "
    "and a colored template panel for line colors plus special fill variants."
)

INVARIANTS = [
    "exactly one full color-5 column separates two nonempty panels",
    "exactly one active panel contains only 0/4 and is the reference",
    "the template's uniquely most-common row defines line columns and colors",
    "ordered non-normal template rows map to ordered non-normal reference rows",
]

AXES = {
    "reference_side": {
        "type": "str",
        "default": "rng",
        "valid": "left|right",
    },
    "template_alignment": {
        "type": "str",
        "default": "rng",
        "valid": "top|center|bottom",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_scale",
    "third_special",
    "variable_width",
)

# (height, reference width, line count, special-row count).  These reproduce
# all five public shape/palette profiles while varying their internal geometry.
_CANONICAL_PROFILES = (
    (11, 7, 2, 2),  # 11 x 13
    (9, 7, 2, 2),   # 9 x 13
    (7, 7, 2, 1),   # 7 x 13
    (9, 7, 1, 2),   # 9 x 11
    (12, 7, 3, 2),  # 12 x 15
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return a stable three-cycle; any three consecutive samples cover it."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, options in (
        ("reference_side", ("left", "right")),
        ("template_alignment", ("top", "center", "bottom")),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        if value not in options:
            raise ValueError(f"{name} must be one of {options}, got {value!r}")


def _profile_dimensions(
    ctx: Any,
    profile: str,
    sample_index: int,
    difficulty: str | None,
) -> tuple[int, int, int, int]:
    """Choose shape semantics without turning them into fake public axes."""
    if profile == "canonical_scale":
        return _CANONICAL_PROFILES[(int(sample_index) // 3) % len(_CANONICAL_PROFILES)]

    rng = ctx.draw_rng("profile_dimensions")
    if profile == "third_special":
        if difficulty == "easy":
            height = 9
            line_count = 2
            reference_width = 5
        elif difficulty == "hard":
            height = rng.choice((12, 13))
            line_count = 3
            reference_width = 9
        else:
            height = rng.choice((10, 11, 12))
            line_count = rng.choice((2, 3))
            reference_width = rng.choice((5, 9))
        # This profile also varies width so either noncanonical profile alone
        # refutes both canonical-fitting shortcuts under query rotation.
        return height, reference_width, line_count, 3

    if profile == "variable_width":
        if difficulty == "easy":
            height, reference_width = 8, 5
        elif difficulty == "hard":
            height, reference_width = rng.choice((11, 12, 13)), 9
        else:
            height = rng.choice((8, 9, 10, 11, 12))
            reference_width = rng.choice((5, 9))
        # A third special row makes this profile independently refute both
        # canonical-fitting shortcuts, not only the fixed-width shortcut.
        return height, reference_width, 4, 3

    raise ValueError(f"unknown schedule profile {profile!r}")


def _special_template_rows(
    normal: list[int],
    line_columns: list[int],
    line_colors: list[int],
    task_colors: tuple[int, int, int],
    special_count: int,
) -> list[list[int]]:
    rows: list[list[int]] = []
    for special_index in range(special_count):
        fill = task_colors[(len(line_columns) + special_index) % len(task_colors)]
        row = [fill] * len(normal)
        if special_index == 0:
            retained = [True] * len(line_columns)
        elif special_index == 1:
            retained = [False] * len(line_columns)
        else:
            retained = [line_index % 2 == 0 for line_index in range(len(line_columns))]
        for line_index, (column, color) in enumerate(zip(line_columns, line_colors)):
            if retained[line_index]:
                row[column] = color
        rows.append(row)

    # The profiles above make these rows distinct, but fail loudly if a future
    # edit accidentally creates a tie with the normal row or another special.
    signatures = {tuple(normal), *(tuple(row) for row in rows)}
    if len(signatures) != special_count + 1:
        raise RuntimeError("template row construction lost semantic distinctions")
    return rows


def _template_active_rows(
    normal: list[int], special_rows: list[list[int]]
) -> list[list[int]]:
    """Interleave specials with enough normal repeats to make the mode unique."""
    if len(special_rows) == 1:
        return [normal, special_rows[0], normal]
    if len(special_rows) == 2:
        return [normal, special_rows[0], normal, special_rows[1], normal]
    if len(special_rows) == 3:
        return [normal, special_rows[0], normal, special_rows[1], special_rows[2], normal]
    raise ValueError("special row count must be 1..3")


def _alignment_start(height: int, active_height: int, alignment: str) -> int:
    free = height - active_height
    if free < 0:
        raise ValueError("template does not fit selected height")
    if alignment == "top":
        return 0
    if alignment == "bottom":
        return free
    # All scheduled profiles leave at least two rows of slack, so this is
    # visibly centered rather than being confused with top/bottom alignment.
    return free // 2


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    side = ctx.draw_choice("reference_side", ("left", "right"))
    alignment = ctx.draw_choice("template_alignment", ("top", "center", "bottom"))
    profile = schedule_profile(seed, sample_index, difficulty)
    height, reference_width, line_count, special_count = _profile_dimensions(
        ctx, profile, sample_index, difficulty
    )

    task_colors = ctx.draw_distinct_colors("task_colors", n=3, exclude={0, 4, 5})
    geometry_rng = ctx.draw_rng("geometry")

    template_width = 2 * line_count + 1
    template_line_columns = list(range(1, template_width, 2))
    line_colors = [task_colors[index % 3] for index in range(line_count)]
    template_normal = [0] * template_width
    for column, color in zip(template_line_columns, line_colors):
        template_normal[column] = color
    template_specials = _special_template_rows(
        template_normal,
        template_line_columns,
        line_colors,
        task_colors,
        special_count,
    )
    active_template = _template_active_rows(template_normal, template_specials)
    template_start = _alignment_start(height, len(active_template), alignment)
    template = full_grid(height, template_width, 5)
    for offset, row in enumerate(active_template):
        template[template_start + offset] = list(row)

    reference_line_columns = sorted(
        geometry_rng.sample(range(reference_width), line_count)
    )
    reference_normal = [0] * reference_width
    for column in reference_line_columns:
        reference_normal[column] = 4
    extra_columns = [
        column for column in range(reference_width)
        if column not in reference_line_columns
    ]
    if not extra_columns:
        raise RuntimeError("reference profile leaves no special-row marker column")

    row_order = list(range(height))
    geometry_rng.shuffle(row_order)
    special_raw_rows = sorted(row_order[:special_count])
    normal_raw_rows = row_order[special_count:special_count + 2]
    if not normal_raw_rows:
        raise RuntimeError("reference profile leaves no normal marker row")

    reference = full_grid(height, reference_width, 0)
    for row in normal_raw_rows:
        reference[row] = list(reference_normal)
    for special_index, row in enumerate(special_raw_rows):
        special = list(reference_normal)
        # At least one extra yellow makes the row distinguishable from the
        # sparsest positive-yellow normal row.  Vary the prefix when possible.
        extra_count = 1 + (special_index % len(extra_columns))
        for column in extra_columns[:extra_count]:
            special[column] = 4
        reference[row] = special

    total_width = reference_width + 1 + template_width
    grid = full_grid(height, total_width, 5)
    if side == "left":
        divider = reference_width
        for row in range(height):
            grid[row][:reference_width] = reference[row]
            grid[row][divider + 1:] = template[row]
    else:
        divider = template_width
        for row in range(height):
            grid[row][:template_width] = template[row]
            grid[row][divider + 1:] = reference[row]
    return grid


def _rectangular(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors")
    return len(grid), width


def _active_rows(
    grid: list[list[int]] | tuple[tuple[int, ...], ...], c0: int, c1: int
) -> tuple[list[list[int]], list[int]]:
    indexes = [
        row
        for row in range(len(grid))
        if any(grid[row][column] != 5 for column in range(c0, c1))
    ]
    return (
        [[grid[row][column] for column in range(c0, c1)] for row in indexes],
        indexes,
    )


def _facts(grid: Any) -> dict[str, Any]:
    height, width = _rectangular(grid)
    dividers = [
        column
        for column in range(width)
        if all(grid[row][column] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected exactly one solid color-5 divider, found {dividers}")
    divider = dividers[0]
    if divider == 0 or divider == width - 1:
        raise ValueError("divider must separate two nonempty panels")

    left, left_rows = _active_rows(grid, 0, divider)
    right, right_rows = _active_rows(grid, divider + 1, width)
    if not left or not right:
        raise ValueError("both panels need active rows")

    def is_reference(panel: list[list[int]]) -> bool:
        return all(value in (0, 4) for row in panel for value in row)

    left_reference = is_reference(left)
    right_reference = is_reference(right)
    if left_reference == right_reference:
        raise ValueError("exactly one active panel must be a 0/4 reference")

    if left_reference:
        reference, reference_rows = left, left_rows
        template, template_rows = right, right_rows
        reference_side = "left"
    else:
        reference, reference_rows = right, right_rows
        template, template_rows = left, left_rows
        reference_side = "right"

    template_counts = Counter(tuple(row) for row in template)
    highest = max(template_counts.values())
    normal_candidates = [row for row, count in template_counts.items() if count == highest]
    if len(normal_candidates) != 1:
        raise ValueError("template normal row must be uniquely most common")
    template_normal = list(normal_candidates[0])
    template_line_columns = [
        column for column, value in enumerate(template_normal) if value != 0
    ]
    if not template_line_columns:
        raise ValueError("template normal row has no line colors")
    line_colors = [template_normal[column] for column in template_line_columns]
    template_special_indexes = [
        row for row, values in enumerate(template) if values != template_normal
    ]
    if not template_special_indexes:
        raise ValueError("template has no special row")

    yellow_counts = [sum(value == 4 for value in row) for row in reference]
    positive_counts = [count for count in yellow_counts if count > 0]
    if not positive_counts:
        raise ValueError("reference has no positive-yellow row")
    minimum = min(positive_counts)
    reference_normal_candidates = {
        tuple(row)
        for row, count in zip(reference, yellow_counts)
        if count == minimum
    }
    if len(reference_normal_candidates) != 1:
        raise ValueError("reference normal row is not uniquely identifiable")
    reference_normal = list(next(iter(reference_normal_candidates)))
    reference_line_columns = [
        column for column, value in enumerate(reference_normal) if value == 4
    ]
    reference_special_indexes = [
        row
        for row, values in enumerate(reference)
        if any(value == 4 for value in values) and values != reference_normal
    ]

    if len(reference_line_columns) != len(template_line_columns):
        raise ValueError("reference/template line counts differ")
    if len(reference_special_indexes) != len(template_special_indexes):
        raise ValueError("reference/template special-row counts differ")

    off_line_columns = [
        column
        for column in range(len(template_normal))
        if column not in template_line_columns
    ]
    if not off_line_columns:
        raise ValueError("template has no off-line fill column")

    fills: list[int] = []
    retention: list[tuple[bool, ...]] = []
    for row_index in template_special_indexes:
        row = template[row_index]
        fill = row[off_line_columns[0]]
        if any(row[column] != fill for column in off_line_columns):
            raise ValueError("special template row has inconsistent off-line fill")
        fills.append(fill)
        retention.append(
            tuple(
                row[column] == color
                for column, color in zip(template_line_columns, line_colors)
            )
        )

    active_start = template_rows[0]
    active_end = template_rows[-1]
    top_gap = active_start
    bottom_gap = height - 1 - active_end
    if top_gap == 0:
        alignment = "top"
    elif bottom_gap == 0:
        alignment = "bottom"
    elif abs(top_gap - bottom_gap) <= 1:
        alignment = "center"
    else:
        alignment = "offset"

    return {
        "height": height,
        "width": width,
        "divider": divider,
        "reference_side": reference_side,
        "reference": reference,
        "reference_rows": reference_rows,
        "reference_width": len(reference[0]),
        "reference_normal": reference_normal,
        "reference_line_columns": reference_line_columns,
        "reference_special_indexes": reference_special_indexes,
        "template": template,
        "template_rows": template_rows,
        "template_width": len(template[0]),
        "template_normal": template_normal,
        "template_line_columns": template_line_columns,
        "line_colors": line_colors,
        "template_special_indexes": template_special_indexes,
        "fills": fills,
        "retention": retention,
        "template_alignment": alignment,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural errors without raising, including malformed inputs."""
    del difficulty, meta
    try:
        _facts(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """The strict domain is the unambiguous structural domain of the rule."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority."""
    info = _facts(grid)
    reference = info["reference"]
    line_columns = info["reference_line_columns"]
    special_rows = info["reference_special_indexes"]
    line_colors = info["line_colors"]
    fills = info["fills"]
    retention = info["retention"]
    special_lookup = {row: index for index, row in enumerate(special_rows)}

    output = [[0 for _ in row] for row in reference]
    for row_index in range(len(reference)):
        special_index = special_lookup.get(row_index)
        if special_index is None:
            for column, color in zip(line_columns, line_colors):
                output[row_index][column] = color
            continue
        fill = fills[special_index]
        output[row_index] = [fill] * len(reference[row_index])
        for line_index, column in enumerate(line_columns):
            if retention[special_index][line_index]:
                output[row_index][column] = line_colors[line_index]
    return output


def observe_overrides(grid) -> dict[str, str]:
    info = _facts(grid)
    return {
        "reference_side": info["reference_side"],
        "template_alignment": info["template_alignment"],
    }


def _first_two_special_rows_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: only the first two variants are meaningful."""
    info = _facts(grid)
    output = rule_mirror(grid)
    for row in info["reference_special_indexes"][2:]:
        output[row] = [0] * info["reference_width"]
        for column, color in zip(
            info["reference_line_columns"], info["line_colors"]
        ):
            output[row][column] = color
    return output


def _fixed_reference_width_seven(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: canonical output width seven is intrinsic."""
    output = rule_mirror(grid)
    return [row[:7] + [0] * max(0, 7 - len(row)) for row in output]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_two_special_rows_only": _first_two_special_rows_only,
    "fixed_reference_width_seven": _fixed_reference_width_seven,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _safe_witness(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    try:
        return bool(predicate(_facts(grid)))
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "third_special_row": lambda grid: _safe_witness(
        grid, lambda info: len(info["reference_special_indexes"]) >= 3
    ),
    "variable_reference_width": lambda grid: _safe_witness(
        grid, lambda info: info["reference_width"] != 7
    ),
}
WITNESS_RIVALS = {
    "third_special_row": [
        "first_two_special_rows_only",
        "fixed_reference_width_seven",
    ],
    "variable_reference_width": [
        "first_two_special_rows_only",
        "fixed_reference_width_seven",
    ],
}


def lesson_identifiable(
    demos: list[dict[str, Any]], query: dict[str, Any]
) -> list[str]:
    """Name any declared rival that survives every demonstration."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            if survives and rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"competitor {name} could not be evaluated: {exc}")
    return reasons


def mutation_fixtures() -> list[dict[str, Any]]:
    """Small deterministic structural mutations for generic review tooling."""
    base = generate(44, 1)
    info = _facts(base)
    no_divider = deepcopy(base)
    no_divider[0][info["divider"]] = 0

    missing_special = deepcopy(base)
    special_index = info["reference_special_indexes"][0]
    raw_row = info["reference_rows"][special_index]
    start = 0 if info["reference_side"] == "left" else info["divider"] + 1
    missing_special[raw_row][start:start + info["reference_width"]] = info["reference_normal"]
    return [
        {"name": "broken_divider", "grid": no_divider},
        {"name": "missing_reference_special", "grid": missing_special},
    ]
