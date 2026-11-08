"""Marker-count crop + rotation, with observable C4 witnesses.

Labels remain the unchanged canonical Racket program's responsibility. This
module generates inputs and exposes falsifiable, task-local review hooks.
Version 3 removes the old ignored texture/count aliases: unknown keys fail.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "ffcd7510821d"
VERSION = "3.0.0"
RULE_HASH = "77da9e97370c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Count only row-0 maroon (9) cells, remove only those cells, crop the "
    "remaining scene and rotate clockwise by count modulo four. Default "
    "four-example windows cover counts 1, 2, 3, 4. One to four separated, "
    "distinct-color nonrectangular blobs have four different whole-scene "
    "rotations; canonical-scale single objects remain present in every band."
)
INVARIANTS = [
    "rectangular integer-color grid, height 7..14 and width 8..14",
    "background is 0; row 0 has only 0 and 9; row 1 is blank",
    "row-0 marker count is 1..4 by default, or 0..4 by explicit override",
    "all content is in rows 2+, colors 1..8; no off-row maroon is generated",
    "1..4 distinct content colors, each one 4-connected nonrectangular blob",
    "the whole content crop has four pairwise distinct quarter-turn rotations",
]
AXES = {
    "grid_h": {"type": "int", "default": "band-aware with canonical-scale anchors",
               "valid": "7..14"},
    "grid_w": {"type": "int", "default": "band-aware with canonical-scale anchors",
               "valid": "8..14"},
    "n_markers": {"type": "int", "default": "scheduled 1..4", "valid": "0..4"},
    "n_blobs": {"type": "int", "default": "scheduled single/multiple, 1..4", "valid": "1..4"},
    "palette_kind": {"type": "str", "default": "varied", "valid": "warm|cool|varied",
                     "doc": "Sampling support, not an exact palette-size axis."},
}
_PALETTES = {"warm": (2, 4, 6, 7), "cool": (1, 3, 5, 8), "varied": tuple(range(1, 9))}
_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Any four consecutive indexes, at a fixed seed, cover all residues."""
    del difficulty
    return (2 * int(seed) + int(sample_index)) % 4


def _rotate(grid, turns):
    result = [row[:] for row in grid]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _freeze(grid):
    return tuple(map(tuple, grid))


def _crop(grid, *, selected_color=None):
    # The rule clears ROW-0 9s only. A 9 elsewhere would remain content;
    # generation/self_check explicitly exclude that extension of the domain.
    clean = [[0 if r == 0 and value == 9 else value for value in row]
             for r, row in enumerate(grid)]
    if selected_color is not None:
        clean = [[value if value == selected_color else 0 for value in row] for row in clean]
    points = [(r, c) for r, row in enumerate(clean) for c, value in enumerate(row) if value]
    if not points:
        raise ValueError("no content to crop")
    r0, r1 = min(r for r, c in points), max(r for r, c in points)
    c0, c1 = min(c for r, c in points), max(c for r, c in points)
    return [row[c0:c1 + 1] for row in clean[r0:r1 + 1]]


def _orbit_size(grid):
    return len({_freeze(_rotate(grid, turns)) for turns in range(4)})


def _shape_error(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return "grid must be a nonempty list of rows"
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return "grid must be nonempty and rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid values must be integer colors 0..9 (not bool)"
    return None


def _colors(grid):
    return sorted({value for row in grid for value in row} - {0, 9})


def self_check(grid, *, difficulty=None, meta=None):
    """Structural domain plus exact observability; metadata cannot bypass it."""
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]
    errors = []
    if not (7 <= len(grid) <= 14 and 8 <= len(grid[0]) <= 14):
        errors.append("dimensions outside height 7..14 / width 8..14")
    if any(value not in (0, 9) for value in grid[0]):
        errors.append("row 0 must contain only background and markers")
    if grid[0].count(9) > 4:
        errors.append("row 0 must contain 0..4 markers")
    if len(grid) < 2 or any(grid[1]):
        errors.append("row 1 must be blank")
    if any(9 in row for row in grid[1:]):
        errors.append("off-row maroon is outside the documented generator domain")
    by_color = defaultdict(set)
    for r, row in enumerate(grid[2:], 2):
        for c, value in enumerate(row):
            if value not in (0, 9):
                by_color[value].add((r, c))
    if not 1 <= len(by_color) <= 4:
        errors.append("expected 1..4 content colors/blobs")
    for color, cells in by_color.items():
        start = min(cells)
        seen, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in _DIR4:
                neighbor = (r + dr, c + dc)
                if neighbor in cells and neighbor not in seen:
                    seen.add(neighbor)
                    todo.append(neighbor)
        if seen != cells:
            errors.append(f"content color {color} is disconnected")
        height = max(r for r, c in cells) - min(r for r, c in cells) + 1
        width = max(c for r, c in cells) - min(c for r, c in cells) + 1
        if height * width == len(cells):
            errors.append(f"content color {color} is rectangular")
    if by_color and _orbit_size(_crop(grid)) != 4:
        errors.append("content is rotationally ambiguous: fewer than four distinct rotations")
    return errors


