"""Parametric square-tally block ordering for ``d0a85a878975``.

``construction`` is the byte-exact canonical program.  Both settings first
identify lawful solid squares, infer the size-to-color map, count each size,
and apply the canonical smallest-key decrement.  That input-derived count-layer
list is then emitted either in its canonical construction order or in reverse.
Input sampling is independent of the private setting.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

TASK_ID = "d0a85a878975"
HERE = Path(__file__).resolve().parent
BLOCK_ORDERS = ("construction", "reverse_construction")
SETTINGS = tuple({"block_order": value} for value in BLOCK_ORDERS)
_DEMO_SOURCE_INDICES = (4, 5, 0, 1, 2, 3)


def _load_base():
    path = HERE.parents[1] / "generator.py"
    body = path.read_bytes()
    name = "_d0a85a878975_reviewed_base_" + hashlib.sha256(path.as_posix().encode() + body).hexdigest()
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load base generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


_BASE = _load_base()


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _order(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"block_order"}
        or type(settings["block_order"]) is not str
        or settings["block_order"] not in BLOCK_ORDERS
    ):
        raise ValueError(
            "settings must contain only block_order='construction' or 'reverse_construction'"
        )
    return settings["block_order"]


def program(settings: Any) -> str:
    order = _order(settings)
    filename = "canonical.rkt" if order == "construction" else "reverse_construction.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _construction_blocks(sizes: list[int], counts: dict[int, int]) -> list[tuple[int, ...]]:
    pairs = [(size, int(counts.get(size, 0))) for size in sorted(sizes)]
    pairs = [(size, count) for size, count in pairs if count > 0]
    if not pairs:
        raise ValueError("tally has no positive square counts")
    blocks: list[tuple[int, ...]] = []
    while pairs:
        layer_count = min(count for _, count in pairs)
        active = tuple(size for size, _ in pairs)
        blocks.extend([active] * layer_count)
        pairs = [
            (size, count - layer_count)
            for size, count in pairs
            if count - layer_count > 0
        ]
    return blocks


def analyze(grid: Any) -> dict[str, Any]:
    facts = _BASE._scene_analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid square-tally input: " + "; ".join(facts["errors"]))
    blocks = _construction_blocks(facts["sizes"], facts["adjusted_counts"])
    result = dict(facts)
    result["construction_blocks"] = [list(block) for block in blocks]
    result["reverse_construction_blocks"] = [list(block) for block in reversed(blocks)]
    return result


def render_from_blocks(grid: Any, blocks: Any) -> list[list[int]]:
    facts = _BASE._scene_analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid square-tally input: " + "; ".join(facts["errors"]))
    if type(blocks) not in (list, tuple) or not blocks:
        raise ValueError("blocks must be a nonempty sequence")
    sizes = facts["sizes"]
    valid_sizes = set(sizes)
    normalized: list[tuple[int, ...]] = []
    for block in blocks:
        if type(block) not in (list, tuple) or not block:
            raise ValueError("each block must be a nonempty size sequence")
        item = tuple(int(size) for size in block)
        if len(set(item)) != len(item) or any(size not in valid_sizes for size in item):
            raise ValueError("block sizes must be unique lawful input sizes")
        normalized.append(item)

    out_h = max(sizes) + 1
    out_w = sum(max(block) + 1 for block in normalized)
    if out_h > 30 or out_w > 30:
        raise ValueError(f"rendered output {out_h}x{out_w} exceeds ARC bounds")
    output = [[facts["background"] for _ in range(out_w)] for _ in range(out_h)]
    col0 = 0
    for block in normalized:
        glyph_w = max(block) + 1
        for row in range(out_h):
            for col in range(glyph_w):
                cover = [size for size in block if size >= 1 + max(row, col)]
                if cover:
                    output[row][col0 + col] = facts["color_by_size"][min(cover)]
        col0 += glyph_w
    return output


def solve(grid: Any, settings: Any) -> list[list[int]]:
    order = _order(settings)
    facts = analyze(grid)
    key = "construction_blocks" if order == "construction" else "reverse_construction_blocks"
    return render_from_blocks(grid, facts[key])


def _query_rng(seed: int) -> random.Random:
    digest = hashlib.sha256(f"d0a85a878975:parametric:query-order:{seed}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=128)
def _input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [
        _BASE.generate(seed, source_index, difficulty="medium")
        for source_index in _DEMO_SOURCE_INDICES
    ]
    queries = [
        _BASE.generate(seed, 100, difficulty="hard"),
        _BASE.generate(seed, 101, difficulty="easy"),
        _BASE.generate(seed, 102, difficulty="medium"),
        _BASE.generate(
            seed,
            103,
            difficulty="hard",
            grid_h=30,
            grid_w=30,
            n_sizes=4,
            size_start=3,
            smallest_drop=False,
            noise_mode="same_color",
        ),
    ]
    _query_rng(seed).shuffle(queries)
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(signatures) != len(set(signatures)):
        raise ValueError("constructed episode contains duplicate inputs")
    for grid in demos + queries:
        if solve(grid, {"block_order": "construction"}) == solve(
            grid, {"block_order": "reverse_construction"}
        ):
            raise ValueError("constructed input does not distinguish block-order settings")
    return demos, queries


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    _order(settings)
    demo_bank, query_bank = _input_bank(seed)

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": deepcopy(grid), "output": solve(grid, settings)}

    return {
        "train": [pair(grid) for grid in demo_bank[:demos]],
        "test": [pair(grid) for grid in query_bank[:queries]],
        "program_solution": program(settings),
    }


def public_turn(episode: Any, index: Any) -> dict[str, Any]:
    if type(episode) is not dict or set(episode) < {"train", "test"}:
        raise ValueError("episode must contain train and test")
    index = _exact_int(index, "query index", 0, len(episode["test"]) - 1)
    return deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": episode["test"][index]["input"]}],
        }
    )


def _rival_functions(chosen: str) -> dict[str, Callable[[Any], list[list[int]]]]:
    rivals: dict[str, Callable[[Any], list[list[int]]]] = {
        other: (lambda grid, value=other: solve(grid, {"block_order": value}))
        for other in BLOCK_ORDERS
        if other != chosen
    }
    # These inherited shortcuts are meaningful under the canonical output order.
    # For the reversed setting, reverse their rendered columns at the glyph level
    # is not available in the base helpers, so the declared-setting rival remains
    # the qualification-critical alternative.
    if chosen == "construction":
        rivals.update(_BASE.LESSON_COMPETITORS)
    return rivals


def lesson_report(episode: Any, settings: Any) -> dict[str, Any]:
    chosen = _order(settings)
    rivals = _rival_functions(chosen)
    survivors: list[str] = []
    query_disagreements: list[str] = []
    for name, rival in rivals.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
        except Exception:
            fits = False
        if fits:
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                query_disagreements.append(name)
    return {
        "rivals_tested": sorted(rivals),
        "surviving_rivals": sorted(survivors),
        "query_disagreements": sorted(query_disagreements),
    }
