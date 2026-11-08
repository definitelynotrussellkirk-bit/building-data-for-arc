#!/usr/bin/env python3
"""Source-bound 100-lesson census for task 8a2e39528187.

This retained review tool independently mirrors the selected rule, iterates the
*generator's actual* ``LESSON_COMPETITORS`` declaration, checks every cyclic
schedule start, and can require parity with the real canonical Racket program.
The Python mirror is supplementary evidence only; ``--racket`` is the authority
check used by the final review.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "8a2e39528187"
BANDS = ("easy", "medium", "hard")
SAMPLE_STRIDE = 11
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def load_generator(path: Path | None = None):
    path = (path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("lesson_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise RuntimeError(f"canonical row {TASK} is missing")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_row()
    test = row.get("test", [])
    return row["train"] + (test if isinstance(test, list) else [test])


def _components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
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
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = row + drow, col + dcol
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            result.append(tuple(sorted(cells)))
    return result


def _bbox(cells) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent cell-count+bbox implementation, not generator helper reuse."""
    ranked = sorted(_components(grid), key=lambda cells: (len(cells), _bbox(cells)))
    output = [[0 for _ in row] for row in grid]
    for cells, color in zip(ranked, (2, 4, 6, 8)):
        for row, col in cells:
            output[row][col] = color
    return output


def _grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def audit_lessons(module, lessons_per_band: int = 100):
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    demos = int(module.EXAMPLES_NEEDED)
    competitors = dict(module.LESSON_COMPETITORS)
    all_grids: list[list[list[int]]] = []
    expected_outputs: list[list[list[int]]] = []
    totals = Counter()
    by_band: dict[str, Any] = {}

    canonical = canonical_pairs()
    canonical_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in competitors.items()
    }

    for band_index, band in enumerate(BANDS):
        profiles = Counter()
        starts = Counter()
        unique_inputs: set[str] = set()
        competitor_stats = {
            name: Counter(
                lessons=0,
                survives_all_demos=0,
                demo_disagreements=0,
                query_disagreements=0,
            )
            for name in competitors
        }
        band_counts = Counter(lessons=lessons_per_band)

        for lesson_index in range(lessons_per_band):
            seed = 810_000 + band_index * 100_000 + lesson_index
            start = lesson_index * SAMPLE_STRIDE
            starts[str(start % len(module.SCHEDULE_PROFILES))] += 1
            pairs = []
            for offset in range(demos + 1):
                sample_index = start + offset
                grid = module.generate(seed, sample_index, difficulty=band)
                errors = module.self_check(grid)
                band_counts["rows"] += 1
                band_counts["self_check_errors"] += bool(errors)
                unique_inputs.add(_grid_hash(grid))
                observed = module.observe_overrides(grid)
                profiles[str(observed.get("lesson_profile"))] += 1
                output = independent_output(grid)
                pairs.append({"input": grid, "output": output})
                all_grids.append(grid)
                expected_outputs.append(output)

            lesson_errors = module.lesson_identifiable(pairs[:demos], pairs[demos])
            band_counts["unidentifiable_lessons"] += bool(lesson_errors)
            for name, rival in competitors.items():
                stats = competitor_stats[name]
                stats["lessons"] += 1
                demo_disagreements = sum(
                    rival(pair["input"]) != pair["output"] for pair in pairs[:demos]
                )
                survives = demo_disagreements == 0
                stats["demo_disagreements"] += demo_disagreements
                stats["survives_all_demos"] += survives
                stats["query_disagreements"] += (
                    rival(pairs[demos]["input"]) != pairs[demos]["output"]
                )
                band_counts["surviving_competitor_lessons"] += survives

        band_counts["unique_inputs"] = len(unique_inputs)
        totals.update(band_counts)
        by_band[band] = {
            **dict(band_counts),
            "profiles": dict(sorted(profiles.items())),
            "cyclic_start_residues": dict(sorted(starts.items())),
            "competitors": {
                name: dict(stats) for name, stats in sorted(competitor_stats.items())
            },
        }

    report = {
        "schema": "8a2e39528187-lesson-census-v1",
        "task_id": TASK,
        "lessons_per_band": lessons_per_band,
        "examples_per_lesson": demos,
        "queries_per_lesson": 1,
        "bands": list(BANDS),
        "sampling": {
            "seed_formula": "810000 + band_index*100000 + lesson_index",
            "lesson_start_sample_index": f"lesson_index*{SAMPLE_STRIDE}",
            "rows_per_lesson": demos + 1,
            "overlap": "none; stride exceeds rows_per_lesson",
            "cyclic_start_policy": "all schedule residues visited by stride 11",
        },
        "declared_competitors": sorted(competitors),
        "canonical_competitor_fit": {
            name: {"matching_pairs": count, "denominator": len(canonical)}
            for name, count in sorted(canonical_fit.items())
        },
        "domain_limits": {
            "grid_h": "9..10",
            "grid_w": "10..12",
            "object_count": 4,
            "input_colors": "four distinct nonzero colors",
            "size_profiles": [[2, 3, 4, 5], [2, 2, 4, 5]],
            "rank_palette": [2, 4, 6, 8],
            "lesson_profiles": list(module.SCHEDULE_PROFILES),
            "scope": "lawful curriculum support, not a claim of universal ARC induction",
        },
        "totals": dict(totals),
        "by_band": by_band,
    }
    return report, all_grids, expected_outputs


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require the real selected Racket program; never fall back to Python."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = canonical_row()
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-lesson-probe-") as directory:
        runtime = Path(directory)
        prepare_runtime(Catalog(ROOT), runtime, TASK)
        request = runtime / "lesson-probe-request.json"
        response = runtime / "lesson-probe-response.json"
        request.write_text(json.dumps({"program": row["program_solution"], "grids": grids}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("lesson-probe-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    Path("lesson-probe-response.json").write_text(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], runtime, timeout=900)
        if result["timed_out"] or result["exit_code"] != 0:
            raise RuntimeError(
                "Racket batch failed: "
                f"exit={result['exit_code']} timeout={result['timed_out']} "
                f"stderr={result['stderr'][-1000:]}"
            )
        if not response.is_file():
            raise RuntimeError("Racket batch did not create its response file")
        outputs = json.loads(response.read_text())
        if len(outputs) != len(grids):
            raise RuntimeError(f"Racket returned {len(outputs)} outputs for {len(grids)} grids")
        return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require canonical Racket parity")
    args = parser.parse_args()

    generator_path = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    module = load_generator(generator_path)
    report, grids, expected = audit_lessons(module, args.lessons_per_band)
    row = canonical_row()
    normalized_rule = " ".join(row["program_solution"].split())
    report["source"] = {
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "probe_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": hashlib.sha256(normalized_rule.encode()).hexdigest()[:12],
    }
    report["racket"] = {"status": "not_requested", "checked": 0, "mismatches": []}

    exit_code = int(
        report["totals"].get("self_check_errors", 0) > 0
        or report["totals"].get("unidentifiable_lessons", 0) > 0
        or report["totals"].get("surviving_competitor_lessons", 0) > 0
    )
    if args.racket:
        try:
            authoritative = racket_outputs(grids)
            mismatches = [
                index
                for index, (python_output, racket_output) in enumerate(zip(expected, authoritative))
                if python_output != racket_output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(authoritative),
                "mismatches": mismatches[:50],
                "mismatch_count": len(mismatches),
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "mismatches": [],
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": TASK,
                "generator_sha256": report["source"]["generator_sha256"],
                "lessons_per_band": args.lessons_per_band,
                "totals": report["totals"],
                "racket": report["racket"],
            },
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
