"""Racket-backed plus-completion / updated-state pair-recolor episodes."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "8b595f6acd93"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "pair_recolor")
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
DEMO_PROFILES = ((10, 15), (12, 15), (15, 12), (18, 18), (22, 16), (24, 24))
QUERY_PROFILES = ((11, 14), (16, 20), (23, 29), (30, 30))


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings) -> dict:
    if (
        type(settings) is not dict
        or set(settings) != {"mode"}
        or type(settings["mode"]) is not str
        or settings["mode"] not in MODES
    ):
        raise ValueError("settings must contain exactly mode=canonical|pair_recolor")
    return {"mode": settings["mode"]}


def _grid(value):
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integers 0..9 in a rectangle")
    return deepcopy(value)


def program(settings) -> str:
    mode = _settings(settings)["mode"]
    name = "canonical.rkt" if mode == "canonical" else "pair_recolor.rkt"
    return (HERE / "rules" / name).read_text(encoding="utf-8")


def wrong_order_program() -> str:
    return (HERE / "rules/wrong_order.rkt").read_text(encoding="utf-8")


def any_same_color_program(*, pair_recolor: bool = False) -> str:
    name = "any_same_color_arms_pair_recolor.rkt" if pair_recolor else "any_same_color_arms.rkt"
    return (HERE / "rules" / name).read_text(encoding="utf-8")


def diagonal_pair_only_program() -> str:
    return (HERE / "rules/diagonal_pair_only.rkt").read_text(encoding="utf-8")


def _plus_center(grid, r: int, c: int) -> bool:
    h, w = len(grid), len(grid[0])
    return (
        grid[r][c] == 0
        and all(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 3
                for dr, dc in DIRS4)
    )


def _fill_centers(grid):
    source = _grid(grid)
    out = deepcopy(source)
    for r in range(len(source)):
        for c in range(len(source[0])):
            if _plus_center(source, r, c):
                out[r][c] = 4
    return out


def _components(grid, color: int, directions):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            cell = stack.pop()
            component.append(cell)
            r, c = cell
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def transform(grid, settings):
    mode = _settings(settings)["mode"]
    filled = _fill_centers(grid)
    if mode == "canonical":
        return filled
    out = deepcopy(filled)
    for component in _components(filled, 4, DIRS8):
        if len(component) == 2:
            for r, c in component:
                out[r][c] = 8
    return out


def wrong_order_transform(grid):
    source = _grid(grid)
    paired = deepcopy(source)
    for component in _components(source, 4, DIRS8):
        if len(component) == 2:
            for r, c in component:
                paired[r][c] = 8
    return _fill_centers(paired)


def _rng(seed: int, split: str, index: int, height: int, width: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{split}|{index}|{height}|{width}|v1".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _draw_plus(grid, r: int, c: int, color: int = 3, missing=None) -> None:
    for dr, dc in DIRS4:
        if missing == (dr, dc):
            continue
        grid[r + dr][c + dc] = color


def sample_input(seed: int, split: str, index: int, height: int, width: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 32, "index")
    _integer(height, 8, 30, "height")
    _integer(width, 8, 30, "width")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    rng = _rng(seed, split, index, height, width)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    candidates = [(r, c) for r in range(2, height - 2, 5) for c in range(2, width - 2, 5)]
    if len(candidates) < 2:
        raise ValueError("profile is too small for distinguishing motifs")
    rng.shuffle(candidates)
    if height * width >= 400:
        selected = candidates
    else:
        selected = candidates[: min(len(candidates), max(6, height * width // 45))]
    # The first six motifs form a teaching-complete prefix: a causal diagonal
    # pair, an independent orthogonal pair, a trimer, two Stage-A near misses,
    # and a passive true plus.
    roles = ("active", "orthogonal_pair", "trimer", "partial", "mismatch", "passive")
    diagonal_orders = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    reserved = set()
    for position, (r, c) in enumerate(selected):
        role = roles[position % len(roles)]
        if position == 0:
            role = "active"
        if role == "orthogonal_pair":
            grid[r][c] = 4
            grid[r][c + 1] = 4
        elif role == "partial":
            _draw_plus(grid, r, c, missing=DIRS4[(index + position) % 4])
        elif role == "mismatch":
            _draw_plus(grid, r, c, color=6)
        else:
            _draw_plus(grid, r, c)
        if role in {"active", "trimer"}:
            order = diagonal_orders[:]
            rng.shuffle(order)
            dr, dc = order[0]
            grid[r + dr][c + dc] = 4
            if role == "trimer":
                dr2, dc2 = (-dr, -dc)
                grid[r + dr2][c + dc2] = 4
        for rr in range(max(0, r - 2), min(height, r + 3)):
            for cc in range(max(0, c - 2), min(width, c + 3)):
                reserved.add((rr, cc))
    # Non-3/non-4 distractors vary palette and density without altering either rule.
    free = [(r, c) for r in range(height) for c in range(width)
            if (r, c) not in reserved and grid[r][c] == 0]
    rng.shuffle(free)
    noise_count = min(len(free), max(2, height * width // 30))
    for r, c in free[:noise_count]:
        grid[r][c] = rng.choice((1, 2, 5, 6, 7, 9))
    return grid


def generate(seed, settings, demos, queries):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    settings = _settings(settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": settings,
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, count, profiles in (
        ("train", demos, DEMO_PROFILES),
        ("test", queries, QUERY_PROFILES),
    ):
        for index, (height, width) in enumerate(profiles[:count]):
            grid = sample_input(seed, split, index, height, width)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    return episode


class Reference:
    """One protected-Racket process reusable across a bounded test/probe."""

    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=15.0)
        self.names = {}
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.shutdown()

    def apply(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule

        grid = _grid(grid)
        if source not in self.names:
            name = "plus_pair_rule_" + str(len(self.names))
            self.bridge.eval_text(f"(define {name} {wrap_rule(source)})")
            self.names[source] = name
        self.bridge.define_grid("plus_pair_input", grid)
        output = self.bridge.eval_text(f"({self.names[source]} plus_pair_input)")
        self.calls += 1
        return _grid(output)


def hypotheses():
    return {
        "setting:canonical": program({"mode": "canonical"}),
        "setting:pair_recolor": program({"mode": "pair_recolor"}),
        "any_same_color_arms": any_same_color_program(),
        "any_same_color_arms_pair_recolor": any_same_color_program(pair_recolor=True),
        "diagonal_pair_only": diagonal_pair_only_program(),
        "identity": "(rule! (lambda (g) g))",
    }


def fit_demonstrations(train, reference):
    survivors = []
    rejected = {}
    for name, source in hypotheses().items():
        mismatches = []
        for index, pair in enumerate(train):
            if reference.apply(source, pair["input"]) != pair["output"]:
                mismatches.append(index)
        if mismatches:
            rejected[name] = mismatches
        else:
            survivors.append(name)
    return {"survivors": survivors, "rejected_by_demo": rejected}


def verify_episode(episode, reference):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = _settings(episode.get("settings"))
    selected = "setting:" + settings["mode"]
    if episode.get("program_solution") != program(settings):
        raise ValueError("episode program differs from fixed setting")
    seen = set()
    for split, low, high in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{split} count must be in {low}..{high}")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every pair needs input and output")
            input_grid = _grid(pair["input"])
            output_grid = _grid(pair["output"])
            key = json.dumps(input_grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(key)
            if reference.apply(program(settings), input_grid) != output_grid:
                raise ValueError("claimed output differs from executed Racket")
    fit = fit_demonstrations(episode["train"], reference)
    declared = [name for name in fit["survivors"] if name.startswith("setting:")]
    if declared != [selected]:
        raise ValueError("demonstrations do not identify selected setting")
    query_checks = []
    for pair in episode["test"]:
        for name in declared:
            if reference.apply(hypotheses()[name], pair["input"]) != pair["output"]:
                raise ValueError("surviving setting disagrees on query")
        query_checks.append(True)
    return {**fit, "query_checks": query_checks,
            "limit": ("Finite declared settings plus any-arm-color, diagonal-only-pair, "
                      "and identity rivals; the wrong-order program is reserved for the causal witness.")}
