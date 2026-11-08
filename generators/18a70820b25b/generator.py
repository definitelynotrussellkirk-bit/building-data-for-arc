"""Generator for ARC task 6d58a25d / content task 18a70820b25b.

The uniquely largest non-zero 4-connected component is the source shape.
The other non-zero colour appears as isolated marker dots.  For every column
occupied by the source shape, a marker of the other colour *below the
bottommost source cell in that column* selects that column.  Selected columns
are filled from one cell below the source down to the bottom row in the marker
colour.  The input also contains isolated distractors in both colours, matching
the canonical scenes and preventing colour-only shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "18a70820b25b"
TASK_ID = "18a70820b25b"
VERSION = "3.0.0"
RULE_HASH = "f3fa0dad1044"

SUMMARY = (
    "On a zero-background grid, find the uniquely largest non-zero connected "
    "component.  For each column occupied by that source shape, look strictly "
    "below the bottommost source cell.  If the other non-zero colour occurs "
    "there, paint that column from immediately below the source through the "
    "bottom row in the marker colour.  Preserve the source and all distractor "
    "dots."
)

INVARIANTS = [
    "background is colour 0 and exactly two non-zero colours are present",
    "the source is the uniquely largest 4-connected non-zero component",
    "all non-source components are isolated one-cell distractors",
    "at least one but not every occupied source column is selected by a marker below it",
    "the beam colour is the non-source colour and beams start immediately below each selected source column",
]

EXAMPLES_NEEDED = 4

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware with a 20x20 canonical anchor", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "difficulty-aware with a 20x20 canonical anchor", "valid": "10..24"},
    "n_beams": {"type": "int", "default": "difficulty-aware 1..4", "valid": "1..4"},
    "n_scatter_total": {"type": "int", "default": "difficulty-aware 6..24", "valid": "4..24"},
    "n_source_distractors": {"type": "int", "default": "difficulty-aware 2..8", "valid": "0..8"},
    "shape_id": {"type": "int", "default": "rng over six five-column shapes", "valid": "0..5"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "warm|cool|broad|primary"},
    "position_bias": {"type": "str", "default": "rng", "valid": "left|center|right"},
}

# Every shape occupies exactly five columns.  This makes n_beams=1..4 exact
# while preserving a mandatory negative column that refutes "fill all columns".
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    # Canonical 8-cell tree/arrow profile.
    ((0, 2), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (2, 4)),
    # Cross.
    ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 2)),
    # Filled 3x5 rectangle.
    tuple((r, c) for r in range(3) for c in range(5)),
    # Hollow 3x5 frame.
    tuple((r, c) for r in range(3) for c in range(5) if r in (0, 2) or c in (0, 4)),
    # H.
    tuple((r, c) for r in range(3) for c in range(5) if c in (0, 4) or r == 1),
    # Broad arrow.
    ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2)),
)
_SHAPE_LOOKUP = {
    frozenset(shape): index for index, shape in enumerate(_SHAPES)
}

# Ordered (source, marker) pairs.  Pair sets are disjoint, so palette_kind is
# recoverable from the returned grid rather than being decorative metadata.
_PALETTE_PAIRS: dict[str, tuple[tuple[int, int], ...]] = {
    "warm": ((7, 2), (2, 7), (4, 2), (6, 7)),
    "cool": ((9, 8), (8, 9), (3, 8), (1, 9)),
    "broad": ((4, 3), (5, 2), (5, 8), (7, 3)),
    "primary": ((1, 6), (6, 1), (1, 2), (8, 4)),
}
_PAIR_TO_KIND = {
    pair: kind for kind, pairs in _PALETTE_PAIRS.items() for pair in pairs
}
_CANONICAL_ROLE_PAIRS = {(7, 2), (9, 8), (4, 3), (1, 6)}
_POSITION_BIASES = ("left", "center", "right")


def _axis_draw_int(ctx, overrides: dict[str, Any], name: str, default_lo: int, default_hi: int, valid_lo: int, valid_hi: int) -> int:
    """Draw an integer while keeping the full declared override boundary."""
    if name in overrides:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _axis_draw_choice(ctx, overrides: dict[str, Any], name: str, default_options, all_options):
    if name in overrides:
        return ctx.draw_choice(name, all_options)
    return ctx.draw_choice(name, default_options)


def _shape_position(width: int, shape_width: int, bias: str) -> int:
    anchors = {
        "left": 1,
        "center": max(1, (width - shape_width) // 2),
        "right": width - shape_width - 1,
    }
    return anchors[bias]


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _normalized_shape(cells: list[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _analyze(grid: Any) -> dict[str, Any]:
    analysis: dict[str, Any] = {"errors": []}
    errors: list[str] = analysis["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid must be a non-empty list of non-empty rows")
        return analysis
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return analysis
    height = len(grid)
    analysis.update(height=height, width=width)
    if not (10 <= height <= 24 and 10 <= width <= 24):
        errors.append(f"grid dimensions {height}x{width} outside 10..24")
    if any(not isinstance(v, int) or not (0 <= v <= 9) for row in grid for v in row):
        errors.append("grid contains a non-ARC colour value")
        return analysis

    colors = sorted({v for row in grid for v in row if v != 0})
    analysis["colors"] = colors
    if len(colors) != 2:
        errors.append(f"expected exactly two non-zero colours, found {colors}")
        return analysis

    comps = _components(grid)
    analysis["components"] = comps
    if len(comps) < 2:
        errors.append("expected a source component and marker/distractor components")
        return analysis
    ordered = sorted(comps, key=lambda item: len(item[1]), reverse=True)
    if len(ordered) > 1 and len(ordered[0][1]) == len(ordered[1][1]):
        errors.append("largest non-zero component is not unique")
        return analysis

    source_color, source_cells = ordered[0]
    marker_colors = [color for color in colors if color != source_color]
    if len(marker_colors) != 1:
        errors.append("could not identify the marker colour")
        return analysis
    marker_color = marker_colors[0]
    normalized = _normalized_shape(source_cells)
    shape_id = _SHAPE_LOOKUP.get(normalized)
    if shape_id is None:
        errors.append("largest component is not one of the six lawful source shapes")

    source_set = set(source_cells)
    source_rows = [r for r, _ in source_cells]
    source_cols = sorted({c for _, c in source_cells})
    bottoms = {c: max(r for r, cc in source_cells if cc == c) for c in source_cols}
    source_r0, source_r1 = min(source_rows), max(source_rows)
    source_c0, source_c1 = min(source_cols), max(source_cols)

    source_distractors: list[tuple[int, int]] = []
    marker_cells: list[tuple[int, int]] = []
    for color, cells in comps:
        if set(cells) == source_set:
            continue
        if len(cells) != 1:
            errors.append(f"non-source colour-{color} component has size {len(cells)}, expected an isolated dot")
        if color == source_color:
            source_distractors.extend(cells)
        elif color == marker_color:
            marker_cells.extend(cells)

    if not (0 <= len(source_distractors) <= 8):
        errors.append(f"source-colour distractor count {len(source_distractors)} outside 0..8")
    if not (4 <= len(marker_cells) <= 24):
        errors.append(f"marker-colour dot count {len(marker_cells)} outside 4..24")

    trigger_columns = sorted(
        c
        for c in source_cols
        if any(rr > bottoms[c] and cc == c for rr, cc in marker_cells)
    )
    if not (1 <= len(trigger_columns) <= 4):
        errors.append(f"selected source-column count {len(trigger_columns)} outside 1..4")
    if len(trigger_columns) >= len(source_cols):
        errors.append("every occupied source column is selected; no negative column remains")
    if source_r1 >= height - 2:
        errors.append("source leaves too little room for a visible downward projection")
    if trigger_columns and not any(
        cc in trigger_columns and bottoms[cc] < rr < height - 1
        for rr, cc in marker_cells
    ):
        errors.append("no selected column has a marker above the bottom row, so the transformation can be a no-op")

    pair = (source_color, marker_color)
    palette_kind = _PAIR_TO_KIND.get(pair)
    if palette_kind is None:
        # Canonical inputs are all included above; unknown role pairs are not
        # generated and indicate an override-observation ambiguity.
        errors.append(f"source/marker colour pair {pair} is outside the declared palette families")

    analysis.update(
        source_color=source_color,
        marker_color=marker_color,
        source_cells=source_cells,
        source_set=source_set,
        source_distractors=source_distractors,
        marker_cells=marker_cells,
        source_cols=source_cols,
        bottoms=bottoms,
        trigger_columns=trigger_columns,
        source_r0=source_r0,
        source_r1=source_r1,
        source_c0=source_c0,
        source_c1=source_c1,
        shape_id=shape_id,
        palette_kind=palette_kind,
    )
    return analysis


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    anchor = sample_index % 5 == 0
    anchor_slot = (sample_index // 5) % 3

    if anchor and "grid_h" not in overrides:
        h = ctx.draw_int("grid_h", 20, 20)
    else:
        h_ranges = {"easy": (10, 16), "hard": (18, 24)}
        h_lo, h_hi = h_ranges.get(difficulty, (14, 22))
        h = _axis_draw_int(ctx, overrides, "grid_h", h_lo, h_hi, 10, 24)
    if anchor and "grid_w" not in overrides:
        w = ctx.draw_int("grid_w", 20, 20)
    else:
        w_ranges = {"easy": (10, 16), "hard": (18, 24)}
        w_lo, w_hi = w_ranges.get(difficulty, (14, 22))
        w = _axis_draw_int(ctx, overrides, "grid_w", w_lo, w_hi, 10, 24)

    if anchor and "shape_id" not in overrides:
        shape_id = ctx.draw_int("shape_id", 0, 0)
    else:
        shape_id = _axis_draw_int(ctx, overrides, "shape_id", 0, 5, 0, 5)
    shape = _SHAPES[shape_id]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1

    if anchor and "n_beams" not in overrides:
        n_beams = ctx.draw_int("n_beams", (1, 2, 3)[anchor_slot], (1, 2, 3)[anchor_slot])
    else:
        beam_ranges = {"easy": (1, 2), "hard": (3, 4)}
        beam_lo, beam_hi = beam_ranges.get(difficulty, (2, 4))
        n_beams = _axis_draw_int(ctx, overrides, "n_beams", beam_lo, beam_hi, 1, 4)

    if anchor and "n_scatter_total" not in overrides:
        anchor_scatter = (8, 11, 20)[anchor_slot]
        n_scatter_total = ctx.draw_int("n_scatter_total", anchor_scatter, anchor_scatter)
    else:
        scatter_ranges = {"easy": (6, 12), "hard": (16, 24)}
        scatter_lo, scatter_hi = scatter_ranges.get(difficulty, (10, 20))
        scatter_lo = max(scatter_lo, n_beams + 2)
        n_scatter_total = _axis_draw_int(
            ctx, overrides, "n_scatter_total", scatter_lo, scatter_hi, 4, 24
        )
    if n_scatter_total < n_beams:
        exc = ValueError("n_scatter_total must be at least n_beams")
        exc.incompatible_axes = ("n_scatter_total", "n_beams")
        raise exc

    if anchor and "n_source_distractors" not in overrides:
        n_source_distractors = ctx.draw_int("n_source_distractors", 2, 2)
    else:
        source_ranges = {"easy": (2, 3), "hard": (4, 8)}
        source_lo, source_hi = source_ranges.get(difficulty, (2, 6))
        n_source_distractors = _axis_draw_int(
            ctx, overrides, "n_source_distractors", source_lo, source_hi, 0, 8
        )

    if anchor and "palette_kind" not in overrides:
        anchor_kind = ("warm", "cool", "broad")[anchor_slot]
        palette_kind = ctx.draw_choice("palette_kind", (anchor_kind,))
    else:
        palette_kind = _axis_draw_choice(
            ctx, overrides, "palette_kind", tuple(_PALETTE_PAIRS), tuple(_PALETTE_PAIRS)
        )
    palette_rng = ctx.draw_rng("palette_pair")
    pair_options = _PALETTE_PAIRS[palette_kind]
    if anchor:
        shape_color, marker_color = pair_options[0]
    else:
        shape_color, marker_color = palette_rng.choice(pair_options)

    if anchor and "position_bias" not in overrides:
        anchor_bias = _POSITION_BIASES[anchor_slot]
        position_bias = ctx.draw_choice("position_bias", (anchor_bias,))
    else:
        position_bias = _axis_draw_choice(
            ctx, overrides, "position_bias", _POSITION_BIASES, _POSITION_BIASES
        )

    g = full_grid(h, w, 0)
    max_r0 = min(max(2, h // 3), h - shape_h - 3)
    if max_r0 < 2:
        raise ValueError(f"grid_h={h} leaves no lawful source placement")
    r0 = rng.randint(2, max_r0)
    c0 = _shape_position(w, shape_w, position_bias)
    source_cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
    for r, c in source_cells:
        g[r][c] = shape_color

    source_cols = sorted({c for _, c in source_cells})
    bottoms = {c: max(r for r, cc in source_cells if cc == c) for c in source_cols}
    chosen_cols = sorted(rng.sample(source_cols, n_beams))
    unchosen_cols = [c for c in source_cols if c not in chosen_cols]

    # Pick one checkerboard parity that can host every exact marker request.
    feasible_parities: list[int] = []
    for parity in (0, 1):
        enough_triggers = all(
            any(
                (r + c) % 2 == parity and (r, c) not in source_cells
                for r in range(bottoms[c] + 2, h)
            )
            for c in chosen_cols
        )
        free_count = sum(
            1
            for r in range(h)
            for c in range(w)
            if (r + c) % 2 == parity and (r, c) not in source_cells
        )
        if enough_triggers and free_count >= n_scatter_total:
            feasible_parities.append(parity)
    if not feasible_parities:
        exc = ValueError("grid and marker-count overrides leave no isolated-dot layout")
        exc.incompatible_axes = ("grid_h", "grid_w", "n_scatter_total", "n_beams")
        raise exc
    parity = rng.choice(feasible_parities)

    marker_set: set[tuple[int, int]] = set()
    for index, c in enumerate(chosen_cols):
        candidates = [
            r
            for r in range(bottoms[c] + 2, h)
            if (r + c) % 2 == parity and (r, c) not in source_cells
        ]
        # Keep at least one marker above the last row so the beam visibly
        # continues beyond its cue; prefer that for every trigger when possible.
        nonfloor = [r for r in candidates if r < h - 1]
        if nonfloor:
            candidates = nonfloor
        rr = rng.choice(candidates)
        marker_set.add((rr, c))

    # Ordinary draws reserve two canonical-style distractors: one above the
    # source in an unselected source column (refutes "any marker in column")
    # and one outside the source span (refutes "all dots are beam markers").
    extras_needed = n_scatter_total - len(marker_set)
    if extras_needed > 0 and unchosen_cols:
        above = [
            (r, c)
            for c in unchosen_cols
            for r in range(0, r0)
            if (r + c) % 2 == parity and (r, c) not in marker_set
        ]
        if above:
            marker_set.add(rng.choice(above))
            extras_needed -= 1
    if extras_needed > 0:
        outside = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if c not in source_cols
            and (r + c) % 2 == parity
            and (r, c) not in source_cells
            and (r, c) not in marker_set
        ]
        if outside:
            marker_set.add(rng.choice(outside))
            extras_needed -= 1

    fill_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r + c) % 2 == parity
        and (r, c) not in source_cells
        and (r, c) not in marker_set
        # Never accidentally create a new selected source column.
        and not (c in source_cols and r > bottoms[c])
    ]
    rng.shuffle(fill_candidates)
    for cell in fill_candidates:
        if len(marker_set) >= n_scatter_total:
            break
        marker_set.add(cell)
    if len(marker_set) != n_scatter_total:
        exc = ValueError("could not realize exact n_scatter_total without changing n_beams")
        exc.incompatible_axes = ("grid_h", "grid_w", "n_scatter_total", "n_beams")
        raise exc
    for r, c in marker_set:
        g[r][c] = marker_color

    # Add isolated source-colour distractors after the marker layout.  They are
    # kept 4-disconnected from the source and one another, but may sit beside a
    # different-colour marker just as ordinary ARC clutter can.
    source_distractors: list[tuple[int, int]] = []
    distractor_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if g[r][c] == 0
        and all(abs(r - sr) + abs(c - sc) > 1 for sr, sc in source_cells)
    ]
    rng.shuffle(distractor_candidates)
    for r, c in distractor_candidates:
        if len(source_distractors) >= n_source_distractors:
            break
        if all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in source_distractors):
            source_distractors.append((r, c))
    if len(source_distractors) != n_source_distractors:
        exc = ValueError("could not place exact isolated source-colour distractors")
        exc.incompatible_axes = ("grid_h", "grid_w", "n_source_distractors", "n_scatter_total")
        raise exc
    for r, c in source_distractors:
        g[r][c] = shape_color

    problems = self_check(g, difficulty=difficulty, meta={"overrides": overrides})
    if problems:
        raise ValueError(f"internal generator invariant failure: {problems}")
    return g


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return {name: value for name, value in nested.items() if name in AXES}
    return {name: value for name, value in meta.items() if name in AXES}


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    width = analysis["width"]
    shape_width = analysis["source_c1"] - analysis["source_c0"] + 1
    anchors = {
        bias: _shape_position(width, shape_width, bias) for bias in _POSITION_BIASES
    }
    position_bias = min(
        _POSITION_BIASES,
        key=lambda bias: (abs(analysis["source_c0"] - anchors[bias]), _POSITION_BIASES.index(bias)),
    )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_beams": len(analysis["trigger_columns"]),
        "n_scatter_total": len(analysis["marker_cells"]),
        "n_source_distractors": len(analysis["source_distractors"]),
        "shape_id": analysis["shape_id"],
        "palette_kind": analysis["palette_kind"],
        "position_bias": position_bias,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding inputs and verify requested axes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return sorted(set(errors))
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        realized = observed.get(name)
        if realized != requested:
            errors.append(f"override {name}={requested!r} realized as {realized!r}")
    return sorted(set(errors))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror for tests; the Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"input outside task grammar: {analysis['errors']}")
    output = [row[:] for row in grid]
    marker_color = analysis["marker_color"]
    marker_set = set(analysis["marker_cells"])
    for c in analysis["source_cols"]:
        bottom = analysis["bottoms"][c]
        if any((r, c) in marker_set for r in range(bottom + 1, analysis["height"])):
            for r in range(bottom + 1, analysis["height"]):
                output[r][c] = marker_color
    return output


def strict_canonical_like(grid) -> list[str]:
    """Linked empirical manifold shared by every official canonical input."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) != (20, 20):
        reasons.append("canonical inputs are exactly 20x20")
    if analysis["shape_id"] != 0:
        reasons.append("canonical source uses the 8-cell tree/arrow shape")
    if len(analysis["source_distractors"]) != 2:
        reasons.append("canonical inputs contain exactly two isolated source-colour distractors")
    if len(analysis["marker_cells"]) not in {8, 11, 20}:
        reasons.append("canonical marker counts are 8, 11, or 20")
    if not (1 <= len(analysis["trigger_columns"]) <= 3):
        reasons.append("canonical inputs select one to three source columns")
    if (analysis["source_color"], analysis["marker_color"]) not in _CANONICAL_ROLE_PAIRS:
        reasons.append("source/marker role colours are outside the four canonical pairs")
    return reasons


