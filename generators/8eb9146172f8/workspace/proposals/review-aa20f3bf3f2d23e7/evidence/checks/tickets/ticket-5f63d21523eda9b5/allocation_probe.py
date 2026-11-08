#!/usr/bin/env python3
"""Bounded, seed-replayable allocation-quality inspection for this packet.

The probe is intentionally static: it reads the immutable packet manifest,
catalog and task-local retained evidence.  It does not rerun a corpus census,
change allocation, approve data, or call the Racket oracle.
"""
from __future__ import annotations

import ast
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TICKET_ID = "ticket-5f63d21523eda9b5"
SEED = "0f5b1a79e7b735e5f7ba3e089f9c6aad4dc6b331c36b68619c8bc321d6d6a802"
PINNED_SOURCE_PATH = "repo/generators/0a9e3d364bb3/generator.py"
PINNED_SOURCE_SHA256 = "42cf51fb28002b7a663a6816387b5050047798392f5f79827a7204336511ed42"

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"

TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".py", ".log"}
KEYWORD_PATTERNS = {
    "lint": re.compile(r"\blint(?:er|ing)?\b", re.I),
    "rejection_or_repair": re.compile(r"\breject(?:ed|ion)?\b|\brepair(?:ed|s|ing)?\b", re.I),
    "ambiguity_or_rival": re.compile(r"ambig|rival|identif", re.I),
    "grammar": re.compile(r"\bgrammar\b", re.I),
    "dedup_or_uniqueness": re.compile(r"dedup|unique input|duplicate input|uniqueness", re.I),
    "racket": re.compile(r"\bracket\b", re.I),
    "four_query": re.compile(
        r"four[- ]quer(?:y|ies)|--test\s+4|n_test\s*[=:]\s*4|query_count\s*[=:]\s*4",
        re.I,
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seeded_sample(manifest: dict[str, Any], seed: str, count: int) -> list[str]:
    ids = sorted(manifest["generators"])
    return random.Random(int(seed, 16)).sample(ids, min(count, len(ids)))


def policy_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    policy = manifest["main_draw_policy"]
    focus = policy["evaluation_focus"]
    anchors = focus["anchors"]
    related = {task_id for anchor in anchors for task_id in anchor.get("main_ids", [])}
    return {
        "all_ids": len(manifest["all_ids"]),
        "main_ids": len(manifest["main_ids"]),
        "normal_ids": len(policy["normal_ids"]),
        "normal_pool_is_subset_of_main": set(policy["normal_ids"]) <= set(manifest["main_ids"]),
        "normal_pool_uniform_selection": True,
        "focus_probability": focus["probability"],
        "focus_anchors": len(anchors),
        "focus_anchors_with_related_generators": sum(bool(anchor.get("main_ids")) for anchor in anchors),
        "focus_anchors_without_related_generators": sum(not anchor.get("main_ids") for anchor in anchors),
        "focus_related_links": sum(len(anchor.get("main_ids", [])) for anchor in anchors),
        "focus_unique_related_generators": len(related),
        "focus_only_main_ids": sorted(set(manifest["main_ids"]) - set(policy["normal_ids"])),
        "focus_selection_order": "uniform public anchor, then uniform related generator; fall back to the preselected normal task when no related generator exists",
    }


def verify_pinned_source(work: Path = WORK) -> dict[str, Any]:
    path = work / PINNED_SOURCE_PATH
    actual = sha256(path)
    return {
        "path": PINNED_SOURCE_PATH,
        "expected_sha256": PINNED_SOURCE_SHA256,
        "actual_sha256": actual,
        "match": actual == PINNED_SOURCE_SHA256,
    }


def load_catalog(repo: Path = REPO) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in (repo / "catalog/puzzles.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def ast_metadata(source: Path) -> dict[str, Any]:
    tree = ast.parse(source.read_text(), filename=str(source))
    assignments: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and value is not None:
                    assignments[target.id] = value

    def literal(name: str) -> Any:
        node = assignments.get(name)
        if node is None:
            return None
        try:
            return ast.literal_eval(node)
        except (ValueError, TypeError):
            return None

    axes_node = assignments.get("AXES")
    axes_count = len(axes_node.keys) if isinstance(axes_node, ast.Dict) else None
    rival_counts: dict[str, int | None] = {}
    for name in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        node = assignments.get(name)
        rival_counts[name] = len(node.keys) if isinstance(node, ast.Dict) else None
    helpful = literal("HELPFUL_TEXTURES")
    return {
        "version": literal("VERSION"),
        "rule_hash": literal("RULE_HASH"),
        "examples_needed": literal("EXAMPLES_NEEDED"),
        "axes_count": axes_count,
        "helpful_texture_count": len(helpful) if isinstance(helpful, (list, tuple)) else None,
        "literal_rival_counts": rival_counts,
    }


def compact_task_texts(task_dir: Path) -> dict[str, str]:
    candidates = [
        task_dir / "SUMMARY.md",
        task_dir / "notes.md",
        task_dir / "evidence/review_index.json",
        task_dir / "evidence/associated_notes.jsonl",
    ]
    candidates.extend(sorted(task_dir.glob("tests/*.py")))
    candidates.extend(sorted(task_dir.glob("workspace/*.md")))
    candidates.extend(sorted(task_dir.glob("workspace/*.py")))
    texts: dict[str, str] = {}
    for path in candidates:
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            try:
                texts[str(path.relative_to(REPO))] = path.read_text(errors="replace")
            except OSError:
                continue
    return texts


def keyword_evidence(texts: dict[str, str]) -> dict[str, list[str]]:
    return {
        name: sorted(path for path, text in texts.items() if pattern.search(text))
        for name, pattern in KEYWORD_PATTERNS.items()
    }


def review_state(task_dir: Path, current_sha: str) -> dict[str, Any]:
    path = task_dir / "evidence/review_index.json"
    if not path.is_file():
        return {
            "path": None,
            "present": False,
            "current_source_bound": False,
            "audit_count": 0,
            "audit_resolutions": [],
            "actionable_current_audit_count": 0,
            "no_issue_needs_triage_count": 0,
            "decision_count": 0,
        }
    data = json.loads(path.read_text())
    audits = data.get("audits", [])
    actionable = 0
    no_issue_triage = 0
    for audit in audits:
        source_bound = audit.get("source_sha256") == current_sha
        resolution = audit.get("resolution")
        text = str(audit.get("text", "")).lower()
        unresolved = resolution in {None, "unresolved", "needs_triage"}
        if source_bound and unresolved:
            if "no issue found" in text:
                no_issue_triage += 1
            else:
                actionable += 1
    return {
        "path": str(path.relative_to(REPO)),
        "present": True,
        "current_source_bound": data.get("current_source_sha256") == current_sha,
        "audit_count": len(audits),
        "audit_resolutions": [audit.get("resolution") for audit in audits],
        "actionable_current_audit_count": actionable,
        "no_issue_needs_triage_count": no_issue_triage,
        "decision_count": len(data.get("decisions", [])),
    }


def evidence_inventory(task_dir: Path) -> dict[str, Any]:
    files = [path for path in task_dir.rglob("*") if path.is_file()]
    racket_files = [
        path for path in files
        if "racket" in path.name.lower() and "counterexamples" in path.parts
    ]
    audit_manifests = sorted(task_dir.glob("counterexamples/**/audit_assets.json"))
    return {
        "task_files": len(files),
        "task_bytes": sum(path.stat().st_size for path in files),
        "test_files": sorted(str(path.relative_to(REPO)) for path in task_dir.glob("tests/test_*.py")),
        "workspace_files": sorted(str(path.relative_to(REPO)) for path in task_dir.glob("workspace/**/*") if path.is_file()),
        "audit_asset_manifests": sorted(str(path.relative_to(REPO)) for path in audit_manifests),
        "retained_racket_files": sorted(str(path.relative_to(REPO)) for path in racket_files),
        "retained_racket_bytes": sum(path.stat().st_size for path in racket_files),
    }


def sampled_record(
    task_id: str,
    manifest: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    task_dir = REPO / "generators" / task_id
    manifest_row = manifest["generators"][task_id]
    source = REPO / manifest_row["generator"]
    actual_sha = sha256(source)
    cat = catalog[task_id]
    texts = compact_task_texts(task_dir)
    keywords = keyword_evidence(texts)
    review = review_state(task_dir, actual_sha)
    inventory = evidence_inventory(task_dir)
    meta = ast_metadata(source)
    parametric = task_dir / "workspace/parametric/prototype.py"
    explicit_four_query = bool(keywords["four_query"])
    lesson_evidence = bool(keywords["ambiguity_or_rival"])
    dedup_evidence = bool(keywords["dedup_or_uniqueness"])
    retained_racket = bool(inventory["retained_racket_files"])

    risk_flags: list[str] = []
    if review["actionable_current_audit_count"]:
        risk_flags.append("current-source actionable audit is unresolved")
    if not review["present"]:
        risk_flags.append("no current review index")
    if not retained_racket:
        risk_flags.append("no task-local retained Racket receipt in this packet")
    if not explicit_four_query:
        risk_flags.append("no explicit four-query receipt")
    if not parametric.is_file():
        risk_flags.append("no task-local parametric prototype")
    if not dedup_evidence:
        risk_flags.append("no explicit task-local dedup/unique-input receipt")

    gain = 0.0
    if review["actionable_current_audit_count"]:
        gain += 4.0
    if not review["present"]:
        gain += 2.0
    if not explicit_four_query:
        gain += 1.0
    if not parametric.is_file():
        gain += 1.0
    if not lesson_evidence:
        gain += 1.0
    if review["no_issue_needs_triage_count"]:
        gain += 0.5

    cost = 1.0
    if not review["present"]:
        cost += 1.0
    if not inventory["test_files"]:
        cost += 1.0
    if not retained_racket:
        cost += 1.0
    if not lesson_evidence or not dedup_evidence:
        cost += 1.0

    source_labels = cat.get("sources", [])
    external_named = [
        label for label in source_labels
        if "arc-gen" in label.lower() or "re-arc" in label.lower()
    ]
    return {
        "task_id": task_id,
        "source": {
            "path": str(source.relative_to(WORK)),
            "manifest_sha256": manifest_row["generator_sha256"],
            "actual_sha256": actual_sha,
            "hash_match": actual_sha == manifest_row["generator_sha256"],
        },
        "approved": bool(manifest_row.get("approved")),
        "normal_draw_pool": task_id in manifest["main_draw_policy"]["normal_ids"],
        "main_draw_pool": task_id in manifest["main_ids"],
        "catalog": {
            "mix_weight": cat.get("mix_weight"),
            "sources": source_labels,
            "named_arc_gen_or_re_arc_sources": external_named,
            "review_status": cat.get("review_status"),
            "train_safety": cat.get("train_safety"),
            "canonical_rows": cat.get("canonical_rows"),
            "summary": cat.get("summary"),
        },
        "generator_contract": meta,
        "parametric_prototype": str(parametric.relative_to(REPO)) if parametric.is_file() else None,
        "explicit_four_query_evidence_paths": keywords["four_query"],
        "review": review,
        "inventory": inventory,
        "source_specific_evidence_paths": keywords,
        "risk_flags": risk_flags,
        "bounded_estimate": {
            "marginal_quality_gain_units": gain,
            "review_cost_units": cost,
            "estimated_gain_per_cost": round(gain / cost, 3),
            "interpretation": "transparent triage heuristic only; not a quality benchmark, approval score, or measured model-data value",
        },
    }


def pool_summary(
    manifest: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    normal_ids = manifest["main_draw_policy"]["normal_ids"]
    mix = Counter(str(catalog[task_id].get("mix_weight")) for task_id in normal_ids)
    statuses = Counter(catalog[task_id].get("review_status") or "blank" for task_id in normal_ids)
    safety = Counter(catalog[task_id].get("train_safety") or "blank" for task_id in normal_ids)
    provenance = Counter()
    missing_review_index = 0
    actionable_audit = 0
    no_issue_triage = 0
    parametric = 0
    explicit_four_query = 0
    for task_id in normal_ids:
        row = catalog[task_id]
        for label in row.get("sources", []):
            family = "bank" if label.startswith("bank:") else label
            provenance[family] += 1
        task_dir = REPO / "generators" / task_id
        current_sha = manifest["generators"][task_id]["generator_sha256"]
        review = review_state(task_dir, current_sha)
        missing_review_index += int(not review["present"])
        actionable_audit += int(bool(review["actionable_current_audit_count"]))
        no_issue_triage += int(bool(review["no_issue_needs_triage_count"]))
        parametric += int((task_dir / "workspace/parametric/prototype.py").is_file())
        texts = compact_task_texts(task_dir)
        explicit_four_query += int(bool(keyword_evidence(texts)["four_query"]))
    return {
        "normal_pool_records": len(normal_ids),
        "catalog_mix_weight_counts": dict(sorted(mix.items())),
        "catalog_review_status_counts": dict(sorted(statuses.items())),
        "catalog_train_safety_counts": dict(sorted(safety.items())),
        "source_label_family_memberships": dict(sorted(provenance.items())),
        "records_missing_review_index": missing_review_index,
        "records_with_current_actionable_audit": actionable_audit,
        "records_with_no_issue_needing_triage": no_issue_triage,
        "records_with_task_local_parametric_prototype": parametric,
        "records_with_explicit_four_query_evidence": explicit_four_query,
        "coverage_note": "Keyword/file evidence is a lower bound; absence means not exposed in this packet, not proof the work never occurred.",
    }


def alternative_proposal(records: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        records,
        key=lambda row: (
            -row["bounded_estimate"]["estimated_gain_per_cost"],
            -row["bounded_estimate"]["marginal_quality_gain_units"],
            row["task_id"],
        ),
    )
    return {
        "name": "evidence-stratified shadow allocator",
        "production_change": False,
        "preserved_boundaries": [
            "keep the public-evaluation focus at 10%",
            "keep current source/rule pins, approvals, and training admission boundaries",
            "do not alter catalog mix_weight values during the experiment",
        ],
        "shadow_normal_branch": {
            "50_percent": "current-source actionable unresolved audit or retained exact teaching witness",
            "30_percent": "missing current review index, Racket receipt, explicit four-query receipt, or task-local parameter prototype",
            "20_percent": "uniform normal-pool control to retain coverage and detect score blind spots",
        },
        "sample_priority_order": [row["task_id"] for row in ranked],
        "sample_estimates": {
            row["task_id"]: row["bounded_estimate"] for row in ranked
        },
        "bounded_test": {
            "design": "shadow-select 12 normal-branch records with the current uniform allocator and 12 with the stratified allocator; cap each record at 20 reviewer minutes and one batched Racket-label receipt",
            "primary_metric": "qualified deliverables per reviewer hour",
            "qualified_deliverable": "current-source-bound patch or separate prototype with focused tests, matching authority labels, four distinct queries, no surviving declared rival, and no duplicate visible inputs",
            "secondary_metrics": [
                "source-bound audit findings closed or precisely retained",
                "reviewer minutes and Racket executions",
                "distinct query/input rate",
                "lesson ambiguity and hard integrity failure rates",
            ],
            "early_stop": "stop the shadow arm after 6 records per arm if it has two hard integrity failures (source/authority mismatch, answer leakage, or duplicate-query padding) or uses >1.5x reviewer time with no additional qualified deliverable",
            "decision_rule": "after 12 per arm, expand only if the stratified arm yields at least 25% more qualified deliverables per reviewer hour with no higher ambiguity or hard-failure rate; otherwise retain the current allocator",
        },
        "coverage_gaps": [
            "only three seeded records were inspected",
            "no sampled catalog row identifies ARC-GEN or RE-ARC provenance, so source-specific linter/rejection/grammar quality for those sources remains unknown",
            "the heuristic estimates marginal review leverage, not model accuracy or universal task quality",
            "task-local keyword absence may reflect missing retained receipts rather than missing historical work",
        ],
    }


def build_report(work: Path = WORK) -> dict[str, Any]:
    manifest = json.loads((work / "PACKET-MANIFEST.json").read_text())
    catalog = load_catalog(work / "repo")
    sample_ids = seeded_sample(manifest, SEED, 3)
    records = [sampled_record(task_id, manifest, catalog) for task_id in sample_ids]
    report = {
        "schema": "arcpuzzles-bounded-allocation-quality-v1",
        "ticket_id": TICKET_ID,
        "seed": SEED,
        "pinned_ticket_source": verify_pinned_source(work),
        "sample_method": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.generators), 3)",
        "sampled_ids": sample_ids,
        "draw_policy": policy_summary(manifest),
        "parametric_priority_counts": manifest.get("parametric_priority", {}).get("counts", {}),
        "normal_pool_snapshot": pool_summary(manifest, catalog),
        "sampled_records": records,
        "source_provenance_observation": {
            "sample_contains_named_arc_gen_or_re_arc": any(
                row["catalog"]["named_arc_gen_or_re_arc_sources"] for row in records
            ),
            "statement": "Provenance labels were recorded but were not used as quality evidence; no sampled row exposes ARC-GEN or RE-ARC as a catalog source label.",
        },
        "alternative": alternative_proposal(records),
        "limitations": [
            "static packet inspection only; no corpus-wide rerun or model job",
            "no allocation, approval, catalog weight, or training-boundary change was made",
            "retained reviewer-reported evidence remains reviewer-reported until maintainer assessment",
        ],
    }
    if not report["pinned_ticket_source"]["match"]:
        raise RuntimeError("pinned ticket source changed")
    if not all(row["source"]["hash_match"] for row in records):
        raise RuntimeError("sampled source hash mismatch")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    policy = report["draw_policy"]
    pool = report["normal_pool_snapshot"]
    lines = [
        "# Bounded allocation-quality proposal",
        "",
        f"Ticket `{report['ticket_id']}`; seed `{report['seed']}`.",
        f"Seeded sample: {', '.join(f'`{x}`' for x in report['sampled_ids'])}.",
        "",
        "## Observed allocation",
        "",
        f"The packet has {policy['all_ids']} records, {policy['main_ids']} main IDs, and "
        f"{policy['normal_ids']} uniformly selected normal IDs. The public-evaluation focus remains "
        f"{policy['focus_probability']['numerator']}/{policy['focus_probability']['denominator']}; "
        f"only {policy['focus_anchors_with_related_generators']} of {policy['focus_anchors']} anchors "
        f"has related generators in this packet, covering {policy['focus_unique_related_generators']} IDs. "
        "The other focused anchors retain the normal task and act as inspired-extension prompts.",
        "",
        f"Normal-pool catalog mix weights are `{pool['catalog_mix_weight_counts']}`. They are dataset "
        "sampling weights, not authoring-review priorities.",
        "",
        "## Sample",
        "",
        "| task | provenance | review state | key gap/finding | estimated gain/cost |",
        "|---|---|---|---|---:|",
    ]
    for row in report["sampled_records"]:
        review = row["review"]
        if review["actionable_current_audit_count"]:
            state = "current actionable audit"
        elif not review["present"]:
            state = "no review index"
        elif review["no_issue_needs_triage_count"]:
            state = "finite no-issue audit, needs triage"
        else:
            state = "indexed"
        key = row["risk_flags"][0] if row["risk_flags"] else "no sampled gap"
        provenance = ", ".join(row["catalog"]["sources"]) or "none"
        ratio = row["bounded_estimate"]["estimated_gain_per_cost"]
        lines.append(f"| `{row['task_id']}` | {provenance} | {state} | {key} | {ratio:.3f} |")
    lines.extend([
        "",
        "The estimate is a transparent triage heuristic for marginal review leverage. It is not an "
        "approval score, source ranking, or measured model-data value.",
        "",
        "## Alternative and stopping rule",
        "",
        "Run a shadow allocator only: 50% current-source actionable audits/exact teaching witnesses, "
        "30% missing review/Racket/four-query/parameter receipts, and 20% uniform controls. Keep the "
        "production 10% public focus, all approvals, catalog weights, and training boundaries unchanged.",
        "",
        report["alternative"]["bounded_test"]["design"] + ".",
        "",
        "Primary metric: " + report["alternative"]["bounded_test"]["primary_metric"] + ".",
        "",
        "Stopping rule: " + report["alternative"]["bounded_test"]["early_stop"] + ".",
        "",
        "Decision rule: " + report["alternative"]["bounded_test"]["decision_rule"] + ".",
        "",
        "## Coverage limits",
        "",
    ])
    lines.extend(f"- {item}" for item in report["alternative"]["coverage_gaps"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report(WORK)
    report_path = HERE / "allocation_report.json"
    proposal_path = HERE / "proposal.md"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    proposal_path.write_text(render_markdown(report))
    print(json.dumps({
        "ticket_id": report["ticket_id"],
        "sampled_ids": report["sampled_ids"],
        "normal_pool_records": report["normal_pool_snapshot"]["normal_pool_records"],
        "sample_priority_order": report["alternative"]["sample_priority_order"],
        "report": str(report_path),
        "proposal": str(proposal_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
