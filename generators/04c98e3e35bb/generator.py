"""Border contact of SAME-COLOR four-connected components (04c98e3e35bb).

This module samples inputs. The pinned Racket program remains the label authority.
Default lessons mix contact witnesses with unconstrained object layouts. Diagnostic
Python predictions below are declared rivals/witnesses, never training labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects
from puzzle_generators.helpers.shape import normalize, rect_cells

GENERATOR_ID = "04c98e3e35bb"
TASK_ID = GENERATOR_ID
RULE_HASH = "264a1a87abe5"
VERSION = "3.2.0"
SUMMARY = (
    "On fixed background 0, recolor each same-color four-connected component "
    "to 2 when it touches any grid edge, otherwise to 8. Input colors 1..9, "
    "including 2 and 8, are legal. Different-color contacts and same-color "
    "diagonal contacts do not join components. Every production input has "
    "at least one border component and one strictly interior component."
)
INVARIANTS = [
    "rectangular integer grid, dimensions 6..25, fixed background 0",
    "one to four border and one to four interior same-color four-components in generated inputs",
    "validator also accepts lawful canonical inputs and larger component counts",
    "input palette may include output colors 2 and 8",
    "counts are realized exactly; incomplete placement raises instead of returning fewer objects",
]
OBJ_SHAPES = ("rect", "L", "T", "plus", "blob", "line", "single")
HELPFUL_TEXTURES = ("mixed",) + OBJ_SHAPES
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "canonical profile / band-weighted 6..25", "valid": "6..25"},
    "grid_w": {"type": "int", "default": "canonical profile / band-weighted 6..25", "valid": "6..25"},
    "n_border_objs": {"type": "int", "default": "1..4", "valid": "1..4"},
    "n_interior_objs": {"type": "int", "default": "1..4", "valid": "1..4"},
    "obj_color": {"type": "color", "default": "uniform 1..9", "valid": "1..9",
                  "doc": "Exact color of the first occupied cell in row-major order; other colors are independently permuted."},
    "mixed_colors": {"type": "bool", "default": "true in contact profiles; random in free layouts", "valid": "0|1",
                     "doc": "False means exactly one foreground color; true means at least two."},
    "obj_size_min": {"type": "int", "default": "1", "valid": "1..5",
                     "doc": "Lower shape-construction scale, not an exact cell count. T uses at least 3; L/line/plus at least 2. Singletons ignore scale and reject explicit scale combinations."},
    "obj_size_max": {"type": "int", "default": "2", "valid": "2..6",
                     "doc": "Upper random construction scale before intrinsic shape minima; not a bounding-box bound. Mixed texture includes singleton draws. Incompatible min/max or packing requests raise with named axes."},
    "texture": {"type": "str", "default": "mixed", "valid": "mixed|rect|L|T|plus|blob|line|single"},
}
# obj_shape remains a checked compatibility alias, not a second independent axis.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 16
SCHEDULE_PROFILES = ("contact_0", "contact_1", "contact_2", "contact_3", "free")
_PROFILES = ((6, 6, 3), (7, 7, 4), (8, 8, 4), (7, 9, 5))


class IncompatibleOverrides(ValueError):
    """A refused joint request with the controls needed to reproduce it."""
    def __init__(self, reason, axes):
        super().__init__(reason)
        self.incompatible_axes = tuple(sorted(set(axes)))


def schedule_profile(seed, sample_index, difficulty=None):
    if sample_index % 4 == 3:
        return "free"
    return "contact_" + str((sample_index // 4 + sample_index % 4) % 4)


def _components(grid, *, diagonal=False, univalued=True):
    return find_objects(grid, bg=0, without_bg=True, univalued=univalued, diagonal=diagonal)


def _border(obj, h, w):
    return any(r in (0, h-1) or c in (0, w-1) for _, (r, c) in obj)


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    h, w = len(grid), len(grid[0])
    if not 6 <= h <= 25 or not 6 <= w <= 25:
        return ["grid dimensions must be 6..25"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integers 0..9, excluding booleans"]
    if not any(v == 0 for row in grid for v in row):
        return ["fixed background 0 must be present"]
    objs = _components(grid)
    if not objs:
        return ["at least one nonzero component is required"]
    border = sum(_border(obj, h, w) for obj in objs)
    reasons = []
    if border == 0:
        reasons.append("need at least one border-touching component")
    if border == len(objs):
        reasons.append("need at least one strictly interior component, not merely an interior cell")
    return reasons


def strict_canonical_like(grid):
    """Task-domain validity, including contact cases, not exact profile equality."""
    return self_check(grid)


def observe_overrides(grid):
    h, w = len(grid), len(grid[0])
    objs = _components(grid)
    nb = sum(_border(obj, h, w) for obj in objs)
    colors = [v for row in grid for v in row if v]
    return {"grid_h": h, "grid_w": w, "n_border_objs": nb,
            "n_interior_objs": len(objs)-nb, "obj_color": colors[0],
            "mixed_colors": len(set(colors)) > 1}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - {"obj_shape"}
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = {k: v for k, v in overrides.items() if v is not None}
    for name, value in clean.items():
        if name in ("texture", "obj_shape"):
            if value not in HELPFUL_TEXTURES:
                raise ValueError(f"unknown {name}: {value!r}")
        elif name == "mixed_colors":
            if type(value) not in (int, bool) or value not in (0, 1):
                raise ValueError("mixed_colors must be bool or integer 0/1")
        elif type(value) is not int:
            raise ValueError(f"{name} must be an integer, excluding booleans")
    if "obj_shape" in clean:
        if "texture" in clean and clean["texture"] != clean["obj_shape"]:
            raise IncompatibleOverrides("obj_shape and texture aliases disagree", ("obj_shape", "texture"))
        clean["texture"] = clean.pop("obj_shape")
    if clean.get("texture") == "single" and {"obj_size_min", "obj_size_max"} & set(clean):
        raise IncompatibleOverrides("singleton shape has no size scale", set(clean) & {"texture", "obj_size_min", "obj_size_max"})
    return clean


def _control(ctx, name, default):
    """Keep explicit domains independent of the default curriculum distribution."""
    spec = AXES[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        if spec["type"] == "bool":
            return bool(ctx.draw_choice(name, (False, True)))
        if spec["type"] == "str":
            return ctx.draw_choice(name, HELPFUL_TEXTURES)
        lo, hi = (int(v) for v in spec["valid"].split(".."))
        return ctx.draw_int_strict(name, lo, hi)
    # A singleton conditional distribution is intentional: its value was
    # selected by the keyed profile/geometry RNG and is still recorded here.
    return ctx.draw_choice(name, (default,))


def _shape_cells(shape, s_min, s_max, rng):
    if shape == "single":
        return [(0, 0)]
    if shape == "rect":
        return normalize(rect_cells(rng.randint(s_min, s_max), rng.randint(s_min, s_max)))
    if shape == "L":
        n = max(2, rng.randint(s_min, s_max))
        return [(0, c) for c in range(n)] + [(r, 0) for r in range(1, n)]
    if shape == "T":
        n = max(3, rng.randint(s_min, s_max))
        return [(0, c) for c in range(n)] + [(r, n//2) for r in range(1, n)]
    if shape == "plus":
        n = max(2, rng.randint(s_min, s_max))
        return normalize([(0, c) for c in range(-n+1, n)] + [(r, 0) for r in range(-n+1, n)])
    if shape == "line":
        n = max(2, rng.randint(s_min, s_max))
        return [(0, c) for c in range(n)] if rng.randrange(2) else [(r, 0) for r in range(n)]
    if shape == "blob":
        target = rng.randint(s_min, s_max) + 1
        cells = {(0, 0)}
        while len(cells) < target:
            frontier = sorted({(r+dr, c+dc) for r, c in cells
                               for dr, dc in ((-1,0),(1,0),(0,-1),(0,1))} - cells)
            cells.add(rng.choice(frontier))
        return normalize(cells)
    raise ValueError(f"unknown shape: {shape}")


def _transform(grid, rng, *, transpose=True):
    if rng.randrange(2):
        grid = list(reversed(grid))
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if transpose and rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    return grid


def _recolor_symbols(grid, anchor, rng, *, interior_palette=False):
    symbols = sorted({v for row in grid for v in row if v})
    first = next(v for row in grid for v in row if v)
    mapping = {first: anchor}
    if interior_palette:
        h, w = len(grid), len(grid[0])
        interior_symbols = sorted({v for obj in _components(grid) if not _border(obj, h, w) for v, _ in obj})
        choices = [v for v in interior_symbols if v != first]
        rng.shuffle(choices)
        for color in (2, 8):
            if any(mapping.get(v) == color for v in interior_symbols):
                continue
            mapping[choices.pop()] = color
    available = [v for v in range(1, 10) if v not in mapping.values()]
    rng.shuffle(available)
    for symbol in symbols:
        if symbol not in mapping:
            mapping[symbol] = available.pop()
    return [[mapping[v] if v else 0 for v in row] for row in grid]


def _contact_grid(ctx, profile, anchor):
    """A movable contact motif plus extra objects; no canonical grids replayed."""
    rng = ctx.draw_rng("contact_geometry")
    h, w, palette = _PROFILES[profile]
    g = full_grid(h, w, 0)
    # Congruent L components have opposite outcomes. Their diagonal contact
    # and a third, differently colored bridge distinguish four rival rules.
    # Keep an arm cell strictly inside: a corner L alone has no such cell.
    offset = rng.randint(1, w-5)
    for r, c in ((0,0), (0,1), (1,0), (2,1), (2,2), (3,1)):
        g[r][c+offset] = 1
    for r, c in ((1,1), (1,2), (1,3)):
        g[r][c+offset] = 2
    # New colors can touch existing objects: only equal-color 4-contact merges.
    interior = [(r,c) for r in range(1,h-1) for c in range(1,w-1) if not g[r][c]]
    rng.shuffle(interior)
    for symbol in range(3, min(palette,4)+1):
        r,c = interior.pop()
        g[r][c] = symbol
    # Reflections preserve every listed canonical dimension profile. The free
    # quarter supplies unrelated aspect ratios and arbitrary object placement.
    g = _transform(g, ctx.draw_rng("contact_orientation"), transpose=(h == w))
    # A later independent solver selected one largest object per color, using
    # row-major order to break ties. If the interior L would win that tie,
    # extend the main border L by one edge cell. Otherwise retain both sizes.
    # The largest/first object is now a border object in either orientation,
    # so choosing it for cyan is observably wrong in every contact draw.
    symbol_one = [obj for obj in _components(g) if next(iter(obj))[0] == 1]
    border_cells = {cell for obj in symbol_one if _border(obj,h,w) for _,cell in obj}
    interior_cells = {cell for obj in symbol_one if not _border(obj,h,w) for _,cell in obj}
    if min(interior_cells) < min(border_cells):
        extensions = [(r,c) for r in range(h) for c in range(w)
                      if (r in (0,h-1) or c in (0,w-1)) and not g[r][c]
                      and any((r+dr,c+dc) in border_cells for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))
                      and not any((r+dr,c+dc) in interior_cells for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))]
        if not extensions:
            raise RuntimeError("contact profile has no border extension for rank witness")
        r,c = rng.choice(extensions)
        g[r][c] = 1
    # A separate small border object defeats the shape-based degree-two-loop
    # hypothesis independently authored from the earlier visible examples.
    # Its color also occurs in the contact motif, so singleton-color filtering
    # cannot hide it. Prefer a domino; use an isolated singleton if necessary.
    clear = []
    for r in range(h):
        for c in range(w):
            if r not in (0,h-1) and c not in (0,w-1):
                continue
            if all(g[nr][nc] == 0 for nr in range(max(0,r-1),min(h,r+2))
                   for nc in range(max(0,c-1),min(w,c+2))):
                clear.append((r,c))
    clear_set = set(clear)
    dominoes = [(point, neighbor) for point in clear
                for neighbor in ((point[0]+1,point[1]),(point[0],point[1]+1))
                if neighbor in clear_set]
    if not clear:
        raise RuntimeError("contact profile has no isolated border witness position")
    extra = rng.choice(dominoes) if dominoes else (rng.choice(clear),)
    for r,c in extra:
        g[r][c] = 1
    if palette == 5:
        first = next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v)
        border = [(r,c) for r in range(h) for c in range(w)
                  if (r in (0,h-1) or c in (0,w-1)) and not g[r][c] and (r,c) > first]
        r,c = rng.choice(border)
        g[r][c] = 5
    return _recolor_symbols(g, anchor, ctx.draw_rng("palette"), interior_palette=True)


def _packed_grid(ctx, h, w, nb, ni, texture, s_min, s_max, mixed, anchor, clean):
    rng = ctx.draw_rng("object_placement")
    # A repeated color is deliberate in monochrome mode; four-neighbor
    # separation preserves its object identities while allowing diagonals.
    n = nb + ni
    classes = [1]*n if not mixed else [1,2] + [rng.randint(1, min(5,n)) for _ in range(n-2)]
    rng.shuffle(classes)
    for attempt in range(12):
        g = full_grid(h, w, 0)
        success = True
        for index, color in enumerate(classes):
            border = index < nb
            placed = False
            # Mixed texture is a mixture of scales/shapes, including singleton
            # objects. The final attempt uses its singleton member to guarantee
            # exact count feasibility even in a 6x6 canvas; explicit shapes are
            # never changed or silently shrunk.
            for draw in range(18):
                shape = ("single" if attempt == 11 else rng.choice(OBJ_SHAPES)) if texture == "mixed" else texture
                cells = _shape_cells(shape, s_min, s_max, rng)
                cells_grid = full_grid(max(r for r,c in cells)+1, max(c for r,c in cells)+1, 0)
                for r,c in cells:
                    cells_grid[r][c] = 1
                cells_grid = _transform(cells_grid, rng)
                cells = [(r,c) for r,row in enumerate(cells_grid) for c,v in enumerate(row) if v]
                rh, rw = len(cells_grid), len(cells_grid[0])
                if border:
                    origins = [(r,c) for r in range(h-rh+1) for c in range(w-rw+1)
                               if r == 0 or c == 0 or r+rh == h or c+rw == w]
                else:
                    origins = [(r,c) for r in range(1,h-rh) for c in range(1,w-rw)]
                rng.shuffle(origins)
                for rr,cc in origins:
                    points = [(rr+r,cc+c) for r,c in cells]
                    if any(g[r][c] for r,c in points):
                        continue
                    if any(g[r+dr][c+dc] == color for r,c in points
                           for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))
                           if 0 <= r+dr < h and 0 <= c+dc < w):
                        continue
                    for r,c in points:
                        g[r][c] = color
                    placed = True
                    break
                if placed:
                    break
            if not placed:
                success = False
                break
        if success:
            return _recolor_symbols(g, anchor, ctx.draw_rng("palette"))
    raise IncompatibleOverrides(
        "cannot pack requested full objects within the bounded placement search; no short grid returned",
        set(clean) & {"grid_h", "grid_w", "n_border_objs", "n_interior_objs", "texture", "obj_size_min", "obj_size_max", "mixed_colors"})


def generate(seed, sample_index, *, difficulty=None, **overrides):
    clean = _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=clean)
    anchor = _control(ctx, "obj_color", ctx.draw_rng("anchor_color").randint(1,9))
    profile = schedule_profile(seed, sample_index, difficulty)
    if not clean and profile != "free":
        grid = _contact_grid(ctx, int(profile[-1]), anchor)
        realized = observe_overrides(grid)
        for key in ("grid_h", "grid_w", "n_border_objs", "n_interior_objs", "mixed_colors"):
            _control(ctx, key, realized[key])
        # Construction-scale values for the mixture are declared sampling knobs,
        # not recoverable extrema; they do not override the witness motif.
        _control(ctx, "texture", "mixed")
        _control(ctx, "obj_size_min", 1)
        _control(ctx, "obj_size_max", 2)
        return grid
    rng = ctx.draw_rng("free_profile")
    # Explicit-axis checks get roomy defaults, while dimension overrides remain
    # authoritative in every difficulty. Free production has a size curriculum.
    lo, hi = {"easy": (6,12), "hard": (12,25)}.get(difficulty, (8,18))
    default_h = 20 if clean else rng.randint(lo,hi)
    default_w = 20 if clean else rng.randint(lo,hi)
    h, w = _control(ctx,"grid_h",default_h), _control(ctx,"grid_w",default_w)
    nb = _control(ctx,"n_border_objs",rng.randint(1,3))
    ni = _control(ctx,"n_interior_objs",rng.randint(1,3))
    mixed = _control(ctx,"mixed_colors",bool(rng.randrange(2)))
    texture = _control(ctx,"texture","mixed")
    s_min = _control(ctx,"obj_size_min",1)
    s_max = _control(ctx,"obj_size_max",max(2,s_min))
    if s_min > s_max:
        raise IncompatibleOverrides("obj_size_min exceeds obj_size_max", ("obj_size_min","obj_size_max"))
    grid = _packed_grid(ctx,h,w,nb,ni,texture,s_min,s_max,mixed,anchor,clean)
    observed = observe_overrides(grid)
    if observed["n_border_objs"] != nb or observed["n_interior_objs"] != ni:
        raise RuntimeError("placement changed a requested component count")
    return grid


def _component_prediction(grid, *, diagonal=False, univalued=True, global_color=False):
    """Diagnostic Python interpretation; official checks obtain labels in Racket."""
    h, w = len(grid), len(grid[0])
    if global_color:
        palette = sorted({v for row in grid for v in row if v})
        objs = [{(v,(r,c)) for r,row in enumerate(grid) for c,value in enumerate(row) if value == v} for v in palette]
    else:
        objs = _components(grid, diagonal=diagonal, univalued=univalued)
    out = [list(row) for row in grid]
    for obj in objs:
        value = 2 if _border(obj,h,w) else 8
        for _, (r,c) in obj:
            out[r][c] = value
    return out


def _global_color(grid):
    return _component_prediction(grid, global_color=True)


def _color_blind_4(grid):
    return _component_prediction(grid, univalued=False)


def _same_color_8(grid):
    return _component_prediction(grid, diagonal=True)


def _color_blind_8(grid):
    return _component_prediction(grid, diagonal=True, univalued=False)


def _edge_cells_only(grid):
    h,w = len(grid),len(grid[0])
    return [[0 if not v else (2 if r in (0,h-1) or c in (0,w-1) else 8)
             for c,v in enumerate(row)] for r,row in enumerate(grid)]


def _preserve_input_2(grid):
    out = _component_prediction(grid)
    return [[2 if grid[r][c] == 2 else v for c,v in enumerate(row)] for r,row in enumerate(out)]


def _force_input_8_red(grid):
    out = _component_prediction(grid)
    return [[2 if grid[r][c] == 8 else v for c,v in enumerate(row)] for r,row in enumerate(out)]


def _degree_two_loop(grid):
    """Recolor occupancy using the degree-two chains seen in the examples."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}

    counts = {}
    for r, c in occupied:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    structural = {(r, c) for r, c in occupied if counts[grid[r][c]] > 1}

    def neighbors(cell):
        r, c = cell
        return {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} & structural

    degree_two = {cell for cell in structural if len(neighbors(cell)) == 2}
    unseen = set(degree_two)
    red = set()
    while unseen:
        start = unseen.pop()
        component = {start}
        pending = [start]
        while pending:
            cell = pending.pop()
            for other in neighbors(cell) & unseen:
                unseen.remove(other)
                component.add(other)
                pending.append(other)
        if len(component) == 3:
            red.update(component)

    return [[0 if (r, c) not in occupied else 2 if (r, c) in red else 8
             for c in range(w)] for r in range(h)]

