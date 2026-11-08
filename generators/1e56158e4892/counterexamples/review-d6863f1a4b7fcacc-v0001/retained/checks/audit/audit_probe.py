#!/usr/bin/env python3
"""Reproduce the two assigned audit findings without private runner imports.

Usage:
  python3 checks/audit/audit_probe.py prepare
  # run the supported `arcpuzzles apply` commands printed by prepare
  python3 checks/audit/audit_probe.py finalize
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
AUDIT = PACKET / "checks" / "audit"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def apply_canonical_code(grid: list[list[int]], code: int) -> list[list[int]]:
    return {
        1: rotate_cw,
        2: rotate_180,
        3: flip_lr,
        4: transpose,
    }.get(code, lambda x: x)(grid)


def apply_misdocumented_code(grid: list[list[int]], code: int) -> list[list[int]]:
    # The audited generator's SUMMARY claims this mapping.
    return {
        1: lambda x: x,
        2: rotate_cw,
        3: rotate_180,
        4: lambda x: rotate_cw(rotate_180(x)),
    }.get(code, lambda x: x)(grid)


def gallery(grids: list[list[list[int]]]) -> list[list[int]]:
    h = max(len(g) for g in grids)
    w = sum(len(g[0]) for g in grids) + len(grids) - 1
    out = [[0] * w for _ in range(h)]
    left = 0
    for grid in grids:
        top = (h - len(grid)) // 2
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(grid[0]) + 1
    return out


def a4_input() -> list[list[int]]:
    grid = [[0] * 11 for _ in range(8)]
    grid[0][1] = 2
    grid[0][7] = 2
    for r, c in [(3, 3), (4, 3), (5, 3), (5, 4)]:
        grid[r][c] = 8
    return grid


def a4_rivals(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    codes = [v for v in grid[0] if v in (1, 2, 3, 4)]
    object_grid = [row[:] for row in grid]
    object_grid[0] = [0] * len(object_grid[0])
    base = crop_nonzero(object_grid)
    return {
        "independent_from_base_with_canonical_code_mapping": gallery(
            [apply_canonical_code(base, code) for code in codes]
        ),
        "generator_summary_claim_independent_with_documented_mapping": gallery(
            [apply_misdocumented_code(base, code) for code in codes]
        ),
    }


PANEL_STARTS = (0, 6, 12, 18)


def norm_panel(panel: list[list[int]]) -> tuple[tuple[int, int], ...]:
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value]
    if not cells:
        return tuple()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def count_shortcut(grid: list[list[int]]) -> list[list[int]]:
    panels = [[row[c0 : c0 + 5] for row in grid[:5]] for c0 in PANEL_STARTS]
    norms = [norm_panel(panel) for panel in panels]
    counts = [len(shape) for shape in norms]
    return [
        [
            8 if i == j else 1 if norms[i] == norms[j] else 2 if counts[i] == counts[j] else 0
            for j in range(4)
        ]
        for i in range(4)
    ]


def relation_counterexample() -> list[list[int]]:
    grid = [[0] * 23 for _ in range(5)]
    patterns = [
        # L tetromino
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        # A nontrivial rotation of the same L tetromino
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        # T tetromino: same cell count but not rotation-equivalent to L
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        # P-like pentomino, giving a third class and a different count
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
    ]
    for c0, color, pattern in zip(PANEL_STARTS, (1, 2, 3, 4), patterns):
        for r, c in pattern:
            grid[r][c0 + c] = color
    return grid


def documented_domain_a4(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    codes = [(c, value) for c, value in enumerate(grid[0]) if value]
    motif = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c]]
    return (
        8 <= h <= 10
        and 11 <= w <= 14
        and 1 <= len(codes) <= 4
        and all(1 <= value <= 4 for _, value in codes)
        and all(value == 0 for value in grid[1])
        and 3 <= len(motif) <= 5
        and len({grid[r][c] for r, c in motif}) == 1
    )


def documented_domain_1e(grid: list[list[int]]) -> bool:
    if len(grid) != 5 or any(len(row) != 23 for row in grid):
        return False
    colors: list[int] = []
    for c0 in PANEL_STARTS:
        values = [grid[r][c] for r in range(5) for c in range(c0, c0 + 5) if grid[r][c]]
        if not (3 <= len(values) <= 7) or len(set(values)) != 1:
            return False
        colors.append(values[0])
    return len(set(colors)) == 4


def prepare() -> None:
    a4 = AUDIT / "a4dabc2e7822"
    one = AUDIT / "1e56158e4892"
    a4.mkdir(parents=True, exist_ok=True)
    one.mkdir(parents=True, exist_ok=True)

    write_json(a4 / "input.json", {"input": a4_input()})
    write_json(one / "input.json", {"input": relation_counterexample()})

    module = load_generator("1e56158e4892")
    seeds = list(range(42000, 42064))
    generated = [module.generate(seed, 0) for seed in seeds]
    write_json(one / "generated64-input.json", {"inputs": generated})
    write_json(
        one / "generated64-replay.json",
        {
            "task_id": "1e56158e4892",
            "seed_start": seeds[0],
            "seed_end_inclusive": seeds[-1],
            "sample_index": 0,
            "difficulty": None,
            "overrides": {},
            "n_inputs": len(generated),
            "generator_sha256": sha256(REPO / "generators/1e56158e4892/generator.py"),
        },
    )
    print("Prepared inputs. Run from packet_root:")
    print("python3 run_with_racket.py python3 -m arcpuzzles apply a4dabc2e7822 --input ../checks/audit/a4dabc2e7822/input.json --out ../checks/audit/a4dabc2e7822/racket.json")
    print("python3 run_with_racket.py python3 -m arcpuzzles apply 1e56158e4892 --input ../checks/audit/1e56158e4892/input.json --out ../checks/audit/1e56158e4892/racket.json")
    print("python3 run_with_racket.py python3 -m arcpuzzles apply 1e56158e4892 --input ../checks/audit/1e56158e4892/generated64-input.json --out ../checks/audit/1e56158e4892/generated64-racket.json")


def validator_result(task_id: str, grid: list[list[int]]) -> list[str]:
    module = load_generator(task_id)
    return list(module.self_check(grid))


def finalize() -> None:
    a4_dir = AUDIT / "a4dabc2e7822"
    one_dir = AUDIT / "1e56158e4892"

    a4_apply = read_json(a4_dir / "racket.json")
    a4_grid = a4_apply["results"][0]["input"]
    a4_actual = a4_apply["results"][0]["output"]
    a4_competitors = a4_rivals(a4_grid)
    a4_evidence = {
        "task_id": "a4dabc2e7822",
        "finding": "The authority applies the script cumulatively, but the generator SUMMARY teaches independent transforms and also gives the wrong code mapping.",
        "generator_sha256": a4_apply["generator_sha256"],
        "executed_rule_hash": a4_apply["executed_rule_hash"],
        "seed": None,
        "sample_index": None,
        "overrides": None,
        "input": a4_grid,
        "actual_racket_output": a4_actual,
        "rival_outputs": a4_competitors,
        "actual_differs_from_independent_rival": a4_actual != a4_competitors["independent_from_base_with_canonical_code_mapping"],
        "actual_differs_from_generator_summary_claim": a4_actual != a4_competitors["generator_summary_claim_independent_with_documented_mapping"],
        "validator_errors": validator_result("a4dabc2e7822", a4_grid),
        "passes_validator": validator_result("a4dabc2e7822", a4_grid) == [],
        "belongs_to_documented_generator_domain": documented_domain_a4(a4_grid),
        "racket_apply_command": a4_apply["command"],
        "racket_apply_cwd": a4_apply["cwd"],
        "source": "checks/audit/a4dabc2e7822/racket.json",
    }
    write_json(a4_dir / "counterexample.json", a4_evidence)

    one_apply = read_json(one_dir / "racket.json")
    one_grid = one_apply["results"][0]["input"]
    one_actual = one_apply["results"][0]["output"]
    one_rival = count_shortcut(one_grid)
    one_evidence = {
        "task_id": "1e56158e4892",
        "finding": "Distinct rotation classes are assigned distinct cell counts, so cell count plus exact equality solves generated outputs without learning rotation equivalence.",
        "generator_sha256": one_apply["generator_sha256"],
        "executed_rule_hash": one_apply["executed_rule_hash"],
        "seed": None,
        "sample_index": None,
        "overrides": None,
        "input": one_grid,
        "actual_racket_output": one_actual,
        "rival_output": one_rival,
        "actual_differs_from_rival": one_actual != one_rival,
        "validator_errors": validator_result("1e56158e4892", one_grid),
        "passes_validator": validator_result("1e56158e4892", one_grid) == [],
        "belongs_to_documented_generator_domain": documented_domain_1e(one_grid),
        "racket_apply_command": one_apply["command"],
        "racket_apply_cwd": one_apply["cwd"],
        "source": "checks/audit/1e56158e4892/racket.json",
    }
    write_json(one_dir / "counterexample.json", one_evidence)

    batch_apply = read_json(one_dir / "generated64-racket.json")
    records = []
    fit = 0
    validator_pass = 0
    documented_pass = 0
    for idx, result in enumerate(batch_apply["results"]):
        rival = count_shortcut(result["input"])
        matches = rival == result["output"]
        errors = validator_result("1e56158e4892", result["input"])
        in_domain = documented_domain_1e(result["input"])
        fit += int(matches)
        validator_pass += int(not errors)
        documented_pass += int(in_domain)
        records.append(
            {
                "index": idx,
                "seed": 42000 + idx,
                "sample_index": 0,
                "rival_matches_racket": matches,
                "validator_errors": errors,
                "belongs_to_documented_generator_domain": in_domain,
                "input_sha256": result["input_sha256"],
                "output_sha256": result["output_sha256"],
            }
        )
    summary = {
        "task_id": "1e56158e4892",
        "generator_sha256": batch_apply["generator_sha256"],
        "executed_rule_hash": batch_apply["executed_rule_hash"],
        "probe": "cell-count plus exact-orientation rival",
        "seed_start": 42000,
        "seed_end_inclusive": 42063,
        "sample_index": 0,
        "difficulty": None,
        "overrides": {},
        "n_inputs": len(records),
        "rival_fit_count": fit,
        "rival_fit_fraction": fit / len(records),
        "validator_pass_count": validator_pass,
        "documented_domain_count": documented_pass,
        "records": records,
        "racket_apply_command": batch_apply["command"],
        "racket_apply_cwd": batch_apply["cwd"],
        "source": "checks/audit/1e56158e4892/generated64-racket.json",
    }
    write_json(one_dir / "generated64-summary.json", summary)

    print(json.dumps({
        "a4_counterexample": a4_evidence["actual_differs_from_independent_rival"],
        "a4_validator_pass": a4_evidence["passes_validator"],
        "1e_counterexample": one_evidence["actual_differs_from_rival"],
        "1e_validator_pass": one_evidence["passes_validator"],
        "1e_generated_rival_fit": f"{fit}/{len(records)}",
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "finalize"))
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    else:
        finalize()


if __name__ == "__main__":
    main()
