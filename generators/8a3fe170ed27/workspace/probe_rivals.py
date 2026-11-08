#!/usr/bin/env python3
"""Authoring probe: actual declared rivals, canonical fits, and Racket witnesses.

Run from the packet root, with a fresh output directory:
  python3 review.py run ../.venv/bin/python3 \
    generators/8a3fe170ed27/workspace/probe_rivals.py \
    --out ../checks/rival-probe

This scores individual source-bound inputs. It does not replace lesson-census
or claim lesson/query-rotation identifiability. No Python rule mirror labels
any input: labels come from canonical data and the public Catalog.apply API.
"""

import argparse
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "8a3fe170ed27"
DECLARATIONS = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def inventory(generator):
    """Keep same-name callable aliases together, preserving all declarations."""
    entries = []
    for namespace in DECLARATIONS:
        declaration = getattr(generator, namespace, {})
        if not isinstance(declaration, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        for name, function in sorted(declaration.items()):
            if not isinstance(name, str) or not callable(function):
                raise TypeError(f"Invalid rival declaration: {namespace}:{name}")
            existing = next((entry for entry in entries
                             if entry["name"] == name and entry["function"] is function), None)
            if existing is not None:
                existing["declared_in"].append(namespace)
            else:
                entries.append(dict(name=name, function=function, declared_in=[namespace]))
    if not entries:
        raise ValueError("No executable rivals are declared")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="fresh evidence directory")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--indices", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.seed < 0 or any(index < 0 for index in args.indices):
        parser.error("seed and indices must be nonnegative")
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {"schema": "row-wave-rival-probe-v1", "task_id": TASK_ID,
              "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "root": str(root), "errors": [], "status": "incomplete",
              "scope": "canonical fits and individual Racket-labeled counterexamples; no lesson claims"}
    try:
        generator, source, digest = load_selected_generator(TASK_ID, root=root)
        report.update(generator_source=str(source), generator_sha256=digest,
                      canonical_ledger_sha256=sha256(canonical_path(root)),
                      probe_sha256=sha256(__file__))
        entries = inventory(generator)
        canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        records = [{"origin": "canonical", "variant": pair["variant"],
                    "split": pair["split"], "pair_index": pair["pair_index"],
                    "input": pair["input"]} for pair in canonical]
        for band in ("easy", "default", "hard"):
            for index in args.indices:
                grid = generator.generate(args.seed, index,
                                          difficulty=None if band == "default" else band)
                records.append(dict(origin="generated", band=band, seed=args.seed,
                                    sample_index=index, input=grid))
        if len(records) > 64:
            raise ValueError("At most 64 total canonical/generated inputs per probe")
        save(args.out / "inputs.json", records)
        applied = Catalog(root).apply(
            TASK_ID, [record["input"] for record in records],
            reference="canonical", timeout=args.timeout, check_generator_domain=True)
        save(args.out / "racket.json", applied)
        report["authority"] = {key: applied[key] for key in (
            "reference", "rule_task_id", "executed_rule_hash", "catalog_rule_hash",
            "rule_hash_matches_catalog", "rule_text_sha256", "generator_sha256")}
        if applied["generator_sha256"] != digest or sha256(source) != digest:
            raise RuntimeError("Generator source changed during the probe")
        if not applied["rule_hash_matches_catalog"]:
            report["errors"].append("Executed rule hash differs from catalog")
        labels = applied["results"]
        if len(labels) != len(records):
            raise RuntimeError("Reference returned an incomplete label population")
        for i, label in enumerate(labels):
            if label.get("error") is not None or label.get("output") is None:
                report["errors"].append(f"Reference label failed for input {i}: {label.get('error')}")
            if label.get("generator_domain", {}).get("status") != "valid":
                report["errors"].append(f"Input {i} rejected by selected generator domain")
            if i < len(canonical) and label.get("output") != canonical[i]["output"]:
                report["errors"].append(f"Reference disagrees with canonical label {i}")
        if report["errors"]:
            raise RuntimeError("Reference/domain verification failed; see retained racket.json")

        report["canonical_pairs"] = len(canonical)
        report["generated_inputs"] = len(records) - len(canonical)
        report["rivals"] = []
        for entry in entries:
            function = entry["function"]
            evidence = {key: value for key, value in entry.items() if key != "function"}
            try:
                evidence["callable_source_sha256"] = hashlib.sha256(
                    inspect.getsource(function).encode()).hexdigest()
            except (OSError, TypeError):
                evidence["callable_source_sha256"] = None
            evidence.update(canonical_fit=0, canonical_total=len(canonical),
                            canonical_mismatch_indices=[], generated_refutation_indices=[], errors=[])
            for i, (record, label) in enumerate(zip(records, labels, strict=True)):
                supplied = deepcopy(record["input"])
                try:
                    prediction = normalize_grid(function(supplied))
                    if supplied != record["input"]:
                        raise ValueError("rival mutated its input")
                    if prediction != normalize_grid(function(deepcopy(record["input"]))):
                        raise ValueError("rival prediction is not deterministic")
                    different = prediction != label["output"]
                    if i < len(canonical):
                        evidence["canonical_fit"] += not different
                        if different:
                            evidence["canonical_mismatch_indices"].append(i)
                    elif different:
                        evidence["generated_refutation_indices"].append(i)
                        evidence.setdefault("first_counterexample", dict(
                            input_index=i, input_sha256=label["input_sha256"],
                            reference_output_sha256=label["output_sha256"], rival_output=prediction))
                except Exception as error:
                    evidence["errors"].append(dict(input_index=i, error=repr(error)))
            if evidence["errors"]:
                report["errors"].append(f"Rival {entry['name']} raised or violated purity")
            if "CANONICAL_SHORTCUTS" in entry["declared_in"]:
                if evidence["canonical_fit"] != len(canonical):
                    report["errors"].append(f"Shortcut {entry['name']} does not fit every canonical pair")
                if not evidence["generated_refutation_indices"]:
                    report["errors"].append(f"No generated counterexample for shortcut {entry['name']}")
            report["rivals"].append(evidence)
        report["generator_sha256_after"] = sha256(source)
        if report["generator_sha256_after"] != digest:
            report["errors"].append("Generator changed during rival scoring")
    except Exception as error:
        report["errors"].append(repr(error))
    report["status"] = "passed" if not report["errors"] else "failed"
    report["exit_code"] = 0 if report["status"] == "passed" else 1
    save(args.out / "report.json", report)
    print(json.dumps({key: report.get(key) for key in (
        "status", "exit_code", "generator_sha256", "canonical_pairs", "generated_inputs", "errors")},
        indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
