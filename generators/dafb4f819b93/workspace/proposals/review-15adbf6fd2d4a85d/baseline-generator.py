"""Generator for training task a406ac07 / dafb4f819b93.

The right column assigns one color to every row and the bottom row assigns
one color to every column.  Both borders use the same ordered set of
distinct colors, but their run lengths may differ.  Every zero cell whose
row and column labels agree is filled with that shared color.

The four public scenes are all 10x10 and use four or five contiguous color
runs.  Two have matching border sequences and two have independently sized
row/column runs, so border asymmetry is answer-bearing rather than noise.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "dafb4f819b93"
VERSION = "3.0.0"
TASK_ID = "dafb4f819b93"
RULE_HASH = "6bb5aaacd2ec"

SUMMARY = (
    "An 8..14 square has contiguous color runs on its right and bottom "
    "borders. Their ordered colors agree while their run lengths may differ; "
    "fill an interior cell exactly when its row and column labels agree."
)

INVARIANTS = [
    "the grid is square with side length 8..14",
    "the interior is all background zero",
    "the right and bottom borders are entirely nonzero",
    "both borders contain the same ordered 4..6 distinct color runs",
    "matching and independently sized border partitions are both supported",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-aware rng 8..14",
        "valid": "8..14",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware rng 4..6",
        "valid": "4..6",
    },
    "border_relation": {
        "type": "str",
        "default": "rng matched|different",
        "valid": "matched|different",
    },
}

_VALID_N = (8, 14)
_VALID_COLORS = (4, 6)
_BORDER_RELATIONS = ("matched", "different")
_PROFILE_PRIOR = 0.08

# Exact right-column and bottom-row sequences for all public inputs.  There
# is no placement nuisance because the labels occupy fixed grid boundaries.
_PROFILE_SPECS = (
    (
        (5, 6, 6, 7, 7, 7, 8, 9, 9, 9),
        (5, 6, 6, 7, 7, 7, 8, 9, 9, 9),
    ),
    (
        (9, 9, 8, 8, 7, 7, 6, 6, 5, 5),
        (9, 9, 8, 8, 7, 7, 6, 6, 5, 5),
    ),
    (
        (8, 8, 8, 4, 4, 5, 5, 3, 3, 3),
        (8, 8, 4, 4, 4, 5, 5, 3, 3, 3),
    ),
    (
        (3, 3, 3, 4, 4, 6, 6, 9, 7, 7),
        (3, 3, 4, 6, 6, 6, 9, 9, 7, 7),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_n", "n_colors"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    relation = overrides.get("border_relation")
    if relation is not None and type(relation) is not str:
        raise ValueError("border_relation must be a string")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _runs(sequence):
    colors = []
    lengths = []
    for value in sequence:
        if not colors or colors[-1] != value:
            colors.append(value)
            lengths.append(1)
        else:
            lengths[-1] += 1
    return tuple(colors), tuple(lengths)


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    n = len(grid)
    right = tuple(row[-1] for row in grid) if grid else ()
    bottom = tuple(grid[-1]) if grid else ()
    right_colors, right_lengths = _runs(right)
    bottom_colors, bottom_lengths = _runs(bottom)
    return {
        "grid": grid,
        "n": n,
        "right": right,
        "bottom": bottom,
        "right_colors": right_colors,
        "bottom_colors": bottom_colors,
        "right_lengths": right_lengths,
        "bottom_lengths": bottom_lengths,
        "n_colors": len(right_colors),
        "border_relation": (
            "matched" if right == bottom else "different"
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]
    n = len(coerced)
    if width != n:
        errors.append("grid must be square")
    if not (_VALID_N[0] <= n <= _VALID_N[1]):
        errors.append("grid side length must be in 8..14")
    if any(
        type(value) is not int or not (0 <= value <= 9)
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
    if width != n:
        return errors
    if any(
        coerced[r][c] != 0
        for r in range(n - 1)
        for c in range(n - 1)
    ):
        errors.append("all non-border cells must be background zero")
    right = tuple(coerced[r][-1] for r in range(n))
    bottom = tuple(coerced[-1])
    if any(value == 0 for value in right + bottom):
        errors.append("right and bottom borders must be entirely nonzero")
    right_colors, _ = _runs(right)
    bottom_colors, _ = _runs(bottom)
    if right_colors != bottom_colors:
        errors.append("both borders must use the same ordered color runs")
    if (
        len(set(right_colors)) != len(right_colors)
        or len(set(bottom_colors)) != len(bottom_colors)
    ):
        errors.append("each border color must occupy exactly one contiguous run")
    if not (_VALID_COLORS[0] <= len(right_colors) <= _VALID_COLORS[1]):
        errors.append("borders must contain 4..6 distinct color runs")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_n": scene["n"],
        "n_colors": scene["n_colors"],
        "border_relation": scene["border_relation"],
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    source = scene["grid"]
    right = scene["right"]
    bottom = scene["bottom"]
    n = scene["n"]
    return [
        [
            source[r][c]
            if source[r][c] != 0
            else right[r]
            if right[r] == bottom[c]
            else 0
            for c in range(n)
        ]
        for r in range(n)
    ]


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return scene["n"], scene["right"], scene["bottom"]


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    (len(right), tuple(right), tuple(bottom))
    for right, bottom in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _paint_scene(right, bottom):
    if len(right) != len(bottom):
        raise ValueError("right and bottom border lengths must agree")
    n = len(right)
    if right[-1] != bottom[-1]:
        raise ValueError("bottom-right border labels must agree")
    grid = full_grid(n, n, 0)
    for r, value in enumerate(right):
        grid[r][-1] = value
    for c, value in enumerate(bottom):
        grid[-1][c] = value
    return grid


def _composition(total, parts, rng):
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    points = (0, *cuts, total)
    return tuple(
        points[index + 1] - points[index]
        for index in range(parts)
    )


def _different_composition(total, original, rng):
    for _ in range(32):
        candidate = _composition(total, len(original), rng)
        if candidate != original:
            return candidate
    adjusted = list(original)
    donor = next(index for index, value in enumerate(adjusted) if value > 1)
    receiver = (donor + 1) % len(adjusted)
    adjusted[donor] -= 1
    adjusted[receiver] += 1
    return tuple(adjusted)


def _expand(colors, lengths):
    sequence = []
    for color, length in zip(colors, lengths):
        sequence.extend([color] * length)
    return tuple(sequence)


def _draw_general(n, n_colors, relation, rng):
    colors = tuple(rng.sample(range(1, 10), n_colors))
    right_lengths = _composition(n, n_colors, rng)
    if relation == "matched":
        bottom_lengths = right_lengths
    else:
        bottom_lengths = _different_composition(n, right_lengths, rng)
    return _paint_scene(
        _expand(colors, right_lengths),
        _expand(colors, bottom_lengths),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        right, bottom = profile
        colors, _ = _runs(right)
        relation = "matched" if right == bottom else "different"
        ctx.draw_int("grid_n", len(right), len(right))
        ctx.draw_int("n_colors", len(colors), len(colors))
        ctx.draw_choice("border_relation", (relation,))
        grid = _paint_scene(right, bottom)
    else:
        if overrides.get("grid_n") is not None:
            n = ctx.draw_int("grid_n", *_VALID_N)
        else:
            n = ctx.draw_int(
                "grid_n",
                *{
                    "easy": (8, 10),
                    "medium": (9, 12),
                    "hard": (11, 14),
                }[band],
            )
        if overrides.get("n_colors") is not None:
            n_colors = ctx.draw_int("n_colors", *_VALID_COLORS)
        else:
            n_colors = ctx.draw_int(
                "n_colors",
                *{
                    "easy": (4, 4),
                    "medium": (4, 5),
                    "hard": (5, 6),
                }[band],
            )
        relation = ctx.draw_choice(
            "border_relation",
            _BORDER_RELATIONS,
        )
        grid = _draw_general(
            n,
            n_colors,
            relation,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
