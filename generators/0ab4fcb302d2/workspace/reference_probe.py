"""Independent semantic oracle and audit tool for generator 0ab4fcb302d2.

The parser and output constructors in this file deliberately do not import
production geometry helpers.  Future reviewers can use it to inspect the
advertised axes, enumerate shortcut disagreements, audit sliding lessons, and
compare generated cases with the real Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "0ab4fcb302d2"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def parse(grid: Any) -> dict[str, Any]:
    """Parse one lawful mini-grid solely from rendered pixels."""
    if not isinstance(grid, list) or len(grid) != 3:
        raise ValueError("grid must contain exactly three list rows")
    if any(not isinstance(row, list) or len(row) != 3 for row in grid):
        raise ValueError("grid must be rectangular 3x3")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")

    gap_rows = [r for r in range(3) if all(grid[r][c] == 0 for c in range(3))]
    gap_cols = [c for c in range(3) if all(grid[r][c] == 0 for r in range(3))]
    if len(gap_rows) != 1 or len(gap_cols) != 1:
        raise ValueError(
            f"expected one all-zero row and column, found {gap_rows=} {gap_cols=}"
        )
    gap_row, gap_col = gap_rows[0], gap_cols[0]
    rows = [r for r in range(3) if r != gap_row]
    cols = [c for c in range(3) if c != gap_col]
    cells = [(r, c) for r in rows for c in cols]
    values = [grid[r][c] for r, c in cells]
    if any(value == 0 for value in values):
        raise ValueError("every non-gap intersection must be nonzero")
    markers = [index for index, value in enumerate(values) if value == 2]
    if len(markers) != 1:
        raise ValueError(f"expected one red marker, found {len(markers)}")
    fills = [value for value in values if value != 2]
    if len(fills) != 3 or len(set(fills)) != 1:
        raise ValueError("the other three quadrant cells must share one fill color")
    block_color = fills[0]
    if block_color in (0, 2):
        raise ValueError("fill color must be nonzero and non-red")
    return {
        "gap_row": gap_row,
        "gap_col": gap_col,
        "marker_corner": markers[0],
        "block_color": block_color,
    }


def observed(grid: Any) -> dict[str, int]:
    return parse(grid)


def _output_for_diagonal(grid: Any, *, main_diagonal: bool) -> list[list[int]]:
    info = parse(grid)
    top = 1 if info["gap_row"] == 0 else 0
    bottom = 4 if info["gap_row"] == 2 else 5
    left = 1 if info["gap_col"] == 0 else 0
    right = 4 if info["gap_col"] == 2 else 5
    starts = (
        ((top, left), (bottom, right))
        if main_diagonal
        else ((top, right), (bottom, left))
    )
    out = [[0] * 9 for _ in range(9)]
    for row0, col0 in starts:
        for row in range(row0, row0 + 4):
            for col in range(col0, col0 + 4):
                out[row][col] = info["block_color"]
    return out


def rule_output(grid: Any) -> list[list[int]]:
    info = parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["marker_corner"] in (0, 3)
    )


def gap_parity_output(grid: Any) -> list[list[int]]:
    """Wrong canonical-perfect shortcut: compare gap indices, ignore marker."""
    info = parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["gap_row"] == info["gap_col"]
    )


def inverse_gap_parity_output(grid: Any) -> list[list[int]]:
    """Wrong generated-data shortcut: invert gap parity and ignore marker."""
    info = parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["gap_row"] != info["gap_col"]
    )


def always_main_output(grid: Any) -> list[list[int]]:
    return _output_for_diagonal(grid, main_diagonal=True)


def always_anti_output(grid: Any) -> list[list[int]]:
    return _output_for_diagonal(grid, main_diagonal=False)


def counterexample_input() -> list[list[int]]:
    """Exact gap-parity counterexample requested by the review question."""
    return [[0, 0, 0], [0, 3, 2], [0, 3, 3]]


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected rule using the repository's real Racket bridge."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical = None
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canonical = row
                break
    if canonical is None:
        raise KeyError(TASK)

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": canonical["program_solution"], "grids": grids}),
            encoding="utf-8",
        )
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


def _digest(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def audit(module, count: int = 250) -> dict[str, Any]:
    """Return a reusable generator/shortcut/lesson census."""
    canonical = canonical_pairs()
    report: dict[str, Any] = {
        "task_id": TASK,
        "canonical_pairs": len(canonical),
        "canonical_rule_matches": sum(
            rule_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "gap_parity_canonical_matches": sum(
            gap_parity_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "counterexample": counterexample_input(),
        "counterexample_outputs_disagree": (
            rule_output(counterexample_input()) != gap_parity_output(counterexample_input())
        ),
        "bands": {},
        "lesson_windows": {},
    }
    all_digests: set[str] = set()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        name = "default" if band is None else band
        counts = Counter()
        axes = {key: set() for key in ("gap_row", "gap_col", "marker_corner", "block_color")}
        for index in range(count):
            seed = 17_000 + band_index * 100_000 + index
            sample_index = band_index * count + index
            grid = module.generate(seed, sample_index, difficulty=band)
            info = observed(grid)
            digest = _digest(grid)
            all_digests.add(digest)
            counts["draws"] += 1
            counts["self_check_failures"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                seed, sample_index, difficulty=band
            )
            counts["gap_parity_disagreements"] += (
                rule_output(grid) != gap_parity_output(grid)
            )
            counts["inverse_gap_parity_disagreements"] += (
                rule_output(grid) != inverse_gap_parity_output(grid)
            )
            counts["always_main_disagreements"] += (
                rule_output(grid) != always_main_output(grid)
            )
            counts["always_anti_disagreements"] += (
                rule_output(grid) != always_anti_output(grid)
            )
            for key, value in info.items():
                axes[key].add(value)
        report["bands"][name] = {
            **counts,
            "axis_values": {key: sorted(values) for key, values in axes.items()},
        }

        rotation = Counter()
        failures = []
        for start in range(32):
            grids = [
                module.generate(700_000 + band_index * 1000 + start, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(grids)):
                demos = [
                    {"input": deepcopy(grid), "output": rule_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_index
                ]
                query = {"input": deepcopy(grids[query_index])}
                issues = module.lesson_identifiable(demos, query)
                rotation["checks"] += 1
                rotation["failures"] += bool(issues)
                if issues and len(failures) < 8:
                    failures.append({
                        "start": start,
                        "query_index": query_index,
                        "issues": issues,
                    })
        report["lesson_windows"][name] = {**rotation, "examples": failures}
    report["unique_inputs"] = len(all_digests)

    random.seed(20261004)
    before = random.getstate()
    module.generate(9, 11, difficulty="hard")
    report["global_random_state_unchanged"] = random.getstate() == before
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(load_generator(args.generator), count=args.count)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    failures = sum(row["self_check_failures"] for row in report["bands"].values())
    failures += sum(row["failures"] for row in report["lesson_windows"].values())
    failures += not report["counterexample_outputs_disagree"]
    failures += not report["global_random_state_unchanged"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
