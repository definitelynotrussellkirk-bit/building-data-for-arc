"""Inputs for M110: count same-color FOUR-connected components of 1/2/3.

Version 3 removes the singleton/lattice shortcut. Components have independent
areas, may touch different colors and borders, and can touch diagonally without
merging. Colors 4..9 are irrelevant distractors. Labels still come from Racket.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc91f4798e24"
TASK_ID = "dc91f4798e24"
VERSION = "3.0.1"
RULE_HASH = "1493886adfda"
SUMMARY = (
    "Count the four-connected components of colors 1, 2, 3, not their areas. "
    "Random connected shapes, diagonal contacts, border contacts and optional "
    "colors 4..9 break pixel-count, eight-connected and color-blind shortcuts. "
    "Output is a three-row left-aligned histogram of width max(1, counts)."
)
INVARIANTS = [
    "rectangular ARC grid with colors 0..9 and positive counts of 1, 2, 3",
    "at least two target-color component counts differ on ordinary draws",
    "ordinary draws have at least one multi-cell target component",
    "growth never joins two planted components of the same color",
]
HELPFUL_TEXTURES = ("default", "sparse", "dense", "varied", "diagonal")
DEGENERATE_TEXTURES = ("equal_counts", "missing_color", "no_components")
AXES = {
    "grid_h": {"type": "int", "default": "40% canonical-scale, else difficulty-scaled 7..18", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "40% canonical-scale, else difficulty-scaled 8..22", "valid": "8..22"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "|".join(HELPFUL_TEXTURES)},
}
# Every listed axis can be combined; unexpected placement failures are defects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"Unknown override axis/axes: {unknown}; supported: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    # Reject bools/fractions instead of silently truncating dimensions in GenCtx.
    for key in ("grid_h", "grid_w"):
        value = overrides.get(key)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{key} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Keep the original shape/palette envelope represented at EVERY band.
    # These are dimension profiles only, never copies of canonical grids.
    scale_rng = ctx.draw_rng("scale_profile")
    canonical_scale = scale_rng.random() < 0.4
    preferred_h, preferred_w = scale_rng.choice(((7, 8), (8, 9), (8, 11), (9, 9), (9, 10)))
    def dimension(key, lo, hi, preferred):
        if overrides.get(key) is not None:
            return ctx.draw_int(key, lo, hi)
        if canonical_scale:
            return ctx.draw_choice(key, (preferred,))
        return ctx.draw_int_diff(key, lo, hi)
    h = dimension("grid_h", 7, 18, preferred_h)
    w = dimension("grid_w", 8, 22, preferred_w)
    choices = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") is not None else HELPFUL_TEXTURES
    texture = ctx.draw_choice("texture", choices)
    if texture in DEGENERATE_TEXTURES:
        return _draw_degenerate(texture, h, w)

    rng = ctx.draw_rng("counts")
    cmax = min({"easy": 3, "hard": 7}.get(difficulty, 5), h * w // 12)
    triples = [(a, b, c) for a in range(1, cmax + 1)
               for b in range(1, cmax + 1) for c in range(1, cmax + 1)
               if len({a, b, c}) > 1]
    counts = rng.choice(triples)
    diagonal = texture == "diagonal" or (
        texture in ("default", "varied") and ctx.draw_rng("diagonal").random() < 0.5)
    area_max = {"sparse": 2, "default": 3, "dense": 5, "varied": 6, "diagonal": 4}[texture]
    # Cap area on small grids without changing the requested component counts.
    area_max = min(area_max, max(2, h * w // (2 * sum(counts))))
    sizes_rng = ctx.draw_rng("areas")
    sizes = [sizes_rng.randint(1, area_max) for _ in range(sum(counts))]
    sizes[sizes_rng.randrange(len(sizes))] = area_max  # break pixel counting on every ordinary draw
    for attempt in range(64):
        grid = _place(h, w, counts, sizes, diagonal, ctx.draw_rng(f"layout-{attempt}"))
        if grid is not None:
            break
    else:
        raise RuntimeError(f"Placement exhausted: seed={seed}, index={sample_index}, "
                           f"shape={(h, w)}, counts={counts}, texture={texture}")
    # Distractors never overwrite targets. They may touch/bridge target colors;
    # the rule's components are monochromatic, not binary foreground islands.
    noise = ctx.draw_rng("noise")
    noise_max = {"sparse": 1, "default": 2, "dense": 4, "varied": 5, "diagonal": 3}[texture]
    n_noise = 1 if canonical_scale else noise.randint(0, noise_max)
    if n_noise:
        palette = noise.sample(list(range(4, 10)), 1 if texture != "varied" else noise.randint(1, 3))
        free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
        noise.shuffle(free)
        for r, c in free[:n_noise]:
            grid[r][c] = noise.choice(palette)
    return grid


def _place(h, w, counts, sizes, diagonal, rng):
    """Plant components then grow them, preserving same-color ownership."""
    grid = full_grid(h, w, 0)
    owner = [[-1 for _ in range(w)] for _ in range(h)]
    colors = [color for color, count in zip((1, 2, 3), counts) for _ in range(count)]
    bodies = [[] for _ in colors]

    def permitted(r, c, index):
        return (0 <= r < h and 0 <= c < w and grid[r][c] == 0
                and all(not (0 <= r + dr < h and 0 <= c + dc < w)
                        or grid[r + dr][c + dc] != colors[index]
                        or owner[r + dr][c + dc] == index
                        for dr, dc in _NEIGHBORS))

    def paint(r, c, index):
        grid[r][c] = colors[index]
        owner[r][c] = index
        bodies[index].append((r, c))

    if diagonal:
        color = rng.choice([c for c, count in zip((1, 2, 3), counts) if count >= 2])
        indices = [i for i, c in enumerate(colors) if c == color][:2]
        r, c = rng.randrange(h - 1), rng.randrange(w - 1)
        if rng.randrange(2):
            paint(r, c + 1, indices[0]); paint(r + 1, c, indices[1])
        else:
            paint(r, c, indices[0]); paint(r + 1, c + 1, indices[1])
    order = list(range(len(colors)))
    rng.shuffle(order)
    for index in order:
        if bodies[index]:
            continue
        # Uniform rejection sampling avoids scanning the whole canvas for
        # every seed. The bounded fallback is also uniform over legal cells.
        for _ in range(32):
            r, c = rng.randrange(h), rng.randrange(w)
            if permitted(r, c, index):
                paint(r, c, index)
                break
        else:
            candidates = [(r, c) for r in range(h) for c in range(w)
                          if permitted(r, c, index)]
            if not candidates:
                return None
            paint(*rng.choice(candidates), index)
    rng.shuffle(order)
    for index in order:
        while len(bodies[index]) < sizes[index]:
            # Sorted sets prevent PYTHONHASHSEED-dependent frontier order.
            frontier = sorted({(r + dr, c + dc) for r, c in bodies[index]
                               for dr, dc in _NEIGHBORS if permitted(r + dr, c + dc, index)})
            if not frontier:
                return None
            paint(*rng.choice(frontier), index)
    return grid


def _components(grid, color, connectivity=4):
    h, w = len(grid), len(grid[0])
    seen, comps = set(), []
    moves = _NEIGHBORS if connectivity == 4 else _NEIGHBORS + ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack, comp = [(r, c)], []
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in moves:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Validate ordinary task inputs, including all canonical demonstrations.

    Multi-cell witnesses are checked by tests/semantic hooks, not required of
    arbitrary lawful inputs: a singleton-only input is still a valid instance.
    Explicit degenerates intentionally fall outside this default curriculum.
    """
    if (not isinstance(grid, (list, tuple)) or not grid
            or not all(isinstance(row, (list, tuple)) for row in grid)
            or not grid[0] or any(len(row) != len(grid[0]) for row in grid)):
        return ["expected a nonempty rectangular grid"]
    if not (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30):
        return ["grid dimensions must be 1..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid cells must be integer ARC colors 0..9"]
    counts = [len(_components(grid, c)) for c in (1, 2, 3)]
    errors = [f"color {c} is absent; default teaches all three rows"
              for c, count in zip((1, 2, 3), counts) if not count]
    if len(set(counts)) == 1:
        errors.append(f"component counts are not contrasted: {counts}")
    if max(counts) > 30:
        errors.append("component histogram would exceed ARC width 30")
    return errors


