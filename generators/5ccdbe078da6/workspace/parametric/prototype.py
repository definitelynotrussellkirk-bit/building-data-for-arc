"""Native parametric family for pair-bbox outlines and occlusion-selected fill.

The default returns the canonical Racket bytes exactly. Both settings share an
input-only sampler. The first two demonstrations are constructive finite-rival
witnesses; later rows add size, boundary and interaction diversity.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import random
import sys

TASK_ID = "5ccdbe078da6"
VERSION = "1.0.0"
FINISHES = ("outline", "fill_most_occluded")
SETTINGS = tuple({"finish": value} for value in FINISHES)
DEFAULT = {"finish": "outline"}
CANONICAL_PROGRAM_SHA256 = "d8da2d7cc24bf7494d55936b92c67f375f8352f916589caa54932d1e9722543a"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]


def _load_local(name, path):
    module_name = f"_5ccd_parametric_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


O = _load_local("oracle", HERE / "oracle.py")


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if (not isinstance(settings, dict) or set(settings) != {"finish"}
            or settings["finish"] not in FINISHES):
        raise ValueError("settings must be exactly {'finish': 'outline|fill_most_occluded'}")
    return settings["finish"]


def _source(name):
    value = (HERE / name).read_text()
    if not value.strip():
        raise ValueError(f"empty Racket source: {name}")
    return value


def canonical_source():
    source = _source("canonical.rkt")
    observed = hashlib.sha256(source.encode()).hexdigest()
    if observed != CANONICAL_PROGRAM_SHA256:
        raise ValueError(f"canonical source drift: {observed}")
    return source


def program(settings):
    finish = _settings(settings)
    return canonical_source() if finish == "outline" else _source("most_occluded.rkt")


def counterfactual_program(name):
    if name != "largest_perimeter":
        raise ValueError("only the source-bound largest_perimeter counterfactual is retained")
    return _source("largest_perimeter_counterfactual.rkt")


def _rng(seed, split, index):
    raw = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _pair_points(box, orientation):
    r0, c0, r1, c1 = box
    if orientation == "down_right":
        return ((r0, c0), (r1, c1))
    if orientation == "down_left":
        return ((r0, c1), (r1, c0))
    if orientation == "horizontal":
        if r0 != r1:
            raise ValueError("horizontal spec must have one row")
        return ((r0, c0), (r0, c1))
    if orientation == "vertical":
        if c0 != c1:
            raise ValueError("vertical spec must have one column")
        return ((r0, c0), (r1, c0))
    raise ValueError(f"unknown orientation: {orientation}")


def _reading_colors(seed, split, index):
    values = sorted(_rng(seed, split + "/colors", index).sample(range(1, 10), 3))
    low, middle, high = values
    return [high, low, middle] if (seed + index + (split == "test")) % 2 == 0 else [middle, high, low]


def _grid_from_specs(height, width, specs, colors):
    ordered = sorted(specs, key=lambda spec: min(_pair_points(*spec)))
    grid = [[0] * width for _ in range(height)]
    used = set()
    for (box, orientation), color in zip(ordered, colors):
        points = _pair_points(box, orientation)
        if any(point in used for point in points):
            raise ValueError("pair endpoints overlap")
        used.update(points)
        for r, c in points:
            if not (0 <= r < height and 0 <= c < width):
                raise ValueError("pair endpoint outside grid")
            grid[r][c] = color
    if O.reading_order(grid) != colors:
        raise AssertionError("constructed colors do not follow requested reading order")
    return grid


DEMO_SPECS = (
    (12, 14, (
        ((1, 1, 5, 11), "down_right"),
        ((4, 11, 8, 13), "down_right"),
        ((7, 8, 10, 12), "down_left"),
    )),
    (13, 15, (
        ((0, 1, 8, 12), "down_left"),
        ((9, 6, 12, 10), "down_right"),
        ((11, 8, 11, 13), "horizontal"),
    )),
)
TRAIN_SIZES = ((12, 14), (13, 15), (10, 17), (18, 11), (22, 24), (26, 20))
QUERY_SIZES = ((14, 16), (19, 13), (24, 27), (30, 30))
STRESS_SPECS = (
    ((0, 0, 24, 27), "down_right"),
    ((3, 5, 29, 25), "down_right"),
    ((7, 2, 26, 29), "down_left"),
)


def _random_specs(seed, split, index, height, width):
    rng = _rng(seed, split + "/geometry", index)
    target = (index + (1 if split == "test" else 0)) % 2
    for _ in range(4096):
        specs = []
        endpoints = set()
        for _pair in range(3):
            for _attempt in range(128):
                r0 = rng.randrange(0, height - 2)
                r1 = rng.randrange(r0 + 2, height)
                c0 = rng.randrange(0, width - 2)
                c1 = rng.randrange(c0 + 2, width)
                orientation = rng.choice(("down_right", "down_left"))
                spec = ((r0, c0, r1, c1), orientation)
                points = set(_pair_points(*spec))
                if not points.intersection(endpoints) and spec not in specs:
                    specs.append(spec)
                    endpoints.update(points)
                    break
            else:
                specs = []
                break
        if len(specs) != 3:
            continue
        grid = _grid_from_specs(height, width, specs, _reading_colors(seed, split, index))
        intermediate = O.occlusion_intermediate(grid)
        selected = intermediate["selected_index"]
        if selected != target:
            continue
        row = intermediate["colors"][selected]
        if row["loss"] <= 0 or len(O.interior_cells(tuple(row["bbox"]))) < 4:
            continue
        if O.solve(grid, "outline") == O.solve(grid, "fill_most_occluded"):
            continue
        if index >= 2:
            points = [p for cells in O.positions(grid).values() for p in cells]
            if (max(r for r, c in points) - min(r for r, c in points) < height // 2
                    or max(c for r, c in points) - min(c for r, c in points) < width // 2):
                continue
        return grid
    raise RuntimeError(f"bounded scene search exhausted for {seed}/{split}/{index}")


@lru_cache(maxsize=256)
def _scene_tuple(seed, split, index):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "train":
        _integer(index, 0, 5, "train index")
        if index < 2:
            height, width, specs = DEMO_SPECS[index]
            grid = _grid_from_specs(height, width, specs, _reading_colors(seed, split, index))
        else:
            height, width = TRAIN_SIZES[index]
            grid = _random_specs(seed, split, index, height, width)
    elif split == "test":
        _integer(index, 0, 3, "test index")
        height, width = QUERY_SIZES[index]
        if index == 3:
            grid = _grid_from_specs(height, width, STRESS_SPECS, _reading_colors(seed, split, index))
        else:
            grid = _random_specs(seed, split, index, height, width)
    else:
        raise ValueError("split must be train or test")
    errors = O.validate_pair_grid(grid)
    if errors:
        raise AssertionError(errors)
    return tuple(tuple(row) for row in grid)


def _scene(seed, split, index):
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [_scene(seed, "train", index) for index in range(demos)],
        "test": [_scene(seed, "test", index) for index in range(queries)],
    }
    keys = [json.dumps(grid, separators=(",", ":"))
            for split in ("train", "test") for grid in result[split]]
    if len(keys) != len(set(keys)):
        raise AssertionError("episode inputs must be distinct")
    return result


def generate(seed, settings, demos=3, queries=4):
    finish = _settings(settings)
    source = program(settings)
    inputs = sample_inputs(seed, demos=demos, queries=queries)
    result = {"task_id": TASK_ID, "seed": seed, "settings": copy.deepcopy(settings),
              "prototype_version": VERSION, "program_solution": source}
    for split in ("train", "test"):
        result[split] = [{"input": grid, "output": O.solve(grid, finish)}
                         for grid in inputs[split]]
    return result


def public_turn(episode, query_index=0):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [{"input": copy.deepcopy(pair["input"]),
                   "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def write_examples(out, seed=17, demos=3):
    from reviewer_support import public_challenge_bytes

    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("example destination must be new or empty")
    public = out / "public"
    private = out / "private"
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, settings in enumerate(SETTINGS):
        episode = generate(seed, settings, demos=demos, queries=4)
        visible = public_challenge_bytes(public_turn(episode))
        public_name = f"challenge-{hashlib.sha256(visible).hexdigest()}.json"
        private_name = f"episode-{index}.json"
        (public / public_name).write_bytes(visible)
        (private / private_name).write_text(json.dumps(episode, indent=2) + "\n")
        entries.append({"settings": settings, "public": "public/" + public_name,
                        "private": "private/" + private_name,
                        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest()})
    report = {"schema": "arcpuzzles-parametric-examples-v1", "task_id": TASK_ID,
              "seed": seed, "demos": demos, "queries": 4, "entries": entries,
              "training_admitted": False}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
