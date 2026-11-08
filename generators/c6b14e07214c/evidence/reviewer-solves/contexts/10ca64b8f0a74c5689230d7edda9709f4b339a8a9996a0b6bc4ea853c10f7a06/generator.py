"""Nearest-seed fill inputs; labels remain exclusively canonical Racket output.

Defaults cycle through a canonical-profile draw, a distance/tie contrast, and
an extra-source contrast. Every three consecutive default draws teach the
six declared rivals. Exact overrides remain independent but can disable that
teaching guarantee; ``lesson_identifiable`` then checks the realized lesson.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "c6b14e07214c"
TASK_ID = "c6b14e07214c"
VERSION = "2.0.0"
RULE_HASH = "d219d22bc8a3"
SUMMARY = "Manhattan nearest-seed fill in a 7-frame, with numeric color ties and preserved interior 7s."
INVARIANTS = [
    "one complete rectangular color-7 outline encloses the fill region; exterior is 0",
    "two to six singleton seeds have distinct colors from 1,2,3,4,5,6,8,9",
    "zero to two interior color-7 cells are preserved, not treated as seeds",
    "at least one interior background cell is available for filling",
]
AXES = {
    "grid_h": {"type": "int", "default": "9/10 in canonical/geometry phases, otherwise 9..22", "valid": "9..22"},
    "grid_w": {"type": "int", "default": "9/10 in canonical/geometry phases, otherwise 9..22", "valid": "9..22"},
    "frame_h": {"type": "int", "default": "7/8 in canonical phase, otherwise 5..9", "valid": "5..9"},
    "frame_w": {"type": "int", "default": "7/8 in canonical phase, otherwise 5..9", "valid": "5..9"},
    "n_seeds": {"type": "int", "default": "2..3 canonical; 2 geometry; 4..6 many", "valid": "2..6"},
    "n_interior_sevens": {"type": "int", "default": "0..1 canonical; 1..2 geometry; 0..2 many", "valid": "0..2"},
}
_BOUNDS = {"grid_h": (9, 22), "grid_w": (9, 22), "frame_h": (5, 9),
           "frame_w": (5, 9), "n_seeds": (2, 6), "n_interior_sevens": (0, 2)}
_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical", "geometry", "many_sources")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _axis(ctx, name, defaults):
    """A restricted default mixture is not a restricted override domain.

    Both paths record the value actually drawn. No clipping or hidden redraw
    changes a recorded count, and every advertised Cartesian combination fits.
    """
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, *_BOUNDS[name])
    return ctx.draw_choice(name, defaults)


def _positions(ih, iw, count, colors, profile, rng):
    cells = [(r, c) for r in range(ih) for c in range(iw)]
    if profile == "geometry" and count == 2:
        # A is earlier in scan order and has the larger color. At q, both
        # L1 distances are 2*k, but squared L2 and L-infinity prefer A.
        k = rng.randint(1, min((ih - 1) // 2, iw - 1))
        r = rng.randint(k, ih - 1 - k)
        sign = rng.choice((-1, 1))
        c = rng.randint(k, iw - 1) if sign == -1 else rng.randint(0, iw - 1 - k)
        a, b, q = (r, c), (r + k, c + sign*k), (r - k, c + sign*k)
        return [(a, max(colors)), (b, min(colors))], {q}
    if profile == "many_sources" and count >= 4:
        # Reserve a zero q uniquely closest to a source omitted by the
        # three-smallest-colors rival. All 8 corner/neighbor placements fit
        # even the minimum 3x3 interior with six seeds and two interior 7s.
        placements = [
            ((0, 0), (1, 0)), ((0, 0), (0, 1)),
            ((0, iw-1), (1, iw-1)), ((0, iw-1), (0, iw-2)),
            ((ih-1, 0), (ih-2, 0)), ((ih-1, 0), (ih-1, 1)),
            ((ih-1, iw-1), (ih-2, iw-1)), ((ih-1, iw-1), (ih-1, iw-2)),
        ]
        source, q = rng.choice(placements)
        available = [p for p in cells if p != source and abs(p[0]-q[0]) + abs(p[1]-q[1]) > 1]
        rest = rng.sample(available, count-1)
        other_colors = [v for v in colors if v != max(colors)]
        rng.shuffle(other_colors)
        return [(source, max(colors)), *list(zip(rest, other_colors))], {q}
    return list(zip(rng.sample(cells, count), colors)), set()


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer; sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    anchor = ctx.draw_choice("canonical_side", (9, 10))
    # Full size support in every band; difficulty changes weights, not legality.
    sizes = list(range(9, 23))
    sizes += list(range(9, 14)) * 2 if difficulty == "easy" else (
        list(range(16, 23)) * 2 if difficulty == "hard" else [])
    core = profile == "canonical"
    # Keep two of three teaching phases at canonical scale; a one-third
    # mixture was too sparse in an independent 20-draw/band floor census.
    # This is a distribution choice, not a special case for evaluation seeds.
    canonical_scale = profile in ("canonical", "geometry")
    h = _axis(ctx, "grid_h", (anchor,) if canonical_scale else sizes)
    w = _axis(ctx, "grid_w", (anchor,) if canonical_scale else sizes)
    fh = _axis(ctx, "frame_h", (anchor-2,) if core else range(5, 10))
    fw = _axis(ctx, "frame_w", (anchor-2,) if core else range(5, 10))
    seed_defaults = ((3,) if anchor == 9 else (2, 3)) if core else (
        (2,) if profile == "geometry" else (4, 5, 6))
    n = _axis(ctx, "n_seeds", seed_defaults)
    obstacles = _axis(ctx, "n_interior_sevens", (0, 1) if core else (
        (1, 2) if profile == "geometry" else (0, 1, 2)))
    rng = ctx.draw_rng("layout")
    r0, c0 = rng.randint(0, h-fh), rng.randint(0, w-fw)
    colors = ctx.draw_rng("palette").sample(_COLORS, n)
    planted, reserved = _positions(fh-2, fw-2, n, colors, profile, rng)
    g = full_grid(h, w, 0)
    draw_frame(g, r0, c0, r0+fh-1, c0+fw-1, 7)
    for (r, c), color in planted:
        g[r0+1+r][c0+1+c] = color
    occupied = {p for p, _ in planted}
    free = [(r, c) for r in range(fh-2) for c in range(fw-2)
            if (r, c) not in occupied and (r, c) not in reserved]
    for r, c in rng.sample(free, obstacles):
        g[r0+1+r][c0+1+c] = 7
    return g


def _geometry(grid):
    sevens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    if not sevens:
        raise ValueError("no color-7 frame")
    r0, r1 = min(r for r, _ in sevens), max(r for r, _ in sevens)
    c0, c1 = min(c for _, c in sevens), max(c for _, c in sevens)
    interior = [(r, c) for r in range(r0+1, r1) for c in range(c0+1, c1)]
    seeds = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] not in (0, 7)]
    return (r0, c0, r1, c1), interior, seeds


def observe_overrides(grid):
    (r0, c0, r1, c1), interior, seeds = _geometry(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "frame_h": r1-r0+1,
            "frame_w": c1-c0+1, "n_seeds": len(seeds),
            "n_interior_sevens": sum(grid[r][c] == 7 for r, c in interior)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30):
        return ["grid dimensions must be within 3..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors in 0..9 (not bool or float)"]
    try:
        (r0, c0, r1, c1), interior, seeds = _geometry(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if r1-r0 < 2 or c1-c0 < 2:
        errors.append("frame must have an interior")
    outline = [(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)
               if r in (r0, r1) or c in (c0, c1)]
    if any(grid[r][c] != 7 for r, c in outline):
        errors.append("incomplete rectangular color-7 outline")
    if any(v != 0 and not (r0 <= r <= r1 and c0 <= c <= c1)
           for r, row in enumerate(grid) for c, v in enumerate(row)):
        errors.append("nonzero exterior cell")
    if not 2 <= len(seeds) <= 6 or len({v for _, _, v in seeds}) != len(seeds):
        errors.append("expected 2..6 singleton seeds with distinct nonzero, non-7 colors")
    if sum(grid[r][c] == 7 for r, c in interior) > 2:
        errors.append("at most two preserved interior color-7 cells")
    if not any(grid[r][c] == 0 for r, c in interior):
        errors.append("no blank interior cell to fill")
    return errors


def strict_canonical_like(grid):
    """The declared task domain, not literal canonical dimensions or palette."""
    return self_check(grid)


def _winner(seeds, r, c, metric, tie):
    def key(seed):
        sr, sc, color = seed
        dr, dc = abs(sr-r), abs(sc-c)
        distance = dr+dc if metric == "l1" else (dr*dr+dc*dc if metric == "l2" else max(dr, dc))
        if tie == "scan":
            return distance, sr, sc, color
        return distance, -color if tie == "high" else color, sr, sc
    return min(seeds, key=key)[2]


def _rival_fill(grid, *, metric, tie="low", cap=None, repaint=False):
    """Diagnostic rival engine only; never used to generate training labels."""
    _, interior, seeds = _geometry(grid)
    selected = sorted(seeds, key=lambda s: s[2])[:cap] if cap is not None else seeds
    out = [list(row) for row in grid]
    for r, c in interior:
        if grid[r][c] == 0 or (repaint and grid[r][c] == 7):
            out[r][c] = _winner(selected, r, c, metric, tie)
    return out


def _euclidean(grid):
    return _rival_fill(grid, metric="l2")


def _chebyshev(grid):
    return _rival_fill(grid, metric="linf")


def _prefer_high(grid):
    return _rival_fill(grid, metric="l1", tie="high")


def _scan_ties(grid):
    return _rival_fill(grid, metric="l1", tie="scan")


def _three_sources(grid):
    return _rival_fill(grid, metric="l1", cap=3)


def _repaint_sevens(grid):
    return _rival_fill(grid, metric="l1", repaint=True)


def _contrast(grid, *, metric="l1", tie="low", cap=None):
    # An input-only distance inequality, checked independently by Racket in
    # the semantic gate. It does not emit positive example labels.
    _, interior, seeds = _geometry(grid)
    selected = sorted(seeds, key=lambda s: s[2])[:cap] if cap is not None else seeds
    return any(grid[r][c] == 0 and
               _winner(seeds, r, c, "l1", "low") != _winner(selected, r, c, metric, tie)
               for r, c in interior)


def _metric_l2_witness(grid):
    return _contrast(grid, metric="l2")


def _metric_linf_witness(grid):
    return _contrast(grid, metric="linf")


def _low_color_witness(grid):
    return _contrast(grid, tie="high")


def _scan_witness(grid):
    return _contrast(grid, tie="scan")


def _fourth_source_witness(grid):
    return _contrast(grid, cap=3)


def _interior_seven_witness(grid):
    return observe_overrides(grid)["n_interior_sevens"] > 0


SEMANTIC_RIVALS = {
    "euclidean_distance": _euclidean, "chebyshev_distance": _chebyshev,
    "prefer_high_color": _prefer_high, "scan_order_ties": _scan_ties,
    "three_smallest_sources": _three_sources, "repaint_interior_sevens": _repaint_sevens,
}
CANONICAL_SHORTCUTS = {"three_smallest_sources": _three_sources}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "l2_counterexample": _metric_l2_witness, "linf_counterexample": _metric_linf_witness,
    "numeric_tie": _low_color_witness, "scan_tie": _scan_witness,
    "extra_source": _fourth_source_witness, "preserved_seven": _interior_seven_witness,
}
WITNESS_RIVALS = {
    "l2_counterexample": ["euclidean_distance"], "linf_counterexample": ["chebyshev_distance"],
    "numeric_tie": ["prefer_high_color"], "scan_tie": ["scan_order_ties"],
    "extra_source": ["three_smallest_sources"], "preserved_seven": ["repaint_interior_sevens"],
}


def lesson_identifiable(demos, query):
    """Offline finite-rival check; query labels must never be shown to a solver."""
    if not demos or any("output" not in pair for pair in [*demos, query]):
        return ["offline authoritative demo and query outputs are required"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(p["input"]) == p["output"] for p in demos) and rival(query["input"]) != query["output"]:
            reasons.append(f"query-changing rival survives demos: {name}")
    return reasons


def mutation_fixtures():
    grid = generate(0, 0)
    bbox, _, seeds = _geometry(grid)
    r0, c0, _, _ = bbox
    missing = [row[:] for row in grid]
    missing[r0][c0] = 0
    duplicate = [row[:] for row in grid]
    duplicate[seeds[0][0]][seeds[0][1]] = seeds[1][2]
    return [("missing_outline", missing), ("duplicate_seed_color", duplicate),
            ("no_frame", full_grid(9, 9, 0)), ("ragged", [[0], [0, 0]])]
