"""Native row-classification family; labels are claims until Racket replay.

The canonical setting is byte-for-byte unchanged.  The alternative discovers
consecutive uniform-row bands, then keeps every band of maximal length.
Input sampling does not depend on the episode's private rule setting.
"""
from __future__ import annotations

from pathlib import Path
import random


HOME = Path(__file__).resolve().parent
MODES = ("all_uniform", "longest_uniform_run")
QUERY_SHAPES = ((3, 3), (17, 12), (24, 23), (30, 30))


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly one supported mode")
    return settings["mode"]


def _integer(name, value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def program(settings):
    """Return the complete rule! source, preserving the canonical exact bytes."""
    name = "canonical.rkt" if _mode(settings) == "all_uniform" else "longest.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def _validate_grid(grid):
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("grid must have 3..30 rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be a rectangular list of lists")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors 0..9")


def band_intermediate(grid):
    """Input-dependent stage A, retained privately for causal inspection."""
    _validate_grid(grid)
    uniform = [len(set(row)) == 1 for row in grid]
    bands = []
    cursor = 0
    while cursor < len(uniform):
        if not uniform[cursor]:
            cursor += 1
            continue
        start = cursor
        while cursor < len(uniform) and uniform[cursor]:
            cursor += 1
        bands.append({"start": start, "stop": cursor, "length": cursor - start})
    longest = max((band["length"] for band in bands), default=0)
    return {"uniform_rows": uniform, "bands": bands, "maximum_length": longest}


def solve(grid, mode):
    """Independent Python label claim. Native qualification executes Racket."""
    _mode({"mode": mode})
    state = band_intermediate(grid)
    chosen = set()
    for band in state["bands"]:
        if mode == "all_uniform" or band["length"] == state["maximum_length"]:
            chosen.update(range(band["start"], band["stop"]))
    return [[5 if r in chosen else 0] * len(grid[0]) for r in range(len(grid))]


def _rng(seed, stream, index):
    # Separate streams make query prefixes invariant under the demo count and
    # preserve identical inputs across both settings without shared global RNG.
    return random.Random(f"2a5919c40197:parametric-v1:{seed}:{stream}:{index}")


def _anchor(rng):
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    patterns = ((1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), (1, 0, 0))
    mask = rng.choice(patterns)
    grid = []
    for r, uniform in enumerate(mask):
        a, b = palette[r % 3], palette[(r + 1) % 3]
        grid.append([a, a, a] if uniform else [a, b, a])
    return grid


def _mask(lengths, height, rng, *, shuffle=True):
    lengths = list(lengths)
    if shuffle:
        rng.shuffle(lengths)
    extra = height - sum(lengths) - (len(lengths) - 1)
    if extra < 0:
        raise ValueError("band lengths do not fit the requested canvas")
    gaps = [0] + [1] * (len(lengths) - 1) + [0]
    # Boundary contact is frequent, while the remaining mixed rows vary the
    # spacings and supply distractors throughout the actual canvas.
    slots = list(range(1, len(gaps) - 1))
    if rng.randrange(2):
        slots.append(0)
    if rng.randrange(2):
        slots.append(len(gaps) - 1)
    for _ in range(extra):
        gaps[rng.choice(slots)] += 1
    result = [False] * gaps[0]
    for i, length in enumerate(lengths):
        result += [True] * length + [False] * gaps[i + 1]
    return result


def _paint_input(mask, width, rng):
    # Every cell contains content; large cases are not small motifs in padding.
    palette = rng.sample(list(range(10)), rng.randint(4, 8))
    offset = rng.randrange(len(palette))
    bands = []
    start = None
    for r, uniform in enumerate(mask + [False]):
        if uniform and start is None:
            start = r
        if not uniform and start is not None:
            bands.append((start, r))
            start = None
    longest = max(stop - start for start, stop in bands)
    shorter = [(start, stop) for start, stop in bands if 2 <= stop - start < longest]
    same_color = set(range(*rng.choice(shorter))) if shorter else set()
    solid_color = rng.choice(palette)
    rows = []
    mixed_index = 0
    for r, uniform in enumerate(mask):
        a = palette[(offset + r) % len(palette)]
        b = palette[(offset + r + 1) % len(palette)]
        if uniform:
            # Winning bands change color internally. One shorter band uses a
            # single repeated color, distinguishing equal-color grouping under
            # BOTH settings while retaining both types of adjacency.
            row = [solid_color if r in same_color else a] * width
        else:
            kind = mixed_index % 5
            if kind == 0:
                row = [a] * width
                row[rng.randrange(3, width - 1)] = b
            elif kind == 1:
                row = [a] * width
                row[-1] = b
            elif kind == 2:
                row = [a if c % 2 == 0 else b for c in range(width)]
            elif kind == 3:
                cut = rng.randrange(1, width)
                row = [a] * cut + [b] * (width - cut)
            else:
                row = [rng.choice(palette) for _ in range(width)]
                row[0], row[-1] = a, b
            mixed_index += 1
        rows.append(row)
    if rng.randrange(2):
        rows.reverse()
    return rows


def _demo(seed, index):
    rng = _rng(seed, "demo", index)
    if index == 0:
        # Tied maxima and a losing singleton; fixes k>=3 fallback thresholds.
        return _paint_input(_mask([2, 1, 2], 7, rng), 7, rng)
    if index == 1:
        # A unique larger maximum fixes the complementary k=1/2 thresholds.
        # Its losing runner-up occupies 3/10 or 4/12 of this scene, MORE than
        # a winning 2/7 band in demo0. No fixed fraction-of-height threshold
        # can explain both examples. Keep this compact geometry deliberate.
        longest = rng.choice((4, 5))
        lengths = [longest, longest - 1, 1]
        height = sum(lengths) + 2
        return _paint_input(_mask(lengths, height, rng), 9, rng)
    if index == 2:
        return _anchor(rng)
    height = (11, 16, 22)[index - 3]
    width = (6, 15, 21)[index - 3]
    longest = (3, 4, 6)[index - 3]
    lengths = [longest, longest - 1, 1]
    if index == 5:
        lengths.append(longest)
    return _paint_input(_mask(lengths, height, rng), width, rng)


def _query(seed, index):
    rng = _rng(seed, "query", index)
    if index == 0:
        return _anchor(rng)
    height, width = QUERY_SHAPES[index]
    high = (0, 4, 5, 7)[index]
    # Half the requests have ties, half a unique winner; a runner-up of high-1
    # keeps the ranking distinction substantive at the large boundaries.
    lengths = [high, high - 1, 1, high if rng.randrange(2) else 2]
    return _paint_input(_mask(lengths, height, rng), width, rng)


def generate(seed, settings, demos, queries):
    """Construct one lesson with independent counts and an episode-fixed rule.

    Query0 is a novel canonical-scale input. The remaining query profiles carry
    multiple bands and mixed rows across 17x12, 24x23 and 30x30 canvases.
    A bounded per-slot retry only handles visible input collisions (e.g. two
    3x3 anchors); it does not search for a rule or use any private query label.
    """
    mode = _mode(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    # Compute all supported slots before taking prefixes. In particular, a
    # future demo count cannot change collision decisions for any query.
    seen = set()
    buckets = []
    for stream, count, sampler in (("demo", 6, _demo), ("query", 4, _query)):
        pairs = []
        for index in range(count):
            for attempt in range(32):
                draw_seed = seed if attempt == 0 else f"{seed}:retry:{stream}:{index}:{attempt}"
                grid = sampler(draw_seed, index)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    pairs.append({"input": grid, "output": solve(grid, mode)})
                    break
            else:
                raise RuntimeError("distinct input construction exhausted its 32 retries")
        buckets.append(pairs)
    return {"train": buckets[0][:demos], "test": buckets[1][:queries],
            "program_solution": program(settings)}
