"""Input-only curriculum for the eight-neighbor, zero-center filling rule.

Two clean profiles retain canonical scale; two contrast profiles distinguish
cardinal-only filling, mixed-color enclosure, occupied centers and component
bounding boxes. All labels continue to come from the canonical Racket rule.
Diagnostic negative textures are deliberately outside AXES['texture'].valid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "98a65dc7fcb1"
VERSION = "2.0.0"
RULE_HASH = "7878169c3c87"
SUMMARY = "Fill only zero centers with eight equal nonzero neighbors; include decisive near-misses."
INVARIANTS = [
    "rectangular integer grid, colors 0..9, background 0",
    "ordinary draws contain the exact requested number of hollow monochrome 3x3 rings",
    "decoy motifs are not targets, and ordinary draws always change under the rule",
    "4x4 motif reservations have a blank-cell gap; attached positive rings are allowed",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = ("default", "contrast", "attached")
DEGENERATE_TEXTURES = ("no_rings", "filled_centers", "missing_corner")
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7..18, capacity-conditioned", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "scheduled 9..18, capacity-conditioned", "valid": "5..18"},
    "n_rings": {"type": "int", "default": "scheduled 1..6, capacity-conditioned", "valid": "1..6"},
    "n_decoys": {"type": "int", "default": "clean 0; contrast 3..6, capacity-conditioned", "valid": "0..6"},
    "palette_kind": {"type": "str", "default": "rng default|warm|cool|varied", "valid": "default|warm|cool|varied"},
    "texture": {"type": "str", "default": "scheduled default|contrast|attached", "valid": "default|contrast|attached"},
}
# Strict rejection policy. The capacity error carries the actual axis names.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = (0, 1, 2, 3)
OFFSETS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
OFFSETS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


class IncompatibleOverrides(ValueError):
    """A requested combination cannot fit without changing an exact count."""
    incompatible_axes = ("grid_h", "grid_w", "n_rings", "n_decoys")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % 4


def _valid_grid(grid):
    return (isinstance(grid, list) and bool(grid) and isinstance(grid[0], list)
            and bool(grid[0]) and len(grid) <= 30 and len(grid[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(v) is int and 0 <= v <= 9 for v in row)
                    for row in grid))


def _ring_centers(grid):
    found = []
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            color = grid[r - 1][c - 1]
            if (grid[r][c] == 0 and color != 0
                    and all(grid[r + dr][c + dc] == color for dr, dc in OFFSETS8)):
                found.append((r, c, color))
    return found


def _components(grid, *, same_color=False):
    """Eight-connected foreground components, ignoring color for motif counts."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    parts = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        part, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in OFFSETS8:
                p = (r + dr, c + dc)
                if p in remaining and (not same_color or grid[p[0]][p[1]] == grid[r][c]):
                    remaining.remove(p)
                    part.add(p)
                    todo.append(p)
        parts.append(part)
    return parts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Training-domain validation, not a label generator or an ARC validity test."""
    del difficulty, meta
    if not _valid_grid(grid):
        return ["expected a nonempty rectangular ARC integer grid (0..9, at most 30x30)"]
    if not _ring_centers(grid):
        return ["no zero center with eight equal nonzero neighbors"]
    return []


def observe_overrides(grid):
    """Exact for emitted, separated motifs; not an arbitrary-scene object parser."""
    n = len(_ring_centers(grid))
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_rings": n, "n_decoys": len(_components(grid)) - n}


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}")
    for name, lo, hi in (("grid_h", 5, 18), ("grid_w", 5, 18),
                         ("n_rings", 1, 6), ("n_decoys", 0, 6)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, got {value!r}")
    for name, options in (("palette_kind", PALETTE_KINDS),
                          ("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)):
        if overrides.get(name) is not None and overrides[name] not in options:
            raise ValueError(f"{name} must be one of {options}, got {overrides[name]!r}")


def _exact_int(ctx, name, lo, hi, default):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _starts(length, count, rng):
    # A motif spans four cells. Random slack before/between/after motifs avoids
    # fixing centers to one congruence class or one absolute edge margin.
    slack = length - (5 * count - 1)
    gaps = [0] * (count + 1)
    for _ in range(slack):
        gaps[rng.randrange(count + 1)] += 1
    at = gaps[0]
    starts = []
    for i in range(count):
        starts.append(at)
        at += 5 + gaps[i + 1]
    return starts


def _motif(kind, color, other, rng):
    block = full_grid(4, 4, 0)
    for r in range(3):
        for c in range(3):
            if (r, c) != (1, 1):
                block[r][c] = color
    if kind == "attached":
        block[1][3] = color
    elif kind == "missing_corner":
        block[0][0] = 0
    elif kind == "mixed_corner":
        block[0][0] = other
    elif kind == "occupied_center":
        block[1][1] = other
    elif kind == "missing_side":
        block[0][1] = 0
    elif kind != "ring":
        raise ValueError(f"unknown motif {kind}")
    for _ in range(rng.randrange(4)):
        block = [list(row) for row in zip(*block[::-1])]
    if rng.randrange(2):
        block = [row[::-1] for row in block]
    return block


def _draw_from_degenerate(name, rng=None, h=8, w=8):
    del rng
    grid = full_grid(h, w, 0)
    if name == "no_rings":
        return grid
    for r in range(1, 4):
        for c in range(1, 4):
            if name == "filled_centers" or (r, c) not in ((1, 1), (2, 2)):
                grid[r][c] = 4
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    planned_texture = ("default", "default", "contrast", "attached")[profile]
    texture = (ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
               if overrides.get("texture") is not None
               else ctx.draw_choice("texture", (planned_texture,)))
    if texture in DEGENERATE_TEXTURES:
        if overrides.get("n_rings") is not None or overrides.get("n_decoys") is not None:
            raise IncompatibleOverrides("diagnostic negative textures do not accept positive motif counts")
        h = _exact_int(ctx, "grid_h", 5, 18, 8)
        w = _exact_int(ctx, "grid_w", 5, 18, 8)
        return _draw_from_degenerate(texture, h=h, w=w)

    planning = ctx.draw_rng("planning")
    if texture == "default":
        desired_shape = (7, 9) if profile % 2 == 0 else planning.choice(((9, 9), (9, 10)))
        planned_rings = 3 if desired_shape == (9, 10) else 2
        planned_decoys = 0
    else:
        lo, hi = {"easy": (1, 2), "hard": (3, 6)}.get(difficulty, (2, 4))
        planned_rings = planning.randint(lo, hi)
        planned_decoys = planning.randint(3, 6 if difficulty == "hard" else 4)
        upper = {"easy": 14, "hard": 18}.get(difficulty, 15)
        desired_shape = (planning.randint(9, upper), planning.randint(9, upper))

    n_rings = overrides.get("n_rings") if overrides.get("n_rings") is not None else planned_rings
    n_decoys = overrides.get("n_decoys") if overrides.get("n_decoys") is not None else planned_decoys
    hmax = overrides.get("grid_h") or 18
    wmax = overrides.get("grid_w") or 18
    max_slots = ((hmax + 1) // 5) * ((wmax + 1) // 5)
    # Condition unpinned defaults before recording draws; NEVER clamp a count
    # supplied by a caller, or an already-recorded exact count.
    if n_rings + n_decoys > max_slots and overrides.get("n_decoys") is None:
        n_decoys = max(0, max_slots - n_rings)
    if n_rings + n_decoys > max_slots and overrides.get("n_rings") is None:
        n_rings = max(1, max_slots - n_decoys)
    if n_rings + n_decoys > max_slots:
        raise IncompatibleOverrides(
            f"grid_h={hmax}, grid_w={wmax} support {max_slots} separated 4x4 reservations, "
            f"not n_rings={n_rings} plus n_decoys={n_decoys}")
    n_rings = _exact_int(ctx, "n_rings", 1, 6, n_rings)
    n_decoys = _exact_int(ctx, "n_decoys", 0, 6, n_decoys)
    h_choices = [overrides["grid_h"]] if overrides.get("grid_h") is not None else range(5, 19)
    w_choices = [overrides["grid_w"]] if overrides.get("grid_w") is not None else range(5, 19)
    feasible = [(h, w) for h in h_choices for w in w_choices
                if ((h + 1) // 5) * ((w + 1) // 5) >= n_rings + n_decoys]
    # Keep ordinary choices close to the intended size, with random tie-breaking.
    distances = [abs(h-desired_shape[0]) + abs(w-desired_shape[1]) for h, w in feasible]
    best = min(distances)
    h, w = planning.choice([shape for shape, d in zip(feasible, distances) if d == best])
    h = _exact_int(ctx, "grid_h", 5, 18, h)
    w = _exact_int(ctx, "grid_w", 5, 18, w)
    layout = ctx.draw_rng("layout")
    plans = [(nr, nc) for nr in range(1, (h+1)//5 + 1)
             for nc in range(1, (w+1)//5 + 1) if nr*nc >= n_rings+n_decoys]
    nr, nc = layout.choice(plans)
    slots = [(r, c) for r in _starts(h, nr, layout) for c in _starts(w, nc, layout)]
    layout.shuffle(slots)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = list({"warm": (2, 4, 6, 9), "cool": (1, 3, 5, 7, 8)}.get(kind, range(1, 10)))
    colors = ctx.draw_rng("colors")
    colors.shuffle(palette)
    decoys = ("missing_corner", "mixed_corner", "occupied_center", "missing_side")
    grid = full_grid(h, w, 0)
    for i, (r, c) in enumerate(slots[:n_rings+n_decoys]):
        color = (palette[i % len(palette)] if i < n_rings or kind == "varied"
                 else colors.choice(palette))
        other = colors.choice([v for v in palette if v != color])
        motif = ("attached" if texture == "attached" else "ring") if i < n_rings else decoys[(i-n_rings) % 4]
        block = _motif(motif, color, other, ctx.draw_rng(f"motif:{i}"))
        for dr in range(4):
            for dc in range(4):
                grid[r+dr][c+dc] = block[dr][dc]
    # The constructor uses a reserved blank moat, so no accidental cross-motif
    # ring can appear and no placement can silently underfill.
    if observe_overrides(grid) != {"grid_h": h, "grid_w": w, "n_rings": n_rings, "n_decoys": n_decoys}:
        raise RuntimeError("motif construction violated exact counts")
    return grid


# These are audit hooks only. generate() NEVER calls a rule mirror or a rival
# to assign outputs. The bridge still labels examples from Racket.
def rule_mirror(grid):
    out = [row[:] for row in grid]
    for r, c, color in _ring_centers(grid):
        out[r][c] = color
    return out


def rival_cardinal_only(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            ns = [grid[r+dr][c+dc] for dr, dc in OFFSETS4]
            if grid[r][c] == 0 and ns[0] and len(set(ns)) == 1:
                out[r][c] = ns[0]
    return out


def rival_any_nonzero_neighbors(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            ns = [grid[r+dr][c+dc] for dr, dc in OFFSETS8]
            if grid[r][c] == 0 and all(ns):
                out[r][c] = ns[0]
    return out


def rival_overwrite_center(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            ns = [grid[r+dr][c+dc] for dr, dc in OFFSETS8]
            if ns[0] and len(set(ns)) == 1:
                out[r][c] = ns[0]
    return out


def rival_component_box(grid):
    out = [row[:] for row in grid]
    for part in _components(grid, same_color=True):
        r0, r1 = min(r for r, c in part), max(r for r, c in part)
        c0, c1 = min(c for r, c in part), max(c for r, c in part)
        colors = {grid[r][c] for r, c in part}
        if r1-r0 == c1-c0 == 2 and len(colors) == 1:
            color = next(iter(colors))
            for r in range(r0, r1+1):
                for c in range(c0, c1+1):
                    out[r][c] = color
    return out


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    parts = _components(grid, same_color=True)
    if not (7 <= len(grid) <= 10 and 7 <= len(grid[0]) <= 10
            and len(parts) in (2, 3) and len(_ring_centers(grid)) == len(parts)
            and all(len(part) == 8 for part in parts)):
        return ["not a small clean two/three-ring scene"]
    return []


SEMANTIC_RIVALS = {
    "cardinal_only": rival_cardinal_only,
    "any_nonzero_neighbors": rival_any_nonzero_neighbors,
    "overwrite_center": rival_overwrite_center,
    "component_box": rival_component_box,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes_cardinal(grid):
    return rival_cardinal_only(grid) != rule_mirror(grid)


def _refutes_mixed(grid):
    return rival_any_nonzero_neighbors(grid) != rule_mirror(grid)


def _refutes_overwrite(grid):
    return rival_overwrite_center(grid) != rule_mirror(grid)


def _refutes_box(grid):
    return rival_component_box(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "corners_matter": _refutes_cardinal,
    "same_color_matters": _refutes_mixed,
    "zero_center_matters": _refutes_overwrite,
    "local_not_bbox": _refutes_box,
}
WITNESS_RIVALS = {
    "corners_matter": ["cardinal_only"],
    "same_color_matters": ["any_nonzero_neighbors"],
    "zero_center_matters": ["overwrite_center"],
    "local_not_bbox": ["component_box"],
}


def lesson_identifiable(demos, query):
    """Finite-rival diagnostic, not proof against every possible algorithm."""
    if isinstance(query, dict):
        query = query["input"]
    expected = rule_mirror(query)
    return [f"{name} fits all demos but disagrees on query"
            for name, fn in LESSON_COMPETITORS.items()
            if all(fn(p["input"]) == p["output"] for p in demos)
            and fn(query) != expected]
