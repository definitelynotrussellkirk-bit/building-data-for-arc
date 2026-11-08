"""Matched-input bbox-fill / short-side-component relay family.

The exact canonical program crops the bounding box of every nonzero cell and
returns a solid color-8 rectangle.  The alternate program first derives that
outer box, uses its shorter side length as an input-dependent selector, then
crops the unique interior same-color component with that many cells and renders
its exact normalized shape in color 8.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "ebe355c22d70"
PARAMETERS = {"mode": ["outer_fill", "short_side_relay"]}
DEFAULT = {"mode": "outer_fill"}
SETTINGS = [{"mode": value} for value in PARAMETERS["mode"]]
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_PROGRAM_PATHS = {
    "outer_fill": HERE / "canonical.rkt",
    "short_side_relay": HERE / "short-side-relay.rkt",
}
LONG_SIDE_COUNTERFACTUAL = (HERE / "long-side-counterfactual.rkt").read_text()

# grid_h, grid_w, outer_h, outer_w, selected-shape salt
_DEMO_PROFILES = (
    (12, 16, 8, 12, 0),
    (16, 13, 13, 9, 1),
    (15, 19, 10, 15, 2),
    (20, 16, 16, 11, 3),
    (19, 23, 12, 18, 4),
    (24, 20, 19, 14, 5),
)
_QUERY_PROFILES = (
    (13, 17, 9, 13, 6),
    (18, 16, 14, 10, 7),
    (24, 27, 18, 22, 8),
    (30, 30, 28, 27, 9),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = value["mode"]
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be 'outer_fill' or 'short_side_relay'")
    return {"mode": mode}


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(_digest([TASK_ID, "bbox-relay-v1", seed, domain, index]), 16))


def program(settings: object) -> str:
    chosen = _settings(settings)
    return _PROGRAM_PATHS[chosen["mode"]].read_text()


def _bbox_nonzero(grid: list[list[int]]) -> tuple[int, int, int, int]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("scene must contain nonzero cells")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _component_records(grid: list[list[int]]) -> list[dict]:
    """Same-color four-neighbor objects in row-major discovery order."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            records.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return records


