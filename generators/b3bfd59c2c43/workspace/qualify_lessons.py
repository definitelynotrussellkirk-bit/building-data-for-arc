#!/usr/bin/env python3
"""Source-bound lesson/rival qualification probe for b3bfd59c2c43.

This is intentionally task-local. It exercises the selected generator's actual
``generate`` sampler, ``lesson_identifiable`` hook, and declared competitor maps
without copying rival names into the probe. The lesson assembly is explicit and
reproducible: 100 lessons per band by default, three consecutive demos and one
query, stride 11 between lesson starts, and deterministic SHA-256-derived seeds.

Outputs use the generator's independently tested ``rule_mirror``. The normal
battery's ``rule_smoke``/``authority_sync`` gates remain the authority check; this
probe is a larger curriculum-identifiability census, not a replacement for the
Racket oracle.
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
from typing import Any, Callable

WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO_ROOT = TASK_DIR.parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
TASK_ID = TASK_DIR.name
BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11
N_QUERIES = 1

for candidate in (REPO_ROOT / "shared" / "runtime", REPO_ROOT / "src"):
    sys.path.insert(0, str(candidate))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"qualify_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed(band: str, lesson_index: int) -> int:
    payload = f"{TASK_ID}|qualification-v1|{band}|{lesson_index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_canonical() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} not found in {CANONICAL_PATH}")


def _declared_rivals(gen) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    rivals: dict[str, Callable] = {}
    for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        value = getattr(gen, attr, {})
        if not isinstance(value, dict):
            raise TypeError(f"{attr} must be a dict, got {type(value).__name__}")
        for name, fn in value.items():
            if not isinstance(name, str) or not callable(fn):
                raise TypeError(f"invalid {attr} entry {name!r}: {fn!r}")
            prior = rivals.get(name)
            if prior is not None and prior is not fn:
                raise ValueError(f"rival {name!r} is declared with two functions")
            rivals[name] = fn
    if not rivals:
        raise RuntimeError("generator declares no CANONICAL_SHORTCUTS/LESSON_COMPETITORS")
    return rivals


def _canonical_rival_census(gen, canonical: dict[str, Any], rivals: dict[str, Callable]) -> dict[str, Any]:
    pairs = canonical.get("train") or []
    parity = [gen.rule_mirror(pair["input"]) == pair["output"] for pair in pairs]
    if not all(parity):
        raise AssertionError(f"rule_mirror disagrees with canonical pairs at {[i for i, ok in enumerate(parity) if not ok]}")
    rows: dict[str, Any] = {}
    for name, fn in rivals.items():
        matches = [fn(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs]
        rows[name] = {
            "matching_pairs": sum(matches),
            "total_pairs": len(matches),
            "fits_every_canonical_pair": all(matches),
            "per_pair": matches,
        }
    return {
        "canonical_pairs": len(pairs),
        "rule_mirror_matches_all": all(parity),
        "rivals": rows,
    }


def _materialize_lesson(gen, *, band: str, lesson_index: int, n_demos: int) -> dict[str, Any]:
    seed = _seed(band, lesson_index)
    start = lesson_index * LESSON_STRIDE
    pairs = []
    for offset in range(n_demos + N_QUERIES):
        sample_index = start + offset
        grid = gen.generate(seed, sample_index, difficulty=band)
        errors = gen.self_check(grid, difficulty=band)
        if errors:
            raise AssertionError(
                f"generated invalid grid band={band} lesson={lesson_index} "
                f"sample_index={sample_index}: {errors}"
            )
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return {
        "band": band,
        "lesson_index": lesson_index,
        "seed": seed,
        "sample_index": start,
        "demos": pairs[:n_demos],
        "query": pairs[n_demos],
    }


def _band_census(gen, rivals: dict[str, Callable], *, band: str, lessons: int, n_demos: int) -> dict[str, Any]:
    unique_inputs: set[str] = set()
    hook_failures: list[dict[str, Any]] = []
    witness_hits = Counter()
    rival_rows = {
        name: {
            "input_disagreements": 0,
            "demo_survivor_lessons": 0,
            "harmful_survivor_lessons": 0,
            "query_disagreement_lessons": 0,
            "first_harmful_survivor": None,
        }
        for name in rivals
    }

    for lesson_index in range(lessons):
        lesson = _materialize_lesson(gen, band=band, lesson_index=lesson_index, n_demos=n_demos)
        all_pairs = [*lesson["demos"], lesson["query"]]
        for pair in all_pairs:
            unique_inputs.add(_grid_hash(pair["input"]))
            for witness_name, predicate in getattr(gen, "SEMANTIC_WITNESSES", {}).items():
                if predicate(copy.deepcopy(pair["input"])):
                    witness_hits[witness_name] += 1

        reasons = gen.lesson_identifiable(lesson["demos"], lesson["query"])
        if reasons:
            hook_failures.append({
                "lesson_index": lesson_index,
                "seed": lesson["seed"],
                "sample_index": lesson["sample_index"],
                "reasons": reasons,
            })

        for name, rival in rivals.items():
            row = rival_rows[name]
            matches = [rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in all_pairs]
            row["input_disagreements"] += sum(not match for match in matches)
            survives_demos = all(matches[:n_demos])
            differs_query = not matches[n_demos]
            if survives_demos:
                row["demo_survivor_lessons"] += 1
            if differs_query:
                row["query_disagreement_lessons"] += 1
            if survives_demos and differs_query:
                row["harmful_survivor_lessons"] += 1
                if row["first_harmful_survivor"] is None:
                    row["first_harmful_survivor"] = {
                        "lesson_index": lesson_index,
                        "seed": lesson["seed"],
                        "sample_index": lesson["sample_index"],
                    }

    input_count = lessons * (n_demos + N_QUERIES)
    return {
        "lessons": lessons,
        "n_demos": n_demos,
        "n_queries": N_QUERIES,
        "materialized_inputs": input_count,
        "unique_inputs": len(unique_inputs),
        "hook_identifiable_lessons": lessons - len(hook_failures),
        "hook_unidentifiable_lessons": len(hook_failures),
        "hook_failure_examples": hook_failures[:10],
        "witness_input_hits": dict(sorted(witness_hits.items())),
        "rivals": rival_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, default=WORKSPACE / "qualification.json")
    parser.add_argument("--expected-generator-sha256")
    args = parser.parse_args()
    if args.per_band <= 0:
        parser.error("--per-band must be positive")

    source_hash = _sha256(GENERATOR_PATH)
    if args.expected_generator_sha256 and source_hash != args.expected_generator_sha256:
        raise SystemExit(
            f"generator hash mismatch: expected {args.expected_generator_sha256}, got {source_hash}"
        )

    gen = _load_generator()
    if getattr(gen, "TASK_ID", None) != TASK_ID:
        raise RuntimeError(f"loaded TASK_ID={getattr(gen, 'TASK_ID', None)!r}, expected {TASK_ID!r}")
    n_demos = getattr(gen, "EXAMPLES_NEEDED", 3)
    if type(n_demos) is not int or not 2 <= n_demos <= 5:
        raise RuntimeError(f"EXAMPLES_NEEDED must be an int in 2..5, got {n_demos!r}")
    rivals = _declared_rivals(gen)
    canonical = _load_canonical()

    result = {
        "schema": "b3bfd59c2c43-lesson-qualification-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "generator_version": getattr(gen, "VERSION", None),
        "sampler": {
            "implementation": "generator.generate",
            "bands": list(BANDS),
            "lessons_per_band": args.per_band,
            "demos_per_lesson": n_demos,
            "queries_per_lesson": N_QUERIES,
            "sample_index_start": "lesson_index * 11",
            "within_lesson": "consecutive sample indexes",
            "seed": "uint64(first 8 bytes SHA256(task|qualification-v1|band|lesson_index))",
        },
        "domain_limits": [
            "Generated outputs use generator.rule_mirror rather than one Racket call per row.",
            "Authority parity is separately enforced by battery rule_smoke/authority_sync and checked here on canonical pairs.",
            "This is a deterministic task-local census, not a claim of universal rule induction.",
        ],
        "declared_rivals": sorted(rivals),
        "canonical": _canonical_rival_census(gen, canonical, rivals),
        "bands": {
            band: _band_census(gen, rivals, band=band, lessons=args.per_band, n_demos=n_demos)
            for band in BANDS
        },
    }
    result["totals"] = {
        "lessons": sum(row["lessons"] for row in result["bands"].values()),
        "materialized_inputs": sum(row["materialized_inputs"] for row in result["bands"].values()),
        "unique_inputs": sum(row["unique_inputs"] for row in result["bands"].values()),
        "hook_unidentifiable_lessons": sum(row["hook_unidentifiable_lessons"] for row in result["bands"].values()),
        "harmful_survivor_lessons": {
            name: sum(row["rivals"][name]["harmful_survivor_lessons"] for row in result["bands"].values())
            for name in rivals
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": source_hash,
        "lessons": result["totals"]["lessons"],
        "unique_inputs": result["totals"]["unique_inputs"],
        "hook_unidentifiable_lessons": result["totals"]["hook_unidentifiable_lessons"],
        "harmful_survivor_lessons": result["totals"]["harmful_survivor_lessons"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if result["totals"]["hook_unidentifiable_lessons"] == 0 and not any(result["totals"]["harmful_survivor_lessons"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
