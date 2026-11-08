"""Native matched-input parametric family for ``b19deac47327``.

``project_only`` is the exact selected canonical Racket rule. The nearby
``project_then_bridge`` setting performs the canonical projection first, then
uses the resulting interior border-colored seed cells as an input-dependent
intermediate: it groups aligned seeds, selects the unique group with the most
seeds, and fills the span between that group's endpoints. Python labels are
claims only; native qualification re-executes every label in protected Racket.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable


TASK_ID = "b19deac47327"
CANONICAL_PROGRAM_SHA256 = "18c042039414a6bd8745b9ffc3277879010959e3ce76d64d94d4d16925343dd8"
FINISH_RULES = ("project_only", "project_then_bridge")
SETTINGS = tuple({"finish_rule": value} for value in FINISH_RULES)
DEFAULT_SETTINGS = SETTINGS[0]

Grid = list[list[int]]


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    orientation: str
    winner_side: str
    winner_count: int
    distractor_count: int
    tie_marker: bool = False


# Ordinary demonstration counts are prefixes of this six-profile curriculum.
# The first two profiles already cover both orientations and both winner sides.
DEMO_PROFILES = (
    Profile(12, 10, "horizontal", "first", 4, 3),
    Profile(12, 13, "vertical", "second", 4, 3),
    Profile(15, 17, "horizontal", "second", 5, 4, True),
    Profile(17, 15, "vertical", "first", 5, 4),
    Profile(18, 20, "horizontal", "first", 5, 4),
    Profile(20, 18, "vertical", "second", 5, 4),
)
QUERY_PROFILES = (
    Profile(13, 15, "horizontal", "second", 4, 3, True),
    Profile(18, 22, "vertical", "first", 5, 4),
    Profile(24, 27, "horizontal", "first", 5, 4),
    Profile(30, 30, "vertical", "second", 5, 4),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish_rule"}:
        raise ValueError("settings must contain exactly finish_rule")
    value = settings["finish_rule"]
    if type(value) is not str or value not in FINISH_RULES:
        raise ValueError("finish_rule must be project_only or project_then_bridge")
    return {"finish_rule": value}


def _root_and_canonical() -> tuple[Path, Path]:
    for root in Path(__file__).resolve().parents:
        direct = root / "data/canonical/puzzles.jsonl"
        if direct.is_file() and (root / "RUNTIME_MANIFEST.json").is_file():
            return root, direct
        shared = root / "shared/data/canonical/puzzles.jsonl"
        if shared.is_file():
            return root, shared
    raise FileNotFoundError("parametric prototype needs its source or staged runtime")


ROOT, CANONICAL_PATH = _root_and_canonical()
PARAMETRIC_HOME = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def canonical_record() -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one selected canonical row; found {len(matches)}")
    source = matches[0].get("program_solution")
    if not isinstance(source, str) or hashlib.sha256(source.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("selected canonical program changed; re-author and requalify")
    return matches[0]


def program(settings: object) -> str:
    setting = normalize_settings(settings)["finish_rule"]
    filename = "canonical.rkt" if setting == "project_only" else "bridge_longest.rkt"
    source = (PARAMETRIC_HOME / filename).read_text(encoding="utf-8")
    if setting == "project_only" and source != canonical_record()["program_solution"]:
        raise ValueError("canonical.rkt must remain byte-identical to selected authority")
    return source


def _grid(value: object) -> Grid:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def _solid(values: Iterable[int]) -> int | None:
    values = list(values)
    if values and len(set(values)) == 1 and values[0] not in (0, 1):
        return values[0]
    return None


def _facts(grid: object, *, allow_interior_border_colors: bool = False) -> dict[str, Any]:
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    top = _solid(grid[0])
    bottom = _solid(grid[-1])
    left = _solid(row[0] for row in grid)
    right = _solid(row[-1] for row in grid)
    horizontal = top is not None and bottom is not None
    vertical = left is not None and right is not None
    if horizontal == vertical:
        raise ValueError("exactly one pair of opposite solid colored borders is required")
    if horizontal:
        orientation = "horizontal"
        first_color, second_color = top, bottom
        extent, lane_extent = height, width
    else:
        orientation = "vertical"
        first_color, second_color = left, right
        extent, lane_extent = width, height
    assert first_color is not None and second_color is not None
    if first_color == second_color:
        raise ValueError("border colors must differ")
    allowed = {0, 1, first_color, second_color}
    palette = {cell for row in grid for cell in row}
    if not palette <= allowed:
        raise ValueError("input contains colors outside background, marker, and border colors")
    markers: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            on_colored_border = row in (0, height - 1) if horizontal else col in (0, width - 1)
            value = grid[row][col]
            if value == 1:
                if on_colored_border:
                    raise ValueError("markers cannot replace the colored border")
                markers.append((row, col))
            elif not on_colored_border and value in (first_color, second_color) and not allow_interior_border_colors:
                raise ValueError("border colors cannot appear in the input interior")
            elif not on_colored_border and value not in (0, 1, first_color, second_color):
                raise ValueError("invalid interior value")
    return {
        "height": height,
        "width": width,
        "orientation": orientation,
        "first_color": first_color,
        "second_color": second_color,
        "extent": extent,
        "lane_extent": lane_extent,
        "markers": markers,
    }


def _marker_axis_lane(facts: dict[str, Any], cell: tuple[int, int]) -> tuple[int, int]:
    row, col = cell
    if facts["orientation"] == "horizontal":
        return row, col
    return col, row


def _cell_from_axis_lane(facts: dict[str, Any], axis: int, lane: int) -> tuple[int, int]:
    if facts["orientation"] == "horizontal":
        return axis, lane
    return lane, axis


def project(grid: Grid) -> Grid:
    """Python mirror of the exact canonical projection stage."""
    facts = _facts(grid)
    output = copy.deepcopy(grid)
    destinations: set[tuple[int, int]] = set()
    for marker in facts["markers"]:
        axis, lane = _marker_axis_lane(facts, marker)
        first = 2 * axis < facts["extent"]
        destination = _cell_from_axis_lane(facts, axis - 1 if first else axis + 1, lane)
        row, col = destination
        if not (0 <= row < facts["height"] and 0 <= col < facts["width"]):
            raise ValueError("marker projection leaves the grid")
        if grid[row][col] != 0:
            raise ValueError("every projection destination must be background")
        if destination in destinations:
            raise ValueError("projection destinations must be unique")
        destinations.add(destination)
        output[row][col] = facts["first_color"] if first else facts["second_color"]
    return output


def _records(original: Grid, intermediate: Grid) -> list[dict[str, Any]]:
    facts = _facts(original)
    intermediate = _grid(intermediate)
    if (len(intermediate), len(intermediate[0])) != (facts["height"], facts["width"]):
        raise ValueError("intermediate dimensions must match the original input")
    records: list[dict[str, Any]] = []
    for line in range(1, facts["extent"] - 1):
        for side, color in (("first", facts["first_color"]), ("second", facts["second_color"])):
            cells: list[tuple[int, int]] = []
            lanes: list[int] = []
            for lane in range(facts["lane_extent"]):
                row, col = _cell_from_axis_lane(facts, line, lane)
                if original[row][col] == 0 and intermediate[row][col] == color:
                    cells.append((row, col))
                    lanes.append(lane)
            if len(lanes) >= 2:
                lo, hi = min(lanes), max(lanes)
                records.append({
                    "side": side,
                    "color": color,
                    "line": line,
                    "count": len(lanes),
                    "span": hi - lo + 1,
                    "lo": lo,
                    "hi": hi,
                    "cells": cells,
                })
    return records


def _record_score(record: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        record["count"],
        record["span"],
        -record["line"],
        1 if record["side"] == "first" else 0,
    )


def bridge_longest(original: Grid, intermediate: Grid) -> Grid:
    """Bridge the input-dependent aligned seed group selected after projection."""
    facts = _facts(original)
    records = _records(original, intermediate)
    output = copy.deepcopy(intermediate)
    if not records:
        return output
    winner = max(records, key=_record_score)
    for lane in range(winner["lo"], winner["hi"] + 1):
        row, col = _cell_from_axis_lane(facts, winner["line"], lane)
        output[row][col] = winner["color"]
    return output


def solve(grid: Grid, settings: object) -> Grid:
    setting = normalize_settings(settings)["finish_rule"]
    projected = project(grid)
    return projected if setting == "project_only" else bridge_longest(grid, projected)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:bridge-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _narrow_positions(count: int, lane_extent: int, rng: random.Random) -> list[int]:
    width = 2 * count - 1
    if width > lane_extent - 2:
        raise ValueError("lane is too narrow for the winner group")
    maximum_start = lane_extent - width
    starts = list(range(1, maximum_start + 1)) or [0]
    start = rng.choice(starts)
    return [start + 2 * index for index in range(count)]


def _wide_positions(count: int, lane_extent: int) -> list[int]:
    if count < 2:
        raise ValueError("wide groups need at least two cells")
    positions = [round(index * (lane_extent - 1) / (count - 1)) for index in range(count)]
    if len(set(positions)) != count:
        raise ValueError("lane is too narrow for a wide distractor")
    return positions


def _put_marker(grid: Grid, facts: dict[str, Any], side: str, projected_axis: int, lane: int) -> None:
    marker_axis = projected_axis + 1 if side == "first" else projected_axis - 1
    row, col = _cell_from_axis_lane(facts, marker_axis, lane)
    dest_row, dest_col = _cell_from_axis_lane(facts, projected_axis, lane)
    if not (0 <= row < facts["height"] and 0 <= col < facts["width"]):
        raise RuntimeError("constructed marker leaves the grid")
    if grid[row][col] != 0 or grid[dest_row][dest_col] != 0:
        raise RuntimeError("constructive marker or destination collision")
    grid[row][col] = 1


def _profile_for(split: str, index: int) -> Profile:
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "index")
    return profiles[index]


def sample_input(seed: int, split: str, index: int) -> Grid:
    _integer(seed, 0, 2**63 - 1, "seed")
    profile = _profile_for(split, index)
    rng = _rng(seed, split, index)
    colors = rng.sample(range(2, 10), 2)
    grid = [[0 for _ in range(profile.width)] for _ in range(profile.height)]
    if profile.orientation == "horizontal":
        grid[0] = [colors[0]] * profile.width
        grid[-1] = [colors[1]] * profile.width
    else:
        for row in grid:
            row[0], row[-1] = colors
    facts = _facts(grid)

    winner_lanes = _narrow_positions(profile.winner_count, facts["lane_extent"], rng)
    distractor_lanes = _wide_positions(profile.distractor_count, facts["lane_extent"])
    extra_lanes = [1, 3]
    opposite = "second" if profile.winner_side == "first" else "first"

    def projected_axis(side: str, distance: int) -> int:
        return distance if side == "first" else facts["extent"] - 1 - distance

    # The winner has more seeds but a narrower span and lies farther from its
    # border. The wide distractor and two-seed near-border group defeat simple
    # widest, nearest, first-record and bridge-everything shortcuts.
    for lane in winner_lanes:
        _put_marker(grid, facts, profile.winner_side, projected_axis(profile.winner_side, 4), lane)
    for lane in distractor_lanes:
        _put_marker(grid, facts, opposite, projected_axis(opposite, 3), lane)
    for lane in extra_lanes:
        _put_marker(grid, facts, "first", projected_axis("first", 1), lane)

    if profile.tie_marker:
        if facts["extent"] % 2 != 1:
            raise RuntimeError("tie profile needs an odd projection extent")
        tie_axis = facts["extent"] // 2
        occupied = {lane for marker in _facts(grid)["markers"]
                    for axis, lane in [_marker_axis_lane(facts, marker)] if axis == tie_axis}
        lane_options = [lane for lane in range(facts["lane_extent"]) if lane not in occupied]
        lane = rng.choice(lane_options)
        row, col = _cell_from_axis_lane(facts, tie_axis, lane)
        dest_row, dest_col = _cell_from_axis_lane(facts, tie_axis - 1, lane)
        if grid[row][col] != 0 or grid[dest_row][dest_col] != 0:
            raise RuntimeError("tie-marker construction collided")
        grid[row][col] = 1

    facts = _facts(grid)
    projected = project(grid)
    records = _records(grid, projected)
    if len(records) < 3:
        raise RuntimeError("constructive scene must expose at least three aligned groups")
    winner = max(records, key=_record_score)
    expected_side = profile.winner_side
    if winner["side"] != expected_side or winner["count"] != profile.winner_count:
        raise RuntimeError("constructive winner differs from the profile")
    if winner["count"] <= max(record["count"] for record in records if record is not winner):
        raise RuntimeError("constructive winner must have a unique seed count")
    if winner["span"] >= max(record["span"] for record in records if record is not winner):
        raise RuntimeError("constructive winner must not also be the widest span")
    if bridge_longest(grid, projected) == projected:
        raise RuntimeError("constructive bridge must add at least one cell")
    return grid


def analyze(grid: Grid) -> dict[str, Any]:
    facts = _facts(grid)
    projected = project(grid)
    records = _records(grid, projected)
    if not records:
        raise ValueError("input has no aligned projection-seed group")
    winner = max(records, key=_record_score)
    bridged = bridge_longest(grid, projected)
    added = sum(
        projected[row][col] != bridged[row][col]
        for row in range(facts["height"])
        for col in range(facts["width"])
    )
    marker_lanes = sorted({_marker_axis_lane(facts, marker)[1] for marker in facts["markers"]})
    boundaries = [lane for lane in (0, facts["lane_extent"] - 1) if lane in marker_lanes]
    return {
        "height": facts["height"],
        "width": facts["width"],
        "orientation": facts["orientation"],
        "marker_count": len(facts["markers"]),
        "records": copy.deepcopy(records),
        "winner": copy.deepcopy(winner),
        "bridge_added_cells": added,
        "orthogonal_boundary_markers": boundaries,
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    normalized = normalize_settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    test_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    return {
        "train": [{"input": grid, "output": solve(grid, normalized)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, normalized)} for grid in test_inputs],
        "program_solution": program(normalized),
    }


def public_turn(episode: object, query_index: int = 0) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs train pairs and the selected query")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }
