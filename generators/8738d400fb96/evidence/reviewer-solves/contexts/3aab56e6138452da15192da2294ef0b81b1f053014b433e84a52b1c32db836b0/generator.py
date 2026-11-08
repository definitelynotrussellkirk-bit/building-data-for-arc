"""Sample signed translations selected by two color-coded markers.

The unchanged Racket authority selects the largest same-color four-connected
color-3 component, moves it by marker1 - marker2, and clips color-8 paint onto
an empty canvas. Python predictions below are diagnostic rivals, never labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects, to_indices

GENERATOR_ID = "8738d400fb96"
TASK_ID = GENERATOR_ID
RULE_HASH = "fc4e32aa0363"
VERSION = "2.0.0"
SUMMARY = "Move the largest four-connected green component by the signed 2-to-1 marker vector; clip and recolor to 8."
INVARIANTS = [
    "rectangular integer-color grid with background 0 and exactly one marker of colors 1 and 2",
    "a uniquely largest four-connected color-3 component, with at least two cells",
    "other green components and foreign colors are allowed; marker contact is lawful",
    "signed translations may retain all, some, or none of the selected component",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..16, favors canonical heights", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "10..18, favors canonical widths", "valid": "10..18"},
    "blob_size": {"type": "int", "default": "3..9, difficulty-weighted", "valid": "3..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 8
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("signed_contrast", "full", "partial", "empty")
_STEPS = ((-1, 0), (0, -1), (0, 1), (1, 0))
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CANONICAL_PROFILES = ((10, 12), (9, 11), (10, 13), (8, 12))


def schedule_profile(seed, sample_index, difficulty=None):
    """Public semantic schedule; geometric random choices still vary by seed."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _neighbors(p, steps=_STEPS):
    return {(p[0] + dr, p[1] + dc) for dr, dc in steps}


def _inside(p, h, w):
    return 0 <= p[0] < h and 0 <= p[1] < w


def _components(grid, *, green=True, diagonal=False):
    found = find_objects(grid, univalued=True, diagonal=diagonal,
                         without_bg=True, bg=0)
    return sorted((to_indices(obj) for obj in found
                   if not green or next(iter(obj))[0] == 3), key=min)


def _scene(grid):
    components = _components(grid)
    main = max(components, key=len)
    marker = {color: next((r, c) for r, row in enumerate(grid)
                           for c, v in enumerate(row) if v == color)
              for color in (1, 2)}
    delta = tuple(marker[1][i] - marker[2][i] for i in (0, 1))
    return main, components, delta


