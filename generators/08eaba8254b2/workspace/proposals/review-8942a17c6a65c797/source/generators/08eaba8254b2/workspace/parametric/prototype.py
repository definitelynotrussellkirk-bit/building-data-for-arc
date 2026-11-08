"""Racket-backed occupancy-XOR / updated-state exact-pair episodes."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

TASK_ID = "08eaba8254b2"
HERE = Path(__file__).resolve().parent
MODES = ("xor", "xor_pair_recolor")
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DEMO_WIDTHS = (5, 7, 9, 12, 18, 24)
QUERY_WIDTHS = (6, 14, 22, 30)


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
        raise ValueError("settings must contain exactly mode=xor|xor_pair_recolor")
    return {"mode": settings["mode"]}


def _grid(value, *, rows: int | None = None):
    if (
        type(value) is not list
        or not value
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or (rows is not None and len(value) != rows)
        or (rows is None and not 1 <= len(value) <= 30)
    ):
        expected = f"exactly {rows}" if rows is not None else "1..30"
        raise ValueError(f"grid must have {expected} nonempty rectangular rows")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integers 0..9 in a rectangle")
    return deepcopy(value)


def _input_grid(value):
    return _grid(value, rows=9)


def _output_grid(value):
    return _grid(value, rows=4)


def program(settings) -> str:
    mode = _settings(settings)["mode"]
    name = "xor.rkt" if mode == "xor" else "xor_pair_recolor.rkt"
    return (HERE / "rules" / name).read_text(encoding="utf-8")


def wrong_order_program() -> str:
    return (HERE / "rules/wrong_order.rkt").read_text(encoding="utf-8")


def touching_program() -> str:
    return (HERE / "rules/touching_recolor.rkt").read_text(encoding="utf-8")


def _xor_intermediate(grid):
    source = _input_grid(grid)
    width = len(source[0])
    return [
        [3 if (source[r][c] == 0) != (source[5 + r][c] == 0) else 0
         for c in range(width)]
        for r in range(4)
    ]


def _components(grid, color: int, directions=DIRS4):
    source = _grid(grid)
    height, width = len(source), len(source[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if source[r][c] == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def transform(grid, settings):
    mode = _settings(settings)["mode"]
    base = _xor_intermediate(grid)
    if mode == "xor":
        return base
    out = deepcopy(base)
    for component in _components(base, 3):
        if len(component) == 2:
            for r, c in component:
                out[r][c] = 8
    return out


def wrong_order_transform(grid):
    # Recoloring input 3s before XOR cannot change zero/nonzero occupancy.
    return _xor_intermediate(grid)


def _rng(seed: int, split: str, index: int, width: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{split}|{index}|{width}|v1".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _xor_mask(seed: int, split: str, index: int, width: int):
    rng = _rng(seed, split, index, width)
    mask = set()
    for block, start in enumerate(range(0, width, 4)):
        if block == 0:
            if (seed + index) % 2 == 0 and start + 1 < width:
                mask.update({(0, start), (0, start + 1)})
            else:
                mask.update({(0, start), (1, start)})
            continue
        role = (block + index) % 3
        if role == 0:
            mask.update({(0, start), (1, start), (2, start)})
        elif role == 1:
            mask.add((3, start))
        elif start + 1 < width:
            mask.update({(1, start), (1, start + 1), (2, start), (2, start + 1)})
        else:
            mask.add((2, start))
    # A deterministic row reflection diversifies geometry without changing sizes.
    if rng.randrange(2):
        mask = {(3 - r, c) for r, c in mask}
    return mask


def sample_input(seed: int, split: str, index: int, width: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 32, "index")
    _integer(width, 5, 30, "width")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    rng = _rng(seed, split, index, width)
    mask = _xor_mask(seed, split, index, width)
    grid = [[0 for _ in range(width)] for _ in range(9)]
    separator_palette = [1, 4, 5, 6, 7, 9]
    for c in range(width):
        grid[4][c] = separator_palette[(c + index + seed) % len(separator_palette)]
    top_palette = (1, 2, 4, 6, 7, 9)
    bottom_palette = (1, 2, 4, 5, 6, 7, 9)
    for r in range(4):
        for c in range(width):
            if (r, c) in mask:
                if rng.randrange(2):
                    grid[r][c] = rng.choice(top_palette)
                else:
                    grid[5 + r][c] = rng.choice(bottom_palette)
            elif rng.random() < 0.62:
                grid[r][c] = rng.choice(top_palette)
                grid[5 + r][c] = rng.choice(bottom_palette)
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
    for split, count, widths in (
        ("train", demos, DEMO_WIDTHS),
        ("test", queries, QUERY_WIDTHS),
    ):
        for index, width in enumerate(widths[:count]):
            grid = sample_input(seed, split, index, width)
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

        grid = _input_grid(grid)
        if source not in self.names:
            name = "xor_pair_rule_" + str(len(self.names))
            self.bridge.eval_text(f"(define {name} {wrap_rule(source)})")
            self.names[source] = name
        self.bridge.define_grid("xor_pair_input", grid)
        output = self.bridge.eval_text(f"({self.names[source]} xor_pair_input)")
        self.calls += 1
        return _grid(output)


def hypotheses():
    return {
        "setting:xor": program({"mode": "xor"}),
        "setting:xor_pair_recolor": program({"mode": "xor_pair_recolor"}),
        "touching_component_rival": touching_program(),
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
            input_grid = _input_grid(pair["input"])
            output_grid = _output_grid(pair["output"])
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
        if reference.apply(hypotheses()[selected], pair["input"]) != pair["output"]:
            raise ValueError("surviving setting disagrees on query")
        query_checks.append(True)
    return {
        **fit,
        "query_checks": query_checks,
        "limit": (
            "Finite declared settings plus identity and touching-component rivals; "
            "the wrong-order program is reserved for the causal witness."
        ),
    }
