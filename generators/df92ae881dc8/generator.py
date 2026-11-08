"""Semantic generator for ARC task df92ae881dc8.

Infer a period from long foreground runs.  Full-height columns replicate in
one direction at that period; otherwise the longest horizontal run seeds four
candidate nested-L completions and the completion covering most cells wins.
Every completed path cell uses the foreground color and every other cell 5.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "df92ae881dc8"
TASK_ID = "df92ae881dc8"
VERSION = "4.0.0"
RULE_HASH = "0951369de1b8"
SUMMARY = "Infer periodic long-run spacing, then extend full columns or choose the maximal nested-L completion; fill non-path cells gray."
INVARIANTS = [
    "the input uses literal zero background and one nonzero non-gray foreground color",
    "significant rows and columns contain a consecutive foreground run of length at least three",
    "the period is the mode of consecutive significant-line gaps in 2..4, defaulting to two",
    "a full-height foreground column selects the column-replication branch",
    "without a full column, the longest horizontal run selects the nested-L branch",
    "longest-run ties follow the canonical bottommost-then-rightmost key order",
    "four diagonal nested-L directions compete and the first maximal-coverage candidate wins",
    "all original foreground cells remain foreground in the output",
    "all completed path cells use the foreground color and every other cell becomes literal gray 5",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "full_p2_right",
    "full_p2_left",
    "full_p3_right",
    "full_p3_left",
    "full_p4_right",
    "full_p4_left",
    "l_p2_up_left",
    "l_p2_down_left",
    "l_p3_up_left",
    "l_p3_up_right",
    "l_p4_down_left",
    "l_p4_down_right",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable periodic completion lessons",
        "valid": "public_1|public_2|public_3|public_4|full_p2_right|full_p2_left|full_p3_right|full_p3_left|full_p4_right|full_p4_left|l_p2_up_left|l_p2_down_left|l_p3_up_left|l_p3_up_right|l_p4_down_left|l_p4_down_right",
    }
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_PUBLIC_ROWS = {
    "public_1": "0000100100/0000100100/0000100111/0000100000/0000100000/0000111111/0000000000/0000000000/0000000000/0000000000",
    "public_2": "0000000000/0000000000/0000000000/0000000000/8888880000/0000080000/8888080000/0008080000/8808080000/0808080000",
    "public_3": "0202020200/0202220200/0200000200/0222222200/0000000000/0000000000/0000000000/0000000000/0000000000/0000000000",
    "public_4": "4444440000/0000040000/0000040000/4440040000/0040040000/0040040000/4440040000/0000040000/0000040000/4444440000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _max_run(values):
    best = current = 0
    for value in values:
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _valid_diffs(values):
    return [later - earlier for earlier, later in zip(values, values[1:]) if 2 <= later - earlier <= 4]


def _mode_first(values):
    counts = Counter(values)
    best = max(counts.values())
    return next(value for value in values if counts[value] == best)


def _row_runs(grid, foreground):
    runs = []
    for row, values in enumerate(grid):
        col = 0
        row_runs = []
        while col < len(values):
            if values[col] != foreground:
                col += 1
                continue
            start = col
            while col + 1 < len(values) and values[col + 1] == foreground:
                col += 1
            row_runs.insert(0, (row, start, col, col - start + 1))
            col += 1
        runs.extend(row_runs)
    return runs


def _grow_candidate(foreground_cells, chosen_run, period, height, width, row_step, col_step):
    row0, start, end, _ = chosen_run
    base = end if col_step == 1 else start
    complete = set(foreground_cells)
    multiplier = 1
    while True:
        row = row0 + row_step * period * multiplier
        col = base + col_step * period * multiplier
        if row < 0 or row >= height:
            return complete
        if 0 <= col < width:
            horizontal = range(0, col + 1) if col_step == 1 else range(col, width)
            vertical = range(0, row + 1) if row_step == 1 else range(row, height)
            complete.update((row, cc) for cc in horizontal)
            complete.update((rr, col) for rr in vertical)
        else:
            complete.update((row, cc) for cc in range(width))
        multiplier += 1


def _rule_facts(grid):
    height, width = len(grid), len(grid[0])
    colors = sorted({value for row in grid for value in row if value > 0})
    foreground = colors[0]
    foreground_cells = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == foreground}
    significant_rows = [row for row in range(height) if _max_run([grid[row][col] == foreground for col in range(width)]) >= 3]
    significant_cols = [col for col in range(width) if _max_run([grid[row][col] == foreground for row in range(height)]) >= 3]
    diffs = _valid_diffs(significant_rows) + _valid_diffs(significant_cols)
    period = _mode_first(diffs) if diffs else 2
    full_cols = [col for col in range(width) if all(grid[row][col] == foreground for row in range(height))]
    if full_cols:
        complete = set(foreground_cells)
        directions = []
        for col in full_cols:
            has_left = 0 <= col - period < width and any(grid[row][col - period] == foreground for row in range(height))
            has_right = 0 <= col + period < width and any(grid[row][col + period] == foreground for row in range(height))
            if has_left and col + period < width:
                direction = 1
            elif has_right and col - period >= 0:
                direction = -1
            elif col + period < width:
                direction = 1
            else:
                direction = -1
            directions.append(direction)
            target = col + direction * period
            while 0 <= target < width:
                complete.update((row, target) for row in range(height))
                target += direction * period
        return {
            "foreground": foreground,
            "foreground_cells": foreground_cells,
            "significant_rows": significant_rows,
            "significant_cols": significant_cols,
            "period": period,
            "full_cols": full_cols,
            "branch": "full_columns",
            "directions": directions,
            "chosen_run": None,
            "winner": None,
            "candidates": [],
            "complete_cells": complete,
        }
    runs = [run for run in _row_runs(grid, foreground) if run[3] >= 3]
    chosen = sorted(runs, key=lambda run: -(10000 * run[3] + 100 * run[0] + run[1]))[0]
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    candidates = [_grow_candidate(foreground_cells, chosen, period, height, width, *direction) for direction in directions]
    winner_index = max(range(4), key=lambda index: len(candidates[index]))
    return {
        "foreground": foreground,
        "foreground_cells": foreground_cells,
        "significant_rows": significant_rows,
        "significant_cols": significant_cols,
        "period": period,
        "full_cols": [],
        "branch": "nested_l",
        "directions": [],
        "chosen_run": chosen,
        "winner": directions[winner_index],
        "candidates": candidates,
        "complete_cells": candidates[winner_index],
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _rule_facts(grid)
    return [[facts["foreground"] if (row, col) in facts["complete_cells"] else 5 for col in range(len(grid[0]))] for row in range(len(grid))]


def _general_profile(facts):
    period = facts["period"]
    if facts["branch"] == "full_columns":
        if len(facts["full_cols"]) != 1 or len(set(facts["directions"])) != 1:
            return None
        side = "right" if facts["directions"][0] == 1 else "left"
        name = f"full_p{period}_{side}"
    else:
        row_step, col_step = facts["winner"]
        vertical = "up" if row_step == -1 else "down"
        horizontal = "left" if col_step == -1 else "right"
        name = f"l_p{period}_{vertical}_{horizontal}"
    return name if name in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    nonzero = {value for row in grid for value in row if value != 0}
    if height < 6 or width < 6:
        errors.append("expected both dimensions to be at least six")
    if len(nonzero) != 1 or 5 in nonzero:
        errors.append("expected exactly one nonzero non-gray foreground color")
    if all(value != 0 for row in grid for value in row):
        errors.append("expected literal zero background")
    if sum(value != 0 for row in grid for value in row) < 6:
        errors.append("expected at least six foreground cells")
    if not errors:
        foreground = next(iter(nonzero))
        has_full_col = any(all(grid[row][col] == foreground for row in range(height)) for col in range(width))
        has_long_row = any(_max_run([value == foreground for value in row]) >= 3 for row in grid)
        if not has_full_col and not has_long_row:
            errors.append("expected a full foreground column or horizontal run of length at least three")
    facts = None
    if not errors:
        facts = _rule_facts(grid)
        if facts["period"] not in (2, 3, 4):
            errors.append("inferred period must be two, three, or four")
        if facts["branch"] == "nested_l" and facts["chosen_run"] is None:
            errors.append("nested-L branch requires a horizontal run of length at least three")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match a declared completion profile")
    output = rule_mirror(grid) if not errors else None
    changed = sum(a != b for row_a, row_b in zip(grid, output or []) for a, b in zip(row_a, row_b)) if output else 0
    result.update({"facts": facts, "output": output, "changed": changed, "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(f"scene profile drifted from {requested} to {analysis['scene_profile']}")
    return errors


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _dimensions(difficulty, rng):
    ranges = {None: (10, 16), "easy": (8, 12), "medium": (10, 16), "hard": (14, 20)}
    low, high = ranges[difficulty]
    return rng.randint(low, high), rng.randint(low, high)


def _full_scene(ctx, period, direction):
    rng = ctx.draw_rng("geometry")
    for _ in range(200):
        height, width = _dimensions(ctx.difficulty, rng)
        choices = [col for col in range(period, width - period)]
        if not choices:
            continue
        col = rng.choice(choices)
        hint_col = col - period if direction == 1 else col + period
        foreground = rng.choice(_COLORS)
        grid = [[0] * width for _ in range(height)]
        for row in range(height):
            grid[row][col] = foreground
        start = rng.randint(0, height - 3)
        for row in range(start, start + 3):
            grid[row][hint_col] = foreground
        facts = _rule_facts(grid)
        if facts["period"] == period and facts["directions"] == [direction]:
            return grid
    raise AssertionError("could not construct full-column lesson")


def _l_scene(ctx, period, target):
    rng = ctx.draw_rng("geometry")
    for _ in range(3000):
        height, width = _dimensions(ctx.difficulty, rng)
        run_length = rng.randint(5, min(8, width - 1))
        row = rng.randint(1, height - 2)
        starts = list(range(0, width - run_length + 1))
        rng.shuffle(starts)
        evidence_rows = [candidate for candidate in (row - period, row + period) if 0 <= candidate < height]
        rng.shuffle(evidence_rows)
        for start in starts:
            for evidence_row in evidence_rows:
                foreground = rng.choice(_COLORS)
                grid = [[0] * width for _ in range(height)]
                for col in range(start, start + run_length):
                    grid[row][col] = foreground
                evidence_start = rng.randint(0, width - 3)
                for col in range(evidence_start, evidence_start + 3):
                    grid[evidence_row][col] = foreground
                facts = _rule_facts(grid)
                if facts["branch"] == "nested_l" and facts["period"] == period and facts["winner"] == target:
                    return grid
    raise AssertionError(f"could not construct nested-L lesson for {period=} {target=}")


def _general_scene(ctx, profile):
    parts = profile.split("_")
    period = int(parts[1][1])
    if parts[0] == "full":
        return _full_scene(ctx, period, 1 if parts[2] == "right" else -1)
    row_step = -1 if parts[2] == "up" else 1
    col_step = -1 if parts[3] == "left" else 1
    return _l_scene(ctx, period, (row_step, col_step))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 3)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
