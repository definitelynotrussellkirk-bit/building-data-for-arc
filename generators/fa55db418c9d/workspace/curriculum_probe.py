#!/usr/bin/env python3
"""Source-bound Racket-labelled curriculum and rival census for fa55db418c9d.

Run from the packet root through the bundled Racket wrapper::

  python3 run_with_racket.py python3 \
    generators/fa55db418c9d/workspace/curriculum_probe.py \
    --lessons-per-band 100 --out ../checks/curriculum-probe-final.json

The probe uses the generator's *actual* semantic declarations, labels every
sample with the selected canonical Racket rule, checks all cyclic schedule
starts induced by the sampler, and records counts rather than claiming
universal induction outside the generated default domain.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any


TASK_ID = "fa55db418c9d"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
TOOLS_ROOT = REPO_ROOT / "shared" / "tools"
for path in (TOOLS_ROOT, RUNTIME_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
# Source layout stores staged ``scripts/*`` modules flat under shared/tools.
# Give rule_wrap the same package view that portable runtimes provide.
if "scripts" not in sys.modules:
    scripts_pkg = types.ModuleType("scripts")
    scripts_pkg.__path__ = [str(TOOLS_ROOT)]
    sys.modules["scripts"] = scripts_pkg


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _load_generator():
    path = TASK_DIR / "generator.py"
    name = f"curriculum_probe_{TASK_ID}_{_sha_file(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_record() -> dict[str, Any]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise RuntimeError(f"canonical record {TASK_ID} not found")


def _pairs(record: dict[str, Any]) -> list[dict[str, Any]]:
    test = record.get("test", [])
    tests = test if isinstance(test, list) else [test]
    return [*record.get("train", []), *tests]


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _seed(band: str, lesson_index: int) -> int:
    raw = f"fa55-curriculum-probe-v1:{band}:{lesson_index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:12], 16)


def _grid_key(grid: list[list[int]]) -> str:
    return _sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _racket_outputs(rule_source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    outputs: list[list[list[int]]] = []
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define probe-rule {wrap_rule(rule_source)})")
        for offset in range(0, len(grids), 32):
            batch = grids[offset : offset + 32]
            result = bridge.eval_text(
                f"(map probe-rule '{_racket_literal(batch)})"
            )
            if not isinstance(result, list) or len(result) != len(batch):
                raise RuntimeError(
                    f"Racket returned {type(result).__name__} / "
                    f"{len(result) if isinstance(result, list) else '?'} for batch {offset}"
                )
            outputs.extend(result)
    return outputs


def run_probe(lessons_per_band: int) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    gen = _load_generator()
    canonical = _canonical_record()
    n_demos = int(gen.EXAMPLES_NEEDED)
    bands = ("easy", "medium", "hard")
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for band in bands:
        for lesson_index in range(lessons_per_band):
            seed = _seed(band, lesson_index)
            start = 11 * lesson_index
            for offset in range(n_demos + 1):
                sample_index = start + offset
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    errors = gen.self_check(grid, difficulty=band)
                    if errors:
                        raise ValueError(f"self_check: {errors}")
                    replay = gen.generate(seed, sample_index, difficulty=band)
                    if replay != grid:
                        raise AssertionError("deterministic replay mismatch")
                    records.append(
                        {
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "start_sample_index": start,
                            "sample_index": sample_index,
                            "offset": offset,
                            "role": "demo" if offset < n_demos else "query",
                            "profile": gen.schedule_profile(seed, sample_index, band),
                            "input": grid,
                        }
                    )
                except Exception as exc:
                    failures.append(
                        {
                            "kind": "generation",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    canonical_pairs = _pairs(canonical)
    all_grids = [pair["input"] for pair in canonical_pairs] + [
        record["input"] for record in records
    ]
    outputs = _racket_outputs(canonical["program_solution"], all_grids)
    canonical_outputs = outputs[: len(canonical_pairs)]
    generated_outputs = outputs[len(canonical_pairs) :]

    canonical_mismatches = 0
    mirror_mismatches = 0
    for index, (pair, actual) in enumerate(zip(canonical_pairs, canonical_outputs)):
        if actual != pair["output"]:
            canonical_mismatches += 1
            failures.append({"kind": "canonical_racket_mismatch", "pair": index})
        mirror = gen.rule_mirror(copy.deepcopy(pair["input"]))
        if mirror != actual:
            mirror_mismatches += 1
            failures.append({"kind": "canonical_mirror_mismatch", "pair": index})

    for record, actual in zip(records, generated_outputs):
        record["output"] = actual
        mirror = gen.rule_mirror(copy.deepcopy(record["input"]))
        if mirror != actual:
            mirror_mismatches += 1
            if mirror_mismatches <= 10:
                failures.append(
                    {
                        "kind": "generated_mirror_mismatch",
                        "band": record["band"],
                        "lesson_index": record["lesson_index"],
                        "sample_index": record["sample_index"],
                    }
                )

    shortcut_fit = {}
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        fits = [
            shortcut(copy.deepcopy(pair["input"])) == actual
            for pair, actual in zip(canonical_pairs, canonical_outputs)
        ]
        shortcut_fit[name] = {
            "fits": sum(fits),
            "pairs": len(fits),
            "fits_all": all(fits),
        }

    by_lesson: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_lesson[(record["band"], record["lesson_index"])].append(record)

    band_reports: dict[str, Any] = {}
    first_straight_witness = None
    for band in bands:
        lessons = [by_lesson[(band, i)] for i in range(lessons_per_band)]
        unique_inputs: set[str] = set()
        profile_counts: Counter[str] = Counter()
        start_residues: Counter[str] = Counter()
        witness_hits = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
        rival_grid_disagreements = Counter({name: 0 for name in gen.LESSON_COMPETITORS})
        rival_lesson_refutations = Counter({name: 0 for name in gen.LESSON_COMPETITORS})
        rival_query_disagreements = Counter({name: 0 for name in gen.LESSON_COMPETITORS})
        lesson_failures = []

        for lesson_index, lesson in enumerate(lessons):
            if len(lesson) != n_demos + 1:
                lesson_failures.append(
                    {"lesson_index": lesson_index, "reason": f"materialized {len(lesson)} rows"}
                )
                continue
            lesson.sort(key=lambda row: row["offset"])
            start_residues[str(lesson[0]["start_sample_index"] % len(gen.SCHEDULE_PROFILES))] += 1
            demos = [
                {"input": row["input"], "output": row["output"]}
                for row in lesson[:n_demos]
            ]
            query = {"input": lesson[n_demos]["input"]}
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append(
                    {"lesson_index": lesson_index, "reason": reasons[:4]}
                )

            for row in lesson:
                grid, truth = row["input"], row["output"]
                unique_inputs.add(_grid_key(grid))
                profile_counts[str(row["profile"])] += 1
                for name, predicate in gen.SEMANTIC_WITNESSES.items():
                    fired = bool(predicate(grid))
                    witness_hits[name] += int(fired)
                    if fired:
                        named = gen.WITNESS_RIVALS.get(name, [])
                        if not named or not any(
                            gen.LESSON_COMPETITORS[rival](copy.deepcopy(grid)) != truth
                            for rival in named
                        ):
                            failures.append(
                                {
                                    "kind": "witness_claim_failed",
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "sample_index": row["sample_index"],
                                    "witness": name,
                                }
                            )
                for name, competitor in gen.LESSON_COMPETITORS.items():
                    rival_grid_disagreements[name] += int(
                        competitor(copy.deepcopy(grid)) != truth
                    )

                facts = gen.semantic_observables(grid)
                if (
                    first_straight_witness is None
                    and "straight_triomino" in facts.get("blue_decoy_kinds", [])
                ):
                    rival_name = "recolor every blue size-three component"
                    first_straight_witness = {
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": row["seed"],
                        "sample_index": row["sample_index"],
                        "input": grid,
                        "racket_output": truth,
                        "rival": rival_name,
                        "rival_output": gen.CANONICAL_SHORTCUTS[rival_name](
                            copy.deepcopy(grid)
                        ),
                    }

            query_row = lesson[n_demos]
            for name, competitor in gen.LESSON_COMPETITORS.items():
                refuted = any(
                    competitor(copy.deepcopy(demo["input"])) != demo["output"]
                    for demo in demos
                )
                rival_lesson_refutations[name] += int(refuted)
                rival_query_disagreements[name] += int(
                    competitor(copy.deepcopy(query_row["input"])) != query_row["output"]
                )

        band_reports[band] = {
            "lessons": lessons_per_band,
            "grids": sum(len(lesson) for lesson in lessons),
            "unique_inputs": len(unique_inputs),
            "lesson_failures": lesson_failures[:20],
            "lesson_failure_count": len(lesson_failures),
            "start_residues_mod_schedule": dict(sorted(start_residues.items())),
            "profile_counts": dict(sorted(profile_counts.items())),
            "witness_hits": dict(sorted(witness_hits.items())),
            "rival_grid_disagreements": dict(sorted(rival_grid_disagreements.items())),
            "rival_lesson_refutations": dict(sorted(rival_lesson_refutations.items())),
            "rival_query_disagreements": dict(sorted(rival_query_disagreements.items())),
        }

    passed = (
        not failures
        and canonical_mismatches == 0
        and mirror_mismatches == 0
        and all(row["fits_all"] for row in shortcut_fit.values())
        and all(row["lesson_failure_count"] == 0 for row in band_reports.values())
        and all(
            all(count == lessons_per_band for count in row["rival_lesson_refutations"].values())
            for row in band_reports.values()
        )
    )

    return {
        "schema": "fa55db418c9d-curriculum-probe-v1",
        "task_id": TASK_ID,
        "source": {
            "generator_sha256": _sha_file(TASK_DIR / "generator.py"),
            "probe_sha256": _sha_file(Path(__file__)),
            "canonical_row_sha256": _sha_bytes(
                json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
            ),
            "declared_rule_hash": gen.RULE_HASH,
            "computed_rule_hash": _sha_bytes(
                " ".join(canonical["program_solution"].split()).encode()
            )[:12],
            "generator_version": gen.VERSION,
        },
        "sampler": {
            "bands": list(bands),
            "lessons_per_band": lessons_per_band,
            "examples_per_lesson": n_demos,
            "query_per_lesson": 1,
            "seed": "sha256('fa55-curriculum-probe-v1:{band}:{lesson_index}')[:12]",
            "lesson_start_sample_index": "11 * lesson_index",
            "within_lesson": "consecutive sample_index values start..start+EXAMPLES_NEEDED",
            "domain": "default generated inputs only; no overrides; finite measured census, not universal induction",
            "declared_axes": gen.AXES,
            "declared_schedule_profiles": list(gen.SCHEDULE_PROFILES),
        },
        "canonical": {
            "pairs": len(canonical_pairs),
            "racket_stored_output_mismatches": canonical_mismatches,
            "python_mirror_mismatches": mirror_mismatches,
            "canonical_shortcuts": shortcut_fit,
        },
        "bands": band_reports,
        "strongest_shortcut_witness": first_straight_witness,
        "failure_count": len(failures),
        "failure_examples": failures[:40],
        "passed": passed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    report = run_probe(args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    concise = {
        "passed": report["passed"],
        "failure_count": report["failure_count"],
        "canonical": report["canonical"],
        "bands": {
            band: {
                "lessons": row["lessons"],
                "grids": row["grids"],
                "unique_inputs": row["unique_inputs"],
                "lesson_failure_count": row["lesson_failure_count"],
                "rival_lesson_refutations": row["rival_lesson_refutations"],
            }
            for band, row in report["bands"].items()
        },
    }
    print(json.dumps(concise, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
