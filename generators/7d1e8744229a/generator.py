"""Generate palette-recolored copies of the canonical 5x5 symbolic seed.

The input is not arbitrary texture.  It is the top-left 5x5 portion of the
fixed 10x10 symbolic output template, recolored by three distinct nonzero ARC
colors.  The Racket oracle reads the three role colors from (0,0), (0,1), and
(2,2), then recolors the complete 10x10 template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "7d1e8744229a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a51754da50c2"

SUMMARY = (
    "Interpret the canonical 5x5 seed as a three-symbol pattern.  The colors "
    "at (0,0), (0,1), and (2,2) are the three symbol roles; recolor the fixed "
    "10x10 symbolic template with those roles."
)

INVARIANTS = [
    "input is exactly 5x5",
    "exactly three pairwise-distinct nonzero ARC colors occur",
    "the normalized input equals the canonical 5x5 role template",
    "role 0 occupies the four corners, role 1 occupies sixteen cells, and role 2 occupies the centered five-cell plus",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "5",
        "valid": "5",
    },
    "template": {
        "type": "str",
        "default": "canonical",
        "valid": ["canonical"],
    },
    "palette_size": {
        "type": "int",
        "default": "3",
        "valid": "3",
    },
}

# Symbol 0 is the corner role, symbol 1 the surrounding body role, and symbol
# 2 the centered plus role.  This exact morphology is shared by every
# canonical train/test input; only the three role colors change.
INPUT_TEMPLATE = (
    (0, 1, 1, 1, 0),
    (1, 1, 2, 1, 1),
    (1, 2, 2, 2, 1),
    (1, 1, 2, 1, 1),
    (0, 1, 1, 1, 0),
)

OUTPUT_TEMPLATE = (
    (0, 1, 1, 1, 0, 0, 2, 1, 0, 2),
    (1, 1, 2, 1, 1, 0, 2, 1, 0, 2),
    (1, 2, 2, 2, 1, 0, 2, 1, 0, 2),
    (1, 1, 2, 1, 1, 0, 2, 1, 0, 2),
    (0, 1, 1, 1, 0, 0, 2, 1, 0, 2),
    (0, 0, 0, 0, 0, 2, 2, 1, 0, 2),
    (2, 2, 2, 2, 2, 2, 1, 1, 0, 2),
    (1, 1, 1, 1, 1, 1, 1, 0, 0, 2),
    (0, 0, 0, 0, 0, 0, 0, 0, 2, 2),
    (2, 2, 2, 2, 2, 2, 2, 2, 2, 1),
)

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _role_colors(grid) -> tuple[int, int, int] | None:
    if len(grid) < 3 or len(grid[0]) < 3:
        return None
    return grid[0][0], grid[0][1], grid[2][2]


def _normalize_with_roles(grid, roles: tuple[int, int, int]):
    mapping = {color: index for index, color in enumerate(roles)}
    if len(mapping) != 3:
        return None
    normalized = []
    for row in grid:
        normalized_row = []
        for value in row:
            if value not in mapping:
                return None
            normalized_row.append(mapping[value])
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject any scene outside the exact canonical symbolic-input grammar."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if (height, width) != (5, 5):
        return [f"expected exact 5x5 input, found {height}x{width}"]

    roles = _role_colors(grid)
    assert roles is not None
    if any(color == 0 for color in roles):
        errors.append(f"role colors must be nonzero, found {roles}")
    if len(set(roles)) != 3:
        errors.append(f"role colors must be pairwise distinct, found {roles}")
    if errors:
        return errors

    normalized = _normalize_with_roles(grid, roles)
    if normalized != INPUT_TEMPLATE:
        errors.append(
            "grid does not match the canonical 5x5 role template after anchor-color normalization"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical manifold is exactly the recolored 5x5 role template."""
    return self_check(grid)


def _witness_corner_role(grid) -> bool:
    if self_check(grid):
        return False
    role = grid[0][0]
    cells = {(row, col) for row in range(5) for col in range(5) if grid[row][col] == role}
    return cells == {(0, 0), (0, 4), (4, 0), (4, 4)}


def _witness_body_role(grid) -> bool:
    if self_check(grid):
        return False
    role = grid[0][1]
    return sum(value == role for row in grid for value in row) == 16


def _witness_center_plus_role(grid) -> bool:
    if self_check(grid):
        return False
    role = grid[2][2]
    cells = {(row, col) for row in range(5) for col in range(5) if grid[row][col] == role}
    return cells == {(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)}


SEMANTIC_WITNESSES = {
    "four_corner_role": _witness_corner_role,
    "sixteen_cell_body_role": _witness_body_role,
    "centered_five_cell_plus_role": _witness_center_plus_role,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that demos expose one shared symbolic expansion for the query.

    The oracle's anchor lookup and a whole-template interpretation are
    answer-equivalent on every lawful input.  That is an intentional exception,
    not ambiguity: malformed recombinations are rejected by the teaching
    grammar rather than presented as lessons.
    """
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the canonical teaching grammar")

    palettes = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = self_check(demo["input"])
        if input_errors:
            reasons.append(f"demo {index} input is outside the canonical teaching grammar")
            continue
        roles = _role_colors(demo["input"])
        assert roles is not None
        palettes.add(roles)
        normalized_output = _normalize_with_roles(demo["output"], roles)
        if normalized_output != OUTPUT_TEMPLATE:
            reasons.append(f"demo {index} output does not encode the fixed 10x10 role template")

    if len(palettes) < 2:
        reasons.append("demonstrations do not vary the role-color assignment")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    return {
        "grid_size": len(grid) if grid and len(grid) == len(grid[0]) else (len(grid), len(grid[0]) if grid else 0),
        "template": "canonical" if not self_check(grid) else "invalid",
        "palette_size": len({value for row in grid for value in row}),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic canonical-shaped input; Racket owns output."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_size = ctx.draw_int("grid_size", 5, 5)
    template = ctx.draw_choice("template", ("canonical",))
    palette_size = ctx.draw_int("palette_size", 3, 3)
    if grid_size != 5 or template != "canonical" or palette_size != 3:
        raise ValueError("only the exact canonical 5x5 three-role grammar is supported")

    if difficulty == "easy":
        pool = (1, 2, 3, 4, 5)
    elif difficulty == "medium":
        pool = (1, 2, 3, 4, 5, 6, 7)
    else:
        pool = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    role_a = ctx.draw_choice("role_a", pool)
    role_b = ctx.draw_choice("role_b", tuple(color for color in pool if color != role_a))
    role_c = ctx.draw_choice(
        "role_c",
        tuple(color for color in pool if color not in {role_a, role_b}),
    )
    palette = (role_a, role_b, role_c)
    grid = [
        [palette[symbol] for symbol in row]
        for row in INPUT_TEMPLATE
    ]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]
