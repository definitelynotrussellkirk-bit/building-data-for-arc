"""Generator for 21ada29469bf — sort an inner matrix by row/column headers.

The input is a square ``(n+1) x (n+1)`` grid.  Cell ``(0, 0)`` is an unused
zero.  The remaining top-row cells are column keys and the remaining left-edge
cells are row keys.  Both key strips are permutations of ``1..n``.  The output
is the inner ``n x n`` body with rows ordered by increasing left key and
columns ordered by increasing top key.

The default four-example curriculum deliberately contains all three linked
canonical header profiles plus a larger row-only reorder.  This simultaneously
anchors canonical scale, varies output size, and refutes identity, one-axis,
fixed-3x3, and body-texture shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "21ada29469bf"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "32d07d8a907c"

SUMMARY = (
    "Treat the first row and first column as metadata. Sort the inner body's "
    "rows by the ascending left-edge keys and its columns by the ascending "
    "top-edge keys, then output only that reordered body."
)

INVARIANTS = [
    "the grid is square and cell (0,0) is 0",
    "top-row cells 1..n and left-column cells 1..n are each a permutation of 1..n",
    "the inner n x n body is data and the output shape is exactly n x n",
    "row and column permutations are independent; either axis may already be ordered",
]

PERM_KINDS = (
    "identity",
    "reverse",
    "rotate_left",
    "rotate_right",
    "swap_first",
    "swap_last",
)

# Every exact axis can be recovered from a returned grid by observe_overrides().
# The single forbidden Cartesian point is a lawful oracle input but a no-op
# teaching example, so generation rejects it explicitly while self_check keeps
# the structural/oracle grammar separate from curriculum policy.
AXES = {
    "n": {"type": "int", "default": "four-profile schedule", "valid": "3..5"},
    "row_perm": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "|".join(PERM_KINDS),
    },
    "col_perm": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "|".join(PERM_KINDS),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"row_perm": "identity", "col_perm": "identity"},
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

# These are the exact linked (row keys, column keys) profiles in the two train
# examples and held-out canonical query.  Mixing a row strip from one with a
# column strip from another is structurally executable, but not strict-linked
# canonical evidence.
_CANONICAL_HEADER_SIGNATURES = frozenset(
    {
        ((2, 3, 1), (3, 1, 2)),
        ((3, 1, 2), (2, 1, 3)),
        ((1, 2, 3), (3, 2, 1)),
    }
)

# (name, n, row permutation kind, column permutation kind)
_SCHEDULE = (
    ("canonical_train_a", 3, "rotate_left", "rotate_right"),
    ("canonical_train_b", 3, "rotate_right", "swap_first"),
    ("canonical_query", 3, "identity", "reverse"),
    ("larger_row_only", 5, "reverse", "identity"),
)
SCHEDULE_PROFILES = tuple(profile[0] for profile in _SCHEDULE)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the period-four curriculum to the lesson-level semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _permutation(kind: str, n: int) -> list[int]:
    values = list(range(1, n + 1))
    if kind == "identity":
        return values
    if kind == "reverse":
        return list(reversed(values))
    if kind == "rotate_left":
        return values[1:] + values[:1]
    if kind == "rotate_right":
        return values[-1:] + values[:-1]
    if kind == "swap_first":
        values[0], values[1] = values[1], values[0]
        return values
    if kind == "swap_last":
        values[-2], values[-1] = values[-1], values[-2]
        return values
    raise ValueError(f"unknown permutation kind: {kind!r}")


def _permutation_kind(values: list[int]) -> str | None:
    n = len(values)
    for kind in PERM_KINDS:
        if values == _permutation(kind, n):
            return kind
    return None


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], default: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if height != width:
        errors.append(f"grid must be square, found {height}x{width}")
    n = height - 1
    if not 2 <= n <= 8:
        errors.append(f"body size n must be in 2..8, found {n}")
    if grid[0][0] != 0:
        errors.append(f"cell (0,0) must be 0, found {grid[0][0]}")

    row_keys = [grid[row][0] for row in range(1, height)]
    col_keys = [grid[0][col] for col in range(1, width)]
    expected = list(range(1, n + 1)) if n >= 0 else []
    if sorted(row_keys) != expected:
        errors.append(f"left-edge row keys must be a permutation of 1..{n}: {row_keys}")
    if sorted(col_keys) != expected:
        errors.append(f"top-edge column keys must be a permutation of 1..{n}: {col_keys}")

    body = [list(row[1:]) for row in grid[1:]]
    body_palette = frozenset(value for row in body for value in row)
    row_kind = _permutation_kind(row_keys) if 3 <= n <= 5 else None
    col_kind = _permutation_kind(col_keys) if 3 <= n <= 5 else None

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "n": n,
        "row_keys": row_keys,
        "col_keys": col_keys,
        "body": body,
        "body_palette": body_palette,
        "row_perm": row_kind,
        "col_perm": col_kind,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return nested
    return {name: meta[name] for name in AXES if name in meta}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural input grammar and exact generated overrides."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested = _meta_overrides(meta)
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def canonical_profile_signature(grid):
    """Return the complete linked canonical header profile, else ``None``."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["n"] != 3:
        return None
    if analysis["body_palette"] != frozenset(range(4, 10)):
        return None
    signature = (tuple(analysis["row_keys"]), tuple(analysis["col_keys"]))
    return signature if signature in _CANONICAL_HEADER_SIGNATURES else None


