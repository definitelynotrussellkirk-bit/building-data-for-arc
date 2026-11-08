"""Semantic generator for ARC task 2b34f380ed25.

The canvas encodes a macro-grid through exact length-three runs.  Full uniform
nonzero/non-yellow gap lines split that macro-grid into panels.  Yellow gap
strips exchange balanced macro halves in positional order; an unmarked panel
instead lets its sole non-1 color replace every macro value 1.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2b34f380ed25"
TASK_ID = "2b34f380ed25"
VERSION = "3.1.0"
RULE_HASH = "76c7916140ea"
SUMMARY = "Decode run-three macro bands, split panels at uniform divider lines, exchange balanced halves across yellow marks in positional order, or fill 1-valued cells from a panel's sole other color."
INVARIANTS = [
    "literal zero is background and macro bands are inferred from maximal equal nonzero runs of exactly three",
    "macro values are the nonzero modes of row-band by column-band intersections",
    "full uniform nonzero lines other than color 4 split the macro board at inter-band gaps",
    "an all-4 gap strip marks a mirror between the macro columns or rows on its sides",
    "a marked panel exchanges halves in positional order only when its two sides have equal macro width or height",
    "an unmarked panel replaces 1 only when it contains exactly one distinct nonzero non-1 macro color",
    "painting changes only intersections of detected row and column bands; gaps and margins survive",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 7))
GENERAL_PROFILES = (
    "fill_uniform_panel",
    "multicolor_preserve_plus_fill",
    "vertical_swap_two",
    "vertical_swap_four",
    "horizontal_swap_two",
    "horizontal_swap_four",
    "unbalanced_vertical_plus_fill",
    "unbalanced_horizontal_plus_fill",
    "row_split_mixed",
    "four_panel_mixed",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
# Two counterexample lanes plus one unconstrained-context lane.  Six consecutive
# draws contain two of each: every five-demo/query rotation retains witnesses.
# Only the semantic lane repeats; colors, dimensions and context profiles vary.
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("ordered_halves", "unbalanced_guard", "context")
_CONTEXT_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "periodic ordered-half witness, unbalanced-guard witness, then a varied original context",
        "valid": "public_1|public_2|public_3|public_4|public_5|public_6|fill_uniform_panel|multicolor_preserve_plus_fill|vertical_swap_two|vertical_swap_four|horizontal_swap_two|horizontal_swap_four|unbalanced_vertical_plus_fill|unbalanced_horizontal_plus_fill|row_split_mixed|four_panel_mixed",
    }
}

_PUBLIC_ROWS = (
    "000040000/022241110/022241110/022241110/000040000/011148880/011148880/011148880/000040000",
    "000000000/011106660/011106660/011106660/000000000/011101110/011101110/011101110/000000000/777777777/000000000/033309990/033309990/033309990/444444444/022208880/022208880/022208880/000000000",
    "000000000/011101110/011101110/011101110/000000000/088801110/088801110/088801110/000000000",
    "0000000005000040000/0111044405022248880/0111044405022248880/0111044405022248880/0000000005000040000/0111011105033341110/0111011105033341110/0111011105033341110/0000000005000040000/5555555555555555555/0000000005000000000/0111088805011101110/0111088805011101110/0111088805011101110/4444444445000000000/0666033305022201110/0666033305022201110/0666033305022201110/0000000005000000000",
    "00004000050000000005000000000/01114333050666011105011101110/01114333050666011105011101110/01114333050666011105011101110/00004000050000000005000000000/03334555050111011105044401110/03334555050111011105044401110/03334555050111011105044401110/00004000050000000005000000000/55555555555555555555555555555/00000000050000000005000000000/02220111050111011105088805550/02220111050111011105088805550/02220111050111011105088805550/00000000050000000005444444444/01110111050111088805011106660/01110111050111088805011106660/01110111050111088805011106660/00000000050000000005000000000",
    "00000000090000400009000000000/03330111090888411109011107770/03330111090888411109011107770/03330111090888411109011107770/00000000090000400009000000000/01110111090666433309011101110/01110111090666433309011101110/01110111090666433309011101110/00000000090000400009000000000/99999999999999999999999999999/00000000090000000009000000000/08880333090555011109022207770/08880333090555011109022207770/08880333090555011109022207770/44444444490000000009444444444/02220111090111011109088801110/02220111090111011109088801110/02220111090111011109088801110/00000000090000000009000000000/99999999999999999999999999999/00004000090000000009000000000/06664666090777011109011102220/06664666090777011109011102220/06664666090777011109011102220/00004000094444444449000000000/03334111090222088809011101110/03334111090222088809011101110/03334111090222088809011101110/00004000090000000009000000000",
)


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(line, (list, tuple)) or len(line) != width for line in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for line in grid for value in line):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _has_run_three(values):
    index = 0
    while index < len(values):
        value = values[index]
        end = index + 1
        while end < len(values) and values[end] == value:
            end += 1
        if value != 0 and end - index == 3:
            return True
        index = end
    return False


def _intervals(flags):
    result = []
    start = None
    for index, flag in enumerate(flags + [False]):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            result.append((start, index - 1))
            start = None
    return result


def _mode(values):
    counts = Counter(values)
    maximum = max(counts.values())
    return next(value for value in values if counts[value] == maximum)


def _uniform(values):
    return bool(values) and all(value == values[0] for value in values)


def _groups(count, cuts):
    result = []
    start = 0
    for cut in cuts:
        result.append((start, cut))
        start = cut + 1
    result.append((start, count - 1))
    return result


def _all_four_rect(grid, top, left, bottom, right):
    return top <= bottom and left <= right and all(grid[row][col] == 4 for row in range(top, bottom + 1) for col in range(left, right + 1))


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    row_bands = _intervals([_has_run_three(list(line)) for line in grid])
    col_bands = _intervals([_has_run_three([grid[row][col] for row in range(height)]) for col in range(width)])
    if not row_bands or not col_bands:
        raise ValueError("no run-three macro bands detected")
    macro = []
    for row_start, row_end in row_bands:
        line = []
        for col_start, col_end in col_bands:
            values = [grid[row][col] for row in range(row_start, row_end + 1) for col in range(col_start, col_end + 1) if grid[row][col] > 0]
            line.append(0 if not values else _mode(values))
        macro.append(line)
    row_cuts = []
    for index in range(len(row_bands) - 1):
        for row in range(row_bands[index][1] + 1, row_bands[index + 1][0]):
            values = list(grid[row])
            if _uniform(values) and values[0] > 0 and values[0] != 4:
                row_cuts.append(index)
                break
    col_cuts = []
    for index in range(len(col_bands) - 1):
        for col in range(col_bands[index][1] + 1, col_bands[index + 1][0]):
            values = [grid[row][col] for row in range(height)]
            if _uniform(values) and values[0] > 0 and values[0] != 4:
                col_cuts.append(index)
                break
    row_groups = _groups(len(row_bands), row_cuts)
    col_groups = _groups(len(col_bands), col_cuts)
    new_macro = [line[:] for line in macro]
    panel_facts = []
    for row_group in row_groups:
        for col_group in col_groups:
            vertical_marks = []
            for index in range(col_group[0], col_group[1]):
                col_start = col_bands[index][1] + 1
                col_end = col_bands[index + 1][0] - 1
                if _all_four_rect(grid, row_bands[row_group[0]][0], col_start, row_bands[row_group[1]][1], col_end):
                    vertical_marks.append(index)
            horizontal_marks = []
            for index in range(row_group[0], row_group[1]):
                row_start = row_bands[index][1] + 1
                row_end = row_bands[index + 1][0] - 1
                if _all_four_rect(grid, row_start, col_bands[col_group[0]][0], row_end, col_bands[col_group[1]][1]):
                    horizontal_marks.append(index)
            balanced_vertical = []
            balanced_horizontal = []
            for mark in vertical_marks:
                lefts = list(range(col_group[0], mark + 1))
                rights = list(range(mark + 1, col_group[1] + 1))
                balanced_vertical.append(len(lefts) == len(rights))
                if len(lefts) == len(rights):
                    for macro_row in range(row_group[0], row_group[1] + 1):
                        for left_col, right_col in zip(lefts, rights):
                            new_macro[macro_row][left_col] = macro[macro_row][right_col]
                            new_macro[macro_row][right_col] = macro[macro_row][left_col]
            for mark in horizontal_marks:
                tops = list(range(row_group[0], mark + 1))
                bottoms = list(range(mark + 1, row_group[1] + 1))
                balanced_horizontal.append(len(tops) == len(bottoms))
                if len(tops) == len(bottoms):
                    for top_row, bottom_row in zip(tops, bottoms):
                        for macro_col in range(col_group[0], col_group[1] + 1):
                            new_macro[top_row][macro_col] = macro[bottom_row][macro_col]
                            new_macro[bottom_row][macro_col] = macro[top_row][macro_col]
            non_one = sorted({macro[row][col] for row in range(row_group[0], row_group[1] + 1) for col in range(col_group[0], col_group[1] + 1) if macro[row][col] not in (0, 1)})
            if not vertical_marks and not horizontal_marks and len(non_one) == 1:
                for row in range(row_group[0], row_group[1] + 1):
                    for col in range(col_group[0], col_group[1] + 1):
                        if macro[row][col] == 1:
                            new_macro[row][col] = non_one[0]
                action = "fill"
            elif vertical_marks or horizontal_marks:
                action = "marked"
            else:
                action = "preserve"
            panel_facts.append({
                "row_group": row_group,
                "col_group": col_group,
                "vertical_marks": vertical_marks,
                "horizontal_marks": horizontal_marks,
                "balanced_vertical": balanced_vertical,
                "balanced_horizontal": balanced_horizontal,
                "non_one_colors": non_one,
                "action": action,
            })
    output = [list(line) for line in grid]
    for row in range(height):
        row_index = next((index for index, interval in enumerate(row_bands) if interval[0] <= row <= interval[1]), None)
        if row_index is None:
            continue
        for col in range(width):
            col_index = next((index for index, interval in enumerate(col_bands) if interval[0] <= col <= interval[1]), None)
            if col_index is not None:
                output[row][col] = new_macro[row_index][col_index]
    return {
        "row_bands": row_bands,
        "col_bands": col_bands,
        "row_cuts": row_cuts,
        "col_cuts": col_cuts,
        "row_groups": row_groups,
        "col_groups": col_groups,
        "macro": macro,
        "new_macro": new_macro,
        "panel_facts": panel_facts,
        "output": output,
        "changed": sum(a != b for line_a, line_b in zip(grid, output) for a, b in zip(line_a, line_b)),
    }


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def _paint_macro(grid, facts, values):
    output = [list(line) for line in grid]
    for ri, (top, bottom) in enumerate(facts["row_bands"]):
        for ci, (left, right) in enumerate(facts["col_bands"]):
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    output[row][col] = values[ri][ci]
    return output


def _reflection_rival(grid, *, vertical=True, horizontal=True):
    """Plausible geometric reflection, changing only the marked-panel action."""
    facts = _extract_facts(grid)
    macro = facts["macro"]
    values = [line[:] for line in facts["new_macro"]]
    for panel in facts["panel_facts"]:
        top, bottom = panel["row_group"]
        left, right = panel["col_group"]
        if vertical and any(panel["balanced_vertical"]):
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    values[row][col] = macro[row][left + right - col]
        # The authority reads the ORIGINAL macro for both actions.  A horizontal
        # mark wins when both act; the rival preserves that overwrite contract.
        if any(panel["balanced_horizontal"]):
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    values[row][col] = (macro[top + bottom - row][col]
                                        if horizontal else facts["new_macro"][row][col])
    return _paint_macro(grid, facts, values)


def _vertical_reflection(grid):
    return _reflection_rival(grid, horizontal=False)


def _horizontal_reflection(grid):
    return _reflection_rival(grid, vertical=False)


def _ignore_unbalanced_marks(grid):
    """Treat an unbalanced mark as absent, incorrectly enabling lone-color fill."""
    facts = _extract_facts(grid)
    values = [line[:] for line in facts["new_macro"]]
    for panel in facts["panel_facts"]:
        balances = panel["balanced_vertical"] + panel["balanced_horizontal"]
        if not balances or any(balances) or len(panel["non_one_colors"]) != 1:
            continue
        top, bottom = panel["row_group"]
        left, right = panel["col_group"]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if facts["macro"][row][col] == 1:
                    values[row][col] = panel["non_one_colors"][0]
    return _paint_macro(grid, facts, values)


SEMANTIC_RIVALS = {
    "geometric_reflection": _reflection_rival,
    "vertical_reflection": _vertical_reflection,
    "horizontal_reflection": _horizontal_reflection,
    "ignore_unbalanced_marks": _ignore_unbalanced_marks,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _vertical_pairing_witness(grid):
    return rule_mirror(grid) != _vertical_reflection(grid)


def _horizontal_pairing_witness(grid):
    return rule_mirror(grid) != _horizontal_reflection(grid)


def _unbalanced_guard_witness(grid):
    return rule_mirror(grid) != _ignore_unbalanced_marks(grid)


SEMANTIC_WITNESSES = {
    "vertical_ordered_halves": _vertical_pairing_witness,
    "horizontal_ordered_halves": _horizontal_pairing_witness,
    "unbalanced_mark_suppresses_fill": _unbalanced_guard_witness,
}
WITNESS_RIVALS = {
    "vertical_ordered_halves": ["vertical_reflection", "geometric_reflection"],
    "horizontal_ordered_halves": ["horizontal_reflection", "geometric_reflection"],
    "unbalanced_mark_suppresses_fill": ["ignore_unbalanced_marks"],
}


def _panel_signature(facts):
    signature = []
    for panel in facts["panel_facts"]:
        if panel["vertical_marks"]:
            kind = "v_bal" if all(panel["balanced_vertical"]) else "v_unbal"
        elif panel["horizontal_marks"]:
            kind = "h_bal" if all(panel["balanced_horizontal"]) else "h_unbal"
        else:
            kind = panel["action"]
        signature.append((panel["row_group"], panel["col_group"], kind))
    return signature


def _general_profile(facts):
    rows, cols = len(facts["row_bands"]), len(facts["col_bands"])
    row_groups, col_groups = facts["row_groups"], facts["col_groups"]
    signature = [entry[2] for entry in _panel_signature(facts)]
    if len(row_groups) == len(col_groups) == 1:
        panel = facts["panel_facts"][0]
        if signature == ["fill"]:
            return "fill_uniform_panel"
        if signature == ["v_bal"] and cols == 2 and panel["vertical_marks"] == [0]:
            return "vertical_swap_two"
        if signature == ["v_bal"] and cols == 4 and panel["vertical_marks"] == [1]:
            return "vertical_swap_four"
        if signature == ["h_bal"] and rows == 2 and panel["horizontal_marks"] == [0]:
            return "horizontal_swap_two"
        if signature == ["h_bal"] and rows == 4 and panel["horizontal_marks"] == [1]:
            return "horizontal_swap_four"
    if len(row_groups) == 1 and len(col_groups) == 2:
        if signature == ["preserve", "fill"]:
            return "multicolor_preserve_plus_fill"
        if signature == ["v_unbal", "fill"]:
            return "unbalanced_vertical_plus_fill"
    if len(row_groups) == 2 and len(col_groups) == 1:
        if signature == ["h_unbal", "fill"]:
            return "unbalanced_horizontal_plus_fill"
        if signature == ["v_bal", "fill"]:
            return "row_split_mixed"
    if len(row_groups) == len(col_groups) == 2 and signature == ["fill", "v_bal", "h_bal", "preserve"]:
        return "four_panel_mixed"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if len(grid) < 9 or len(grid[0]) < 9:
        errors.append("training macro boards must be at least 9x9")
    if not any(value == 0 for line in grid for value in line):
        errors.append("literal zero background/gaps must be present")
    try:
        facts = _extract_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return result
    if any(end - start + 1 != 3 for start, end in facts["row_bands"] + facts["col_bands"]):
        errors.append("every detected macro band must have thickness three")
    if not 2 <= len(facts["row_bands"]) <= 7 or not 2 <= len(facts["col_bands"]) <= 7:
        errors.append("training macro dimensions must each be in 2..7")
    if any(value == 0 for line in facts["macro"] for value in line):
        errors.append("every logical macro position must have a nonzero modal value")
    if facts["changed"] == 0:
        errors.append("at least one macro cell must visibly change")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match one declared macro-panel profile")
    result.update({"facts": facts, "output": facts["output"], "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(f"scene profile drifted from {requested} to {analysis['scene_profile']}")
    return errors


def strict_canonical_like(grid):
    """The declared solid-macro domain, including every original canonical pair."""
    return self_check(grid)


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _dimension_range(difficulty):
    return {None: (2, 6), "easy": (2, 3), "medium": (3, 5), "hard": (5, 7)}[difficulty]


def _starts(count, cuts):
    positions = [1]
    for index in range(count - 1):
        positions.append(positions[-1] + 3 + (3 if index in cuts else 1))
    return positions


def _random_values(rng, rows, cols, legal):
    return [[rng.choice(legal) for _ in range(cols)] for _ in range(rows)]


def _set_panel(matrix, row_group, col_group, values):
    iterator = iter(values)
    for row in range(row_group[0], row_group[1] + 1):
        for col in range(col_group[0], col_group[1] + 1):
            matrix[row][col] = next(iterator)


def _fill_values(rng, size, target):
    values = [1, target] + [rng.choice((1, target)) for _ in range(size - 2)]
    rng.shuffle(values)
    return values


def _preserve_values(rng, size, colors):
    values = [1, colors[0], colors[1]] + [rng.choice((1,) + tuple(colors)) for _ in range(size - 3)]
    rng.shuffle(values)
    return values


def _build_canvas(matrix, row_cuts, col_cuts, vertical_marks, horizontal_marks, separator_color):
    rows, cols = len(matrix), len(matrix[0])
    row_starts, col_starts = _starts(rows, set(row_cuts)), _starts(cols, set(col_cuts))
    height, width = row_starts[-1] + 4, col_starts[-1] + 4
    canvas = [[0] * width for _ in range(height)]
    for row in range(rows):
        for col in range(cols):
            for rr in range(row_starts[row], row_starts[row] + 3):
                for cc in range(col_starts[col], col_starts[col] + 3):
                    canvas[rr][cc] = matrix[row][col]
    for row_group, col_after in vertical_marks:
        marker_col = col_starts[col_after] + 3
        for row in range(row_starts[row_group[0]], row_starts[row_group[1]] + 3):
            canvas[row][marker_col] = 4
    for col_group, row_after in horizontal_marks:
        marker_row = row_starts[row_after] + 3
        for col in range(col_starts[col_group[0]], col_starts[col_group[1]] + 3):
            canvas[marker_row][col] = 4
    for cut in row_cuts:
        separator_row = row_starts[cut] + 4
        canvas[separator_row] = [separator_color] * width
    for cut in col_cuts:
        separator_col = col_starts[cut] + 4
        for row in range(height):
            canvas[row][separator_col] = separator_color
    return canvas


def _pad_zero_margins(canvas, rng):
    height, width = len(canvas), len(canvas[0])
    extra_rows = rng.randint(0, min(4, 30 - height))
    extra_cols = rng.randint(0, min(4, 30 - width))
    top = rng.randint(0, extra_rows)
    left = rng.randint(0, extra_cols)
    bottom = extra_rows - top
    right = extra_cols - left
    padded_width = width + left + right
    result = [[0] * padded_width for _ in range(top)]
    result.extend([[0] * left + line[:] + [0] * right for line in canvas])
    result.extend([[0] * padded_width for _ in range(bottom)])
    return result


def _general_scene(ctx, profile, rng):
    for _ in range(500):
        low, high = _dimension_range(ctx.difficulty)
        separator_color = rng.choice((2, 3, 5, 6, 7, 8, 9))
        legal = [color for color in range(1, 10) if color not in (4, separator_color)]
        row_cuts = []
        col_cuts = []
        vertical_marks = []
        horizontal_marks = []
        if profile == "fill_uniform_panel":
            rows, cols = rng.randint(low, high), rng.randint(low, high)
        elif profile == "multicolor_preserve_plus_fill":
            rows, cols = rng.randint(low, high), 4
            col_cuts = [1]
        elif profile == "vertical_swap_two":
            rows, cols = rng.randint(low, high), 2
            vertical_marks = [((0, rows - 1), 0)]
        elif profile == "vertical_swap_four":
            rows, cols = rng.randint(low, high), 4
            vertical_marks = [((0, rows - 1), 1)]
        elif profile == "horizontal_swap_two":
            rows, cols = 2, rng.randint(low, high)
            horizontal_marks = [((0, cols - 1), 0)]
        elif profile == "horizontal_swap_four":
            rows, cols = 4, rng.randint(low, high)
            horizontal_marks = [((0, cols - 1), 1)]
        elif profile == "unbalanced_vertical_plus_fill":
            rows, cols = rng.randint(low, high), 4
            col_cuts = [2]
            vertical_marks = [((0, rows - 1), 0)]
        elif profile == "unbalanced_horizontal_plus_fill":
            rows, cols = 4, rng.randint(low, high)
            row_cuts = [2]
            horizontal_marks = [((0, cols - 1), 0)]
        elif profile == "row_split_mixed":
            rows, cols = 4, 2
            row_cuts = [1]
            vertical_marks = [((0, 1), 0)]
        else:
            # Keep the four original panel roles, with four bands on each
            # marked axis so ordered half exchange differs from reflection.
            rows = cols = 6
            row_cuts = col_cuts = [1]
            vertical_marks = [((0, 1), 3)]
            horizontal_marks = [((0, 1), 3)]
        matrix = _random_values(rng, rows, cols, legal)
        row_groups = _groups(rows, row_cuts)
        col_groups = _groups(cols, col_cuts)
        target = rng.choice([color for color in legal if color != 1])
        if profile == "fill_uniform_panel":
            _set_panel(matrix, row_groups[0], col_groups[0], _fill_values(rng, rows * cols, target))
        elif profile == "multicolor_preserve_plus_fill":
            colors = rng.sample([color for color in legal if color != 1], 2)
            _set_panel(matrix, row_groups[0], col_groups[0], _preserve_values(rng, rows * 2, colors))
            _set_panel(matrix, row_groups[0], col_groups[1], _fill_values(rng, rows * 2, target))
        elif profile == "unbalanced_vertical_plus_fill":
            _set_panel(matrix, row_groups[0], col_groups[0], _fill_values(rng, rows * 3, target))
            _set_panel(matrix, row_groups[0], col_groups[1], _fill_values(rng, rows, target))
        elif profile == "unbalanced_horizontal_plus_fill":
            _set_panel(matrix, row_groups[0], col_groups[0], _fill_values(rng, cols * 3, target))
            _set_panel(matrix, row_groups[1], col_groups[0], _fill_values(rng, cols, target))
        elif profile == "row_split_mixed":
            _set_panel(matrix, row_groups[1], col_groups[0], _fill_values(rng, 4, target))
        elif profile == "four_panel_mixed":
            _set_panel(matrix, row_groups[0], col_groups[0], _fill_values(rng, 4, target))
            colors = rng.sample([color for color in legal if color != 1], 2)
            _set_panel(matrix, row_groups[1], col_groups[1], _preserve_values(rng, 16, colors))
        canvas = _build_canvas(matrix, row_cuts, col_cuts, vertical_marks, horizontal_marks, separator_color)
        if profile == "fill_uniform_panel":
            canvas = _pad_zero_margins(canvas, rng)
        analysis = _analysis(canvas)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            if profile == "four_panel_mixed" and not (
                _vertical_pairing_witness(canvas) and _horizontal_pairing_witness(canvas)
            ):
                continue
            return canvas
    raise AssertionError(f"could not construct {profile}")


def _validate_draw_args(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool or a coerced scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool or a coerced scalar")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None):
    _validate_draw_args(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_draw_args(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    lane = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_profile") is not None:
        choices = SCENE_PROFILES
    elif lane == "ordered_halves":
        choices = ("four_panel_mixed",)
    elif lane == "unbalanced_guard":
        choices = ("unbalanced_vertical_plus_fill", "unbalanced_horizontal_plus_fill")
    else:
        choices = _CONTEXT_PROFILES
    profile = ctx.draw_choice("scene_profile", choices)
    if profile in PUBLIC_PROFILES:
        return [line[:] for line in _PUBLIC_INPUTS[profile]]
    canvas = _general_scene(ctx, profile, ctx.draw_rng("geometry"))
    analysis = _analysis(canvas)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return canvas
