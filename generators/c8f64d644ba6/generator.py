"""Generator for ARC task 6a1e5592 / content hash c8f64d644ba6.

Rule: the upper red band contains blank sockets.  Each disconnected gray
source object below is cleared, normalized, and moved into the first blank
socket that supports that exact shape; moved cells are recolored blue.
Gray objects are processed largest-first, with reading order breaking ties.

The canonical task has three or four distinct gray polyominoes, including
same-size/different-shape cases, a full red top row, sockets beginning on row
1 or 2, and bottom-anchored source objects whose left-to-right order differs
from the sockets.  Sample indices 0, 1, and 2 modulo 10 select the three
complete linked canonical morphology profiles.  Other indices generalize the
same grammar across larger canvases and transformed polyominoes.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8f64d644ba6"
TASK_ID = "c8f64d644ba6"
VERSION = "2.0.0"
RULE_HASH = "9b6643f8c252"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A full red top row and a shallow red band contain several blank, "
    "shape-specific sockets. Three or four disconnected gray polyominoes "
    "are bottom-anchored below. The rule clears the gray sources, processes "
    "them largest-first, and paints each normalized shape blue in its first "
    "supported blank placement."
)

INVARIANTS = [
    "palette is exactly {0, 2, 5}",
    "row 0 is entirely red and red cells occur only in rows 0..2",
    "there are exactly 3 or 4 distinct gray source shapes",
    "every gray source touches the bottom row and is separated from the band",
    "the canonical rule places every gray cell into a blue socket on row 1 or 2",
    "the moved blue components have the same normalized shapes as the sources",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 10..11 easy, 10..12 medium, 12..14 hard; "
        "30% linked canonical-profile schedule pins 10",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 15..17 easy, 15..19 medium, 18..22 hard; "
        "30% linked canonical-profile schedule pins 15",
        "valid": "15..22",
    },
    "n_shapes": {
        "type": "int",
        "default": "rng 3..4; linked canonical profiles pin 3 or 4",
        "valid": "3..4",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_H_LO, _H_HI = 10, 14
_W_LO, _W_HI = 15, 22


def _shape(*rows: str) -> tuple[tuple[int, int], ...]:
    cells = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "#"
    ]
    return _normalize(cells)


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(shape) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


# Exact canonical source morphologies, paired with the socket top-left used by
# the official three distinct inputs.  Source positions are still randomized.
_A10 = _shape(".##.", ".##.", "####", ".##.")
_A5 = _shape(".##", "###")
_A4 = _shape(".#.", "###")
_A3 = _shape("#", "#", "#")
_B6_STAIR = _shape("#..", "##.", "###")
_B6_RECT = _shape("###", "###")
_B4 = _shape("#", "#", "#", "#")
_C11 = _shape("#.#", "###", "###", "###")
_C8 = _shape("#...", "###.", "####")
_C6 = _shape("#.", "##", "#.", "##")

_CANONICAL_LAYOUTS = (
    (
        (_A10, 1, 10),
        (_A5, 2, 0),
        (_A4, 1, 7),
        (_A3, 1, 4),
    ),
    (
        (_B6_STAIR, 1, 1),
        (_B6_RECT, 2, 6),
        (_B4, 1, 14),
    ),
    (
        (_C11, 1, 6),
        (_C8, 1, 11),
        (_C6, 1, 1),
    ),
)


def _profile_signature_from_layout(layout):
    return (
        10,
        15,
        tuple(sorted((shape, row) for shape, row, _ in layout)),
    )


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature_from_layout(layout) for layout in _CANONICAL_LAYOUTS
)

# A broad source bank.  D4 transforms are added below, then deduplicated.
_BASE_SHAPES = (
    _A10,
    _A5,
    _A4,
    _A3,
    _B6_STAIR,
    _B6_RECT,
    _B4,
    _C11,
    _C8,
    _C6,
    _shape(".#.", "###", ".#."),
    _shape("##.", ".##", "..#"),
    _shape("#..", "###", "..#"),
    _shape("##", "#.", "##"),
    _shape("###", ".#.", ".#."),
    _shape("##..", ".###"),
)


def _rotate(shape):
    return _normalize((c, -r) for r, c in shape)


def _reflect(shape):
    return _normalize((r, -c) for r, c in shape)


def _all_variants(shapes):
    out = set()
    for base in shapes:
        cur = base
        for _ in range(4):
            out.add(cur)
            out.add(_reflect(cur))
            cur = _rotate(cur)
    return tuple(sorted(out, key=lambda s: (len(s), _dims(s), s)))


_GENERAL_SHAPES = tuple(
    shape
    for shape in _all_variants(_BASE_SHAPES)
    if 3 <= len(shape) <= 11 and _dims(shape)[0] <= 4 and _dims(shape)[1] <= 4
)


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIRS4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _source_objects(grid):
    source_components = _components(grid, 5)
    return sorted(
        source_components,
        key=lambda cells: (
            -len(cells),
            _bbox(cells)[0],
            _bbox(cells)[1],
        ),
    )


def _clear_sources(grid):
    out = [row[:] for row in grid]
    for cells in _components(grid, 5):
        for r, c in cells:
            out[r][c] = 0
    return out


def _valid_placements(grid, acc, shape):
    h, w = len(grid), len(grid[0])
    top_cells = [(r, c) for r, c in shape if r == 0]
    placements = []
    for r0 in range(1, h):
        for c0 in range(w):
            if not all(
                0 <= r0 + dr < h
                and 0 <= c0 + dc < w
                and grid[r0 + dr][c0 + dc] == 0
                and acc[r0 + dr][c0 + dc] == 0
                for dr, dc in shape
            ):
                continue
            if not all(
                grid[r0 - 1][c0 + dc] == 2
                for _, dc in top_cells
            ):
                continue
            placements.append((r0, c0))
    return placements


def _placement_trace(grid):
    acc = _clear_sources(grid)
    trace = []
    for cells in _source_objects(grid):
        shape = _normalize(cells)
        placements = _valid_placements(grid, acc, shape)
        pos = placements[0] if placements else None
        trace.append(
            {
                "shape": shape,
                "source_bbox": _bbox(cells),
                "placement": pos,
                "candidate_count": len(placements),
            }
        )
        if pos is not None:
            r0, c0 = pos
            for dr, dc in shape:
                acc[r0 + dr][c0 + dc] = 1
    return trace, acc


def _python_apply(grid):
    return _placement_trace(grid)[1]


def canonical_profile_signature(grid):
    """Complete linked official morphology signature, or ``None``."""
    try:
        h, w = len(grid), len(grid[0])
        trace, _ = _placement_trace(grid)
    except Exception:
        return None
    if any(item["placement"] is None for item in trace):
        return None
    return (
        h,
        w,
        tuple(
            sorted(
                (item["shape"], item["placement"][0])
                for item in trace
            )
        ),
    )


def _source_destination_orders(grid):
    trace, _ = _placement_trace(grid)
    physical = sorted(
        trace,
        key=lambda item: (
            item["source_bbox"][1],
            item["source_bbox"][0],
        ),
    )
    placed = sorted(
        (item for item in trace if item["placement"] is not None),
        key=lambda item: (item["placement"][1], item["placement"][0]),
    )
    return (
        [item["shape"] for item in physical],
        [item["shape"] for item in placed],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons, not merely malformed palettes.

    The check independently simulates the canonical largest-first placement
    rule and compares normalized source/output morphology, so removing a
    support, changing a socket cell, merging sources, moving a source off the
    bottom, or creating an unmatched source is rejected.
    """
    del difficulty, meta
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errors = []
    values = {value for row in grid for value in row}
    if values != {0, 2, 5}:
        errors.append(f"palette must be exactly {{0,2,5}}, found {sorted(values)}")
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(
            f"dims {h}x{w} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}"
        )
    if any(value != 2 for value in grid[0]):
        errors.append("row 0 must be entirely red(2)")
    if any(grid[r][c] == 2 for r in range(3, h) for c in range(w)):
        errors.append("red(2) cells may occur only in rows 0..2")

    source_components = _components(grid, 5)
    if len(source_components) not in (3, 4):
        errors.append(
            f"expected exactly 3 or 4 gray source objects, got {len(source_components)}"
        )
    source_shapes = [_normalize(cells) for cells in source_components]
    if len(set(source_shapes)) != len(source_shapes):
        errors.append("gray source shapes must have distinct normalized forms")
    for index, cells in enumerate(source_components):
        r1, _, r2, _ = _bbox(cells)
        if r2 != h - 1:
            errors.append(f"gray source {index} does not touch the bottom row")
        if r1 < 5:
            errors.append(f"gray source {index} intrudes into the blank separator")
        if not (3 <= len(cells) <= 11):
            errors.append(
                f"gray source {index} size {len(cells)} outside canonical envelope 3..11"
            )

    if errors:
        return errors

    trace, output = _placement_trace(grid)
    for index, item in enumerate(trace):
        if item["placement"] is None:
            errors.append(f"gray source {index} has no supported blank placement")
        elif item["placement"][0] not in (1, 2):
            errors.append(
                f"gray source {index} first placement begins on row "
                f"{item['placement'][0]}, expected row 1 or 2"
            )

    blue_components = _components(output, 1)
    blue_shapes = sorted(_normalize(cells) for cells in blue_components)
    if len(blue_components) != len(source_components):
        errors.append(
            f"rule paints {len(blue_components)} blue objects for "
            f"{len(source_components)} gray sources"
        )
    if blue_shapes != sorted(source_shapes):
        errors.append("moved blue shapes do not match normalized gray sources")
    if sum(value == 1 for row in output for value in row) != sum(
        value == 5 for row in grid for value in row
    ):
        errors.append("rule does not move every gray cell exactly once")
    if any(value == 5 for row in output for value in row):
        errors.append("rule leaves gray source cells behind")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return [f"self_check: {reason}" for reason in reasons]
    if (len(grid), len(grid[0])) != (10, 15):
        reasons.append("canonical canvas is exactly 10x15")
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        reasons.append("linked source-shape/socket-row profile is not canonical")
    source_order, destination_order = _source_destination_orders(grid)
    if source_order == destination_order:
        reasons.append("canonical source order differs from destination order")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_shapes": len(_components(grid, 5)) if grid and grid[0] else 0,
    }


