"""Generator for H106 — infer a D4 panel transform and apply it to a query.

The input is an ``s x (3s+2)`` grid.  Two full color-5 columns separate
three square panels.  Panel B is panel A under one of the eight D4 transforms;
the answer is panel C under that same transform.

Ordinary draws schedule every transform branch, retain a canonical 5x17
component in every difficulty band, and use connected monochrome motifs with
full eight-image D4 orbits.  Thus A->B identifies one transform and C separates
all transform outputs.  The three advertised axes are exact and recoverable
from the returned pixels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e078230e5469"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "b95936763d1c"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read three equal square panels separated by full color-5 columns. Infer "
    "the D4 transform mapping panel A to panel B, then apply it to panel C. "
    "Ordinary lessons cover all eight transforms with connected asymmetric "
    "motifs and preserve a recurring canonical 5x17 profile."
)

INVARIANTS = [
    "background is 0 and both separator columns are solid color 5",
    "the input contains three equal square panels with side 3..6",
    "A and B are nonempty monochrome panels in the same color",
    "C is nonempty, monochrome, and uses a different color",
    "ordinary A uniquely identifies one D4 transform and ordinary C separates all eight",
]

ALL_TRANSFORMS = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip_h",
    "flip_v",
    "transpose",
    "anti",
)
# The Racket authority tries non-identity branches first and identity last.
_RULE_PRIORITY = (
    "rot90",
    "rot180",
    "rot270",
    "flip_h",
    "flip_v",
    "transpose",
    "anti",
    "id",
)
PALETTE_KINDS = ("default", "warm", "cool", "varied")
SCHEDULE_PROFILES = ALL_TRANSFORMS

AXES = {
    "square_size": {
        "type": "int",
        "default": "difficulty-aware 3..6 with a recurring canonical-size anchor",
        "valid": "3..6",
    },
    "transform": {
        "type": "str",
        "default": "eight-example schedule",
        "valid": "id|rot90|rot180|rot270|flip_h|flip_v|transpose|anti",
    },
    "palette_kind": {
        "type": "str",
        "default": "four-example schedule",
        "valid": "default|warm|cool|varied",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_SEPARATOR_COLOR = 5
_WARM_COLORS = (2, 4, 7, 9)
_COOL_COLORS = (1, 3, 6, 8)
_OBSERVED_CANONICAL_FAMILY = ("rot90", "flip_v", "transpose")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"]
    return []


def _transform(panel, name):
    """Return a fresh square panel under the named D4 transform."""
    if name == "id":
        return [list(row) for row in panel]
    if name == "rot90":
        return [list(row) for row in zip(*panel[::-1])]
    if name == "rot180":
        return [list(reversed(row)) for row in reversed(panel)]
    if name == "rot270":
        return [list(row) for row in zip(*panel)][::-1]
    if name == "flip_h":
        return [list(reversed(row)) for row in panel]
    if name == "flip_v":
        return [list(row) for row in reversed(panel)]
    if name == "transpose":
        return [list(row) for row in zip(*panel)]
    if name == "anti":
        return _transform(_transform(panel, "transpose"), "rot180")
    raise ValueError(f"unknown transform: {name!r}")


# Keep the historical helper name for source-bound reproducers.
def _apply(name, grid):
    return _transform(grid, name)


def _panels(grid):
    n = len(grid)
    return (
        [list(row[:n]) for row in grid],
        [list(row[n + 1:2 * n + 1]) for row in grid],
        [list(row[2 * n + 2:3 * n + 2]) for row in grid],
    )


def _support(panel):
    return frozenset(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    )


def _panel_colors(panel):
    return {value for row in panel for value in row if value != 0}


def _is_connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = set(pending)
    while pending:
        r, c = pending.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _matching_transforms(panel_a, panel_b):
    target = _freeze(panel_b)
    return [name for name in _RULE_PRIORITY if _freeze(_transform(panel_a, name)) == target]


def _infer_transform(grid):
    panel_a, panel_b, _ = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if not matches:
        raise ValueError("no D4 transform maps panel A to panel B")
    return matches[0]


def _apply_rule(grid):
    """Pure Python mirror for tests and semantic checks; Racket is authoritative."""
    _, _, panel_c = _panels(grid)
    return _transform(panel_c, _infer_transform(grid))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible three-panel input grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    n = len(grid)
    width = len(grid[0])
    if not 3 <= n <= 6:
        errors.append(f"square side must be in 3..6, got {n}")
    if width != 3 * n + 2:
        errors.append(f"expected n x (3n+2) grid, got {n}x{width}")
        return errors

    for column in (n, 2 * n + 1):
        bad_rows = [r for r in range(n) if grid[r][column] != _SEPARATOR_COLOR]
        if bad_rows:
            errors.append(
                f"column {column} must be full color-{_SEPARATOR_COLOR}; "
                f"bad rows {bad_rows[:3]}"
            )

    panel_a, panel_b, panel_c = _panels(grid)
    for label, panel in zip("ABC", (panel_a, panel_b, panel_c)):
        if any(value == _SEPARATOR_COLOR for row in panel for value in row):
            errors.append(f"panel {label} contains reserved separator color {_SEPARATOR_COLOR}")
        colors = _panel_colors(panel)
        if not colors:
            errors.append(f"panel {label} must contain a nonzero motif")
        elif len(colors) != 1:
            errors.append(f"panel {label} must be monochrome, found {sorted(colors)}")

    if errors:
        return errors

    color_a = next(iter(_panel_colors(panel_a)))
    color_b = next(iter(_panel_colors(panel_b)))
    color_c = next(iter(_panel_colors(panel_c)))
    if color_a != color_b:
        errors.append(f"panels A and B must share one color, got {color_a} and {color_b}")
    if color_c == color_a:
        errors.append("panel C must use a color distinct from panels A/B")
    if not _matching_transforms(panel_a, panel_b):
        errors.append("no D4 transform maps panel A to panel B")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the connected sparse morphology shared by canonical and generated rows."""
    errors = self_check(grid)
    if errors:
        return errors

    palette = {value for row in grid for value in row}
    if len(palette) != 4:
        errors.append(f"profile requires exactly four colors, found {sorted(palette)}")

    for label, panel in zip("ABC", _panels(grid)):
        cells = _support(panel)
        if not 3 <= len(cells) <= 7:
            errors.append(f"panel {label} must contain 3..7 motif cells, found {len(cells)}")
        if not _is_connected(cells):
            errors.append(f"panel {label} motif must be 4-connected")
    return errors