def strict_canonical_like(grid) -> list[str]:
    """Require one complete official linked profile, not mixed marginals."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["n"] != 3:
        errors.append(f"strict canonical body size is 3, found {analysis['n']}")
    if analysis["body_palette"] != frozenset(range(4, 10)):
        errors.append(
            "strict canonical body palette must contain every color 4..9 and no others"
        )
    signature = (tuple(analysis["row_keys"]), tuple(analysis["col_keys"]))
    if signature not in _CANONICAL_HEADER_SIGNATURES:
        errors.append(f"header strips are not one complete linked canonical profile: {signature}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact caller-facing axis from a generated lawful grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    if not 3 <= analysis["n"] <= 5:
        return {}
    if analysis["row_perm"] is None or analysis["col_perm"] is None:
        return {}
    return {
        "n": analysis["n"],
        "row_perm": analysis["row_perm"],
        "col_perm": analysis["col_perm"],
    }


def profile_signature(grid) -> tuple[Any, ...] | None:
    """Task-linked signature used by focused census evidence."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["n"],
        tuple(analysis["row_keys"]),
        tuple(analysis["col_keys"]),
        tuple(sorted(analysis["body_palette"])),
    )


def _row_order(row_keys: list[int]) -> list[int]:
    return sorted(range(len(row_keys)), key=row_keys.__getitem__)


def _col_order(col_keys: list[int]) -> list[int]:
    return sorted(range(len(col_keys)), key=col_keys.__getitem__)


def _reorder(body: list[list[int]], row_order: list[int], col_order: list[int]):
    return [[body[row][col] for col in col_order] for row in row_order]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _reorder(
        analysis["body"],
        _row_order(analysis["row_keys"]),
        _col_order(analysis["col_keys"]),
    )


def _rival_identity_inner(grid):
    return [row[:] for row in _analysis(grid)["body"]]


def _rival_rows_only(grid):
    analysis = _analysis(grid)
    n = analysis["n"]
    return _reorder(analysis["body"], _row_order(analysis["row_keys"]), list(range(n)))


def _rival_columns_only(grid):
    analysis = _analysis(grid)
    n = analysis["n"]
    return _reorder(analysis["body"], list(range(n)), _col_order(analysis["col_keys"]))


