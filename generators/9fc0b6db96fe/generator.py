"""Input generator for transform-the-legend-ordered-gallery.

Cell ``(0, 0)`` is a shared transform key (1 identity, 2 clockwise rotation,
3 half-turn, 4 left-right reflection).  The other nonzero cells of row 0 form
an ordered color legend.  Rows 2+ contain one separated component per legend
color.  The selected Racket authority crops and transforms those components in
legend order, then packs them left-to-right with one blank column between them.

This sampler exposes only three controls that are recoverable from returned
pixels: exact canonical profile, key, and legend layout.  Every ordinary draw
makes body scan order disagree with legend order; every nonidentity-key draw
contains a component whose transformed crop genuinely changes.
"""
from __future__ import annotations

from collections import deque
from itertools import permutations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fc0b6db96fe"
TASK_ID = GENERATOR_ID
RULE_HASH = "0235d1a8fb27"
VERSION = "3.1.0"
SUMMARY = (
    "Read the transform key at (0,0) and the ordered nonzero legend across row 0. "
    "For each legend color, crop its body component, apply the shared key, and "
    "pack the transformed crops into a one-row gallery in legend order."
)

INVARIANTS = [
    "the input has one of the five exact canonical (height,width,legend-count) profiles",
    "row 1 is blank; row 0 contains a valid key and a supported ordered legend",
    "rows 2+ contain exactly one separated 3..5-cell component per legend color",
    "body scan order differs from legend order on every generated input",
    "every generated nonidentity key changes at least one component crop",
    "default keys form a seed-permuted four-cycle, so every four consecutive examples expose all keys",
]

_PROFILE_SPECS = {
    "h9_w15_n4": (9, 15, 4),
    "h9_w14_n4": (9, 14, 4),
    "h12_w15_n3": (12, 15, 3),
    "h11_w13_n4": (11, 13, 4),
    "h9_w15_n3": (9, 15, 3),
}
_PROFILE_NAMES = tuple(_PROFILE_SPECS)
_PROFILE_OPTIONS = {
    "easy": _PROFILE_NAMES + ("h9_w15_n3",) * 8 + ("h9_w15_n4",) * 4 + ("h9_w14_n4",) * 2,
    "medium": _PROFILE_NAMES + ("h9_w14_n4",) * 5 + ("h11_w13_n4",) * 5,
    "hard": _PROFILE_NAMES + ("h12_w15_n3",) * 8 + ("h11_w13_n4",) * 5 + ("h9_w15_n4",) * 2,
}
_LEGEND_POSITIONS = {
    3: {
        "contiguous": (1, 2, 3),
        "spaced": (1, 3, 5),
        "mixed": (1, 2, 4),
    },
    4: {
        "contiguous": (1, 2, 3, 4),
        "spaced": (1, 3, 5, 7),
        "mixed": (1, 3, 4, 5),
    },
}
_LAYOUT_NAMES = ("contiguous", "spaced", "mixed")

AXES = {
    "profile": {
        "type": "str",
        "default": "uniform over the five exact canonical profiles",
        "valid": "h9_w15_n4|h9_w14_n4|h12_w15_n3|h11_w13_n4|h9_w15_n3",
    },
    "key": {
        "type": "int",
        "default": "seed-permuted four-cycle over sample_index; every consecutive four draws contain 1..4",
        "valid": "1..4",
    },
    "legend_layout": {
        "type": "str",
        "default": "uniform contiguous|spaced|mixed",
        "valid": "contiguous|spaced|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize_shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(cells):
    """All rotations/reflections of a small polyomino, normalized and unique."""
    variants = set()
    current = tuple(cells)
    for reflected in (False, True):
        shape = tuple((r, -c if reflected else c) for r, c in current)
        for _ in range(4):
            variants.add(_normalize_shape(shape))
            shape = tuple((c, -r) for r, c in shape)
    return variants


_BASE_MOTIFS = (
    ((0, 0), (1, 0), (1, 1)),                         # L triomino
    ((0, 0), (0, 1), (0, 2)),                         # line triomino
    ((0, 0), (1, 0), (2, 0), (2, 1)),                 # L tetromino
    ((0, 1), (1, 0), (1, 1), (1, 2)),                 # T tetromino
    ((0, 0), (1, 0), (1, 1), (2, 1)),                 # zig-zag tetromino
    ((0, 0), (0, 1), (1, 0), (1, 1)),                 # square tetromino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),         # P pentomino
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),         # V pentomino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),         # plus pentomino
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),         # W pentomino
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),         # T pentomino
)
_MOTIFS = tuple(sorted({v for base in _BASE_MOTIFS for v in _shape_variants(base)}))


def _render_shape(cells):
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    grid = [[0] * w for _ in range(h)]
    for r, c in cells:
        grid[r][c] = 1
    return grid


def _transform_grid(grid, key):
    if key == 1:
        return [list(row) for row in grid]
    if key == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if key == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if key == 4:
        return [list(reversed(row)) for row in grid]
    return [list(row) for row in grid]


