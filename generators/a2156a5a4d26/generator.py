"""Generator for arc_puzzle_bank_21_set2:S2_M7 — pair-color rectangle fill.

Authoritative rule: for every non-zero color that appears EXACTLY twice, treat
its two cells as opposite rectangle corners and fill the inclusive bounding
rectangle with that color.  Colors with any other multiplicity stay unchanged.

The public examples have three correlations that are not part of the rule:
all qualifying pairs use the NW->SE diagonal, every non-zero color qualifies,
and every qualifying rectangle is three rows tall.  Ordinary generated lessons
alternate canonical-profile anchors with a counterexample profile that breaks
all three correlations at once.  Two consecutive demonstrations therefore
always include a shortcut-rebutting example.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2156a5a4d26"
TASK_ID = "a2156a5a4d26"
VERSION = "2.0.0"
RULE_HASH = "c60ea943a128"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a 0-background grid, every color appearing exactly twice marks two "
    "opposite corners of a nondegenerate rectangle. Fill each such inclusive "
    "bounding rectangle with that color. Other non-zero colors may be present "
    "with non-pair multiplicities and remain unchanged. Qualifying rectangles "
    "do not overlap or contain distractor cells."
)

INVARIANTS = [
    "background is 0 and cell values are ARC colors 0..9",
    "at least two non-zero colors appear exactly twice",
    "each exactly-twice color occupies different rows and different columns",
    "qualifying pair bounding rectangles are pairwise non-overlapping",
    "non-pair distractor cells lie outside every qualifying rectangle",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchor by difficulty",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchor by difficulty",
        "valid": "10..14",
    },
    "n_pairs": {
        "type": "int",
        "default": "2 on easy/medium; 3 on hard",
        "valid": "2..3",
    },
    "pair_height": {
        "type": "int",
        "default": "3 on anchor slots; 2 on shortcut-counterexample slots",
        "valid": "2..3",
    },
    "pair_width": {
        "type": "int",
        "default": "4 on anchors; keyed 2..4 on counterexamples",
        "valid": "2..4",
    },
    "n_distractors": {
        "type": "int",
        "default": "0 on anchors; 1 on shortcut-counterexample slots",
        "valid": "0..2",
    },
}

# Every boundary combination in AXES is realizable.  In the smallest 9x10
# canvas, three 3x4 qualifying rectangles fit in three row bands and still
# leave room for two disjoint 2x2 triplet-distractor boxes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("anchor", "shortcut_counterexample")
_CANONICAL_PROFILE_BY_BAND = {
    "easy": (9, 10, 2),
    "medium": (10, 11, 2),
    "hard": (12, 12, 3),
    None: (10, 11, 2),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternate profiles so every two-consecutive-demo window has a rebuttal."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 2]


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int | None) -> int:
    """Consume exact overrides against full bounds; otherwise record the default."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    if default is not None:
        return int(ctx.draw_choice(label, (default,)))
    return ctx.draw_int(label, lo, hi)


def _positions_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def _bbox_cells(cells: list[tuple[int, int]]) -> set[tuple[int, int]]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }


