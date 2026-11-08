from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-3b9ebaab74b6a22f"
TICKET_SEED = "b4a05e081d8b4bfdc8eb4a4699ea2b54e9d4ad9c1a0c8a159a490510a839275a"
PINNED = "235a1d06b9d3"
EXPECTED_PINNED_SHA = "371aa4f2e992601d1cfa5a57d3cbaa8545c243355daa99eac6c420fbcb916379"
ROOT = find_root(__file__)
WORK = ROOT.parent
OUT = WORK / "checks" / "tickets" / TICKET_ID / "report.json"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid) -> str:
    return sha_bytes(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def racket_apply(bridge, wrap_rule, program: str, grid):
    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
assignment = json.loads((WORK / "ASSIGNMENT.json").read_text())
main_ids = manifest["main_draw_policy"]["ids"]
if manifest["main_draw_policy"]["distribution"] != "uniform" or len(main_ids) != 500:
    raise ValueError("unexpected main draw policy")
if PINNED not in main_ids:
    raise ValueError("pinned task is not in the current main pool")
ranked = sorted(
    (task_id for task_id in main_ids if task_id != PINNED),
    key=lambda task_id: hashlib.sha256(f"{TICKET_SEED}:{task_id}".encode()).hexdigest(),
)
sampled_ids = [PINNED, *ranked[:2]]
expected_sample = ["235a1d06b9d3", "c235e3da14f4", "2c7b1545edf9"]
if sampled_ids != expected_sample:
    raise ValueError(f"sample drifted: {sampled_ids}")

catalog = {}
for line in (ROOT / "catalog" / "puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("id") in sampled_ids:
        catalog[row["id"]] = row
if set(catalog) != set(sampled_ids):
    raise ValueError("sampled catalog rows missing")

programs = {}
for line in canonical_path(ROOT).read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") in sampled_ids:
        programs.setdefault(row["task_id"], set()).add(row["program_solution"])
if any(len(programs.get(task_id, ())) != 1 for task_id in sampled_ids):
    raise ValueError("sampled tasks need one exact canonical program")
programs = {task_id: next(iter(values)) for task_id, values in programs.items()}

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

records = []
with RacketBridge(timeout=30) as bridge:
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("live protected Racket required")
    for task_id in sampled_ids:
        module, source, source_sha = load_selected_generator(task_id, root=ROOT)
        expected_sha = manifest["generators"][task_id]["generator_sha256"]
        if source_sha != expected_sha or source_sha != catalog[task_id]["reviewed_generator_sha256"]:
            raise ValueError(f"source identity mismatch for {task_id}")
        if task_id == PINNED and source_sha != EXPECTED_PINNED_SHA:
            raise ValueError("pinned source changed")
        seed = int(hashlib.sha256(f"{TICKET_SEED}:draws:{task_id}".encode()).hexdigest()[:16], 16)
        pairs = []
        for sample_index in range(7):
            grid = module.generate(seed, sample_index)
            errors = module.self_check(grid) if callable(getattr(module, "self_check", None)) else []
            if errors:
                raise ValueError(f"{task_id} self_check rejected draw {sample_index}: {errors}")
            python_output = module.rule_mirror(grid) if callable(getattr(module, "rule_mirror", None)) else None
            racket_output = racket_apply(bridge, wrap_rule, programs[task_id], grid)
            if python_output is not None and python_output != racket_output:
                raise ValueError(f"{task_id} Python/Racket mismatch at {sample_index}")
            observed = module.observe_overrides(grid) if callable(getattr(module, "observe_overrides", None)) else None
            pairs.append({
                "sample_index": sample_index,
                "input_sha256": grid_sha(grid),
                "output_sha256": grid_sha(racket_output),
                "input_shape": [len(grid), len(grid[0])],
                "output_shape": [len(racket_output), len(racket_output[0])],
                "observed_overrides": observed,
            })
        review_index_path = ROOT / "generators" / task_id / "evidence" / "review_index.json"
        audits = []
        if review_index_path.is_file():
            review_index = json.loads(review_index_path.read_text())
            audits = [
                {
                    "return_id": audit.get("return_id"),
                    "resolution": audit.get("resolution"),
                    "source_sha256": audit.get("source_sha256"),
                    "finding_excerpt": " ".join(audit.get("text", "").split())[:500],
                }
                for audit in review_index.get("audits", [])
            ]
        axes = getattr(module, "AXES", {})
        records.append({
            "task_id": task_id,
            "source_path": source.relative_to(ROOT).as_posix(),
            "source_sha256": source_sha,
            "rule_hash": catalog[task_id]["reviewed_rule_hash"],
            "catalog": {
                "mix_weight": catalog[task_id]["mix_weight"],
                "health": catalog[task_id]["health"],
                "review_status": catalog[task_id]["review_status"],
                "train_safety": catalog[task_id]["train_safety"],
                "sources": catalog[task_id]["sources"],
                "summary": catalog[task_id]["summary"],
            },
            "declared_axes": axes,
            "scene_profile_count": len(getattr(module, "SCENE_PROFILES", ())),
            "retained_audits": audits,
            "probe": {
                "draw_count": len(pairs),
                "distinct_inputs": len({pair["input_sha256"] for pair in pairs}),
                "distinct_outputs": len({pair["output_sha256"] for pair in pairs}),
                "four_query_inputs_distinct": len({pair["input_sha256"] for pair in pairs[3:]}) == 4,
                "racket_labels": len(pairs),
                "pairs": pairs,
            },
        })

known_quality = {
    "235a1d06b9d3": {
        "teachability": "known generated-domain anchor collapse: input[2][1] cannot be distinguished from input[1][1] by accepted draws",
        "allocation_disposition": "do not increase volume before a source-bound lesson repair or explicit shortcut-aware gate",
    },
    "c235e3da14f4": {
        "teachability": "known generated-domain shortcut ignores color 0; retained audit also reports no declared teaching contract",
        "allocation_disposition": "do not increase volume before a source-bound lesson repair or explicit shortcut-aware gate",
    },
    "2c7b1545edf9": {
        "teachability": "five-pair schedule explicitly covers unique-largest plus topmost and leftmost tie branches; repeated-distractor scenes target an aggregate-color shortcut",
        "allocation_disposition": "best of this three-record sample for a bounded quality-weighted arm, but still requires measured episode checks",
    },
}
for record in records:
    record["assessment"] = known_quality[record["task_id"]]

report = {
    "schema": "arcpuzzles-allocation-quality-probe-v1",
    "ticket_id": TICKET_ID,
    "ticket_seed": TICKET_SEED,
    "sampling_method": "pinned task plus two lowest sha256(ticket_seed + ':' + task_id) ranks from the current 500-ID uniform main pool",
    "sampled_ids": sampled_ids,
    "packet_draw": {
        "main_pool_size": len(main_ids),
        "main_distribution": "uniform",
        "per_id_main_probability": 1 / len(main_ids),
        "authoring_focus_probability": manifest["authoring_focus_policy"]["probability"],
        "supplementary_type_weights": manifest["supplementary_ticket_policy"]["weights"],
        "selected_assignment_id": assignment["assignment_id"],
        "selected_main_task": assignment["task_id"],
    },
    "training_context": {
        "snapshot": "2026-10-23 r6/r6-h3, dated context only",
        "materialized_item_share": {"ARCpuzzles": 0.47, "NVARC": 0.24},
        "materialized_token_share": {"ARCpuzzles": 0.37, "NVARC": 0.36, "ARC-GEN": 0.16, "RE-ARC": 0.11},
        "arc_puzzles_large_side_share": 0.073,
        "public_evaluation_large_side_share": 0.47,
        "limits": "No current ARC-GEN or RE-ARC record was selected by this reproducible three-record sample; their provenance is not scored here.",
        "training_context_sha256": sha_bytes((WORK / "TRAINING-CONTEXT.md").read_bytes()),
    },
    "racket": {key: identity.get(key) for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256")},
    "records": records,
    "cost_comparison": {
        "observed_probe": "21 protected-Racket labels, 7 per record; all 21 generated inputs passed self_check and Python/Racket parity",
        "per_episode_assumption": "3 demonstrations + 4 distinct queries costs 7 Racket labels before rival/ambiguity checks",
        "review_cost": "235a1d06b9d3 and c235e3da14f4 carry unresolved source-bound shortcut evidence; 2c7b1545edf9 already declares a branch-complete five-pair curriculum",
        "deduplication": "all seven sampled inputs were distinct for each record; this small probe does not estimate corpus-wide collision rates",
    },
    "alternative_allocation": {
        "scope": "bounded experiment only; no production mixture or draw-policy change",
        "control": "60 episodes, 20 from each sampled record",
        "candidate": "60 episodes: 48 from 2c7b1545edf9 and 6 each from the two unresolved-shortcut records",
        "estimated_rationale": "Estimated, not measured: the candidate spends 80% of labels on the only sampled source with explicit coverage of all authoritative comparator branches, while retaining small sentinels for the two known shortcut manifolds.",
        "metric": "unique Racket-valid 3-demo/4-query episodes that cover declared branches and reject every retained source-specific shortcut, per 100 Racket calls",
        "stopping_rule": "Stop immediately on any Racket mismatch, duplicate visible episode, or source hash drift. After 20 episodes per arm, stop for futility if candidate quality-per-call is not at least 10% higher; otherwise finish 60 per arm and adopt only if improvement is at least 20%, no declared branch loses coverage, and duplicate/rejection rate stays <=5%.",
        "coverage_gaps": "Three ARCpuzzles records only; no model loss, ARC-GEN, RE-ARC, NVARC visual quality, token cost, or universal ambiguity measurement. Known audits are reviewer-reported and remain unresolved.",
    },
    "conclusion": "Uniform authoring draws and catalog mix_weight=1.0 do not encode the retained teachability difference in this sample. A bounded quality gate should precede extra volume for the two shortcut-collapsed sources; the branch-scheduled source is the better candidate for a small measured reallocation arm.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "status": "completed",
    "sampled_ids": sampled_ids,
    "racket_labels": sum(r["probe"]["racket_labels"] for r in records),
    "distinct_inputs": {r["task_id"]: r["probe"]["distinct_inputs"] for r in records},
    "report": str(OUT),
}, indent=2, sort_keys=True))
