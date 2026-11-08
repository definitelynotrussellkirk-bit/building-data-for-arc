"""Whole-object gravity: slide every object straight down to the floor.

Every input contains several separated, single-color polyominoes.  Each object
moves as one rigid shape by its own maximum legal downward offset; cells within
an object do not collapse independently, and objects of the same color do not
share one common offset.  Disjoint column lanes make the Racket rule's
no-obstacle ``move-to-wall`` semantics exact and collision-free.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_motion import components, parity_check

VERSION = "2.0.0"
TASK_ID = "generic_dense_motion_gen1"
GENERATOR_ID = TASK_ID
SUMMARY = (
    "Slide every nonzero 4-connected object straight down until its own bottom "
    "touches the floor, preserving each object's color and exact shape."
)
INVARIANTS = (
    "background is black and occupies more than half the grid",
    "objects are single-color 4-connected polyominoes in disjoint column lanes",
    "every object begins strictly above the floor and moves by a positive offset",
    "different objects require different downward offsets",
    "same-color objects occur at different heights and therefore move independently",
    "at least one uneven-bottom shape refutes per-column cell gravity in every pair",
    "the output preserves dimensions, colors, component count, and normalized shapes",
)
AXES = {"difficulty": ("easy", "medium", "hard")}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

PROGRAM = """(rule!
 ;; WHOLE-OBJECT GRAVITY.  Find each single-color 4-connected nonzero object,
 ;; then slide that object's complete cell set DOWN by its own largest in-bounds
 ;; offset.  Objects occupy disjoint column lanes, so the no-obstacle primitive
 ;; is exact: no moved object can overwrite another one.
 (lambda (g)
   (let ((objs (objects g 0)))
     (foldl (lambda (o acc)
              (move-to-wall acc (obj-cells o) 'down 0))
            g objs))))"""


def _normalized_rule_text(source: str) -> str:
    code = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return " ".join(code.split())


RULE_HASH = hashlib.sha256(_normalized_rule_text(PROGRAM).encode("utf-8")).hexdigest()

_BAND_CONFIG = {
    "easy": {
        "dims": ((14, 20), (15, 21), (14, 21), (15, 20)),
        "objects": 5,
        "palette": 3,
        "train": 3,
        "test": 1,
    },
    "medium": {
        "dims": ((16, 23), (17, 24), (16, 24), (17, 23)),
        "objects": 6,
        "palette": 3,
        "train": 4,
        "test": 1,
    },
    "hard": {
        "dims": ((18, 26), (19, 27), (18, 27), (19, 26)),
        "objects": 7,
        "palette": 4,
        "train": 4,
        "test": 2,
    },
}

# Every shape is 4-connected, two columns wide, and has unequal bottom heights
# in its occupied columns.  That last property makes per-column gravity visibly
# different from rigid whole-object motion.
_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (2, 0), (3, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 0)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (3, 0)),
)


def _normalize_cells(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _mirror_shape(shape):
    width = max(c for _, c in shape) + 1
    return _normalize_cells((r, width - 1 - c) for r, c in shape)


_ALLOWED_SHAPES = {
    _normalize_cells(shape)
    for base in _SHAPES
    for shape in (base, _mirror_shape(base))
}


def _shape_has_uneven_bottom(cells) -> bool:
    bottoms = defaultdict(list)
    for r, c in cells:
        bottoms[c].append(r)
    return len({max(rows) for rows in bottoms.values()}) >= 2


def _grid_profile(difficulty: str, h: int, w: int, object_count: int) -> bool:
    config = _BAND_CONFIG.get(difficulty)
    return bool(config and (h, w) in config["dims"] and object_count == config["objects"])


def _build_input(
    ctx,
    pair_index: int,
    *,
    h: int,
    w: int,
    palette: list[int],
    object_count: int,
    gap_order: list[int],
    color_offset: int,
    shape_offset: int,
):
    grid = [[0] * w for _ in range(h)]
    rng = ctx.draw_rng(f"layout_{pair_index}")
    occupied_width = 3 * object_count - 1
    lane_offset = rng.randint(0, w - occupied_width)

    for lane in range(object_count):
        shape = _SHAPES[(shape_offset + pair_index + lane) % len(_SHAPES)]
        if rng.randrange(2):
            shape = _mirror_shape(shape)
        else:
            shape = _normalize_cells(shape)
        bh = max(r for r, _ in shape) + 1
        gap = gap_order[(lane + pair_index) % object_count]
        top = h - bh - gap
        left = lane_offset + 3 * lane
        color = palette[(color_offset + pair_index + lane) % len(palette)]
        for r, c in shape:
            grid[top + r][left + c] = color
    return grid


def _apply(grid):
    """Python mirror of PROGRAM: independently move every object to the floor."""
    h = len(grid)
    out = [row[:] for row in grid]
    for color, cells in components(grid, bg=0):
        offset = min(h - 1 - r for r, _ in cells)
        for r, c in cells:
            out[r][c] = 0
        for r, c in cells:
            out[r + offset][c] = color
    return out


def _rival_per_cell_gravity(grid):
    """Wrong rule: collapse cells independently inside each column."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        start = h - len(values)
        for index, value in enumerate(values):
            out[start + index][c] = value
    return out


def _rival_global_shift(grid):
    """Wrong rule: translate the entire foreground by one common offset."""
    h, w = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    offset = h - 1 - max(r for r, _, _ in cells)
    out = [[0] * w for _ in range(h)]
    for r, c, color in cells:
        out[r + offset][c] = color
    return out


def _rival_color_group_shift(grid):
    """Wrong rule: move every disconnected object of one color together."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color in sorted({value for row in grid for value in row if value != 0}):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        offset = h - 1 - max(r for r, _ in cells)
        for r, c in cells:
            out[r + offset][c] = color
    return out


def _rival_move_largest_only(grid):
    """Wrong rule: move only the first largest object and leave all others."""
    h = len(grid)
    objs = components(grid, bg=0)
    color, cells = max(objs, key=lambda item: len(item[1]))
    offset = h - 1 - max(r for r, _ in cells)
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = 0
    for r, c in cells:
        out[r + offset][c] = color
    return out


def _object_signatures(grid):
    return sorted((color, _normalize_cells(cells)) for color, cells in components(grid, bg=0))


def _drop_sequence(grid):
    h = len(grid)
    objs = sorted(components(grid, bg=0), key=lambda item: min(c for _, c in item[1]))
    return tuple(h - 1 - max(r for r, _ in cells) for _, cells in objs)


def strict_canonical_like(grid):
    """Return concise reasons when an input is outside the teaching grammar."""
    reasons = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9)
        for row in grid for value in row
    ):
        reasons.append("all cells must be ARC colors 0..9")
    if sum(value == 0 for row in grid for value in row) <= h * w // 2:
        reasons.append("black background must occupy more than half the grid")

    objs = components(grid, bg=0)
    profile_bands = [band for band in _BAND_CONFIG if _grid_profile(band, h, w, len(objs))]
    if len(profile_bands) != 1:
        reasons.append("dimensions and object count must match one declared difficulty profile")

    seen_columns = set()
    gaps = []
    color_gaps = defaultdict(list)
    for index, (color, cells) in enumerate(objs):
        signature = _normalize_cells(cells)
        if signature not in _ALLOWED_SHAPES:
            reasons.append(f"object {index} is not one of the allowed uneven-bottom shapes")
        if not _shape_has_uneven_bottom(cells):
            reasons.append(f"object {index} has a flat bottom and hides whole-object motion")
        columns = {c for _, c in cells}
        if seen_columns & columns:
            reasons.append("two objects share a column lane")
        seen_columns |= columns
        gap = h - 1 - max(r for r, _ in cells)
        gaps.append(gap)
        color_gaps[color].append(gap)
        if gap <= 0:
            reasons.append(f"object {index} already touches the floor")
        if color == 0:
            reasons.append(f"object {index} uses the background color")
    if len(gaps) != len(set(gaps)):
        reasons.append("objects must require distinct downward offsets")
    expected_palette = 4 if len(objs) == 7 else 3
    if len(color_gaps) != expected_palette:
        reasons.append(f"scene must expose exactly {expected_palette} object colors")
    if not any(len(values) >= 2 and len(set(values)) >= 2 for values in color_gaps.values()):
        reasons.append("same-color objects at different heights are required")
    if objs and _apply(grid) == grid:
        reasons.append("scene must fire the motion rule")
    return sorted(set(reasons))


def _whole_object_witness(grid):
    return _rival_per_cell_gravity(grid) != _apply(grid)


def _independent_offset_witness(grid):
    return _rival_global_shift(grid) != _apply(grid)


def _same_color_independence_witness(grid):
    return _rival_color_group_shift(grid) != _apply(grid)


def _all_objects_move_witness(grid):
    return _rival_move_largest_only(grid) != _apply(grid)


SEMANTIC_WITNESSES = {
    "whole_object_not_per_cell_gravity": _whole_object_witness,
    "object_specific_offsets_not_global_shift": _independent_offset_witness,
    "same_color_objects_move_independently": _same_color_independence_witness,
    "every_object_moves_not_largest_only": _all_objects_move_witness,
}
SEMANTIC_RIVALS = {
    "per_cell_gravity": _rival_per_cell_gravity,
    "global_foreground_shift": _rival_global_shift,
    "same_color_group_shift": _rival_color_group_shift,
    "move_largest_only": _rival_move_largest_only,
}
WITNESS_RIVALS = {
    "whole_object_not_per_cell_gravity": ["per_cell_gravity"],
    "object_specific_offsets_not_global_shift": ["global_foreground_shift"],
    "same_color_objects_move_independently": ["same_color_group_shift"],
    "every_object_moves_not_largest_only": ["move_largest_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject any lesson for which a named wrong rule survives every demo."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]
    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the grammar: {grammar[0]}")
            continue
        if _apply(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output is not rigid whole-object gravity")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            query_agrees = rival(query["input"]) == query["output"]
            suffix = "and also matches the query" if query_agrees else "but disagrees on the query"
            reasons.append(f"competitor {name} fits every demonstration {suffix}")
    return sorted(set(reasons))


def generate_task(seed, *, difficulty="medium"):
    if difficulty not in _BAND_CONFIG:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    config = _BAND_CONFIG[difficulty]
    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
    )
    palette = list(
        ctx.draw_distinct_colors(
            "palette", n=config["palette"], exclude=[0]
        )
    )
    dimension_offset = ctx.draw_int("dimension_offset", 0, len(config["dims"]) - 1)
    color_offset = ctx.draw_int("color_offset", 0, len(palette) - 1)
    shape_offset = ctx.draw_int("shape_offset", 0, len(_SHAPES) - 1)
    gap_order = list(range(1, config["objects"] + 1))
    ctx.draw_rng("gap_order").shuffle(gap_order)

    total_pairs = config["train"] + config["test"]
    pairs = []
    for pair_index in range(total_pairs):
        h, w = config["dims"][(dimension_offset + pair_index) % len(config["dims"])]
        gin = _build_input(
            ctx,
            pair_index,
            h=h,
            w=w,
            palette=palette,
            object_count=config["objects"],
            gap_order=gap_order,
            color_offset=color_offset,
            shape_offset=shape_offset,
        )
        pairs.append({"input": gin, "output": _apply(gin)})

    task = {
        "train": pairs[: config["train"]],
        "test": pairs[config["train"] :],
        "program": PROGRAM,
        "chain": ["objects", "move_to_wall_down", "whole_object"],
        "meta": {
            "difficulty": difficulty,
            "palette": palette,
            "background": 0,
            "object_count": config["objects"],
            "n_train": config["train"],
            "n_test": config["test"],
            "version": VERSION,
            "rule_hash": RULE_HASH,
        },
    }
    findings = self_check_task(task)
    if findings:
        raise AssertionError(f"generated task failed self_check_task: {findings[:3]}")
    return task


def self_check_task(task):
    """Validate lesson structure, semantics, and shortcut counterexamples."""
    if not isinstance(task, dict):
        return ["task must be a dict"]
    reasons = []
    meta = task.get("meta") or {}
    difficulty = meta.get("difficulty")
    config = _BAND_CONFIG.get(difficulty)
    train = task.get("train") or []
    test = task.get("test") or []

    if config is None:
        reasons.append("meta.difficulty must be easy, medium, or hard")
        config = {"train": -1, "test": -1, "objects": -1, "palette": -1, "dims": ()}
    if task.get("program") != PROGRAM:
        reasons.append("task program must equal the selected PROGRAM authority")
    if task.get("chain") != ["objects", "move_to_wall_down", "whole_object"]:
        reasons.append("task chain must name rigid whole-object downward motion")
    if meta.get("version") != VERSION:
        reasons.append("meta.version does not match VERSION")
    if meta.get("rule_hash") != RULE_HASH:
        reasons.append("meta.rule_hash does not match RULE_HASH")
    if meta.get("background") != 0:
        reasons.append("meta.background must be black")
    palette = meta.get("palette")
    if not isinstance(palette, list) or len(palette) != config["palette"]:
        reasons.append("meta.palette has the wrong size for the difficulty")
        palette = []
    elif len(set(palette)) != len(palette) or 0 in palette or any(not 1 <= c <= 9 for c in palette):
        reasons.append("meta.palette must be distinct nonzero ARC colors")
    if meta.get("object_count") != config["objects"]:
        reasons.append("meta.object_count disagrees with the difficulty profile")
    if len(train) != config["train"] or meta.get("n_train") != config["train"]:
        reasons.append("train pair count disagrees with the difficulty profile")
    if len(test) != config["test"] or meta.get("n_test") != config["test"]:
        reasons.append("test pair count disagrees with the difficulty profile")

    seen_inputs = set()
    train_dims = set()
    train_drop_sequences = set()
    for split_name, split in (("train", train), ("test", test)):
        for pair_index, pair in enumerate(split):
            label = f"{split_name}[{pair_index}]"
            if not isinstance(pair, dict):
                reasons.append(f"{label} must be a dict")
                continue
            gin, gout = pair.get("input"), pair.get("output")
            grammar = strict_canonical_like(gin)
            if grammar:
                reasons.extend(f"{label}: {reason}" for reason in grammar)
                continue
            if not isinstance(gout, list) or not gout or len(gout) != len(gin) \
                    or any(len(row) != len(gin[0]) for row in gout):
                reasons.append(f"{label}: output must match input dimensions")
                continue
            h, w = len(gin), len(gin[0])
            if not _grid_profile(difficulty, h, w, len(components(gin, bg=0))):
                reasons.append(f"{label}: dimensions/object count disagree with difficulty")
            key = tuple(tuple(row) for row in gin)
            if key in seen_inputs:
                reasons.append(f"{label}: duplicate input grid within the lesson")
            seen_inputs.add(key)
            expected = _apply(gin)
            if gout != expected:
                reasons.append(f"{label}: output is not rigid whole-object gravity")
                continue
            if gin == gout:
                reasons.append(f"{label}: transformation is a no-op")
            if _object_signatures(gin) != _object_signatures(gout):
                reasons.append(f"{label}: object colors or normalized shapes changed")
            if any(max(r for r, _ in cells) != h - 1 for _, cells in components(gout, bg=0)):
                reasons.append(f"{label}: every output object must touch the floor")
            if set(color for color, _ in components(gin, bg=0)) != set(palette):
                reasons.append(f"{label}: observable object colors disagree with meta.palette")
            for name, witness in SEMANTIC_WITNESSES.items():
                if not witness(gin):
                    reasons.append(f"{label}: missing semantic witness {name}")
            for name, rival in SEMANTIC_RIVALS.items():
                if rival(gin) == gout:
                    reasons.append(f"{label}: rival {name} survives")
            if split_name == "train":
                train_dims.add((h, w))
                train_drop_sequences.add(_drop_sequence(gin))

    if len(train_dims) < 2:
        reasons.append("train split must vary grid dimensions")
    if len(train_drop_sequences) < 2:
        reasons.append("train split must vary the left-to-right object offsets")
    for query_index, query in enumerate(test):
        reasons.extend(
            f"test[{query_index}] lesson not identifiable: {reason}"
            for reason in lesson_identifiable(train, query)
        )
    return sorted(set(reasons))


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