def _largest_component(grid):
    """Keep one largest component per input color, breaking ties in scan order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()
    components_by_color = {}

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            pending = [(row, column)]
            seen.add((row, column))
            component = []
            while pending:
                current_row, current_column = pending.pop()
                component.append((current_row, current_column))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    neighbor_row = current_row + dr
                    neighbor_column = current_column + dc
                    neighbor = (neighbor_row, neighbor_column)
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_column < width
                        and neighbor not in seen
                        and grid[neighbor_row][neighbor_column] == color
                    ):
                        seen.add(neighbor)
                        pending.append(neighbor)
            components_by_color.setdefault(color, []).append(component)

    for components in components_by_color.values():
        selected = max(range(len(components)), key=lambda index: len(components[index]))
        for index, component in enumerate(components):
            replacement = 8 if index == selected else 2
            for row, column in component:
                output[row][column] = replacement

    return output


SEMANTIC_RIVALS = {"global_color": _global_color, "color_blind_4": _color_blind_4,
                   "same_color_8": _same_color_8, "color_blind_8": _color_blind_8,
                   "edge_cells_only": _edge_cells_only, "preserve_input_2": _preserve_input_2,
                   "force_input_8_red": _force_input_8_red, "degree_two_loop": _degree_two_loop,
                   "largest_component": _largest_component}
CANONICAL_SHORTCUTS = {name: fn for name, fn in SEMANTIC_RIVALS.items() if name not in ("edge_cells_only", "degree_two_loop", "largest_component")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_for(rival):
    return lambda grid: _component_prediction(grid) != rival(grid)


SEMANTIC_WITNESSES = {name: _witness_for(fn) for name,fn in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Require each declared rival to be refuted by an actual demonstration.

    This is a sufficient finite-rival teaching contract, not uniqueness among
    all programs. It intentionally does not inspect masked query labels.
    """
    return [f"demonstrations do not refute {name}" for name,rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]


def mutation_fixtures():
    border_only = full_grid(6,6,0)
    for r,c in ((0,0),(0,1),(1,0),(1,1)):
        border_only[r][c] = 3
    interior_only = full_grid(6,6,0)
    interior_only[2][2] = 2
    return [("border_cells_are_not_interior_component", border_only),
            ("missing_border_component", interior_only)]