def _structural_errors(grid: Any, *, require_two_pairs: bool) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid rows must have equal width"]

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not (0 <= value <= 9):
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                if len(errors) >= 4:
                    return errors

    positions = _positions_by_color(grid)
    pair_colors = [color for color, cells in positions.items() if len(cells) == 2]
    needed = 2 if require_two_pairs else 1
    if len(pair_colors) < needed:
        errors.append(
            f"need at least {needed} qualifying color(s) appearing exactly twice; "
            f"found {len(pair_colors)}"
        )
        return errors

    boxes: list[tuple[int, set[tuple[int, int]]]] = []
    for color in sorted(pair_colors):
        a, b = positions[color]
        if a[0] == b[0] or a[1] == b[1]:
            errors.append(
                f"color {color} pair {a}/{b} is collinear instead of opposite corners"
            )
            continue
        box = _bbox_cells([a, b])
        for other_color, other_box in boxes:
            if box & other_box:
                errors.append(
                    f"qualifying rectangles for colors {other_color} and {color} overlap"
                )
        boxes.append((color, box))

    if errors:
        return errors

    pair_set = set(pair_colors)
    for color, cells in positions.items():
        if color in pair_set:
            continue
        for cell in cells:
            for pair_color, box in boxes:
                if cell in box:
                    errors.append(
                        f"distractor color {color} at {cell} lies inside color "
                        f"{pair_color}'s qualifying rectangle"
                    )
                    if len(errors) >= 4:
                        return errors
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural task grammar; canonical inputs and every normal draw must pass."""
    del difficulty, meta
    return _structural_errors(grid, require_two_pairs=False)


def strict_canonical_like(grid) -> list[str]:
    """Task-linked teaching predicate, anchored to all canonical train/test inputs."""
    errors = _structural_errors(grid, require_two_pairs=True)
    if errors:
        return errors
    counts = Counter(value for row in grid for value in row if value != 0)
    bad = sorted((color, count) for color, count in counts.items() if count not in (2, 3))
    if bad:
        return [
            "non-pair colors on the teaching manifold must be triplet distractors; "
            f"found {bad}"
        ]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests/evidence only; canonical Racket is authority."""
    errors = _structural_errors(grid, require_two_pairs=False)
    if errors:
        raise ValueError("rule_mirror expects a lawful task scene: " + "; ".join(errors))
    out = [list(row) for row in grid]
    positions = _positions_by_color(grid)
    for color in sorted(positions):
        cells = positions[color]
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r][c] = color
    return out


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact declared axis from a returned generated grid."""
    errors = _structural_errors(grid, require_two_pairs=True)
    if errors:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
    positions = _positions_by_color(grid)
    pairs = [cells for cells in positions.values() if len(cells) == 2]
    heights = {abs(cells[0][0] - cells[1][0]) + 1 for cells in pairs}
    widths = {abs(cells[0][1] - cells[1][1]) + 1 for cells in pairs}
    if len(heights) != 1 or len(widths) != 1:
        raise ValueError("generated exact pair_height/pair_width are not uniform")
    distractors = [cells for cells in positions.values() if len(cells) != 2]
    if any(len(cells) != 3 for cells in distractors):
        raise ValueError("generated non-pair colors must be triplet distractors")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(pairs),
        "pair_height": next(iter(heights)),
        "pair_width": next(iter(widths)),
        "n_distractors": len(distractors),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    errors = strict_canonical_like(grid)
    if errors:
        return {"valid": False, "errors": errors}
    positions = _positions_by_color(grid)
    pairs = [cells for cells in positions.values() if len(cells) == 2]
    main = anti = 0
    heights = []
    for cells in pairs:
        a, b = sorted(cells)
        heights.append(abs(a[0] - b[0]) + 1)
        if a[1] < b[1]:
            main += 1
        else:
            anti += 1
    counts = Counter(value for row in grid for value in row if value != 0)
    return {
        "valid": True,
        "n_pairs": len(pairs),
        "main_pairs": main,
        "anti_pairs": anti,
        "pair_heights": tuple(sorted(set(heights))),
        "triplet_distractors": sum(1 for count in counts.values() if count == 3),
    }


def _apply_pair_rule_with_filter(grid, predicate: Callable[[int, list[tuple[int, int]]], bool]):
    out = [list(row) for row in grid]
    positions = _positions_by_color(grid)
    for color in sorted(positions):
        cells = positions[color]
        if not predicate(color, cells):
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                out[r][c] = color
    return out


def _main_diagonal_only(grid):
    def qualifies(_color, cells):
        if len(cells) != 2:
            return False
        a, b = sorted(cells)
        return a[0] != b[0] and a[1] < b[1]
    return _apply_pair_rule_with_filter(grid, qualifies)


def _fill_every_nonzero_bbox(grid):
    return _apply_pair_rule_with_filter(grid, lambda _color, cells: bool(cells))


def _height_three_only(grid):
    return _apply_pair_rule_with_filter(
        grid,
        lambda _color, cells: (
            len(cells) == 2 and abs(cells[0][0] - cells[1][0]) + 1 == 3
        ),
    )


def _outline_only(grid):
    out = [list(row) for row in grid]
    positions = _positions_by_color(grid)
    for color in sorted(positions):
        cells = positions[color]
        if len(cells) != 2:
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    out[r][c] = color
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _witness_anti_diagonal(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and int(profile.get("anti_pairs", 0)) > 0)


def _witness_triplet_distractor(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and int(profile.get("triplet_distractors", 0)) > 0)


def _witness_noncanonical_height(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and 2 in profile.get("pair_heights", ()))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "anti_diagonal_pair": _witness_anti_diagonal,
    "triplet_distractor": _witness_triplet_distractor,
    "pair_height_not_three": _witness_noncanonical_height,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "main_diagonal_only": _main_diagonal_only,
    "fill_every_nonzero_bbox": _fill_every_nonzero_bbox,
    "height_three_only": _height_three_only,
    "outline_only": _outline_only,
    "identity": _identity,
}
WITNESS_RIVALS = {
    "anti_diagonal_pair": ["main_diagonal_only"],
    "triplet_distractor": ["fill_every_nonzero_bbox"],
    "pair_height_not_three": ["height_three_only"],
}

# Each of these shortcuts reproduces every canonical train/test pair, so the
# public task alone cannot disprove it.  Counterexample-profile generated draws
# must do that work.
CANONICAL_SHORTCUTS = {
    "main_diagonal_only": _main_diagonal_only,
    "fill_every_nonzero_bbox": _fill_every_nonzero_bbox,
    "height_three_only": _height_three_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits all demos but changes the query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    reasons: list[str] = []
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            reasons.append(f"{role} input is not lawful: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the exactly-twice rectangle rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed near-misses that structural self_check must reject."""
    no_pair = full_grid(7, 8, 0)
    no_pair[1][1] = no_pair[1][2] = no_pair[2][1] = 4

    same_row = full_grid(7, 8, 0)
    same_row[1][1] = same_row[1][5] = 2
    same_row[4][1] = 3
    same_row[6][4] = 3

    overlap = full_grid(7, 8, 0)
    overlap[1][1] = overlap[4][5] = 2
    overlap[2][2] = overlap[5][6] = 3

    distractor_inside = full_grid(8, 9, 0)
    distractor_inside[1][1] = distractor_inside[4][5] = 2
    distractor_inside[5][1] = distractor_inside[7][4] = 3
    distractor_inside[2][2] = distractor_inside[2][3] = distractor_inside[3][2] = 7

    ragged = [[0, 2, 0, 0], [0, 0, 2], [0, 3, 0, 0], [0, 0, 0, 3]]

    return [
        ("no_exactly_twice_color", no_pair),
        ("collinear_pair_not_rectangle_corners", same_row),
        ("overlapping_qualifying_rectangles", overlap),
        ("distractor_inside_qualifying_rectangle", distractor_inside),
        ("ragged_grid", ragged),
    ]


