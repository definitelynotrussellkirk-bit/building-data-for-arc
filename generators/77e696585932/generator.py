"""Generator for ARC task 1a07d186 / content hash 77e696585932.

The input contains one or more full-span, solid, nonzero rows or columns plus
isolated off-line pixels.  A pixel whose color matches a full line is erased
from its source location and placed one cell outside the nearest matching line.
Rows win an exact row-versus-column distance tie.  Full lines remain unchanged;
off-line colors with no matching full line are distractors and disappear.

The three-example schedule covers row-only scenes, column-only scenes, and a
same-color row/column cross containing row-nearer, column-nearer, and exact-tie
pixels.  Every scene also contains distractors.  This directly rebuts row-only,
column-only, fixed-direction, keep-all-pixels, modal-color, and marker-as-answer
shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "77e696585932"
TASK_ID = GENERATOR_ID
RULE_HASH = "315cb8671701"
VERSION = "2.0.0"

SUMMARY = (
    "Keep every solid nonzero full row or column. Erase all other cells, then "
    "move each isolated off-line pixel whose color matches a full line to the "
    "cell immediately outside its nearest matching line. Compare row and column "
    "distance, choosing the row on an exact tie. Off-line colors without a "
    "matching line are distractors and disappear."
)

INVARIANTS = [
    "background is 0 and the grid is rectangular",
    "there is at least one solid nonzero full row or full column",
    "every line color has at least one isolated matching off-line pixel",
    "matching pixels start at least two cells from their nearest matching line",
    "at least one isolated off-line distractor color has no matching full line",
    "matching destinations are in bounds, off all full lines, and pairwise distinct",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
SCENE_PROFILES = ("rows", "columns", "cross")
_CANONICAL_SHAPES = ((15, 14), (18, 19), (15, 16), (19, 26))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled across canonical-sized 12..20 grids",
        "valid": "12..20",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled across canonical-sized 12..26 grids",
        "valid": "12..26",
    },
    "scene_profile": {
        "type": "enum",
        "default": "three-example rows/columns/cross schedule",
        "valid": ["rows", "columns", "cross"],
    },
    "matching_pixel_count": {
        "type": "int",
        "default": "difficulty-scheduled 3..8",
        "valid": "3..8",
    },
    "distractor_count": {
        "type": "int",
        "default": "difficulty-scheduled 1..3",
        "valid": "1..3",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _full_lines(grid: list[list[int]]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    rows = [
        (r, grid[r][0])
        for r in range(h)
        if grid[r][0] != 0 and len(set(grid[r])) == 1
    ]
    cols = [
        (c, grid[0][c])
        for c in range(w)
        if grid[0][c] != 0 and len({grid[r][c] for r in range(h)}) == 1
    ]
    return rows, cols


def _nearest_destination(
    r: int,
    c: int,
    color: int,
    full_rows: list[tuple[int, int]],
    full_cols: list[tuple[int, int]],
) -> dict[str, Any]:
    row_matches = [(abs(rr - r), rr) for rr, value in full_rows if value == color]
    col_matches = [(abs(cc - c), cc) for cc, value in full_cols if value == color]
    dr, br = min(row_matches) if row_matches else (9999, -1)
    dc, bc = min(col_matches) if col_matches else (9999, -1)
    if dr <= dc:
        dest = (br - 1 if r < br else br + 1, c)
        branch = "tie_row" if dr == dc and dc != 9999 else "row"
        side = "above" if r < br else "below"
    else:
        dest = (r, bc - 1 if c < bc else bc + 1)
        branch = "column"
        side = "left" if c < bc else "right"
    return {
        "row_distance": dr,
        "column_distance": dc,
        "destination": dest,
        "branch": branch,
        "side": side,
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    full_rows, full_cols = _full_lines(g)
    row_set = {r for r, _ in full_rows}
    col_set = {c for c, _ in full_cols}
    line_colors = {value for _, value in full_rows + full_cols}
    if not full_rows and not full_cols:
        errors.append("no solid nonzero full row or column")
        return {
            "errors": errors,
            "h": h,
            "w": w,
            "full_rows": full_rows,
            "full_cols": full_cols,
        }

    off_line: list[tuple[int, int, int]] = []
    matching: list[dict[str, Any]] = []
    distractors: list[tuple[int, int, int]] = []
    for r in range(h):
        for c in range(w):
            value = g[r][c]
            if value == 0 or r in row_set or c in col_set:
                continue
            cell = (r, c, value)
            off_line.append(cell)
            if value in line_colors:
                move = _nearest_destination(r, c, value, full_rows, full_cols)
                matching.append({"cell": cell, **move})
            else:
                distractors.append(cell)

    if not matching:
        errors.append("no off-line pixel matches a full-line color")
    if not distractors:
        errors.append("no off-line distractor color absent from all full lines")

    for r, c, _ in off_line:
        neighbors = [
            (r + dr, c + dc)
            for dr, dc in _DIRS4
            if 0 <= r + dr < h and 0 <= c + dc < w
        ]
        if any(g[nr][nc] != 0 and nr not in row_set and nc not in col_set for nr, nc in neighbors):
            errors.append(f"off-line nonzero cell ({r},{c}) is not 4-neighbor isolated")
            break

    matched_colors = {item["cell"][2] for item in matching}
    missing_line_colors = sorted(line_colors - matched_colors)
    if missing_line_colors:
        errors.append(f"full-line colors without a matching off-line pixel: {missing_line_colors}")

    destinations: list[tuple[int, int]] = []
    source_cells = {(r, c) for r, c, _ in off_line}
    for item in matching:
        r, c, _ = item["cell"]
        nearest = min(item["row_distance"], item["column_distance"])
        if nearest < 2:
            errors.append(f"matching pixel ({r},{c}) is already adjacent to its nearest line")
        dr, dc = item["destination"]
        if not (0 <= dr < h and 0 <= dc < w):
            errors.append(f"matching pixel ({r},{c}) moves out of bounds to ({dr},{dc})")
        elif dr in row_set or dc in col_set:
            errors.append(f"matching destination ({dr},{dc}) lies on a full line")
        elif (dr, dc) in source_cells:
            errors.append(f"matching destination ({dr},{dc}) overlaps an off-line source cell")
        destinations.append((dr, dc))
    if len(set(destinations)) != len(destinations):
        errors.append("two matching pixels share one destination")

    profile = None
    row_colors = [value for _, value in full_rows]
    col_colors = [value for _, value in full_cols]
    branches = {item["branch"] for item in matching}
    if len(full_rows) == 2 and not full_cols and len(set(row_colors)) == 2:
        profile = "rows"
    elif len(full_cols) == 3 and not full_rows and len(set(col_colors)) == 3:
        profile = "columns"
    elif (
        len(full_rows) == 1
        and len(full_cols) == 1
        and row_colors == col_colors
        and {"row", "column", "tie_row"}.issubset(branches)
    ):
        profile = "cross"

    return {
        "errors": sorted(set(errors)),
        "h": h,
        "w": w,
        "grid": g,
        "full_rows": full_rows,
        "full_cols": full_cols,
        "line_colors": line_colors,
        "off_line": off_line,
        "matching": matching,
        "distractors": distractors,
        "profile": profile,
        "branches": branches,
        "sides": {item["side"] for item in matching},
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding lessons."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if not 12 <= analysis["h"] <= 20:
        reasons.append(f"height {analysis['h']} is outside canonical envelope 12..20")
    if not 12 <= analysis["w"] <= 26:
        reasons.append(f"width {analysis['w']} is outside canonical envelope 12..26")
    palette_size = len({value for row in analysis["grid"] for value in row})
    if not 3 <= palette_size <= 5:
        reasons.append(f"palette size {palette_size} is outside canonical 3..5")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    if analysis["profile"] is None:
        raise ValueError("scene does not match any declared generated profile")
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "scene_profile": analysis["profile"],
        "matching_pixel_count": len(analysis["matching"]),
        "distractor_count": len(analysis["distractors"]),
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        **observe_overrides(grid),
        "full_row_count": len(analysis["full_rows"]),
        "full_column_count": len(analysis["full_cols"]),
        "line_color_count": len(analysis["line_colors"]),
        "branches": sorted(analysis["branches"]),
        "sides": sorted(analysis["sides"]),
        "palette_size": len({value for row in analysis["grid"] for value in row}),
    }


def _scheduled_offset(seed: int, label: str, modulus: int) -> int:
    return stable_rng(seed, f"{TASK_ID}|{label}", VERSION).randrange(modulus)


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))



def _sample_separated(values: Iterable[int], count: int, min_gap: int, rng) -> list[int]:
    choices = list(values)
    combinations: list[tuple[int, ...]] = []
    if count == 2:
        combinations = [(a, b) for i, a in enumerate(choices) for b in choices[i + 1:] if b - a >= min_gap]
    elif count == 3:
        combinations = [
            (a, b, c)
            for i, a in enumerate(choices)
            for j, b in enumerate(choices[i + 1:], start=i + 1)
            for c in choices[j + 1:]
            if b - a >= min_gap and c - b >= min_gap
        ]
    else:
        raise ValueError("only two or three separated positions are supported")
    if not combinations:
        raise RuntimeError(f"no {count}-position layout with gap {min_gap}")
    return list(rng.choice(combinations))

def _candidate_ok(
    candidate: dict[str, Any], selected: list[dict[str, Any]]
) -> bool:
    cell = (candidate["r"], candidate["c"])
    dest = candidate["destination"]
    selected_cells = {(item["r"], item["c"]) for item in selected}
    selected_dests = {item["destination"] for item in selected}
    if cell in selected_cells or dest in selected_dests:
        return False
    if cell in selected_dests or dest in selected_cells:
        return False
    if any(abs(cell[0] - r) + abs(cell[1] - c) <= 1 for r, c in selected_cells):
        return False
    return True


def _select_matching(
    candidates: list[dict[str, Any]],
    mandatory: list[Callable[[dict[str, Any]], bool]],
    count: int,
    rng,
) -> list[dict[str, Any]]:
    for _ in range(80):
        pool = list(candidates)
        rng.shuffle(pool)
        selected: list[dict[str, Any]] = []
        success = True
        for predicate in mandatory:
            chosen = next(
                (item for item in pool if predicate(item) and _candidate_ok(item, selected)),
                None,
            )
            if chosen is None:
                success = False
                break
            selected.append(chosen)
            pool.remove(chosen)
        if not success:
            continue
        for item in pool:
            if len(selected) >= count:
                break
            if _candidate_ok(item, selected):
                selected.append(item)
        if len(selected) == count:
            return selected
    raise RuntimeError(f"unable to place {count} isolated matching pixels")


def _row_candidates(
    h: int, w: int, rows: list[tuple[int, int]]
) -> list[dict[str, Any]]:
    row_set = {r for r, _ in rows}
    candidates: list[dict[str, Any]] = []
    for rr, color in rows:
        for r in range(h):
            if r in row_set or abs(r - rr) < 2:
                continue
            for c in range(1, w - 1):
                destination = (rr - 1 if r < rr else rr + 1, c)
                candidates.append({
                    "r": r,
                    "c": c,
                    "color": color,
                    "branch": "row",
                    "side": "above" if r < rr else "below",
                    "destination": destination,
                })
    return candidates


def _column_candidates(
    h: int, w: int, cols: list[tuple[int, int]]
) -> list[dict[str, Any]]:
    col_set = {c for c, _ in cols}
    candidates: list[dict[str, Any]] = []
    for cc, color in cols:
        for c in range(w):
            if c in col_set or abs(c - cc) < 2:
                continue
            for r in range(1, h - 1):
                destination = (r, cc - 1 if c < cc else cc + 1)
                candidates.append({
                    "r": r,
                    "c": c,
                    "color": color,
                    "branch": "column",
                    "side": "left" if c < cc else "right",
                    "destination": destination,
                })
    return candidates


def _cross_candidates(h: int, w: int, rr: int, cc: int, color: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for r in range(h):
        if r == rr:
            continue
        for c in range(w):
            if c == cc:
                continue
            dr, dc = abs(r - rr), abs(c - cc)
            if dr < 2 or dc < 2:
                continue
            if dr <= dc:
                branch = "tie_row" if dr == dc else "row"
                destination = (rr - 1 if r < rr else rr + 1, c)
                side = "above" if r < rr else "below"
            else:
                branch = "column"
                destination = (r, cc - 1 if c < cc else cc + 1)
                side = "left" if c < cc else "right"
            candidates.append({
                "r": r,
                "c": c,
                "color": color,
                "branch": branch,
                "side": side,
                "destination": destination,
            })
    return candidates


def _place_distractors(
    grid: list[list[int]],
    count: int,
    color: int,
    matching: list[dict[str, Any]],
    full_rows: Iterable[int],
    full_cols: Iterable[int],
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    row_set, col_set = set(full_rows), set(full_cols)
    blocked = {(item["r"], item["c"]) for item in matching}
    blocked |= {item["destination"] for item in matching}
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r not in row_set and c not in col_set and grid[r][c] == 0 and (r, c) not in blocked
    ]
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    matching_cells = {(item["r"], item["c"]) for item in matching}
    for r, c in candidates:
        if any(abs(r - rr) + abs(c - cc) <= 1 for rr, cc in matching_cells | set(selected)):
            continue
        selected.append((r, c))
        if len(selected) == count:
            break
    if len(selected) != count:
        raise RuntimeError(f"unable to place {count} isolated distractors")
    for r, c in selected:
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    band_offset = {"easy": 0, "medium": 1, "hard": 2}[band]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    profile = _draw_scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        SCENE_PROFILES[
            (_scheduled_offset(seed, "profile", len(SCENE_PROFILES)) + int(sample_index))
            % len(SCENE_PROFILES)
        ],
    )
    scheduled_h, scheduled_w = _CANONICAL_SHAPES[
        (_scheduled_offset(seed, "shape", len(_CANONICAL_SHAPES)) + int(sample_index) + band_offset)
        % len(_CANONICAL_SHAPES)
    ]
    h = _draw_scheduled_int(ctx, "grid_h", 12, 20, scheduled_h)
    w = _draw_scheduled_int(ctx, "grid_w", 12, 26, scheduled_w)
    matching_default = {
        "easy": 3 + ((int(sample_index) + _scheduled_offset(seed, "matching", 2)) % 2),
        "medium": 5 + ((int(sample_index) + _scheduled_offset(seed, "matching", 2)) % 2),
        "hard": 7 + ((int(sample_index) + _scheduled_offset(seed, "matching", 2)) % 2),
    }[band]
    matching_count = _draw_scheduled_int(
        ctx, "matching_pixel_count", 3, 8, matching_default
    )
    distractor_default = {"easy": 1, "medium": 2, "hard": 3}[band]
    distractor_count = _draw_scheduled_int(
        ctx, "distractor_count", 1, 3, distractor_default
    )

    n_line_colors = {"rows": 2, "columns": 3, "cross": 1}[profile]
    colors = ctx.draw_distinct_colors(
        "scene_colors", n=n_line_colors + 1, exclude={0}
    )
    line_colors, distractor_color = colors[:-1], colors[-1]
    rng = ctx.draw_rng(f"layout:{profile}:{band}")
    grid = full_grid(h, w, 0)

    if profile == "rows":
        row_positions = _sample_separated(range(2, h - 2), 2, 3, rng)
        lines = list(zip(row_positions, line_colors))
        for rr, color in lines:
            for c in range(w):
                grid[rr][c] = color
        candidates = _row_candidates(h, w, lines)
        mandatory = [
            lambda item, color=line_colors[0]: item["color"] == color and item["side"] == "above",
            lambda item, color=line_colors[1]: item["color"] == color and item["side"] == "below",
        ]
        matching = _select_matching(candidates, mandatory, matching_count, rng)
        full_rows, full_cols = row_positions, []
    elif profile == "columns":
        col_positions = _sample_separated(range(2, w - 2), 3, 3, rng)
        lines = list(zip(col_positions, line_colors))
        for cc, color in lines:
            for r in range(h):
                grid[r][cc] = color
        candidates = _column_candidates(h, w, lines)
        mandatory = [
            lambda item, color=line_colors[0]: item["color"] == color and item["side"] == "left",
            lambda item, color=line_colors[1]: item["color"] == color and item["side"] == "right",
            lambda item, color=line_colors[2]: item["color"] == color,
        ]
        matching = _select_matching(candidates, mandatory, matching_count, rng)
        full_rows, full_cols = [], col_positions
    else:
        rr = rng.randint(4, h - 5)
        cc = rng.randint(4, w - 5)
        color = line_colors[0]
        for c in range(w):
            grid[rr][c] = color
        for r in range(h):
            grid[r][cc] = color
        candidates = _cross_candidates(h, w, rr, cc, color)
        mandatory = [
            lambda item: item["branch"] == "row",
            lambda item: item["branch"] == "column",
            lambda item: item["branch"] == "tie_row",
        ]
        matching = _select_matching(candidates, mandatory, matching_count, rng)
        full_rows, full_cols = [rr], [cc]

    for item in matching:
        grid[item["r"]][item["c"]] = item["color"]
    _place_distractors(
        grid,
        distractor_count,
        distractor_color,
        matching,
        full_rows,
        full_cols,
        rng,
    )

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "scene_profile": profile,
        "matching_pixel_count": matching_count,
        "distractor_count": distractor_count,
    }
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, observed {observed}")
    return grid


def _expected_output(grid: Any) -> list[list[int]]:
    """Python mirror for semantic tests; the canonical Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["h"], analysis["w"], 0)
    for r, _ in analysis["full_rows"]:
        out[r] = list(analysis["grid"][r])
    for c, _ in analysis["full_cols"]:
        for r in range(analysis["h"]):
            out[r][c] = analysis["grid"][r][c]
    for item in analysis["matching"]:
        r, c = item["destination"]
        out[r][c] = item["cell"][2]
    return out


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes proving self_check rejects structural impostors."""
    base = generate(20260725, 4, difficulty="medium", scene_profile="rows")
    analysis = _analyze(base)
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_lines = [list(row) for row in base]
    for r, _ in analysis["full_rows"]:
        no_lines[r] = [0] * analysis["w"]
    fixtures.append(("no_full_line", no_lines))

    no_matching = [list(row) for row in base]
    for item in analysis["matching"]:
        r, c, _ = item["cell"]
        no_matching[r][c] = 0
    fixtures.append(("no_matching_pixels", no_matching))

    no_distractor = [list(row) for row in base]
    for r, c, _ in analysis["distractors"]:
        no_distractor[r][c] = 0
    fixtures.append(("no_distractor", no_distractor))

    adjacent = [list(row) for row in base]
    item = analysis["matching"][0]
    r, c, color = item["cell"]
    adjacent[r][c] = 0
    ar, ac = item["destination"]
    adjacent[ar][ac] = color
    fixtures.append(("already_adjacent_to_line", adjacent))

    recombined = [list(row) for row in base]
    line_row, old_color = analysis["full_rows"][0]
    used = {value for row in base for value in row}
    replacement = next(value for value in range(1, 10) if value not in used)
    recombined[line_row] = [replacement] * analysis["w"]
    assert replacement not in used and old_color != replacement
    fixtures.append(("novel_line_color_without_matching_pixel", recombined))
    return fixtures


def _rival_output(grid: Any, mode: str) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["h"], analysis["w"], 0)
    for r, _ in analysis["full_rows"]:
        out[r] = list(analysis["grid"][r])
    for c, _ in analysis["full_cols"]:
        for r in range(analysis["h"]):
            out[r][c] = analysis["grid"][r][c]

    items = list(analysis["matching"])
    if mode == "move_only_first":
        items = items[:1]
    for item in items:
        r, c, color = item["cell"]
        row_matches = [(abs(rr - r), rr) for rr, value in analysis["full_rows"] if value == color]
        col_matches = [(abs(cc - c), cc) for cc, value in analysis["full_cols"] if value == color]
        if mode == "rows_only":
            if not row_matches:
                continue
            _, br = min(row_matches)
            destination = (br - 1 if r < br else br + 1, c)
        elif mode == "columns_only":
            if not col_matches:
                continue
            _, bc = min(col_matches)
            destination = (r, bc - 1 if c < bc else bc + 1)
        elif mode == "tie_to_column":
            dr, br = min(row_matches) if row_matches else (9999, -1)
            dc, bc = min(col_matches) if col_matches else (9999, -1)
            if dr < dc:
                destination = (br - 1 if r < br else br + 1, c)
            else:
                destination = (r, bc - 1 if c < bc else bc + 1)
        else:
            destination = item["destination"]
        out[destination[0]][destination[1]] = color

    if mode == "keep_distractors":
        for r, c, color in analysis["distractors"]:
            out[r][c] = color
    return out


def _rival_rows_only(grid):
    return _rival_output(grid, "rows_only")


def _rival_columns_only(grid):
    return _rival_output(grid, "columns_only")


def _rival_tie_to_column(grid):
    return _rival_output(grid, "tie_to_column")


def _rival_keep_distractors(grid):
    return _rival_output(grid, "keep_distractors")


def _rival_move_only_first(grid):
    return _rival_output(grid, "move_only_first")


SEMANTIC_RIVALS = {
    "rows_only": _rival_rows_only,
    "columns_only": _rival_columns_only,
    "tie_to_column": _rival_tie_to_column,
    "keep_distractors": _rival_keep_distractors,
    "move_only_first": _rival_move_only_first,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "tie_to_column": _rival_tie_to_column,
}

SCHEDULE_PROFILES = SCENE_PROFILES


def schedule_profile(seed, sample_index, difficulty=None):
    return SCENE_PROFILES[
        (_scheduled_offset(seed, "profile", len(SCENE_PROFILES)) + int(sample_index))
        % len(SCENE_PROFILES)
    ]


def _profile_witness(name: str):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["profile"] == name

    return predicate


SEMANTIC_WITNESSES = {
    "row_full_lines": _profile_witness("rows"),
    "column_full_lines": _profile_witness("columns"),
    "same_color_row_column_cross": _profile_witness("cross"),
    "nearest_row_branch": lambda grid: (
        not _analyze(grid)["errors"] and "row" in _analyze(grid)["branches"]
    ),
    "nearest_column_branch": lambda grid: (
        not _analyze(grid)["errors"] and "column" in _analyze(grid)["branches"]
    ),
    "row_wins_exact_tie": lambda grid: (
        not _analyze(grid)["errors"] and "tie_row" in _analyze(grid)["branches"]
    ),
    "distractor_erasure_cue": lambda grid: (
        not _analyze(grid)["errors"] and bool(_analyze(grid)["distractors"])
    ),
    "multiple_matching_pixels": lambda grid: (
        not _analyze(grid)["errors"] and len(_analyze(grid)["matching"]) >= 3
    ),
}

WITNESS_RIVALS = {
    "row_full_lines": ["columns_only"],
    "column_full_lines": ["rows_only"],
    "same_color_row_column_cross": ["tie_to_column"],
    "nearest_row_branch": ["columns_only"],
    "nearest_column_branch": ["rows_only"],
    "row_wins_exact_tie": ["tie_to_column"],
    "distractor_erasure_cue": ["keep_distractors"],
    "multiple_matching_pixels": ["move_only_first"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one row, one column, and one mixed cross demonstration."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        analysis = _analyze(pair.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = _expected_output(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
        analyses.append(analysis)
        if analysis["profile"] is not None:
            profiles.add(analysis["profile"])

    missing_profiles = sorted(set(SCENE_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit profiles {missing_profiles}")
    branches = {branch for analysis in analyses for branch in analysis["branches"]}
    for branch in ("row", "column", "tie_row"):
        if branch not in branches:
            reasons.append(f"demonstrations omit the {branch} nearest-line branch")
    if not all(analysis["distractors"] for analysis in analyses):
        reasons.append("every demonstration must include an erased distractor")
    if not any(len(analysis["line_colors"]) >= 3 for analysis in analyses):
        reasons.append("no demonstration rebuts a modal-line-color shortcut")
    if not any({"above", "below"}.issubset(analysis["sides"]) for analysis in analyses):
        reasons.append("no demonstration shows both sides of a full row")
    if not any({"left", "right"}.issubset(analysis["sides"]) for analysis in analyses):
        reasons.append("no demonstration shows both sides of a full column")

    query_analysis = _analyze(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside the teaching grammar")
    else:
        if query_analysis["profile"] not in profiles:
            reasons.append("query profile was not demonstrated")
        if query.get("output") != _expected_output(query["input"]):
            reasons.append("query output disagrees with the canonical rule")
    return sorted(set(reasons))