def self_check(grid, *, difficulty=None, meta=None):
    """Check pixels, independent of caller metadata or the sampling schedule."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged or non-sequence row"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9, not booleans"]
    counts = {color: sum(v == color for row in grid for v in row) for color in (0, 1, 2, 3)}
    errors = []
    if not counts[0]:
        errors.append("background 0 must be present")
    for color in (1, 2):
        if counts[color] != 1:
            errors.append(f"expected exactly one color-{color} marker; found {counts[color]}")
    components = _components(grid)
    if not components or max(map(len, components)) < 2:
        errors.append("expected a green component of at least two cells")
    elif sum(len(c) == max(map(len, components)) for c in components) != 1:
        errors.append("largest four-connected green component must be unique")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    main, _, _ = _scene(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "blob_size": len(main)}


def _polyomino(n, rng):
    cells = {(0, 0)}
    while len(cells) < n:
        frontier = set().union(*(_neighbors(p) for p in cells)) - cells
        candidates = []
        for p in sorted(frontier):
            trial = cells | {p}
            if (max(r for r, _ in trial) - min(r for r, _ in trial) < 4
                    and max(c for _, c in trial) - min(c for _, c in trial) < 5):
                candidates.append(p)
        cells.add(rng.choice(candidates))
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _grow(start, size, allowed, rng):
    cells = {start}
    while len(cells) < size:
        frontier = (set().union(*(_neighbors(p) for p in cells)) & allowed) - cells
        if not frontier:
            return None
        cells.add(rng.choice(sorted(frontier)))
    return cells


def _green_space(board, green):
    return board - green - set().union(*(_neighbors(p) for p in green))


def _contrast(main, board, delta, h, w, rng):
    """Build a visible diagonal green decoy, earlier/later greens, and big noise."""
    dr, dc = delta
    visible = {p for p in board if _inside((p[0] + dr, p[1] + dc), h, w)}
    allowed = _green_space(board, main)
    starts = sorted(allowed & visible & set().union(*(_neighbors(p, _DIAGONALS) for p in main)))
    rng.shuffle(starts)
    green = None
    for start in starts:
        patch = _grow(start, 2, allowed, rng)
        if patch:
            green = main | patch
            break
    if green is None:
        return None
    # Separate components before and after the main's complete row-major span
    # make both first-component and last-component shortcuts observably wrong.
    for earlier in (True, False):
        candidates = sorted(p for p in _green_space(board, green)
                            if (p < min(main) if earlier else p > max(main)))
        if not candidates:
            return None
        green.add(rng.choice(candidates))
    allowed = board - green
    candidates = sorted(allowed & visible)
    if not candidates:
        return None
    rng.shuffle(candidates)
    for start in candidates:
        noise = _grow(start, len(main) + rng.randint(1, 3), allowed, rng)
        if noise:
            return green, noise
    return None


def _varied_noise(main, board, rng):
    green = set(main)
    for _ in range(rng.randint(0, 2)):
        allowed = _green_space(board, green)
        if not allowed:
            break
        start = rng.choice(sorted(allowed))
        patch = _grow(start, rng.randint(1, len(main) - 1), allowed, rng)
        green.update(patch or {start})
    allowed = board - green
    starts = sorted(allowed)
    rng.shuffle(starts)
    size = rng.randint(1, len(main) + 3)
    for start in starts:
        noise = _grow(start, size, allowed, rng)
        if noise:
            return green, noise
    return None


def _layout(h, w, n, phase, rng):
    board = {(r, c) for r in range(h) for c in range(w)}
    vectors = [(dr, dc) for dr in range(-4, 5) for dc in range(-5, 6) if dr or dc]
    if phase == 0:
        vectors = [(dr, dc) for dr, dc in vectors
                   if (dr < 0 or dc < 0) and dr != dc
                   and (abs(dr), abs(dc)) not in ((3, 4), (0, 4), (3, 0))]
    # Every retry explores valid geometry. No retry ever returns a partial scene
    # or silently drops a requested cell/marker.
    for _ in range(32):
        shape = _polyomino(n, rng)
        bh, bw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
        rng.shuffle(vectors)
        for dr, dc in vectors:
            origins = [(r, c) for r in range(h - bh + 1) for c in range(w - bw + 1)]
            rng.shuffle(origins)
            for r0, c0 in origins:
                main = {(r0 + r, c0 + c) for r, c in shape}
                kept = sum(_inside((r + dr, c + dc), h, w) for r, c in main)
                if not ((phase < 2 and kept == n) or (phase == 2 and 0 < kept < n)
                        or (phase == 3 and kept == 0)):
                    continue
                parts = (_contrast(main, board, (dr, dc), h, w, rng) if phase == 0
                         else _varied_noise(main, board, rng))
                if parts is None:
                    continue
                green, noise = parts
                free = board - green - noise
                marker_pairs = sorted((p, (p[0] + dr, p[1] + dc)) for p in free
                                      if (p[0] + dr, p[1] + dc) in free)
                if not marker_pairs:
                    continue
                a, b = rng.choice(marker_pairs)
                grid = full_grid(h, w, 0)
                for r, c in green:
                    grid[r][c] = 3
                color = rng.choice((4, 5, 6, 7, 8, 9))
                for r, c in noise:
                    grid[r][c] = color
                grid[a[0]][a[1]], grid[b[0]][b[1]] = 2, 1
                return grid
    raise RuntimeError("no lawful layout found; refusing an incomplete grid")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("size_profile", _CANONICAL_PROFILES * 3 + (None,))
    hs, ws = list(range(8, 17)), list(range(10, 19))
    if core:
        hs += [core[0]] * 60
        ws += [core[1]] * 60
    h, w = ctx.draw_choice("grid_h", hs), ctx.draw_choice("grid_w", ws)
    favored = {"easy": (3, 4, 5), "medium": (4, 5, 6), "hard": (6, 7, 8, 9)}
    n = ctx.draw_choice("blob_size", list(range(3, 10)) + list(favored.get(difficulty, (4, 5, 6))) * 3)
    return _layout(h, w, n, sample_index % LESSON_SCHEDULE_PERIOD, ctx.draw_rng("layout"))


def _diagnostic_prediction(grid, mode="reference"):
    """Diagnostic Python model; actual training labels come from Racket."""
    main, components, (dr, dc) = _scene(grid)
    cells = main
    if mode == "all_green":
        cells = set().union(*components)
    elif mode == "green8":
        cells = max(_components(grid, diagonal=True), key=len)
    elif mode in ("first_green", "last_green"):
        cells = components[0 if mode == "first_green" else -1]
    elif mode == "non_singleton_green":
        cells = set().union(*(c for c in components if len(c) > 1))
    elif mode == "largest_nonmarker":
        cells = max((c for c in _components(grid, green=False)
                     if grid[min(c)[0]][min(c)[1]] not in (1, 2)), key=len)
    elif mode == "all_nonmarker":
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1, 2)}
    if mode == "absolute_vector":
        dr, dc = abs(dr), abs(dc)
    elif mode == "fixed_step_3_4":
        dr, dc = (3 if dr > 0 else -3 if dr < 0 else 0), (4 if dc > 0 else -4 if dc < 0 else 0)
    elif mode == "reverse_vector":
        dr, dc = -dr, -dc
    elif mode == "swap_components":
        dr, dc = dc, dr
    h, w = len(grid), len(grid[0])
    if mode == "avoid_clipping":
        dr = max(-min(r for r, _ in main), min(dr, h - 1 - max(r for r, _ in main)))
        dc = max(-min(c for _, c in main), min(dc, w - 1 - max(c for _, c in main)))
    out = full_grid(h, w, 0)
    for r, c in cells:
        r, c = r + dr, c + dc
        if mode == "wrap_translation":
            r, c = r % h, c % w
        if _inside((r, c), h, w):
            out[r][c] = 3 if mode == "no_recolor" else 8
    return out


def _rival(mode):
    def predict(grid):
        return _diagnostic_prediction(grid, mode)
    predict.__name__ = mode
    return predict


_SELECTOR_NAMES = ("all_green", "green8", "first_green", "last_green",
                   "largest_nonmarker", "all_nonmarker", "non_singleton_green")
_VECTOR_NAMES = ("absolute_vector", "fixed_step_3_4", "swap_components")
SEMANTIC_RIVALS = {name: _rival(name) for name in _SELECTOR_NAMES + _VECTOR_NAMES +
                  ("reverse_vector", "wrap_translation", "avoid_clipping", "no_recolor")}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in _SELECTOR_NAMES + ("fixed_step_3_4",)}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _separates(grid, names):
    reference = _diagnostic_prediction(grid)
    return all(SEMANTIC_RIVALS[name](grid) != reference for name in names)


def _retained_count(grid):
    return sum(v == 8 for row in _diagnostic_prediction(grid) for v in row)


SEMANTIC_WITNESSES = {
    "selector_contrast": lambda grid: _separates(grid, _SELECTOR_NAMES),
    "signed_nonstandard_vector": lambda grid: _separates(grid, _VECTOR_NAMES),
    "partial_clipping": lambda grid: 0 < _retained_count(grid) < len(_scene(grid)[0]),
    "empty_clipping": lambda grid: _retained_count(grid) == 0,
}
WITNESS_RIVALS = {
    "selector_contrast": list(_SELECTOR_NAMES),
    "signed_nonstandard_vector": list(_VECTOR_NAMES),
    "partial_clipping": ["wrap_translation", "avoid_clipping"],
    "empty_clipping": ["wrap_translation", "avoid_clipping"],
}


def lesson_identifiable(demos, query):
    """Finite named-rival check; not proof of unique induction."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
