"""Generator for ARC task ``62b1bc3c7907`` — Ferrers diagram from headers.

The input is an empty interior with two mutually-consistent numeric headers:
column 0 gives the left-aligned row widths and row 0 gives the corresponding
column heights.  The output drops both headers and paints the unique Ferrers
diagram green(3) on black(0).
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations_with_replacement
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "62b1bc3c7907"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "0d90669b637e"

SUMMARY = (
    "Read the left header as nonincreasing row widths and the top header as "
    "their matching column heights. Drop both headers and fill the unique "
    "left-aligned Ferrers diagram with green(3); the input interior is blank."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the top-left corner is 0 and every non-header input cell is 0",
    "column-0 row widths are nonincreasing and lie in 0..w-1",
    "row-0 column heights are exactly the conjugate counts of those row widths",
    "normal generated lessons are nondegenerate: first row is full, last row has width 1, and at least three row widths occur",
]

COUNTER_HYPOTHESES = [
    "right-align each bar instead of left-aligning it",
    "draw one green cell for every nonzero row header",
    "color each bar with its numeric row-header value instead of green(3)",
    "mistake the top-header heights for row widths",
    "emit a fixed-size output independent of the input dimensions",
]

# One exact caller-visible control is enough for this task.  Each profile has a
# unique observable input shape.  The profile schedule keeps canonical-scale
# anchors in every difficulty band while larger profiles add lawful variation.
_PROFILE_SHAPES = {
    "5x5_anchor": (5, 5),
    "5x6_anchor": (5, 6),
    "6x7_anchor": (6, 7),
    "6x6_partition": (6, 6),
    "7x7_partition": (7, 7),
    "7x8_partition": (7, 8),
    "8x9_partition": (8, 9),
    "9x9_partition": (9, 9),
}
SCENE_PROFILES = tuple(_PROFILE_SHAPES)
_PROFILE_BY_SHAPE = {shape: name for name, shape in _PROFILE_SHAPES.items()}
_ANCHOR_PROFILES = {"5x5_anchor", "5x6_anchor", "6x7_anchor"}
_PROFILES_BY_BAND = {
    "easy": ("5x5_anchor", "5x6_anchor", "6x7_anchor", "6x6_partition"),
    "medium": ("5x6_anchor", "6x7_anchor", "7x7_partition", "7x8_partition"),
    "hard": ("6x7_anchor", "5x5_anchor", "8x9_partition", "9x9_partition"),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic difficulty/sample-index curriculum",
        "valid": "5x5_anchor|5x6_anchor|6x7_anchor|6x6_partition|7x7_partition|7x8_partition|8x9_partition|9x9_partition",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot for a sequential lesson."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _column_heights(row_widths: Sequence[int], ncols: int) -> tuple[int, ...]:
    return tuple(sum(width > c for width in row_widths) for c in range(ncols))


def _top_as_row_widths(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Named wrong rule: misread top column-heights as row widths."""
    h, w = len(grid), len(grid[0])
    top = list(grid[0][1:])
    out = full_grid(h - 1, w - 1, 0)
    for r in range(h - 1):
        width = top[r] if r < len(top) else 0
        for c in range(min(width, w - 1)):
            out[r][c] = 3
    return out


@lru_cache(maxsize=None)
def _partition_candidates(h: int, w: int, full_count_palette: bool) -> tuple[tuple[int, ...], ...]:
    """Enumerate small, nondegenerate Ferrers partitions for one profile.

    Anchor profiles additionally expose every numeric count in the canonical
    shape's palette, so the mechanical canonical-profile gate has exact support
    rather than merely a nearby size envelope.
    """
    nrows, ncols = h - 1, w - 1
    candidates: list[tuple[int, ...]] = []
    for ascending in combinations_with_replacement(range(1, ncols + 1), nrows):
        rows = tuple(reversed(ascending))
        if rows[0] != ncols or rows[-1] != 1 or len(set(rows)) < 3:
            continue
        top = _column_heights(rows, ncols)
        if full_count_palette:
            expected = set(range(1, max(nrows, ncols) + 1))
            if set(rows) | set(top) != expected:
                continue
        # Keep a plausible wrong interpretation falsifiable even on square
        # profiles; otherwise a self-conjugate partition could make the top
        # header look like a second row-width list.
        wrong_widths = tuple(top[r] if r < len(top) else 0 for r in range(nrows))
        if wrong_widths == rows:
            continue
        candidates.append(rows)
    if not candidates:
        raise RuntimeError(f"no Ferrers candidates for profile {h}x{w}")
    return tuple(candidates)


