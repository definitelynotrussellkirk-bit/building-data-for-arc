"""Input sampler for multi-marker, rotation-coded template stamping.

The unchanged Racket authority extracts the single color-2 prototype, normalizes
its bounding box, and stamps a clockwise rotation at every marker onto a fresh
zero grid: 1=id, 3=90, 4=180, 6=270.  Stamp pixels outside the canvas are
clipped and overlapping stamps form a union.

Default even sample indices are explicit teaching scenes: all four rotation
codes plus a repeated code occur in five disjoint stamp regions, using a shape
with four distinct rotations.  Therefore each teaching scene refutes all
single-code mapping errors, the canonical-fitting "one stamp per code" shortcut,
and the canonical-fitting "only three markers" shortcut.  Odd indices alternate
between a canonical-profile component and a broad component.  Exact overrides
always choose the broad constructor and remain valid in every difficulty band.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2288bfea426b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4df94edcd4cc"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "One 4-connected red(2) prototype and 2-5 isolated rotation markers. "
    "Markers 1/3/4/6 stamp the bounding-box-normalized prototype at 0/90/180/270 "
    "degrees clockwise in cyan(8) on a fresh zero grid; edge pixels clip and "
    "overlapping stamps union. Alternating teaching scenes expose all codes, "
    "marker multiplicity, and canonical-fitting shortcuts."
)
INVARIANTS = [
    "background is 0; input colors are exactly from 0,1,2,3,4,6",
    "one 4-connected color-2 prototype of 3..6 cells",
    "2..5 isolated markers use only 1,3,4,6",
    "prototype and marker cells do not 4-touch",
    "Racket is the label authority; Python predictions are semantic contracts only",
]
AXES = {
    "grid_h": {"type": "int", "default": "teaching 18; core 13; broad 10..18", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "teaching 18; core 13; broad 11..18", "valid": "11..18"},
    "template_size": {"type": "int", "default": "teaching 5..6; core 5; broad 3..6", "valid": "3..6"},
    "n_markers": {"type": "int", "default": "teaching 5; core 3; broad 2..5", "valid": "2..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("teaching", "ordinary")

_CODES = (1, 3, 4, 6)
_TURNS = {1: 0, 3: 1, 4: 2, 6: 3}
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AXIS_BOUNDS = {
    "grid_h": (10, 18),
    "grid_w": (11, 18),
    "template_size": (3, 6),
    "n_markers": (2, 5),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Every three consecutive default indices contain a teaching scene."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("missing color-2 prototype")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


@lru_cache(maxsize=6)
def _polyominoes(size):
    """All fixed 4-connected polyominoes through size six, without retries."""
    if size == 1:
        return (((0, 0),),)
    result = set()
    for smaller in _polyominoes(size - 1):
        occupied = set(smaller)
        frontier = {(r + dr, c + dc) for r, c in smaller for dr, dc in _STEPS} - occupied
        for point in sorted(frontier):
            result.add(_normalize((*smaller, point)))
    return tuple(sorted(result))


def _rotate_turns(cells, turns):
    result = tuple(cells)
    for _ in range(turns % 4):
        result = _normalize((c, -r) for r, c in result)
    return tuple(sorted(result))


def _rotated(cells, code):
    if code not in _TURNS:
        raise ValueError(f"unknown rotation marker: {code}")
    return _rotate_turns(cells, _TURNS[code])


def _scene(grid):
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    markers = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _CODES]
    return source, _normalize(source), markers


def observe_overrides(grid):
    source, _, markers = _scene(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(source),
        "n_markers": len(markers),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds ARC 30x30 limit"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 3, 4, 6) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,3,4,6"]

    source = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    markers = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _CODES}
    errors = []
    if not 3 <= len(source) <= 6:
        errors.append(f"prototype must contain 3..6 cells, found {len(source)}")
    if source:
        reached = {min(source)}
        todo = list(reached)
        for r, c in todo:
            for dr, dc in _STEPS:
                point = r + dr, c + dc
                if point in source and point not in reached:
                    reached.add(point)
                    todo.append(point)
        if reached != source:
            errors.append("color-2 prototype must be one 4-connected component")
    if not 2 <= len(markers) <= 5:
        errors.append(f"expected 2..5 rotation markers, found {len(markers)}")
    occupied = source | markers
    if any((r + dr, c + dc) in occupied for r, c in markers for dr, dc in _STEPS):
        errors.append("markers must not 4-touch the prototype or another marker")
    return errors


def strict_canonical_like(grid):
    """The sampler's lawful one-prototype domain, not an exact silhouette test."""
    return self_check(grid)


