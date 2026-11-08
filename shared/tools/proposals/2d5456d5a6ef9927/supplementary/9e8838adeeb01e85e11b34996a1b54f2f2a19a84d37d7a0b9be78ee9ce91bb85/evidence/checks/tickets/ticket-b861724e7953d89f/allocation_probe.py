#!/usr/bin/env python3
"""Bounded, deterministic static probe for the owner-allocation ticket.

The probe freezes the actual draw policy, ticket-seeded sample, catalog/weight
facts, and local evidence signals.  It intentionally does not run a corpus-wide
battery, Racket census, model job, or deduplication scan.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TICKET_ID = "ticket-b861724e7953d89f"
TARGET_TASK_ID = "0a9e3d364bb3"
TARGET_SHA256 = "42cf51fb28002b7a663a6816387b5050047798392f5f79827a7204336511ed42"
SEED = "d168b92302760f899412f1dc4159821e94f8a276cc27b96d9bf32d12cf68e1f3"
SIGNALS = (
    "racket",
    "dedup",
    "duplicate",
    "ambigu",
    "grammar",
    "reject",
    "repair",
    "census",
    "linter",
    "four-example",
    "four_query",
    "four-query",
    "lesson_competitor",
    "semantic_rival",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_by_id(path: Path, key: str = "id") -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get(key):
            rows[str(row[key])] = row
    return rows


def literal_assignments(source: str) -> tuple[dict[str, Any], set[str], set[str]]:
    tree = ast.parse(source)
    assignments: dict[str, Any] = {}
    defined_names: set[str] = set()
    functions: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value_node = node.value
            for target in targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
                    try:
                        assignments[target.id] = ast.literal_eval(value_node)
                    except (ValueError, TypeError):
                        pass
    return assignments, defined_names, functions


def text_signal_counts(root: Path) -> dict[str, int]:
    counts = Counter()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".jsonl", ".txt"}:
            continue
        if path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for signal in SIGNALS:
            counts[signal] += text.count(signal)
    return dict(sorted(counts.items()))


def sample_record(
    work: Path,
    task_id: str,
    packet: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
    generator_catalog: dict[str, dict[str, Any]],
    weights: dict[str, Any],
) -> dict[str, Any]:
    generator_dir = work / "repo/generators" / task_id
    source_path = generator_dir / "generator.py"
    source = source_path.read_text(encoding="utf-8")
    assignments, defined_names, functions = literal_assignments(source)
    axes = assignments.get("AXES")
    axis_names = sorted(axes) if isinstance(axes, dict) else []
    tests = sorted(str(path.relative_to(work)) for path in generator_dir.glob("tests/test_*.py"))
    workspace_tools = sorted(str(path.relative_to(work)) for path in generator_dir.glob("workspace/**/*.py"))
    evidence_files = sorted(str(path.relative_to(work)) for path in generator_dir.glob("evidence/**/*") if path.is_file())
    counterexample_files = sorted(
        str(path.relative_to(work)) for path in generator_dir.glob("counterexamples/**/*") if path.is_file()
    )
    catalog_row = catalog.get(task_id, {})
    generator_catalog_row = generator_catalog.get(task_id, {})
    manifest_row = packet["generators"][task_id]
    return {
        "task_id": task_id,
        "source_path": str(source_path.relative_to(work)),
        "source_sha256": sha256_file(source_path),
        "manifest": manifest_row,
        "catalog": {
            key: catalog_row.get(key)
            for key in (
                "health",
                "mix_weight",
                "notes_count",
                "review_status",
                "train_safety",
                "sources",
                "summary",
                "version",
            )
        },
        "derived_catalog": {
            key: generator_catalog_row.get(key)
            for key in (
                "lint_status",
                "combinatorial_reach",
                "diversity_score",
                "reach_score",
                "live_axes",
                "locked_axes",
                "tech_debt",
            )
        },
        "generator_weight": weights.get(task_id),
        "declarations": {
            "version": assignments.get("VERSION"),
            "examples_needed": assignments.get("EXAMPLES_NEEDED"),
            "axis_count": len(axis_names),
            "axis_names": axis_names,
            "has_self_check": "self_check" in functions,
            "has_lesson_competitors": "LESSON_COMPETITORS" in defined_names,
            "has_canonical_shortcuts": "CANONICAL_SHORTCUTS" in defined_names,
            "has_schedule_period": "LESSON_SCHEDULE_PERIOD" in defined_names,
        },
        "artifacts": {
            "tests": tests,
            "workspace_tools": workspace_tools,
            "evidence_file_count": len(evidence_files),
            "counterexample_file_count": len(counterexample_files),
            "public_parametric_prototype": (generator_dir / "workspace/parametric/prototype.py").exists(),
        },
        "evidence_signal_counts": text_signal_counts(generator_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    work = Path(__file__).resolve().parents[3]
    packet = json.loads((work / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    weights = json.loads(
        (work / "repo/shared/data/derived/generator_weights.json").read_text(encoding="utf-8")
    )
    catalog = jsonl_by_id(work / "repo/catalog/puzzles.jsonl")
    generator_catalog = jsonl_by_id(
        work / "repo/shared/data/derived/generator_catalog.jsonl", key="task_id"
    )

    target_source = work / f"repo/generators/{TARGET_TASK_ID}/generator.py"
    target_sha256 = sha256_file(target_source)
    if target_sha256 != TARGET_SHA256:
        raise RuntimeError(f"target source hash mismatch: {target_sha256}")

    normal_ids = list(packet["main_draw_policy"]["normal_ids"])
    sample_size = min(3, len(normal_ids))
    sampled_ids = random.Random(int(SEED, 16)).sample(sorted(normal_ids), sample_size)
    samples = [
        sample_record(work, task_id, packet, catalog, generator_catalog, weights)
        for task_id in sampled_ids
    ]

    evaluation_focus = packet["main_draw_policy"]["evaluation_focus"]
    focus_tiers = Counter(anchor.get("selected_tier") for anchor in evaluation_focus["anchors"])
    weight_counts = Counter(weights.values())
    source_families = sorted(
        {
            str(source)
            for sample in samples
            for source in (sample.get("catalog", {}).get("sources") or [])
        }
    )
    has_arcgen_or_rearc = any(
        "arc-gen" in source.lower() or "re-arc" in source.lower() for source in source_families
    )

    result = {
        "schema": "arcpuzzles-ticket-allocation-quality-v1",
        "ticket_id": TICKET_ID,
        "target": {
            "task_id": TARGET_TASK_ID,
            "source_path": str(target_source.relative_to(work)),
            "expected_sha256": TARGET_SHA256,
            "actual_sha256": target_sha256,
            "verified": target_sha256 == TARGET_SHA256,
        },
        "sampling": {
            "seed": SEED,
            "method": "random.Random(int(seed, 16)).sample(sorted(normal_ids), min(3, len(normal_ids)))",
            "normal_pool_count": len(normal_ids),
            "sampled_ids": sampled_ids,
            "all_sampled_in_normal_pool": all(task_id in normal_ids for task_id in sampled_ids),
            "all_sampled_approved": all(packet["generators"][task_id]["approved"] for task_id in sampled_ids),
        },
        "current_policy": {
            "main_id_count": len(packet.get("main_ids", [])),
            "normal_pool_count": len(normal_ids),
            "evaluation_focus_probability": evaluation_focus.get("probability"),
            "evaluation_anchor_count": len(evaluation_focus.get("anchors", [])),
            "eligible_related_generators": evaluation_focus.get("eligible_related_generators"),
            "mapped_tasks": evaluation_focus.get("mapped_tasks"),
            "fallback": evaluation_focus.get("fallback"),
            "focus_selected_tiers": dict(sorted(focus_tiers.items())),
            "selection_quotas": packet.get("selection", {}).get("quotas"),
            "owner_generator_count": packet.get("selection", {}).get("owner_generator_count"),
            "packet_generator_count": len(packet.get("generators", {})),
            "generator_weight_distribution": {
                str(weight): count for weight, count in sorted(weight_counts.items(), key=lambda item: item[0])
            },
        },
        "samples": samples,
        "comparison": {
            "representation": {
                "source_families_in_sample": source_families,
                "arc_gen_or_re_arc_selected": has_arcgen_or_rearc,
                "coverage_gap": (
                    "No ARC-GEN or RE-ARC record was selected by this three-record draw; source-family "
                    "quality cannot be compared from this sample."
                    if not has_arcgen_or_rearc
                    else None
                ),
            },
            "teachability": {
                "7c7f1f574a18": (
                    "Strong retained evidence: two focused test files, semantic-census tooling, declared "
                    "rivals, self-check, and reviewed-safe accepted-repair status."
                ),
                "9c26c4b2c305": (
                    "Strong four-example curriculum evidence: EXAMPLES_NEEDED=4, rivals/shortcuts, a lesson "
                    "probe, retained counterexamples, and reviewed-safe accepted-repair status."
                ),
                "5553241d87bf": (
                    "Accepted reviewed-safe repair with one focused test and retained semantic note, but the "
                    "packet exposes less task-local lesson/rival/schedule evidence than the other two."
                ),
            },
            "parameter_and_four_query_coverage": {
                "finding": (
                    "None of the three sampled records ships a public workspace/parametric/prototype.py. "
                    "9c26c4b2c305 explicitly supports four-example lesson windows; that is useful pedagogy "
                    "but is not the same artifact as a bounded four-query parametric episode export."
                ),
                "estimate": True,
            },
            "quality_per_cost_estimate": {
                "7c7f1f574a18": "high evidence maturity / medium review and Racket cost",
                "9c26c4b2c305": "high evidence maturity / medium review and Racket cost",
                "5553241d87bf": "medium evidence visibility / medium-high grammar and review cost",
                "basis": (
                    "Static packet evidence only: tests, retained notes/counterexamples, declarations, catalog "
                    "reach/lint metadata, and text signal counts. No fresh Racket or dedup census was run."
                ),
                "estimate": True,
            },
        },
        "alternative_allocation": {
            "scope": "review budget inside the 90% non-focus path; do not alter admission or training weights",
            "strata": [
                {
                    "share_percent": 50,
                    "target": (
                        "approved reviewed-safe originals with strong rule evidence but no bounded public "
                        "parametric/four-query artifact"
                    ),
                },
                {
                    "share_percent": 30,
                    "target": (
                        "approved or repair-ready records with thinner local ambiguity/grammar/dedup evidence, "
                        "using one bounded lesson/census probe"
                    ),
                },
                {
                    "share_percent": 20,
                    "target": (
                        "source-family and discovery coverage, explicitly including ARC-GEN and RE-ARC when "
                        "eligible, plus no-test/no-note records for cheap triage"
                    ),
                },
            ],
            "expected_direction": (
                "Estimated to improve accepted teachable lessons per reviewer/Racket hour by matching review "
                "depth to evidence debt while preserving a discovery lane; magnitude is unknown."
            ),
            "estimate": True,
        },
        "bounded_test": {
            "arms": ["current uniform normal-pool queue", "proposed stratified review queue"],
            "assignments_per_arm": 60,
            "cap_per_assignment": {"reviewer_minutes": 30, "racket_evaluations": 2000},
            "metrics": [
                "accepted source-bound lessons per reviewer hour",
                "four-query-identifiable settings accepted",
                "post-intake rejection rate",
                "ambiguity rate",
                "duplicate rate",
                "Racket evaluations per accepted lesson",
            ],
            "interim_after_per_arm": 20,
            "stopping_rule": (
                "Stop at 20 per arm if the stratified arm improves accepted lessons/hour by less than 10% "
                "or increases post-intake rejection by more than 5 percentage points. Otherwise finish 60; "
                "adopt only if the lower 95% bootstrap bound for the accepted-lessons/hour difference is above 0."
            ),
        },
        "coverage_limits": [
            "Three of 162 current normal-pool records only.",
            "No ARC-GEN or RE-ARC record selected by the deterministic sample.",
            "Static retained evidence only; no fresh Racket, model, corpus-wide rejection, or deduplication run.",
            "Cost and expected-quality comparisons are explicitly estimates, not measurements.",
        ],
        "status": "completed",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": "completed",
        "normal_pool_count": len(normal_ids),
        "sampled_ids": sampled_ids,
        "arc_gen_or_re_arc_selected": has_arcgen_or_rearc,
        "output": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
