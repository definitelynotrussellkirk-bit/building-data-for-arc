"""Color/palette utilities."""
from __future__ import annotations

import random
from typing import Iterable


def non_bg_colors(bg: int) -> list[int]:
    """All ARC colors except `bg`, sorted ascending."""
    if not (0 <= bg <= 9):
        raise ValueError(f"non_bg_colors: bg {bg} not in 0..9")
    return [c for c in range(10) if c != bg]


def random_palette(
    rng: random.Random, n: int, *,
    bg: int | None = 0, exclude: Iterable[int] = (),
) -> tuple[int, ...]:
    """n distinct ARC colors from 0..9.

    By default `bg=0` is excluded (the common "n non-bg colors" case);
    pass `bg=None` to allow 0, or `bg=5` to exclude a different bg.
    `exclude` is unioned with `{bg}`.

    Replaces the literal `rng.sample([1,2,3,4,5,6,7,8,9], n)` idiom
    that recurs ~30 times across generators. Deterministic for a given
    (seed, label, version) when called via `ctx.draw_rng(label)`."""
    bad: set[int] = {int(x) for x in exclude}
    if bg is not None:
        bad.add(int(bg))
    legal = [c for c in range(10) if c not in bad]
    if n > len(legal):
        raise ValueError(
            f"random_palette: want {n} distinct, only {len(legal)} legal")
    return tuple(rng.sample(legal, n))


def color_name(c: int) -> str:
    """Canonical ARC color name. Useful for diagnostics."""
    return ["black", "blue", "red", "green", "yellow",
            "gray", "magenta", "orange", "cyan", "maroon"][c]
