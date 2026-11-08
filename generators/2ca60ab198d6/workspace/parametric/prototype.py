"""Row selection and a dependent column-guide extension.

Python outputs are claims, verified by the native protected-Racket worker.
Inputs share a setting-independent grammar; demonstration labels teach the rule.
"""
from __future__ import annotations

import json
import random

SELECTIONS = ("rows", "rows_then_columns")
CANONICAL_PROGRAM = """(rule!
 ;; Keep only the rows whose leading cell is orange(7), dropping that
 ;; marker column.
 (map (lambda (r) (rest (row g r))) (filter (lambda (r) (= (at g r 0) 7)) (range h))))"""


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _selection(settings):
    if (type(settings) is not dict or set(settings) != {"selection"}
            or type(settings["selection"]) is not str
            or settings["selection"] not in SELECTIONS):
        raise ValueError("settings must contain exactly selection=rows|rows_then_columns")
    return settings["selection"]


def _rule(row_mode="orange", column_mode=None, keep_header=False):
    """Compile a small, explicit reference or audit rival to standalone Racket."""
    ordering = row_mode if row_mode in {"output_ascending", "output_descending"} else None
    if ordering:
        row_mode = "orange"
    def ordered(expression):
        if ordering is None:
            return expression
        op = "<" if ordering == "output_ascending" else ">"
        return f"(sort {expression} (lambda (a b) ({op} (first a) (first b))))"
    base = "(filter (lambda (r) (= (at g r 0) 7)) (range h))"
    row_expr = {
        "orange": base,
        "nonzero": "(filter (lambda (r) (not (= (at g r 0) 0))) (range h))",
        "any_seven": "(filter (lambda (r) (ormap (lambda (x) (= x 7)) (row g r))) (range h))",
        "alternating": f"(range (first {base}) h 2)",
        "first_three": f"(take {base} 3)",
        "reverse": f"(reverse {base})",
    }[row_mode]
    prefix = f"(rule! (let* ([idx {row_expr}] [payload (map (lambda (r) (rest (row g r))) idx)]) "
    if column_mode is None:
        return prefix + ordered("payload") + "))"
    guide = {
        "raw_top": "(rest (row g 0))",
        "raw_second": "(rest (row g 1))",
        "last_kept": "(last payload)",
    }.get(column_mode, "(first payload)")
    selected = "(filter (lambda (c) (= (list-ref guide c) 7)) (range (- w 1)))"
    columns = {
        "nonzero": "(filter (lambda (c) (not (= (list-ref guide c) 0))) (range (- w 1)))",
        "first_three": "(take chosen (min 3 (length chosen)))",
        "span": "(range (first chosen) (+ 1 (last chosen)))",
        "first_n": "(range (length chosen))",
        "last_n": "(range (- (- w 1) (length chosen)) (- w 1))",
        "reverse": "(reverse chosen)",
        "union": "(filter (lambda (c) (ormap (lambda (r) (= (list-ref r c) 7)) payload)) (range (- w 1)))",
    }.get(column_mode, "chosen")
    body = "payload" if keep_header else "(rest payload)"
    expression = (f"(let* ([guide {guide}] [chosen {selected}] [cols {columns}]) "
                  + f"(map (lambda (r) (map (lambda (c) (list-ref r c)) cols)) {body}))")
    return prefix + ordered(expression) + "))"


def program(settings):
    selection = _selection(settings)
    return CANONICAL_PROGRAM if selection == "rows" else _rule(column_mode="orange")


