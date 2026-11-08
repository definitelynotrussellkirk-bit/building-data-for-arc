"""Semantic generator for ARC task 5d1263287a4f.

Canonical rule: split the input into three equal horizontal panels and return
the leftmost panel.  Canonical layouts are A|A|A and A|mirror-horizontal(A)|A.

The generator varies the source tile (shape, palette, and texture) and restricts
middle/right panels to exact copies or horizontal mirrors of that tile.  This
keeps decoys structurally tied to the canonical motif instead of emitting three
unrelated random panels, while controlled right-mirror profiles refute the
shortcut "return any repeated outer panel" and teach the leftmost position.

Counter-hypotheses exercised by the distribution:
  * fixed-size crop — tile height/width vary across the canonical 2..5 range,
    with the full 2..10 override envelope remaining valid;
  * fixed-color/modal-color echo — palettes and modal colors vary, and the
    output preserves every cell rather than returning a count or one color;
  * compression/downsampling — the output is an exact copy of one full tile;
  * content-selected/rightmost panel — right-mirror profiles make the first
    panel uniquely correct while canonical A|A|A and A|mirror(A)|A remain common.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5d1263287a4f"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
# 2.1.0 makes the shortcut-breaking layouts a four-slot lesson schedule instead
# of a probability.  Every three consecutive demonstrations now refute the
# canonical-fitting ``return the rightmost third`` shortcut, while explicit
# panel_layout overrides and the authoritative crop-left rule stay unchanged.
RULE_HASH = "92f6a0f9f7b3"
SUMMARY = "Split into three equal horizontal panels and return the leftmost; decoys are copies or horizontal mirrors."

INVARIANTS = [
    "input width is exactly three times the panel width",
    "middle and right panels are each the left panel or its horizontal mirror",
    "the left panel is horizontally asymmetric so panel layouts are observable",
    "the output is an exact h×(w/3) copy of the leftmost panel",
    "the source panel uses exactly 3 or 4 ARC colors",
]

TILE_PATTERNS = (
    "row_runs",
    "column_runs",
    "diagonal_runs",
    "blobs",
    "balanced_scatter",
)
PANEL_LAYOUTS = (
    "all_same",
    "middle_mirror",
    "right_mirror",
    "both_mirror",
)
# Four examples are assembled from consecutive sample indices: three demos and
# one query.  Every cyclic three-slot demo window contains either right_mirror
# or both_mirror, where the rightmost panel differs from the official output.
SCHEDULE_PROFILES = (
    "right_mirror",
    "all_same",
    "both_mirror",
    "middle_mirror",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng: easy 2..3, medium 3..4, hard 4..5",
        "valid": "2..10",
    },
    "grid_w_third": {
        "type": "int",
        "default": "band rng: easy 2..3, medium 3..4, hard 4..5",
        "valid": "2..10",
    },
    "palette_size": {
        "type": "int",
        "default": "rng 3..4",
        "valid": "3..4",
    },
    "tile_pattern": {
        "type": "str",
        "default": "rng across five lawful tile textures",
        "valid": "|".join(TILE_PATTERNS),
    },
    "panel_layout": {
        "type": "str",
        "default": "four-slot lesson schedule over A/copy-or-mirror layouts",
        "valid": "|".join(PANEL_LAYOUTS),
    },
}

_VALID_H = (2, 10)
_VALID_THIRD = (2, 10)
_BAND_DIMS = {
    "easy": (2, 3),
    "medium": (3, 4),
    "hard": (4, 5),
}


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_DIMS:
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the fixed lesson role; seed/band only affect nuisance variation."""
    del seed
    _band(difficulty)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative plain integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _banded_int(ctx, overrides, label, band_range, valid_range) -> int:
    """Use band-shaped defaults but validate explicit values globally.

    An exact AXES override is a contract, not a request to be clipped to the
    current difficulty band.  This helper keeps every declared boundary usable
    under easy, medium, and hard.
    """
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, *valid_range)
    return ctx.draw_int(label, *band_range)


