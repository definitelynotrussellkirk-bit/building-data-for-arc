"""Independent authoring probes for task 764b6b9e7771.

This module is intentionally separate from the selected generator.  It loads
canonical pairs, executes a small Python transcription of the Racket rule, and
implements the canonical-fitting rivals used by task-local tests and review
notes.  It is not label authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

TASK_ID = "764b6b9e7771"
DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
DELTA_TO_DIRECTION = {value: key for key, value in DIRECTIONS.items()}


def find_root(start: str | os.PathLike[str]) -> Path:
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        if (candidate / "shared/data/canonical/puzzles.jsonl").is_file():
            return candidate
        if (candidate / "data/canonical/puzzles.jsonl").is_file():
            return candidate
    raise FileNotFoundError(f"no ARCpuzzles runtime root above {start}")


def _canonical_path(root: Path) -> Path:
    for rel in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
        path = root / rel
        if path.is_file():
            return path
    raise FileNotFoundError(root)


def canonical_row(root: Path | None = None) -> dict:
    root = root or find_root(__file__)
    with _canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def canonical_pairs(root: Path | None = None) -> list[dict]:
    row = canonical_row(root)
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def normalized_rule_hash(source: str) -> str:
    # Match the repository rule hash: comments removed, whitespace normalized.
    source = re.sub(r";[^\n]*", "", source)
    source = " ".join(source.split())
    return hashlib.sha256(source.encode()).hexdigest()[:12]


def base_authority_path(root: Path | None = None) -> Path:
    root = root or find_root(__file__)
    for rel in (
        "shared/data/base/solutions/banks/3cb9777539c7/H145__764b6b9e7771.json",
        "data/base/solutions/banks/3cb9777539c7/H145__764b6b9e7771.json",
    ):
        path = root / rel
        if path.is_file():
            return path
    raise FileNotFoundError("base authority record")


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or Path(__file__).parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location("reviewed_764b6b9e7771", source)
    if not spec or not spec.loader:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _markers(grid):
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    blue = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if len(red) != 1 or len(blue) != 1:
        raise ValueError("expected one red start and one blue direction marker")
    return red[0], blue[0]


def _right(vector):
    return vector[1], -vector[0]


def _turn(vector, side):
    right = _right(vector)
    return right if side == "right" else (-right[0], -right[1])


def _reflect(vector, mirror):
    dr, dc = vector
    if mirror == 4:
        return -dc, -dr
    if mirror == 6:
        return dc, dr
    raise ValueError(f"not a mirror: {mirror!r}")


def _relative_turn(before, after):
    right = _right(before)
    if after == right:
        return "right"
    if after == (-right[0], -right[1]):
        return "left"
    raise ValueError(f"non-cardinal quarter turn: {before!r} -> {after!r}")


def trace(grid, *, swap_mirrors: bool = False) -> tuple[list[list[int]], dict]:
    """Independent transcription of the selected Racket rule."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    if (dr, dc) not in DELTA_TO_DIRECTION:
        raise ValueError("direction marker is not cardinal-adjacent")
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    visited = set()
    mirrors = []
    turn_sides = []
    painted = []
    stop = None
    while True:
        state = (r, c, dr, dc)
        if state in visited:
            stop = "loop"
            break
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            stop = "edge"
            break
        cell = grid[nr][nc]
        if cell == 5:
            stop = "wall"
            break
        if cell == 0:
            out[nr][nc] = 8
            painted.append((nr, nc))
        if cell in (4, 6):
            mirrors.append((nr, nc, cell))
            use = 10 - cell if swap_mirrors else cell
            before = (dr, dc)
            dr, dc = _reflect(before, use)
            turn_sides.append(_relative_turn(before, (dr, dc)))
        r, c = nr, nc
    return out, {
        "painted": tuple(painted),
        "mirrors": tuple(mirrors),
        "turn_sides": tuple(turn_sides),
        "stop": stop,
        "states": len(visited),
    }


def intended_output(grid):
    return trace(grid)[0]


def straight_to_edge_rival(grid):
    """Canonical-fitting rival: ignore mirrors and walls, keep the launch ray."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w):
            return out
        if grid[r][c] == 0:
            out[r][c] = 8


def stop_at_first_obstacle_rival(grid):
    """Canonical-fitting rival: draw straight and stop at any later nonzero cell."""
    start, arrow = _markers(grid)
    r, c = arrow
    dr, dc = arrow[0] - start[0], arrow[1] - start[1]
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w):
            return out
        if grid[r][c] != 0:
            return out
        out[r][c] = 8


def swapped_mirrors_rival(grid):
    return trace(grid, swap_mirrors=True)[0]


def first_two_mirrors_rival(grid):
    """Canonical-fitting rival: only the first two encountered mirrors reflect."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    visited = set()
    mirror_index = 0
    while True:
        state = (r, c, dr, dc)
        if state in visited:
            return out
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
            return out
        cell = grid[nr][nc]
        if cell == 0:
            out[nr][nc] = 8
        elif cell in (4, 6):
            mirror_index += 1
            if mirror_index <= 2:
                dr, dc = _reflect((dr, dc), cell)
        r, c = nr, nc


def repeat_first_turn_side_rival(grid):
    """Canonical-fitting rival: repeat the first mirror's relative turn forever."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    visited = set()
    first_side = None
    while True:
        state = (r, c, dr, dc)
        if state in visited:
            return out
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
            return out
        cell = grid[nr][nc]
        if cell == 0:
            out[nr][nc] = 8
        elif cell in (4, 6):
            before = (dr, dc)
            if first_side is None:
                after = _reflect(before, cell)
                first_side = _relative_turn(before, after)
                dr, dc = after
            else:
                dr, dc = _turn(before, first_side)
        r, c = nr, nc


def observed(grid) -> dict:
    start, arrow = _markers(grid)
    delta = (arrow[0] - start[0], arrow[1] - start[1])
    _, report = trace(grid)
    if not report["mirrors"]:
        raise ValueError("cannot observe turn_side without an interacting mirror")
    first_type = report["mirrors"][0][2]
    if first_type == 4:
        turned = (-delta[1], -delta[0])
    else:
        turned = (delta[1], delta[0])
    right = (delta[1], -delta[0])
    if turned == right:
        turn_side = "right"
    elif turned == (-right[0], -right[1]):
        turn_side = "left"
    else:  # Defensive: cardinal input plus a 4/6 mirror should make this unreachable.
        raise ValueError("first mirror does not make a cardinal quarter-turn")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_mirrors": sum(value in (4, 6) for row in grid for value in row),
        "n_walls": sum(value == 5 for row in grid for value in row),
        "direction": DELTA_TO_DIRECTION[delta],
        "turn_side": turn_side,
    }
