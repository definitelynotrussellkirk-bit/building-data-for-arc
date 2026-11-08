#!/usr/bin/env python3
"""Deterministic morphology/shortcut census for generator 056999828b88.

Examples:
  python3 shape_support_probe.py --generator ../generator.py --out shape_support_after.json
  python3 shape_support_probe.py --generator generator_v4_baseline.py --out shape_support_before.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
REPO_ROOT = WORKSPACE.parents[2]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BANDS = ("easy", "medium", "hard")


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"probe_056999828b88_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shape_text(shape: Any) -> str:
    return ";".join(f"{r},{c}" for r, c in shape)


def _legacy_keys(module) -> set[tuple[tuple[int, int], ...]]:
    declared = getattr(module, "_LEGACY_SHAPE_KEYS", None)
    if declared is not None:
        return set(declared)
    return {
        module._shape_key(shape)
        for shapes in module._SHAPES_BY_SIZE.values()
        for shape in shapes
    }


def _fallback_rivals(module) -> dict[str, Any]:
    candidates = {
        "color_order": "_color_pack",
        "scan_order": "_scan_pack",
        "bbox_area_order": "_bbox_area_pack",
        "bbox_semiperimeter_order": "_bbox_semiperimeter_pack",
        "boundary_perimeter_order": "_boundary_perimeter_pack",
        "adjacency_edges_order": "_adjacency_edges_pack",
        "boundary_cells_order": "_boundary_cells_pack",
        "max_span_shape_order": "_max_span_shape_pack",
        "min_span_shape_order": "_min_span_shape_pack",
        "descending_size": "_descending_size_pack",
        "legacy_shape_lookup": "_legacy_shape_pack",
        "color_union": "_color_union_pack",
        "global_color_frequency": "_global_color_frequency_pack",
    }
    return {
        name: getattr(module, attr)
        for name, attr in candidates.items()
        if hasattr(module, attr)
    }


def run_census(module, *, per_band: int, seed: int) -> dict[str, Any]:
    classes: dict[int, set] = defaultdict(set)
    profiles: Counter[str] = Counter()
    schedule: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    rival_disagreements: Counter[str] = Counter()
    self_check_failures: list[dict[str, Any]] = []
    crashes: list[dict[str, Any]] = []
    legacy = _legacy_keys(module)
    witnesses = getattr(module, "SEMANTIC_WITNESSES", {})
    rivals = getattr(module, "SEMANTIC_RIVALS", None) or _fallback_rivals(module)
    schedule_fn = getattr(module, "schedule_profile", None)
    lesson_rows: dict[str, list[tuple[int, Any, Any]]] = {
        band: [] for band in BANDS
    }
    draws = 0

    for band in BANDS:
        for sample_index in range(per_band):
            try:
                grid = module.generate(seed, sample_index, difficulty=band)
                draws += 1
                errors = module.self_check(grid, difficulty=band)
                if errors and len(self_check_failures) < 20:
                    self_check_failures.append(
                        {"band": band, "sample_index": sample_index, "errors": errors}
                    )
                objects = module._components(grid)
                profile = tuple(sorted(len(obj["cells"]) for obj in objects))
                profiles[str(profile)] += 1
                for obj in objects:
                    size = len(obj["cells"])
                    classes[size].add(module._shape_key(obj["cells"]))
                truth = module._size_pack(grid)
                lesson_rows[band].append((sample_index, grid, truth))
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_hits[name] += 1
                for name, rival in rivals.items():
                    if rival(grid) != truth:
                        rival_disagreements[name] += 1
                if schedule_fn is not None:
                    schedule[str(schedule_fn(seed, sample_index, difficulty=band))] += 1
            except Exception as exc:  # probe must preserve a bounded crash sample
                if len(crashes) < 20:
                    crashes.append(
                        {
                            "band": band,
                            "sample_index": sample_index,
                            "type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )

    n_demos = int(getattr(module, "EXAMPLES_NEEDED", 0) or 0)
    survivor_counts = {name: 0 for name in rivals}
    survivor_examples: dict[str, list[dict[str, Any]]] = {
        name: [] for name in rivals
    }
    lesson_windows = 0
    if n_demos > 0:
        for band in BANDS:
            by_index = {
                sample_index: (grid, truth)
                for sample_index, grid, truth in lesson_rows[band]
            }
            for start in range(max(0, per_band - n_demos + 1)):
                window = [by_index.get(index) for index in range(start, start + n_demos)]
                if any(item is None for item in window):
                    continue
                lesson_windows += 1
                for name, rival in rivals.items():
                    if all(rival(grid) == truth for grid, truth in window):
                        survivor_counts[name] += 1
                        if len(survivor_examples[name]) < 10:
                            survivor_examples[name].append(
                                {"band": band, "start_sample_index": start}
                            )

    override_failures: list[dict[str, Any]] = []
    override_draws = 0
    for band in BANDS:
        for grid_h in (8, 10):
            for grid_w in (10, 12):
                for n_objects in (3, 4):
                    for sample_index in range(4):
                        override_draws += 1
                        try:
                            grid = module.generate(
                                seed + 1,
                                sample_index,
                                difficulty=band,
                                grid_h=grid_h,
                                grid_w=grid_w,
                                n_objects=n_objects,
                            )
                            observed = module.observe_overrides(grid)
                            wanted = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "n_objects": n_objects,
                            }
                            errors = module.self_check(grid, difficulty=band)
                            if observed != wanted or errors:
                                override_failures.append(
                                    {
                                        "band": band,
                                        "sample_index": sample_index,
                                        "wanted": wanted,
                                        "observed": observed,
                                        "errors": errors,
                                    }
                                )
                        except Exception as exc:
                            override_failures.append(
                                {
                                    "band": band,
                                    "sample_index": sample_index,
                                    "wanted": {
                                        "grid_h": grid_h,
                                        "grid_w": grid_w,
                                        "n_objects": n_objects,
                                    },
                                    "type": type(exc).__name__,
                                    "message": str(exc),
                                }
                            )

    classes_json = {
        str(size): sorted(_shape_text(shape) for shape in shapes)
        for size, shapes in sorted(classes.items())
    }
    novel_json = {
        str(size): sorted(_shape_text(shape) for shape in shapes if shape not in legacy)
        for size, shapes in sorted(classes.items())
    }
    return {
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "seed": seed,
        "per_band": per_band,
        "planned_draws": per_band * len(BANDS),
        "draws": draws,
        "crashes": crashes,
        "self_check_failures": self_check_failures,
        "class_counts_by_size": {
            size: len(values) for size, values in classes_json.items()
        },
        "novel_class_counts_by_size": {
            size: len(values) for size, values in novel_json.items()
        },
        "total_class_count": sum(len(values) for values in classes_json.values()),
        "classes_by_size": classes_json,
        "novel_classes_by_size": novel_json,
        "size_profiles": dict(sorted(profiles.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
        "lesson_survival": {
            "n_demos": n_demos,
            "windows": lesson_windows,
            "survivor_counts": dict(sorted(survivor_counts.items())),
            "survivor_examples": {
                name: examples
                for name, examples in sorted(survivor_examples.items())
                if examples
            },
        },
        "schedule_profiles": dict(sorted(schedule.items())),
        "override_matrix": {
            "draws": override_draws,
            "failures": override_failures,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=WORKSPACE.parent / "generator.py",
        help="generator file to census (default: selected ../generator.py)",
    )
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--seed", type=int, default=246810)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    generator_path = args.generator.resolve()
    module = _load(generator_path)
    report = {
        "schema": "056999828b88-shape-support-probe/2",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        **run_census(module, per_band=args.per_band, seed=args.seed),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if not report["crashes"] and not report["self_check_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