def _competitor_copy(grid):
    return [row[:] for row in grid]


def _competitor_all_source_columns(grid):
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    for c in analysis["source_cols"]:
        for r in range(analysis["bottoms"][c] + 1, analysis["height"]):
            out[r][c] = analysis["marker_color"]
    return out


def _competitor_start_at_marker(grid):
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    for c in analysis["trigger_columns"]:
        first = min(r for r, cc in analysis["marker_cells"] if cc == c and r > analysis["bottoms"][c])
        for r in range(first, analysis["height"]):
            out[r][c] = analysis["marker_color"]
    return out


def _competitor_stop_at_marker(grid):
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    for c in analysis["trigger_columns"]:
        first = min(r for r, cc in analysis["marker_cells"] if cc == c and r > analysis["bottoms"][c])
        for r in range(analysis["bottoms"][c] + 1, first + 1):
            out[r][c] = analysis["marker_color"]
    return out


def _competitor_use_source_colour(grid):
    correct = rule_mirror(grid)
    analysis = _analyze(grid)
    source_cells = set(analysis["source_cells"])
    for r in range(analysis["height"]):
        for c in analysis["trigger_columns"]:
            if (r, c) not in source_cells and correct[r][c] == analysis["marker_color"]:
                correct[r][c] = analysis["source_color"]
    return correct


