"""Teach the unchanged local 3x3-window corner-union rule.

The Racket authority starts from zero, scans the ORIGINAL input, and unions
corners of all nonzero monochrome 3x3 windows. It erases unmatched foreground.
Input construction and diagnostic rivals below never supply training labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a06827026857"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4f871ddb0a9d"
SUMMARY = (
    "Union the corners of every solid monochrome nonzero 3x3 window onto a "
    "zero output. Teach repeated colors, attached nonmatching foreground, "
    "and overlapping windows as well as separated canonical-size squares."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("clean", "mixed")
CASES = ("clean", "repeated", "attached", "overlap", "mixed")
INVARIANTS = [
    "rectangular integer-color grid, background 0, dimensions 5..20",
    "one to five base 3x3 targets; at most one has a same-color corner appendage",
    "at most one additional solid 3x4, 4x3 or 4x4 overlapping-window block",
    "different components have at least one background cell of separation",
    "every requested base square is present; impossible joint controls raise",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical or broad", "valid": "5..20"},
    "grid_w": {"type": "int", "default": "canonical or broad", "valid": "5..20"},
    "square_count": {"type": "int", "default": "clean 2; mixed 2..5; forced small canvas 1",
                     "valid": "1..5"},
    "case": {"type": "str", "default": "alternating clean/mixed",
             "valid": "|".join(CASES)},
}
# Exact feasible cases return their requested values. Capacity failures name
# the responsible explicit controls in the ValueError's incompatible_axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic profile for the unoverridden sampler, not a grid period."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _capacity(h, w, side):
    return ((h + 1) // (side + 1)) * ((w + 1) // (side + 1))


def _resolve(ctx, sample_index, difficulty, overrides):
    requested = {k: v for k, v in overrides.items() if v is not None}
    for name, lo, hi in (("grid_h", 5, 20), ("grid_w", 5, 20),
                         ("square_count", 1, 5)):
        if name in requested:
            value = requested[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "case" in requested and requested["case"] not in CASES:
        raise ValueError(f"case must be one of {CASES}")
    modes = ([requested["case"]] if "case" in requested else
             list(dict.fromkeys((schedule_profile(ctx.seed, sample_index), "clean"))))
    selected = None
    for mode in modes:
        if "square_count" in requested:
            counts = [requested["square_count"]]
        else:
            maximum = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
            count = (2 if mode == "clean" else
                     ctx.draw_rng(f"base_square_count:{difficulty}").randint(2, maximum))
            counts = list(dict.fromkeys((count, 2, 1)))
        for count in counts:
            if mode == "repeated" and count < 2:
                continue
            side = 3 if mode in ("clean", "repeated") else 4
            slots = count + (mode in ("overlap", "mixed"))
            pairs = [(h, w) for h in range(5, 21) for w in range(5, 21)
                     if ("grid_h" not in requested or h == requested["grid_h"])
                     and ("grid_w" not in requested or w == requested["grid_w"])
                     and _capacity(h, w, side) >= slots]
            if pairs:
                selected = mode, count, pairs
                break
        if selected is not None:
            break
    if selected is None:
        error = ValueError(
            "incompatible grid_h/grid_w/square_count/case: requested objects "
            "do not fit the documented separated-slot layout, or repeated "
            "case has fewer than two squares"
        )
        error.incompatible_axes = tuple(sorted(requested))
        raise error
    mode, count, pairs = selected
    anchors = [(9, 9), (8, 10), (9, 11)]
    preferred = [p for p in anchors if p in pairs] if mode == "clean" else []
    if not preferred:
        lo, hi = {"easy": (8, 12), "medium": (9, 16), "hard": (12, 20)}.get(
            difficulty, (9, 16))
        preferred = [p for p in pairs if lo <= p[0] <= hi and lo <= p[1] <= hi]
    h, w = ctx.draw_rng(f"canvas:{difficulty}").choice(preferred or pairs)
    # Record resolved values only. A supplied override is never clipped, dropped,
    # or recorded as honored when its pixels realize something else.
    h = ctx.draw_choice("grid_h", (h,))
    w = ctx.draw_choice("grid_w", (w,))
    count = ctx.draw_choice("square_count", (count,))
    mode = ctx.draw_choice("case", (mode,))
    return h, w, count, mode


def _orient(points, rng):
    points = set(points)
    if rng.randrange(2):
        points = {(r, -c) for r, c in points}
    for _ in range(rng.randrange(4)):
        points = {(c, -r) for r, c in points}
    top, left = min(r for r, _ in points), min(c for _, c in points)
    return {(r - top, c - left) for r, c in points}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w, count, mode = _resolve(ctx, sample_index, difficulty, overrides)
    has_overlap = mode in ("overlap", "mixed")
    colors = list(ctx.draw_distinct_colors("object_colors", n=count + has_overlap,
                                          exclude={0}))
    if mode == "repeated":
        colors[:count] = [colors[0]] * count
    elif mode == "mixed" and count >= 2:
        colors[count - 1] = colors[0]
    shapes = [{(r, c) for r in range(3) for c in range(3)} for _ in range(count)]
    if mode in ("attached", "mixed"):
        # Orthogonally attached to a corner, so even degree-two thinning fails.
        shapes[0].add((0, 3))
    if has_overlap:
        bh, bw = ctx.draw_choice("overlap_shape", ((3, 4), (4, 3), (4, 4)))
        shapes.append({(r, c) for r in range(bh) for c in range(bw)})
    side = 3 if mode in ("clean", "repeated") else 4
    nr, nc = (h + 1) // (side + 1), (w + 1) // (side + 1)
    rng = ctx.draw_rng("layout")
    slots = rng.sample([(r, c) for r in range(nr) for c in range(nc)], len(shapes))
    r0 = rng.randint(0, h - (nr * (side + 1) - 1))
    c0 = rng.randint(0, w - (nc * (side + 1) - 1))
    grid = full_grid(h, w, 0)
    for index, (points, color, (sr, sc)) in enumerate(zip(shapes, colors, slots)):
        points = _orient(points, ctx.draw_rng(f"orientation:{index}"))
        ph, pw = max(r for r, _ in points) + 1, max(c for _, c in points) + 1
        top = r0 + sr * (side + 1) + rng.randint(0, side - ph)
        left = c0 + sc * (side + 1) + rng.randint(0, side - pw)
        for r, c in points:
            grid[top + r][left + c] = color
    return grid


def _components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append((color, cells))
    return result


def _box(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _kind(cells):
    top, left, bottom, right = _box(cells)
    h, w = bottom - top + 1, right - left + 1
    if len(cells) == h * w:
        if (h, w) == (3, 3):
            return "square"
        if (h, w) in ((3, 4), (4, 3), (4, 4)):
            return "overlap"
    if len(cells) == 10:
        for r in range(top, bottom - 1):
            for c in range(left, right - 1):
                square = {(r + dr, c + dc) for dr in range(3) for dc in range(3)}
                attachments = {(r, c - 1), (r + 2, c - 1), (r, c + 3), (r + 2, c + 3),
                               (r - 1, c), (r - 1, c + 2), (r + 3, c), (r + 3, c + 2)}
                if square <= cells and cells - square <= attachments:
                    return "attached"
    return "unsupported"


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["expected integer colors 0..9, not booleans"]
    if not (5 <= len(grid) <= 20 and 5 <= len(grid[0]) <= 20):
        return ["helpful canvas dimensions must be in 5..20"]
    components = _components(grid)
    kinds = [_kind(cells) for _, cells in components]
    errors = []
    owners = {point: index for index, (_, cells) in enumerate(components) for point in cells}
    if any((r + dr, c + dc) in owners and owners[r + dr, c + dc] != index
           for (r, c), index in owners.items()
           for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        errors.append("different components require a background-cell gap")
    if not 1 <= kinds.count("square") + kinds.count("attached") <= 5:
        errors.append("expected 1..5 base 3x3 targets")
    if kinds.count("attached") > 1 or kinds.count("overlap") > 1:
        errors.append("at most one appendage and one overlap block")
    if "unsupported" in kinds:
        errors.append("foreground component outside the documented helpful grammar")
    if not any(v == 0 for row in grid for v in row):
        errors.append("expected zero background, not a full-canvas identity")
    return errors


def strict_canonical_like(grid):
    """Lawful instances of this documented input manifold, not exact profiles."""
    return self_check(grid)


def observe_overrides(grid):
    components = _components(grid)
    kinds = [_kind(cells) for _, cells in components]
    colors = [color for (color, _), kind in zip(components, kinds) if kind != "overlap"]
    attached, overlap = "attached" in kinds, "overlap" in kinds
    mode = ("mixed" if attached and overlap else "attached" if attached else
            "overlap" if overlap else "repeated" if len(set(colors)) < len(colors) else "clean")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "square_count": kinds.count("square") + kinds.count("attached"), "case": mode}


def _paint_boxes(grid, groups):
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in groups:
        t, l, b, r = _box(cells)
        for y, x in ((t, l), (t, r), (b, l), (b, r)):
            out[y][x] = color
    return out


def _color_boxes(grid):
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, set()).add((r, c))
    return _paint_boxes(grid, groups.items())


def _component_boxes(grid):
    return _paint_boxes(grid, _components(grid))


def _isolated_squares(grid):
    return _paint_boxes(grid, [(color, cells) for color, cells in _components(grid)
                               if _kind(cells) == "square"])


def _preserve_nonmatches(grid):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 2):
        for c in range(len(grid[0]) - 2):
            color = grid[r][c]
            if color and all(grid[r + dr][c + dc] == color
                             for dr in range(3) for dc in range(3)):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)):
                    out[r + dr][c + dc] = 0
    return out


def _degree_two(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            neighbors = sum(0 <= y < len(grid) and 0 <= x < len(row) and grid[y][x] == color
                            for y, x in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
            if color and neighbors == 2:
                out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "color_boxes": _color_boxes,
    "component_boxes": _component_boxes,
    "isolated_squares": _isolated_squares,
    "preserve_nonmatches": _preserve_nonmatches,
    "degree_two": _degree_two,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _attached_witness(grid):
    return any(_kind(cells) == "attached" for _, cells in _components(grid))


def _overlap_witness(grid):
    return any(_kind(cells) == "overlap" for _, cells in _components(grid))


def _repeated_witness(grid):
    colors = [color for color, cells in _components(grid) if _kind(cells) in ("square", "attached")]
    return len(colors) != len(set(colors))


SEMANTIC_WITNESSES = {
    "attached_foreground": _attached_witness,
    "overlapping_windows": _overlap_witness,
    "repeated_target_color": _repeated_witness,
}
WITNESS_RIVALS = {
    "attached_foreground": list(SEMANTIC_RIVALS),
    "overlapping_windows": ["component_boxes", "isolated_squares", "preserve_nonmatches", "degree_two"],
    "repeated_target_color": ["color_boxes"],
}


def lesson_identifiable(demos, query):
    """Finite rival check against supplied labels; never an answer oracle."""
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"requires at least {EXAMPLES_NEEDED} demonstrations")
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"unrefuted rival {name} disagrees on the query")
    return reasons
