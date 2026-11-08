from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import re
import time

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
SEED = "fe116f7d1558c61dce7668c7a95c1ee3b69c2fae2ee7362fa59272778b2d36c0"
TARGET = "5295bc5ff1cb"
TARGET_SHA = "625977bee7e1093d9279914f378c4e84a02548e14e14727d318352dffd4e96a3"
TARGET_RULE = "e3633abbbdea"
EXPECTED_SAMPLE = ["bee63e6e52bd", "11c53dabb028", "4512012999bb"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path, key: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[row[key]] = row
    return rows


def rule_hash(source: str) -> str | None:
    match = re.search(r'^RULE_HASH\s*=\s*["\']([^"\']+)', source, re.MULTILINE)
    return match.group(1) if match else None


def parametric_summary(task_dir: Path, actual_sha: str) -> dict:
    manifest_path = task_dir / "workspace" / "parametric" / "evidence" / "manifest.json"
    if not manifest_path.is_file():
        return {
            "manifest_present": False,
            "current_source_bound": False,
            "variant_approved": None,
            "production_parametric_api": None,
            "parameters": None,
            "episodes": None,
            "queries_per_episode": None,
            "racket_executions": None,
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_export = manifest.get("current_owner_export")
    export_manifest = None
    if isinstance(current_export, str):
        candidate = REPO / current_export / "manifest.json"
        if candidate.is_file():
            export_manifest = json.loads(candidate.read_text(encoding="utf-8"))
    episodes = export_manifest.get("episodes") if export_manifest else None
    queries = export_manifest.get("queries") if export_manifest else None
    return {
        "manifest_present": True,
        "manifest_path": str(manifest_path.relative_to(WORK)),
        "manifest_sha256": sha256(manifest_path),
        "current_source_bound": manifest.get("generator_sha256") == actual_sha,
        "verification_status": manifest.get("verification_status"),
        "variant_approved": manifest.get("variant_approved"),
        "production_parametric_api": manifest.get("production_parametric_api"),
        "parameters": manifest.get("parameters"),
        "episodes": episodes,
        "queries_per_episode": (queries / episodes if isinstance(queries, int) and isinstance(episodes, int) and episodes else None),
        "racket_executions": export_manifest.get("racket_grid_executions") if export_manifest else None,
        "export_status": export_manifest.get("status") if export_manifest else None,
    }


def review_metrics(reviews: list[dict], actual_sha: str) -> dict:
    for row in reversed(reviews):
        after = row.get("after") or {}
        if after.get("source_hash") != actual_sha:
            continue
        metrics = after.get("metrics") or {}
        return {
            "source_bound": True,
            "racket_parity": metrics.get("racket_parity"),
            "focused_tests": metrics.get("focused_tests"),
            "downstream": metrics.get("downstream"),
            "diversity": metrics.get("diversity"),
        }
    return {
        "source_bound": False,
        "racket_parity": None,
        "focused_tests": None,
        "downstream": None,
        "diversity": None,
    }


def main() -> int:
    started = time.perf_counter()
    packet = json.loads((WORK / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    policy = packet["main_draw_policy"]
    normal_ids = sorted(policy["normal_ids"])
    sampled = random.Random(int(SEED, 16)).sample(normal_ids, 3)

    catalog = load_jsonl(REPO / "catalog" / "puzzles.jsonl", "id")
    assignments = load_jsonl(REPO / "shared" / "data" / "derived" / "kimi_generator_assignment.jsonl", "task_id")
    weights = json.loads((REPO / "shared" / "data" / "derived" / "generator_weights.json").read_text(encoding="utf-8"))
    reviews_by_task: dict[str, list[dict]] = {}
    for line in (REPO / "shared" / "data" / "derived" / "kimi_generator_reviews.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            reviews_by_task.setdefault(row["task_id"], []).append(row)

    observations = {}
    for task_id in [TARGET, *sampled]:
        task_dir = REPO / "generators" / task_id
        source_path = task_dir / "generator.py"
        source = source_path.read_text(encoding="utf-8")
        actual_sha = sha256(source_path)
        actual_rule = rule_hash(source)
        cat = catalog[task_id]
        assignment = assignments[task_id]
        packet_row = packet["generators"][task_id]
        test_modules = sorted(str(path.relative_to(WORK)) for path in (task_dir / "tests").glob("test*.py")) if (task_dir / "tests").is_dir() else []
        observations[task_id] = {
            "source_path": str(source_path.relative_to(WORK)),
            "actual_source_sha256": actual_sha,
            "actual_rule_hash": actual_rule,
            "packet_approved": packet_row.get("approved"),
            "packet_source_fresh": packet_row.get("generator_sha256") == actual_sha,
            "catalog_source_fresh": cat.get("reviewed_generator_sha256") == actual_sha,
            "catalog_rule_fresh": cat.get("reviewed_rule_hash") == actual_rule,
            "derived_assignment_source_fresh": assignment.get("generator_sha256") == actual_sha,
            "derived_assignment_rule_fresh": assignment.get("rule_hash_pinned") == actual_rule,
            "catalog_weight": weights.get(task_id),
            "sources": cat.get("sources"),
            "canonical_rows": cat.get("canonical_rows"),
            "review_status": cat.get("review_status"),
            "train_safety": cat.get("train_safety"),
            "health": cat.get("health"),
            "complexity": assignment.get("complexity_label"),
            "monitor_gate_status": assignment.get("monitor_gate_status"),
            "historical_or_stale_findings": assignment.get("findings"),
            "summary": cat.get("summary"),
            "test_module_count": len(test_modules),
            "test_modules": test_modules,
            "current_review_metrics": review_metrics(reviews_by_task.get(task_id, []), actual_sha),
            "parametric": parametric_summary(task_dir, actual_sha),
            "parametric_priority_origin": packet.get("parametric_priority", {}).get("related_generators", {}).get(task_id),
        }

    draw_source = REPO / "src" / "arcpuzzles" / "review_full_draw.py"
    draw_text = draw_source.read_text(encoding="utf-8")
    training_context = WORK / "TRAINING-CONTEXT.md"
    current_policy = {
        "source": str(draw_source.relative_to(WORK)),
        "source_sha256": sha256(draw_source),
        "all_ids": len(packet["all_ids"]),
        "main_ids": len(packet["main_ids"]),
        "normal_ids": len(normal_ids),
        "normal_selection": "uniform index over normal_ids derived from the assignment seed",
        "evaluation_focus_probability": policy["evaluation_focus"]["probability"],
        "evaluation_anchor_count": len(policy["evaluation_focus"]["anchors"]),
        "catalog_weights_used_by_authoring_draw": "generator_weights" in draw_text,
        "catalog_weight_file": "repo/shared/data/derived/generator_weights.json",
    }

    sample_weights = {task_id: observations[task_id]["catalog_weight"] for task_id in sampled}
    stale_assignment_rows = [task_id for task_id in sampled if not observations[task_id]["derived_assignment_source_fresh"]]
    prototype_rows = [task_id for task_id in sampled if observations[task_id]["parametric"]["manifest_present"]]
    simultaneous_four_query_rows = [
        task_id
        for task_id in sampled
        if observations[task_id]["parametric"].get("queries_per_episode") == 4
    ]

    result = {
        "schema": "bounded-owner-allocation-quality-v1",
        "ticket_id": "ticket-9bf180a44d26a83a",
        "task_id": TARGET,
        "status": "completed",
        "training_context": {
            "path": str(training_context.relative_to(WORK)),
            "sha256": sha256(training_context),
            "dated_snapshot": "2026-10-23 11:10-11:17 UTC training report",
            "reported_materialized_token_shares": {
                "ARCpuzzles": 0.37,
                "NVARC": 0.36,
                "ARC-GEN": 0.16,
                "RE-ARC": 0.11,
            },
            "caution": "The snapshot is older/frozen mixture evidence; source-bound current bytes and admission must be checked separately.",
        },
        "target_identity": {
            "expected_source_sha256": TARGET_SHA,
            "expected_rule_hash": TARGET_RULE,
            "source_matches": observations[TARGET]["actual_source_sha256"] == TARGET_SHA,
            "rule_matches": observations[TARGET]["actual_rule_hash"] == TARGET_RULE,
            "in_normal_pool": TARGET in normal_ids,
        },
        "authoring_policy": current_policy,
        "sample": {
            "seed": SEED,
            "recipe": "random.Random(int(seed, 16)).sample(sorted(main_draw_policy.normal_ids), 3)",
            "sampled_ids": sampled,
            "expected_ids_match": sampled == EXPECTED_SAMPLE,
            "observations": {task_id: observations[task_id] for task_id in sampled},
        },
        "pinned_target_observation": observations[TARGET],
        "catalog_weight_observation": {
            "sampled_weights": sample_weights,
            "all_equal_one": set(sample_weights.values()) == {1.0},
            "assessment": "Catalog weights are equal across materially different evidence states and are not read by the authoring draw; they are neither approval nor quality-per-cost scores.",
        },
        "source_freshness_observation": {
            "stale_derived_assignment_rows": stale_assignment_rows,
            "assessment": "Current catalog and packet bindings match the sampled source bytes, but two older derived assignment rows do not. Allocation or mastery logic should bind to source/rule hashes rather than ID-only state.",
        },
        "parameter_and_query_observation": {
            "sampled_current_parametric_rows": prototype_rows,
            "sampled_simultaneous_four_query_rows": simultaneous_four_query_rows,
            "target_has_current_parametric_manifest": observations[TARGET]["parametric"]["manifest_present"],
            "assessment": "The sample spans a current unapproved prototype, reviewed generators without parameter packages, and stale auxiliary metadata. The existing prototype records one query per episode, not four simultaneous queries.",
        },
        "external_source_coverage": {
            "ARC_GEN_or_RE_ARC_source_specific_records_in_packet": False,
            "assessment": "The packet supplies aggregate token shares only; it has no current source-specific ARC-GEN/RE-ARC linter, rejection, repair, ambiguity, grammar, Racket, or dedup receipts. No relative quality conclusion is supported for those libraries.",
        },
        "alternative_allocation_estimate": {
            "kind": "30-assignment authoring-policy pilot; not a dataset-mixture or training-weight change",
            "current_expected_counts": {
                "uniform_normal_pool": 27,
                "public_evaluation_focus": 3,
            },
            "proposed_counts": {
                "fresh_reviewed_missing_current_parameter_package": 18,
                "current_prototype_needing_four_query_or_acceptance_evidence": 6,
                "source_identity_or_remeasurement_repair": 3,
                "public_evaluation_focus": 3,
            },
            "estimated_tradeoff": "The pilot spends more review/Racket effort on converting existing work into source-bound four-query supervision and on stale-identity cleanup, while retaining most capacity for lower-risk fresh reviewed parameter authoring.",
            "metrics": [
                "routine-complete returns",
                "accepted fixed-setting parameter packages",
                "episodes with four distinct simultaneous Racket-labelled queries",
                "declared-rival ambiguity rate",
                "source/rule hash mismatch rate",
                "deduplicated unique visible inputs",
                "reviewer minutes",
                "Racket label executions",
                "accepted four-query episodes per 100 Racket executions",
            ],
            "stopping_rule": "After at least three assignments in each non-evaluation stratum, stop expanding a stratum if fewer than half are routine-complete, or if its median reviewer minutes exceed twice the fresh-reviewed stratum without at least a 20% gain in accepted source-bound four-query episodes per 100 Racket executions. Stop immediately on private-answer leakage, source/rule mismatch in retained evidence, or duplicate public payloads accepted as distinct.",
            "estimate_status": "proposal from a three-record normal-pool sample plus the pinned target; not an empirical optimum",
        },
        "interpretation": [
            "5295bc5ff1cb is a low-complexity, source-fresh, reviewed-safe normal-pool candidate with strong Racket/downstream evidence but no current parameter package.",
            "bee63e6e52bd has a current source-bound unapproved prototype and substantial Racket evidence, but its current export averages one query per episode rather than four simultaneous queries.",
            "11c53dabb028 demonstrates why stale derived assignment state must not override current catalog/source bindings.",
            "4512012999bb had historical high loss/graylist evidence but current source-bound review is strong; high loss alone is not a defect or downweighting reason.",
        ],
        "limits": [
            "Exactly three current normal-pool records were sampled; this is not a census or a measured training-ablation result.",
            "No model job, new Racket battery, or mixture change was run.",
            "Review cost estimates use retained evidence maturity and complexity labels, not directly measured minutes for these records.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }

    checks = {
        "target_source_matches_pin": result["target_identity"]["source_matches"],
        "target_rule_matches_pin": result["target_identity"]["rule_matches"],
        "target_in_normal_pool": result["target_identity"]["in_normal_pool"],
        "sample_matches_seed_recipe": result["sample"]["expected_ids_match"],
        "authoring_draw_does_not_use_catalog_weights": current_policy["catalog_weights_used_by_authoring_draw"] is False,
        "three_records_only": len(sampled) == 3,
    }
    result["checks"] = checks

    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "sampled_ids": sampled, "checks": checks, "report": str(out)}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
