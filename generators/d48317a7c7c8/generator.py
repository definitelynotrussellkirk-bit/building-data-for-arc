"""Sample exact yellow three-bar cap tasks, with executable shortcut witnesses.

Only inputs are generated here. The pinned canonical Racket program supplies
labels. Rich scenes vary placement/orientation and include wrong-color bars,
overlong and bent yellow components, diagonal contacts, and unavailable caps.
"""
from __future__ import annotations

from functools import lru_cache, partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "d48317a7c7c8"
TASK_ID = GENERATOR_ID
RULE_HASH = "b2af6531f18d"
VERSION = "3.0.0"
SUMMARY = (
    "Cap each straight, monochrome 4-connected yellow component of exactly "
    "three cells with color 8 at each independently available endpoint. "
    "Nonzero and off-grid cap positions, other colors, and other components "
    "stay unchanged. Ordinary scenes supply contrasting distractors."
)
INVARIANTS = [
    "rectangular ARC integer grid with background 0",
    "at least one exact straight three-cell color-4 component has an available cap",
    "target count is exact; same-color cardinal contacts never merge separate objects",
    "wrong-color straight threes and nonstraight/overlong yellow foils are ordinary support",
    "cap availability is tested independently at each end against the original input",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile mixture or 8..24", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "canonical-profile mixture or 8..24", "valid": "8..24"},
    "n_bars": {"type": "int", "default": "weighted feasible 2..10; 1 by explicit override", "valid": "1..10"},
    "distractor_color": {"type": "int", "default": "weighted toward canonical 6", "valid": "1|2|3|5|6|7|8|9"},
}
# Geometry/count rejections carry the exact participating axes and a numeric
# construction budget. This budget describes supported packing, not a theorem
# about the densest possible ARC scene. No ordinary or single-axis draw rejects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_CANONICAL_SHAPES = ((10, 9), (9, 8), (8, 10), (10, 8))


def _components(grid, *, diagonal=False, multicolor=False):
    components = find_objects(grid, univalued=not multicolor, diagonal=diagonal,
                           without_bg=True, bg=0)
    result = []
    for obj in components:
        colors = {color for color, _ in obj}
        result.append((next(iter(colors)) if len(colors) == 1 else -1,
                       frozenset(cell for _, cell in obj)))
    return sorted(result, key=lambda item: (min(item[1]), item[0]))


def _ends(cells):
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(rows) == 1:
        return ((rows[0], cols[0] - 1), (rows[0], cols[-1] + 1))
    if len(cols) == 1:
        return ((rows[0] - 1, cols[0]), (rows[-1] + 1, cols[0]))
    return ()


def _inside(grid, cell):
    return 0 <= cell[0] < len(grid) and 0 <= cell[1] < len(grid[0])


def _available(grid, cell):
    return _inside(grid, cell) and grid[cell[0]][cell[1]] == 0


def _targets(grid):
    return [cells for color, cells in _components(grid)
            if color == 4 and len(cells) == 3 and _ends(cells)]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task domain; metadata cannot waive malformed inputs."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["ARC grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors in 0..9 (not bool)"]
    targets = _targets(grid)
    if not targets:
        return ["no exact straight three-cell yellow component"]
    if not any(_available(grid, cap) for cells in targets for cap in _ends(cells)):
        return ["no target has an available in-bounds background cap"]
    return []


def strict_canonical_like(grid):
    """The rule domain, including canonical distractors and one-sided caps."""
    return self_check(grid)


def observe_overrides(grid):
    colored_bars = {color for color, cells in _components(grid)
                    if color not in (0, 4) and len(cells) == 3 and _ends(cells)}
    if len(colored_bars) != 1:
        raise ValueError("expected one observable nonyellow three-bar color")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_bars": len(_targets(grid)), "distractor_color": colored_bars.pop()}


def _horizontal_capacity(h, w):
    return 2 + (h - 8) // 2 + (h // 2) * ((w - 8) // 6)


def supported_bar_capacity(h, w):
    """Guaranteed capacity of the documented rich-scene fallback construction."""
    return min(10, max(_horizontal_capacity(h, w), _horizontal_capacity(w, h)))