_KEY_SENSITIVE_MOTIFS = {
    key: tuple(motif for motif in _MOTIFS if _transform_grid(_render_shape(motif), key) != _render_shape(motif))
    for key in (2, 3, 4)
}


def _scheduled_default_key(seed, sample_index, difficulty):
    """Choose a seed-specific key cycle that covers all four keys per lesson window."""
    band = difficulty if difficulty is not None else "unspecified"
    order = [1, 2, 3, 4]
    stable_rng(seed, f"{TASK_ID}|key_schedule|{band}", VERSION).shuffle(order)
    return order[sample_index % len(order)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if overrides.get("profile") is not None and type(overrides["profile"]) is not str:
        raise ValueError("profile must be a string")
    if overrides.get("key") is not None and type(overrides["key"]) is not int:
        raise ValueError("key must be an integer")
    if overrides.get("legend_layout") is not None and type(overrides["legend_layout"]) is not str:
        raise ValueError("legend_layout must be a string")


def _choose_motifs(ctx, n, key):
    rng = ctx.draw_rng("component_shapes")
    motifs = []
    first_pool = _MOTIFS if key == 1 else _KEY_SENSITIVE_MOTIFS[key]
    motifs.append(rng.choice(first_pool))
    motifs.extend(rng.choice(_MOTIFS) for _ in range(n - 1))
    return motifs


def _edge_column(rng, w, motif_width, side):
    if side == "left":
        return rng.randint(0, min(2, w - motif_width))
    lo = max(0, w - motif_width - 2)
    return rng.randint(lo, w - motif_width)


def _slot_origins(ctx, h, w, motifs):
    """Construct separated slots; no rejection loop and no dropped component."""
    rng = ctx.draw_rng("component_positions")
    n = len(motifs)
    origins = []
    if n == 4:
        for index, motif in enumerate(motifs):
            bh = max(r for r, _ in motif) + 1
            bw = max(c for _, c in motif) + 1
            top = index < 2
            left = index % 2 == 0
            r0 = 2 if top else h - bh
            c0 = _edge_column(rng, w, bw, "left" if left else "right")
            origins.append((r0, c0))
        return origins
    if n == 3:
        for index, motif in enumerate(motifs):
            bh = max(r for r, _ in motif) + 1
            bw = max(c for _, c in motif) + 1
            if index == 0:
                origins.append((2, _edge_column(rng, w, bw, "left")))
            elif index == 1:
                origins.append((2, _edge_column(rng, w, bw, "right")))
            else:
                center = (w - bw) // 2
                origins.append((h - bh, rng.randint(max(0, center - 2), min(w - bw, center + 2))))
        return origins
    raise ValueError(f"unsupported legend count {n}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", _PROFILE_OPTIONS.get(difficulty, _PROFILE_NAMES))
    scheduled_key = _scheduled_default_key(seed, sample_index, difficulty)
    if overrides.get("key") is None:
        key = ctx.draw_int("key", scheduled_key, scheduled_key)
    else:
        key = ctx.draw_int("key", 1, 4)
    layout = ctx.draw_choice("legend_layout", _LAYOUT_NAMES)
    h, w, n = _PROFILE_SPECS[profile]

    colors = tuple(ctx.draw_rng("legend_colors").sample([c for c in range(1, 10) if c != key], n))
    grid = full_grid(h, w, 0)
    grid[0][0] = key
    for column, color in zip(_LEGEND_POSITIONS[n][layout], colors):
        grid[0][column] = color

    motifs = _choose_motifs(ctx, n, key)
    origins = _slot_origins(ctx, h, w, motifs)
    derangements = tuple(p for p in permutations(range(n)) if all(i != p[i] for i in range(n)))
    body_permutation = ctx.draw_rng("body_order").choice(derangements)
    physical_colors = tuple(colors[i] for i in body_permutation)
    for motif, (r0, c0), color in zip(motifs, origins, physical_colors):
        for dr, dc in motif:
            if grid[r0 + dr][c0 + dc] != 0:
                raise RuntimeError("constructive component slots unexpectedly overlap")
            grid[r0 + dr][c0 + dc] = color
    return grid


def _rectangular_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    return None


def _same_color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(2, h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _nonzero_components(grid):
    """Racket-equivalent body components: 4-connected through any nonzero color."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(2, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _legend_entries(grid):
    return [(c, value) for c, value in enumerate(grid[0][1:], start=1) if value != 0]


def _layout_name(n, positions):
    return next((name for name, expected in _LEGEND_POSITIONS.get(n, {}).items() if tuple(positions) == expected), None)


def _profile_name(grid, n):
    signature = (len(grid), len(grid[0]), n)
    return next((name for name, spec in _PROFILE_SPECS.items() if spec == signature), None)


def self_check(grid, *, difficulty=None, meta=None):
    malformed = _rectangular_grid_error(grid)
    if malformed:
        return [malformed]
    h, w = len(grid), len(grid[0])
    errors = []
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    key = grid[0][0]
    if key not in (1, 2, 3, 4):
        errors.append(f"cell (0,0)={key} is not a key in 1..4")
    if h < 3:
        return errors + ["grid needs row 0, blank row 1, and a body"]
    if any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be blank")

    entries = _legend_entries(grid)
    positions = [column for column, _ in entries]
    colors = [color for _, color in entries]
    n = len(colors)
    profile = _profile_name(grid, n)
    if profile is None:
        errors.append(f"(height,width,legend-count)=({h},{w},{n}) is not a canonical profile")
    layout = _layout_name(n, positions)
    if layout is None:
        errors.append(f"legend positions {positions} are not a supported layout")
    if len(set(colors)) != n:
        errors.append("legend colors must be distinct")
    if key in colors:
        errors.append("key color must be distinct from legend colors")

    allowed = set(colors)
    for r in range(2, h):
        for c in range(w):
            value = grid[r][c]
            if value and value not in allowed:
                errors.append(f"body color {value} is absent from the legend")
                break
        if errors and errors[-1].startswith("body color"):
            break

    for r in range(2, h):
        for c in range(w):
            value = grid[r][c]
            if not value:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < h and nc < w and grid[nr][nc] not in (0, value):
                    errors.append("different body colors may not touch orthogonally")
                    break
            if errors and errors[-1] == "different body colors may not touch orthogonally":
                break
        if errors and errors[-1] == "different body colors may not touch orthogonally":
            break

    color_components = {}
    for color in colors:
        components = _same_color_components(grid, color)
        color_components[color] = components
        if len(components) != 1:
            errors.append(f"legend color {color} has {len(components)} body components, expected 1")
        elif not 3 <= len(components[0]) <= 5:
            errors.append(f"legend color {color} component has {len(components[0])} cells, expected 3..5")

    if colors and all(len(color_components.get(color, ())) == 1 for color in colors):
        scan = [grid[cells[0][0]][cells[0][1]] for cells in _nonzero_components(grid)]
        if scan == colors:
            errors.append("body scan order must differ from legend order")
        if sorted(scan) != sorted(colors):
            errors.append("body components do not realize the legend colors exactly once")
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    entries = _legend_entries(grid)
    n = len(entries)
    return {
        "profile": _profile_name(grid, n),
        "key": grid[0][0],
        "legend_layout": _layout_name(n, [column for column, _ in entries]),
    }


def strict_canonical_like(grid):
    return self_check(grid)


def _component_crop(grid, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [grid[r][c] if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _pack_gallery(parts, gap=1):
    if not parts:
        return [[0]]
    height = max(len(part) for part in parts)
    width = sum(len(part[0]) for part in parts) + gap * (len(parts) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for part in parts:
        for r, row in enumerate(part):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(part[0]) + gap
    return out


def _gallery(grid, *, legend_order=True, apply_key=True):
    components = _nonzero_components(grid)
    if legend_order:
        ordered = []
        for _, color in _legend_entries(grid):
            matches = [cells for cells in components if grid[cells[0][0]][cells[0][1]] == color]
            if not matches:
                raise ValueError(f"legend color {color} has no body component")
            ordered.append(matches[0])
    else:
        ordered = components
    key = grid[0][0] if apply_key else 1
    return _pack_gallery([_transform_grid(_component_crop(grid, cells), key) for cells in ordered])


def reference_output(grid):
    """Python mirror for tests/semantic rivals; canonical Racket remains authority."""
    return _gallery(grid)


def _body_scan_order_rival(grid):
    return _gallery(grid, legend_order=False)


def _ignore_key_rival(grid):
    return _gallery(grid, apply_key=False)


def _legend_order_changes_answer(grid):
    return reference_output(grid) != _body_scan_order_rival(grid)


def _key_transform_changes_answer(grid):
    return grid[0][0] != 1 and reference_output(grid) != _ignore_key_rival(grid)


SEMANTIC_WITNESSES = {
    "legend_order_changes_answer": _legend_order_changes_answer,
    "key_transform_changes_answer": _key_transform_changes_answer,
}
SEMANTIC_RIVALS = {
    "body_scan_order": _body_scan_order_rival,
    "ignore_key": _ignore_key_rival,
}
WITNESS_RIVALS = {
    "legend_order_changes_answer": ["body_scan_order"],
    "key_transform_changes_answer": ["ignore_key"],
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Require the demonstrations to falsify any query-changing named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    pairs = list(demos) + [query]
    for index, episode in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{label} must contain input and output")
            continue
        errors = strict_canonical_like(episode["input"])
        if errors:
            reasons.append(f"{label} is outside the strict grammar: {errors[0]}")
            continue
        if episode["output"] != reference_output(episode["input"]):
            reasons.append(f"{label} output disagrees with the selected rule")
    if reasons:
        return reasons

    truth = reference_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos) and rival(query["input"]) != truth:
            reasons.append(f"named rival {name!r} fits every demo but changes the query answer")
    return reasons
