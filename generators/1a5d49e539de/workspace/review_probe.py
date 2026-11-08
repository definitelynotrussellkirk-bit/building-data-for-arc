#!/usr/bin/env python3
"""Source-bound distribution and lesson probe for generator 1a5d49e539de.

Run from a staged runtime or from ``repo`` with ``shared/runtime`` on
``PYTHONPATH``.  The probe deliberately iterates the generator's live semantic
rival declarations so future edits cannot silently leave a copied rival list
stale.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "1a5d49e539de"


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _components8(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    out = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            out.append(cells)
    return out


def _is_lr_symmetric(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    normalized = {(row - row0, col - col0) for row, col in cells}
    width = max(col for _, col in normalized) + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def _target_facts(grid):
    components = _components8(grid)
    target = [i for i, cells in enumerate(components) if not _is_lr_symmetric(cells)]
    if len(target) != 1:
        raise AssertionError(f"expected one target, got {target}")
    index = target[0]
    sizes = [len(cells) for cells in components]
    return index, sum(size < sizes[index] for size in sizes), max(sizes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError:
        source_path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", source_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {source_path}")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
    source = Path(gen.__file__).read_bytes()
    report = {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "version": gen.VERSION,
        "per_band": args.per_band,
        "bands": {},
        "override_cases": 0,
        "override_failures": [],
    }

    for band in ("easy", "medium", "hard"):
        inputs = set()
        outputs = set()
        dimensions = Counter()
        colors = Counter()
        target_indices = Counter()
        target_ranks = Counter()
        max_object_size = 0
        strict = 0
        invalid = []
        ambiguous_windows = []
        rival_refutations = Counter()

        pairs = []
        for sample_index in range(args.per_band + gen.EXAMPLES_NEEDED):
            seed = 150000 + sample_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid)
            if errors:
                invalid.append({"sample_index": sample_index, "errors": errors})
            strict += not gen.strict_canonical_like(grid)
            output = gen.rule_mirror(grid)
            pairs.append({"input": grid, "output": output})
            if sample_index < args.per_band:
                inputs.add(_freeze(grid))
                outputs.add(_freeze(output))
                dimensions[len(grid)] += 1
                colors[next(value for row in grid for value in row if value)] += 1
                target_index, target_rank, local_max = _target_facts(grid)
                target_indices[target_index] += 1
                target_ranks[target_rank] += 1
                max_object_size = max(max_object_size, local_max)

        for start in range(args.per_band):
            demos = pairs[start:start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                ambiguous_windows.append({"start": start, "reasons": reasons})
            for name, rival in gen.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rival_refutations[name] += 1

        report["bands"][band] = {
            "draws": args.per_band,
            "strict_accepted": strict,
            "invalid": invalid,
            "unique_inputs": len(inputs),
            "unique_outputs": len(outputs),
            "dimensions": dict(sorted(dimensions.items())),
            "colors": dict(sorted(colors.items())),
            "target_indices": dict(sorted(target_indices.items())),
            "target_size_ranks": dict(sorted(target_ranks.items())),
            "max_object_size": max_object_size,
            "lesson_windows": args.per_band,
            "ambiguous_windows": ambiguous_windows,
            "rival_refutations": dict(sorted(rival_refutations.items())),
        }

    for band in (None, "easy", "medium", "hard"):
        for grid_size in range(20, 24):
            for color in range(1, 10):
                report["override_cases"] += 1
                try:
                    grid = gen.generate(
                        1701,
                        grid_size * 10 + color,
                        difficulty=band,
                        grid_size=grid_size,
                        color=color,
                    )
                    observed = gen.observe_overrides(grid)
                    expected = {"grid_size": grid_size, "color": color}
                    if observed != expected:
                        report["override_failures"].append(
                            {"band": band, "expected": expected, "observed": observed}
                        )
                except Exception as exc:  # evidence, not concealment
                    report["override_failures"].append(
                        {
                            "band": band,
                            "grid_size": grid_size,
                            "color": color,
                            "exception": repr(exc),
                        }
                    )

    report["passed"] = (
        not report["override_failures"]
        and all(
            not band["invalid"]
            and not band["ambiguous_windows"]
            and band["strict_accepted"] == band["draws"] + gen.EXAMPLES_NEEDED
            and all(value == band["lesson_windows"] for value in band["rival_refutations"].values())
            for band in report["bands"].values()
        )
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "out": str(args.out)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
