"""Lawful lesson generator for ARC task 0701a2c36d45.

The input is a one-row rotation-code header followed by three equal panels,
separated by full maroon (9) rows.  Rotate each panel occupancy according to
its header code and paint positions receiving at least two votes cyan (8).

The generator intentionally exposes only controls that can be reconstructed
exactly from returned pixels.  Its cyclic curriculum includes plain agreement,
one-panel noise, a two-panel signal, and a mixed example containing both kinds
of evidence, so majority voting remains identifiable under hold-one-out lessons.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0701a2c36d45"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "606946fe96ab"

SUMMARY = (
    "Read the three rotation codes in the first row. Split the remaining "
    "input at full color-9 rows into three equal panels, rotate each panel's "
    "nonzero occupancy by its code (1=0°, 2=90°, 3=180°, 4=270° clockwise), "
    "and output a panel-sized grid whose cells are color 8 exactly where at "
    "least two rotated panels are occupied."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

HELPFUL_TEXTURES = ("plain", "noise_robust", "two_agree", "mixed_vote")
SCHEDULE_PROFILES = HELPFUL_TEXTURES

INVARIANTS = [
    "one header row is followed by three full color-9 separator rows and three equal panels",
    "the first three header cells are rotation codes in 1..4 and remaining header cells are zero",
    "each panel contains one connected monochrome occupancy and the three panel colors are distinct",
    "after header rotations, cells with at least two of three occupancy votes are painted 8",
    "plain, one-panel-noise, two-panel-signal, and mixed-vote examples are lawful teaching branches",
]

AXES = {
    "panel_h": {
        "type": "int",
        "default": "keyed curriculum, canonical 4 emphasized",
        "valid": "3..8",
    },
    "panel_w": {
        "type": "int",
        "default": "keyed curriculum, canonical 4 emphasized",
        "valid": "3..8",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-weighted keyed choice",
        "valid": "2..8",
        "doc": "minimum aligned panel occupancy size (the shared base size)",
    },
    "texture": {
        "type": "str",
        "default": "four-slot cyclic lesson schedule",
        "valid": "plain|two_agree|noise_robust|mixed_vote",
        "doc": (
            "plain: all panels agree; noise_robust: one panel has one extra "
            "cell that is rejected; two_agree: two panels share one extra "
            "cell that survives; mixed_vote: one panel swaps a base cell for "
            "an extra, creating one one-vote cell and one two-vote cell."
        ),
    },
}

# The complete advertised Cartesian product is constructive, including
# shape_size=8 with a 3x3 panel (the two-agree extra fills the ninth cell).
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Connected, asymmetric fallbacks inside a 3x3 box, indexed by cell count.
_FALLBACK_SHAPES = {
    2: ((0, 0), (1, 0)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
    6: ((0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    points = list(cells)
    if not points:
        return []
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return sorted((r - min_r, c - min_c) for r, c in points)


def _rot90_cw(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    points = _normalize(cells)
    if not points:
        return []
    height = max(r for r, _ in points) + 1
    return _normalize((c, height - 1 - r) for r, c in points)


def _rot(cells: Iterable[tuple[int, int]], turns: int) -> list[tuple[int, int]]:
    out = _normalize(cells)
    for _ in range(turns % 4):
        out = _rot90_cw(out)
    return out


def _fits(cells: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    points = _normalize(cells)
    return not points or (
        max(r for r, _ in points) < h and max(c for _, c in points) < w
    )


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    if not points:
        return False
    reached = {next(iter(points))}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbour in points and neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    return reached == points


def _extra_candidates(
    cells: Iterable[tuple[int, int]], panel_h: int, panel_w: int
) -> list[tuple[int, int]]:
    base = set(_normalize(cells))
    candidates: set[tuple[int, int]] = set()
    limit = min(panel_h, panel_w)
    for r, c in base:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in base or point[0] < 0 or point[1] < 0:
                continue
            if point[0] >= limit or point[1] >= limit:
                continue
            grown = sorted(base | {point})
            if all(_fits(_rot(grown, turns), panel_h, panel_w) for turns in range(4)):
                candidates.add(point)
    return sorted(candidates)


def _random_motif(rng, size: int, panel_h: int, panel_w: int):
    """Return (connected asymmetric base, adjacent extra) constructively."""
    limit = min(panel_h, panel_w)
    for _ in range(160):
        cells = {(rng.randrange(limit), rng.randrange(limit))}
        while len(cells) < size:
            frontier = sorted({
                neighbour
                for r, c in cells
                for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if 0 <= neighbour[0] < limit
                and 0 <= neighbour[1] < limit
                and neighbour not in cells
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size:
            continue
        base = _normalize(cells)
        extras = _extra_candidates(base, panel_h, panel_w)
        if extras and _rot(base, 1) != base:
            return base, rng.choice(extras)

    base = list(_FALLBACK_SHAPES[size])
    extras = _extra_candidates(base, panel_h, panel_w)
    if not extras:  # The declared domain makes this unreachable.
        raise RuntimeError(
            f"no constructive extra for shape_size={size}, panel={panel_h}x{panel_w}"
        )
    return _normalize(base), extras[0]


def _mixed_variant_candidates(
    base: Iterable[tuple[int, int]], panel_h: int, panel_w: int
) -> list[list[tuple[int, int]]]:
    """Same-size connected variants with one removed base cell and one extra.

    Relative to two unchanged base panels, the removed coordinate receives two
    votes and the added coordinate receives one.  Requiring normalization to be
    unchanged keeps those coordinates aligned after inverse/forward rotations.
    """
    base_set = set(_normalize(base))
    extras = _extra_candidates(base_set, panel_h, panel_w)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for removed in sorted(base_set):
        for added in extras:
            candidate = sorted((base_set - {removed}) | {added})
            if not _connected(candidate):
                continue
            if _normalize(candidate) != candidate:
                continue
            if not all(_fits(_rot(candidate, turns), panel_h, panel_w) for turns in range(4)):
                continue
            variants.add(tuple(candidate))
    return [list(candidate) for candidate in sorted(variants)]


def _paint(
    grid: list[list[int]], top: int, left: int,
    cells: Iterable[tuple[int, int]], color: int,
) -> None:
    for r, c in cells:
        grid[top + r][left + c] = color


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    for name, lo, hi in (("panel_h", 3, 8), ("panel_w", 3, 8), ("shape_size", 2, 8)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    texture = overrides.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(
            f"texture override {texture!r} must be one of {HELPFUL_TEXTURES!r}"
        )


def _dimension_options(difficulty) -> tuple[int, ...]:
    # Every band accepts every exact value.  The repeated canonical width/height
    # makes the exact 16x4 canonical profile common rather than accidental.
    tails = {
        "easy": (3, 5, 6, 7, 8),
        "medium": (5, 3, 6, 7, 8),
        "hard": (8, 7, 6, 5, 3),
    }.get(difficulty, (3, 5, 6, 7, 8))
    return (4,) * 16 + tails


def _shape_size_options(difficulty) -> tuple[int, ...]:
    return {
        "easy": (2, 2, 2, 3, 3, 3, 4, 4, 5, 6, 7, 8),
        "medium": (2, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 7, 8),
        "hard": (2, 3, 4, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8),
    }.get(difficulty, (2, 3, 4, 4, 5, 5, 6, 7, 8))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Six-slot cycle with at least two mixed witnesses in every five draws."""
    del seed, difficulty
    return (
        "mixed_vote", "plain", "mixed_vote",
        "noise_robust", "mixed_vote", "two_agree",
    )[sample_index % 6]


