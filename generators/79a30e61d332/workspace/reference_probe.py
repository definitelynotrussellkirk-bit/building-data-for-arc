"""Independent oracle and reusable probes for task 79a30e61d332.

This is reviewer/test tooling.  The canonical Racket program remains the label
authority; :func:`intended_output` is an independently written Python parity
oracle and the rivals are deliberately simpler alternative hypotheses.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterable

TASK = "79a30e61d332"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_79a30e61d332", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def canonical_record():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK:
                return record
    raise KeyError(TASK)


def selected_record():
    path = ROOT / "shared/data/base/solutions/training/d94c3b52__79a30e61d332.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _rectangular(grid) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
    )


def tile_shape(grid) -> tuple[int, int]:
    if not _rectangular(grid):
        raise ValueError("grid must be nonempty and rectangular")
    h, w = len(grid), len(grid[0])
    if (h, w) != (17, 25):
        raise ValueError(f"expected 17x25, got {h}x{w}")
    return 4, 6


def tile_mask(grid, tr: int, tc: int) -> tuple[int, ...]:
    return tuple(
        int(grid[1 + 4 * tr + dr][1 + 4 * tc + dc] != 0)
        for dr in range(3)
        for dc in range(3)
    )


def tile_values(grid, tr: int, tc: int) -> tuple[int, ...]:
    return tuple(
        grid[1 + 4 * tr + dr][1 + 4 * tc + dc]
        for dr in range(3)
        for dc in range(3)
    )


def tile_positions() -> list[tuple[int, int]]:
    return [(tr, tc) for tr in range(4) for tc in range(6)]


def seed_position(grid) -> tuple[int, int]:
    seeds = [
        pos
        for pos in tile_positions()
        if 8 in tile_values(grid, *pos)
    ]
    if len(seeds) != 1:
        raise ValueError(f"expected one seed tile, got {len(seeds)}")
    return seeds[0]


def row_sums(mask: Iterable[int]) -> tuple[int, int, int]:
    cells = tuple(mask)
    return tuple(sum(cells[3 * r : 3 * r + 3]) for r in range(3))  # type: ignore[return-value]


def key_positions(grid, *, mode: str = "exact") -> list[tuple[int, int]]:
    seed = seed_position(grid)
    key = tile_mask(grid, *seed)
    if mode == "exact":
        predicate = lambda mask: mask == key
    elif mode == "row_sums":
        signature = row_sums(key)
        predicate = lambda mask: row_sums(mask) == signature
    else:
        raise ValueError(mode)
    return [pos for pos in tile_positions() if predicate(tile_mask(grid, *pos))]


def aligned_pairs(keys: Iterable[tuple[int, int]]):
    keys = list(keys)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if a[0] == b[0]:
                yield a, b, "horizontal"
            if a[1] == b[1]:
                yield a, b, "vertical"


def bridge_tiles(keys: Iterable[tuple[int, int]], *, allowed_axes=("horizontal", "vertical")):
    keys = set(keys)
    result: set[tuple[int, int]] = set()
    allowed = set(allowed_axes)
    for a, b, axis in aligned_pairs(sorted(keys)):
        if axis not in allowed:
            continue
        if axis == "horizontal":
            result.update((a[0], c) for c in range(min(a[1], b[1]) + 1, max(a[1], b[1])))
        else:
            result.update((r, a[1]) for r in range(min(a[0], b[0]) + 1, max(a[0], b[0])))
    return result - keys


def bridge_axes(grid, keys=None) -> set[str]:
    keys = set(keys if keys is not None else key_positions(grid))
    axes = set()
    for a, b, axis in aligned_pairs(sorted(keys)):
        if axis == "horizontal":
            candidates = [(a[0], c) for c in range(min(a[1], b[1]) + 1, max(a[1], b[1]))]
        else:
            candidates = [(r, a[1]) for r in range(min(a[0], b[0]) + 1, max(a[0], b[0]))]
        if any(pos not in keys for pos in candidates):
            axes.add(axis)
    return axes


def layout_profile(grid) -> str:
    axes = bridge_axes(grid)
    if axes == {"horizontal"}:
        return "horizontal"
    if axes == {"vertical"}:
        return "vertical"
    if axes == {"horizontal", "vertical"}:
        return "mixed"
    return "none"


def observed(grid):
    seed = seed_position(grid)
    return {
        "layout_profile": layout_profile(grid),
        "n_keys": len(key_positions(grid)),
        "key_cells": sum(tile_mask(grid, *seed)),
    }


def _solve_with_keys(grid, keys, *, allowed_axes=("horizontal", "vertical")):
    out = deepcopy(grid)
    keys = set(keys)
    bridges = bridge_tiles(keys, allowed_axes=allowed_axes)
    for tr, tc in tile_positions():
        color = 8 if (tr, tc) in keys else 7 if (tr, tc) in bridges else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                r, c = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                if out[r][c] != 0:
                    out[r][c] = color
    return out


def intended_output(grid):
    return _solve_with_keys(grid, key_positions(grid, mode="exact"))


def row_sums_only_rival(grid):
    """Wrong rule: tile row totals define equality, not exact cell positions."""
    return _solve_with_keys(grid, key_positions(grid, mode="row_sums"))


def horizontal_only_rival(grid):
    return _solve_with_keys(grid, key_positions(grid), allowed_axes=("horizontal",))


def vertical_only_rival(grid):
    return _solve_with_keys(grid, key_positions(grid), allowed_axes=("vertical",))


def seed_lines_only_rival(grid):
    """Wrong rule: bridge only along rows/columns that contain the color-8 seed."""
    keys = set(key_positions(grid))
    seed = seed_position(grid)
    out = deepcopy(grid)
    for tr, tc in tile_positions():
        if (tr, tc) in keys:
            color = 8
        else:
            on_seed_row = tr == seed[0] and any(
                other[0] == tr
                and min(seed[1], other[1]) < tc < max(seed[1], other[1])
                for other in keys - {seed}
            )
            on_seed_col = tc == seed[1] and any(
                other[1] == tc
                and min(seed[0], other[0]) < tr < max(seed[0], other[0])
                for other in keys - {seed}
            )
            color = 7 if on_seed_row or on_seed_col else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                r, c = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                if out[r][c] != 0:
                    out[r][c] = color
    return out


def first_two_keys_rival(grid):
    """Wrong rule: use only the seed and the first other exact match."""
    exact = key_positions(grid)
    seed = seed_position(grid)
    other = next(pos for pos in exact if pos != seed)
    return _solve_with_keys(grid, [seed, other])


def keys_only_rival(grid):
    return _solve_with_keys(grid, key_positions(grid), allowed_axes=())


def row_sum_collision_positions(grid):
    seed = seed_position(grid)
    exact = tile_mask(grid, *seed)
    signature = row_sums(exact)
    return [
        pos
        for pos in tile_positions()
        if tile_mask(grid, *pos) != exact and row_sums(tile_mask(grid, *pos)) == signature
    ]


def output_diff_cells(left, right):
    return [
        (r, c)
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def racket_outputs(grids):
    """Execute the canonical Racket authority in a relocated runtime; no fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('parity-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
