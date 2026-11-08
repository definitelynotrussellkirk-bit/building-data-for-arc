"""Generator for ARC task 67a3c6ac.

The canonical operation is a horizontal reflection: reverse every row while
preserving row order.  The generator deliberately emits multicolor scenes on
which that operation is visible and distinguishable from the other elementary
D4 transforms.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c690e739e0ce"
VERSION = "3.0.0"
TASK_ID = "c690e739e0ce"
RULE_HASH = "04808a5aa3d1"

SUMMARY = (
    "A 3..20 by 3..20 grid uses exactly 2..6 colors. Reverse every row "
    "left-to-right while keeping the row order unchanged. Normal lessons "
    "contain at least two asymmetric rows and are rejected when identity, "
    "vertical reflection, rotation, or transpose would give the same answer."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is a rectangular 3..20 by 3..20 ARC grid",
    "input uses exactly 2..6 distinct colors",
    "at least two rows contain a mismatched left/right cell pair",
    "at least two colors participate in left/right mismatches",
    "flip-lr is visible and has a unique answer among elementary D4 transforms",
]

TEXTURES = (
    "noise",
    "row_bands",
    "column_bands",
    "checker",
    "frame_noise",
    "mixed_palindrome",
)
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 3|4|6|7 in easy; difficulty-aware otherwise",
        "valid": "3..20",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 3|4|6|7 in easy; difficulty-aware otherwise",
        "valid": "3..20",
    },
    "palette_size": {
        "type": "int",
        "default": "4 in easy; difficulty-aware 3..6 otherwise",
        "valid": "2..6",
    },
    "texture": {
        "type": "str",
        "default": "keyed random structural texture",
        "valid": "|".join(TEXTURES),
    },
}

_CANONICAL_PROFILES = {(3, 3, 4), (4, 4, 4), (6, 6, 4), (7, 7, 4)}
_BAND_DIMENSIONS = {
    "easy": (3, 4, 6, 7),
    "medium": tuple(range(5, 15)),
    "hard": tuple(range(10, 21)),
}
_BAND_PALETTES = {
    "easy": (4,),
    "medium": (3, 4, 5),
    "hard": (4, 5, 6),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lower, upper in (
        ("grid_h", 3, 20),
        ("grid_w", 3, 20),
        ("palette_size", 2, 6),
    ):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")
    texture = overrides.get("texture")
    if texture is not None and texture not in TEXTURES:
        raise ValueError(f"texture must be one of {TEXTURES}, got {texture!r}")
    return difficulty or "medium"


def _draw_choice_axis(ctx, name: str, default_options: tuple[Any, ...], overrides):
    """Consume an exact override while keeping default difficulty narrowing."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, [overrides[name]])
    return ctx.draw_choice(name, list(default_options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic teaching input; Racket remains output authority."""
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Easy ordinary draws are exact canonical shape/palette profiles.  The
    # per-axis singleton draws preserve contract-v6 keyed provenance.
    if band == "easy" and "grid_h" not in overrides and "grid_w" not in overrides:
        canonical_size = ctx.draw_choice("canonical_profile_size", [3, 4, 6, 7])
        height = ctx.draw_choice("grid_h", [canonical_size])
        width = ctx.draw_choice("grid_w", [canonical_size])
    else:
        height = _draw_choice_axis(ctx, "grid_h", _BAND_DIMENSIONS[band], overrides)
        width = _draw_choice_axis(ctx, "grid_w", _BAND_DIMENSIONS[band], overrides)

    palette_size = _draw_choice_axis(
        ctx, "palette_size", _BAND_PALETTES[band], overrides
    )
    texture = _draw_choice_axis(ctx, "texture", TEXTURES, overrides)
    palette = list(ctx.draw_distinct_colors("palette", n=palette_size))

    for attempt in range(128):
        rng = ctx.draw_rng(f"cells:{texture}:{attempt}")
        grid = _make_texture(texture, height, width, palette, rng)
        forbidden_rows: set[int] = set()
        if texture == "mixed_palindrome":
            palindrome_row = rng.randrange(height)
            forbidden_rows.add(palindrome_row)
            _make_row_palindromic(grid, palindrome_row)
        _ensure_palette_coverage(grid, palette, rng, forbidden_rows=forbidden_rows)
        if texture == "mixed_palindrome":
            _make_row_palindromic(grid, palindrome_row)
        if not self_check(grid):
            return grid
    # Extremely small/two-color combinations can make a decorative texture
    # overconstrained (notably a 3x3 frame).  Boundary overrides are globally
    # valid, so finish with a deterministic constructive witness instead of
    # rejecting a declared-valid request.
    fallback = _constructive_fallback(height, width, palette)
    errors = self_check(fallback)
    if errors:  # Defensive: the construction is exhaustively tested below.
        raise AssertionError("constructive fallback invalid: " + "; ".join(errors))
    return fallback


def _constructive_fallback(h: int, w: int, palette: list[int]):
    """Build a guaranteed-visible left-edge code for every legal profile."""
    grid = full_grid(h, w, palette[0])
    grid[0][0] = palette[1]
    grid[1][0] = palette[1]
    candidates = [
        (row, col)
        for col in range((w + 1) // 2)
        for row in range(h)
        if (row, col) not in {(0, 0), (1, 0)}
    ]
    for color, (row, col) in zip(palette[2:], candidates):
        grid[row][col] = color
    return grid


def _make_texture(texture: str, h: int, w: int, palette: list[int], rng):
    if texture == "noise":
        return [[rng.choice(palette) for _ in range(w)] for _ in range(h)]
    if texture == "row_bands":
        grid = full_grid(h, w, palette[0])
        for row in range(h):
            base = palette[row % len(palette)]
            for col in range(w):
                grid[row][col] = base if rng.random() < 0.72 else rng.choice(palette)
        return grid
    if texture == "column_bands":
        grid = full_grid(h, w, palette[0])
        for row in range(h):
            for col in range(w):
                base = palette[col % len(palette)]
                grid[row][col] = base if rng.random() < 0.78 else rng.choice(palette)
        return grid
    if texture == "checker":
        grid = [
            [palette[(row + col) % len(palette)] for col in range(w)]
            for row in range(h)
        ]
        perturbations = max(2, (h * w) // 8)
        for _ in range(perturbations):
            row, col = rng.randrange(h), rng.randrange(w)
            grid[row][col] = rng.choice(palette)
        return grid
    if texture == "frame_noise":
        grid = full_grid(h, w, palette[0])
        for row in range(h):
            for col in range(w):
                if row in (0, h - 1) or col in (0, w - 1):
                    grid[row][col] = palette[1]
                else:
                    grid[row][col] = rng.choice(palette)
        return grid
    if texture == "mixed_palindrome":
        return [[rng.choice(palette) for _ in range(w)] for _ in range(h)]
    raise ValueError(f"unknown texture {texture!r}")


def _ensure_palette_coverage(
    grid: list[list[int]],
    palette: list[int],
    rng,
    *,
    forbidden_rows: set[int] | None = None,
) -> None:
    forbidden_rows = forbidden_rows or set()
    positions = [
        (row, col)
        for row in range(len(grid))
        if row not in forbidden_rows
        for col in range(len(grid[0]))
    ]
    if len(positions) < len(palette):
        raise ValueError("grid is too small to realize the requested palette")
    rng.shuffle(positions)
    for color, (row, col) in zip(palette, positions):
        grid[row][col] = color


def _make_row_palindromic(grid: list[list[int]], row: int) -> None:
    width = len(grid[0])
    for col in range(width // 2):
        grid[row][width - 1 - col] = grid[row][col]


def _coerce_grid(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, (list, tuple)):
        return []
    result: list[list[Any]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            return []
        result.append(list(row))
    return result


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return grid[::-1]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot270(grid):
    return [list(row) for row in zip(*grid)][::-1]


_TRANSFORMS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": lambda grid: [row[:] for row in grid],
    "flip_lr": _flip_lr,
    "flip_ud": _flip_ud,
    "rot180": _rot180,
    "transpose": _transpose,
    "rot90": _rot90,
    "rot270": _rot270,
}


def _analysis(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or any(
        not isinstance(row, (list, tuple)) for row in grid
    ):
        return {"errors": ["grid must use literal row lists"]}
    values = _coerce_grid(grid)
    errors: list[str] = []
    if not values or not values[0]:
        return {"errors": ["grid must be a nonempty rectangle"]}
    width = len(values[0])
    if any(not row or len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}

    height = len(values)
    if not 3 <= height <= 20:
        errors.append(f"height must be in 3..20, got {height}")
    if not 3 <= width <= 20:
        errors.append(f"width must be in 3..20, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values
        for value in row
    ):
        errors.append("all cells must be literal integer ARC colors 0..9")

    colors = {value for row in values for value in row if type(value) is int}
    if not 2 <= len(colors) <= 6:
        errors.append(f"grid must use exactly 2..6 colors, got {len(colors)}")

    asymmetric_rows = [
        row_index
        for row_index, row in enumerate(values)
        if row != row[::-1]
    ]
    mismatched_pairs = []
    mismatch_colors: set[int] = set()
    for row_index, row in enumerate(values):
        for col in range(width // 2):
            mirror_col = width - 1 - col
            if row[col] != row[mirror_col]:
                mismatched_pairs.append((row_index, col, mirror_col))
                if type(row[col]) is int:
                    mismatch_colors.add(row[col])
                if type(row[mirror_col]) is int:
                    mismatch_colors.add(row[mirror_col])
    if len(asymmetric_rows) < 2:
        errors.append("at least two rows must visibly change under flip-lr")
    if len(mismatched_pairs) < 2:
        errors.append("at least two mirrored cell pairs must differ")
    if len(mismatch_colors) < 2:
        errors.append("at least two colors must participate in left/right mismatches")

    target = _flip_lr(values)
    competing_matches = [
        name
        for name, transform in _TRANSFORMS.items()
        if name != "flip_lr" and transform(values) == target
    ]
    if competing_matches:
        errors.append(
            "flip-lr answer is ambiguous with " + ", ".join(competing_matches)
        )

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "palette_size": len(colors),
        "colors": tuple(sorted(colors)),
        "asymmetric_rows": tuple(asymmetric_rows),
        "palindromic_rows": tuple(
            row_index
            for row_index, row in enumerate(values)
            if row == row[::-1]
        ),
        "mismatched_pair_count": len(mismatched_pairs),
        "mismatch_color_count": len(mismatch_colors),
        "competing_matches": tuple(competing_matches),
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact pixel-observable axis from the returned grid."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["height"]),
        "grid_w": int(facts["width"]),
        "palette_size": int(facts["palette_size"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, rule-hiding, or exact-override-drifting scenes."""
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if requested:
        observed = observe_overrides(grid)
        for axis in ("grid_h", "grid_w", "palette_size"):
            if axis in requested and observed.get(axis) != requested[axis]:
                errors.append(
                    f"override {axis} requested {requested[axis]!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors


def profile_signature(grid) -> dict[str, Any]:
    """Task-linked structural facts used by count-backed review censuses."""
    facts = _analysis(grid)
    return {"valid": not facts["errors"], **facts}


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical four-color square profiles and their semantics."""
    facts = _analysis(grid)
    if facts["errors"]:
        return list(facts["errors"])
    profile = (facts["height"], facts["width"], facts["palette_size"])
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}"]
    return []


MIN_STRICT_FRAC = 0.30


def _witness_odd_width(grid) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and facts["width"] % 2 == 1


def _witness_even_width(grid) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and facts["width"] % 2 == 0


def _witness_mixed_rows(grid) -> bool:
    facts = _analysis(grid)
    return (
        not facts["errors"]
        and bool(facts["palindromic_rows"])
        and bool(facts["asymmetric_rows"])
    )


def _witness_all_rows_change(grid) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and not facts["palindromic_rows"]


def _witness_four_plus_colors(grid) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and facts["palette_size"] >= 4


SEMANTIC_WITNESSES = {
    "odd_width_fixed_center_column": _witness_odd_width,
    "even_width_full_column_swap": _witness_even_width,
    "mixed_palindromic_and_asymmetric_rows": _witness_mixed_rows,
    "all_rows_change": _witness_all_rows_change,
    "four_or_more_colors": _witness_four_plus_colors,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require D4-consistent demos to determine one exact query answer."""
    if not isinstance(demos, list) or not demos:
        return ["lesson needs at least one demonstration"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    candidates = []
    for name, transform in _TRANSFORMS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and transform(_coerce_grid(pair["input"])) == _coerce_grid(pair["output"])
            for pair in demos
        ):
            candidates.append(name)
    if not candidates:
        return ["no elementary D4 transform matches every demonstration"]
    if "flip_lr" not in candidates:
        return [f"demonstrations select {candidates}, not flip_lr"]

    query_grid = _coerce_grid(query["input"])
    answer_groups: dict[str, list[str]] = {}
    for name in candidates:
        answer = _TRANSFORMS[name](query_grid)
        key = repr(answer)
        answer_groups.setdefault(key, []).append(name)
    if len(answer_groups) != 1:
        detail = "; ".join(
            f"{names}" for names in answer_groups.values()
        )
        return [f"competing demo-consistent transforms disagree on query: {detail}"]
    return []


def rule_mirror(grid) -> list[list[int]]:
    """Exact Python test mirror only; the Racket program is output authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid lesson input: " + "; ".join(facts["errors"]))
    return _flip_lr(facts["grid"])
