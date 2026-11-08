"""Task-linked generator for ARC task 703a842c8e24.

The first cell of every row is a shift header.  The rest of that row is
cyclically rotated to the right by ``header mod body_width``; the header stays
fixed.  A four-profile schedule deliberately teaches the parts of the rule
that the public examples leave ambiguous: headers larger than four,
wraparound rather than clipping, modulo-identity shifts, and row-local rather
than global headers.
"""
from __future__ import annotations

from math import gcd
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "703a842c8e24"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3ecc6b0e255e"

SUMMARY = (
    "Each row keeps its first-cell shift header and cyclically rotates the "
    "remaining cells right by that row's header modulo the body width. A "
    "four-profile schedule exposes wraparound, modulo identity, large headers, "
    "scattered bodies, and row-specific shifts."
)

INVARIANTS = [
    "all cells are ARC integers 0..9 and background is 0",
    "every row begins with a nonzero shift header",
    "every row body contains both background and foreground",
    "at least two body colors and at least two header values are present",
    "at least one row undergoes a visible non-identity cyclic rotation",
    "the canonical Racket program remains the output authority",
]

PROFILES = ("canonical", "wraparound", "mixed_modulo", "dense_scattered")
SCHEDULE_PROFILES = PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile- and difficulty-linked",
        "valid": "3..8",
        "doc": "Exact grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "profile- and difficulty-linked",
        "valid": "6..13",
        "doc": "Exact grid width, including the header column.",
    },
    "n_body_colors": {
        "type": "int",
        "default": "rng 2..6",
        "valid": "2..6",
        "doc": "Exact number of distinct nonzero colors in row bodies.",
    },
    "profile": {
        "type": "str",
        "default": "sample_index mod 4 curriculum",
        "valid": ("canonical", "wraparound", "mixed_modulo", "dense_scattered"),
        "probe": "diagnostic",
        "doc": "Internal lesson profile; exact semantic effects can depend on dimensions.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _right_rotate(body: Sequence[int], shift: int) -> list[int]:
    values = list(body)
    if not values:
        return []
    amount = int(shift) % len(values)
    if amount == 0:
        return values
    return values[-amount:] + values[:-amount]


def _nonzero_runs(body: Sequence[int]) -> int:
    runs = 0
    active = False
    for value in body:
        if value != 0 and not active:
            runs += 1
            active = True
        elif value == 0:
            active = False
    return runs


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    body_width = width - 1
    if body_width <= 0:
        return {"errors": ["grid needs a header column and a non-empty body"]}

    headers = [int(row[0]) for row in grid]
    bodies = [list(row[1:]) for row in grid]
    shifts = [header % body_width for header in headers]
    rotated = [_right_rotate(body, header) for header, body in zip(headers, bodies)]
    truth = [[header, *out] for header, out in zip(headers, rotated)]

    wrap_rows = []
    identity_rows = []
    scattered_rows = []
    for index, (body, shift, out) in enumerate(zip(bodies, shifts, rotated)):
        if shift > 0 and any(value != 0 for value in body[body_width - shift :]):
            wrap_rows.append(index)
        if out == body:
            identity_rows.append(index)
        if _nonzero_runs(body) >= 2:
            scattered_rows.append(index)

    return {
        "errors": [],
        "height": height,
        "width": width,
        "body_width": body_width,
        "headers": headers,
        "bodies": bodies,
        "effective_shifts": shifts,
        "truth": truth,
        "body_colors": {
            value for body in bodies for value in body if value != 0
        },
        "wrap_rows": wrap_rows,
        "identity_rows": identity_rows,
        "scattered_rows": scattered_rows,
        "visible_rows": [
            index for index, (body, out) in enumerate(zip(bodies, rotated)) if body != out
        ],
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python diagnostic mirror; the canonical Racket rule is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["truth"]]


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the executable grammar without enforcing profile marginals."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height = analysis["height"]
    width = analysis["width"]
    if not 3 <= height <= 8:
        errors.append(f"height {height} is outside 3..8")
    if not 6 <= width <= 13:
        errors.append(f"width {width} is outside 6..13")

    headers = analysis["headers"]
    for row_index, (header, body) in enumerate(zip(headers, analysis["bodies"])):
        if not 1 <= header <= 9:
            errors.append(f"row {row_index} header must be in 1..9")
        if not any(value != 0 for value in body):
            errors.append(f"row {row_index} body has no foreground")
        if not any(value == 0 for value in body):
            errors.append(f"row {row_index} body has no background")

    if len(set(headers)) < 2:
        errors.append("at least two distinct row headers are required")
    if len(analysis["body_colors"]) < 2:
        errors.append("at least two distinct nonzero body colors are required")
    if not analysis["visible_rows"]:
        errors.append("all row rotations are visually identity")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the empirical public-example manifold, not just any lawful grid."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) != (4, 9):
        errors.append("canonical examples are exactly 4x9")
    if set(analysis["headers"]) != {1, 2, 3, 4}:
        errors.append("canonical examples use row headers 1,2,3,4 exactly once")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in {5, 6, 7}:
        errors.append("canonical examples use five to seven colors including zero")
    return errors


def observe_overrides(grid: Grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_body_colors": len(analysis["body_colors"]),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every consecutive four examples visit every semantic lesson profile."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))


