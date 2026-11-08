from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
PACKET = ROOT.parent
sys.path.insert(0, str(ROOT))


def load_gen(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_finalize_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def differing_cells(actual, rival):
    return [
        {"row": r, "col": c, "racket": actual[r][c], "rival": rival[r][c]}
        for r in range(len(actual))
        for c in range(len(actual[r]))
        if actual[r][c] != rival[r][c]
    ]


def main() -> None:
    probe = json.loads((PACKET / "checks/audit/audit-probe.json").read_text())
    configs = {
        "87079dd3fc4a": {
            "rival_name": "first_marker_only",
            "rival_description": "Apply the projection rule only to the first/only green marker.",
            "rival_key": "first_marker_only_output",
            "provenance": {
                "kind": "canonical_pair",
                "canonical_unique_index": probe["87079dd3fc4a"]["counterexample"]["canonical_unique_index"],
            },
            "documented_domain": "Yes: this is an unmodified canonical input with two valid markers on dense guides.",
            "sampler_support": "No in the measured ordinary sampler: 0/600 draws had more than one marker.",
            "sample_observation": probe["87079dd3fc4a"]["default_draw_marker_counts"],
        },
        "c96915f33c65": {
            "rival_name": "global_unique_color_only",
            "rival_description": "Bloom an isolated seed only when its color occurs exactly once in the whole grid.",
            "rival_key": "unique_color_shortcut_output",
            "provenance": {"kind": "handcrafted_semantic_boundary"},
            "documented_domain": "Yes by the stated rule/invariants: both same-colored seeds are isolated, interior, and have zero cardinal neighbors.",
            "sampler_support": "No in the measured ordinary sampler: 0/600 draws repeated a nonzero color because colors are sampled without replacement.",
            "sample_observation": {
                "draws_checked": probe["c96915f33c65"]["default_draws_checked"],
                "draws_with_repeated_nonzero_color": probe["c96915f33c65"]["default_draws_with_repeated_nonzero_color"],
            },
        },
    }

    summary = {}
    for task_id, cfg in configs.items():
        task_dir = PACKET / "checks/audit" / task_id
        racket = json.loads((task_dir / "racket.json").read_text())
        rival_doc = json.loads((task_dir / "rival.json").read_text())
        input_grid = json.loads((task_dir / "input.json").read_text())
        result = racket["results"][0]
        rival_output = rival_doc["output"]
        expected_python = probe[task_id]["counterexample"]["authority_output"]
        if result["input"] != input_grid:
            raise AssertionError(f"{task_id}: apply input mismatch")
        if result["output"] != expected_python:
            raise AssertionError(f"{task_id}: Python mirror disagrees with Racket")
        diffs = differing_cells(result["output"], rival_output)
        if not diffs:
            raise AssertionError(f"{task_id}: counterexample does not refute rival")
        mod = load_gen(task_id)
        validator_messages = mod.self_check(input_grid)
        evidence = {
            "schema": "arcpuzzles-audit-counterexample-v1",
            "task_id": task_id,
            "generator_version": getattr(mod, "VERSION", None),
            "generator_sha256": racket["generator_sha256"],
            "executed_rule_hash": racket["executed_rule_hash"],
            "rule_text_sha256": racket["rule_text_sha256"],
            "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
            "provenance": cfg["provenance"],
            "input_sha256": result["input_sha256"],
            "input": input_grid,
            "racket_output_sha256": result["output_sha256"],
            "racket_output": result["output"],
            "rival_name": cfg["rival_name"],
            "rival_description": cfg["rival_description"],
            "rival_output": rival_output,
            "difference_count": len(diffs),
            "differences": diffs,
            "valid_output": result["valid_output"],
            "validator": {
                "function": "generator.self_check",
                "messages": validator_messages,
                "passes": not validator_messages,
            },
            "documented_domain": cfg["documented_domain"],
            "ordinary_sampler_support": cfg["sampler_support"],
            "ordinary_sampler_observation": cfg["sample_observation"],
            "apply_command": racket["command"],
            "apply_cwd": "repo",
            "sampling_probe_command": [
                "python3", "run_with_racket.py", "python3", "../checks/audit/probe_audit_targets.py"
            ],
            "sampling_probe_cwd": "packet_root",
            "source_files": [
                f"checks/audit/{task_id}/input.json",
                f"checks/audit/{task_id}/racket.json",
                f"checks/audit/{task_id}/rival.json",
                "checks/audit/audit-probe.json",
            ],
        }
        (task_dir / "counterexample.json").write_text(json.dumps(evidence, indent=2) + "\n")
        summary[task_id] = {
            "validator_passes": not validator_messages,
            "difference_count": len(diffs),
            "generator_sha256": racket["generator_sha256"],
            "rule_hash": racket["executed_rule_hash"],
        }
    print(json.dumps({"status": "PASS", "tasks": summary}, indent=2))


if __name__ == "__main__":
    main()
