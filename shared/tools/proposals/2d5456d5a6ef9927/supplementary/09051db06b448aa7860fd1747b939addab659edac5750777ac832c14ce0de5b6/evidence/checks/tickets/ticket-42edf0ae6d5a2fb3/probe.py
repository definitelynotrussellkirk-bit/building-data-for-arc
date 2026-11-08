#!/usr/bin/env python3
"""One bounded, source-pinned allocation probe; no production changes or Racket jobs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import random
import sys
import time

W = Path(__file__).resolve().parents[3]
R = W / "repo"
SEED = "0a996209ce0e4950f46bd0d1c9c2e20dfae278e7ee36a953b16875aefa3aabdb"
TICKET = "ticket-42edf0ae6d5a2fb3"
PINNED = "88b8e6aaa49d"
EXPECTED = "ff975d4d5cce91725c18577964ebebef03a1b543ed6a9f4bcb68f9a11c4dc802"
RULE = "d4b6baaa86e7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    manifest = json.loads((W / "PACKET-MANIFEST.json").read_text())
    catalog = {row["id"]: row for row in map(json.loads, (R / "catalog/puzzles.jsonl").read_text().splitlines())}
    rng = random.Random(int(SEED, 16))
    ids = [PINNED] + rng.sample(sorted(set(manifest["main_ids"]) - {PINNED}), 2)
    policy = manifest["main_draw_policy"]
    focus = policy["evaluation_focus"]
    mapped = [anchor for anchor in focus["anchors"] if anchor["main_ids"]]
    sys.path[:0] = [str(R / "src"), str(R / "shared/runtime")]
    records = []
    for tid in ids:
        row = catalog[tid]
        source = R / row["generator"]
        actual_sha = sha(source)
        spec = importlib.util.spec_from_file_location("allocation_" + tid, source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        current_rule = getattr(module, "RULE_HASH", None)
        identities_match = (actual_sha == row.get("reviewed_generator_sha256")
                            == manifest["generators"][tid]["generator_sha256"]
                            and current_rule == row.get("reviewed_rule_hash")
                            == manifest["generators"][tid]["rule_hash"])
        if tid == PINNED and (actual_sha != EXPECTED or current_rule != RULE):
            raise ValueError("Pinned source/rule identity mismatch")
        receipt_path = R / row["approval_receipt"] if row.get("approval_receipt") else None
        receipt = json.loads(receipt_path.read_text()) if receipt_path and receipt_path.exists() else None
        evidence = []
        for name in ["notes.md", "evidence/review_index.json", "evidence/associated_notes.jsonl"]:
            path = source.parent / name
            if path.exists():
                evidence.append({"path": str(path.relative_to(W)), "sha256": sha(path)})
        if receipt_path and receipt_path.exists():
            evidence.append({"path": str(receipt_path.relative_to(W)), "sha256": sha(receipt_path)})
        n_demo = getattr(module, "EXAMPLES_NEEDED", None)
        used_demos = n_demo if isinstance(n_demo, int) else 3
        start_index = rng.randrange(1000000)
        t0 = time.perf_counter()
        grids = [module.generate(int(SEED, 16), start_index + i, difficulty=None)
                 for i in range(used_demos + 4)]
        generation_seconds = time.perf_counter() - t0
        errors = [module.self_check(grid) if hasattr(module, "self_check") else None for grid in grids]
        query_grids = grids[used_demos:]
        t0 = time.perf_counter()
        query_hashes = [hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                        for grid in query_grids]
        hash_seconds = time.perf_counter() - t0
        mirror = getattr(module, "rule_mirror", None)
        mirror_outputs = [mirror(grid) for grid in query_grids] if callable(mirror) else None
        observe = getattr(module, "observe_overrides", None)
        record = {
            "task_id": tid, "source_path": str(source.relative_to(W)), "generator_sha256": actual_sha,
            "rule_hash": current_rule, "catalog_and_manifest_identity_match": identities_match,
            "mix_weight": row.get("mix_weight"), "train_safety": row.get("train_safety"),
            "review_status": row.get("review_status"), "sources": row.get("sources"),
            "selection_reasons": manifest["selection"]["reasons"].get(tid),
            "parametric_record": manifest["parametric_priority"]["related_generators"].get(tid),
            "approval_receipt": receipt, "evidence": evidence,
            "axes": getattr(module, "AXES", None), "declared_demo_count": n_demo,
            "declared_lesson_hook": callable(getattr(module, "lesson_identifiable", None)),
            "probe": {
                "generation_seed_integer": int(SEED, 16), "start_index": start_index,
                "difficulty": None, "overrides": {}, "used_demo_count": used_demos,
                "demo_count_fallback": n_demo is None, "query_count": 4,
                "input_dimensions": [[len(g), len(g[0])] for g in grids],
                "query_input_sha256": query_hashes, "distinct_query_inputs": len(set(query_hashes)),
                "self_check_errors": errors,
                "observed_query_axes": [observe(g) for g in query_grids] if callable(observe) else None,
                "mirror_output_dimensions": [[len(g), len(g[0])] for g in mirror_outputs] if mirror_outputs else None,
                "mirror_is_not_production_racket_validation": True,
                "production_four_query_episode_validation": "not_run",
                "generation_seconds": generation_seconds, "local_query_hashing_seconds": hash_seconds,
                "racket_seconds": None, "review_minutes": None, "global_dedup_seconds": None,
            },
        }
        records.append(record)
    result = {
        "schema": "allocation-quality-ticket-v1", "ticket_id": TICKET, "status": "completed",
        "seed": SEED, "observed_utc": datetime.now(timezone.utc).isoformat(),
        "sampling": {"method": "Pinned task plus Random(int(ticket_seed,16)).sample(sorted(main_ids minus pinned),2)",
                     "ids": ids, "scope": "Three source records, not a representative library census"},
        "source_files": [{"path": str(p.relative_to(W)), "sha256": sha(p)}
                         for p in [W/"PACKET-MANIFEST.json", W/"TRAINING-CONTEXT.md",
                                   R/"catalog/puzzles.jsonl", R/"src/arcpuzzles/review_full_draw.py"]],
        "allocation": {
            "packet_records": len(manifest["all_ids"]), "main_candidates": len(manifest["main_ids"]),
            "normal_candidates": len(policy["normal_ids"]), "owner_generator_count_context": manifest["selection"]["owner_generator_count"],
            "selection_policy": manifest["selection"]["policy"], "selection_quotas": manifest["selection"]["quotas"],
            "focus_probability": focus["probability"], "evaluation_anchors": len(focus["anchors"]),
            "mapped_evaluation_anchors": len(mapped), "related_generators": focus["eligible_related_generators"],
            "focus_fallback": focus["fallback"],
            "idealized_direct_related_draw_probability": 0.1 * len(mapped) / len(focus["anchors"]),
            "interpretation": "10% is authoring focus, not 10% direct related-generator draws; unmatched focus anchors fall back to the normal pool. Catalog mix_weight and frozen training token shares are separate quantities.",
        },
        "records": records,
        "interpretation": {
            "training_context": "October 23 r6/r6-h3 report: export default sampler, four queries, 7.3% output-side>=20 versus 47% public evaluation; older r4 mastery is not evidence of current-source quality.",
            "source_specific": {
                PINNED: "Current hashes match. Accepted October 11 repair is reviewer-reported; receipt retains shared semantic-gate alias failure. Notes report 41 tests, 300 lessons/1200 query rotations, not a newly executed four-query production check. Current API grid_h/grid_w<=8 cannot supply 20-side outputs; this is a scope limit, not poor labels.",
                "b8e2a07c1b6c": "Current hashes match July 24 accepted-source note. Six observable axes and eight directions are documented; imported notes report final lint/override repairs and 726 explicit incompatible-combination rejections. No current declaration of required demos or lesson-identifiability hook; four generated inputs do not establish teachability. Source bounds 12..18 exclude 20-side outputs. Older date alone does not make unchanged bytes stale.",
                "86af5978a32a": "Current hashes match October 12 reviewer-reported accepted repair. Four demos and finite rivals address orientation/order/color-8 shortcuts. Source half_size=3..5 permits 25x25 outputs at 5, but default schedule uses 3/4. Notes report 174 tests, 12/12 battery stages and 300 lessons/1500 rotations; this probe does not rerun Racket or validate a four-query half_size=5 production episode.",
            },
            "quality_and_cost": "All three catalog mix weights are 1.0 despite different size support, demo contracts and evidence gaps. The probe measures only input generation and local query hashing. Racket, human-review and global-dedup costs are unknown, so quality per total cost cannot be numerically ranked. Lack of receipts is not a quality defect; high loss and provenance alone are not defect evidence.",
            "external_source_gap": "No source-specific ARC-GEN or RE-ARC lint/rejection/grammar receipts are shipped for these three ARCpuzzles records. Their reported 16%/11% token shares are context only; no quality ranking or source census was attempted. No NVARC data was opened.",
        },
        "alternative_allocation": {
            "proposal_only": True, "changes_applied": False,
            "owner_review_slots_percent": {"ordinary_current_priority": 60, "existing_size_capability_missing_four_query_receipt": 30, "existing_evaluation_authoring_focus": 10},
            "candidate": "86af5978a32a at its exact current generator/rule hashes, candidate override half_size=5; keep half_size=3/4 controls. This is an experiment candidate, not newly validated production guidance.",
            "estimated_benefit": "Shift some authoring effort from already small-only families to validating existing meaningful large-output support. Expected increase in validated distinct large queries per owner/Racket minute is a hypothesis; magnitude and net quality benefit are unknown.",
            "bounded_experiment": "Owner may run six source-pinned episodes on 86af5978a32a: three ticket-derived seeds, each paired default versus half_size=5, four independently counted demos and four queries. Use the canonical Racket oracle, existing finite-rival hook and standard dedup. Record wall/CPU Racket time, review minutes, all rejection reasons, distinct accepted query count, and actual output sizes. This proposal performs no runs or admission.",
            "stop_rule": "Cap each episode at 120 seconds and total authoring at 30 minutes; stop on first label mismatch, malformed override or source/rule drift. Finish after six episodes; do not change mixture or admit anything if either arm lacks four distinct valid queries, preserves a declared rival, or costs are missing. Compare validated large-query yield per measured total cost; an inconclusive result keeps current allocation.",
        },
        "execution": {"command": [sys.executable, "-B", str(Path(__file__).resolve())],
                      "cwd": os.getcwd(), "mount_namespace": os.readlink("/proc/self/ns/mnt"),
                      "targeted_probes": 1, "timeout_seconds": 120,
                      "elapsed_seconds": time.perf_counter() - started,
                      "elapsed_authoring_minutes": None, "exit_code": 0,
                      "scope": "Input smoke and source/evidence metadata only; no Racket/battery/model/census"},
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
