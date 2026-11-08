"""Generator for arc_puzzle_bank_sixteenth21:E108 — fill equal-pair midpoints.

Every active color appears in exactly two cells.  The two cells lie in the
same row or column, exactly two positions apart, and the intervening cell is
zero.  The oracle fills that midpoint with the endpoint color.  Every draw also
contains a protected zero gap between DIFFERENT colors, alternating its axis.
The four-draw schedule teaches both positive orientations and both equality
conditions in any three demonstrations, including any query holdout of four
consecutive draws. Official-size, two-motif mixed scenes occupy half the schedule;
the other draws vary size and motif count. All non-zero ARC colors remain legal.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e2fa7e7aee7c"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "f12a9797c652"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

SUMMARY = (
    "A zero-background grid contains two to nine independent motifs. In each "
    "motif, two cells of one unique non-zero color lie exactly two cells apart "
    "in the same row or column, with a zero midpoint. The output fills every "
    "such midpoint with the matching endpoint color while preserving all "
    "endpoints. A different-color gap stays zero in every generated input/output "
    "pair. Horizontal and vertical negative gaps alternate, while positive modes "
    "cycle mixed/horizontal/vertical/mixed. Residues 0 and 3 use official-scale "
    "7x7 or 8x8 scenes with two motifs; exact overrides remain available."
)

INVARIANTS = [
    "background is 0 and every non-zero color is used by exactly one motif",
    "each motif has exactly two equal-color endpoints at orthogonal distance 2",
    "the midpoint of every motif is 0 in the input",
    "at least two motifs are present, and horizontal/vertical/mixed lessons are all supported",
    "generated draws reserve an unchanged midpoint between unequal-color endpoints",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7/8 at residues 0 and 3 modulo 4; otherwise difficulty-weighted 7..18",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 7/8 at residues 0 and 3 modulo 4; otherwise difficulty-weighted 7..18",
        "valid": "7..18",
    },
    "triples": {
        "type": "int",
        "default": "canonical 2 at residues 0 and 3 modulo 4; otherwise difficulty-weighted 2..9",
        "valid": "2..9",
    },
    "orientation_mode": {
        "type": "str",
        "default": "sample-index cycle mixed|horizontal|vertical|mixed; explicit override wins",
        "valid": "horizontal|vertical|mixed",
    },
}

_ORIENTATIONS = ("horizontal", "vertical", "mixed")
_MODE_SCHEDULE = ("mixed", "horizontal", "vertical", "mixed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule for ordinary draws; randomness changes layout, not this profile."""
    del seed, difficulty
    residue = sample_index % LESSON_SCHEDULE_PERIOD
    return (residue in (0, 3), _MODE_SCHEDULE[residue],
            "horizontal" if residue % 2 == 0 else "vertical")


SCHEDULE_PROFILES = (
    (True, "mixed", "horizontal"),
    (False, "horizontal", "vertical"),
    (False, "vertical", "horizontal"),
    (True, "mixed", "vertical"),
)


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 7, 18), ("grid_w", 7, 18), ("triples", 2, 9)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    mode = overrides.get("orientation_mode")
    if mode is not None and mode not in _ORIENTATIONS:
        raise ValueError("orientation_mode must be horizontal, vertical, or mixed")


