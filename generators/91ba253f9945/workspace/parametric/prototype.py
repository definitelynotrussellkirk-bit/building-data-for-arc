"""Native matched-input quarter-turn family for task ``91ba253f9945``.

The hidden episode setting selects clockwise or counterclockwise rotation.
Inputs are independent of that setting.  Step A identifies the source frame and
extracts an input-dependent sorted list of local ``(u, v, color)`` markers;
Step B rotates that intermediate and renders it in the target frame.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "91ba253f9945"
PARAMETER = "turn"
TURNS = ("counterclockwise", "clockwise")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_ROOT = _HOME.parents[3]
_CANONICAL_PATH = _ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASES = tuple(
    (vx, vy)
    for vx in _CARDINAL
    for vy in _CARDINAL
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)
_FRAME_LOCAL = {(0, 0), (1, 0), (0, 1)}

_TRAIN_PROFILES = ((12, 18), (13, 17), (15, 21), (18, 24), (22, 27), (26, 29))
_QUERY_PROFILES = ((11, 15), (16, 20), (24, 28), (30, 30))
# Marker coordinates exclude the source-frame cells and every local point whose
# clockwise or counterclockwise image would land on a target-frame cell.
_TURN_FRAME_FORBIDDEN = _FRAME_LOCAL | {(-1, 0), (0, -1)}
_MARKER_CANDIDATES = tuple(
    (u, v)
    for u in range(-3, 4)
    for v in range(-3, 4)
    if (u, v) not in _TURN_FRAME_FORBIDDEN
)


def _load_canonical_program() -> str:
    matches = []
    for line in _CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    if len(set(matches)) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, got {len(matches)}")
    return matches[0]


_CANONICAL_PROGRAM = _load_canonical_program()
_CCW_EXPR = "(gpos tgt (- (second p)) (first p))"
_CW_EXPR = "(gpos tgt (second p) (- (first p)))"
if _CANONICAL_PROGRAM.count(_CCW_EXPR) != 1:
    raise RuntimeError("canonical quarter-turn expression changed")


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in TURNS:
        raise ValueError(f"{PARAMETER} must be one of {TURNS!r}")
    return value


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program(settings: dict[str, str]) -> str:
    turn = _validate_settings(settings)
    if turn == "counterclockwise":
        return _CANONICAL_PROGRAM
    return _CANONICAL_PROGRAM.replace(_CCW_EXPR, _CW_EXPR, 1)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != w
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return h, w


def _find_frame(grid: list[list[int]], colors: tuple[int, int, int]):
    positions = []
    for color in colors:
        matches = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one color-{color} frame cell")
        positions.append(matches[0])
    origin, px, py = positions
    vx = (px[0] - origin[0], px[1] - origin[1])
    vy = (py[0] - origin[0], py[1] - origin[1])
    if vx not in _CARDINAL or vy not in _CARDINAL or vx[0] * vy[0] + vx[1] * vy[1] != 0:
        raise ValueError(f"colors {colors!r} do not form an orthogonal unit frame")
    return origin, (vx, vy)


def _gpos(frame, u: int, v: int) -> tuple[int, int]:
    origin, (vx, vy) = frame
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _lpos(frame, r: int, c: int) -> tuple[int, int]:
    origin, (vx, vy) = frame
    dr, dc = r - origin[0], c - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def extract_intermediate(grid: list[list[int]]) -> tuple[tuple[int, int, int], ...]:
    """Step A: source-local marker state consumed by the turn/render step."""
    h, w = _validate_grid(grid)
    source = _find_frame(grid, (2, 3, 4))
    points = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color not in (8, 9):
                continue
            u, v = _lpos(source, r, c)
            if max(abs(u), abs(v)) <= 3:
                points.append((u, v, color))
    if not points:
        raise ValueError("source frame has no nearby 8/9 markers")
    return tuple(sorted(points))


def _turned(u: int, v: int, turn: str) -> tuple[int, int]:
    if turn == "counterclockwise":
        return -v, u
    if turn == "clockwise":
        return v, -u
    raise ValueError(f"turn must be one of {TURNS!r}")


def apply_rule(grid: list[list[int]], turn: str) -> list[list[int]]:
    if type(turn) is not str or turn not in TURNS:
        raise ValueError(f"turn must be one of {TURNS!r}")
    h, w = _validate_grid(grid)
    target = _find_frame(grid, (5, 6, 7))
    out = [row[:] for row in grid]
    for u, v, color in extract_intermediate(grid):
        tu, tv = _turned(u, v, turn)
        r, c = _gpos(target, tu, tv)
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError("transformed marker is out of bounds")
        out[r][c] = color
    return out


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|matched-inputs-v3|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _sample_pattern(seed: int, split: str, index: int) -> tuple[tuple[int, int, int], ...]:
    """Create a fresh asymmetric source-local marker set for one episode pair."""
    rng = _rng(seed, f"{split}-pattern", index)
    marker_count = rng.randint(4, 7)
    for _ in range(128):
        coordinates = rng.sample(_MARKER_CANDIDATES, marker_count)
        colors = [8, 9] + [rng.choice((8, 9)) for _ in range(marker_count - 2)]
        rng.shuffle(colors)
        pattern = tuple(sorted((u, v, color) for (u, v), color in zip(coordinates, colors)))
        ccw = {(-v, u, color) for u, v, color in pattern}
        cw = {(v, -u, color) for u, v, color in pattern}
        if ccw != cw:
            return pattern
    raise RuntimeError("failed to sample an asymmetric marker pattern")


def _cell(origin, basis, u: int, v: int) -> tuple[int, int]:
    vx, vy = basis
    return origin[0] + u * vx[0] + v * vy[0], origin[1] + u * vx[1] + v * vy[1]


def _options(h: int, w: int, basis, locals_):
    required = set(locals_) | _FRAME_LOCAL
    options = []
    for r in range(h):
        for c in range(w):
            origin = (r, c)
            cells = {_cell(origin, basis, u, v) for u, v in required}
            if len(cells) == len(required) and all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                options.append((origin, cells))
    return options


def _paint_frame(grid, origin, basis, colors):
    for local, color in zip(((0, 0), (1, 0), (0, 1)), colors):
        r, c = _cell(origin, basis, *local)
        grid[r][c] = color


def _safe_boundary_cell(grid, blocked, side: str):
    h, w = len(grid), len(grid[0])
    candidates = {
        "top": [(0, c) for c in range(w)],
        "bottom": [(h - 1, c) for c in range(w)],
        "left": [(r, 0) for r in range(h)],
        "right": [(r, w - 1) for r in range(h)],
    }[side]
    return next(((r, c) for r, c in candidates if grid[r][c] == 0 and (r, c) not in blocked), None)


def _sample_input(
    seed: int,
    split: str,
    index: int,
    *,
    pattern: tuple[tuple[int, int, int], ...] | None = None,
) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    h, w = profiles[index]
    pattern = _sample_pattern(seed, split, index) if pattern is None else tuple(sorted(pattern))
    rng = _rng(seed, f"{split}-layout", index)
    source_basis = _BASES[rng.randrange(len(_BASES))]
    target_basis = _BASES[rng.randrange(len(_BASES))]
    source_locals = [(u, v) for u, v, _ in pattern]
    target_locals = {
        _turned(u, v, turn)
        for u, v, _ in pattern
        for turn in TURNS
    }
    source_options = _options(h, w, source_basis, source_locals)
    target_options = _options(h, w, target_basis, target_locals)
    if not source_options or not target_options:
        raise RuntimeError("profile cannot fit required frames")

    selected = None
    for _ in range(8192):
        source_origin, source_cells = rng.choice(source_options)
        target_origin, target_cells = rng.choice(target_options)
        if source_cells & target_cells:
            continue
        if abs(source_origin[0] - target_origin[0]) + abs(source_origin[1] - target_origin[1]) < 5:
            continue
        selected = source_origin, source_cells, target_origin, target_cells
        break
    if selected is None:
        raise RuntimeError("could not place disjoint source and target frames")
    source_origin, source_cells, target_origin, target_cells = selected

    grid = [[0 for _ in range(w)] for _ in range(h)]
    _paint_frame(grid, source_origin, source_basis, (2, 3, 4))
    for u, v, color in pattern:
        r, c = _cell(source_origin, source_basis, u, v)
        grid[r][c] = color
    _paint_frame(grid, target_origin, target_basis, (5, 6, 7))
    blocked = set(source_cells) | set(target_cells)

    # Irrelevant 8/9 cells force the solver to use the source-local radius.
    decoy_goal = 3 + index if split == "train" else (4, 6, 8, 10)[index]
    candidates = []
    source_frame = (source_origin, source_basis)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in blocked:
                continue
            u, v = _lpos(source_frame, r, c)
            if max(abs(u), abs(v)) > 3:
                candidates.append((r, c))
    rng.shuffle(candidates)
    for offset, (r, c) in enumerate(candidates[:decoy_goal]):
        grid[r][c] = 8 if offset % 2 == 0 else 9

    # Color-1 nuisance content varies independently of the causal marker list.
    nuisance_goal = 4 + index if split == "train" else (5, 8, 12, 24)[index]
    if split == "test" and index == 3:
        for side in ("top", "bottom", "left", "right"):
            cell = _safe_boundary_cell(grid, blocked, side)
            if cell is not None:
                grid[cell[0]][cell[1]] = 1
        quadrants = (
            (range(0, h // 2), range(0, w // 2)),
            (range(0, h // 2), range(w // 2, w)),
            (range(h // 2, h), range(0, w // 2)),
            (range(h // 2, h), range(w // 2, w)),
        )
        for rows, cols in quadrants:
            cells = [(r, c) for r in rows for c in cols if grid[r][c] == 0 and (r, c) not in blocked]
            if cells:
                r, c = rng.choice(cells)
                grid[r][c] = 1

    free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0 and (r, c) not in blocked]
    rng.shuffle(free)
    current_ones = sum(value == 1 for row in grid for value in row)
    for r, c in free[: max(0, nuisance_goal - current_ones)]:
        grid[r][c] = 1

    # Construction-time assertions protect both hidden settings on identical input.
    ccw = apply_rule(grid, "counterclockwise")
    cw = apply_rule(grid, "clockwise")
    if ccw == cw:
        raise RuntimeError("scene does not distinguish the turn setting")
    return grid


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    turn = _validate_settings(settings)

    train_all = []
    for index in range(MAX_DEMOS):
        grid = _sample_input(seed, "train", index)
        train_all.append({"input": grid, "output": apply_rule(grid, turn)})
    # Always materialize all four controller-side queries, then expose a prefix.
    test_all = []
    for index in range(MAX_QUERIES):
        grid = _sample_input(seed, "test", index)
        test_all.append({"input": grid, "output": apply_rule(grid, turn)})

    train = train_all[:demos]
    test = test_all[:queries]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in (*train, *test)]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    intermediates = [extract_intermediate(pair["input"]) for pair in (*train, *test)]
    if len(intermediates) != len(set(intermediates)):
        raise RuntimeError("demonstration and query marker motifs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}