def _witness_four_shapes(grid):
    return len(_components(grid, 5)) == 4


def _witness_same_size_distinct(grid):
    shapes = [_normalize(cells) for cells in _components(grid, 5)]
    by_size = defaultdict(set)
    for shape in shapes:
        by_size[len(shape)].add(shape)
    return any(len(group) >= 2 for group in by_size.values())


def _witness_mixed_socket_rows(grid):
    trace, _ = _placement_trace(grid)
    rows = {item["placement"][0] for item in trace if item["placement"]}
    return rows == {1, 2}


def _witness_source_socket_permutation(grid):
    source_order, destination_order = _source_destination_orders(grid)
    return source_order != destination_order


def _witness_first_blank_distractor(grid):
    trace, _ = _placement_trace(grid)
    return any(item["candidate_count"] >= 2 for item in trace)


def _witness_deep_socket(grid):
    trace, _ = _placement_trace(grid)
    return any(
        item["placement"] is not None
        and item["placement"][0] + _dims(item["shape"])[0] - 1 >= 4
        for item in trace
    )


SEMANTIC_WITNESSES = {
    "four_source_shapes": _witness_four_shapes,
    "same_size_distinct_shapes": _witness_same_size_distinct,
    "mixed_socket_start_rows": _witness_mixed_socket_rows,
    "source_socket_permutation": _witness_source_socket_permutation,
    "later_supported_distractor": _witness_first_blank_distractor,
    "socket_reaches_row_4": _witness_deep_socket,
}


