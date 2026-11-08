"""gen1: KEEP ONLY THE LARGEST object, erase every other object.

Transform: among the same-color 4-connected components on a dense field, find
the one with the most cells (``pick-max objs obj-size``) and erase the cells of
all the others. Every generated pair contains a unique largest object plus
smaller counterexamples that rule out position, color-mass, and bounding-box
shortcuts.

Selection concept: keep the single object that maximizes cell count.
"""
from __future__ import annotations

import hashlib
from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_select import (
    parity_check,
    measure,
    py_objects,
    erase_objects,
    make_blob,
    place_shapes,
)

VERSION = "1.2.0"
TASK_ID = "generic_dense_select_gen1"
SUMMARY = "Keep only the unique 4-connected object with the greatest cell count."
INVARIANTS = (
    "the modal nonzero color is background",
    "there is exactly one largest object by cell count",
    "every smaller object is erased to background",
    "a same-color decoy refutes color-mass/color-echo shortcuts",
    "a smaller object with a larger bounding box refutes bbox-area selection",
    "the winner is neither first nor last in row-major object order",
)

# The executable rule has one task-specific literal (the sampled background).
# Hash the normalized template so any semantic rule edit invalidates evidence
# while preserving the lawful per-task background specialization.
RULE_TEMPLATE = (
    "(rule! (lambda (g) "
    "(let* ((bg {bg}) (objs (objects g bg)) "
    "(keep (pick-max objs obj-size))) "
    "(foldl (lambda (o acc) "
    "(if (eq? o keep) acc (erase-cells acc (obj-cells o) bg))) "
    "g objs))))"
)
RULE_HASH = hashlib.sha256(RULE_TEMPLATE.encode("utf-8")).hexdigest()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _program_for(bg: int) -> str:
    return RULE_TEMPLATE.format(bg=bg)


def _counts_for(difficulty):
    if difficulty == "easy":
        return (6, 8)
    if difficulty == "hard":
        return (10, 13)
    return (8, 11)  # medium: number of distractor blobs


def _grid_bounds_for(difficulty):
    if difficulty == "easy":
        return (16, 18)
    if difficulty == "hard":
        return (20, 22)
    return (18, 20)


def _bbox_area(obj) -> int:
    rs = [r for r, _ in obj["cells"]]
    cs = [c for _, c in obj["cells"]]
    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def _transform_shape(cells, code):
    """Apply one of eight dihedral transforms and normalize to the origin."""
    pts = [(int(r), int(c)) for r, c in cells]
    if code >= 4:
        pts = [(r, -c) for r, c in pts]
    for _ in range(code % 4):
        pts = [(c, -r) for r, c in pts]
    r0 = min(r for r, _ in pts)
    c0 = min(c for _, c in pts)
    return sorted([[r - r0, c - c0] for r, c in pts])


def _compact_winner(rng, size):
    """Connected 10..15-cell winner with bbox area at most 15."""
    width = 4 if size <= 12 else 5
    cells = [(r, c) for r in range(3) for c in range(width)][:size]
    return _transform_shape(cells, rng.randrange(8))


def _bbox_decoy(rng):
    """Eight connected cells spanning a 5x4 bbox (area 20)."""
    cells = [
        (0, 0), (1, 0), (2, 0), (3, 0),
        (4, 0), (4, 1), (4, 2), (4, 3),
    ]
    return _transform_shape(cells, rng.randrange(8))


def _apply(g, bg=0):
    """Keep only the largest object by cell count; erase the rest.

    ``pick-max`` is stable: a malformed tie keeps the earliest row-major object.
    Generated lessons never contain a tie, but matching that fallback keeps the
    Python mirror byte-exact with the Racket authority on adversarial inputs.
    """
    objs = py_objects(g, bg=bg)
    if not objs:
        return [row[:] for row in g]
    best = max(o["size"] for o in objs)
    keep = next(o for o in objs if o["size"] == best)
    return erase_objects(g, [o for o in objs if o is not keep], bg=bg)


def _infer_bg(grid):
    if not isinstance(grid, list) or not grid:
        return None
    if any(not isinstance(row, list) or not row for row in grid):
        return None
    if len({len(row) for row in grid}) != 1:
        return None
    counts = Counter(v for row in grid for v in row)
    if not counts:
        return None
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return top[0][0]