def _full_d4_orbit(panel) -> bool:
    return len({_freeze(_transform(panel, name)) for name in ALL_TRANSFORMS}) == 8


def _teaching_reasons(grid) -> list[str]:
    reasons = strict_canonical_like(grid)
    if reasons:
        return reasons
    panel_a, panel_b, panel_c = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1:
        reasons.append(f"A->B transform must be unique, got {matches}")
    if not _full_d4_orbit(panel_a):
        reasons.append("panel A must have a full eight-image D4 orbit")
    if not _full_d4_orbit(panel_c):
        reasons.append("panel C must have a full eight-image D4 orbit")
    return reasons


def _paint_panel(cells, size: int, color: int):
    panel = full_grid(size, size, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel


def _grow_connected_support(rng, size: int, cell_count: int):
    cells = {(rng.randrange(size), rng.randrange(size))}
    while len(cells) < cell_count:
        frontier = set()
        for r, c in cells:
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (0 <= neighbor[0] < size and 0 <= neighbor[1] < size
                        and neighbor not in cells):
                    frontier.add(neighbor)
        if not frontier:
            raise RuntimeError("connected motif growth exhausted its frontier")
        cells.add(rng.choice(sorted(frontier)))
    return frozenset(cells)


def _sample_asymmetric_support(rng, size: int, cell_count: int):
    for _ in range(512):
        cells = _grow_connected_support(rng, size, cell_count)
        panel = _paint_panel(cells, size, 1)
        if _full_d4_orbit(panel):
            return cells
    raise RuntimeError(
        f"could not sample connected D4-asymmetric {size}x{size} motif "
        f"with {cell_count} cells"
    )


def _paste_panel(grid, panel, left: int) -> None:
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            grid[r][left + c] = value


def schedule_profile(seed, sample_index, difficulty=None):
    """Every sliding eight-example window contains every transform once."""
    del difficulty
    return ALL_TRANSFORMS[(int(seed) + int(sample_index)) % len(ALL_TRANSFORMS)]


def _scheduled_size(seed, sample_index, difficulty):
    residue = (int(seed) + int(sample_index)) % 4
    if residue == 0:
        return 5
    if difficulty == "easy":
        return (3, 4, 3)[residue - 1]
    if difficulty == "hard":
        return (6, 5, 6)[residue - 1]
    return (3, 4, 6)[residue - 1]


def _draw_square_size(ctx, overrides, seed, sample_index, difficulty):
    if "square_size" in overrides:
        return ctx.draw_int_strict("square_size", 3, 6)
    scheduled = _scheduled_size(seed, sample_index, difficulty)
    return ctx.draw_choice("square_size", (scheduled,))


def _draw_palette(ctx, palette_kind):
    rng = ctx.draw_rng("palette_colors")
    if palette_kind == "warm":
        return tuple(rng.sample(list(_WARM_COLORS), 2))
    if palette_kind == "cool":
        return tuple(rng.sample(list(_COOL_COLORS), 2))
    if palette_kind == "default":
        return rng.choice(_COOL_COLORS), rng.choice(_WARM_COLORS)
    if palette_kind == "varied":
        return rng.choice(_WARM_COLORS), rng.choice(_COOL_COLORS)
    raise ValueError(f"unknown palette kind: {palette_kind!r}")


def _cell_count(rng, size: int, difficulty):
    if difficulty == "easy":
        lo, hi = 3, 4
    elif difficulty == "hard":
        lo, hi = 5, 7
    else:
        lo, hi = 4, 6
    hi = min(hi, size * size - 2, 7)
    lo = min(lo, hi)
    return rng.randint(lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic transform-identifying analogy input."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None:
        if type(difficulty) is not str or difficulty not in ("easy", "medium", "hard"):
            raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size = _draw_square_size(ctx, overrides, seed, sample_index, difficulty)

    scheduled_transform = schedule_profile(seed, sample_index, difficulty)
    if "transform" in overrides:
        transform = ctx.draw_choice("transform", ALL_TRANSFORMS)
    else:
        transform = ctx.draw_choice("transform", (scheduled_transform,))

    scheduled_palette = PALETTE_KINDS[(int(seed) + int(sample_index)) % len(PALETTE_KINDS)]
    if "palette_kind" in overrides:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        palette_kind = ctx.draw_choice("palette_kind", (scheduled_palette,))
    exemplar_color, query_color = _draw_palette(ctx, palette_kind)

    exemplar_rng = ctx.draw_rng("exemplar_support")
    query_rng = ctx.draw_rng("query_support")
    exemplar_count = _cell_count(exemplar_rng, size, difficulty)
    query_count = _cell_count(query_rng, size, difficulty)
    exemplar_support = _sample_asymmetric_support(exemplar_rng, size, exemplar_count)
    query_support = _sample_asymmetric_support(query_rng, size, query_count)

    panel_a = _paint_panel(exemplar_support, size, exemplar_color)
    panel_b = _transform(panel_a, transform)
    panel_c = _paint_panel(query_support, size, query_color)

    grid = full_grid(size, 3 * size + 2, 0)
    for r in range(size):
        grid[r][size] = _SEPARATOR_COLOR
        grid[r][2 * size + 1] = _SEPARATOR_COLOR
    _paste_panel(grid, panel_a, 0)
    _paste_panel(grid, panel_b, size + 1)
    _paste_panel(grid, panel_c, 2 * size + 2)
    return grid


def _palette_kind_from_colors(exemplar_color, query_color):
    exemplar_warm = exemplar_color in _WARM_COLORS
    query_warm = query_color in _WARM_COLORS
    if not exemplar_warm and query_warm:
        return "default"
    if exemplar_warm and query_warm:
        return "warm"
    if not exemplar_warm and not query_warm:
        return "cool"
    return "varied"


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    panel_a, _, panel_c = _panels(grid)
    exemplar_color = next(iter(_panel_colors(panel_a)))
    query_color = next(iter(_panel_colors(panel_c)))
    return {
        "square_size": len(grid),
        "transform": _infer_transform(grid),
        "palette_kind": _palette_kind_from_colors(exemplar_color, query_color),
    }


def _rival_fixed(name):
    def rival(grid):
        return _transform(_panels(grid)[2], name)
    return rival


def _rival_copy_panel_b(grid):
    return [list(row) for row in _panels(grid)[1]]


def _rival_observed_transform_family_only(grid):
    panel_a, panel_b, panel_c = _panels(grid)
    target = _freeze(panel_b)
    for name in _OBSERVED_CANONICAL_FAMILY:
        if _freeze(_transform(panel_a, name)) == target:
            return _transform(panel_c, name)
    return _transform(panel_c, "id")


def _transform_witness(expected):
    def witness(grid):
        return not _teaching_reasons(grid) and _infer_transform(grid) == expected
    return witness


def _safe_name(name: str) -> str:
    return name.replace("-", "_")


SEMANTIC_RIVALS = {
    f"fixed_{_safe_name(name)}": _rival_fixed(name)
    for name in ALL_TRANSFORMS
}
SEMANTIC_RIVALS.update({
    "copy_panel_b": _rival_copy_panel_b,
    "observed_transform_family_only": _rival_observed_transform_family_only,
})

SEMANTIC_WITNESSES = {
    f"transform_{_safe_name(name)}_unique": _transform_witness(name)
    for name in ALL_TRANSFORMS
}

WITNESS_RIVALS = {}
for name in ALL_TRANSFORMS:
    witness_name = f"transform_{_safe_name(name)}_unique"
    rivals = [
        f"fixed_{_safe_name(other)}"
        for other in ALL_TRANSFORMS
        if other != name
    ]
    rivals.append("copy_panel_b")
    if name not in _OBSERVED_CANONICAL_FAMILY and name != "id":
        rivals.append("observed_transform_family_only")
    WITNESS_RIVALS[witness_name] = rivals

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "observed_transform_family_only": _rival_observed_transform_family_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a serializable lesson that refutes every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    profiles = set()
    survivors = set(LESSON_COMPETITORS)

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        teaching_errors = _teaching_reasons(grid)
        if teaching_errors:
            errors.append(f"demo {index} is outside the teaching grammar: {teaching_errors[0]}")
            continue
        authoritative = _apply_rule(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        profiles.add(_infer_transform(grid))
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    if len(profiles) < 2:
        errors.append("demonstrations need at least two distinct transform branches")

    query_grid = query["input"]
    query_errors = _teaching_reasons(query_grid)
    if query_errors:
        errors.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif "output" in query and query["output"] != _apply_rule(query_grid):
        errors.append("query output disagrees with the selected rule")

    if survivors:
        errors.append("demonstrations leave rival rule(s) alive: " + ", ".join(sorted(survivors)))
    return errors
