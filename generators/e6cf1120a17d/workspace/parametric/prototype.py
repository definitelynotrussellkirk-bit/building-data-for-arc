"""Canonical/marker-selected corner-routing episodes for e6cf1120a17d."""
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

TASK_ID = "e6cf1120a17d"
SCHEMA = "arcpuzzles-e6cf1120a17d-corner-routing-v1"
HOME = Path(__file__).resolve().parent
ROUTINGS = ("diagonal", "min_color_turn")
DEMO_PROFILES = (
    (9, 9, 5, 5),
    (12, 14, 7, 8),
    (16, 18, 10, 11),
    (20, 22, 14, 15),
    (24, 26, 18, 19),
    (28, 29, 22, 23),
)
QUERY_PROFILES = (
    (10, 13, 6, 8),
    (16, 19, 10, 12),
    (24, 27, 18, 20),
    (30, 30, 28, 28),
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
MIN_COLOR_TURN_PROGRAM = (HOME / "rules" / "min_color_turn.rkt").read_text(encoding="utf-8")
ALWAYS_CLOCKWISE_PROGRAM = (HOME / "rules" / "always_clockwise.rkt").read_text(encoding="utf-8")
ALWAYS_COUNTERCLOCKWISE_PROGRAM = (HOME / "rules" / "always_counterclockwise.rkt").read_text(encoding="utf-8")


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"routing"}
            or type(settings["routing"]) is not str
            or settings["routing"] not in ROUTINGS):
        raise ValueError("settings must contain exactly routing=diagonal|min_color_turn")
    return {"routing": settings["routing"]}


def program(settings):
    routing = settings_value(settings)["routing"]
    return CANONICAL_PROGRAM if routing == "diagonal" else MIN_COLOR_TURN_PROGRAM


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


def analyze_input(grid):
    strict_grid(grid)
    h, w = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for value in row:
            if value:
                counts[value] = counts.get(value, 0) + 1
    if len(counts) < 5:
        raise ValueError("input requires one rectangle color and four marker colors")
    rect_color = max(counts, key=counts.get)
    rect_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == rect_color]
    if not rect_cells:
        raise ValueError("missing rectangle")
    r0 = min(r for r, _ in rect_cells)
    r1 = max(r for r, _ in rect_cells)
    c0 = min(c for _, c in rect_cells)
    c1 = max(c for _, c in rect_cells)
    if r0 < 1 or c0 < 1 or r1 >= h - 1 or c1 >= w - 1 or r1 - r0 + 1 < 5 or c1 - c0 + 1 < 5:
        raise ValueError("rectangle must be at least 5x5 with a one-cell margin")
    inside = ((r0 + 1, c0 + 1), (r0 + 1, c1 - 1), (r1 - 1, c1 - 1), (r1 - 1, c0 + 1))
    outside = ((r0 - 1, c0 - 1), (r0 - 1, c1 + 1), (r1 + 1, c1 + 1), (r1 + 1, c0 - 1))
    markers = tuple(grid[r][c] for r, c in inside)
    if any(value in (0, rect_color) for value in markers) or len(set(markers)) != 4:
        raise ValueError("markers must be four distinct nonzero non-rectangle colors")
    inside_set = set(inside)
    for r in range(h):
        for c in range(w):
            expected = rect_color if r0 <= r <= r1 and c0 <= c <= c1 and (r, c) not in inside_set else 0
            if (r, c) in inside_set:
                continue
            if grid[r][c] != expected:
                raise ValueError("input must contain only the marked rectangle")
    min_index = markers.index(min(markers))
    return {
        "rect_color": rect_color,
        "bbox": (r0, c0, r1, c1),
        "inside": inside,
        "outside": outside,
        "markers": markers,
        "min_index": min_index,
        "min_color": markers[min_index],
        "turn": "clockwise" if min_index in (0, 2) else "counterclockwise",
    }


def fixture_grid(height, width, *, rectangle, rect_color, marker_colors):
    integer(height, 7, 30, "height")
    integer(width, 7, 30, "width")
    if type(rectangle) not in (tuple, list) or len(rectangle) != 4:
        raise ValueError("rectangle must be rr,rc,rh,rw")
    rr, rc, rh, rw = rectangle
    for value, name in zip(rectangle, ("rr", "rc", "rh", "rw")):
        integer(value, 0, 30, name)
    if rh < 5 or rw < 5 or rr < 1 or rc < 1 or rr + rh >= height or rc + rw >= width:
        raise ValueError("rectangle must fit with one-cell margin")
    if type(rect_color) is not int or not 1 <= rect_color <= 9:
        raise ValueError("rect_color must be 1..9")
    if (type(marker_colors) not in (tuple, list) or len(marker_colors) != 4
            or any(type(v) is not int or not 1 <= v <= 9 or v == rect_color for v in marker_colors)
            or len(set(marker_colors)) != 4):
        raise ValueError("marker_colors must be four distinct colors excluding rect_color")
    grid = [[0] * width for _ in range(height)]
    for r in range(rr, rr + rh):
        for c in range(rc, rc + rw):
            grid[r][c] = rect_color
    positions = ((rr + 1, rc + 1), (rr + 1, rc + rw - 2),
                 (rr + rh - 2, rc + rw - 2), (rr + rh - 2, rc + 1))
    for (r, c), color in zip(positions, marker_colors):
        grid[r][c] = color
    analyze_input(grid)
    return grid


def python_oracle(grid, settings):
    routing = settings_value(settings)["routing"]
    info = analyze_input(grid)
    output = [row[:] for row in grid]
    for r, c in info["inside"]:
        output[r][c] = 0
    step = 2 if routing == "diagonal" else (1 if info["turn"] == "clockwise" else -1)
    for index, color in enumerate(info["markers"]):
        r, c = info["outside"][(index + step) % 4]
        output[r][c] = color
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
    height, width, rect_h, rect_w = profile
    integer(height, 7, 30, "height")
    integer(width, 7, 30, "width")
    integer(rect_h, 5, height - 2, "rect_h")
    integer(rect_w, 5, width - 2, "rect_w")
    rng = _rng(seed, domain, index, attempt)
    rr = rng.randint(1, height - rect_h - 1)
    rc = rng.randint(1, width - rect_w - 1)
    rect_color = rng.choice(range(1, 10))
    palette = rng.sample([value for value in range(1, 10) if value != rect_color], 4)
    palette.sort()
    desired_min = (index + (0 if domain == "demo" else 2)) % 4
    markers = [None] * 4
    markers[desired_min] = palette[0]
    remaining_positions = [i for i in range(4) if i != desired_min]
    remaining_colors = palette[1:]
    rng.shuffle(remaining_colors)
    for position, color in zip(remaining_positions, remaining_colors):
        markers[position] = color
    return fixture_grid(height, width, rectangle=(rr, rc, rect_h, rect_w),
                        rect_color=rect_color, marker_colors=tuple(markers))


@lru_cache(maxsize=1)
def rival_programs():
    return {
        "diagonal": CANONICAL_PROGRAM,
        "min_color_turn": MIN_COLOR_TURN_PROGRAM,
        "always_clockwise": ALWAYS_CLOCKWISE_PROGRAM,
        "always_counterclockwise": ALWAYS_COUNTERCLOCKWISE_PROGRAM,
    }


def check_teaching(train, settings, *, engine=None):
    routing = settings_value(settings)["routing"]
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
    if survivors != [routing]:
        raise ValueError(f"demonstrations do not identify {routing}; surviving rules={survivors}")
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
