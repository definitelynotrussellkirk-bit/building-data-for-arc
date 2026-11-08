#!/usr/bin/env python3
"""Input-only observable contrast candidates; no labels, rivals or Racket calls.

A uniform-demo axis followed by a different query value may merit inspection.
It is not a semantic failure, nor a requirement to demonstrate every query
value. Cross-version observer results are diagnostics, not final coverage.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def input_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--axis", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source, census_path = args.generator.resolve(), args.census.resolve()
    if args.out.exists():
        parser.error("--out must be a new JSON path")
    source_hash = digest(source.read_bytes())
    census_bytes = census_path.read_bytes()
    census = json.loads(census_bytes)
    spec = importlib.util.spec_from_file_location("lesson_contrast_observer", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    observer = getattr(module, "observe_overrides", None)
    if not callable(observer):
        parser.error("provided generator has no callable observe_overrides")
    axes = list(dict.fromkeys(args.axis))
    results = {axis: {kind: {"cases": 0, "contrast_candidates": 0, "first_cases": []}
                      for kind in ("production", "rotations")} for axis in axes}
    skipped = []
    for ordinal, lesson in enumerate(census.get("lessons", [])):
        instance = lesson.get("instance")
        address = {"census_lesson_ordinal": ordinal,
                   **{key: lesson.get(key) for key in ("band", "index", "seed", "sample_index")}}
        if not isinstance(instance, dict):
            skipped.append(address)
            continue
        train, queries = instance.get("train", []), instance.get("test", [])
        pairs = train + queries
        grids = [pair["input"] for pair in pairs]
        observed = [observer(deepcopy(grid)) for grid in grids]
        for values in observed:
            if not isinstance(values, dict) or any(axis not in values for axis in axes):
                parser.error(f"observer omitted requested axes at lesson {ordinal}")
        hashes = [input_hash(grid) for grid in grids]
        cases = [("production", list(range(len(train))), len(train) + q)
                 for q in range(len(queries))]
        cases += [("rotations", [i for i in range(len(pairs)) if i != q], q)
                  for q in range(len(pairs))]
        for kind, demo_indices, query_index in cases:
            for axis in axes:
                row = results[axis][kind]
                row["cases"] += 1
                demo_values = [observed[i][axis] for i in demo_indices]
                query_value = observed[query_index][axis]
                if (demo_values and all(value == demo_values[0] for value in demo_values)
                        and query_value != demo_values[0]):
                    row["contrast_candidates"] += 1
                    if len(row["first_cases"]) < 5:
                        row["first_cases"].append({
                            "lesson_address": address, "demo_pair_indices": demo_indices,
                            "query_pair_index": query_index, "demo_values": demo_values,
                            "query_value": query_value,
                            "demo_input_sha256": [hashes[i] for i in demo_indices],
                            "query_input_sha256": hashes[query_index]})
    # Bind the imported observer to stable source bytes before publishing.
    if digest(source.read_bytes()) != source_hash:
        parser.error("generator source changed while probing; no report written")
    same_source = source_hash == census.get("generator_sha256")
    report = {
        "schema": "observable-lesson-contrast-candidates-v1",
        "status": "diagnostic_contrast_candidates",
        "generator_path": str(source), "generator_sha256": source_hash,
        "census_path": str(census_path), "census_sha256": digest(census_bytes),
        "census_generator_sha256": census.get("generator_sha256"),
        "same_source": same_source,
        "observer_basis": "same_source_observer_diagnostic" if same_source
                          else "cross_version_observer_diagnostic",
        "axes": results, "materialized_lessons": len(census.get("lessons", [])) - len(skipped),
        "skipped_unmaterialized_lessons": len(skipped), "first_skipped_addresses": skipped[:5],
        "limits": ["Input-only contrast candidates, not semantic failures or rival scores.",
                   "Uniform demonstrations need not demonstrate every possible query value.",
                   "Cross-version observers do not establish final-source lesson coverage.",
                   "Production cases use original train inputs; rotations hold out each input once."],
    }
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"same_source": same_source, "observer_basis": report["observer_basis"],
                      "axes": {axis: {kind: {key: value for key, value in row.items()
                                              if key != "first_cases"}
                                       for kind, row in kinds.items()}
                               for axis, kinds in results.items()}, "out": str(args.out)}))


if __name__ == "__main__":
    main()
