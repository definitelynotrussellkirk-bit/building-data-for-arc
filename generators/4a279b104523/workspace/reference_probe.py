"""Independent oracle and distribution probe for task 4a279b104523.

This is reviewer tooling, not label authority. The optional Racket path invokes
the selected canonical program and never silently substitutes this Python oracle.
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

ROOT = Path(__file__).resolve().parents[3]
TASK = "4a279b104523"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | Path | None = None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py")
    candidate = candidate.resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical()
    train = row.get("train") or []
    test = row.get("test") or []
    if isinstance(train, dict):
        train = [train]
    if isinstance(test, dict):
        test = [test]
    return list(train) + list(test)


def rule_hash() -> str:
    source = canonical()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def axis_row(grid: list[list[int]]) -> int:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    rows = [r for r, row in enumerate(grid) if all(value == 8 for value in row)]
    if len(rows) != 1:
        raise ValueError(f"expected one full color-8 row, found {len(rows)}")
    return rows[0]


def source_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]


def observed(grid: list[list[int]]) -> dict[str, object]:
    axis = axis_row(grid)
    cells = source_cells(grid)
    has_above = any(r < axis for r, _, _ in cells)
    has_below = any(r > axis for r, _, _ in cells)
    side = "both" if has_above and has_below else "above" if has_above else "below" if has_below else "none"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(cells),
        "source_side": side,
        "axis_row": axis,
        "n_content_colors": len({value for _, _, value in cells}),
        "profile": (len(grid), len(grid[0]), len({value for row in grid for value in row})),
        "off_center_axis": 2 * axis != len(grid) - 1,
    }


def geometry_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent row-major implementation of the selected written rule."""
    h, w = len(grid), len(grid[0])
    axis = axis_row(grid)
    out = [[0 for _ in range(w)] for _ in range(h)]
    out[axis] = [8 for _ in range(w)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 8):
                continue
            out[r][c] = value
            rr = 2 * axis - r
            if 0 <= rr < h:
                out[rr][c] = value
    return out


def above_only_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: preserve input and mirror only cells above the axis."""
    out = deepcopy(grid)
    axis = axis_row(grid)
    for r, c, value in source_cells(grid):
        if r < axis:
            rr = 2 * axis - r
            if 0 <= rr < len(grid):
                out[rr][c] = value
    return out


def grid_center_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: mirror content around the geometric grid center."""
    out = deepcopy(grid)
    h = len(grid)
    for r, c, value in source_cells(grid):
        rr = h - 1 - r
        if 0 <= rr < h:
            out[rr][c] = value
    return out


def pinned_profile_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(f"profile-floor:v1:{TASK}:{band}:{index}".encode()).hexdigest()
    return int(digest[:12], 16)


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
        request = {"program": canonical()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
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


def audit(module, count: int) -> dict:
    canonical_rows = canonical_pairs()
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "rule_hash": rule_hash(),
        "canonical_self_check": [module.self_check(deepcopy(pair["input"])) for pair in canonical_rows],
        "canonical_geometry_matches": sum(geometry_output(pair["input"]) == pair["output"] for pair in canonical_rows),
        "bands": {},
    }
    all_inputs: set[str] = set()
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        shapes: set[tuple[int, int]] = set()
        profiles: set[tuple[int, int, int]] = set()
        for index in range(count):
            grid = module.generate(10_000 + index, index * 17 + 3, difficulty=band)
            obs = observed(grid)
            counts[f"side_{obs['source_side']}"] += 1
            counts["off_center_axis"] += bool(obs["off_center_axis"])
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(10_000 + index, index * 17 + 3, difficulty=band)
            counts["above_only_disagreements"] += geometry_output(grid) != above_only_rival(grid)
            counts["grid_center_disagreements"] += geometry_output(grid) != grid_center_rival(grid)
            shapes.add((len(grid), len(grid[0])))
            profiles.add(obs["profile"])
            all_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        report["bands"][band] = dict(counts, distinct_shapes=len(shapes), distinct_profiles=len(profiles))
    report["distinct_inputs"] = len(all_inputs)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count)
    path = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(any(report["canonical_self_check"]))
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [module.generate(319, i, source_side=("above", "below", "both")[i % 3]) for i in range(24)]
        try:
            outputs = racket_outputs(grids)
            mismatches = [i for i, (grid, output) in enumerate(zip(grids, outputs)) if geometry_output(grid) != output]
            report["racket"] = {"status": "passed" if not mismatches else "failed", "checked": len(outputs), "mismatches": mismatches}
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {"status": "unavailable_or_failed", "checked": 0, "error": f"{type(exc).__name__}: {exc}"}
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"version": report["version"], "bands": report["bands"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
