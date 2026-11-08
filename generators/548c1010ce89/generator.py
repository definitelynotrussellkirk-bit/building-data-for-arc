"""Semantic generator for ARC task 548c1010ce89.

Paint every entirely zero row and every entirely zero column red (2), while
preserving every cell in rows and columns that contain foreground content.
Either family of empty lines may occur without the other.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "548c1010ce89"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "506bc3722b18"
SUMMARY = "Replace every all-zero row and all-zero column with red 2, preserving all other cells."

INVARIANTS = [
    "zero is the semantic background used to detect empty lines",
    "at least one all-zero row or all-zero column exists",
    "every line not selected as empty contains foreground",
    "all cells in an empty row become red 2",
    "all cells in an empty column become red 2",
    "every cell outside empty rows and columns is preserved exactly",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_PROFILES = (
    "rows_and_cols_sparse", "rows_and_cols_dense", "columns_only", "rows_only",
    "single_empty_row", "single_empty_col", "multiple_empty_rows", "multiple_empty_cols",
    "boundary_empty_lines", "adjacent_empty_lines", "multicolor_foreground", "red_foreground_preserved",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "scheduled broad draws with two both-axis witnesses per four samples",
                           "valid": "|".join(SCENE_PROFILES)}}

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("both_axes_a", "broad_a", "both_axes_b", "broad_b")
_BOTH_AXIS_PROFILES = tuple(
    profile for profile in SCENE_PROFILES
    if profile not in {"public_train_1", "columns_only", "rows_only"}
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-cycle whose every three-of-four rotation contains a both-axis witness."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


_PUBLIC_INPUTS = {
    "public_train_1": (
        "88880888880088", "08000088880888", "88080888880088", "80880880080880",
        "88880880000888", "88800880800888", "80880888880008", "88000800880088",
        "80080888080888", "88080888880080", "08080000000808", "88880888880080",
    ),
    "public_train_2": (
        "1000111101101010111", "1010111100111111011", "1111001101000101010",
        "1011111101111111111", "1011011101111111111", "1101011000010110001",
        "1001101001111111010", "1100111101011101111", "0000000000000000000",
        "1110011101001111111", "1100110001100010101", "1010100101111001111",
    ),
    "public_train_3": (
        "303333303330303", "303033303030030", "000000000000000", "300300330303300",
        "303333333303333", "303333330033033", "003030303003330", "300333003033003",
        "303333303333303", "300330333333330", "303333330333033", "303330300303330",
        "000000000000000", "303003033033330", "300303303033003", "300333330330033",
        "003303300303030",
    ),
    "public_test_1": (
        "4040440044440444440440400", "4440040440444444044440400", "0000000000000000000000000",
        "4044400444440444444440440", "4404440000444404440440444", "4440440444444444404040404",
        "4004040444444040444040444", "4444400404004400444000040", "0440440440440440040400404",
        "4440440044444004044400444", "4044400404404404404400004", "4404000444044444404440444",
        "0000000000000000000000000", "0440000044440440044440044", "4444440444404044044440444",
        "4444400404004444444400404", "0444440444440404404440440", "0444400444040404444440044",
        "4440440040444444444440000", "4404440440444044404400044", "0000000000000000000000000",
        "4444040404440000404440444", "0444440404044044044040444", "4444440440000444004440440",
        "4040440400044444040440040", "4404040040440440004040444", "4004440404444404444000444",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(value) for value in row) for row in mask): profile
    for profile, mask in _PUBLIC_INPUTS.items()
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _classify(info):
    rows, cols = info["empty_rows"], info["empty_cols"]
    if 2 in info["foreground_colors"]:
        return "red_foreground_preserved"
    if len(info["foreground_colors"]) > 1:
        return "multicolor_foreground"
    if not rows:
        return "columns_only"
    if not cols:
        return "rows_only"
    if len(rows) == 1:
        return "single_empty_row"
    if len(cols) == 1:
        return "single_empty_col"
    if len(rows) >= 4 and len(cols) <= 3:
        return "multiple_empty_rows"
    if len(cols) >= 4 and len(rows) <= 3:
        return "multiple_empty_cols"
    h, w = info["height"], info["width"]
    if any(index in (0, h - 1) for index in rows) or any(index in (0, w - 1) for index in cols):
        return "boundary_empty_lines"
    if any(b == a + 1 for a, b in zip(rows, rows[1:])) or any(b == a + 1 for a, b in zip(cols, cols[1:])):
        return "adjacent_empty_lines"
    return "rows_and_cols_dense" if info["active_density"] >= 0.68 else "rows_and_cols_sparse"


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    empty_rows = tuple(row for row in range(height) if all(grid[row][col] == 0 for col in range(width)))
    empty_cols = tuple(col for col in range(width) if all(grid[row][col] == 0 for row in range(height)))
    foreground = [(row, col, grid[row][col]) for row in range(height) for col in range(width) if grid[row][col] != 0]
    if not empty_rows and not empty_cols:
        errors.append("at least one all-zero row or column is required")
    if len(foreground) < 20:
        errors.append("foreground is too small to teach empty-line detection")
    active_area = max(1, (height - len(empty_rows)) * (width - len(empty_cols)))
    active_density = len(foreground) / active_area
    if active_density < 0.40:
        errors.append("foreground is too sparse for the canonical noisy-field family")
    output = [list(row) for row in grid]
    for row in empty_rows:
        output[row] = [2] * width
    for col in empty_cols:
        for row in range(height):
            output[row][col] = 2
    info = {
        "empty_rows": empty_rows, "empty_cols": empty_cols,
        "foreground_count": len(foreground),
        "foreground_colors": tuple(sorted({color for _, _, color in foreground})),
        "active_density": active_density, "output": output,
    }
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature) or _classify(result | info)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared empty-line lesson")
    if output == [list(row) for row in grid]:
        errors.append("lesson must visibly paint an empty line")
    result.update(info)
    result.update({"scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _axis_rule(grid, *, paint_rows, paint_cols):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    if paint_rows:
        for row in info["empty_rows"]:
            output[row] = [2] * info["width"]
    if paint_cols:
        for col in info["empty_cols"]:
            for row in range(info["height"]):
                output[row][col] = 2
    return output


def _rows_only_rule(grid):
    return _axis_rule(grid, paint_rows=True, paint_cols=False)


def _columns_only_rule(grid):
    return _axis_rule(grid, paint_rows=False, paint_cols=True)


def _has_both_axes(grid):
    info = _analysis(grid)
    return not info["errors"] and bool(info["empty_rows"]) and bool(info["empty_cols"])


def _has_rows_only(grid):
    info = _analysis(grid)
    return not info["errors"] and bool(info["empty_rows"]) and not info["empty_cols"]


def _has_columns_only(grid):
    info = _analysis(grid)
    return not info["errors"] and bool(info["empty_cols"]) and not info["empty_rows"]


def strict_canonical_like(grid):
    return self_check(grid)


SEMANTIC_RIVALS = {
    "rows_only": _rows_only_rule,
    "columns_only": _columns_only_rule,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "both_axes": _has_both_axes,
    "rows_only_branch": _has_rows_only,
    "columns_only_branch": _has_columns_only,
}
WITNESS_RIVALS = {"both_axes": ["rows_only", "columns_only"]}
BRANCH_WITNESSES = ("rows_only_branch", "columns_only_branch")


def _dimensions(rng, band):
    ranges = {"easy": ((12, 14), (14, 16)), "medium": ((15, 19), (15, 20)), "hard": ((23, 27), (23, 27))}
    (h1, h2), (w1, w2) = ranges[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _separated_indices(rng, size, count, *, boundary=False, adjacent=False):
    if boundary:
        chosen = {0}
        pool = list(range(2, size - 1))
    elif adjacent:
        start = rng.randint(1, size - count - 1)
        return tuple(range(start, start + count))
    else:
        chosen, pool = set(), list(range(1, size - 1))
    rng.shuffle(pool)
    for value in pool:
        if all(abs(value - prior) > 1 for prior in chosen):
            chosen.add(value)
            if len(chosen) == count:
                break
    if len(chosen) != count:
        raise RuntimeError("could not place separated empty lines")
    return tuple(sorted(chosen))


def _general_grid(rng, profile, band):
    height, width = _dimensions(rng, band)
    row_count = col_count = 2
    boundary = adjacent = False
    density = 0.55
    palette_size = 1
    include_red = False
    if profile == "rows_and_cols_dense": density = 0.82
    elif profile == "columns_only": row_count = 0
    elif profile == "rows_only": col_count = 0
    elif profile == "single_empty_row": row_count, col_count = 1, 2
    elif profile == "single_empty_col": row_count, col_count = 2, 1
    elif profile == "multiple_empty_rows": row_count, col_count = 4, 2
    elif profile == "multiple_empty_cols": row_count, col_count = 2, 4
    elif profile == "boundary_empty_lines": boundary = True
    elif profile == "adjacent_empty_lines": adjacent = True
    elif profile == "multicolor_foreground": palette_size = 3
    elif profile == "red_foreground_preserved": include_red = True
    elif profile != "rows_and_cols_sparse": raise ValueError(f"unknown scene_profile: {profile!r}")

    empty_rows = set(_separated_indices(rng, height, row_count, boundary=boundary, adjacent=adjacent)) if row_count else set()
    empty_cols = set(_separated_indices(rng, width, col_count, boundary=boundary, adjacent=adjacent)) if col_count else set()
    active_rows = [row for row in range(height) if row not in empty_rows]
    active_cols = [col for col in range(width) if col not in empty_cols]
    colors = [color for color in range(1, 10) if color != 2]
    rng.shuffle(colors)
    palette = colors[:palette_size]
    if include_red:
        palette = [2, colors[0]]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    active_cells = [(row, col) for row in active_rows for col in active_cols]
    rng.shuffle(active_cells)
    selected = active_cells[:round(len(active_cells) * density)]
    for row, col in selected:
        grid[row][col] = rng.choice(palette)
    for row in active_rows:
        if not any(grid[row][col] for col in active_cols):
            grid[row][rng.choice(active_cols)] = rng.choice(palette)
    for col in active_cols:
        if not any(grid[row][col] for row in active_rows):
            grid[rng.choice(active_rows)][col] = rng.choice(palette)
    for index, color in enumerate(palette):
        if not any(value == color for row in grid for value in row):
            row, col = active_cells[index]
            grid[row][col] = color
    if include_red and not any(value == 2 for row in grid for value in row):
        grid[active_rows[0]][active_cols[0]] = 2
    return grid


def _public_grid(profile):
    return [[int(value) for value in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = (
        SCENE_PROFILES
        if requested is not None or scheduled.startswith("broad_")
        else _BOTH_AXIS_PROFILES
    )
    profile = context.draw_choice("scene_profile", list(profile_options))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors


def lesson_identifiable(demos, query):
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the task grammar: {errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the empty-line rule")
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the task grammar: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the empty-line rule")
    if reasons or len(valid_demos) != len(demos):
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but predicts a different query"
                )
    return reasons
