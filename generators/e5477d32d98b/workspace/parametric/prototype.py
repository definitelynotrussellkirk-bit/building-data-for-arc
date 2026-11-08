"""Forward/reverse normalized stencil episodes for e5477d32d98b."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "e5477d32d98b"
SCHEMA = "arcpuzzles-e5477d32d98b-stencil-v1"
HOME = Path(__file__).resolve().parent
DIRECTIONS = ("forward", "reverse")
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
DEMO_PROFILES = (
    (4, 3, "balanced"),
    (6, 4, "sparse"),
    (8, 5, "dense"),
    (5, 6, "balanced"),
    (10, 7, "sparse"),
    (12, 8, "dense"),
)
QUERY_PROFILES = (
    (4, 3, "balanced"),
    (8, 5, "sparse"),
    (15, 7, "dense"),
    (30, 9, "balanced"),
)
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"direction"}
            or type(settings["direction"]) is not str
            or settings["direction"] not in DIRECTIONS):
        raise ValueError("settings must contain exactly direction=forward|reverse")
    return {"direction": settings["direction"]}


def program(settings):
    direction = settings_value(settings)["direction"]
    return (HOME / "rules" / f"{direction}.rkt").read_text(encoding="utf-8")


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


def _connected(cells):
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = {pending[0]}
    while pending:
        row, col = pending.pop()
        for dr, dc in _DIRS4:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return len(seen) == len(cells)


def panels(grid):
    strict_grid(grid)
    height, width = len(grid), len(grid[0])
    if not 4 <= height <= 30 or (width - 2) % 3:
        raise ValueError("input requires three equal panels and two separators")
    panel_width = (width - 2) // 3
    if not 3 <= panel_width <= 9:
        raise ValueError("panel width must be in 3..9")
    if any(row[panel_width] != 5 or row[2 * panel_width + 1] != 5 for row in grid):
        raise ValueError("input requires two full color-5 separator columns")
    result = [
        [[row[index * (panel_width + 1) + col] for col in range(panel_width)]
         for row in grid]
        for index in range(3)
    ]
    palettes = [{value for row in panel for value in row if value} for panel in result]
    if any(len(palette) != 1 for palette in palettes):
        raise ValueError("every panel must contain exactly one nonzero object color")
    if palettes[0] != palettes[1] or palettes[0] == palettes[2] or 5 in set().union(*palettes):
        raise ValueError("before/after share one color; query uses another; 5 is reserved")
    for panel in result:
        cells = {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value}
        if not _connected(cells):
            raise ValueError("each panel object must be 4-connected")
    return result


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


def _transform(cells, height, width, orientation):
    if orientation == 0:
        return set(cells)
    if orientation == 1:
        return {(r, width - 1 - c) for r, c in cells}
    if orientation == 2:
        return {(height - 1 - r, c) for r, c in cells}
    return {(height - 1 - r, width - 1 - c) for r, c in cells}


def _branch_sets(rng, core, height, width, density, count=3):
    available = height * width - len(core)
    if available < count:
        raise ValueError("not enough free cells for disjoint stencil branches")
    target_total = {
        "sparse": max(count, min(12, available // 8)),
        "balanced": max(count, min(40, available // 3)),
        "dense": max(count, min(96, (available * 2) // 3)),
    }[density]
    target_total = min(target_total, available)
    targets = [target_total // count] * count
    for index in range(target_total % count):
        targets[index] += 1
    rng.shuffle(targets)

    branches = [set() for _ in range(count)]
    for _ in range(height * width * count * 8):
        if all(len(branches[i]) >= targets[i] for i in range(count)):
            break
        order = list(range(count))
        rng.shuffle(order)
        progressed = False
        occupied = core | set().union(*branches)
        for index in order:
            if len(branches[index]) >= targets[index]:
                continue
            support = core | branches[index]
            candidates = []
            for row in range(height):
                for col in range(width):
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
    if any(len(branches[i]) != targets[i] for i in range(count)):
        raise ValueError(f"could not construct {count} disjoint connected stencil branches")
    return tuple(branches)


def sample_input(seed, domain, index, profile, attempt=0):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    integer(attempt, 0, 31, "attempt")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    height, panel_width, density = profile
    integer(height, 4, 30, "panel height")
    integer(panel_width, 3, 9, "panel width")
    if density not in {"sparse", "balanced", "dense"}:
        raise ValueError("unknown density profile")
    rng = _rng(seed, domain, index, attempt)
    orientation = rng.randrange(4)
    standard_core = {(0, col) for col in range(panel_width)} | {
        (row, panel_width - 1) for row in range(height)
    }
    core = _transform(standard_core, height, panel_width, orientation)
    branch_before, branch_after, branch_query = _branch_sets(
        rng, core, height, panel_width, density
    )
    color_source, color_query = rng.sample(COLORS, 2)
    shapes = (
        core | branch_before,
        core | branch_after,
        core | branch_query,
    )
    colors = (color_source, color_source, color_query)
    result = []
    for row in range(height):
        fields = [[colors[p] if (row, col) in shapes[p] else 0
                   for col in range(panel_width)] for p in range(3)]
        result.append(fields[0] + [5] + fields[1] + [5] + fields[2])
    panels(result)
    return result


def _normalized(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def python_oracle(grid, settings):
    before, after, query = panels(grid)
    if settings_value(settings)["direction"] == "reverse":
        before, after = after, before
    before_cells = _normalized({(r, c) for r, row in enumerate(before) for c, value in enumerate(row) if value})
    after_cells = _normalized({(r, c) for r, row in enumerate(after) for c, value in enumerate(row) if value})
    query_cells = {(r, c) for r, row in enumerate(query) for c, value in enumerate(row) if value}
    query_top = min(r for r, _ in query_cells)
    query_left = min(c for _, c in query_cells)
    query_color = next(value for row in query for value in row if value)
    output = [row[:] for row in query]
    for row, col in after_cells - before_cells:
        rr, cc = query_top + row, query_left + col
        if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
            output[rr][cc] = query_color
    return output


@lru_cache(maxsize=1)
def rival_programs():
    results = {direction: program({"direction": direction}) for direction in DIRECTIONS}
    expressions = {
        "identity": "q",
        "copy_before": "(if b qcolor 0)",
        "copy_after": "(if a qcolor 0)",
        "add_both_differences": "(if (not (equal? b a)) qcolor q)",
    }
    for name, expression in expressions.items():
        results[name] = """(rule!
          (let* ((pw (quotient (- (cols g) 2) 3))
                 (before (subgrid g 0 0 (- (rows g) 1) (- pw 1)))
                 (after (subgrid g 0 (+ pw 1) (- (rows g) 1) (* 2 pw)))
                 (query (subgrid g 0 (+ (* 2 pw) 2) (- (rows g) 1) (- (cols g) 1)))
                 (qcolor (first (filter (lambda (v) (not (= v 0))) (apply append query)))))
            (grid-from-fn (rows query) (cols query)
              (lambda (r c)
                (let ((b (not (= (at before r c) 0)))
                      (a (not (= (at after r c) 0)))
                      (q (at query r c)))
                  """ + expression + ")))))"
    return results


def check_teaching(train, settings, *, engine=None):
    direction = settings_value(settings)["direction"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pairs require exactly input/output")
        panels(pair["input"])
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
    if survivors != [direction]:
        raise ValueError(f"demonstrations do not identify {direction}; surviving rules={survivors}")
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
            for attempt in range(32):
                grid = sample_input(seed, domain, index, profiles[index], attempt)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError("could not generate a distinct input within 32 draws")
            seen.add(key)
            episode[split].append({"input": grid, "output": python_oracle(grid, settings)})
    return episode
