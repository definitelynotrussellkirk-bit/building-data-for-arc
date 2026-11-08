"""Semantic generator for ARC task 661dffbdf39a.

Detect rows and columns containing a strict majority of gray cells.  Output
only those clean separator lines, coloring every intersection with the one
non-black/non-gray marker color found in the noisy input.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "661dffbdf39a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d006d6b4ed8b"
SUMMARY = "Clean majority-gray rows and columns and mark all intersections with the noise color."
INVARIANTS = [
    "black is the background and gray is the separator-line color",
    "at least two rows and two columns contain a strict majority of gray cells",
    "exactly one non-black/non-gray color supplies both noise and intersection markers",
    "the output removes all noise, completes the detected lines, and marks every row-column intersection",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_COUNTS = {
    "grid_2x2": (2, 2), "grid_2x4": (2, 4), "grid_3x2": (3, 2),
    "grid_3x4": (3, 4), "grid_4x3": (4, 3), "grid_5x6": (5, 6),
}
GENERAL_PROFILES = tuple(GENERAL_COUNTS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "weighted exact-public and generalized line layouts", "valid": "public_train_1|public_train_2|public_train_3|public_test_1|grid_2x2|grid_2x4|grid_3x2|grid_3x4|grid_4x3|grid_5x6"}}

_PUBLIC_ROWS = {
    "public_train_1": (
        "00300533030500000","00003300003500000","00003500003500000","00000500300500000","00000500000300000","55555555555355555","33000500000500000","00000530330500000","00003500000500030","33030500000500000","00000500030500030","55353555535555553","00033503300500033","00000503000500003","30000300300300030","30000500003500033","30000300300500000","55555555555555555","30000500030500000","30300500000530303","30000530000500000",
    ),
    "public_train_2": (
        "0002500205000","2000502005000","0000202005000","0000500005000","2555555525555","0200502005000","0020500205020","0000500005000","0000500005000","5555555555255","0000500005000","0200502005000","0000500005002","0000500005000","5555555555555","0000500005000","0000500005000","0000500005000","0000500005200",
    ),
    "public_train_3": (
        "000400050005000540050405","040500050005000500050005","004400040005004500050045","555555555555555555555555","000500050005000500050005","000500050005000500050004","000504450005000500050005","555555555555555555554555","000500054044000500050005","000500050005000500050005","400500040005000400054005","555555555555555555555555","000500050005000500050405","000540050005400500050005","000540050005004500050005","555555555455554555555555","000400050005000504040005","000504054004004500050005","000504054405000504050005","555555554555555555555555","000500050004040440050005",
    ),
    "public_test_1": (
        "000005010001000015001005100","000001000005000005000005000","100015100005000005010001110","000005000005000005000005100","000005000005000005000005001","555555555551115555551551555","000005000005000005000005000","000005000005001005000005000","000005000005000005101005001","000001101005010005000005010","000105000001000001000005010","551555555555555155555155555","000005000005000005000005000","000005000001001005000005000","000005001005000005000005010","000005000005000005000005000","000005001005000005101005000","155555551555155551155555155","000005000005000105000005000","000005000001010005000005001","000005000001000005010005000","000005000005000005001005000",
    ),
}
_PUBLIC_INPUTS = {name: [[int(v) for v in row] for row in rows] for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid: return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]: return ["rows must be non-empty"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid): return ["grid must be rectangular"], h, w
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row): return ["cells must be integer ARC colors"], h, w
    return [], h, w


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors: return result
    colors = {v for row in grid for v in row}
    markers = colors - {0, 5}
    if len(markers) != 1: errors.append(f"exactly one marker color is required, found {len(markers)}")
    marker = next(iter(markers)) if len(markers) == 1 else None
    rows = tuple(r for r in range(h) if sum(v == 5 for v in grid[r]) > w // 2)
    cols = tuple(c for c in range(w) if sum(grid[r][c] == 5 for r in range(h)) > h // 2)
    if len(rows) < 2: errors.append("at least two strict-majority gray rows are required")
    if len(cols) < 2: errors.append("at least two strict-majority gray columns are required")
    output = [[0 for _ in range(w)] for _ in range(h)]
    if marker is not None:
        row_set, col_set = set(rows), set(cols)
        for r in range(h):
            for c in range(w):
                if r in row_set and c in col_set: output[r][c] = marker
                elif r in row_set or c in col_set: output[r][c] = 5
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None and not errors:
        profile = next((name for name, counts in GENERAL_COUNTS.items() if counts == (len(rows), len(cols))), None)
    if profile not in SCENE_PROFILES: errors.append("detected line counts do not match a declared scene profile")
    result.update({"marker": marker, "rows": rows, "cols": cols, "output": output, "scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid); profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _band(difficulty):
    if difficulty in (None, "medium"): return "medium"
    if difficulty in ("easy", "hard"): return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _general_grid(rng, profile, band):
    n_rows, n_cols = GENERAL_COUNTS[profile]
    bounds = {"easy": (12, 16), "medium": (17, 22), "hard": (23, 28)}
    lo, hi = bounds[band]
    for _ in range(80):
        h, w = rng.randint(max(lo, n_rows * 2 + 2), hi), rng.randint(max(lo, n_cols * 2 + 2), hi)
        active_rows = tuple(sorted(rng.sample(range(h), n_rows)))
        active_cols = tuple(sorted(rng.sample(range(w), n_cols)))
        marker = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
        grid = [[0 for _ in range(w)] for _ in range(h)]
        for r in active_rows:
            for c in range(w): grid[r][c] = 5
        for c in active_cols:
            for r in range(h): grid[r][c] = 5
        line_noise = rng.uniform(0.06, 0.22)
        for r in range(h):
            for c in range(w):
                if grid[r][c] == 5 and rng.random() < line_noise: grid[r][c] = marker
        distractor_density = rng.uniform(0.035, 0.11)
        for r in range(h):
            for c in range(w):
                if grid[r][c] == 0 and rng.random() < distractor_density: grid[r][c] = marker
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile and info["rows"] == active_rows and info["cols"] == active_cols:
            return grid
    raise ValueError(f"could not create majority-line scene for {profile}/{band}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES: raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    weighted = list(PUBLIC_PROFILES) + [p for p in GENERAL_PROFILES for _ in range(4)]
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile in PUBLIC_PROFILES: return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_grid(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    if info["errors"]: return list(info["errors"])
    if info["output"] == grid: return ["line cleaning must change the grid"]
    return []
