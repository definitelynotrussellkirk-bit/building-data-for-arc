"""Independent classifier and finite rival bank for abee0b4bed48.

Written from the Catalog authority and proposed family contract before reading
the prototype. No production or prototype implementation is imported.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable


def strict_grid(grid):
    if type(grid) is not list or len(grid) != 3:
        raise ValueError("the domain has exactly three list rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30 or len(grid[0]) % 3:
        raise ValueError("width must be 3..30 divisible by three")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or value not in (0, 5) for value in row)
           for row in grid):
        raise ValueError("expected rectangular exact lists with exact integer colors 0 or 5")
    return [row[:] for row in grid]


def strict_settings(settings):
    if type(settings) is not dict or set(settings) != {"order"}:
        raise ValueError("expected exactly the order key")
    value = settings["order"]
    if type(value) is not str or value not in ("input", "frequency"):
        raise ValueError("order must be input or frequency")
    return value


def masks(grid):
    return [sum((grid[r][start+c] == 5) << (3*r+c) for r in range(3) for c in range(3))
            for start in range(0, len(grid[0]), 3)]


def mask_grid(values):
    return [[5 if value & (1 << (3*r+c)) else 0
             for value in values for c in range(3)] for r in range(3)]


def classify(value):
    count = value.bit_count()
    if count == 1:
        return 4
    if count == 8:
        return 3
    if count == 3:
        if value == 7:
            return 6
        if value == 448:
            return 1
        return 9
    return 0


def decode(grid):
    return [classify(value) for value in masks(strict_grid(grid))]


def paint(labels):
    return [[value for value in labels for _ in range(3)] for _ in range(3)]


def order_indices(labels, order):
    if order == "input":
        return list(range(len(labels)))
    histogram = Counter(labels)
    return sorted(range(len(labels)), key=lambda i: (-histogram[labels[i]], labels[i], i))


def analyze(grid, settings):
    labels = decode(grid)
    order = strict_settings(settings)
    histogram = Counter(labels)
    permutation = order_indices(labels, order)
    ordered = [labels[index] for index in permutation]
    return {"labels": labels, "frequencies": [histogram[value] for value in labels],
            "permutation": permutation, "ordered_labels": ordered, "output": paint(ordered)}


def model(grid, settings):
    return analyze(grid, settings)["output"]


def _decode_with(grid, order, classifier):
    labels = [classifier(value) for value in masks(grid)]
    return paint([labels[i] for i in order_indices(labels, order)])


def _order_with(grid, order, key, *, always=False):
    values = masks(grid)
    labels = [classify(value) for value in values]
    indexes = list(range(len(labels)))
    if order == "frequency" or always:
        indexes.sort(key=lambda i: key(i, values, labels))
    return paint([labels[i] for i in indexes])


def _skip_when_unique(grid, order):
    labels = [classify(value) for value in masks(grid)]
    if len(set(labels)) == len(labels):
        return paint(labels)
    return paint([labels[i] for i in order_indices(labels, order)])


def _first_seen_groups(grid, order):
    labels = [classify(value) for value in masks(grid)]
    first = {value: labels.index(value) for value in labels}
    return _order_with(grid, order, lambda i, vs, ls: first[ls[i]])


def _connected(value):
    occupied = {i for i in range(9) if value & (1 << i)}
    if not occupied:
        return False
    reached = {min(occupied)}
    todo = list(reached)
    while todo:
        point = todo.pop()
        r, c = divmod(point, 3)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r+dr, c+dc
            neighbor = rr*3+cc
            if 0 <= rr < 3 and 0 <= cc < 3 and neighbor in occupied and neighbor not in reached:
                reached.add(neighbor)
                todo.append(neighbor)
    return reached == occupied


def _paint_masked(grid, order, *, gray_only):
    values = masks(grid)
    labels = [classify(value) for value in values]
    indices = order_indices(labels, order)
    return [[(labels[index] if bool(values[index] & (1 << (3*r+c))) == gray_only
              else (0 if gray_only else 5)) for index in indices for c in range(3)] for r in range(3)]


def _shifted_zones(grid, order):
    shifted = [row[1:] + row[:1] for row in grid]
    return model(shifted, {"order": order})


def _row_major_chunks(grid, order):
    flat = [cell for row in grid for cell in row]
    values = [sum((cell == 5) << j for j, cell in enumerate(flat[i:i+9]))
              for i in range(0, len(flat), 9)]
    labels = [classify(value) for value in values]
    return paint([labels[i] for i in order_indices(labels, order)])


def _global_count(grid, order):
    count = sum(cell == 5 for row in grid for cell in row)
    if count == 1:
        label = 4
    elif count == 8:
        label = 3
    elif count == 3:
        if sum(cell == 5 for cell in grid[0]) == 3:
            label = 6
        elif sum(cell == 5 for cell in grid[2]) == 3:
            label = 1
        else:
            label = 9
    else:
        label = 0
    return paint([label] * (len(grid[0])//3))


def _rows_without_count_gate(value):
    if value.bit_count() in (1, 8):
        return classify(value)
    if value & 7 == 7:
        return 6
    if value & 448 == 448:
        return 1
    return 9 if value.bit_count() == 3 else 0


def _count_as_label(value):
    return {1: 4, 3: 9, 8: 3}.get(value.bit_count(), 0)


@dataclass(frozen=True)
class Rival:
    name: str
    description: str
    predict: Callable


RIVALS = [
    Rival("identity", "Preserve every original zero/gray pixel.", lambda g, o: [row[:] for row in g]),
    Rival("setting_input", "Always use left-to-right decoded labels.", lambda g, o: model(g, {"order": "input"})),
    Rival("setting_frequency", "Always order by descending decoded-class frequency and numeric label.", lambda g, o: model(g, {"order": "frequency"})),
    Rival("frequency_ascending", "Order rare decoded classes before frequent ones.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (Counter(ls)[ls[i]], ls[i], i))),
    Rival("sort_labels", "Sort numeric decoded labels ascending, ignoring occurrence counts.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (ls[i], i), always=True)),
    Rival("sort_labels_desc", "Sort numeric decoded labels descending, ignoring occurrence counts.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-ls[i], i), always=True)),
    Rival("stable_frequency", "Sort descending class frequency but retain input order for all frequency ties.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-Counter(ls)[ls[i]], i))),
    Rival("reverse_label_ties", "Use descending numeric labels to break equal-frequency ties.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-Counter(ls)[ls[i]], -ls[i], i))),
    Rival("gray_count_sort", "Order by original gray count ascending.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (vs[i].bit_count(), i))),
    Rival("gray_count_sort_desc", "Order by original gray count descending.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-vs[i].bit_count(), i))),
    Rival("gray_count_frequency", "Use original gray-count frequencies and ascending gray-count ties.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls:
              (-Counter(x.bit_count() for x in vs)[vs[i].bit_count()], vs[i].bit_count(), i))),
    Rival("weighted_gray_mass", "Rank each decoded class by its total original gray mass.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls:
              (-sum(v.bit_count() for v, lab in zip(vs, ls) if lab == ls[i]), ls[i], i))),
    Rival("pattern_frequency", "Rank exact binary patterns rather than decoded classes.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-Counter(vs)[vs[i]], ls[i], i))),
    Rival("first_seen_groups", "Group decoded classes in their first-occurrence order.", _first_seen_groups),
    Rival("ignore_zero_frequency", "Exclude fallback zero labels from histogram ranking, putting them last.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls: (-(Counter(ls)[ls[i]] if ls[i] else 0), ls[i], i))),
    Rival("stable_singletons", "Sort frequency ties numerically except singleton classes, whose input order remains.",
          lambda g, o: _order_with(g, o, lambda i, vs, ls:
              (-Counter(ls)[ls[i]], i if Counter(ls)[ls[i]] == 1 else ls[i], i))),
    Rival("skip_order_if_all_unique", "Leave decoded input order when all labels are distinct; only frequency-sort repeated classes.", _skip_when_unique),
    Rival("all_three_same", "Map every three-gray pattern to label nine.",
          lambda g, o: _decode_with(g, o, _count_as_label)),
    Rival("top_bottom_swapped", "Swap the top-row and bottom-row three-gray labels.",
          lambda g, o: _decode_with(g, o, lambda v: {6: 1, 1: 6}.get(classify(v), classify(v)))),
    Rival("one_center_only", "Recognize one-gray patterns only at the center.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if v.bit_count() == 1 and v != 16 else classify(v))),
    Rival("one_corner_only", "Recognize one-gray patterns only at a corner.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if v.bit_count() == 1 and v not in (1, 4, 64, 256) else classify(v))),
    Rival("ring_only", "Recognize eight-gray patterns only when their missing cell is the center.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if v.bit_count() == 8 and v != 495 else classify(v))),
    Rival("eight_corner_hole_only", "Recognize eight-gray patterns only when their hole is at a corner.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if v.bit_count() == 8 and (511 ^ v) not in (1, 4, 64, 256) else classify(v))),
    Rival("other_three_diagonal_only", "Recognize only full diagonals as the other-three class.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if classify(v) == 9 and v not in (273, 84) else classify(v))),
    Rival("other_three_middle_only", "Recognize only the full middle row as the other-three class.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if classify(v) == 9 and v != 56 else classify(v))),
    Rival("other_three_connected_only", "Require a four-connected pattern for the other-three class.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if classify(v) == 9 and not _connected(v) else classify(v))),
    Rival("other_three_nonrow_only", "Reject the full middle row from the other-three class.",
          lambda g, o: _decode_with(g, o, lambda v: 0 if v == 56 else classify(v))),
    Rival("rows_without_count_gate", "Recognize full top/bottom rows even when extra gray cells are present.",
          lambda g, o: _decode_with(g, o, _rows_without_count_gate)),
    Rival("fallback_nonzero_to_nine", "Assign nine to all nonempty patterns with inactive gray counts.",
          lambda g, o: _decode_with(g, o, lambda v: 9 if v and classify(v) == 0 else classify(v))),
    Rival("fallback_nearest_count", "Map inactive counts to the nearest active count class.",
          lambda g, o: _decode_with(g, o, lambda v: classify(v) if classify(v) else
              {1: 4, 3: 9, 8: 3}[min((1, 3, 8), key=lambda k: (abs(k-v.bit_count()), k))])),
    Rival("top_row_presence", "For three-gray patterns, any top-row gray gives six, else any bottom-row gray gives one.",
          lambda g, o: _decode_with(g, o, lambda v: (6 if v & 7 else 1 if v & 448 else 9) if v.bit_count() == 3 else classify(v))),
    Rival("transposed_tile", "Treat full left/right columns as the top/bottom classes.",
          lambda g, o: _decode_with(g, o, lambda v: classify(sum(bool(v & (1 << (3*r+c))) << (3*c+r)
                                                            for r in range(3) for c in range(3))))),
    Rival("paint_gray_only", "Recolor only original gray cells, leaving zero cells unchanged.",
          lambda g, o: _paint_masked(g, o, gray_only=True)),
    Rival("paint_background_only", "Paint only original zero cells and preserve gray cells.",
          lambda g, o: _paint_masked(g, o, gray_only=False)),
    Rival("shift_zone_boundary", "Shift every three-column zone boundary cyclically by one column.", _shifted_zones),
    Rival("row_major_nine_chunks", "Partition the row-major flattened strip into nine-pixel chunks.", _row_major_chunks),
    Rival("global_count", "Classify the whole strip by its total gray count and broadcast one label.", _global_count),
    Rival("minimum_two_zones", "Apply the rule only when at least two zones are present.",
          lambda g, o: model(g, {"order": o}) if len(g[0]) >= 6 else [row[:] for row in g]),
]

RIVAL_BY_NAME = {rival.name: rival for rival in RIVALS}


def fit_demos(train, settings):
    """Fit without access to any query input or label."""
    order = strict_settings(settings)
    survivors, rejected, errors = [], {}, {}
    for rival in RIVALS:
        try:
            first = next((i for i, pair in enumerate(train)
                          if rival.predict(pair["input"], order) != pair["output"]), None)
            if first is None:
                survivors.append(rival.name)
            else:
                rejected[rival.name] = first
        except Exception as exc:
            errors[rival.name] = type(exc).__name__ + ": " + str(exc)
    return {"survivors": survivors, "rejected_at_demo": rejected, "execution_errors": errors}


def assess_queries(test, settings, fitted):
    order = strict_settings(settings)
    divergent, errors = {}, {}
    for name in fitted["survivors"]:
        try:
            indices = [i for i, pair in enumerate(test)
                       if RIVAL_BY_NAME[name].predict(pair["input"], order) != pair["output"]]
            if indices:
                divergent[name] = indices
        except Exception as exc:
            errors[name] = type(exc).__name__ + ": " + str(exc)
    return {"query_disagreeing_survivors": divergent, "execution_errors": errors}