def _draw_exact_int(ctx, name, default, low, high):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default, default)


def _slots(height, width, count, rng):
    """Separated slots guarantee exact cardinality even at 7x8 / four blobs."""
    if count == 1:
        return [(2, 0, height - 2, width)]
    body_h = height - 2
    if count == 2 and rng.randrange(2):
        left = (width - 1) // 2
        return [(2, 0, body_h, left), (2, left + 1, body_h, width - left - 1)]
    if count == 2:
        top = (body_h - 1) // 2
        return [(2, 0, top, width), (3 + top, 0, body_h - top - 1, width)]
    top, left = (body_h - 1) // 2, (width - 1) // 2
    slots = [(2, 0, top, left), (2, left + 1, top, width - left - 1),
             (3 + top, 0, body_h - top - 1, left),
             (3 + top, left + 1, body_h - top - 1, width - left - 1)]
    rng.shuffle(slots)
    return slots[:count]


def _blob(rng, height, width, target):
    """Uniform frontier choices avoid a fixed directional walk bias.

    Bounded rejection is only for shape morphology, never for blob count.
    A randomly oriented L triomino is the explicit fitting fallback.
    """
    target = max(3, min(target, height * width - 1))
    for _ in range(32):
        cells = {(rng.randrange(height), rng.randrange(width))}
        while len(cells) < target:
            frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _DIR4
                               if 0 <= r + dr < height and 0 <= c + dc < width} - cells)
            cells.add(rng.choice(frontier))
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        if (r1 - r0 + 1) * (c1 - c0 + 1) > len(cells):
            return {(r-r0, c-c0) for r, c in cells}
    missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
    return {(r, c) for r in range(2) for c in range(2)} - {missing}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown or removed override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "n_markers", "n_blobs"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, not a coercible value")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    single = (profile + int(seed) // 4) % 2 == 0
    axis_rng = ctx.draw_rng("default_axes")
    if single:
        # Canonical dimensions have substantial support in EVERY difficulty.
        default_h, default_w = axis_rng.randint(8, 9), axis_rng.randint(9, 12)
        default_blobs = 1
    else:
        band = difficulty or "medium"
        lo = {"easy": 7, "medium": 9, "hard": 11}[band]
        default_h, default_w = axis_rng.randint(lo, 14), axis_rng.randint(max(8, lo), 14)
        default_blobs = axis_rng.randint(2, 4)
    height = _draw_exact_int(ctx, "grid_h", default_h, 7, 14)
    width = _draw_exact_int(ctx, "grid_w", default_w, 8, 14)
    markers = _draw_exact_int(ctx, "n_markers", profile + 1, 0, 4)
    count = _draw_exact_int(ctx, "n_blobs", default_blobs, 1, 4)
    palette = (ctx.draw_choice("palette_kind", tuple(_PALETTES))
               if overrides.get("palette_kind") is not None
               else ctx.draw_choice("palette_kind", ("varied",)))
    rng = ctx.draw_rng("layout")
    colors = rng.sample(_PALETTES[palette], count)
    target_lo, target_hi = {"easy": (3, 6), "medium": (4, 9), "hard": (5, 12)}[difficulty or "medium"]
    # Reject a symmetric SCENE, not merely a filled rectangular bounding box.
    for attempt in range(64):
        grid = full_grid(height, width, 0)
        for column in rng.sample(range(width), markers):
            grid[0][column] = 9
        for color, (r0, c0, slot_h, slot_w) in zip(colors, _slots(height, width, count, rng)):
            cells = _blob(rng, slot_h, slot_w, rng.randint(target_lo, target_hi))
            if attempt == 63:  # Guaranteed asymmetric fallback, same exact axes.
                missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
                cells = {(r, c) for r in range(2) for c in range(2)} - {missing}
            bh = max(r for r, c in cells) + 1
            bw = max(c for r, c in cells) + 1
            ro, co = r0 + rng.randrange(slot_h - bh + 1), c0 + rng.randrange(slot_w - bw + 1)
            for r, c in cells:
                grid[ro+r][co+c] = color
        if _orbit_size(_crop(grid)) == 4:
            errors = self_check(grid)
            if errors:
                raise AssertionError("constructed invalid scene: " + "; ".join(errors))
            return grid
    raise AssertionError("asymmetric fallback failed")


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_markers": grid[0].count(9), "n_blobs": len(_colors(grid))}


