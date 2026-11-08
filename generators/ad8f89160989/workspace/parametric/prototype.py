#!/usr/bin/env python3
"""Episode-fixed union versus overlap-highlight halo family.

Step A computes an integer coverage map: for every background cell, how many
orthogonally adjacent source seeds vote to paint it. Step B consumes those
counts. The canonical ``union`` setting maps every positive count to cyan (8).
The alternative keeps count-one cells cyan and marks count-two-or-more cells
blue (1). Inputs are generated independently of the hidden setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, public_challenge_id

TASK_ID = "ad8f89160989"
PROTOTYPE_VERSION = "1.1.0"
MODES = ("union", "overlap_highlight")
DEFAULT_SETTINGS = {"coverage_mode": "union"}
SETTINGS = tuple({"coverage_mode": mode} for mode in MODES)
SEED_COLORS = (2, 3, 4, 6, 7, 9)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = (*DIRS4, (-1, -1), (-1, 1), (1, -1), (1, 1))
HERE = Path(__file__).resolve().parent

DEMO_CORE = (
    {
        "name": "pair_controls",
        "dims": (10, 12),
        "motifs": (
            (2, "top_left", "opposite", "same"),
            (2, "bottom_right", "perpendicular", "different"),
        ),
        "isolates": 3,
        "boundary_isolate": True,
    },
    {"name": "triple", "dims": (10, 11), "motifs": ((3, "top_edge"),), "isolates": 3, "boundary_isolate": False},
    {"name": "quad", "dims": (11, 12), "motifs": ((4, "center"),), "isolates": 3, "boundary_isolate": True},
)
DEMO_EXTRA = (
    {"name": "pair_triple", "dims": (12, 13), "motifs": ((2, "top_left"), (3, "bottom_right")), "isolates": 2, "boundary_isolate": False},
    {"name": "quad_pair", "dims": (13, 12), "motifs": ((4, "top_right"), (2, "bottom_left")), "isolates": 3, "boundary_isolate": True},
    {"name": "edge_mix", "dims": (14, 14), "motifs": ((3, "left_edge"), (4, "bottom_right")), "isolates": 4, "boundary_isolate": False},
)
QUERY_CORE = (
    {"name": "transfer", "dims": (14, 15), "motifs": ((2, "top_left"), (3, "bottom_right")), "isolates": 4, "boundary_isolate": True},
    {"name": "boundary", "dims": (16, 14), "motifs": ((4, "top_edge"), (2, "bottom_edge")), "isolates": 4, "boundary_isolate": False},
    {"name": "dense", "dims": (22, 20), "motifs": ((2, "top_left"), (3, "top_right"), (4, "bottom_left")), "isolates": 6, "boundary_isolate": True},
    {"name": "large", "dims": (30, 30), "motifs": ((2, "top_left"), (3, "top_right"), (4, "bottom_left"), (4, "bottom_right")), "isolates": 5, "boundary_isolate": True},
)
QUERY_EXTRA = (
    {"name": "wide", "dims": (18, 30), "motifs": ((2, "left_edge"), (3, "top_right"), (4, "bottom_right")), "isolates": 5, "boundary_isolate": False},
    {"name": "tall", "dims": (30, 18), "motifs": ((4, "top_edge"), (2, "bottom_left"), (3, "bottom_right")), "isolates": 5, "boundary_isolate": True},
    {"name": "square", "dims": (28, 28), "motifs": ((3, "center"), (2, "top_left"), (4, "bottom_right")), "isolates": 7, "boundary_isolate": False},
    {"name": "four_pairs", "dims": (24, 24), "motifs": ((2, "top_left"), (2, "top_right"), (2, "bottom_left"), (2, "bottom_right")), "isolates": 6, "boundary_isolate": True},
)


def _root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _canonical_program(*, root: Path | str | None = None) -> str:
    programs: list[str] = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for raw in stream:
            if raw.strip():
                row = json.loads(raw)
                if row.get("task_id") == TASK_ID and type(row.get("program_solution")) is str:
                    programs.append(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    return programs[0]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"coverage_mode"}:
        raise ValueError("settings must contain exactly coverage_mode")
    mode = value["coverage_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"coverage_mode must be one of {MODES}, got {mode!r}")
    return {"coverage_mode": mode}


def program(settings: Any, *, root: Path | str | None = None) -> str:
    chosen = _settings(settings)
    if chosen == DEFAULT_SETTINGS:
        return _canonical_program(root=root)
    return (HERE / "overlap_highlight.rkt").read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 5 <= len(value) <= 30
        or type(value[0]) is not list
        or not 5 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 5..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    seeds = [cell for row in value for cell in row if cell != 0]
    if not seeds:
        raise ValueError("grid must contain at least one source seed")
    if len(seeds) > 24:
        raise ValueError("grid may contain at most 24 source seeds")
    if any(cell not in SEED_COLORS for cell in seeds):
        raise ValueError(f"input seeds must use only {SEED_COLORS}; colors 1, 5, and 8 are reserved")
    return deepcopy(value)


def coverage_counts(value: Any) -> list[list[int]]:
    source = _grid(value)
    height, width = len(source), len(source[0])
    counts = [[0 for _ in range(width)] for _ in range(height)]
    seeds = [(r, c) for r, row in enumerate(source) for c, cell in enumerate(row) if cell != 0]
    for row, column in seeds:
        for dr, dc in DIRS4:
            rr, cc = row + dr, column + dc
            if 0 <= rr < height and 0 <= cc < width and source[rr][cc] == 0:
                counts[rr][cc] += 1
    return counts


def coverage_histogram(value: Any) -> dict[str, int]:
    counts = coverage_counts(value)
    result: dict[str, int] = {}
    for row in counts:
        for count in row:
            if count:
                key = str(count)
                result[key] = result.get(key, 0) + 1
    return result


def _render(source: list[list[int]], counts: list[list[int]], mode: str) -> list[list[int]]:
    output = deepcopy(source)
    for row in range(len(source)):
        for column in range(len(source[0])):
            if source[row][column] != 0:
                continue
            count = counts[row][column]
            if count == 0:
                output[row][column] = 0
            elif mode == "union" or count == 1:
                output[row][column] = 8
            else:
                output[row][column] = 1
    return output


def apply_python(value: Any, settings: Any) -> list[list[int]]:
    source = _grid(value)
    mode = _settings(settings)["coverage_mode"]
    return _render(source, coverage_counts(source), mode)


def apply_binary_intermediate(value: Any) -> list[list[int]]:
    """Counterfactual: clip Step A's counts to booleans before Step B."""
    source = _grid(value)
    binary = [[1 if count else 0 for count in row] for row in coverage_counts(source)]
    return _render(source, binary, "overlap_highlight")


