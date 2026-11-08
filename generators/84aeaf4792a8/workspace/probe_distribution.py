#!/usr/bin/env python3
"""Authoring-only sample support and declared-rival probe for this task.

Loads canonical answers and calls the public Racket authority. Never use this
script during a blind solve. It is a finite distribution check, not a lesson
identifiability test; use the public lesson-census command for assembled lessons.
Run through review.py run so the local public APIs and Racket are available.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from importlib import util
import json
from pathlib import Path
import sys
import time
import traceback

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "84aeaf4792a8"
BANDS = ("easy", "medium", "hard")


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_module(name, source):
    spec = util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {source}")
    module = util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def declarations(generator):
    result = {}
    # Preserve namespaces and use the actual declarations, including future
    # additions. A same-named callable in another namespace is not substituted.
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declared = getattr(generator, namespace, None)
        if not isinstance(declared, dict) or not declared:
            raise ValueError(f"Missing/non-dictionary {namespace}")
        for name, rival in declared.items():
            if not isinstance(name, str) or not name or not callable(rival):
                raise ValueError(f"Invalid {namespace} declaration: {name!r}")
            result[f"{namespace}.{name}"] = rival
    return result


def prediction(rival, grid):
    supplied = deepcopy(grid)
    predicted = rival(supplied)
    if supplied != grid:
        raise ValueError("Rival mutated its input")
    # Fail visibly on unserializable predictions; retain ordinary wrong grids
    # as counterexamples rather than treating them as reference outputs.
    json.dumps(predicted)
    return predicted


def summarize(rows, expected_classes, oracle, rival_names):
    shape_counts = Counter(oracle.rotation_key(component.cells)
                           for row in rows
                           for component in oracle.components(row["input"]))
    return {
        "samples": len(rows),
        "unique_inputs": len({row["input_sha256"] for row in rows}),
        "unique_racket_outputs": len({row["output_sha256"] for row in rows}),
        "observed": {
            axis: dict(sorted(Counter(str(row["observed"][axis]) for row in rows).items(),
                              key=lambda item: int(item[0])))
            for axis in ("grid_h", "grid_w", "n_components", "n_families", "n_distinct_colors")
        },
        "multiplicity_partitions": dict(sorted(Counter(
            "+".join(map(str, row["multiplicity_partition"])) for row in rows).items())),
        "shape_classes": {
            "observed_count": len(shape_counts),
            "supported_count": len(expected_classes),
            "observed": [{"cells": shape, "component_occurrences": shape_counts[shape]}
                         for shape in sorted(shape_counts)],
            "missing": sorted(expected_classes - shape_counts.keys()),
            "outside_documented_support": sorted(shape_counts.keys() - expected_classes),
        },
        "rival_refutations": {
            name: sum(row["rival_status"][name] == "refuted" for row in rows)
            for name in rival_names
        },
    }


def run(args, output, report):
    root = find_root(__file__)
    task = Path(__file__).resolve().parent.parent
    source = task / "generator.py"
    oracle_source = task / "tests/shape_matrix_oracle.py"
    generator_sha256 = file_hash(source)
    generator = load_module("distribution_generator_84aeaf4792a8", source)
    oracle = load_module("distribution_oracle_84aeaf4792a8", oracle_source)
    rivals = declarations(generator)
    catalog = Catalog(root)
    selected = catalog.describe(TASK_ID)
    if selected["generator_sha256"] != generator_sha256:
        raise ValueError("Loaded generator differs from the catalog selection")
    if selected["rule_hash"] != generator.RULE_HASH:
        raise ValueError("Generator rule pin differs from selected authority")
    report["source"] = {
        "generator": str(source.relative_to(root)),
        "generator_sha256": generator_sha256,
        "version": generator.VERSION,
        "declared_rule_hash": generator.RULE_HASH,
        "catalog_rule_hash": selected["rule_hash"],
        "oracle": str(oracle_source.relative_to(root)),
        "oracle_sha256": file_hash(oracle_source),
        "probe": str(Path(__file__).resolve().relative_to(root)),
        "probe_sha256": file_hash(__file__),
    }
    report["declarations"] = list(rivals)
    report["authority_calls"] = []
    report["canonical"] = []
    report["first_refutations"] = {}
    authority = output / "authority"
    authority.mkdir()
    rule_text_hash = None

    def apply_authority(inputs, label):
        nonlocal rule_text_hash
        if not 1 <= len(inputs) <= 64:
            raise ValueError("Racket batches must contain 1..64 inputs")
        index = len(report["authority_calls"])
        relative = f"authority/{index:02d}-{label}.json"
        call = {"api": "Catalog(root).apply", "task_id": TASK_ID,
                "reference": "canonical", "timeout": args.timeout,
                "inputs_count": len(inputs), "cwd": str(Path.cwd()),
                "evidence_path": relative}
        report["authority_calls"].append(call)
        write_json(output / "report.json", report)
        applied = catalog.apply(TASK_ID, inputs, reference="canonical", timeout=args.timeout)
        write_json(output / relative, applied)
        call["completed"] = True
        call["elapsed_seconds"] = applied["elapsed_seconds"]
        if (applied["generator_sha256"] != generator_sha256
                or applied["executed_rule_hash"] != generator.RULE_HASH
                or not applied["rule_hash_matches_catalog"]):
            raise ValueError(f"Source/authority binding mismatch in {relative}")
        if rule_text_hash is None:
            rule_text_hash = applied["rule_text_sha256"]
            report["source"]["rule_text_sha256"] = rule_text_hash
        elif rule_text_hash != applied["rule_text_sha256"]:
            raise ValueError("Rule bytes changed between Racket batches")
        if len(applied["results"]) != len(inputs):
            raise ValueError("Incomplete Racket result batch")
        for result, grid in zip(applied["results"], inputs, strict=True):
            if result["input"] != grid or result["error"] or not result["valid_output"]:
                raise ValueError(f"Invalid Racket result in {relative}: {result['index']}")
        print(f"Racket {label}: {len(inputs)} inputs checked", flush=True)
        return applied["results"], relative

    canon = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not canon:
        raise ValueError("No labeled canonical pairs")
    canonical_results = []
    for start in range(0, len(canon), 64):
        results, evidence = apply_authority([pair["input"] for pair in canon[start:start + 64]],
                                            f"canonical-{start}")
        canonical_results.extend((result, evidence) for result in results)
    for pair, (result, evidence) in zip(canon, canonical_results, strict=True):
        reference = result["output"]
        independent = oracle.solve(pair["input"])
        row = {**pair, "racket_output": reference, "independent_output": independent,
               "authority_evidence": evidence, "authority_result_index": result["index"],
               "rival_predictions": {name: prediction(rival, pair["input"])
                                     for name, rival in rivals.items()}}
        report["canonical"].append(row)
        if pair["output"] != reference or independent != reference:
            raise ValueError("Canonical label/independent oracle differs from Racket")
    report["canonical_fits"] = {
        name: {"pairs": len(canon),
               "fits": sum(row["rival_predictions"][name] == row["racket_output"]
                           for row in report["canonical"]),
               "fits_all": all(row["rival_predictions"][name] == row["racket_output"]
                               for row in report["canonical"])}
        for name in rivals
    }
    for name, result in report["canonical_fits"].items():
        if name.startswith("CANONICAL_SHORTCUTS.") and not result["fits_all"]:
            raise ValueError(f"Misdeclared canonical shortcut: {name}")

    all_rows = []
    expected_classes = oracle.supported_shape_classes()
    with (output / "samples.jsonl").open("x") as samples:
        for band in BANDS:
            for start in range(0, args.per_band, 64):
                batch = []
                for sample_index in range(start, min(start + 64, args.per_band)):
                    grid = generator.generate(args.seed, sample_index, difficulty=band)
                    oracle.assert_domain(grid)
                    reasons = generator.self_check(deepcopy(grid), difficulty=band)
                    if reasons:
                        raise ValueError(f"Invalid generated input {band}/{sample_index}: {reasons}")
                    batch.append({"id": f"{band}:{sample_index}",
                                  "replay": {"seed": args.seed, "sample_index": sample_index,
                                             "difficulty": band, "overrides": {}},
                                  "input": grid, "input_sha256": value_hash(grid),
                                  "observed": oracle.observed(grid),
                                  "multiplicity_partition": oracle.partition(grid)})
                results, evidence = apply_authority([row["input"] for row in batch],
                                                    f"{band}-{start}")
                for row, result in zip(batch, results, strict=True):
                    row.update({"output": result["output"],
                                "output_sha256": value_hash(result["output"]),
                                "independent_output": oracle.solve(row["input"]),
                                "authority_evidence": evidence,
                                "authority_result_index": result["index"],
                                "rival_status": {}})
                    if row["independent_output"] != row["output"]:
                        write_json(output / "authority-mismatch.json", row)
                        raise ValueError(f"Independent oracle differs from Racket on {row['id']}")
                    for name, rival in rivals.items():
                        predicted = prediction(rival, row["input"])
                        differs = predicted != row["output"]
                        row["rival_status"][name] = "refuted" if differs else "agrees"
                        if differs and name not in report["first_refutations"]:
                            report["first_refutations"][name] = {
                                "sample_id": row["id"], "replay": row["replay"],
                                "input": row["input"], "input_sha256": row["input_sha256"],
                                "racket_output": row["output"], "rival_output": predicted,
                                "authority_evidence": evidence,
                                "authority_result_index": result["index"],
                                "passes_self_check": True, "passes_independent_domain": True,
                            }
                    samples.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
                    all_rows.append(row)
                samples.flush()
                report["completed_samples"] = len(all_rows)
                write_json(output / "report.json", report)
    if file_hash(source) != generator_sha256:
        raise ValueError("Generator source changed during the probe")
    report["overall"] = summarize(all_rows, expected_classes, oracle, rivals)
    report["per_band"] = {band: summarize(
        [row for row in all_rows if row["replay"]["difficulty"] == band],
        expected_classes, oracle, rivals) for band in BANDS}
    report["status"] = "pass"
    print(json.dumps({"status": report["status"], "samples": len(all_rows),
                      "unique_inputs": report["overall"]["unique_inputs"],
                      "unique_racket_outputs": report["overall"]["unique_racket_outputs"],
                      "observed_shape_classes": report["overall"]["shape_classes"]["observed_count"],
                      "declared_rivals_with_refutations": len(report["first_refutations"])}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=128)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--out", type=Path, required=True,
                        help="New authoring evidence directory; existing paths are refused")
    args = parser.parse_args()
    if args.per_band < 1 or args.timeout <= 0:
        parser.error("--per-band and --timeout must be positive")
    output = args.out.resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"Refusing to overwrite existing evidence: {output}")
    started = time.monotonic()
    receipt = {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
               "started_utc": datetime.now(timezone.utc).isoformat(),
               "python_version": sys.version}
    report = {"schema": "shape-matrix-distribution-probe-v1", "task_id": TASK_ID,
              "status": "running", "completed_samples": 0,
              "population": {"seed": args.seed, "sample_indices": [0, args.per_band - 1],
                             "per_band": args.per_band, "bands": list(BANDS), "overrides": {}},
              "limitations": [
                  "Finite explicit-seed sample evidence; no proof of full stochastic support.",
                  "Single inputs are scored independently; witness frequency does not establish lesson identifiability.",
                  "Only actual CANONICAL_SHORTCUTS and LESSON_COMPETITORS declarations are scored.",
                  "Racket labels are authoring/audit evidence and do not change catalog approval.",
              ]}
    exit_code = 0
    try:
        run(args, output, report)
    except Exception as error:
        exit_code = 1
        report["status"] = "error"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        (output / "error.log").write_text(traceback.format_exc())
        if hasattr(error, "run"):
            write_json(output / "failed-process.json", error.run)
        print(f"Probe failed: {type(error).__name__}: {error}", file=sys.stderr)
    finally:
        write_json(output / "report.json", report)
        receipt.update({"exit_code": exit_code, "status": report["status"],
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "finished_utc": datetime.now(timezone.utc).isoformat(),
                        "evidence": [{"path": str(path.relative_to(output)),
                                      "bytes": path.stat().st_size, "sha256": file_hash(path)}
                                     for path in sorted(output.rglob("*")) if path.is_file()]})
        write_json(output / "receipt.json", receipt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
