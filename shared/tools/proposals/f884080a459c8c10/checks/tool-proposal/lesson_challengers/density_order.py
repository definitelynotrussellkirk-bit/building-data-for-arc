"""Intentional external rival: align special reference rows by yellow density.
Copied independent parser from the retained audit; no generator imports.
"""
from collections import Counter


def facts(grid):
    """Independent structural reading of the reference/template row rule."""
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(row[c] == 5 for row in grid)]
    assert len(dividers) == 1
    d = dividers[0]

    def panel(start, stop):
        return [row[start:stop] for row in grid if any(value != 5 for value in row[start:stop])]

    left, right = panel(0, d), panel(d + 1, w)
    if all(value in (0, 4) for row in left for value in row):
        reference, template = left, right
    else:
        reference, template = right, left
    signatures = Counter(map(tuple, template))
    modal = [row for row, count in signatures.items() if count == max(signatures.values())]
    assert len(modal) == 1
    normal = list(modal[0])
    template_columns = [c for c, value in enumerate(normal) if value]
    colors = [normal[c] for c in template_columns]
    off_line = [c for c in range(len(normal)) if c not in template_columns]
    specials = [row for row in template if row != normal]
    positive = [row for row in reference if 4 in row]
    reference_normal = min(positive, key=lambda row: row.count(4))
    reference_columns = [c for c, value in enumerate(reference_normal) if value == 4]
    reference_special_rows = [r for r, row in enumerate(reference) if 4 in row and row != reference_normal]
    assert len(reference_columns) == len(template_columns)
    assert len(reference_special_rows) == len(specials)
    return {
        "reference": reference, "columns": reference_columns, "colors": colors,
        "special_rows": reference_special_rows,
        "yellow_counts": [reference[r].count(4) for r in reference_special_rows],
        "fills": [row[off_line[0]] for row in specials],
        "retention": [[row[c] == color for c, color in zip(template_columns, colors)] for row in specials],
    }


def predict(grid, *, density_order=False):
    info = facts(grid)
    rows = info["special_rows"]
    if density_order:
        rows = sorted(rows, key=lambda r: (info["reference"][r].count(4), r))
    index_for = {row: index for index, row in enumerate(rows)}
    result = []
    for r, reference_row in enumerate(info["reference"]):
        if r in index_for:
            index = index_for[r]
            row = [info["fills"][index]] * len(reference_row)
            for k, c in enumerate(info["columns"]):
                if info["retention"][index][k]:
                    row[c] = info["colors"][k]
        else:
            row = [0] * len(reference_row)
            for c, color in zip(info["columns"], info["colors"]):
                row[c] = color
        result.append(row)
    return result


def density_order(grid):
    return predict(grid, density_order=True)
