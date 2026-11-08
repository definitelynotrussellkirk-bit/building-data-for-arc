"""Generator for 9a94379ed070 — recover a motif and expand its fractal.

A q×q binary motif is used twice on a q×q separator lattice: it selects the
active macro blocks and the active cells inside every such block.  One complete
macro row or macro column is then overpainted green (3), hiding part of the
self-similar construction.  The canonical Racket rule removes green, recovers
one visible motif copy, and paints the full motif×motif product; cyan (8) marks
cells whose macro and micro ranks agree, while red (2) marks the other product
cells.

The generator varies q, motif density/topology, marker orientation/position,
and the harmless source color while retaining the exact canonical grammar.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9a94379ed070"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "ae44c1c82119"

SUMMARY = (
    "A q×q motif (q=3..5) selects both macro blocks and micro cells on a "
    "q×q lattice with one-cell zero separators. One complete macro row or "
    "column is overpainted green, hiding some motif copies. Remove green and "
    "form the motif's self-product; output cyan where macro/micro row-major "
    "ranks match and red elsewhere."
)

INVARIANTS = [
    "side length is q*(q+1)-1 for q in 3..5",
    "the same q×q motif selects macro blocks and cells inside each block",
    "the motif touches every row and column and has q+1..q²-q active cells",
    "one full q-cell macro-interior row or column band is color 3",
    "all visible motif copies are exact and use one nonzero, non-3 source color",
]

HELPFUL_TEXTURES = ("sparse", "irregular", "dense")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "tile_size": {
        "type": "int",
        "default": "difficulty-skewed",
        "valid": "3..5",
    },
    "tile_color": {
        "type": "color",
        "default": "rng helpful",
        "valid": "1..9 (≠3)",
    },
    "stripe_orientation": {
        "type": "str",
        "default": "rng helpful",
        "valid": "row|column",
    },
    "stripe_index": {
        "type": "int",
        "default": "rng within tile_size",
        "valid": "0..4",
    },
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": "sparse|irregular|dense",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard") and not isinstance(
        difficulty, (int, float)
    ):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', 'hard', or a number"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    if "tile_size" in overrides:
        value = overrides["tile_size"]
        if not isinstance(value, int) or isinstance(value, bool) or not 3 <= value <= 5:
            raise ValueError("tile_size must be an integer in 3..5")
    if "tile_color" in overrides:
        value = overrides["tile_color"]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 9
            or value == 3
        ):
            raise ValueError("tile_color must be an integer color in 1..9 except 3")
    if "stripe_orientation" in overrides and overrides["stripe_orientation"] not in (
        "row",
        "column",
    ):
        raise ValueError("stripe_orientation must be 'row' or 'column'")
    if "stripe_index" in overrides:
        value = overrides["stripe_index"]
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 4:
            raise ValueError("stripe_index must be an integer in 0..4")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES:
        raise ValueError("texture must be sparse, irregular, or dense")

    if (
        "tile_size" in overrides
        and "stripe_index" in overrides
        and overrides["stripe_index"] >= overrides["tile_size"]
    ):
        raise ValueError(
            "incompatible overrides: stripe_index must be smaller than tile_size"
        )


def _component_count(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _active_count(q: int, texture: str, rng) -> int:
    if texture == "sparse":
        return q + 1
    if texture == "dense":
        return q * q - q
    # This interval includes every canonical motif count (5, 9, and 10).
    return rng.randint(q + 2, q * q - q - 1)


def _sample_motif(q: int, texture: str, rng) -> tuple[tuple[int, int], ...]:
    """Sample an exact-density motif with full row/column support.

    The mild component cap avoids pepper-noise distributions while still
    providing connected, split, and asymmetric motifs.  The deterministic
    fallback is only a safety net; ordinary parameter ranges find a sample
    quickly.
    """
    count = _active_count(q, texture, rng)
    positions = [(row, col) for row in range(q) for col in range(q)]
    for _ in range(4096):
        cells = tuple(sorted(rng.sample(positions, count)))
        if len({row for row, _ in cells}) != q:
            continue
        if len({col for _, col in cells}) != q:
            continue
        if _component_count(cells) <= 4:
            return cells

    # Connected staircase plus deterministic fill, preserving exact count and
    # touching every row/column. This branch is deterministic under the keyed
    # RNG and remains lawful for every q/texture combination.
    chosen = {(i, i) for i in range(q)}
    chosen.add((0, 1))
    for cell in positions:
        if len(chosen) >= count:
            break
        chosen.add(cell)
    return tuple(sorted(chosen))


def _texture_from_count(q: int, count: int) -> str:
    if count == q + 1:
        return "sparse"
    if count == q * q - q:
        return "dense"
    return "irregular"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    forced_index = overrides.get("stripe_index")
    minimum_q = max(3, int(forced_index) + 1) if forced_index is not None else 3
    q = ctx.draw_int_diff("tile_size", minimum_q, 5)
    tile_color = ctx.draw_color("tile_color", exclude={0, 3})
    orientation = ctx.draw_choice("stripe_orientation", ("row", "column"))
    stripe_index = ctx.draw_int("stripe_index", 0, q - 1)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    motif = _sample_motif(q, texture, ctx.draw_rng("motif"))
    side = q * (q + 1) - 1
    grid = full_grid(side, side, 0)

    for block_row, block_col in motif:
        row0 = block_row * (q + 1)
        col0 = block_col * (q + 1)
        for tile_row, tile_col in motif:
            grid[row0 + tile_row][col0 + tile_col] = tile_color

    start = stripe_index * (q + 1)
    if orientation == "row":
        for row in range(start, start + q):
            for col in range(side):
                grid[row][col] = 3
    else:
        for row in range(side):
            for col in range(start, start + q):
                grid[row][col] = 3

    errors = self_check(grid)
    if errors:  # Loud internal invariant failure; never emit a silent fallback.
        raise RuntimeError("generated invalid 9a94379ed070 grid: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid colors must be integer ARC colors 0..9"]
    return []


def _analyze(grid) -> tuple[dict | None, list[str]]:
    errors = _basic_grid_errors(grid)
    if errors:
        return None, errors

    height, width = len(grid), len(grid[0])
    if height != width:
        return None, [f"grid must be square; got {height}x{width}"]
    candidates = [q for q in range(3, 6) if q * (q + 1) - 1 == height]
    if len(candidates) != 1:
        return None, [
            f"side {height} is not q*(q+1)-1 for an allowed tile_size q=3..5"
        ]
    q = candidates[0]

    colors = {value for row in grid for value in row}
    non_marker = colors - {0, 3}
    if len(non_marker) != 1:
        errors.append(
            "expected exactly one nonzero, non-3 motif color; "
            f"found {sorted(non_marker)}"
        )
        return None, errors
    tile_color = next(iter(non_marker))
    if 3 not in colors:
        return None, errors + ["missing green marker stripe (color 3)"]

    stripe_candidates: list[tuple[str, int]] = []
    for orientation in ("row", "column"):
        for index in range(q):
            start = index * (q + 1)
            expected = {
                (row, col)
                for row in range(height)
                for col in range(width)
                if (
                    start <= row < start + q
                    if orientation == "row"
                    else start <= col < start + q
                )
            }
            actual = {
                (row, col)
                for row in range(height)
                for col in range(width)
                if grid[row][col] == 3
            }
            if actual == expected:
                stripe_candidates.append((orientation, index))
    if len(stripe_candidates) != 1:
        return None, errors + [
            "green cells must form exactly one full macro-interior row or column band; "
            f"matched {stripe_candidates}"
        ]
    orientation, stripe_index = stripe_candidates[0]

    clean = [[0 if value == 3 else value for value in row] for row in grid]
    blocks: dict[tuple[int, int], tuple[tuple[int, ...], ...]] = {}
    nonempty: dict[tuple[int, int], tuple[tuple[int, ...], ...]] = {}
    for block_row in range(q):
        for block_col in range(q):
            row0 = block_row * (q + 1)
            col0 = block_col * (q + 1)
            block = tuple(
                tuple(clean[row0 + row][col0 + col] for col in range(q))
                for row in range(q)
            )
            blocks[(block_row, block_col)] = block
            if any(value for row in block for value in row):
                nonempty[(block_row, block_col)] = block

    if len(nonempty) < 2:
        return None, errors + [
            f"at least two visible motif copies are required; found {len(nonempty)}"
        ]
    distinct_blocks = set(nonempty.values())
    if len(distinct_blocks) != 1:
        return None, errors + [
            f"all visible motif copies must be exact; found {len(distinct_blocks)} variants"
        ]
    tile = next(iter(distinct_blocks))
    tile_values = {value for row in tile for value in row}
    if not tile_values <= {0, tile_color} or tile_color not in tile_values:
        return None, errors + ["visible motif tile has an illegal color or is empty"]

    motif = tuple(
        (row, col)
        for row in range(q)
        for col in range(q)
        if tile[row][col] == tile_color
    )
    count = len(motif)
    if not q + 1 <= count <= q * q - q:
        errors.append(
            f"motif must contain q+1..q²-q cells; q={q}, found {count}"
        )
    if len({row for row, _ in motif}) != q:
        errors.append("motif must touch every tile row")
    if len({col for _, col in motif}) != q:
        errors.append("motif must touch every tile column")

    motif_set = set(motif)
    if orientation == "row":
        hidden = {(row, col) for row, col in motif_set if row == stripe_index}
        expected_visible = {
            (row, col) for row, col in motif_set if row != stripe_index
        }
    else:
        hidden = {(row, col) for row, col in motif_set if col == stripe_index}
        expected_visible = {
            (row, col) for row, col in motif_set if col != stripe_index
        }
    if not hidden:
        errors.append("green stripe must hide at least one active macro block")
    if len(expected_visible) < 2:
        errors.append("green stripe must leave at least two visible motif copies")
    if set(nonempty) != expected_visible:
        errors.append(
            "visible macro blocks do not equal motif-active blocks minus the hidden stripe: "
            f"expected {sorted(expected_visible)}, found {sorted(nonempty)}"
        )

    expected_grid = full_grid(height, width, 0)
    for block_row, block_col in motif:
        row0 = block_row * (q + 1)
        col0 = block_col * (q + 1)
        for tile_row, tile_col in motif:
            expected_grid[row0 + tile_row][col0 + tile_col] = tile_color
    start = stripe_index * (q + 1)
    if orientation == "row":
        for row in range(start, start + q):
            for col in range(width):
                expected_grid[row][col] = 3
    else:
        for row in range(height):
            for col in range(start, start + q):
                expected_grid[row][col] = 3
    if grid != expected_grid:
        errors.append(
            "grid contains separator/copy corruption outside the exact motif-lattice grammar"
        )

    ordered_visible = tuple(sorted(expected_visible))
    ordered_hidden = tuple(sorted(hidden))
    facts = {
        "tile_size": q,
        "tile_color": tile_color,
        "stripe_orientation": orientation,
        "stripe_index": stripe_index,
        "texture": _texture_from_count(q, count),
        "motif_cell_count": count,
        "motif_component_count": _component_count(motif),
        "motif_positions": motif,
        "hidden_block_count": len(hidden),
        "hidden_block_positions": ordered_hidden,
        "visible_block_count": len(expected_visible),
        "visible_block_positions": ordered_visible,
        "first_visible_block": ordered_visible[0] if ordered_visible else None,
        "output_cyan_count": count,
        "output_red_count": count * count - count,
        "canonical_profile": height in (11, 19) and len(colors) == 3,
        "side": height,
        "palette": sorted(colors),
    }
    return facts, errors


def semantic_observables(grid) -> dict:
    """Recover task-linked semantic facts from returned cells only."""
    facts, errors = _analyze(grid)
    if errors or facts is None:
        raise ValueError("invalid 9a94379ed070 grid: " + "; ".join(errors))
    return facts


def observe_overrides(grid) -> dict:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete canonical teaching grammar."""
    del difficulty, meta
    _facts, errors = _analyze(grid)
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python test mirror; the Racket program remains authority."""
    facts = semantic_observables(grid)
    q = facts["tile_size"]
    clean = [[0 if value == 3 else value for value in row] for row in grid]

    tile = None
    for block_row in range(q):
        for block_col in range(q):
            row0 = block_row * (q + 1)
            col0 = block_col * (q + 1)
            candidate = [
                clean[row0 + row][col0 : col0 + q] for row in range(q)
            ]
            if any(value for row in candidate for value in row):
                tile = candidate
                break
        if tile is not None:
            break
    if tile is None:  # guarded by semantic_observables
        raise ValueError("no visible tile")

    positions = [
        (row, col)
        for row in range(q)
        for col in range(q)
        if tile[row][col] != 0
    ]
    rank = {position: index for index, position in enumerate(positions)}
    side = len(grid)
    output = full_grid(side, side, 0)
    for block_pos in positions:
        block_row, block_col = block_pos
        row0 = block_row * (q + 1)
        col0 = block_col * (q + 1)
        for tile_pos in positions:
            tile_row, tile_col = tile_pos
            output[row0 + tile_row][col0 + tile_col] = (
                8 if rank[block_pos] == rank[tile_pos] else 2
            )
    return output