def _scheduled_texture(ctx, desired: str) -> str:
    """Record a full-domain keyed draw while deterministically selecting desired.

    A fresh keyed RNG predicts the index used by draw_choice; rotating the full
    option domain puts the scheduled value at that index. Explicit caller
    overrides still pass through draw_choice's ordinary validity/provenance path.
    """
    choices = list(HELPFUL_TEXTURES)
    chosen_index = ctx.draw_rng("texture").randrange(len(choices))
    ordered = [value for value in choices if value != desired]
    ordered.insert(chosen_index, desired)
    return ctx.draw_choice("texture", tuple(ordered))


def _code_candidates(rng):
    from itertools import combinations, permutations

    candidates = [
        list(order)
        for subset in combinations((1, 2, 3, 4), 3)
        for order in permutations(subset)
    ]
    rng.shuffle(candidates)
    return candidates


def _codes_teach_rotation(codes, variants, panel_h: int, panel_w: int) -> bool:
    aligned = [set(_normalize(cells)) for cells in variants]
    raw = [
        set(_rot(variants[index], -(codes[index] - 1)))
        for index in range(3)
    ]
    return (
        _render_votes(panel_h, panel_w, raw, 2)
        != _render_votes(panel_h, panel_w, aligned, 2)
    )


def _panel_colors(rng, codes):
    colors = rng.sample(list(codes), 2) + [rng.choice((5, 6, 7))]
    rng.shuffle(colors)
    return colors


