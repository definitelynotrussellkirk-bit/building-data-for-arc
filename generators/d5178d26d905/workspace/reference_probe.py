"""Independent parser/oracle for task d5178d26d905 review tests.

This module deliberately does not import production generator helpers.  It
mirrors the selected Racket authority from the structural rule description:
identify the 0/4 reference panel and colored template panel, extract template
line colors, map ordered special template rows to ordered special reference
rows, and repaint the reference geometry.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_ID = "d5178d26d905"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__))


def _rectangular(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors")
    return len(grid), width


def _active_rows(grid: list[list[int]], c0: int, c1: int) -> tuple[list[list[int]], list[int]]:
    indexes = [
        row
        for row in range(len(grid))
        if any(grid[row][col] != 5 for col in range(c0, c1))
    ]
    return [[grid[row][col] for col in range(c0, c1)] for row in indexes], indexes


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _rectangular(grid)
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected one solid color-5 divider, found {dividers}")
    divider = dividers[0]
    if divider == 0 or divider == width - 1:
        raise ValueError("divider must separate two nonempty panels")

    left, left_rows = _active_rows(grid, 0, divider)
    right, right_rows = _active_rows(grid, divider + 1, width)
    if not left or not right:
        raise ValueError("both panels need active rows")

    def is_reference(panel: list[list[int]]) -> bool:
        return all(value in (0, 4) for row in panel for value in row)

    left_ref, right_ref = is_reference(left), is_reference(right)
    if left_ref == right_ref:
        raise ValueError("exactly one panel must be a 0/4 reference")

    if left_ref:
        reference, reference_rows = left, left_rows
        template, template_rows = right, right_rows
        side = "left"
    else:
        reference, reference_rows = right, right_rows
        template, template_rows = left, left_rows
        side = "right"

    counts = Counter(tuple(row) for row in template)
    highest = max(counts.values())
    normal_candidates = [row for row, count in counts.items() if count == highest]
    if len(normal_candidates) != 1:
        raise ValueError("template normal row is not uniquely most common")
    template_normal = list(normal_candidates[0])
    line_cols = [col for col, value in enumerate(template_normal) if value != 0]
    if not line_cols:
        raise ValueError("template normal row has no line colors")
    line_colors = [template_normal[col] for col in line_cols]
    template_special_indexes = [
        row for row, values in enumerate(template) if values != template_normal
    ]

    yellow_counts = [sum(value == 4 for value in row) for row in reference]
    positive = [count for count in yellow_counts if count > 0]
    if not positive:
        raise ValueError("reference has no yellow line marker row")
    minimum = min(positive)
    normal_candidates = {
        tuple(row)
        for row, count in zip(reference, yellow_counts)
        if count == minimum
    }
    if len(normal_candidates) != 1:
        raise ValueError("reference normal row is not uniquely identifiable")
    reference_normal = list(next(iter(normal_candidates)))
    reference_line_cols = [
        col for col, value in enumerate(reference_normal) if value == 4
    ]
    reference_special_indexes = [
        row
        for row, values in enumerate(reference)
        if any(value == 4 for value in values) and values != reference_normal
    ]

    if len(reference_line_cols) != len(line_cols):
        raise ValueError("reference/template line counts differ")
    if len(reference_special_indexes) != len(template_special_indexes):
        raise ValueError("reference/template special-row counts differ")

    fills: list[int] = []
    retention: list[tuple[bool, ...]] = []
    off_line = [col for col in range(len(template_normal)) if col not in line_cols]
    if not off_line:
        raise ValueError("template needs an off-line fill position")
    for row_index in template_special_indexes:
        row = template[row_index]
        fill = row[off_line[0]]
        if any(row[col] != fill for col in off_line):
            raise ValueError("special template row has inconsistent fill cells")
        fills.append(fill)
        retention.append(tuple(row[col] == color for col, color in zip(line_cols, line_colors)))

    active_start = template_rows[0]
    active_end = template_rows[-1]
    top_gap = active_start
    bottom_gap = height - 1 - active_end
    if top_gap == 0:
        alignment = "top"
    elif bottom_gap == 0:
        alignment = "bottom"
    elif abs(top_gap - bottom_gap) <= 1:
        alignment = "center"
    else:
        alignment = "offset"

    return {
        "height": height,
        "width": width,
        "divider": divider,
        "reference_side": side,
        "reference": reference,
        "reference_rows": reference_rows,
        "reference_width": len(reference[0]),
        "reference_normal": reference_normal,
        "reference_line_cols": reference_line_cols,
        "reference_special_indexes": reference_special_indexes,
        "template": template,
        "template_rows": template_rows,
        "template_width": len(template[0]),
        "template_normal": template_normal,
        "template_line_cols": line_cols,
        "line_colors": line_colors,
        "template_special_indexes": template_special_indexes,
        "fills": fills,
        "retention": retention,
        "template_alignment": alignment,
    }


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    info = analyze(grid)
    reference = info["reference"]
    ref_lines = info["reference_line_cols"]
    special_rows = info["reference_special_indexes"]
    line_colors = info["line_colors"]
    fills = info["fills"]
    retention = info["retention"]
    special_lookup = {row: index for index, row in enumerate(special_rows)}

    output = [[0 for _ in row] for row in reference]
    for row in range(len(reference)):
        special_index = special_lookup.get(row)
        if special_index is None:
            for col, color in zip(ref_lines, line_colors):
                output[row][col] = color
            continue
        fill = fills[special_index]
        output[row] = [fill] * len(reference[row])
        for line_index, col in enumerate(ref_lines):
            if retention[special_index][line_index]:
                output[row][col] = line_colors[line_index]
    return output


def yellow_density_order(grid: list[list[int]]) -> list[list[int]]:
    """Independent rival that orders reference specials by yellow density."""
    info = analyze(grid)
    reference = info["reference"]
    ref_lines = info["reference_line_cols"]
    line_colors = info["line_colors"]
    ordered_rows = sorted(
        info["reference_special_indexes"],
        key=lambda row: (reference[row].count(4), row),
    )
    special_lookup = {row: index for index, row in enumerate(ordered_rows)}
    fills = info["fills"]
    retention = info["retention"]

    output = [[0 for _ in row] for row in reference]
    for row_index in range(len(reference)):
        special_index = special_lookup.get(row_index)
        if special_index is None:
            for column, color in zip(ref_lines, line_colors):
                output[row_index][column] = color
            continue
        output[row_index] = [fills[special_index]] * len(reference[row_index])
        for line_index, column in enumerate(ref_lines):
            if retention[special_index][line_index]:
                output[row_index][column] = line_colors[line_index]
    return output


def pair(grid: list[list[int]]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def observed_controls(grid: list[list[int]]) -> dict[str, str]:
    info = analyze(grid)
    return {
        "reference_side": info["reference_side"],
        "template_alignment": info["template_alignment"],
    }


def first_two_special_rows_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: only the first two special rows are mapped."""
    info = analyze(grid)
    output = intended_output(grid)
    for row in info["reference_special_indexes"][2:]:
        output[row] = [0] * info["reference_width"]
        for col, color in zip(info["reference_line_cols"], info["line_colors"]):
            output[row][col] = color
    return output


def fixed_reference_width_seven(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: force the output width to seven columns."""
    output = intended_output(grid)
    return [row[:7] + [0] * max(0, 7 - len(row)) for row in output]