def _draw_int_axis(ctx, overrides: dict[str, Any], label: str, default_bounds: tuple[int, int], global_bounds: tuple[int, int]) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, *global_bounds)
    return ctx.draw_int(label, *default_bounds)


def _default_dimension_bounds(profile: str, difficulty: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if profile == "canonical":
        return (4, 4), (9, 9)
    table = {
        "easy": {
            "wraparound": ((3, 5), (6, 9)),
            "mixed_modulo": ((3, 5), (6, 9)),
            "dense_scattered": ((3, 5), (6, 9)),
        },
        "medium": {
            "wraparound": ((4, 6), (8, 11)),
            "mixed_modulo": ((4, 6), (7, 10)),
            "dense_scattered": ((4, 6), (8, 11)),
        },
        "hard": {
            "wraparound": ((6, 8), (10, 13)),
            "mixed_modulo": ((6, 8), (9, 10)),
            "dense_scattered": ((6, 8), (10, 13)),
        },
    }
    return table[difficulty][profile]


def _coprime_large_header(body_width: int, rng) -> int:
    choices = [value for value in range(5, 10) if value % body_width and gcd(value, body_width) == 1]
    if not choices:
        choices = [value for value in range(5, 10) if value % body_width]
    if not choices:
        choices = [1]
    return rng.choice(choices)


def _headers_for(profile: str, height: int, body_width: int, rng) -> list[int]:
    if profile == "canonical":
        return [1 + (row % 4) for row in range(height)]

    headers = [rng.randint(1, 9) for _ in range(height)]
    if profile == "wraparound":
        headers[0] = _coprime_large_header(body_width, rng)
        headers[1] = 1 if headers[0] != 1 else 2
    elif profile == "mixed_modulo":
        headers[0] = body_width if body_width <= 9 else 9
        headers[1] = 1 if headers[0] != 1 else 2
    else:
        headers[0] = _coprime_large_header(body_width, rng)
        headers[1] = 1 if headers[0] != 1 else 2

    if len(set(headers)) < 2:
        headers[-1] = 2 if headers[0] != 2 else 3
    return headers


def _separated_pair(rng, body_width: int) -> set[int]:
    choices = [
        (left, right)
        for left in range(1, body_width)
        for right in range(left + 2, body_width)
    ]
    if choices:
        return set(rng.choice(choices))
    return set(rng.sample(list(range(1, body_width)), 2))


def _sparse_pair(rng, body_width: int) -> set[int]:
    return set(rng.sample(list(range(1, body_width)), 2))


def _positions_for(profile: str, height: int, body_width: int, rng) -> list[set[int]]:
    positions: list[set[int]] = []
    for row in range(height):
        if profile == "dense_scattered":
            available = list(range(1, body_width))
            if row == 0:
                selected = {1, 3}
                extras = [value for value in available if value not in {1, 2, 3}]
                desired = rng.randint(2, max(2, body_width - 2))
                rng.shuffle(extras)
                selected.update(extras[: max(0, desired - len(selected))])
            else:
                desired = rng.randint(max(2, (body_width - 1) // 2), body_width - 1)
                selected = set(rng.sample(available, desired))
        elif row == 0 and profile == "wraparound":
            other = rng.choice(list(range(1, body_width - 1)))
            selected = {other, body_width - 1}
        elif row == 0 and profile in {"canonical", "mixed_modulo"}:
            selected = _separated_pair(rng, body_width)
        elif row == 1 and profile == "mixed_modulo":
            other = rng.choice(list(range(1, body_width - 1)))
            selected = {other, body_width - 1}
        else:
            selected = _sparse_pair(rng, body_width)
        positions.append(selected)
    return positions


def _body_palette(profile: str, count: int, rng) -> list[int]:
    if profile == "canonical":
        header_colors = [1, 2, 3, 4]
        extra_colors = [5, 6]
        rng.shuffle(header_colors)
        rng.shuffle(extra_colors)
        return (header_colors + extra_colors)[:count]
    return rng.sample(list(range(1, 10)), count)


def _build_grid(profile: str, height: int, width: int, n_body_colors: int, header_rng, layout_rng, palette_rng) -> Grid:
    body_width = width - 1
    headers = _headers_for(profile, height, body_width, header_rng)
    positions = _positions_for(profile, height, body_width, layout_rng)
    flat_positions = [(row, column) for row, row_positions in enumerate(positions) for column in sorted(row_positions)]
    if len(flat_positions) < n_body_colors:
        raise AssertionError("constructor did not reserve enough foreground cells for the palette")

    palette = _body_palette(profile, n_body_colors, palette_rng)
    palette_rng.shuffle(flat_positions)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, header in enumerate(headers):
        grid[row][0] = header

    for color, (row, body_column) in zip(palette, flat_positions):
        grid[row][1 + body_column] = color
    for row, body_column in flat_positions[len(palette) :]:
        grid[row][1 + body_column] = palette_rng.choice(palette)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    band = difficulty or "medium"

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "profile" in overrides and overrides["profile"] is not None:
        profile = ctx.draw_choice("profile", PROFILES)
    else:
        profile = ctx.draw_choice("profile", (scheduled,))

    height_bounds, width_bounds = _default_dimension_bounds(profile, band)
    height = _draw_int_axis(ctx, overrides, "grid_h", height_bounds, (3, 8))
    width = _draw_int_axis(ctx, overrides, "grid_w", width_bounds, (6, 13))
    n_body_colors = ctx.draw_int("n_body_colors", 2, 6)

    grid = _build_grid(
        profile,
        height,
        width,
        n_body_colors,
        ctx.draw_rng("headers"),
        ctx.draw_rng("layout"),
        ctx.draw_rng("palette"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("constructed invalid instance: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_body_colors": n_body_colors,
    }
    if observed != expected:
        raise AssertionError(f"constructor failed to realize exact axes: {observed!r} != {expected!r}")
    return [row[:] for row in grid]


def _rival_headers_1_to_4_else_identity(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    result = []
    for header, body in zip(analysis["headers"], analysis["bodies"]):
        result.append([header, *(_right_rotate(body, header) if header <= 4 else list(body))])
    return result


def _rival_clip_right_no_wrap(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    result = []
    for header, body, shift in zip(analysis["headers"], analysis["bodies"], analysis["effective_shifts"]):
        shifted = list(body) if shift == 0 else [0] * shift + list(body[:-shift])
        result.append([header, *shifted])
    return result


def _rival_zero_modulo_moves_one(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    result = []
    for header, body, shift in zip(analysis["headers"], analysis["bodies"], analysis["effective_shifts"]):
        result.append([header, *_right_rotate(body, 1 if shift == 0 else shift)])
    return result


def _rival_first_header_for_all_rows(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    first = analysis["headers"][0]
    return [
        [header, *_right_rotate(body, first)]
        for header, body in zip(analysis["headers"], analysis["bodies"])
    ]


SEMANTIC_RIVALS: dict[str, Rival] = {
    "headers_1_to_4_else_identity": _rival_headers_1_to_4_else_identity,
    "clip_right_without_wraparound": _rival_clip_right_no_wrap,
    "zero_modulo_moves_one": _rival_zero_modulo_moves_one,
    "use_first_header_for_all_rows": _rival_first_header_for_all_rows,
}
CANONICAL_SHORTCUTS = {
    "headers_1_to_4_else_identity": _rival_headers_1_to_4_else_identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def semantic_observables(grid: Grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    truth = analysis["truth"]
    return {
        **observe_overrides(grid),
        "large_header": any(header > 4 for header in analysis["headers"]),
        "wraparound_row": bool(analysis["wrap_rows"]),
        "identity_modulo_row": bool(analysis["identity_rows"]),
        "scattered_row": bool(analysis["scattered_rows"]),
        "row_specific_headers": len(set(analysis["headers"])) >= 2,
        "visible_transform": truth != [list(row) for row in grid],
    }


def _rival_disagrees(grid: Grid, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "large_header_counterexample": lambda grid: (
        semantic_observables(grid).get("large_header") is True
        and _rival_disagrees(grid, "headers_1_to_4_else_identity")
    ),
    "cyclic_wraparound_counterexample": lambda grid: (
        semantic_observables(grid).get("wraparound_row") is True
        and _rival_disagrees(grid, "clip_right_without_wraparound")
    ),
    "modulo_identity_counterexample": lambda grid: (
        semantic_observables(grid).get("identity_modulo_row") is True
        and _rival_disagrees(grid, "zero_modulo_moves_one")
    ),
    "row_specific_headers_counterexample": lambda grid: (
        semantic_observables(grid).get("row_specific_headers") is True
        and _rival_disagrees(grid, "use_first_header_for_all_rows")
    ),
}

WITNESS_RIVALS = {
    "large_header_counterexample": ["headers_1_to_4_else_identity"],
    "cyclic_wraparound_counterexample": ["clip_right_without_wraparound"],
    "modulo_identity_counterexample": ["zero_modulo_moves_one"],
    "row_specific_headers_counterexample": ["use_first_header_for_all_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that a four-example lesson falsifies every named finite rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Grid]] = []
    witness_hits = {name: False for name in SEMANTIC_WITNESSES}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the row-rotation rule")
            continue
        valid_demos.append(demo)
        for name, predicate in SEMANTIC_WITNESSES.items():
            witness_hits[name] |= bool(predicate(demo["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[0]}")
    else:
        expected_query = rule_mirror(query["input"])
        if query.get("output") is not None and query["output"] != expected_query:
            reasons.append("query output disagrees with the row-rotation rule")
    if reasons:
        return reasons

    for name, hit in witness_hits.items():
        if not hit:
            reasons.append(f"demonstrations do not include witness {name}")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"competitor {name!r} still fits every demonstration")
    return reasons