def _build_grid(
    panel_h: int,
    panel_w: int,
    codes: list[int],
    panel_colors: list[int],
    variants: list[list[tuple[int, int]]],
) -> list[list[int]]:
    grid = full_grid(1 + 3 * (panel_h + 1), panel_w, 0)
    for index, code in enumerate(codes):
        grid[0][index] = code
    for index in range(3):
        separator = 1 + index * (panel_h + 1)
        grid[separator] = [9] * panel_w
        cells = _rot(variants[index], -(codes[index] - 1))
        shape_h = max(r for r, _ in cells) + 1
        shape_w = max(c for _, c in cells) + 1
        top = separator + 1 + (panel_h - shape_h) // 2
        left = (panel_w - shape_w) // 2
        _paint(grid, top, left, cells, panel_colors[index])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    panel_h = ctx.draw_choice("panel_h", _dimension_options(difficulty))
    panel_w = ctx.draw_choice("panel_w", _dimension_options(difficulty))
    shape_size = ctx.draw_choice("shape_size", _shape_size_options(difficulty))
    texture = _scheduled_texture(
        ctx, schedule_profile(seed, sample_index, difficulty=difficulty)
    )
    motif_rng = ctx.draw_rng("motif")
    palette_rng = ctx.draw_rng("palette")
    code_candidates = _code_candidates(palette_rng)

    for _ in range(160):
        base, extra = _random_motif(motif_rng, shape_size, panel_h, panel_w)
        grown = sorted(set(base) | {extra})
        variants = [list(base), list(base), list(base)]
        if texture == "noise_robust":
            variants[0] = grown
        elif texture == "two_agree":
            variants[1] = grown
            variants[2] = grown
        elif texture == "mixed_vote":
            mixed_candidates = _mixed_variant_candidates(base, panel_h, panel_w)
            if not mixed_candidates:
                continue
            variants[0] = motif_rng.choice(mixed_candidates)
        # Prefer a code arrangement that makes ignoring the header observably
        # wrong.  The only unavoidable exception in the declared Cartesian
        # domain is a two-agree 8+1 construction filling a 3x3 square.
        saturated_two_agree = (
            texture == "two_agree"
            and shape_size + 1 == min(panel_h, panel_w) ** 2
        )
        viable_codes = [
            codes for codes in code_candidates
            if _codes_teach_rotation(codes, variants, panel_h, panel_w)
        ]
        if not viable_codes and not saturated_two_agree:
            continue
        codes = list(palette_rng.choice(viable_codes or code_candidates))
        panel_colors = _panel_colors(palette_rng, codes)
        grid = _build_grid(panel_h, panel_w, codes, panel_colors, variants)
        errors = self_check(grid)
        if errors:
            raise RuntimeError("internal generator contract failure: " + "; ".join(errors))
        return grid
    raise RuntimeError("failed to construct a rotation-discriminating lesson")


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty 2D list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integer ARC digits 0..9"]
    return []


def _split_segments(grid: list[list[int]]):
    width = len(grid[0])
    chunks: list[list[list[int]]] = []
    start = 0
    separator_rows = []
    for r, row in enumerate(grid):
        if all(value == 9 for value in row):
            chunks.append([list(part) for part in grid[start:r]])
            separator_rows.append(r)
            start = r + 1
    chunks.append([list(part) for part in grid[start:]])
    return chunks, separator_rows, width