def _apply(grid, row_mode="orange", column_mode=None, keep_header=False):
    if row_mode in {"output_ascending", "output_descending"}:
        output = _apply(grid, "orange", column_mode, keep_header)
        return sorted(output, key=lambda row: row[0], reverse=row_mode == "output_descending")
    rows = [i for i, row in enumerate(grid) if row[0] == 7]
    if row_mode == "nonzero":
        rows = [i for i, row in enumerate(grid) if row[0] != 0]
    elif row_mode == "any_seven":
        rows = [i for i, row in enumerate(grid) if 7 in row]
    elif row_mode == "alternating":
        rows = list(range(rows[0], len(grid), 2))
    elif row_mode == "first_three":
        rows = rows[:3]
    elif row_mode == "reverse":
        rows = rows[::-1]
    payload = [grid[i][1:] for i in rows]
    if column_mode is None:
        return payload
    guide = (grid[0][1:] if column_mode == "raw_top" else grid[1][1:]
             if column_mode == "raw_second" else payload[-1]
             if column_mode == "last_kept" else payload[0])
    cols = [i for i, value in enumerate(guide) if value == 7]
    if column_mode == "nonzero":
        cols = [i for i, value in enumerate(guide) if value != 0]
    elif column_mode == "first_three":
        cols = cols[:3]
    elif column_mode == "span":
        cols = list(range(cols[0], cols[-1] + 1))
    elif column_mode == "first_n":
        cols = list(range(len(cols)))
    elif column_mode == "last_n":
        cols = list(range(len(guide) - len(cols), len(guide)))
    elif column_mode == "reverse":
        cols = cols[::-1]
    elif column_mode == "union":
        cols = [i for i in range(len(guide)) if any(row[i] == 7 for row in payload)]
    return [[row[c] for c in cols] for row in (payload if keep_header else payload[1:])]


def interpret(grid, selection):
    _selection({"selection": selection})
    return _apply(grid, column_mode=None if selection == "rows" else "orange")


def rival_specs(selection):
    _selection({"selection": selection})
    column = None if selection == "rows" else "orange"
    rivals = {name + "_row_selector": (name, column, False)
              for name in ("nonzero", "any_seven", "alternating", "first_three", "reverse",
                           "output_ascending", "output_descending")}
    rivals["other_setting"] = ("orange", "orange" if column is None else None, False)
    if column is not None:
        rivals.update({name + "_column_guide": ("orange", name, False)
                       for name in ("raw_top", "raw_second", "last_kept", "nonzero",
                                    "first_three", "span", "first_n", "last_n", "reverse", "union")})
        rivals["keep_column_guide_row"] = ("orange", "orange", True)
    return rivals


def rival_programs(selection):
    return {name: _rule(*spec) for name, spec in rival_specs(selection).items()}


def teaching_check(demos, queries, selection):
    """Fit finite rivals to demos only, then report their query conflicts."""
    rejected, survivors, conflicts = {}, [], []
    for name, spec in rival_specs(selection).items():
        failures = [i for i, pair in enumerate(demos) if _apply(pair["input"], *spec) != pair["output"]]
        if failures:
            rejected[name] = failures
        else:
            survivors.append(name)
            for i, pair in enumerate(queries):
                if _apply(pair["input"], *spec) != pair["output"]:
                    conflicts.append({"rival": name, "query_index": i})
    return {"rejected_by_demo": rejected, "survivors": survivors, "query_ambiguities": conflicts,
            "scope": "Finite declared rivals only; Python screen, not Racket verification."}


def domain_errors(grid):
    if (type(grid) is not list or not 6 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 7 <= len(grid[0]) <= 30):
        return ["input must have 6..30 rows and 7..30 columns"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in grid):
        return ["input must be rectangular with exact integer colors 0..9"]
    rows = [row for row in grid if row[0] == 7]
    if not 3 <= len(rows) <= len(grid) - 2:
        return ["need at least three selected and two rejected rows"]
    header = rows[0][1:]
    errors = []
    if not 2 <= header.count(7) <= width - 3:
        errors.append("selected header needs two selected and two rejected columns")
    if not any(cell not in (0, 7) for cell in header) or 0 not in header:
        errors.append("header needs zero and nonzero non-orange distractors")
    if any(not any(row[1:]) or 7 not in row[1:] for row in grid):
        errors.append("every payload row needs visible content and an orange cue or decoy")
    return errors


