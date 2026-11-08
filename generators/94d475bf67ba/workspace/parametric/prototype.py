"""Constructive nested-frame lessons; Python labels are checked by native Racket.

The two mandatory demonstrations expose tied ownership maxima and an innermost
winner. Input streams are independent of setting and requested pair counts.
This extends geometry only in the separate parametric family, not production.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("all", "largest_owned")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

# Each triple lists outer-to-inner (height, width). These families are
# constructive witnesses, not rejection-selected examples or cached labels.
TIED_SPANS = (
    ((13, 13), (9, 9), (3, 3)),
    ((12, 15), (8, 11), (3, 4)),
    ((15, 18), (11, 14), (6, 9)),
    ((16, 20), (12, 16), (8, 10)),
)
INNER_SPANS = (
    ((18, 18), (14, 14), (10, 10)),
    ((17, 19), (13, 15), (9, 11)),
    ((16, 21), (12, 17), (8, 13)),
    ((18, 20), (14, 16), (10, 12)),
)
LARGE_SPANS = (
    ((30, 30), (26, 26), (22, 22)),
    ((30, 30), (14, 18), (8, 12)),
    ((30, 30), (26, 26), (8, 10)),
    ((30, 30), (26, 26), (2, 22)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly mode='all' or 'largest_owned'")
    return settings["mode"]


def program(settings):
    mode = _mode(settings)
    return (HOME / ("canonical.rkt" if mode == "all" else "largest_owned.rkt")).read_text(encoding="utf-8")


def _inside(frame, r, c):
    top, left, bottom, right = frame["box"]
    return top < r < bottom and left < c < right


def _outline(box):
    top, left, bottom, right = box
    return ({(top, c) for c in range(left, right + 1)}
            | {(bottom, c) for c in range(left, right + 1)}
            | {(r, left) for r in range(top, bottom + 1)}
            | {(r, right) for r in range(top, bottom + 1)})


def analyze(grid):
    """Validate the admitted grammar and expose the actual ownership intermediate.

    Counts align with frames sorted outer-to-inner. Nonoperative terminal
    outlines remain in this inventory with count zero and preserve their cells.
    """
    if (type(grid) is not list or not 7 <= len(grid) <= 30
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be within 7..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    colors = sorted({value for row in grid for value in row if value})
    if len(colors) not in (2, 3):
        raise ValueError("expected two or three distinct nonzero frame colors")
    frames = []
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        box = (min(r for r, _ in cells), min(c for _, c in cells),
               max(r for r, _ in cells), max(c for _, c in cells))
        height, span = box[2] - box[0] + 1, box[3] - box[1] + 1
        if height < 2 or span < 2 or cells != _outline(box):
            raise ValueError(f"color {color} is not one exact rectangular outline")
        frames.append({"color": color, "box": list(box), "height": height, "width": span,
                       "area": height * span, "border_size": len(cells),
                       "operative": height >= 3 and span >= 3})
    frames.sort(key=lambda frame: frame["area"], reverse=True)
    for outer, inner in zip(frames, frames[1:]):
        a, b = outer["box"], inner["box"]
        if min(b[0] - a[0], b[1] - a[1], a[2] - b[2], a[3] - b[3]) < 2:
            raise ValueError("frames must be strictly nested with a complete zero ring")
    if not all(frame["operative"] for frame in frames[:2]):
        raise ValueError("at least the two outermost frames must be operative")
    owners, counts = _ownership(grid, [frame for frame in frames if frame["operative"]])
    if any(counts.get(frame["color"], 0) <= 0 for frame in frames if frame["operative"]):
        raise ValueError("every operative frame must own some zero cells")
    return {"frames": frames, "owned_counts": [counts.get(frame["color"], 0) for frame in frames],
            "owners": owners}


def _ownership(grid, frames, *, maximum_color=False):
    counts = {frame["color"]: 0 for frame in frames}
    owners = [[0 for _ in row] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                continue
            hits = [frame for frame in frames if _inside(frame, r, c)]
            if hits:
                owner = (max(hits, key=lambda frame: frame["color"]) if maximum_color
                         else min(hits, key=lambda frame: frame["area"]))
                owners[r][c] = owner["color"]
                counts[owner["color"]] += 1
    return owners, counts


def predict(grid, mode, *, rival=None):
    """Independent typed Python claims; Racket remains the label authority."""
    if mode not in MODES:
        raise ValueError("unknown rule mode")
    frames = [frame for frame in analyze(grid)["frames"] if frame["operative"]]
    if rival in ("two_levels_only", "canonical_two_levels"):
        frames = frames[:2]
    owners, counts = _ownership(grid, frames, maximum_color=rival in (
        "maximum_color_owner", "canonical_maximum_color_owner"))
    if mode == "all" or rival in ("canonical_two_levels", "canonical_maximum_color_owner"):
        selected = set(counts)
    elif rival == "outermost_only":
        selected = {frames[0]["color"]}
    elif rival == "innermost_only":
        selected = {frames[-1]["color"]}
    else:
        scores = dict(counts)
        if rival == "raw_contained_count":
            scores = {frame["color"]: sum(value == 0 and _inside(frame, r, c)
                      for r, row in enumerate(grid) for c, value in enumerate(row)) for frame in frames}
        elif rival == "border_count_in_score":
            scores = {frame["color"]: counts[frame["color"]] + frame["border_size"] for frame in frames}
        high = max(scores.values(), default=0)
        selected = {color for color, score in scores.items() if score == high and score > 0}
        if rival == "tie_first_only":
            selected = {next(frame["color"] for frame in reversed(frames) if frame["color"] in selected)} if selected else set()
    output = deepcopy(grid)
    for r, row in enumerate(owners):
        for c, color in enumerate(row):
            if rival == "selected_containment_paint" and grid[r][c] == 0:
                hits = [frame for frame in frames if frame["color"] in selected and _inside(frame, r, c)]
                if hits:
                    output[r][c] = min(hits, key=lambda frame: frame["area"])["color"]
                continue
            if color in selected:
                output[r][c] = color
    return output


def candidate_outputs(grid):
    result = {mode: predict(grid, mode) for mode in MODES}
    for name in ("raw_contained_count", "outermost_only", "innermost_only", "two_levels_only",
                 "maximum_color_owner", "tie_first_only", "border_count_in_score",
                 "canonical_two_levels", "canonical_maximum_color_owner", "selected_containment_paint"):
        result[name] = predict(grid, "largest_owned", rival=name)
    return result


def teaching_report(demos, query_inputs, mode):
    """Fit finite rivals to demos only; query labels are never accepted here."""
    if mode not in MODES or not demos:
        raise ValueError("a known mode and at least one labeled demonstration are required")
    predictions = [candidate_outputs(pair["input"]) for pair in demos]
    names = list(predictions[0])
    survivors = [name for name in names if all(pred[name] == pair["output"] for pred, pair in zip(predictions, demos))]
    rejected_by = {name: [i for i, (pred, pair) in enumerate(zip(predictions, demos)) if pred[name] != pair["output"]]
                   for name in names if name not in survivors}
    ambiguous = []
    for index, grid in enumerate(query_inputs):
        choices = candidate_outputs(grid)
        disagree = [name for name in survivors if choices[name] != choices[mode]]
        if disagree:
            ambiguous.append({"query_index": index, "disagreeing_survivors": disagree})
    return {"survivors": survivors, "rejected_by_demonstration": rejected_by,
            "ambiguous_queries": ambiguous,
            "scope": "finite named hypotheses; fitted only to demonstration input/output pairs"}


def _rng(seed, split, index):
    digest = hashlib.sha256(f"94d475bf67ba:owned-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _render(spans, rng, *, shape=None, descending_colors=False):
    spans = list(spans)
    if rng.randrange(2):
        spans = [(w, h) for h, w in spans]
        if shape is not None:
            shape = (shape[1], shape[0])
    if shape is None:
        shape = (spans[0][0] + rng.randrange(min(4, 30 - spans[0][0]) + 1),
                 spans[0][1] + rng.randrange(min(4, 30 - spans[0][1]) + 1))
    height, width = shape
    colors = rng.sample(range(1, 10), len(spans))
    if descending_colors:
        colors.sort(reverse=True)
    grid = [[0] * width for _ in range(height)]
    top = rng.randrange(height - spans[0][0] + 1)
    left = rng.randrange(width - spans[0][1] + 1)
    for index, ((h, w), color) in enumerate(zip(spans, colors)):
        if index:
            parent_h, parent_w = spans[index - 1]
            top += rng.randint(2, parent_h - h - 2)
            left += rng.randint(2, parent_w - w - 2)
        for r, c in _outline((top, left, top + h - 1, left + w - 1)):
            grid[r][c] = color
    return grid


def _scene(seed, split, index):
    rng = _rng(seed, split, index)
    if split == "demo" and index < 2:
        spans = rng.choice(TIED_SPANS if index == 0 else INNER_SPANS)
        return _render(spans, rng, descending_colors=index == 0)
    if split == "query":
        if index == 0:
            return _render(((7, 7), (3, 3)), rng, shape=(7, 7))
        if index == 1:
            return _render(((10, 13), (6, 9), (2, 5)), rng, shape=(10, 13))
        if index == 2:
            return _render(((21, 27), (17, 23), (7, 11)), rng, shape=(21, 27))
        return _render(rng.choice(LARGE_SPANS), rng, shape=(30, 30))
    n_frames = rng.choice((2, 3))
    minimum = 4 * (n_frames - 1) + 3
    h, w = rng.randint(minimum, 26), rng.randint(minimum, 26)
    spans = [(h, w)]
    for depth in range(1, n_frames):
        minimum_child = 4 * (n_frames - depth - 1) + 3
        h, w = rng.randint(minimum_child, h - 4), rng.randint(minimum_child, w - 4)
        spans.append((h, w))
    return _render(spans, rng)


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, *DEMO_LIMITS, "demos")
    _integer(queries, *QUERY_LIMITS, "queries")
    output = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count, stream in (("train", demos, "demo"), ("test", queries, "query")):
        for index in range(count):
            grid = _scene(seed, stream, index)
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                # No duplicate filler, retries, hidden reduced counts, or seed fallbacks.
                raise ValueError("constructive scene collision; use a different seed")
            seen.add(key)
            output[split].append({"input": grid, "output": predict(grid, mode)})
    report = teaching_report(output["train"], [], mode)
    if report["survivors"] != [mode]:
        raise ValueError(f"constructive demonstrations failed finite teaching check: {report['survivors']}")
    return output


def public_challenge(episode, query_index=0, *, all_queries=False):
    """Projection only: the existing consumer controls sequential revelation.

    Default is one query, with no total, turn, seed, program, setting or future
    input hint. The grouped projection is for controller storage/export checks.
    """
    if type(all_queries) is not bool:
        raise ValueError("all_queries must be Boolean")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    selected = episode["test"] if all_queries else [episode["test"][query_index]]
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in selected]}