def _place_triplet_distractors(
    grid: list[list[int]],
    colors: list[int],
    reserved: set[tuple[int, int]],
    rng,
) -> None:
    """Place separated L-triominoes whose bbox exposes the count-only shortcut."""
    h, w = len(grid), len(grid[0])
    candidates = [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if not ({(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} & reserved)
    ]
    rng.shuffle(candidates)
    for color in colors:
        placed = False
        for r, c in candidates:
            box = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
            if box & reserved:
                continue
            missing = rng.randrange(4)
            cells = sorted(box)
            for index, (rr, cc) in enumerate(cells):
                if index != missing:
                    grid[rr][cc] = color
            reserved |= box
            placed = True
            break
        if not placed:
            raise RuntimeError("could not place a non-overlapping triplet distractor")


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
    profile = schedule_profile(seed, sample_index, difficulty)
    anchor_h, anchor_w, anchor_pairs = _CANONICAL_PROFILE_BY_BAND[difficulty]

    h = _draw_int_axis(ctx, "grid_h", 9, 14, anchor_h)
    w = _draw_int_axis(ctx, "grid_w", 10, 14, anchor_w)
    n_pairs = _draw_int_axis(ctx, "n_pairs", 2, 3, anchor_pairs)
    pair_height = _draw_int_axis(
        ctx,
        "pair_height",
        2,
        3,
        3 if profile == "anchor" else 2,
    )
    pair_width = _draw_int_axis(
        ctx,
        "pair_width",
        2,
        4,
        4 if profile == "anchor" else None,
    )
    n_distractors = _draw_int_axis(
        ctx,
        "n_distractors",
        0,
        2,
        0 if profile == "anchor" else 1,
    )

    # The declared Cartesian domain is intentionally chosen so this packing
    # proof holds even at every simultaneous boundary override.
    total_pair_rows = n_pairs * pair_height
    if total_pair_rows > h:
        raise ValueError(
            f"pair packing requires {total_pair_rows} rows but grid_h={h}"
        )

    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(range(1, 10), n_pairs + n_distractors)
    pair_colors = colors[:n_pairs]
    distractor_colors = colors[n_pairs:]

    top_margin = layout_rng.randint(0, h - total_pair_rows)
    reserved: set[tuple[int, int]] = set()
    for index, color in enumerate(pair_colors):
        r1 = top_margin + index * pair_height
        r2 = r1 + pair_height - 1
        c1 = layout_rng.randint(0, w - pair_width)
        c2 = c1 + pair_width - 1
        box = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        # Row bands make this a proof, not a retry heuristic.
        if box & reserved:
            raise AssertionError("row-band rectangle packing overlapped")
        if profile == "shortcut_counterexample":
            # Anti-diagonal corners falsify the public-only NW->SE shortcut.
            grid[r1][c2] = color
            grid[r2][c1] = color
        else:
            grid[r1][c1] = color
            grid[r2][c2] = color
        reserved |= box

    _place_triplet_distractors(grid, distractor_colors, reserved, layout_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != expected[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={expected[axis]!r} observed={observed[axis]!r}"
            )
    return grid
