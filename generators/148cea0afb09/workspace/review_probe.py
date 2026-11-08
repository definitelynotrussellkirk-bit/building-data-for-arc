#!/usr/bin/env python3
"""Independent review probe for ARC task 148cea0afb09.

This module deliberately does not import production helpers for geometry,
selection, or labeling.  It is safe for task-local regression tests and gives
future reviewers one command that audits determinism, validator support,
canonical parity, and the declared bbox-area shortcut.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable

TASK = "148cea0afb09"
ROOT = Path(__file__).resolve().parents[3]
CANONICAL = (
    ROOT
    / "shared/data/base/solutions/banks/0eb6e7ee3b18"
    / "medium_126_select_ranked_object_and_scale2__148cea0afb09.json"
)


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path) if path else ROOT / f"generators/{TASK}/generator.py"
    spec = importlib.util.spec_from_file_location(f"review_generator_{TASK}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    return json.loads(CANONICAL.read_text())


def canonical_pairs(*, include_test: bool = True) -> list[dict]:
    record = canonical()
    visible = json.loads(record["visible_context"]["samples_text"])
    pairs = [
        {"input": [list(row) for row in pair["input"]],
         "output": [list(row) for row in pair["output"]]}
        for pair in visible["train"]
    ]
    if include_test:
        expected = record["verification"]["expected_test_outputs"]
        for pair, output in zip(visible.get("test", []), expected, strict=True):
            pairs.append(
                {"input": [list(row) for row in pair["input"]],
                 "output": [list(row) for row in output]}
            )
    return pairs


def _rectangular_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("cells must be integers")
    return len(grid), width


def components(grid) -> list[tuple[tuple[int, int], ...]]:
    """4-connected components of any nonzero cells after clearing (0,0)."""
    h, w = _rectangular_grid(grid)
    work = [list(row) for row in grid]
    work[0][0] = 0
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for sr in range(h):
        for sc in range(w):
            if work[sr][sc] == 0 or (sr, sc) in seen:
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
                        0 <= nr < h
                        and 0 <= nc < w
                        and work[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty component")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    r1, c1, r2, c2 = bbox(cells)
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def crop_and_scale(grid, cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = tuple(cells)
    r1, c1, r2, c2 = bbox(cells)
    selected = set(cells)
    crop = [
        [grid[r][c] if (r, c) in selected else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    expanded: list[list[int]] = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        expanded.extend([doubled[:], doubled[:]])
    return expanded


def _solve_ranked(grid, key) -> list[list[int]]:
    _rectangular_grid(grid)
    rank = grid[0][0]
    comps = components(grid)
    if type(rank) is not int or not 1 <= rank <= len(comps):
        raise ValueError(f"rank {rank!r} outside 1..{len(comps)}")
    ordered = sorted(comps, key=key)
    return crop_and_scale(grid, ordered[rank - 1])


def solve_by_size(grid) -> list[list[int]]:
    return _solve_ranked(grid, lambda cells: len(cells))


def solve_by_bbox(grid) -> list[list[int]]:
    """Plausible wrong rule: rank objects by bbox area, not cell area."""
    return _solve_ranked(grid, bbox_area)


def observed(grid) -> dict[str, int]:
    _rectangular_grid(grid)
    comps = components(grid)
    colors = {grid[r][c] for comp in comps for r, c in comp}
    if len(colors) != 1:
        raise ValueError(f"expected one component color, found {sorted(colors)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_components": len(comps),
        "rank": grid[0][0],
        "component_color": next(iter(colors)),
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require the packet's real Racket authority; there is no Python fallback."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["racket_target"]["target_code"]
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
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list[list[list[int]]]]:
    counters: Counter[str] = Counter()
    by_band: dict[str, dict] = {}
    samples: list[list[list[int]]] = []
    all_inputs: set[str] = set()
    canonical_set = canonical_pairs()
    canonical_self_check = [module.self_check(pair["input"]) for pair in canonical_set]
    canonical_size_matches = sum(
        solve_by_size(pair["input"]) == pair["output"] for pair in canonical_set
    )
    canonical_bbox_matches = sum(
        solve_by_bbox(pair["input"]) == pair["output"] for pair in canonical_set
    )
    for band in (None, "easy", "medium", "hard"):
        local: Counter[str] = Counter()
        profiles: set[tuple[int, int, int, int, int]] = set()
        for index in range(count):
            seed = 5003 + index
            sample_index = 13 * index + 7
            grid = module.generate(seed, sample_index, difficulty=band)
            local["samples"] += 1
            local["self_check_errors"] += bool(module.self_check(grid))
            local["nondeterministic"] += grid != module.generate(
                seed, sample_index, difficulty=band
            )
            obs = observed(grid)
            local["bbox_rival_disagreements"] += (
                solve_by_size(grid) != solve_by_bbox(grid)
            )
            local["observer_mismatches"] += module.observe_overrides(grid) != obs
            profiles.add(tuple(obs.values()))
            digest = hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest()
            all_inputs.add(digest)
            if len(samples) < 32:
                samples.append(grid)
        local["distinct_profiles"] = len(profiles)
        by_band[str(band)] = dict(local)
        counters.update(local)
    counters["distinct_inputs"] = len(all_inputs)
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_size_matches": canonical_size_matches,
        "canonical_bbox_matches": canonical_bbox_matches,
        "canonical_self_check_errors": canonical_self_check,
        "counts": dict(counters),
        "by_band": by_band,
        "sampling_design": (
            "The same deterministic seed/index schedule is crossed with four bands; "
            "cross-band draws are not independent."
        ),
        "warning": "Python mirrors are supplementary; --racket is authority evidence.",
    }
    return report, [pair["input"] for pair in canonical_set] + samples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="samples per band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical_size_matches"] != len(canonical_pairs())
        or any(report["canonical_self_check_errors"])
        or report["counts"]["self_check_errors"]
        or report["counts"]["nondeterministic"]
        or report["counts"]["observer_mismatches"]
        or report["counts"]["bbox_rival_disagreements"]
        != report["counts"]["samples"]
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            expected = [solve_by_size(grid) for grid in grids]
            mismatches = [i for i, pair in enumerate(zip(outputs, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # noqa: BLE001 - retained in report
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("version", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
