"""Native prototype for episode-fixed midpoint fill pass count.

The default setting is the exact canonical one-pass rule.  The alternative runs
that same rule a second time on the first pass's output.  Generated lessons
contain relay chains where pass one creates an endpoint required by pass two.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "fe54bfae4cee"
ROOT = find_root(__file__)
PASS_OPTIONS = (1, 2)
DEFAULT_PASSES = 1
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
CANONICAL_SOURCE_SHA256 = "92b2f2721622256c4dfcd8bfa4311234c31b54cd25344b8933746391aeef86a0"
CANONICAL_RULE_HASH = "92b2f2721622"
COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
TILE_SIZE = 6
MOTIF_CYCLE = (
    "chain2",
    "chain3",
    "standalone",
    "longspan",
    "diagonal",
    "blocked",
    "cross",
)

# Local coordinates stay in 1..4 so neighboring six-cell tiles remain at least
# three cells apart and cannot accidentally create an exact-gap pair.
_TEMPLATES: dict[str, tuple[tuple[int, int, str], ...]] = {
    "chain2": ((1, 1, "a"), (1, 3, "a"), (3, 2, "a")),
    "chain3": ((1, 1, "a"), (1, 3, "a"), (3, 2, "a"), (2, 4, "a")),
    "standalone": ((1, 1, "a"), (1, 3, "a")),
    "longspan": ((1, 1, "a"), (1, 4, "a")),
    "diagonal": ((1, 1, "a"), (3, 3, "a")),
    "blocked": ((1, 1, "a"), (1, 2, "b"), (1, 3, "a")),
    "cross": ((2, 1, "a"), (2, 3, "a"), (1, 2, "b"), (3, 2, "b")),
}

_DEMO_SPECS: tuple[tuple[int, int, tuple[str, ...]], ...] = (
    (12, 18, ("chain2", "cross", "longspan", "diagonal", "blocked", "standalone")),
    (12, 18, ("chain3", "blocked", "cross", "standalone", "longspan", "diagonal")),
    (18, 18, ("chain2", "chain3", "cross", "blocked", "standalone", "longspan", "diagonal", "chain2", "standalone")),
    (18, 24, ("chain3", "chain2", "cross", "blocked", "standalone", "longspan", "diagonal", "chain2", "chain3", "cross", "blocked", "standalone")),
    (24, 24, tuple(MOTIF_CYCLE[i % len(MOTIF_CYCLE)] for i in range(16))),
    (30, 24, tuple(MOTIF_CYCLE[i % len(MOTIF_CYCLE)] for i in range(20))),
)

_QUERY_SPECS: tuple[tuple[int, int, tuple[str, ...] | None], ...] = (
    (7, 7, None),
    (12, 12, ("chain3", "cross", "blocked", "diagonal")),
    (18, 24, tuple(MOTIF_CYCLE[i % len(MOTIF_CYCLE)] for i in range(12))),
    (30, 30, tuple(MOTIF_CYCLE[i % len(MOTIF_CYCLE)] for i in range(25))),
)


def _literal_int(name: str, value, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def _pass_count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("fill_passes must be a literal integer")
    if value not in PASS_OPTIONS:
        raise ValueError(f"fill_passes must be one of {PASS_OPTIONS}")
    return value


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return copy.deepcopy(grid)


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("exactly one canonical Racket program is required")
    program = next(iter(programs))
    if hashlib.sha256(program.encode("utf-8")).hexdigest() != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical Racket source changed; review the family")
    normalized = hashlib.sha256(" ".join(program.split()).encode("utf-8")).hexdigest()[:12]
    if normalized != CANONICAL_RULE_HASH:
        raise ValueError("canonical normalized rule hash changed; review the family")
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return program


def _replace_symbol(source: str, old: str, new: str) -> str:
    return re.sub(
        rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9_-])",
        new,
        source,
    )


@lru_cache(maxsize=len(PASS_OPTIONS))
def program_for(passes: int) -> str:
    passes = _pass_count(passes)
    canonical = canonical_program()
    if passes == 1:
        return canonical
    body = canonical.removeprefix("(rule! ").removesuffix(")")
    second = _replace_symbol(body, "g", "first")
    if second == body or " g" in second:
        raise ValueError("failed to bind the second pass to the first-pass grid")
    return f"(rule! (let ((first {body})) {second}))"


def _apply_one_pass(grid: list[list[int]]) -> list[list[int]]:
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    out = copy.deepcopy(source)
    for row in range(height):
        for col in range(width - 2):
            color = source[row][col]
            if color != 0 and color == source[row][col + 2] and source[row][col + 1] == 0:
                out[row][col + 1] = color
    # The canonical rule tests vertical pairs against the same source grid and
    # writes them after horizontal pairs, so vertical wins a shared midpoint.
    for row in range(height - 2):
        for col in range(width):
            color = source[row][col]
            if color != 0 and color == source[row + 2][col] and source[row + 1][col] == 0:
                out[row + 1][col] = color
    return out


def _apply_n(grid: list[list[int]], passes: int) -> list[list[int]]:
    result = _validate_grid(grid)
    for _ in range(passes):
        result = _apply_one_pass(result)
    return result


def apply_passes(grid: list[list[int]], passes: int) -> list[list[int]]:
    return _apply_n(grid, _pass_count(passes))


def apply_until_stable(grid: list[list[int]]) -> list[list[int]]:
    current = _validate_grid(grid)
    for _ in range(64):
        following = _apply_one_pass(current)
        if following == current:
            return following
        current = following
    raise RuntimeError("midpoint closure did not stabilize within 64 passes")


def skip_first_pass(grid: list[list[int]]) -> list[list[int]]:
    """Ablate pass A from the two-pass rule, leaving one pass on the source."""
    return _apply_one_pass(grid)


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{role}:{index}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _transform(row: int, col: int, transform: int) -> tuple[int, int]:
    if not 0 <= transform < 8:
        raise ValueError("transform must be in 0..7")
    if transform >= 4:
        col = TILE_SIZE - 1 - col
    for _ in range(transform % 4):
        row, col = col, TILE_SIZE - 1 - row
    return row, col


def _write_motif(
    grid: list[list[int]],
    kind: str,
    tile_row: int,
    tile_col: int,
    primary: int,
    secondary: int,
    transform: int,
) -> None:
    if kind not in _TEMPLATES:
        raise ValueError(f"unknown motif kind: {kind}")
    row_offset, col_offset = tile_row * TILE_SIZE, tile_col * TILE_SIZE
    for local_row, local_col, role in _TEMPLATES[kind]:
        local_row, local_col = _transform(local_row, local_col, transform)
        row, col = row_offset + local_row, col_offset + local_col
        color = primary if role == "a" else secondary
        if grid[row][col] != 0:
            raise RuntimeError("motif placement collision")
        grid[row][col] = color


def _tile_scene(
    height: int,
    width: int,
    kinds: Iterable[str],
    *,
    seed: int,
    role: str,
    index: int,
) -> list[list[int]]:
    if height % TILE_SIZE or width % TILE_SIZE:
        raise ValueError("tiled scenes need dimensions divisible by six")
    kinds = tuple(kinds)
    tile_rows, tile_cols = height // TILE_SIZE, width // TILE_SIZE
    if len(kinds) > tile_rows * tile_cols:
        raise ValueError("too many motifs for scene")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    rng = _rng(seed, role, index)
    palette = list(COLORS)
    rng.shuffle(palette)
    for motif_index, kind in enumerate(kinds):
        tile_row, tile_col = divmod(motif_index, tile_cols)
        primary = palette[motif_index % len(palette)]
        secondary = palette[(motif_index + 3) % len(palette)]
        if secondary == primary:
            secondary = palette[(motif_index + 1) % len(palette)]
        _write_motif(
            grid,
            kind,
            tile_row,
            tile_col,
            primary,
            secondary,
            rng.randrange(8),
        )
    return grid


def _boundary_scene(seed: int, role: str, index: int) -> list[list[int]]:
    rng = _rng(seed, role, index)
    colors = list(COLORS)
    rng.shuffle(colors)
    chain_color, decoy_color = colors[:2]
    grid = [[0 for _ in range(7)] for _ in range(7)]
    # This relay touches the top and left boundaries. Pass one fills (0,1);
    # pass two uses it with (2,1) to fill (1,1).
    for row, col in ((0, 0), (0, 2), (2, 1)):
        grid[row][col] = chain_color
    # A same-color longer span is a visible exact-gap negative at the boundary.
    grid[6][2] = decoy_color
    grid[6][5] = decoy_color
    return grid


def _scene(seed: int, role: str, index: int) -> list[list[int]]:
    if role == "demo":
        height, width, kinds = _DEMO_SPECS[index]
        return _tile_scene(height, width, kinds, seed=seed, role=role, index=index)
    height, width, kinds = _QUERY_SPECS[index]
    if kinds is None:
        return _boundary_scene(seed, role, index)
    return _tile_scene(height, width, kinds, seed=seed, role=role, index=index)


def _pair(seed: int, role: str, index: int, passes: int) -> dict:
    grid = _scene(seed, role, index)
    output = apply_passes(grid, passes)
    if output == grid:
        raise RuntimeError("constructed pair has no active midpoint")
    return {"input": grid, "output": output}


def generate_episode(seed: int, passes: int, demos: int, queries: int) -> dict:
    seed = _literal_int("seed", seed, 0, 2**63 - 1)
    passes = _pass_count(passes)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)

    train = [_pair(seed, "demo", index, passes) for index in range(demos)]
    test = [_pair(seed, "query", index, passes) for index in range(queries)]
    identifiers = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*train, *test]
    ]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("episode contains duplicate inputs")
    if apply_passes(train[0]["input"], 1) == apply_passes(train[0]["input"], 2):
        raise RuntimeError("first demonstration does not distinguish pass count")
    deep = train[1]["input"]
    if len({
        json.dumps(apply_passes(deep, 1), separators=(",", ":")),
        json.dumps(apply_passes(deep, 2), separators=(",", ":")),
        json.dumps(apply_until_stable(deep), separators=(",", ":")),
    }) != 3:
        raise RuntimeError("second demonstration does not distinguish finite pass count from closure")
    return copy.deepcopy(
        {
            "train": train,
            "test": test,
            "program_solution": program_for(passes),
        }
    )


def crossed_midpoints(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    source = _validate_grid(grid)
    result: list[tuple[int, int, int, int]] = []
    for row in range(1, len(source) - 1):
        for col in range(1, len(source[0]) - 1):
            if source[row][col] != 0:
                continue
            horizontal = source[row][col - 1]
            vertical = source[row - 1][col]
            if (
                horizontal != 0
                and horizontal == source[row][col + 1]
                and vertical != 0
                and vertical == source[row + 1][col]
            ):
                result.append((row, col, horizontal, vertical))
    return result


def causal_witness() -> dict:
    grid = [[0 for _ in range(7)] for _ in range(7)]
    color = 3
    for row, col in ((2, 1), (2, 3), (4, 2)):
        grid[row][col] = color
    return {
        "input": grid,
        "color": color,
        "created_first": [2, 2],
        "created_second": [3, 2],
        "step_a": "canonical exact-gap midpoint fill on the source",
        "intermediate": "the first-pass grid containing the new endpoint at [2,2]",
        "step_b": "the same midpoint rule on the first-pass grid",
    }


def _changed_count(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        left[row][col] != right[row][col]
        for row in range(len(left))
        for col in range(len(left[0]))
    )


def _classify_tile(tile: list[list[int]]) -> str | None:
    cells = [
        (row, col, value)
        for row, values in enumerate(tile)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    if crossed_midpoints(tile):
        return "cross"
    colors = {value for _, _, value in cells}
    first = _apply_one_pass(tile)
    second = _apply_one_pass(first)
    third = _apply_one_pass(second)
    change1 = _changed_count(tile, first)
    change2 = _changed_count(first, second)
    change3 = _changed_count(second, third)
    if len(colors) == 1 and len(cells) == 3 and change1 and change2 and not change3:
        return "chain2"
    if len(colors) == 1 and len(cells) == 4 and change1 and change2 and change3:
        return "chain3"
    if len(colors) == 1 and len(cells) == 2 and change1:
        return "standalone"
    if len(colors) == 1 and len(cells) == 2:
        (row1, col1, _), (row2, col2, _) = cells
        if (row1 == row2 and abs(col1 - col2) == 3) or (
            col1 == col2 and abs(row1 - row2) == 3
        ):
            return "longspan"
        if abs(row1 - row2) == abs(col1 - col2) == 2:
            return "diagonal"
    if len(colors) == 2 and len(cells) == 3 and not change1:
        return "blocked"
    raise ValueError(f"unclassified motif tile: {cells}")


def scene_profile(grid: list[list[int]]) -> dict:
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    kinds: set[str] = set()
    if height % TILE_SIZE == 0 and width % TILE_SIZE == 0:
        for row in range(0, height, TILE_SIZE):
            for col in range(0, width, TILE_SIZE):
                tile = [values[col : col + TILE_SIZE] for values in source[row : row + TILE_SIZE]]
                kind = _classify_tile(tile)
                if kind is not None:
                    kinds.add(kind)
    return {
        "shape": [height, width],
        "nonzero": sum(value != 0 for row in source for value in row),
        "motif_kinds": kinds,
        "crossed_midpoints": len(crossed_midpoints(source)),
    }