def _prediction(grid, rival=None):
    """Executable semantic contract; the unchanged Racket program is authority."""
    _, shape, markers = _scene(grid)
    h, w = len(grid), len(grid[0])
    if rival == "first_three_markers":
        markers = markers[:3]
    seen = set()
    out = full_grid(h, w, 0)
    for ar, ac, code in markers:
        if rival == "deduplicate_marker_code" and code in seen:
            continue
        seen.add(code)
        actual = code
        if isinstance(rival, tuple) and len(rival) == 3 and rival[0] == "map" and code == rival[1]:
            actual = rival[2]
        for dr, dc in _rotated(shape, actual):
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 8
    return out


def _rival(name):
    def predict(grid):
        return _prediction(grid, name)
    predict.__name__ = name
    return predict


def _mapping_rival(code, replacement):
    def predict(grid):
        return _prediction(grid, ("map", code, replacement))
    predict.__name__ = f"code_{code}_as_{replacement}"
    return predict


SEMANTIC_RIVALS = {
    "deduplicate_marker_code": _rival("deduplicate_marker_code"),
    "first_three_markers": _rival("first_three_markers"),
}
SEMANTIC_RIVALS.update({
    f"code_{code}_as_{replacement}": _mapping_rival(code, replacement)
    for code in _CODES for replacement in _CODES if replacement != code
})
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("deduplicate_marker_code", "first_three_markers")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(name):
    def distinguishes(grid):
        return _prediction(grid) != SEMANTIC_RIVALS[name](grid)
    distinguishes.__name__ = f"distinguishes_{name}"
    return distinguishes


