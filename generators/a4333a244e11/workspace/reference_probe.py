"""Independent oracle and reproducible audit for a4333a244e11.

This module is reviewer tooling, not a replacement label authority.  The Python
oracle is intentionally independent of the production generator.  ``--racket``
executes the selected canonical Racket rule and never silently falls back.
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
from typing import Any

TASK_ID = "a4333a244e11"

# The task-test runner relocates reviewer files.  Resolve the nearest runtime
# containing canonical data instead of guessing a fixed parent depth.
try:
    from reviewer_support import canonical_pairs as load_canonical_pairs
    from reviewer_support import canonical_path, find_root
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        support = ancestor / "shared" / "runtime"
        if (support / "reviewer_support.py").is_file():
            sys.path.insert(0, str(support))
            break
    from reviewer_support import canonical_pairs as load_canonical_pairs
    from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]

PALETTES = {
    "canonical": frozenset((2, 3)),
    "warm": frozenset((4, 9)),
    "cool": frozenset((1, 6)),
    "varied": frozenset((5, 7)),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    if path is None:
        candidates = (
            ROOT / "generators" / TASK_ID / "generator.py",
            ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
            HOME / "generator.py",
        )
        candidate = next((item for item in candidates if item.is_file()), candidates[0])
    else:
        candidate = Path(path)
    candidate = candidate.resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    path = canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row {TASK_ID} not found in {path}")


def _grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return deepcopy(value)


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    return [
        {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        for pair in load_canonical_pairs(TASK_ID, root=ROOT, variant=0)
    ]


def canonical_rule_hash() -> str:
    program = canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        facts["errors"].append("grid must be a non-empty list of non-empty rows")
        return facts
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        facts["errors"].append("grid must be rectangular")
        return facts
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        facts["errors"].append("cells must be integer ARC colors 0..9")
        return facts
    height = len(grid)
    if height < 7 or width < 9:
        facts["errors"].append("canvas is too small for the framed two-seed grammar")
        return facts

    top, left, bottom, right = 1, 1, height - 2, width - 2
    frame = {
        *((top, col) for col in range(left, right + 1)),
        *((bottom, col) for col in range(left, right + 1)),
        *((row, left) for row in range(top, bottom + 1)),
        *((row, right) for row in range(top, bottom + 1)),
    }
    actual_eights = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    }
    if actual_eights != frame:
        facts["errors"].append("color 8 must be exactly the inset rectangular frame")

    outer = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    if any(grid[row][col] != 0 for row, col in outer):
        facts["errors"].append("the one-cell outer margin must remain background")

    seeds = [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] not in (0, 8)
    ]
    if len(seeds) != 2:
        facts["errors"].append(f"expected exactly two interior seeds, found {len(seeds)}")
    elif seeds[0][2] == seeds[1][2]:
        facts["errors"].append("the two seeds must have distinct colors")

    allowed = frame | {(row, col) for row, col, _ in seeds}
    extras = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in allowed
    ]
    if extras:
        facts["errors"].append("non-background cells occur outside the frame/seeds grammar")

    facts.update(
        grid=deepcopy(grid),
        height=height,
        width=width,
        frame_h=bottom,
        frame_w=right,
        frame=(top, left, bottom, right),
        seeds=seeds,
    )
    if len(seeds) == 2:
        ordered = sorted(seeds)
        dr = abs(ordered[0][0] - ordered[1][0])
        dc = abs(ordered[0][1] - ordered[1][1])
        facts["alignment"] = "row" if dr == 0 else "column" if dc == 0 else "diagonal"
        facts["tie_mode"] = "present" if (dr + dc) % 2 == 0 else "absent"
        facts["color_order"] = "ascending" if ordered[0][2] < ordered[1][2] else "descending"
        palette = frozenset(seed[2] for seed in seeds)
        facts["palette_kind"] = next((name for name, values in PALETTES.items() if values == palette), None)
    return facts


def _distances(row: int, col: int, seeds, metric: str):
    result = []
    for seed_row, seed_col, color in seeds:
        if metric == "manhattan":
            distance = abs(row - seed_row) + abs(col - seed_col)
        elif metric == "euclidean":
            distance = (row - seed_row) ** 2 + (col - seed_col) ** 2
        else:
            raise ValueError(metric)
        result.append((distance, color))
    return sorted(result)


def rule_output(grid: Any, *, metric: str = "manhattan", tie: str = "zero", reassign_colors: bool = False) -> list[list[int]]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = deepcopy(facts["grid"])
    seeds = sorted(facts["seeds"])
    if reassign_colors:
        colors = sorted(seed[2] for seed in seeds)
        seeds = [(seed[0], seed[1], color) for seed, color in zip(seeds, colors)]
    _, _, bottom, right = facts["frame"]
    for row in range(2, bottom):
        for col in range(2, right):
            if output[row][col] != 0:
                continue
            distances = _distances(row, col, seeds, metric)
            if distances[0][0] < distances[1][0]:
                output[row][col] = distances[0][1]
            elif tie == "lower_color":
                output[row][col] = min(seed[2] for seed in seeds)
    return output


def ascending_position_rival(grid: Any) -> list[list[int]]:
    return rule_output(grid, reassign_colors=True)


def euclidean_rival(grid: Any) -> list[list[int]]:
    return rule_output(grid, metric="euclidean")


def lower_color_tie_rival(grid: Any) -> list[list[int]]:
    return rule_output(grid, tie="lower_color")


def axis_aligned_ascending_rival(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return rule_output(grid, reassign_colors=facts["alignment"] != "diagonal")


def axis_aligned_lower_color_tie_rival(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    tie = "lower_color" if facts["alignment"] != "diagonal" else "zero"
    return rule_output(grid, tie=tie)


def observed(grid: Any) -> dict[str, Any]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("palette_kind") is None:
        raise ValueError("seed palette is outside the generated palette families")
    return {
        "frame_h": facts["frame_h"],
        "frame_w": facts["frame_w"],
        "palette_kind": facts["palette_kind"],
        "alignment": facts["alignment"],
        "tie_mode": facts["tie_mode"],
        "color_order": facts["color_order"],
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
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,grid) for grid in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(generator, count: int) -> tuple[dict[str, Any], list[list[list[int]]]]:
    report: dict[str, Any] = {
        "schema": f"{TASK_ID}-independent-audit-v1",
        "version": generator.VERSION,
        "generator_sha256": hashlib.sha256(Path(generator.__file__).read_bytes()).hexdigest(),
        "rule_hash": canonical_rule_hash(),
        "bands": {},
        "canonical": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "self_check_errors": [generator.self_check(pair["input"]) for pair in pairs],
        "python_matches": sum(rule_output(pair["input"]) == pair["output"] for pair in pairs),
    }
    retained = [pair["input"] for pair in pairs]
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        inputs, shapes, axes = set(), set(), {name: set() for name in generator.AXES}
        for index in range(count):
            grid = generator.generate(1009 + index, index, difficulty=band)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(generator.self_check(grid))
            counts["nondeterministic"] += grid != generator.generate(1009 + index, index, difficulty=band)
            truth = rule_output(grid)
            counts["changed"] += truth != grid
            counts["ascending_rival_disagreements"] += ascending_position_rival(grid) != truth
            counts["euclidean_rival_disagreements"] += euclidean_rival(grid) != truth
            counts["tie_rival_disagreements"] += lower_color_tie_rival(grid) != truth
            counts["axis_aligned_ascending_rival_disagreements"] += (
                axis_aligned_ascending_rival(grid) != truth
            )
            counts["axis_aligned_tie_rival_disagreements"] += (
                axis_aligned_lower_color_tie_rival(grid) != truth
            )
            stats = observed(grid)
            for name, value in stats.items():
                axes[name].add(value)
            shapes.add((len(grid), len(grid[0])))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 8:
                retained.append(grid)
        report["bands"][str(band)] = {
            **counts,
            "distinct_inputs": len(inputs),
            "shapes": sorted(map(list, shapes)),
            "axis_values": {name: sorted(values) for name, values in axes.items()},
        }
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    generator = load_generator(args.generator)
    report, grids = audit(generator, args.count)
    exit_code = int(
        report["canonical"]["python_matches"] != report["canonical"]["pairs"]
        or any(report["canonical"]["self_check_errors"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["bands"].values())
    )
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        try:
            actual = racket_outputs(grids)
            mismatches = [index for index, (grid, output) in enumerate(zip(grids, actual)) if rule_output(grid) != output]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(actual),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # retained as explicit evidence; never a fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"canonical": report["canonical"], "bands": report["bands"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