def _erase_only(grid):
    return _clear_sources(grid)


def _recolor_in_place(grid):
    return [
        [1 if value == 5 else value for value in row]
        for row in grid
    ]


def lesson_identifiable(demos, query) -> list[str]:
    """Check the deliberately scheduled three-demo curriculum.

    The first three sample indices expose all official linked profiles: one
    four-object lesson, one same-size/different-shape tie, mixed row-1/row-2
    sockets, and an all-row-1 counterexample.  Each output must equal an
    independent Python simulation of the Racket rule and must refute erase-only
    and recolor-in-place shortcuts.
    """
    reasons = []
    if len(demos) < 3:
        return ["need at least three demonstrations"]
    profiles = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if output != _python_apply(grid):
            reasons.append(f"demo {index} output disagrees with placement rule")
        profiles.add(canonical_profile_signature(grid))
        if output == _erase_only(grid):
            reasons.append(f"demo {index} does not refute erase-only")
        if output == _recolor_in_place(grid):
            reasons.append(f"demo {index} does not refute recolor-in-place")
    if not _CANONICAL_SIGNATURES.issubset(profiles):
        reasons.append("demos do not cover all three linked canonical profiles")
    if not any(_witness_four_shapes(pair["input"]) for pair in demos):
        reasons.append("demos omit the four-source branch")
    if not any(_witness_same_size_distinct(pair["input"]) for pair in demos):
        reasons.append("demos omit same-size/different-shape matching")
    if not any(_witness_mixed_socket_rows(pair["input"]) for pair in demos):
        reasons.append("demos omit mixed row-1/row-2 sockets")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != _python_apply(q_grid):
        reasons.append("query answer disagrees with placement rule")
    return reasons


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _pack_columns(shapes, width, rng):
    widths = [_dims(shape)[1] for shape in shapes]
    required = sum(widths) + len(widths) - 1
    if required > width:
        return None
    buckets = [0] * (len(widths) + 1)
    for _ in range(width - required):
        buckets[rng.randrange(len(buckets))] += 1
    columns = []
    cursor = buckets[0]
    for index, shape_width in enumerate(widths):
        columns.append(cursor)
        cursor += shape_width
        if index + 1 < len(widths):
            cursor += 1 + buckets[index + 1]
    return columns


