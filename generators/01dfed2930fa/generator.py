"""Generator for arc_puzzle_bank_21_set20_bundle:medium_p05 (task 01dfed2930fa).

THE RULE (what a solver must learn to see):
  Color-8 walls partition the grid into rooms (4-conn non-8 regions).
  A room fills with its seed color ONLY when its seeds are exactly one
  DISTINCT color (several same-color seeds still fill). Rooms with two
  seed colors, or none, stay as they are.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - 2-4 rooms via vertical AND horizontal walls (old: always one
    vertical wall, exactly 2 rooms)
  - wall GAPS merge rooms into L shapes the flood must follow
  - mixed_room boards: one room carries TWO seed colors and stays
    unfilled (the rule's uniqueness gate — previously only a frozen
    degenerate, never in training data)
  - twin_seeds boards: a room with 2-3 seeds of the SAME color fills
    normally — 'exactly one seed CELL' is refuted
  - empty rooms stay empty

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_walls   one open region
  - no_seeds   rooms but nothing to fill with (identity)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01dfed2930fa"
VERSION = "2.1.0"
TASK_ID = "01dfed2930fa"
SUMMARY = (
    "8-walled grid (border + 1-2 dividers, optional gaps) with rooms "
    "holding one seed color each — sometimes several seeds of that "
    "color, sometimes a two-color room that stays unfilled, sometimes "
    "an empty room; rule floods each room with its unique seed color."
)

# Rivals: 'fill every room with any seed' refuted by two-color rooms
# staying unfilled. 'exactly one seed cell required' refuted by
# twin-seed rooms that fill. 'rooms are rectangles' refuted by
# gap-merged L-rooms. 3 demos incl. >=1 mixed or twin board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "outer border is all 8; dividers are 8",
    ">=1 room fills (exactly one distinct seed color present)",
    "mixed_room boards: a room with 2 seed colors stays unfilled",
    "twin_seeds boards: 2-3 same-color seeds in one room (it fills)",
]

DEGENERATE_TEXTURES = ("no_walls", "no_seeds")
HELPFUL_TEXTURES = ("plain", "gapped", "mixed_room", "twin_seeds", "empty_room")

# Every three consecutive ordinary samples carry both semantic gate branches.
# The phase varies by seed/band so a lesson does not always present them in the
# same order, while remaining independent of sample_index and therefore truly
# periodic across sliding windows.
SCHEDULE_PROFILES = ("mixed_room", "twin_seeds", "structural")
_STRUCTURAL_TEXTURES = ("plain", "gapped", "empty_room")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..10 (hard 10..13)",
                "valid": "7..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 9..12 (hard 12..14)",
                "valid": "7..14", "doc": "Grid width."},
    "n_vdivs": {"type": "int", "default": "rng 1..2", "valid": "0..2",
                "doc": "Vertical divider walls."},
    "n_hdivs": {"type": "int", "default": "rng 0..1", "valid": "0..1",
                "doc": "Horizontal divider walls."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|gapped|mixed_room|twin_seeds|empty_room|"
                         "no_walls|no_seeds",
                "doc": "Set to a degenerate name to build a rule-hiding input."},
}


def _rooms(g):
    h, w = len(g), len(g[0])
    seen, out = set(), []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 8 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and g[nr][nc] != 8
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                out.append(cells)
    return out


def _schedule_phase(seed, difficulty=None) -> int:
    band = "default" if difficulty is None else str(difficulty)
    return stable_rng(
        seed,
        f"{TASK_ID}|texture-schedule|{band}",
        VERSION,
    ).randrange(len(SCHEDULE_PROFILES))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared three-slot ordinary teaching schedule profile."""
    return SCHEDULE_PROFILES[
        (int(sample_index) + _schedule_phase(seed, difficulty))
        % len(SCHEDULE_PROFILES)
    ]


