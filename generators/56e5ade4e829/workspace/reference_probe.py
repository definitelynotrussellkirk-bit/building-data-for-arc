"""Independent oracle, shortcut, and curriculum audit for 56e5ade4e829.

This reviewer-owned tool deliberately re-derives the transformation from input
pixels.  It does not import production geometry helpers.  The canonical Racket
program remains the label authority; ``racket_outputs`` executes it when exact
parity evidence is requested.
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

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK = "56e5ade4e829"
ROOT = find_root(__file__)
HOME = next(
    path
    for path in (
        ROOT / "generators" / TASK,
        ROOT / "puzzle_generators" / "per_puzzle" / TASK,
    )
    if (path / "generator.py").is_file()
)
GENERATOR = HOME / "generator.py"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", GENERATOR)).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_56e5ade4e829", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT, labeled_only=True)


def cells(grid, color):
    return frozenset(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )


def normalize(points):
    points = frozenset(points)
    if not points:
        return frozenset()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return frozenset((row - top, col - left) for row, col in points)


def operands(grid):
    return normalize(cells(grid, 1)), normalize(cells(grid, 2))


def marker(grid):
    controls = [
        value
        for row in grid
        for value in row
        if value not in (0, 1, 2)
    ]
    if len(controls) != 1:
        raise ValueError(f"expected one singleton marker, found {controls!r}")
    return controls[0]


def relation(grid):
    first, second = operands(grid)
    if first == second:
        return "identical"
    if first and second and (first < second or second < first):
        return "subset"
    if first & second and first - second and second - first:
        return "partial"
    return "other"


def control(grid):
    value = marker(grid)
    if value == 3:
        return 1
    if value == 4:
        return 2
    return 0


def _paint_crop(points):
    points = normalize(points)
    if not points:
        return [[0]]
    height = max(row for row, _ in points) + 1
    width = max(col for _, col in points) + 1
    return [
        [8 if (row, col) in points else 0 for col in range(width)]
        for row in range(height)
    ]


def geometry_output(grid):
    """Independent Python transcription of the selected Racket behavior."""
    first, second = operands(grid)
    value = marker(grid)
    if value == 3:
        result = first & second
    elif value == 4:
        result = first | second
    else:
        result = first ^ second
    return _paint_crop(result)


def ignore_intersection_marker(grid):
    """Plausible wrong rule that fits every canonical labeled pair.

    Public examples never use a color-3 marker, so a learner can infer
    ``4 means union; every other singleton marker means XOR`` and remain
    perfectly consistent with the canonical demonstrations.
    """
    first, second = operands(grid)
    result = first | second if marker(grid) == 4 else first ^ second
    return _paint_crop(result)


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "ctrl": control(grid),
        "relation": relation(grid),
    }


def racket_outputs(grids):
    """Execute the canonical Racket program; never silently fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile
    from reviewer_support import canonical_path

    row = None
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            candidate = json.loads(line)
            if candidate.get("task_id") == TASK:
                row = candidate
                break
    if row is None:
        raise KeyError(TASK)

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": row["program_solution"], "grids": grids}),
            encoding="utf-8",
        )
        script = r'''import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, per_band=160):
    pairs = canonical_pairs()
    report = {
        "schema": "56e5ade4e829-independent-audit-v1",
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical": {
            "pairs": len(pairs),
            "python_oracle_matches": sum(
                geometry_output(pair["input"]) == pair["output"] for pair in pairs
            ),
            "shortcut_matches": sum(
                ignore_intersection_marker(pair["input"]) == pair["output"]
                for pair in pairs
            ),
            "self_check_errors": [module.self_check(pair["input"]) for pair in pairs],
        },
        "by_band": {},
        "rotations": {"checked": 0, "failures": []},
    }
    racket_batch = [pair["input"] for pair in pairs]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        inputs = set()
        outputs = set()
        for index in range(per_band):
            seed = 70_001 + 1000 * band_index + index
            sample_index = 17 * index + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                seed, sample_index, difficulty=band
            )
            stats = observed(grid)
            counts[f"ctrl_{stats['ctrl']}"] += 1
            counts[f"relation_{stats['relation']}"] += 1
            intended = geometry_output(grid)
            rival = ignore_intersection_marker(grid)
            counts["shortcut_disagreements"] += intended != rival
            inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
            outputs.add(hashlib.sha256(json.dumps(intended).encode()).hexdigest())
            if index < 12:
                racket_batch.append(grid)
        counts["unique_inputs"] = len(inputs)
        counts["unique_outputs"] = len(outputs)
        report["by_band"][band] = dict(counts)

        # Exhaust several cyclic starts and every legal query rotation.
        for seed in range(4):
            for start in range(9):
                lesson = []
                for offset in range(module.EXAMPLES_NEEDED + 1):
                    grid = module.generate(
                        90_000 + seed,
                        start + offset,
                        difficulty=band,
                    )
                    lesson.append({"input": grid, "output": geometry_output(grid)})
                for query_index, query in enumerate(lesson):
                    demos = [pair for i, pair in enumerate(lesson) if i != query_index]
                    report["rotations"]["checked"] += 1
                    reasons = module.lesson_identifiable(demos, query)
                    if reasons:
                        report["rotations"]["failures"].append(
                            {
                                "band": band,
                                "seed": 90_000 + seed,
                                "start": start,
                                "query_index": query_index,
                                "reasons": reasons,
                            }
                        )
    return report, racket_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=160)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 100:
        parser.error("--per-band must be at least 100")
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        expected = [geometry_output(grid) for grid in grids]
        actual = racket_outputs(grids)
        mismatches = [i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]]
        report["racket"] = {
            "status": "pass" if not mismatches else "fail",
            "checked": len(grids),
            "mismatches": mismatches[:20],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "racket": report["racket"]}))
    if report["rotations"]["failures"] or report["racket"]["status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
