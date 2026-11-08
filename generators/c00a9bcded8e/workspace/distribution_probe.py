"""Independent, reproducible distribution and lesson audit for c00a9bcded8e.

Run from any directory.  The probe does not provide training labels and never
replaces the Racket authority.  It independently extracts solid rectangles,
checks canonical dimension support and spatial-template diversity, scores the
*declared* lesson rivals, and rotates every sample in six-item blocks through
the query position while keeping one demonstration from each schedule slot.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK = "c00a9bcded8e"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: Path | None = None):
    source = (path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_c00a9bcded8e", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def canonical_record() -> dict[str, Any]:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent from {ledger}")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_record()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(tests)


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Independent 4-connected component extraction."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            box_h, box_w = bottom - top + 1, right - left + 1
            found.append(
                {
                    "color": color,
                    "size": len(cells),
                    "top": top,
                    "left": left,
                    "height": box_h,
                    "width": box_w,
                    "area": box_h * box_w,
                    "solid": len(cells) == box_h * box_w,
                    "center_row": (top + bottom) / 2,
                    "center_col": (left + right) / 2,
                }
            )
    return found


def rectangles(grid: list[list[int]]) -> list[dict[str, Any]]:
    return sorted(
        (
            item
            for item in components(grid)
            if item["solid"] and item["area"] >= 9
        ),
        key=lambda item: (item["center_row"], item["center_col"]),
    )


def frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def layout_signature(rects: list[dict[str, Any]]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        (
            int(item["top"]),
            int(item["left"]),
            int(item["height"]),
            int(item["width"]),
        )
        for item in rects
    )


def audit(module, *, per_band: int, seed: int) -> tuple[dict[str, Any], bool]:
    canonical = canonical_pairs()
    canonical_rects = [rectangles(pair["input"]) for pair in canonical]
    canonical_heights = sorted({r["height"] for rows in canonical_rects for r in rows})
    canonical_widths = sorted({r["width"] for rows in canonical_rects for r in rows})

    report: dict[str, Any] = {
        "schema": "c00a9bcded8e-distribution-probe-v1",
        "task_id": TASK,
        "version": module.VERSION,
        "sampling": {
            "bands": ["easy", "medium", "hard"],
            "per_band": per_band,
            "seed_formula": f"{seed} + sample_index",
            "sample_index_range": [0, per_band - 1],
            "production_lesson_policy": "three consecutive demonstrations; following sample is query",
            "cyclic_query_policy": (
                "non-overlapping six-sample blocks; each sample is query once; "
                "the demonstrations are the nearest later sample from each of the three schedule slots"
            ),
        },
        "canonical": {
            "pairs": len(canonical),
            "rectangle_heights": canonical_heights,
            "rectangle_widths": canonical_widths,
        },
        "declared_lesson_competitors": sorted(module.LESSON_COMPETITORS),
        "declared_canonical_shortcuts": sorted(module.CANONICAL_SHORTCUTS),
        "bands": {},
        "failures": [],
    }

    generated_heights: set[int] = set()
    generated_widths: set[int] = set()
    all_layouts: set[tuple[tuple[int, ...], ...]] = set()
    all_inputs: set[tuple[tuple[int, ...], ...]] = set()

    shortcut_fit = {}
    for name, shortcut in module.CANONICAL_SHORTCUTS.items():
        fits = [shortcut(pair["input"]) == pair["output"] for pair in canonical]
        shortcut_fit[name] = {"pair_matches": fits, "fits_all": all(fits)}
        if not all(fits):
            report["failures"].append(
                f"declared canonical shortcut {name!r} does not fit every canonical pair"
            )
    report["canonical_shortcut_fit"] = shortcut_fit

    for band in ("easy", "medium", "hard"):
        grids: list[list[list[int]]] = []
        outputs: list[list[list[int]]] = []
        layouts: set[tuple[tuple[int, ...], ...]] = set()
        inputs: set[tuple[tuple[int, ...], ...]] = set()
        heights: set[int] = set()
        widths: set[int] = set()
        rivals = Counter()
        self_check_failures: list[dict[str, Any]] = []
        nondeterministic: list[int] = []
        rectangle_count_failures: list[dict[str, Any]] = []

        for sample_index in range(per_band):
            sample_seed = seed + sample_index
            grid = module.generate(sample_seed, sample_index, difficulty=band)
            replay = module.generate(sample_seed, sample_index, difficulty=band)
            if grid != replay:
                nondeterministic.append(sample_index)
            issues = module.self_check(grid, difficulty=band)
            if issues:
                self_check_failures.append({"sample_index": sample_index, "issues": issues})
            rects = rectangles(grid)
            expected_count = 3 * (2 + sample_index % 3)
            if len(rects) != expected_count:
                rectangle_count_failures.append(
                    {
                        "sample_index": sample_index,
                        "expected": expected_count,
                        "observed": len(rects),
                    }
                )
            signature = layout_signature(rects)
            layouts.add(signature)
            inputs.add(frozen(grid))
            heights.update(int(r["height"]) for r in rects)
            widths.update(int(r["width"]) for r in rects)
            output = module.rule_mirror(grid)
            for name, rival in module.LESSON_COMPETITORS.items():
                rivals[name] += int(rival(grid) != output)
            grids.append(grid)
            outputs.append(output)

        production_failures = []
        for start in range(max(0, per_band - module.EXAMPLES_NEEDED)):
            demo_indices = list(range(start, start + module.EXAMPLES_NEEDED))
            query_index = start + module.EXAMPLES_NEEDED
            demos = [
                {"input": grids[i], "output": outputs[i]}
                for i in demo_indices
            ]
            query = {"input": grids[query_index], "output": outputs[query_index]}
            reasons = module.lesson_identifiable(demos, query)
            if reasons:
                production_failures.append(
                    {
                        "start": start,
                        "demo_indices": demo_indices,
                        "query_index": query_index,
                        "reasons": reasons,
                    }
                )

        cyclic_failures = []
        cyclic_checked = 0
        for block_start in range(0, per_band - 5, 6):
            block = list(range(block_start, block_start + 6))
            for query_index in block:
                demo_indices = []
                for slot in range(3):
                    candidates = [
                        index
                        for index in block
                        if index != query_index and index % 3 == slot
                    ]
                    # Select cyclically after the query where possible so both
                    # copies of each slot are exercised across query rotations.
                    candidates.sort(key=lambda index: ((index - query_index) % 6, index))
                    demo_indices.append(candidates[0])
                demos = [
                    {"input": grids[i], "output": outputs[i]}
                    for i in demo_indices
                ]
                query = {"input": grids[query_index], "output": outputs[query_index]}
                reasons = module.lesson_identifiable(demos, query)
                cyclic_checked += 1
                if reasons:
                    cyclic_failures.append(
                        {
                            "block_start": block_start,
                            "demo_indices": demo_indices,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

        band_report = {
            "samples": per_band,
            "distinct_inputs": len(inputs),
            "distinct_layouts": len(layouts),
            "rectangle_heights": sorted(heights),
            "rectangle_widths": sorted(widths),
            "rival_disagreements": dict(sorted(rivals.items())),
            "self_check_failures": self_check_failures,
            "nondeterministic_indices": nondeterministic,
            "rectangle_count_failures": rectangle_count_failures,
            "production_lessons_checked": max(0, per_band - module.EXAMPLES_NEEDED),
            "production_lesson_failures": production_failures,
            "cyclic_queries_checked": cyclic_checked,
            "cyclic_query_failures": cyclic_failures,
        }
        report["bands"][band] = band_report

        generated_heights.update(heights)
        generated_widths.update(widths)
        all_layouts.update(layouts)
        all_inputs.update(inputs)

        for label, failures in (
            ("self-check", self_check_failures),
            ("determinism", nondeterministic),
            ("rectangle-count", rectangle_count_failures),
            ("production lesson", production_failures),
            ("cyclic query", cyclic_failures),
        ):
            if failures:
                report["failures"].append(f"{band}: {label} failures={len(failures)}")

    missing_heights = sorted(set(canonical_heights) - generated_heights)
    missing_widths = sorted(set(canonical_widths) - generated_widths)
    if missing_heights:
        report["failures"].append(f"missing canonical rectangle heights: {missing_heights}")
    if missing_widths:
        report["failures"].append(f"missing canonical rectangle widths: {missing_widths}")

    report["pooled"] = {
        "samples": 3 * per_band,
        "distinct_inputs": len(all_inputs),
        "distinct_layouts": len(all_layouts),
        "rectangle_heights": sorted(generated_heights),
        "rectangle_widths": sorted(generated_widths),
        "missing_canonical_heights": missing_heights,
        "missing_canonical_widths": missing_widths,
    }
    report["passed"] = not report["failures"]
    return report, report["passed"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=4400)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 6:
        parser.error("--per-band must be at least 6")

    module, source = load_generator(args.generator)
    report, passed = audit(module, per_band=args.per_band, seed=args.seed)
    report["generator_path"] = str(source)
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "generator_sha256": report["generator_sha256"],
                "canonical": report["canonical"],
                "pooled": report["pooled"],
                "bands": {
                    band: {
                        "samples": details["samples"],
                        "distinct_layouts": details["distinct_layouts"],
                        "production_lesson_failures": len(details["production_lesson_failures"]),
                        "cyclic_query_failures": len(details["cyclic_query_failures"]),
                        "rival_disagreements": details["rival_disagreements"],
                    }
                    for band, details in report["bands"].items()
                },
                "failures": report["failures"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