def _build_grid(h: int, w: int, row_widths: Sequence[int]) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    top = _column_heights(row_widths, w - 1)
    for r, width in enumerate(row_widths, start=1):
        grid[r][0] = int(width)
    for c, height in enumerate(top, start=1):
        grid[0][c] = int(height)
    return grid


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
    h, w = len(grid), len(grid[0])
    if h < 2 or w < 2:
        errors.append(f"grid must have header plus interior, found {h}x{w}")
        return {"errors": errors, "height": h, "width": w}
    if grid[0][0] != 0:
        errors.append("top-left header corner must be 0")

    nonzero_body = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][c] != 0
    ]
    if nonzero_body:
        errors.append(f"input interior must be blank; found {len(nonzero_body)} nonzero cell(s)")

    row_widths = tuple(int(grid[r][0]) for r in range(1, h))
    top_heights = tuple(int(grid[0][c]) for c in range(1, w))
    if any(width > w - 1 for width in row_widths):
        errors.append(f"row header exceeds output width {w - 1}: {row_widths}")
    if any(height > h - 1 for height in top_heights):
        errors.append(f"column header exceeds output height {h - 1}: {top_heights}")
    if any(row_widths[i] < row_widths[i + 1] for i in range(len(row_widths) - 1)):
        errors.append(f"row headers must be nonincreasing: {row_widths}")

    if not any(row_widths):
        errors.append("Ferrers headers must describe at least one filled output cell")

    expected_top = _column_heights(row_widths, w - 1)
    if top_heights != expected_top:
        errors.append(
            f"top header must be conjugate to row widths: expected {expected_top}, got {top_heights}"
        )

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "row_widths": row_widths,
        "top_heights": top_heights,
        "scene_profile": _PROFILE_BY_SHAPE.get((h, w)),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept structurally valid Ferrers-header inputs and reject impostors."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = _meta_overrides(meta)
    for name, value in requested.items():
        if name in AXES and observe_overrides(grid).get(name) != value:
            errors.append(
                f"override {name}={value!r} realized as {observe_overrides(grid).get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked teaching grammar shared by canonical and generated scenes."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analysis(grid)
    rows = analysis["row_widths"]
    width = analysis["width"]
    if rows[0] != width - 1:
        reasons.append("first Ferrers row must span the full output width")
    if rows[-1] != 1:
        reasons.append("last Ferrers row must be a one-cell tail")
    if len(set(rows)) < 3:
        reasons.append("need at least three distinct row widths to expose the threshold rule")
    if rule_mirror(grid) == _top_as_row_widths(grid):
        reasons.append("top-header-as-row-width shortcut is answer-equivalent on this scene")
    return reasons


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared profile from the generated grid shape."""
    errors = _rectangular_errors(grid)
    if errors:
        return {}
    return {"scene_profile": _PROFILE_BY_SHAPE.get((len(grid), len(grid[0])))}


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Test-only mirror of the selected Racket rule; Racket remains authority."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h - 1, w - 1, 0)
    for r in range(h - 1):
        width = int(grid[r + 1][0])
        for c in range(min(width, w - 1)):
            out[r][c] = 3
    return out


def _right_aligned(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h - 1, w - 1, 0)
    ncols = w - 1
    for r in range(h - 1):
        width = min(int(grid[r + 1][0]), ncols)
        for c in range(ncols - width, ncols):
            out[r][c] = 3
    return out


def _unit_bars(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h - 1, w - 1, 0)
    for r in range(h - 1):
        if int(grid[r + 1][0]) > 0:
            out[r][0] = 3
    return out


def _header_colored_bars(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h - 1, w - 1, 0)
    for r in range(h - 1):
        width = min(int(grid[r + 1][0]), w - 1)
        color = int(grid[r + 1][0])
        for c in range(width):
            out[r][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "right_aligned_bars": _right_aligned,
    "one_cell_per_nonzero_row": _unit_bars,
    "row_header_value_as_fill_color": _header_colored_bars,
    "top_header_values_as_row_widths": _top_as_row_widths,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not strict_canonical_like(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "partial_row_refutes_right_alignment": lambda grid: _valid_and_refutes(grid, "right_aligned_bars"),
    "multi_cell_row_refutes_unit_bars": lambda grid: _valid_and_refutes(grid, "one_cell_per_nonzero_row"),
    "green_role_refutes_header_coloring": lambda grid: _valid_and_refutes(grid, "row_header_value_as_fill_color"),
    "dual_headers_refute_top_as_row_widths": lambda grid: _valid_and_refutes(grid, "top_header_values_as_row_widths"),
}

WITNESS_RIVALS = {
    "partial_row_refutes_right_alignment": ["right_aligned_bars"],
    "multi_cell_row_refutes_unit_bars": ["one_cell_per_nonzero_row"],
    "green_role_refutes_header_coloring": ["row_header_value_as_fill_color"],
    "dual_headers_refute_top_as_row_widths": ["top_header_values_as_row_widths"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo lesson to reject all named query-changing rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the selected rule")

    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = str(ctx.draw_choice("scene_profile", options))
    h, w = _PROFILE_SHAPES[profile]

    candidates = _partition_candidates(h, w, profile in _ANCHOR_PROFILES)
    rng = ctx.draw_rng("partition")
    row_widths = rng.choice(candidates)
    grid = _build_grid(h, w, row_widths)

    # Fail closed if a future edit breaks the profile's exact semantics.
    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError(f"generated invalid Ferrers scene: {errors}")
    observed = observe_overrides(grid).get("scene_profile")
    if observed != profile:
        raise RuntimeError(f"scene_profile {profile!r} realized as {observed!r}")
    return grid