def _rival_lexicographic_body(grid):
    """Ignore headers and infer order only from body texture."""
    body = [row[:] for row in _analysis(grid)["body"]]
    rows = sorted(body)
    col_order = sorted(
        range(len(rows[0])),
        key=lambda col: tuple(row[col] for row in rows),
    )
    return [[row[col] for col in col_order] for row in rows]


def _rival_fixed_3x3_only(grid):
    truth = rule_mirror(grid)
    return [row[:3] for row in truth[:3]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity_inner": _rival_identity_inner,
    "rows_only": _rival_rows_only,
    "columns_only": _rival_columns_only,
    "body_lexicographic": _rival_lexicographic_body,
    "fixed_3x3_only": _rival_fixed_3x3_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_3x3_only": _rival_fixed_3x3_only}


def semantic_features(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    truth = rule_mirror(grid)
    return {
        "errors": [],
        "n": analysis["n"],
        "row_perm": analysis["row_perm"],
        "col_perm": analysis["col_perm"],
        "row_moves": analysis["row_keys"] != list(range(1, analysis["n"] + 1)),
        "col_moves": analysis["col_keys"] != list(range(1, analysis["n"] + 1)),
        "strict_signature": canonical_profile_signature(grid),
        "lexicographic_differs": _rival_lexicographic_body(grid) != truth,
        "fixed_3x3_differs": _rival_fixed_3x3_only(grid) != truth,
    }


def _feature_predicate(name: str):
    return lambda grid: bool(semantic_features(grid).get(name))


SEMANTIC_WITNESSES = {
    "both_axes_reordered": lambda grid: bool(
        (features := semantic_features(grid)).get("row_moves")
        and features.get("col_moves")
    ),
    "row_only_reordered": lambda grid: bool(
        (features := semantic_features(grid)).get("row_moves")
        and not features.get("col_moves")
    ),
    "column_only_reordered": lambda grid: bool(
        not (features := semantic_features(grid)).get("row_moves")
        and features.get("col_moves")
    ),
    "headers_beat_body_texture": _feature_predicate("lexicographic_differs"),
    "larger_than_fixed_3x3": _feature_predicate("fixed_3x3_differs"),
}

WITNESS_RIVALS = {
    "both_axes_reordered": ["identity_inner", "rows_only", "columns_only"],
    "row_only_reordered": ["identity_inner", "columns_only"],
    "column_only_reordered": ["identity_inner", "rows_only"],
    "headers_beat_body_texture": ["body_lexicographic"],
    "larger_than_fixed_3x3": ["fixed_3x3_only"],
}


def _pair_errors(pair: Any, label: str, *, output_required: bool) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} must contain an input grid"]
    errors = [f"{label}: {message}" for message in self_check(pair["input"])]
    if output_required and "output" not in pair:
        errors.append(f"{label} must contain an output grid")
    elif "output" in pair and pair["output"] != rule_mirror(pair["input"]):
        errors.append(f"{label} output disagrees with header-guided row/column sorting")
    return errors


def lesson_identifiable(demos, query) -> list[str]:
    """Require every sliding four-demo window to kill the named shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}", output_required=True))
    reasons.extend(_pair_errors(query, "query", output_required=False))
    if reasons:
        return reasons

    features = [semantic_features(pair["input"]) for pair in demos]
    if not any(item["row_moves"] and item["col_moves"] for item in features):
        reasons.append("demonstrations never require sorting both axes")
    if not any(item["row_moves"] and not item["col_moves"] for item in features):
        reasons.append("demonstrations never isolate row sorting with columns already ordered")
    if not any(not item["row_moves"] and item["col_moves"] for item in features):
        reasons.append("demonstrations never isolate column sorting with rows already ordered")
    if not any(item["strict_signature"] is not None for item in features):
        reasons.append("demonstrations contain no complete linked canonical anchor")
    if not any(item["n"] > 3 for item in features):
        reasons.append("demonstrations never refute a fixed-3x3 interpretation")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor survives every demonstration: {name}")
    return reasons


def _build(n: int, row_keys: list[int], col_keys: list[int], body: list[list[int]]):
    grid = full_grid(n + 1, n + 1, 0)
    for index in range(n):
        grid[index + 1][0] = row_keys[index]
        grid[0][index + 1] = col_keys[index]
    for row in range(n):
        for col in range(n):
            grid[row + 1][col + 1] = body[row][col]
    return grid


def _balanced_body(n: int, rng, row_keys: list[int], col_keys: list[int]):
    """Construct varied data with no accidental rival equivalences."""
    colors = list(range(n + 1, 10))
    values = [colors[index % len(colors)] for index in range(n * n)]
    for _ in range(512):
        rng.shuffle(values)
        body = [values[row * n : (row + 1) * n] for row in range(n)]
        if len({tuple(row) for row in body}) != n:
            continue
        columns = {tuple(body[row][col] for row in range(n)) for col in range(n)}
        if len(columns) != n:
            continue
        grid = _build(n, row_keys, col_keys, body)
        truth = rule_mirror(grid)
        if truth == body:
            continue
        if _rival_lexicographic_body(grid) == truth:
            continue
        return [row[:] for row in body]
    raise ValueError("could not construct a shortcut-separating inner body")


def mutation_fixtures():
    """Targeted malformed scenes for strict defect-lint and focused tests."""
    base = generate(191, 0, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    bad_corner = [row[:] for row in base]
    bad_corner[0][0] = 9
    fixtures.append(("nonzero_corner", bad_corner))

    duplicate_top_key = [row[:] for row in base]
    duplicate_top_key[0][2] = duplicate_top_key[0][1]
    fixtures.append(("duplicate_top_key", duplicate_top_key))

    missing_left_key = [row[:] for row in base]
    missing_left_key[2][0] = 0
    fixtures.append(("missing_left_key", missing_left_key))

    ragged = [row[:] for row in base]
    ragged[-1].pop()
    fixtures.append(("ragged_grid", ragged))

    boolean_cell = [row[:] for row in base]
    boolean_cell[1][1] = True
    fixtures.append(("boolean_cell", boolean_cell))

    return fixtures


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    row_pinned = overrides.get("row_perm") is not None
    col_pinned = overrides.get("col_perm") is not None
    if (
        row_pinned
        and col_pinned
        and overrides["row_perm"] == "identity"
        and overrides["col_perm"] == "identity"
    ):
        raise ValueError(
            "incompatible overrides: row_perm='identity' and col_perm='identity' "
            "would create a no-op lesson"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    _, default_n, default_row, default_col = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]

    # A single pinned identity axis must remain independently usable.  When its
    # scheduled unpinned partner is also identity, move only that unpinned
    # default; reject only the explicitly pinned identity+identity pair above.
    if row_pinned and overrides["row_perm"] == "identity" and not col_pinned:
        if default_col == "identity":
            default_col = "reverse"
    if col_pinned and overrides["col_perm"] == "identity" and not row_pinned:
        if default_row == "identity":
            default_row = "reverse"

    n = _scheduled_int(ctx, "n", 3, 5, default_n)
    row_kind = _scheduled_choice(ctx, "row_perm", PERM_KINDS, default_row)
    col_kind = _scheduled_choice(ctx, "col_perm", PERM_KINDS, default_col)
    if row_kind == "identity" and col_kind == "identity":
        raise ValueError("constructed no-op lesson: both key strips are already ordered")

    row_keys = _permutation(row_kind, n)
    col_keys = _permutation(col_kind, n)
    rng = ctx.draw_rng(f"body:{difficulty or 'default'}")
    body = _balanced_body(n, rng, row_keys, col_keys)
    grid = _build(n, row_keys, col_keys, body)

    errors = self_check(grid, meta={"overrides": overrides})
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