def make_input(seed, sample_index, *, height, width, n_keep, n_columns, density):
    """Construct a lawful input with content spread across the entire canvas."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(sample_index, "sample_index", 0, 1000000)
    _integer(height, "height", 6, 30)
    _integer(width, "width", 7, 30)
    _integer(n_keep, "n_keep", 3, height - 2)
    _integer(n_columns, "n_columns", 2, width - 3)
    if type(density) not in (float, int) or not 0.15 <= density <= 0.9:
        raise ValueError("density must be a real number in 0.15..0.9")
    rng = random.Random(f"2ca60ab198d6:nested-v1:{seed}:{sample_index}")
    first = sample_index % 3
    kept = {first, first + 1, height - 1}
    kept.update(rng.sample([r for r in range(first + 2, height - 1)], n_keep - 3))
    rows = sorted(kept)
    pw = width - 1
    if sample_index % 3 == 1 and n_columns <= pw - 4:
        cols = {1, pw - 2}
        allowed = set(range(1, pw - 1))
    elif sample_index % 3 == 2 and n_columns >= 4:
        cols = {0, 1, pw - 1}
        allowed = set(range(pw))
    else:
        cols = set(rng.sample(range(pw), 2))
        allowed = set(range(pw))
    cols.update(rng.sample(sorted(allowed - cols), n_columns - len(cols)))
    dropped_cols = sorted(set(range(pw)) - cols)
    sentinel = min(cols)
    other_selected = min(cols - {sentinel})
    non_seven = (1, 2, 3, 4, 5, 6, 8, 9)
    grid = [[0] + [rng.choice(non_seven) if rng.random() < density else 0 for _ in range(pw)]
            for _ in range(height)]
    rejected = sorted(set(range(height)) - kept)
    for i, r in enumerate(rejected):
        grid[r][0] = rng.choice(non_seven) if i % 2 == 0 else 0
    for r in rows:
        grid[r][0] = 7
    # Wrong-header rules remain executable. Every body/decoy mask has an
    # outside orange and a missing true orange, making it differ from the guide.
    for r in range(height):
        grid[r][dropped_cols[(r + sample_index) % len(dropped_cols)] + 1] = 7
        grid[r][other_selected + 1] = 7
        grid[r][sentinel + 1] = rng.choice(non_seven)
    for c in cols:
        grid[first][c + 1] = 7
    for c in dropped_cols:
        grid[first][c + 1] = rng.choice(non_seven) if rng.random() < density else 0
    grid[first][dropped_cols[0] + 1] = 0
    grid[first][dropped_cols[-1] + 1] = 5
    # Distinct values make row order and the column crop observable.
    grid[rows[1]][sentinel + 1] = 1
    grid[rows[-1]][sentinel + 1] = 2
    if len(rows) >= 4:
        # The seed-44 two-demo lesson previously admitted sorting by the
        # first output cell. This constructive 1,9,...,2 witness rules out
        # both monotone orders without adding a demonstration or retrying.
        grid[rows[2]][sentinel + 1] = 9
    errors = domain_errors(grid)
    if errors:
        raise AssertionError(errors)
    return grid


_DEMO_PROFILES = ((8, 9, 4, 2, .25), (10, 11, 5, 4, .75), (6, 7, 3, 2, .50),
                  (14, 17, 7, 7, .22), (22, 25, 12, 12, .75), (30, 30, 16, 14, .50))
_QUERY_PROFILES = ((6, 7, 3, 2, .35), (13, 17, 6, 6, .70),
                   (23, 26, 12, 13, .22), (30, 30, 18, 15, .80))


def generate(seed, settings, demos=3, queries=4):
    selection = _selection(settings)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    def pair(profile, index):
        h, w, nr, nc, density = profile
        grid = make_input(seed, index, height=h, width=w, n_keep=nr, n_columns=nc, density=density)
        return {"input": grid, "output": interpret(grid, selection)}
    train = [pair(profile, i + 1) for i, profile in enumerate(_DEMO_PROFILES[:demos])]
    test = [pair(profile, i + 101) for i, profile in enumerate(_QUERY_PROFILES[:queries])]
    inputs = [json.dumps(p["input"], separators=(",", ":")) for p in train + test]
    if len(set(inputs)) != len(inputs):
        raise ValueError("deterministic draw contains duplicate inputs")
    teaching = teaching_check(train, test, selection)
    if teaching["query_ambiguities"]:
        raise ValueError(f"visible demonstrations underidentify declared rivals: {teaching}")
    return {"train": train, "test": test, "program_solution": program(settings),
            "settings": dict(settings), "seed": seed, "teaching": teaching}
