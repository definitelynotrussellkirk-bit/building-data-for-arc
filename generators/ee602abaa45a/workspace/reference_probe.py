"""Independent oracle and audit tooling for task ee602abaa45a.

This module intentionally does not import helpers from the production generator.
It parses framed candidates directly from pixels, implements the published rule,
and can compare a batch against the selected Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "ee602abaa45a"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _components(grid: list[list[int]], predicate) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if (sr, sc) in seen or not predicate(color):
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                        and predicate(grid[nr][nc])
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def frames(grid: list[list[int]]) -> list[dict]:
    """Parse color>=7 rectangular frame components in rule reading order."""
    parsed: list[dict] = []
    for component in _components(grid, lambda value: value >= 7):
        r0, c0, r1, c1 = component["bbox"]
        bottom = r1 - 1
        selector = grid[bottom][c0 + 1]
        transform = grid[bottom][c0 + 2]
        candidates: dict[int, list[tuple[int, int]]] = {}
        for color in (1, 2):
            candidates[color] = [
                (r, c)
                for r in range(r0 + 1, bottom)
                for c in range(c0 + 1, c1)
                if grid[r][c] == color
            ]
        parsed.append(
            {
                **component,
                "selector": selector,
                "transform": transform,
                "candidates": candidates,
            }
        )
    return sorted(parsed, key=lambda frame: frame["bbox"][:2])


def _crop(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = list(cells)
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    result = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        result[r - r0][c - c0] = 1
    return result


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 3:
        return deepcopy(grid)
    if code == 4:
        return _rotate_cw(grid)
    if code == 5:
        return [row[::-1] for row in grid[::-1]]
    if code == 6:
        return [row[::-1] for row in grid]
    raise ValueError(f"unsupported transform code {code}")


def reference_output(
    grid: list[list[int]],
    *,
    selector_override: int | None = None,
    ignore_transform: bool = False,
    order: str = "reading",
    alignment: str = "center",
) -> list[list[int]]:
    """Compute the task output from pixels, with optional rival behavior."""
    parsed = frames(grid)
    if order == "left_to_right":
        parsed = sorted(parsed, key=lambda frame: (frame["bbox"][1], frame["bbox"][0]))
    elif order != "reading":
        raise ValueError(f"unknown order {order}")

    pieces: list[list[list[int]]] = []
    for frame in parsed:
        selector = selector_override if selector_override is not None else frame["selector"]
        pattern = _crop(frame["candidates"].get(selector, []))
        code = 3 if ignore_transform else frame["transform"]
        transformed = _transform(pattern, code)
        pieces.append(
            [
                [frame["color"] if value else 0 for value in row]
                for row in transformed
            ]
        )

    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        top = 0 if alignment == "top" else (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    output[top + r][left + c] = value
        left += len(piece[0]) + 1
    return output


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    parsed = frames(grid)
    if len(parsed) != 2:
        raise ValueError(f"expected two frames, found {len(parsed)}")
    first, second = parsed
    first_left = first["bbox"][1]
    second_left = second["bbox"][1]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "selector_first": first["selector"],
        "transform_pair": f"{first['transform']}-{second['transform']}",
        "layout_order": "left_first" if first_left < second_left else "right_first",
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket parity worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])


def audit(module, count: int, *, include_racket: bool = False) -> dict:
    counters: Counter = Counter()
    samples: list[list[list[int]]] = []
    hashes: set[str] = set()
    output_hashes: set[str] = set()
    by_band: dict[str, dict] = {}
    rivals = {
        "always_candidate_1": lambda grid: reference_output(grid, selector_override=1),
        "always_candidate_2": lambda grid: reference_output(grid, selector_override=2),
        "ignore_transform": lambda grid: reference_output(grid, ignore_transform=True),
        "left_to_right": lambda grid: reference_output(grid, order="left_to_right"),
        "top_align": lambda grid: reference_output(grid, alignment="top"),
    }
    for band in (None, "easy", "medium", "hard"):
        band_counts: Counter = Counter()
        profiles: set[tuple] = set()
        for index in range(count):
            grid = module.generate(1009 + index, index, difficulty=band)
            issues = module.self_check(grid)
            expected = reference_output(grid)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            out_digest = hashlib.sha256(json.dumps(expected, separators=(",", ":")).encode()).hexdigest()
            hashes.add(digest)
            output_hashes.add(out_digest)
            band_counts["samples"] += 1
            band_counts["self_check_errors"] += bool(issues)
            band_counts["nondeterministic"] += grid != module.generate(1009 + index, index, difficulty=band)
            profiles.add(tuple(observed(grid).items()))
            for name, rival in rivals.items():
                band_counts[f"rival_disagreements:{name}"] += rival(grid) != expected
            if len(samples) < 24:
                samples.append(grid)
        band_counts["profiles"] = len(profiles)
        by_band[str(band)] = dict(band_counts)
        counters.update(band_counts)
    canonical = canonical_pairs()
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": sum(
            reference_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
        "distinct_inputs": len(hashes),
        "distinct_outputs": len(output_hashes),
        "counts": dict(counters),
        "by_band": by_band,
        "sampling_design": (
            "The same deterministic seed/index schedule is crossed with four bands; "
            "counts are evidence over those calls, not independent random estimates."
        ),
    }
    if include_racket:
        racket = racket_outputs([pair["input"] for pair in canonical] + samples)
        python_outputs = [reference_output(pair["input"]) for pair in canonical] + [
            reference_output(grid) for grid in samples
        ]
        report["racket_parity"] = {
            "checked": len(racket),
            "matches": sum(a == b for a, b in zip(racket, python_outputs)),
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--generator")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count, include_racket=args.racket)
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
