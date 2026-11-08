#!/usr/bin/env python3
"""Audit every cyclic start of a small deterministic lesson schedule.

From a reviewer packet root::

    python3 run_with_racket.py python3 \
      generators/e521d16d403e/workspace/check_lesson_windows.py \
      --period 4 --seeds 0,1,17 --bands easy,medium,hard --train 3 --queries 1 \
      --out ../checks/lesson-windows.json

Copying this file into another task's workspace changes the default task ID.
The runtime/bootstrap must supply ``arcpuzzles`` and ``reviewer_support``.
Only the public ``Catalog.apply`` API supplies authoritative Racket outputs.

For each seed/band we draw sample indices 0..period+train+queries-2 exactly
once. Every start 0..period-1 uses its actual contiguous slice, including fresh
draws beyond the first period. Production reserves the final ``queries``
examples; each one-query rotation holds out one of the same window's examples
and uses *all* remaining examples as demonstrations. A surviving rival is
ambiguous only if its query answer differs. Agreement on the whole window is
reported separately and is not itself a failure.

All three rival dictionaries are discovered from the selected generator.
Predictions, inputs and reference outputs are stored once per unique input;
per-window witnesses refer to those exact records by input hash and retain
actual sample indices. The first failure also includes self-contained grids.
This is finite coverage of declared rivals and requested starts, not a proof
against undeclared hypotheses or untested seeds/overrides.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import time
from typing import Any


DECLARATIONS = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
BATCH_SIZE = 64


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_partition(rival_matches: Mapping[str, Mapping[int, bool | None]],
                    demo_indices: Sequence[int], query_indices: Sequence[int]) -> dict[str, Any]:
    """Score known predictions, preserving real sample indices and error states.

    ``None`` means a rival could not be evaluated, never a valid refutation.
    This pure function has no dependency on generator code or reference labels.
    """
    demos, queries = list(demo_indices), list(query_indices)
    if not rival_matches:
        raise ValueError("No named rivals to score")
    if not demos or not queries:
        raise ValueError("Both demonstration and query indices must be nonempty")
    if len(set(demos)) != len(demos) or len(set(queries)) != len(queries):
        raise ValueError("Repeated sample indices in a partition")
    if set(demos) & set(queries):
        raise ValueError("Demonstration and query indices overlap")
    result: dict[str, Any] = {
        "demo_indices": demos, "query_indices": queries, "rivals": {},
        "ambiguous_rivals": [], "unchanged_survivors": [], "error_rivals": [],
    }
    for name in sorted(rival_matches):
        flags = rival_matches[name]
        for index in [*demos, *queries]:
            if index not in flags or (flags[index] is not None and type(flags[index]) is not bool):
                raise ValueError(f"Missing/invalid prediction match for {name} sample {index}")
        refutations = [i for i in demos if flags[i] is False]
        differences = [i for i in queries if flags[i] is False]
        errors = [i for i in [*demos, *queries] if flags[i] is None]
        if errors:
            status = "error"
            result["error_rivals"].append(name)
        elif refutations:
            status = "refuted"
        elif differences:
            status = "ambiguous"
            result["ambiguous_rivals"].append(name)
        else:
            status = "unchanged_survivor"
            result["unchanged_survivors"].append(name)
        result["rivals"][name] = {
            "refuting_demo_indices": refutations,
            "differing_query_indices": differences,
            "error_indices": errors, "status": status,
        }
    return result


def collect_rivals(module: Any) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Freeze the declared callables; fail visibly on misleading name collisions."""
    rivals, groups = {}, {}
    for declaration in DECLARATIONS:
        declared = getattr(module, declaration, {})
        if not isinstance(declared, Mapping):
            raise ValueError(f"{declaration} must be a name -> callable mapping")
        for name, rival in declared.items():
            if not isinstance(name, str) or not name.strip() or not callable(rival):
                raise ValueError(f"Invalid named rival in {declaration}: {name!r}")
            if name in rivals and rivals[name] is not rival:
                raise ValueError(f"Different callables share rival name {name!r}; use distinct names")
            rivals[name] = rival
        groups[declaration] = sorted(declared)
    if not rivals:
        raise ValueError("No named rivals were declared")
    return dict(sorted(rivals.items())), groups


