#!/usr/bin/env python3
"""Episode-fixed guide direction prototype for d1dab66b0d54."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "d1dab66b0d54"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DEFAULT = {"direction": "forward"}
SETTINGS = ({"direction": "forward"}, {"direction": "backward"})
Grid = list[list[int]]


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_d1dab66b0d54_generator_for_parametric", path)
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


_FORWARD_PROGRAM = _canonical_program()
_BACKWARD_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (greens (find-color g 3))
                (all-same-row (let* ((r0 (fst (first greens))))
                                (for/and ((p (rest greens))) (= (fst p) r0))))
                (spacing (if all-same-row
                             (let* ((cols (sort (map snd greens) <)))
                               (- (second cols) (first cols)))
                             (let* ((rows (sort (map fst greens) <)))
                               (- (second rows) (first rows)))))
                (dr (if all-same-row 0 (- spacing)))
                (dc (if all-same-row (- spacing) 0))
                (reds (find-color g 2))
                (cleared (recolor-cells g reds 0)))
           (reduce (lambda (g2 p)
                     (let* ((nr (+ (fst p) dr))
                            (nc (+ (snd p) dc)))
                       (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                           (set-cell g2 nr nc 2)
                           g2)))
                   cleared
                   reds))))"""


def _integer(value: Any, lower: int, upper: int, name: str) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"direction"}:
        raise ValueError("settings must contain exactly direction")
    direction = value["direction"]
    if type(direction) is not str or direction not in ("forward", "backward"):
        raise ValueError("direction must be 'forward' or 'backward'")
    return {"direction": direction}


def program(settings: Any) -> str:
    return _FORWARD_PROGRAM if _settings(settings)["direction"] == "forward" else _BACKWARD_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def transform(grid: Any, settings: Any) -> Grid:
    chosen = _settings(settings)
    analysis = GEN._analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid guide scene: " + "; ".join(analysis["errors"]))
    sign = 1 if chosen["direction"] == "forward" else -1
    dr, dc = ((sign * analysis["spacing"], 0)
              if analysis["orientation"] == "col"
              else (0, sign * analysis["spacing"]))
    height, width = analysis["height"], analysis["width"]
    if any(not (0 <= r + dr < height and 0 <= c + dc < width) for r, c in analysis["reds"]):
        raise ValueError("selected direction moves the ring out of bounds")
    output = [row[:] for row in grid]
    for r, c in analysis["reds"]:
        output[r][c] = 0
    for r, c in analysis["reds"]:
        output[r + dr][c + dc] = 2
    return output


def _rng(seed: int, label: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|{seed}|{label}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


_DEMO_PROFILES = (
    (11, 15, "row", 3, 4, 1),
    (16, 11, "col", 3, 4, 1),
    (15, 20, "row", 4, 5, 1),
    (21, 14, "col", 4, 5, 2),
    (18, 24, "row", 5, 5, 2),
    (24, 18, "col", 5, 5, 2),
)
_QUERY_PROFILES = (
    (13, 19, "row", 3, 5, 1),
    (20, 13, "col", 4, 5, 2),
    (23, 27, "row", 5, 5, 2),
    (30, 30, "col", 5, 6, 2),
)


def _candidate(seed: int, index: int, *, query: bool) -> Grid:
    profile = (_QUERY_PROFILES if query else _DEMO_PROFILES)[index % (4 if query else 6)]
    height, width, orientation, spacing, count, source_index = profile
    rng = _rng(seed, "query" if query else "demo", index)
    axis_length = height if orientation == "col" else width
    span = (count - 1) * spacing
    starts = list(range(1, axis_length - span - 1))
    start = starts[rng.randrange(len(starts))]
    cross_length = width if orientation == "col" else height
    cross = rng.randint(1, cross_length - 2)
    grid = GEN._build_scene(
        height,
        width,
        orientation,
        spacing,
        count,
        source_index,
        start=start,
        cross=cross,
    )
    if GEN.self_check(grid):
        raise RuntimeError("prototype constructed a scene outside the canonical grammar")
    # The interior source is deliberate: both directions are total and visibly distinct.
    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise RuntimeError("candidate does not distinguish direction")
    return grid


def _unique_candidate(seed: int, index: int, *, query: bool, seen: set[str]) -> Grid:
    """Construct a novel scene with a fixed, bounded retry sequence."""
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
        raise RuntimeError("demonstrations fail to identify direction")
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
        analysis = GEN._analyze(grid)
        if analysis["errors"]:
            raise ValueError("invalid guide scene")
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
    refuted = [i for i, pair in enumerate(episode["train"])
               if transform(pair["input"], other) != pair["output"]]
    if len(refuted) != len(episode["train"]):
        raise ValueError("direction is not identified by every demonstration")
    return {"racket_checked": True, "alternate_refuted_by_demos": refuted}
