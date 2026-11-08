"""Independent oracle and repeatable audit for d62a0e470ae8.

This module is review tooling, not label authority.  Its Python oracle is an
independent transcription used to catch generator/helper mistakes; ``--racket``
additionally calls the repository's selected canonical Racket program.
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
from typing import Any, Iterable

TASK = "d62a0e470ae8"
ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators" / TASK


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or HOME / "generator.py").resolve()
    runtime = ROOT / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("reviewed_d62a0e470ae8", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    source = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with source.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent from {source}")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_row()
    test = row.get("test", [])
    tests = test if isinstance(test, list) else [test]
    return list(row.get("train", [])) + list(tests)


def _rectangular(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def components(grid: list[list[int]], *, clear_key: bool = True) -> list[dict[str, Any]]:
    """Row-major, same-color, four-connected objects matching ARC prelude semantics."""
    if not _rectangular(grid):
        raise ValueError("grid must be a non-empty rectangle")
    work = [list(row) for row in grid]
    if clear_key:
        work[0][0] = 0
    h, w = len(work), len(work[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = work[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and work[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells), "size": len(cells)})
    return result


def crop_object(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    cells = obj["cells"]
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _turn_right(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def transform_for_key(grid: list[list[int]], key: int) -> list[list[int]]:
    if key == 1:
        return _turn_right(grid)
    if key == 2:
        return [list(reversed(row)) for row in grid]
    if key == 3:
        return [list(row) for row in reversed(grid)]
    if key == 4:
        return [list(reversed(row)) for row in reversed(grid)]
    return [list(row) for row in grid]


def authority_output(
    grid: list[list[int]],
    *,
    selector: str = "largest",
    transform_mode: str = "key",
    include_all: bool = False,
) -> list[list[int]]:
    """Independent mirror with switches used to express plausible rivals."""
    key = grid[0][0]
    clean = [list(row) for row in grid]
    clean[0][0] = 0
    objs = components(clean, clear_key=False)
    if not objs:
        raise ValueError("no non-key object")
    if include_all:
        cells = [(r, c) for r, row in enumerate(clean) for c, v in enumerate(row) if v]
        pseudo = {"cells": tuple(cells), "size": len(cells)}
        crop = crop_object(clean, pseudo)
    else:
        if selector == "largest":
            obj = max(objs, key=lambda item: item["size"])
        elif selector == "smallest":
            obj = min(objs, key=lambda item: item["size"])
        elif selector == "first":
            obj = objs[0]
        else:
            raise ValueError(f"unknown selector {selector!r}")
        crop = crop_object(clean, obj)
    dispatch = key
    if transform_mode == "identity":
        dispatch = 0
    elif transform_mode == "clockwise":
        dispatch = 1
    elif transform_mode == "key4_identity" and key == 4:
        dispatch = 0
    elif transform_mode != "key":
        raise ValueError(f"unknown transform_mode {transform_mode!r}")
    return transform_for_key(crop, dispatch)


def observed(grid: list[list[int]]) -> dict[str, Any]:
    objs = components(grid)
    sizes = sorted((obj["size"] for obj in objs), reverse=True)
    return {
        "grid_profile": f"{len(grid)}x{len(grid[0])}",
        "key": grid[0][0],
        "main_size": sizes[0] if sizes else 0,
        "n_distractors": max(0, len(sizes) - 1),
    }


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected Racket rule; never silently substitute the Python oracle."""
    grids = list(grids)
    runtime = ROOT / "shared" / "runtime"
    source = ROOT / "src"
    for path in (runtime, source):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": program, "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                f"Racket parity worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module: Any, *, per_band: int = 80, with_racket: bool = False) -> dict[str, Any]:
    bands = (None, "easy", "medium", "hard")
    counters: Counter[str] = Counter()
    by_band: dict[str, Any] = {}
    sample_grids: list[list[list[int]]] = []
    rival_names = sorted(getattr(module, "SEMANTIC_RIVALS", {}))
    witness_names = sorted(getattr(module, "SEMANTIC_WITNESSES", {}))
    for band in bands:
        row: Counter[str] = Counter()
        profiles: Counter[str] = Counter()
        keys: Counter[int] = Counter()
        main_sizes: Counter[int] = Counter()
        distractors: Counter[int] = Counter()
        hashes: set[str] = set()
        for index in range(per_band):
            seed = 51000 + index
            sample_index = index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            row["draws"] += 1
            row["self_check_errors"] += bool(module.self_check(grid))
            row["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            stats = observed(grid)
            profiles[stats["grid_profile"]] += 1
            keys[stats["key"]] += 1
            main_sizes[stats["main_size"]] += 1
            distractors[stats["n_distractors"]] += 1
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = authority_output(grid)
            if hasattr(module, "rule_mirror"):
                row["mirror_mismatches"] += module.rule_mirror(grid) != intended
            for name in witness_names:
                row[f"witness:{name}"] += bool(module.SEMANTIC_WITNESSES[name](deepcopy(grid)))
            for name in rival_names:
                row[f"rival_disagrees:{name}"] += module.SEMANTIC_RIVALS[name](deepcopy(grid)) != intended
            if len(sample_grids) < 24:
                sample_grids.append(grid)
        row["distinct_inputs"] = len(hashes)
        by_band[str(band)] = {
            **dict(row),
            "profiles": dict(sorted(profiles.items())),
            "keys": dict(sorted(keys.items())),
            "main_sizes": dict(sorted(main_sizes.items())),
            "n_distractors": dict(sorted(distractors.items())),
        }
        counters.update(row)

    canonical = canonical_pairs()
    report: dict[str, Any] = {
        "schema": f"{TASK}-independent-audit-v1",
        "task": TASK,
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_python_matches": sum(
            authority_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
        "counts": dict(counters),
        "by_band": by_band,
    }
    if with_racket:
        grids = [pair["input"] for pair in canonical] + sample_grids
        actual = racket_outputs(grids)
        expected = [authority_output(grid) for grid in grids]
        report["racket_cases"] = len(grids)
        report["racket_python_matches"] = sum(a == b for a, b in zip(actual, expected))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--per-band", type=int, default=80)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    report = audit(load_generator(args.generator), per_band=args.per_band, with_racket=args.racket)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text)
    print(text, end="")
    bad = report["canonical_python_matches"] != report["canonical_pairs"]
    bad |= any(report["canonical_self_check_errors"])
    bad |= report["counts"].get("self_check_errors", 0) > 0
    bad |= report["counts"].get("nondeterministic", 0) > 0
    bad |= report["counts"].get("mirror_mismatches", 0) > 0
    if args.racket:
        bad |= report.get("racket_python_matches") != report.get("racket_cases")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
