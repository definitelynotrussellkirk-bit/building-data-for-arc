#!/usr/bin/env python3
"""Reproduce the assignment-seeded generator allocation audit without importing generators."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_SEED = "c20415a2b2d39a350aeb5796cb5466663e67ec2767581860360b99c60e404a4a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalog(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def declared_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def check_summary(path: Path, root: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text())
    return {
        "path": path.relative_to(root).as_posix(),
        "verdict": data.get("verdict"),
        "verdict_note": data.get("verdict_note"),
        "counts": data.get("counts"),
        "first_failing_stage": data.get("first_failing_stage"),
        "first_incomplete_stage": data.get("first_incomplete_stage"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."), help="WORK directory")
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = root / "PACKET-MANIFEST.json"
    catalog_path = root / "repo/catalog/puzzles.jsonl"
    weights_path = root / "repo/shared/data/derived/generator_weights.json"
    draw_path = root / "repo/src/arcpuzzles/review_full_draw.py"
    manifest = json.loads(manifest_path.read_text())
    catalog = load_catalog(catalog_path)
    weights = json.loads(weights_path.read_text())

    ids = sorted(manifest["generators"])
    sampled = random.Random(int(args.seed, 16)).sample(ids, min(args.count, len(ids)))
    policy = manifest["main_draw_policy"]
    focus = policy["evaluation_focus"]
    anchors = focus["anchors"]
    related = [anchor for anchor in anchors if anchor.get("main_ids")]

    observations: list[dict[str, Any]] = []
    semantic_names = {
        "strict_canonical_like",
        "SEMANTIC_WITNESSES",
        "lesson_identifiable",
        "SEMANTIC_RIVALS",
        "LESSON_COMPETITORS",
    }
    for task_id in sampled:
        source = root / "repo/generators" / task_id / "generator.py"
        names = declared_names(source)
        entry = catalog[task_id]
        base = root / "checks/allocation-audit"
        lint_summary = check_summary(base / f"{task_id}-lint/checks/{task_id}_audit_battery_summary.json", root)
        semantic_summary = check_summary(base / f"{task_id}-semantic/checks/{task_id}_audit_battery_summary.json", root)
        review_index = root / "repo/generators" / task_id / "evidence/review_index.json"
        observations.append({
            "task_id": task_id,
            "generator_path": source.relative_to(root).as_posix(),
            "generator_sha256": sha256(source),
            "manifest_generator_sha256": manifest["generators"][task_id]["generator_sha256"],
            "catalog_source": entry.get("sources", []),
            "catalog_review_status": entry.get("review_status", ""),
            "catalog_train_safety": entry.get("train_safety"),
            "catalog_mix_weight": entry.get("mix_weight"),
            "derived_sampling_weight": weights.get(task_id),
            "rule_hash_declared": "RULE_HASH" in names,
            "semantic_contract_names": sorted(names & semantic_names),
            "review_index_path": review_index.relative_to(root).as_posix() if review_index.is_file() else None,
            "lint_check": lint_summary,
            "semantic_check": semantic_summary,
        })

    report = {
        "schema": "arcpuzzles-randomized-allocation-audit-v1",
        "seed": args.seed,
        "sampler": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.generators), count)",
        "population_size": len(ids),
        "sample_size": len(sampled),
        "sampled_ids": sampled,
        "source_files": {
            "manifest": {"path": manifest_path.relative_to(root).as_posix(), "sha256": sha256(manifest_path)},
            "draw_policy": {"path": draw_path.relative_to(root).as_posix(), "sha256": sha256(draw_path)},
            "catalog": {"path": catalog_path.relative_to(root).as_posix(), "sha256": sha256(catalog_path)},
            "weights": {"path": weights_path.relative_to(root).as_posix(), "sha256": sha256(weights_path)},
        },
        "authoring_draw": {
            "main_ids": len(manifest["main_ids"]),
            "normal_ids": len(policy["normal_ids"]),
            "evaluation_focus_probability": focus["probability"],
            "evaluation_focus_anchors": len(anchors),
            "anchors_with_direct_related_generators": len(related),
            "direct_related_generator_slots": sum(len(a.get("main_ids", [])) for a in related),
            "selected_tiers": dict(Counter(a.get("selected_tier") for a in anchors)),
            "parametric_priority_counts": manifest["parametric_priority"]["counts"],
        },
        "sample_observations": observations,
        "coverage_limits": [
            "Three IDs are an assignment-seeded spot sample, not an estimate of corpus-wide rates.",
            "Authoring draw probability and downstream dataset sampling weight are separate mechanisms.",
            "Interrupted checks remain interrupted; retained accepted review evidence is not reclassified as a new pass.",
            "None of the sampled catalog source entries is ARC-GEN or RE-ARC, so this sample supports no source-specific conclusion about either corpus.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"sampled_ids": sampled, "out": str(args.out), "sha256": sha256(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
