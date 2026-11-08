"""Generator for arc_puzzle_bank_21_set3:S3_E6 (Down-Left Echo).

Every maroon (9) source attempts to paint a gray (5) cell one step down-left.
The paint occurs only when that target is in bounds and background 0.  Lawful
training scenes include positive echoes, occupied-target blockers, boundary
sources, and one unrelated canonical-style distractor object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be743fd05a59"
TASK_ID = "be743fd05a59"
VERSION = "3.0.0"
RULE_HASH = "1ee75c1a7933"

SUMMARY = (
    "On a 0-background grid, every isolated maroon (9) source casts a gray "
    "(5) echo exactly one cell down-left. In-bounds background targets are "
    "painted; occupied targets and out-of-bounds targets are skipped. Each "
    "scene retains at least one paintable source and includes one unrelated "
    "color-1/3/4 bar, domino, or 2x2 block matching the canonical distractor "
    "grammar."
)

INVARIANTS = [
    "the input is an 8..12 by 9..14 ARC grid with background 0",
    "there are 2..6 pairwise-isolated maroon (9) source cells",
    "every in-bounds source target is either background or the one distractor color",
    "at least one source has an in-bounds empty target, so the output is non-identity",
    "the non-source foreground is one canonical-style object plus optional singleton target blockers",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DISTRACTOR_COLORS = (1, 3, 4)
_DISTRACTOR_STYLES = ("domino", "bar", "block")
_BRANCH_SCHEDULE = ((0, 0), (1, 0), (0, 1), (1, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..14",
        "valid": "9..14",
    },
    "source_count": {
        "type": "int",
        "default": "difficulty-aware 2..6, raised only before drawing for explicit branch counts",
        "valid": "2..6",
    },
    "blocked_source_count": {
        "type": "int",
        "default": "four-step teaching schedule",
        "valid": "0..2",
    },
    "boundary_source_count": {
        "type": "int",
        "default": "four-step teaching schedule",
        "valid": "0..2",
    },
    "distractor_color": {
        "type": "color",
        "default": "rng from canonical colors",
        "valid": "1|3|4",
    },
    "distractor_style": {
        "type": "str",
        "default": "rng canonical-style object",
        "valid": "domino|bar|block",
    },
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override axis/axes: {', '.join(unknown)}")

    int_ranges = {
        "grid_h": (8, 12),
        "grid_w": (9, 14),
        "source_count": (2, 6),
        "blocked_source_count": (0, 2),
        "boundary_source_count": (0, 2),
    }
    for name, (lo, hi) in int_ranges.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")

    color = overrides.get("distractor_color")
    if color is not None and color not in _DISTRACTOR_COLORS:
        raise ValueError(
            f"distractor_color must be one of {_DISTRACTOR_COLORS}"
        )
    style = overrides.get("distractor_style")
    if style is not None and style not in _DISTRACTOR_STYLES:
        raise ValueError(
            f"distractor_style must be one of {_DISTRACTOR_STYLES}"
        )

    source = overrides.get("source_count")
    blocked = overrides.get("blocked_source_count")
    boundary = overrides.get("boundary_source_count")
    if source is not None and blocked is not None and boundary is not None:
        if blocked + boundary > source - 1:
            raise ValueError(
                "blocked_source_count + boundary_source_count must leave at "
                "least one paintable source"
            )
    elif source is not None and blocked is not None and blocked > source - 1:
        raise ValueError("blocked_source_count must leave one paintable source")
    elif source is not None and boundary is not None and boundary > source - 1:
        raise ValueError("boundary_source_count must leave one paintable source")


def _dimension_bounds(difficulty):
    if difficulty == "easy":
        return (8, 9), (9, 10)
    if difficulty == "hard":
        return (10, 12), (12, 14)
    return (8, 11), (9, 12)


def _source_bounds(difficulty):
    if difficulty == "easy":
        return 2, 3
    if difficulty == "hard":
        return 4, 6
    return 3, 5


def _draw_dimension(ctx, label, declared_lo, declared_hi, default_lo, default_hi):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, declared_lo, declared_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _scheduled_branch_pair(seed, sample_index):
    offset = stable_rng(seed, f"{TASK_ID}|branch_schedule", VERSION).randrange(
        len(_BRANCH_SCHEDULE)
    )
    return _BRANCH_SCHEDULE[(offset + int(sample_index)) % len(_BRANCH_SCHEDULE)]


def _record_scheduled(ctx, label, value):
    # draw_choice over a singleton is a public, provenance-preserving way to
    # record a deterministic schedule rather than a random draw.
    return ctx.draw_choice(label, (value,))


def _draw_branch_counts(ctx, source_count):
    blocked_explicit = ctx.overrides.get("blocked_source_count") is not None
    boundary_explicit = ctx.overrides.get("boundary_source_count") is not None
    desired_blocked, desired_boundary = _scheduled_branch_pair(
        ctx.seed, ctx.sample_index
    )

    if blocked_explicit:
        blocked = ctx.draw_int("blocked_source_count", 0, 2)
    else:
        blocked = None
    if boundary_explicit:
        boundary = ctx.draw_int("boundary_source_count", 0, 2)
    else:
        boundary = None

    if blocked is not None and boundary is not None:
        if blocked + boundary > source_count - 1:
            raise ValueError(
                "blocked_source_count + boundary_source_count must leave at "
                "least one paintable source"
            )
        return blocked, boundary

    if blocked is not None:
        capacity = source_count - 1 - blocked
        if capacity < 0:
            raise ValueError("blocked_source_count must leave one paintable source")
        boundary = _record_scheduled(
            ctx, "boundary_source_count", min(desired_boundary, capacity, 2)
        )
        return blocked, boundary

    if boundary is not None:
        capacity = source_count - 1 - boundary
        if capacity < 0:
            raise ValueError("boundary_source_count must leave one paintable source")
        blocked = _record_scheduled(
            ctx, "blocked_source_count", min(desired_blocked, capacity, 2)
        )
        return blocked, boundary

    feasible = [
        pair
        for pair in _BRANCH_SCHEDULE
        if pair[0] + pair[1] <= source_count - 1
    ]
    scheduled = (desired_blocked, desired_boundary)
    if scheduled not in feasible:
        scheduled = feasible[(ctx.seed + ctx.sample_index) % len(feasible)]
    blocked = _record_scheduled(ctx, "blocked_source_count", scheduled[0])
    boundary = _record_scheduled(ctx, "boundary_source_count", scheduled[1])
    return blocked, boundary


def _candidate_source_positions(h, w, *, boundary):
    if boundary:
        # Left-edge and bottom-edge sources both exercise the bounds check.
        return [(r, 0) for r in range(h - 1)] + [
            (h - 1, c) for c in range(1, w)
        ]
    return [(r, c) for r in range(h - 1) for c in range(1, w)]


def _target(position):
    r, c = position
    return r + 1, c - 1


def _in_bounds(position, h, w):
    r, c = position
    return 0 <= r < h and 0 <= c < w


def _choose_sources(h, w, kinds, rng):
    chosen: list[tuple[int, int]] = []
    reserved_targets: set[tuple[int, int]] = set()
    kind_by_source: dict[tuple[int, int], str] = {}

    # Boundary positions are scarcer; place them first, then blocked, then active.
    ordered_kinds = sorted(kinds, key={"boundary": 0, "blocked": 1, "active": 2}.get)
    for index, kind in enumerate(ordered_kinds):
        candidates = _candidate_source_positions(h, w, boundary=kind == "boundary")
        rng.shuffle(candidates)
        for pos in candidates:
            if pos in chosen or pos in reserved_targets:
                continue
            if any(abs(pos[0] - r) + abs(pos[1] - c) < 3 for r, c in chosen):
                continue
            target = _target(pos)
            if kind != "boundary":
                if not _in_bounds(target, h, w):
                    continue
                if target in chosen or target in reserved_targets:
                    continue
            # Do not place a boundary source on a previously reserved target.
            chosen.append(pos)
            kind_by_source[pos] = kind
            if kind != "boundary":
                reserved_targets.add(target)
            break
        else:
            raise ValueError(
                f"could not place source {index + 1}/{len(ordered_kinds)} "
                f"of kind {kind!r} on {h}x{w} grid"
            )
    return chosen, kind_by_source, reserved_targets


def _shape_cells(style, rng):
    if style == "block":
        return ((0, 0), (0, 1), (1, 0), (1, 1))
    horizontal = bool(rng.randrange(2))
    length = 2 if style == "domino" else 3
    if horizontal:
        return tuple((0, dc) for dc in range(length))
    return tuple((dr, 0) for dr in range(length))


def _place_distractor(g, style, color, forbidden, blocked_targets, rng):
    h, w = len(g), len(g[0])
    shape = _shape_cells(style, rng)
    sh = max(dr for dr, _ in shape) + 1
    sw = max(dc for _, dc in shape) + 1
    anchors = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(anchors)
    for r0, c0 in anchors:
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        if cells & forbidden:
            continue
        # Keep the canonical-style object separate from singleton target blockers.
        if any(
            abs(r - br) + abs(c - bc) == 1
            for r, c in cells
            for br, bc in blocked_targets
        ):
            continue
        for r, c in cells:
            g[r][c] = color
        return cells
    raise ValueError(f"could not place {style} distractor on {h}x{w} grid")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (h_lo, h_hi), (w_lo, w_hi) = _dimension_bounds(difficulty)
    h = _draw_dimension(ctx, "grid_h", 8, 12, h_lo, h_hi)
    w = _draw_dimension(ctx, "grid_w", 9, 14, w_lo, w_hi)

    source_override = overrides.get("source_count")
    blocked_override = overrides.get("blocked_source_count")
    boundary_override = overrides.get("boundary_source_count")
    desired_blocked, desired_boundary = _scheduled_branch_pair(seed, sample_index)
    minimum_sources = 2
    if blocked_override is not None:
        minimum_sources = max(minimum_sources, blocked_override + 1)
    else:
        minimum_sources = max(minimum_sources, desired_blocked + 1)
    if boundary_override is not None:
        minimum_sources = max(
            minimum_sources,
            (blocked_override or desired_blocked) + boundary_override + 1,
        )
    elif blocked_override is not None:
        minimum_sources = max(
            minimum_sources, blocked_override + desired_boundary + 1
        )
    else:
        minimum_sources = max(
            minimum_sources, desired_blocked + desired_boundary + 1
        )

    if source_override is not None:
        source_count = ctx.draw_int("source_count", 2, 6)
    else:
        s_lo, s_hi = _source_bounds(difficulty)
        s_lo = max(s_lo, minimum_sources)
        s_hi = max(s_hi, s_lo)
        source_count = ctx.draw_int("source_count", s_lo, min(6, s_hi))

    blocked_count, boundary_count = _draw_branch_counts(ctx, source_count)
    if blocked_count + boundary_count > source_count - 1:
        raise ValueError(
            "blocked_source_count + boundary_source_count must leave at least "
            "one paintable source"
        )

    distractor_color = ctx.draw_choice("distractor_color", _DISTRACTOR_COLORS)
    distractor_style = ctx.draw_choice("distractor_style", _DISTRACTOR_STYLES)
    rng = ctx.draw_rng("layout")

    kinds = (
        ["blocked"] * blocked_count
        + ["boundary"] * boundary_count
        + ["active"] * (source_count - blocked_count - boundary_count)
    )
    sources, kind_by_source, reserved_targets = _choose_sources(h, w, kinds, rng)
    g = full_grid(h, w, 0)
    for r, c in sources:
        g[r][c] = 9

    blocked_targets = {
        _target(source)
        for source, kind in kind_by_source.items()
        if kind == "blocked"
    }
    for r, c in blocked_targets:
        g[r][c] = distractor_color

    forbidden = set(sources) | reserved_targets
    _place_distractor(
        g,
        distractor_style,
        distractor_color,
        forbidden,
        blocked_targets,
        rng,
    )

    errors = self_check(g)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return g


def _coerce_grid(grid):
    if not isinstance(grid, list):
        return None
    rows = []
    for row in grid:
        if isinstance(row, str):
            if not row or not row.isdigit():
                return None
            rows.append([int(value) for value in row])
        elif isinstance(row, list):
            rows.append(list(row))
        else:
            return None
    return rows


def _components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _valid_decorative_shape(component):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    size = len(component)
    if size == 2:
        return (height, width) in ((1, 2), (2, 1))
    if size == 3:
        return (height, width) in ((1, 3), (3, 1))
    if size == 4:
        return height == width == 2
    return False


def _analyze(grid):
    g = _coerce_grid(grid)
    if g is None or not g or not g[0]:
        return None, ["grid must be a non-empty rectangular list or digit-string grid"]
    h, w = len(g), len(g[0])
    if any(len(row) != w for row in g):
        return None, ["ragged grid"]
    errors = []
    if not (8 <= h <= 12 and 9 <= w <= 14):
        errors.append(f"grid size {h}x{w} outside 8..12 by 9..14")
    if any(type(value) is not int or not 0 <= value <= 9 for row in g for value in row):
        return None, errors + ["grid contains a non-integer or color outside 0..9"]
    illegal = sorted({value for row in g for value in row} - {0, 1, 3, 4, 9})
    if illegal:
        errors.append(f"input uses illegal color(s): {illegal}")

    sources = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 9]
    if not 2 <= len(sources) <= 6:
        errors.append(f"expected 2..6 maroon sources, found {len(sources)}")
    for i, first in enumerate(sources):
        for second in sources[i + 1 :]:
            if abs(first[0] - second[0]) + abs(first[1] - second[1]) < 3:
                errors.append("maroon sources must be pairwise Manhattan-separated by at least 3")
                break
        if errors and errors[-1].startswith("maroon sources"):
            break

    distractor_colors = sorted(
        {value for row in g for value in row if value not in (0, 9)}
    )
    if len(distractor_colors) != 1 or distractor_colors[0] not in _DISTRACTOR_COLORS:
        errors.append(
            "expected exactly one distractor color from {1,3,4}"
        )
        distractor_color = None
    else:
        distractor_color = distractor_colors[0]

    active = blocked = boundary = 0
    target_cells = set()
    for r, c in sources:
        target = (r + 1, c - 1)
        if not _in_bounds(target, h, w):
            boundary += 1
            continue
        target_cells.add(target)
        value = g[target[0]][target[1]]
        if value == 0:
            active += 1
        elif value == 9:
            errors.append("a maroon source occupies another source's echo target")
        elif distractor_color is not None and value == distractor_color:
            blocked += 1
        else:
            errors.append("an echo target contains an undeclared blocker color")
    if active < 1:
        errors.append("at least one source must have an in-bounds empty echo target")
    if blocked > 2:
        errors.append(f"at most two occupied-target blockers are lawful, found {blocked}")
    if boundary > 2:
        errors.append(f"at most two boundary sources are lawful, found {boundary}")

    decoration_style = None
    if distractor_color is not None:
        colored_cells = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if g[r][c] == distractor_color
        }
        components = _components(colored_cells)
        decorative = []
        for component in components:
            if len(component) == 1:
                cell = next(iter(component))
                if cell not in target_cells:
                    errors.append(
                        "singleton distractor must be an occupied echo target"
                    )
            else:
                decorative.append(component)
        if len(decorative) != 1:
            errors.append(
                f"expected exactly one non-singleton distractor object, found {len(decorative)}"
            )
        elif not _valid_decorative_shape(decorative[0]):
            errors.append(
                "distractor object must be a domino, length-3 bar, or 2x2 block"
            )
        else:
            size = len(decorative[0])
            decoration_style = {2: "domino", 3: "bar", 4: "block"}[size]

    analysis = {
        "grid_h": h,
        "grid_w": w,
        "source_count": len(sources),
        "blocked_source_count": blocked,
        "boundary_source_count": boundary,
        "distractor_color": distractor_color,
        "distractor_style": decoration_style,
        "active_source_count": active,
    }
    return analysis, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def observe_overrides(grid):
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe malformed scene: " + "; ".join(errors))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "source_count": analysis["source_count"],
        "blocked_source_count": analysis["blocked_source_count"],
        "boundary_source_count": analysis["boundary_source_count"],
        "distractor_color": analysis["distractor_color"],
        "distractor_style": analysis["distractor_style"],
    }


def rule_mirror(grid):
    """Python mirror for focused tests only; Racket remains output authority."""
    g = _coerce_grid(grid)
    if g is None:
        raise ValueError("invalid grid")
    errors = self_check(g)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    out = [row[:] for row in g]
    h, w = len(g), len(g[0])
    for r in range(h):
        for c in range(w):
            if g[r][c] != 9:
                continue
            rr, cc = r + 1, c - 1
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = 5
    return out