def generator_path(root: Path, task_id: str) -> Path:
    candidates = [root / "generators" / task_id / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / task_id / "generator.py"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No selected generator for {task_id} under {root}")


def _source_unchanged(source: Path, expected: str) -> None:
    if file_digest(source) != expected:
        raise RuntimeError("Generator source changed during the audit; no mixed-source pass is permitted")


def _load_generator(source: Path, source_bytes: bytes):
    name = "lesson_window_subject_" + hashlib.sha256(source_bytes).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Compile pinned source bytes so a stale .pyc cannot supply different code.
    exec(compile(source_bytes, str(source), "exec"), module.__dict__)
    return module


def _prediction(rival, grid, normalize_grid):
    """Copy both directions; catch mutation and directly observable nondeterminism."""
    predictions = []
    for _ in range(2):
        argument = copy.deepcopy(grid)
        value = rival(argument)
        if argument != grid:
            raise ValueError("Rival mutated its input")
        if value is None:
            raise ValueError("Rival returned None instead of an output grid")
        predictions.append(normalize_grid(value))
    if predictions[0] != predictions[1]:
        raise ValueError("Rival returned different predictions for the same input")
    return predictions[0]


def _add_input(pool: dict[str, Any], grid) -> str:
    key = digest(grid)
    if key in pool and pool[key]["input"] != grid:
        raise RuntimeError("Input hash collision")
    pool.setdefault(key, {"input": copy.deepcopy(grid)})
    return key


def _reference_outputs(catalog, task_id: str, pool: dict[str, Any], source: Path,
                       source_hash: str, rule_hash: str, report: dict[str, Any], normalize_grid):
    keys = list(pool)
    receipts = report.setdefault("reference", {}).setdefault("batches", [])
    stable = None
    for offset in range(0, len(keys), BATCH_SIZE):
        _source_unchanged(source, source_hash)
        batch_keys = keys[offset:offset + BATCH_SIZE]
        request = [copy.deepcopy(pool[key]["input"]) for key in batch_keys]
        applied = catalog.apply(task_id, request, timeout=120)
        _source_unchanged(source, source_hash)
        identity = {field: applied.get(field) for field in
                    ("generator_sha256", "rule_text_sha256", "executed_rule_hash")}
        receipt = {**identity, "batch_index": len(receipts), "input_count": len(batch_keys),
                   "input_hashes_sha256": digest(batch_keys),
                   "elapsed_seconds": applied.get("elapsed_seconds")}
        receipts.append(receipt)
        if not all(isinstance(value, str) and value for value in identity.values()):
            raise RuntimeError("Reference apply omitted required source/rule hashes")
        if identity["generator_sha256"] != source_hash:
            raise RuntimeError("Reference apply used a different generator source")
        if identity["executed_rule_hash"] != rule_hash:
            raise RuntimeError("Executed reference rule differs from the initially selected canonical rule")
        if applied.get("rule_hash_matches_catalog") is False:
            raise RuntimeError("Reference apply reports a canonical rule hash mismatch")
        if stable is not None and identity != stable:
            raise RuntimeError("Source or executed rule changed between reference batches")
        stable = identity
        rows = applied.get("results")
        if not isinstance(rows, list) or len(rows) != len(batch_keys):
            raise RuntimeError("Reference apply returned the wrong number of results")
        for key, row in zip(batch_keys, rows, strict=True):
            if not isinstance(row, dict) or row.get("input") != pool[key]["input"]:
                raise RuntimeError("Reference apply changed input order or returned the wrong input")
            if row.get("error"):
                raise RuntimeError(f"Reference failed on {key}: {str(row['error'])[:1000]}")
            if row.get("input_sha256", key) != key:
                raise RuntimeError("Reference apply input hash mismatch")
            output = normalize_grid(row.get("output"))
            output_hash = digest(output)
            if row.get("output_sha256", output_hash) != output_hash:
                raise RuntimeError("Reference apply output hash mismatch")
            pool[key].update({"authoritative_output": output,
                              "output_sha256": output_hash, "rivals": {}})
    report["reference"].update({"api": "Catalog.apply", "label_authority": "canonical Racket rule",
                                "batch_limit": BATCH_SIZE, "unique_inputs_applied": len(keys),
                                "stable_hashes": stable})


def _attach_witnesses(partition: dict[str, Any], samples: dict[int, str], pool: dict[str, Any]):
    witnesses = {}
    for name in partition["ambiguous_rivals"]:
        witnesses[name] = {
            "demonstrations": [{"sample_index": i, "input_sha256": samples[i]}
                               for i in partition["demo_indices"]],
            "disagreeing_queries": [{"sample_index": i, "input_sha256": samples[i]}
                                    for i in partition["rivals"][name]["differing_query_indices"]],
        }
    partition["failure_witnesses"] = witnesses


def _full_witness(name: str, partition: dict[str, Any], samples: dict[int, str],
                  pool: dict[str, Any], *, seed: int, band: str, start: int, mode: str):
    def example(index):
        key = samples[index]
        entry = pool[key]
        return {"sample_index": index, "input_sha256": key, "input": entry["input"],
                "authoritative_output": entry["authoritative_output"],
                "rival_output": entry["rivals"][name]["output"]}
    return {"rival": name, "seed": seed, "band": band, "start_sample_index": start,
            "mode": mode, "demonstrations": [example(i) for i in partition["demo_indices"]],
            "disagreeing_queries": [example(i) for i in
                                    partition["rivals"][name]["differing_query_indices"]]}


def audit(args, report: dict[str, Any]) -> None:
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

    root = find_root(__file__)
    source = generator_path(root, args.task_id)
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    canonical_file = canonical_path(root)
    canonical_hash = file_digest(canonical_file)
    report["source"] = {"root": str(root), "generator_path": str(source),
                        "generator_sha256": source_hash, "canonical_ledger_sha256": canonical_hash,
                        "checker_path": str(Path(__file__).resolve()),
                        "checker_sha256": file_digest(Path(__file__))}
    gen = _load_generator(source, source_bytes)
    rivals, groups = collect_rivals(gen)
    report["declarations"] = groups
    report["source"]["generator_version"] = str(getattr(gen, "VERSION", "undeclared"))
    report["source"]["declared_rule_hash"] = getattr(gen, "RULE_HASH", None)
    catalog = Catalog(root)
    description = catalog.describe(args.task_id)
    if description["generator_sha256"] != source_hash:
        raise RuntimeError("Catalog selected a different generator source")
    rule_hash = description["rule_hash"]
    if not rule_hash:
        raise ValueError("No canonical rule hash is available")
    report["source"]["catalog_rule_hash"] = rule_hash

    pairs = canonical_pairs(args.task_id, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("No labeled canonical pairs; canonical-fit cannot be established")
    pool: dict[str, Any] = report.setdefault("inputs", {})
    canonical_records = []
    for ordinal, pair in enumerate(pairs):
        key = _add_input(pool, pair["input"])
        canonical_records.append({"canonical_index": ordinal, "variant": pair["variant"],
                                  "split": pair["split"], "pair_index": pair["pair_index"],
                                  "input_sha256": key, "ledger_output_sha256": digest(pair["output"])})
    report["canonical"] = {"labeled_pair_count": len(pairs),
                            "unique_input_count": len(pool), "pairs": canonical_records}

    sequence_length = args.period + args.train + args.queries - 1
    sequences = report.setdefault("sequences", [])
    for band in args.bands:
        for seed in args.seeds:
            samples = []
            for index in range(sequence_length):
                try:
                    grid = normalize_grid(gen.generate(seed, index, difficulty=band))
                except Exception as exc:
                    report["errors"].append({"stage": "generation", "seed": seed, "band": band,
                                             "sample_index": index,
                                             "error": f"{type(exc).__name__}: {str(exc)[:1000]}"})
                    raise RuntimeError(f"Generation failed at seed={seed}, band={band}, sample_index={index}") from exc
                key = _add_input(pool, grid)
                samples.append({"sample_index": index, "input_sha256": key})
            sequences.append({"seed": seed, "band": band, "samples": samples,
                              "unique_input_count": len({s["input_sha256"] for s in samples})})
    _source_unchanged(source, source_hash)
    _reference_outputs(catalog, args.task_id, pool, source, source_hash, rule_hash, report, normalize_grid)

    for key, entry in pool.items():
        for name, rival in rivals.items():
            try:
                prediction = _prediction(rival, entry["input"], normalize_grid)
                entry["rivals"][name] = {"output": prediction, "output_sha256": digest(prediction),
                                           "matches": prediction == entry["authoritative_output"]}
            except Exception as exc:
                error = {"stage": "rival_prediction", "rival": name, "input_sha256": key,
                         "error": f"{type(exc).__name__}: {str(exc)[:1000]}"}
                report["errors"].append(error)
                entry["rivals"][name] = {"matches": None, "error": error["error"]}

    canonical_mismatches = []
    for pair, record in zip(pairs, canonical_records, strict=True):
        entry = pool[record["input_sha256"]]
        if pair["output"] != entry["authoritative_output"]:
            mismatch = {**record, "ledger_output": pair["output"],
                        "authoritative_output": entry["authoritative_output"]}
            canonical_mismatches.append(mismatch)
            report["errors"].append({"stage": "canonical_reference", **mismatch})
    fit, counterexamples = {}, {}
    for name in rivals:
        flags = [pool[p["input_sha256"]]["rivals"][name]["matches"] for p in canonical_records]
        fit[name] = None if any(flag is None for flag in flags) else all(flags)
        counterexamples[name] = [p["canonical_index"] for p, flag in zip(canonical_records, flags, strict=True)
                                 if flag is not True]
    shortcut_fit = {name: fit[name] for name in groups["CANONICAL_SHORTCUTS"]}
    report["canonical"].update({"all_named_rival_fit": fit,
                                 "declared_shortcut_fit": shortcut_fit,
                                 "counterexample_pair_indices": counterexamples,
                                 "reference_ledger_mismatches": canonical_mismatches})
    for name, fits in shortcut_fit.items():
        if fits is not True:
            report["errors"].append({"stage": "canonical_shortcut_declaration", "rival": name,
                                     "canonical_pair_indices": counterexamples[name],
                                     "error": "Declared canonical shortcut does not fit every labeled canonical pair"})

    windows = report.setdefault("windows", [])
    counts = {"production": Counter(), "one_query_rotation": Counter()}
    survivor_counts = {"production": Counter(), "one_query_rotation": Counter()}
    refuted_counts = {"production": Counter(), "one_query_rotation": Counter()}
    width = args.train + args.queries
    for sequence in sequences:
        samples = {s["sample_index"]: s["input_sha256"] for s in sequence["samples"]}
        matches = {name: {i: pool[key]["rivals"][name]["matches"] for i, key in samples.items()}
                   for name in rivals}
        for start in range(args.period):
            indices = list(range(start, start + width))
            production = score_partition(matches, indices[:args.train], indices[args.train:])
            rotations = [score_partition(matches, [i for i in indices if i != query], [query])
                         for query in indices]
            window = {"seed": sequence["seed"], "band": sequence["band"],
                      "start_sample_index": start, "sample_indices": indices,
                      "production": production, "one_query_rotations": rotations}
            windows.append(window)
            for mode, partition in [("production", production),
                                    *[("one_query_rotation", r) for r in rotations]]:
                _attach_witnesses(partition, samples, pool)
                counts[mode]["windows"] += 1
                counts[mode]["ambiguous_windows"] += bool(partition["ambiguous_rivals"])
                counts[mode]["ambiguous_rival_cases"] += len(partition["ambiguous_rivals"])
                counts[mode]["error_windows"] += bool(partition["error_rivals"])
                survivor_counts[mode].update(partition["unchanged_survivors"])
                refuted_counts[mode].update(name for name, result in partition["rivals"].items()
                                           if result["status"] == "refuted")
                if partition["ambiguous_rivals"] and "first_failure_witness" not in report:
                    report["first_failure_witness"] = _full_witness(
                        partition["ambiguous_rivals"][0], partition, samples, pool,
                        seed=sequence["seed"], band=sequence["band"], start=start, mode=mode)

    _source_unchanged(source, source_hash)
    if file_digest(canonical_file) != canonical_hash:
        raise RuntimeError("Canonical ledger changed during the audit")
    final_description = Catalog(root).describe(args.task_id)
    if (final_description["generator_sha256"] != source_hash
            or final_description["rule_hash"] != rule_hash):
        raise RuntimeError("Final catalog source/rule identity changed during the audit")
    report["source"]["unchanged_through_completion"] = True
    generated_keys = {sample["input_sha256"] for sequence in sequences for sample in sequence["samples"]}
    report["summary"] = {
        "named_rival_count": len(rivals), "canonical_shortcut_count": len(shortcut_fit),
        "generated_sample_count": len(sequences) * sequence_length,
        "generated_unique_input_count": len(generated_keys), "unique_input_count": len(pool),
        "unique_output_count": len({entry["output_sha256"] for entry in pool.values()}),
        "production": dict(counts["production"]),
        "one_query_rotation": dict(counts["one_query_rotation"]),
        "unchanged_survivor_counts": {mode: {name: values[name] for name in rivals}
                                      for mode, values in survivor_counts.items()},
        "refuted_window_counts": {mode: {name: values[name] for name in rivals}
                                   for mode, values in refuted_counts.items()},
        "per_band_generated_unique_input_count": {
            band: len({sample["input_sha256"] for sequence in sequences if sequence["band"] == band
                       for sample in sequence["samples"]}) for band in args.bands},
    }
    expected_windows = len(args.seeds) * len(args.bands) * args.period
    report["passed"] = bool(
        not report["errors"] and all(value is True for value in shortcut_fit.values())
        and counts["production"]["windows"] == expected_windows
        and counts["one_query_rotation"]["windows"] == expected_windows * width
        and not any(c["ambiguous_windows"] or c["error_windows"] for c in counts.values())
    )


def _csv(value: str) -> list[str]:
    result = [part.strip() for part in value.split(",") if part.strip()]
    if not result:
        raise argparse.ArgumentTypeError("Expected a nonempty comma-separated list")
    if len(result) != len(set(result)):
        raise argparse.ArgumentTypeError("Duplicate list entries are not allowed")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task-id", default=Path(__file__).resolve().parents[1].name)
    parser.add_argument("--period", type=int, default=4)
    parser.add_argument("--seeds", type=_csv, default=_csv("0,1,17"))
    parser.add_argument("--bands", type=_csv, default=_csv("easy,medium,hard"))
    parser.add_argument("--train", type=int, default=3)
    parser.add_argument("--queries", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True, help="New output JSON path; never overwritten")
    args = parser.parse_args(argv)
    if min(args.period, args.train, args.queries) < 1:
        parser.error("--period, --train and --queries must be positive")
    try:
        args.seeds = [int(seed) for seed in args.seeds]
    except ValueError:
        parser.error("--seeds must contain integers")
    if len(args.seeds) != len(set(args.seeds)):
        parser.error("--seeds must not contain duplicate integer values")
    if any(band not in {"easy", "medium", "hard"} for band in args.bands):
        parser.error("--bands must select from easy,medium,hard")
    output = args.out.absolute()
    if output.exists() or output.is_symlink():
        parser.error("--out must be a new path")
    actual_argv = [sys.executable, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)]
    report = {"schema": "arcpuzzles-lesson-windows-v1", "task_id": args.task_id, "passed": False,
              "started_utc": datetime.now(timezone.utc).isoformat(), "errors": [],
              "invocation": {"cwd": str(Path.cwd()), "argv": actual_argv,
                             "command": shlex.join(actual_argv)},
              "configuration": {"period": args.period, "seeds": args.seeds, "bands": args.bands,
                                "train": args.train, "queries": args.queries,
                                "sequence_length_per_seed_band": args.period + args.train + args.queries - 1,
                                "actual_start_indices": list(range(args.period)),
                                "rotation_demo_count": args.train + args.queries - 1},
              "evidence_format": "inputs[input_sha256] contains each exact input, Racket output and rival prediction; "
                                 "window witness indices refer to the retained seed/band sequence, never modulo repeats",
              "scope": "All requested cyclic starts; finite declared-rival evidence for these seeds/bands only"}
    started = time.monotonic()
    try:
        audit(args, report)
    except Exception as exc:
        report["errors"].append({"stage": "audit", "error": f"{type(exc).__name__}: {str(exc)[:2000]}"})
        report["passed"] = False
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["error_count"] = len(report["errors"])
    output.parent.mkdir(parents=True, exist_ok=True)
    # Compact, deduplicated storage keeps the default census well below 2 MiB.
    encoded = json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n"
    with output.open("x", encoding="utf-8") as handle:
        handle.write(encoded)
    print(json.dumps({"passed": report["passed"], "error_count": report["error_count"],
                      "summary": report.get("summary"), "out": str(output),
                      "report_bytes": len(encoded.encode("utf-8"))}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
