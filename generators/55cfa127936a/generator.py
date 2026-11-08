"""Semantic generator for ARC task 55cfa127936a.

For each column, preserve only its topmost yellow (4) cell and clear every
lower yellow cell to zero.  Columns without yellow remain empty.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "55cfa127936a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4ad262163127"
SUMMARY = "Keep only the topmost yellow cell in each column and clear all lower yellow cells."
INVARIANTS = [
    "background is zero and the only foreground color is yellow 4",
    "each active column contains one or more yellow cells",
    "inactive columns remain all zero",
    "the output retains exactly the minimum-row yellow in each active column",
    "at least one active column has multiple yellow cells so erasure is visible",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
GENERAL_PROFILES = (
    "mixed_counts", "all_multi_active", "one_inactive_column", "many_inactive_columns",
    "all_columns_active", "top_boundary", "bottom_topmost", "consecutive_stacks",
    "spaced_stacks", "full_columns", "two_per_active", "varied_counts", "shared_top_row",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "uniform rng over three public and thirteen semantic lessons",
                           "valid": "|".join(SCENE_PROFILES)}}

_PUBLIC_INPUTS = {
    "public_train_1": ("0400404", "0000004", "4004000", "0400000", "0040400", "4000004"),
    "public_train_2": ("00040000", "04000040", "40000000", "00004000", "40000400", "00004040"),
    "public_test_1": ("000040000", "004000400", "400000004", "040004000", "400000004", "000400000"),
}
_PUBLIC_SIGNATURES = {tuple(tuple(int(v) for v in row) for row in mask): profile
                      for profile, mask in _PUBLIC_INPUTS.items()}


def _band(difficulty):
    if difficulty in (None, "medium"): return "medium"
    if difficulty in ("easy", "hard"): return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid: return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]: return ["grid must have non-empty rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid): return ["grid must be rectangular"], h, w
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 4):
                return ["cells must be integer colors 0 or 4"], h, w
    return [], h, w


def _classify(info):
    positions, counts = info["positions"], info["active_counts"]
    active = [cells for cells in positions if cells]
    inactive = len(positions) - len(active); h, w = info["height"], info["width"]
    if active and all(len(cells) == h for cells in active): return "full_columns"
    tops = [cells[0] for cells in active]
    if tops and all(top == 0 for top in tops): return "top_boundary"
    if tops and min(tops) >= h // 2: return "bottom_topmost"
    if tops and len(set(tops)) == 1: return "shared_top_row"
    if active and all(all(b == a + 1 for a, b in zip(cells, cells[1:])) for cells in active) and any(len(cells) >= 3 for cells in active): return "consecutive_stacks"
    if active and all(all(b >= a + 2 for a, b in zip(cells, cells[1:])) for cells in active) and any(len(cells) >= 3 for cells in active): return "spaced_stacks"
    if counts and all(count == 2 for count in counts): return "two_per_active"
    if len(set(counts)) >= 4: return "varied_counts"
    if inactive >= max(3, w // 2): return "many_inactive_columns"
    if inactive == 0: return "all_columns_active"
    if counts and min(counts) >= 2: return "all_multi_active"
    if inactive == 1: return "one_inactive_column"
    return "mixed_counts"


def _analysis(grid):
    errors, h, w = _validate_grid(grid); result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors: return result
    positions = tuple(tuple(r for r in range(h) if grid[r][c] == 4) for c in range(w))
    active_counts = tuple(len(cells) for cells in positions if cells)
    total = sum(active_counts)
    if len(active_counts) < 4: errors.append("at least four active columns are required for a useful lesson")
    if total < 8: errors.append("at least eight yellow cells are required for canonical-scale structure")
    if not active_counts or max(active_counts) < 2: errors.append("at least one column must visibly erase a lower yellow")
    if total == h * w: errors.append("an all-yellow field is an uninformative degenerate")
    output = [[0 for _ in range(w)] for _ in range(h)]
    for c, cells in enumerate(positions):
        if cells: output[cells[0]][c] = 4
    info = {"positions": positions, "active_counts": active_counts, "active_columns": len(active_counts),
            "inactive_columns": w - len(active_counts), "total_marks": total, "output": output}
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature) or _classify(result | info)
    if profile not in SCENE_PROFILES: errors.append("grid does not match a declared topmost-column lesson")
    if output == [list(row) for row in grid]: errors.append("lesson must visibly erase at least one lower yellow")
    result.update(info); result.update({"scene_profile": profile, "errors": errors}); return result


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


def _dimensions(rng, band):
    (h1, h2), (w1, w2) = {"easy": ((6, 8), (7, 10)), "medium": ((9, 12), (10, 14)), "hard": ((13, 16), (14, 18))}[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _choose_positions(rng, h, count, mode):
    if mode == "top":
        others = rng.sample(range(1, h), count - 1); return tuple(sorted((0, *others)))
    if mode == "bottom": return tuple(sorted(rng.sample(range(h // 2, h), count)))
    if mode == "consecutive":
        start = rng.randint(0, h - count); return tuple(range(start, start + count))
    if mode == "spaced":
        pool = list(range(0, h, 2))
        if len(pool) < count: pool = list(range(1, h, 2)) + pool
        return tuple(sorted(rng.sample(pool, count)))
    return tuple(sorted(rng.sample(range(h), count)))


def _general_grid(rng, profile, band):
    h, w = _dimensions(rng, band); inactive = 2; mode = "random"; counts = None
    if profile == "one_inactive_column": inactive = 1
    elif profile == "many_inactive_columns": inactive = min(max(3, w // 2), w - 4)
    elif profile == "all_columns_active": inactive = 0
    elif profile == "all_multi_active": counts = [3] * (w - inactive)
    elif profile == "top_boundary": mode = "top"; counts = [2] * (w - inactive)
    elif profile == "bottom_topmost": mode = "bottom"; counts = [2] * (w - inactive)
    elif profile == "consecutive_stacks": mode = "consecutive"; counts = [3] * (w - inactive)
    elif profile == "spaced_stacks": mode = "spaced"; counts = [3] * (w - inactive)
    elif profile == "full_columns":
        # Keep zero as the unambiguous background even when every active
        # column is filled from top to bottom.
        w = max(w, 9); inactive = w - 4; counts = [h] * 4
    elif profile == "two_per_active": counts = [2] * (w - inactive)
    elif profile == "varied_counts": counts = [1 + i % min(5, h) for i in range(w - inactive)]
    elif profile == "shared_top_row": counts = [2] * (w - inactive)
    elif profile not in {"mixed_counts"}: raise ValueError(f"unknown scene_profile: {profile!r}")
    active_n = w - inactive
    if profile in {"mixed_counts", "one_inactive_column"}:
        counts = ([3, 2] + [1 + (i % 3) for i in range(active_n - 2)])[:active_n]
    elif counts is None:
        counts = ([3, 2] + [1 + (i % 3) for i in range(active_n - 2)])[:active_n]
    active_cols = sorted(rng.sample(range(w), active_n)); grid = [[0 for _ in range(w)] for _ in range(h)]
    for index, (col, count) in enumerate(zip(active_cols, counts)):
        local_mode = mode
        if profile == "shared_top_row":
            chosen = (1, min(h - 1, 3 + index % max(1, h - 3)))
        elif profile == "spaced_stacks" and index == 0:
            chosen = (1, 3, 5)[:count]
        elif profile == "consecutive_stacks" and index == 0:
            chosen = (1, 2, 3)[:count]
        elif profile == "varied_counts" and index == 0:
            chosen = (0,)
        elif profile == "varied_counts" and index == 1:
            chosen = (1, 3)[:count]
        elif profile == "varied_counts" and index == 2:
            chosen = (0, 1, 3)[:count]
        elif profile in {"mixed_counts", "one_inactive_column", "many_inactive_columns", "all_columns_active", "all_multi_active"} and index == 0:
            chosen = (0, 1, 3)[:count]
        elif profile in {"mixed_counts", "one_inactive_column", "many_inactive_columns", "all_columns_active", "all_multi_active"} and index == 1 and count >= 2:
            chosen = (0, 2, 4)[:count]
        elif profile in {"mixed_counts", "one_inactive_column", "many_inactive_columns", "all_columns_active", "all_multi_active"} and index == 2:
            chosen = (1, 2, 4)[:count]
        else:
            chosen = _choose_positions(rng, h, min(count, h), local_mode)
        for row in chosen: grid[row][col] = 4
    return grid


def _public_grid(profile): return [[int(value) for value in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES: raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES)); rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}: raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid); errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown: errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES: errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested: errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
