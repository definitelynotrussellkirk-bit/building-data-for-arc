"""Semantic generator for ARC task 7c21f478e6ac.

Each isolated nonzero seed expands into a same-color Manhattan-radius-one plus
(center plus the four cardinal neighbours), clipped at the grid boundary.
Generated seeds stay far enough apart that pluses never overlap, matching the
canonical examples and avoiding an unspecified color-collision rule.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7c21f478e6ac"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9e63f6b27275"
SUMMARY = (
    "On a fresh zero background of unchanged dimensions, replace every isolated "
    "nonzero seed by a plus consisting of the seed cell and its in-bounds four "
    "cardinal neighbours, all in that seed's color. Boundary arms are clipped."
)
INVARIANTS = [
    "the grid is rectangular and uses ARC colors 0..9",
    "every lesson contains two through seven isolated nonzero seed cells",
    "seed centers are Manhattan-distance at least four, so output pluses do not overlap",
    "both interior and boundary-clipped seeds occur in the scheduled curriculum",
    "the output authority is the pinned canonical Racket rule",
]

# One exact, observable axis replaces the previous nine declarations whose
# values were ignored, not recorded by GenCtx, or impossible to recover from a
# returned grid.  Profiles are mutually exclusive under observe_overrides().
SCENE_PROFILES = (
    "canonical_like",
    "interior_monochrome",
    "interior_multicolor",
    "edge_monochrome",
    "edge_multicolor",
    "corner_monochrome",
    "corner_multicolor",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index modulo the seven-profile semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    }
}
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = len(SCENE_PROFILES)
MIN_STRICT_FRAC = 1.0

_CANONICAL_SHAPES = ((7, 7, 2), (8, 8, 2), (7, 9, 2), (9, 9, 2), (9, 9, 3))
_GENERAL_SIZE_RANGES = {
    "easy": (6, 9, 8, 11, 2, 3),
    "medium": (9, 13, 11, 15, 3, 5),
    "hard": (13, 18, 14, 19, 4, 7),
}


def _band(difficulty: str | None) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """The lesson schedule is deliberately independent of seed and band.

    Any seven consecutive sample indexes contain every decisive profile once,
    so an EXAMPLES_NEEDED-sized demonstration block always refutes the named
    shortcut families before its query is asked.
    """
    del seed
    _band(difficulty)  # validate the public argument even though the cycle is shared
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")


def _is_boundary(r: int, c: int, h: int, w: int) -> bool:
    return r in (0, h - 1) or c in (0, w - 1)


def _is_corner(r: int, c: int, h: int, w: int) -> bool:
    return r in (0, h - 1) and c in (0, w - 1)


def _seed_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _candidate_positions(h: int, w: int, region: str) -> list[tuple[int, int]]:
    if region == "interior":
        return [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    if region == "edge":
        return [
            (r, c)
            for r in range(h)
            for c in range(w)
            if _is_boundary(r, c, h, w) and not _is_corner(r, c, h, w)
        ]
    if region == "corner":
        return [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    raise ValueError(f"unknown position region: {region!r}")


def _far_enough(candidate: tuple[int, int], placed: list[tuple[int, int]]) -> bool:
    r, c = candidate
    return all(abs(r - rr) + abs(c - cc) >= 4 for rr, cc in placed)


def _choose_positions(
    rng, h: int, w: int, count: int, boundary_kind: str
) -> list[tuple[int, int]]:
    """Randomized deterministic backtracking over the legal position grammar.

    The previous one-pass greedy chooser could paint itself into a corner on a
    small canonical canvas even though a legal arrangement existed.  This
    search uses the same keyed RNG for option order, but backtracks instead of
    turning an unlucky early choice into a generation crash.
    """
    interior = _candidate_positions(h, w, "interior")
    first_pool = (
        interior
        if boundary_kind == "interior"
        else _candidate_positions(h, w, boundary_kind)
    )
    placed: list[tuple[int, int]] = []

    def search(depth: int) -> bool:
        if depth == count:
            return True
        pool = first_pool if depth == 0 else interior
        options = [
            position
            for position in pool
            if position not in placed and _far_enough(position, placed)
        ]
        rng.shuffle(options)
        for position in options:
            placed.append(position)
            if search(depth + 1):
                return True
            placed.pop()
        return False

    if not search(0):
        raise ValueError(
            f"profile geometry has no legal placement: {h}x{w}, "
            f"count={count}, boundary_kind={boundary_kind}"
        )
    return placed


def _general_dimensions(rng, band: str) -> tuple[int, int, int]:
    h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = _GENERAL_SIZE_RANGES[band]
    for _ in range(100):
        h = rng.randint(h_lo, h_hi)
        w = rng.randint(w_lo, w_hi)
        # Keep the general profiles structurally distinct from canonical_like.
        if (h, w) not in {(hh, ww) for hh, ww, _ in _CANONICAL_SHAPES}:
            return h, w, rng.randint(n_lo, n_hi)
    raise RuntimeError("failed to draw a noncanonical general canvas")


def _color_sequence(rng, count: int, multicolor: bool) -> list[int]:
    if not multicolor:
        return [rng.randint(1, 9)] * count
    first, second = rng.sample(range(1, 10), 2)
    colors = [first, second]
    colors.extend(rng.randint(1, 9) for _ in range(count - 2))
    rng.shuffle(colors)
    return colors


def _build_profile(rng, profile: str, band: str) -> list[list[int]]:
    # Three of seven scheduled profiles anchor the exact canonical
    # (height, width, palette-size) support while varying the decisive
    # interior/edge/corner clipping branch.
    if profile in {"canonical_like", "edge_multicolor", "corner_multicolor"}:
        h, w, n = rng.choice(_CANONICAL_SHAPES)
        multicolor = True
        boundary_kind = (
            "interior" if profile == "canonical_like"
            else profile.split("_", 1)[0]
        )
    else:
        h, w, n = _general_dimensions(rng, band)
        multicolor = profile.endswith("multicolor")
        boundary_kind = profile.split("_", 1)[0]

    if boundary_kind not in {"interior", "edge", "corner"}:
        raise ValueError(f"unknown boundary profile: {profile!r}")
    grid = full_grid(h, w, 0)
    placed = _choose_positions(rng, h, w, n, boundary_kind)

    for (r, c), color in zip(placed, _color_sequence(rng, n, multicolor)):
        grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, band)
    if overrides.get("scene_profile") is None:
        # A singleton keyed choice preserves provenance while keeping the
        # sequential semantic schedule exact.
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    return _build_profile(ctx.draw_rng("layout"), profile, band)


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return errors
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    if not (5 <= len(grid) <= 20 and 5 <= width <= 20):
        errors.append("grid dimensions must each be in 5..20")
    return errors


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    _band(difficulty)
    seeds = _seed_cells(grid)
    if not 2 <= len(seeds) <= 7:
        errors.append(f"seed count {len(seeds)} outside 2..7")
    for index, (r, c, _value) in enumerate(seeds):
        for rr, cc, _other in seeds[index + 1 :]:
            distance = abs(r - rr) + abs(c - cc)
            if distance < 4:
                errors.append(
                    "seed centers must be Manhattan-distance at least four; "
                    f"found distance {distance}"
                )
                return errors
    return errors


def _profile_of(grid: list[list[int]]) -> str:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    seeds = _seed_cells(grid)
    distinct = len({value for _, _, value in seeds})
    if (
        all(not _is_boundary(r, c, h, w) for r, c, _ in seeds)
        and (h, w, len(seeds)) in _CANONICAL_SHAPES
        and distinct >= 2
    ):
        return "canonical_like"
    has_corner = any(_is_corner(r, c, h, w) for r, c, _ in seeds)
    has_edge = any(_is_boundary(r, c, h, w) for r, c, _ in seeds)
    region = "corner" if has_corner else ("edge" if has_edge else "interior")
    color_kind = "monochrome" if distinct == 1 else "multicolor"
    profile = f"{region}_{color_kind}"
    if profile not in SCENE_PROFILES:
        raise ValueError(f"grid does not realize a declared scene profile: {profile}")
    return profile


def observe_overrides(grid):
    return {"scene_profile": _profile_of(grid)}


def strict_canonical_like(grid):
    """Task grammar, not an exact-size predicate; accepts every canonical input."""
    return self_check(grid)


def _apply_plus_unchecked(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r, c, value in _seed_cells(grid):
        for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < h and 0 <= cc < w:
                output[rr][cc] = value
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _apply_plus_unchecked(grid)


# ---------------------------------------------------------------------------
# Named shortcut families and evidence hooks
# ---------------------------------------------------------------------------

def _identity(grid):
    return [list(row) for row in grid]


def _paint_offsets(grid, offsets, *, include_all=True, color_fn: Callable | None = None):
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    seeds = _seed_cells(grid)
    if not include_all:
        seeds = seeds[:1]
    modal = Counter(value for _, _, value in seeds).most_common(1)[0][0] if seeds else 0
    for r, c, value in seeds:
        paint = color_fn(value, modal) if color_fn else value
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                output[rr][cc] = paint
    return output


def _diagonal_x(grid):
    return _paint_offsets(grid, ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)))


def _without_center(grid):
    return _paint_offsets(grid, ((-1, 0), (1, 0), (0, -1), (0, 1)))


def _square_3x3(grid):
    return _paint_offsets(grid, tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)))


def _horizontal_only(grid):
    return _paint_offsets(grid, ((0, -1), (0, 0), (0, 1)))


def _vertical_only(grid):
    return _paint_offsets(grid, ((-1, 0), (0, 0), (1, 0)))


def _first_seed_only(grid):
    return _paint_offsets(grid, ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)), include_all=False)


def _modal_color_plus(grid):
    return _paint_offsets(
        grid,
        ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)),
        color_fn=lambda _value, modal: modal,
    )


def _fixed_color_plus(grid):
    return _paint_offsets(
        grid,
        ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)),
        color_fn=lambda _value, _modal: 1,
    )


def _interior_only(grid):
    h, w = len(grid), len(grid[0])
    filtered = full_grid(h, w, 0)
    for r, c, value in _seed_cells(grid):
        if not _is_boundary(r, c, h, w):
            filtered[r][c] = value
    return _apply_plus_unchecked(filtered)


def _boundary_only(grid):
    h, w = len(grid), len(grid[0])
    filtered = full_grid(h, w, 0)
    for r, c, value in _seed_cells(grid):
        if _is_boundary(r, c, h, w):
            filtered[r][c] = value
    return _apply_plus_unchecked(filtered)


SEMANTIC_RIVALS = {
    "identity_seed_only": _identity,
    "diagonal_x": _diagonal_x,
    "cardinals_without_center": _without_center,
    "full_3x3_square": _square_3x3,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "first_seed_only": _first_seed_only,
    "modal_color_plus": _modal_color_plus,
    "fixed_color_one_plus": _fixed_color_plus,
    "ignore_boundary_seeds": _interior_only,
    "expand_only_boundary_seeds": _boundary_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every canonical seed is interior, so the canonical examples cannot
    # distinguish this shortcut. Generated edge/corner profiles must.
    "ignore_boundary_seeds": _interior_only,
}


def _valid(grid) -> bool:
    return not self_check(grid)


def _has_boundary_seed(grid) -> bool:
    if not _valid(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(_is_boundary(r, c, h, w) for r, c, _ in _seed_cells(grid))


def _has_interior_seed(grid) -> bool:
    if not _valid(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(not _is_boundary(r, c, h, w) for r, c, _ in _seed_cells(grid))


def _has_multiple_colors(grid) -> bool:
    return _valid(grid) and len({v for _, _, v in _seed_cells(grid)}) >= 2


SEMANTIC_WITNESSES = {
    "cardinal_growth_not_identity": _valid,
    "cardinal_not_diagonal": _valid,
    "center_is_retained": _valid,
    "not_a_filled_3x3_square": _valid,
    "both_horizontal_and_vertical_arms": _valid,
    "every_seed_expands": _valid,
    "per_seed_color_preserved": _has_multiple_colors,
    "boundary_seed_is_clipped_not_ignored": _has_boundary_seed,
    "interior_seed_is_not_a_boundary_only_rule": _has_interior_seed,
}
WITNESS_RIVALS = {
    "cardinal_growth_not_identity": ["identity_seed_only"],
    "cardinal_not_diagonal": ["diagonal_x"],
    "center_is_retained": ["cardinals_without_center"],
    "not_a_filled_3x3_square": ["full_3x3_square"],
    "both_horizontal_and_vertical_arms": ["horizontal_only", "vertical_only"],
    "every_seed_expands": ["first_seed_only"],
    "per_seed_color_preserved": ["modal_color_plus", "fixed_color_one_plus"],
    "boundary_seed_is_clipped_not_ignored": ["ignore_boundary_seeds"],
    "interior_seed_is_not_a_boundary_only_rule": ["expand_only_boundary_seeds"],
}


def lesson_identifiable(demos, query):
    """Return reasons only when a named plausible rival survives the demos and
    would answer the query differently.

    The seven-profile schedule means every normal lesson contains one example
    from each semantic profile, but this hook independently validates the
    materialized outputs and names any surviving counter-hypothesis.
    """
    checked = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(demo["input"])
        if errors:
            return [f"demo {index} input is off-grammar: {errors[0]}"]
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            return [f"demo {index} output disagrees with the pinned rule mirror"]
        checked.append(demo)
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input/output pair"]
    q_errors = self_check(query["input"])
    if q_errors:
        return [f"query input is off-grammar: {q_errors[0]}"]
    true_query = rule_mirror(query["input"])

    reasons = []
    for name, competitor in sorted(LESSON_COMPETITORS.items()):
        fits_demos = all(competitor(demo["input"]) == demo["output"] for demo in checked)
        if fits_demos and competitor(query["input"]) != true_query:
            reasons.append(
                f"competitor {name!r} fits every demo but answers the query differently"
            )
    return reasons