def _weighted_values(lo: int, hi: int, difficulty) -> tuple[int, ...]:
    """Full-domain choices with a band bias; explicit boundary overrides stay legal."""
    values = list(range(lo, hi + 1))
    span = max(1, (hi - lo + 1) // 3)
    if difficulty == "easy":
        values.extend(range(lo, min(hi + 1, lo + span)))
        values.extend(range(lo, min(hi + 1, lo + span)))
    elif difficulty == "hard":
        values.extend(range(max(lo, hi - span + 1), hi + 1))
        values.extend(range(max(lo, hi - span + 1), hi + 1))
    else:
        mid = (lo + hi) // 2
        values.extend(range(max(lo, mid - 1), min(hi, mid + 1) + 1))
    return tuple(values)


def _candidate_motifs(height: int, width: int, orientation: str):
    if orientation == "horizontal":
        return [
            ((row, col), (row, col + 1), (row, col + 2))
            for row in range(height)
            for col in range(width - 2)
        ]
    return [
        ((row, col), (row + 1, col), (row + 2, col))
        for row in range(height - 2)
        for col in range(width)
    ]


def _orientation_schedule(count: int, mode: str, rng) -> tuple[str, ...]:
    if mode == "horizontal":
        return ("horizontal",) * count
    if mode == "vertical":
        return ("vertical",) * count
    horizontal_count = 1 + rng.randrange(count - 1)
    schedule = ["horizontal"] * horizontal_count
    schedule.extend(["vertical"] * (count - horizontal_count))
    rng.shuffle(schedule)
    return tuple(schedule)


def _cross_gap_partners(first, second_orientation, height, width, gap_axis):
    """Enumerate local second motifs that leave a genuine unequal-color zero gap.

    The two seeded motifs later receive distinct colors. Neither their true
    footprints nor any later footprint may occupy the reserved gap midpoint.
    Enumerating endpoint relations avoids sparse-scene rejection sampling.
    """
    sr, sc = (0, 1) if second_orientation == "horizontal" else (1, 0)
    gr, gc = (0, 1) if gap_axis == "horizontal" else (1, 0)
    first_cells = set(first)
    partners = []
    for ar, ac in (first[0], first[-1]):
        for gap_sign in (-1, 1):
            gap = (ar + gap_sign * gr, ac + gap_sign * gc)
            br, bc = ar + 2 * gap_sign * gr, ac + 2 * gap_sign * gc
            for motif_sign in (-1, 1):
                second = tuple(sorted(
                    (br + k * motif_sign * sr, bc + k * motif_sign * sc)
                    for k in range(3)
                ))
                if not all(0 <= r < height and 0 <= c < width for r, c in second):
                    continue
                if first_cells.intersection(second) or gap in first_cells or gap in second:
                    continue
                partners.append((second, gap))
    return partners


def _choose_disjoint_motifs(height: int, width: int, schedule, rng, gap_axis):
    """Exact random footprints with a protected equality witness and bounded restarts."""
    pools = {
        orientation: _candidate_motifs(height, width, orientation)
        for orientation in ("horizontal", "vertical")
    }
    indexed_schedule = list(enumerate(schedule))
    for _attempt in range(128):
        order = indexed_schedule[:]
        rng.shuffle(order)
        first_index, first_orientation = order[0]
        second_index, second_orientation = order[1]
        first = rng.choice(pools[first_orientation])
        partners = _cross_gap_partners(first, second_orientation, height, width, gap_axis)
        if not partners:
            continue
        second, reserved_gap = rng.choice(partners)
        used = set(first) | set(second) | {reserved_gap}
        chosen_by_index = {first_index: first, second_index: second}
        for original_index, orientation in order[2:]:
            candidates = pools[orientation][:]
            rng.shuffle(candidates)
            motif = next(
                (candidate for candidate in candidates if not (set(candidate) & used)),
                None,
            )
            if motif is None:
                break
            chosen_by_index[original_index] = motif
            used.update(motif)
        if len(chosen_by_index) == len(schedule):
            return [chosen_by_index[index] for index in range(len(schedule))]
    raise ValueError(
        f"cannot place {len(schedule)} disjoint {schedule!r} motifs in "
        f"a {height}x{width} grid"
    )


def _analyze(grid) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {}, ["rows must be non-empty lists or tuples"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    height = len(grid)
    if height > 30 or width > 30:
        errors.append("grid exceeds the ARC 30x30 limit")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {}, errors + ["cells must be integer ARC colors 0..9"]

    by_color: dict[int, list[tuple[int, int]]] = {}
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color:
                by_color.setdefault(color, []).append((row, col))

    orientations: list[str] = []
    midpoints: list[tuple[int, int]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times; expected exactly two endpoints")
            continue
        (row_a, col_a), (row_b, col_b) = cells
        if row_a == row_b and abs(col_a - col_b) == 2:
            orientation = "horizontal"
            midpoint = (row_a, (col_a + col_b) // 2)
        elif col_a == col_b and abs(row_a - row_b) == 2:
            orientation = "vertical"
            midpoint = ((row_a + row_b) // 2, col_a)
        else:
            errors.append(
                f"color {color} endpoints are not orthogonally separated by exactly two cells"
            )
            continue
        if grid[midpoint[0]][midpoint[1]] != 0:
            errors.append(f"color {color} midpoint {midpoint} is not zero")
        orientations.append(orientation)
        midpoints.append(midpoint)

    if len(by_color) < 2:
        errors.append(f"expected at least two motifs, found {len(by_color)}")
    if len(set(midpoints)) != len(midpoints):
        errors.append("two motifs share a midpoint")

    orientation_set = set(orientations)
    if orientation_set == {"horizontal"}:
        orientation_mode = "horizontal"
    elif orientation_set == {"vertical"}:
        orientation_mode = "vertical"
    elif orientation_set == {"horizontal", "vertical"}:
        orientation_mode = "mixed"
    else:
        orientation_mode = "invalid"

    features: dict[str, object] = {
        "grid_h": height,
        "grid_w": width,
        "triples": len(by_color),
        "orientation_mode": orientation_mode,
        "colors": tuple(sorted(by_color)),
        "midpoints": tuple(sorted(midpoints)),
        "orientation_counts": dict(Counter(orientations)),
    }
    return features, errors


def observe_overrides(grid) -> dict[str, int | str]:
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe invalid midpoint lesson: " + "; ".join(errors))
    return {
        "grid_h": int(features["grid_h"]),
        "grid_w": int(features["grid_w"]),
        "triples": int(features["triples"]),
        "orientation_mode": str(features["orientation_mode"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _features, errors = _analyze(grid)
    return errors


def _apply_rule_mirror(grid):
    """Test-only mirror; the canonical Racket rule remains output authority."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width - 2):
            left, middle, right = grid[row][col:col + 3]
            if left != 0 and left == right and middle == 0:
                output[row][col + 1] = left
    for row in range(height - 2):
        for col in range(width):
            top, middle, bottom = grid[row][col], grid[row + 1][col], grid[row + 2][col]
            if top != 0 and top == bottom and middle == 0:
                output[row + 1][col] = top
    return output


def strict_canonical_like(grid):
    """The lawful independent-pair manifold, including unchanged canonical inputs."""
    return self_check(grid)


def _false_gap_midpoints(grid, axis):
    """Unequal-color gaps whose cells stay zero under the intended rule.

    A raw x-0-y pattern can coincide with a third motif's actual midpoint;
    that is not a counterexample demonstrating that the cell stays empty.
    """
    features, errors = _analyze(grid)
    if errors:
        return ()
    true_midpoints = set(features["midpoints"])
    dr, dc = (0, 1) if axis == "horizontal" else (1, 0)
    result = []
    for r in range(len(grid) - 2 * dr):
        for c in range(len(grid[0]) - 2 * dc):
            a, b = grid[r][c], grid[r + 2 * dr][c + 2 * dc]
            midpoint = (r + dr, c + dc)
            if (a and b and a != b and grid[midpoint[0]][midpoint[1]] == 0
                    and midpoint not in true_midpoints):
                result.append(midpoint)
    return tuple(result)


def _gap_rival(grid, *, axes=("horizontal", "vertical"), blind_axes=()):
    """Declared competitor only; authoritative training labels come from Racket."""
    output = [list(row) for row in grid]
    for axis in axes:
        dr, dc = (0, 1) if axis == "horizontal" else (1, 0)
        for r in range(len(grid) - 2 * dr):
            for c in range(len(grid[0]) - 2 * dc):
                a, b = grid[r][c], grid[r + 2 * dr][c + 2 * dc]
                if (a and b and grid[r + dr][c + dc] == 0
                        and (a == b or axis in blind_axes)):
                    output[r + dr][c + dc] = a
    return output


def _color_blind(grid):
    return _gap_rival(grid, blind_axes=("horizontal", "vertical"))


def _horizontal_color_blind(grid):
    return _gap_rival(grid, blind_axes=("horizontal",))


def _vertical_color_blind(grid):
    return _gap_rival(grid, blind_axes=("vertical",))


def _horizontal_only(grid):
    return _gap_rival(grid, axes=("horizontal",))


def _vertical_only(grid):
    return _gap_rival(grid, axes=("vertical",))


def _has_horizontal_false_gap(grid):
    return bool(_false_gap_midpoints(grid, "horizontal"))


def _has_vertical_false_gap(grid):
    return bool(_false_gap_midpoints(grid, "vertical"))


def _has_horizontal_motif(grid):
    features, errors = _analyze(grid)
    return not errors and features["orientation_counts"].get("horizontal", 0) > 0


def _has_vertical_motif(grid):
    features, errors = _analyze(grid)
    return not errors and features["orientation_counts"].get("vertical", 0) > 0


SEMANTIC_RIVALS = {
    "color_blind": _color_blind,
    "horizontal_color_blind": _horizontal_color_blind,
    "vertical_color_blind": _vertical_color_blind,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
}
SEMANTIC_WITNESSES = {
    "horizontal_unequal_gap_stays_zero": _has_horizontal_false_gap,
    "vertical_unequal_gap_stays_zero": _has_vertical_false_gap,
    "horizontal_equal_gap_is_filled": _has_horizontal_motif,
    "vertical_equal_gap_is_filled": _has_vertical_motif,
}
WITNESS_RIVALS = {
    "horizontal_unequal_gap_stays_zero": ["color_blind", "horizontal_color_blind"],
    "vertical_unequal_gap_stays_zero": ["color_blind", "vertical_color_blind"],
    "horizontal_equal_gap_is_filled": ["vertical_only"],
    "vertical_equal_gap_is_filled": ["horizontal_only"],
}
CANONICAL_SHORTCUTS = {
    "color_blind": _color_blind,
    "horizontal_color_blind": _horizontal_color_blind,
    "vertical_color_blind": _vertical_color_blind,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject actual named-rival ambiguity; agreement everywhere is not a defect.

    This also checks custom or rejection-altered assemblies against their supplied
    authoritative labels. The finite rival family is not a universal proof.
    """
    return [
        f"{name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]


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
    rng = ctx.draw_rng("layout")

    canonical_profile = not overrides and sample_index % 4 in (0, 3)
    if canonical_profile:
        size = ctx.draw_choice("canonical_size", (7, 8))
        height = ctx.draw_choice("grid_h", (size,))
        width = ctx.draw_choice("grid_w", (size,))
        motif_count = ctx.draw_choice("triples", (2,))
        orientation_mode = ctx.draw_choice("orientation_mode", ("mixed",))
    else:
        height = ctx.draw_choice("grid_h", _weighted_values(7, 18, difficulty))
        width = ctx.draw_choice("grid_w", _weighted_values(7, 18, difficulty))
        motif_count = ctx.draw_choice("triples", _weighted_values(2, 9, difficulty))
        mode_options = (_ORIENTATIONS if overrides.get("orientation_mode") is not None
                        else (_MODE_SCHEDULE[sample_index % 4],))
        orientation_mode = ctx.draw_choice("orientation_mode", mode_options)

    schedule = _orientation_schedule(motif_count, orientation_mode, rng)
    gap_axis = "horizontal" if sample_index % 2 == 0 else "vertical"
    motifs = _choose_disjoint_motifs(height, width, schedule, rng, gap_axis)
    colors = ctx.draw_distinct_colors("colors", n=motif_count, exclude=(0,))

    grid = full_grid(height, width, 0)
    for color, motif in zip(colors, motifs):
        first, _midpoint, last = motif
        grid[first[0]][first[1]] = color
        grid[last[0]][last[1]] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid midpoint lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "triples": motif_count,
        "orientation_mode": orientation_mode,
    }
    if observed != expected:
        raise AssertionError(f"axis provenance mismatch: expected {expected}, observed {observed}")
    if _apply_rule_mirror(grid) == grid:
        raise AssertionError("constructed a no-op midpoint lesson")
    if not _false_gap_midpoints(grid, gap_axis):
        raise AssertionError("constructed lesson lost its protected unequal-color gap")
    return grid