def _competitor_any_marker_in_source_column(grid):
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    marker_cols = {c for _, c in analysis["marker_cells"]}
    for c in analysis["source_cols"]:
        if c in marker_cols:
            for r in range(analysis["bottoms"][c] + 1, analysis["height"]):
                out[r][c] = analysis["marker_color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy_input": _competitor_copy,
    "fill_all_source_columns": _competitor_all_source_columns,
    "start_at_marker": _competitor_start_at_marker,
    "stop_at_marker": _competitor_stop_at_marker,
    "use_source_colour": _competitor_use_source_colour,
    "any_marker_in_source_column": _competitor_any_marker_in_source_column,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject episodes where a named rival fits demos but changes the query."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate([*demos, query]):
        label = f"demo {index}" if index < len(demos) else "query"
        input_grid = pair.get("input")
        output_grid = pair.get("output")
        grammar_errors = self_check(input_grid)
        if grammar_errors:
            reasons.append(f"{label} input violates the task grammar: {grammar_errors}")
            continue
        expected = rule_mirror(input_grid)
        if output_grid is not None and output_grid != expected:
            reasons.append(f"{label} output does not match the downward column-selection rule")
    if reasons:
        return reasons
    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule '{name}' fits every demo but changes the query")
    return reasons


def _witness_canonical_profile(grid) -> bool:
    return not strict_canonical_like(grid)


def _witness_selective_columns(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and 0 < len(analysis["trigger_columns"]) < len(analysis["source_cols"])


def _witness_source_colour_distractors(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["source_distractors"])


def _witness_above_marker_rebuts_anywhere(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    untriggered = set(analysis["source_cols"]) - set(analysis["trigger_columns"])
    has_above = any(c in untriggered and r < analysis["source_r0"] for r, c in analysis["marker_cells"])
    return has_above and _competitor_any_marker_in_source_column(grid) != rule_mirror(grid)


def _witness_gap_rebuts_start_at_marker(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    has_gap = any(
        c in analysis["trigger_columns"] and r > analysis["bottoms"][c] + 1
        for r, c in analysis["marker_cells"]
    )
    return has_gap and _competitor_start_at_marker(grid) != rule_mirror(grid)


def _witness_outside_span_distractor(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(c not in analysis["source_cols"] for _, c in analysis["marker_cells"])


SEMANTIC_WITNESSES = {
    "exact_canonical_profile": _witness_canonical_profile,
    "some_but_not_all_source_columns_selected": _witness_selective_columns,
    "isolated_source_colour_distractors": _witness_source_colour_distractors,
    "above_source_marker_rebuts_anywhere_in_column": _witness_above_marker_rebuts_anywhere,
    "blank_gap_rebuts_start_at_marker": _witness_gap_rebuts_start_at_marker,
    "marker_colour_distractor_outside_source_span": _witness_outside_span_distractor,
}

# A claim means that when the witness fires, at least one named rival is
# expected to disagree with the authoritative Racket output.  The semantic
# gate verifies these claims by executing both programs on generated grids.
WITNESS_RIVALS = {
    "some_but_not_all_source_columns_selected": ["fill_all_source_columns"],
    "above_source_marker_rebuts_anywhere_in_column": ["any_marker_in_source_column"],
    "blank_gap_rebuts_start_at_marker": ["start_at_marker", "stop_at_marker"],
}