def _rng(seed: int, split: str, token: str) -> random.Random:
    payload = f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{split}|{token}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _zone_candidates(height: int, width: int, zone: str) -> list[tuple[int, int]]:
    middle_row, middle_column = height // 2, width // 2
    if zone == "center":
        return [(middle_row, middle_column)]
    elif zone == "top_left":
        rows = range(2, max(3, height // 2))
        columns = range(2, max(3, width // 2))
    elif zone == "top_right":
        rows = range(2, max(3, height // 2))
        columns = range(min(width - 3, width // 2 + 1), width - 2)
    elif zone == "bottom_left":
        rows = range(min(height - 3, height // 2 + 1), height - 2)
        columns = range(2, max(3, width // 2))
    elif zone == "bottom_right":
        rows = range(min(height - 3, height // 2 + 1), height - 2)
        columns = range(min(width - 3, width // 2 + 1), width - 2)
    elif zone == "top_edge":
        return [(1, c) for c in range(2, width - 2)]
    elif zone == "bottom_edge":
        return [(height - 2, c) for c in range(2, width - 2)]
    elif zone == "left_edge":
        return [(r, 1) for r in range(2, height - 2)]
    elif zone == "right_edge":
        return [(r, width - 2) for r in range(2, height - 2)]
    else:
        raise ValueError(f"unknown scene zone {zone!r}")
    return [(r, c) for r in rows for c in columns]


def _pick_anchor(
    rng: random.Random,
    height: int,
    width: int,
    zone: str,
    reserved: set[tuple[int, int]],
    anchors: list[tuple[int, int]],
) -> tuple[int, int]:
    candidates = _zone_candidates(height, width, zone)
    rng.shuffle(candidates)
    for row, column in candidates:
        footprint = {(row, column), *((row + dr, column + dc) for dr, dc in DIRS4)}
        if not footprint.isdisjoint(reserved):
            continue
        if any(abs(row - rr) + abs(column - cc) < 6 for rr, cc in anchors):
            continue
        return row, column
    raise ValueError(f"no anchor available for zone {zone!r} in {height}x{width}")


def _motif_fields(value: Any) -> tuple[int, str, str, str]:
    if type(value) not in (tuple, list) or len(value) not in (2, 4):
        raise ValueError("motif must be (coverage, zone) or (coverage, zone, orientation, colors)")
    coverage, zone = value[:2]
    orientation, colors = ("random", "random") if len(value) == 2 else value[2:]
    if type(coverage) is not int or coverage not in (2, 3, 4):
        raise ValueError("motif coverage must be 2, 3, or 4")
    if type(zone) is not str:
        raise ValueError("motif zone must be a string")
    if orientation not in ("random", "opposite", "perpendicular"):
        raise ValueError(f"unknown motif orientation {orientation!r}")
    if orientation != "random" and coverage != 2:
        raise ValueError("controlled orientation is supported only for coverage-two motifs")
    if colors not in ("random", "same", "different"):
        raise ValueError(f"unknown motif color policy {colors!r}")
    if colors == "different" and coverage > len(SEED_COLORS):
        raise ValueError("not enough distinct seed colors for motif")
    return coverage, zone, orientation, colors


def _motif_directions(rng: random.Random, coverage: int, orientation: str) -> list[tuple[int, int]]:
    if orientation == "opposite":
        options = [((-1, 0), (1, 0)), ((0, -1), (0, 1))]
        return list(options[rng.randrange(len(options))])
    if orientation == "perpendicular":
        options = [
            ((-1, 0), (0, -1)),
            ((-1, 0), (0, 1)),
            ((1, 0), (0, -1)),
            ((1, 0), (0, 1)),
        ]
        return list(options[rng.randrange(len(options))])
    directions = list(DIRS4)
    rng.shuffle(directions)
    return directions[:coverage]


def _motif_colors(rng: random.Random, count: int, policy: str) -> list[int]:
    if policy == "same":
        color = SEED_COLORS[rng.randrange(len(SEED_COLORS))]
        return [color] * count
    if policy == "different":
        return rng.sample(list(SEED_COLORS), count)
    return [SEED_COLORS[rng.randrange(len(SEED_COLORS))] for _ in range(count)]


def _scene(seed: int, split: str, index: int, spec: dict[str, Any]) -> list[list[int]]:
    height, width = spec["dims"]
    rng = _rng(seed, split, f"{index}:{spec['name']}")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    anchors: list[tuple[int, int]] = []
    reserved: set[tuple[int, int]] = set()
    motif_groups: list[tuple[list[tuple[int, int]], str]] = []
    seed_positions: list[tuple[int, int]] = []
    motif_fields = [_motif_fields(item) for item in spec["motifs"]]

    for coverage, zone, orientation, color_policy in motif_fields:
        row, column = _pick_anchor(rng, height, width, zone, reserved, anchors)
        anchors.append((row, column))
        full_footprint = {(row, column), *((row + dr, column + dc) for dr, dc in DIRS4)}
        reserved.update(full_footprint)
        chosen = _motif_directions(rng, coverage, orientation)
        positions = [(row + dr, column + dc) for dr, dc in chosen]
        motif_groups.append((positions, color_policy))
        seed_positions.extend(positions)

    isolate_candidates = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(isolate_candidates)
    isolate_count = int(spec["isolates"])
    if spec.get("boundary_isolate"):
        boundary = [
            p for p in isolate_candidates
            if p[0] in (0, height - 1) or p[1] in (0, width - 1)
        ]
        boundary_set = set(boundary)
        interior = [p for p in isolate_candidates if p not in boundary_set]
        isolate_candidates = boundary + interior
    isolate_positions: list[tuple[int, int]] = []
    expected_motif_seeds = sum(item[0] for item in motif_fields)
    for row, column in isolate_candidates:
        if len(isolate_positions) >= isolate_count:
            break
        if (row, column) in reserved or (row, column) in seed_positions:
            continue
        if any(abs(row - rr) + abs(column - cc) < 3 for rr, cc in [*seed_positions, *isolate_positions]):
            continue
        if any(abs(row - rr) + abs(column - cc) <= 1 for rr, cc in anchors):
            continue
        isolate_positions.append((row, column))
    expected = expected_motif_seeds + isolate_count
    if len(seed_positions) + len(isolate_positions) != expected:
        raise ValueError(
            f"could not place all seeds for scene {spec['name']}: "
            f"{len(seed_positions) + len(isolate_positions)} != {expected}"
        )

    for positions, policy in motif_groups:
        for (row, column), color in zip(positions, _motif_colors(rng, len(positions), policy)):
            grid[row][column] = color
    isolate_palette = list(SEED_COLORS)
    rng.shuffle(isolate_palette)
    isolate_colors = [
        isolate_palette[i] if i < min(3, len(isolate_positions))
        else SEED_COLORS[rng.randrange(len(SEED_COLORS))]
        for i in range(len(isolate_positions))
    ]
    for (row, column), color in zip(isolate_positions, isolate_colors):
        grid[row][column] = color

    histogram = coverage_histogram(grid)
    for coverage, _, _, _ in motif_fields:
        if histogram.get(str(coverage), 0) < 1:
            raise AssertionError(f"scene {spec['name']} lost required coverage {coverage}: {histogram}")
    return grid


def _role_order(seed: int, split: str, core: tuple[dict, ...], extra: tuple[dict, ...]) -> list[dict]:
    first = list(core)
    tail = list(extra)
    _rng(seed, split, "core-order").shuffle(first)
    _rng(seed, split, "extra-order").shuffle(tail)
    return [*first, *tail]


def generate_episode(seed: Any, settings: Any, *, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 3, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)
    demo_specs = _role_order(seed, "demo", DEMO_CORE, DEMO_EXTRA)
    query_specs = _role_order(seed, "query", QUERY_CORE, QUERY_EXTRA)

    train = []
    for index, spec in enumerate(demo_specs[:demos]):
        source = _scene(seed, "demo", index, spec)
        train.append({"input": source, "output": apply_python(source, chosen)})
    test = []
    for index, spec in enumerate(query_specs[:queries]):
        source = _scene(seed, "query", index, spec)
        test.append({"input": source, "output": apply_python(source, chosen)})

    episode = {
        "schema": "ad8f89160989-overlap-count-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "settings": deepcopy(chosen),
        "program": program(chosen),
        "train": train,
        "test": test,
    }
    errors = episode_errors(episode)
    if errors:
        raise AssertionError("constructed invalid episode: " + "; ".join(errors))
    return episode


def teaching_survivors(episode: Any) -> list[dict[str, str]]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    return [
        deepcopy(settings)
        for settings in SETTINGS
        if all(apply_python(pair["input"], settings) == pair["output"] for pair in episode["train"])
    ]


def _rival_output(value: Any, hypothesis: str) -> list[list[int]]:
    source = _grid(value)
    counts = coverage_counts(source)
    if hypothesis in MODES:
        return _render(source, counts, hypothesis)
    if hypothesis == "all_halo_blue":
        output = deepcopy(source)
        for r, row in enumerate(counts):
            for c, count in enumerate(row):
                if source[r][c] == 0 and count:
                    output[r][c] = 1
        return output
    if hypothesis == "exactly_two":
        output = deepcopy(source)
        for r, row in enumerate(counts):
            for c, count in enumerate(row):
                if source[r][c] == 0 and count:
                    output[r][c] = 1 if count == 2 else 8
        return output
    if hypothesis == "at_least_three":
        output = deepcopy(source)
        for r, row in enumerate(counts):
            for c, count in enumerate(row):
                if source[r][c] == 0 and count:
                    output[r][c] = 1 if count >= 3 else 8
        return output
    if hypothesis == "diagonal_overlap":
        height, width = len(source), len(source[0])
        diagonal = [[0 for _ in range(width)] for _ in range(height)]
        seeds = [(r, c) for r, row in enumerate(source) for c, cell in enumerate(row) if cell]
        for r, c in seeds:
            for dr, dc in DIRS8[4:]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width and source[rr][cc] == 0:
                    diagonal[rr][cc] += 1
        return _render(source, diagonal, "overlap_highlight")
    if hypothesis in ("opposite_only", "mixed_axis_only", "color_pair_only"):
        output = _render(source, counts, "union")
        height, width = len(source), len(source[0])
        for r, row in enumerate(counts):
            for c, count in enumerate(row):
                if source[r][c] != 0 or count < 2:
                    continue
                neighbors = [
                    (dr, dc, source[r + dr][c + dc])
                    for dr, dc in DIRS4
                    if 0 <= r + dr < height
                    and 0 <= c + dc < width
                    and source[r + dr][c + dc] != 0
                ]
                vectors = {(dr, dc) for dr, dc, _ in neighbors}
                vertical = any(dr != 0 for dr, _, _ in neighbors)
                horizontal = any(dc != 0 for _, dc, _ in neighbors)
                colors = {color for _, _, color in neighbors}
                matches = (
                    hypothesis == "opposite_only"
                    and (vectors == {(-1, 0), (1, 0)} or vectors == {(0, -1), (0, 1)})
                ) or (
                    hypothesis == "mixed_axis_only" and vertical and horizontal
                ) or (
                    hypothesis == "color_pair_only" and len(colors) >= 2
                )
                if matches:
                    output[r][c] = 1
        return output
    if hypothesis == "maximum_only":
        output = _render(source, counts, "union")
        maximum = max(max(row) for row in counts)
        for r, row in enumerate(counts):
            for c, count in enumerate(row):
                if source[r][c] == 0 and count >= 2 and count == maximum:
                    output[r][c] = 1
        return output
    if hypothesis == "fixed_center":
        output = _render(source, counts, "union")
        r, c = len(source) // 2, len(source[0]) // 2
        if source[r][c] == 0 and counts[r][c]:
            output[r][c] = 1
        return output
    raise ValueError(f"unknown semantic hypothesis {hypothesis!r}")


SEMANTIC_HYPOTHESES = (
    *MODES,
    "all_halo_blue",
    "exactly_two",
    "at_least_three",
    "diagonal_overlap",
    "opposite_only",
    "mixed_axis_only",
    "maximum_only",
    "color_pair_only",
    "fixed_center",
)


def semantic_survivors(episode: Any) -> list[str]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    return [
        hypothesis
        for hypothesis in SEMANTIC_HYPOTHESES
        if all(_rival_output(pair["input"], hypothesis) == pair["output"] for pair in episode["train"])
    ]


def episode_errors(episode: Any) -> list[str]:
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    try:
        chosen = _settings(episode.get("settings"))
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    if episode.get("program") != program(chosen):
        errors.append("episode program does not match settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 3 <= len(train) <= 6:
        errors.append("episode needs 3..6 demonstrations")
        train = []
    if type(test) is not list or not 1 <= len(test) <= 8:
        errors.append("episode needs 1..8 queries")
        test = []
    seen: set[str] = set()
    train_valid = bool(train)
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            label = f"{split}[{index}]"
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                errors.append(f"{label} must contain exactly input and output")
                if split == "train":
                    train_valid = False
                continue
            try:
                source = _grid(pair["input"])
                expected = apply_python(source, chosen)
            except ValueError as error:
                errors.append(f"{label} invalid input: {error}")
                if split == "train":
                    train_valid = False
                continue
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                errors.append(f"{label} duplicates an earlier input")
            seen.add(key)
            if pair["output"] != expected:
                errors.append(f"{label} output does not match settings")
    if train_valid:
        if teaching_survivors({"train": train}) != [chosen]:
            errors.append("demonstrations do not identify one declared setting")
        if semantic_survivors({"train": train}) != [chosen["coverage_mode"]]:
            errors.append("demonstrations leave a declared semantic rival")
    return errors


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_id(episode: Any, query_index: Any = 0) -> str:
    return public_challenge_id(public_turn(episode, query_index))


def _control_grid(active: tuple[int, ...], colors: tuple[int, ...]) -> list[list[int]]:
    grid = [[0 for _ in range(9)] for _ in range(9)]
    positions = ((3, 4), (5, 4), (4, 3), (4, 5))
    for index in active:
        r, c = positions[index]
        grid[r][c] = colors[index]
    grid[1][1] = 7
    return grid


def crossed_controls() -> dict[str, bool]:
    pair = _control_grid((0, 1), (2, 3, 4, 6))
    quad = _control_grid((0, 1, 2, 3), (2, 3, 4, 6))
    recolored = _control_grid((0, 1, 2, 3), (9, 7, 6, 4))
    pair_counts, quad_counts, recolored_counts = map(coverage_counts, (pair, quad, recolored))
    overlap_mask = lambda counts: [[count >= 2 for count in row] for row in counts]
    return {
        "fixed_geometry_different_intermediate": pair_counts != quad_counts,
        "fixed_intermediate_different_colors": quad != recolored and quad_counts == recolored_counts,
        "fixed_geometry_outputs_differ": apply_python(pair, SETTINGS[1]) != apply_python(quad, SETTINGS[1]),
        "fixed_intermediate_overlap_mask_equal": overlap_mask(quad_counts) == overlap_mask(recolored_counts),
    }
