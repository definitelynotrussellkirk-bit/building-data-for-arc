"""Semantic generator for ARC task 196d5de2ea8c.

The first uniform row and first uniform column form a divider cross.  The rule
ignores input row zero and column zero while taking the unique modal color of
each of the four remaining regions, then emits those four modes at the corners
of a 3x3 output whose middle row and column use the divider color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "196d5de2ea8c"
TASK_ID = "196d5de2ea8c"
VERSION = "4.1.0"
RULE_HASH = "4af43de85dfe"
SUMMARY = "Find the first uniform row/column, summarize four inner regions by their modal colors, and place those modes around the divider-colored cross of a 3x3 output; the default lesson schedule alternates an ignored-border counterexample with broad family coverage."
INVARIANTS = [
    "exactly one row and one column are uniform, so the canonical first-match divider is unambiguous",
    "the divider may be any ARC color, including zero",
    "row zero and column zero affect divider detection but are excluded from every region mode",
    "each sampled region has a unique mode; zero and the divider color remain lawful region modes",
    "the four region modes occupy output corners and the divider occupies the other five cells",
    "every four consecutive default draws contain two examples where including row zero or column zero changes the answer",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "centered_distinct",
    "row_offcenter",
    "col_offcenter",
    "both_offcenter",
    "zero_divider",
    "zero_quadrant",
    "repeated_modes",
    "divider_reused_mode",
    "heavy_noise",
    "outer_border_decoys",
    "close_runner_up",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
SCHEDULE_PROFILES = ("ignored_border_counterexample", "broad_mix")
LESSON_SCHEDULE_PERIOD = 2
EXAMPLES_NEEDED = 3
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and eleven generalized region-mode lessons",
        "valid": "public_1|public_2|public_3|public_4|centered_distinct|row_offcenter|col_offcenter|both_offcenter|zero_divider|zero_quadrant|repeated_modes|divider_reused_mode|heavy_noise|outer_border_decoys|close_runner_up",
    }
}

_PUBLIC_ROWS = (
    "7769645939746686999/1111111131999999994/4111111734999999993/6111111135999999994/3111111738999999998/4111111433999999996/1111111837999999999/9111111432999999999/5111111232999999992/4111111337999999994/4565399838811131496/3333333333333333333/7421743237113123495/1888888139222222229/8888888132222222224/8888888932222222222/7888888537222222224/2888888339222222222/4343791931944195857",
    "6768238118336519477/8333328344444444441/1333328844444444444/5333338444444444445/2333348344444444442/1694828458933714688/8888888888888888888/9888568758429224571/3222248911111111119/1222248411111111117/3222238611111111113/5222228111111111116/3222268611111111116/6222238511111111114/2222238811111111118/7222268611111111118/7222298811111111116/6222238811111111117/6316128991872518731",
    "3944638612089461917/4111111111018888882/8111111113088888884/9111111115028888881/3111111111058888885/8111111115058888883/4111111118088888882/2111111119018888884/9111111111098888881/6739135287043283914/0000000000000000000/3199758926027866984/9222222224094444443/7222222224094444445/3222222223014444446/9222222229014444446/9222222221024444445/8222222224014444442/1234523451095891798",
    "4985477787164229937/7222222221144444445/4222222221124444447/1222222221174444448/3222222221144444448/2222222226154444449/5712957644164556141/1111111111111111111/1957449467156979995/5000000001158888889/9000000007168888888/4000000007168888889/9000000009148888887/9000000006168888888/9000000005198888885/7000000006128888888/7000000001178888889/1000000001198888886/7423221541144887888",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["grid dimensions must be within 7..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _unique_mode(values):
    counts = Counter(values)
    maximum = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == maximum)
    if len(winners) != 1:
        raise ValueError(f"region mode must be unique, tied colors={winners}")
    ordered = sorted(counts.values(), reverse=True)
    runner = ordered[1] if len(ordered) > 1 else 0
    return winners[0], dict(counts), maximum - runner, maximum / len(values)


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    uniform_rows = [row for row in range(height) if len(set(grid[row])) == 1]
    uniform_cols = [col for col in range(width) if len({grid[row][col] for row in range(height)}) == 1]
    if not uniform_rows or not uniform_cols:
        raise ValueError("canonical rule requires a uniform row and column")
    div_row, div_col = uniform_rows[0], uniform_cols[0]
    if not (1 < div_row < height - 1 and 1 < div_col < width - 1):
        raise ValueError("divider must leave four non-empty regions after excluding row/column zero")
    divider = grid[div_row][div_col]
    bounds = (
        (1, div_row, 1, div_col),
        (1, div_row, div_col + 1, width),
        (div_row + 1, height, 1, div_col),
        (div_row + 1, height, div_col + 1, width),
    )
    modes, region_counts, margins, fractions = [], [], [], []
    for row1, row2, col1, col2 in bounds:
        values = [grid[row][col] for row in range(row1, row2) for col in range(col1, col2)]
        mode, counts, margin, fraction = _unique_mode(values)
        modes.append(mode)
        region_counts.append(counts)
        margins.append(margin)
        fractions.append(fraction)
    output = [
        [modes[0], divider, modes[1]],
        [divider, divider, divider],
        [modes[2], divider, modes[3]],
    ]
    ignored_border = [grid[0][col] for col in range(width)] + [grid[row][0] for row in range(1, height)]
    return {
        "height": height,
        "width": width,
        "uniform_rows": uniform_rows,
        "uniform_cols": uniform_cols,
        "div_row": div_row,
        "div_col": div_col,
        "divider": divider,
        "bounds": bounds,
        "modes": modes,
        "region_counts": region_counts,
        "margins": margins,
        "fractions": fractions,
        "ignored_border_colors": sorted(set(ignored_border)),
        "output": output,
        "changed": grid != output,
    }


def _offcenter(position, size):
    return abs(position - (size - 1) / 2) > 1.5


def _general_signature(facts):
    modes = facts["modes"]
    divider = facts["divider"]
    row_off = _offcenter(facts["div_row"], facts["height"])
    col_off = _offcenter(facts["div_col"], facts["width"])
    if len(facts["ignored_border_colors"]) >= 8:
        if not row_off and not col_off and len(set(modes)) == 4 and 0 not in modes and divider not in modes and divider != 0:
            return "outer_border_decoys"
        return None
    if divider == 0:
        if len(set(modes)) == 4 and 0 not in modes and not row_off and not col_off:
            return "zero_divider"
        return None
    if modes.count(0) == 1:
        if len(set(modes)) == 4 and divider not in modes and not row_off and not col_off:
            return "zero_quadrant"
        return None
    if 0 in modes:
        return None
    if modes.count(divider) == 1 and len(set(modes)) == 4 and not row_off and not col_off:
        return "divider_reused_mode"
    if divider in modes:
        return None
    if len(set(modes)) == 3 and not row_off and not col_off:
        return "repeated_modes"
    if len(set(modes)) != 4:
        return None
    if min(facts["margins"]) <= 2 and not row_off and not col_off:
        return "close_runner_up"
    if max(facts["fractions"]) <= 0.48 and not row_off and not col_off:
        return "heavy_noise"
    if row_off and col_off:
        return "both_offcenter"
    if row_off:
        return "row_offcenter"
    if col_off:
        return "col_offcenter"
    return "centered_distinct"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    try:
        facts = _extract_facts(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "scene_profile": None}
    if len(facts["uniform_rows"]) != 1:
        errors.append(f"expected exactly one uniform row, got {facts['uniform_rows']}")
    if len(facts["uniform_cols"]) != 1:
        errors.append(f"expected exactly one uniform column, got {facts['uniform_cols']}")
    if not facts["changed"]:
        errors.append("canonical rule must visibly summarize the input")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_signature(facts)
    if profile is None:
        errors.append("scene does not match a declared semantic profile")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": facts["output"]}


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Return fail-closed reasons for scenes outside the supported rule family."""
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return 13, 17
    if difficulty == "medium":
        return 17, 21
    if difficulty == "hard":
        return 19, 25
    return 15, 23


