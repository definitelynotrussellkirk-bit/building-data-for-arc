#!/usr/bin/env python3
"""Racket-backed exhaustive probe for the five-slot 0c4c1974cbf2 curriculum.

This is a reviewer tool, not a production dependency.  It dynamically reads the
selected generator's rival declarations, labels generated inputs through the
public canonical Catalog.apply API, enumerates all five cyclic starts in all
three difficulty bands, and rotates each of the four materialized pairs through
the query position.  The JSON output contains exact grids, hashes, source hashes,
replay coordinates, and per-rival verdicts so a future reviewer can reproduce or
extend the check without copying a stale rival-name list.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "0c4c1974cbf2"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed-base", type=int, default=20261012)
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> int:
    args = _args()
    gen = _load_generator()
    root = find_root(__file__)
    period = len(gen.SCHEDULE_PROFILES)
    bands = ("easy", "medium", "hard")
    pair_count = gen.EXAMPLES_NEEDED + 1

    requests: list[dict[str, Any]] = []
    all_inputs: list[list[list[int]]] = []
    for band_index, band in enumerate(bands):
        for start in range(period):
            seed = args.seed_base + band_index * 100 + start
            indexes = list(range(start, start + pair_count))
            offset = len(all_inputs)
            inputs = [gen.generate(seed, index, difficulty=band) for index in indexes]
            all_inputs.extend(inputs)
            requests.append(
                {
                    "band": band,
                    "start": start,
                    "seed": seed,
                    "sample_indices": indexes,
                    "input_offsets": list(range(offset, offset + pair_count)),
                }
            )

    authority = Catalog(root).apply(
        TASK_ID, all_inputs, reference="canonical", timeout=args.timeout
    )
    authority_results = authority["results"]
    failures: list[str] = []
    if not authority.get("rule_hash_matches_catalog"):
        failures.append("canonical authority hash does not match catalog")
    if any(item.get("error") for item in authority_results):
        failures.append("canonical authority returned one or more execution errors")

    labelled: list[dict[str, Any]] = []
    for grid, item in zip(all_inputs, authority_results):
        output = item["output"]
        if gen.rule_mirror(grid) != output:
            failures.append(f"Python rule_mirror disagrees for input {item['input_sha256']}")
        labelled.append(
            {
                "input": grid,
                "output": output,
                "input_sha256": item["input_sha256"],
                "output_sha256": item["output_sha256"],
            }
        )

    canonical_shortcuts: dict[str, Any] = {}
    canonical = canonical_pairs(TASK_ID, root=root)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_shortcuts[name] = {
            "fits_all": all(fits),
            "pair_fits": fits,
        }
        if not all(fits):
            failures.append(f"declared canonical shortcut {name!r} does not fit all canonical pairs")

    lesson_rows: list[dict[str, Any]] = []
    rotations_checked = 0
    rival_checks = 0
    for request in requests:
        pairs = [labelled[index] for index in request["input_offsets"]]
        rotations: list[dict[str, Any]] = []
        for query_index in range(pair_count):
            demos = [
                {"input": pair["input"], "output": pair["output"]}
                for index, pair in enumerate(pairs)
                if index != query_index
            ]
            query_pair = pairs[query_index]
            query = {"input": query_pair["input"], "output": query_pair["output"]}
            hook_reasons = gen.lesson_identifiable(demos, query)
            rival_rows: dict[str, Any] = {}
            for name, rival in gen.LESSON_COMPETITORS.items():
                predictions = [rival(pair["input"]) for pair in demos]
                refuted_at = [
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, demos))
                    if prediction != pair["output"]
                ]
                query_prediction = rival(query["input"])
                rival_rows[name] = {
                    "refuted_by_demo_positions": refuted_at,
                    "fits_all_demos": not refuted_at,
                    "differs_on_query": query_prediction != query["output"],
                    "query_prediction_sha256": _sha_json(query_prediction),
                }
                rival_checks += 1
                if not refuted_at:
                    failures.append(
                        f"{request['band']} start={request['start']} rotation={query_index}: "
                        f"rival {name!r} fits all demos"
                    )
            rotations.append(
                {
                    "query_position": query_index,
                    "query_input_sha256": query_pair["input_sha256"],
                    "demo_positions": [i for i in range(pair_count) if i != query_index],
                    "hook_reasons": hook_reasons,
                    "rivals": rival_rows,
                }
            )
            rotations_checked += 1
            if hook_reasons:
                failures.append(
                    f"{request['band']} start={request['start']} rotation={query_index}: "
                    + "; ".join(hook_reasons)
                )
        lesson_rows.append(
            {
                **request,
                "profiles": [
                    gen.schedule_profile(request["seed"], index, request["band"])
                    for index in request["sample_indices"]
                ],
                "pairs": pairs,
                "rotations": rotations,
            }
        )

    report = {
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(root)),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "assembly_policy": {
            "pairs_per_instance": pair_count,
            "demonstrations": gen.EXAMPLES_NEEDED,
            "queries": 1,
            "cyclic_starts": period,
            "query_rotation": "each labelled pair held out once",
        },
        "authority": {
            "reference": authority.get("reference"),
            "rule_hash_matches_catalog": authority.get("rule_hash_matches_catalog"),
            "executed_rule_hash": authority.get("executed_rule_hash"),
            "catalog_rule_hash": authority.get("catalog_rule_hash"),
            "source_sha256": authority.get("source_sha256"),
            "input_count": len(all_inputs),
        },
        "canonical_shortcuts": canonical_shortcuts,
        "summary": {
            "bands": len(bands),
            "cyclic_starts_per_band": period,
            "instances": len(lesson_rows),
            "unique_input_hashes": len({pair["input_sha256"] for pair in labelled}),
            "rotations_checked": rotations_checked,
            "rival_checks": rival_checks,
            "failure_count": len(failures),
            "status": "pass" if not failures else "fail",
        },
        "failures": failures,
        "instances": lesson_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
