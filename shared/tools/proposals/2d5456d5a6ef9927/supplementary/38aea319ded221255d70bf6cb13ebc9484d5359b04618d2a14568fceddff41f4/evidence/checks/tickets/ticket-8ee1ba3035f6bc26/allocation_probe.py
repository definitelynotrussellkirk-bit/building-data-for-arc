#!/usr/bin/env python3
"""Reproducible bounded allocation-quality probe for one ARC review ticket.

This is intentionally source-only: it joins the packet draw policy, catalog,
weights, generator declarations, and retained review evidence without importing
or executing the sampled generators. Authoring probabilities and downstream
sampling weights are kept separate.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "arcpuzzles-allocation-quality-ticket-v1"
DEFAULT_SEED = "9bc134f1609b62f979f7550c46c63f25f0b6c0a58e99161be9f16eaa2f665372"
TARGET_TASK_ID = "9db8deba5903"
SEMANTIC_NAMES = {
    "strict_canonical_like",
    "SEMANTIC_WITNESSES",
    "SEMANTIC_RIVALS",
    "LESSON_COMPETITORS",
    "lesson_identifiable",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl_index(path: Path, key: str, wanted: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            value = str(row.get(key, ""))
            if value in wanted:
                result[value] = row
                if len(result) == len(wanted):
                    break
    return result


def source_declarations(path: Path, literals: Iterable[str]) -> tuple[dict[str, Any], set[str]]:
    wanted = set(literals)
    values: dict[str, Any] = {}
    names: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            names.add(target.id)
            if target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    values[target.id] = "<nonliteral>"
    return values, names


def retained_audits(task_dir: Path) -> list[dict[str, Any]]:
    index = task_dir / "evidence/review_index.json"
    if not index.is_file():
        return []
    rows = []
    for row in load_json(index).get("audits", []):
        text = str(row.get("text", ""))
        rows.append(
            {
                "return_id": row.get("return_id"),
                "source_sha256": row.get("source_sha256"),
                "resolution": row.get("resolution"),
                "verification_status": row.get("verification_status"),
                "assets_manifest": row.get("assets_manifest"),
                "teaching_or_ambiguity_evidence": any(
                    word in text.lower() for word in ("teaching", "ambigu", "shortcut", "rival")
                ),
                "summary_excerpt": " ".join(text.split())[:600],
            }
        )
    return rows


def source_class(sources: list[str]) -> str:
    joined = " ".join(sources).lower()
    if any(token in joined for token in ("re-arc", "re_arc", "rearc")):
        return "RE-ARC"
    if any(token in joined for token in ("arc-gen", "arc_gen", "arcgen")):
        return "ARC-GEN"
    if any(item.startswith("bank:") for item in sources):
        return "internal_bank"
    if "evaluation" in joined:
        return "public_evaluation"
    if "training" in joined or "augmented" in joined:
        return "official_or_augmented_arc"
    return "other_or_unknown"


def task_record(
    work: Path,
    task_id: str,
    manifest: dict[str, Any],
    weights: dict[str, float],
    catalog: dict[str, dict[str, Any]],
    puzzles: dict[str, dict[str, Any]],
    canonical: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    repo = work / "repo"
    task_dir = repo / "generators" / task_id
    source = task_dir / "generator.py"
    literals, names = source_declarations(
        source,
        ("VERSION", "SUMMARY", "AXES", "EXAMPLES_NEEDED", "MIN_STRICT_FRAC"),
    )
    cat = catalog.get(task_id, {})
    puzzle = puzzles.get(task_id, {})
    canon = canonical.get(task_id, {})
    axes = literals.get("AXES") if isinstance(literals.get("AXES"), dict) else {}
    audits = retained_audits(task_dir)
    open_resolutions = {"unresolved", "needs_triage", "open", None, ""}
    parametric_dir = task_dir / "workspace/parametric"
    parametric_files = sorted(
        p.relative_to(work).as_posix() for p in parametric_dir.rglob("*") if p.is_file()
    ) if parametric_dir.is_dir() else []
    source_version = literals.get("VERSION")
    derived_version = cat.get("version")
    sources = list(puzzle.get("sources") or ([canon["source"]] if canon.get("source") else []))
    normal_ids = set(manifest["main_draw_policy"]["normal_ids"])
    focus = manifest["main_draw_policy"]["evaluation_focus"]["probability"]
    normal_share = 1.0 - int(focus["numerator"]) / int(focus["denominator"])
    return {
        "task_id": task_id,
        "generator_path": source.relative_to(work).as_posix(),
        "generator_sha256": sha256_file(source),
        "manifest_generator_sha256": manifest["generators"][task_id]["generator_sha256"],
        "manifest_approved": bool(manifest["generators"][task_id].get("approved")),
        "source_version": source_version,
        "catalog_version": puzzle.get("version"),
        "derived_catalog_version": derived_version,
        "derived_catalog_stale": bool(source_version and derived_version and source_version != derived_version),
        "sources": sources,
        "source_class": source_class(sources),
        "train_safety": puzzle.get("train_safety"),
        "review_status": puzzle.get("review_status"),
        "health": puzzle.get("health"),
        "catalog_mix_weight": puzzle.get("mix_weight"),
        "dataset_sampling_weight": weights.get(task_id),
        "in_normal_authoring_pool": task_id in normal_ids,
        "unconditional_uniform_normal_probability": (
            normal_share / len(normal_ids) if task_id in normal_ids else 0.0
        ),
        "parametric_priority_tier": next(
            (
                tier
                for tier, ids in manifest["parametric_priority"]["tiers"].items()
                if task_id in ids
            ),
            None,
        ),
        "declared_axes": sorted(axes),
        "declared_axis_count": len(axes),
        "examples_needed": literals.get("EXAMPLES_NEEDED"),
        "semantic_contract_names": sorted(names & SEMANTIC_NAMES),
        "has_task_local_parametric_artifact": bool(parametric_files),
        "parametric_artifact_paths": parametric_files,
        "four_query_supervision_retained": any(
            "four-query" in p.lower() or "4-query" in p.lower() for p in parametric_files
        ),
        "canonical_train_pairs": canon.get("n_train"),
        "canonical_test_pairs": canon.get("n_test"),
        "racket_primitive_count": len(cat.get("racket_primitives", [])),
        "catalog_lint_status": cat.get("lint_status"),
        "catalog_tech_debt": cat.get("tech_debt", []),
        "catalog_improve": cat.get("improve", []),
        "diversity_score": cat.get("diversity_score"),
        "reach_score": cat.get("reach_score"),
        "retained_audits": audits,
        "open_audit_count": sum(a.get("resolution") in open_resolutions for a in audits),
        "teachability_evidence_count": sum(
            bool(a.get("teaching_or_ambiguity_evidence")) for a in audits
        ),
        "cost_proxy": {
            "review_minutes_budget": 10,
            "racket_primitive_count": len(cat.get("racket_primitives", [])),
            "declared_axis_count": len(axes),
            "canonical_labeled_pairs": (canon.get("n_train") or 0) + (canon.get("n_test") or 0),
            "deduplication_risk_proxy": (
                "higher" if (cat.get("diversity", {}) or {}).get("uniq_out", 1.0) < 0.8 else "ordinary"
            ),
        },
    }


def build_report(work_root: Path, seed: str = DEFAULT_SEED, sample_size: int = 3) -> dict[str, Any]:
    work = Path(work_root).resolve()
    repo = work / "repo"
    manifest_path = work / "PACKET-MANIFEST.json"
    manifest = load_json(manifest_path)
    population = sorted(str(x) for x in manifest["generators"])
    sampled = random.Random(int(seed, 16)).sample(population, min(sample_size, len(population)))
    wanted = set(sampled + [TARGET_TASK_ID])
    weights_path = repo / "shared/data/derived/generator_weights.json"
    derived_catalog_path = repo / "shared/data/derived/generator_catalog.jsonl"
    puzzle_catalog_path = repo / "catalog/puzzles.jsonl"
    canonical_path = repo / "shared/data/canonical/puzzle_db.jsonl"
    weights = load_json(weights_path)
    catalog = jsonl_index(derived_catalog_path, "task_id", wanted)
    puzzles = jsonl_index(puzzle_catalog_path, "id", wanted)
    canonical = jsonl_index(canonical_path, "task_id", wanted)
    sample = [
        task_record(work, tid, manifest, weights, catalog, puzzles, canonical)
        for tid in sampled
    ]
    target = task_record(
        work, TARGET_TASK_ID, manifest, weights, catalog, puzzles, canonical
    )
    focus = manifest["main_draw_policy"]["evaluation_focus"]
    source_counts = Counter(row["source_class"] for row in sample)
    normal_open = [row for row in sample if row["in_normal_authoring_pool"] and row["open_audit_count"]]
    open_rows = [row for row in sample if row["open_audit_count"]]
    anomaly_rows = [
        row for row in sample
        if (row["train_safety"] == "reviewed_safe" and row["dataset_sampling_weight"] == 0.0)
        or (row["train_safety"] != "reviewed_safe" and (row["dataset_sampling_weight"] or 0) > 0)
    ]
    return {
        "schema": SCHEMA,
        "ticket_id": "ticket-8ee1ba3035f6bc26",
        "seed": seed,
        "sampling_method": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.generators), 3)",
        "population_count": len(population),
        "sampled_ids": sampled,
        "source_files": {
            "manifest": {"path": manifest_path.relative_to(work).as_posix(), "sha256": sha256_file(manifest_path)},
            "draw_implementation": {
                "path": "repo/src/arcpuzzles/review_full_draw.py",
                "sha256": sha256_file(repo / "src/arcpuzzles/review_full_draw.py"),
            },
            "weights": {"path": weights_path.relative_to(work).as_posix(), "sha256": sha256_file(weights_path)},
            "derived_catalog": {"path": derived_catalog_path.relative_to(work).as_posix(), "sha256": sha256_file(derived_catalog_path)},
            "puzzle_catalog": {"path": puzzle_catalog_path.relative_to(work).as_posix(), "sha256": sha256_file(puzzle_catalog_path)},
        },
        "authoring_policy": {
            "normal_pool_count": len(manifest["main_draw_policy"]["normal_ids"]),
            "main_pool_count": len(manifest["main_ids"]),
            "evaluation_focus_probability": focus["probability"],
            "evaluation_anchor_count": len(focus.get("anchors", [])),
            "evaluation_related_generator_count": focus.get("eligible_related_generators"),
            "evaluation_mapped_task_count": focus.get("mapped_tasks"),
            "normal_selection": "uniform within the 90% normal branch",
            "scope": focus.get("scope"),
            "parametric_priority_counts": manifest["parametric_priority"]["counts"],
        },
        "target_record": target,
        "sample": sample,
        "observed_quality_cost": {
            "sample_source_classes": dict(sorted(source_counts.items())),
            "records_with_open_audits": len(open_rows),
            "normal_pool_records_with_open_audits": len(normal_open),
            "sampling_weight_or_safety_anomalies": len(anomaly_rows),
            "records_with_retained_four_query_supervision": sum(
                row["four_query_supervision_retained"] for row in sample
            ),
            "records_with_task_local_parametric_artifacts": sum(
                row["has_task_local_parametric_artifact"] for row in sample
            ),
            "interpretation": (
                "This seeded sample finds source-bound teachability/domain evidence and weight-state inconsistencies, "
                "while no sampled record retains four-query supervision. The sample is too small to estimate corpus rates."
            ),
        },
        "alternative_allocation": {
            "name": "evidence-gated normal-stratum trial",
            "status": "proposal_only_no_policy_change",
            "total_assignments": 30,
            "evaluation_focus_assignments": 3,
            "normal_assignments": 27,
            "targeted_normal_assignments": 6,
            "uniform_normal_assignments": 21,
            "targeted_slots": {
                "open_teachability_or_semantic_evidence": 2,
                "sampling_weight_or_train_safety_mismatch": 2,
                "missing_parameter_or_four_query_evidence": 2,
            },
            "quality_per_cost_estimate": {
                "basis": "sample-conditioned issue-yield proxy, not a corpus-wide rate",
                "current_uniform_proxy": f"{len(normal_open)} open-audit record(s) surfaced among {sum(r['in_normal_authoring_pool'] for r in sample)} sampled normal-eligible records",
                "targeted_proxy": f"{len(open_rows)} open-audit record(s) plus {len(anomaly_rows)} weight/safety anomaly record(s) would be deliberately surfaced among three reviews",
                "directional_expectation": "higher actionable-evidence yield at equal reviewer minutes; magnitude unknown",
                "extra_cost_expectation": "Racket replay and four-query dedup may add up to 25% per targeted assignment; estimate only",
            },
            "bounded_test": {
                "design": "Within 30 assignments, compare the six targeted normal slots against six matched uniform-normal slots using existing receipts plus at most one focused replay per assignment.",
                "primary_metric": "accepted ambiguity-free, Racket-replayed, deduplicated four-query episodes per reviewer-hour",
                "secondary_metrics": [
                    "actionable source-bound finding or resolved metadata inconsistency per reviewer-hour",
                    "Racket failure fraction",
                    "duplicate-query fraction",
                    "surviving declared-rival fraction",
                ],
            },
            "adoption_rule": {
                "minimum_quality_per_cost_ratio": 1.25,
                "require_no_higher_racket_or_ambiguity_failure_rate": True,
                "early_stop": "Stop after three matched pairs if targeted output is <=0.5x baseline or costs >2x baseline.",
                "final_stop": "Stop at 30 assignments; do not expand without owner review of receipts.",
            },
        },
        "coverage_limits": [
            "Only three assignment-seeded records were inspected; rates and effect sizes are unknown.",
            "No sampled record is ARC-GEN or RE-ARC, so this probe supports no source-specific conclusion about either corpus.",
            "Derived generator_catalog rows are stale relative to all three sampled source versions; lint/axis metadata are treated as leads, not current verdicts.",
            "Dataset weights are reported as stored and are not authoring draw probabilities.",
            "No corpus-wide rerun, model job, new approval, or training-policy change was performed.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    rows = {row["task_id"]: row for row in report["sample"]}
    lines = [
        "# Allocation-quality probe",
        "",
        f"Seed: `{report['seed']}`",
        f"Sample: `{', '.join(report['sampled_ids'])}`",
        "",
        "## Current policy",
        "",
        "The authoring draw uses a 10% evaluation-focus branch and a 90% uniform normal branch over "
        f"{report['authoring_policy']['normal_pool_count']} IDs. Dataset weights are a separate mechanism.",
        "",
        "## Sample findings",
        "",
    ]
    for tid in report["sampled_ids"]:
        row = rows[tid]
        lines.append(
            f"- `{tid}`: approved={row['manifest_approved']}, train_safety={row['train_safety']}, "
            f"dataset_weight={row['dataset_sampling_weight']}, normal_pool={row['in_normal_authoring_pool']}, "
            f"open_audits={row['open_audit_count']}, parametric_artifact={row['has_task_local_parametric_artifact']}, "
            f"four_query={row['four_query_supervision_retained']}, source={row['source_class']}."
        )
    lines += [
        "",
        "The notable mismatch is concrete: a reviewed-safe record has weight 0, while an unverified record with an unresolved "
        "domain/validator audit has weight 1. Another full-weight reviewed-safe record retains unresolved teaching ambiguity. "
        "All three derived catalog rows predate their current source versions.",
        "",
        "## Bounded alternative",
        "",
        "Keep the 10% evaluation-focus branch unchanged. In a 30-assignment experiment, use 3 focus assignments and 27 normal "
        "assignments; stratify 6 of the normal assignments across open teachability evidence, weight/safety mismatches, and missing "
        "parameter/four-query evidence, leaving 21 uniform. Compare six targeted assignments with six matched uniform assignments.",
        "",
        "Adopt only if targeted allocation yields at least 1.25x accepted ambiguity-free, Racket-replayed, deduplicated four-query "
        "episodes per reviewer-hour without a higher failure rate. Stop after three matched pairs if yield is <=0.5x or cost exceeds 2x; "
        "always stop at 30 assignments.",
        "",
        "## Limits",
        "",
    ]
    lines.extend(f"- {item}" for item in report["coverage_limits"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--sample-size", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.work_root, args.seed, args.sample_size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"sampled_ids": report["sampled_ids"], "out": str(args.out), "status": "completed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