def _normalized_mask(cells: list[tuple[int, int]], *, solid: bool = False) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    occupied = set(cells)
    return [
        [8 if solid or (r, c) in occupied else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _outer_dimensions(grid: list[list[int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox_nonzero(grid)
    return r1 - r0 + 1, c1 - c0 + 1


def _nonblue_components(grid: list[list[int]]) -> list[dict]:
    return [record for record in _component_records(grid) if record["color"] != 1]


def _component_by_size(grid: list[list[int]], size: int) -> dict:
    matches = [record for record in _nonblue_components(grid) if record["size"] == size]
    if len(matches) != 1:
        raise ValueError(f"expected one nonblue component of size {size}, got {len(matches)}")
    return matches[0]


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Independent Python claim generator; protected Racket remains authority."""
    _grid(grid)
    mode = _settings(settings)["mode"]
    height, width = _outer_dimensions(grid)
    if mode == "outer_fill":
        return [[8] * width for _ in range(height)]
    selected = _component_by_size(grid, min(height, width))
    return _normalized_mask(selected["cells"])


def _transform_target_size(grid: list[list[int]], target: int) -> list[list[int]]:
    return _normalized_mask(_component_by_size(grid, target)["cells"])


def _long_side_component(grid: list[list[int]]) -> list[list[int]]:
    height, width = _outer_dimensions(grid)
    return _transform_target_size(grid, max(height, width))


def _height_component(grid: list[list[int]]) -> list[list[int]]:
    height, _ = _outer_dimensions(grid)
    return _transform_target_size(grid, height)


def _width_component(grid: list[list[int]]) -> list[list[int]]:
    _, width = _outer_dimensions(grid)
    return _transform_target_size(grid, width)


def _smallest_component(grid: list[list[int]]) -> list[list[int]]:
    selected = min(_nonblue_components(grid), key=lambda record: (record["size"], record["bbox"]))
    return _normalized_mask(selected["cells"])


def _largest_component(grid: list[list[int]]) -> list[list[int]]:
    selected = max(_nonblue_components(grid), key=lambda record: (record["size"], tuple(-v for v in record["bbox"])))
    return _normalized_mask(selected["cells"])


def _first_component(grid: list[list[int]]) -> list[list[int]]:
    return _normalized_mask(_nonblue_components(grid)[0]["cells"])


def _last_component(grid: list[list[int]]) -> list[list[int]]:
    return _normalized_mask(_nonblue_components(grid)[-1]["cells"])


def _fixed_color_two(grid: list[list[int]]) -> list[list[int]]:
    matches = [record for record in _nonblue_components(grid) if record["color"] == 2]
    if len(matches) != 1:
        raise ValueError("scene must contain one color-2 component")
    return _normalized_mask(matches[0]["cells"])


def _solid_selected_bbox(grid: list[list[int]]) -> list[list[int]]:
    height, width = _outer_dimensions(grid)
    selected = _component_by_size(grid, min(height, width))
    return _normalized_mask(selected["cells"], solid=True)


RIVAL_TRANSFORMS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "long_side_component": _long_side_component,
    "height_component": _height_component,
    "width_component": _width_component,
    "smallest_component": _smallest_component,
    "largest_component": _largest_component,
    "first_component": _first_component,
    "last_component": _last_component,
    "fixed_color_2": _fixed_color_two,
    "solid_selected_bbox": _solid_selected_bbox,
}


def _snake(size: int, width: int) -> list[tuple[int, int]]:
    width = max(2, min(width, size - 1))
    cells = []
    for index in range(size):
        r, offset = divmod(index, width)
        c = offset if r % 2 == 0 else width - 1 - offset
        cells.append((r, c))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def _selected_shape(size: int, salt: int) -> list[tuple[int, int]]:
    width = min(size - 1, max(3, math.isqrt(size) + 1 + (salt % 2)))
    if size % width == 0 and width < size - 1:
        width += 1
    shape = _snake(size, width)
    rows = {r for r, _ in shape}
    cols = {c for _, c in shape}
    if len(rows) < 2 or len(cols) < 2 or len(shape) == len(rows) * len(cols):
        raise RuntimeError("selected relay shape must be a non-solid two-dimensional polyomino")
    return shape


def _compact_shape(size: int, salt: int) -> list[tuple[int, int]]:
    width = min(size - 1, 2 + (salt % 4))
    return _snake(size, width)


def _place_compact(
    size: int,
    salt: int,
    bounds: tuple[int, int, int, int],
    occupied: set[tuple[int, int]],
    preference: str,
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Place a connected distractor, retrying lawful snake aspect ratios.

    The preferred compact shape is stable for existing seeds.  A crowded scene
    can leave no translation for that one aspect ratio, so fall back through
    the remaining connected snake shapes before declaring the profile
    impossible.
    """
    preferred = _compact_shape(size, salt)
    try:
        return _place(preferred, bounds, occupied, preference, rng)
    except RuntimeError as first_error:
        original_width = _shape_extent(preferred)[1]
        widths = sorted(
            range(2, size),
            key=lambda width: (
                abs(math.ceil(size / width) - width),
                abs(width - original_width),
                width,
            ),
        )
        for width in widths:
            alternative = _snake(size, width)
            if alternative == preferred:
                continue
            try:
                return _place(alternative, bounds, occupied, preference, rng)
            except RuntimeError:
                continue
        raise first_error


def _shape_extent(shape: list[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _place(
    shape: list[tuple[int, int]],
    bounds: tuple[int, int, int, int],
    occupied: set[tuple[int, int]],
    preference: str,
    rng: random.Random,
) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = bounds
    sh, sw = _shape_extent(shape)
    candidates = [
        (r, c)
        for r in range(r0, r1 - sh + 2)
        for c in range(c0, c1 - sw + 2)
        if all((r + dr, c + dc) not in occupied for dr, dc in shape)
    ]
    if not candidates:
        raise RuntimeError(f"cannot place {sh}x{sw} shape inside {bounds}")
    center_r = (r0 + r1 - sh + 1) / 2
    center_c = (c0 + c1 - sw + 1) / 2

    def score(rc: tuple[int, int]) -> tuple[float, float]:
        r, c = rc
        jitter = rng.random() * 1e-6
        if preference == "tl":
            base = r + c
        elif preference == "tr":
            base = r + (c1 - sw + 1 - c)
        elif preference == "bl":
            base = (r1 - sh + 1 - r) + c
        elif preference == "br":
            base = (r1 - sh + 1 - r) + (c1 - sw + 1 - c)
        else:
            base = abs(r - center_r) + abs(c - center_c)
        return base, jitter

    top, left = min(candidates, key=score)
    return [(top + dr, left + dc) for dr, dc in shape]


def _component_sizes(short_side: int, long_side: int) -> list[int]:
    candidates = [
        short_side,
        long_side,
        3,
        short_side - 2,
        short_side + 2,
        long_side + 2,
        short_side + 4,
        long_side - 2,
    ]
    result: list[int] = []
    for value in candidates:
        if value >= 2 and value not in result:
            result.append(value)
        if len(result) == 6:
            break
    if len(result) != 6 or result[0] != short_side or result[1] != long_side:
        raise RuntimeError("profile does not yield six distinct component sizes")
    return result


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain == "demo":
        profile = _DEMO_PROFILES[index]
    elif domain == "query":
        profile = _QUERY_PROFILES[index]
    else:
        raise ValueError(domain)
    grid_h, grid_w, outer_h, outer_w, salt = profile
    rng = _rng(seed, domain, index)
    max_r0, max_c0 = grid_h - outer_h, grid_w - outer_w
    if domain == "query" and index == 3:
        r0 = rng.choice((0, max_r0))
        c0 = rng.choice((0, max_c0))
    else:
        r0 = rng.randint(0, max_r0)
        c0 = rng.randint(0, max_c0)
    r1, c1 = r0 + outer_h - 1, c0 + outer_w - 1
    grid = [[0] * grid_w for _ in range(grid_h)]
    if (seed + index + (0 if domain == "demo" else 1)) % 2:
        corners = ((r0, c1), (r1, c0))
    else:
        corners = ((r0, c0), (r1, c1))
    occupied = set(corners)
    for r, c in corners:
        grid[r][c] = 1

    short_side, long_side = min(outer_h, outer_w), max(outer_h, outer_w)
    sizes = _component_sizes(short_side, long_side)
    selected_color = 2 + ((seed + index + (3 if domain == "query" else 0)) % 8)
    colors = [selected_color] + [color for color in range(2, 10) if color != selected_color]
    colors = colors[: len(sizes)]

    # Put the long-side distractor across the interior near the top/left.  It is
    # a plausible wrong relay and also guarantees an object before the selected
    # component in row-major discovery order.
    if outer_w > outer_h:
        long_cells = [(r0 + 1, c) for c in range(c0, c1 + 1)]
    else:
        long_cells = [(r, c0 + 1) for r in range(r0, r1 + 1)]
    if occupied.intersection(long_cells):
        raise RuntimeError("long-side distractor overlaps a blue corner")
    occupied.update(long_cells)
    for r, c in long_cells:
        grid[r][c] = colors[1]

    selected = _place(
        _selected_shape(short_side, salt),
        (r0, c0, r1, c1),
        occupied,
        "center",
        rng,
    )
    occupied.update(selected)
    for r, c in selected:
        grid[r][c] = colors[0]

    preferences = ("tl", "tr", "bl", "br")
    for offset, (size, color, preference) in enumerate(
        zip(sizes[2:], colors[2:], preferences), start=2
    ):
        cells = _place_compact(
            size,
            salt + offset,
            (r0, c0, r1, c1),
            occupied,
            preference,
            rng,
        )
        occupied.update(cells)
        for r, c in cells:
            grid[r][c] = color

    _validate_scene(grid, outer_h, outer_w, short_side, long_side)
    return grid


def _validate_scene(
    grid: list[list[int]], outer_h: int, outer_w: int, short_side: int, long_side: int
) -> None:
    height, width = _outer_dimensions(grid)
    if (height, width) != (outer_h, outer_w):
        raise RuntimeError(f"outer bbox drifted to {(height, width)}")
    nonblue = _nonblue_components(grid)
    sizes = [record["size"] for record in nonblue]
    if sizes.count(short_side) != 1 or sizes.count(long_side) != 1:
        raise RuntimeError("relay sizes are not unique")
    selected = _component_by_size(grid, short_side)
    mask = _normalized_mask(selected["cells"])
    if len(mask) < 2 or len(mask[0]) < 2 or all(value == 8 for row in mask for value in row):
        raise RuntimeError("selected component lost non-solid two-dimensional structure")
    if nonblue[0]["size"] == short_side or nonblue[-1]["size"] == short_side:
        raise RuntimeError("selected component must be neither first nor last")
    if not any(record["color"] == 2 for record in nonblue):
        raise RuntimeError("fixed-color rival requires a color-2 component")


def validate_request(seed: int, settings: object, demos: int, queries: int) -> dict[str, str]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    if type(queries) is not int or queries != QUERY_COUNT:
        raise ValueError("queries must be the exact integer 4")
    return _settings(settings)


def certify(
    episode: dict,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    if len(test) != QUERY_COUNT:
        raise ValueError("episode must contain exactly four queries")
    pairs = train + test
    if len({_digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    for pair in pairs:
        _grid(pair.get("input"))
        _grid(pair.get("output"))

    apply = execute or (
        lambda source, grid: transform(
            grid, next(setting for setting in SETTINGS if program(setting) == source)
        )
    )
    setting_records = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        setting_records.append(
            {
                "settings": dict(setting),
                "disagreeing_demo_indices": [
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, train))
                    if prediction != pair["output"]
                ],
            }
        )
    survivors = [
        record["settings"]
        for record in setting_records
        if not record["disagreeing_demo_indices"]
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected mode: {survivors}")

    extra_refutations = {}
    for name, rival in RIVAL_TRANSFORMS.items():
        disagreements = [
            index
            for index, pair in enumerate(train)
            if rival(pair["input"]) != pair["output"]
        ]
        if not disagreements:
            raise ValueError(f"extra rival {name!r} survives every demonstration")
        extra_refutations[name] = disagreements

    query_records = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        query_records.append(
            {
                "input_sha256": _digest(pair["input"]),
                "output_sha256": _digest(pair["output"]),
                "survivors": survivors,
                "unanimous": True,
            }
        )
    return {
        "scope": "two declared modes plus nine finite component-selection/rendering shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": setting_records,
        "extra_refutations": extra_refutations,
        "queries": query_records,
        "limits": "Finite authored rival set only; not a uniqueness proof.",
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    if settings is None:
        _integer(seed, 0, 2**63 - 1, "seed")
        settings = _rng(seed, "settings").choice(SETTINGS)
    chosen = validate_request(seed, settings, demos, queries)
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(QUERY_COUNT):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode = {
        "schema": "ebe355c22d70-bbox-relay-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    _integer(index, 0, QUERY_COUNT - 1, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    """One protected Racket bridge for bounded authoring evidence."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "short-side-relay.rkt",
        HERE / "long-side-counterfactual.rkt",
        HERE.parents[1] / "generator.py",
        REPO / "shared/data/canonical/puzzles.jsonl",
        REPO / "shared/runtime/reviewer_support.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def write_batch(episodes: list[dict], destination: Path, *, metadata: dict | None = None) -> dict:
    """Write first-turn public bytes; keep settings, answers and future queries private."""
    destination = Path(destination)
    rows = [
        (
            public_challenge_id(public_turn(episode, 0)),
            public_challenge_bytes(public_turn(episode, 0)),
            episode,
        )
        for episode in episodes
    ]
    rows.sort(key=lambda row: row[0])
    if not rows or len({identifier for identifier, _, _ in rows}) != len(rows):
        raise ValueError("batch must be nonempty with distinct first-turn challenges")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    public.mkdir()
    for identifier, body, _ in rows:
        (public / f"{identifier}.json").write_bytes(body)
    (destination / "public.jsonl").write_bytes(b"".join(body for _, body, _ in rows))
    private = {
        "schema": "ebe355c22d70-bbox-relay-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": [
            dict(
                episode,
                public_id=identifier,
                turn_ids=[
                    public_challenge_id(public_turn(episode, index))
                    for index in range(QUERY_COUNT)
                ],
            )
            for identifier, _, episode in rows
        ],
    }
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    )
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {
        "schema": "ebe355c22d70-bbox-relay-export-v1",
        "public_projection": "first query only; later turns controller-private",
        "writer_executes_racket": False,
        "public_ids": [identifier for identifier, _, _ in rows],
        "files": {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--mode", choices=PARAMETERS["mode"], default="outer_fill")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"mode": args.mode}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {
            "payload_argv": sys.argv,
            "runtime_identity": execute.identity,
            "finite_scope": "two modes plus named shortcuts; long-side counterfactual separately executable",
            "qualification": "not_run",
            "acceptance": "not_requested",
            "training_admitted": False,
        }
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "public_ids": manifest["public_ids"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
