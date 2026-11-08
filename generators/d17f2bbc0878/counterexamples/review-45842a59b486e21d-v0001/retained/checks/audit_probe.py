"""Build exact Racket-backed evidence for the two assigned audit targets."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

PACKET = Path(__file__).resolve().parents[1]
ROOT = PACKET / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def canonical(task):
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task:
                return row
    raise KeyError(task)


def load_generator(task):
    path = ROOT / f"generators/{task}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def racket_output(task, grid):
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = canonical(task)
    with tempfile.TemporaryDirectory(prefix=f"audit-{task}-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, task)
        request = {"program": row["program_solution"], "grids": [grid]}
        (stage / "request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket failed: {result}")
        return json.loads(result["stdout"])[0]


def components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def bar_output(grid, *, fixed_bottom=False):
    out = deepcopy(grid)
    sizes = sorted((len(cells) for cells in components(grid, 6)), reverse=True)
    bar = []
    for index, size in enumerate(sizes):
        if index:
            bar.append(0)
        bar.extend([3] * size)
    if fixed_bottom:
        marker_r, marker_c = len(grid) - 1, 0
    else:
        marker_r, marker_c = next(
            (r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2
        )
    for offset, value in enumerate(bar, start=1):
        c = marker_c + offset
        if value == 3 and c < len(grid[0]):
            out[marker_r][c] = 3
    return out


def minority_crop(grid, *, erase_other=False):
    colors = sorted({value for row in grid for value in row if value})
    counts = {color: sum(value == color for row in grid for value in row) for color in colors}
    minority = min(colors, key=lambda color: (counts[color], color))
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == minority]
    r0 = min(r for r, _ in points); r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points); c1 = max(c for _, c in points)
    return [
        [value if (not erase_other or value in (0, minority)) else 0 for value in row[c0:c1 + 1]]
        for row in grid[r0:r1 + 1]
    ]


def diff_count(left, right):
    h = max(len(left), len(right))
    w = max(max((len(row) for row in left), default=0), max((len(row) for row in right), default=0))
    total = 0
    for r in range(h):
        for c in range(w):
            a = left[r][c] if r < len(left) and c < len(left[r]) else None
            b = right[r][c] if r < len(right) and c < len(right[r]) else None
            total += a != b
    return total


def hashes(task, generator_path):
    row = canonical(task)
    normalized = " ".join(row["program_solution"].split())
    return {
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "canonical_rule_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
        "canonical_rule_hash12": hashlib.sha256(normalized.encode()).hexdigest()[:12],
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def audit_116():
    task = "1165179c0d2e"
    module, path = load_generator(task)
    row = canonical(task)
    pairs = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])
    # Pair 1 has repeated sizes 4,4,1 and its marker is at (9,1), not bottom/col0.
    witness = deepcopy(pairs[1]["input"])
    actual = racket_output(task, witness)
    rival = bar_output(witness, fixed_bottom=True)

    sample = {
        "draws": 0,
        "self_check_failures": 0,
        "marker_bottom_col0": 0,
        "distinct_component_sizes": 0,
        "fixed_bottom_rival_matches_independent_rule": 0,
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            seed = 116_517_000 + band_index * 1000 + index
            grid = module.generate(seed, index, difficulty=band)
            sample["draws"] += 1
            sample["self_check_failures"] += bool(module.self_check(grid))
            markers = [(r, c) for r, values in enumerate(grid) for c, value in enumerate(values) if value == 2]
            sample["marker_bottom_col0"] += markers == [(len(grid) - 1, 0)]
            sizes = [len(cells) for cells in components(grid, 6)]
            sample["distinct_component_sizes"] += len(sizes) == len(set(sizes))
            sample["fixed_bottom_rival_matches_independent_rule"] += (
                bar_output(grid, fixed_bottom=True) == bar_output(grid, fixed_bottom=False)
            )

    return {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": "Sampler makes marker location and size uniqueness deterministic, enabling a fixed-bottom-row rival.",
        **hashes(task, path),
        "source": {"kind": "canonical_pair", "pair_index": 1},
        "seed": None,
        "sample_index": None,
        "difficulty": None,
        "overrides": {},
        "input": witness,
        "actual_racket_output": actual,
        "rival_name": "ignore the color-2 marker; always draw the sorted-size bar on the final row starting at column 1",
        "rival_output": rival,
        "differing_cells": diff_count(actual, rival),
        "target_self_check": module.self_check(witness),
        "passes_target_validator": module.self_check(witness) == [],
        "belongs_documented_generated_domain": False,
        "domain_reason": "Canonical marker is not at bottom/column zero and component sizes include a tie (4,4,1).",
        "canonical_profile": {
            "marker": [(r, c) for r, values in enumerate(witness) for c, value in enumerate(values) if value == 2],
            "component_sizes": sorted((len(cells) for cells in components(witness, 6)), reverse=True),
        },
        "actual_sampler_probe": sample,
        "sampling_design": "100 deterministic draws in each of easy, medium and hard; seed=116517000+1000*band_index+i, sample_index=i.",
        "command": ["python3", "run_with_racket.py", "python3", "-B", "../checks/audit_probe.py"],
        "working_directory": "repo (via packet-root run_with_racket.py)",
    }


def audit_d17():
    task = "d17f2bbc0878"
    module, path = load_generator(task)
    row = canonical(task)
    pairs = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])

    witness = [[0] * 10 for _ in range(10)]
    # Minority color 2 defines a 5x5 bbox; majority color 1 has one cell inside
    # that bbox plus seven outside. Authority crops the original grid and must
    # preserve the interior majority cell.
    for r, c in ((2, 2), (2, 6), (6, 2), (6, 6)):
        witness[r][c] = 2
    for r, c in ((0, 0), (0, 1), (0, 2), (4, 4), (8, 8), (8, 9), (9, 8), (9, 9)):
        witness[r][c] = 1
    actual = racket_output(task, witness)
    rival = minority_crop(witness, erase_other=True)

    sample = {
        "draws": 0,
        "self_check_failures": 0,
        "erase_other_rival_matches_independent_rule": 0,
        "outputs_containing_majority_inside_crop": 0,
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            seed = 17_200_000 + band_index * 1000 + index
            grid = module.generate(seed, index, difficulty=band)
            sample["draws"] += 1
            sample["self_check_failures"] += bool(module.self_check(grid))
            intended = minority_crop(grid, erase_other=False)
            erased = minority_crop(grid, erase_other=True)
            sample["erase_other_rival_matches_independent_rule"] += intended == erased
            minority = min(
                {value for row_values in grid for value in row_values if value},
                key=lambda color: sum(value == color for row_values in grid for value in row_values),
            )
            sample["outputs_containing_majority_inside_crop"] += any(
                value not in (0, minority) for row_values in intended for value in row_values
            )

    canonical_errors = [module.self_check(pair["input"]) for pair in pairs]
    return {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": "Validator and sampler forbid overlapping color bboxes, so they cannot teach that crop preserves majority cells inside the minority bbox.",
        **hashes(task, path),
        "source": {"kind": "synthetic_authority-domain_counterexample"},
        "seed": None,
        "sample_index": None,
        "difficulty": None,
        "overrides": {},
        "input": witness,
        "actual_racket_output": actual,
        "rival_name": "erase every non-minority color before cropping to the minority bbox",
        "rival_output": rival,
        "differing_cells": diff_count(actual, rival),
        "target_self_check": module.self_check(witness),
        "passes_target_validator": module.self_check(witness) == [],
        "belongs_documented_generated_domain": False,
        "domain_reason": "The canonical Racket authority permits overlapping color bboxes; generator self_check rejects them.",
        "canonical_self_check_errors": canonical_errors,
        "canonical_inputs_rejected": sum(bool(errors) for errors in canonical_errors),
        "canonical_inputs_total": len(canonical_errors),
        "actual_sampler_probe": sample,
        "sampling_design": "100 deterministic draws in each of easy, medium and hard; seed=17200000+1000*band_index+i, sample_index=i.",
        "command": ["python3", "run_with_racket.py", "python3", "-B", "../checks/audit_probe.py"],
        "working_directory": "repo (via packet-root run_with_racket.py)",
    }


def main():
    reports = [audit_116(), audit_d17()]
    for report in reports:
        out = PACKET / "checks" / f"audit-{report['task_id']}-counterexample.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "task_id": report["task_id"],
            "differing_cells": report["differing_cells"],
            "passes_target_validator": report["passes_target_validator"],
            "sampler": report["actual_sampler_probe"],
            "out": str(out),
        }, indent=2))


if __name__ == "__main__":
    main()
