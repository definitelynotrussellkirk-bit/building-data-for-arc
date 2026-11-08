"""Generator for arc_puzzle_bank_21_set6:medium_f04 — object halos.

Rule: each separated object gets a 1-cell orthogonal halo of its color
drawn in surrounding background cells.

Combinatorial axes: grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, touching_objects, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e826540d45d"
VERSION = "1.4.1"
TASK_ID = "7e826540d45d"

SUMMARY = (
    "Separated small objects whose orthogonal halos can be drawn without overlap; "
    "exact size, object-count and distinct-color controls are observable, while "
    "palette_size controls the sampled color pool."
)

INVARIANTS = [
    "background is 0",
    "objects are separated by at least two blank cells",
    "objects may share colors only when n_distinct_colors requests it",
    "each object has in-bounds blank neighbors for a visible halo",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 8, 9),
    "varied": (1, 2, 4, 6, 8),
}
DEGENERATE_TEXTURES = ("no_objects", "touching_objects", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "default",
                       "valid": "default|warm|cool|varied"},
    "n_objects":      {"type": "int", "default": "3", "valid": "1..5"},
    # This is a real input to color sampling but is not recoverable exactly from
    # a grid when the pool is larger than the number of objects.
    "palette_size":   {"type": "int", "default": "3", "valid": "1..5",
                       "exact": False, "probe": "diagnostic"},
    "position_bias":  {"type": "str", "default": "wide_separation_for_halos",
                       "valid": "wide_separation_for_halos", "probe": "diagnostic"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse",
                       "probe": "diagnostic"},
    "texture":        {"type": "str", "default": "default",
                       "valid": "default|warm|cool|varied",
                       "doc": "Backward-compatible alias for palette_kind."},
}

# Singletons and dominoes make the full advertised 1..5 object range feasible
# even at the smallest exact canvas; larger shapes retain the original grammar.
SHAPES = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _components(grid):
    """Return same-color 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def observe_overrides(grid):
    """Recover every exact, grid-observable numeric axis."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    objects = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(objects),
        "n_distinct_colors": len({color for color, _ in objects}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify a rectangular board with separated visible source objects."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    objects = _components(grid)
    if not objects:
        return ["expected at least one nonzero object"]
    h = len(grid)
    errors = []
    for _color, cells in objects:
        if any(not (1 <= r < h - 1 and 1 <= c < w - 1) for r, c in cells):
            errors.append("objects must leave an in-bounds halo margin")
            break

    # The generator's placement contract keeps every pair of object cells out
    # of the other's two-cell Chebyshev neighborhood.  This both preserves two
    # blank cells of separation and prevents one-ring halos from overlapping.
    for index, (_color, cells) in enumerate(objects):
        for _other_color, other_cells in objects[index + 1 :]:
            if any(
                abs(r - rr) <= 2 and abs(c - cc) <= 2
                for r, c in cells
                for rr, cc in other_cells
            ):
                errors.append("objects must remain separated so halo zones do not overlap")
                return errors
    return errors


def _clear(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    rs = [r0 + r for r, _ in cells]
    cs = [c0 + c for _, c in cells]
    if min(rs) < 1 or min(cs) < 1 or max(rs) >= h - 1 or max(cs) >= w - 1:
        return False
    for r in range(max(0, min(rs) - 2), min(h, max(rs) + 3)):
        for c in range(max(0, min(cs) - 2), min(w, max(cs) + 3)):
            if g[r][c] != 0:
                return False
    return True


def _incompatible(message, *axes):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(dict.fromkeys(axes))
    return exc


def _strict_request(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override: " + ", ".join(sorted(unknown)))


def _explicit_int(overrides, name):
    if name not in overrides:
        return None
    value = overrides[name]
    if type(value) is not int:
        raise TypeError(f"{name} override must be an integer (not bool)")
    return value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_request(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(requested_texture, overrides)

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_bounds, w_bounds = (10, 11), (12, 13)
    elif difficulty == "hard":
        h_bounds, w_bounds = (13, 16), (16, 18)
    else:
        h_bounds, w_bounds = (10, 13), (12, 16)
    h = ctx.draw_int_strict("grid_h", *((8, 16) if "grid_h" in overrides else h_bounds))
    w = ctx.draw_int_strict("grid_w", *((10, 18) if "grid_w" in overrides else w_bounds))

    requested_distinct = _explicit_int(overrides, "n_distinct_colors")
    default_objects = max(3, requested_distinct or 0)
    n_objects = ctx.draw_int_strict(
        "n_objects", *((1, 5) if "n_objects" in overrides else (default_objects, default_objects))
    )
    default_palette_size = max(3, requested_distinct or 0)
    palette_size = ctx.draw_int_strict(
        "palette_size",
        *((1, 5) if "palette_size" in overrides else (default_palette_size, default_palette_size)),
    )
    default_distinct = min(3, n_objects, palette_size)
    n_distinct = ctx.draw_int_strict(
        "n_distinct_colors",
        *((1, 5) if "n_distinct_colors" in overrides else (default_distinct, default_distinct)),
    )
    if n_distinct > n_objects:
        raise _incompatible(
            "n_distinct_colors cannot exceed n_objects",
            "n_distinct_colors", "n_objects",
        )
    if n_distinct > palette_size:
        raise _incompatible(
            "n_distinct_colors cannot exceed palette_size",
            "n_distinct_colors", "palette_size",
        )

    explicit_kind = overrides.get("palette_kind")
    explicit_texture = overrides.get("texture")
    if explicit_kind is not None and explicit_texture is not None and explicit_kind != explicit_texture:
        raise _incompatible(
            "palette_kind and texture aliases must agree",
            "palette_kind", "texture",
        )
    requested_kind = explicit_kind or explicit_texture or "default"
    kind_options = PALETTE_KINDS if explicit_kind is not None else (requested_kind,)
    palette_kind = ctx.draw_choice("palette_kind", kind_options)
    texture_options = PALETTE_KINDS if explicit_texture is not None else (palette_kind,)
    texture = ctx.draw_choice("texture", texture_options)
    if texture != palette_kind:
        raise _incompatible(
            "palette_kind and texture aliases must agree",
            "palette_kind", "texture",
        )
    ctx.draw_choice("position_bias", ("wide_separation_for_halos",))
    ctx.draw_choice("density", ("sparse",))

    palette = list(PALETTES[palette_kind])
    if palette_size > len(palette):
        raise _incompatible(
            "palette_size exceeds the selected palette",
            "palette_size", "palette_kind",
        )

    rng = ctx.draw_rng("layout")
    sampled = rng.sample(palette, palette_size)
    distinct = sampled[:n_distinct]
    colors = [distinct[index % n_distinct] for index in range(n_objects)]

    # Reset-and-retry is deterministic because the same keyed RNG advances.
    # Compact shapes and exhaustive position scans make all ordinary and every
    # individually pinned control feasible; only genuinely conflicting exact
    # combinations can exhaust the bounded search.
    positions = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for _outer in range(80):
        g = full_grid(h, w, 0)
        ok = True
        for object_index, color in enumerate(colors):
            shapes = list(SHAPES)
            rng.shuffle(shapes)
            starts = list(positions)
            rng.shuffle(starts)
            placed = False
            for cells in shapes:
                for r0, c0 in starts:
                    if _clear(g, r0, c0, cells):
                        for dr, dc in cells:
                            g[r0 + dr][c0 + dc] = color
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                ok = False
                break
        if ok and len(_components(g)) == n_objects:
            return g
    axes = [name for name in ("grid_h", "grid_w", "n_objects") if name in overrides]
    raise _incompatible(
        f"could not place {n_objects} separated halo objects in {h}x{w}",
        *(axes or ("grid_h", "grid_w", "n_objects")),
    )


def _draw_from_degenerate(name, overrides):
    h = overrides.get("grid_h", 11)
    w = overrides.get("grid_w", 13)
    if type(h) is not int or not 8 <= h <= 16:
        raise ValueError("grid_h override must be an integer in 8..16")
    if type(w) is not int or not 10 <= w <= 18:
        raise ValueError("grid_w override must be an integer in 10..18")
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "touching_objects":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (2, 0)]:
            g[2 + dr][5 + dc] = 6
        return g
    if name == "single_object":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[h // 2 + dr][w // 2 + dc] = 4
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