def _panel_votes(grid: list[list[int]], *, rotate_header: bool = True):
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    chunks, separators, width = _split_segments(grid)
    if len(separators) != 3 or len(chunks) != 4 or len(chunks[0]) != 1:
        raise ValueError("expected one header and three panels split by three separators")
    header, panels = chunks[0], chunks[1:]
    if any(not panel or any(len(row) != width for row in panel) for panel in panels):
        raise ValueError("panels must be nonempty and rectangular")
    votes = []
    for index, panel in enumerate(panels):
        cells = [
            (r, c)
            for r, row in enumerate(panel)
            for c, value in enumerate(row)
            if value not in (0, 9)
        ]
        turns = header[0][index] - 1 if rotate_header else 0
        votes.append(set(_rot(cells, turns)))
    return header, panels, votes


def _render_votes(
    panel_h: int,
    panel_w: int,
    votes: Iterable[Iterable[tuple[int, int]]],
    threshold: int,
) -> list[list[int]]:
    counts = Counter(cell for cells in votes for cell in cells)
    output = [[0] * panel_w for _ in range(panel_h)]
    for (r, c), count in counts.items():
        if count >= threshold and 0 <= r < panel_h and 0 <= c < panel_w:
            output[r][c] = 8
    return output


def _solve_threshold(grid, threshold: int, *, rotate_header: bool = True):
    _, panels, votes = _panel_votes(grid, rotate_header=rotate_header)
    return _render_votes(len(panels[0]), len(panels[0][0]), votes, threshold)


def _rule_mirror(grid):
    """Independent Python mirror used for tests; canonical Racket is authority."""
    return _solve_threshold(grid, 2)


def _rival_union(grid):
    return _solve_threshold(grid, 1)


def _rival_unanimity(grid):
    return _solve_threshold(grid, 3)


def _rival_first_panel(grid):
    _, panels, votes = _panel_votes(grid)
    return _render_votes(len(panels[0]), len(panels[0][0]), [votes[0]], 1)


def _rival_ignore_header(grid):
    return _solve_threshold(grid, 2, rotate_header=False)


