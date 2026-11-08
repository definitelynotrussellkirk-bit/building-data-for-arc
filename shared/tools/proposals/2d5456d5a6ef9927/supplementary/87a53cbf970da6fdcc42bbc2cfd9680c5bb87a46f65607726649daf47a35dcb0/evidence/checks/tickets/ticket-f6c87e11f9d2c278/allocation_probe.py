#!/usr/bin/env python3
"""One bounded, source-bound audit of the ARC puzzle authoring allocation."""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
PACKET = WORK / "PACKET-MANIFEST.json"
AUDIT_ASSIGNMENT = WORK / "AUDIT_ASSIGNMENT.json"
OUT = HERE / "allocation-audit.json"
SEED = "1787aa4ba72967380955541c461737ab76cc60b47e241ee1199ff432fa970278"
EXPECTED_SAMPLE = ["959992fc8fa9", "21c2b55a15ee", "056999828b88"]
TICKET_ID = "ticket-f6c87e11f9d2c278"
TICKET_SOURCE = "generators/02b1f274e160/generator.py"
TICKET_SOURCE_SHA256 = "10b7611b7a2f4df7ae697fa34500765bc272da3870c5548598d5f695677d7bff"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(WORK))


def evidence(path: Path) -> dict:
    return {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def load_catalog() -> dict[str, dict]:
    rows = {}
    for line in (REPO / "catalog" / "puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def tier_for(manifest: dict, task_id: str) -> str | None:
    for tier, ids in manifest["parametric_priority"]["tiers"].items():
        if task_id in ids:
            return tier
    return None


def review_record(task_id: str) -> tuple[dict, Path]:
    path = REPO / "generators" / task_id / "evidence" / "review_index.json"
    return json.loads(path.read_text(encoding="utf-8")), path


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)

    manifest = json.loads(PACKET.read_text(encoding="utf-8"))
    assignment = json.loads(AUDIT_ASSIGNMENT.read_text(encoding="utf-8"))
    ticket = next(row for row in assignment["tickets"] if row["ticket_id"] == TICKET_ID)
    assert ticket["seed"] == SEED
    assert ticket["source"]["path"] == f"repo/{TICKET_SOURCE}"
    assert ticket["source"]["sha256"] == TICKET_SOURCE_SHA256
    assert sha256_file(REPO / TICKET_SOURCE) == TICKET_SOURCE_SHA256

    sample = random.Random(int(SEED, 16)).sample(sorted(manifest["all_ids"]), 3)
    assert sample == EXPECTED_SAMPLE
    assert len(manifest["all_ids"]) == 300

    catalog = load_catalog()
    assert set(manifest["all_ids"]) <= set(catalog)
    packet_weights = Counter(catalog[task_id]["mix_weight"] for task_id in manifest["all_ids"])

    normal = manifest["main_draw_policy"]["normal_ids"]
    priority = manifest["parametric_priority"]
    focus = manifest["main_draw_policy"]["evaluation_focus"]
    assert normal == priority["main_ids"]
    assert len(normal) == 162
    assert priority["selected_tier"] == "approved_originals_need_parameters"
    assert focus["probability"] == {"numerator": 1, "denominator": 10}
    assert len(focus["anchors"]) == 120
    assert sum(bool(row["main_ids"]) for row in focus["anchors"]) == 1

    policy_source = REPO / "src" / "arcpuzzles" / "review_full_draw.py"
    policy_text = policy_source.read_text(encoding="utf-8")
    assert "pool = policy['normal_ids']" in policy_text
    assert "roll = int.from_bytes(hashlib.sha256(seed + b':evaluation-focus').digest(), 'big') % 10" in policy_text
    assert "mix_weight" not in policy_text[: policy_text.index("allocation efficiently produces high-quality data")]

    observations: list[dict] = []

    # 959992fc8fa9: approved/current normal pool, but retained evidence records three
    # source-bound teaching/distribution failures.
    task_id = "959992fc8fa9"
    row = catalog[task_id]
    record, review_path = review_record(task_id)
    battery_path = (
        REPO / "generators" / task_id / "counterexamples" /
        "review-d19682319424723a-v0002" / "retained" / "checks" / "audit" /
        task_id / "battery_failures.json"
    )
    battery = json.loads(battery_path.read_text(encoding="utf-8"))
    assert manifest["generators"][task_id]["approved"] is True
    assert task_id in normal and tier_for(manifest, task_id) == "approved_originals_need_parameters"
    assert row["review_status"] == "improved" and row["train_safety"] == "reviewed_safe"
    assert row["mix_weight"] == 1.0 and row["sources"] == ["augmented", "training"]
    assert record["current_source_sha256"] == manifest["generators"][task_id]["generator_sha256"]
    assert battery["verdict_note"] == "9 green, 0 advisory, 3 failed, 0 interrupted, 0 pending of 12"
    assert battery["findings"]["profile_floor"]["exact_profile_hits"] == 0
    assert battery["findings"]["profile_floor"]["draws"] == 60
    assert battery["findings"]["profile_floor"]["inclusive_envelope_hits"] == 6
    assert battery["findings"]["semantic_gate"]["hooks"] == "none"
    assert battery["findings"]["authority_sync"]["execution_parity"] is True
    observations.append({
        "task_id": task_id,
        "manifest_approved": True,
        "in_normal_authoring_pool": True,
        "parametric_tier": tier_for(manifest, task_id),
        "catalog": {key: row.get(key) for key in ("mix_weight", "sources", "review_status", "train_safety", "version")},
        "parameter_and_query_evidence": {
            "prototype_manifest_present": (REPO / "generators" / task_id / "workspace" / "parametric" / "evidence" / "manifest.json").exists(),
            "task_test_files": len(list((REPO / "generators" / task_id / "tests").glob("test*.py"))),
        },
        "retained_findings": {
            "battery": battery["verdict_note"],
            "canonical_profile_hits": "0/60 exact; 6/60 inclusive envelope",
            "semantic_contract": "none of strict_canonical_like, SEMANTIC_WITNESSES, lesson_identifiable",
            "authority": "two exact-text groups; execution parity passed",
        },
        "allocation_read": (
            "Approval and catalog weight do not erase current source-bound teaching/evidence debt; "
            "a parametric assignment here should budget for contract repair and canonical-profile support."
        ),
        "evidence": [evidence(review_path), evidence(battery_path)],
    })

    # 21c2b55a15ee: unapproved and outside the normal pool; retained override evidence
    # quantifies why source volume/weight alone is not usable-data quality.
    task_id = "21c2b55a15ee"
    row = catalog[task_id]
    record, review_path = review_record(task_id)
    ignored_path = (
        REPO / "generators" / task_id / "counterexamples" /
        "review-835b131676bab072-v0001" / "retained" / "checks" / "audit" /
        f"{task_id}-counterexample" / "ignored-n-components.json"
    )
    override_path = (
        REPO / "generators" / task_id / "counterexamples" /
        "review-835b131676bab072-v0001" / "retained" / "checks" / "audit" /
        f"{task_id}-override" / "result.json"
    )
    ignored = json.loads(ignored_path.read_text(encoding="utf-8"))
    override = json.loads(override_path.read_text(encoding="utf-8"))
    audit_text = "\n".join(item["text"] for item in record["audits"])
    assert manifest["generators"][task_id]["approved"] is False
    assert task_id not in normal and tier_for(manifest, task_id) == "other_unapproved"
    assert row["mix_weight"] == 1.0 and row["train_safety"] == "unverified"
    assert row["sources"] == ["bank:ad4abc25f505"]
    assert record["current_source_sha256"] == manifest["generators"][task_id]["generator_sha256"]
    assert "10,505 categorized findings" in audit_text
    assert "1,620 ignored/misrealized `grid_h` cases" in audit_text
    assert "1,620 `grid_w` cases" in audit_text
    assert "`RULE_HASH` is absent" in audit_text
    assert ignored["outputs_identical"] is True
    assert override.get("passed") is False
    observations.append({
        "task_id": task_id,
        "manifest_approved": False,
        "in_normal_authoring_pool": False,
        "parametric_tier": tier_for(manifest, task_id),
        "catalog": {key: row.get(key) for key in ("mix_weight", "sources", "review_status", "train_safety", "version")},
        "parameter_and_query_evidence": {
            "prototype_manifest_present": (REPO / "generators" / task_id / "workspace" / "parametric" / "evidence" / "manifest.json").exists(),
            "task_test_files": len(list((REPO / "generators" / task_id / "tests").glob("test*.py"))),
        },
        "retained_findings": {
            "override_findings": 10505,
            "grid_h_mismatches": 1620,
            "grid_w_mismatches": 1620,
            "ignored_n_components_witness": True,
            "missing_rule_hash": True,
            "ordinary_self_check_can_still_pass": True,
        },
        "allocation_read": (
            "Whitelist/catalog weight is not evidence of reliable controls. Repair cost and four-query "
            "coverage are presently uncertain because advertised axes are ignored or unprobeable."
        ),
        "evidence": [evidence(review_path), evidence(ignored_path), evidence(override_path)],
    })

    # 056999828b88: a mature accepted repair with strong measured evidence, but retained
    # morphology limits and no packet-local parametric/four-query artifact.
    task_id = "056999828b88"
    row = catalog[task_id]
    record, review_path = review_record(task_id)
    shortcut_path = (
        REPO / "generators" / task_id / "counterexamples" /
        "review-72e9283938f12a74-v0001" / "retained" / "checks" / "audit-probes.json"
    )
    connectivity_path = REPO / "generators" / task_id / "counterexamples" / "current-shortcut" / "checks" / "connectivity-final.json"
    shortcut_text = "\n".join(item["text"] for item in record["audits"])
    notes_path = REPO / "generators" / task_id / "notes.md"
    notes = notes_path.read_text(encoding="utf-8")
    assert manifest["generators"][task_id]["approved"] is True
    assert task_id not in normal and tier_for(manifest, task_id) is None
    assert row["mix_weight"] == 1.0 and row["review_status"] == "accepted_repair"
    assert row["train_safety"] == "reviewed_safe" and row["version"] == "6.1.0"
    assert record["current_source_sha256"] == manifest["generators"][task_id]["generator_sha256"]
    assert "600-draw probe" in shortcut_text and "zero I4 examples" in shortcut_text
    assert "600 draws at seed246810 yield 46 observed classes" in notes
    assert "All 591 measured overlapping windows refute both rivals" in notes
    assert shortcut_path.exists() and connectivity_path.exists()
    observations.append({
        "task_id": task_id,
        "manifest_approved": True,
        "in_normal_authoring_pool": False,
        "parametric_tier": None,
        "catalog": {key: row.get(key) for key in ("mix_weight", "sources", "review_status", "train_safety", "version")},
        "parameter_and_query_evidence": {
            "prototype_manifest_present": (REPO / "generators" / task_id / "workspace" / "parametric" / "evidence" / "manifest.json").exists(),
            "task_test_files": len(list((REPO / "generators" / task_id / "tests").glob("test*.py"))),
        },
        "retained_findings": {
            "current_repair_evidence": "600/600 parity/oracle reported; 591 overlapping four-demo windows refute two registered rivals",
            "deduplication_measurement": "500 distinct inputs in the 600-draw census",
            "morphology_gap": "retained 600-draw audit observed zero straight I4 examples",
            "bounded_support": "46 of 49 shape classes observed in a finite current-source sample",
        },
        "allocation_read": (
            "This is lower-risk evidence work than an unreviewed source, but the retained morphology gap "
            "and absent four-query prototype still make completion quality measurable rather than automatic."
        ),
        "evidence": [evidence(review_path), evidence(shortcut_path), evidence(connectivity_path), evidence(notes_path)],
    })

    # None of the deterministic sample advertises ARC-GEN or RE-ARC in catalog sources.
    sampled_sources = [source for item in observations for source in item["catalog"]["sources"]]
    source_text = " ".join(sampled_sources).lower()
    arc_gen_or_re_arc_sampled = "arc-gen" in source_text or "re-arc" in source_text or "re_arc" in source_text
    assert arc_gen_or_re_arc_sampled is False

    report = {
        "schema": "arcpuzzles-allocation-quality-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "seed": SEED,
        "sampling": {
            "recipe": "random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.all_ids), 3)",
            "population": 300,
            "sampled_ids": sample,
            "arc_gen_or_re_arc_sampled": arc_gen_or_re_arc_sampled,
        },
        "current_policy": {
            "authoring": {
                "normal_pool_count": len(normal),
                "normal_pool_tier": priority["selected_tier"],
                "normal_pool_equals_priority_main_ids": True,
                "evaluation_focus_probability": focus["probability"],
                "evaluation_anchor_count": len(focus["anchors"]),
                "anchors_with_direct_related_generator": 1,
                "anchors_using_inspired_extension_fallback": 119,
            },
            "parametric_priority_counts": priority["counts"],
            "catalog_dataset_weights": {
                "packet_rows": 300,
                "distribution": {str(weight): count for weight, count in sorted(packet_weights.items())},
                "sample_weights": {task_id: catalog[task_id]["mix_weight"] for task_id in sample},
            },
            "distinction": (
                "review_full_draw.py chooses authoring work from normal_ids with a separate 1-in-10 evaluation-focus roll; "
                "catalog mix_weight is dataset sampling metadata and does not drive that authoring draw."
            ),
            "ticket_weight_note": manifest["supplementary_ticket_policy"]["weight_basis"],
            "evidence": [evidence(PACKET), evidence(policy_source), evidence(REPO / "catalog" / "puzzles.jsonl")],
        },
        "sample_observations": observations,
        "assessment": {
            "measured": (
                "The current normal authoring pool is concentrated in one 162-task tier, while the deterministic three-task "
                "sample spans an approved-normal source with unresolved contract debt, an unapproved source with quantified "
                "control failures, and an accepted repair with strong but bounded coverage evidence. All three have catalog "
                "mix_weight 1.0, so that field alone does not rank authoring quality or repair cost."
            ),
            "quality_dimensions": {
                "representation": "The sample exposes canonical-profile undercoverage, unreliable declared controls, and bounded morphology support.",
                "teachability": "Retained evidence ranges from no executable semantic contract to registered-rival rejection; approval alone is not uniform teaching evidence.",
                "parameter_and_four_query_supervision": "None of the three sampled task directories contains a parametric evidence manifest.",
                "cost": "Expected review/Racket/dedup cost varies sharply; exact corpus-wide minutes are not measured in this bounded audit.",
            },
        },
        "alternative_allocation_estimate": {
            "scope": "authoring assignments only; no change to approval, training admission, or catalog mix_weight",
            "shares": {
                "approved_originals_missing_parameters": 0.55,
                "repair_or_contract_debt_then_parameters": 0.20,
                "existing_prototypes_or_accepted_repairs_missing_four_query_evidence": 0.15,
                "public_evaluation_focus": 0.10,
            },
            "baseline_comparison": (
                "Current policy reserves 10% evaluation focus and otherwise draws from one 162-item approved-original tier. "
                "The pilot keeps the 10% focus but uses 35 percentage points of the remaining allocation for measured debt "
                "repair and evidence completion before adding more undifferentiated source volume."
            ),
            "estimate_label": "Heuristic proposal from a three-record source-bound sample; not a measured optimum.",
        },
        "bounded_test": {
            "design": "40 assignments: 20 current-policy and 20 stratified-pilot, with equal reviewer-minute and protected-Racket-call caps.",
            "minimum_before_early_stop": "12 completed or terminal assignments per arm",
            "metrics": [
                "routine-complete return rate",
                "accepted parameter-setting count",
                "four-query episodes with four distinct visible inputs and Racket-verified labels",
                "unresolved rival or lesson ambiguity rate",
                "reviewer minutes per accepted evidence package",
                "protected Racket calls per accepted evidence package",
                "deduplicated unique visible inputs",
                "source-contract blockers",
            ],
            "stopping_rule": [
                "Immediately stop any arm for hidden query-answer leakage or an admission-boundary violation.",
                "After at least 12 per arm, stop the pilot as inferior when completion is more than 15 percentage points lower and it has no 20% gain in accepted settings/four-query episodes per 100 Racket calls.",
                "Also stop the pilot when cost per accepted evidence package exceeds 1.5 times current policy without a compensating quality gain.",
                "Prefer the pilot only with at least a 15-point completion/quality gain or a 20% quality-per-cost gain and no safety/admission regression; otherwise finish all 20 per arm and retain the incumbent.",
            ],
        },
        "limitations": [
            "Only three of 300 packet tasks were inspected; one is in the normal authoring pool.",
            "No sampled catalog source explicitly names ARC-GEN or RE-ARC, so this ticket makes no source-specific claim about them.",
            "Retained audit evidence is source-bound and heterogeneous; it is not a fresh corpus-wide rerun.",
            "No model job, corpus-wide Racket battery, draw-policy change, approval, or training admission was performed.",
            "The proposed shares and thresholds are testable estimates, not an optimal-allocation proof.",
        ],
        "command": "python3 review.py run python3 ../checks/tickets/ticket-f6c87e11f9d2c278/allocation_probe.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }

    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "completed", "sampled_ids": sample, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
