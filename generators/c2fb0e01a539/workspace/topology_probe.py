"""Independent topology oracle and reusable audit for c2fb0e01a539.

This module is test/review tooling, not label authority.  ``true_output`` computes
4-connected zero regions directly from pixels and preserves every input cell,
painting only enclosed zeros with color 7.  ``--racket`` additionally requires
and executes the repository's canonical Racket authority; it never falls back to
this Python mirror.
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

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK = "c2fb0e01a539"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

Grid = list[list[int]]
Cell = tuple[int, int]
Region = set[Cell]


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK, root=ROOT)


def regions(grid: Grid, *, directions: Iterable[tuple[int, int]] = _DIR4) -> list[Region]:
    """Return zero-cell components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    directions = tuple(directions)
    seen: set[Cell] = set()
    found: list[Region] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            component: Region = set()
            pending = deque([(row, col)])
            seen.add((row, col))
            while pending:
                current = pending.popleft()
                component.add(current)
                cr, cc = current
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            found.append(component)
    return found


def touches_border(region: Iterable[Cell], height: int, width: int) -> bool:
    return any(r in (0, height - 1) or c in (0, width - 1) for r, c in region)


def holes(grid: Grid, *, eight_neighbor: bool = False) -> list[Region]:
    directions = _DIR8 if eight_neighbor else _DIR4
    height, width = len(grid), len(grid[0])
    return [
        region
        for region in regions(grid, directions=directions)
        if not touches_border(region, height, width)
    ]


def true_output(grid: Grid) -> Grid:
    result = deepcopy(grid)
    for region in holes(grid):
        for row, col in region:
            result[row][col] = 7
    return result


def profile_signature(grid: Grid) -> tuple[int, ...]:
    return tuple(sorted(len(region) for region in holes(grid)))


def hash_grid(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Apply the real selected Racket source in an isolated staged runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    source_root = ROOT
    sys.path.insert(0, str(source_root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = None
    canonical_path = source_root / "shared/data/canonical/puzzles.jsonl"
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            candidate = json.loads(line)
            if candidate.get("task_id") == TASK and candidate.get("program_solution"):
                row = candidate
                break
    if row is None:
        raise KeyError(f"no canonical rule for {TASK}")

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(source_root), stage, TASK)
        request = {"program": row["program_solution"], "grids": grids}
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
            raise RuntimeError(f"Racket parity worker failed: {result}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list[Grid]]:
    """Run a deterministic per-band audit and cyclic lesson-rival census."""
    counters = Counter()
    per_band: dict[str, dict] = {}
    retained: list[Grid] = [pair["input"] for pair in canonical_pairs()]
    declared_profiles = tuple(getattr(module, "SCHEDULE_PROFILES", ()))
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))

    canonical_errors = [module.self_check(pair["input"]) for pair in canonical_pairs()]
    canonical_mismatches = [
        index
        for index, pair in enumerate(canonical_pairs())
        if true_output(pair["input"]) != pair["output"]
    ]

    for band in (None, "easy", "medium", "hard"):
        local = Counter()
        seen_inputs: set[str] = set()
        seen_profiles: set[str] = set()
        for index in range(count):
            grid = module.generate(1709 + index, index, difficulty=band)
            local["samples"] += 1
            local["self_check_errors"] += bool(module.self_check(grid))
            local["nondeterministic"] += grid != module.generate(
                1709 + index, index, difficulty=band
            )
            local["mirror_mismatches"] += module.rule_mirror(grid) != true_output(grid)
            local["changed"] += true_output(grid) != grid
            seen_inputs.add(hash_grid(grid))
            if hasattr(module, "schedule_profile"):
                seen_profiles.add(module.schedule_profile(1709 + index, index, band))
            if index < 8:
                retained.append(grid)
        local["distinct_inputs"] = len(seen_inputs)
        local["profiles_seen"] = len(seen_profiles)
        per_band[str(band)] = dict(local, profile_names=sorted(seen_profiles))
        counters.update(local)

        # Every cyclic start must have demonstrations that eliminate each named
        # competitor whenever it would change the next query.
        for start in range(8):
            pairs = []
            for offset in range(module.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = module.generate(2903 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": true_output(grid)})
            demos, query = pairs[:-1], pairs[-1]
            local_reasons = module.lesson_identifiable(demos, query)
            if local_reasons:
                counters["ambiguous_cyclic_lessons"] += 1
            for name, solve in competitors.items():
                if all(solve(pair["input"]) == pair["output"] for pair in demos):
                    if solve(query["input"]) != query["output"]:
                        counters[f"surviving_query_changer:{name}"] += 1

    report = {
        "schema": f"{TASK}-topology-audit-v1",
        "task_id": TASK,
        "version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "canonical_self_check_errors": canonical_errors,
        "canonical_oracle_mismatches": canonical_mismatches,
        "declared_profiles": list(declared_profiles),
        "counts": dict(counters),
        "per_band": per_band,
        "sampling_design": (
            "The same deterministic seed/index schedule is crossed with four bands; "
            "counts are diagnostics, not independent statistical samples."
        ),
        "warning": "The Python oracle is supplementary; --racket is required for authority parity.",
    }
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    module = load_generator(args.generator)
    report, retained = audit(module, args.count)
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or bool(report["canonical_oracle_mismatches"])
        or report["counts"].get("self_check_errors", 0) > 0
        or report["counts"].get("nondeterministic", 0) > 0
        or report["counts"].get("mirror_mismatches", 0) > 0
        or report["counts"].get("ambiguous_cyclic_lessons", 0) > 0
        or any(key.startswith("surviving_query_changer:") for key in report["counts"])
    )
    if args.racket:
        try:
            outputs = racket_outputs(retained)
            mismatches = [
                i for i, (grid, output) in enumerate(zip(retained, outputs))
                if true_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # retained evidence must make unavailability loud
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"counts": report["counts"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
