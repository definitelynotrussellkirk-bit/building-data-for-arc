"""Independent oracle and repeatable audit for task 697e51dfedef.

This is reviewer tooling, not label authority.  The Python oracle is deliberately
small and independent of ``generator.py``; ``racket_outputs`` executes the
selected canonical Racket rule when an authority parity check is required.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "697e51dfedef"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
for candidate in (REPO_ROOT / "shared/runtime", REPO_ROOT):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

RANK_COLORS = (2, 4, 8)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or TASK_HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_697e51dfedef", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def components(grid: list[list[int]]) -> list[dict]:
    """Return same-color 4-connected components without using generator code."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            ordered = tuple(sorted(cells))
            result.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "origin": ordered[0],
                }
            )
    return result


def _recolor(grid: list[list[int]], ordered: Iterable[dict]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for component, color in zip(ordered, RANK_COLORS):
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def oracle_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent statement of the intended size-rank law."""
    return _recolor(grid, sorted(components(grid), key=lambda item: item["size"]))


def reading_order_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: recolor components by top-left reading order."""
    return _recolor(grid, sorted(components(grid), key=lambda item: item["origin"]))


def observed_axes(grid: list[list[int]]) -> dict[str, int | str]:
    ordered = sorted(components(grid), key=lambda item: item["origin"])
    sizes = [item["size"] for item in ordered]
    if sizes == sorted(sizes):
        order = "ascending"
    elif sizes == sorted(sizes, reverse=True):
        order = "descending"
    else:
        order = "scrambled"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "layout_order": order}


def witness_input() -> list[list[int]]:
    """Exact lawful input where reading order and size rank disagree."""
    grid = [[0] * 7 for _ in range(7)]
    # Reading order sizes are 3, 1, 2.  Intended rank colors are therefore
    # 8, 2, 4; the rival would use 2, 4, 8.
    for row, col in ((0, 0), (0, 1), (1, 0)):
        grid[row][col] = 3
    grid[3][3] = 6
    for row, col in ((5, 5), (5, 6)):
        grid[row][col] = 9
    return grid


def grid_digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected canonical Racket rule; never silently fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    src = REPO_ROOT / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-authority-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        request = stage / "probe-request.json"
        request.write_text(json.dumps({"grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
bundle = runner._load_bundle('697e51dfedef')
bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
try:
    grids = json.loads(Path('probe-request.json').read_text())['grids']
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in grids]))
finally:
    bridge.shutdown()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(f"Racket authority probe failed: {result}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket authority returned an incomplete batch")
        return outputs


def audit(module, *, per_band: int = 100) -> dict:
    """Return a compact, reproducible distribution/semantic report."""
    report: dict[str, object] = {
        "task_id": TASK_ID,
        "generator": str(Path(module.__file__).resolve()),
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical": {},
        "bands": {},
    }
    canonical = canonical_pairs()
    report["canonical"] = {
        "pairs": len(canonical),
        "oracle_matches": sum(oracle_output(pair["input"]) == pair["output"] for pair in canonical),
        "rival_matches": sum(reading_order_rival(pair["input"]) == pair["output"] for pair in canonical),
        "self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
    }
    for band in ("easy", "medium", "hard"):
        counters: Counter[str] = Counter()
        shapes: set[tuple[int, int]] = set()
        palettes: set[tuple[int, ...]] = set()
        orders: set[str] = set()
        digests: set[str] = set()
        for index in range(per_band):
            grid = module.generate(12_000 + index, index, difficulty=band)
            counters["samples"] += 1
            counters["invalid"] += bool(module.self_check(grid))
            counters["nondeterministic"] += grid != module.generate(12_000 + index, index, difficulty=band)
            counters["witnesses"] += oracle_output(grid) != reading_order_rival(grid)
            shapes.add((len(grid), len(grid[0])))
            palettes.add(tuple(sorted({cell for row in grid for cell in row})))
            orders.add(str(observed_axes(grid)["layout_order"]))
            digests.add(grid_digest(grid))
        report["bands"][band] = {
            **dict(counters),
            "unique_inputs": len(digests),
            "shapes": len(shapes),
            "palettes": len(palettes),
            "layout_orders": sorted(orders),
        }
    witness = witness_input()
    report["witness"] = {
        "input": witness,
        "intended": oracle_output(witness),
        "reading_order": reading_order_rival(witness),
        "differs": oracle_output(witness) != reading_order_rival(witness),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args(argv)
    module = load_generator(args.generator)
    report = audit(module, per_band=args.per_band)
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
        expected = [oracle_output(grid) for grid in grids]
        actual = racket_outputs(grids)
        report["racket"] = {"cases": len(grids), "matches": actual == expected}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
