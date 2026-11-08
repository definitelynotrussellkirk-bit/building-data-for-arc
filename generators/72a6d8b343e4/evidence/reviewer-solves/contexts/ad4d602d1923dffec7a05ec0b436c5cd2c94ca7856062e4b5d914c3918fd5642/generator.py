"""Input generator for Endpoint Bridge (72a6d8b343e4).

The unchanged Racket authority connects a nonzero color only when it appears
exactly twice and those two cells share a row or column.  This sampler includes
both positive bridge pairs and negative evidence: diagonal exact pairs and
aligned triples.  Reserved footprints keep all teaching cases independent, so
line order and accidental overwrites cannot become alternate rules.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "72a6d8b343e4"
TASK_ID = GENERATOR_ID
RULE_HASH = "3650a4704dc3"
VERSION = "3.0.0"

SUMMARY = (
    "A sparse 0-background grid contains distinct-color marker families. "
    "Colors appearing exactly twice are connected only when their cells share "
    "a row or column; the inclusive span is filled with that color. Diagonal "
    "pairs, singletons, and aligned three-occurrence colors remain unchanged."
)

INVARIANTS = [
    "background is 0 and every foreground color is in 1..9",
    "separated horizontal and vertical exact pairs have empty, disjoint spans",
    "aligned triples reserve a clean span but remain unchanged because count != 2",
    "all advertised axes are recoverable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "canonical-weighted 6..12", "valid": "6..12"},
    "n_horizontal": {"type": "int", "default": "0..2", "valid": "0..2"},
    "n_vertical": {"type": "int", "default": "0..2", "valid": "0..2"},
    "n_diagonal": {"type": "int", "default": "0..1", "valid": "0..1"},
    "n_triples": {"type": "int", "default": "0..1", "valid": "0..1"},
    "n_singletons": {"type": "int", "default": "0..1", "valid": "0..1"},
    "n_adjacent": {"type": "int", "default": "0..1", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_RANGES = {
    "grid_h": (6, 12),
    "grid_w": (6, 12),
    "n_horizontal": (0, 2),
    "n_vertical": (0, 2),
    "n_diagonal": (0, 1),
    "n_triples": (0, 1),
    "n_singletons": (0, 1),
    "n_adjacent": (0, 1),
}


def _line_cells(a, b):
    r1, c1 = a
    r2, c2 = b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return tuple((r1, c) for c in range(lo, hi + 1))
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return tuple((r, c1) for r in range(lo, hi + 1))
    return ()


@lru_cache(maxsize=256)
def _candidate_pool(kind, h, w):
    """Return immutable (occupied, reserved-footprint) candidates."""
    candidates = []
    if kind == "horizontal":
        for r in range(h):
            for c1 in range(w - 2):
                for c2 in range(c1 + 2, w):
                    occupied = ((r, c1), (r, c2))
                    candidates.append((occupied, _line_cells(*occupied)))
    elif kind == "vertical":
        for c in range(w):
            for r1 in range(h - 2):
                for r2 in range(r1 + 2, h):
                    occupied = ((r1, c), (r2, c))
                    candidates.append((occupied, _line_cells(*occupied)))
    elif kind == "adjacent":
        for r in range(h):
            for c in range(w - 1):
                occupied = ((r, c), (r, c + 1))
                candidates.append((occupied, occupied))
        for r in range(h - 1):
            for c in range(w):
                occupied = ((r, c), (r + 1, c))
                candidates.append((occupied, occupied))
    elif kind == "diagonal":
        cells = [(r, c) for r in range(h) for c in range(w)]
        for index, a in enumerate(cells):
            for b in cells[index + 1:]:
                if a[0] != b[0] and a[1] != b[1]:
                    occupied = (a, b)
                    candidates.append((occupied, occupied))
    elif kind == "singleton":
        for r in range(h):
            for c in range(w):
                occupied = ((r, c),)
                candidates.append((occupied, occupied))
    else:
        raise ValueError(f"unknown placement kind: {kind}")
    return tuple(candidates)


def _triple_options(h, w, used, rng):
    """Aligned pair plus a third marker aligned with neither endpoint."""
    lines = list(_candidate_pool("horizontal", h, w))
    lines.extend(_candidate_pool("vertical", h, w))
    rng.shuffle(lines)
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    options = []
    for occupied, footprint in lines:
        if any(cell in used for cell in footprint):
            continue
        a, b = occupied
        thirds = [
            p for p in all_cells
            if p not in used
            and p not in footprint
            and p[0] not in (a[0], b[0])
            and p[1] not in (a[1], b[1])
        ]
        rng.shuffle(thirds)
        for third in thirds[:4]:
            options.append((occupied + (third,), footprint + (third,)))
        if len(options) >= 256:
            break
    rng.shuffle(options)
    return options


def _placement_options(kind, h, w, used, rng):
    if kind == "triple":
        return _triple_options(h, w, used, rng)
    options = [
        candidate for candidate in _candidate_pool(kind, h, w)
        if all(cell not in used for cell in candidate[1])
    ]
    rng.shuffle(options)
    # Short spans leave more room while the shuffle randomizes equal-length ties.
    options.sort(key=lambda candidate: len(candidate[1]))
    return options


def _place_objects(kinds, h, w, rng):
    """Backtrack over disjoint reserved footprints; all declared domains fit 6x6."""
    placements = []
    used = set()

    def search(index):
        if index == len(kinds):
            return True
        kind = kinds[index]
        options = _placement_options(kind, h, w, used, rng)
        for occupied, footprint in options[:384]:
            used.update(footprint)
            placements.append((kind, occupied, footprint))
            if search(index + 1):
                return True
            placements.pop()
            used.difference_update(footprint)
        return False

    if not search(0):
        raise ValueError(
            f"could not realize layout {kinds!r} on {h}x{w}; this is a generator defect"
        )
    return placements


def _draw_axis(ctx, name, default_options, overrides):
    lo, hi = _RANGES[name]
    options = list(range(lo, hi + 1)) if name in overrides else list(default_options)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")



def _is_canonical_anchor(seed, sample_index, *, has_overrides):
    """Schedule exactly one canonical-profile draw in every block of three."""
    if has_overrides:
        return False
    block, slot = divmod(sample_index, 3)
    digest = hashlib.sha256(
        f"{TASK_ID}|{VERSION}|canonical-profile|{seed}|{block}".encode()
    ).digest()
    return slot == digest[0] % 3

def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Every band supports the same exact override domain; difficulty only weights defaults.
    has_overrides = any(value is not None for value in overrides.values())
    canonical_anchor = _is_canonical_anchor(
        seed, sample_index, has_overrides=has_overrides
    )
    if canonical_anchor:
        h = _draw_axis(ctx, "grid_h", [8], overrides)
        w = _draw_axis(ctx, "grid_w", [9, 10, 11], overrides)
        layout_kind = ctx.draw_rng("canonical_layout").randrange(3)
        profiles = (
            (1, 1, 0),  # horizontal + vertical bridge
            (1, 0, 1),  # horizontal bridge + adjacent pair
            (0, 1, 1),  # vertical bridge + adjacent pair
        )
        wanted_h, wanted_v, wanted_adjacent = profiles[layout_kind]
        n_horizontal = _draw_axis(ctx, "n_horizontal", [wanted_h], overrides)
        n_vertical = _draw_axis(ctx, "n_vertical", [wanted_v], overrides)
        n_diagonal = _draw_axis(ctx, "n_diagonal", [0], overrides)
        n_triples = _draw_axis(ctx, "n_triples", [0], overrides)
        n_singletons = _draw_axis(ctx, "n_singletons", [0], overrides)
        n_adjacent = _draw_axis(ctx, "n_adjacent", [wanted_adjacent], overrides)
    else:
        h_defaults = [6, 7, 8, 8, 8, 9] if difficulty == "easy" else [7, 8, 8, 8, 9, 10, 11, 12]
        w_defaults = [7, 8, 9, 9, 10, 11] if difficulty == "easy" else [7, 8, 9, 9, 10, 10, 11, 12]
        h = _draw_axis(ctx, "grid_h", h_defaults, overrides)
        w = _draw_axis(ctx, "grid_w", w_defaults, overrides)

        if difficulty == "easy":
            h_options, v_options = [0, 1, 1], [0, 1, 1]
        elif difficulty == "hard":
            h_options, v_options = [1, 1, 2, 2], [1, 1, 2, 2]
        else:
            h_options, v_options = [0, 1, 1, 2], [0, 1, 1, 2]
        if overrides.get("n_vertical") == 0 and "n_horizontal" not in overrides:
            h_options = [1, 1, 2]
        n_horizontal = _draw_axis(ctx, "n_horizontal", h_options, overrides)
        if n_horizontal == 0 and "n_vertical" not in overrides:
            v_options = [1, 1, 2]
        n_vertical = _draw_axis(ctx, "n_vertical", v_options, overrides)
        n_diagonal = _draw_axis(ctx, "n_diagonal", [1], overrides)
        n_triples = _draw_axis(ctx, "n_triples", [1], overrides)
        n_singletons = _draw_axis(ctx, "n_singletons", [0, 1], overrides)
        n_adjacent = _draw_axis(
            ctx, "n_adjacent", [0, 1, 1] if difficulty == "easy" else [0, 1], overrides
        )

    kinds = (
        ["horizontal"] * n_horizontal
        + ["vertical"] * n_vertical
        + ["triple"] * n_triples
        + ["adjacent"] * n_adjacent
        + ["diagonal"] * n_diagonal
        + ["singleton"] * n_singletons
    )
    # Constrained line-bearing objects go first; within-kind geometry remains random.
    priority = {"horizontal": 0, "vertical": 1, "triple": 2,
                "adjacent": 3, "diagonal": 4, "singleton": 5}
    kinds.sort(key=priority.__getitem__)
    placements = _place_objects(kinds, h, w, ctx.draw_rng("layout"))
    colors = ctx.draw_rng("colors").sample(range(1, 10), len(placements))
    grid = full_grid(h, w, 0)
    for color, (_, occupied, _) in zip(colors, placements):
        for r, c in occupied:
            grid[r][c] = color
    return grid


def _positions(grid):
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))
    return positions


def _classification(grid):
    counts = Counter()
    reserved = []
    errors = []
    for color, points in _positions(grid).items():
        if len(points) == 1:
            counts["n_singletons"] += 1
            continue
        if len(points) == 2:
            a, b = points
            segment = _line_cells(a, b)
            if not segment:
                counts["n_diagonal"] += 1
                continue
            distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if distance == 1:
                counts["n_adjacent"] += 1
                continue
            counts["n_horizontal" if a[0] == b[0] else "n_vertical"] += 1
            if any(grid[r][c] != 0 for r, c in segment[1:-1]):
                errors.append(f"color {color} bridge interior is not empty")
            reserved.append((color, set(segment)))
            continue
        if len(points) == 3:
            aligned = []
            for i, a in enumerate(points):
                for b in points[i + 1:]:
                    segment = _line_cells(a, b)
                    if len(segment) >= 3:
                        aligned.append(segment)
            if len(aligned) != 1:
                errors.append(f"color {color} triple must have exactly one separated aligned pair")
                continue
            if any(grid[r][c] not in (0, color) for r, c in aligned[0]):
                errors.append(f"color {color} triple witness span is obstructed")
            counts["n_triples"] += 1
            reserved.append((color, set(aligned[0])))
            continue
        errors.append(f"color {color} appears {len(points)} times; expected 1, 2, or 3")

    for i, (color_a, cells_a) in enumerate(reserved):
        for color_b, cells_b in reserved[i + 1:]:
            if cells_a & cells_b:
                errors.append(f"reserved spans for colors {color_a} and {color_b} overlap")
    return counts, errors


def observe_overrides(grid):
    counts, _ = _classification(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_horizontal": counts["n_horizontal"],
        "n_vertical": counts["n_vertical"],
        "n_diagonal": counts["n_diagonal"],
        "n_triples": counts["n_triples"],
        "n_singletons": counts["n_singletons"],
        "n_adjacent": counts["n_adjacent"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    h, w = len(grid), width
    errors = []
    if not (6 <= h <= 12 and 6 <= w <= 12):
        errors.append(f"grid shape {h}x{w} outside [6,12]x[6,12]")
    bad = [value for row in grid for value in row
           if type(value) is not int or not 0 <= value <= 9]
    if bad:
        errors.append("cells must be integer colors in 0..9")
        return errors
    counts, geometry_errors = _classification(grid)
    errors.extend(geometry_errors)
    override_evidence = (
        isinstance(meta, dict)
        and isinstance(meta.get("overrides"), dict)
        and bool(meta["overrides"])
    )
    if counts["n_horizontal"] + counts["n_vertical"] == 0 and not override_evidence:
        errors.append(
            "no separated aligned exact pair; the canonical rule would not demonstrate a bridge"
        )
    for name in ("n_horizontal", "n_vertical"):
        if counts[name] > 2:
            errors.append(f"{name}={counts[name]} exceeds 2")
    for name in ("n_diagonal", "n_triples", "n_singletons", "n_adjacent"):
        if counts[name] > 1:
            errors.append(f"{name}={counts[name]} exceeds 1")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def rule_mirror(grid):
    """Pure-Python mirror for tests; the canonical Racket program stays authoritative."""
    out = [list(row) for row in grid]
    for color, points in _positions(grid).items():
        if len(points) != 2:
            continue
        for r, c in _line_cells(points[0], points[1]):
            out[r][c] = color
    return out


def _overconnect_multiples(grid):
    """RIVAL: connect aligned occurrences even when a color appears 3+ times."""
    out = [list(row) for row in grid]
    for color, points in _positions(grid).items():
        for index, a in enumerate(points):
            for b in points[index + 1:]:
                for r, c in _line_cells(a, b):
                    out[r][c] = color
    return out


def _connect_diagonal_l(grid):
    """RIVAL: exact pairs always connect; diagonal pairs use a row-then-column L."""
    out = [list(row) for row in grid]
    for color, points in _positions(grid).items():
        if len(points) != 2:
            continue
        a, b = points
        cells = list(_line_cells(a, b))
        if not cells:
            r1, c1 = a
            r2, c2 = b
            lo_c, hi_c = sorted((c1, c2))
            lo_r, hi_r = sorted((r1, r2))
            cells = [(r1, c) for c in range(lo_c, hi_c + 1)]
            cells.extend((r, c2) for r in range(lo_r, hi_r + 1))
        for r, c in cells:
            out[r][c] = color
    return out


def _has_exactly_two_witness(grid):
    return _overconnect_multiples(grid) != rule_mirror(grid)


def _has_axis_alignment_witness(grid):
    return _connect_diagonal_l(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "exactly_two_only": _has_exactly_two_witness,
    "axis_alignment_only": _has_axis_alignment_witness,
}
SEMANTIC_RIVALS = {
    "overconnect_multiples": _overconnect_multiples,
    "connect_diagonal_l": _connect_diagonal_l,
}
WITNESS_RIVALS = {
    "exactly_two_only": ["overconnect_multiples"],
    "axis_alignment_only": ["connect_diagonal_l"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