def _draw_degenerate(name, h, w):
    grid = full_grid(h, w, 0)
    if name != "no_components":
        for c in (1, 2, 3):
            if name == "missing_color" and c == 2:
                continue
            grid[1][2 * c - 1] = c
            grid[3][2 * c - 1] = c
    return grid


def _bars(counts):
    width = max(1, *counts)
    return [[color if c < count else 0 for c in range(width)]
            for color, count in zip((1, 2, 3), counts)]


def _histogram(grid):
    """Diagnostic Python oracle only; generate() never emits labels."""
    return _bars([len(_components(grid, c)) for c in (1, 2, 3)])


def _pixel_rival(grid):
    return _bars([sum(row.count(c) for row in grid) for c in (1, 2, 3)])


def _eight_rival(grid):
    return _bars([len(_components(grid, c, 8)) for c in (1, 2, 3)])


def _binary_rival(grid):
    binary = [[int(bool(v)) for v in row] for row in grid]
    islands = _components(binary, 1)
    return _bars([sum(any(grid[r][col] == color for r, col in island) for island in islands)
                  for color in (1, 2, 3)])


def strict_canonical_like(grid):
    # Semantic domain, not an exact shape/position template.
    return self_check(grid)


def _multi_witness(grid):
    return _pixel_rival(grid) != _histogram(grid)


def _diagonal_witness(grid):
    return _eight_rival(grid) != _histogram(grid)


def _binary_witness(grid):
    return _binary_rival(grid) != _histogram(grid)


SEMANTIC_RIVALS = {"pixel_count": _pixel_rival, "eight_connected": _eight_rival,
                   "binary_foreground": _binary_rival}
SEMANTIC_WITNESSES = {"multi_cell": _multi_witness, "diagonal_contact": _diagonal_witness,
                      "color_separation": _binary_witness}
WITNESS_RIVALS = {"multi_cell": ["pixel_count"], "diagonal_contact": ["eight_connected"],
                  "color_separation": ["binary_foreground"]}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"eight_connected": _eight_rival, "binary_foreground": _binary_rival}
