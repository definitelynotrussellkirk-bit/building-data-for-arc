"""One bounded read-only allocation evidence probe; no generator imports or execution.

Run once from the supplied WORK runtime: python3 .../probe.py --out evidence.json
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

TICKET = "ticket-9f79d62ef9a17c0e"
SEED = "ff748a80bc7048a637b9e94a4d62789d531b7fceb7c3d37aee00a98b43ebf0a5"
TARGET = "195dfcc5b541"
PIN = "af8350048eca44100de1d539ba7bb3f295bb82cbf99411f7eef218c4c1e56ed7"
EXPECTED = [TARGET, "2b34f380ed25", "079232b060cd"]

OBSERVATIONS = {
 TARGET: {
  "representation": "Original training:50f325b5; dense stencil/copy matching under rotations and reflections. Current grammar intentionally covers two chiral stencil families and 2..4 isolated copies, not arbitrary shapes or overlap-order cases.",
  "teachability": "Current notes declare three demonstrations and rotations_only as a canonical-fitting rival; every generated pair contains a reflection-only witness. Notes report 300/300 lessons and 1200 query rotations without declared-rival ambiguity, not fresh results of this probe.",
  "repair_and_rejections": "Prior source had inert/conflicting axes, top-edge-only placement, canonical admission and no-copy gaps. Current notes retain partial baseline, initial 10/12 repaired battery due active-text authority divergence, and an override run exceeding its foreground window before constructive sampling removed that cost. Historical index audits bind a different source; do not count them as freshly reproduced current defects.",
  "coverage_gap": "Packet prototype status is missing; retained lesson policy is 3 demos/1 query. No current four-query parametric receipt found in the inspected task files.",
 },
 "2b34f380ed25": {
  "representation": "Original training:4e7e0eb9; macro-band panel decoding, balanced positional half exchange, unbalanced-mark preservation and contextual fill. Bounded layouts and palette roles; not arbitrary intersecting marks.",
  "teachability": "Current five-demo curriculum retains ordered-halves and unbalanced-guard refuters. Notes report 300 lessons/1800 clean query rotations. Earlier three-demo reflection ambiguity and only 1/3200 forced-profile guard refutations motivated repairs.",
  "repair_and_rejections": "A 17-value profile repair triggered finite-enum lint; final repair consolidated into 16 existing profiles. Prior portability, padding, readiness and packaging failures remain evidence, not erased by later results. Owner corrected setting-order public filenames and reports 13 focused tests.",
  "coverage_gap": "Packet classifies the prototype stale/unqualified_evidence despite retained owner-current half_swap/reflection evidence. Inspect actual saved episode counts below: these are not evidence of four distinct queries. Prioritize qualification and count extension over pretending a prototype is absent or approved.",
 },
 "079232b060cd": {
  "representation": "Bank-origin beam/wall family, not identified as ARC-GEN or RE-ARC. Colored border beams, pass-through, corners and collision precedence add a different reasoning structure to the two original-task families.",
  "teachability": "Same-source retained audit shows advertised crossing texture can have its vertical beam blocked before the nominal crossing. Racket agrees with mirror; this is missing promised teaching support, not wrong labels. Current source declares four examples but no SEMANTIC_RIVALS/LESSON_COMPETITORS registry.",
  "repair_and_rejections": "Unresolved source-bound crossing guarantee and reported difficulty-dependent override rejections. June derived lint pass is not sufficient against the later exact-source witness.",
  "coverage_gap": "Not approved in packet; catalog safety unverified. No task-local parametric prototype or four-query receipt found. Repair and teaching qualification should precede increased sampling.",
 },
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    from reviewer_support import find_root
    root = find_root(__file__).resolve()
    work = root.parent
    bindings = {}
    def read(path):
        path = Path(path)
        data = path.read_bytes()
        bindings[str(path.relative_to(work))] = {"sha256": sha(data), "bytes": len(data)}
        return data
    manifest = json.loads(read(work / "PACKET-MANIFEST.json"))
    generators = manifest["generators"]
    def rank(tid):
        return sha(bytes.fromhex(SEED) + b":" + tid.encode())
    selected = [TARGET] + sorted((tid for tid in generators if tid != TARGET), key=rank)[:2]
    if selected != EXPECTED:
        raise ValueError(f"Packet sampling changed: expected {EXPECTED}, got {selected}")
    catalog = {r["id"]: r for line in read(root / "catalog/puzzles.jsonl").decode().splitlines()
               if line.strip() and (r := json.loads(line))}
    derived = {r["task_id"]: r for line in read(root / "shared/data/derived/generator_catalog.jsonl").decode().splitlines()
               if line.strip() and (r := json.loads(line))}
    authorities = {}
    for line in read(root / "shared/data/canonical/puzzles.jsonl").decode().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") in selected and row.get("program_solution"):
            source = row["program_solution"]
            authorities.setdefault(row["task_id"], []).append({
                "raw_rule_sha256": sha(source.encode()),
                "normalized_rule_hash": sha(" ".join(source.split()).encode())[:12],
                "n_train": len(row.get("train", [])), "n_test": len(row.get("test", [])),
            })
    for tid in selected:
        if not authorities.get(tid) or any(r["normalized_rule_hash"] != generators[tid]["rule_hash"] for r in authorities[tid]):
            raise ValueError(f"Canonical rule no longer matches packet: {tid}")
    if generators[TARGET]["rule_hash"] != "22e420574f26":
        raise ValueError("Pinned target rule hash mismatch")
    # Inspect actual policy implementation, not only narrative instructions.
    implementation = {}
    for relative, words in [("src/arcpuzzles/review_full_draw.py", ("normal_ids", "int.from_bytes", "probability")),
                            ("src/arcpuzzles/catalog.py", ("mix_weight", "reviewed_safe", "generator_changed_since_review"))]:
        lines = read(root / relative).decode().splitlines()
        implementation[relative] = [{"line": i + 1, "text": line.strip()} for i, line in enumerate(lines)
                                    if any(word in line for word in words)]
    records = []
    for tid in selected:
        base = root / "generators" / tid
        source = read(base / "generator.py")
        source_sha = sha(source)
        if source_sha != generators[tid]["generator_sha256"]:
            raise ValueError(f"Source no longer matches packet: {tid}")
        if tid == TARGET and source_sha != PIN:
            raise ValueError("Pinned target hash mismatch")
        tree = ast.parse(source.decode())
        constants = {}
        names = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                        if target.id in {"VERSION", "RULE_HASH", "EXAMPLES_NEEDED", "INVARIANTS", "HELPFUL_TEXTURES", "DEGENERATE_TEXTURES"}:
                            try:
                                constants[target.id] = ast.literal_eval(node.value)
                            except (ValueError, TypeError):
                                pass
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
        note_path = base / "notes.md"
        notes = read(note_path).decode()
        note_terms = ("rival", "lint", "failed", "failure", "reject", "query", "census", "limitation", "stale")
        excerpts = [{"line": i + 1, "text": line.strip()} for i, line in enumerate(notes.splitlines())
                    if any(word in line.lower() for word in note_terms)][:35]
        index_path = base / "evidence/review_index.json"
        index = json.loads(read(index_path)) if index_path.is_file() else {}
        audits = [{k: row.get(k) for k in ("return_id", "source_sha256", "resolution", "verification_status", "assets_manifest")}
                  | {"matches_current_source": row.get("source_sha256") == source_sha}
                  for row in index.get("audits", [])]
        row = catalog[tid]
        if row.get("approval_receipt"):
            receipt_path = root / row["approval_receipt"]
            if receipt_path.is_file():
                read(receipt_path)
        record = {
            "task_id": tid, "rank_digest": rank(tid), "source_sha256": source_sha,
            "packet_record": generators[tid],
            "canonical_authorities": authorities[tid],
            "catalog": {k: row.get(k) for k in ("version", "mix_weight", "train_safety", "sources", "aliases", "review_status", "reviewed_generator_sha256", "reviewed_rule_hash", "approval_verification_status")},
            "lineage_and_prototype": manifest["parametric_priority"]["related_generators"].get(tid),
            "in_normal_authoring_pool": tid in manifest["main_draw_policy"]["normal_ids"],
            "static_declarations": constants,
            "semantic_hooks_present": sorted(names & {"lesson_identifiable", "SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"}),
            "prototype_source_present": (base / "workspace/parametric/prototype.py").is_file(),
            "historical_derived_catalog": derived.get(tid),
            "historical_derived_version_matches_current": derived.get(tid, {}).get("version") == constants.get("VERSION"),
            "retained_audit_bindings": audits, "notes_excerpts": excerpts,
            "assessment": OBSERVATIONS[tid],
        }
        if tid == "2b34f380ed25":
            evidence = base / "workspace/parametric/evidence"
            proto_bytes = read(base / "workspace/parametric/prototype.py")
            current = json.loads(read(evidence / "owner-current/manifest.json"))
            read(evidence / "manifest.json")
            receipt = json.loads(read(evidence / "owner-correction/receipt.json"))
            episodes = []
            for er in current["episodes"]:
                path = evidence / "owner-current" / er["private_path"]
                ep = json.loads(read(path))
                episodes.append({"path": str(path.relative_to(work)), "n_train": len(ep["train"]), "n_test": len(ep["test"]),
                                 "parameters": ep["parameters"], "rivals": er.get("rivals"),
                                 "distinct_inputs": len({json.dumps(p["input"], separators=(",", ":")) for p in ep["train"] + ep["test"]})})
            record["retained_parametric"] = {"status": current["status"], "episodes": episodes,
                 "prototype_sha256": sha(proto_bytes), "recorded_source_matches": current["source_sha256"].get(f"generators/{tid}/workspace/parametric/prototype.py") == sha(proto_bytes),
                 "owner_correction_receipt": receipt, "fresh_racket_verification": "not_run"}
        if tid == "079232b060cd":
            path = base / "counterexamples/review-f4ee04c336989569-v0001/retained/checks/audit/079232b060cd/report.json"
            record["retained_crossing_receipt"] = json.loads(read(path))
        records.append(record)
    focus = manifest["main_draw_policy"]["evaluation_focus"]
    priority = manifest["parametric_priority"]
    facts = {
        "packet_generator_count": len(generators), "owner_generator_count": manifest["selection"]["owner_generator_count"],
        "packet_selection_policy": manifest["selection"]["policy"], "packet_quotas": manifest["selection"]["quotas"],
        "normal_authoring_pool_count": len(manifest["main_draw_policy"]["normal_ids"]),
        "normal_draw": "Seed integer modulo normal_ids length, as inspected in review_full_draw.py; catalog mix_weight is not used for this draw.",
        "selected_tier": priority["selected_tier"], "tier_counts": priority["counts"],
        "provided_original_tasks": priority["provided_tasks"], "covered_original_tasks": priority["covered_original_tasks"],
        "evaluation_focus": {k: v for k, v in focus.items() if k != "anchors"},
        "evaluation_anchor_count": len(focus["anchors"]),
        "evaluation_anchor_tiers": dict(Counter(a["selected_tier"] for a in focus["anchors"])),
        "supplementary_weights": manifest["supplementary_ticket_policy"]["weights"],
        "weight_basis": manifest["supplementary_ticket_policy"]["weight_basis"],
        "sample_mix_weights": {r["task_id"]: r["catalog"]["mix_weight"] for r in records},
        "interpretation": "Equal positive dataset mix weights do not equal approval, main-authoring probability, episode quality or training admission. The unreviewed beam source has weight 1.0 but is not approved. Packet selection is purposive, not a representative sample of the owner's full library.",
    }
    proposal = {
        "status": "proposed_only", "consumer": "bounded_owner_allocation_experiment_proposal",
        "decision": "Preserve all production probabilities and catalog weights. Compare a small shadow allocation that includes qualification/teaching repair with new-variant-only authoring.",
        "comparison": {
            "budget_minutes_each": 120,
            "baseline": {"allocation": "Three 40-minute attempts at new prototypes on approved-original missing-parameter families, including the pinned stencil family.",
                         "assumed_completion_probability_per_attempt": 0.4, "estimated_qualified_deliverables": 1.2, "estimated_deliverables_per_hour": 0.6},
            "alternative": {"allocation": "60 minutes for the pinned stencil prototype, 30 minutes to qualify/extend the existing panel prototype to four distinct queries, 30 minutes for the source-bound beam crossing teaching repair.",
                            "assumed_completion_probabilities": {"stencil": 0.5, "panel": 0.8, "beam": 0.6},
                            "estimated_qualified_deliverables": 1.9, "estimated_deliverables_per_hour": 0.95},
            "estimate_warning": "These probabilities are explicit planning assumptions, not observed success rates or a measured optimal allocation. Panel work reuses retained programs; beam work begins with an exact source-bound counterexample. A repaired canonical contract and a parametric receipt are different deliverable types: record their types and report both throughput and four-query episode yield separately.",
        },
        "label_cost_model": [
            {"demos": 3, "queries_before": 1, "queries_after": 4, "labels_before": 4, "labels_after": 7, "label_multiplier": 1.75},
            {"demos": 5, "queries_before": 1, "queries_after": 4, "labels_before": 6, "labels_after": 9, "label_multiplier": 1.5},
            {"retained_panel_demos": 3, "retained_panel_queries": 2, "target_queries": 4, "labels_before": 5, "labels_after": 7, "label_multiplier": 1.4}],
        "cost_limits": "Label counts assume one actual-Racket evaluation per accepted pair; additional rival evaluations, duplicate/rejection draws, bridge startup, and human repair time add cost. No wall-time extrapolation or acceptance-rate estimate is available from this read-only sample.",
        "bounded_future_test": "One owner-approved 120-minute shadow pilot per arm, no production allocation edits. Freeze source IDs/hashes and seeds; retain actual review minutes, accepted/distinct query counts, attempted and rejected draws with reasons, Racket label/rival calls, grammar checks and demonstrations-only ambiguity outcomes. End each attempt at its allotted limit, preserve failures, and do not add tasks to rescue an arm.",
        "stopping_rule": "Stop a source on authority mismatch, unsupported input grammar, unrecoverable duplicate exhaustion, or a query-changing surviving rival. At 120 minutes stop the arm. Retain four-query episodes only with four distinct queries, matching Racket labels and demonstrations-only rival checks. If no such episodes pass, report zero yield; do not recommend production reweighting from this pilot. Require a separate owner review before any probability/catalog change.",
        "recommendation_strength": "Exploratory scheduling proposal; the three-record sample cannot establish a corpus-wide quality ranking or learning benefit.",
    }
    report = {"schema": "bounded-allocation-quality-proposal-v1", "ticket_id": TICKET,
              "outcome": "completed", "ticket_type": "allocation_quality", "finding_classification": "not_applicable",
              "seed": SEED, "sampling_algorithm": "Pinned target plus the first two other PACKET-MANIFEST.generators IDs in ascending SHA256(bytes.fromhex(ticket_seed)+b':'+task_id.encode()).",
              "selected_ids": selected, "pool_size": len(generators), "source_bindings": bindings,
              "draw_and_weight_facts": facts, "policy_implementation_excerpts": implementation,
              "records": records, "proposal": proposal,
              "limits": ["Read-only retained-source/evidence inspection; no generation, Racket, census, model job or benchmark was run.",
                         "No sampled record is identified as ARC-GEN or RE-ARC; no comparative quality claim about those sources is supported.",
                         "June derived lint/catalog summaries can be stale; current source hashes and dated retained receipts are kept separate.",
                         "Current target and panel approvals are reviewer-reported retained decisions, not newly reproduced batteries.",
                         "Four-query learning value and total review/label/dedup costs remain unmeasured."]}
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["command"] = [sys.executable, *sys.argv]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"outcome": report["outcome"], "selected_ids": selected,
                      "elapsed_seconds": report["elapsed_seconds"], "out": str(args.out)}))

if __name__ == "__main__":
    main()
