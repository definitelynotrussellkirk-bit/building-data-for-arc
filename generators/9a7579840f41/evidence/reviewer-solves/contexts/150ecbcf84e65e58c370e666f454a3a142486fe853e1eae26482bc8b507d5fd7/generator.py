"""Generator for arc_puzzle_bank_21_set6_s:S6_H4 — stamp template at wire turns.

Rule: follow the color-1 WIRE from the color-7 start; at every TURN of
that ordered wire, stamp the normalized color-4 TEMPLATE shape with the
turn cell as its top-left anchor.  The output is a fresh grid containing
only those color-4 stamps.

The generator constructs self-avoiding orthogonal paths with an exact
requested turn count, including both staircase and direction-reversing
families.  A separate connected template is placed away from both the wire
and all answer stamps.  Every declared AXES value is recoverable from the
returned input grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9a7579840f41"
VERSION = "3.3.0"  # canonical perpendicular entry; semantic shortcut witnesses
TASK_ID = "9a7579840f41"
RULE_HASH = "7dd342fe1468"

SUMMARY = (
    "A zero-background grid contains one connected color-4 template, one "
    "color-7 start marker, and one non-branching color-1 wire. Follow the "
    "wire from the start; at every direction change, stamp the normalized "
    "template with top-left alignment onto a fresh output grid. Grid size, "
    "template size/shape, exact turn count, start orientation, path signs, "
    "segment lengths, and placements vary."
)

INVARIANTS = [
    "exactly one connected color-4 template and exactly one color-7 start",
    "the start touches exactly the first wire cell and enters perpendicular to its first segment",
    "the ordered wire has at least one turn and every turn admits a full top-left-aligned template stamp",
    "the input template is separate from the wire/start and from every answer-stamp cell",
]

# These are explicit must-reject fixtures for the defect-lint texture probe.
# They are deliberately not AXES: they are malformed lessons, not lawful
# generation modes.
DEGENERATE_TEXTURES = (
    "no_template",
    "no_wire",
    "straight_wire_no_turns",
)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Only exact, independently observable controls are declared.  Difficulty
# changes their default distribution through draw_int_diff, while every listed
# boundary remains a lawful explicit override in every band.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "12..18"},
    "n_turns": {"type": "int", "default": "difficulty-aware", "valid": "1..5"},
    "template_size": {"type": "int", "default": "difficulty-aware", "valid": "2..5"},
    "start_axis": {
        "type": "str",
        "default": "rng",
        "valid": "horizontal|vertical",
    },
}

# Exact linked axis profiles observed across all official train/test inputs.
# A default-only 30% curriculum prior keeps these empirical profiles present
# in every difficulty band; explicit overrides always bypass the prior.
_CANONICAL_AXIS_PROFILES = (
    (7, 14, 2, 3, "vertical"),
    (9, 15, 2, 3, "vertical"),
    (10, 16, 3, 2, "vertical"),
)
_CANONICAL_PROFILE_RATE = 0.30

_TEMPLATE_BASES = {
    2: (
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
}


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform(cells, rotation, reflect):
    out = list(cells)
    if reflect:
        max_c = max(c for _, c in out)
        out = [(r, max_c - c) for r, c in out]
    for _ in range(rotation % 4):
        max_r = max(r for r, _ in out)
        out = [(c, max_r - r) for r, c in out]
        out = list(_normalize(out))
    return _normalize(out)


def _shape_variants(size):
    variants = set()
    for base in _TEMPLATE_BASES[size]:
        for reflect in (False, True):
            for rotation in range(4):
                variants.add(_transform(base, rotation, reflect))
    return tuple(sorted(variants))


def _segment_lengths(rng, count, budget):
    """Return count lengths in 2..4 whose sum does not exceed budget."""
    minimum = 2 * count
    if minimum > budget:
        return None
    lengths = [2] * count
    extra_capacity = min(budget - minimum, 2 * count)
    extra = rng.randint(0, extra_capacity)
    slots = [i for i in range(count) for _ in range(2)]
    rng.shuffle(slots)
    for i in slots[:extra]:
        lengths[i] += 1
    return lengths


def _relative_path(
    start_axis,
    horizontal_lengths,
    vertical_lengths,
    horizontal_signs,
    vertical_signs,
):
    path = [(0, 0)]
    hi = vi = 0
    n_segments = len(horizontal_lengths) + len(vertical_lengths)
    for segment in range(n_segments):
        horizontal = (segment % 2 == 0) == (start_axis == "horizontal")
        if horizontal:
            direction = (0, horizontal_signs[hi])
            length = horizontal_lengths[hi]
            hi += 1
        else:
            direction = (vertical_signs[vi], 0)
            length = vertical_lengths[vi]
            vi += 1
        for _ in range(length):
            r, c = path[-1]
            path.append((r + direction[0], c + direction[1]))
    return path


def _sign_patterns(rng, horizontal_count, vertical_count, path_mode, *, randomize):
    """Return segment-sign sequences for one structural path family."""
    base_pairs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if randomize:
        rng.shuffle(base_pairs)

    patterns = []
    if path_mode == "staircase":
        for h_base, v_base in base_pairs:
            patterns.append(
                (
                    [h_base] * horizontal_count,
                    [v_base] * vertical_count,
                )
            )
    elif path_mode == "reversal":
        eligible = []
        if horizontal_count >= 2:
            eligible.append("horizontal")
        if vertical_count >= 2:
            eligible.append("vertical")
        if randomize:
            rng.shuffle(eligible)
        for reversed_axis in eligible:
            for h_base, v_base in base_pairs:
                horizontal_signs = [h_base] * horizontal_count
                vertical_signs = [v_base] * vertical_count
                if reversed_axis == "horizontal":
                    horizontal_signs = [
                        h_base if i % 2 == 0 else -h_base
                        for i in range(horizontal_count)
                    ]
                else:
                    vertical_signs = [
                        v_base if i % 2 == 0 else -v_base
                        for i in range(vertical_count)
                    ]
                patterns.append((horizontal_signs, vertical_signs))
    else:
        raise ValueError(f"unknown path mode: {path_mode}")

    if randomize:
        rng.shuffle(patterns)
    return patterns


def _turns(path):
    return [
        path[i]
        for i in range(1, len(path) - 1)
        if (
            path[i][0] - path[i - 1][0],
            path[i][1] - path[i - 1][1],
        )
        != (
            path[i + 1][0] - path[i][0],
            path[i + 1][1] - path[i][1],
        )
    ]


def _wire_topology_error(path):
    pset = set(path)
    if len(pset) != len(path):
        return "wire repeats a cell"
    for i, cell in enumerate(path):
        actual = {
            (cell[0] + dr, cell[1] + dc)
            for dr, dc in _CARD
            if (cell[0] + dr, cell[1] + dc) in pset
        }
        expected = set()
        if i:
            expected.add(path[i - 1])
        if i + 1 < len(path):
            expected.add(path[i + 1])
        if actual != expected:
            return "wire self-touches or branches"
    return None


def _translated_layouts(path, shape, h, w):
    """Yield translations with a perpendicular, unambiguous start entry."""
    first_step = (path[1][0] - path[0][0], path[1][1] - path[0][1])
    start_offsets = (
        (-first_step[1], first_step[0]),
        (first_step[1], -first_step[0]),
    )
    turn_cells = _turns(path)
    bh = max(r for r, _ in shape) + 1
    bw = max(c for _, c in shape) + 1
    path_cells = set(path)

    for offset_r, offset_c in start_offsets:
        start = (path[0][0] + offset_r, path[0][1] + offset_c)
        touched_wire = {
            (start[0] + dr, start[1] + dc)
            for dr, dc in _CARD
            if (start[0] + dr, start[1] + dc) in path_cells
        }
        if touched_wire != {path[0]}:
            continue

        all_cells = path + [start]
        row_lo = -min(r for r, _ in all_cells)
        row_hi = h - 1 - max(r for r, _ in all_cells)
        col_lo = -min(c for _, c in all_cells)
        col_hi = w - 1 - max(c for _, c in all_cells)
        for tr, tc in turn_cells:
            row_lo = max(row_lo, -tr)
            row_hi = min(row_hi, h - bh - tr)
            col_lo = max(col_lo, -tc)
            col_hi = min(col_hi, w - bw - tc)
        if row_lo > row_hi or col_lo > col_hi:
            continue

        for row_shift in range(row_lo, row_hi + 1):
            for col_shift in range(col_lo, col_hi + 1):
                shifted_path = [
                    (r + row_shift, c + col_shift) for r, c in path
                ]
                shifted_start = (
                    start[0] + row_shift,
                    start[1] + col_shift,
                )
                shifted_turns = [
                    (r + row_shift, c + col_shift) for r, c in turn_cells
                ]
                yield shifted_path, shifted_start, shifted_turns


def _template_placements(shape, h, w, occupied, answer_cells):
    bh = max(r for r, _ in shape) + 1
    bw = max(c for _, c in shape) + 1
    for top in range(h - bh + 1):
        for left in range(w - bw + 1):
            cells = {(top + r, left + c) for r, c in shape}
            if cells & answer_cells:
                continue
            if any(
                max(abs(r - rr), abs(c - cc)) <= 1
                for r, c in cells
                for rr, cc in occupied
            ):
                continue
            yield tuple(sorted(cells))


def _try_layout(
    rng,
    h,
    w,
    n_turns,
    start_axis,
    shape,
    path_mode,
    *,
    random_lengths=True,
):
    n_segments = n_turns + 1
    horizontal_count = sum(
        (segment % 2 == 0) == (start_axis == "horizontal")
        for segment in range(n_segments)
    )
    vertical_count = n_segments - horizontal_count

    h_budget = w - (2 if start_axis == "horizontal" else 1)
    v_budget = h - (2 if start_axis == "vertical" else 1)
    if random_lengths:
        horizontal_lengths = _segment_lengths(rng, horizontal_count, h_budget)
        vertical_lengths = _segment_lengths(rng, vertical_count, v_budget)
    else:
        horizontal_lengths = [2] * horizontal_count
        vertical_lengths = [2] * vertical_count
    if horizontal_lengths is None or vertical_lengths is None:
        return None

    sign_patterns = _sign_patterns(
        rng,
        horizontal_count,
        vertical_count,
        path_mode,
        randomize=random_lengths,
    )
    for horizontal_signs, vertical_signs in sign_patterns:
        path = _relative_path(
            start_axis,
            horizontal_lengths,
            vertical_lengths,
            horizontal_signs,
            vertical_signs,
        )
        if _wire_topology_error(path) or len(_turns(path)) != n_turns:
            continue
        layouts = list(_translated_layouts(path, shape, h, w))
        if random_lengths:
            rng.shuffle(layouts)
        for shifted_path, shifted_start, shifted_turns in layouts:
            occupied = set(shifted_path) | {shifted_start}
            answer_cells = {
                (tr + dr, tc + dc)
                for tr, tc in shifted_turns
                for dr, dc in shape
            }
            # A perpendicular marker makes the first wire cell look like a
            # local corner only to the wrong rule that treats color 7 as wire.
            # Keep at least one in-bounds cell of that false stamp outside the
            # true answer so every generated example falsifies the shortcut.
            false_start_stamp = {
                (shifted_path[0][0] + dr, shifted_path[0][1] + dc)
                for dr, dc in shape
                if (
                    0 <= shifted_path[0][0] + dr < h
                    and 0 <= shifted_path[0][1] + dc < w
                )
            }
            if not false_start_stamp - answer_cells:
                continue
            placements = list(
                _template_placements(shape, h, w, occupied, answer_cells)
            )
            if not placements:
                continue
            template_cells = rng.choice(placements) if random_lengths else placements[0]
            return shifted_path, shifted_start, shifted_turns, template_cells
    return None


def _construct_layout(rng, h, w, n_turns, template_size, start_axis):
    variants = _shape_variants(template_size)
    # A one-turn path has only one segment on each axis, so a direction
    # reversal is structurally impossible.  From two turns onward both lawful
    # path families are sampled directly rather than hidden behind metadata.
    requested_mode = (
        rng.choice(("staircase", "reversal"))
        if n_turns >= 2
        else "staircase"
    )
    for _ in range(240):
        shape = rng.choice(variants)
        result = _try_layout(
            rng,
            h,
            w,
            n_turns,
            start_axis,
            shape,
            requested_mode,
            random_lengths=True,
        )
        if result is not None:
            return shape, result

    # Deterministic exhaustive fallback preserves every requested observable
    # axis.  It tries the requested hidden family first, then the other lawful
    # family only if geometry leaves no placement for the first.
    fallback_modes = [requested_mode]
    if n_turns >= 2:
        fallback_modes.append(
            "reversal" if requested_mode == "staircase" else "staircase"
        )
    for path_mode in fallback_modes:
        for shape in variants:
            result = _try_layout(
                rng,
                h,
                w,
                n_turns,
                start_axis,
                shape,
                path_mode,
                random_lengths=False,
            )
            if result is not None:
                return shape, result
    raise RuntimeError(
        "no valid layout for requested exact axes: "
        f"h={h} w={w} n_turns={n_turns} template_size={template_size} "
        f"start_axis={start_axis}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            return _draw_from_degenerate(texture)
        raise ValueError(f"unknown texture fixture: {texture!r}")

    explicit_axes = {
        key for key in AXES if key in overrides and overrides[key] is not None
    }
    curriculum_rng = ctx.draw_rng("curriculum")
    canonical_profile = None
    if not explicit_axes and curriculum_rng.random() < _CANONICAL_PROFILE_RATE:
        canonical_profile = curriculum_rng.choice(_CANONICAL_AXIS_PROFILES)

    if canonical_profile is None:
        h = ctx.draw_int_diff("grid_h", 7, 16)
        w = ctx.draw_int_diff("grid_w", 12, 18)
        n_turns = ctx.draw_int_diff("n_turns", 1, 5)
        template_size = ctx.draw_int_diff("template_size", 2, 5)
        start_axis = ctx.draw_choice("start_axis", ("horizontal", "vertical"))
    else:
        profile_h, profile_w, profile_turns, profile_size, profile_axis = canonical_profile
        h = ctx.draw_choice("grid_h", (profile_h,))
        w = ctx.draw_choice("grid_w", (profile_w,))
        n_turns = ctx.draw_choice("n_turns", (profile_turns,))
        template_size = ctx.draw_choice("template_size", (profile_size,))
        start_axis = ctx.draw_choice("start_axis", (profile_axis,))
    rng = ctx.draw_rng("layout")

    _, (path, start, _, template_cells) = _construct_layout(
        rng,
        h,
        w,
        n_turns,
        template_size,
        start_axis,
    )
    grid = full_grid(h, w, 0)
    for r, c in template_cells:
        grid[r][c] = 4
    for r, c in path:
        grid[r][c] = 1
    grid[start[0]][start[1]] = 7
    return grid


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _trace_wire_from_start(grid):
    h, w = len(grid), len(grid[0])
    starts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if len(starts) != 1:
        return None, f"expected exactly one start, found {len(starts)}"
    start = starts[0]
    wire = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    if not wire:
        return None, "expected a non-empty color-1 wire"
    adjs = [
        (start[0] + dr, start[1] + dc)
        for dr, dc in _CARD
        if (start[0] + dr, start[1] + dc) in wire
    ]
    if len(adjs) != 1:
        return None, f"start touches {len(adjs)} wire cells, expected 1"

    path = []
    prev = start
    cur = adjs[0]
    seen = {start}
    while True:
        path.append(cur)
        seen.add(cur)
        nxt = [
            (cur[0] + dr, cur[1] + dc)
            for dr, dc in _CARD
            if (cur[0] + dr, cur[1] + dc) in wire
            and (cur[0] + dr, cur[1] + dc) != prev
            and (cur[0] + dr, cur[1] + dc) not in seen
        ]
        if len(nxt) > 1:
            return path, "wire branches while following from start"
        if not nxt:
            break
        prev, cur = cur, nxt[0]
    if set(path) != wire:
        return path, "wire has disconnected or cyclic cells not reached from start"
    topology_error = _wire_topology_error(path)
    if topology_error:
        return path, topology_error
    return path, None


def _turn_count(path):
    return len(_turns(path))


def _has_direction_reversal(path):
    directions = [
        (b[0] - a[0], b[1] - a[1])
        for a, b in zip(path, path[1:])
    ]
    horizontal = [dc for dr, dc in directions if dr == 0]
    vertical = [dr for dr, dc in directions if dc == 0]
    return (
        bool(horizontal) and min(horizontal) < 0 < max(horizontal)
    ) or (
        bool(vertical) and min(vertical) < 0 < max(vertical)
    )


def observe_overrides(grid):
    path, error = _trace_wire_from_start(grid)
    if error:
        raise ValueError(error)
    template_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    first_step = (
        path[1][0] - path[0][0],
        path[1][1] - path[0][1],
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_turns": _turn_count(path),
        "template_size": len(template_cells),
        "start_axis": "horizontal" if first_step[0] == 0 else "vertical",
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is empty or not a list-of-lists"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return ["grid is ragged or has zero width"]

    errs = []
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 4, 7}:
        errs.append(f"unexpected colors: {sorted(palette - {0, 1, 4, 7})}")

    comps4 = _color_components(grid, 4)
    if len(comps4) != 1:
        errs.append(
            f"expected exactly one connected color-4 template, found {len(comps4)}"
        )
    elif not (2 <= len(comps4[0]) <= 5):
        errs.append(
            f"template size must be 2..5 cells, found {len(comps4[0])}"
        )

    path, wire_err = _trace_wire_from_start(grid)
    if wire_err:
        errs.append(wire_err)
    else:
        if not _has_perpendicular_entry(grid):
            errs.append(
                "color-7 start must enter perpendicular to the first wire segment"
            )
        if len(path) < 3:
            errs.append(f"wire path too short to contain a turn: len={len(path)}")
            return errs
        turns = _turns(path)
        if not turns:
            errs.append(
                "wire has no turn; straight_wire_no_turns degenerate leaked into normal path"
            )
        elif len(comps4) == 1:
            shape = _normalize(comps4[0])
            bh = max(r for r, _ in shape) + 1
            bw = max(c for _, c in shape) + 1
            h, w = len(grid), len(grid[0])
            clipped = [
                turn
                for turn in turns
                if turn[0] + bh > h or turn[1] + bw > w
            ]
            if clipped:
                errs.append(
                    f"{len(clipped)} turn(s) would clip the top-left-aligned template stamp"
                )
    return errs


def _entry_geometry(grid):
    path, error = _trace_wire_from_start(grid)
    if error or len(path) < 2:
        return None
    start = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    )
    entry = (path[0][0] - start[0], path[0][1] - start[1])
    first_step = (
        path[1][0] - path[0][0],
        path[1][1] - path[0][1],
    )
    return entry, first_step


def _has_perpendicular_entry(grid):
    geometry = _entry_geometry(grid)
    if geometry is None:
        return False
    entry, first_step = geometry
    return entry[0] * first_step[0] + entry[1] * first_step[1] == 0


def strict_canonical_like(grid):
    """Accept the canonical grammar, including its perpendicular start entry."""
    errors = self_check(grid)
    if errors:
        return errors
    if not _has_perpendicular_entry(grid):
        return ["color-7 start must enter perpendicular to the first wire segment"]
    return []


def _template_shape(grid):
    components = _color_components(grid, 4)
    if len(components) != 1:
        raise ValueError("expected exactly one color-4 template")
    return _normalize(components[0])


def rule_mirror(grid):
    """Pure Python mirror for tests and executable semantic adversaries."""
    errors = strict_canonical_like(grid)
    if errors:
        raise ValueError("invalid wire-turn input: " + "; ".join(errors))
    path, error = _trace_wire_from_start(grid)
    if error:
        raise ValueError(error)
    output = full_grid(len(grid), len(grid[0]), 0)
    shape = _template_shape(grid)
    for turn_r, turn_c in _turns(path):
        for shape_r, shape_c in shape:
            output[turn_r + shape_r][turn_c + shape_c] = 4
    return output


def _marker_inclusive_local_corner_rival(grid):
    """Wrong shortcut: treat color 7 as wire and stamp every local corner."""
    errors = strict_canonical_like(grid)
    if errors:
        raise ValueError("invalid wire-turn input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    augmented_wire = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] in {1, 7}
    }
    local_corners = [
        (r, c)
        for r, c in augmented_wire
        if (
            ((r - 1, c) in augmented_wire or (r + 1, c) in augmented_wire)
            and ((r, c - 1) in augmented_wire or (r, c + 1) in augmented_wire)
        )
    ]
    output = full_grid(h, w, 0)
    shape = _template_shape(grid)
    for turn_r, turn_c in local_corners:
        for shape_r, shape_c in shape:
            r, c = turn_r + shape_r, turn_c + shape_c
            if 0 <= r < h and 0 <= c < w:
                output[r][c] = 4
    return output


def _perpendicular_entry_refutes_marker_inclusive_corners(grid):
    if strict_canonical_like(grid):
        return False
    return (
        _has_perpendicular_entry(grid)
        and _marker_inclusive_local_corner_rival(grid) != rule_mirror(grid)
    )


EXAMPLES_NEEDED = 3
SEMANTIC_WITNESSES = {
    "perpendicular_entry_refutes_marker_inclusive_corners":
        _perpendicular_entry_refutes_marker_inclusive_corners,
}
SEMANTIC_RIVALS = {
    "marker_inclusive_local_corners": _marker_inclusive_local_corner_rival,
}
WITNESS_RIVALS = {
    "perpendicular_entry_refutes_marker_inclusive_corners": [
        "marker_inclusive_local_corners"
    ],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require labeled demonstrations to refute every named shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(
                "query input is outside the canonical grammar: "
                + query_errors[0]
            )

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = strict_canonical_like(demo["input"])
        if input_errors:
            reasons.append(
                f"demo {index} input is outside the canonical grammar: "
                + input_errors[0]
            )
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
        valid_demos.append(demo)

    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(
                competitor(demo["input"]) == demo["output"]
                for demo in valid_demos
            ):
                reasons.append(
                    f"named competitor survives all demonstrations: {name}"
                )
    return reasons


def _draw_from_degenerate(name):
    grid = full_grid(10, 12, 0)
    template = ((0, 0), (0, 1), (1, 0))
    if name == "no_template":
        grid[3][2] = 7
        for c in range(3, 7):
            grid[3][c] = 1
        for r in range(4, 6):
            grid[r][6] = 1
        return grid
    if name == "no_wire":
        for dr, dc in template:
            grid[dr][dc] = 4
        grid[5][5] = 7
        return grid
    if name == "straight_wire_no_turns":
        for dr, dc in template:
            grid[dr][dc] = 4
        grid[5][2] = 7
        for c in range(3, 9):
            grid[5][c] = 1
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")


def mutation_fixtures():
    """Named task-semantic impostors that self_check must reject."""
    disconnected_template = _draw_from_degenerate("straight_wire_no_turns")
    disconnected_template[5][6] = 0
    disconnected_template[6][6] = 1
    disconnected_template[7][6] = 1
    disconnected_template[0][0] = 4
    disconnected_template[0][1] = 4
    disconnected_template[2][0] = 4

    branched_wire = full_grid(10, 12, 0)
    for r, c in ((0, 0), (0, 1), (1, 0)):
        branched_wire[r][c] = 4
    branched_wire[5][1] = 7
    for r, c in ((5, 2), (5, 3), (5, 4), (5, 5), (6, 4), (7, 4)):
        branched_wire[r][c] = 1

    self_touching_wire = full_grid(10, 12, 0)
    for r, c in ((0, 0), (0, 1), (1, 0)):
        self_touching_wire[r][c] = 4
    self_touching_wire[3][1] = 7
    for r, c in (
        (3, 2), (3, 3), (3, 4), (4, 4), (5, 4),
        (5, 3), (5, 2), (4, 2),
    ):
        self_touching_wire[r][c] = 1

    extra_start = generate(91, 7, difficulty="medium")
    extra_start = [row[:] for row in extra_start]
    for r, row in enumerate(extra_start):
        for c, value in enumerate(row):
            if value == 0:
                extra_start[r][c] = 7
                break
        else:
            continue
        break

    return [
        ("no_template", _draw_from_degenerate("no_template")),
        ("no_wire", _draw_from_degenerate("no_wire")),
        ("straight_wire", _draw_from_degenerate("straight_wire_no_turns")),
        ("disconnected_template", disconnected_template),
        ("branched_wire", branched_wire),
        ("self_touching_wire", self_touching_wire),
        ("extra_start", extra_start),
    ]
