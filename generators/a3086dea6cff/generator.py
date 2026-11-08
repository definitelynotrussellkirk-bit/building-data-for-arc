"""Generator for ``arc_additional_puzzles_21_set4:M26`` — pair connectors.

For every colour that occurs exactly twice, connect the two cells when they
share a row or a column.  Generated three-example lessons deliberately include
both connector orientations, canonical-scale scenes, crossings, and two
otherwise-canonical counterexamples: a non-aligned pair and a three-cell colour.
Those counterexamples distinguish the exact rule from plausible shortcuts while
the canonical Racket program remains the output authority.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3086dea6cff"
TASK_ID = "a3086dea6cff"
VERSION = "3.0.0"
RULE_HASH = "7563337a81ab"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A black 8-13 by 10-15 grid contains 2-4 active same-colour pairs. "
    "Every scene has at least one horizontal and one vertical pair, and most "
    "lesson windows include an interior crossing. For a colour occurring "
    "exactly twice, fill the inclusive segment only when its cells share a "
    "row or column. A scheduled non-aligned pair and a scheduled collinear "
    "three-cell colour remain unchanged, refuting L-connection and count-"
    "agnostic shortcuts."
)

INVARIANTS = [
    "background is 0 and every non-background colour is distinct by role",
    "2-4 active colours occur exactly twice with endpoint separation at least 3",
    "every generated scene contains both horizontal and vertical active pairs",
    "active segments may cross only through empty interior cells; endpoints are distinct",
    "at most one scheduled decoy colour occurs: either one non-aligned pair or one gapped collinear triple",
    "every three consecutive examples contain a canonical-scale anchor, both decoy types, and a crossing witness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-skewed 8..13",
        "valid": "8..13",
        "doc": "Canvas height; exact overrides are valid in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-skewed 10..15",
        "valid": "10..15",
        "doc": "Canvas width; exact overrides are valid in every band.",
    },
    "n_pairs": {
        "type": "int",
        "default": "canonical anchor or difficulty-skewed 2..4",
        "valid": "2..4",
        "doc": "Number of active aligned same-colour pairs, excluding decoys.",
    },
}

SCHEDULE_PROFILES = ("canonical", "triple_decoy", "nonaligned_decoy")
_CANONICAL_PROFILES = ((8, 10, 3), (9, 11, 3), (10, 12, 3), (11, 13, 4))


def _normalize_difficulty(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_request(difficulty, overrides) -> str:
    band = _normalize_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    return band


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, label: str, lo: int, hi: int, default, overrides) -> int:
    if overrides.get(label) is not None:
        return int(ctx.draw_int(label, lo, hi))
    if default is not None:
        return int(ctx.draw_choice(label, (int(default),)))
    return int(ctx.draw_int_diff(label, lo, hi))


def _segment_cells(segment: tuple[str, int, int, int]) -> set[tuple[int, int]]:
    orient, fixed, lo, hi = segment
    if orient == "h":
        return {(fixed, col) for col in range(lo, hi + 1)}
    return {(row, fixed) for row in range(lo, hi + 1)}


def _segment_endpoints(segment: tuple[str, int, int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    orient, fixed, lo, hi = segment
    if orient == "h":
        return (fixed, lo), (fixed, hi)
    return (lo, fixed), (hi, fixed)


def _all_segments(height: int, width: int) -> list[tuple[str, int, int, int]]:
    segments: list[tuple[str, int, int, int]] = []
    for row in range(height):
        for left in range(width - 3):
            for right in range(left + 3, width):
                segments.append(("h", row, left, right))
    for col in range(width):
        for top in range(height - 3):
            for bottom in range(top + 3, height):
                segments.append(("v", col, top, bottom))
    return segments


def _crossing_seed_segments(height: int, width: int, rng) -> list[tuple[str, int, int, int]]:
    row = rng.randint(2, height - 3)
    col = rng.randint(2, width - 3)
    horizontal = (
        "h",
        row,
        rng.randint(0, col - 2),
        rng.randint(col + 2, width - 1),
    )
    vertical = (
        "v",
        col,
        rng.randint(0, row - 2),
        rng.randint(row + 2, height - 1),
    )
    return [horizontal, vertical]


def _noncrossing_seed_segments(height: int, width: int, rng) -> list[tuple[str, int, int, int]]:
    horizontals = [segment for segment in _all_segments(height, width) if segment[0] == "h"]
    verticals = [segment for segment in _all_segments(height, width) if segment[0] == "v"]
    rng.shuffle(horizontals)
    rng.shuffle(verticals)
    for horizontal in horizontals:
        h_cells = _segment_cells(horizontal)
        h_endpoints = set(_segment_endpoints(horizontal))
        for vertical in verticals:
            v_cells = _segment_cells(vertical)
            v_endpoints = set(_segment_endpoints(vertical))
            if h_cells.isdisjoint(v_cells) and h_endpoints.isdisjoint(v_endpoints):
                return [horizontal, vertical]
    raise ValueError("could not place disjoint horizontal and vertical seed segments")


def _choose_active_segments(
    height: int,
    width: int,
    n_pairs: int,
    *,
    allow_crossing: bool,
    rng,
) -> list[tuple[str, int, int, int]]:
    chosen = (
        _crossing_seed_segments(height, width, rng)
        if allow_crossing
        else _noncrossing_seed_segments(height, width, rng)
    )
    candidates = _all_segments(height, width)
    rng.shuffle(candidates)
    for candidate in candidates:
        if len(chosen) >= n_pairs:
            break
        candidate_cells = _segment_cells(candidate)
        candidate_endpoints = set(_segment_endpoints(candidate))
        occupied_endpoints = {
            cell
            for segment in chosen
            for cell in _segment_endpoints(segment)
        }
        occupied_segment_cells = {
            cell
            for segment in chosen
            for cell in _segment_cells(segment)
        }
        # Endpoints never lie on another segment, and no new segment may pass
        # through an existing endpoint. Interior/interior crossings are lawful.
        if candidate_endpoints & occupied_segment_cells:
            continue
        if occupied_endpoints & candidate_cells:
            continue
        if not allow_crossing and candidate_cells & occupied_segment_cells:
            continue
        chosen.append(candidate)
    if len(chosen) != n_pairs:
        raise ValueError(
            f"could not place {n_pairs} active pairs in {height}x{width} grid"
        )
    return chosen


def _place_triple_decoy(
    height: int,
    width: int,
    forbidden: set[tuple[int, int]],
    rng,
) -> list[tuple[int, int]]:
    candidates: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        free_cols = [col for col in range(width) if (row, col) not in forbidden]
        for cols in combinations(free_cols, 3):
            if cols[-1] - cols[0] < 4:
                continue
            if set(range(cols[0], cols[-1] + 1)) == set(cols):
                continue
            if any((row, col) in forbidden for col in range(cols[0], cols[-1] + 1)):
                continue
            candidates.append(tuple((row, col) for col in cols))
    for col in range(width):
        free_rows = [row for row in range(height) if (row, col) not in forbidden]
        for rows in combinations(free_rows, 3):
            if rows[-1] - rows[0] < 4:
                continue
            if set(range(rows[0], rows[-1] + 1)) == set(rows):
                continue
            if any((row, col) in forbidden for row in range(rows[0], rows[-1] + 1)):
                continue
            candidates.append(tuple((row, col) for row in rows))
    if not candidates:
        raise ValueError("could not place a gapped collinear triple decoy")
    return list(rng.choice(candidates))


def _l_path(a: tuple[int, int], b: tuple[int, int]) -> set[tuple[int, int]]:
    r1, c1 = a
    r2, c2 = b
    horizontal = {(r1, col) for col in range(min(c1, c2), max(c1, c2) + 1)}
    vertical = {(row, c2) for row in range(min(r1, r2), max(r1, r2) + 1)}
    return horizontal | vertical


def _place_nonaligned_decoy(
    height: int,
    width: int,
    forbidden: set[tuple[int, int]],
    rng,
) -> list[tuple[int, int]]:
    free = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
    ]
    candidates = []
    for a, b in combinations(free, 2):
        if a[0] == b[0] or a[1] == b[1]:
            continue
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 4:
            continue
        if not (_l_path(a, b) - {a, b} - forbidden):
            continue
        candidates.append((a, b))
    if not candidates:
        raise ValueError("could not place a non-aligned pair decoy")
    return list(rng.choice(candidates))


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _positions_by_color(grid) -> tuple[list[int], dict[int, list[tuple[int, int]]]]:
    _validate_grid(grid)
    order: list[int] = []
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                continue
            if value not in positions:
                order.append(value)
                positions[value] = []
            positions[value].append((row, col))
    return order, positions


def _analyze(grid) -> tuple[dict, list[str]]:
    try:
        height, width = _validate_grid(grid)
        _order, positions = _positions_by_color(grid)
    except ValueError as exc:
        return {}, [str(exc)]

    errors: list[str] = []
    horizontal = []
    vertical = []
    nonaligned = []
    triples = []
    for color, cells in positions.items():
        if len(cells) == 2:
            (r1, c1), (r2, c2) = cells
            if r1 == r2:
                if abs(c2 - c1) < 3:
                    errors.append(f"color {color} horizontal endpoints are too close")
                horizontal.append((color, tuple(cells)))
            elif c1 == c2:
                if abs(r2 - r1) < 3:
                    errors.append(f"color {color} vertical endpoints are too close")
                vertical.append((color, tuple(cells)))
            else:
                nonaligned.append((color, tuple(cells)))
        elif len(cells) == 3:
            rows = {row for row, _col in cells}
            cols = {col for _row, col in cells}
            if len(rows) == 1:
                coords = sorted(col for _row, col in cells)
            elif len(cols) == 1:
                coords = sorted(row for row, _col in cells)
            else:
                errors.append(f"color {color} triple is not collinear")
                continue
            if coords[-1] - coords[0] < 4:
                errors.append(f"color {color} triple span is too short")
            if set(range(coords[0], coords[-1] + 1)) == set(coords):
                errors.append(f"color {color} triple is already contiguous")
            triples.append((color, tuple(cells)))
        else:
            errors.append(
                f"color {color} appears {len(cells)} times; expected an active pair or one supported decoy"
            )

    facts = {
        "grid_h": height,
        "grid_w": width,
        "positions": positions,
        "horizontal": horizontal,
        "vertical": vertical,
        "nonaligned": nonaligned,
        "triples": triples,
        "n_pairs": len(horizontal) + len(vertical),
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    facts, errors = _analyze(grid)
    if errors:
        return errors
    if not 8 <= facts["grid_h"] <= 13:
        errors.append("grid height must be 8..13")
    if not 10 <= facts["grid_w"] <= 15:
        errors.append("grid width must be 10..15")
    if not 2 <= facts["n_pairs"] <= 4:
        errors.append("grid must contain 2..4 active aligned pairs")
    if not facts["horizontal"]:
        errors.append("grid must contain a horizontal active pair")
    if not facts["vertical"]:
        errors.append("grid must contain a vertical active pair")
    if len(facts["nonaligned"]) > 1:
        errors.append("grid may contain at most one non-aligned pair decoy")
    if len(facts["triples"]) > 1:
        errors.append("grid may contain at most one triple decoy")
    if facts["nonaligned"] and facts["triples"]:
        errors.append("grid must not combine both decoy types in one scene")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {axis: int(facts[axis]) for axis in AXES}


def _paint_rule(grid, *, nonaligned_l: bool = False, any_count: bool = False):
    order, positions = _positions_by_color(grid)
    output = [row[:] for row in grid]
    for color in order:
        cells = positions[color]
        if any_count and len(cells) >= 2:
            rows = {row for row, _col in cells}
            cols = {col for _row, col in cells}
            if len(rows) == 1:
                row = next(iter(rows))
                for col in range(min(cols), max(cols) + 1):
                    output[row][col] = color
            elif len(cols) == 1:
                col = next(iter(cols))
                for row in range(min(rows), max(rows) + 1):
                    output[row][col] = color
            continue
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for col in range(min(c1, c2), max(c1, c2) + 1):
                output[r1][col] = color
        elif c1 == c2:
            for row in range(min(r1, r2), max(r1, r2) + 1):
                output[row][c1] = color
        elif nonaligned_l:
            for row, col in _l_path(cells[0], cells[1]):
                output[row][col] = color
    return output


def rule_mirror(grid):
    """Pure Python mirror used only for review probes; Racket is authoritative."""
    return _paint_rule(grid)


def _connect_non_aligned_with_l(grid):
    return _paint_rule(grid, nonaligned_l=True)


def _connect_aligned_any_count(grid):
    return _paint_rule(grid, any_count=True)


def _horizontal_only(grid):
    order, positions = _positions_by_color(grid)
    output = [row[:] for row in grid]
    for color in order:
        cells = positions[color]
        if len(cells) == 2 and cells[0][0] == cells[1][0]:
            row = cells[0][0]
            for col in range(min(cells[0][1], cells[1][1]), max(cells[0][1], cells[1][1]) + 1):
                output[row][col] = color
    return output


def _vertical_only(grid):
    order, positions = _positions_by_color(grid)
    output = [row[:] for row in grid]
    for color in order:
        cells = positions[color]
        if len(cells) == 2 and cells[0][1] == cells[1][1]:
            col = cells[0][1]
            for row in range(min(cells[0][0], cells[1][0]), max(cells[0][0], cells[1][0]) + 1):
                output[row][col] = color
    return output


def _vertical_wins_crossings(grid):
    _order, positions = _positions_by_color(grid)
    output = [row[:] for row in grid]
    for orient in ("h", "v"):
        for color, cells in positions.items():
            if len(cells) != 2:
                continue
            (r1, c1), (r2, c2) = cells
            if orient == "h" and r1 == r2:
                for col in range(min(c1, c2), max(c1, c2) + 1):
                    output[r1][col] = color
            elif orient == "v" and c1 == c2:
                for row in range(min(r1, r2), max(r1, r2) + 1):
                    output[row][c1] = color
    return output


CANONICAL_SHORTCUTS = {
    "connect_non_aligned_with_l": _connect_non_aligned_with_l,
    "connect_aligned_any_count": _connect_aligned_any_count,
}

SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "vertical_wins_crossings": _vertical_wins_crossings,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_nonaligned_pair(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["nonaligned"])


def _witness_triple(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["triples"])


def _witness_both_orientations(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["horizontal"] and facts["vertical"])


def _witness_crossing(grid) -> bool:
    facts, errors = _analyze(grid)
    if errors:
        return False
    for _hcolor, hcells in facts["horizontal"]:
        h_segment = _segment_cells(("h", hcells[0][0], min(hcells[0][1], hcells[1][1]), max(hcells[0][1], hcells[1][1])))
        h_endpoints = set(hcells)
        for _vcolor, vcells in facts["vertical"]:
            v_segment = _segment_cells(("v", vcells[0][1], min(vcells[0][0], vcells[1][0]), max(vcells[0][0], vcells[1][0])))
            if (h_segment & v_segment) - h_endpoints - set(vcells):
                return True
    return False


SEMANTIC_WITNESSES = {
    "nonaligned_pair": _witness_nonaligned_pair,
    "three_occurrence_color": _witness_triple,
    "both_orientations": _witness_both_orientations,
    "interior_crossing": _witness_crossing,
}

WITNESS_RIVALS = {
    "nonaligned_pair": ("connect_non_aligned_with_l",),
    "three_occurrence_color": ("connect_aligned_any_count",),
    "both_orientations": ("horizontal_only", "vertical_only"),
    "interior_crossing": ("vertical_wins_crossings",),
}


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts, _errors = _analyze(grid)
    if facts["nonaligned"] or facts["triples"]:
        reasons.append("canonical-profile scenes contain active aligned pairs only")
    profile = (
        facts["grid_h"],
        facts["grid_w"],
        len(facts["positions"]) + 1,
    )
    canonical_profiles = {(height, width, n_pairs + 1) for height, width, n_pairs in _CANONICAL_PROFILES}
    if profile not in canonical_profiles:
        reasons.append(f"profile {profile} is outside the four canonical profiles")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < 2:
        return ["lesson needs at least two demonstrations"]
    witness_hits = {name: 0 for name in SEMANTIC_WITNESSES}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match the pair-connector rule")
        for name, witness in SEMANTIC_WITNESSES.items():
            witness_hits[name] += int(witness(pair["input"]))
    for required in ("nonaligned_pair", "three_occurrence_color", "both_orientations", "interior_crossing"):
        if witness_hits[required] == 0:
            reasons.append(f"demonstrations lack required witness {required!r}")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos if isinstance(pair, dict) and "input" in pair and "output" in pair):
            reasons.append(f"competitor {name!r} fits every demonstration")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the pair-connector rule")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_request(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    anchor = None
    if profile == "canonical":
        anchor = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
    height = _draw_axis(ctx, "grid_h", 8, 13, anchor[0] if anchor else None, overrides)
    width = _draw_axis(ctx, "grid_w", 10, 15, anchor[1] if anchor else None, overrides)
    n_pairs = _draw_axis(ctx, "n_pairs", 2, 4, anchor[2] if anchor else None, overrides)

    layout_rng = ctx.draw_rng("layout")
    crossing = profile != "triple_decoy"
    segments = _choose_active_segments(
        height,
        width,
        n_pairs,
        allow_crossing=crossing,
        rng=layout_rng,
    )
    decoy_count = 0 if profile == "canonical" else 1
    colors = ctx.draw_distinct_colors(
        "palette",
        n=n_pairs + decoy_count,
        exclude={0},
    )

    grid = full_grid(height, width, 0)
    for color, segment in zip(colors[:n_pairs], segments):
        for row, col in _segment_endpoints(segment):
            grid[row][col] = color

    if profile != "canonical":
        forbidden = {
            cell
            for segment in segments
            for cell in _segment_cells(segment)
        }
        decoy_color = colors[-1]
        if profile == "triple_decoy":
            decoy_cells = _place_triple_decoy(height, width, forbidden, layout_rng)
        else:
            decoy_cells = _place_nonaligned_decoy(height, width, forbidden, layout_rng)
        for row, col in decoy_cells:
            grid[row][col] = decoy_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "n_pairs": n_pairs}
    if observed != expected:
        raise RuntimeError(f"internal axis observation mismatch: {observed} != {expected}")
    return grid
