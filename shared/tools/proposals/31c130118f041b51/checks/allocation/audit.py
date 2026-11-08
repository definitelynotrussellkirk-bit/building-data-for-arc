#!/usr/bin/env python3
"""Reproduce a bounded allocation audit without executing sampled generators."""
import argparse
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import sys

SEED = "e00421814a7b8e18266cc1ee1b4f12e0f565cfa4dce7ed5b870534a92524b974"
EXPECTED = ["8a6282b87245", "531e65dffc0a", "9d6ff77830f1"]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def prob(f):
    return {"fraction": str(f), "decimal": float(f)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    root = p.parse_args().work_root.resolve()
    raw = (root / "PACKET-MANIFEST.json").read_bytes()
    m = json.loads(raw)
    files = {"PACKET-MANIFEST.json": {"sha256": sha(raw), "bytes": len(raw)}}
    def read(path, text=False):
        raw = (root / path).read_bytes()
        digest = sha(raw)
        if m["files"].get(path) != digest:
            raise ValueError("Packet source/evidence mismatch: " + path)
        files[path] = {"sha256": digest, "bytes": len(raw), "matches_packet_manifest": True}
        return raw.decode() if text else json.loads(raw)
    ids = random.Random(int(SEED, 16)).sample(sorted(m["generators"]), 3)
    assert ids == EXPECTED
    rows = [json.loads(x) for x in read("repo/catalog/puzzles.jsonl", True).splitlines()]
    catalog = {x["id"]: x for x in rows}
    for name in ("review_full_draw.py", "catalog.py", "datasets.py"):
        read("repo/src/arcpuzzles/" + name, True)
    d, priority = m["main_draw_policy"], m["parametric_priority"]
    focus = d["evaluation_focus"]
    anchors = focus["anchors"]
    empty = sum(not x["main_ids"] for x in anchors)
    focus_p = Fraction(focus["probability"]["numerator"], focus["probability"]["denominator"])
    normal_mass = 1 - focus_p + focus_p * Fraction(empty, len(anchors))
    approved = [tid for tid, row in m["generators"].items() if row["approved"]]
    approved_weight = sum(catalog[tid]["mix_weight"] for tid in approved)
    tasks = {}
    for tid in ids:
        home = "repo/generators/" + tid + "/"
        source = read(home + "generator.py", True)
        read(home + "SUMMARY.md", True)
        index = read(home + "evidence/review_index.json")
        digest = sha(source.encode())
        assert digest == m["generators"][tid]["generator_sha256"]
        assert tid not in m["main_ids"]
        literals = {}
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            literals[target.id] = ast.literal_eval(node.value)
                        except (ValueError, TypeError):
                            pass
        tasks[tid] = {
            "generator_sha256": digest,
            "rule_hash": m["generators"][tid]["rule_hash"],
            "source_path": home + "generator.py",
            "version": literals.get("VERSION"),
            "sources": catalog[tid]["sources"],
            "train_safety": catalog[tid]["train_safety"],
            "approved": tid in approved,
            "mix_weight": catalog[tid]["mix_weight"],
            "main_target_probability": prob(Fraction(0)),
            "priority_tiers": [k for k,v in priority["tiers"].items() if tid in v],
            "related_original_metadata": priority["related_generators"].get(tid),
            "pinned_packet_default_dataset_attempt_probability": prob(Fraction(1, int(approved_weight))) if tid in approved else prob(Fraction(0)),
            "audits": [{"source_sha256": a["source_sha256"],
                        "matches_current_source": a["source_sha256"] == digest,
                        "resolution": a.get("resolution"),
                        "verification_status": a.get("verification_status"),
                        "return_id": a.get("return_id")} for a in index.get("audits", [])],
            "parametric_directory_present": (root / home / "workspace/parametric").is_dir(),
            "four_query_episode_verified": False,
            "current_linter_verdict": "unknown; no current-source executed linter receipt inspected",
            "executed_grammar_coverage": "unknown",
            "declared_axes": literals.get("AXES", {})
        }
        if tid == "8a6282b87245":
            assert source.count("if cols_range & used_cols: continue") == 2
            base = home + "counterexamples/review-8e2f7f4db37de5d2-v0002/retained/checks/audit/"
            repro = read(base + tid + "/reproduction.json")
            inputs = read(base + tid + "/generated_inputs.json")
            audit = read(base + tid + "-combined/checks/" + tid + "_audit_summary.json")
            battery = read(base + tid + "-combined/checks/" + tid + "_audit_battery_summary.json")
            result = read(base + tid + "-combined/result.json")
            assert repro["generator_sha256"] == digest
            assert isinstance(inputs, list) and len(inputs) == 60
            witness = repro["counterexample"]
            actual, rival = witness["selected_output"], witness["rival_output"]
            assert len(actual) == len(rival) and all(len(a) == len(b) for a,b in zip(actual,rival))
            differences = sum(a != b for ra, rb in zip(actual, rival) for a,b in zip(ra,rb))
            assert differences == witness["differing_cell_count"] == 16
            tasks[tid].update({
                "finding": "Current-source default placement eliminates shared-column collisions, leaving independent edge snapping sufficient on retained samples.",
                "evidence_status": "Retained Racket-labelled reproduction re-read and source-bound; no fresh Racket/generation run.",
                "retained_probe": {k:v for k,v in repro["generated_probe"].items() if k != "per_sample"},
                "fresh_consistency_checks": {"retained_inputs": len(inputs),
                    "unique_retained_inputs": len({sha(json.dumps(x,sort_keys=True,separators=(",",":")).encode()) for x in inputs}),
                    "witness_differing_cells": differences},
                "retained_audit": audit,
                "retained_lint_status": battery["stages"]["lint"]["status"],
                "retained_grammar_status": battery["stages"]["grammar"]["status"],
                "cost_evidence": {"labelled_generated_inputs": 60, "labelled_separating_witness": 1,
                    "semantic_stage_seconds": result["audit_stages"]["semantic_gate"]["battery_stage"]["duration_seconds"],
                    "review_minutes": None, "racket_total_seconds": None},
                "limits": ["No task tests and missing semantic contract are retained failures.",
                    "Missing rule-parameter prototype; four-query production unverified.",
                    "Known witness lowers diagnosis cost but does not measure repair cost."]
            })
        elif tid == "531e65dffc0a":
            read(home + "notes.md", True)
            read(home + "workspace/README.md", True)
            old = read(home + "workspace/distribution_before_after.json")
            assert old["after"]["source_version"] == "2.0.0"
            assert literals["VERSION"] == "2.1.0"
            tasks[tid].update({
                "finding": "Current accepted source has explicit finite-rival teaching support but a narrow one-prototype scene grammar.",
                "evidence_status": "Current code inspected; quantitative final checks are retained reviewer reports in notes, not newly rerun.",
                "static_observations": {"geometry_rivals": 6, "single_code_mapping_rivals": 12,
                    "rival_registry_entries": 18, "duplicate_rival": "yellow_identity = code_4_as_2",
                    "default_mixture": {"teaching":0.5,"ordinary_profile":0.375,"broad":0.125},
                    "teaching_attempt_cap":256,"prototype_cells":[2,6],"broad_dimensions":[8,18],
                    "exact_overrides_bypass_teaching_schedule":True,
                    "multiple_prototype_domain_sampled":False,
                    "input_axes_are_not_verified_rule_parameter_variants":True},
                "retained_reviewer_reported": {"task_tests_passed":104,"override_draws":53910,
                    "production_lessons_per_band":100,"production_unique_inputs":1200,
                    "independent_candidate_grids":576,"independent_unique_grids":241,
                    "independent_query_checks":2196,
                    "intermediate_medium_linear_ambiguity":[37,183],
                    "intermediate_medium_cyclic_ambiguity":[159,732],
                    "intermediate_source_sha256":"3d5acb565e4eb85a561c32a3a507d0a7f6f09e690eebc22fceef1951d7d2837d"},
                "excluded_stale_evidence": {"path":home+"workspace/distribution_before_after.json",
                    "reported_after_version":"2.0.0","selected_version":"2.1.0",
                    "reason":"Its 96/96 lesson and 384/384 rotation claims do not bind to current bytes."},
                "limits": ["The old override audit is needs_triage but bound to superseded source.",
                    "Single-query rotations do not establish a four-query export.",
                    "Source-specific workload counts are not elapsed-time measurements.",
                    "Finite rivals and small polyominoes do not establish arbitrary scene/rule coverage."]
            })
        else:
            assert literals["AXES"]["k_holes"]["valid"] == "1|2|3"
            assert "rng.randint(1, 3)" in source
            assert '"no color-1 marker cells in row 0"' in source
            tasks[tid].update({
                "finding":"Default support excludes k=0 and validator rejects no-marker inputs, matching the current-source canonical-branch audit.",
                "evidence_status":"Source restrictions confirmed statically; canonical/Racket claim remains retained reviewer-reported.",
                "static_observations":{"default_k":[1,2,3],"advertised_k":[1,2,3],
                    "no_marker_rejected":True,"raw_override_zero_is_reachable_but_not_validated":True,
                    "rule_hash_constant_present":"RULE_HASH" in literals,
                    "shape_grammar":"Height-5 rectangles with nonadjacent single-cell interior holes",
                    "width_by_hole_count":{"0":5,"1":5,"2":7,"3":9},
                    "layout_attempt_cap":40,"placement_attempt_cap":40,
                    "fallback":"Returns last grid after layout exhaustion; failure frequency unmeasured",
                    "executable_semantic_contract":False},
                "limits":["Default volume cannot supply the omitted branch.",
                    "Width and single-cell-hole confounding is a static coverage concern, not a measured canonical-fitting shortcut.",
                    "Repair time, rejection rate, linter/grammar pass, four-query support, and rule variants remain unknown."]
            })
    assumptions = {
        "approved_original_parameters":{"alternative_share":0.7,"pass_probability":0.65,"review_minutes":60,"racket_minutes":10},
        "original_known_repairs":{"alternative_share":0.2,"pass_probability":0.60,"review_minutes":45,"racket_minutes":8},
        "other_evidence_ranked_repairs":{"alternative_share":0.1,"pass_probability":0.50,"review_minutes":30,"racket_minutes":5}}
    alternative_success = sum(x["alternative_share"]*x["pass_probability"] for x in assumptions.values())
    alternative_review = sum(x["alternative_share"]*x["review_minutes"] for x in assumptions.values())
    alternative_racket = sum(x["alternative_share"]*x["racket_minutes"] for x in assumptions.values())
    report = {
        "schema":"arcpuzzles-randomized-allocation-audit-v1",
        "status":"complete_bounded_static_and_retained_evidence_audit",
        "audit_seed":SEED,
        "sampling":{"algorithm":"random.Random(int(seed,16)).sample(sorted(manifest['generators']),3)",
                    "population":len(m["generators"]),"sampled_ids_in_order":ids},
        "source_access":"after parent confirmed blind solve finished",
        "policy_approval_admission_changed":False,
        "new_generator_runs":0,"new_racket_runs":0,"new_model_jobs":0,
        "authoring_allocation":{"all_ids":len(m["all_ids"]),"main_ids":len(m["main_ids"]),
            "normal_ids":len(d["normal_ids"]),"selected_tier":priority["selected_tier"],
            "tier_counts":{k:len(v) for k,v in priority["tiers"].items()},
            "current_prototypes":priority["counts"]["current_prototypes"],
            "provided_tasks":priority["provided_tasks"],"covered_original_tasks":priority["covered_original_tasks"],
            "unmapped_original_tasks":len(priority["unmapped_original_tasks"]),
            "focus_probability":prob(focus_p),"focus_anchors":len(anchors),"unmapped_focus_anchors":empty,
            "mapped_focus_anchors":[a for a in anchors if a["main_ids"]],
            "nominal_normal_target_mass":prob(normal_mass),
            "nominal_per_normal_target_probability":prob(normal_mass/len(d["normal_ids"])),
            "nominal_each_direct_related_target_probability":prob(Fraction(1,2400)),
            "interpretation":"Ten-percent focus is not a ten-percent direct evaluation-target quota; unmapped anchors keep a normal target for an inspired extension.",
            "probability_scope":"Nominal probabilities of configured uniform/modulo hashed draws; no assignment census run."},
        "dataset_weights":{"catalog_weight_counts":dict(Counter(str(x["mix_weight"]) for x in rows)),
            "pinned_manifest_approved_count":len(approved),"pinned_approved_weight_sum":approved_weight,
            "approval_gate":"reviewed_safe, no semantic veto, positive finite weight, source matching reviewed hash, and current canonical rule matching reviewed hash",
            "consumer":"datasets.py applies approval/other filters, then rng.choices with mix_weight; uniform mode uses equal weights",
            "accepted_distribution":"Generation/policy failures and episode-content deduplication alter accepted frequency.",
            "scope":"Pinned complete original packet eligibility; no dataset export or training admission measured."},
        "sampled_tasks":tasks,
        "alternative":{"status":"proposal_not_implemented",
            "normal_authoring_mix":{"approved_original_parameters":0.7,"original_known_repairs":0.2,"other_evidence_ranked_repairs":0.1},
            "evaluation_focus":"Preserve independent 10% authoring focus",
            "within_bucket":"Uniform over current-source actionable candidates, rotating reasoning categories; exclude superseded or unreproduced leads.",
            "quality_unit":"Source-bound family improvement covering a missing reasoning distinction or meaningful rule setting, with canonical/domain checks, Racket labels, finite-rival query identifiability and distinct four-query support.",
            "illustrative_not_sample_fitted_assumptions":assumptions,
            "illustrative_comparison":{"current_qualified_upgrades_per_review_hour":0.65,
                "alternative_expected_upgrades":alternative_success,
                "alternative_review_minutes":alternative_review,
                "alternative_racket_minutes":alternative_racket,
                "alternative_qualified_upgrades_per_review_hour":alternative_success*60/alternative_review,
                "relative_efficiency_change":(alternative_success*60/alternative_review)/0.65-1},
            "sensitivity":"If all buckets cost 60 reviewer minutes, proposal yields 0.625 vs 0.65 upgrades/hour (3.85% worse). With listed costs and other-repair success 0.50, original-repair success must exceed 0.40 to improve yield. Do not adopt on these assumptions alone."},
        "bounded_test":{"status":"not_run",
            "design":"20 future scheduled reviews: 10 current-policy and 10 alternative (7/2/1), assigned before inspection; retain immutable draws, focus and source hashes.",
            "per_target_caps":{"reviewer_minutes":90,"racket_machine_minutes":15},
            "total_caps":{"assignments":20,"reviewer_hours":30,"racket_machine_hours":5},
            "validation":"12 unique default lessons per band with four distinct Racket-labelled queries each; record demos and per-query rival checks. For meaningful rule prototypes cover two settings within the same budget. Check schedule residues/rotations only when claimed. Incomplete evidence is not a pass.",
            "metrics":["qualified_upgrades/reviewer_hour","new_reasoning_or_parameter_settings",
                "Racket_seconds/qualified_upgrade","unique_inputs_and_episodes_before_after_dedup",
                "canonical_rejections","declared_rival_query_ambiguity","four_query_failures","source_and_reasoning_coverage"],
            "stop":"Stop at individual or total caps. Pause an arm after two newly introduced canonical-domain regressions or two omitted known-branch counterexamples; retain every failure.",
            "decision":"Recommend limited follow-up only with at least 10% higher qualified-upgrade yield per reviewer hour, no higher Racket cost per upgrade and equal quality checks. Otherwise retain policy or report inconclusive; no population-significance or model-improvement claim."},
        "coverage_limits":["Only three sampled IDs; no corpus defect-rate or optimal-policy estimate.",
            "No ARC-GEN or RE-ARC lineage identified in sampled metadata; no claim about those sources.",
            "Public/internal provenance alone did not imply teachability.",
            "No executed current linter or grammar census in selectively inspected evidence; pending/absent is not passing.",
            "No fresh four-query or rule-parameter runs for sampled sources.",
            "No current model accuracy, human-difficulty calibration, training admission or policy change claimed."],
        "source_evidence":[dict(path=k,**v) for k,v in sorted(files.items())],
        "reproduction":{"cwd":".","argv":["../.venv-review/bin/python","checks/allocation/audit.py","--work-root","."],
            "python":sys.executable}
    }
    output = root / "checks/allocation/audit.json"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"completed","sampled_ids":ids,"source_evidence_files":len(files),
        "unique_retained_8a_inputs":tasks[ids[0]]["fresh_consistency_checks"]["unique_retained_inputs"],
        "new_generator_runs":0,"new_racket_runs":0,"audit_sha256":sha(output.read_bytes())},sort_keys=True))

if __name__ == "__main__":
    main()