def _choose_parameters(ctx, difficulty, overrides):
    core = ctx.sample_index % 2 == 0
    fixed_h, fixed_w = overrides.get("grid_h"), overrides.get("grid_w")
    capacity = supported_bar_capacity(fixed_h or 24, fixed_w or 24)
    requested = overrides.get("n_bars")
    if requested is not None and requested > capacity:
        axes = tuple(name for name in ("grid_h", "grid_w", "n_bars")
                     if overrides.get(name) is not None)
        error = ValueError(
            f"incompatible {axes}: rich-scene packing for grid_h={fixed_h}, "
            f"grid_w={fixed_w} supports n_bars<={capacity}, requested {requested}")
        error.incompatible_axes = axes
        raise error
    favored = [2] * 90 if core else ([2, 3] * 5 if difficulty == "easy" else
              ([4, 5, 6, 7] * 4 if difficulty == "hard" else [2, 3, 4] * 5))
    # Every ordinary scene retains both independent cap teaching roles. The
    # smaller explicit one-target control is still honored without shortening.
    counts = list(range(1 if requested == 1 else 2, capacity + 1))
    counts += [count for count in favored if count <= capacity]
    n_bars = ctx.draw_choice("n_bars", counts)
    color = ctx.draw_choice("distractor_color", list(_COLORS) + [6] * 12)
    feasible = [(h, w) for h in range(8, 25) for w in range(8, 25)
                if (fixed_h is None or h == fixed_h)
                and (fixed_w is None or w == fixed_w)
                and supported_bar_capacity(h, w) >= n_bars]
    if not feasible:
        raise RuntimeError("feasible count selection lost its geometry support")
    anchor_h, anchor_w = ctx.draw_rng("canonical_profile").choice(_CANONICAL_SHAPES)
    heights = sorted({h for h, _ in feasible})
    if core and anchor_h in heights:
        heights += [anchor_h] * 100
    elif difficulty == "hard":
        heights += [h for h in heights if h >= 13] * 3
    h = ctx.draw_choice("grid_h", heights)
    widths = sorted(w for hh, w in feasible if hh == h)
    if core and anchor_w in widths:
        widths += [anchor_w] * 100
    elif difficulty == "hard":
        widths += [w for w in widths if w >= 13] * 3
    return h, ctx.draw_choice("grid_w", widths), n_bars, color


# Each pattern declares occupied cells (row, col, color role), protected empty
# caps, and required off-grid caps. Role 4 is yellow; 1 is the distractor color;
# 2 is a noncyan blocker. Keeping all claimed rival caps disjoint makes each
# geometric witness an actual output disagreement, not merely a named object.
_PATTERNS = {
    "edge": (((1, 0, 4), (1, 1, 4), (1, 2, 4), (0, 3, 4)), ((1, 3),), ((1, -1),)),
    "blocked": (((0, 1, 4), (0, 2, 4), (0, 3, 4), (0, 0, 2)), ((0, 4),), ()),
    "bar": (((0, 1, 4), (0, 2, 4), (0, 3, 4)), ((0, 0), (0, 4)), ()),
    "colored": (((0, 1, 1), (0, 2, 1), (0, 3, 1)), ((0, 0), (0, 4)), ()),
    "long": (((0, 1, 4), (0, 2, 4), (0, 3, 4), (0, 4, 4)), ((0, 0), (0, 5)), ()),
    "bent": (((0, 1, 4), (0, 2, 4), (0, 3, 4), (1, 1, 4)), ((0, 0), (0, 4)), ()),
    "ell": (((0, 0, 4), (1, 0, 4), (1, 1, 4)), (), ()),
}


def _transform_point(r, c, rotation, reflected):
    if reflected:
        c = -c
    for _ in range(rotation):
        r, c = c, -r
    return r, c


@lru_cache(maxsize=128)
def _placements(h, w, kind):
    pixels, opened, outside = _PATTERNS[kind]
    variants = set()
    for rotation in range(4):
        for reflected in (False, True):
            raw = [(*_transform_point(r, c, rotation, reflected), role)
                   for r, c, role in pixels]
            low_r, low_c = min(r for r, _, _ in raw), min(c for _, c, _ in raw)
            points = tuple(sorted((r-low_r, c-low_c, role) for r, c, role in raw))
            caps = tuple(sorted((r-low_r, c-low_c) for r, c in
                         (_transform_point(r, c, rotation, reflected) for r, c in opened)))
            off = tuple(sorted((r-low_r, c-low_c) for r, c in
                        (_transform_point(r, c, rotation, reflected) for r, c in outside)))
            variants.add((points, caps, off))
    result = []
    for pixels, opened, outside in sorted(variants):
        ph = max(r for r, _, _ in pixels) + 1
        pw = max(c for _, c, _ in pixels) + 1
        for r0 in range(h-ph+1):
            for c0 in range(w-pw+1):
                caps = tuple((r+r0, c+c0) for r, c in opened)
                if not all(0 <= r < h and 0 <= c < w for r, c in caps):
                    continue
                if any(0 <= r+r0 < h and 0 <= c+c0 < w for r, c in outside):
                    continue
                result.append((tuple((r+r0, c+c0, role) for r, c, role in pixels), caps))
    return tuple(result)


def _fits(grid, reserved, pixels, caps):
    h, w = len(grid), len(grid[0])
    if any(grid[r][c] != 0 or (r, c) in reserved for r, c, _ in pixels):
        return False
    if any(grid[r][c] != 0 or (r, c) in reserved for r, c in caps):
        return False
    for r, c, color in pixels:
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == color:
                return False
    return True


