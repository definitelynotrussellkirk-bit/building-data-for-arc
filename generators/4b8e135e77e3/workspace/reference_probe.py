"""Independent oracle and reproducible audit for 4b8e135e77e3.

This module is test/reviewer tooling.  Its Python oracle is deliberately
independent of the generator implementation; ``--racket`` executes the selected
canonical Racket authority and never silently substitutes the Python oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "4b8e135e77e3"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _rot_cw(dr, dc):
    return dc, -dr


def orbit_output(grid, *, tally_mode="count", shape_mode="all"):
    """Independent row-major implementation of the documented transformation."""
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError(f"expected one anchor, found {len(anchors)}")
    ar, ac = anchors[0]
    if tally_mode == "count":
        k = sum(value == 1 for value in grid[0])
    elif tally_mode == "prefix":
        k = 0
        for value in grid[0]:
            if value != 1:
                break
            k += 1
    else:
        raise ValueError(f"unknown tally_mode {tally_mode!r}")
    if shape_mode == "all":
        allowed = set(range(2, 9))
    elif shape_mode == "six_only":
        allowed = {6}
    else:
        raise ValueError(f"unknown shape_mode {shape_mode!r}")
    shape = [(r - ar, c - ac, value)
             for r, row in enumerate(grid) for c, value in enumerate(row)
             if value in allowed]
    out = [[0] * w for _ in range(h)]
    out[ar][ac] = 9
    for quarter in range(k):
        for base_dr, base_dc, value in shape:
            dr, dc = base_dr, base_dc
            for _ in range(quarter):
                dr, dc = _rot_cw(dr, dc)
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w and (rr, cc) != (ar, ac):
                out[rr][cc] = value
    return out


def palette_gated_tally_output(grid):
    noncanonical = any(value not in (0, 1, 6, 9) for row in grid for value in row)
    return orbit_output(grid, tally_mode="prefix" if noncanonical else "count")


def layout_gated_shape_output(grid):
    ones = [column for column, value in enumerate(grid[0]) if value == 1]
    scattered = ones != list(range(len(ones)))
    return orbit_output(grid, shape_mode="six_only" if scattered else "all")


def observed(grid):
    ones = [c for c, value in enumerate(grid[0]) if value == 1]
    shape = [value for row in grid for value in row if 2 <= value <= 8]
    colors = set(shape)
    palette_kind = ("canonical" if colors == {6} else
                    "monochrome" if len(colors) == 1 else "multicolor")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "k_rot": len(ones),
        "shape_size": len(shape),
        "palette_kind": palette_kind,
        "tally_layout": "prefix" if ones == list(range(len(ones))) else "scattered",
    }


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
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


def audit(module, count):
    totals = Counter()
    by_band = {}
    parity_grids = [pair["input"] for pair in canonical_pairs()]
    declared = {}
    for contract_name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, rival in getattr(module, contract_name, {}).items():
            declared.setdefault(name, rival)
    independent_rivals = {
        "prefix_tally_only": lambda grid: orbit_output(grid, tally_mode="prefix"),
        "color6_only": lambda grid: orbit_output(grid, shape_mode="six_only"),
        "palette_gated_tally": palette_gated_tally_output,
        "layout_gated_shape": layout_gated_shape_output,
    }
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        profiles = Counter()
        inputs = set()
        for index in range(count):
            seed = 4109 + index
            sample_index = index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            issues = module.self_check(grid)
            stats = observed(grid)
            intended = orbit_output(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counts["transformed"] += intended != grid
            counts["scattered_tally"] += stats["tally_layout"] == "scattered"
            counts["noncanonical_color"] += stats["palette_kind"] != "canonical"
            counts["prefix_rival_disagreements"] += intended != orbit_output(grid, tally_mode="prefix")
            counts["six_only_rival_disagreements"] += intended != orbit_output(grid, shape_mode="six_only")
            for name, rival in independent_rivals.items():
                counts[f"independent_rival_disagreements:{name}"] += intended != rival(grid)
            for name, rival in declared.items():
                counts[f"declared_rival_disagreements:{name}"] += intended != rival(grid)
            profiles[(stats["grid_h"], stats["grid_w"], stats["palette_kind"])] += 1
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 8:
                parity_grids.append(grid)
        counts["distinct_inputs"] = len(inputs)
        by_band[str(band)] = {**counts, "profiles": {str(k): v for k, v in profiles.items()}}
        totals.update(counts)
    pairs = canonical_pairs()
    canonical_matches = sum(orbit_output(pair["input"]) == pair["output"] for pair in pairs)
    canonical_declared_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in declared.items()
    }
    canonical_independent_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in independent_rivals.items()
    }
    return {
        "schema": f"{TASK}-independent-audit-v2",
        "task_id": TASK,
        "version": module.VERSION,
        "canonical_oracle_matches": canonical_matches,
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in pairs],
        "declared_rivals": sorted(declared),
        "canonical_declared_rival_fit": canonical_declared_fit,
        "canonical_independent_rival_fit": canonical_independent_fit,
        "counts": dict(totals),
        "by_band": by_band,
        "sampling_design": "Four bands use the same deterministic index schedule; aggregate distinct-input counts are sums of per-band counts, not a global union.",
        "warning": "Python geometry is supplementary evidence; use --racket for authority parity.",
    }, parity_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(any(report["canonical_self_check_errors"]) or report["counts"]["self_check_errors"] or report["counts"]["nondeterministic"])
    if args.racket:
        try:
            actual = racket_outputs(grids)
            expected = [orbit_output(grid) for grid in grids]
            mismatches = [index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]]
            report["racket"] = {"status": "passed" if not mismatches else "failed", "checked": len(actual), "mismatches": mismatches}
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # counted and retained; no fallback
            report["racket"] = {"status": "unavailable_or_failed", "checked": 0, "error": f"{type(exc).__name__}: {exc}"}
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("version", "canonical_oracle_matches", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
