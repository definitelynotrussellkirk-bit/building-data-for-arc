#!/usr/bin/env python3
"""Exhaustively probe four-pair lesson windows under every query rotation.

This is a task-local diagnostic, not the selected generator.  It loads the
adjacent ``generator.py`` directly, enumerates overlapping windows for each
band/seed, and checks the three documented teaching rivals independently of the
generator's ``lesson_identifiable`` hook:

* fixed border color;
* fixed output dimensions;
* a centered-marker-only gate.

The hook result is also compared with the independent result so hook drift is
visible.  Exit status is nonzero when any window/rotation fails.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "5ee8de1860a7"
BANDS = ("easy", "medium", "hard")


def _load_generator():
    script = Path(__file__).resolve()
    task_dir = script.parent.parent
    repo_root = task_dir.parent.parent
    runtime = repo_root / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    source = task_dir / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"rotation_probe_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _marker(grid: list[list[int]]) -> tuple[int, int, int]:
    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(cells) != 1:
        raise ValueError(f"expected one marker, found {len(cells)}")
    return cells[0]


def _border_output(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    color = _marker(grid)[2]
    return [
        [
            color
            if row in (0, height - 1) or col in (0, width - 1)
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def _independent_reasons(
    demos: list[dict[str, Any]], query: dict[str, Any]
) -> list[str]:
    demo_facts = []
    for pair in demos:
        grid = pair["input"]
        row, col, color = _marker(grid)
        demo_facts.append((len(grid), len(grid[0]), row, col, color))
    q_grid = query["input"]
    q_row, q_col, q_color = _marker(q_grid)
    q_height, q_width = len(q_grid), len(q_grid[0])

    reasons = []
    colors = {color for _, _, _, _, color in demo_facts}
    if len(colors) == 1 and q_color not in colors:
        reasons.append("fixed_color")
    dimensions = {(height, width) for height, width, _, _, _ in demo_facts}
    if len(dimensions) == 1 and (q_height, q_width) not in dimensions:
        reasons.append("fixed_dimensions")
    demos_centered = all(
        (row, col) == (height // 2, width // 2)
        for height, width, row, col, _ in demo_facts
    )
    if demos_centered and (q_row, q_col) != (q_height // 2, q_width // 2):
        reasons.append("center_only")
    return reasons


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--windows", type=int, default=201)
    parser.add_argument("--max-failures", type=int, default=100)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.seeds < 1 or args.windows < 1 or args.max_failures < 1:
        raise SystemExit("--seeds, --windows, and --max-failures must be positive")

    generator, source = _load_generator()
    failures: list[dict[str, Any]] = []
    windows_checked = 0
    rotations_checked = 0
    unique_inputs: set[str] = set()

    for band in BANDS:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            grids = [
                generator.generate(seed, sample_index, difficulty=band)
                for sample_index in range(
                    args.sample_start,
                    args.sample_start + args.windows + 3,
                )
            ]
            pairs = [
                {"input": grid, "output": _border_output(grid)} for grid in grids
            ]
            for grid in grids:
                payload = json.dumps(grid, separators=(",", ":")).encode()
                unique_inputs.add(hashlib.sha256(payload).hexdigest())

            for offset in range(args.windows):
                window = pairs[offset : offset + 4]
                sample_index = args.sample_start + offset
                windows_checked += 1
                for query_index, query in enumerate(window):
                    demos = [
                        pair for index, pair in enumerate(window) if index != query_index
                    ]
                    rotations_checked += 1
                    independent = _independent_reasons(demos, query)
                    hook = generator.lesson_identifiable(demos, query)
                    if independent or hook:
                        failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "query_index": query_index,
                                "independent_reasons": independent,
                                "hook_reasons": hook,
                                "inputs": [pair["input"] for pair in window],
                            }
                        )
                        if len(failures) >= args.max_failures:
                            break
                if len(failures) >= args.max_failures:
                    break
            if len(failures) >= args.max_failures:
                break
        if len(failures) >= args.max_failures:
            break

    report = {
        "schema": "5ee8de1860a7-rotation-window-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "settings": {
            "bands": list(BANDS),
            "seed_start": args.seed_start,
            "seeds": args.seeds,
            "sample_start": args.sample_start,
            "windows_per_seed_band": args.windows,
            "query_policy": "all four rotations",
        },
        "windows_checked": windows_checked,
        "rotations_checked": rotations_checked,
        "unique_inputs": len(unique_inputs),
        "failure_count": len(failures),
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limitations": [
            "Finite seed/sample census, not a proof over every integer seed.",
            "Checks the three documented lesson competitors only.",
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