def _winner_context(grid):
    bg = _infer_bg(grid)
    if bg is None:
        return None
    objs = py_objects(grid, bg=bg)
    if not objs:
        return None
    best = max(o["size"] for o in objs)
    winners = [o for o in objs if o["size"] == best]
    if len(winners) != 1:
        return None
    keep = winners[0]
    return bg, objs, keep, objs.index(keep)


def _has_same_color_decoy(grid) -> bool:
    ctx = _winner_context(grid)
    return bool(
        ctx
        and any(o is not ctx[2] and o["color"] == ctx[2]["color"] for o in ctx[1])
    )


def _has_bbox_area_decoy(grid) -> bool:
    ctx = _winner_context(grid)
    return bool(
        ctx
        and any(o is not ctx[2] and _bbox_area(o) > _bbox_area(ctx[2]) for o in ctx[1])
    )


def _winner_not_first(grid) -> bool:
    ctx = _winner_context(grid)
    return bool(ctx and ctx[3] > 0)


def _winner_not_last(grid) -> bool:
    ctx = _winner_context(grid)
    return bool(ctx and ctx[3] < len(ctx[1]) - 1)


def strict_canonical_like(grid):
    """Return reasons when a grid falls outside this generator's lesson grammar."""
    reasons = []
    bg = _infer_bg(grid)
    if bg is None:
        return ["grid must be nonempty, rectangular, with a unique modal background"]
    h, w = len(grid), len(grid[0])
    if not (16 <= h <= 22 and 16 <= w <= 22):
        reasons.append("grid dimensions must each be in 16..22")
    if not isinstance(bg, int) or isinstance(bg, bool) or not (1 <= bg <= 9):
        reasons.append("background must be a nonzero ARC color")
    area = h * w
    if sum(v == bg for row in grid for v in row) <= area // 2:
        reasons.append("background must occupy more than half the grid")

    objs = py_objects(grid, bg=bg)
    if not (7 <= len(objs) <= 14):
        reasons.append("input must contain 7..14 isolated objects")
    if objs:
        sizes = [o["size"] for o in objs]
        best = max(sizes)
        if sizes.count(best) != 1:
            reasons.append("largest object must be unique by cell count")
        if not (10 <= best <= 15):
            reasons.append("winner size must be in 10..15")
        if any(not (3 <= size <= 8) for size in sizes if size != best):
            reasons.append("every distractor must have size 3..8")
        if not (4 <= len({o["color"] for o in objs}) <= 6):
            reasons.append("input must use 4..6 object colors")
    if not _has_same_color_decoy(grid):
        reasons.append("missing smaller same-color decoy")
    if not _has_bbox_area_decoy(grid):
        reasons.append("missing smaller object with larger bbox area")
    if not _winner_not_first(grid):
        reasons.append("winner must not be first in row-major object order")
    if not _winner_not_last(grid):
        reasons.append("winner must not be last in row-major object order")
    return reasons


def _keep_selected(grid, selector):
    bg = _infer_bg(grid)
    if bg is None:
        return [row[:] for row in grid]
    objs = py_objects(grid, bg=bg)
    if not objs:
        return [row[:] for row in grid]
    selected = selector(objs)
    if not isinstance(selected, list):
        selected = [selected]
    selected_ids = {id(o) for o in selected}
    return erase_objects(grid, [o for o in objs if id(o) not in selected_ids], bg=bg)


def _rival_keep_first(grid):
    return _keep_selected(grid, lambda objs: objs[0])


def _rival_keep_last(grid):
    return _keep_selected(grid, lambda objs: objs[-1])


def _rival_keep_largest_bbox(grid):
    return _keep_selected(
        grid,
        lambda objs: next(o for o in objs if _bbox_area(o) == max(_bbox_area(x) for x in objs)),
    )


def _rival_keep_largest_color_mass(grid):
    def select(objs):
        totals = Counter()
        for obj in objs:
            totals[obj["color"]] += obj["size"]
        largest = max(totals.values())
        color = next(obj["color"] for obj in objs if totals[obj["color"]] == largest)
        return [obj for obj in objs if obj["color"] == color]
    return _keep_selected(grid, select)


