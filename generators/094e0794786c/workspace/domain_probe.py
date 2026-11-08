"""Exhaustive declared-domain probe for generator 094e0794786c.

Run from the packet root with:

    python3 review.py run python3 generators/094e0794786c/workspace/domain_probe.py \
        --out ../checks/domain-probe.json

The probe is deliberately independent of the Racket labels. It checks that every
advertised exact axis combination constructs a lawful, exactly observable input,
and records the finite polyomino-bank support used by the selected generator.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def analyze(generator):
    shape_bank_sizes = {
        str(size): len(generator._polyominoes(size))
        for size in range(3, 8)
    }
    pair_support = {}
    all_size_pairs_have_distinguishing_shapes = True
    for n_cells_1 in range(3, 8):
        first_bank = generator._polyominoes(n_cells_1)
        for n_cells_2 in range(3, 8):
            second_bank = generator._polyominoes(n_cells_2)
            compatible_first = sum(
                any(
                    generator._distinguishes_shortcuts(first, second)
                    for second in second_bank
                )
                for first in first_bank
            )
            key = f"{n_cells_1}x{n_cells_2}"
            pair_support[key] = {
                "first_bank": len(first_bank),
                "second_bank": len(second_bank),
                "compatible_first_shapes": compatible_first,
            }
            if compatible_first == 0:
                all_size_pairs_have_distinguishing_shapes = False

    failures = []
    cases = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for grid_h in range(8, 13):
            for grid_w in range(9, 15):
                for n_cells_1 in range(3, 8):
                    for n_cells_2 in range(3, 8):
                        cases += 1
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_cells_1": n_cells_1,
                            "n_cells_2": n_cells_2,
                        }
                        try:
                            grid = generator.generate(
                                941_079 + cases,
                                cases,
                                difficulty=difficulty,
                                **requested,
                            )
                            observed = generator.observe_overrides(grid)
                            findings = generator.self_check(grid)
                        except Exception as exc:  # evidence, not a hidden retry
                            failures.append(
                                {
                                    "difficulty": difficulty,
                                    "requested": requested,
                                    "exception": f"{type(exc).__name__}: {exc}",
                                }
                            )
                            continue
                        if observed != requested or findings:
                            failures.append(
                                {
                                    "difficulty": difficulty,
                                    "requested": requested,
                                    "observed": observed,
                                    "self_check": findings,
                                }
                            )

    return {
        "schema": "094e0794786c-domain-probe-v1",
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "shape_bank_sizes": shape_bank_sizes,
        "size_pair_support": pair_support,
        "all_size_pairs_have_distinguishing_shapes": (
            all_size_pairs_have_distinguishing_shapes
        ),
        "axis_cases": cases,
        "axis_failures": failures,
    }


def _load_selected_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("selected_094e0794786c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = analyze(_load_selected_generator())
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    raise SystemExit(1 if report["axis_failures"] else 0)


if __name__ == "__main__":
    main()
