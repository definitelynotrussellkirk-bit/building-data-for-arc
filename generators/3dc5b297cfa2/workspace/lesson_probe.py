#!/usr/bin/env python3
"""Source-bound sliding-lesson probe for generator 3dc5b297cfa2.

This task-local tool samples the generator's real `generate` API, uses the
module's declared EXAMPLES_NEEDED / LESSON_COMPETITORS / witnesses, and records
whether every sampled demo window eliminates every declared rival. It is a
curriculum diagnostic, not a proof of universal induction. The selected Racket
rule remains authoritative; the probe first binds the Python mirror to all
canonical pairs and records source hashes so stale evidence is obvious.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "3dc5b297cfa2"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"lesson_probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs.extend(row.get("train") or [])
            test = row.get("test") or []
            if isinstance(test, dict):
                test = [test]
            pairs.extend(test)
    return pairs


def _seed_for(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}|lesson-probe-v1|{band}|{lesson_index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def run_probe(lessons_per_band: int) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    gen = _load_generator()
    n_demos = int(getattr(gen, "EXAMPLES_NEEDED"))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS"))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES"))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))

    canonical = _canonical_pairs()
    canonical_mismatches: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical):
        actual = gen.rule_mirror(copy.deepcopy(pair["input"]))
        if actual != pair["output"]:
            canonical_mismatches.append({"pair_index": index})

    shortcut_fits: dict[str, int] = {}
    for name, shortcut in sorted(shortcuts.items()):
        shortcut_fits[name] = sum(
            shortcut(copy.deepcopy(pair["input"])) == pair["output"] for pair in canonical
        )

    bands: dict[str, Any] = {}
    global_unique: set[str] = set()
    failures: list[dict[str, Any]] = []
    for band in BANDS:
        unique_inputs: set[str] = set()
        witness_hits: Counter[str] = Counter()
        rival_demo_disagreements: Counter[str] = Counter()
        rival_query_disagreements: Counter[str] = Counter()
        rival_survived_lessons: Counter[str] = Counter()
        identifiable = 0
        draws = 0

        for lesson_index in range(lessons_per_band):
            seed = _seed_for(band, lesson_index)
            start = lesson_index * LESSON_STRIDE
            demos: list[dict[str, Any]] = []
            inputs: list[list[list[int]]] = []
            for offset in range(n_demos):
                grid = gen.generate(seed, start + offset, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    failures.append({
                        "band": band,
                        "lesson_index": lesson_index,
                        "sample_index": start + offset,
                        "kind": "self_check",
                        "details": errors,
                    })
                output = gen.rule_mirror(copy.deepcopy(grid))
                demos.append({"input": grid, "output": output})
                inputs.append(grid)
            query_grid = gen.generate(seed, start + n_demos, difficulty=band)
            query = {
                "input": query_grid,
                "output": gen.rule_mirror(copy.deepcopy(query_grid)),
            }
            inputs.append(query_grid)

            for grid in inputs:
                digest = _grid_hash(grid)
                unique_inputs.add(digest)
                global_unique.add(digest)
                draws += 1
                for name, predicate in witnesses.items():
                    if predicate(copy.deepcopy(grid)):
                        witness_hits[name] += 1

            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                failures.append({
                    "band": band,
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "sample_index_start": start,
                    "kind": "unidentifiable",
                    "details": reasons,
                })
            else:
                identifiable += 1

            for name, rival in competitors.items():
                disagreements = sum(
                    rival(copy.deepcopy(pair["input"])) != pair["output"] for pair in demos
                )
                rival_demo_disagreements[name] += disagreements
                if disagreements == 0:
                    rival_survived_lessons[name] += 1
                if rival(copy.deepcopy(query["input"])) != query["output"]:
                    rival_query_disagreements[name] += 1

        bands[band] = {
            "lessons": lessons_per_band,
            "examples_per_lesson": n_demos,
            "queries_per_lesson": 1,
            "draws_including_overlapping_windows": draws,
            "unique_inputs": len(unique_inputs),
            "identifiable_lessons": identifiable,
            "witness_hits_over_all_demo_and_query_inputs": dict(sorted(witness_hits.items())),
            "rival_demo_disagreements": dict(sorted(rival_demo_disagreements.items())),
            "rival_query_disagreements": dict(sorted(rival_query_disagreements.items())),
            "rival_survived_lessons": dict(sorted(rival_survived_lessons.items())),
        }

    status = "PASS" if not canonical_mismatches and not failures else "FAIL"
    return {
        "schema": "3dc5b297cfa2-lesson-probe-v1",
        "status": status,
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
            "generator_sha256": _sha256(GENERATOR_PATH),
            "declared_rule_hash": getattr(gen, "RULE_HASH", None),
            "canonical_jsonl_sha256": _sha256(CANONICAL_PATH),
            "probe_path": str(HERE.relative_to(ROOT)),
            "probe_sha256": _sha256(HERE),
        },
        "sampler": {
            "api": "generate(seed, sample_index, difficulty=band)",
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "examples_needed": n_demos,
            "lesson_sample_index_start": "lesson_index * 11",
            "demo_offsets": list(range(n_demos)),
            "query_offset": n_demos,
            "seed_derivation": "uint64_be(sha256(task_id|lesson-probe-v1|band|lesson_index)[:8])",
        },
        "canonical_binding": {
            "usable_pairs": len(canonical),
            "python_mirror_mismatches": canonical_mismatches,
            "declared_canonical_shortcut_fit_counts": shortcut_fits,
        },
        "declared_competitors": sorted(competitors),
        "declared_witnesses": sorted(witnesses),
        "bands": bands,
        "global_unique_inputs": len(global_unique),
        "failure_count": len(failures),
        "failure_examples": failures[:20],
        "domain_limits": [
            "This is a deterministic sampled curriculum audit, not a proof over every legal override combination.",
            "Rival scoring uses the generator's independent Python rule_mirror after checking it against all canonical pairs; the selected Racket rule remains authority.",
            "The probe measures declared rivals only and cannot rule out unnamed shortcuts.",
            "Lesson windows use independent per-lesson seeds and stride-11 sample starts; they are not the exact training dataloader ordering.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"lesson-probe {report['status']}: "
        f"{args.lessons_per_band} lessons/band, "
        f"{report['global_unique_inputs']} unique inputs, "
        f"{report['failure_count']} failures"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
