#!/usr/bin/env python3
"""Source-bound large lesson probe for generator 4179e1ac3cf7.

The parent process stages the current repository generator with arcpuzzles'
portable runtime.  A worker then keeps one canonical Racket bridge open while
materializing real 4-demo/1-query lessons.  It dynamically iterates the final
generator's SEMANTIC_WITNESSES, LESSON_COMPETITORS, and CANONICAL_SHORTCUTS;
there is no copied rival-name list to drift.

This tool measures whether named rivals are distinguished on this finite pinned
sample.  It does not claim universal rule induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TASK_ID = "4179e1ac3cf7"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11
SCHEMA = "4179e1ac3cf7-lesson-probe-v1"


def _repo_root() -> Path:
    """Repository root in the retained source layout (not worker staging)."""
    return Path(__file__).resolve().parents[3]


def pinned_seed(band: str, index: int) -> int:
    """Stable independent lesson seed; fully specified in the JSON report."""
    payload = f"{TASK_ID}|{SCHEMA}|{band}|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def lesson_plan(
    per_band: int, *, n_demos: int = 4, n_queries: int = 1
) -> list[dict[str, Any]]:
    if per_band < 1:
        raise ValueError("per_band must be positive")
    if n_demos < 1 or n_queries < 1:
        raise ValueError("n_demos and n_queries must be positive")
    # A stride larger than one lesson window makes start-index windows disjoint
    # within each band.  Seeds are also independently varied.
    if LESSON_SAMPLE_STRIDE < n_demos + n_queries:
        raise ValueError("lesson stride is smaller than the lesson window")
    return [
        {
            "band": band,
            "ordinal": index,
            "seed": pinned_seed(band, index),
            "sample_index": index * LESSON_SAMPLE_STRIDE,
            "n_demos": n_demos,
            "n_queries": n_queries,
        }
        for band in BANDS
        for index in range(per_band)
    ]


def grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counter_json(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def _canonical_pairs(path: Path) -> tuple[dict, list[dict]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID or row.get("content_hash") == TASK_ID:
                test = row.get("test") or []
                if isinstance(test, dict):
                    test = [test]
                return row, list(row.get("train") or []) + list(test)
    raise ValueError(f"canonical row {TASK_ID} not found in {path}")


def _worker(request_path: Path, result_path: Path) -> int:
    """Execute inside an arcpuzzles staged runtime."""
    request = json.loads(request_path.read_text())
    plan = request["plan"]
    from puzzle_generators import runner

    bundle = runner._load_bundle(TASK_ID)
    module = bundle.generator_module
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)

    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}) or {})
    witnesses = dict(getattr(module, "SEMANTIC_WITNESSES", {}) or {})
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}) or {})
    lesson_hook = getattr(module, "lesson_identifiable", None)
    strict_hook = getattr(module, "strict_canonical_like", None)
    python_rule = getattr(module, "rule_mirror", None)
    observe = getattr(module, "observe_overrides", None)

    stats: dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "racket_rule": {
            "source_label": bundle.rule_file,
            "sha256": hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
            "normalized_sha12": hashlib.sha256(
                " ".join(bundle.rule_source.split()).encode()
            ).hexdigest()[:12],
        },
        "staged_generator": {
            "path": str(Path(module.__file__).resolve()),
            "sha256": file_hash(Path(module.__file__).resolve()),
        },
        "declared_names": {
            "witnesses": sorted(witnesses),
            "competitors": sorted(competitors),
            "canonical_shortcuts": sorted(shortcuts),
        },
        "sampler": {
            "lesson_assembly": "runner.run_one with 4 sequential demos and 1 sequential query",
            "labels": "selected canonical Racket authority through one persistent bridge",
            "bands": list(BANDS),
            "seed_formula": f"sha256('{TASK_ID}|{SCHEMA}|<band>|<ordinal>')[:8] as unsigned big-endian integer",
            "sample_index_formula": f"ordinal * {LESSON_SAMPLE_STRIDE}",
            "sample_stride": LESSON_SAMPLE_STRIDE,
            "plan": plan,
            "axis_domains": getattr(module, "AXES", {}),
            "weighted_options": {},
        },
        "totals": Counter(),
        "per_band": {},
        "axis_values": {},
        "witnesses": {},
        "competitors": {},
        "canonical_shortcuts": {},
        "errors": [],
        "error_examples": [],
        "limitations": [
            "Finite pinned sample; disagreement rates do not establish universal induction.",
            "Lessons use the repository runner's duplicate/rejection policy, so replay is defined by the recorded seed, start index, and source hashes.",
        ],
    }

    weighted = getattr(module, "_weighted_options", None)
    if callable(weighted):
        for band in BANDS:
            stats["sampler"]["weighted_options"][band] = {
                axis: list(weighted(axis, band)) for axis in getattr(module, "AXES", {})
            }

    global_inputs: set[str] = set()
    per_band_inputs: dict[str, set[str]] = {band: set() for band in BANDS}
    axis_values: dict[str, Counter] = {
        axis: Counter() for axis in getattr(module, "AXES", {})
    }
    witness_counts = {
        name: Counter(
            input_hits=0,
            demo_hits=0,
            query_hits=0,
            lessons_with_demo_hit=0,
            lessons_with_any_hit=0,
        )
        for name in witnesses
    }
    competitor_counts = {
        name: Counter(
            input_disagreements=0,
            input_agreements=0,
            lessons_refuted_by_demos=0,
            lessons_survived_all=0,
            lessons_query_discriminates=0,
            errors=0,
        )
        for name in competitors
    }

    try:
        for lesson_index, spec in enumerate(plan):
            band = spec["band"]
            band_stats = stats["per_band"].setdefault(
                band,
                Counter(
                    lessons=0,
                    inputs=0,
                    unique_inputs=0,
                    self_check_errors=0,
                    strict_errors=0,
                    python_racket_mismatches=0,
                    unidentifiable_lessons=0,
                    run_errors=0,
                ),
            )
            try:
                instance = runner.run_one(
                    TASK_ID,
                    seed=spec["seed"],
                    sample_index=spec["sample_index"],
                    n_train=spec["n_demos"],
                    n_test=spec["n_queries"],
                    difficulty=band,
                    bundle=bundle,
                    bridge=bridge,
                    fn_name=fn_name,
                )
            except Exception as exc:
                band_stats["run_errors"] += 1
                stats["totals"]["run_errors"] += 1
                stats["errors"].append(
                    f"lesson {lesson_index} ({band}, seed={spec['seed']}, start={spec['sample_index']}): "
                    f"run_one raised {type(exc).__name__}: {exc}"
                )
                continue

            demos = instance["train"]
            query = instance["test"][0]
            pairs = [("demo", i, pair) for i, pair in enumerate(demos)] + [
                ("query", 0, query)
            ]
            band_stats["lessons"] += 1
            stats["totals"]["lessons"] += 1

            lesson_witness_hits = {name: {"demo": 0, "query": 0} for name in witnesses}
            competitor_outputs: dict[str, list[tuple[str, bool]]] = {
                name: [] for name in competitors
            }

            for split, pair_index, pair in pairs:
                inp, authoritative = pair["input"], pair["output"]
                digest = grid_hash(inp)
                global_inputs.add(digest)
                per_band_inputs[band].add(digest)
                band_stats["inputs"] += 1
                stats["totals"]["inputs"] += 1

                findings = list(module.self_check(inp) or [])
                if findings:
                    band_stats["self_check_errors"] += 1
                    stats["totals"]["self_check_errors"] += 1
                    if len(stats["error_examples"]) < 12:
                        stats["error_examples"].append(
                            {
                                "kind": "self_check",
                                "replay": spec,
                                "split": split,
                                "pair_index": pair_index,
                                "input_sha256": digest,
                                "findings": findings,
                            }
                        )

                if callable(strict_hook):
                    strict_result = strict_hook(inp)
                    strict_findings = (
                        [] if strict_result is True else
                        ["predicate returned False"] if strict_result is False else
                        list(strict_result or [])
                    )
                    if strict_findings:
                        band_stats["strict_errors"] += 1
                        stats["totals"]["strict_errors"] += 1

                if callable(python_rule) and python_rule(inp) != authoritative:
                    band_stats["python_racket_mismatches"] += 1
                    stats["totals"]["python_racket_mismatches"] += 1
                    if len(stats["error_examples"]) < 12:
                        stats["error_examples"].append(
                            {
                                "kind": "python_racket_mismatch",
                                "replay": spec,
                                "split": split,
                                "pair_index": pair_index,
                                "input_sha256": digest,
                            }
                        )

                if callable(observe):
                    observed = observe(inp)
                    for axis, value in observed.items():
                        axis_values.setdefault(axis, Counter())[value] += 1

                for name, witness in witnesses.items():
                    try:
                        fired = bool(witness(inp))
                    except Exception as exc:
                        stats["totals"]["witness_errors"] += 1
                        stats["errors"].append(
                            f"witness {name} raised on {band}/{digest[:12]}: "
                            f"{type(exc).__name__}: {exc}"
                        )
                        continue
                    if fired:
                        witness_counts[name]["input_hits"] += 1
                        key = "demo" if split == "demo" else "query"
                        witness_counts[name][f"{key}_hits"] += 1
                        lesson_witness_hits[name][key] += 1

                for name, competitor in competitors.items():
                    try:
                        agrees = competitor(inp) == authoritative
                    except Exception as exc:
                        competitor_counts[name]["errors"] += 1
                        stats["totals"]["competitor_errors"] += 1
                        stats["errors"].append(
                            f"competitor {name} raised on {band}/{digest[:12]}: "
                            f"{type(exc).__name__}: {exc}"
                        )
                        continue
                    competitor_counts[name][
                        "input_agreements" if agrees else "input_disagreements"
                    ] += 1
                    competitor_outputs[name].append((split, agrees))

            for name, split_hits in lesson_witness_hits.items():
                if split_hits["demo"]:
                    witness_counts[name]["lessons_with_demo_hit"] += 1
                if split_hits["demo"] or split_hits["query"]:
                    witness_counts[name]["lessons_with_any_hit"] += 1

            for name, values in competitor_outputs.items():
                demo_agreements = [agrees for split, agrees in values if split == "demo"]
                query_agreements = [agrees for split, agrees in values if split == "query"]
                if len(demo_agreements) != len(demos) or len(query_agreements) != 1:
                    continue
                if not all(demo_agreements):
                    competitor_counts[name]["lessons_refuted_by_demos"] += 1
                elif query_agreements[0]:
                    competitor_counts[name]["lessons_survived_all"] += 1
                else:
                    competitor_counts[name]["lessons_query_discriminates"] += 1

            if callable(lesson_hook):
                try:
                    reasons = list(lesson_hook(demos, query) or [])
                except Exception as exc:
                    reasons = [f"hook raised {type(exc).__name__}: {exc}"]
                if reasons:
                    band_stats["unidentifiable_lessons"] += 1
                    stats["totals"]["unidentifiable_lessons"] += 1
                    if len(stats["error_examples"]) < 12:
                        stats["error_examples"].append(
                            {
                                "kind": "unidentifiable_lesson",
                                "replay": spec,
                                "reasons": reasons,
                            }
                        )
    finally:
        try:
            bridge.shutdown()
        except Exception as exc:
            stats["errors"].append(f"bridge shutdown raised {type(exc).__name__}: {exc}")

    stats["totals"] = _counter_json(stats["totals"])
    stats["totals"]["unique_inputs"] = len(global_inputs)
    for band, counter in list(stats["per_band"].items()):
        counter["unique_inputs"] = len(per_band_inputs[band])
        stats["per_band"][band] = _counter_json(counter)
    stats["axis_values"] = {
        axis: _counter_json(values) for axis, values in axis_values.items()
    }
    stats["witnesses"] = {
        name: _counter_json(values) for name, values in witness_counts.items()
    }
    stats["competitors"] = {
        name: _counter_json(values) for name, values in competitor_counts.items()
    }

    canonical_path = Path("puzzle_generators/data/canonical/puzzles.jsonl")
    if not canonical_path.exists():
        canonical_path = runner.CANONICAL_PUZZLES
    _, canonical_pairs = _canonical_pairs(canonical_path)
    for name, shortcut in shortcuts.items():
        record = {"pairs": len(canonical_pairs), "fits": 0, "errors": []}
        for index, pair in enumerate(canonical_pairs):
            try:
                if shortcut(pair["input"]) == pair["output"]:
                    record["fits"] += 1
            except Exception as exc:
                record["errors"].append(
                    f"pair {index}: {type(exc).__name__}: {exc}"
                )
        record["fits_all"] = record["fits"] == record["pairs"] and not record["errors"]
        stats["canonical_shortcuts"][name] = record

    # Fail only on objective contract failures.  A rival that survives all five
    # examples is reported as a limitation rather than promoted to universal
    # failure; a demo-fitting/query-changing rival is already counted by the
    # lesson hook as unidentifiable.
    objective_failures = (
        int(stats["totals"].get("run_errors", 0))
        + int(stats["totals"].get("self_check_errors", 0))
        + int(stats["totals"].get("strict_errors", 0))
        + int(stats["totals"].get("python_racket_mismatches", 0))
        + int(stats["totals"].get("unidentifiable_lessons", 0))
        + int(stats["totals"].get("witness_errors", 0))
        + int(stats["totals"].get("competitor_errors", 0))
        + len(stats["errors"])
        + sum(not row["fits_all"] for row in stats["canonical_shortcuts"].values())
    )
    for name, row in stats["witnesses"].items():
        if int(row.get("input_hits", 0)) == 0:
            objective_failures += 1
            stats["errors"].append(f"declared witness {name} never fired")
    for name, row in stats["competitors"].items():
        if int(row.get("input_disagreements", 0)) == 0:
            objective_failures += 1
            stats["errors"].append(f"declared competitor {name} never disagreed")

    stats["objective_failure_count"] = objective_failures
    stats["status"] = "pass" if objective_failures == 0 else "fail"
    result_path.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
    return 0 if objective_failures == 0 else 1


def _parent(args: argparse.Namespace) -> int:
    repo = _repo_root()
    generator_path = repo / "generators" / TASK_ID / "generator.py"
    canonical_path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    plan = lesson_plan(args.per_band, n_demos=4, n_queries=1)

    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(repo), stage, TASK_ID)
        worker_script = stage / "lesson_probe.py"
        shutil.copy2(Path(__file__).resolve(), worker_script)
        request_path = stage / "request.json"
        result_path = stage / "worker-result.json"
        request_path.write_text(json.dumps({"plan": plan}, separators=(",", ":")))
        result = run_process(
            [
                sys.executable,
                "-B",
                str(worker_script.name),
                "--worker",
                str(request_path.name),
                str(result_path.name),
            ],
            stage,
            timeout=args.timeout,
        )
        if result["timed_out"]:
            raise RuntimeError(f"worker timed out after {args.timeout}s")
        if not result_path.exists():
            raise RuntimeError(
                "worker produced no report; "
                f"exit={result['exit_code']} stdout={result['stdout'][-1000:]} "
                f"stderr={result['stderr'][-2000:]}"
            )
        report = json.loads(result_path.read_text())
        report["source_binding"] = {
            "generator_path": str(generator_path.relative_to(repo)),
            "generator_sha256": file_hash(generator_path),
            "probe_path": str(Path(__file__).resolve().relative_to(repo)),
            "probe_sha256": file_hash(Path(__file__).resolve()),
            "canonical_path": str(canonical_path.relative_to(repo)),
            "canonical_sha256": file_hash(canonical_path),
            "worker_exit_code": result["exit_code"],
            "worker_timed_out": result["timed_out"],
        }
        report["command_contract"] = {
            "cwd": "repo",
            "argv": [
                "python3",
                f"generators/{TASK_ID}/workspace/lesson_probe.py",
                "--per-band",
                str(args.per_band),
                "--out",
                str(args.out),
            ],
        }
        # The staged copy must be byte-identical to the retained source.
        staged_hash = report["staged_generator"]["sha256"]
        if staged_hash != report["source_binding"]["generator_sha256"]:
            report["status"] = "fail"
            report["objective_failure_count"] = int(report["objective_failure_count"]) + 1
            report["errors"].append(
                "staged generator hash does not match retained source generator"
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "status": report["status"],
        "generator_sha256": report["source_binding"]["generator_sha256"],
        "rule_hash": report["declared_rule_hash"],
        "lessons": report["totals"].get("lessons", 0),
        "inputs": report["totals"].get("inputs", 0),
        "unique_inputs": report["totals"].get("unique_inputs", 0),
        "per_band": report["per_band"],
        "competitors": report["competitors"],
        "witnesses": report["witnesses"],
        "objective_failure_count": report["objective_failure_count"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" and result["exit_code"] == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--worker", nargs=2, metavar=("REQUEST", "RESULT"))
    args = parser.parse_args(argv)
    if args.worker:
        return _worker(Path(args.worker[0]), Path(args.worker[1]))
    if args.out is None:
        parser.error("--out is required outside worker mode")
    return _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