def _snake_rows(h: int, w: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(h)
        for c in (range(w) if r % 2 == 0 else range(w - 1, -1, -1))
    ]


def _snake_cols(h: int, w: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for c in range(w)
        for r in (range(h) if c % 2 == 0 else range(h - 1, -1, -1))
    ]


def _diagonal_order(h: int, w: int) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(h) for c in range(w)]
    return sorted(
        cells,
        key=lambda rc: (
            rc[0] + rc[1],
            rc[0] if (rc[0] + rc[1]) % 2 == 0 else -rc[0],
        ),
    )


def _balanced_lengths(total: int, parts: int, rng) -> list[int]:
    """Positive near-equal segment lengths with randomized color ownership."""
    base, extra = divmod(total, parts)
    lengths = [base + (i < extra) for i in range(parts)]
    rng.shuffle(lengths)
    return lengths


def _seam_allowed(
    h: int,
    w: int,
    rng,
    *,
    force_right_background: bool = False,
) -> set[tuple[int, int]]:
    """Cells eligible for foreground while blocking every repetition seam.

    Copy/copy boundaries only need one blocked endpoint per row.  A source tile
    followed by its mirror compares the source's right edge with itself, so the
    shortcut-breaking right_mirror/both_mirror layouts keep that whole edge as
    background.  This preserves the canonical three-component fragmentation
    envelope without changing the visible crop rule.
    """
    if force_right_background:
        blocked_left = [False] * h
    else:
        blocked_left = [True]
        if w == 2:
            blocked_left.extend([True] * (h - 1))
        else:
            blocked_left.extend(bool(rng.getrandbits(1)) for _ in range(h - 1))
    return {
        (r, c)
        for r in range(h)
        for c in range(w)
        if not ((blocked_left[r] and c == 0)
                or (not blocked_left[r] and c == w - 1))
    }


