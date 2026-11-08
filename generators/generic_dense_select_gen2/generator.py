"""gen2: KEEP ONLY THE SOLID SQUARES, erase every non-square object.

Transform: among the same-color 4-connected components on a dense field, keep
those whose cells form a solid N×N block (`square?`) and erase the cells of
every other shape. The input plants a mix of solid 2×2 / 3×3 squares and
irregular non-square blobs of varied colors; the output keeps only the squares.

Selection concept: keep the objects satisfying a shape predicate.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_select import (
    parity_check, measure, py_objects, erase_objects, is_square,
    solid_square, make_nonsquare_blob, place_shapes,
)

VERSION = "1.2.0"  # add task-level executable invariants
TASK_ID = "generic_dense_select_gen2"


def _counts_for(difficulty):
    if difficulty == "easy":
        return (2, 3), (3, 4)
    if difficulty == "hard":
        return (3, 5), (5, 7)
    return (3, 4), (4, 6)      # medium: (n_squares range, n_nonsquares range)


def _apply(g, bg=0):
    """Keep solid squares; erase everything else.

    Mirrors `(let ((objs (objects g bg)))
              (foldl (lambda (o acc) (if (square? o) acc
                       (erase-cells acc (obj-cells o) bg))) g objs))`.
    """
    objs = py_objects(g, bg=bg)
    return erase_objects(g, [o for o in objs if not is_square(o)], bg=bg)


def _build_input(ctx, idx, palette, n_sq, n_non, bg=0):
    rng = ctx.draw_rng(f"input_{idx}")
    gh = ctx.draw_int(f"gh_{idx}", 16, 22)
    gw = ctx.draw_int(f"gw_{idx}", 16, 22)

    shapes_colors = []
    # required squares first (placed into the emptiest grid)
    for _ in range(n_sq):
        n = rng.choice([2, 2, 3])           # 2×2 (4 cells) or 3×3 (9 cells)
        shapes_colors.append((solid_square(n), rng.choice(palette)))
    # required non-squares
    for _ in range(n_non):
        s = rng.randint(3, 8)
        shapes_colors.append((make_nonsquare_blob(rng, s), rng.choice(palette)))

    # interleave so neither class is always last / clustered
    rng.shuffle(shapes_colors)
    g, _placed = place_shapes(rng, gh, gw, shapes_colors, bg=bg)
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (sq_lo, sq_hi), (nn_lo, nn_hi) = _counts_for(difficulty)

    # Make the modal background a real axis. This family previously emitted
    # 0% nonzero-background outputs, even though the corrected eval target is
    # roughly two-thirds nonzero modal backgrounds. Keep object colours distinct
    # from `bg` and pass that bg through both the Python mirror and Racket rule.
    bg = ctx.draw_color("bg_color", exclude=[0])
    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0, bg]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = ("(rule! (lambda (g) "
               f"(let ((bg {bg}) (objs (objects g {bg}))) "
               "(foldl (lambda (o acc) "
               "(if (square? o) acc (erase-cells acc (obj-cells o) bg))) "
               "g objs))))")

    pairs = []
    for idx in range(n_train + n_test):
        n_sq = ctx.draw_int(f"n_sq_{idx}", sq_lo, sq_hi)
        n_non = ctx.draw_int(f"n_non_{idx}", nn_lo, nn_hi)
        gin = _build_input(ctx, idx, palette, n_sq, n_non, bg=bg)
        gout = _apply(gin, bg=bg)
        # discriminator must actually fire and output must survive
        assert gout != gin, f"gen2 seed pair {idx}: no non-square removed"
        assert any(v != 0 for row in gout for v in row), "gen2: empty output"
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["objects", "filter_square", "erase_others"],
        "meta": {"difficulty": difficulty, "palette": palette,
                 "bg_color": bg, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)


def self_check_task(task):
    """Lightweight structural checks for generated dense-select tasks."""
    errs = []
    pairs = task.get("train", []) + task.get("test", [])
    if not pairs:
        return ["task must contain at least one pair"]
    for i, pair in enumerate(pairs):
        inp = pair.get("input")
        out = pair.get("output")
        if not inp or not out:
            errs.append(f"pair {i}: missing input or output grid")
            continue
        if any(len(row) != len(inp[0]) for row in inp) or any(len(row) != len(out[0]) for row in out):
            errs.append(f"pair {i}: ragged grid")
            continue
        if len(out) > len(inp) or len(out[0]) > len(inp[0]):
            errs.append(f"pair {i}: output should be a selected/cropped sub-grid")
        out_vals = {v for row in out for v in row}
        inp_vals = {v for row in inp for v in row}
        if not out_vals <= inp_vals:
            errs.append(f"pair {i}: output introduces colors not present in input")
        if all(v == 0 for row in out for v in row):
            errs.append(f"pair {i}: output is all background")
    return errs
