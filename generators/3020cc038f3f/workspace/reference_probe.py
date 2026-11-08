"""Independent oracle and distribution probe for 3020cc038f3f.

This file is reviewer-owned test tooling.  It deliberately re-derives the rule
from pixels instead of importing production geometry helpers.  The canonical
Racket program remains the label authority; ``racket_outputs`` executes it when
real parity evidence is requested.
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

TASK = "3020cc038f3f"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "generators" / TASK / "generator.py"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", GENERATOR)).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_3020cc038f3f", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical row {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def normalize(cells):
    if not cells:
        return frozenset()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def operands(grid):
    return normalize(_cells(grid, 1)), normalize(_cells(grid, 2))


def relation(grid):
    first, second = operands(grid)
    if first == second:
        return "identical"
    if first & second and first - second and second - first:
        return "partial"
    return "other"


def geometry_output(grid):
    """Independent Python transcription used only as supplementary evidence."""
    first, second = operands(grid)
    ctrl = grid[0][0]
    height = max((max(r for r, _ in cells) + 1 if cells else 0) for cells in (first, second))
    width = max((max(c for _, c in cells) + 1 if cells else 0) for cells in (first, second))
    if ctrl == 3:
        result = first | second
    elif ctrl == 4:
        result = first ^ second
    elif ctrl == 5:
        result = first & second
    else:
        result = frozenset()
    if not result:
        return [[0]]
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in result:
        out[r][c] = 8
    return out


def shape_statistics_shortcut(grid):
    """Plausible wrong rule that fits all public examples.

    It infers the operation from operand statistics instead of reading control:
    identical operands -> overlap shape, two triominoes -> union, otherwise XOR.
    """
    first, second = operands(grid)
    if first == second:
        result = first
    elif len(first) == len(second) == 3:
        result = first | second
    else:
        result = first ^ second
    if not result:
        return [[0]]
    height = max(max(r for r, _ in cells) + 1 for cells in (first, second))
    width = max(max(c for _, c in cells) + 1 for cells in (first, second))
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in result:
        out[r][c] = 8
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "ctrl": grid[0][0],
        "overlap_kind": relation(grid),
    }


def witness_input():
    """Explicit canonical-like union case that the statistics shortcut mislabels XOR."""
    grid = [[0] * 10 for _ in range(7)]
    grid[0][0] = 3
    for dr, dc in ((0, 0), (1, 0), (1, 1), (1, 2)):
        grid[1 + dr][1 + dc] = 1
    for dr, dc in ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)):
        grid[1 + dr][6 + dc] = 2
    return grid


def racket_outputs(grids):
    """Require and execute the selected Racket authority; never fall back."""
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
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, per_band=160):
    report = {
        "schema": "3020cc038f3f-independent-audit-v1",
        "generator_version": module.VERSION,
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "per_band": per_band,
            "seed": "7001 + 1000*band_index + i",
            "sample_index": "17*i + 5",
        },
        "by_band": {},
        "canonical": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "python_oracle_matches": sum(geometry_output(p["input"]) == p["output"] for p in pairs),
        "shortcut_matches": sum(shape_statistics_shortcut(p["input"]) == p["output"] for p in pairs),
        "self_check_errors": [module.self_check(deepcopy(p["input"])) for p in pairs],
    }
    racket_batch = [p["input"] for p in pairs] + [witness_input()]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        inputs = set()
        outputs = set()
        for i in range(per_band):
            seed = 7001 + 1000 * band_index + i
            sample_index = 17 * i + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            replay = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != replay
            stats = observed(grid)
            counts[f"ctrl_{stats['ctrl']}"] += 1
            counts[f"relation_{stats['overlap_kind']}"] += 1
            intended = geometry_output(grid)
            rival = shape_statistics_shortcut(grid)
            counts["rival_disagreements"] += intended != rival
            counts["empty_outputs"] += intended == [[0]]
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            outputs.add(hashlib.sha256(json.dumps(intended, separators=(",", ":")).encode()).hexdigest())
            if i < 12:
                racket_batch.append(grid)
        counts["unique_inputs"] = len(inputs)
        counts["unique_outputs"] = len(outputs)
        report["by_band"][band] = dict(counts)
    report["witness"] = {
        "input": witness_input(),
        "intended": geometry_output(witness_input()),
        "statistics_shortcut": shape_statistics_shortcut(witness_input()),
    }
    return report, racket_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=160)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 100:
        parser.error("--per-band must be at least 100 for the required lesson audit")
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = (args.generator or GENERATOR).resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        actual = racket_outputs(grids)
        expected = [geometry_output(grid) for grid in grids]
        mismatches = [i for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
        report["racket"] = {
            "status": "pass" if not mismatches else "fail",
            "checked": len(grids),
            "mismatches": mismatches[:20],
        }
        if mismatches:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            raise SystemExit(1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "racket": report["racket"], "by_band": report["by_band"]}))


if __name__ == "__main__":
    main()
