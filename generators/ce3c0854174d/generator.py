"""Cumulative transform timelines with executable symbol and lesson checks.

Labels remain the selected Racket rule's responsibility. The Python gallery
interpreter is a diagnostic used by rival checks, not label authority.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce3c0854174d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "442270b293a4"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A zero-background grid has a contiguous row-0 script and one connected, "
    "single-color template below a blank separator row. The fixed script "
    "legend is 1=clockwise quarter-turn, 2=half-turn, 3=left-right reflection, "
    "4=transpose. Apply codes cumulatively to the current cropped template. "
    "Pack the resulting states left-to-right, top-aligned, with one blank "
    "column between states. Codes 5..7 supported by Racket are outside this "
    "sampler's declared 1..4 vocabulary. Templates use colors 5..9. Default "
    "three-demo lessons interleave asymmetric full-legend witnesses with "
    "canonical-profile and symmetric/rectangular examples."
)

INVARIANTS = [
    "background is 0; all cells are integer colors 0..9",
    "row 0 has 2..5 codes from 1..4, contiguous from the left, then zeros",
    "row 1 is blank; one connected monochrome template of color 5..9 is below it",
]
AXES = {
    "height": {"type": "int", "default": "mixture 7..12", "valid": "7..12"},
    "width": {"type": "int", "default": "mixture 10..16", "valid": "10..16"},
    "script_len": {"type": "int", "default": "curriculum 3..5", "valid": "2..5"},
}

TRANSFORM_CODES = {1: "cw90", 2: "half_turn", 3: "flip_lr", 4: "transpose"}
DIHEDRAL_OPERATIONS = (
    "identity", "cw90", "half_turn", "ccw90", "flip_lr", "flip_ud",
    "transpose", "anti_transpose",
)
SHAPES = [
    [(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
]


def _transform(grid, operation):
    if operation == "identity":
        return [list(row) for row in grid]
    if operation == "cw90":
        return [list(row) for row in zip(*grid[::-1])]
    if operation == "half_turn":
        return [list(reversed(row)) for row in reversed(grid)]
    if operation == "ccw90":
        return [list(row) for row in zip(*grid)][::-1]
    if operation == "flip_lr":
        return [list(reversed(row)) for row in grid]
    if operation == "flip_ud":
        return [list(row) for row in reversed(grid)]
    if operation == "transpose":
        return [list(row) for row in zip(*grid)]
    if operation == "anti_transpose":
        return _transform(_transform(grid, "transpose"), "half_turn")
    raise ValueError(f"unknown transform operation: {operation}")


def _template(grid):
    cells = [(r, c) for r in range(1, len(grid))
             for c, value in enumerate(grid[r]) if value != 0]
    if not cells:
        raise ValueError("missing template")
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def _pack(states):
    height = max(len(state) for state in states)
    width = sum(len(state[0]) for state in states) + len(states) - 1
    out = full_grid(height, width, 0)
    left = 0
    for state in states:
        for r, row in enumerate(state):
            out[r][left:left + len(row)] = row
        left += len(state[0]) + 1
    return out


def predict_gallery(grid, *, mapping=None, cumulative=True):
    """Python diagnostic; every training label is still executed in Racket."""
    legend = TRANSFORM_CODES if mapping is None else mapping
    start = _template(grid)
    current = start
    states = []
    for code in (value for value in grid[0] if value != 0):
        current = _transform(current if cumulative else start, legend[code])
        states.append(current)
    if not states:
        raise ValueError("missing script")
    return _pack(states)


def _asymmetric(template):
    orbit = {tuple(tuple(row) for row in _transform(template, op))
             for op in DIHEDRAL_OPERATIONS}
    return len(orbit) == 8


def _shape_grid(cells):
    shape = full_grid(max(r for r, _ in cells) + 1,
                      max(c for _, c in cells) + 1, 0)
    for r, c in cells:
        shape[r][c] = 1
    return shape


def _draw_axis(ctx, name, lo, hi, default):
    # Exact overrides are never clamped, coerced, or narrowed by a default band.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    witness = sample_index % 2 == 0
    profile = ctx.draw_choice("canonical_profile", ((9, 12, 3), (10, 14, 2), (9, 13, 3)))
    default_h = ctx.draw_int_diff("broad_height", 7, 12) if witness else profile[0]
    default_w = ctx.draw_int_diff("broad_width", 10, 16) if witness else profile[1]
    default_len = (5 if difficulty == "hard" else 4) if witness else (
        3 if difficulty == "easy" else (rng.choice((4, 5)) if difficulty == "hard"
                                       else rng.choice((3, 4))))
    h = _draw_axis(ctx, "height", 7, 12, default_h)
    w = _draw_axis(ctx, "width", 10, 16, default_w)
    length = _draw_axis(ctx, "script_len", 2, 5, default_len)
    # Four consecutive default draws contain two full-legend witnesses.
    # Holding out any one therefore leaves a complete symbol demonstration.
    vocabulary = list(TRANSFORM_CODES) if witness else rng.sample(
        list(TRANSFORM_CODES), min(length, profile[2]))
    rng.shuffle(vocabulary)
    script = vocabulary[:length]
    script.extend(rng.choice(vocabulary) for _ in range(length - len(script)))
    rng.shuffle(script)
    shapes = [_shape_grid(cells) for cells in SHAPES]
    candidates = [shape for shape in shapes if _asymmetric(shape)] if witness else shapes
    template = _transform(rng.choice(candidates), rng.choice(DIHEDRAL_OPERATIONS))
    top = rng.randint(2, h - len(template))
    left = rng.randint(0, w - len(template[0]))
    color = rng.choice((5, 6, 7, 8, 9))
    out = full_grid(h, w, 0)
    out[0][:length] = script
    for r, row in enumerate(template):
        for c, value in enumerate(row):
            if value:
                out[top + r][left + c] = color
    return out


def observe_overrides(grid):
    return {"height": len(grid), "width": len(grid[0]),
            "script_len": sum(value != 0 for value in grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or len(grid) < 3
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty grid with script, separator, and template rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9; bool/float/string are not colors"]
    script = [value for value in grid[0] if value != 0]
    errors = []
    if not 2 <= len(script) <= 5 or any(value not in TRANSFORM_CODES for value in script):
        errors.append("script must have 2..5 codes from 1..4")
    if list(grid[0]) != script + [0] * (width - len(script)):
        errors.append("script must be contiguous from column 0, followed by zeros")
    if any(grid[1]):
        errors.append("row 1 must separate script and template")
    cells = {(r, c) for r in range(2, len(grid)) for c, value in enumerate(grid[r]) if value != 0}
    if not cells:
        errors.append("missing template")
        return errors
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1 or not colors <= {5, 6, 7, 8, 9}:
        errors.append("template must have one color from 5..9")
    start = min(cells)
    seen, pending = {start}, [start]
    while pending:
        r, c = pending.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                pending.append(point)
    if seen != cells:
        errors.append("template must be one four-connected object")
    return errors


def strict_canonical_like(grid):
    """Task-domain structure; exact size/palette support is checked separately."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def _substitute_code(grid, *, code, operation):
    return predict_gallery(grid, mapping={**TRANSFORM_CODES, code: operation})


