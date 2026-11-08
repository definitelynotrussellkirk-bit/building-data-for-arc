"""Canonical endpoints and longest-color-gated run projection for 8a761b80b11b."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "8a761b80b11b"
SCHEMA = "arcpuzzles-8a761b80b11b-run-projection-v1"
HOME = Path(__file__).resolve().parent
MARKINGS = ("endpoints", "longest_color_gate")
DEMO_PROFILES = (
    (7, 12, 4, 7),
    (9, 16, 6, 10),
    (12, 20, 8, 13),
    (16, 24, 10, 16),
    (20, 27, 12, 19),
    (24, 29, 14, 22),
)
QUERY_PROFILES = (
    (10, 15, 6, 9),
    (16, 22, 10, 14),
    (24, 28, 16, 18),
    (30, 30, 20, 20),
)


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return programs[0]


CANONICAL_PROGRAM = _canonical_program()
LONGEST_COLOR_GATE_PROGRAM = (HOME / "rules" / "longest_color_gate.rkt").read_text(encoding="utf-8")
FIRST_RUN_COLOR_GATE_PROGRAM = (HOME / "rules" / "first_run_color_gate.rkt").read_text(encoding="utf-8")
ALL_CENTERS_PROGRAM = (HOME / "rules" / "all_centers.rkt").read_text(encoding="utf-8")


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"marking"}
            or type(settings["marking"]) is not str
            or settings["marking"] not in MARKINGS):
        raise ValueError("settings must contain exactly marking=endpoints|longest_color_gate")
    return {"marking": settings["marking"]}


def program(settings):
    marking = settings_value(settings)["marking"]
    return CANONICAL_PROGRAM if marking == "endpoints" else LONGEST_COLOR_GATE_PROGRAM


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return grid


def _scan_runs(grid):
    runs = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            start, color = column, row[column]
            while column < len(row) and row[column] == color:
                column += 1
            if column < len(row) and row[column] != 0:
                raise ValueError("adjacent different colors require a background gap")
            runs.append({"row": row_index, "start": start, "end": column - 1,
                         "length": column - start, "color": color})
    return runs


def analyze_input(grid):
    strict_grid(grid)
    runs = _scan_runs(grid)
    if len(runs) < 4:
        raise ValueError("input requires at least four horizontal runs")
    longest_length = max(run["length"] for run in runs)
    longest = [run for run in runs if run["length"] == longest_length]
    if len(longest) != 1:
        raise ValueError("input requires a unique longest run")
    anchor_color = longest[0]["color"]
    if sum(run["color"] == anchor_color for run in runs) < 2:
        raise ValueError("longest-run color must recur on a shorter run")
    if runs[0]["color"] == anchor_color:
        raise ValueError("first run color must differ from longest-run color")
    return {
        "runs": runs,
        "longest": longest[0],
        "anchor_color": anchor_color,
        "first_run_color": runs[0]["color"],
    }


def fixture_grid(height, width, *, runs):
    integer(height, 1, 30, "height")
    integer(width, 1, 30, "width")
    if type(runs) not in (tuple, list) or not runs:
        raise ValueError("runs must be a nonempty sequence")
    grid = [[0] * width for _ in range(height)]
    for item in runs:
        if type(item) not in (tuple, list) or len(item) != 4:
            raise ValueError("each run must be row,start,end,color")
        row, start, end, color = item
        for value, low, high, name in (
            (row, 0, height - 1, "row"), (start, 0, width - 1, "start"),
            (end, 0, width - 1, "end"), (color, 1, 9, "color"),
        ):
            integer(value, low, high, name)
        if end < start:
            raise ValueError("run end precedes start")
        for column in range(start, end + 1):
            if grid[row][column] != 0:
                raise ValueError("runs overlap")
            grid[row][column] = color
    analyze_input(grid)
    return grid


def python_oracle(grid, settings):
    marking = settings_value(settings)["marking"]
    info = analyze_input(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for run in info["runs"]:
        row, start, end, length, color = (run[key] for key in ("row", "start", "end", "length", "color"))
        if marking == "endpoints" or color == info["anchor_color"]:
            output[row][start] = color
            output[row][end] = color
        else:
            output[row][start + (length - 1) // 2] = color
            output[row][start + length // 2] = color
    return output


class RacketEngine:
    def __init__(self):
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("a live protected Racket bridge is required")
        self._wrapped = {}
        self.evaluations = 0

    def apply(self, source, grid):
        strict_grid(grid)
        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        self.evaluations += 1
        return strict_grid(self.bridge.eval_text(f"({wrapped} {literal})"))

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


@contextmanager
def _engine(existing):
    if existing is None:
        with RacketEngine() as created:
            yield created
    else:
        yield existing


def _rng(seed, domain, index, attempt=0):
    key = json.dumps([TASK_ID, SCHEMA, seed, domain, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:16], "big"))


def sample_input(seed, domain, index, profile, attempt=0):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    integer(attempt, 0, 63, "attempt")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    height, width, n_runs, longest_length = profile
    integer(height, 4, 30, "height")
    integer(width, 7, 30, "width")
    integer(n_runs, 4, height, "n_runs")
    integer(longest_length, 5, width, "longest_length")
    rng = _rng(seed, domain, index, attempt)
    rows = sorted(rng.sample(range(height), n_runs))
    longest_index = 1 + ((index + (1 if domain == "query" else 0)) % (n_runs - 1))
    repeat_index = (longest_index + 1) % n_runs
    if repeat_index == 0:
        repeat_index = (repeat_index + 1) % n_runs
    if repeat_index == longest_index:
        repeat_index = (repeat_index + 1) % n_runs
    palette = rng.sample(range(1, 10), 5)
    anchor = palette[0]
    lengths = []
    span = max(2, min(longest_length - 1, 12) - 2 + 1)
    for run_index in range(n_runs):
        if run_index == longest_index:
            length = longest_length
        else:
            length = 3 + ((run_index + 2 * index) % span)
            length = min(length, longest_length - 1, width)
        lengths.append(length)
    # Teach both center branches and keep a non-anchor observable on every episode.
    lengths[0] = min(4, longest_length - 1)
    parity_index = 2 if longest_index != 2 else 3
    lengths[parity_index] = min(5, longest_length - 1)
    colors = []
    for run_index in range(n_runs):
        if run_index in (longest_index, repeat_index):
            colors.append(anchor)
        else:
            colors.append(palette[1 + (run_index % 4)])
    if colors[0] == anchor:
        colors[0] = palette[1]
    run_specs = []
    for row, length, color in zip(rows, lengths, colors):
        start = rng.randint(0, width - length)
        run_specs.append((row, start, start + length - 1, color))
    return fixture_grid(height, width, runs=run_specs)


@lru_cache(maxsize=1)
def rival_programs():
    return {
        "endpoints": CANONICAL_PROGRAM,
        "longest_color_gate": LONGEST_COLOR_GATE_PROGRAM,
        "first_run_color_gate": FIRST_RUN_COLOR_GATE_PROGRAM,
        "all_centers": ALL_CENTERS_PROGRAM,
    }


def check_teaching(train, settings, *, engine=None):
    marking = settings_value(settings)["marking"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    seen_inputs = set()
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pairs require exactly input/output")
        analyze_input(pair["input"])
        strict_grid(pair["output"])
        key = json.dumps(pair["input"], separators=(",", ":"))
        if key in seen_inputs:
            raise ValueError("demonstrations must identify the rule with distinct inputs")
        seen_inputs.add(key)
    survivors = []
    distinctions = {}
    with _engine(engine) as runtime:
        for name, source in rival_programs().items():
            mismatches = [index for index, pair in enumerate(train)
                          if runtime.apply(source, pair["input"]) != pair["output"]]
            if mismatches:
                distinctions[name] = {"first_demonstration": mismatches[0]}
            else:
                survivors.append(name)
    if survivors != [marking]:
        raise ValueError(f"demonstrations do not identify {marking}; surviving rules={survivors}")
    return {
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
        "declared_rivals": list(rival_programs()),
        "distinctions": distinctions,
        "limits": "Finite named rule family only; not uniqueness over arbitrary programs.",
    }


def generate(seed, settings, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    settings = settings_value(settings)
    source = program(settings)
    episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": settings,
        "program_solution": source,
        "train": [],
        "test": [],
        "variant_approved": False,
        "training_admitted": False,
    }
    seen = set()
    for split, domain, count, profiles in (
        ("train", "demo", demos, DEMO_PROFILES),
        ("test", "query", queries, QUERY_PROFILES),
    ):
        for index in range(count):
            for attempt in range(64):
                grid = sample_input(seed, domain, index, profiles[index], attempt)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError("could not generate a distinct input within 64 draws")
            seen.add(key)
            episode[split].append({"input": grid, "output": python_oracle(grid, settings)})
    return episode