def _divider_position(size, relation, rng):
    if relation == "center":
        return size // 2
    return rng.choice((3, 4, size - 4, size - 3))


def _rectangle_cells(bounds, count, rng):
    row1, row2, col1, col2 = bounds
    region_height, region_width = row2 - row1, col2 - col1
    candidates = []
    best = 0
    for block_height in range(1, region_height + 1):
        for block_width in range(1, region_width + 1):
            area = block_height * block_width
            if area <= count and area >= best:
                if area > best:
                    candidates = []
                    best = area
                candidates.append((block_height, block_width))
    block_height, block_width = rng.choice(candidates)
    start_row = rng.randint(row1, row2 - block_height)
    start_col = rng.randint(col1, col2 - block_width)
    chosen = {(row, col) for row in range(start_row, start_row + block_height) for col in range(start_col, start_col + block_width)}
    remaining = [(row, col) for row in range(row1, row2) for col in range(col1, col2) if (row, col) not in chosen]
    rng.shuffle(remaining)
    chosen.update(remaining[:count - len(chosen)])
    return chosen


def _fill_region(grid, bounds, target, style, rng, *, forbidden_runner=()):
    row1, row2, col1, col2 = bounds
    cells = [(row, col) for row in range(row1, row2) for col in range(col1, col2)]
    area = len(cells)
    if style == "heavy":
        target_count = max(4, int(area * rng.uniform(0.39, 0.45)))
    elif style == "runner":
        target_count = max(4, area // 3)
    else:
        target_count = max(4, int(area * rng.uniform(0.58, 0.70)))
    target_count = min(area - 1, target_count)
    target_cells = _rectangle_cells(bounds, target_count, rng)
    for row, col in target_cells:
        grid[row][col] = target
    remaining = [cell for cell in cells if cell not in target_cells]
    rng.shuffle(remaining)
    decoys = [color for color in range(10) if color != target]
    rng.shuffle(decoys)
    offset = 0
    runner = None
    if style == "runner":
        runner_options = [
            color for color in decoys if color not in set(forbidden_runner)
        ]
        if not runner_options:
            raise ValueError("runner profile has no lawful runner color")
        runner = runner_options[0]
        runner_count = target_count - 1
        for row, col in remaining[:runner_count]:
            grid[row][col] = runner
        offset = runner_count
        decoys = [color for color in decoys if color != runner]
    for index, (row, col) in enumerate(remaining[offset:]):
        grid[row][col] = decoys[index % len(decoys)]
    return runner


def _general_scene(ctx, profile, rng):
    low, high = _size_range(ctx.difficulty)
    for _ in range(100):
        canonical_scale = ctx.draw_choice("scale_profile", (True, False, False))
        if canonical_scale:
            height = width = 19
        else:
            height, width = rng.randint(low, high), rng.randint(low, high)
        row_relation = "off" if profile in {"row_offcenter", "both_offcenter"} else "center"
        col_relation = "off" if profile in {"col_offcenter", "both_offcenter"} else "center"
        div_row = _divider_position(height, row_relation, rng)
        div_col = _divider_position(width, col_relation, rng)
        divider = 0 if profile == "zero_divider" else rng.randint(1, 9)
        nonzero = [color for color in range(1, 10) if color != divider]
        if profile == "zero_quadrant":
            modes = rng.sample(nonzero, 3) + [0]
            rng.shuffle(modes)
        elif profile == "repeated_modes":
            modes = rng.sample(nonzero, 3)
            modes.insert(rng.randrange(4), rng.choice(modes))
        elif profile == "divider_reused_mode":
            modes = rng.sample(nonzero, 3) + [divider]
            rng.shuffle(modes)
        else:
            modes = rng.sample(nonzero, 4)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        bounds = (
            (1, div_row, 1, div_col),
            (1, div_row, div_col + 1, width),
            (div_row + 1, height, 1, div_col),
            (div_row + 1, height, div_col + 1, width),
        )
        border_witness_color = None
        for index, (region, mode) in enumerate(zip(bounds, modes)):
            style = "heavy" if profile == "heavy_noise" else "runner" if profile == "close_runner_up" and index == 0 else "standard"
            runner = _fill_region(
                grid,
                region,
                mode,
                style,
                rng,
                forbidden_runner=(divider,),
            )
            if index == 0 and runner is not None:
                border_witness_color = runner
        border_cells = [(0, col) for col in range(width)] + [(row, 0) for row in range(1, height)]
        if profile == "outer_border_decoys":
            rng.shuffle(border_cells)
            for index, (row, col) in enumerate(border_cells):
                grid[row][col] = index % 10
        elif profile == "close_runner_up":
            if border_witness_color is None:
                raise AssertionError("close-runner profile did not produce a runner")
            for row, col in border_cells:
                grid[row][col] = border_witness_color
        else:
            border_color = rng.choice([color for color in range(10) if color != divider])
            for row, col in border_cells:
                grid[row][col] = border_color
        for col in range(width):
            grid[div_row][col] = divider
        for row in range(height):
            grid[row][div_col] = divider
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the two-slot production lesson schedule used without overrides."""
    _validate_call(seed, sample_index, difficulty, {})
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _deterministic_mode(values):
    counts = Counter(values)
    maximum = max(counts.values())
    return min(color for color, count in counts.items() if count == maximum)


def _output_from_modes(modes, divider):
    return [
        [modes[0], divider, modes[1]],
        [divider, divider, divider],
        [modes[2], divider, modes[3]],
    ]


def _modes_for_bounds(grid, bounds):
    return [
        _deterministic_mode(
            grid[row][col]
            for row in range(row1, row2)
            for col in range(col1, col2)
        )
        for row1, row2, col1, col2 in bounds
    ]


def _include_outer_border_rule(grid):
    """Wrong shortcut: include row zero/column zero in adjacent region modes."""
    facts = _extract_facts(grid)
    height, width = facts["height"], facts["width"]
    div_row, div_col = facts["div_row"], facts["div_col"]
    bounds = (
        (0, div_row, 0, div_col),
        (0, div_row, div_col + 1, width),
        (div_row + 1, height, 0, div_col),
        (div_row + 1, height, div_col + 1, width),
    )
    return _output_from_modes(_modes_for_bounds(grid, bounds), facts["divider"])


def _sample_region_corners_rule(grid):
    """Wrong shortcut: use each region's first cell instead of its mode."""
    facts = _extract_facts(grid)
    modes = [grid[row1][col1] for row1, _row2, col1, _col2 in facts["bounds"]]
    return _output_from_modes(modes, facts["divider"])


def _single_global_mode_rule(grid):
    """Wrong shortcut: summarize all four regions with one global mode."""
    facts = _extract_facts(grid)
    values = [
        grid[row][col]
        for row1, row2, col1, col2 in facts["bounds"]
        for row in range(row1, row2)
        for col in range(col1, col2)
    ]
    mode = _deterministic_mode(values)
    return _output_from_modes([mode] * 4, facts["divider"])


SEMANTIC_RIVALS = {
    "include_outer_border": _include_outer_border_rule,
    "sample_region_corners": _sample_region_corners_rule,
    "single_global_mode": _single_global_mode_rule,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "include_outer_border": _include_outer_border_rule,
}


def _rival_differs(grid, name):
    return not strict_canonical_like(grid) and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "ignored_outer_border_changes_answer": lambda grid: _rival_differs(grid, "include_outer_border"),
    "regional_modes_not_corner_samples": lambda grid: _rival_differs(grid, "sample_region_corners"),
    "four_regions_not_one_global_mode": lambda grid: _rival_differs(grid, "single_global_mode"),
}
WITNESS_RIVALS = {
    "ignored_outer_border_changes_answer": ("include_outer_border",),
    "regional_modes_not_corner_samples": ("sample_region_corners",),
    "four_regions_not_one_global_mode": ("single_global_mode",),
}


def lesson_identifiable(demos, query):
    """Reject a lesson when a named wrong rule fits demos but changes query."""
    errors = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    checked_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        if strict_canonical_like(pair["input"]):
            errors.append(f"demo {index} input is outside the supported family")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demo {index} output does not match the rule")
            continue
        checked_demos.append(pair)
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        errors.append("query is missing input/output")
        return errors
    if strict_canonical_like(query["input"]):
        errors.append("query input is outside the supported family")
        return errors
    if rule_mirror(query["input"]) != query["output"]:
        errors.append("query output does not match the rule")
        return errors
    if errors:
        return errors
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in checked_demos):
            if competitor(query["input"]) != query["output"]:
                errors.append(
                    f"competitor {name!r} fits every demo but changes the query"
                )
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("scene_profile") is not None:
        profile_options = SCENE_PROFILES
    elif schedule_profile(seed, sample_index, difficulty) == "ignored_border_counterexample":
        profile_options = ("close_runner_up",)
    else:
        profile_options = PUBLIC_PROFILES + GENERAL_PROFILES * 4
    profile = ctx.draw_choice("scene_profile", profile_options)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