def _paint_source(grid, shape, bottom_row, left):
    height, _ = _dims(shape)
    top = bottom_row - height + 1
    for dr, dc in shape:
        grid[top + dr][left + dc] = 5


def _build_grid(h, w, socket_layout, source_order, rng):
    grid = full_grid(h, w, 0)
    for r in range(3):
        for c in range(w):
            grid[r][c] = 2
    for shape, row, col in socket_layout:
        for dr, dc in shape:
            grid[row + dr][col + dc] = 0

    source_columns = _pack_columns(source_order, w, rng)
    if source_columns is None:
        return None
    for shape, col in zip(source_order, source_columns):
        _paint_source(grid, shape, h - 1, col)
    return grid


def _nonidentity_order(items, rng):
    items = list(items)
    if len(items) <= 1:
        return items
    shuffled = items[:]
    for _ in range(12):
        rng.shuffle(shuffled)
        if shuffled != items:
            return shuffled[:]
    return items[1:] + items[:1]


def _canonical_grid(profile_index, rng):
    layout = list(_CANONICAL_LAYOUTS[profile_index])
    destination_shapes = [shape for shape, _, _ in sorted(layout, key=lambda x: x[2])]
    source_order = _nonidentity_order(destination_shapes, rng)
    for _ in range(40):
        grid = _build_grid(10, 15, layout, source_order, rng)
        if grid is not None and not self_check(grid):
            return grid
        source_order = _nonidentity_order(destination_shapes, rng)
    raise ValueError("could not materialize canonical linked profile")


def _choose_general_shapes(rng, n_shapes, width, difficulty, equal_size_pair):
    if difficulty == "easy":
        pool = [shape for shape in _GENERAL_SHAPES if len(shape) <= 6]
    elif difficulty == "hard":
        pool = [shape for shape in _GENERAL_SHAPES if len(shape) >= 4]
    else:
        pool = list(_GENERAL_SHAPES)

    by_size = defaultdict(list)
    for shape in pool:
        by_size[len(shape)].append(shape)

    for _ in range(200):
        chosen = []
        if equal_size_pair:
            eligible_sizes = [size for size, group in by_size.items() if len(group) >= 2]
            size = rng.choice(eligible_sizes)
            chosen.extend(rng.sample(by_size[size], 2))
        candidates = pool[:]
        rng.shuffle(candidates)
        for shape in candidates:
            if shape in chosen:
                continue
            chosen.append(shape)
            if len(chosen) == n_shapes:
                break
        if len(chosen) != n_shapes:
            continue
        rng.shuffle(chosen)
        if sum(_dims(shape)[1] for shape in chosen) + n_shapes - 1 <= width:
            return chosen
    raise ValueError("could not choose a packable distinct shape set")


def _general_grid(h, w, n_shapes, difficulty, sample_index, rng):
    equal_size_pair = sample_index % 2 == 1
    mixed_rows = sample_index % 3 != 2
    for _ in range(240):
        shapes = _choose_general_shapes(
            rng, n_shapes, w, difficulty, equal_size_pair
        )
        destination_order = shapes[:]
        rng.shuffle(destination_order)
        columns = _pack_columns(destination_order, w, rng)
        if columns is None:
            continue
        rows = [1] * n_shapes
        if mixed_rows:
            rows[rng.randrange(n_shapes)] = 2
        socket_layout = [
            (shape, row, col)
            for shape, row, col in zip(destination_order, rows, columns)
        ]
        source_order = _nonidentity_order(destination_order, rng)
        grid = _build_grid(h, w, socket_layout, source_order, rng)
        if grid is not None and not self_check(grid):
            return grid
    raise ValueError("could not construct a lawful generalized socket lesson")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    has_axis_override = any(
        overrides.get(label) is not None
        for label in ("grid_h", "grid_w", "n_shapes")
    )

    profile_index = sample_index % 10
    if not has_axis_override and profile_index < len(_CANONICAL_LAYOUTS):
        n_shapes = len(_CANONICAL_LAYOUTS[profile_index])
        ctx.draw_int("grid_h", 10, 10)
        ctx.draw_int("grid_w", 15, 15)
        ctx.draw_int("n_shapes", n_shapes, n_shapes)
        return _canonical_grid(profile_index, rng)

    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 10, 11, 15, 17
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 14, 18, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 12, 15, 19

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)
    n_shapes = _banded_int(ctx, overrides, "n_shapes", 3, 4, 3, 4)
    return _general_grid(h, w, n_shapes, band, sample_index, rng)
