"""Native parametric family for the color-keyed stencil library.

``single_stage`` is the exact canonical program: read a color's anchor-relative
stencil from the top library and stamp it at every body seed of that color.

``border_routed_cascade`` adds a genuine second state-dependent step.  The first
stamp is materialized.  If that intermediate touches the grid border, the next
library panel is selected; otherwise the previous panel is selected.  That
second stencil is then stamped from every first-stage cell.  Thus the second
operation cannot be selected until the input-dependent first-stage state exists.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root


TASK_ID = "fdffdd0bbde7"
PARAMETER_NAME = "composition"
COMPOSITIONS = ("single_stage", "border_routed_cascade")
DEFAULT_COMPOSITION = "single_stage"
PROTOTYPE_VERSION = "border-routed-cascade-v1"
HERE = Path(__file__).resolve().parent

_DEMO_PROFILES = (
    (14, 18, 5, 3, 8),
    (16, 21, 5, 3, 9),
    (12, 17, 5, 3, 7),
    (18, 24, 6, 4, 11),
    (20, 25, 6, 4, 13),
    (22, 27, 6, 4, 15),
)
_QUERY_PROFILES = (
    (15, 20, 5, 3, 9),
    (21, 24, 6, 4, 13),
    (25, 28, 6, 4, 17),
    (30, 30, 6, 4, 24),
)
_BASE_PATTERNS = (
    ((-1, 0), (0, 1), (1, 0)),
    ((0, -1), (1, -1), (1, 0), (1, 1)),
    ((-1, -1), (-1, 0), (0, -1), (1, 1)),
    ((-1, 1), (0, 1), (1, 0), (1, -1)),
)

_CANONICAL_TAIL = (
    "(define body-cells (filter (lambda (cell) (> (first cell) top-rows)) "
    "(nonzero-cells g))) (for/fold ((out (empty-grid (rows g) (cols g) 0))) "
    "((cell (in-list body-cells))) (let* ((color (third cell)) (entry (first "
    "(filter (lambda (e) (= (first e) color)) entries)))) (stamp-offsets out "
    "(list (first cell) (second cell)) (second entry) color)))))"
)

_CASCADE_TAIL = (
    "(define (grow-centers centers offsets) (remove-duplicates (filter "
    "(lambda (p) (in-bounds? (first p) (second p) (rows g) (cols g))) "
    "(flatmap (lambda (p) (map (lambda (d) (list (+ (first p) (first d)) "
    "(+ (second p) (second d)))) offsets)) centers)))) "
    "(define (border-cell? p) (or (= (first p) 0) (= (second p) 0) "
    "(= (first p) (- (rows g) 1)) (= (second p) (- (cols g) 1)))) "
    "(define (entry-index color) (let loop ((xs entries) (i 0)) "
    "(if (= (first (first xs)) color) i (loop (rest xs) (+ i 1))))) "
    "(define (entry-at index) (let loop ((xs entries) (i index)) "
    "(if (= i 0) (first xs) (loop (rest xs) (- i 1))))) "
    "(define body-cells (filter (lambda (cell) (> (first cell) top-rows)) "
    "(nonzero-cells g))) (for/fold ((out (empty-grid (rows g) (cols g) 0))) "
    "((cell (in-list body-cells))) (let* ((color (third cell)) "
    "(index (entry-index color)) (entry (entry-at index)) "
    "(seed (list (first cell) (second cell))) "
    "(stage-a (grow-centers (list seed) (second entry))) "
    "(touches-border? (any? border-cell? stage-a)) "
    "(route-index (if touches-border? "
    "(if (= index (- (length entries) 1)) 0 (+ index 1)) "
    "(if (= index 0) (- (length entries) 1) (- index 1)))) "
    "(routed (entry-at route-index)) "
    "(stage-b (grow-centers stage-a (second routed)))) "
    "(paint-cells out stage-b color)))))"
)


def _canonical_rows() -> list[dict[str, Any]]:
    root = find_root(__file__)
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    return rows


def canonical_program() -> str:
    programs = {row.get("program_solution") for row in _canonical_rows()}
    if len(programs) != 1 or not all(type(program) is str and program for program in programs):
        raise ValueError(f"{TASK_ID}: expected one concrete canonical program")
    return programs.pop()


def validate_composition(value: Any) -> str:
    if type(value) is not str or value not in COMPOSITIONS:
        raise ValueError(f"declared composition must be one of {COMPOSITIONS}")
    return value


def _replace_tail(replacement: str) -> str:
    canonical = canonical_program()
    if canonical.count(_CANONICAL_TAIL) != 1:
        raise ValueError("canonical stencil tail changed; refusing an unbound rewrite")
    return canonical.replace(_CANONICAL_TAIL, replacement)


def rule_text(composition: Any) -> str:
    selected = validate_composition(composition)
    if selected == "single_stage":
        return canonical_program()
    return _replace_tail(_CASCADE_TAIL)


def counterfactual_rule(kind: str) -> str:
    program = rule_text("border_routed_cascade")
    if kind == "skip_a":
        old = "(stage-b (grow-centers stage-a (second routed)))"
        new = "(stage-b (grow-centers (list seed) (second routed)))"
    elif kind == "wrong_intermediate":
        old = "(if touches-border? (if (= index (- (length entries) 1)) 0 (+ index 1)) (if (= index 0) (- (length entries) 1) (- index 1)))"
        new = "(if touches-border? (if (= index 0) (- (length entries) 1) (- index 1)) (if (= index (- (length entries) 1)) 0 (+ index 1)))"
    elif kind == "always_next":
        old = "(if touches-border? (if (= index (- (length entries) 1)) 0 (+ index 1)) (if (= index 0) (- (length entries) 1) (- index 1)))"
        new = "(if (= index (- (length entries) 1)) 0 (+ index 1))"
    elif kind == "always_previous":
        old = "(if touches-border? (if (= index (- (length entries) 1)) 0 (+ index 1)) (if (= index 0) (- (length entries) 1) (- index 1)))"
        new = "(if (= index 0) (- (length entries) 1) (- index 1))"
    else:
        raise ValueError(f"unknown counterfactual kind: {kind}")
    if program.count(old) != 1:
        raise ValueError(f"counterfactual rewrite point changed: {kind}")
    return program.replace(old, new)


def _seed_int(seed: int, split: str, index: int) -> int:
    payload = f"{PROTOTYPE_VERSION}:{seed}:{split}:{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def _panel_spans(width: int, count: int, rng: random.Random) -> tuple[list[tuple[int, int]], list[int]]:
    usable = width - (count - 1)
    base, remainder = divmod(usable, count)
    widths = [base + (position < remainder) for position in range(count)]
    rng.shuffle(widths)
    if min(widths) < 4:
        raise ValueError("profile cannot fit interior off-center anchors")
    spans: list[tuple[int, int]] = []
    dividers: list[int] = []
    col = 0
    for position, panel_width in enumerate(widths):
        spans.append((col, col + panel_width - 1))
        col += panel_width
        if position < count - 1:
            dividers.append(col)
            col += 1
    if col != width:
        raise RuntimeError("panel partition did not consume width")
    return spans, dividers


def _transform(offsets: Iterable[tuple[int, int]], transform: int) -> tuple[tuple[int, int], ...]:
    result = []
    for row, col in offsets:
        if transform == 0:
            point = (row, col)
        elif transform == 1:
            point = (col, -row)
        elif transform == 2:
            point = (-row, -col)
        elif transform == 3:
            point = (-col, row)
        elif transform == 4:
            point = (row, -col)
        elif transform == 5:
            point = (-row, col)
        elif transform == 6:
            point = (col, row)
        elif transform == 7:
            point = (-col, -row)
        else:
            raise ValueError(transform)
        result.append(point)
    normalized = tuple(sorted(set(result)))
    if len(normalized) != len(tuple(offsets)) or (0, 0) in normalized:
        raise RuntimeError("invalid transformed stencil")
    return normalized


def _grow(
    centers: Iterable[tuple[int, int]],
    offsets: Iterable[tuple[int, int]],
    height: int,
    width: int,
) -> tuple[tuple[int, int], ...]:
    cells = {
        (row + dr, col + dc)
        for row, col in centers
        for dr, dc in offsets
        if 0 <= row + dr < height and 0 <= col + dc < width
    }
    return tuple(sorted(cells))


def _touches_border(cells: Iterable[tuple[int, int]], height: int, width: int) -> bool:
    return any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells)


def _choose_spread(
    candidates: list[tuple[int, int]],
    used: set[tuple[int, int]],
    rng: random.Random,
) -> tuple[int, int]:
    available = [point for point in candidates if point not in used]
    if not available:
        raise RuntimeError("no available body position")
    rng.shuffle(available)
    if not used:
        return available[0]
    return max(
        available,
        key=lambda point: min(abs(point[0] - row) + abs(point[1] - col) for row, col in used),
    )


def _body_positions(
    *,
    height: int,
    width: int,
    separator: int,
    entries: list[dict[str, Any]],
    body_count: int,
    rng: random.Random,
) -> list[tuple[int, int, int]]:
    if body_count < 2 * len(entries):
        raise ValueError("body_count must cover both routing branches for every color")
    body_rows = range(separator + 1, height)
    all_points = [(row, col) for row in body_rows for col in range(width)]
    used: set[tuple[int, int]] = set()
    selected: list[tuple[int, int, int]] = []

    border_groups = (
        [(row, 0) for row in body_rows],
        [(row, width - 1) for row in body_rows],
        [(height - 1, col) for col in range(width)],
        [(row, col) for row in body_rows for col in (0, width - 1)],
    )
    for index, entry in enumerate(entries):
        offsets = entry["offsets"]
        edge_candidates = [
            point
            for point in border_groups[index % len(border_groups)]
            if _touches_border(_grow([point], offsets, height, width), height, width)
        ]
        if not edge_candidates:
            edge_candidates = [
                point
                for point in all_points
                if _touches_border(_grow([point], offsets, height, width), height, width)
            ]
        edge = _choose_spread(edge_candidates, used, rng)
        used.add(edge)
        selected.append((edge[0], edge[1], entry["color"]))

        interior_candidates = [
            point
            for point in all_points
            if 1 < point[1] < width - 2
            and separator + 2 < point[0] < height - 2
            and not _touches_border(_grow([point], offsets, height, width), height, width)
        ]
        if not interior_candidates:
            interior_candidates = [
                point
                for point in all_points
                if not _touches_border(_grow([point], offsets, height, width), height, width)
            ]
        interior = _choose_spread(interior_candidates, used, rng)
        used.add(interior)
        selected.append((interior[0], interior[1], entry["color"]))

    color_cycle = [entry["color"] for entry in entries]
    while len(selected) < body_count:
        color = color_cycle[(len(selected) - 2 * len(entries)) % len(color_cycle)]
        entry = next(row for row in entries if row["color"] == color)
        want_border = len(selected) % 5 == 0
        candidates = [
            point
            for point in all_points
            if _touches_border(_grow([point], entry["offsets"], height, width), height, width)
            == want_border
        ]
        chosen = _choose_spread(candidates or all_points, used, rng)
        used.add(chosen)
        selected.append((chosen[0], chosen[1], color))
    return selected


def build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError(f"unsupported {split} profile index {index}")
    height, width, lib_h, entry_count, body_count = profiles[index]
    rng = random.Random(_seed_int(seed, split, index))
    spans, dividers = _panel_spans(width, entry_count, rng)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for divider in dividers:
        for row in range(lib_h):
            grid[row][divider] = 9

    colors = rng.sample(list(range(1, 9)), entry_count)
    entries: list[dict[str, Any]] = []
    for panel_index, (span, color) in enumerate(zip(spans, colors)):
        center_row = lib_h // 2
        center_col = (span[0] + span[1]) // 2
        row_candidates = [row for row in range(1, lib_h - 1) if row != center_row]
        col_candidates = [col for col in range(span[0] + 1, span[1]) if col != center_col]
        if not row_candidates or not col_candidates:
            raise RuntimeError("profile lacks off-center interior anchor")
        anchor = (rng.choice(row_candidates), rng.choice(col_candidates))
        offsets = _transform(_BASE_PATTERNS[panel_index], rng.randrange(8))
        cells = [(anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets]
        if any(not (0 <= row < lib_h and span[0] <= col <= span[1]) for row, col in cells):
            # All profiles have room for +/-1.  If a randomly selected off-center
            # anchor is too close to one side, use the first fitting alternative.
            fitting = []
            for row in row_candidates:
                for col in col_candidates:
                    candidate = [(row + dr, col + dc) for dr, dc in offsets]
                    if all(0 <= rr < lib_h and span[0] <= cc <= span[1] for rr, cc in candidate):
                        fitting.append(((row, col), candidate))
            if not fitting:
                raise RuntimeError("no fitting off-center anchor for transformed stencil")
            anchor, cells = rng.choice(fitting)
        grid[anchor[0]][anchor[1]] = 9
        for row, col in cells:
            grid[row][col] = color
        entries.append({"color": color, "anchor": anchor, "offsets": tuple(sorted(offsets))})

    for row, col, color in _body_positions(
        height=height,
        width=width,
        separator=lib_h,
        entries=entries,
        body_count=body_count,
        rng=rng,
    ):
        grid[row][col] = color
    return grid


def analyze_input(grid: Any, *, anchor_mode: str = "visible") -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or len(grid) > 30
        or len(grid[0]) > 30
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("expected a rectangular 1..30 ARC grid")
    if anchor_mode not in {"visible", "center", "center_row", "center_col"}:
        raise ValueError(f"unknown anchor mode: {anchor_mode}")
    height, width = len(grid), len(grid[0])
    separator = next(
        (row for row, values in enumerate(grid) if all(value == 0 for value in values)),
        None,
    )
    if separator is None:
        raise ValueError("missing blank separator row")
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(separator))
    ]
    spans: list[tuple[int, int]] = []
    start = 0
    for divider in dividers + [width]:
        if divider > start:
            spans.append((start, divider - 1))
        start = divider + 1
    entries = []
    for c1, c2 in spans:
        anchors = [
            (row, col)
            for row in range(separator)
            for col in range(c1, c2 + 1)
            if grid[row][col] == 9
        ]
        colors = sorted(
            {
                grid[row][col]
                for row in range(separator)
                for col in range(c1, c2 + 1)
                if grid[row][col] not in (0, 9)
            }
        )
        if len(anchors) != 1 or len(colors) != 1:
            raise ValueError("each panel needs one anchor and one stencil color")
        actual_row, actual_col = anchors[0]
        center_row, center_col = separator // 2, (c1 + c2) // 2
        if anchor_mode == "visible":
            anchor = (actual_row, actual_col)
        elif anchor_mode == "center":
            anchor = (center_row, center_col)
        elif anchor_mode == "center_row":
            anchor = (center_row, actual_col)
        else:
            anchor = (actual_row, center_col)
        color = colors[0]
        colored_cells = [
            (row, col)
            for row in range(separator)
            for col in range(c1, c2 + 1)
            if grid[row][col] == color
        ]
        entries.append(
            {
                "span": (c1, c2),
                "visible_anchor": (actual_row, actual_col),
                "anchor": anchor,
                "color": color,
                "offsets": tuple(sorted((row - anchor[0], col - anchor[1]) for row, col in colored_cells)),
            }
        )
    body = tuple(
        (row, col, grid[row][col])
        for row in range(separator + 1, height)
        for col in range(width)
        if grid[row][col] != 0
    )
    entry_colors = {entry["color"] for entry in entries}
    if any(color not in entry_colors for _, _, color in body):
        raise ValueError("body color has no library entry")
    return {
        "height": height,
        "width": width,
        "separator": separator,
        "dividers": tuple(dividers),
        "spans": tuple(spans),
        "entries": tuple(entries),
        "body": body,
    }


def _render(
    grid: Any,
    *,
    composition: str,
    anchor_mode: str = "visible",
    routing: str = "border",
    skip_a: bool = False,
) -> list[list[int]]:
    parsed = analyze_input(grid, anchor_mode=anchor_mode)
    height, width = parsed["height"], parsed["width"]
    entries = list(parsed["entries"])
    by_color = {entry["color"]: (index, entry) for index, entry in enumerate(entries)}
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, color in parsed["body"]:
        index, entry = by_color[color]
        stage_a = _grow([(row, col)], entry["offsets"], height, width)
        if composition == "single_stage":
            cells = stage_a
        else:
            border = _touches_border(stage_a, height, width)
            if routing == "border":
                choose_next = border
            elif routing == "swapped":
                choose_next = not border
            elif routing == "next":
                choose_next = True
            elif routing == "previous":
                choose_next = False
            else:
                raise ValueError(routing)
            routed_index = (index + (1 if choose_next else -1)) % len(entries)
            centers = [(row, col)] if skip_a else stage_a
            cells = _grow(centers, entries[routed_index]["offsets"], height, width)
        for rr, cc in cells:
            output[rr][cc] = color
    return output


def output_for(grid: Any, composition: Any) -> list[list[int]]:
    return _render(grid, composition=validate_composition(composition))


def branch_counts(grid: Any) -> dict[str, int]:
    parsed = analyze_input(grid)
    by_color = {entry["color"]: entry for entry in parsed["entries"]}
    counts = {"border": 0, "interior": 0}
    for row, col, color in parsed["body"]:
        stage_a = _grow([(row, col)], by_color[color]["offsets"], parsed["height"], parsed["width"])
        counts["border" if _touches_border(stage_a, parsed["height"], parsed["width"]) else "interior"] += 1
    return counts


def select_inputs(seed: int, *, demos: int, queries: int) -> dict[str, list[dict[str, Any]]]:
    _validate_request(seed=seed, composition=DEFAULT_COMPOSITION, demos=demos, queries=queries)
    selected = {
        "train": [{"input": build_input(seed, "train", index)} for index in range(demos)],
        "test": [{"input": build_input(seed, "test", index)} for index in range(queries)],
    }
    serialized = [
        json.dumps(row["input"], separators=(",", ":"))
        for split in ("train", "test")
        for row in selected[split]
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    return selected


def shortcut_outputs(grid: Any, chosen: str) -> dict[str, list[list[int]]]:
    if chosen == "single_stage":
        return {
            "panel_center_anchor": _render(grid, composition="single_stage", anchor_mode="center"),
            "center_row_anchor": _render(grid, composition="single_stage", anchor_mode="center_row"),
            "center_col_anchor": _render(grid, composition="single_stage", anchor_mode="center_col"),
        }
    return {
        "always_next": _render(grid, composition="border_routed_cascade", routing="next"),
        "always_previous": _render(grid, composition="border_routed_cascade", routing="previous"),
        "swapped_route": _render(grid, composition="border_routed_cascade", routing="swapped"),
        "skip_first_stage": _render(grid, composition="border_routed_cascade", skip_a=True),
        "panel_center_anchor": _render(
            grid, composition="border_routed_cascade", anchor_mode="center"
        ),
        "center_row_anchor": _render(
            grid, composition="border_routed_cascade", anchor_mode="center_row"
        ),
        "center_col_anchor": _render(
            grid, composition="border_routed_cascade", anchor_mode="center_col"
        ),
    }


def assess_demos(demonstrations: list[dict[str, Any]], composition: Any) -> dict[str, Any]:
    chosen = validate_composition(composition)
    labels = [output_for(row["input"], chosen) for row in demonstrations]
    declared = [
        mode
        for mode in COMPOSITIONS
        if all(output_for(row["input"], mode) == label for row, label in zip(demonstrations, labels))
    ]
    shortcut_names = sorted(shortcut_outputs(demonstrations[0]["input"], chosen))
    shortcuts = [
        name
        for name in shortcut_names
        if all(
            shortcut_outputs(row["input"], chosen)[name] == label
            for row, label in zip(demonstrations, labels)
        )
    ]
    return {
        "composition": chosen,
        "demonstrations": len(demonstrations),
        "declared_setting_survivors": declared,
        "shortcut_survivors": shortcuts,
        "tested_shortcuts": shortcut_names,
    }


def _validate_request(*, seed: Any, composition: Any, demos: Any, queries: Any) -> str:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a nonnegative literal integer below 2**63")
    selected = validate_composition(composition)
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    return selected


def generate_episode(seed: Any, *, composition: Any, demos: Any, queries: Any) -> dict[str, Any]:
    selected_composition = _validate_request(
        seed=seed, composition=composition, demos=demos, queries=queries
    )
    inputs = select_inputs(seed, demos=demos, queries=queries)
    episode = {
        split: [
            {"input": copy.deepcopy(row["input"]), "output": output_for(row["input"], selected_composition)}
            for row in inputs[split]
        ]
        for split in ("train", "test")
    }
    episode["program_solution"] = rule_text(selected_composition)
    return episode


def _seed_intermediate(grid: Any, *, prefer_border: bool) -> dict[str, Any]:
    parsed = analyze_input(grid)
    entries = list(parsed["entries"])
    by_color = {entry["color"]: (index, entry) for index, entry in enumerate(entries)}
    for row, col, color in parsed["body"]:
        index, entry = by_color[color]
        stage_a = _grow([(row, col)], entry["offsets"], parsed["height"], parsed["width"])
        border = _touches_border(stage_a, parsed["height"], parsed["width"])
        if border == prefer_border:
            routed_index = (index + (1 if border else -1)) % len(entries)
            return {
                "seed": [row, col, color],
                "stage_a_cells": len(stage_a),
                "stage_a": [list(point) for point in stage_a],
                "touches_border": border,
                "route": "next" if border else "previous",
                "routed_color": entries[routed_index]["color"],
            }
    raise RuntimeError("input lacks requested routing branch")


def causal_cases(grid: Any) -> list[dict[str, Any]]:
    actual_program = rule_text("border_routed_cascade")
    actual_output = output_for(grid, "border_routed_cascade")
    cases = []
    for kind, prefer_border in (("skip_a", True), ("wrong_intermediate", False)):
        counterfactual_program = counterfactual_rule(kind)
        if kind == "skip_a":
            counterfactual_output = _render(
                grid, composition="border_routed_cascade", skip_a=True
            )
        else:
            counterfactual_output = _render(
                grid, composition="border_routed_cascade", routing="swapped"
            )
        if counterfactual_output == actual_output:
            raise RuntimeError(f"counterfactual {kind} did not change output")
        cases.append(
            {
                "ablation": kind,
                "settings": {PARAMETER_NAME: "border_routed_cascade"},
                "program": actual_program,
                "counterfactual_program": counterfactual_program,
                "input": copy.deepcopy(grid),
                "intermediate_value": _seed_intermediate(grid, prefer_border=prefer_border),
                "output": copy.deepcopy(actual_output),
                "counterfactual_output": counterfactual_output,
            }
        )
    return cases
