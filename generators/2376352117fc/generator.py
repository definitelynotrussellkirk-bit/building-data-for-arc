"""Marker-vector translation, with clipping and input/target contact coverage.

Generation returns inputs only. The unchanged Racket authority provides labels.
The Python mirror and rivals below are audit/semantic-contract helpers, never
used to label generated training examples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2376352117fc"
TASK_ID = "2376352117fc"
VERSION = "3.0.0"
RULE_HASH = "6dc047f6d566"
SUMMARY = (
    "One blue(1) marker, one red(2) marker, and a connected green(3) motif. "
    "Translate the motif by the blue-to-red vector, recolor it cyan(8), and "
    "draw ONLY its in-bounds cells on a fresh zero background. Original "
    "markers and motif are erased. Full, partial, and empty translations "
    "are lawful; target/input overlaps are not obstacles."
)
INVARIANTS = [
    "rectangular 0-background grid using only colors 0, 1, 2, and 3",
    "exactly one color-1 marker and one distinct color-2 marker",
    "one 4-connected color-3 motif of 3-8 cells",
    "translated cells may be clipped or overlap input cells",
]
TEXTURES = ("full_clear", "partial_clear", "full_overlap", "partial_overlap", "empty")
HELPFUL_TEXTURES = TEXTURES
DIRECTIONS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
_SIGNS = {"N": (-1, 0), "NE": (-1, 1), "E": (0, 1), "SE": (1, 1),
          "S": (1, 0), "SW": (1, -1), "W": (0, -1), "NW": (-1, -1)}
# Every three consecutive profiles contain partial clipping, a full translation,
# and an input/target overlap, refuting both canonical-compatible shortcuts.
# Only one in eight is empty. A seed rotates the cycle, not the geometry.
SCHEDULE_PROFILES = ("full_overlap", "partial_clear", "full_overlap", "partial_overlap",
                     "full_clear", "full_overlap", "partial_clear", "empty")
AXES = {
    "grid_h": {"type": "int", "default": "compact-weighted 7..18", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "compact-weighted 7..19", "valid": "7..19"},
    "motif_size": {"type": "int", "default": "difficulty-weighted 3..8", "valid": "3..8"},
    "texture": {"type": "str", "default": "eight-profile schedule", "valid": "|".join(TEXTURES)},
    "vector_kind": {"type": "str", "default": "rng all eight directions", "valid": "|".join(DIRECTIONS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _connected(cells):
    if not cells:
        return False
    cells = set(cells)
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            cell = r + dr, c + dc
            if cell in cells and cell not in seen:
                seen.add(cell)
                stack.append(cell)
    return seen == cells


def _build_motif(rng, size, contact_direction=None):
    cells = {(0, 0)}
    if contact_direction is not None:
        dr, dc = contact_direction
        cells.add((dr, dc))
        if dr and dc:
            # Preserve 4-connectivity while providing a diagonal self-contact.
            cells.add(rng.choice(((dr, 0), (0, dc))))
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))} - cells)
        cells.add(rng.choice(frontier))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return tuple(sorted((r - rmin, c - cmin) for r, c in cells))


def _try_layout(rng, h, w, motif, texture, direction):
    """Finite geometry search; no marker/motif placement retry roulette."""
    sh = 1 + max(r for r, _ in motif)
    sw = 1 + max(c for _, c in motif)
    if sh > h or sw > w:
        return None
    sr, sc = _SIGNS[direction]
    drs = (0,) if sr == 0 else tuple(sr * n for n in range(1, h))
    dcs = (0,) if sc == 0 else tuple(sc * n for n in range(1, w))
    vectors = [(dr, dc) for dr in drs for dc in dcs]
    rng.shuffle(vectors)
    origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(origins)
    want_visibility = texture.split("_")[0]
    want_contact = texture.endswith("overlap")
    relative = set(motif)
    for dr, dc in vectors:
        self_contact = bool(relative & {(r + dr, c + dc) for r, c in motif})
        if texture.endswith("clear") and self_contact:
            continue
        for r0, c0 in origins:
            source = {(r0 + r, c0 + c) for r, c in motif}
            targets = {(r + dr, c + dc) for r, c in source
                       if 0 <= r + dr < h and 0 <= c + dc < w}
            count = len(targets)
            visibility = "empty" if count == 0 else "full" if count == len(motif) else "partial"
            if visibility != want_visibility:
                continue
            # If the source itself does not intersect the target, an overlap
            # must involve a marker. A red target would force blue onto the
            # source, so only a blue-marker target is geometrically possible.
            candidates = (sorted(targets) if want_contact and not self_contact else
                          [(r, c) for r in range(max(0, -dr), min(h, h - dr))
                           for c in range(max(0, -dc), min(w, w - dc))])
            valid = []
            for p1 in candidates:
                p2 = p1[0] + dr, p1[1] + dc
                if not (0 <= p2[0] < h and 0 <= p2[1] < w):
                    continue
                if p1 in source or p2 in source:
                    continue
                contact = self_contact or p1 in targets or p2 in targets
                if texture != "empty" and contact != want_contact:
                    continue
                valid.append(p1)
            if valid:
                p1 = rng.choice(valid)
                p2 = p1[0] + dr, p1[1] + dc
                grid = full_grid(h, w, 0)
                for r, c in source:
                    grid[r][c] = 3
                grid[p1[0]][p1[1]] = 1
                grid[p2[0]][p2[1]] = 2
                return grid
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name in ("grid_h", "grid_w", "motif_size"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, not {type(overrides[name]).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    anchor_weight = {None: 4, "easy": 5, "medium": 4, "hard": 3}[difficulty]
    h = ctx.draw_choice("grid_h", tuple(range(7, 19)) + (7, 8, 9) * anchor_weight)
    w = ctx.draw_choice("grid_w", tuple(range(7, 20)) + (10, 11, 12) * anchor_weight)
    sizes = tuple(range(3, 9))
    if difficulty == "easy":
        sizes += (3, 4) * 3
    elif difficulty == "hard":
        sizes += (6, 7, 8) * 2
    size = ctx.draw_choice("motif_size", sizes)
    options = TEXTURES if overrides.get("texture") is not None else (schedule_profile(seed, sample_index),)
    texture = ctx.draw_choice("texture", options)
    direction = ctx.draw_choice("vector_kind", DIRECTIONS)
    rng = ctx.draw_rng("layout")
    for _ in range(32):
        motif = _build_motif(rng, size, _SIGNS[direction] if texture.endswith("overlap") else None)
        grid = _try_layout(rng, h, w, motif, texture, direction)
        if grid is not None:
            return grid
    raise ValueError(f"no layout for h={h}, w={w}, size={size}, texture={texture}, direction={direction}")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty sequences"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be within 1..30"]
    if any(type(v) is not int or v not in (0, 1, 2, 3) for row in grid for v in row):
        return ["input cells must be integer colors 0, 1, 2, or 3"]
    errors = []
    for color in (1, 2):
        count = len(_positions(grid, color))
        if count != 1:
            errors.append(f"expected exactly one color-{color} marker, found {count}")
    motif = _positions(grid, 3)
    if not 3 <= len(motif) <= 8:
        errors.append(f"expected 3-8 color-3 motif cells, found {len(motif)}")
    if motif and not _connected(motif):
        errors.append("color-3 motif is not 4-connected")
    return errors


def _geometry(grid):
    p1, p2 = _positions(grid, 1)[0], _positions(grid, 2)[0]
    dr, dc = p2[0] - p1[0], p2[1] - p1[1]
    source = set(_positions(grid, 3))
    targets = {(r + dr, c + dc) for r, c in source
               if 0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])}
    return dr, dc, source, targets


def observe_overrides(grid):
    dr, dc, source, targets = _geometry(grid)
    visibility = "empty" if not targets else "full" if len(targets) == len(source) else "partial"
    contact = any(grid[r][c] != 0 for r, c in targets)
    texture = visibility if visibility == "empty" else visibility + ("_overlap" if contact else "_clear")
    signs = ((dr > 0) - (dr < 0), (dc > 0) - (dc < 0))
    direction = next(key for key, value in _SIGNS.items() if value == signs)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "motif_size": len(source),
            "texture": texture, "vector_kind": direction}


def rule_mirror(grid):
    """Independent audit helper, NOT a training-label authority."""
    _, _, _, targets = _geometry(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c in targets:
        out[r][c] = 8
    return out


def _all_or_nothing(grid):
    _, _, source, targets = _geometry(grid)
    return rule_mirror(grid) if len(targets) == len(source) else full_grid(len(grid), len(grid[0]), 0)


def _background_only(grid):
    out = rule_mirror(grid)
    for r, c in _geometry(grid)[3]:
        if grid[r][c] != 0:
            out[r][c] = 0
    return out


def _preserve_input(grid):
    out = [row[:] for row in grid]
    for r, c in _geometry(grid)[3]:
        out[r][c] = 8
    return out


def _reverse_vector(grid):
    dr, dc, source, _ = _geometry(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c in source:
        rr, cc = r - dr, c - dc
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            out[rr][cc] = 8
    return out


def _partial_witness(grid):
    _, _, source, targets = _geometry(grid)
    return 0 < len(targets) < len(source)


def _contact_witness(grid):
    return any(grid[r][c] != 0 for r, c in _geometry(grid)[3])


strict_canonical_like = self_check
SEMANTIC_RIVALS = {"all_or_nothing": _all_or_nothing, "background_only": _background_only,
                   "preserve_input": _preserve_input, "reverse_vector": _reverse_vector}
CANONICAL_SHORTCUTS = {"all_or_nothing": _all_or_nothing, "background_only": _background_only}
SEMANTIC_WITNESSES = {"partial_clipping": _partial_witness, "input_target_overlap": _contact_witness}
WITNESS_RIVALS = {"partial_clipping": ["all_or_nothing"], "input_target_overlap": ["background_only"]}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Finite-rival diagnostic, not a claim of uniqueness over all programs."""
    query_grid = query["input"] if isinstance(query, dict) else query
    expected = rule_mirror(query_grid)
    return [f"rival {name} survives demos and disagrees on query"
            for name, rival in SEMANTIC_RIVALS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query_grid) != expected]


def mutation_fixtures():
    base = full_grid(7, 8, 0)
    base[0][0], base[1][2] = 1, 2
    base[3][3] = base[4][3] = base[4][4] = 3
    result = []
    for name, r, c, value in (("extra_blue", 0, 1, 1), ("missing_red", 1, 2, 0),
                               ("disconnected_green", 6, 7, 3), ("extraneous_color", 2, 6, 9)):
        grid = [row[:] for row in base]
        grid[r][c] = value
        result.append((name, grid))
    result.append(("ragged", [[0, 1], [2]]))
    return result
