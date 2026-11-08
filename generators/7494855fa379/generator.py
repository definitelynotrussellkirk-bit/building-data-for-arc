"""Inputs for the fixed yellow-ring predicate; Racket remains label authority.

A zero cell becomes 6 exactly when all eight neighbors are 4. The ordinary
two-position curriculum alternates canonical-size positive examples with rich
contrast examples. Each contrast contains positive rings, a missing-corner
near miss, a monochrome non-yellow ring, and an occupied yellow-ring center.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "7494855fa379"
RULE_HASH = "856baaecfaa1"
VERSION = "3.2.0"
SUMMARY = (
    "Fill only zero centers with eight color-4 neighbors using fixed color 6. "
    "Generate separated 3x3 motifs at varied positions, including edge positions. "
    "Canonical-size positive cases alternate with multiple targets and three "
    "unchanged distractors: missing corner, non-yellow ring, and occupied center. "
    "Exact dimensions and positive-ring counts are honored or explicitly refused."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_core", "contrast")
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES = ("default", "contrast")
DEGENERATE_TEXTURES = ("no_blocks", "solid_squares", "center_already_filled")
# Occupied rings are lawful no-action boundaries. A blank grid is a negative
# fixture outside this sampler's nonempty motif grammar, though the rule is total.
LAWFUL_DEGENERATE_TEXTURES = ("solid_squares", "center_already_filled")
INVARIANTS = [
    "the sampler domain contains separated 3x3 motifs on background 0; difficulty is not validity",
    "ordinary draws contain 1..6 positive yellow rings with eight 4s and a zero center",
    "unoverridden contrast draws contain at least two targets and all three counterexamples",
    "motifs are separate under four-connectivity; diagonal contacts, positions and colors vary",
    "ordinary draws alternate canonical-size/palette cases and comprehensive contrasts",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled and difficulty-weighted", "valid": "4..18"},
    "grid_w": {"type": "int", "default": "scheduled and difficulty-weighted", "valid": "5..20"},
    "n_blocks": {"type": "int", "default": "1..2 core, 2 contrast, subject to space", "valid": "1..6"},
    "texture": {"type": "str", "default": "alternating default and contrast",
                "valid": "default|contrast|solid_squares|center_already_filled"},
}
# Geometry refusals carry the actual requested axes on their exception.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [{"texture": DEGENERATE_TEXTURES, "n_blocks": None}]
_BOUNDS = {"grid_h": (4, 18), "grid_w": (5, 20), "n_blocks": (1, 6)}
_NEIGHBORS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
_CORNERS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CANONICAL_SHAPES = ((5, 7), (8, 8), (9, 9))


def schedule_profile(seed, sample_index, difficulty=None):
    return "canonical_core" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "contrast"


def _validate_request(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _BOUNDS:
            lo, hi = _BOUNDS[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        elif not isinstance(value, str) or value not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture: {value!r}")


def _incompatible(overrides, reason):
    axes = tuple(sorted(name for name, value in overrides.items() if value is not None))
    error = ValueError(f"incompatible overrides {axes}: {reason}")
    error.incompatible_axes = axes
    raise error


def _capacity(height, width):
    """Largest count in the two supported layout families, not a packing theorem."""
    spaced = ((height + 1) // 4) * ((width + 1) // 4)
    # Alternate tiles of a 3-cell lattice can touch diagonally but never share
    # a cardinal edge. This includes canonical train[1], 6x9/3, and 9x9/5.
    checkerboard = ((height // 3) * (width // 3) + 1) // 2
    return max(spaced, checkerboard)


def _weighted(values, favored):
    values = list(values)
    return values + [value for value in favored if value in values] * 5


def _shape(ctx, overrides, needed, *, core=False):
    height = overrides.get("grid_h")
    width = overrides.get("grid_w")
    canonical = [shape for shape in _CANONICAL_SHAPES if _capacity(*shape) >= needed]
    if core and height is None and width is None and canonical:
        h, w = ctx.draw_choice("canonical_shape", canonical)
        return ctx.draw_choice("grid_h", (h,)), ctx.draw_choice("grid_w", (w,))
    heights = [h for h in range(4, 19) if _capacity(h, width or 20) >= needed]
    if height is not None and height not in heights:
        _incompatible(overrides, f"supported grid_h/grid_w layouts have fewer than {needed} motif slots")
    if not heights:
        _incompatible(overrides, f"supported grid_w layouts have fewer than {needed} motif slots")
    favored_h = range(5, 9) if ctx.difficulty == "easy" else range(11, 19) if ctx.difficulty == "hard" else range(7, 13)
    h = ctx.draw_choice("grid_h", _weighted(heights, favored_h))
    widths = [w for w in range(5, 21) if _capacity(h, w) >= needed]
    favored_w = range(7, 12) if ctx.difficulty == "easy" else range(13, 21) if ctx.difficulty == "hard" else range(9, 15)
    w = ctx.draw_choice("grid_w", _weighted(widths, favored_w))
    return h, w


def _starts(length, count, rng):
    """Ordered 3-cell intervals with a real gap and randomized spare space."""
    slack = length - (4 * count - 1)
    offsets = sorted(rng.randint(0, slack) for _ in range(count))
    return [4 * index + offset for index, offset in enumerate(offsets)]


def _positions(height, width, count, rng):
    tilings = [(nr, nc) for nr in range(1, (height + 1) // 4 + 1)
               for nc in range(1, (width + 1) // 4 + 1) if nr * nc >= count]
    rows, columns = height // 3, width // 3
    checkers = [[(3 * r, 3 * c) for r in range(rows) for c in range(columns)
                 if (r + c) % 2 == parity] for parity in (0, 1)]
    checkers = [slots for slots in checkers if len(slots) >= count]
    if checkers and (not tilings or rng.choice((False, True))):
        top, left = rng.randint(0, height - 3 * rows), rng.randint(0, width - 3 * columns)
        return [(top + r, left + c) for r, c in rng.sample(rng.choice(checkers), count)]
    nr, nc = rng.choice(tilings)
    slots = [(r, c) for r in _starts(height, nr, rng) for c in _starts(width, nc, rng)]
    return rng.sample(slots, count)


def _put_ring(grid, origin, color=4, center=0, missing=None):
    r0, c0 = origin
    for dr, dc in _NEIGHBORS:
        if (dr, dc) != missing:
            grid[r0 + 1 + dr][c0 + 1 + dc] = color
    grid[r0 + 1][c0 + 1] = center


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    # Explicit geometry/count requests take precedence over the automatic
    # lesson schedule. Request texture='contrast' to pin its extra motifs too.
    controlled = any(overrides.get(name) is not None for name in _BOUNDS)
    scheduled = "default" if profile == "canonical_core" or controlled else "contrast"
    options = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") is not None else (scheduled,)
    texture = ctx.draw_choice("texture", options)
    if texture in DEGENERATE_TEXTURES:
        if overrides.get("n_blocks") is not None:
            _incompatible(overrides, "n_blocks counts positive rings, but this texture has zero")
        h, w = _shape(ctx, overrides, 1, core=True)
        grid = full_grid(h, w, 0)
        if texture != "no_blocks":
            origin = _positions(h, w, 1, ctx.draw_rng("layout"))[0]
            _put_ring(grid, origin, center=4 if texture == "solid_squares" else 8)
        return grid
    extra = 3 if texture == "contrast" else 0
    max_capacity = _capacity(overrides.get("grid_h") or 18, overrides.get("grid_w") or 20)
    counts = [n for n in range(1, 7) if n + extra <= max_capacity]
    requested_count = overrides.get("n_blocks")
    if not counts or (requested_count is not None and requested_count not in counts):
        _incompatible(overrides, f"supported grid_h/grid_w layouts offer {max_capacity} slots for n_blocks plus {extra} distractors")
    if requested_count is None:
        if texture == "default" and all(overrides.get(k) is None for k in _BOUNDS):
            counts = [n for n in counts if n <= 2]
        elif texture == "contrast" and any(n >= 2 for n in counts):
            # Two positives already teach 'all targets'. More duplicate positives
            # add morphology drift without another predicate distinction.
            counts = [2]
    favored_n = (1, 2) if difficulty == "easy" else (4, 5, 6) if difficulty == "hard" else (2, 3, 4)
    n = ctx.draw_choice("n_blocks", _weighted(counts, favored_n))
    h, w = _shape(ctx, overrides, n + extra, core=texture == "default")
    grid = full_grid(h, w, 0)
    positions = _positions(h, w, n + extra, ctx.draw_rng("layout"))
    for origin in positions[:n]:
        _put_ring(grid, origin)
    if texture == "contrast":
        _put_ring(grid, positions[n], missing=ctx.draw_choice("missing_corner", _CORNERS))
        _put_ring(grid, positions[n + 1], color=ctx.draw_choice("distractor_color", (1, 2, 3, 5, 6, 7, 8, 9)))
        _put_ring(grid, positions[n + 2], center=ctx.draw_choice("occupied_center", (1, 2, 3, 4, 5, 7, 8, 9)))
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the sampled motif grammar, not the broader total Racket domain."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["ARC grid dimensions must be at most 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not bool or float)"]
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    if not remaining:
        return ["expected at least one 3x3 motif; no_blocks is a negative fixture"]
    while remaining:
        start = remaining.pop()
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    pending.append(point)
        top, bottom = min(r for r, _ in component), max(r for r, _ in component)
        left, right = min(c for _, c in component), max(c for _, c in component)
        if bottom - top != 2 or right - left != 2:
            return ["each nonzero component must be one separated 3x3 motif"]
        center = grid[top + 1][left + 1]
        ring = {(dr, dc): grid[top + 1 + dr][left + 1 + dc] for dr, dc in _NEIGHBORS}
        values = list(ring.values())
        yellow = all(value == 4 for value in values)
        wrong_color = center == 0 and values[0] not in (0, 4) and len(set(values)) == 1
        missing = [offset for offset, value in ring.items() if value != 4]
        corner = (center == 0 and len(missing) == 1 and missing[0] in _CORNERS
                  and ring[missing[0]] == 0)
        if not (yellow or wrong_color or corner):
            return ["component is not a yellow ring/occupied ring, monochrome decoy, or missing-corner decoy"]
    return []


def _features(grid):
    result = {"targets": 0, "corner_near_miss": 0, "wrong_ring_color": 0, "occupied_center": 0}
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            neighbors = [grid[r + dr][c + dc] for dr, dc in _NEIGHBORS]
            if all(value == 4 for value in neighbors):
                if grid[r][c] == 0:
                    result["targets"] += 1
                elif grid[r][c] != 6:
                    result["occupied_center"] += 1
            if grid[r][c] != 0:
                continue
            if neighbors.count(4) == 7 and all(grid[r + dr][c + dc] == 4
                                              for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                result["corner_near_miss"] += 1
            if neighbors[0] not in (0, 4) and all(value == neighbors[0] for value in neighbors):
                result["wrong_ring_color"] += 1
    return result


def observe_overrides(grid):
    """Infer exact controls for generated returns, independently of bookkeeping.

    Validator-supported no-action motifs outside advertised texture modes need
    not have an inverse texture name; this hook's contract is generated returns.
    """
    features = _features(grid)
    if features["targets"]:
        texture = "contrast" if any(features[k] for k in ("corner_near_miss", "wrong_ring_color", "occupied_center")) else "default"
    elif not any(value for row in grid for value in row):
        texture = "no_blocks"
    else:
        texture = "center_already_filled" if any(value == 8 for row in grid for value in row) else "solid_squares"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blocks": features["targets"], "texture": texture}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if not errors and not _features(grid)["targets"]:
        errors.append("ordinary training input must contain a positive ring")
    return errors


def _rival(grid, mode):
    """Named WRONG-rule predictions for diagnostics, never generation labels."""
    out = [list(row) for row in grid]
    if mode == "identity":
        return out
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            values = [grid[r + dr][c + dc] for dr, dc in _NEIGHBORS]
            fire = all(v == 4 for v in values)
            if mode == "orthogonal_only":
                fire = all(grid[r + dr][c + dc] == 4 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            elif mode == "seven_of_eight":
                fire = values.count(4) >= 7
            elif mode == "any_color_ring":
                fire = values[0] != 0 and all(v == values[0] for v in values)
            if fire and (grid[r][c] == 0 or mode == "overwrite_center"):
                out[r][c] = 4 if mode == "fill_yellow" else 6
                if mode == "first_only":
                    return out
    return out


def _identity(grid): return _rival(grid, "identity")
def _fill_yellow(grid): return _rival(grid, "fill_yellow")
def _orthogonal_only(grid): return _rival(grid, "orthogonal_only")
def _seven_of_eight(grid): return _rival(grid, "seven_of_eight")
def _any_color_ring(grid): return _rival(grid, "any_color_ring")
def _overwrite_center(grid): return _rival(grid, "overwrite_center")
def _first_only(grid): return _rival(grid, "first_only")
def _has_target(grid): return _features(grid)["targets"] > 0
def _has_multiple(grid): return _features(grid)["targets"] > 1
def _has_corner(grid): return _features(grid)["corner_near_miss"] > 0
def _has_wrong_color(grid): return _features(grid)["wrong_ring_color"] > 0
def _has_occupied(grid): return _features(grid)["occupied_center"] > 0


SEMANTIC_WITNESSES = {
    "positive_target": _has_target, "multiple_targets": _has_multiple,
    "corner_near_miss": _has_corner, "wrong_ring_color": _has_wrong_color,
    "occupied_center": _has_occupied,
}
SEMANTIC_RIVALS = {
    "identity": _identity, "fill_yellow": _fill_yellow,
    "orthogonal_only": _orthogonal_only, "seven_of_eight": _seven_of_eight,
    "any_color_ring": _any_color_ring, "overwrite_center": _overwrite_center,
    "first_only": _first_only,
}
WITNESS_RIVALS = {
    "positive_target": ["identity", "fill_yellow"], "multiple_targets": ["first_only"],
    "corner_near_miss": ["orthogonal_only", "seven_of_eight"],
    "wrong_ring_color": ["any_color_ring"], "occupied_center": ["overwrite_center"],
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("orthogonal_only", "seven_of_eight", "any_color_ring", "overwrite_center")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Check only the declared finite rivals; this is not universal induction."""
    return [f"{name} fits all demos and changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
