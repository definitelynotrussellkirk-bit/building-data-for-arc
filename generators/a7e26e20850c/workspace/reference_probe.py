"""Independent audit/oracle for ``a7e26e20850c``.

This is retained reviewer tooling, not production label authority.  It parses the
legend and gray components independently of ``generator.py``, checks the declared
first-three-entry shortcut, and can optionally require parity with the real Racket
rule.  It is safe to copy with a staged task runtime.
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
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "a7e26e20850c"
RUNTIME = ROOT / "shared" / "runtime"
if RUNTIME.exists():
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path: str | Path | None = None):
    generator_path = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_a7e26e20850c", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def canonical_record() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent from {path}")


def legend_runs(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return ``(run_length, color)`` in left-to-right order."""
    row = grid[0]
    runs: list[tuple[int, int]] = []
    col = 0
    while col < len(row):
        color = row[col]
        if color == 0:
            col += 1
            continue
        start = col
        while col < len(row) and row[col] == color:
            col += 1
        runs.append((col - start, color))
    return runs


def gray_components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    """Four-connected gray components in the Racket rule's body rows."""
    remaining = {
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 5
    }
    components: list[frozenset[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(frozenset(component))
    return components


def _recolor(grid: list[list[int]], *, limit: int | None, leave_missing: bool) -> list[list[int]]:
    out = deepcopy(grid)
    runs = legend_runs(grid)
    if limit is not None:
        runs = runs[:limit]
    mapping = dict(runs)
    for component in gray_components(grid):
        color = mapping.get(len(component))
        if color is None:
            if leave_missing:
                continue
            raise ValueError(f"object size {len(component)} has no legend entry")
        for row, col in component:
            out[row][col] = color
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    return _recolor(grid, limit=None, leave_missing=False)


def first_three_rival(grid: list[list[int]]) -> list[list[int]]:
    return _recolor(grid, limit=3, leave_missing=True)


def observed(grid: list[list[int]]) -> dict[str, Any]:
    components = gray_components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_sizes": len(legend_runs(grid)),
        "object_count": len(components),
        "object_sizes": sorted(len(component) for component in components),
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require the repository's actual Racket bridge; never silently fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix="a7e26e20850c-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = stage / "parity-request.json"
        request.write_text(json.dumps({"program": program, "grids": grids}), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,grid) for grid in request["grids"]]))
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
            raise RuntimeError("Racket worker returned an incomplete output batch")
        return outputs


def audit(module, count: int = 100) -> dict[str, Any]:
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive integer")

    pairs = canonical_pairs()
    canonical_matches = sum(intended_output(pair["input"]) == pair["output"] for pair in pairs)
    canonical_rival_matches = sum(first_three_rival(pair["input"]) == pair["output"] for pair in pairs)

    counts = Counter()
    dimensions: set[tuple[int, int]] = set()
    n_sizes: set[int] = set()
    object_sizes: set[int] = set()
    hashes: set[str] = set()
    samples_for_parity: list[list[list[int]]] = [pair["input"] for pair in pairs]
    by_band: dict[str, dict[str, int]] = {}

    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        local = Counter()
        for index in range(count):
            seed = 1009 + 1000 * band_index + index
            sample_index = index * 7 + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            repeated = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            local["samples"] += 1
            issues = module.self_check(grid)
            counts["self_check_errors"] += bool(issues)
            local["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += grid != repeated
            local["nondeterministic"] += grid != repeated

            stats = observed(grid)
            dimensions.add((stats["grid_h"], stats["grid_w"]))
            n_sizes.add(stats["n_sizes"])
            object_sizes.update(stats["object_sizes"])
            counts["object_count_mismatches"] += stats["object_count"] != 3
            local["object_count_mismatches"] += stats["object_count"] != 3
            counts["axis_observation_mismatches"] += module.observe_overrides(grid) != {
                "grid_h": stats["grid_h"],
                "grid_w": stats["grid_w"],
                "n_sizes": stats["n_sizes"],
            }
            intended = intended_output(grid)
            rival = first_three_rival(grid)
            counts["rival_disagreements"] += intended != rival
            local["rival_disagreements"] += intended != rival
            digest = hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            hashes.add(digest)
            if index < 4:
                samples_for_parity.append(grid)
        by_band[str(band)] = dict(local)

    counts["distinct_inputs"] = len(hashes)
    report = {
        "schema": "a7e26e20850c-reference-probe-v1",
        "version": module.VERSION,
        "canonical_matches": canonical_matches,
        "canonical_rival_matches": canonical_rival_matches,
        "counts": dict(counts),
        "by_band": by_band,
        "observed": {
            "dimensions": [list(item) for item in sorted(dimensions)],
            "n_sizes": sorted(n_sizes),
            "object_sizes": sorted(object_sizes),
        },
        "parity_samples": samples_for_parity,
        "scope": (
            "Finite deterministic sampling over four difficulty bands; declared-rival "
            "disagreement is evidence against one shortcut, not universal identifiability."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require real Racket parity")
    args = parser.parse_args()

    module = load_generator(args.generator)
    report = audit(module, args.count)
    generator_path = (args.generator or ROOT / "generators" / TASK / "generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = hashlib.sha256(
        " ".join(canonical_record()["program_solution"].split()).encode("utf-8")
    ).hexdigest()[:12]
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical_matches"] != len(canonical_pairs())
        or report["counts"]["self_check_errors"]
        or report["counts"]["nondeterministic"]
        or report["counts"]["object_count_mismatches"]
        or report["counts"]["axis_observation_mismatches"]
    )

    if args.racket:
        try:
            grids = report.pop("parity_samples")
            outputs = racket_outputs(grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(grids, outputs))
                if intended_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report.pop("parity_samples", None)
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    else:
        report.pop("parity_samples", None)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": report["version"],
        "canonical_matches": report["canonical_matches"],
        "counts": report["counts"],
        "racket": report["racket"],
        "out": str(args.out),
    }, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
