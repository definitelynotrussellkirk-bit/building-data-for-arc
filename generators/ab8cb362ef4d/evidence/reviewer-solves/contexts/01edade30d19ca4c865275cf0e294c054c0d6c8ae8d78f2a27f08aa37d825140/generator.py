"""Generator for “Apply Gravity Inside Each Box” (ab8cb362ef4d).

Each color-5 connected component supplies a rectangular box by its bounding box.
The selected authority restores that full border to 5, then independently packs
all nonzero interior cells to the bottom of each interior column while preserving
their top-to-bottom order.  A lawful input may therefore contain one non-5 cell
overwriting a side of a box; that is a semantic branch, not a malformed frame.
"""
from __future__ import annotations

from math import ceil

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ab8cb362ef4d"
TASK_ID = GENERATOR_ID
RULE_HASH = "94102b577ef7"
VERSION = "2.0.0"
SUMMARY = (
    "One to three separated color-5 boxes contain colored cells in separate, "
    "stacked, or mixed columns. Gravity acts independently inside every box; "
    "the output also repairs an optional non-5 overwrite on a box border."
)

INVARIANTS = [
    "1..3 disconnected color-5 components define rectangular bounding boxes",
    "each box has at most one non-5 border overwrite and at least two interior markers",
    "all nonzero cells lie on or inside a box and at least one interior marker can fall",
    "2..7 distinct marker colors are used; 0 is background and 5 is the frame color",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

AXES = {
    "grid_h": {"type": "int", "default": "three-step canonical-profile schedule", "valid": "11..16"},
    "grid_w": {"type": "int", "default": "three-step canonical-profile schedule", "valid": "12..18"},
    "n_frames": {"type": "int", "default": "schedule cycles 2,3,1", "valid": "1..3"},
    "n_colors": {"type": "int", "default": "schedule cycles 6,7,6", "valid": "2..7"},
    "column_pattern": {
        "type": "str",
        "default": "schedule cycles mixed,separate,stacked",
        "valid": "separate|stacked|mixed",
    },
    "border_overwrites": {"type": "int", "default": "schedule cycles 1,0,0", "valid": "0..1"},
}

# Every three consecutive examples expose all declared rival-refuting branches.
_SCHEDULE = (
    dict(grid_h=12, grid_w=14, n_frames=2, n_colors=6,
         column_pattern="mixed", border_overwrites=1),
    dict(grid_h=13, grid_w=15, n_frames=3, n_colors=7,
         column_pattern="separate", border_overwrites=0),
    dict(grid_h=11, grid_w=13, n_frames=1, n_colors=6,
         column_pattern="stacked", border_overwrites=0),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_PATTERNS = ("separate", "stacked", "mixed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Public, deterministic teaching-schedule residue used by the gate."""
    del seed, difficulty
    return sample_index % len(_SCHEDULE)


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "n_frames", "n_colors", "border_overwrites"}:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        elif name == "column_pattern" and type(value) is not str:
            raise ValueError(f"column_pattern must be a string, not {type(value).__name__}")


def _marker_counts(n_frames, n_colors, pattern):
    total = max(n_colors, 2 * n_frames)
    if pattern == "mixed":
        total = max(total, 2 * n_frames + 1)
    counts = [2] * n_frames
    remaining = total - 2 * n_frames
    order = [0] + list(range(1, n_frames)) if pattern == "mixed" else list(range(n_frames))
    index = 0
    while remaining:
        counts[order[index % len(order)]] += 1
        remaining -= 1
        index += 1
    return counts


def _minimum_size(pattern, count, index):
    if pattern == "separate" or (pattern == "mixed" and index > 0):
        return 4, count + 2
    if pattern == "stacked":
        # The lead stack gets one spare interior row, guaranteeing a real fall.
        return count + (3 if index == 0 else 2), 4
    # Mixed lead: two columns plus at least one spare interior cell, so the
    # stacked column contains a gap rather than already being bottom-packed.
    interior_h = max(3, ceil((count + 1) / 2))
    return interior_h + 2, 4


def _separated(left, right):
    ar0, ac0, ar1, ac1 = left
    br0, bc0, br1, bc1 = right
    # At least one complete zero row OR column separates any two boxes.
    return (ar1 + 1 < br0 or br1 + 1 < ar0
            or ac1 + 1 < bc0 or bc1 + 1 < ac0)


def _positions_for(h, w, fh, fw, anchor, rng):
    rows = range(h - fh + 1)
    cols = range(w - fw + 1)
    if anchor == "tl":
        target = (0, 0)
    elif anchor == "tr":
        target = (0, w - fw)
    else:
        target = (h - fh, 0)
    positions = [(r, c, r + fh - 1, c + fw - 1) for r in rows for c in cols]
    jitter = {rect: rng.random() for rect in positions}
    positions.sort(key=lambda rect: (
        abs(rect[0] - target[0]) + abs(rect[1] - target[1]), jitter[rect]
    ))
    return positions


def _place_rectangles(h, w, sizes, rng):
    anchors = ("tl", "tr", "bl")
    candidates = [
        _positions_for(h, w, fh, fw, anchors[index], rng)
        for index, (fh, fw) in enumerate(sizes)
    ]
    order = sorted(range(len(sizes)), key=lambda i: sizes[i][0] * sizes[i][1], reverse=True)
    placed = [None] * len(sizes)

    def search(depth):
        if depth == len(order):
            return True
        index = order[depth]
        for rect in candidates[index]:
            if all(other is None or _separated(rect, other) for other in placed):
                placed[index] = rect
                if search(depth + 1):
                    return True
                placed[index] = None
        return False

    if not search(0):
        raise ValueError(f"cannot place frame sizes {sizes} in {h}x{w}")
    return list(placed)


def _choose_boxes(ctx, h, w, counts, pattern, band):
    minima = [_minimum_size(pattern, count, index) for index, count in enumerate(counts)]
    if any(fh > h or fw > w for fh, fw in minima):
        raise ValueError(f"requested marker pattern cannot fit in {h}x{w}")
    rng = ctx.draw_rng(f"box_geometry:{band}")
    desired = [
        (min(h, fh + rng.randint(0, 2)), min(w, fw + rng.randint(0, 2)))
        for fh, fw in minima
    ]
    # Prefer varied dimensions, but deterministic minimum dimensions are a
    # constructive fallback for every advertised boundary combination.
    for sizes in (desired, minima):
        try:
            return _place_rectangles(h, w, sizes, rng)
        except ValueError:
            continue
    raise ValueError(f"no constructive layout for {h}x{w}, counts={counts}, pattern={pattern}")


def _draw_border(grid, box):
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = 5
        grid[r1][c] = 5
    for r in range(r0, r1 + 1):
        grid[r][c0] = 5
        grid[r][c1] = 5


def _marker_positions(box, count, pattern, index, rng):
    r0, c0, r1, c1 = box
    rows = list(range(r0 + 1, r1))
    cols = list(range(c0 + 1, c1))
    if pattern == "separate" or (pattern == "mixed" and index > 0):
        chosen_cols = rng.sample(cols, count)
        positions = [(r1 - 1, chosen_cols[0])]
        upper = rows[:-1]
        positions.extend((rng.choice(upper), c) for c in chosen_cols[1:])
        return positions
    if pattern == "stacked":
        c = rng.choice(cols)
        if index == 0:
            # Keep one hole immediately above the bottom marker.
            chosen_rows = rows[:count - 1] + [rows[-1]]
        else:
            chosen_rows = sorted(rng.sample(rows, count))
        return [(r, c) for r in chosen_rows]

    # Mixed lead: an actual gapped stack plus an occupied second column.
    first, second = rng.sample(cols, 2)
    positions = [(rows[0], first), (rows[-1], first), (rows[0], second)]
    available = [(r, c) for c in (second, first) for r in rows
                 if (r, c) not in positions]
    positions.extend(rng.sample(available, count - 3))
    return positions


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    scheduled = dict(_SCHEDULE[schedule_profile(seed, sample_index, difficulty)])
    effective = {**scheduled, **{key: value for key, value in overrides.items() if value is not None}}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=effective)

    h = ctx.draw_int("grid_h", 11, 16)
    w = ctx.draw_int("grid_w", 12, 18)
    n_frames = ctx.draw_int("n_frames", 1, 3)
    n_colors = ctx.draw_int("n_colors", 2, 7)
    pattern = ctx.draw_choice("column_pattern", _PATTERNS)
    border_overwrites = ctx.draw_int("border_overwrites", 0, 1)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    counts = _marker_counts(n_frames, n_colors, pattern)
    boxes = _choose_boxes(ctx, h, w, counts, pattern, band)
    grid = full_grid(h, w, 0)
    for box in boxes:
        _draw_border(grid, box)

    palette_rng = ctx.draw_rng(f"palette:{band}")
    palette = palette_rng.sample(list(_MARKER_COLORS), n_colors)
    marker_total = sum(counts)
    marker_colors = palette + [palette[i % n_colors] for i in range(marker_total - n_colors)]
    palette_rng.shuffle(marker_colors)

    cursor = 0
    placement_rng = ctx.draw_rng(f"markers:{band}")
    for index, (box, count) in enumerate(zip(boxes, counts)):
        positions = _marker_positions(box, count, pattern, index, placement_rng)
        colors = marker_colors[cursor:cursor + count]
        cursor += count
        for (r, c), color in zip(positions, colors):
            grid[r][c] = color

    if border_overwrites:
        r0, c0, r1, c1 = boxes[0]
        candidates = (
            [(r0, c) for c in range(c0 + 1, c1)]
            + [(r1, c) for c in range(c0 + 1, c1)]
            + [(r, c0) for r in range(r0 + 1, r1)]
            + [(r, c1) for r in range(r0 + 1, r1)]
        )
        r, c = ctx.draw_rng(f"border_overwrite:{band}").choice(candidates)
        grid[r][c] = palette[0]
    return grid


def _five_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            component = []
            while stack:
                pr, pc = stack.pop()
                component.append((pr, pc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 5
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _frame_boxes(grid):
    boxes = []
    for component in _five_components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        boxes.append((min(rows), min(cols), max(rows), max(cols)))
    return sorted(boxes)


def _observed(grid, boxes):
    colors = {value for row in grid for value in row if value not in (0, 5)}
    overwrites = 0
    column_counts = []
    occupied_per_box = []
    for r0, c0, r1, c1 in boxes:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r in (r0, r1) or c in (c0, c1)) and grid[r][c] != 5:
                    overwrites += 1
        occupied = 0
        for c in range(c0 + 1, c1):
            count = sum(grid[r][c] not in (0, 5) for r in range(r0 + 1, r1))
            if count:
                occupied += 1
                column_counts.append(count)
        occupied_per_box.append(occupied)
    if column_counts and all(count == 1 for count in column_counts):
        pattern = "separate"
    elif boxes and all(count == 1 for count in occupied_per_box):
        pattern = "stacked"
    else:
        pattern = "mixed"
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "n_frames": len(boxes), "n_colors": len(colors),
        "column_pattern": pattern, "border_overwrites": overwrites,
    }


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    issues = self_check(grid)
    if issues:
        raise ValueError("cannot observe malformed grid: " + "; ".join(issues[:3]))
    return _observed(grid, _frame_boxes(grid))


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    h, w = len(grid), width
    errors = []
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")

    boxes = _frame_boxes(grid)
    if not 1 <= len(boxes) <= 3:
        errors.append(f"expected 1..3 color-5 frame components, found {len(boxes)}")
    covered = set()
    movable = 0
    all_marker_colors = set()
    for box in boxes:
        r0, c0, r1, c1 = box
        if r1 - r0 + 1 < 4 or c1 - c0 + 1 < 4:
            errors.append(f"frame {box} is smaller than 4x4")
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                covered.add((r, c))
        if any(grid[r][c] != 5 for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1))):
            errors.append(f"frame {box} must retain all four color-5 corners")
        overwritten = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                border = r in (r0, r1) or c in (c0, c1)
                value = grid[r][c]
                if border:
                    if value == 0:
                        errors.append(f"frame {box} has a zero border gap at {(r, c)}")
                    elif value != 5:
                        overwritten.append((r, c, value))
                elif value == 5:
                    errors.append(f"frame {box} has interior color 5 at {(r, c)}")
        if len(overwritten) > 1:
            errors.append(f"frame {box} has {len(overwritten)} border overwrites; maximum is one")
        markers = [(r, c, grid[r][c]) for r in range(r0 + 1, r1)
                   for c in range(c0 + 1, c1) if grid[r][c] not in (0, 5)]
        if len(markers) < 2:
            errors.append(f"frame {box} has fewer than two interior markers")
        movable += sum(r < r1 - 1 for r, _, _ in markers)
        all_marker_colors.update(value for _, _, value in markers)
        all_marker_colors.update(value for _, _, value in overwritten)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and (r, c) not in covered:
                errors.append(f"nonzero cell {(r, c)} lies outside every frame bounding box")
                break
        if errors and errors[-1].startswith("nonzero cell"):
            break
    if movable == 0:
        errors.append("no interior marker can move downward")
    if not 2 <= len(all_marker_colors) <= 7:
        errors.append(f"expected 2..7 distinct non-frame colors, found {len(all_marker_colors)}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _apply_reference(grid):
    """Python mirror used only for executable rival contracts and tests."""
    out = [[0 for _ in row] for row in grid]
    for r0, c0, r1, c1 in _frame_boxes(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = 5
        for c in range(c0 + 1, c1):
            values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
            start = r1 - len(values)
            for offset, value in enumerate(values):
                out[start + offset][c] = value
    return out


def _first_frame_only(grid):
    boxes = _frame_boxes(grid)
    full = _apply_reference(grid)
    out = [[0 for _ in row] for row in grid]
    if boxes:
        r0, c0, r1, c1 = boxes[0]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = full[r][c]
    return out


def _preserve_damaged_border(grid):
    out = _apply_reference(grid)
    for r0, c0, r1, c1 in _frame_boxes(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = grid[r][c]
    return out


def _one_per_column(grid):
    out = _apply_reference(grid)
    for r0, c0, r1, c1 in _frame_boxes(grid):
        for c in range(c0 + 1, c1):
            values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
            for r in range(r0 + 1, r1):
                out[r][c] = 0
            if values:
                out[r1 - 1][c] = values[-1]
    return out


def _has_multiple_frames(grid):
    return len(_frame_boxes(grid)) > 1


def _has_damaged_border(grid):
    boxes = _frame_boxes(grid)
    return bool(boxes and _observed(grid, boxes)["border_overwrites"])


def _has_stacked_column(grid):
    for r0, c0, r1, c1 in _frame_boxes(grid):
        for c in range(c0 + 1, c1):
            if sum(grid[r][c] not in (0, 5) for r in range(r0 + 1, r1)) >= 2:
                return True
    return False


SEMANTIC_WITNESSES = {
    "multiple_frames": _has_multiple_frames,
    "damaged_border": _has_damaged_border,
    "stacked_column": _has_stacked_column,
}
SEMANTIC_RIVALS = {
    "first_frame_only": _first_frame_only,
    "preserve_damaged_border": _preserve_damaged_border,
    "one_per_column": _one_per_column,
}
WITNESS_RIVALS = {
    "multiple_frames": ["first_frame_only"],
    "damaged_border": ["preserve_damaged_border"],
    "stacked_column": ["one_per_column"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query):
    """Report any named rival that fits every demo but changes the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits and rival(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demo but changes the query")
    return reasons
