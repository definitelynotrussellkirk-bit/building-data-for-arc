#!/usr/bin/env python3
"""Rescore retained version-4.0.1 Racket labels against one area-only rival.

This script uses only the standard library, does not load a generator, and
does not execute Racket. The complete materialized source census is retained
separately and bound by its full SHA-256. Outputs are never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import sys


TASK_ID = "12ace26107fd"
GENERATOR_SHA256 = "6ad956a18b488e22280ac6b6658cbbae8c68b4502b7db65980cf384019a8fc77"
CENSUS_SHA256 = "b829dd51375c8eadda5adb6d84d4c8907a0862ed19883eeb572fcfebe75961fc"
RIVAL_NAME = "canonical_area_lookup"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def normalize_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("missing nonempty grid")
    result = []
    for row in grid:
        if isinstance(row, str):
            row = [int(char) for char in row if not char.isspace()]
        if not isinstance(row, list) or not row:
            raise ValueError("missing nonempty row")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("expected literal ARC digits")
        result.append(row)
    if len({len(row) for row in result}) != 1:
        raise ValueError("ragged grid")
    return result


def foreground_area(grid):
    return sum(value not in (0, 9) for row in grid for value in row)


def area_lookup(grid):
    """Ignore geometry: reuse canonical size classes and a bounded count table."""
    size = foreground_area(grid)
    if not 3 <= size <= 14:
        raise ValueError("rival is defined on the selected generator's area 3..14")
    canonical_sizes = {5: [[4, 1]], 9: [[8, 1]], 13: [[8, 4, 1]], 14: [[9, 4, 1]]}
    if size in canonical_sizes:
        return canonical_sizes[size]
    return [[9, size - 9]] if 10 <= size <= 12 else [[size]]


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--canonical-ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--counterexample", type=Path, required=True)
    args = parser.parse_args(argv)
    census_raw = args.census.read_bytes()
    if digest(census_raw) != CENSUS_SHA256:
        raise ValueError("source census changed; this replay is pinned to its original bytes")
    data = json.loads(census_raw)
    if data["task_id"] != TASK_ID or data["generator_sha256"] != GENERATOR_SHA256:
        raise ValueError("unexpected generator source binding")
    canonical_rows = [json.loads(line) for line in args.canonical_ledger.read_text().splitlines()
                      if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    canonical_checks = []
    for record in canonical_rows:
        for split in ("train", "test"):
            pairs = record.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for index, pair in enumerate(pairs):
                if split == "test" and "output" not in pair:
                    continue
                inp, expected = normalize_grid(pair["input"]), normalize_grid(pair["output"])
                prediction = area_lookup(inp)
                if prediction != expected:
                    raise ValueError("rival does not fit every labeled canonical pair")
                canonical_checks.append({"split": split, "pair_index": index, "input": inp,
                                         "expected": expected, "rival_prediction": prediction})
    if len(canonical_checks) != 3:
        raise ValueError("canonical population changed")

    totals = Counter()
    per_band = {}
    rows = []
    input_hashes, ambiguous_query_hashes = set(), set()
    first_counterexample = None
    for lesson in data["lessons"]:
        instance = lesson["instance"]
        if digest(normalized_json(instance)) != lesson["instance_sha256"]:
            raise ValueError("materialized lesson hash mismatch")
        train, test = instance["train"], instance["test"]
        if len(train) != 5 or len(test) != 1:
            raise ValueError("expected five demonstrations and one query")
        pairs = train + test
        predictions = [normalize_grid(area_lookup(pair["input"])) for pair in pairs]
        expected = [normalize_grid(pair["output"]) for pair in pairs]
        matches = [pred == out for pred, out in zip(predictions, expected)]
        production_ambiguous = all(matches[:5]) and not matches[5]
        rotations = [{"query_index": index, "all_demonstrations_match": all(
                          match for other, match in enumerate(matches) if other != index),
                      "query_matches": matches[index],
                      "ambiguous": not matches[index] and all(
                          match for other, match in enumerate(matches) if other != index)}
                     for index in range(6)]
        row = {key: lesson[key] for key in ("band", "index", "seed", "sample_index", "instance_sha256")}
        row.update({"pair_areas": [foreground_area(pair["input"]) for pair in pairs],
                    "reference_outputs": expected, "rival_predictions": predictions,
                    "production_ambiguous": production_ambiguous, "rotations": rotations})
        rows.append(row)
        band_counts = per_band.setdefault(lesson["band"], Counter())
        for count in (totals, band_counts):
            count["lessons"] += 1
            count["production_ambiguous"] += production_ambiguous
            count["rotations"] += len(rotations)
            count["rotations_ambiguous"] += sum(item["ambiguous"] for item in rotations)
        for index, pair in enumerate(pairs):
            identity = digest(normalized_json(pair["input"]))
            input_hashes.add(identity)
            if rotations[index]["ambiguous"]:
                ambiguous_query_hashes.add(identity)
        if production_ambiguous and first_counterexample is None:
            first_counterexample = {**row, "instance": instance,
                "query_expected": expected[5], "query_rival_prediction": predictions[5]}

    if (totals["lessons"], totals["production_ambiguous"], totals["rotations"],
            totals["rotations_ambiguous"]) != (300, 20, 1800, 128):
        raise ValueError(f"expected original rescore counts, got {dict(totals)}")
    source_binding = {key: data[key] for key in ("generator_sha256", "rule_source_sha256",
        "rule_callable_sha256", "declared_rule_hash", "runtime_manifest_sha256")}
    source_binding.update({"census_sha256": CENSUS_SHA256,
                           "census_path": str(args.census),
                           "canonical_records_sha256": digest(normalized_json(canonical_rows))})
    rival_source = inspect.getsource(foreground_area) + "\n" + inspect.getsource(area_lookup)
    report = {
        "schema": "area-shortcut-retained-census-rescore-v1", "task_id": TASK_ID,
        "source_binding": source_binding, "rival_name": RIVAL_NAME,
        "rival_source": rival_source, "rival_source_sha256": digest(rival_source.encode()),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "label_authority": "Existing materialized production census, labeled by the canonical Racket rule",
        "new_racket_execution": False, "generator_loaded": False,
        "canonical_checks": canonical_checks,
        "summary": {**totals, "unique_inputs": len(input_hashes),
                    "unique_ambiguous_query_inputs": len(ambiguous_query_hashes)},
        "per_band": per_band, "sampler": data["sampler"], "lessons": rows,
        "limits": ["This is a rescore of the pinned 300-lesson census, not a new label verification.",
                   "The size-only rival was added after the census's three-rival pass.",
                   "The selected lookup is not an exhaustive family of alternative rules."]}
    counterexample = {
        "schema": "area-lookup-teaching-counterexample-v1", "task_id": TASK_ID,
        "source_binding": source_binding, "rival_name": RIVAL_NAME,
        "rival_source": rival_source, "rival_source_sha256": digest(rival_source.encode()),
        "label_authority": report["label_authority"], "new_racket_execution": False,
        "finding": "A canonical-fitting area-only rival matches all five demonstrations but changes the query.",
        "lesson": first_counterexample,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    write_new(args.out / "report.json", report)
    write_new(args.counterexample, counterexample)
    print(json.dumps({"source_binding": source_binding, "summary": report["summary"],
                      "per_band": per_band, "counterexample": str(args.counterexample)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
