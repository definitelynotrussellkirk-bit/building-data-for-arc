#!/usr/bin/env python3
"""Bounded, source-only allocation audit extractor for ARC review packets.

This deliberately does not import generator modules or execute Racket. It joins the
immutable packet manifest, authoring policy, catalog metadata, dataset weights,
canonical provenance, and retained review evidence for a reproducible sample.
"""
from __future__ import annotations

import argparse
import ast
import json
import random
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "arcpuzzles-allocation-audit-extract-v1"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_index(path: Path, key: str, wanted: set[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            value = str(row.get(key, ""))
            if value in wanted:
                found[value] = row
                if len(found) == len(wanted):
                    break
    return found


def _literal_assignments(path: Path, names: Iterable[str]) -> dict[str, Any]:
    wanted = set(names)
    values: dict[str, Any] = {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value_node = node.value
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(value_node)
                except (ValueError, TypeError):
                    values[target.id] = "<nonliteral>"
    return values


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _evidence_paths(root: Path, task_dir: Path) -> list[str]:
    paths: list[str] = []
    for sub in (task_dir / "evidence", task_dir / "counterexamples"):
        if sub.is_dir():
            paths.extend(_relative(root, p) for p in sorted(sub.rglob("*")) if p.is_file())
    for name in ("generator.py", "notes.md", "SUMMARY.md"):
        p = task_dir / name
        if p.is_file():
            paths.append(_relative(root, p))
    return sorted(set(paths))


def _retained_audits(task_dir: Path) -> list[dict[str, Any]]:
    path = task_dir / "evidence" / "review_index.json"
    if not path.is_file():
        return []
    result = []
    for row in _json(path).get("audits", []):
        result.append({
            "source_sha256": row.get("source_sha256"),
            "resolution": row.get("resolution"),
            "resolution_reason": row.get("resolution_reason"),
            "verification_status": row.get("verification_status"),
            "assets_manifest": row.get("assets_manifest"),
            "text": row.get("text", ""),
        })
    return result


def _source_class(sources: list[str]) -> str:
    joined = " ".join(sources).lower()
    if "re-arc" in joined or "re_arc" in joined or "rearc" in joined:
        return "RE-ARC"
    if "arc-gen" in joined or "arc_gen" in joined or "arcgen" in joined:
        return "ARC-GEN"
    if any(source.startswith("bank:") for source in sources):
        return "internal_bank"
    if any("evaluation" in source for source in sources):
        return "public_evaluation"
    return "other_or_unknown"


def build_report(packet_root: Path, seed: str, sample_size: int = 3) -> dict[str, Any]:
    packet_root = packet_root.resolve()
    work = packet_root / "WORK"
    repo = work / "repo"
    manifest = _json(work / "PACKET-MANIFEST.json")
    all_ids = sorted(str(x) for x in manifest["all_ids"])
    sample = random.Random(int(seed, 16)).sample(all_ids, min(sample_size, len(all_ids)))
    wanted = set(sample)

    catalog = _jsonl_index(repo / "shared/data/derived/generator_catalog.jsonl", "task_id", wanted)
    puzzle_catalog = _jsonl_index(repo / "catalog/puzzles.jsonl", "id", wanted)
    canonical = _jsonl_index(repo / "shared/data/canonical/puzzle_db.jsonl", "task_id", wanted)
    weights = _json(repo / "shared/data/derived/generator_weights.json")

    policy = manifest["main_draw_policy"]
    normal_pool = set(policy["normal_ids"])
    main_pool = set(manifest["main_ids"])
    focus = policy["evaluation_focus"]
    numerator = int(focus["probability"]["numerator"])
    denominator = int(focus["probability"]["denominator"])
    normal_share = 1.0 - numerator / denominator

    rows: list[dict[str, Any]] = []
    for task_id in sample:
        task_dir = repo / "generators" / task_id
        generator_path = task_dir / "generator.py"
        literals = _literal_assignments(
            generator_path,
            ("VERSION", "SUMMARY", "AXES", "INVARIANTS", "EXAMPLES_NEEDED", "MIN_STRICT_FRAC"),
        )
        cat = catalog.get(task_id, {})
        puzzle = puzzle_catalog.get(task_id, {})
        canon = canonical.get(task_id, {})
        sources = list(puzzle.get("sources") or ([canon["source"]] if canon.get("source") else []))
        retained = _retained_audits(task_dir)
        axes = literals.get("AXES") if isinstance(literals.get("AXES"), dict) else {}
        evidence = _evidence_paths(packet_root, task_dir)
        rows.append({
            "task_id": task_id,
            "manifest_approved": bool(manifest["generators"][task_id].get("approved")),
            "generator_sha256": manifest["generators"][task_id].get("generator_sha256"),
            "version": literals.get("VERSION"),
            "summary": literals.get("SUMMARY") or cat.get("summary"),
            "sources": sources,
            "source_class": _source_class(sources),
            "canonical_train_pairs": canon.get("n_train"),
            "canonical_test_pairs": canon.get("n_test"),
            "canonical_difficulty": canon.get("difficulty"),
            "train_safety": puzzle.get("train_safety"),
            "health": puzzle.get("health"),
            "catalog_mix_weight": puzzle.get("mix_weight"),
            "dataset_sampling_weight": weights.get(task_id),
            "in_main_authoring_pool": task_id in main_pool,
            "in_normal_authoring_pool": task_id in normal_pool,
            "unconditional_normal_authoring_probability": (
                normal_share / len(normal_pool) if task_id in normal_pool else 0.0
            ),
            "catalog_lint_status": cat.get("lint_status"),
            "catalog_tech_debt": cat.get("tech_debt", []),
            "catalog_improve": cat.get("improve", []),
            "combinatorial_reach": cat.get("combinatorial_reach"),
            "reach_score": cat.get("reach_score"),
            "diversity_score": cat.get("diversity_score"),
            "live_axes": cat.get("live_axes", []),
            "locked_axes": cat.get("locked_axes", []),
            "declared_axis_count": len(axes),
            "declared_axes": sorted(axes),
            "racket_primitive_count": len(cat.get("racket_primitives", [])),
            "retained_audits": retained,
            "unresolved_audit_count": sum(a.get("resolution") == "unresolved" for a in retained),
            "evidence_paths": evidence,
        })

    return {
        "schema": SCHEMA,
        "seed": seed,
        "sampling_method": "random.Random(int(seed, 16)).sample(sorted(all_ids), min(sample_size, len(all_ids)))",
        "population_count": len(all_ids),
        "sample_size": len(sample),
        "sampled_ids": sample,
        "authoring_policy": {
            "implementation_path": "WORK/repo/src/arcpuzzles/review_full_draw.py",
            "selection_function": "main_selection_for_seed",
            "normal_pool_count": len(normal_pool),
            "main_pool_count": len(main_pool),
            "normal_pool_selection": "uniform conditional on the 90% normal branch",
            "evaluation_focus_probability": focus["probability"],
            "evaluation_anchor_count": len(focus.get("anchors", [])),
            "evaluation_related_generator_count": focus.get("eligible_related_generators"),
            "evaluation_mapped_task_count": focus.get("mapped_tasks"),
            "scope": focus.get("scope"),
        },
        "dataset_weight_source": "WORK/repo/shared/data/derived/generator_weights.json",
        "catalog_source": "WORK/repo/shared/data/derived/generator_catalog.jsonl",
        "sample": rows,
        "coverage_limits": [
            "Source-only bounded inspection; no corpus-wide rerun, model training, or new Racket execution.",
            "The three sampled records are internal-bank generators; this sample contains no ARC-GEN or RE-ARC record.",
            "Dataset sampling weights are reported as stored and are not interpreted as authoring draw probabilities.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, default=Path.cwd())
    parser.add_argument("--seed", required=True)
    parser.add_argument("--sample-size", type=int, default=3)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(args.packet_root, args.seed, args.sample_size)
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