def _neighbors(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _grow_support(
    allowed: set[tuple[int, int]],
    target: int,
    pattern: str,
    rng,
) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    """Grow a connected foreground support and preserve its discovery order."""
    if pattern == "row_runs":
        start = min(allowed, key=lambda rc: (rc[0], rc[1]))
    elif pattern == "column_runs":
        start = min(allowed, key=lambda rc: (rc[1], rc[0]))
    elif pattern == "diagonal_runs":
        start = min(allowed, key=lambda rc: (rc[0] + rc[1], rc[0]))
    else:
        start = rng.choice(sorted(allowed))

    support = {start}
    discovery = [start]
    random_rank = {cell: rng.random() for cell in allowed}
    while len(support) < target:
        frontier = {
            neighbor
            for cell in support
            for neighbor in _neighbors(cell)
            if neighbor in allowed and neighbor not in support
        }
        if not frontier:
            raise RuntimeError("connected support growth exhausted unexpectedly")
        if pattern == "row_runs":
            chosen = min(frontier, key=lambda rc: (rc[0], rc[1]))
        elif pattern == "column_runs":
            chosen = min(frontier, key=lambda rc: (rc[1], rc[0]))
        elif pattern == "diagonal_runs":
            chosen = min(
                frontier,
                key=lambda rc: (rc[0] + rc[1], abs(rc[0] - rc[1]), rc[0]),
            )
        elif pattern == "blobs":
            chosen = rng.choice(sorted(frontier))
        else:  # balanced_scatter: irregular support, separately shuffled colors
            chosen = min(frontier, key=random_rank.__getitem__)
        support.add(chosen)
        discovery.append(chosen)
    return discovery, support


def _ordered_support(
    support: set[tuple[int, int]],
    discovery: list[tuple[int, int]],
    h: int,
    w: int,
    pattern: str,
    rng,
) -> list[tuple[int, int]]:
    if pattern == "row_runs":
        return [cell for cell in _snake_rows(h, w) if cell in support]
    if pattern == "column_runs":
        return [cell for cell in _snake_cols(h, w) if cell in support]
    if pattern == "diagonal_runs":
        return [cell for cell in _diagonal_order(h, w) if cell in support]
    if pattern == "blobs":
        return discovery
    cells = sorted(support)
    rng.shuffle(cells)
    return cells


def _paint_support(
    h: int,
    w: int,
    palette: tuple[int, ...],
    pattern: str,
    rng,
    *,
    force_right_background: bool = False,
) -> list[list[int]]:
    """Paint a modal background plus one connected multi-color motif.

    In the repeated input, the seam blockers make that motif appear as three
    foreground components.  This matches the canonical fragmentation envelope
    while retaining exact cell-level texture diversity inside each tile.
    """
    background = palette[0]
    foreground_colors = list(palette[1:])
    rng.shuffle(foreground_colors)
    tile = [[background for _ in range(w)] for _ in range(h)]
    allowed = _seam_allowed(
        h,
        w,
        rng,
        force_right_background=force_right_background,
    )
    total = h * w
    lower = max(len(foreground_colors), (45 * total + 99) // 100)
    upper = max(lower, (60 * total) // 100)
    target = min(len(allowed), rng.randint(lower, upper))

    # Only the 2x2/four-color boundary needs one extra eligible cell.  Keep
    # (0,0) background so ties still identify the intended modal color.
    if target < len(foreground_colors):
        extras = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if (r, c) not in allowed and (r, c) != (0, 0)
        ]
        for cell in extras[:len(foreground_colors) - target]:
            allowed.add(cell)
        target = len(foreground_colors)

    discovery, support = _grow_support(allowed, target, pattern, rng)
    order = _ordered_support(support, discovery, h, w, pattern, rng)
    lengths = _balanced_lengths(len(order), len(foreground_colors), rng)
    cursor = 0
    for color, length in zip(foreground_colors, lengths):
        for r, c in order[cursor:cursor + length]:
            tile[r][c] = color
        cursor += length
    return tile


def _make_tile(
    h: int,
    w: int,
    palette: tuple[int, ...],
    pattern: str,
    rng,
    *,
    force_right_background: bool = False,
) -> list[list[int]]:
    if pattern not in TILE_PATTERNS:
        raise ValueError(f"unknown tile_pattern: {pattern!r}")
    return _paint_support(
        h,
        w,
        palette,
        pattern,
        rng,
        force_right_background=force_right_background,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    allowed = set(AXES)
    unknown = set(overrides) - allowed
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _banded_int(ctx, overrides, "grid_h", _BAND_DIMS[band], _VALID_H)
    third = _banded_int(
        ctx, overrides, "grid_w_third", _BAND_DIMS[band], _VALID_THIRD
    )
    pattern = ctx.draw_choice("tile_pattern", TILE_PATTERNS)
    if "panel_layout" in overrides and overrides["panel_layout"] is not None:
        layout = ctx.draw_choice("panel_layout", PANEL_LAYOUTS)
    else:
        scheduled_layout = schedule_profile(seed, sample_index, band)
        # Keep the exact scheduled value in the standard keyed-draw provenance
        # used by override/audit tooling; a singleton choice is deterministic.
        layout = ctx.draw_choice("panel_layout", (scheduled_layout,))
    if "palette_size" in overrides and overrides["palette_size"] is not None:
        palette_size = ctx.draw_int("palette_size", 3, 4)
    else:
        foreground_capacity = h * (third - 1)
        max_palette_size = 4 if foreground_capacity >= 3 else 3
        palette_size = ctx.draw_int("palette_size", 3, max_palette_size)
    palette = ctx.draw_distinct_colors("palette", n=palette_size)
    for attempt in range(64):
        tile = _make_tile(
            h,
            third,
            palette,
            pattern,
            ctx.draw_rng(f"tile_cells_{attempt}"),
            force_right_background=layout in {"right_mirror", "both_mirror"},
        )
        mirror = [list(reversed(row)) for row in tile]
        if tile != mirror:
            break
    else:
        raise RuntimeError("could not mint a horizontally asymmetric source tile")

    if layout == "all_same":
        panels = (tile, tile, tile)
    elif layout == "middle_mirror":
        panels = (tile, mirror, tile)
    elif layout == "right_mirror":
        panels = (tile, tile, mirror)
    elif layout == "both_mirror":
        panels = (tile, mirror, mirror)
    else:  # protected by draw_choice; keeps direct helper misuse fail-loud
        raise ValueError(f"unknown panel_layout: {layout!r}")

    # Every output row is fresh; panels and source tiles are never returned by
    # reference, so callers cannot mutate later deterministic replays.
    return [
        list(panels[0][r]) + list(panels[1][r]) + list(panels[2][r])
        for r in range(h)
    ]


def _analysis(grid) -> dict:
    errors: list[str] = []
    result = {
        "errors": errors,
        "tile": None,
        "palette_size": None,
        "panel_layout": None,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be nonempty")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be nonempty")
        return result
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    if not _VALID_H[0] <= h <= _VALID_H[1]:
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if w % 3 != 0:
        errors.append(f"width {w} must be divisible by 3")
        return result
    third = w // 3
    if not _VALID_THIRD[0] <= third <= _VALID_THIRD[1]:
        errors.append(
            f"third width {third} outside {_VALID_THIRD[0]}..{_VALID_THIRD[1]}"
        )
    left = [list(row[:third]) for row in grid]
    middle = [list(row[third:2 * third]) for row in grid]
    right = [list(row[2 * third:]) for row in grid]
    mirror = [list(reversed(row)) for row in left]
    if left == mirror:
        errors.append("left panel must be horizontally asymmetric")
    layout = None
    for name, expected_middle, expected_right in (
        ("all_same", left, left),
        ("middle_mirror", mirror, left),
        ("right_mirror", left, mirror),
        ("both_mirror", mirror, mirror),
    ):
        if middle == expected_middle and right == expected_right:
            layout = name
            break
    if layout is None:
        errors.append(
            "middle/right panels must each be the left panel or its horizontal mirror"
        )
    colors = {value for row in left for value in row}
    if not 3 <= len(colors) <= 4:
        errors.append(
            f"source panel must use exactly 3 or 4 colors, got {len(colors)}"
        )
    result.update(
        {
            "tile": left,
            "palette_size": len(colors),
            "panel_layout": layout,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject off-task panels, degenerate tiles, malformed grids, and bad colors."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover the exact directly observable AXES values from a returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w_third": len(grid[0]) // 3,
        "palette_size": int(analysis["palette_size"]),
        "panel_layout": str(analysis["panel_layout"]),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror for tests only; the canonical Racket rule is authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["tile"]]

def _rightmost_panel(grid) -> list[list[int]]:
    """Canonical-fitting shortcut: crop the rightmost third instead of the left."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    third = len(grid[0]) // 3
    return [list(row[2 * third:]) for row in grid]


def _rightmost_counterexample(grid) -> bool:
    return _rightmost_panel(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "rightmost_panel": _rightmost_panel,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    "rightmost_panel_counterexample": _rightmost_counterexample,
}
WITNESS_RIVALS = {
    "rightmost_panel_counterexample": ["rightmost_panel"],
}


def _pair_errors(pair, label: str) -> list[str]:
    if not isinstance(pair, dict):
        return [f"{label}: pair must be a mapping with input and output"]
    missing = [key for key in ("input", "output") if key not in pair]
    if missing:
        return [f"{label}: pair is missing {', '.join(missing)}"]
    try:
        expected = rule_mirror(pair["input"])
    except Exception as exc:
        return [f"{label}: invalid input: {type(exc).__name__}: {exc}"]
    if pair["output"] != expected:
        return [f"{label}: output does not match the leftmost-panel rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared canonical shortcut survives the demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of input/output pairs"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    expected_query = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            if survives and rival(query["input"]) != expected_query:
                reasons.append(
                    f"named rival {name!r} fits every demo but changes the query"
                )
        except Exception as exc:
            reasons.append(f"named rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons

