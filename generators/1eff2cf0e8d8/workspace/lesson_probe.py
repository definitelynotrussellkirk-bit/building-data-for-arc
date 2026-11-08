#!/usr/bin/env python3
"""Large, source-bound lesson audit for Template Copies.

This probe uses the repository's real ``puzzle_generators.runner.run_one``
sampler and selected Racket authority.  It deliberately discovers shortcuts,
competitors, witnesses, and the lesson length from the loaded generator instead
of keeping a second handwritten list that can drift.

Run from the repository root through the packet's Racket wrapper, for example::

    python3 ../run_with_racket.py python3 \
      generators/1eff2cf0e8d8/workspace/lesson_probe.py \
      --lessons-per-band 100 --expected-generator-sha256 SHA \
      --out ../checks/1eff2cf0e8d8_lesson_probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

TASK_ID = "1eff2cf0e8d8"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BANDS = ("easy", "medium", "hard")
SEED_NAMESPACE = f"{TASK_ID}:lesson-probe:v1"


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{SEED_NAMESPACE}:{band}:{lesson_index}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    for line in CANONICAL_PATH.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        raw_pairs = list(row.get("train") or [])
        tests = row.get("test") or []
        raw_pairs.extend(tests if isinstance(tests, list) else [tests])
        return [
            {
                "input": _normalize_grid(pair["input"]),
                "output": _normalize_grid(pair["output"]),
            }
            for pair in raw_pairs
        ]
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _canonical_rule_source() -> str:
    for line in CANONICAL_PATH.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            source = str(row.get("program_solution") or "").strip()
            if not source:
                raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
            return source
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _selected_bundle(gen):
    """Build the same explicit canonical bundle used by review worker.py."""
    # Review packets store the historical ``scripts`` modules under
    # ``shared/tools`` instead of an installed scripts/ package.  The shared
    # rule wrapper imports ``scripts.comment_solutions`` for its parser, so
    # expose that directory as a namespace package without copying files.
    if "scripts" not in sys.modules:
        scripts_pkg = types.ModuleType("scripts")
        scripts_pkg.__path__ = [str(REPO / "shared" / "tools")]
        sys.modules["scripts"] = scripts_pkg

    from puzzle_generators import runner

    source = _canonical_rule_source()
    return runner.GeneratorBundle(
        task_id=TASK_ID,
        rule_task_id=TASK_ID,
        rule_source=source,
        rule_callable_text=runner.wrap_rule(source),
        rule_file="shared/data/canonical/puzzles.jsonl",
        generator_module=gen,
        allow_identity_output=bool(getattr(gen, "ALLOW_IDENTITY_OUTPUT", False)),
        kind="per_puzzle",
    )


def _grid_digest(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def score_lesson(gen, demos: list[dict], query: dict) -> dict[str, Any]:
    """Score every competitor declared by *this exact loaded source*."""
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    disagreements: dict[str, int] = {}
    survived: list[str] = []
    query_disagreements: list[str] = []
    errors: dict[str, str] = {}
    for name, rival in sorted(competitors.items()):
        try:
            count = sum(
                rival(copy.deepcopy(pair["input"])) != pair["output"]
                for pair in demos
            )
            disagreements[name] = count
            if count == 0:
                survived.append(name)
                if rival(copy.deepcopy(query["input"])) != query["output"]:
                    query_disagreements.append(name)
        except Exception as exc:  # retained in the JSON; never silently skipped
            errors[name] = f"{type(exc).__name__}: {exc}"
    reasons = list(gen.lesson_identifiable(copy.deepcopy(demos), copy.deepcopy(query)))
    return {
        "identifiability_reasons": reasons,
        "competitor_demo_disagreements": disagreements,
        "survived_demos": survived,
        "survived_demos_but_changed_query": query_disagreements,
        "competitor_errors": errors,
    }


def _resolve_sample_indices(gen, seed: int, start: int, band: str, inputs: list) -> list[int | None]:
    """Recover the actual accepted sequential indices used by run_one."""
    resolved: list[int | None] = []
    cursor = start
    for actual in inputs:
        match = None
        for sample_index in range(cursor, start + len(inputs) * 5):
            candidate = gen.generate(seed, sample_index, difficulty=band)
            if candidate == actual:
                match = sample_index
                cursor = sample_index + 1
                break
        resolved.append(match)
    return resolved


def _canonical_shortcut_audit(gen) -> dict[str, Any]:
    pairs = _canonical_pairs()
    rows: dict[str, Any] = {}
    for name, shortcut in sorted(
        dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {}).items()
    ):
        errors: list[str] = []
        fits = 0
        for index, pair in enumerate(pairs):
            try:
                if shortcut(copy.deepcopy(pair["input"])) == pair["output"]:
                    fits += 1
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        rows[name] = {
            "fits": fits,
            "usable_pairs": len(pairs),
            "fits_all": fits == len(pairs) and not errors,
            "errors": errors,
        }
    return {"usable_pairs": len(pairs), "shortcuts": rows}


def run_probe(*, lessons_per_band: int, expected_generator_sha256: str | None) -> dict[str, Any]:
    if lessons_per_band < 100:
        raise ValueError("lessons_per_band must be at least 100")
    generator_sha = source_sha256(GENERATOR_PATH)
    if expected_generator_sha256 and generator_sha != expected_generator_sha256:
        raise ValueError(
            "generator hash mismatch: expected "
            f"{expected_generator_sha256}, observed {generator_sha}"
        )

    gen = _load_generator()
    from puzzle_generators import runner

    bundle = _selected_bundle(gen)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    examples_needed = int(getattr(gen, "EXAMPLES_NEEDED"))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})

    result: dict[str, Any] = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": generator_sha,
        "generator_version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "executed_rule_hash": normalized_rule_hash(bundle.rule_source),
        "seed_namespace": SEED_NAMESPACE,
        "actual_sampler": {
            "call": "puzzle_generators.runner.run_one",
            "n_train": examples_needed,
            "n_test": 1,
            "lesson_start_sample_index": "lesson_index (cycles every residue)",
            "pair_indices": "sequential accepted sample indices from each start",
            "seed": "first 64 bits of SHA256(seed_namespace:band:lesson_index)",
            "difficulty": "easy|medium|hard passed to every generate call",
            "authority": "canonical program_solution in an explicit GeneratorBundle",
        },
        "lessons_per_band": lessons_per_band,
        "examples_needed": examples_needed,
        "declared_competitors": sorted(competitors),
        "declared_witnesses": sorted(witnesses),
        "canonical_shortcuts": _canonical_shortcut_audit(gen),
        "domain_limits": {
            "axes": getattr(gen, "AXES", {}),
            "invariants": getattr(gen, "INVARIANTS", []),
            "claim_scope": (
                "This probe measures the declared four-slot sampler and named "
                "competitors only; it is not a proof of universal induction or "
                "coverage of unnamed rival programs."
            ),
        },
        "per_band": {},
        "failures": [],
    }

    global_input_hashes: set[str] = set()
    try:
        for band in BANDS:
            band_input_hashes: set[str] = set()
            start_residues: Counter[int] = Counter()
            profile_windows: Counter[str] = Counter()
            witness_hits: Counter[str] = Counter()
            competitor_refuted_lessons: Counter[str] = Counter()
            competitor_demo_disagreements: Counter[str] = Counter()
            lessons_identifiable = 0
            sampler_shifted = 0
            parity_checks = 0
            parity_mismatches = 0
            validator_failures = 0
            competitor_errors = 0

            for lesson_index in range(lessons_per_band):
                seed = derive_seed(band, lesson_index)
                start = lesson_index
                start_residues[start % examples_needed] += 1
                try:
                    instance = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=start,
                        n_train=examples_needed,
                        n_test=1,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    result["failures"].append({
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "kind": "run_one_error",
                        "detail": f"{type(exc).__name__}: {exc}",
                    })
                    continue

                demos = instance["train"]
                query = instance["test"][0]
                all_pairs = [*demos, query]
                actual_indices = _resolve_sample_indices(
                    gen, seed, start, band, [pair["input"] for pair in all_pairs]
                )
                expected_indices = list(range(start, start + len(all_pairs)))
                if actual_indices != expected_indices:
                    sampler_shifted += 1
                profile_windows["|".join(
                    str(gen.schedule_profile(seed, index, band))
                    if index is not None else "unresolved"
                    for index in actual_indices[:examples_needed]
                )] += 1

                for pair_index, pair in enumerate(all_pairs):
                    digest = _grid_digest(pair["input"])
                    band_input_hashes.add(digest)
                    global_input_hashes.add(digest)
                    errors = list(gen.self_check(copy.deepcopy(pair["input"])))
                    if errors:
                        validator_failures += 1
                        if len(result["failures"]) < 12:
                            result["failures"].append({
                                "band": band,
                                "lesson_index": lesson_index,
                                "pair_index": pair_index,
                                "kind": "self_check",
                                "detail": errors,
                            })
                    parity_checks += 1
                    if gen.rule_mirror(copy.deepcopy(pair["input"])) != pair["output"]:
                        parity_mismatches += 1
                        if len(result["failures"]) < 12:
                            result["failures"].append({
                                "band": band,
                                "lesson_index": lesson_index,
                                "pair_index": pair_index,
                                "kind": "racket_python_parity",
                                "input": pair["input"],
                                "racket_output": pair["output"],
                                "python_output": gen.rule_mirror(pair["input"]),
                            })
                    for name, predicate in witnesses.items():
                        try:
                            if predicate(copy.deepcopy(pair["input"])):
                                witness_hits[name] += 1
                        except Exception as exc:
                            if len(result["failures"]) < 12:
                                result["failures"].append({
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "pair_index": pair_index,
                                    "kind": "witness_error",
                                    "name": name,
                                    "detail": f"{type(exc).__name__}: {exc}",
                                })

                scored = score_lesson(gen, demos, query)
                if not scored["identifiability_reasons"]:
                    lessons_identifiable += 1
                elif len(result["failures"]) < 12:
                    result["failures"].append({
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "kind": "unidentifiable",
                        "reasons": scored["identifiability_reasons"],
                        "survived_demos": scored["survived_demos"],
                    })
                for name, count in scored["competitor_demo_disagreements"].items():
                    competitor_demo_disagreements[name] += count
                    if count:
                        competitor_refuted_lessons[name] += 1
                competitor_errors += len(scored["competitor_errors"])
                for name, detail in scored["competitor_errors"].items():
                    if len(result["failures"]) < 12:
                        result["failures"].append({
                            "band": band,
                            "lesson_index": lesson_index,
                            "kind": "competitor_error",
                            "name": name,
                            "detail": detail,
                        })

            result["per_band"][band] = {
                "lessons_requested": lessons_per_band,
                "lessons_identifiable": lessons_identifiable,
                "lesson_failures": lessons_per_band - lessons_identifiable,
                "pairs_requested": lessons_per_band * (examples_needed + 1),
                "unique_inputs": len(band_input_hashes),
                "start_residues": {str(k): v for k, v in sorted(start_residues.items())},
                "profile_windows": dict(sorted(profile_windows.items())),
                "sampler_shifted_lessons": sampler_shifted,
                "validator_failures": validator_failures,
                "racket_python_parity_checks": parity_checks,
                "racket_python_parity_mismatches": parity_mismatches,
                "witness_hits_over_demos_and_queries": {
                    name: witness_hits.get(name, 0) for name in sorted(witnesses)
                },
                "competitor_refuted_lessons": {
                    name: competitor_refuted_lessons.get(name, 0)
                    for name in sorted(competitors)
                },
                "competitor_demo_disagreements": {
                    name: competitor_demo_disagreements.get(name, 0)
                    for name in sorted(competitors)
                },
                "competitor_errors": competitor_errors,
            }
    finally:
        bridge.shutdown()

    result["unique_inputs_global"] = len(global_input_hashes)
    if result["declared_rule_hash"] != result["executed_rule_hash"]:
        result["failures"].append({
            "kind": "rule_hash_mismatch",
            "declared": result["declared_rule_hash"],
            "executed": result["executed_rule_hash"],
        })

    shortcut_failures = [
        name
        for name, row in result["canonical_shortcuts"]["shortcuts"].items()
        if not row["fits_all"]
    ]
    blocking: list[str] = []
    if result["declared_rule_hash"] != result["executed_rule_hash"]:
        blocking.append("declared RULE_HASH does not match executed canonical authority")
    if shortcut_failures:
        blocking.append(f"declared canonical shortcuts did not fit: {shortcut_failures}")
    for band, row in result["per_band"].items():
        if row["lessons_identifiable"] != lessons_per_band:
            blocking.append(f"{band}: not every lesson identifiable")
        if row["validator_failures"]:
            blocking.append(f"{band}: validator failures")
        if row["racket_python_parity_mismatches"]:
            blocking.append(f"{band}: Racket/Python mismatches")
        if row["competitor_errors"]:
            blocking.append(f"{band}: competitor errors")
        missing = [
            name for name, count in row["competitor_refuted_lessons"].items()
            if count != lessons_per_band
        ]
        if missing:
            blocking.append(f"{band}: competitors survive some demos: {missing}")
    result["blocking_findings"] = blocking
    result["status"] = "PASS" if not blocking else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--expected-generator-sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = run_probe(
        lessons_per_band=args.lessons_per_band,
        expected_generator_sha256=args.expected_generator_sha256,
    )
    output = args.out if args.out.is_absolute() else Path.cwd() / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"lesson-probe: {result['status']} {TASK_ID}; "
        + ", ".join(
            f"{band}={row['lessons_identifiable']}/{row['lessons_requested']} "
            f"identifiable, {row['unique_inputs']} unique inputs"
            for band, row in result["per_band"].items()
        )
    )
    print(f"generator_sha256={result['generator_sha256']}")
    print(f"evidence={output}")
    for finding in result["blocking_findings"]:
        print(f"BLOCK: {finding}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
