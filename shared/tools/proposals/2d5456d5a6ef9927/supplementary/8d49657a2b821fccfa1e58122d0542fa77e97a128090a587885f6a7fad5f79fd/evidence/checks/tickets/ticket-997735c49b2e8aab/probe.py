#!/usr/bin/env python3
"""Bounded, source-bound allocation-quality inspection for one review ticket.

This probe intentionally performs no generator draw, Racket execution, model job,
or policy mutation.  It verifies current identities, deterministically samples the
packet, and summarizes the evidence already retained for those exact source bytes.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

TICKET_ID = "ticket-997735c49b2e8aab"
TICKET_SEED = "055de6b134ba6e3219e7bc95c9944c3e1ba14bc3e30eb21788bd70897a4501b1"
ANCHOR_ID = "033db13a9d37"
ANCHOR_SHA256 = "9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4"
ANCHOR_RULE_HASH = "3773168d1737"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assignment_nodes(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and value is not None:
                    result[target.id] = value
    return result


def literal(node: ast.AST | None, default: Any = None) -> Any:
    if node is None:
        return default
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return default


def dict_key_names(node: ast.AST | None) -> list[str]:
    if not isinstance(node, ast.Dict):
        return []
    result = []
    for key in node.keys:
        value = literal(key)
        if isinstance(value, str):
            result.append(value)
    return result


def test_function_count(path: Path) -> int:
    if not path.is_file():
        return 0
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(tree))


def task_test_count(home: Path) -> int:
    return sum(test_function_count(path) for path in sorted((home / "tests").glob("test_*.py")))


def review_index_summary(repo: Path, path: Path, current_sha: str) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": None,
            "present": False,
            "current_source_bound": False,
            "audit_count": 0,
            "open_audit_count": 0,
        }
    data = read_json(path)
    audits = data.get("audits", []) if isinstance(data, dict) else []
    open_audits = [a for a in audits if a.get("resolution") not in {"resolved", "no_issue"}]
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": sha256(path),
        "present": True,
        "current_source_bound": data.get("current_source_sha256") == current_sha,
        "audit_count": len(audits),
        "open_audit_count": len(open_audits),
        "audit_bindings": [
            {
                "return_id": row.get("return_id"),
                "resolution": row.get("resolution"),
                "source_sha256": row.get("source_sha256"),
                "matches_current_source": row.get("source_sha256") == current_sha,
                "verification_status": row.get("verification_status"),
            }
            for row in audits
        ],
    }


def evidence_for_sample(repo: Path, record: dict[str, Any]) -> dict[str, Any]:
    task_id = record["id"]
    home = repo / "generators" / task_id
    source = repo / record["generator"]
    nodes = assignment_nodes(source)
    axes = literal(nodes.get("AXES"), {})
    if not isinstance(axes, dict):
        axes = {}
    schedule = literal(nodes.get("SCHEDULE_PROFILES"), [])
    if not isinstance(schedule, (list, tuple, set, frozenset)):
        schedule = []
    declarations = {
        name: dict_key_names(nodes.get(name))
        for name in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_WITNESSES")
    }
    notes_path = home / "notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.is_file() else ""
    ref_manifest_path = home / "evidence" / "reference-rule" / "manifest.json"
    ref_manifest = read_json(ref_manifest_path) if ref_manifest_path.is_file() else None

    if task_id == "generic_waypoint_route_gen2" and isinstance(ref_manifest, dict):
        four_query = {
            "status": "retained_fixed_fixture_only",
            "retained_counts": ref_manifest.get("canonical_record_counts"),
            "live_runtime_counts": ref_manifest.get("current_runtime_counts"),
            "approved": ref_manifest.get("approved"),
            "labels_from": ref_manifest.get("labels_from"),
            "manifest_path": ref_manifest_path.relative_to(repo).as_posix(),
            "manifest_sha256": sha256(ref_manifest_path),
        }
    elif re.search(r"four distinct quer|four-query|4 distinct quer", notes, re.I):
        four_query = {
            "status": "reported_in_notes_not_reexecuted",
            "notes_path": notes_path.relative_to(repo).as_posix(),
            "notes_sha256": sha256(notes_path),
        }
    else:
        four_query = {"status": "no_current_four_query_receipt_found"}

    source_sha = sha256(source)
    review_path = home / "evidence" / "review_index.json"
    return {
        "task_id": task_id,
        "identity": {
            "source_path": source.relative_to(repo).as_posix(),
            "source_sha256": source_sha,
            "reviewed_generator_sha256": record.get("reviewed_generator_sha256"),
            "source_matches_reviewed": source_sha == record.get("reviewed_generator_sha256"),
            "rule_hash": record.get("rule_hash"),
            "reviewed_rule_hash": record.get("reviewed_rule_hash"),
            "rule_matches_reviewed": record.get("rule_hash") == record.get("reviewed_rule_hash"),
            "version": record.get("version"),
        },
        "allocation": {
            "approved": record.get("approved"),
            "approval_reasons": record.get("approval_reasons", []),
            "mix_weight": record.get("mix_weight"),
            "in_main_draw": record.get("in_main_draw"),
            "train_safety": record.get("train_safety"),
            "review_status": record.get("review_status"),
            "kind": record.get("kind"),
            "sources": record.get("sources", []),
        },
        "representation_and_teachability": {
            "summary": record.get("summary"),
            "axis_names": sorted(axes),
            "axis_count": len(axes),
            "examples_needed": literal(nodes.get("EXAMPLES_NEEDED")),
            "schedule_profiles": list(schedule),
            "semantic_declarations": declarations,
            "focused_test_functions": task_test_count(home),
            "parametric_workspace_present": (home / "workspace" / "parametric").is_dir(),
            "four_query_evidence": four_query,
        },
        "review_evidence": review_index_summary(repo, review_path, source_sha),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    work = args.work_root.resolve()
    repo = work / "repo"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles.catalog import Catalog  # type: ignore

    manifest_path = work / "PACKET-MANIFEST.json"
    training_context_path = work / "TRAINING-CONTEXT.md"
    manifest = read_json(manifest_path)
    catalog = Catalog(repo)

    sampled_ids = random.Random(int(TICKET_SEED, 16)).sample(sorted(manifest["all_ids"]), 3)
    main_ids = set(manifest["main_draw_policy"]["ids"])

    all_records = []
    for task_id in sorted(manifest["all_ids"]):
        row = catalog.describe(task_id)
        row["in_main_draw"] = task_id in main_ids
        all_records.append(row)

    sample_records = []
    for task_id in sampled_ids:
        row = catalog.describe(task_id)
        row["in_main_draw"] = task_id in main_ids
        packet_row = manifest["generators"][task_id]
        if sha256(repo / packet_row["generator"]) != packet_row["generator_sha256"]:
            raise AssertionError(f"packet source drift: {task_id}")
        sample_records.append(evidence_for_sample(repo, row))

    anchor = catalog.describe(ANCHOR_ID)
    anchor_path = repo / anchor["generator"]
    anchor_check = {
        "task_id": ANCHOR_ID,
        "source_path": anchor["generator"],
        "source_sha256": sha256(anchor_path),
        "source_matches_pin": sha256(anchor_path) == ANCHOR_SHA256,
        "rule_hash": anchor.get("rule_hash"),
        "rule_matches_pin": anchor.get("rule_hash") == ANCHOR_RULE_HASH,
        "approved": anchor.get("approved"),
        "note": "The deterministic three-record sample is not forced to include the ticket anchor; its identity is verified separately.",
    }
    if not anchor_check["source_matches_pin"] or not anchor_check["rule_matches_pin"]:
        raise AssertionError("ticket anchor identity drift")

    weight_counts = Counter(str(row.get("mix_weight")) for row in all_records)
    approved = [row for row in all_records if row.get("approved")]
    approved_main = [row for row in all_records if row.get("approved") and row["id"] in main_ids]
    positive_unapproved = [row for row in all_records if (row.get("mix_weight") or 0) > 0 and not row.get("approved")]
    source_categories = Counter()
    for row in all_records:
        for source in row.get("sources", []):
            source_categories[source.split(":", 1)[0]] += 1

    result = {
        "schema": "arcpuzzles-allocation-quality-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "ticket_seed": TICKET_SEED,
        "sampling_method": "random.Random(int(ticket_seed, 16)).sample(sorted(PACKET_MANIFEST.all_ids), 3)",
        "sampled_ids": sampled_ids,
        "ticket_anchor": anchor_check,
        "dated_context": {
            "path": "TRAINING-CONTEXT.md",
            "sha256": sha256(training_context_path),
            "scope": "Dated October 23, 2026 training report; not a live benchmark or current per-record approval source.",
            "reported_materialized_token_shares": {
                "ARCpuzzles": 0.37,
                "NVARC": 0.36,
                "ARC-GEN": 0.16,
                "RE-ARC": 0.11,
            },
            "reported_external_draw_protocol": "RE-ARC and ARC-GEN execute fresh generators and export eight draws per generator; later queries may be dropped for ambiguity or token limits.",
        },
        "packet": {
            "generator_count": len(all_records),
            "main_draw_distribution": manifest["main_draw_policy"]["distribution"],
            "main_draw_count": len(main_ids),
            "approved_count": len(approved),
            "approved_main_count": len(approved_main),
            "positive_weight_unapproved_count": len(positive_unapproved),
            "catalog_weight_counts": dict(sorted(weight_counts.items())),
            "source_category_counts": dict(sorted(source_categories.items())),
            "selection_policy": manifest["selection"].get("policy"),
            "selection_quotas": manifest["selection"].get("quotas"),
            "parametric_selected_tier": manifest["parametric_priority"].get("selected_tier"),
            "evaluation_focus": manifest["parametric_priority"].get("evaluation_focus"),
            "interpretation": "Uniform packet authoring draw and catalog mix_weight are selection/export controls, not quality certificates; effective training approval additionally requires current source/rule binding.",
        },
        "records": sample_records,
        "sample_observations": {
            "a5e17b975ae0": "Approved bank-derived repair with four exact axes, declared rivals/witnesses, task tests, and retained 1,200 production plus 2,000 cyclic query-rotation checks; no current parameter workspace or retained four-query export was found. Its finite wall grammar is explicit.",
            "c2cd365ed4fa": "Approved augmented/training histogram family with six exact axes and tests for Racket exactness, override boundaries, connectivity witnesses, and semantic impostors. It has no review index, lesson-competitor declaration, parameter workspace, or retained four-query episode in this packet.",
            "generic_waypoint_route_gen2": "Weight-zero unreviewed generic semantic variant. A retained protected-Racket fixture has three demos and four queries, but the live runtime still emits three demos and one query; the reference manifest explicitly denies approval/training admission and records an unused-context limitation.",
        },
        "external_source_evidence": {
            "ARC-GEN": "No sampled catalog row is explicitly ARC-GEN and no source-specific retained episode/rejection ledger is included here. Only dated aggregate token share and pipeline code are present, so no quality ranking is made.",
            "RE-ARC": "No sampled catalog row is explicitly RE-ARC and the off-box RE-ARC corpus is absent. The packet contains integration/quality-report code and dated aggregate share, not current sampled grammar/ambiguity receipts; no quality ranking is made.",
            "coverage_limit": "Provenance and aggregate share alone do not establish labels, teachability, grammar coverage, deduplication, or cost.",
        },
        "alternative_allocation": {
            "kind": "shadow experiment only; preserve current authoring draw, catalog weights, approvals, and training mixture",
            "quality_unit": "One source/rule-current, duplicate-visible-content-free episode with three demonstrations and four distinct Racket-labelled queries, plus demonstration-only refutation of each declared relevant rival or an explicit absence/limit statement.",
            "proposal": [
                {"records": 4, "stratum": "approved current generators lacking retained four-query evidence", "reason": "measures direct supervision readiness instead of inferring it from weight or approval"},
                {"records": 3, "stratum": "approved current generators with strong lesson/rival evidence but no parameter workspace", "reason": "tests whether a second meaningful setting adds quality without weakening established teaching"},
                {"records": 2, "stratum": "unapproved or weight-zero variants with retained Racket fixtures and a concrete API/admission gap", "reason": "measures repair cost before any promotion"},
                {"records": 1, "stratum": "existing evaluation-focus path", "reason": "preserves the packet's independent focus channel"},
            ],
            "estimated_cost": {
                "static_screen": "zero new labels; verify source/rule hashes, approval, open audits, counts, and visible-content identity first",
                "base_labels": 70,
                "base_labels_basis": "10 records × (3 demonstrations + 4 queries)",
                "paired_parameter_labels_max": 14,
                "maximum_labels": 84,
                "estimate_limit": "Label counts are exact design arithmetic; reviewer minutes, Racket seconds, acceptance yield, and model value are unmeasured.",
            },
            "comparison": "The current uniform authoring draw gives every selected ID equal opportunity regardless of four-query evidence, while catalog weights are nearly all 1.0. In this three-record sample, a static evidence screen separates two approved weight-1 generators from one unapproved weight-0 variant and reveals three different missing-support costs. The alternative spends labels only after that screen; the sample is too small to estimate a population gain.",
            "metrics": [
                "qualified episodes per reviewer minute",
                "qualified distinct query labels per Racket second",
                "visible-content duplicate rejection rate",
                "source/rule freshness failures",
                "declared-rival ambiguity and missing-contract rate",
                "parameter-setting coverage and four-query support by stratum/source",
                "grammar/size/source coverage without counting provenance as quality",
            ],
            "bounded_test": "Pre-register 20 future assignments: 10 current-policy and 10 alternative-stratified, with immutable source/rule pins. At most two episode attempts per record and one optional paired setting for the best two alternative records. Keep all failures.",
            "stopping_rule": "Stop either arm at its assignment/attempt cap. Stop the alternative early after any label/source drift, after two newly introduced canonical-domain regressions, or if fewer than 7/10 records yield qualified episodes. Adopt no allocation change unless qualified yield per reviewer hour improves at least 10%, Racket seconds per qualified episode do not worsen, and every stratum has at least one success; otherwise retain current policy or report inconclusive.",
        },
        "coverage_gaps": [
            "Three seeded records cannot estimate corpus quality, model benefit, or an optimal allocation.",
            "No new Racket labels, generator draws, model jobs, linter census, grammar census, or dataset export were run for this ticket.",
            "Retained counts are source-bound reports, not newly executed measurements.",
            "ARC-GEN and RE-ARC were not sampled and no current source-specific episode receipts were available in the packet.",
            "High loss is not treated as a defect, and proposed variants remain separate from production support and training admission.",
        ],
        "new_generator_runs": 0,
        "new_racket_runs": 0,
        "new_model_jobs": 0,
        "policy_or_admission_changed": False,
    }

    result_path = out / "result.json"
    write_json(result_path, result)
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "sampled_ids": sampled_ids,
        "approved_count": len(approved),
        "positive_weight_unapproved_count": len(positive_unapproved),
        "result": result_path.relative_to(work).as_posix(),
        "result_sha256": sha256(result_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
