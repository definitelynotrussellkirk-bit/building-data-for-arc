"""Independent oracle and repeatable audit for generator 96c1983b6cb5.

This file deliberately does not import transform or validation helpers from the
selected generator.  It is reviewer tooling, not an alternative label authority.
With ``--racket`` it executes the selected canonical Racket program and fails
rather than silently falling back to the Python oracle.
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

TASK = "96c1983b6cb5"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

# Canonical rule order, copied from the selected Racket source's public names.
TRANSFORM_NAMES = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip-h",
    "flip-v",
    "transpose",
    "anti-transpose",
)
CANONICAL_TRANSFORMS = frozenset({1, 4, 6})
PALETTE_PAIRS = ((2, 3), (4, 5), (6, 7), (1, 6), (5, 2))


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST")
        or ROOT / f"generators/{TASK}/generator.py"
    ).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", selected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent from {path}")


def canonical_pairs() -> list[dict]:
    row = canonical()
    test = row.get("test")
    tests = test if isinstance(test, list) else [test]
    return list(row.get("train") or []) + [item for item in tests if item]


def normalized_rule_hash() -> str:
    source = str(canonical()["program_solution"])
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if not width or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    separators = [
        col
        for col in range(width)
        if all(row[col] == 8 for row in grid)
    ]
    if len(separators) != 2:
        raise ValueError(f"expected exactly two full color-8 separators, found {separators}")
    left, right = separators
    if not (0 < left < right < width - 1):
        raise ValueError("separator columns must leave three nonempty panels")
    panels = (
        [list(row[:left]) for row in grid],
        [list(row[left + 1:right]) for row in grid],
        [list(row[right + 1:]) for row in grid],
    )
    if any(len(panel) != len(grid) or any(len(row) != len(grid) for row in panel) for panel in panels):
        raise ValueError("panels must be square and match grid height")
    return panels


def transform_grid(panel: list[list[int]], code: int) -> list[list[int]]:
    """Apply one D4 transform using the selected Racket program's order."""
    source = [list(row) for row in panel]
    if not source or any(len(row) != len(source) for row in source):
        raise ValueError("transform expects a nonempty square panel")
    if code == 0:
        return source
    if code == 1:  # 90 degrees clockwise
        return [list(row) for row in zip(*source[::-1])]
    if code == 2:
        return [list(reversed(row)) for row in reversed(source)]
    if code == 3:  # 90 degrees counter-clockwise
        return [list(row) for row in zip(*source)][::-1]
    if code == 4:  # flip left-right
        return [list(reversed(row)) for row in source]
    if code == 5:  # flip up-down
        return [list(row) for row in reversed(source)]
    if code == 6:
        return [list(row) for row in zip(*source)]
    if code == 7:
        return transform_grid(transform_grid(source, 6), 2)
    raise ValueError(f"unknown transform code {code}")


def transform_cells(cells: Iterable[tuple[int, int]], n: int, code: int) -> frozenset[tuple[int, int]]:
    marker = [[0] * n for _ in range(n)]
    for row, col in cells:
        marker[row][col] = 1
    changed = transform_grid(marker, code)
    return frozenset(
        (row, col)
        for row, values in enumerate(changed)
        for col, value in enumerate(values)
        if value
    )


def foreground(panel: list[list[int]]) -> tuple[int, frozenset[tuple[int, int]]]:
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"panel needs exactly one nonzero color, found {sorted(colors)}")
    color = next(iter(colors))
    cells = frozenset(
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value == color
    )
    if not cells:
        raise ValueError("panel is empty")
    return color, cells


def infer_transform(grid: list[list[int]]) -> int:
    panel_a, panel_b, _ = split_panels(grid)
    color_a, cells_a = foreground(panel_a)
    color_b, cells_b = foreground(panel_b)
    if color_a != color_b:
        raise ValueError("A and B must use the same foreground color")
    matches = [
        code
        for code in range(8)
        if transform_cells(cells_a, len(panel_a), code) == cells_b
    ]
    if len(matches) != 1:
        raise ValueError(f"A->B transform must be unique, found {matches}")
    return matches[0]


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    *_, panel_c = split_panels(grid)
    return transform_grid(panel_c, infer_transform(grid))


def observed(grid: list[list[int]]) -> dict[str, int]:
    panel_a, _, panel_c = split_panels(grid)
    source, cells_a = foreground(panel_a)
    target, cells_c = foreground(panel_c)
    pair = (source, target)
    if pair not in PALETTE_PAIRS:
        raise ValueError(f"unknown palette pair {pair}")
    return {
        "panel_n": len(panel_a),
        "transform": infer_transform(grid),
        "a_cells": len(cells_a),
        "c_cells": len(cells_c),
        "palette_id": PALETTE_PAIRS.index(pair),
    }


def canonical_subset_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: knows only transforms shown by the three canonical pairs."""
    *_, panel_c = split_panels(grid)
    code = infer_transform(grid)
    return transform_grid(panel_c, code if code in CANONICAL_TRANSFORMS else 1)


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {
            "program": canonical()["program_solution"],
            "grids": grids,
        }
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                "Racket parity worker failed: "
                + result.get("stderr", "")
                + result.get("stdout", "")
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list[list[list[int]]]]:
    by_band: dict[str, dict] = {}
    retained: list[list[list[int]]] = []
    all_inputs: set[str] = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        panels: set[int] = set()
        transforms: set[int] = set()
        palettes: set[int] = set()
        inputs: set[str] = set()
        for index in range(count):
            seed = 10_003 + band_index * 100_000 + index
            sample_index = index * 11 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            inputs.add(digest)
            all_inputs.add(digest)
            facts = observed(grid)
            panels.add(facts["panel_n"])
            transforms.add(facts["transform"])
            palettes.add(facts["palette_id"])
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counts["canonical_size"] += facts["panel_n"] == 3
            truth = reference_output(grid)
            counts["changed_outputs"] += truth != split_panels(grid)[2]
            counts["canonical_subset_counterexamples"] += canonical_subset_rival(grid) != truth
            if len(retained) < 48:
                retained.append(grid)
        by_band[band] = dict(
            counts,
            distinct_inputs=len(inputs),
            panel_n=sorted(panels),
            transforms=sorted(transforms),
            palettes=sorted(palettes),
        )
    canonical_rows = canonical_pairs()
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": normalized_rule_hash(),
        "canonical_pairs": len(canonical_rows),
        "canonical_python_matches": sum(
            reference_output(pair["input"]) == pair["output"] for pair in canonical_rows
        ),
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in canonical_rows],
        "distinct_inputs": len(all_inputs),
        "by_band": by_band,
        "sampling_design": (
            "Three disjoint seed ranges, sample_index=11*i+3. Distinct counts are set "
            "cardinalities, not independent-probability estimates."
        ),
    }, [pair["input"] for pair in canonical_rows] + retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=140, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require real canonical Racket parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["by_band"].values())
    )
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(grids, outputs))
                if reference_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # loud CLI evidence, never a silent fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
