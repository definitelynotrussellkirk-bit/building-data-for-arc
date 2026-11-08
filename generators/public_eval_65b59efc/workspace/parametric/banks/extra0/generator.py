"""Public 65b59efc: decode token panels into a tiled drawing.

The top bank defines binary templates keyed by source colors.  The middle bank
contains sparse source-color tokens on an n-by-n macro canvas, potentially in
panels unrelated to the token identity.  The bottom bank maps each source color
to an output color.  The output expands every token into its keyed template.
"""
from __future__ import annotations

from pathlib import Path
import copy
import math

from puzzle_generators.base import gen_ctx

TASK_ID = GENERATOR_ID = "public_eval_65b59efc"
RULE_TASK_ID = "ee_65b59efc"
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
SUMMARY = "Decode sparse colored macro tokens through keyed templates and palettes."
AXES = {}
BINDING_MODES = ("self", "next_token")
RIVALS = ("previous_token", "position_block", "first_template", "source_palette")


def _int(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return len(grid), width


def analyse(grid: list[list[int]]) -> dict[str, object]:
    """Parse a lawful decoder board without relying on trailing dimensions."""
    height, width = _validate_grid(grid)
    separator_rows = [r for r in range(2, min(height, 8)) if grid[r][0] == 5]
    if not separator_rows:
        raise ValueError("missing first separator row")
    n = separator_rows[0]
    if not 2 <= n <= 5 or height < 2 * n + 3:
        raise ValueError("invalid tile size or band layout")
    second_separator = 2 * n + 1
    if second_separator >= height or grid[second_separator][0] != 5:
        raise ValueError("missing second separator row")

    starts: list[int] = []
    templates: dict[int, list[list[int]]] = {}
    source_order: list[int] = []
    start = 0
    while start + n <= width:
        values = {
            grid[r][c]
            for r in range(n)
            for c in range(start, start + n)
            if grid[r][c] not in (0, 5)
        }
        if not values:
            break
        if len(values) != 1:
            raise ValueError("each template block must have exactly one source color")
        source = next(iter(values))
        if source in templates:
            raise ValueError("source colors must be unique")
        template = [
            [1 if grid[r][c] == source else 0 for c in range(start, start + n)]
            for r in range(n)
        ]
        if not any(any(row) for row in template):
            raise ValueError("empty template")
        starts.append(start)
        source_order.append(source)
        templates[source] = template
        start += n + 1
    if not 2 <= len(starts) <= 5:
        raise ValueError("need two to five template blocks")

    tokens = [[0] * n for _ in range(n)]
    owners = [[-1] * n for _ in range(n)]
    legal = set(source_order)
    for owner, start in enumerate(starts):
        for r in range(n):
            for c in range(n):
                value = grid[n + 1 + r][start + c]
                if value in (0, 5):
                    continue
                if value not in legal:
                    raise ValueError("mask token has no matching template")
                if tokens[r][c] and tokens[r][c] != value:
                    raise ValueError("conflicting mask tokens")
                if tokens[r][c] and owners[r][c] != owner:
                    raise ValueError("duplicate mask token across blocks")
                tokens[r][c] = value
                owners[r][c] = owner
    if sum(value != 0 for row in tokens for value in row) < 2:
        raise ValueError("need at least two occupied macro cells")

    bottom = 2 * n + 2
    target_colors: dict[int, int] = {}
    for source, start in zip(source_order, starts):
        values = {
            grid[r][c]
            for r in range(bottom, height)
            for c in range(start, start + n)
            if grid[r][c] not in (0, 5)
        }
        if len(values) != 1:
            raise ValueError("each palette block must contain exactly one target color")
        target_colors[source] = next(iter(values))

    return {
        "tile_size": n,
        "starts": starts,
        "source_order": source_order,
        "templates": templates,
        "tokens": tokens,
        "owners": owners,
        "target_colors": target_colors,
    }


def _bindings(info: dict[str, object], mode: str, rival: str | None) -> dict[tuple[int, int], int]:
    if mode not in BINDING_MODES:
        raise ValueError("unknown binding mode")
    if rival is not None and rival not in RIVALS:
        raise ValueError("unknown rival")
    tokens = info["tokens"]
    occupied = [(r, c, value) for r, row in enumerate(tokens) for c, value in enumerate(row) if value]
    if rival == "previous_token":
        return {(r, c): occupied[(i - 1) % len(occupied)][2] for i, (r, c, _) in enumerate(occupied)}
    if rival == "position_block":
        sources = info["source_order"]
        owners = info["owners"]
        return {(r, c): sources[owners[r][c]] for r, c, _ in occupied}
    if rival == "first_template":
        first = info["source_order"][0]
        return {(r, c): first for r, c, _ in occupied}
    if mode == "self":
        return {(r, c): value for r, c, value in occupied}
    return {(r, c): occupied[(i + 1) % len(occupied)][2] for i, (r, c, _) in enumerate(occupied)}


def solve(
    grid: list[list[int]],
    binding_mode: str = "self",
    rival: str | None = None,
) -> list[list[int]]:
    info = analyse(grid)
    n = info["tile_size"]
    templates = info["templates"]
    target_colors = info["target_colors"]
    bindings = _bindings(info, binding_mode, rival)
    out = [[0] * (n * n) for _ in range(n * n)]
    for (macro_r, macro_c), source in bindings.items():
        color = source if rival == "source_palette" else target_colors[source]
        template = templates[source]
        for r in range(n):
            for c in range(n):
                if template[r][c]:
                    out[macro_r * n + r][macro_c * n + c] = color
    return out


def _random_template(n: int, rng, salt: int) -> list[list[int]]:
    """Produce a connected-enough asymmetric binary glyph with an interior bit."""
    for attempt in range(256):
        local = rng.random
        cells = {(0, 0), (n - 1, (salt + attempt) % n), (1, 1)}
        # A biased random walk creates recognizable, non-rectangular shapes.
        r, c = salt % n, (2 * salt + attempt) % n
        cells.add((r, c))
        for _ in range(n * 2 + 2):
            dr, dc = ((0, 1), (1, 0), (0, -1), (-1, 0))[int(local() * 4) % 4]
            r = max(0, min(n - 1, r + dr))
            c = max(0, min(n - 1, c + dc))
            cells.add((r, c))
        if 4 <= len(cells) <= n * n - 2:
            grid = [[1 if (rr, cc) in cells else 0 for cc in range(n)] for rr in range(n)]
            # Forbid the common transpose/180 symmetries.
            if grid != [row[::-1] for row in grid[::-1]] and grid != [list(row) for row in zip(*grid)]:
                return grid
    raise RuntimeError("failed to construct asymmetric template")


def sample(seed: int, index: int) -> list[list[int]]:
    _int(seed, 0, 2**63 - 1, "seed")
    _int(index, 0, 2**31 - 1, "sample_index")
    ctx = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK_ID)
    rng = ctx.draw_rng("templates_masks_palette")
    profile = index % 4
    n = (3, 4, 5, 5)[profile]
    k = (3, 3, 3, 4)[profile]
    sources = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], k)
    targets = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], k)

    templates: list[list[list[int]]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for i in range(k):
        for bump in range(64):
            template = _random_template(n, rng, i * 17 + bump)
            key = tuple(tuple(row) for row in template)
            if key not in seen:
                seen.add(key)
                templates.append(template)
                break
        else:
            raise RuntimeError("template bank collision")

    semantic_width = k * n + (k - 1)
    width = 30 if profile == 3 else semantic_width
    bottom_height = 4 if profile == 3 else 2
    height = 2 * n + 2 + bottom_height
    grid = [[0] * width for _ in range(height)]
    starts = [i * (n + 1) for i in range(k)]

    # Top template bank.
    for start, source, template in zip(starts, sources, templates):
        for r in range(n):
            for c in range(n):
                if template[r][c]:
                    grid[r][start + c] = source
    for separator in (n, 2 * n + 1):
        for c in range(semantic_width):
            grid[separator][c] = 5
    for sep in (start + n for start in starts[:-1]):
        for r in range(height - bottom_height):
            grid[r][sep] = 5

    # Middle token panels.  Consecutive tokens are always different, and token
    # identity is deliberately decorrelated from the panel that stores it.
    count = min(n * n, k + 4)
    positions = rng.sample([(r, c) for r in range(n) for c in range(n)], count)
    order = sources[:]
    rng.shuffle(order)
    sequence = [order[i % k] for i in range(count)]
    if sequence[-1] == sequence[0]:
        sequence[-1] = order[1]
    for i, ((r, c), token) in enumerate(zip(positions, sequence)):
        source_index = sources.index(token)
        owner = (source_index + 1 + i) % k
        if owner == source_index:
            owner = (owner + 1) % k
        grid[n + 1 + r][starts[owner] + c] = token

    # Bottom palette bank.
    bottom = 2 * n + 2
    for i, (start, target) in enumerate(zip(starts, targets)):
        r = bottom + (i % bottom_height)
        c = start + ((2 * i + seed + index) % n)
        grid[r][c] = target
    for sep in (start + n for start in starts[:-1]):
        for r in range(bottom, height):
            grid[r][sep] = 5

    # Parse-time self-check catches accidental layout ambiguity.
    info = analyse(grid)
    if info["source_order"] != sources:
        raise RuntimeError("constructed source order drifted")
    if any(info["target_colors"][source] != target for source, target in zip(sources, targets)):
        raise RuntimeError("constructed palette drifted")
    return grid


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: object) -> list[list[int]]:
    if difficulty not in (None, "easy", "medium", "hard") or overrides:
        raise ValueError("unsupported difficulty or override")
    return sample(seed, sample_index)


def check_invariants(grid: list[list[int]]) -> list[str]:
    try:
        analyse(grid)
    except ValueError as error:
        return [str(error)]
    return []
