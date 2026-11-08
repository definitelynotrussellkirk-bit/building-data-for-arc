"""Racket-backed normalized-intersection episodes with a parity-controlled route."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "729429f8ea2c"
SCHEMA = "arcpuzzles-729429f8ea2c-parity-v1"
HOME = Path(__file__).resolve().parent
MODES = ("intersection", "parity_transform")
DEMO_PROFILES = (
    (14, 16, 5, 5, "sparse"),
    (16, 18, 6, 6, "balanced"),
    (18, 20, 7, 7, "dense"),
    (15, 21, 6, 8, "balanced"),
    (22, 24, 9, 9, "dense"),
    (24, 26, 10, 10, "balanced"),
)
QUERY_PROFILES = (
    (14, 16, 5, 5, "sparse"),
    (20, 22, 8, 8, "balanced"),
    (26, 28, 10, 11, "dense"),
    (30, 30, 12, 12, "dense"),
)
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str
            or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly mode=intersection|parity_transform")
    return {"mode": settings["mode"]}


def program(settings):
    mode = settings_value(settings)["mode"]
    return (HOME / "rules" / f"{mode}.rkt").read_text(encoding="utf-8")


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


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component = set()
            while pending:
                cell = pending.pop()
                component.add(cell)
                for dr, dc in _DIRS4:
                    nxt = (cell[0] + dr, cell[1] + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(component)
    return result


def _normalized(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return {(row - top, col - left) for row, col in cells}


def _largest_component(grid, color):
    components = sorted(_components(grid, color), key=len, reverse=True)
    if len(components) < 2:
        raise ValueError(f"color {color} needs a main component and a distractor")
    if len(components[0]) == len(components[1]):
        raise ValueError(f"color {color} must have a unique largest component")
    return components[0]


def validate_input(grid):
    strict_grid(grid)
    extras = sorted({value for row in grid for value in row if value not in (0, 2, 3)})
    if extras:
        raise ValueError(f"input may contain only colors 0, 2 and 3; found {extras}")
    shape2 = _normalized(_largest_component(grid, 2))
    shape3 = _normalized(_largest_component(grid, 3))
    if not shape2 & shape3:
        raise ValueError("normalized largest components must have a nonempty intersection")
    return grid


def intermediate(grid):
    validate_input(grid)
    shape2 = _normalized(_largest_component(grid, 2))
    shape3 = _normalized(_largest_component(grid, 3))
    cells = sorted(shape2 & shape3)
    return {
        "cells": [list(cell) for cell in cells],
        "count": len(cells),
        "parity": "odd" if len(cells) % 2 else "even",
    }


def _render(cells, color=8):
    cells = set(cells)
    if not cells:
        return [[0]]
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    return [[color if (row, col) in cells else 0 for col in range(width)]
            for row in range(height)]


def _rotate_cw(cells):
    cells = set(cells)
    height = max(row for row, _ in cells) + 1
    return {(col, height - 1 - row) for row, col in cells}


def _flip_lr(cells):
    cells = set(cells)
    width = max(col for _, col in cells) + 1
    return {(row, width - 1 - col) for row, col in cells}


def python_oracle(grid, settings):
    mode = settings_value(settings)["mode"]
    cells = {tuple(cell) for cell in intermediate(grid)["cells"]}
    if mode == "parity_transform":
        cells = _rotate_cw(cells) if len(cells) % 2 else _flip_lr(cells)
    return _render(cells)


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
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _connected_shape(rng, size, max_height, max_width):
    for _ in range(320):
        cells = {(0, 0)}
        for _step in range(size * 100):
            if len(cells) == size:
                break
            row, col = rng.choice(tuple(cells))
            dr, dc = rng.choice(_DIRS4)
            cells.add((row + dr, col + dc))
        normalized = _normalized(cells)
        if (len(normalized) == size
                and max(row for row, _ in normalized) < max_height
                and max(col for _, col in normalized) < max_width):
            return normalized
    raise ValueError("could not construct a bounded connected intersection")


def _asymmetric_intersection(rng, parity, box_height, box_width, density):
    ranges = {
        "sparse": (3, 6),
        "balanced": (7, 12),
        "dense": (13, 20),
    }
    low, high = ranges[density]
    high = min(high, box_height * box_width - 4)
    candidates = [size for size in range(low, high + 1) if size % 2 == parity]
    rng.shuffle(candidates)
    for size in candidates:
        for _ in range(96):
            cells = _connected_shape(rng, size, box_height, box_width)
            plain = _render(cells)
            rotated = _render(_rotate_cw(cells))
            flipped = _render(_flip_lr(cells))
            if plain != rotated and plain != flipped and rotated != flipped:
                return cells
    raise ValueError("could not construct an asymmetric intersection with requested parity")


def _branches(rng, core, box_height, box_width, density):
    available = box_height * box_width - len(core)
    if available < 4:
        raise ValueError("not enough room for two distinct branches")
    total = {
        "sparse": max(4, min(10, available // 4)),
        "balanced": max(6, min(22, available // 3)),
        "dense": max(8, min(40, available // 2)),
    }[density]
    total = min(total, available)
    targets = [total // 2, total - total // 2]
    rng.shuffle(targets)
    branches = [set(), set()]
    for _ in range(box_height * box_width * 24):
        if all(len(branches[index]) >= targets[index] for index in range(2)):
            break
        order = [0, 1]
        rng.shuffle(order)
        occupied = core | branches[0] | branches[1]
        progressed = False
        for index in order:
            if len(branches[index]) >= targets[index]:
                continue
            support = core | branches[index]
            candidates = []
            for row in range(box_height):
                for col in range(box_width):
                    cell = (row, col)
                    if cell in occupied:
                        continue
                    if any((row + dr, col + dc) in support for dr, dc in _DIRS4):
                        candidates.append(cell)
            if candidates:
                chosen = rng.choice(candidates)
                branches[index].add(chosen)
                occupied.add(chosen)
                progressed = True
        if not progressed:
            break
    if any(len(branches[index]) != targets[index] for index in range(2)):
        raise ValueError("could not construct disjoint connected source branches")
    return branches[0], branches[1]


def _placement_candidates(height, width, cells):
    box_height = max(row for row, _ in cells) + 1
    box_width = max(col for _, col in cells) + 1
    return [(top, left)
            for top in range(height - box_height + 1)
            for left in range(width - box_width + 1)]


def _placement_is_free(occupied, cells, top, left, height, width):
    for row, col in cells:
        rr, cc = top + row, left + col
        if not (0 <= rr < height and 0 <= cc < width):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < height and 0 <= nc < width and occupied[nr][nc]:
                    return False
    return True


def _place(grid, occupied, cells, color, rng, target=None):
    height, width = len(grid), len(grid[0])
    candidates = _placement_candidates(height, width, cells)
    rng.shuffle(candidates)
    if target is not None:
        candidates.sort(key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2)
    for top, left in candidates:
        if not _placement_is_free(occupied, cells, top, left, height, width):
            continue
        for row, col in cells:
            rr, cc = top + row, left + col
            grid[rr][cc] = color
            occupied[rr][cc] = True
        return (top, left)
    return None


def sample_input(seed, domain, index, profile, attempt=0):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    integer(attempt, 0, 63, "attempt")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    height, width, box_height, box_width, density = profile
    integer(height, 1, 30, "grid height")
    integer(width, 1, 30, "grid width")
    integer(box_height, 3, height, "shape box height")
    integer(box_width, 3, width, "shape box width")
    if density not in {"sparse", "balanced", "dense"}:
        raise ValueError("unknown density profile")
    rng = _rng(seed, domain, index, attempt)
    parity = 1 if index % 2 == 0 else 0
    core = _asymmetric_intersection(rng, parity, box_height, box_width, density)
    branch2, branch3 = _branches(rng, core, box_height, box_width, density)
    shape2, shape3 = core | branch2, core | branch3

    for placement_attempt in range(96):
        local = random.Random(rng.getrandbits(256) ^ placement_attempt)
        grid = [[0] * width for _ in range(height)]
        occupied = [[False] * width for _ in range(height)]
        corners = [(0, 0), (0, width), (height, 0), (height, width)]
        first_corner = local.randrange(4)
        second_corner = 3 - first_corner
        if _place(grid, occupied, shape2, 2, local, corners[first_corner]) is None:
            continue
        if _place(grid, occupied, shape3, 3, local, corners[second_corner]) is None:
            continue
        distractors = 1 + local.randrange(3)
        okay = True
        for color in (2, 3):
            for _ in range(distractors):
                if _place(grid, occupied, {(0, 0)}, color, local) is None:
                    okay = False
                    break
            if not okay:
                break
        if not okay:
            continue
        try:
            validate_input(grid)
        except ValueError:
            continue
        observed = intermediate(grid)
        if observed["count"] != len(core) or observed["parity"] != ("odd" if parity else "even"):
            continue
        return grid
    raise ValueError("could not place the two largest shapes and their distractors")


def _policy_program(policy):
    if policy not in {"always_rotate", "always_flip", "inverse_parity"}:
        raise ValueError("unknown policy")
    if policy == "always_rotate":
        decision = "#t"
    elif policy == "always_flip":
        decision = "#f"
    else:
        decision = "(= (modulo (length pts) 2) 0)"
    return f'''(rule!
  (let ((dummy 0))
    (define (normalize cells)
      (let ((bb (bbox-of-cells cells)))
        (map (lambda (p) (list (- (first p) (first bb)) (- (second p) (second bb)))) cells)))
    (define (rotate-cw cells height)
      (map (lambda (p) (list (second p) (- height 1 (first p)))) cells))
    (define (flip-lr cells width)
      (map (lambda (p) (list (first p) (- width 1 (second p)))) cells))
    (let* ((comp2 (first (sort (objects (keep-only g 2) 0) (lambda (a b) (> (obj-size a) (obj-size b))))))
           (comp3 (first (sort (objects (keep-only g 3) 0) (lambda (a b) (> (obj-size a) (obj-size b))))))
           (n2 (normalize (obj-cells comp2)))
           (n3 (normalize (obj-cells comp3)))
           (pts (sort (filter (lambda (p) (member p n3)) n2)
                      (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b)))))))
      (if (empty? pts)
          (list (list 0))
          (let* ((height (+ (apply max (map first pts)) 1))
                 (width (+ (apply max (map second pts)) 1))
                 (rotate? {decision})
                 (out-pts (if rotate? (rotate-cw pts height) (flip-lr pts width)))
                 (out-height (if rotate? width height))
                 (out-width (if rotate? height width)))
            (paint-cells (empty-grid out-height out-width 0) out-pts 8))))))'''


@lru_cache(maxsize=1)
def rival_programs():
    return {
        "intersection": program({"mode": "intersection"}),
        "parity_transform": program({"mode": "parity_transform"}),
        "always_rotate": _policy_program("always_rotate"),
        "always_flip": _policy_program("always_flip"),
        "inverse_parity": _policy_program("inverse_parity"),
    }


def check_teaching(train, settings, *, engine=None):
    mode = settings_value(settings)["mode"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pairs require exactly input/output")
        validate_input(pair["input"])
        strict_grid(pair["output"])
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
    if survivors != [mode]:
        raise ValueError(f"demonstrations do not identify {mode}; surviving rules={survivors}")
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