def strict_canonical_like(grid):
    """Same marker/crop grammar; not a claim of exact canonical morphology."""
    return self_check(grid)


def rule_mirror(grid):
    """Review-only cross-check. Never used by the data pipeline to create labels."""
    return _rotate(_crop(grid), grid[0].count(9))


def _fixed_turns(turns):
    return lambda grid: _rotate(_crop(grid), turns)


def _largest_only(grid):
    counts = {color: sum(row.count(color) for row in grid) for color in _colors(grid)}
    color = max(counts, key=lambda value: (counts[value], -value))
    return _rotate(_crop(grid, selected_color=color), grid[0].count(9))


SEMANTIC_RIVALS = {
    "crop_only": _fixed_turns(0),
    "always_clockwise": _fixed_turns(1),
    "always_half_turn": _fixed_turns(2),
    "always_counterclockwise": _fixed_turns(3),
    "reverse_direction": lambda grid: _rotate(_crop(grid), -grid[0].count(9)),
    "count_content_colors": lambda grid: _rotate(_crop(grid), len(_colors(grid))),
    "largest_blob_only": _largest_only,
}
SEMANTIC_WITNESSES = {
    "zero_turns": lambda grid: grid[0].count(9) == 4,
    "one_turn": lambda grid: grid[0].count(9) == 1,
    "two_turns": lambda grid: grid[0].count(9) == 2,
    "three_turns": lambda grid: grid[0].count(9) == 3,
    "multiple_blobs": lambda grid: len(_colors(grid)) > 1,
}
WITNESS_RIVALS = {
    "zero_turns": ["always_clockwise"], "one_turn": ["crop_only"],
    "two_turns": ["crop_only"], "three_turns": ["reverse_direction"],
    "multiple_blobs": ["largest_blob_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"largest_blob_only": _largest_only}


def lesson_identifiable(demos, query):
    """Finite rotation-table version space plus the named non-table rivals.

    This is relative identifiability, not proof against arbitrary programs.
    A branch needs a demo unless every surviving choice gives the same query
    output. Malformed or incorrect labels are errors, not counterexamples.
    """
    possible = {residue: set(range(4)) for residue in range(4)}
    errors = []
    for index, demo in enumerate(demos):
        grid = demo["input"]
        if self_check(grid):
            errors.append(f"demo {index} is outside the generator domain")
            continue
        if demo.get("output") != rule_mirror(grid):
            errors.append(f"demo {index} disagrees with the crop/clockwise rule")
        body = _crop(grid)
        possible[grid[0].count(9) % 4] &= {
            turns for turns in range(4) if _rotate(body, turns) == demo.get("output")}
    grid = query["input"]
    if self_check(grid):
        return errors + ["query is outside the generator domain"]
    expected = rule_mirror(grid)
    if query.get("output") is not None and query["output"] != expected:
        errors.append("query label disagrees with the crop/clockwise rule")
    answers = {_freeze(_rotate(_crop(grid), turns)) for turns in possible[grid[0].count(9) % 4]}
    if len(answers) != 1:
        errors.append(f"query marker class allows {len(answers)} different rotation-table answers")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo.get("output") for demo in demos) and rival(grid) != expected:
            errors.append(f"rival {name} fits demos but changes the query answer")
    return errors


def mutation_fixtures():
    good = generate(17, 0)
    blank = full_grid(len(good), len(good[0]), 0)
    bad_marker = deepcopy(good)
    bad_marker[1][0] = 9
    wrong_color = deepcopy(good)
    wrong_color[0][0] = 8
    square = full_grid(8, 10, 0)
    square[0][0] = 9
    for r, c in [(3, 4), (4, 3), (4, 4), (4, 5), (5, 4)]:
        square[r][c] = 3
    return [("empty_content", blank), ("off_row_marker", bad_marker),
            ("content_in_marker_row", wrong_color), ("symmetric_plus", square),
            ("invalid_color", [[10]]), ("empty_row", [[]])]