SEMANTIC_WITNESSES = {name: _witness(name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not universal proof of rule uniqueness."""
    query_grid = query["input"] if isinstance(query, dict) else query
    expected = _prediction(query_grid)
    return [
        f"declared rival {name} fits every demonstration and disagrees on query"
        for name, predict in LESSON_COMPETITORS.items()
        if all(predict(pair["input"]) == pair["output"] for pair in demos)
        and predict(query_grid) != expected
    ]


def _make_grid(h, w, shape, origin, markers):
    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[origin[0] + dr][origin[1] + dc] = 2
    for r, c, code in markers:
        grid[r][c] = code
    return grid


def _teaching(ctx, h, w, size):
    """Five disjoint 6x6 stamp regions: all codes plus one repeated code."""
    if (h, w) != (18, 18) or size not in (5, 6):
        raise RuntimeError("teaching profile geometry invariant failed")
    rng = ctx.draw_rng("teaching_layout")
    shapes = [shape for shape in _polyominoes(size)
              if len({_rotate_turns(shape, turn) for turn in range(4)}) == 4]
    shape = rng.choice(shapes)
    codes = list(_CODES)
    rng.shuffle(codes)
    codes.append(rng.choice(codes))
    marker_origins = ((0, 0), (0, 6), (0, 12), (6, 0), (6, 6))
    markers = [(r, c, code) for (r, c), code in zip(marker_origins, codes)]
    ph = max(r for r, _ in shape) + 1
    pw = max(c for _, c in shape) + 1
    source_origin = (12 + rng.randrange(7 - ph), 12 + rng.randrange(7 - pw))
    grid = _make_grid(h, w, shape, source_origin, markers)
    expected = _prediction(grid)
    failed = [name for name, predict in SEMANTIC_RIVALS.items() if predict(grid) == expected]
    if failed:
        raise RuntimeError(f"teaching construction failed to refute: {failed}")
    return grid


def _broad(ctx, h, w, size, n_markers, *, distinct_codes=False):
    rng = ctx.draw_rng("broad_layout")
    shape = rng.choice(_polyominoes(size))
    ph = max(r for r, _ in shape) + 1
    pw = max(c for _, c in shape) + 1
    origin = (rng.randrange(h - ph + 1), rng.randrange(w - pw + 1))
    source = {(origin[0] + r, origin[1] + c) for r, c in shape}
    candidates = [
        (r, c) for r in range(h) for c in range(w)
        if (r, c) not in source
        and all((r + dr, c + dc) not in source for dr, dc in _STEPS)
    ]
    positions = []
    for _ in range(n_markers):
        if not candidates:
            raise RuntimeError("marker capacity invariant failed; refusing a shortened scene")
        point = rng.choice(candidates)
        positions.append(point)
        candidates = [candidate for candidate in candidates
                      if abs(candidate[0] - point[0]) + abs(candidate[1] - point[1]) > 1]

    if distinct_codes:
        codes = rng.sample(_CODES, n_markers)
    else:
        repeated = n_markers == 5 or ctx.draw_choice("marker_pattern", ("distinct", "repeated")) == "repeated"
        if repeated:
            if n_markers == 2:
                codes = [rng.choice(_CODES)] * 2
            else:
                base = rng.sample(_CODES, min(n_markers - 1, len(_CODES)))
                codes = base + [rng.choice(base) for _ in range(n_markers - len(base))]
                rng.shuffle(codes)
        else:
            codes = rng.sample(_CODES, n_markers)
    return _make_grid(h, w, shape, origin, [(*point, code) for point, code in zip(positions, codes)])


def _weighted_domain(lo, hi, favored):
    return tuple(range(lo, hi + 1)) + tuple(favored) * 3


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    explicit = any(value is not None for value in overrides.values())
    teaching = not explicit and schedule_profile(seed, sample_index, difficulty) == "teaching"
    core = not explicit and not teaching and sample_index % 4 == 1

    if teaching:
        h = ctx.draw_choice("grid_h", (18,))
        w = ctx.draw_choice("grid_w", (18,))
        size = ctx.draw_choice("template_size", (5, 6))
        n_markers = ctx.draw_choice("n_markers", (5,))
        return _teaching(ctx, h, w, size)

    if core:
        h = ctx.draw_choice("grid_h", (13,))
        w = ctx.draw_choice("grid_w", (13,))
        size = ctx.draw_choice("template_size", (5,))
        n_markers = ctx.draw_choice("n_markers", (3,))
        return _broad(ctx, h, w, size, n_markers, distinct_codes=True)

    favored_h = {
        None: (12, 13, 14, 15), "easy": (10, 11, 12, 13),
        "medium": (12, 13, 14, 15, 16), "hard": (15, 16, 17, 18),
    }[difficulty]
    favored_w = {
        None: (12, 13, 14, 15), "easy": (11, 12, 13, 14),
        "medium": (12, 13, 14, 15, 16), "hard": (15, 16, 17, 18),
    }[difficulty]
    favored_size = {
        None: (3, 4, 5, 6), "easy": (3, 3, 4),
        "medium": (4, 5), "hard": (5, 6, 6),
    }[difficulty]
    favored_markers = {
        None: (2, 3, 4, 5), "easy": (2, 2, 3),
        "medium": (3, 4), "hard": (4, 5, 5),
    }[difficulty]
    h = ctx.draw_choice("grid_h", _weighted_domain(10, 18, favored_h))
    w = ctx.draw_choice("grid_w", _weighted_domain(11, 18, favored_w))
    size = ctx.draw_choice("template_size", _weighted_domain(3, 6, favored_size))
    n_markers = ctx.draw_choice("n_markers", _weighted_domain(2, 5, favored_markers))
    return _broad(ctx, h, w, size, n_markers)
