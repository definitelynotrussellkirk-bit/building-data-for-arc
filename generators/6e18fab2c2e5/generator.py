"""Generator for ARC task 50c07299 / content hash 6e18fab2c2e5."""
from __future__ import annotations
from typing import Any
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e18fab2c2e5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f441e50a1094"
SUMMARY = (
    "On a square color-7 grid, find the 1..5 red cells. For two or more cells "
    "they form one contiguous diagonal; for one cell its quadrant supplies the "
    "diagonal. Remove the old red mark/chain, move from its row-sorted lower "
    "endpoint by N steps toward the top (or inward for one cell), and draw N+1 "
    "red cells continuing along that diagonal."
)
INVARIANTS = [
    "square 12..26 grid with background 7 and foreground 2 only",
    "one red cell off the centre lines, or 2..5 contiguous diagonal red cells",
    "the N-step shifted N+1-cell result remains fully in bounds and disjoint",
    "five consecutive samples cover counts 1..5 and both diagonal slopes",
]
SLOPES = ("main", "anti")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
AXES = {
    "grid_size": {"type": "int", "default": "16 every third sample; otherwise difficulty-banded", "valid": "12..26"},
    "n_cells": {"type": "int", "default": "cyclic 1..5 by sample_index", "valid": "1..5"},
    "diagonal_slope": {"type": "str", "default": "alternating main/anti by sample_index", "valid": "main|anti"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_size(ctx, sample_index: int, band: str, overrides: dict[str, Any]) -> int:
    if overrides.get("grid_size") is not None:
        return ctx.draw_int("grid_size", 12, 26)
    if sample_index % 3 == 0:
        return ctx.draw_choice("grid_size", [16])
    choices = {"easy": list(range(12, 16)), "medium": list(range(17, 22)), "hard": list(range(22, 27))}[band]
    return ctx.draw_choice("grid_size", choices)


def _draw_n(ctx, sample_index: int, overrides: dict[str, Any]) -> int:
    if overrides.get("n_cells") is not None:
        return ctx.draw_int("n_cells", 1, 5)
    return ctx.draw_choice("n_cells", [1 + sample_index % 5])


def _draw_slope(ctx, sample_index: int, overrides: dict[str, Any]) -> str:
    if overrides.get("diagonal_slope") is not None:
        return ctx.draw_choice("diagonal_slope", list(SLOPES))
    return ctx.draw_choice("diagonal_slope", [SLOPES[sample_index % 2]])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    size = _draw_size(ctx, sample_index, band, overrides)
    n = _draw_n(ctx, sample_index, overrides)
    slope = _draw_slope(ctx, sample_index, overrides)
    rng = ctx.draw_rng("placement")
    grid = full_grid(size, size, 7)
    if n == 1:
        lower = bool(rng.getrandbits(1))
        right = lower if slope == "main" else not lower
        row = rng.randint(size // 2 + 1, size - 1) if lower else rng.randint(0, min((size - 1) // 2, size - 3))
        col = rng.randint(size // 2 + 1, size - 1) if right else rng.randint(0, min((size - 1) // 2, size - 3))
        grid[row][col] = 2
        return grid
    top_r = rng.randint(n + 1, size - n)
    if slope == "main":
        top_c = rng.randint(n + 1, size - n)
        for i in range(n):
            grid[top_r + i][top_c + i] = 2
    else:
        top_c = rng.randint(n - 1, size - n - 2)
        for i in range(n):
            grid[top_r + i][top_c - i] = 2
    return grid


def _validate_grid(grid: Any):
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, [], ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, [], ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0]); errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, [], ["grid must be rectangular"]
    if h != w: errors.append("grid must be square")
    if not (12 <= h <= 26): errors.append(f"grid size must be 12..26, got {h}")
    if any(isinstance(v, bool) or not isinstance(v, int) or v not in (2, 7) for row in grid for v in row):
        errors.append("only background 7 and foreground 2 are allowed")
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if not (1 <= len(red) <= 5): errors.append(f"expected 1..5 red cells, got {len(red)}")
    return h, w, red, errors


def _analyse(grid: Any):
    h, w, red, errors = _validate_grid(grid)
    info: dict[str, Any] = {"grid_size": h, "n_cells": len(red), "red": tuple(red)}
    if errors: return info, errors
    ordered = sorted(red); n = len(ordered); first = ordered[0]; last = ordered[-1]
    if n == 1:
        if first[0] == h / 2 or first[1] == w / 2:
            errors.append("single red cell must not lie on a centre line")
        step_r = -1 if first[0] > h / 2 else 1
        step_c = -1 if first[1] > w / 2 else 1
    else:
        row_deltas = [ordered[i + 1][0] - ordered[i][0] for i in range(n - 1)]
        col_deltas = [ordered[i + 1][1] - ordered[i][1] for i in range(n - 1)]
        if any(d != 1 for d in row_deltas): errors.append("red cells must occupy consecutive rows")
        if not (all(d == 1 for d in col_deltas) or all(d == -1 for d in col_deltas)):
            errors.append("red cells must form one contiguous unit-step diagonal")
        step_r = -1; step_c = -1 if last[1] > first[1] else 1
    slope = "main" if step_r == step_c else "anti"
    new_bottom = (last[0] + n * step_r, last[1] + n * step_c)
    output_red = tuple((new_bottom[0] + i * step_r, new_bottom[1] + i * step_c) for i in range(n + 1))
    if any(not (0 <= r < h and 0 <= c < w) for r, c in output_red): errors.append("N-step shifted N+1-cell output would leave the grid")
    if set(output_red) & set(red): errors.append("input and output red chains must be disjoint")
    info.update({"ordered_red": tuple(ordered), "diagonal_slope": slope, "step": (step_r, step_c), "output_red": output_red})
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors: raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    return _analyse(grid)[1]


def rule_mirror(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors: raise ValueError("; ".join(errors))
    out = full_grid(info["grid_size"], info["grid_size"], 7)
    for r, c in info["output_red"]: out[r][c] = 2
    return out


def _witness_single(g):
    i, e = _analyse(g); return not e and i["n_cells"] == 1

def _witness_multi_main(g):
    i, e = _analyse(g); return not e and i["n_cells"] >= 2 and i["diagonal_slope"] == "main"

def _witness_multi_anti(g):
    i, e = _analyse(g); return not e and i["n_cells"] >= 2 and i["diagonal_slope"] == "anti"

def _witness_count_five(g):
    i, e = _analyse(g); return not e and i["n_cells"] == 5

def _witness_noncanonical_size(g):
    i, e = _analyse(g); return not e and i["grid_size"] != 16
SEMANTIC_WITNESSES = {
    "single_cell_quadrant_branch": _witness_single,
    "multi_cell_main_diagonal": _witness_multi_main,
    "multi_cell_anti_diagonal": _witness_multi_anti,
    "maximum_declared_count": _witness_count_five,
    "off_canonical_grid_size": _witness_noncanonical_size,
}


def _rival_identity(grid): return [list(row) for row in grid]
def _rival_shift_without_growth(grid):
    info, errors = _analyse(grid)
    if errors: raise ValueError("; ".join(errors))
    out = full_grid(info["grid_size"], info["grid_size"], 7)
    for r, c in info["output_red"][:-1]: out[r][c] = 2
    return out
SEMANTIC_RIVALS = {"identity_no_move": _rival_identity, "shift_without_growth": _rival_shift_without_growth}
WITNESS_RIVALS = {name: list(SEMANTIC_RIVALS) for name in SEMANTIC_WITNESSES}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED: return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []; counts: set[int] = set(); slopes: set[str] = set(); sizes: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair"); continue
        info, errors = _analyse(pair["input"])
        if errors: reasons.append(f"demo {index} malformed: {errors[0]}"); continue
        if pair["output"] != rule_mirror(pair["input"]): reasons.append(f"demo {index} output is not the N-step, N+1-cell transform")
        counts.add(info["n_cells"]); slopes.add(info["diagonal_slope"]); sizes.add(info["grid_size"])
    if counts != {1, 2, 3, 4, 5}: reasons.append(f"demonstrations do not cover every count 1..5: {sorted(counts)}")
    if slopes != set(SLOPES): reasons.append(f"demonstrations do not cover both diagonal slopes: {sorted(slopes)}")
    if 16 not in sizes or len(sizes) < 2: reasons.append("demonstrations must combine a canonical 16x16 case with a different size")
    if not isinstance(query, dict) or "input" not in query: reasons.append("query is not an input/output pair")
    else:
        _, qerr = _analyse(query["input"])
        if qerr: reasons.append(f"query malformed: {qerr[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]): reasons.append("query output does not match the authoritative transform")
    return reasons