SEMANTIC_RIVALS = {
    f"code_{code}_as_{operation}": partial(_substitute_code, code=code, operation=operation)
    for code, correct in TRANSFORM_CODES.items()
    for operation in DIHEDRAL_OPERATIONS if operation != correct
}
SEMANTIC_RIVALS["independent_not_cumulative"] = partial(predict_gallery, cumulative=False)
SEMANTIC_RIVALS["old_summary_legend"] = partial(
    predict_gallery, mapping={1: "identity", 2: "cw90", 3: "half_turn", 4: "ccw90"})
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _code_witness(grid, *, code):
    return code in grid[0] and _asymmetric(_template(grid))


def _cumulative_witness(grid):
    return predict_gallery(grid) != predict_gallery(grid, cumulative=False)


SEMANTIC_WITNESSES = {
    f"symbol_{code}": partial(_code_witness, code=code) for code in TRANSFORM_CODES
}
SEMANTIC_WITNESSES["sequential_state"] = _cumulative_witness
WITNESS_RIVALS = {
    f"symbol_{code}": [name for name in SEMANTIC_RIVALS if name.startswith(f"code_{code}_as_")]
    for code in TRANSFORM_CODES
}
WITNESS_RIVALS["sequential_state"] = ["independent_not_cumulative"]


def lesson_identifiable(demos, query):
    """Finite rival check, not a uniqueness proof; consumes supplied labels."""
    expected = query.get("output")
    if expected is None:
        return ["query label is required for the authoring identifiability check"]
    return [f"rival {name} fits every demo but differs on the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != expected]


SCHEDULE_PROFILES = ("full_legend_witness", "canonical_and_broad_template")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]
