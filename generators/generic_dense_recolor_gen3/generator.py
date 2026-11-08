"""gen3: per-object recolor by EXACT CELL-COUNT (size -> colour map).

Transform: a fixed mapping size->colour is applied to every object —
all 4-cell objects become one colour, all 5-cell objects another, etc.
Objects of the same area end up the same colour regardless of shape or
position. Input objects share ONE neutral colour, so the rule is
"count each blob's cells and look the colour up".

Racket: foldl over (objects g); per object a cond on (obj-size o)
selecting the mapped colour; recolor-cells repaints. Order-independent.

Generation only ever uses sizes present in the map, so every object is
covered (the cond `else` is a safety fallback that is never reached).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_recolor import (
    components, random_blob, place_shapes, parity_and_stats,
)

VERSION = "1.2.0"  # ensure every size->color clause is demonstrated; add self_check_task
TASK_ID = "generic_dense_recolor_gen3"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (16, 18), (6, 7)
    if difficulty == "hard":
        return (20, 22), (9, 12)
    return (17, 21), (7, 10)           # medium (object count)


def _apply(g, size_color, default_c, bg=0):
    out = [row[:] for row in g]
    for _, cells in components(g, bg=bg):
        color = size_color.get(len(cells), default_c)
        for r, c in cells:
            out[r][c] = color
    return out


def _build_input(ctx, idx, in_color, sizes, n_obj, gh, gw, bg=0):
    rng = ctx.draw_rng(f"input_{idx}")
    # Include every mapped size in every pair; otherwise a cond branch can be
    # present in the target program but never taught by train examples.
    for _attempt in range(30):
        chosen = list(sizes) + [rng.choice(sizes) for _ in range(max(0, n_obj - len(sizes)))]
        rng.shuffle(chosen)
        shapes = [random_blob(rng, s) for s in chosen]
        grid, placed = place_shapes(rng, gh, gw, shapes, in_color)
        present = {len(cells) for _, cells in components(grid, bg=0)}
        if set(sizes).issubset(present):
            if bg != 0:
                grid = [[bg if v == 0 else v for v in row] for row in grid]
            return grid, placed
    # Fall through with the best last attempt; the task-level self-check will
    # fail loudly if coverage is still absent.
    if bg != 0:
        grid = [[bg if v == 0 else v for v in row] for row in grid]
    return grid, placed


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), (nlo, nhi) = _dims_for(difficulty)

    n_sizes = ctx.draw_int("n_sizes", 3, 4)
    # the mapped sizes (distinct) + colours: 1 neutral input + n_sizes outputs.
    # As in gen2, expose modal background as a real axis and pass it through the
    # program; otherwise this family remains a zero-background-only corner.
    use_nonzero_bg = ctx.draw_int("bg_axis", 0, 2) > 0
    bg = ctx.draw_color("bg", exclude=[0]) if use_nonzero_bg else 0
    pal = ctx.draw_distinct_colors("palette", n=n_sizes + 1, exclude=[0, bg])
    in_color = pal[0]
    out_colors = list(pal[1:])
    sizes = sorted(ctx.draw_rng("sizes").sample(range(3, 11), n_sizes))
    size_color = {s: c for s, c in zip(sizes, out_colors)}
    default_c = out_colors[0]

    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    n_obj = ctx.draw_int("n_obj", nlo, nhi)

    cond_clauses = " ".join(
        f"((= s {s}) {size_color[s]})" for s in sizes)
    program = (
        "(rule! (lambda (g) "
        "(foldl (lambda (o acc) "
        "(let ((s (obj-size o))) "
        "(recolor-cells acc (obj-cells o) "
        f"(cond {cond_clauses} (else {default_c}))))) g (objects g {bg}))))"
    )

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin, placed = _build_input(ctx, idx, in_color, sizes, n_obj, gh, gw, bg=bg)
        assert placed >= 6, f"only {placed} objects placed"
        gout = _apply(gin, size_color, default_c, bg=bg)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["objects", "recolor_by_size_map"],
        "meta": {"difficulty": difficulty, "bg": bg, "nonzero_bg": bool(bg),
                 "in_color": in_color, "size_color": size_color, "version": VERSION},
    }


def self_check_task(task) -> list[str]:
    errs = []
    meta = task.get("meta", {})
    bg = int(meta.get("bg", 0))
    mapped = {int(s) for s in meta.get("size_color", {}).keys()}
    if not mapped:
        errs.append("empty size->color map")
        return errs
    train_sizes = set()
    all_sizes = set()
    for split in ("train", "test"):
        for pair in task.get(split, []):
            sizes = {len(cells) for _, cells in components(pair["input"], bg=bg)}
            all_sizes.update(sizes)
            if split == "train":
                train_sizes.update(sizes)
            missing_pair = mapped - sizes
            if missing_pair:
                errs.append(f"{split} pair missing mapped sizes {sorted(missing_pair)}")
                return errs
    if mapped - train_sizes:
        errs.append(f"train split does not exercise mapped sizes {sorted(mapped - train_sizes)}")
    if mapped - all_sizes:
        errs.append(f"task does not exercise mapped sizes {sorted(mapped - all_sizes)}")
    return errs


if __name__ == "__main__":
    parity_and_stats(generate_task, n=25, version_label=VERSION)
