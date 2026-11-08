"""Exhaust the advertised axes and test five-pair lesson rotations.

This probe is intentionally task-local.  It exercises the public generator,
``self_check``, ``observe_overrides``, and ``lesson_identifiable`` APIs without
consulting private labels or importing runner internals.  It can also load a
saved earlier ``generator.py`` via ``--generator`` for before/after comparison.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path
import sys
import time
from types import ModuleType
from typing import Iterable, Sequence

TASK_ID = "73906110dd67"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_runtime_imports() -> None:
    for path in (REPO_ROOT / "src", REPO_ROOT / "shared" / "runtime"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def load_generator(path: Path) -> ModuleType:
    """Load a generator source file under a hash-derived private module name."""
    _ensure_runtime_imports()
    resolved = path.resolve()
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()[:16]
    spec = spec_from_file_location(f"distribution_probe_{TASK_ID}_{digest}", resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {resolved}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid_sha256(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _generated_pair(generator: ModuleType, seed: int, sample_index: int, band: str) -> dict:
    grid = generator.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": generator.rule_mirror(grid)}


def probe_generator(
    generator: ModuleType,
    *,
    heights: Iterable[int] = range(8, 19),
    widths: Iterable[int] = range(10, 19),
    bands: Iterable[str] = ("easy", "medium", "hard"),
    rotation_starts: Iterable[int] = range(12),
) -> dict:
    """Return exhaustive override and cyclic-lesson diagnostics for ``generator``."""
    started = time.monotonic()
    heights = tuple(heights)
    widths = tuple(widths)
    bands = tuple(bands)
    rotation_starts = tuple(rotation_starts)

    errors: list[dict] = []
    row_support: set[int] = set()
    column_support: set[int] = set()
    foreground_colors: set[int] = set()
    dimensions: set[tuple[int, int]] = set()
    input_hashes: set[str] = set()
    origin_patterns: set[tuple[tuple[int, int], ...]] = set()
    row_count_histogram: Counter[int] = Counter()
    column_count_histogram: Counter[int] = Counter()
    total = 0

    axes = product(
        heights,
        widths,
        (3, 4),
        ("consecutive", "spread"),
        ("ascending", "descending", "zigzag"),
        ("low", "high", "mixed"),
        (2, 3),
    )
    axis_values = tuple(axes)
    for band in bands:
        for h, w, n_blobs, size_pattern, input_order, palette, max_width in axis_values:
            requested = {
                "grid_h": h,
                "grid_w": w,
                "n_blobs": n_blobs,
                "size_pattern": size_pattern,
                "input_size_order": input_order,
                "palette_kind": palette,
                "max_bbox_width": max_width,
            }
            try:
                grid = generator.generate(
                    1729,
                    total,
                    difficulty=band,
                    **requested,
                )
                issues = generator.self_check(grid)
                observed = generator.observe_overrides(grid)
                if issues or observed != requested:
                    raise AssertionError(
                        f"requested={requested!r}, observed={observed!r}, issues={issues!r}"
                    )
                facts = generator.semantic_observables(grid)
                origins = tuple(
                    (component["bbox"][0], component["bbox"][1])
                    for component in facts["components"]
                )
                rows = {row for row, _ in origins}
                columns = {column for _, column in origins}
                row_support.update(rows)
                column_support.update(columns)
                foreground_colors.update(facts["colors"])
                dimensions.add((h, w))
                input_hashes.add(_grid_sha256(grid))
                origin_patterns.add(origins)
                row_count_histogram[len(rows)] += 1
                column_count_histogram[len(columns)] += 1
            except Exception as exc:  # retained in report; probe continues
                errors.append(
                    {
                        "band": band,
                        "sample_index": total,
                        "requested": requested,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            total += 1

    ambiguous: list[dict] = []
    rotation_count = 0
    for band in bands:
        for start in rotation_starts:
            pairs = [
                _generated_pair(generator, 12345, start + offset, band)
                for offset in range(5)
            ]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = generator.lesson_identifiable(demos, query)
                rotation_count += 1
                if reasons:
                    ambiguous.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "query_sample_index": start + query_index,
                            "reasons": reasons,
                        }
                    )

    generator_path = Path(generator.__file__).resolve()
    elapsed = time.monotonic() - started
    return {
        "schema": "73906110dd67-distribution-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "generator_version": getattr(generator, "VERSION", None),
        "override_probe": {
            "bands": list(bands),
            "heights": list(heights),
            "widths": list(widths),
            "cases": total,
            "errors": errors,
            "dimensions": [list(pair) for pair in sorted(dimensions)],
            "dimension_count": len(dimensions),
            "foreground_colors": sorted(foreground_colors),
            "origin_row_support": sorted(row_support),
            "origin_column_support": sorted(column_support),
            "origin_row_count_histogram": {
                str(key): value for key, value in sorted(row_count_histogram.items())
            },
            "origin_column_count_histogram": {
                str(key): value for key, value in sorted(column_count_histogram.items())
            },
            "distinct_origin_patterns": len(origin_patterns),
            "unique_inputs": len(input_hashes),
        },
        "rotation_probe": {
            "starts": list(rotation_starts),
            "windows": len(bands) * len(rotation_starts),
            "rotations": rotation_count,
            "ambiguous_count": len(ambiguous),
            "ambiguous": ambiguous,
        },
        "seconds": elapsed,
        "passed": not errors and not ambiguous,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=TASK_HOME / "generator.py",
        help="generator.py to probe (default: selected implementation)",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="probe only boundary canvas sizes; all other axes and rotations remain",
    )
    args = parser.parse_args(argv)

    generator = load_generator(args.generator)
    heights = (8, 18) if args.quick else range(8, 19)
    widths = (10, 18) if args.quick else range(10, 19)
    report = probe_generator(generator, heights=heights, widths=widths)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    compact = {
        "generator_sha256": report["generator_sha256"],
        "generator_version": report["generator_version"],
        "cases": report["override_probe"]["cases"],
        "override_errors": len(report["override_probe"]["errors"]),
        "colors": report["override_probe"]["foreground_colors"],
        "origin_rows": report["override_probe"]["origin_row_support"],
        "origin_columns": report["override_probe"]["origin_column_support"],
        "origin_patterns": report["override_probe"]["distinct_origin_patterns"],
        "rotations": report["rotation_probe"]["rotations"],
        "ambiguous_rotations": report["rotation_probe"]["ambiguous_count"],
        "passed": report["passed"],
    }
    print(json.dumps(compact, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
