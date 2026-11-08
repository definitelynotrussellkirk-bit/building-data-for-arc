#!/usr/bin/env python3
"""Source-bound 100-lessons-per-band probe for dd038eb3d459.

The probe prepares an immutable portable runtime from the current checkout,
materializes lessons through the canonical Racket runner, and scores the
*declared* shortcuts/competitors rather than a duplicated name list.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

TASK_ID = "dd038eb3d459"
BANDS = ("easy", "medium", "hard")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _key(grid: Any) -> str:
    return json.dumps(grid, separators=(",", ":"), sort_keys=False)


def _load_runtime(runtime: Path):
    runtime = runtime.resolve()
    sys.path.insert(0, str(runtime))
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    semantic = importlib.import_module("scripts.generator_semantic_gate")
    profiles = importlib.import_module("scripts.canonical_profile_gate")
    return gen, semantic, profiles


def _summarize(runtime: Path, lessons_per_band: int) -> dict[str, Any]:
    gen, semantic, profiles = _load_runtime(runtime)
    requested = lessons_per_band * len(BANDS)
    lessons, errors = semantic.materialize_lessons(
        TASK_ID,
        requested,
        n_demos=gen.EXAMPLES_NEEDED,
        bands=BANDS,
        pass_difficulty=True,
        legacy=False,
    )

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    canonical = profiles.canonical_pairs(TASK_ID)
    canonical_fit = {
        name: all(rule(copy.deepcopy(pair["input"])) == pair["output"] for pair in canonical)
        for name, rule in shortcuts.items()
    }

    generator_path = (
        runtime / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
    all_inputs: set[str] = set()
    all_outputs: set[str] = set()
    per_band: dict[str, Any] = {}
    counterexamples: dict[str, dict[str, Any]] = {}
    unidentifiable: list[dict[str, Any]] = []
    survivor_counts: Counter[str] = Counter()

    for band in BANDS:
        band_lessons = [lesson for lesson in lessons if lesson["band"] == band]
        band_inputs: set[str] = set()
        band_outputs: set[str] = set()
        corners: Counter[str] = Counter()
        profiles_seen: Counter[str] = Counter()
        red_sizes: Counter[int] = Counter()
        green_sizes: Counter[int] = Counter()
        starts: Counter[int] = Counter()
        demo_disagreements: Counter[str] = Counter()
        query_disagreements: Counter[str] = Counter()
        refuted_lessons: Counter[str] = Counter()

        for lesson in band_lessons:
            starts[lesson["sample_index"] % len(gen.SCHEDULE_PROFILES)] += 1
            reasons = gen.lesson_identifiable(lesson["demos"], lesson["query"])
            if reasons:
                unidentifiable.append(
                    {
                        "band": band,
                        "seed": lesson["seed"],
                        "sample_index": lesson["sample_index"],
                        "reasons": reasons,
                    }
                )

            examples = [*lesson["demos"], lesson["query"]]
            for pair in examples:
                input_key = _key(pair["input"])
                output_key = _key(pair["output"])
                band_inputs.add(input_key)
                band_outputs.add(output_key)
                all_inputs.add(input_key)
                all_outputs.add(output_key)
                observed = gen.observe_overrides(pair["input"])
                corners[str(observed["corner_position"])] += 1
                profiles_seen[f"{observed['grid_h']}x{observed['grid_w']}"] += 1
                red_sizes[int(observed["red_size"])] += 1
                green_sizes[int(observed["green_size"])] += 1

            for name, rival in competitors.items():
                differences = []
                for demo_index, pair in enumerate(lesson["demos"]):
                    rival_output = rival(copy.deepcopy(pair["input"]))
                    differs = rival_output != pair["output"]
                    differences.append(differs)
                    if differs and name not in counterexamples:
                        counterexamples[name] = {
                            "band": band,
                            "seed": lesson["seed"],
                            "lesson_sample_index": lesson["sample_index"],
                            "example_sample_index": lesson["sample_index"] + demo_index,
                            "input": pair["input"],
                            "authoritative_racket_output": pair["output"],
                            "rival_output": rival_output,
                        }
                demo_disagreements[name] += sum(differences)
                if any(differences):
                    refuted_lessons[name] += 1
                else:
                    survivor_counts[name] += 1
                query_pair = lesson["query"]
                if rival(copy.deepcopy(query_pair["input"])) != query_pair["output"]:
                    query_disagreements[name] += 1

        per_band[band] = {
            "lessons": len(band_lessons),
            "examples": len(band_lessons) * (gen.EXAMPLES_NEEDED + 1),
            "unique_inputs": len(band_inputs),
            "unique_outputs": len(band_outputs),
            "cyclic_start_residues": dict(sorted(starts.items())),
            "corner_counts": dict(sorted(corners.items())),
            "canvas_profiles": dict(sorted(profiles_seen.items())),
            "red_size_counts": dict(sorted(red_sizes.items())),
            "green_size_counts": dict(sorted(green_sizes.items())),
            "competitor_demo_disagreements": dict(sorted(demo_disagreements.items())),
            "competitor_query_disagreements": dict(sorted(query_disagreements.items())),
            "competitor_refuted_lessons": dict(sorted(refuted_lessons.items())),
        }

    runtime_manifest = runtime / "RUNTIME_MANIFEST.json"
    result = {
        "schema": "dd038eb3d459-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _digest(generator_path),
        "rule_hash": gen.RULE_HASH,
        "probe_sha256": _digest(Path(__file__)),
        "runtime_manifest_sha256": _digest(runtime_manifest),
        "sampler": {
            "implementation": "scripts.generator_semantic_gate.materialize_lessons -> puzzle_generators.runner.run_one",
            "label_authority": "canonical Racket rule",
            "bands": list(BANDS),
            "lessons_requested_total": requested,
            "lessons_requested_per_band": lessons_per_band,
            "examples_per_lesson": gen.EXAMPLES_NEEDED + 1,
            "demos_per_lesson": gen.EXAMPLES_NEEDED,
            "queries_per_lesson": 1,
            "lesson_start": "k * 11 within each band",
            "lesson_seed": "_pinned_seed(task_id, f'lesson:{band}', k)",
            "sample_consumption": "runner.run_one accepts sequential unique lawful draws beginning at the lesson start",
        },
        "declared_domain": gen.AXES,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "competitors": sorted(competitors),
        "materialized_lessons": len(lessons),
        "materialization_errors": errors,
        "unique_inputs": len(all_inputs),
        "unique_outputs": len(all_outputs),
        "per_band": per_band,
        "competitor_survived_demo_windows": dict(sorted(survivor_counts.items())),
        "unidentifiable_lessons": unidentifiable,
        "first_counterexample_per_competitor": counterexamples,
    }
    result["passed"] = bool(
        not errors
        and len(lessons) == requested
        and not unidentifiable
        and all(canonical_fit.values())
        and all(survivor_counts.get(name, 0) == 0 for name in competitors)
        and all(
            per_band[band]["lessons"] == lessons_per_band
            and per_band[band]["unique_inputs"] == per_band[band]["examples"]
            for band in BANDS
        )
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path.cwd())
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.lessons_per_band < 1:
        parser.error("--lessons-per-band must be positive")
    output = args.out.resolve()

    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    catalog = Catalog(args.library)
    with tempfile.TemporaryDirectory(prefix="dd038eb3d459-lesson-probe-") as tmp:
        runtime = Path(tmp)
        prepare_runtime(catalog, runtime, TASK_ID)
        result = _summarize(runtime, args.lessons_per_band)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "passed": result["passed"],
        "materialized_lessons": result["materialized_lessons"],
        "unique_inputs": result["unique_inputs"],
        "survivors": result["competitor_survived_demo_windows"],
        "out": str(output),
    }, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