SEMANTIC_WITNESSES = {
    "same_color_decoy": _has_same_color_decoy,
    "bbox_area_decoy": _has_bbox_area_decoy,
    "winner_not_first": _winner_not_first,
    "winner_not_last": _winner_not_last,
}
SEMANTIC_RIVALS = {
    "keep_first": _rival_keep_first,
    "keep_last": _rival_keep_last,
    "keep_largest_bbox": _rival_keep_largest_bbox,
    "keep_largest_color_mass": _rival_keep_largest_color_mass,
}
WITNESS_RIVALS = {
    "same_color_decoy": ["keep_largest_color_mass"],
    "bbox_area_decoy": ["keep_largest_bbox"],
    "winner_not_first": ["keep_first"],
    "winner_not_last": ["keep_last"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject lessons in which a named wrong rule survives every demo."""
    reasons = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the grammar: {grammar[0]}")
            continue
        bg = _infer_bg(pair["input"])
        if _apply(pair["input"], bg=bg) != pair["output"]:
            reasons.append(f"pair {index} output is not the largest-by-cell-count result")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits:
            query_agrees = rival(query["input"]) == query["output"]
            suffix = "and also matches the query" if query_agrees else "but disagrees on the query"
            reasons.append(f"competitor {name} fits every demonstration {suffix}")
    return reasons


def _build_input(ctx, idx, palette, n_distractors, *, big_size, big_color, bg=0):
    lo, hi = _grid_bounds_for(ctx.difficulty)
    gh = ctx.draw_int(f"gh_{idx}", lo, hi)
    gw = ctx.draw_int(f"gw_{idx}", lo, hi)
    big_color_index = palette.index(big_color)

    # Retry the complete placement deterministically until the winner is in the
    # middle of row-major order. This makes first/last-position rivals false on
    # every pair rather than merely unlikely at the task level.
    for attempt in range(96):
        rng = ctx.draw_rng(f"input_{idx}_attempt_{attempt}")
        shapes_colors = [
            (_compact_winner(rng, big_size), big_color),
            (_bbox_decoy(rng), big_color),
        ]
        # Cycle through the remaining palette so every declared object color is
        # visible in every pair; shape and placement still vary by seed.
        for j in range(n_distractors - 1):
            size = rng.randint(3, 8)
            color = palette[(big_color_index + 1 + j) % len(palette)]
            shapes_colors.append((make_blob(rng, size), color))

        grid, placed = place_shapes(
            rng, gh, gw, shapes_colors, tries=800, bg=bg
        )
        if placed != len(shapes_colors):
            continue
        ctx_out = _winner_context(grid)
        if ctx_out is None:
            continue
        _, objs, keep, winner_index = ctx_out
        if keep["size"] != big_size or keep["color"] != big_color:
            continue
        if winner_index in (0, len(objs) - 1):
            continue
        if not _has_same_color_decoy(grid) or not _has_bbox_area_decoy(grid):
            continue
        return grid
    raise RuntimeError(f"could not place identifiable dense-select scene for pair {idx}")


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
    )
    n_lo, n_hi = _counts_for(difficulty)

    bg = ctx.draw_color("bg_color", exclude=[0])
    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0, bg]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    size_offset = ctx.draw_int("winner_size_offset", 0, 5)
    color_offset = ctx.draw_int("winner_color_offset", 0, n_pal - 1)

    pairs = []
    for idx in range(n_train + n_test):
        n_d = ctx.draw_int(f"n_distractors_{idx}", n_lo, n_hi)
        big_size = 10 + ((size_offset + idx) % 6)
        big_color = palette[(color_offset + idx) % n_pal]
        gin = _build_input(
            ctx,
            idx,
            palette,
            n_d,
            big_size=big_size,
            big_color=big_color,
            bg=bg,
        )
        gout = _apply(gin, bg=bg)
        pairs.append({"input": gin, "output": gout})

    task = {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": _program_for(bg),
        "chain": ["objects", "pick_max_size", "erase_others"],
        "meta": {
            "difficulty": difficulty,
            "palette": palette,
            "bg_color": bg,
            "version": VERSION,
            "rule_hash": RULE_HASH,
            "n_train": n_train,
            "n_test": n_test,
        },
    }
    errors = self_check_task(task)
    if errors:
        raise AssertionError(f"generated task failed self_check_task: {errors[:3]}")
    return task


def self_check_task(task):
    """Validate the complete lesson without mutating it."""
    errors = []
    if not isinstance(task, dict):
        return ["task must be a dict"]
    meta = task.get("meta") or {}
    bg = meta.get("bg_color")
    palette = meta.get("palette")
    train = task.get("train") or []
    test = task.get("test") or []

    if not isinstance(bg, int) or isinstance(bg, bool) or not (1 <= bg <= 9):
        errors.append("meta.bg_color must be a nonzero ARC color")
    if not isinstance(palette, list) or not (4 <= len(palette) <= 6):
        errors.append("meta.palette must contain 4..6 colors")
        palette = []
    elif len(set(palette)) != len(palette) or bg in palette or 0 in palette:
        errors.append("meta.palette must be distinct and exclude background/zero")
    if meta.get("version") != VERSION:
        errors.append("meta.version does not match generator VERSION")
    if meta.get("rule_hash") != RULE_HASH:
        errors.append("meta.rule_hash does not match RULE_HASH")
    if len(train) != meta.get("n_train") or not (3 <= len(train) <= 4):
        errors.append("train pair count does not match meta.n_train in 3..4")
    if len(test) != meta.get("n_test") or not (1 <= len(test) <= 2):
        errors.append("test pair count does not match meta.n_test in 1..2")
    if task.get("program") != _program_for(bg) if isinstance(bg, int) else True:
        errors.append("program does not match the selected background-specialized rule")
    if task.get("chain") != ["objects", "pick_max_size", "erase_others"]:
        errors.append("chain must name objects -> pick_max_size -> erase_others")

    seen_inputs = set()
    train_colors = set()
    train_sizes = set()
    for split_name, split in (("train", train), ("test", test)):
        for pair_index, pair in enumerate(split):
            label = f"{split_name}[{pair_index}]"
            if not isinstance(pair, dict):
                errors.append(f"{label}: pair must be a dict")
                continue
            gin = pair.get("input")
            gout = pair.get("output")
            if _infer_bg(gin) is None:
                errors.append(f"{label}: input must be a nonempty rectangular grid")
                continue
            key = tuple(tuple(row) for row in gin)
            if key in seen_inputs:
                errors.append(f"{label}: duplicate input grid within lesson")
            seen_inputs.add(key)
            if _infer_bg(gout) is None:
                errors.append(f"{label}: output must be a nonempty rectangular grid")
                continue
            if len(gin) != len(gout) or len(gin[0]) != len(gout[0]):
                errors.append(f"{label}: input and output dimensions must match")
                continue

            grammar = strict_canonical_like(gin)
            if grammar:
                errors.extend(f"{label}: {reason}" for reason in grammar)
                continue
            if _infer_bg(gin) != bg:
                errors.append(f"{label}: modal background disagrees with meta.bg_color")
            objs = py_objects(gin, bg=bg)
            if set(o["color"] for o in objs) != set(palette):
                errors.append(f"{label}: observable object colors disagree with meta.palette")
            expected = _apply(gin, bg=bg)
            if expected != gout:
                errors.append(f"{label}: output is not exact largest-by-cell-count selection")
                continue
            out_objs = py_objects(gout, bg=bg)
            if len(out_objs) != 1:
                errors.append(f"{label}: output must contain exactly one object")
            winner = max(objs, key=lambda obj: obj["size"])
            if split_name == "train":
                train_colors.add(winner["color"])
                train_sizes.add(winner["size"])

    if len(train_colors) < 2:
        errors.append("train split must vary the winning object color")
    if len(train_sizes) < 2:
        errors.append("train split must vary the winning object size")
    for index, query in enumerate(test):
        for reason in lesson_identifiable(train, query):
            errors.append(f"test[{index}] lesson not identifiable: {reason}")
    return sorted(set(errors))


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)
