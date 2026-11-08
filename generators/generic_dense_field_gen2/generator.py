"""gen2: MIRROR a fully-colored grid left<->right.

Transform: `(flip-lr g)` — reflect the dense field horizontally. The input is a
100%-filled grid of a few large contiguous color regions; the output is its
mirror. Teaches a geometric transform on a DENSE field (models routinely fail
geometry once the grid is fully colored rather than sparse).

Density concept: same high-fill / low-component envelope as gen1.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.dense_field import (
    parity_check, measure, make_dense_partition,
)

VERSION = "1.1.0"
TASK_ID = "generic_dense_field_gen2"


def _size_for(difficulty):
    if difficulty == "easy":
        return (12, 18)
    if difficulty == "hard":
        return (22, 29)
    return (16, 24)


def _apply(g):
    """Mirror `(flip-lr g)`: reverse each row."""
    return [row[::-1] for row in g]


def _colors(g):
    return {v for row in g for v in row}


def _is_lr_symmetric(g):
    return all(row == row[::-1] for row in g)


def _force_lr_asymmetry(g, palette):
    """Keep the dense-field envelope while making flip-lr visibly nontrivial."""
    out = [row[:] for row in g]
    left = palette[0]
    right = next(c for c in palette if c != left)
    for row in out:
        row[0] = left
        row[-1] = right
    return out


def _make_nontrivial_input(rng, gh, gw, palette):
    """Resample a dense partition until flip-lr actually changes it.

    An already-LR-symmetric dense field flips to itself, so the pair becomes a
    no-op that teaches nothing about the mirror transform. Resample a few times,
    then force a left/right color difference as a deterministic fallback.
    """
    for _ in range(8):
        gin = make_dense_partition(rng, gh, gw, palette)
        if len(_colors(gin)) >= 2 and not _is_lr_symmetric(gin):
            return gin
    return _force_lr_asymmetry(gin, palette)


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    slo, shi = _size_for(difficulty)

    n_pal = ctx.draw_int("n_palette", 4, 6)
    palette = list(ctx.draw_distinct_colors("palette", n=n_pal, exclude=[0]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = "(rule! (lambda (g) (flip-lr g)))"

    pairs = []
    for idx in range(n_train + n_test):
        r = ctx.draw_rng(f"input_{idx}")
        gh = ctx.draw_int(f"gh_{idx}", slo, shi)
        gw = ctx.draw_int(f"gw_{idx}", slo, shi)
        gin = _make_nontrivial_input(r, gh, gw, palette)
        pairs.append({"input": gin, "output": _apply(gin)})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["flip_lr"],
        "meta": {"difficulty": difficulty, "palette": palette,
                 "forced_asymmetry_guard": True, "version": VERSION},
    }


def self_check_task(task) -> list[str]:
    """Executable invariants for the dense-field left/right mirror concept."""
    errors = []
    pairs = list(task.get("train") or []) + list(task.get("test") or [])
    if not pairs:
        return ["task has no train/test pairs"]
    if task.get("program") != "(rule! (lambda (g) (flip-lr g)))":
        errors.append("program is not the flip-lr rule")
    for i, pair in enumerate(pairs):
        gin = pair.get("input")
        gout = pair.get("output")
        if not gin or not gout or len(gin) != len(gout) or len(gin[0]) != len(gout[0]):
            errors.append(f"pair {i}: malformed or dimension-changing grid")
            continue
        if any(v == 0 for row in gin for v in row):
            errors.append(f"pair {i}: dense-field input contains zero/background cells")
        if len(_colors(gin)) < 2:
            errors.append(f"pair {i}: input uses fewer than two colors")
        if _is_lr_symmetric(gin):
            errors.append(f"pair {i}: input is already left/right symmetric, making flip a no-op")
        if gout != _apply(gin):
            errors.append(f"pair {i}: output is not exactly flip-lr(input)")
    return errors


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
    measure(generate_task, n=25)
