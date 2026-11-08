"""Twelve protected candidate calls on the frozen pre-repair seed-zero lessons."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
AUDIT_PATH = ROOT / "generators/5f9a2df57599/workspace/parametric/audit_native.py"
spec = importlib.util.spec_from_file_location("wall_shape_before_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
out = HERE / "shape-shortcut-before"
if (out / "report.json").exists():
    raise FileExistsError("preserve existing before-state evidence")
episode_bytes = (out / "episodes.json").read_bytes()
prior_bytes = (out / "prior-audit-report.json").read_bytes()
prior = json.loads(prior_bytes)
expected = next(row["sha256"] for row in prior["artifacts"] if row["path"] == "episodes.json")
if hashlib.sha256(episode_bytes).hexdigest() != expected:
    raise ValueError("captured episodes differ from the earlier protected audit artifact")
episodes = json.loads(episode_bytes)
retained = [episode for episode in episodes if episode["seed"] == 0]
if len(episodes) != 6 or len(retained) != 2:
    raise ValueError("expected all six captured episodes and two seed-zero policies")
rows, programs = [], {}
with audit.CachedEvaluator(ROOT) as evaluator:
    for episode in retained:
        policy = episode["settings"]["side_boundary_policy"]
        if len(episode["train"]) != 2 or len(episode["test"]) != 4:
            raise ValueError("before replay must use exactly the two core demos and four queries")
        if audit.source_hash(episode["program_solution"]) not in {row["sha256"] for row in prior["programs"]}:
            raise ValueError("intended program is not retained in the prior protected report")
        program = audit.rival_program(policy, "reject_l3")
        programs[policy] = program
        demo_results = []
        for index, pair in enumerate(episode["train"]):
            actual = evaluator(program, pair["input"])
            if actual != audit.rival_output(pair["input"], policy, "reject_l3"):
                raise ValueError("candidate Python/protected label mismatch")
            demo_results.append(actual == pair["output"])
            rows.append({"policy": policy, "split": "train", "index": index,
                         "input": pair["input"], "previously_verified_intended_output": pair["output"],
                         "fresh_candidate_output": actual, "agrees": actual == pair["output"]})
        survives_demos = all(demo_results)
        # Compare queries only after the demo-only survival result is frozen.
        for index, pair in enumerate(episode["test"]):
            actual = evaluator(program, pair["input"])
            if actual != audit.rival_output(pair["input"], policy, "reject_l3"):
                raise ValueError("candidate Python/protected label mismatch")
            rows.append({"policy": policy, "split": "test", "index": index,
                         "demo_survival_frozen_before_query": survives_demos,
                         "input": pair["input"], "previously_verified_intended_output": pair["output"],
                         "fresh_candidate_output": actual, "agrees": actual == pair["output"]})
    execution = evaluator.evidence()
if execution["actual_evaluations"] != 12 or not all(row["agrees"] for row in rows):
    raise ValueError("the bounded before-state shortcut was not reproduced exactly")
for policy, program in programs.items():
    (out / (policy + "-reject_l3.rkt")).write_text(program)
(out / "cases.json").write_bytes(audit.raw(rows))
(out / "candidate-execution.json").write_bytes(audit.raw(execution))
report = {
    "schema": "wall-shape-shortcut-protected-before-v1",
    "status": "reproduced_distribution_shortcut",
    "task_id": audit.TASK_ID,
    "scope": "Seed 0, two core demos and four queries under each policy, copied from all six earlier source-bound episodes. Twelve fresh candidate applications only; intended labels are those verified by the retained earlier protected audit.",
    "actual_candidate_evaluations": execution["actual_evaluations"],
    "cache_hits": execution["cache_hits"],
    "candidate_matches_previously_verified_intended_labels": 12,
    "fresh_intended_evaluations": 0,
    "source_binding_of_old_sampler_and_labels": prior["source_binding"],
    "prior_audit_report_sha256": hashlib.sha256(prior_bytes).hexdigest(),
    "captured_six_episodes_sha256": hashlib.sha256(episode_bytes).hexdigest(),
    "current_rival_implementation_sha256": hashlib.sha256(AUDIT_PATH.read_bytes()).hexdigest(),
    "replay_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "racket": execution["racket"],
    "query_labels_used_to_select_demo_survival": False,
    "limits": "This demonstrates a checked-distribution shortcut, not query-answer ambiguity or universal behavior. Only the fixed seed-zero subset was freshly replayed against the candidate; the other four captured episodes remain preserved without new execution."
}
report["artifacts"] = [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                       for path in sorted(out.iterdir()) if path.is_file()]
(out / "report.json").write_bytes(audit.raw(report))
print(json.dumps({key: report[key] for key in ("status", "actual_candidate_evaluations", "fresh_intended_evaluations", "candidate_matches_previously_verified_intended_labels")}, sort_keys=True))
