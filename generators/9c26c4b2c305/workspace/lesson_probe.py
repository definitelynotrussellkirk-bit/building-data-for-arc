#!/usr/bin/env python3
"""Source-bound curriculum census for generator 9c26c4b2c305.

The probe checks every declared canonical shortcut against the canonical pairs,
then samples consecutive four-example lessons in each difficulty band.  It
reports cyclic-start coverage, unique inputs, equal-panel-color coverage,
lesson identifiability, and kill/survival counts for the generator's actual
LESSON_COMPETITORS declaration.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "9c26c4b2c305"
WORKSPACE = Path(__file__).resolve().parent
GENERATOR_DIR = WORKSPACE.parent
REPO_ROOT = GENERATOR_DIR.parents[1]
GENERATOR_PATH = GENERATOR_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator():
    sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return [*record.get("train", []), *record.get("test", [])]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def _canonical_shortcut_report(gen) -> dict[str, Any]:
    pairs = _canonical_pairs()
    report: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = 0
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                if rival(pair["input"]) == pair["output"]:
                    fits += 1
            except Exception as exc:  # diagnostic: preserve exact rival failure
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        report[name] = {
            "canonical_pairs": len(pairs),
            "fits": fits,
            "errors": errors,
        }
    return report


def _band_report(gen, band: str, lessons: int, seed_base: int) -> dict[str, Any]:
    starts = Counter()
    palettes = Counter()
    widths = Counter()
    input_hashes: set[str] = set()
    same_color_draws = 0
    same_color_lessons = 0
    identifiable = 0
    lesson_failures: list[dict[str, Any]] = []
    rival_stats = {
        name: {"disagreeing_demos": 0, "killed_lessons": 0, "surviving_lessons": 0, "errors": []}
        for name in gen.LESSON_COMPETITORS
    }

    for lesson_index in range(lessons):
        start_index = lesson_index
        starts[start_index % len(gen.SCHEDULE_PROFILES)] += 1
        demos: list[dict[str, Any]] = []
        killed_this_lesson = {name: False for name in rival_stats}
        lesson_has_same_color = False

        for offset in range(gen.EXAMPLES_NEEDED):
            sample_index = start_index + offset
            seed = seed_base + lesson_index * 101 + offset
            grid = gen.generate(seed, sample_index, difficulty=band)
            expected = gen.rule_mirror(grid)
            demos.append({"input": grid, "output": expected})
            input_hashes.add(_grid_hash(grid))

            info, errors = gen._analyse(grid)
            if errors:
                raise AssertionError(f"generated malformed grid: {errors}")
            observed = gen.observe_overrides(grid)
            palettes[observed["palette_profile"]] += 1
            widths[str(observed["grid_w"])] += 1
            is_same = info["top_colors"] == info["bottom_colors"]
            same_color_draws += int(is_same)
            lesson_has_same_color = lesson_has_same_color or is_same

            for name, rival in gen.LESSON_COMPETITORS.items():
                try:
                    disagrees = rival(grid) != expected
                except Exception as exc:  # diagnostic: retain and fail the probe
                    rival_stats[name]["errors"].append(
                        {
                            "lesson": lesson_index,
                            "offset": offset,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    disagrees = False
                if disagrees:
                    rival_stats[name]["disagreeing_demos"] += 1
                    killed_this_lesson[name] = True

        same_color_lessons += int(lesson_has_same_color)
        query_index = start_index + gen.EXAMPLES_NEEDED
        query = gen.generate(seed_base + lesson_index * 101 + 99, query_index, difficulty=band)
        reasons = gen.lesson_identifiable(
            demos, {"input": query, "output": gen.rule_mirror(query)}
        )
        if reasons:
            lesson_failures.append(
                {"lesson": lesson_index, "start_index": start_index, "reasons": reasons}
            )
        else:
            identifiable += 1

        for name, killed in killed_this_lesson.items():
            key = "killed_lessons" if killed else "surviving_lessons"
            rival_stats[name][key] += 1

    return {
        "band": band,
        "lessons": lessons,
        "draws": lessons * gen.EXAMPLES_NEEDED,
        "unique_inputs": len(input_hashes),
        "cyclic_start_residues": dict(sorted(starts.items())),
        "palette_counts": dict(sorted(palettes.items())),
        "width_counts": dict(sorted(widths.items(), key=lambda item: int(item[0]))),
        "same_panel_color_draws": same_color_draws,
        "same_panel_color_lessons": same_color_lessons,
        "identifiable_lessons": identifiable,
        "lesson_failures": lesson_failures,
        "rivals": rival_stats,
    }


def run_probe(lessons_per_band: int = 100, seed_base: int = 90_000) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    gen = _load_generator()
    bands = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        bands[band] = _band_report(
            gen,
            band,
            lessons_per_band,
            seed_base + band_index * 1_000_000,
        )

    canonical = _canonical_shortcut_report(gen)
    failures: list[str] = []
    for name, result in canonical.items():
        if result["fits"] != result["canonical_pairs"] or result["errors"]:
            failures.append(f"canonical shortcut {name} does not fit every canonical pair")
    for band, result in bands.items():
        if result["identifiable_lessons"] != lessons_per_band:
            failures.append(f"{band}: not every sampled lesson is identifiable")
        if result["same_panel_color_lessons"] != lessons_per_band:
            failures.append(f"{band}: some lessons lack an equal-panel-color witness")
        for name, rival in result["rivals"].items():
            if rival["surviving_lessons"] or rival["errors"]:
                failures.append(f"{band}: rival {name} survived or errored")

    return {
        "schema": "9c26c4b2c305-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "sampler": {
            "lessons_per_band": lessons_per_band,
            "examples_per_lesson": gen.EXAMPLES_NEEDED,
            "seed_base": seed_base,
            "lesson_start": "start_index = lesson_index; all cyclic residues exercised",
            "sample_seed": "seed_base + band_offset + lesson_index*101 + offset",
            "domain": "declared generator domain: 9 rows, width 4..14, solid nonzero separator, one nonzero color per panel, all four occupancy relations",
        },
        "canonical_shortcuts": canonical,
        "bands": bands,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=90_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(args.lessons_per_band, args.seed_base)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
