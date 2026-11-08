"""Native output-order parameterization for ARC generator 1b7cbdffd485.

The exact canonical setting scans row-major, records each nonzero color at its
first occurrence, compares the coordinate spans of those first-hit triples, and
lays the colors out along the dominant axis.  The alternative preserves that
entire input-dependent intermediate and orientation decision, but consumes the
ordered colors in reverse first-seen order.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import copy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root


TASK_ID = "1b7cbdffd485"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
OUTPUT_ORDERS = ("first_seen", "reverse_first_seen")


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _output_order(value):
    if type(value) is not str or value not in OUTPUT_ORDERS:
        raise ValueError("output_order must be first_seen or reverse_first_seen")
    return value


def grid(value):
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program():
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical Racket authority")
    return programs.pop()


def program(settings):
    if type(settings) is not dict or set(settings) != {"output_order"}:
        raise ValueError("only the output_order setting is declared")
    selected = _output_order(settings["output_order"])
    if selected == "first_seen":
        return canonical_program()
    return (HERE / "reverse_first_seen.rkt").read_text(encoding="utf-8")


def _coordinates(height, width, scan_order="row_major"):
    if scan_order == "row_major":
        return ((row, col) for row in range(height) for col in range(width))
    if scan_order == "column_major":
        return ((row, col) for col in range(width) for row in range(height))
    raise ValueError("scan_order must be row_major or column_major")


def _scan_hits(value, scan_order):
    grid(value)
    height, width = len(value), len(value[0])
    seen = set()
    hits = []
    for row, col in _coordinates(height, width, scan_order):
        color = value[row][col]
        if color > 0 and color not in seen:
            seen.add(color)
            hits.append((color, row, col))
    if not hits:
        raise ValueError("rule requires at least one nonzero color")
    return hits


def first_hits(value):
    """Return the canonical row-major first-hit intermediate."""
    return _scan_hits(value, "row_major")


def _orientation(hits, *, strict_tie=False):
    row_span = max(row for _, row, _ in hits) - min(row for _, row, _ in hits)
    col_span = max(col for _, _, col in hits) - min(col for _, _, col in hits)
    if strict_tie:
        return "column" if row_span > col_span else "row"
    return "column" if row_span >= col_span else "row"


def _from_hits(hits, output_order, *, force_orientation=None, strict_tie=False):
    if not hits:
        raise ValueError("first-hit intermediate must not be empty")
    selected = _output_order(output_order)
    colors = [color for color, _, _ in hits]
    if selected == "reverse_first_seen":
        colors.reverse()
    orientation = force_orientation or _orientation(hits, strict_tie=strict_tie)
    if orientation == "column":
        return [[color] for color in colors]
    if orientation == "row":
        return [colors]
    raise ValueError("orientation must be row or column")


def transform(value, output_order):
    return _from_hits(first_hits(value), output_order)


def _connected(value, color):
    cells = {
        (row, col)
        for row in range(len(value))
        for col in range(len(value[0]))
        if value[row][col] == color
    }
    if not cells:
        return False
    queue = deque([next(iter(cells))])
    seen = set(queue)
    while queue:
        row, col = queue.popleft()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def observe(value):
    errors = []
    try:
        grid(value)
    except ValueError as exc:
        return {"errors": [str(exc)], "colors": []}
    colors = []
    for row in value:
        for color in row:
            if color not in colors:
                colors.append(color)
    if 0 in colors:
        errors.append("the admitted grammar fully partitions the canvas; zero is forbidden")
    nonzero = [color for color in colors if color]
    if not 3 <= len(nonzero) <= 6:
        errors.append(f"expected 3..6 nonzero colors, got {len(nonzero)}")
    counts = Counter(cell for row in value for cell in row if cell)
    for color in nonzero:
        if counts[color] < 4:
            errors.append(f"color {color} has fewer than four cells")
        if not _connected(value, color):
            errors.append(f"color {color} is not one 4-connected region")
    hits = first_hits(value) if nonzero else []
    return {
        "errors": errors,
        "height": len(value),
        "width": len(value[0]),
        "colors": nonzero,
        "counts": dict(counts),
        "first_hits": hits,
        "orientation": _orientation(hits) if hits else None,
        "row_span": (
            max(row for _, row, _ in hits) - min(row for _, row, _ in hits)
            if hits
            else None
        ),
        "column_span": (
            max(col for _, _, col in hits) - min(col for _, _, col in hits)
            if hits
            else None
        ),
    }


def _rng(seed, role, slot):
    payload = f"1b7cbdffd485-output-order-v2:{seed}:{role}:{slot}".encode()
    return random.Random(hashlib.sha256(payload).digest())


def _palette(rng, count):
    values = sorted(rng.sample(range(1, 10), count))
    # A proper cyclic shift is neither numeric ascending nor descending.  Thus
    # both the forward and reversed teaching orders reject numeric sorting.
    shift = 1 + rng.randrange(count - 1)
    values = values[shift:] + values[:shift]
    if values == sorted(values, reverse=True):
        values[0], values[1] = values[1], values[0]
    return values


def _tie_quadrants(rng, size):
    """Four equal quadrants: row_span == column_span, hence canonical column."""
    if size % 2:
        raise ValueError("tie quadrants require an even square")
    a, b, c, d = _palette(rng, 4)
    split = size // 2
    return [
        [
            a if row < split and col < split
            else b if row < split
            else c if col < split
            else d
            for col in range(size)
        ]
        for row in range(size)
    ]


def _teaching_corner(rng, height, width):
    """A horizontal-dominant lesson whose frequency order differs from first seen."""
    a, b, c = _palette(rng, 3)
    row_split = height // 3
    col_split = (2 * width) // 3
    result = []
    for row in range(height):
        line = []
        for col in range(width):
            if col >= col_split:
                line.append(b)
            elif row >= row_split:
                line.append(c)
            else:
                line.append(a)
        result.append(line)
    hits = first_hits(result)
    counts = Counter(cell for line in result for cell in line)
    frequency = sorted(
        [color for color, _, _ in hits],
        key=lambda color: (-counts[color], [x[0] for x in hits].index(color)),
    )
    if _orientation(hits) != "row" or frequency == [x[0] for x in hits]:
        raise RuntimeError("teaching corner lost its row/frequency witness")
    return result


def _corner_partition(rng, height, width):
    a, b, c = _palette(rng, 3)
    row_split = max(3, min(height - 3, height // 2 + rng.choice((-2, -1, 0, 1))))
    col_split = max(3, min(width - 3, width // 2 + rng.choice((-1, 0, 1, 2))))
    return [
        [
            b if col >= col_split else c if row >= row_split else a
            for col in range(width)
        ]
        for row in range(height)
    ]


def _four_quadrants(rng, height, width):
    a, b, c, d = _palette(rng, 4)
    row_split = max(3, min(height - 3, height // 2 + rng.choice((-1, 0, 1))))
    col_split = max(3, min(width - 3, width // 2 + rng.choice((-1, 0, 1))))
    return [
        [
            a if row < row_split and col < col_split
            else b if row < row_split
            else c if col < col_split
            else d
            for col in range(width)
        ]
        for row in range(height)
    ]


def _diagonal_partition(rng, height, width):
    """Three connected sloping regions with horizontally spread first hits."""
    a, b, c = _palette(rng, 3)
    result = []
    for row in range(height):
        fraction = row / (height - 1)
        a_width = round(width * (0.55 - 0.40 * fraction))
        c_start = round(width * (0.88 - 0.40 * fraction))
        a_width = max(1, min(width - 3, a_width))
        c_start = max(a_width + 2, min(width - 1, c_start))
        result.append(
            [a if col < a_width else b if col < c_start else c for col in range(width)]
        )
    if _orientation(first_hits(result)) != "row":
        raise RuntimeError("diagonal profile lost its horizontal first-hit witness")
    return result


def _composition(rng, total, count, minimum=2):
    parts = [minimum] * count
    for _ in range(total - minimum * count):
        parts[rng.randrange(count)] += 1
    return parts


def _bands(rng, height, width, count, *, vertical):
    colors = _palette(rng, count)
    thicknesses = _composition(rng, height, count)
    base = []
    cursor = 0
    for thickness in thicknesses[:-1]:
        cursor += thickness
        base.append(cursor)
    previous = base[:]
    boundaries_by_col = []
    for col in range(width):
        current = []
        for index, initial in enumerate(base):
            proposal = initial if col == 0 else previous[index] + rng.choice((-1, 0, 0, 1))
            lower = 2 if index == 0 else current[index - 1] + 2
            upper = height - 2 * (count - index - 1)
            current.append(max(lower, min(upper, proposal)))
        boundaries_by_col.append(current)
        previous = current
    result = [[0 for _ in range(width)] for _ in range(height)]
    for col, boundaries in enumerate(boundaries_by_col):
        for row in range(height):
            band = sum(row >= boundary for boundary in boundaries)
            result[row][col] = colors[band]
    if vertical:
        result = [list(row) for row in zip(*result)]
    return result


def _demo_input(seed, slot):
    rng = _rng(seed, "demo", slot)
    if slot == 0:
        return _tie_quadrants(rng, 14 + 2 * rng.randrange(2))
    if slot == 1:
        return _teaching_corner(rng, 16 + 2 * rng.randrange(2), 18 + 2 * rng.randrange(2))
    if slot == 2:
        return _diagonal_partition(rng, 18 + rng.randrange(3), 19 + rng.randrange(3))
    if slot == 3:
        return _bands(rng, 20, 15, 4, vertical=False)
    if slot == 4:
        return _bands(rng, 16, 23, 5, vertical=True)
    if slot == 5:
        return _corner_partition(rng, 24, 20)
    raise ValueError("unsupported demonstration slot")


def _query_input(seed, slot):
    rng = _rng(seed, "query", slot)
    if slot == 0:
        return _corner_partition(rng, 21, 19)
    if slot == 1:
        return _diagonal_partition(rng, 24, 20)
    if slot == 2:
        return _four_quadrants(rng, 30, 30)
    if slot == 3:
        return _bands(rng, 30, 30, 6, vertical=bool(rng.randrange(2)))
    raise ValueError("exactly four query slots are supported")


HYPOTHESES = OUTPUT_ORDERS + (
    "numeric_order",
    "frequency_order",
    "column_major_order",
    "always_row_first_seen",
    "always_column_first_seen",
    "always_row_reverse_first_seen",
    "always_column_reverse_first_seen",
    "strict_tie_first_seen",
    "strict_tie_reverse_first_seen",
)


def _with_colors(hits, colors, *, force_orientation=None, strict_tie=False):
    orientation = force_orientation or _orientation(hits, strict_tie=strict_tie)
    return [[color] for color in colors] if orientation == "column" else [list(colors)]


def predict(value, hypothesis):
    hits = first_hits(value)
    colors = [color for color, _, _ in hits]
    if hypothesis in OUTPUT_ORDERS:
        return _from_hits(hits, hypothesis)
    if hypothesis == "numeric_order":
        return _with_colors(hits, sorted(colors))
    if hypothesis == "frequency_order":
        counts = Counter(cell for row in value for cell in row if cell)
        ordered = sorted(colors, key=lambda color: (-counts[color], colors.index(color)))
        return _with_colors(hits, ordered)
    if hypothesis == "column_major_order":
        ordered = [color for color, _, _ in _scan_hits(value, "column_major")]
        return _with_colors(hits, ordered)
    if hypothesis == "always_row_first_seen":
        return _with_colors(hits, colors, force_orientation="row")
    if hypothesis == "always_column_first_seen":
        return _with_colors(hits, colors, force_orientation="column")
    if hypothesis == "always_row_reverse_first_seen":
        return _with_colors(hits, list(reversed(colors)), force_orientation="row")
    if hypothesis == "always_column_reverse_first_seen":
        return _with_colors(hits, list(reversed(colors)), force_orientation="column")
    if hypothesis == "strict_tie_first_seen":
        return _with_colors(hits, colors, strict_tie=True)
    if hypothesis == "strict_tie_reverse_first_seen":
        return _with_colors(hits, list(reversed(colors)), strict_tie=True)
    raise ValueError("unknown declared hypothesis")


def _shape(output):
    return (len(output), len(output[0]))


def certificate(train, query_inputs):
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six teaching demonstrations are required")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("exactly four query inputs are required")
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each teaching pair needs input and output")
        grid(pair["input"])
        grid(pair["output"])
    for value in query_inputs:
        grid(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(predict(pair["input"], name) == pair["output"] for pair in train)
    ]
    if len(survivors) != 1 or survivors[0] not in OUTPUT_ORDERS:
        raise ValueError("demonstrations do not identify one declared output order")
    orientations = [_orientation(first_hits(pair["input"])) for pair in train]
    tie_boundary_witness = any(
        observe(pair["input"])["row_span"] == observe(pair["input"])["column_span"]
        for pair in train
    )
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "query_labels_used_for_inference": False,
        "row_output_witness": "row" in orientations,
        "column_output_witness": "column" in orientations,
        "tie_boundary_witness": tie_boundary_witness,
        "predicted_query_sha256": [
            hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()
            for value in predictions
        ],
        "scope": "Finite declared rivals and generated grammar; not universal rule uniqueness.",
    }


def _pair(value, output_order):
    return {"input": copy.deepcopy(value), "output": transform(value, output_order)}


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    if type(settings) is not dict or set(settings) != {"output_order"}:
        raise ValueError("only the output_order setting is declared")
    selected = _output_order(settings["output_order"])

    demo_inputs = [_demo_input(seed, slot) for slot in range(demos)]
    query_inputs = [_query_input(seed, slot) for slot in range(queries)]
    inputs = demo_inputs + query_inputs
    identities = [json.dumps(value, separators=(",", ":")) for value in inputs]
    if len(identities) != len(set(identities)):
        raise ValueError("all demonstration and query inputs must be distinct")
    for value in inputs:
        info = observe(value)
        if info["errors"]:
            raise ValueError("invalid generated scene: " + "; ".join(info["errors"]))
    if _orientation(first_hits(demo_inputs[0])) != "column":
        raise ValueError("first teaching demonstration lost its tie/column witness")
    if observe(demo_inputs[0])["row_span"] != observe(demo_inputs[0])["column_span"]:
        raise ValueError("first teaching demonstration lost its exact tie")
    if _orientation(first_hits(demo_inputs[1])) != "row":
        raise ValueError("second teaching demonstration lost its row witness")

    episode = {
        "train": [_pair(value, selected) for value in demo_inputs],
        "test": [_pair(value, selected) for value in query_inputs],
        "program_solution": program({"output_order": selected}),
    }
    checked = certificate(episode["train"], query_inputs)
    if checked["survivors"] != [selected]:
        raise ValueError("constructed lesson did not identify the selected output order")
    return episode


def causal_witness():
    value = [
        [8, 8, 8, 2, 2, 2],
        [8, 8, 8, 2, 2, 2],
        [8, 8, 8, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
    ]
    hits = first_hits(value)
    actual_intermediate = [color for color, _, _ in hits]
    wrong_intermediate = list(reversed(actual_intermediate))
    return {
        "step_a": "scan row-major and record ordered first-hit color/coordinate triples",
        "intermediate": "ordered (color,row,column) first-hit triples",
        "step_b": "compare coordinate spans, orient the output, and place colors in the episode order",
        "why_b_depends_on_a": "the triples determine both output orientation and the color sequence consumed by the episode order",
        "input": copy.deepcopy(value),
        "output_order": "first_seen",
        "counterfactual_output_order": "reverse_first_seen",
        "actual_intermediate": actual_intermediate,
        "wrong_intermediate": wrong_intermediate,
        "actual_output": transform(value, "first_seen"),
        "counterfactual_output": transform(value, "reverse_first_seen"),
        "actual_program": "canonical row-major first-seen Racket authority",
        "counterfactual_program": "reverse_first_seen.rkt",
        "ablation": "wrong_order",
    }


def public_turn(episode, query_index):
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    query = {"input": copy.deepcopy(episode["test"][query_index]["input"])}
    return {"train": train, "test": [query]}
