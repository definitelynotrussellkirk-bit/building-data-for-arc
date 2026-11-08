"""Input sampler for E34, Center Completion; labels remain canonical Racket.

Ordinary draws interleave missing/mismatched north-south and west-east
neighborhoods, alongside true pluses and an occupied-center decoy. Three
consecutive demonstrations cover both phases. Small or monochrome explicit
overrides remain useful input controls, without a lesson-identifiability claim.
"""
from __future__ import annotations

from collections import Counter
from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6355eb114053"
TASK_ID = GENERATOR_ID
RULE_HASH = "d4bb39745d13"
VERSION = "2.0.0"
SUMMARY = "Fill only zero centers whose four cardinal neighbors share one nonzero color."
INVARIANTS = [
    "rectangular integer-color grids with background zero and at least one eligible center",
    "ordinary scenes contain true pluses, direction/equality near misses, and an occupied-center decoy",
    "exact requested dimensions, eligible-center counts, and nonzero palette sizes are observable",
    "separation is a sampling convenience, not a restriction on accepted task inputs",
]
AXES = {
    "grid_h": {"type": "int", "default": "5..14, canonical-profile mixture", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "5..14, canonical-profile mixture", "valid": "5..14"},
    "n_pluses": {"type": "int", "default": "1..6 subject to packing capacity", "valid": "1..6"},
    "palette_size": {"type": "int", "default": "2..9 nonzero colors; canonical mixture", "valid": "1..9"},
}
# Backward-compatible spelling, not an additional degree of freedom. Focused
# tests exercise this alias, including contradictory simultaneous requests.
OVERRIDE_ALIASES = {"n_distinct_colors": "palette_size"}
# Exact incompatible requests for this disjoint-3x3 constructive sampler.
# Some rejected layouts could support touching pluses under the broader rule.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    [{"grid_h": h, "grid_w": w, "n_pluses": n}
     for h in range(5, 15) for w in range(5, 15) for n in range(1, 7)
     if (h // 3) * (w // 3) < n]
    + [{axis: size, "n_pluses": n}
       for axis in ("grid_h", "grid_w") for size in range(5, 15) for n in range(1, 7)
       if (size // 3) * 4 < n]
    + [{"palette_size": p, "n_distinct_colors": q}
       for p in range(1, 10) for q in range(1, 10) if p != q]
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("north_south", "west_east")
MIN_STRICT_FRAC = 1.0
DEGENERATE_TEXTURES = ("no_pluses", "mismatched_neighbors", "center_already_filled")
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILES = ((7, 8, 2), (8, 9, 2), (6, 10, 3), (9, 9, 2), (8, 10, 3))


def schedule_profile(seed, sample_index, difficulty=None):
    """The semantic phase, independent of geometry and palette draws."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validated_overrides(overrides):
    unknown = set(overrides) - set(AXES) - set(OVERRIDE_ALIASES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    result = {name: value for name, value in overrides.items() if value is not None}
    for name, value in result.items():
        lo, hi = (5, 14) if name in ("grid_h", "grid_w") else ((1, 6) if name == "n_pluses" else (1, 9))
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, excluding bool")
    if ("palette_size" in result and "n_distinct_colors" in result
            and result["palette_size"] != result["n_distinct_colors"]):
        raise ValueError("palette_size and n_distinct_colors name the same exact nonzero color count")
    if "n_distinct_colors" in result:
        result["palette_size"] = result["n_distinct_colors"]
    return result


def _dimensions(ctx, overrides, core):
    n = overrides.get("n_pluses", 1)
    choices = [(h, w) for h in range(5, 15) for w in range(5, 15)
               if (h // 3) * (w // 3) >= n
               and h == overrides.get("grid_h", h)
               and w == overrides.get("grid_w", w)]
    if not choices:
        axes = tuple(name for name in ("grid_h", "grid_w", "n_pluses") if name in overrides)
        exc = ValueError(f"incompatible {', '.join(axes)}: need n_pluses disjoint 3x3 neighborhoods")
        exc.incompatible_axes = axes
        raise exc
    rich = [(h, w) for h, w in choices if (h // 3) * (w // 3) >= n + 3]
    choices = rich or choices
    anchors = [p for p in _PROFILES if p[:2] in choices]
    anchor = ctx.draw_rng("canonical_profile").choice(anchors) if core and anchors else None
    heights = sorted({h for h, _ in choices})
    h = ctx.draw_choice("grid_h", heights + ([anchor[0]] * 40 if anchor else []))
    widths = sorted({w for hh, w in choices if hh == h})
    favored_w = [anchor[1]] * 40 if anchor and anchor[1] in widths else []
    w = ctx.draw_choice("grid_w", widths + favored_w)
    return h, w, anchor


def _positions(h, w, count, rng):
    """Start with guaranteed packing, then relocate each neighborhood freely."""
    slots = [(r, c) for r in range(1, h - 1, 3) for c in range(1, w - 1, 3)]
    rng.shuffle(slots)
    selected = slots[:count]
    if len(selected) != count:
        raise RuntimeError("internal packing capacity disagrees with dimensions")
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    order = list(range(count))
    rng.shuffle(order)
    for index in order:
        others = selected[:index] + selected[index + 1:]
        legal = [p for p in candidates
                 if all(max(abs(p[0]-q[0]), abs(p[1]-q[1])) >= 3 for q in others)]
        selected[index] = rng.choice(legal)
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    requested = _validated_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=requested)
    core = ctx.draw_choice("profile_component", ("canonical", "wide")) == "canonical"
    h, w, anchor = _dimensions(ctx, requested, core)
    capacity = (h // 3) * (w // 3)
    if "n_pluses" in requested:
        n = ctx.draw_int("n_pluses", 1, 6)
    else:
        maximum = min(6, max(1, capacity - 3))
        favored = min(2, maximum) if core else (1 if difficulty == "easy" else maximum)
        n = ctx.draw_choice("n_pluses", list(range(1, maximum + 1)) + [favored] * 5)
    if "palette_size" in requested:
        palette_size = ctx.draw_int("palette_size", 1, 9)
    else:
        palette_size = ctx.draw_choice("palette_size", list(range(2, 10)) + ([anchor[2]] * 40 if anchor else []))
    if "n_distinct_colors" in requested:
        ctx.draw_int("n_distinct_colors", 1, 9)
    colors = ctx.draw_distinct_colors("colors", n=palette_size, exclude=(0,))
    n_decoys = min(3, capacity - n)
    positions = _positions(h, w, n + n_decoys, ctx.draw_rng("layout"))
    grid = full_grid(h, w, 0)
    protected = set()
    paint = ctx.draw_rng("motif_colors")
    missing, mismatched = (0, 1) if sample_index % 2 == 0 else (2, 3)
    for index, (r, c) in enumerate(positions):
        color = paint.choice(colors)
        alternative = paint.choice([v for v in colors if v != color]) if palette_size > 1 else color
        protected.add((r, c))
        for direction, (dr, dc) in enumerate(_DIRECTIONS):
            point = (r + dr, c + dc)
            protected.add(point)
            value = color
            if index == n and direction == missing:
                value = 0
            elif index == n + 1 and direction == mismatched:
                value = alternative if palette_size > 1 else 0
            grid[point[0]][point[1]] = value
        if index == n + 2:
            grid[r][c] = alternative
    # Unused requested colors get a singleton in an unprotected zero. Because
    # each is a new color, it cannot accidentally complete a matching 4-arm set.
    used = {value for row in grid for value in row}
    extra = [color for color in colors if color not in used]
    free = [(r, c) for r in range(h) for c in range(w)
            if grid[r][c] == 0 and (r, c) not in protected]
    ctx.draw_rng("palette_singletons").shuffle(free)
    if len(free) < len(extra):
        raise RuntimeError("insufficient free singleton cells for requested palette")
    for (r, c), color in zip(free, extra):
        grid[r][c] = color
    if len(_same_color_plus_centers(grid)) != n:
        raise RuntimeError("placement created or lost an eligible center")
    return grid


def _same_color_plus_centers(grid):
    centers = []
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            values = [grid[r+dr][c+dc] for dr, dc in _DIRECTIONS]
            if grid[r][c] == 0 and values[0] != 0 and len(set(values)) == 1:
                centers.append((r, c))
    return centers


def observe_overrides(grid):
    count = len({value for row in grid for value in row} - {0})
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pluses": len(_same_color_plus_centers(grid)),
            "palette_size": count, "n_distinct_colors": count}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30):
        return ["positive local-completion examples use dimensions 3..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    if not _same_color_plus_centers(grid):
        return ["no zero center with four same-colored nonzero cardinal neighbors"]
    return []


def strict_canonical_like(grid):
    """Positive examples of the local rule; connected near misses remain lawful."""
    return self_check(grid)


def _draw_from_degenerate(name, rng):
    """Negative validator fixtures, not accepted generate(texture=...) controls."""
    grid = full_grid(8, 8, 0)
    if name == "no_pluses":
        grid[2][2], grid[5][5] = 4, 7
    elif name == "mismatched_neighbors":
        grid[2][3], grid[4][3], grid[3][2], grid[3][4] = 4, 6, 7, 8
    elif name == "center_already_filled":
        grid[2][2] = grid[4][2] = grid[3][1] = grid[3][3] = 5
        grid[3][2] = 9
    else:
        raise ValueError(f"unknown negative fixture {name!r}")
    return grid


def _subset_rival(grid, *, directions):
    """Deliberately wrong rule that omits at least one cardinal condition."""
    out = [list(row) for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            values = [grid[r+_DIRECTIONS[i][0]][c+_DIRECTIONS[i][1]] for i in directions]
            if grid[r][c] == 0 and values[0] != 0 and len(set(values)) == 1:
                out[r][c] = values[0]
    return out


def _unanimity_rival(grid, *, mode):
    """Wrong majority, equality-blind, or occupied-center rule; never label authority."""
    out = [list(row) for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            values = [grid[r+dr][c+dc] for dr, dc in _DIRECTIONS]
            color, count = Counter(values).most_common(1)[0]
            if mode == "overwrite":
                if values[0] != 0 and len(set(values)) == 1:
                    out[r][c] = values[0]
            elif grid[r][c] == 0:
                if mode == "majority" and color != 0 and count >= 3:
                    out[r][c] = color
                elif mode == "nonzero" and all(values):
                    out[r][c] = values[0]
    return out


_SUBSETS = {"north_south_only": (0, 1), "west_east_only": (2, 3),
            "omit_north": (1, 2, 3), "omit_south": (0, 2, 3),
            "omit_west": (0, 1, 3), "omit_east": (0, 1, 2)}
SEMANTIC_RIVALS = {name: partial(_subset_rival, directions=directions)
                   for name, directions in _SUBSETS.items()}
SEMANTIC_RIVALS.update({"majority_three": partial(_unanimity_rival, mode="majority"),
                        "nonzero_without_equality": partial(_unanimity_rival, mode="nonzero"),
                        "overwrite_occupied_center": partial(_unanimity_rival, mode="overwrite")})
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes_rival(grid, *, name):
    """Executable local counterexample predicate, independently checked by Racket."""
    prediction = SEMANTIC_RIVALS[name](grid)
    eligible = set(_same_color_plus_centers(grid))
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            expected = grid[r-1][c] if (r, c) in eligible else value
            if prediction[r][c] != expected:
                return True
    return False


SEMANTIC_WITNESSES = {"refutes_" + name: partial(_refutes_rival, name=name)
                       for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {"refutes_" + name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a claim of universal rule uniqueness."""
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