def _analysis(grid) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    chunks, separator_rows, width = _split_segments(grid)
    if any(9 in row and not all(value == 9 for value in row) for row in grid):
        errors.append("color 9 may appear only in full separator rows")
    if len(separator_rows) != 3:
        errors.append("expected exactly three full color-9 separator rows")
    if len(chunks) != 4:
        errors.append("expected header plus exactly three panel chunks")
        return result

    header, panels = chunks[0], chunks[1:]
    if len(header) != 1:
        errors.append("header must be exactly one row")
    if len(panels) != 3 or any(not panel for panel in panels):
        errors.append("expected exactly three nonempty panels")
        return result
    panel_heights = {len(panel) for panel in panels}
    if len(panel_heights) != 1:
        errors.append("panels must have equal heights")
        return result
    panel_h = len(panels[0])
    panel_w = width
    result.update(panel_h=panel_h, panel_w=panel_w, header=header, panels=panels)
    if not 3 <= panel_h <= 8 or not 3 <= panel_w <= 8:
        errors.append("panel dimensions must each be in 3..8")
    if len(grid) != 1 + 3 * (panel_h + 1):
        errors.append("separator/panel spacing does not match the declared structure")
    if panel_w < 3:
        errors.append("header must have room for three codes")
    elif len(header) == 1:
        if any(header[0][i] not in (1, 2, 3, 4) for i in range(3)):
            errors.append("first three header cells must be rotation codes 1..4")
        if any(value != 0 for value in header[0][3:]):
            errors.append("header cells after the three codes must be zero")

    panel_colors = []
    raw_cells = []
    for index, panel in enumerate(panels):
        colors = {value for row in panel for value in row if value != 0}
        if len(colors) != 1 or 9 in colors:
            errors.append(f"panel {index} must contain one nonzero non-9 color")
        else:
            panel_colors.append(next(iter(colors)))
        cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0]
        raw_cells.append(cells)
        if not _connected(cells):
            errors.append(f"panel {index} occupancy must be 4-connected")
    if len(panel_colors) == 3 and len(set(panel_colors)) != 3:
        errors.append("the three panel colors must be distinct")
    if len({value for row in grid for value in row}) != 6:
        errors.append("teaching inputs must use exactly six colors including 0 and 9")

    if len(header) != 1 or panel_w < 3:
        return result
    try:
        votes = [
            set(_rot(raw_cells[index], header[0][index] - 1))
            for index in range(3)
        ]
    except Exception as exc:  # malformed inputs should diagnose, never crash
        errors.append(f"could not rotate panel occupancies: {exc}")
        return result
    counts = Counter(cell for cells in votes for cell in cells)
    count1 = sorted(cell for cell, count in counts.items() if count == 1)
    count2 = sorted(cell for cell, count in counts.items() if count == 2)
    count3 = sorted(cell for cell, count in counts.items() if count == 3)
    panel_sizes = tuple(sorted(map(len, votes)))
    shape_size = min(panel_sizes)
    if not count1 and not count2 and panel_sizes == (shape_size,) * 3:
        texture = "plain"
    elif (
        len(count1) == 1 and not count2
        and panel_sizes == (shape_size, shape_size, shape_size + 1)
    ):
        texture = "noise_robust"
    elif (
        not count1 and len(count2) == 1
        and panel_sizes == (shape_size, shape_size + 1, shape_size + 1)
    ):
        texture = "two_agree"
    elif (
        len(count1) == 1 and len(count2) == 1
        and panel_sizes == (shape_size, shape_size, shape_size)
    ):
        texture = "mixed_vote"
    elif (
        panel_sizes == (4, 4, 4)
        and len(count1) == 3 and len(count2) == 3 and len(count3) == 1
    ):
        # Two canonical examples deliberately use three different tetrominoes
        # whose pairwise overlap, rather than full agreement, defines the vote.
        texture = "canonical_overlap"
    else:
        texture = "other"
        errors.append(
            "vote profile is outside the canonical or scheduled majority-vote grammar"
        )
    if not 2 <= shape_size <= 8:
        errors.append("aligned panel occupancies must contain 2..8 cells")
    if any(r >= panel_h or c >= panel_w for r, c in counts):
        errors.append("normalized vote coordinates must fit the panel")
    output = _render_votes(panel_h, panel_w, votes, 2)
    if not any(value == 8 for row in output for value in row):
        errors.append("majority-vote output must be nonempty")
    result.update(
        votes=votes,
        counts=counts,
        count1=count1,
        count2=count2,
        count3=count3,
        texture=texture,
        shape_size=shape_size,
        output=output,
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid teaching input: " + "; ".join(analysis["errors"]))
    return {
        "panel_h": analysis["panel_h"],
        "panel_w": analysis["panel_w"],
        "shape_size": analysis["shape_size"],
        "texture": analysis["texture"],
    }


def _witness_single_panel_noise(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["texture"] == "noise_robust"


def _witness_two_panel_signal(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["texture"] == "two_agree"


def _witness_rotation_required(grid) -> bool:
    return not self_check(grid) and _rival_ignore_header(grid) != _rule_mirror(grid)


def _witness_mixed_vote(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["texture"] == "mixed_vote"


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "union_any_panel": _rival_union,
    "unanimity_all_panels": _rival_unanimity,
    "first_panel_only": _rival_first_panel,
    "ignore_header_rotations": _rival_ignore_header,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}
SEMANTIC_WITNESSES = {
    "single_panel_noise": _witness_single_panel_noise,
    "two_panel_signal": _witness_two_panel_signal,
    "mixed_vote": _witness_mixed_vote,
    "rotation_required": _witness_rotation_required,
}
WITNESS_RIVALS = {
    "single_panel_noise": ["union_any_panel", "first_panel_only"],
    "two_panel_signal": ["unanimity_all_panels", "first_panel_only"],
    "mixed_vote": [
        "union_any_panel", "unanimity_all_panels", "first_panel_only"
    ],
    "rotation_required": ["ignore_header_rotations"],
}
BRANCH_WITNESSES = ("single_panel_noise", "two_panel_signal", "mixed_vote")


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != _rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the majority-vote rule")
            continue
        valid_demos.append(demo)

    if strict_canonical_like(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    elif query["output"] != _rule_mirror(query["input"]):
        reasons.append("query output disagrees with the majority-vote rule")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
