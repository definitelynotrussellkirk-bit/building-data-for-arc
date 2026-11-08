#!/usr/bin/env python3
"""Reproducible bounded allocation-quality probe for ticket-a42cea8093566f13.

The probe samples exactly three current manifest records using the ticket seed,
reads retained source-bound evidence, performs only small default-generation
checks, and writes a proposal. It does not run Racket, a full battery, a model
job, or alter allocation/approval/training state.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

TICKET_ID = "ticket-a42cea8093566f13"
TICKET_SEED = "0929ff05eb795686ac76a43365d8d5721759b161f24e37d019b29714eddc0307"
PINNED_TASK_ID = "86af5978a32a"
PINNED_SOURCE_SHA256 = "ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e"
PINNED_RULE_HASH = "80100e676959"
EXPECTED_SAMPLE = ["8b6a2892a064", "022556f7ee2c", "a178821cc6bf"]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def source_literals(source: Path) -> tuple[dict[str, Any], set[str]]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    wanted = {"VERSION", "RULE_HASH", "EXAMPLES_NEEDED", "AXES", "SUMMARY"}
    values: dict[str, Any] = {}
    functions: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value = node.value
        else:
            continue
        for name in names:
            if name in wanted:
                try:
                    values[name] = ast.literal_eval(value)
                except Exception:
                    values[name] = "<dynamic>"
    return values, functions


def load_module(repo_root: Path, task_id: str):
    source = repo_root / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"allocation_probe_{task_id}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_count(path: Path) -> int:
    if not path.exists():
        return 0
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


def review_index_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"present": False, "audits": 0, "decisions": 0, "audit_resolutions": {}}
    row = json.loads(path.read_text(encoding="utf-8"))
    audits = row.get("audits", [])
    return {
        "present": True,
        "schema": row.get("schema"),
        "current_source_sha256": row.get("current_source_sha256"),
        "audits": len(audits),
        "decisions": len(row.get("decisions", [])),
        "audit_resolutions": dict(Counter(item.get("resolution", "missing") for item in audits)),
        "audit_source_hashes": sorted({item.get("source_sha256") for item in audits if item.get("source_sha256")}),
    }


def evidence_keywords(home: Path) -> dict[str, Any]:
    paths = [
        p for p in home.rglob("*")
        if p.is_file() and p.suffix.lower() in {".md", ".json", ".jsonl", ".py"}
        and "__pycache__" not in p.parts
    ]
    snippets = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")[:200_000]
        for p in paths
    ).lower()
    return {
        "parametric_workspace_present": (home / "workspace" / "parametric").is_dir(),
        "mentions_four_distinct_queries": bool(re.search(r"four distinct quer|4 distinct quer|query_count.{0,20}4", snippets)),
        "mentions_racket": "racket" in snippets,
        "mentions_lint": "lint" in snippets,
        "mentions_reject_or_repair": any(word in snippets for word in ("reject", "repair", "rejected draw")),
        "mentions_ambiguity_or_shortcut": any(word in snippets for word in ("ambigu", "shortcut", "rival")),
    }


def dynamic_probe(module, task_id: str, examples_needed: int) -> dict[str, Any]:
    probe_seed = int(hashlib.sha256(f"{TICKET_SEED}:{task_id}".encode()).hexdigest()[:12], 16)
    count = examples_needed + 4
    hashes: list[str] = []
    errors: list[dict[str, Any]] = []
    for sample_index in range(count):
        grid = module.generate(probe_seed, sample_index)
        grid_hash = sha256(json.dumps(grid, separators=(",", ":")).encode())
        hashes.append(grid_hash)
        if hasattr(module, "self_check"):
            reasons = module.self_check(grid)
            if reasons:
                errors.append({"sample_index": sample_index, "reasons": reasons})
    query_hashes = hashes[examples_needed:]
    return {
        "seed": probe_seed,
        "sample_indices": list(range(count)),
        "examples_needed_assumed": examples_needed,
        "draws": count,
        "distinct_inputs": len(set(hashes)),
        "prospective_query_count": 4,
        "distinct_prospective_queries": len(set(query_hashes)),
        "self_check_failures": errors,
        "input_sha256": hashes,
        "qualification": (
            "Small Python generation check only. Prospective queries were not Racket-labelled, "
            "deduplicated against a corpus, or proven identifiable from demonstrations."
        ),
    }


def source_family(sources: list[str]) -> str:
    lowered = [source.lower() for source in sources]
    if any("re-arc" in source or "re_arc" in source for source in lowered):
        return "RE-ARC"
    if any("arc-gen" in source or "arc_gen" in source for source in lowered):
        return "ARC-GEN"
    if any(source.startswith("bank:") for source in lowered):
        return "bank"
    return "internal/other"


def record_observation(task_id: str, catalog: dict[str, Any], static: dict[str, Any], review: dict[str, Any]) -> str:
    if task_id == "022556f7ee2c":
        return (
            "Unverified bank record with three unresolved/needs-triage source-bound audits reproducing the same "
            "three-demo sequential-ray teaching shortcut. Three advertised axes and distinct default draws do not "
            "compensate for a known lesson ambiguity; prioritize repair before additional volume."
        )
    if task_id == "a178821cc6bf":
        return (
            "Independently checked accepted repair with five exact axes, rule mirror, override observation, a "
            "lesson-identifiability hook, retained shortcut counterexample, and focused tests. It is the strongest "
            "sampled candidate for a bounded four-query Racket-labelled conversion, but no such receipt is retained."
        )
    if task_id == "8b6a2892a064":
        return (
            "Catalogued reviewed-safe/improved record with a broad scene-profile axis and focused tests, but no "
            "current review_index. Current notes say a recovered proposal lacks its genuine audit seed, so receipt "
            "continuity is weaker than the catalog status alone suggests; no four-query parametric receipt is retained."
        )
    return "No task-specific observation."


def build_report(work_root: Path) -> dict[str, Any]:
    repo_root = work_root / "repo"
    manifest_path = work_root / "PACKET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pinned_source = repo_root / "generators" / PINNED_TASK_ID / "generator.py"
    if sha256(pinned_source.read_bytes()) != PINNED_SOURCE_SHA256:
        raise AssertionError("ticket binding source changed")
    pinned_values, _ = source_literals(pinned_source)
    if pinned_values.get("RULE_HASH") != PINNED_RULE_HASH:
        raise AssertionError((pinned_values.get("RULE_HASH"), PINNED_RULE_HASH))

    population = sorted(manifest["generators"])
    sampled = random.Random(int(TICKET_SEED, 16)).sample(population, min(3, len(population)))
    if sampled != EXPECTED_SAMPLE:
        raise AssertionError((sampled, EXPECTED_SAMPLE))

    catalog_rows = json_rows(repo_root / "catalog" / "puzzles.jsonl")
    catalog_by_id = {row["id"]: row for row in catalog_rows}
    sample_rows: list[dict[str, Any]] = []

    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
    for task_id in sampled:
        home = repo_root / "generators" / task_id
        source = home / "generator.py"
        values, functions = source_literals(source)
        catalog = catalog_by_id[task_id]
        examples_needed = values.get("EXAMPLES_NEEDED")
        if not isinstance(examples_needed, int) or isinstance(examples_needed, bool) or examples_needed <= 0:
            examples_needed = 3
            examples_basis = "fallback 3 because source declares no positive EXAMPLES_NEEDED"
        else:
            examples_basis = "source EXAMPLES_NEEDED"
        module = load_module(repo_root, task_id)
        test_path = home / "tests" / f"test_generator_{task_id}.py"
        review = review_index_summary(home / "evidence" / "review_index.json")
        keywords = evidence_keywords(home)
        dynamic = dynamic_probe(module, task_id, examples_needed)
        if dynamic["self_check_failures"]:
            raise AssertionError({task_id: dynamic["self_check_failures"]})
        sample_rows.append({
            "task_id": task_id,
            "source": {
                "path": str(source.relative_to(work_root)),
                "sha256": sha256(source.read_bytes()),
                "version": values.get("VERSION"),
                "rule_hash": values.get("RULE_HASH"),
            },
            "catalog": {
                "sources": catalog.get("sources", []),
                "source_family": source_family(catalog.get("sources", [])),
                "mix_weight": catalog.get("mix_weight"),
                "review_status": catalog.get("review_status"),
                "train_safety": catalog.get("train_safety"),
                "approval_verification_status": catalog.get("approval_verification_status"),
                "primitives_count": len(catalog.get("primitives", [])),
                "primitives_qualification": (
                    "Catalog metadata only; this probe did not measure executed grammar coverage."
                ),
            },
            "contract": {
                "summary": values.get("SUMMARY"),
                "axes": values.get("AXES", {}),
                "axis_count": len(values.get("AXES", {})) if isinstance(values.get("AXES"), dict) else None,
                "examples_needed": examples_needed,
                "examples_needed_basis": examples_basis,
                "available_hooks": sorted(functions & {
                    "generate", "self_check", "rule_mirror", "strict_canonical_like",
                    "observe_overrides", "lesson_identifiable",
                }),
                "focused_test_functions": test_count(test_path),
            },
            "retained_evidence": {
                "review_index": review,
                "signals": keywords,
                "paths": [
                    str(path.relative_to(work_root))
                    for path in (
                        home / "notes.md",
                        home / "evidence" / "review_index.json",
                        home / "evidence" / "associated_notes.jsonl",
                        test_path,
                    )
                    if path.exists()
                ],
            },
            "bounded_dynamic_probe": dynamic,
            "assessment": record_observation(task_id, catalog, values, review),
        })

    priority = manifest["parametric_priority"]
    draw_policy = manifest["main_draw_policy"]
    focus = draw_policy["evaluation_focus"]
    direct_anchors = [anchor for anchor in focus["anchors"] if anchor["main_ids"]]
    mix_counts = Counter(str(row.get("mix_weight")) for row in catalog_rows)
    sample_families = Counter(row["catalog"]["source_family"] for row in sample_rows)

    return {
        "schema": "arcpuzzles-bounded-allocation-quality-probe-v1",
        "ticket": {
            "ticket_id": TICKET_ID,
            "consumer": "bounded_owner_allocation_experiment_proposal",
            "seed": TICKET_SEED,
            "pinned_task_id": PINNED_TASK_ID,
            "pinned_source_sha256": PINNED_SOURCE_SHA256,
            "pinned_rule_hash": PINNED_RULE_HASH,
        },
        "sampling": {
            "method": "random.Random(int(ticket_seed, 16)).sample(sorted(PACKET-MANIFEST generators), 3)",
            "population_size": len(population),
            "sampled_ids": sampled,
            "sample_source_families": dict(sample_families),
        },
        "authoring_policy": {
            "all_ids": len(manifest["all_ids"]),
            "main_ids": len(manifest["main_ids"]),
            "normal_ids": len(draw_policy["normal_ids"]),
            "selected_tier": priority["selected_tier"],
            "priority_counts": priority["counts"],
            "evaluation_focus": {
                "probability": focus["probability"],
                "anchors": len(focus["anchors"]),
                "direct_related_anchors": len(direct_anchors),
                "eligible_related_generators": sum(len(anchor["main_ids"]) for anchor in direct_anchors),
                "fallback": focus["fallback"],
                "qualification": focus["scope"],
            },
            "nominal_probability_interpretation": {
                "public_evaluation_focus": "1/10 of authoring assignments",
                "direct_mapped_anchor": "1/10 * 1/120 = 1/1200; each of two descendants is 1/2400",
                "normal_pool_total_including_focus_fallback": "9/10 + 1/10 * 119/120 = 1199/1200",
                "each_of_162_normal_targets": "1199/(1200*162) = 1199/194400 (approximately 0.6168%)",
                "qualification": "Analytical intended hash-modulo probabilities, not measured assignment frequencies.",
            },
        },
        "dataset_catalog": {
            "rows": len(catalog_rows),
            "mix_weight_counts": dict(sorted(mix_counts.items())),
            "sample_weights": {row["task_id"]: row["catalog"]["mix_weight"] for row in sample_rows},
            "distinction": (
                "Catalog mix_weight affects dataset sampling after filters; it is not used by the authoring draw, "
                "which selects from manifest priority pools and reserves 10% for evaluation focus."
            ),
        },
        "records": sample_rows,
        "comparison": {
            "baseline": (
                "Keep the current 10% evaluation focus and hash-uniform normal target selection; treat a selected "
                "generator as one authoring unit without an evidence-gap triage stage."
            ),
            "alternative": (
                "Preserve every draw probability, approval, and training boundary, but add a bounded post-draw "
                "follow-up queue: among each three already-drawn records, spend at most one extra slot on the highest "
                "source-bound value class—unresolved lesson defect first, then independently reviewed family lacking "
                "four-query Racket receipts, then receipt-continuity repair, then new volume."
            ),
            "estimated_quality_per_cost": {
                "baseline_estimate": (
                    "One new or edited record per authoring slot, with unknown admission yield when source-bound "
                    "lesson ambiguity and receipt gaps are not triaged."
                ),
                "alternative_estimate": (
                    "In this sample, all 3/3 records expose a concrete value target and 1/3 has a reproduced lesson "
                    "defect. A <=20-minute follow-up on the best candidate is estimated to yield more usable "
                    "supervision per review/Racket minute than adding another untriaged same-rule record."
                ),
                "estimate_limit": (
                    "Three records are not representative; no measured reviewer-time, rejection-rate, Racket-time, "
                    "deduplication-yield, or model-utility telemetry is present."
                ),
            },
        },
        "bounded_experiment": {
            "population": "12 future assignments produced by the unchanged current draw policy",
            "intervention": (
                "For four consecutive 3-assignment batches, permit one <=20-minute evidence-gap follow-up. "
                "Require exact source binding, retained Racket labels for four distinct queries when supported, "
                "demonstration-only competitor checks, and visible-payload deduplication."
            ),
            "metrics": [
                "accepted source-bound episodes per reviewer+Racket minute",
                "number of four-distinct-query Racket-verified receipts",
                "unresolved lesson competitors after the follow-up",
                "duplicate visible payloads rejected before export",
                "repair/rejection reason and source family",
            ],
            "success_rule": (
                "Adopt the follow-up queue only if at least 2 of 4 interventions produce a source-bound, "
                "competitor-checked receipt with four distinct Racket-labelled queries (or a documented hard support "
                "limit), zero silent duplicates, and median measured follow-up time <=20 minutes."
            ),
            "stop_rule": (
                "Stop after four interventions, or earlier if the first two both exceed 20 minutes, cannot obtain an "
                "independent authority label, or leave a query-changing competitor unresolved."
            ),
            "state_changes": "None in this proposal.",
        },
        "coverage_limits": [
            "The sample is three uniform manifest records, not a stratified estimate of the 162-target normal pool or approved dataset mixture.",
            "No sampled record is labelled ARC-GEN or RE-ARC; no source-family quality or volume claim about either corpus follows.",
            "The dynamic check used Python generation/self_check only; it did not create fresh Racket labels or prove lesson identifiability.",
            "Four distinct generated inputs are not equivalent to four distinct Racket-labelled, demonstration-identifiable queries.",
            "Catalog primitive lists are metadata, not measured executed grammar coverage.",
            "Catalog mix_weight 1.0 does not imply authoring priority, approval, safety, or training admission.",
            "Existing reviewer-reported findings remain source-bound and were not re-executed by this allocation probe.",
        ],
        "outcome": {
            "status": "completed",
            "summary": (
                "Deterministic three-record audit found heterogeneous evidence quality despite identical sample "
                "mix_weight 1.0: one reproduced unresolved lesson shortcut, one independently checked repair, and one "
                "reviewed-safe record with receipt-continuity gaps. Proposed a four-intervention post-draw triage test "
                "while preserving the 10% focus and all current draw/approval/training boundaries."
            ),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    rows = report["records"]
    lines = [
        "# Bounded allocation-quality proposal",
        "",
        f"Ticket: `{TICKET_ID}`  ",
        f"Seed: `{TICKET_SEED}`  ",
        "Sample: " + ", ".join(f"`{row['task_id']}`" for row in rows),
        "",
        "The current 10% evaluation focus, all other authoring probabilities, catalog weights, approvals, and training boundaries remain unchanged.",
        "",
        "## Observed records",
        "",
    ]
    for row in rows:
        lines.extend([
            f"### {row['task_id']}",
            "",
            row["assessment"],
            "",
            f"- Source: `{row['source']['path']}` @ `{row['source']['sha256']}`",
            f"- Catalog: sources `{row['catalog']['sources']}`, mix weight `{row['catalog']['mix_weight']}`, safety `{row['catalog']['train_safety']}`",
            f"- Contract: `{row['contract']['axis_count']}` axes, `{row['contract']['examples_needed']}` demonstrations, hooks `{row['contract']['available_hooks']}`",
            f"- Bounded generation: `{row['bounded_dynamic_probe']['distinct_inputs']}/{row['bounded_dynamic_probe']['draws']}` distinct inputs; four prospective queries `{row['bounded_dynamic_probe']['distinct_prospective_queries']}/4` distinct; no fresh Racket-label claim",
            "",
        ])
    lines.extend([
        "## Alternative allocation experiment",
        "",
        report["comparison"]["alternative"],
        "",
        f"**Experiment.** {report['bounded_experiment']['intervention']}",
        "",
        f"**Success rule.** {report['bounded_experiment']['success_rule']}",
        "",
        f"**Stop rule.** {report['bounded_experiment']['stop_rule']}",
        "",
        "## Coverage limits",
        "",
    ])
    lines.extend(f"- {limit}" for limit in report["coverage_limits"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.work_root.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.proposal.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({
        "sampled_ids": report["sampling"]["sampled_ids"],
        "status": report["outcome"]["status"],
        "summary": report["outcome"]["summary"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
