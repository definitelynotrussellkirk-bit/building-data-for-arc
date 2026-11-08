#!/usr/bin/env python3
"""Source-bound lesson census for ARC task c83b29b14c16.

The probe materializes real four-demo/one-query lessons with the selected
Racket authority.  It measures strict validity, uniqueness, exact-axis ranges,
witness coverage, named-rival disagreement, and lesson-level rival survival.
The finite census is curriculum evidence, not a proof against unlisted rules.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TASK_ID = "c83b29b14c16"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 4
N_QUERIES = 1
STRIDE = 11


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_hash(grid: Any) -> str:
    return _sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"c83b29b14c16:lesson-probe:v1:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _normalize_grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def _canonical_pairs(repo: Path) -> list[dict[str, list[list[int]]]]:
    path = repo / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            tests = row.get("test") or []
            tests = [tests] if isinstance(tests, dict) else tests
            return [
                {
                    "input": _normalize_grid(pair["input"]),
                    "output": _normalize_grid(pair["output"]),
                }
                for pair in [*(row.get("train") or []), *tests]
            ]
    raise FileNotFoundError(f"canonical task {TASK_ID} not found")


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def _worker(args: argparse.Namespace) -> int:
    import importlib
    from puzzle_generators import runner

    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    per_band = int(request["lessons_per_band"])
    canonical = request["canonical_pairs"]
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    if int(getattr(gen, "EXAMPLES_NEEDED", -1)) != N_DEMOS:
        raise AssertionError(
            f"probe expects {N_DEMOS} demos; generator declares "
            f"{getattr(gen, 'EXAMPLES_NEEDED', None)!r}"
        )

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {})
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)
    if not competitors:
        raise AssertionError("generator declares no lesson competitors")

    report: dict[str, Any] = {
        "schema": "c83b29b14c16-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_rule_hash": gen.RULE_HASH,
        "generator_sha256": _sha256_bytes(Path(gen.__file__).read_bytes()),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": per_band,
            "demos_per_lesson": N_DEMOS,
            "queries_per_lesson": N_QUERIES,
            "sample_index_start": "lesson_index * 11",
            "sample_index_stride": STRIDE,
            "within_lesson": "consecutive sample indexes",
            "seed": "first 12 hex digits of sha256(task:lesson-probe:v1:band:index)",
            "labels": "selected canonical Racket rule through puzzle_generators.runner.run_one",
        },
        "declared_domain": copy.deepcopy(gen.AXES),
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "canonical_shortcut_fit": {},
        "bands": {},
        "failures": [],
    }

    for name, rival in sorted(shortcuts.items()):
        matches = 0
        errors: list[str] = []
        for index, pair in enumerate(canonical):
            try:
                matches += int(rival(copy.deepcopy(pair["input"])) == pair["output"])
            except Exception as exc:  # fail loud
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        row = {
            "matches": matches,
            "denominator": len(canonical),
            "fits_all": matches == len(canonical) and not errors,
            "errors": errors,
        }
        report["canonical_shortcut_fit"][name] = row
        if not row["fits_all"]:
            report["failures"].append(
                {"type": "false_canonical_shortcut_claim", "rival": name, "detail": row}
            )

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    all_unique_inputs: set[str] = set()
    try:
        for band in BANDS:
            unique_inputs: set[str] = set()
            unique_pairs: set[str] = set()
            witness_hits = Counter()
            starts = Counter()
            observed_axes = {name: Counter() for name in gen.AXES}
            rival_stats = {
                name: Counter(
                    pair_disagreements=0,
                    query_disagreements=0,
                    lessons_refuted_by_demos=0,
                    lessons_survived_demos=0,
                    survived_demos_wrong_query=0,
                    errors=0,
                )
                for name in competitors
            }
            materialized = 0
            strict_pairs = 0
            identifiable = 0
            mirror_matches = 0
            pair_count = 0

            for lesson_index in range(per_band):
                seed = _seed(band, lesson_index)
                start = lesson_index * STRIDE
                starts[start % 4] += 1
                try:
                    lesson = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=start,
                        n_train=N_DEMOS,
                        n_test=N_QUERIES,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    report["failures"].append(
                        {
                            "type": "materialization_error",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                materialized += 1
                demos = lesson["train"]
                query = lesson["test"][0]
                reasons = list(gen.lesson_identifiable(demos, query) or [])
                if reasons:
                    report["failures"].append(
                        {
                            "type": "lesson_identifiability",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "reasons": reasons,
                        }
                    )
                else:
                    identifiable += 1

                pairs = [*demos, query]
                for offset, pair in enumerate(pairs):
                    pair_count += 1
                    grid = pair["input"]
                    output = pair["output"]
                    input_hash = _grid_hash(grid)
                    pair_hash = _sha256_bytes(
                        (input_hash + _grid_hash(output)).encode()
                    )
                    unique_inputs.add(input_hash)
                    all_unique_inputs.add(input_hash)
                    unique_pairs.add(pair_hash)

                    errors = list(gen.strict_canonical_like(grid) or [])
                    if errors:
                        report["failures"].append(
                            {
                                "type": "strict_validation",
                                "band": band,
                                "lesson_index": lesson_index,
                                "sample_index": start + offset,
                                "errors": errors,
                                "input_sha256": input_hash,
                            }
                        )
                    else:
                        strict_pairs += 1

                    try:
                        observed = gen.observe_overrides(grid)
                        for axis in gen.AXES:
                            observed_axes[axis][observed[axis]] += 1
                    except Exception as exc:
                        report["failures"].append(
                            {
                                "type": "observation_error",
                                "band": band,
                                "lesson_index": lesson_index,
                                "sample_index": start + offset,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )

                    try:
                        mirror = gen.rule_mirror(grid)
                        if mirror != output:
                            report["failures"].append(
                                {
                                    "type": "python_mirror_racket_mismatch",
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "sample_index": start + offset,
                                    "input_sha256": input_hash,
                                }
                            )
                        else:
                            mirror_matches += 1
                    except Exception as exc:
                        report["failures"].append(
                            {
                                "type": "mirror_error",
                                "band": band,
                                "lesson_index": lesson_index,
                                "sample_index": start + offset,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )

                    for name, witness in witnesses.items():
                        try:
                            witness_hits[name] += int(bool(witness(grid)))
                        except Exception as exc:
                            report["failures"].append(
                                {
                                    "type": "witness_error",
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "witness": name,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )

                    for name, rival in competitors.items():
                        try:
                            rival_stats[name]["pair_disagreements"] += int(
                                rival(copy.deepcopy(grid)) != output
                            )
                        except Exception as exc:
                            rival_stats[name]["errors"] += 1
                            report["failures"].append(
                                {
                                    "type": "competitor_error",
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "competitor": name,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )

                for name, rival in competitors.items():
                    stats = rival_stats[name]
                    try:
                        survives = all(
                            rival(copy.deepcopy(pair["input"])) == pair["output"]
                            for pair in demos
                        )
                        query_differs = rival(copy.deepcopy(query["input"])) != query["output"]
                    except Exception:
                        continue  # the per-pair path already recorded the concrete error
                    stats["query_disagreements"] += int(query_differs)
                    if survives:
                        stats["lessons_survived_demos"] += 1
                        stats["survived_demos_wrong_query"] += int(query_differs)
                        if query_differs:
                            report["failures"].append(
                                {
                                    "type": "rival_survived_demos_wrong_query",
                                    "band": band,
                                    "lesson_index": lesson_index,
                                    "sample_index": start,
                                    "competitor": name,
                                }
                            )
                    else:
                        stats["lessons_refuted_by_demos"] += 1

            report["bands"][band] = {
                "requested_lessons": per_band,
                "materialized_lessons": materialized,
                "identifiable_lessons": identifiable,
                "pair_observations": pair_count,
                "strict_pairs": strict_pairs,
                "python_mirror_racket_matches": mirror_matches,
                "unique_inputs": len(unique_inputs),
                "unique_input_output_pairs": len(unique_pairs),
                "start_residues_mod_4": _counter_dict(starts),
                "witness_hits": _counter_dict(witness_hits),
                "observed_axes": {
                    name: _counter_dict(values) for name, values in observed_axes.items()
                },
                "rivals": {
                    name: {key: int(value) for key, value in stats.items()}
                    for name, stats in sorted(rival_stats.items())
                },
            }
    finally:
        bridge.shutdown()

    report["unique_inputs_across_bands"] = len(all_unique_inputs)
    report["passed"] = not report["failures"]
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "failures": len(report["failures"]),
                "lessons_per_band": per_band,
                "unique_inputs_across_bands": report["unique_inputs_across_bands"],
                "generator_sha256": report["generator_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


def _parent(args: argparse.Namespace) -> int:
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    request = {
        "lessons_per_band": args.lessons_per_band,
        "canonical_pairs": _canonical_pairs(repo),
    }

    with tempfile.TemporaryDirectory(prefix="c83b29b14c16-lesson-probe-") as temp:
        stage = Path(temp)
        prepare_runtime(Catalog(repo), stage, TASK_ID)
        shutil.copy2(__file__, stage / "lesson_probe.py")
        (stage / "lesson-probe-request.json").write_text(
            json.dumps(request, indent=2) + "\n", encoding="utf-8"
        )
        run = run_process(
            [
                sys.executable,
                "-B",
                "lesson_probe.py",
                "--worker",
                "--request",
                "lesson-probe-request.json",
                "--output",
                "lesson-probe-report.json",
            ],
            stage,
            timeout=args.timeout,
        )
        report_path = stage / "lesson-probe-report.json"
        if report_path.exists():
            shutil.copy2(report_path, output)
        else:
            output.write_text(
                json.dumps(
                    {
                        "passed": False,
                        "failure": "worker produced no report",
                        "execution": run,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        manifest = stage / "RUNTIME_MANIFEST.json"
        receipt = {
            "schema": "c83b29b14c16-lesson-probe-execution-v1",
            "task_id": TASK_ID,
            "runtime_cwd": str(stage),
            "runtime_manifest_sha256": _sha256_bytes(manifest.read_bytes()),
            "probe_sha256": _sha256_bytes(Path(__file__).read_bytes()),
            "request": {
                "lessons_per_band": args.lessons_per_band,
                "bands": list(BANDS),
                "demos": N_DEMOS,
                "queries": N_QUERIES,
                "stride": STRIDE,
            },
            "execution": run,
            "reference": "selected canonical Racket authority via runner.run_one",
        }
        output.with_suffix(".execution.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        if run.get("stdout"):
            print(run["stdout"], end="")
        if run.get("stderr"):
            print(run["stderr"], file=sys.stderr, end="")
        return 124 if run.get("timed_out") else int(run.get("exit_code", 1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--request", default="lesson-probe-request.json", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.lessons_per_band < 100 and not args.worker:
        parser.error("review evidence requires at least 100 lessons per band")
    return _worker(args) if args.worker else _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
