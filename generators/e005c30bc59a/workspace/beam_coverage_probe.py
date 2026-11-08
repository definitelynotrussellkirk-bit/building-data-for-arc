#!/usr/bin/env python3
"""Measure whether laser-generator draws actually teach the canonical semantics.

The probe is deliberately independent of a generator's private analysis helper for
basic route metrics, so it can compare old and new sources.  When a candidate
module declares CANONICAL_SHORTCUTS, LESSON_COMPETITORS, SEMANTIC_WITNESSES and
rule_mirror, the probe also exercises those *actual declarations* rather than a
copied rival-name list.

Example (from repo/):
  PYTHONPATH=shared/runtime python3 generators/e005c30bc59a/workspace/beam_coverage_probe.py \
    --module before=generators/e005c30bc59a/workspace/baseline_generator.py \
    --module final=generators/e005c30bc59a/generator.py \
    --canonical shared/data/canonical/puzzles.jsonl \
    --task-id e005c30bc59a --samples-per-band 256 \
    --out ../checks/beam_coverage_before_after.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

SOURCE_COLORS = {3, 4, 6, 7, 8, 9}
DIFFICULTIES = ("easy", "medium", "hard")


def load_module(label: str, path: Path):
    spec = importlib.util.spec_from_file_location(f"beam_probe_{label}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inward(source: tuple[int, int], h: int, w: int):
    r, c = source
    if r == 0 and c not in (0, w - 1):
        return "top", (1, 0), False
    if r == h - 1 and c not in (0, w - 1):
        return "bottom", (-1, 0), False
    if c == 0 and r not in (0, h - 1):
        return "left", (0, 1), False
    if c == w - 1 and r not in (0, h - 1):
        return "right", (0, -1), False
    if r in (0, h - 1) and c in (0, w - 1):
        return "corner", None, True
    return "interior", None, False


def bounce(direction: tuple[int, int], kind: int) -> tuple[int, int]:
    dr, dc = direction
    if kind == 1:  # slash
        return (-dc, -dr)
    if kind == 2:  # backslash
        return (dc, dr)
    raise ValueError(kind)


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    sources = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in SOURCE_COLORS
    ]
    mirrors = {
        (r, c): value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2)
    }
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    base = {
        "h": h,
        "w": w,
        "source_count": len(sources),
        "mirror_count": len(mirrors),
        "wall_count": len(walls),
        "source_color": sources[0][2] if len(sources) == 1 else None,
        "source_edge": None,
        "corner_source": False,
        "hit_mirrors": [],
        "path": [],
        "termination": "invalid_source",
        "loop": False,
    }
    if len(sources) != 1 or not h or not w:
        return base
    sr, sc, _ = sources[0]
    edge, direction, corner = inward((sr, sc), h, w)
    base["source_edge"] = edge
    base["corner_source"] = corner
    if direction is None:
        return base
    r, c = sr + direction[0], sc + direction[1]
    states: set[tuple[int, int, int, int]] = set()
    for _ in range(5 * h * w + 8):
        if not (0 <= r < h and 0 <= c < w):
            base["termination"] = "boundary"
            break
        state = (r, c, direction[0], direction[1])
        if state in states:
            base["termination"] = "loop"
            base["loop"] = True
            break
        states.add(state)
        value = grid[r][c]
        if value == 0:
            base["path"].append((r, c))
        elif value == 5:
            base["termination"] = "wall"
            break
        elif value in (1, 2):
            base["hit_mirrors"].append((r, c, value))
            direction = bounce(direction, value)
        else:
            base["termination"] = f"unexpected_{value}"
            break
        r += direction[0]
        c += direction[1]
    else:
        base["termination"] = "fuel"
    return base


def summarize_draws(records: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [record for record in records if "error" not in record]
    analyses = [record["analysis"] for record in successful]
    denom = len(records)
    ok = len(successful)

    def count(predicate: Callable[[dict[str, Any]], bool]) -> int:
        return sum(bool(predicate(a)) for a in analyses)

    def rate(n: int) -> float | None:
        return round(n / ok, 6) if ok else None

    hit_counts = [len(a["hit_mirrors"]) for a in analyses]
    path_lengths = [len(a["path"]) for a in analyses]
    metrics = {
        "requested_draws": denom,
        "successful_draws": ok,
        "generation_errors": denom - ok,
        "unique_inputs": len({record["grid_json"] for record in successful}),
        "corner_source": count(lambda a: a["corner_source"]),
        "non_7_source": count(lambda a: a["source_color"] != 7),
        "hit_any_mirror": count(lambda a: len(a["hit_mirrors"]) >= 1),
        "hit_at_least_two_mirrors": count(lambda a: len(a["hit_mirrors"]) >= 2),
        "hit_both_mirror_kinds": count(
            lambda a: {item[2] for item in a["hit_mirrors"]} == {1, 2}
        ),
        "wall_termination": count(lambda a: a["termination"] == "wall"),
        "boundary_termination": count(lambda a: a["termination"] == "boundary"),
        "loop_termination": count(lambda a: a["termination"] == "loop"),
        "source_edges": dict(sorted(Counter(a["source_edge"] for a in analyses).items())),
        "source_colors": dict(
            sorted(Counter(str(a["source_color"]) for a in analyses).items())
        ),
        "terminations": dict(sorted(Counter(a["termination"] for a in analyses).items())),
        "hit_mirror_count": dict(sorted(Counter(hit_counts).items())),
        "path_length": {
            "min": min(path_lengths) if path_lengths else None,
            "median": statistics.median(path_lengths) if path_lengths else None,
            "max": max(path_lengths) if path_lengths else None,
        },
    }
    for key in (
        "corner_source",
        "non_7_source",
        "hit_any_mirror",
        "hit_at_least_two_mirrors",
        "hit_both_mirror_kinds",
        "wall_termination",
        "boundary_termination",
        "loop_termination",
    ):
        metrics[key + "_rate_of_successful"] = rate(metrics[key])
    if denom != ok:
        metrics["first_generation_errors"] = [
            {k: record[k] for k in ("difficulty", "sample_index", "error")}
            for record in records
            if "error" in record
        ][:10]
    return metrics


def load_canonical(path: Path, task_id: str) -> dict[str, Any]:
    with path.open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(f"task {task_id} not found in {path}")


def declared_semantics(module, grids_by_band, canonical_row):
    result: dict[str, Any] = {}
    rule = getattr(module, "rule_mirror", None)
    competitors = getattr(module, "LESSON_COMPETITORS", None)
    shortcuts = getattr(module, "CANONICAL_SHORTCUTS", None)
    witnesses = getattr(module, "SEMANTIC_WITNESSES", None)
    if not callable(rule) or not isinstance(competitors, dict):
        return result

    if isinstance(shortcuts, dict) and canonical_row is not None:
        usable_pairs = [*canonical_row.get("train", [])]
        shortcut_results = {}
        for name, rival in shortcuts.items():
            fits = []
            errors = []
            for pair_index, pair in enumerate(usable_pairs):
                try:
                    fits.append(rival(pair["input"]) == pair["output"])
                except Exception as exc:  # retained as evidence, not hidden
                    fits.append(False)
                    errors.append({"pair": pair_index, "error": repr(exc)})
            shortcut_results[name] = {
                "canonical_pairs": len(usable_pairs),
                "fits_all": bool(fits) and all(fits),
                "fits_each": fits,
                "errors": errors,
            }
        result["canonical_shortcuts"] = shortcut_results

    witness_report = {}
    if isinstance(witnesses, dict):
        for band, grids in grids_by_band.items():
            witness_report[band] = {
                name: {
                    "count": sum(bool(predicate(grid)) for grid in grids),
                    "denominator": len(grids),
                }
                for name, predicate in witnesses.items()
            }
    result["semantic_witnesses"] = witness_report

    lessons = {}
    for band, grids in grids_by_band.items():
        outputs = [rule(grid) for grid in grids]
        n = len(grids)
        windows = []
        if n >= 4:
            # Cyclic starts make the result independent of where a lesson assembler
            # begins in the deterministic schedule.  The caller should choose a
            # sample count divisible by EXAMPLES_NEEDED for the cleanest check.
            for start in range(n):
                indices = [(start + offset) % n for offset in range(4)]
                surviving = []
                for name, rival in competitors.items():
                    if all(rival(grids[i]) == outputs[i] for i in indices):
                        surviving.append(name)
                windows.append({"start": start, "indices": indices, "surviving": surviving})
        failures = [window for window in windows if window["surviving"]]
        lessons[band] = {
            "policy": "all cyclic windows of four consecutive generated examples",
            "window_count": len(windows),
            "all_competitors_refuted": not failures and bool(windows),
            "failed_window_count": len(failures),
            "first_failed_windows": failures[:10],
        }
    result["lesson_windows"] = lessons
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        action="append",
        required=True,
        metavar="LABEL=PATH",
        help="generator module to sample; repeatable",
    )
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--task-id", default="e005c30bc59a")
    parser.add_argument("--samples-per-band", type=int, default=256)
    parser.add_argument("--seed", default="beam-coverage-probe-v1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples_per_band < 4:
        parser.error("--samples-per-band must be at least 4")

    canonical_row = load_canonical(args.canonical, args.task_id) if args.canonical else None
    report: dict[str, Any] = {
        "schema": "beam-coverage-probe-v1",
        "task_id": args.task_id,
        "seed": args.seed,
        "sample_indices_per_band": [0, args.samples_per_band - 1],
        "samples_per_band": args.samples_per_band,
        "difficulties": list(DIFFICULTIES),
        "modules": {},
    }

    for module_arg in args.module:
        if "=" not in module_arg:
            parser.error(f"module must be LABEL=PATH, got {module_arg!r}")
        label, raw_path = module_arg.split("=", 1)
        path = Path(raw_path).resolve()
        module = load_module(label, path)
        all_records = []
        grids_by_band: dict[str, list[list[list[int]]]] = {}
        band_reports = {}
        for difficulty in DIFFICULTIES:
            records = []
            grids = []
            for sample_index in range(args.samples_per_band):
                try:
                    grid = module.generate(args.seed, sample_index, difficulty=difficulty)
                    analysis = analyze(grid)
                    records.append(
                        {
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "analysis": analysis,
                            "grid_json": json.dumps(grid, separators=(",", ":")),
                        }
                    )
                    grids.append(grid)
                except Exception as exc:
                    records.append(
                        {
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "error": repr(exc),
                        }
                    )
            grids_by_band[difficulty] = grids
            band_reports[difficulty] = summarize_draws(records)
            all_records.extend(records)
        module_report = {
            "path": str(path),
            "source_sha256": sha256(path),
            "version": getattr(module, "VERSION", None),
            "bands": band_reports,
            "overall": summarize_draws(all_records),
        }
        module_report["declared_semantics"] = declared_semantics(
            module, grids_by_band, canonical_row
        )
        report["modules"][label] = module_report

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
