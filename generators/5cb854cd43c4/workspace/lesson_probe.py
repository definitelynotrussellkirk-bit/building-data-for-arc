#!/usr/bin/env python3
"""Source-bound 300-lesson identifiability probe for 5cb854cd43c4.

This is the higher-power companion to the small semantic battery smoke test. It
uses the semantic gate's pinned lesson plan unchanged, stages the *current task
source bytes* as the importable generator, and materializes every output through
the canonical Racket program via ``puzzle_generators.runner.run_one``.

The JSON report records enough provenance to replay the population exactly:
source/rule hashes, sampler module and constants, every replay tuple, per-band
uniqueness, witness counts, and rival disagreement/refutation counts. It makes
no claim outside the bounded generated domain described in ``domain_limits``.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
from typing import Any

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent
REPO = HERE.parents[3]
TOOLS = REPO / "shared" / "tools"
RUNTIME = REPO / "shared" / "runtime"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
TASK_ID = TASK_HOME.name
BANDS = ("easy", "medium", "hard")
LESSONS_TOTAL = 300
DEMOS_PER_LESSON = 3
QUERIES_PER_LESSON = 1


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _grid_key(grid: Any) -> str:
    return json.dumps(grid, separators=(",", ":"), sort_keys=True)


def _load_canonical_rule() -> str:
    with CANONICAL.open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                return source.strip()
    raise RuntimeError(f"canonical task {TASK_ID} not found in {CANONICAL}")


def _install_scripts_namespace() -> None:
    """Expose packet ``shared/tools`` under the package name used by tools."""
    package = types.ModuleType("scripts")
    package.__path__ = [str(TOOLS)]
    sys.modules["scripts"] = package


def _stage_source(overlay: Path) -> Path:
    """Stage exactly the reviewed generator bytes into a portable namespace."""
    package = overlay / "puzzle_generators"
    per_puzzle = package / "per_puzzle"
    target_dir = per_puzzle / TASK_ID
    target_dir.mkdir(parents=True)
    namespace_init = (
        "from pkgutil import extend_path\n"
        "__path__ = extend_path(__path__, __name__)\n"
    )
    (package / "__init__.py").write_text(namespace_init, encoding="utf-8")
    (per_puzzle / "__init__.py").write_text(namespace_init, encoding="utf-8")
    (target_dir / "__init__.py").write_text("", encoding="utf-8")
    target = target_dir / "generator.py"
    shutil.copy2(TASK_HOME / "generator.py", target)
    return target


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def run_probe() -> dict[str, Any]:
    source_path = TASK_HOME / "generator.py"
    source_sha = _sha256(source_path)
    canonical_source = _load_canonical_rule()
    canonical_sha = _sha256_bytes(canonical_source.encode("utf-8"))

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as tmp:
        overlay = Path(tmp)
        staged_source = _stage_source(overlay)
        sys.path.insert(0, str(RUNTIME))
        sys.path.insert(0, str(overlay))
        _install_scripts_namespace()

        from scripts.generator_semantic_gate import (  # type: ignore
            LESSON_SAMPLE_STRIDE,
            _lesson_plan,
            evaluate_competitors,
        )
        from puzzle_generators import runner

        module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        generator = importlib.import_module(module_name)
        if Path(generator.__file__).resolve() != staged_source.resolve():
            raise RuntimeError(
                "source binding failed: imported "
                f"{generator.__file__}, expected {staged_source}"
            )
        if _sha256(Path(generator.__file__)) != source_sha:
            raise RuntimeError("staged generator hash differs from reviewed source")

        plan = _lesson_plan(
            TASK_ID,
            LESSONS_TOTAL,
            bands=BANDS,
            pass_difficulty=True,
            legacy=False,
        )
        planned_by_band = Counter(band for band, *_rest in plan)
        expected_by_band = {band: 100 for band in BANDS}
        if dict(planned_by_band) != expected_by_band:
            raise RuntimeError(
                f"unexpected lesson quotas: {dict(planned_by_band)}"
            )

        bundle = runner.GeneratorBundle(
            task_id=TASK_ID,
            rule_task_id=TASK_ID,
            rule_source=canonical_source,
            rule_callable_text=runner.wrap_rule(canonical_source),
            rule_file="shared/data/canonical/puzzles.jsonl:program_solution",
            generator_module=generator,
            allow_identity_output=False,
            kind="per_puzzle",
        )
        bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)

        band_inputs: dict[str, set[str]] = defaultdict(set)
        band_outputs: dict[str, set[str]] = defaultdict(set)
        band_demo_inputs: dict[str, set[str]] = defaultdict(set)
        band_query_inputs: dict[str, set[str]] = defaultdict(set)
        witness_counts: dict[str, Counter[str]] = {
            name: Counter() for name in generator.SEMANTIC_WITNESSES
        }
        schedule_counts: dict[str, Counter[str]] = {
            band: Counter() for band in BANDS
        }
        rival_metrics: dict[str, dict[str, Counter[str]]] = {
            name: {
                "demo_disagreements": Counter(),
                "query_disagreements": Counter(),
                "lessons_refuted_by_demos": Counter(),
                "lessons_surviving_demos": Counter(),
                "lessons_surviving_all": Counter(),
                "lessons_query_discriminates": Counter(),
            }
            for name in generator.LESSON_COMPETITORS
        }
        identifiable = Counter()
        hook_errors: list[dict[str, Any]] = []
        mirror_disagreements: list[dict[str, Any]] = []
        replay: list[dict[str, Any]] = []

        try:
            for lesson_index, (band, seed, sample_index, axes) in enumerate(plan):
                instance = runner.run_one(
                    TASK_ID,
                    seed=seed,
                    sample_index=sample_index,
                    n_train=DEMOS_PER_LESSON,
                    n_test=QUERIES_PER_LESSON,
                    bundle=bundle,
                    bridge=bridge,
                    fn_name=fn_name,
                    **axes,
                )
                lesson = {
                    "index": lesson_index,
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "replay": (
                        f"band={band} seed={seed} sample_index={sample_index}"
                    ),
                    "demos": instance["train"],
                    "query": instance["test"][0],
                }
                evaluation = evaluate_competitors(
                    generator.LESSON_COMPETITORS,
                    lesson,
                )
                if evaluation["errors"]:
                    hook_errors.append({
                        "lesson": lesson["replay"],
                        "errors": evaluation["errors"],
                    })

                hook_reasons = generator.lesson_identifiable(
                    lesson["demos"], lesson["query"]
                )
                if not isinstance(hook_reasons, list):
                    hook_errors.append({
                        "lesson": lesson["replay"],
                        "errors": [
                            "lesson_identifiable returned "
                            f"{type(hook_reasons).__name__}, expected list"
                        ],
                    })
                    hook_reasons = ["invalid hook return"]
                if hook_reasons:
                    identifiable["failed"] += 1
                else:
                    identifiable["passed"] += 1

                pairs = [*lesson["demos"], lesson["query"]]
                pair_records: list[dict[str, Any]] = []
                for offset, pair in enumerate(pairs):
                    split = "demo" if offset < DEMOS_PER_LESSON else "query"
                    grid = pair["input"]
                    answer = pair["output"]
                    band_inputs[band].add(_grid_key(grid))
                    band_outputs[band].add(_grid_key(answer))
                    if split == "demo":
                        band_demo_inputs[band].add(_grid_key(grid))
                    else:
                        band_query_inputs[band].add(_grid_key(grid))

                    schedule = generator.schedule_profile(
                        seed, sample_index + offset, difficulty=band
                    )
                    schedule_counts[band][schedule] += 1
                    fired = []
                    for witness_name, witness in generator.SEMANTIC_WITNESSES.items():
                        if witness(grid):
                            witness_counts[witness_name][band] += 1
                            fired.append(witness_name)

                    mirror = generator.rule_mirror(grid)
                    if mirror != answer:
                        mirror_disagreements.append({
                            "lesson": lesson["replay"],
                            "offset": offset,
                            "canonical": answer,
                            "mirror": mirror,
                        })

                    rival_disagreements = []
                    for rival_name, rival in generator.LESSON_COMPETITORS.items():
                        if rival(grid) != answer:
                            rival_disagreements.append(rival_name)
                            metric = (
                                "demo_disagreements"
                                if split == "demo"
                                else "query_disagreements"
                            )
                            rival_metrics[rival_name][metric][band] += 1

                    pair_records.append({
                        "offset": offset,
                        "split": split,
                        "sample_index": sample_index + offset,
                        "schedule_profile": schedule,
                        "witnesses": sorted(fired),
                        "rival_disagreements": sorted(rival_disagreements),
                        "input_sha256": _sha256_bytes(
                            _grid_key(grid).encode("utf-8")
                        ),
                        "output_sha256": _sha256_bytes(
                            _grid_key(answer).encode("utf-8")
                        ),
                    })

                refuted = set(evaluation["refuted"])
                survived_demos = set(evaluation["survived_demos"])
                survived_all = set(evaluation["survived_all"])
                query_discriminates = set(evaluation["query_discriminates"])
                for rival_name in generator.LESSON_COMPETITORS:
                    metrics = rival_metrics[rival_name]
                    if rival_name in refuted:
                        metrics["lessons_refuted_by_demos"][band] += 1
                    if rival_name in survived_demos:
                        metrics["lessons_surviving_demos"][band] += 1
                    if rival_name in survived_all:
                        metrics["lessons_surviving_all"][band] += 1
                    if rival_name in query_discriminates:
                        metrics["lessons_query_discriminates"][band] += 1

                replay.append({
                    "lesson_index": lesson_index,
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty_axes": axes,
                    "generator_end_sample_index": instance.get(
                        "end_sample_index", sample_index + len(pairs)
                    ),
                    "hook_reasons": hook_reasons,
                    "competitor_evaluation": evaluation,
                    "pairs": pair_records,
                })
        finally:
            bridge.shutdown()

        per_band = {}
        for band in BANDS:
            per_band[band] = {
                "lessons": planned_by_band[band],
                "pairs": planned_by_band[band]
                * (DEMOS_PER_LESSON + QUERIES_PER_LESSON),
                "unique_inputs": len(band_inputs[band]),
                "unique_demo_inputs": len(band_demo_inputs[band]),
                "unique_query_inputs": len(band_query_inputs[band]),
                "unique_outputs": len(band_outputs[band]),
                "schedule_profiles": _counter_dict(schedule_counts[band]),
                "witness_firings": {
                    name: witness_counts[name][band]
                    for name in sorted(witness_counts)
                },
            }

        rivals = {}
        for name, metrics in sorted(rival_metrics.items()):
            rivals[name] = {
                metric_name: {
                    band: metric_counter[band] for band in BANDS
                }
                | {"total": sum(metric_counter.values())}
                for metric_name, metric_counter in metrics.items()
            }

        failures = []
        if hook_errors:
            failures.append(f"{len(hook_errors)} competitor/hook error records")
        if mirror_disagreements:
            failures.append(
                f"{len(mirror_disagreements)} Python mirror/Racket disagreements"
            )
        if identifiable["failed"]:
            failures.append(
                f"{identifiable['failed']} lessons not identified by hook"
            )
        for name, metrics in rivals.items():
            if metrics["lessons_surviving_demos"]["total"]:
                failures.append(
                    f"{name} survived demos in "
                    f"{metrics['lessons_surviving_demos']['total']} lessons"
                )

        return {
            "schema": "arc-generator-lesson-probe-v1",
            "task_id": TASK_ID,
            "status": "pass" if not failures else "fail",
            "failures": failures,
            "source_binding": {
                "reviewed_source": str(source_path.relative_to(REPO)),
                "generator_sha256": source_sha,
                "staged_import_path": str(staged_source),
                "staged_sha256": _sha256(staged_source),
                "module_file": str(generator.__file__),
                "generator_version": generator.VERSION,
                "declared_rule_hash": generator.RULE_HASH,
            },
            "rule_authority": {
                "source": "shared/data/canonical/puzzles.jsonl:program_solution",
                "program_solution_sha256": canonical_sha,
                "execution": (
                    "puzzle_generators.runner.run_one with one persistent "
                    "Racket bridge"
                ),
                "python_mirror_disagreements": len(mirror_disagreements),
                "mirror_disagreement_examples": mirror_disagreements[:5],
            },
            "sampler": {
                "planner": "scripts.generator_semantic_gate._lesson_plan",
                "runner": "puzzle_generators.runner.run_one",
                "legacy": False,
                "bands": list(BANDS),
                "lessons_total": LESSONS_TOTAL,
                "lessons_per_band": expected_by_band,
                "demos_per_lesson": DEMOS_PER_LESSON,
                "queries_per_lesson": QUERIES_PER_LESSON,
                "lesson_sample_stride": LESSON_SAMPLE_STRIDE,
                "seed_scheme": (
                    "_pinned_seed(task_id, f'lesson:{band}', k) from "
                    "canonical_profile_gate"
                ),
                "difficulty_passed": True,
                "within_lesson": (
                    "run_one starts at the planned sample_index, requests 3 "
                    "train and 1 test pair, and uses its normal validation, "
                    "deduplication, and bounded retry semantics"
                ),
            },
            "lesson_identifiability": {
                "passed": identifiable["passed"],
                "failed": identifiable["failed"],
                "error_records": hook_errors,
            },
            "per_band": per_band,
            "rivals": rivals,
            "domain_limits": [
                "Measured only the three declared canvases: 5x5 with 3 objects, 6x6 with 2 objects, and 8x7 with 3 objects.",
                "Measured only calibrated canonical, strict varied, split-color, and equal-size tie tuples admitted by self_check.",
                "Connectivity is same-color 4-connectivity; diagonal touching and other object models were not sampled as separate domains.",
                "Repeated colors are bounded to two disconnected components sharing a color; broader palette multiplicities were not sampled.",
                "The equal-size branch uses the generator's enumerated tie tuples; unsupported size tuples, including frozen-fixture 6x6 (3,3), are outside this domain.",
                "This finite 300-lesson probe demonstrates elimination of the two declared canonical-fitting rivals on the sampled curriculum; it is not a proof of universal induction or of all possible shortcut families.",
            ],
            "replay": replay,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("checks/lesson_probe_300.json"),
        help="JSON report path (default: checks/lesson_probe_300.json)",
    )
    args = parser.parse_args(argv)
    report = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "status": report["status"],
        "generator_sha256": report["source_binding"]["generator_sha256"],
        "lessons": report["sampler"]["lessons_total"],
        "per_band": report["per_band"],
        "rivals": report["rivals"],
        "failures": report["failures"],
        "report": str(args.out),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
