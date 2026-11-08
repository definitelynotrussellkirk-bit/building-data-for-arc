"""Parametric common-shape family with a real pair-selection dependency.

The canonical setting is the exact task authority: find the D4 class repeated
among the three largest panel objects and emit its canonical shape.  The
alternative first computes the ordered repeated-shape pair, then consumes that
input-dependent intermediate: selector color 1 chooses its left member and 2
chooses its right member, whose observed normalized orientation is emitted.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "1cbcf1ed9a32"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTPUT_MODES = ("canonical_shape", "selector_member")
OBJECT_COLORS = (3, 4, 6, 7, 8, 9)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

STEP_A = "compare the three largest objects up to D4 and retain the ordered repeated-shape pair"
INTERMEDIATE = "the two matching largest objects in left-to-right panel order"
STEP_B = "use selector 1 or 2 to choose a member of that pair and emit its observed normalized orientation"
WHY_DEPENDS = "the selector is an ordinal within the repeated-shape pair, so no absolute panel can be chosen until the pair is known"

# width is derived as sum(panel_widths)+2 full-height divider columns.
_DEMO_PROFILES = (
    # height, widths, shape_h, shape_w, thickness, common_pair, selector, marker_host
    (7, (4, 4, 4), 3, 3, 1, (1, 2), 1, 0),
    (8, (5, 5, 5), 4, 4, 1, (0, 2), 2, 1),
    (11, (6, 6, 6), 5, 5, 1, (0, 1), 1, 2),
    (14, (7, 7, 7), 6, 6, 2, (1, 2), 2, 0),
    (18, (8, 8, 8), 7, 7, 2, (0, 2), 1, 1),
    (22, (9, 9, 9), 8, 8, 2, (0, 1), 2, 2),
)
_QUERY_PROFILES = (
    (16, (6, 6, 6), 5, 5, 2, (1, 2), 2, 0),
    (23, (8, 8, 8), 7, 7, 2, (0, 2), 1, 1),
    (30, (9, 9, 10), 9, 9, 3, (0, 1), 2, 2),
    (27, (9, 9, 9), 8, 8, 3, (1, 2), 1, 0),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _output_mode(value: object) -> str:
    if type(value) is not str or value not in OUTPUT_MODES:
        raise ValueError(f"output_mode must be one of {OUTPUT_MODES!r}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"output_mode"}:
        raise ValueError("settings must contain exactly output_mode")
    return {"output_mode": _output_mode(value["output_mode"])}


def _grid(value: object) -> list[list[int]]:
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
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    programs = {
        row["program_solution"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical authority")
    return programs.pop()


def program(settings: object) -> str:
    mode = _settings(settings)["output_mode"]
    if mode == "canonical_shape":
        return canonical_program()
    return (HERE / "selector_member.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    """Return a standalone wrong-intermediate rule for the causal witness."""
    source = (HERE / "selector_member.rkt").read_text(encoding="utf-8")
    correct = """  (define matching
    (filter (lambda (o) (equal? (canonical (obj-cells o)) common)) largest))"""
    wrong = """  (define matching (list (first largest) (second largest)))"""
    if source.count(correct) != 1:
        raise ValueError("selector program matching-pair clause changed")
    return source.replace(correct, wrong)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        raise ValueError("cannot normalize an empty shape")
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rot90(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_row = max(row for row, _ in points)
    return _normalize((col, max_row - row) for row, col in points)


def _mirror_h(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_col = max(col for _, col in points)
    return _normalize((row, max_col - col) for row, col in points)


def _d4_orbit(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    base = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        current = _mirror_h(base) if reflected else base
        for _ in range(4):
            variants.add(_normalize(current))
            current = _rot90(current)
    return tuple(sorted(variants))


def _canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _d4_orbit(cells)[0]


def _thick_l(height: int, width: int, thickness: int) -> tuple[tuple[int, int], ...]:
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if col < thickness or row >= height - thickness
    }
    return _normalize(cells)


def _thick_t(height: int, width: int, thickness: int) -> tuple[tuple[int, int], ...]:
    left = (width - thickness) // 2
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row < thickness or left <= col < left + thickness
    }
    return _normalize(cells)


def _components(panel: list[list[int]]) -> list[dict[str, object]]:
    unseen = {
        (row, col)
        for row, line in enumerate(panel)
        for col, value in enumerate(line)
        if value != 0
    }
    found: list[dict[str, object]] = []
    while unseen:
        origin = min(unseen)
        color = panel[origin[0]][origin[1]]
        unseen.remove(origin)
        cells = {origin}
        queue = deque([origin])
        while queue:
            row, col = queue.popleft()
            for dr, dc in CARDINAL:
                point = row + dr, col + dc
                if point in unseen and panel[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    queue.append(point)
        normalized = _normalize(cells)
        found.append(
            {
                "color": color,
                "cells": normalized,
                "size": len(cells),
                "canonical": _canonical(normalized),
            }
        )
    return found


def _divider_columns(value: list[list[int]]) -> list[int]:
    return [
        col
        for col in range(len(value[0]))
        if all(row[col] == 5 for row in value)
    ]


def _panel_bounds(value: list[list[int]]) -> tuple[tuple[int, int], ...]:
    bars = _divider_columns(value)
    if len(bars) != 2:
        raise ValueError(f"expected exactly two full-height color-5 dividers, found {len(bars)}")
    first, second = bars
    if not (0 < first < second - 1 < len(value[0]) - 1):
        raise ValueError("divider columns must leave three nonempty panels")
    return ((0, first), (first + 1, second), (second + 1, len(value[0])))


def _records(value: list[list[int]]) -> dict[str, object]:
    _grid(value)
    bounds = _panel_bounds(value)
    largest = []
    for left, right in bounds:
        panel = [row[left:right] for row in value]
        objects = sorted(_components(panel), key=lambda item: (-int(item["size"]), tuple(item["cells"])))
        if not objects:
            raise ValueError("each panel needs at least one object")
        if len(objects) > 1 and objects[0]["size"] == objects[1]["size"]:
            raise ValueError("each panel needs a unique largest object")
        record = dict(objects[0])
        record["panel"] = len(largest)
        record["left"] = left
        largest.append(record)
    signatures = [record["canonical"] for record in largest]
    counts = Counter(signatures)
    repeated = [signature for signature, count in counts.items() if count == 2]
    if len(repeated) != 1 or sorted(counts.values()) != [1, 2]:
        raise ValueError("exactly two largest objects must share one D4 signature")
    common = repeated[0]
    matching = [record for record in largest if record["canonical"] == common]
    distractor = next(record for record in largest if record["canonical"] != common)
    marker_cells = [
        (row, col, value[row][col])
        for row in range(len(value))
        for col in range(len(value[0]))
        if value[row][col] in (1, 2)
    ]
    if len(marker_cells) != 1:
        raise ValueError("input needs exactly one selector cell colored 1 or 2")
    marker_row, marker_col, selector = marker_cells[0]
    marker_host = next(
        index for index, (left, right) in enumerate(bounds) if left <= marker_col < right
    )
    return {
        "bounds": bounds,
        "largest": largest,
        "counts": counts,
        "common": common,
        "matching": matching,
        "distractor": distractor,
        "selector": selector,
        "marker": (marker_row, marker_col),
        "marker_host": marker_host,
    }


def _render(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    points = _normalize(cells)
    height = max(row for row, _ in points) + 1
    width = max(col for _, col in points) + 1
    result = [[0] * width for _ in range(height)]
    for row, col in points:
        result[row][col] = 8
    return result


def solve(value: list[list[int]], output_mode: str) -> list[list[int]]:
    mode = _output_mode(output_mode)
    records = _records(value)
    if mode == "canonical_shape":
        return _render(records["common"])
    selected = records["matching"][int(records["selector"]) - 1]
    return _render(selected["cells"])


def _prediction(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    records = _records(value)
    largest = records["largest"]
    matching = records["matching"]
    selector = int(records["selector"])
    if hypothesis in OUTPUT_MODES:
        return solve(value, hypothesis)
    if hypothesis == "first_common_orientation":
        return _render(matching[0]["cells"])
    if hypothesis == "second_common_orientation":
        return _render(matching[1]["cells"])
    if hypothesis == "first_panel_orientation":
        return _render(largest[0]["cells"])
    if hypothesis == "last_panel_orientation":
        return _render(largest[-1]["cells"])
    if hypothesis == "selector_absolute_panel":
        return _render(largest[0 if selector == 1 else 2]["cells"])
    if hypothesis == "selector_host_panel":
        return _render(largest[int(records["marker_host"])]["cells"])
    if hypothesis == "distractor_orientation":
        return _render(records["distractor"]["cells"])
    if hypothesis == "repeated_size_else_first_canonical":
        sizes = [int(record["size"]) for record in largest]
        repeated_sizes = [size for size, count in Counter(sizes).items() if count == 2]
        if len(repeated_sizes) == 1:
            selected = next(record for record in largest if record["size"] == repeated_sizes[0])
        else:
            selected = largest[0]
        return _render(selected["canonical"])
    raise ValueError(f"unknown hypothesis: {hypothesis}")


HYPOTHESES = OUTPUT_MODES + (
    "first_common_orientation",
    "second_common_orientation",
    "first_panel_orientation",
    "last_panel_orientation",
    "selector_absolute_panel",
    "selector_host_panel",
    "distractor_orientation",
    "repeated_size_else_first_canonical",
)


def analyze(value: list[list[int]]) -> dict[str, object]:
    try:
        records = _records(value)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    largest = records["largest"]
    matching = records["matching"]
    sizes = [int(record["size"]) for record in largest]
    errors = []
    if len(set(sizes)) != 1:
        errors.append("all three largest objects must have the same cell count")
    if any(int(record["color"]) in (0, 1, 2, 5) for record in largest):
        errors.append("largest-object colors must exclude background, selectors, and dividers")
    if matching[0]["cells"] == matching[1]["cells"]:
        errors.append("the repeated pair must use distinct observed orientations")
    return {
        "errors": errors,
        "height": len(value),
        "width": len(value[0]),
        "panel_widths": [right - left for left, right in records["bounds"]],
        "largest_sizes": sizes,
        "largest_colors": [int(record["color"]) for record in largest],
        "common_pair": [int(record["panel"]) for record in matching],
        "signature_counts": {repr(signature): count for signature, count in records["counts"].items()},
        "selector": int(records["selector"]),
        "marker_host": int(records["marker_host"]),
        "common_orientations_distinct": matching[0]["cells"] != matching[1]["cells"],
        "selected_is_canonical": matching[int(records["selector"]) - 1]["cells"] == records["common"],
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"1cbcf1ed9a32-member-selector-v1:{seed}:{split}:{index}".encode("utf-8")
    return random.Random(hashlib.sha256(payload).digest())


def _paint(
    value: list[list[int]],
    cells: Iterable[tuple[int, int]],
    color: int,
    top: int,
    left: int,
) -> None:
    for row, col in cells:
        rr, cc = top + row, left + col
        if value[rr][cc] != 0:
            raise ValueError("shape placement collision")
        value[rr][cc] = color


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    profile = profiles[index]
    height, widths, shape_h, shape_w, thickness, pair, selector, marker_host = profile
    width = sum(widths) + 2
    rng = _rng(seed, split, index)
    value = [[0] * width for _ in range(height)]
    bars = (widths[0], widths[0] + 1 + widths[1])
    for row in value:
        row[bars[0]] = 5
        row[bars[1]] = 5
    bounds = ((0, bars[0]), (bars[0] + 1, bars[1]), (bars[1] + 1, width))

    common_base = _thick_l(shape_h, shape_w, thickness)
    distractor = _thick_t(shape_h, shape_w, thickness)
    if len(common_base) != len(distractor) or _canonical(common_base) == _canonical(distractor):
        raise RuntimeError("profile shapes lost equal-size/D4 distinction")
    canonical = _canonical(common_base)
    noncanonical = [shape for shape in _d4_orbit(common_base) if shape != canonical]
    if len(noncanonical) < 2:
        raise RuntimeError("common shape needs at least two noncanonical orientations")
    offset = rng.randrange(len(noncanonical))
    first_variant = noncanonical[offset]
    second_variant = next(
        noncanonical[(offset + step) % len(noncanonical)]
        for step in range(1, len(noncanonical) + 1)
        if noncanonical[(offset + step) % len(noncanonical)] != first_variant
    )
    pair_shapes = {pair[0]: first_variant, pair[1]: second_variant}
    colors = rng.sample(list(OBJECT_COLORS), 3)
    for panel_index, (left, right) in enumerate(bounds):
        shape = pair_shapes.get(panel_index, distractor)
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        if shape_height > height - 2 or shape_width > right - left:
            raise RuntimeError("profile shape does not fit its panel")
        top = rng.randrange(0, height - shape_height - 1)
        local_left = rng.randrange(0, (right - left) - shape_width + 1)
        _paint(value, shape, colors[panel_index], top, left + local_left)

    marker_left, marker_right = bounds[marker_host]
    marker_col = marker_left + (marker_right - marker_left) // 2
    if value[height - 1][marker_col] != 0:
        raise RuntimeError("reserved marker cell is occupied")
    value[height - 1][marker_col] = selector
    observed = analyze(value)
    if observed["errors"]:
        raise RuntimeError(f"generated invalid input: {observed['errors']}")
    if observed["common_pair"] != list(pair) or observed["selector"] != selector:
        raise RuntimeError("generated profile roles changed")
    if observed["selected_is_canonical"]:
        raise RuntimeError("selected orientation must differ from canonical output")
    return value


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 4, 4)
    mode = _settings(settings)["output_mode"]
    result: dict[str, object] = {}
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            value = _build_input(seed, split, index)
            signature = json.dumps(value, separators=(",", ":"))
            if signature in seen:
                raise ValueError("all demonstration and query inputs must be distinct")
            seen.add(signature)
            pairs.append({"input": value, "output": solve(value, mode)})
        result[split] = pairs
    result["program_solution"] = program({"output_mode": mode})
    return result


def certificate(train: list[dict[str, object]], query_inputs: list[list[list[int]]]) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("certificate requires 2..6 demonstration pairs")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("certificate requires exactly four query inputs")
    survivors = [
        name
        for name in HYPOTHESES
        if all(_prediction(pair["input"], name) == pair["output"] for pair in train)
    ]
    chosen = next((name for name in survivors if name in OUTPUT_MODES), None)
    disagreement = {
        name: bool(chosen) and any(
            _prediction(value, name) != _prediction(value, chosen) for value in query_inputs
        )
        for name in HYPOTHESES
        if name not in OUTPUT_MODES
    }
    observations = [analyze(pair["input"]) for pair in train]
    noncanonical = any(
        solve(pair["input"], "selector_member") != solve(pair["input"], "canonical_shape")
        for pair in train
    )
    return {
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "query_labels_used_for_inference": False,
        "query_disagreement": disagreement,
        "selector_one_witness": any(row["selector"] == 1 for row in observations),
        "selector_two_witness": any(row["selector"] == 2 for row in observations),
        "panel_zero_distractor_witness": any(0 not in row["common_pair"] for row in observations),
        "noncanonical_orientation_witness": noncanonical,
    }


def public_turn(episode: dict[str, object], query_index: object) -> dict[str, object]:
    query_index = _integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def causal_case() -> dict[str, object]:
    value = _build_input(0, "train", 0)
    records = _records(value)
    correct = [int(record["panel"]) for record in records["matching"]]
    wrong_records = records["largest"][:2]
    selector = int(records["selector"])
    wrong = [int(record["panel"]) for record in wrong_records]
    counterfactual = _render(wrong_records[selector - 1]["cells"])
    output = solve(value, "selector_member")
    if output == counterfactual:
        raise RuntimeError("causal counterfactual must change the final output")
    return {
        "step_a": STEP_A,
        "intermediate_description": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_DEPENDS,
        "input": copy.deepcopy(value),
        "settings": {"output_mode": "selector_member"},
        "selector": selector,
        "intermediate": correct,
        "wrong_intermediate": wrong,
        "output": output,
        "counterfactual_output": counterfactual,
        "program": program({"output_mode": "selector_member"}),
        "counterfactual_program": counterfactual_program(),
        "ablation": "wrong_intermediate",
    }