def _scheduled_texture(seed, sample_index, difficulty, ctx):
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "mixed_room":
        return "mixed_room"
    if profile == "twin_seeds":
        return "twin_seeds"
    return ctx.draw_choice("texture", _STRUCTURAL_TEXTURES)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = _scheduled_texture(seed, sample_index, difficulty, ctx)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_v, n_h = 1, 0
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_v = ctx.draw_int("n_vdivs", 1, 2)
        n_h = ctx.draw_int("n_hdivs", 0, 1)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n_v = ctx.draw_int("n_vdivs", 1, 2)
        n_h = ctx.draw_int("n_hdivs", 0, 1)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for c in range(w):
        g[0][c] = 8
        g[h - 1][c] = 8
    for r in range(h):
        g[r][0] = 8
        g[r][w - 1] = 8
    v_cols = []
    for c in rng.sample(range(3, w - 3), min(n_v, max(0, w - 6))):
        if all(abs(c - vc) >= 3 for vc in v_cols):
            v_cols.append(c)
            for r in range(h):
                g[r][c] = 8
    h_rows = []
    for r in rng.sample(range(3, h - 3), min(n_h, max(0, h - 6))):
        h_rows.append(r)
        for c in range(w):
            g[r][c] = 8

    if texture == "gapped" and (v_cols or h_rows):
        # carve 1-2 gaps so rooms merge into L shapes
        cand = ([(r, vc) for vc in v_cols for r in range(1, h - 1) if r not in h_rows]
                + [(hr, c) for hr in h_rows for c in range(1, w - 1) if c not in v_cols])
        rng.shuffle(cand)
        for r, c in cand[:rng.randint(1, 2)]:
            g[r][c] = 0

    rooms = _rooms(g)
    rng.shuffle(rooms)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], min(len(rooms) + 1, 8))
    filled_any = False
    for idx, cells in enumerate(rooms):
        empties = [p for p in cells if g[p[0]][p[1]] == 0]
        if not empties:
            continue
        if texture == "empty_room" and idx == 0 and len(rooms) >= 2:
            continue  # stays seedless and unfilled
        if texture == "mixed_room" and idx == 0 and len(rooms) >= 2 and len(empties) >= 2:
            a, b = rng.sample(empties, 2)
            g[a[0]][a[1]] = palette[-1]
            g[b[0]][b[1]] = palette[idx]
            continue  # two colors: the rule's gate keeps it unfilled
        n_seeds = rng.randint(2, 3) if texture == "twin_seeds" and idx == 0 else 1
        for p in rng.sample(empties, min(n_seeds, len(empties))):
            g[p[0]][p[1]] = palette[idx]
        filled_any = True
    if not filled_any and rooms:
        cells = rooms[0]
        empties = [p for p in cells if g[p[0]][p[1]] == 0]
        if empties:
            p = empties[rng.randrange(len(empties))]
            g[p[0]][p[1]] = palette[0]
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_walls — open field, single region.
    no_seeds — walls only: identity output.
    """
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_walls":
        for _ in range(rng.randint(1, 3)):
            g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = rng.choice(
                [1, 2, 3, 4, 5, 6, 7, 9])
        return g
    for c in range(w):
        g[0][c] = 8
        g[h - 1][c] = 8
    for r in range(h):
        g[r][0] = 8
        g[r][w - 1] = 8
    wall_c = rng.randint(3, w - 4)
    for r in range(h):
        g[r][wall_c] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)):
        errs.append("top/bottom border is not all 8")
    if any(grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)):
        errs.append("left/right border is not all 8")
    rooms = _rooms(grid)
    if len(rooms) < 1:
        errs.append("no non-wall rooms")
    fillable = 0
    for cells in rooms:
        colors = {grid[r][c] for r, c in cells if grid[r][c] not in (0, 8)}
        if len(colors) == 1:
            fillable += 1
    if fillable < 1:
        errs.append("no room has exactly one distinct seed color")
    return errs


def _seed_cells(grid, cells):
    return [
        (r, c, grid[r][c])
        for r, c in sorted(cells)
        if grid[r][c] not in (0, 8)
    ]


def rule_mirror(grid):
    """Independent Python mirror; the canonical Racket remains authoritative."""
    output = [row[:] for row in grid]
    for cells in _rooms(grid):
        seeds = _seed_cells(grid, cells)
        colors = {value for _, _, value in seeds}
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        for r, c in cells:
            if output[r][c] == 0:
                output[r][c] = color
    return output


def _rival_fill_any_first_seed(grid):
    output = [row[:] for row in grid]
    for cells in _rooms(grid):
        seeds = _seed_cells(grid, cells)
        if not seeds:
            continue
        color = seeds[0][2]
        for r, c in cells:
            if output[r][c] == 0:
                output[r][c] = color
    return output


def _rival_exactly_one_seed_cell(grid):
    output = [row[:] for row in grid]
    for cells in _rooms(grid):
        seeds = _seed_cells(grid, cells)
        if len(seeds) != 1:
            continue
        color = seeds[0][2]
        for r, c in cells:
            if output[r][c] == 0:
                output[r][c] = color
    return output


SEMANTIC_RIVALS = {
    "fill_any_first_seed": _rival_fill_any_first_seed,
    "exactly_one_seed_cell": _rival_exactly_one_seed_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_mixed_seed_room(grid):
    return any(
        len({grid[r][c] for r, c in cells if grid[r][c] not in (0, 8)}) >= 2
        for cells in _rooms(grid)
    )


def _has_same_color_twin_seeds(grid):
    for cells in _rooms(grid):
        seeds = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 8)]
        if len(seeds) >= 2 and len(set(seeds)) == 1:
            return True
    return False


SEMANTIC_WITNESSES = {
    "mixed_seed_room_stays_unfilled": _has_mixed_seed_room,
    "same_color_twin_seeds_fill": _has_same_color_twin_seeds,
}
WITNESS_RIVALS = {
    "mixed_seed_room_stays_unfilled": ["fill_any_first_seed"],
    "same_color_twin_seeds_fill": ["exactly_one_seed_cell"],
}


def strict_canonical_like(grid) -> list[str]:
    """Validate the ordinary canonical-like walled-room teaching manifold."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 14:
        reasons.append(f"height {h} is outside ordinary envelope 7..14")
    if not 7 <= w <= 14:
        reasons.append(f"width {w} is outside ordinary envelope 7..14")
    if not any(grid[r][c] == 8 for r in range(1, h - 1) for c in range(1, w - 1)):
        reasons.append("ordinary scenes require at least one internal wall cell")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that collectively falsify both gate rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the rule")
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
