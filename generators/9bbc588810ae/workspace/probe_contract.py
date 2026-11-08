#!/usr/bin/env python3
"""Reproducible semantic/lesson probe for generator 9bbc588810ae.

Runs only public source interfaces.  With ``--racket`` it also labels the three
canonical inputs plus one generated counterexample through public
``Catalog.apply(reference='canonical')`` and verifies the independent Python
mirror against those authoritative outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9bbc588810ae"
BANDS = ("easy", "medium", "hard")


def digest_grid(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    if not path.is_file():
        path = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--per-band", type=int, default=40)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source = load_generator(root)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    failures: list[dict] = []

    canonical = canonical_pairs(TASK_ID, root=root, variant=0)
    canonical_checks = []
    for index, item in enumerate(canonical):
        errors = gen.self_check(item["input"])
        predicted = None if errors else gen.rule_mirror(item["input"])
        ok = not errors and predicted == item["output"]
        canonical_checks.append({
            "index": index,
            "split": item["split"],
            "pair_index": item["pair_index"],
            "self_check": errors,
            "mirror_matches": ok,
            "input_sha256": digest_grid(item["input"]),
        })
        if not ok:
            failures.append({"kind": "canonical_mirror", "index": index})

    generated = []
    transforms, panels, sizes, palettes = set(), set(), set(), set()
    strict_count = witness_count = 0
    unique_inputs = set()
    unique_outputs = set()
    first_witness = None
    for band in BANDS:
        for seed in range(args.per_band):
            sample_index = seed % 17
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid)
            if errors:
                failures.append({"kind": "self_check", "band": band, "seed": seed, "errors": errors})
                continue
            strict_count += not gen.strict_canonical_like(grid)
            axes = gen.observe_axes(grid)
            transforms.add(axes["transform"])
            panels.add(axes["match_panel"])
            sizes.add(axes["query_cells"])
            palettes.add(axes["palette_kind"])
            truth = gen.rule_mirror(grid)
            witness = gen.SEMANTIC_WITNESSES["bbox_count_lowest_color_counterexample"](grid)
            witness_count += bool(witness)
            unique_inputs.add(digest_grid(grid))
            unique_outputs.add(digest_grid(truth))
            if witness and first_witness is None:
                rival = gen.SEMANTIC_RIVALS["bbox_count_lowest_color"](grid)
                first_witness = {
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "profile": gen.schedule_profile(seed, sample_index, band),
                    "axes": axes,
                    "input": grid,
                    "intended_output": truth,
                    "rival_output": rival,
                    "disagrees": rival != truth,
                    "input_sha256": digest_grid(grid),
                }
            generated.append({"band": band, "seed": seed, "sample_index": sample_index, "axes": axes})

    rotation_checks = 0
    rotation_failures = []
    for band in BANDS:
        for seed in (17, 91, 7001):
            for start in range(12):
                labelled = [pair(gen, gen.generate(seed, start + offset, difficulty=band)) for offset in range(4)]
                for query_index in range(4):
                    demos = [item for index, item in enumerate(labelled) if index != query_index]
                    reasons = gen.lesson_identifiable(demos, labelled[query_index])
                    rotation_checks += 1
                    if reasons:
                        row = {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                        rotation_failures.append(row)
                        failures.append({"kind": "rotation", **row})

    report = {
        "schema": "9bbc588810ae-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "canonical": canonical_checks,
        "generated": {
            "draws": len(generated),
            "strict": strict_count,
            "witnesses": witness_count,
            "unique_inputs": len(unique_inputs),
            "unique_outputs": len(unique_outputs),
            "transforms": sorted(transforms),
            "match_panels": sorted(panels),
            "query_cells": sorted(sizes),
            "palettes": sorted(palettes),
        },
        "rotations": {
            "checked": rotation_checks,
            "failures": rotation_failures,
        },
        "counterexample": first_witness,
        "racket": {"requested": args.racket, "executed": False},
        "failures": failures,
    }

    if first_witness is None:
        failures.append({"kind": "missing_witness"})
    elif args.racket:
        from arcpuzzles import Catalog

        inputs = [item["input"] for item in canonical] + [first_witness["input"]]
        receipt = Catalog(root).apply(
            TASK_ID,
            inputs,
            reference="canonical",
            allow_unapproved=True,
            timeout=180,
        )
        comparisons = []
        for index, (grid, result) in enumerate(zip(inputs, receipt["results"], strict=True)):
            expected = gen.rule_mirror(grid)
            ok = result.get("error") is None and result.get("output") == expected
            comparisons.append({
                "index": index,
                "input_sha256": result.get("input_sha256"),
                "output_sha256": result.get("output_sha256"),
                "error": result.get("error"),
                "mirror_matches": ok,
            })
            if not ok:
                failures.append({"kind": "racket_mirror", "index": index})
        report["racket"] = {
            "requested": True,
            "executed": True,
            "generator_sha256": receipt.get("generator_sha256"),
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "comparisons": comparisons,
        }
        if receipt.get("generator_sha256") != source_hash:
            failures.append({"kind": "racket_source_hash"})
        if receipt.get("executed_rule_hash") != gen.RULE_HASH or not receipt.get("rule_hash_matches_catalog"):
            failures.append({"kind": "racket_rule_hash"})

    report["status"] = "pass" if not failures else "fail"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": source_hash,
        "draws": len(generated),
        "rotation_checks": rotation_checks,
        "failures": len(failures),
        "out": str(args.out),
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
