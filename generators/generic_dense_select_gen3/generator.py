"""gen3: KEEP ONLY THE ODD-ONE-OUT shape, erase the repeated ones.

Transform: the field holds several identical copies of one base shape (varied
colors) plus exactly one object of a DIFFERENT shape. `pick-unique` with
`same-shape?` returns that lone object — the one whose shape-equivalence class
is a singleton — and we erase every other object, leaving only the odd one.

Selection concept: keep the unique object that differs from all the rest.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_select import (
    parity_check, measure, py_objects, erase_objects, norm_shape,
    make_blob, place_shapes,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_select_gen3"


def _copies_for(difficulty):
    if difficulty == "easy":
        return (5, 7)
    if difficulty == "hard":
        return (9, 12)
    return (6, 10)             # medium: number of base-shape copies


def _pick_unique(objs):
    """Mirror `(pick-unique objs same-shape?)`: among objects, return the first
    (row-major order) whose shape-equivalence class has exactly one member, or
    None. same-shape? is color-blind and rotation-sensitive (translation-only
    normalization)."""
    if len(objs) < 2:
        return None
    shapes = [norm_shape(o["cells"]) for o in objs]
    singletons = [o for o, s in zip(objs, shapes) if shapes.count(s) == 1]
    return singletons[0] if singletons else None


def _apply(g, bg=0):
    objs = py_objects(g, bg=bg)
    keep = _pick_unique(objs)
    if keep is None:
        return [row[:] for row in g]
    return erase_objects(g, [o for o in objs if o is not keep], bg=bg)


def _build_input(ctx, idx, palette, n_copies, bg=0):
    rng = ctx.draw_rng(f"input_{idx}")
    gh = ctx.draw_int(f"gh_{idx}", 16, 22)
    gw = ctx.draw_int(f"gw_{idx}", 16, 22)

    # base shape (all copies identical orientation -> same normalized shape)
    base_size = rng.randint(4, 8)
    base = make_blob(rng, base_size)
    # odd shape: a DIFFERENT size guarantees a different normalized shape,
    # so it is the only shape-singleton.
    odd_choices = [s for s in range(3, 13) if s != base_size]
    odd_size = rng.choice(odd_choices)
    odd = make_blob(rng, odd_size)

    # Odd shape FIRST so it always places into the emptiest grid (it is the
    # singleton the rule keeps); base copies follow. Positions are random, so
    # final row-major object order and layout still vary freely per seed.
    shapes_colors = [(odd, rng.choice(palette))]
    shapes_colors += [(base, rng.choice(palette)) for _ in range(n_copies)]

    g, _placed = place_shapes(rng, gh, gw, shapes_colors, bg=bg)
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    c_lo, c_hi = _copies_for(difficulty)

    # Nonzero modal background is part of the corrected eval target. The rule is
    # still the same odd-one-out selection; only the background value changes, and
    # it is threaded through objects/erase-cells so bg cells are not mistaken for
    # objects.
    bg = ctx.draw_color("bg_color", exclude=[0])
    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0, bg]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = ("(rule! (lambda (g) "
               f"(let* ((bg {bg}) (objs (objects g bg)) (keep (pick-unique objs same-shape?))) "
               "(foldl (lambda (o acc) "
               "(if (eq? o keep) acc (erase-cells acc (obj-cells o) bg))) "
               "g objs))))")

    pairs = []
    for idx in range(n_train + n_test):
        n_copies = ctx.draw_int(f"n_copies_{idx}", c_lo, c_hi)
        gin = _build_input(ctx, idx, palette, n_copies, bg=bg)
        gout = _apply(gin, bg=bg)
        # exactly one singleton must exist and survive as a non-empty output
        objs = py_objects(gin, bg=bg)
        assert _pick_unique(objs) is not None, f"gen3 seed pair {idx}: no odd-one-out"
        assert gout != gin, f"gen3 seed pair {idx}: nothing removed"
        assert any(v != 0 for row in gout for v in row), "gen3: empty output"
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["objects", "pick_unique_shape", "erase_others"],
        "meta": {"difficulty": difficulty, "palette": palette,
                 "bg_color": bg, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)