def _random_scene(h, w, n_bars, color, rng):
    roles = {4: 4, 1: color, 2: 6 if color == 8 else color}
    kinds = (["edge", "blocked"] if n_bars >= 2 else ["edge"])
    kinds += ["long", "colored", "bent", "ell"] + ["bar"] * max(0, n_bars-2)
    for _ in range(8):
        grid, reserved = full_grid(h, w, 0), set()
        for kind in kinds:
            candidates = _placements(h, w, kind)
            order = list(range(len(candidates)))
            rng.shuffle(order)
            for index in order:
                raw, caps = candidates[index]
                pixels = [(r, c, roles[role]) for r, c, role in raw]
                if _fits(grid, reserved, pixels, caps):
                    for r, c, value in pixels:
                        grid[r][c] = value
                    reserved.update(caps)
                    break
            else:
                break
        else:
            return grid
    return None


def _fallback_scene(h, w, n_bars, color, rng):
    """Guaranteed packing after bounded random placement; never drop objects."""
    transposed = _horizontal_capacity(w, h) > _horizontal_capacity(h, w)
    hh, ww = (w, h) if transposed else (h, w)
    grid = full_grid(hh, ww, 0)
    yellow = [(1, c) for c in range(3)] + [(0, 3)]
    yellow += [(3, c) for c in range(1, 5)]
    yellow += [(5, 1), (5, 2), (5, 3), (6, 1)]
    yellow += [(0, 6), (0, 7), (1, 7)]
    if n_bars >= 2:
        yellow += [(r, 6) for r in range(3, 6)]
        grid[2][6] = 6 if color == 8 else color
    for r, c in yellow:
        grid[r][c] = 4
    for c in range(4, 7):
        grid[7][c] = color
    extra = [(r, 1) for r in range(9, hh, 2)]
    extra += [(r, 9+6*k) for k in range((ww-8)//6) for r in range(0, hh, 2)]
    rng.shuffle(extra)
    for r, c in extra[:max(0, n_bars-2)]:
        for cc in range(c, c+3):
            grid[r][cc] = 4
    if rng.choice((False, True)):
        grid = list(reversed(grid))
    if rng.choice((False, True)):
        grid = [list(reversed(row)) for row in grid]
    if transposed:
        grid = [list(row) for row in zip(*grid)]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        valid = value in _COLORS if name == "distractor_color" else (
            1 <= value <= 10 if name == "n_bars" else 8 <= value <= 24)
        if not valid:
            raise ValueError(f"{name}={value} is outside the declared axis domain")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    h, w, n_bars, color = _choose_parameters(ctx, difficulty, overrides)
    grid = _random_scene(h, w, n_bars, color, ctx.draw_rng("object_placement"))
    if grid is None:
        grid = _fallback_scene(h, w, n_bars, color, ctx.draw_rng("constructive_fallback"))
    observed = observe_overrides(grid)
    if observed != {"grid_h": h, "grid_w": w, "n_bars": n_bars, "distractor_color": color}:
        raise RuntimeError("constructed scene violated its exact observable contract")
    return grid


def _prediction(grid, mode="intended"):
    """Authoring mirror/rivals only. Never used as the label authority."""
    out = [list(row) for row in grid]
    if mode in ("sliding_triples", "maximal_runs"):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                for dr, dc in ((0, 1), (1, 0)):
                    cells = [(r+dr*i, c+dc*i) for i in range(3)]
                    if not all(_inside(grid, p) and grid[p[0]][p[1]] == 4 for p in cells):
                        continue
                    caps = ((r-dr, c-dc), (r+3*dr, c+3*dc))
                    if mode == "maximal_runs" and any(
                        _inside(grid, p) and grid[p[0]][p[1]] == 4 for p in caps):
                        continue
                    for rr, cc in caps:
                        if _available(grid, (rr, cc)):
                            out[rr][cc] = 8
        return out
    components = _components(grid, diagonal=mode == "eight_connected",
                          multicolor=mode == "multicolor_components")
    for color, cells in components:
        if color != 4 and mode != "any_color":
            continue
        if not (len(cells) >= 3 if mode == "at_least_three" else len(cells) == 3):
            continue
        caps = _ends(cells)
        if not caps:
            continue
        if mode == "both_in_bounds" and not all(_inside(grid, p) for p in caps):
            continue
        if mode == "both_empty" and not all(_available(grid, p) for p in caps):
            continue
        for r, c in caps:
            if _inside(grid, (r, c)) and (mode == "overwrite_occupied" or grid[r][c] == 0):
                out[r][c] = 8
    return out


def rule_mirror(grid):
    return _prediction(grid)


SEMANTIC_RIVALS = {
    name: partial(_prediction, mode=name)
    for name in ("any_color", "at_least_three", "sliding_triples", "maximal_runs",
                 "eight_connected", "multicolor_components", "both_in_bounds",
                 "both_empty", "overwrite_occupied")
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _distinguishes(grid, name):
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {name: partial(_distinguishes, name=name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite named-rival check, not a claim of unique universal induction."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for pair in list(demos) + [query]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["lesson pair must contain input and reference output"]
        errors = self_check(pair["input"])
        if errors:
            return errors
        if rule_mirror(pair["input"]) != pair["output"]:
            return ["authoring mirror disagrees with reference output"]
    return [f"rival {name} fits all demonstrations but disagrees on query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
