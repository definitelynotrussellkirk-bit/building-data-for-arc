#!/usr/bin/env python3
"""Episode-fixed motif ordering prototype for d35dbdf1cfc2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "d35dbdf1cfc2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DEFAULT = {"order": "size_desc"}
SETTINGS = ({"order": "size_desc"}, {"order": "size_asc"})
Grid = list[list[int]]


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_d35dbdf1cfc2_generator_for_parametric", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_program() -> str:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise RuntimeError(TASK_ID)


_DESCENDING_PROGRAM = _canonical_program()
_OLD_COMPARATOR = "(> (first a) (first b))"
_NEW_COMPARATOR = "(< (first a) (first b))"
if _DESCENDING_PROGRAM.count(_OLD_COMPARATOR) != 1:
    raise RuntimeError("canonical order comparator changed unexpectedly")
_ASCENDING_PROGRAM = _DESCENDING_PROGRAM.replace(_OLD_COMPARATOR, _NEW_COMPARATOR, 1)


def _integer(value: Any, lower: int, upper: int, name: str) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"order"}:
        raise ValueError("settings must contain exactly order")
    order = value["order"]
    if type(order) is not str or order not in ("size_desc", "size_asc"):
        raise ValueError("order must be 'size_desc' or 'size_asc'")
    return {"order": order}


def program(settings: Any) -> str:
    return _DESCENDING_PROGRAM if _settings(settings)["order"] == "size_desc" else _ASCENDING_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def transform(grid: Any, settings: Any) -> Grid:
    chosen = _settings(settings)
    errors = GEN.self_check(grid)
    if errors:
        raise ValueError("invalid motif gallery: " + "; ".join(errors))
    return GEN.transform_order(grid, chosen["order"])


def _rng(seed: int, label: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|{seed}|{label}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


_DEMO_PROFILES = (
    (11, 13, 3),
    (14, 15, 3),
    (18, 20, 4),
    (21, 17, 4),
    (24, 28, 5),
    (27, 24, 5),
)
_QUERY_PROFILES = (
    (13, 19, 3),
    (20, 13, 4),
    (23, 27, 5),
    (30, 30, 5),
)

_SHAPES = {
    3: (
        ((0, 0), (1, 0), (2, 0)),  # deliberately tall: exercises rotate-cw
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    ),
}


def _shape_sequence(count: int, rng: random.Random) -> tuple[tuple[tuple[int, int], ...], ...]:
    sizes = GEN._SIZE_SCHEDULES[count]
    shapes: list[tuple[tuple[int, int], ...]] = []
    for position, size in enumerate(sizes):
        if position == 0:
            shape = _SHAPES[3][0]
        else:
            options = _SHAPES[size]
            shape = options[(rng.randrange(len(options)) + position) % len(options)]
            rotation = rng.randrange(4)
            reflection = bool(rng.randrange(2))
            shape = GEN._transform_template(shape, rotation, reflection)
        shapes.append(tuple(shape))
    return tuple(shapes)


def _candidate(seed: int, index: int, *, query: bool) -> Grid:
    profiles = _QUERY_PROFILES if query else _DEMO_PROFILES
    height, width, count = profiles[index % len(profiles)]
    rng = _rng(seed, "query" if query else "demo", index)
    palette = GEN.PALETTES[GEN.PALETTE_KINDS[rng.randrange(len(GEN.PALETTE_KINDS))]]
    colors = list(palette[:count])
    rng.shuffle(colors)
    shapes = list(_shape_sequence(count, rng))
    if count == 3:
        slots = rng.sample(list(GEN._CORNER_SLOTS), 3)
    elif count == 4:
        slots = list(GEN._CORNER_SLOTS)
        rng.shuffle(slots)
    else:
        slots = list(GEN._CORNER_SLOTS) + ["center"]
        rng.shuffle(slots)
    grid = GEN._build_scene(height, width, colors, shapes, slots)
    errors = GEN.self_check(grid)
    if errors:
        raise RuntimeError("prototype constructed a scene outside the canonical grammar: " + "; ".join(errors))
    objects = GEN._extract_objects(grid)
    if len({len(obj["cells"]) for obj in objects}) < 2:
        raise RuntimeError("candidate does not expose size ordering")
    if not any(obj["r2"] - obj["r1"] > obj["c2"] - obj["c1"] for obj in objects):
        raise RuntimeError("candidate does not exercise conditional rotation")
    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise RuntimeError("candidate does not distinguish motif order")
    return grid


def _unique_candidate(seed: int, index: int, *, query: bool, seen: set[str]) -> Grid:
    for attempt in range(16):
        candidate_index = index + attempt * 101
        grid = _candidate(seed, candidate_index, query=query)
        if digest(grid) not in seen:
            return grid
    raise RuntimeError("bounded candidate construction could not produce a novel input")


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer(seed, -(2**63), 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)
    train, test = [], []
    seen: set[str] = set()
    for index in range(demos):
        grid = _unique_candidate(seed, index, query=False, seen=seen)
        seen.add(digest(grid))
        train.append({"input": grid, "output": transform(grid, chosen)})
    other = SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]
    if not all(transform(pair["input"], other) != pair["output"] for pair in train):
        raise RuntimeError("demonstrations fail to identify motif order")
    for index in range(queries):
        grid = _unique_candidate(seed, index, query=True, seen=seen)
        seen.add(digest(grid))
        test.append({"input": grid, "output": transform(grid, chosen)})
    return {"train": train, "test": test, "program_solution": program(chosen)}


class RacketRunner:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: Any) -> Grid:
        from puzzle_generators.rule_wrap import wrap_rule
        errors = GEN.self_check(grid)
        if errors:
            raise ValueError("invalid motif gallery")
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    chosen = next(setting for setting in SETTINGS if program(setting) == episode["program_solution"])
    with RacketRunner() as execute:
        for pair in episode["train"] + episode["test"]:
            if execute(episode["program_solution"], pair["input"]) != pair["output"]:
                raise ValueError("Racket label disagreement")
    other = SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]
    refuted = [
        index
        for index, pair in enumerate(episode["train"])
        if transform(pair["input"], other) != pair["output"]
    ]
    if len(refuted) != len(episode["train"]):
        raise ValueError("motif order is not identified by every demonstration")
    return {"racket_checked": True, "alternate_refuted_by_demos": refuted}
