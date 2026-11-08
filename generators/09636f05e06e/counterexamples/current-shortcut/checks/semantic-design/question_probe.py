"""Final-source evidence for the exact generator-shortcuts review question."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
PACKET = WORK.parent
TASK = "09636f05e06e"
SOURCE = REPO / "generators" / TASK / "generator.py"
EXPECTED_SHA = "0477dc50fdff9ac43529ebbddd8173ac0641eaf0311929f51d51439040493e69"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gen():
    assert sha(SOURCE) == EXPECTED_SHA, "Final generator bytes changed."
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("question_target", SOURCE)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen


def main():
    gen = load_gen()
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        attempts = 0
        selected = None
        for seed in range(128):
            for index in range(4):
                if gen.schedule_profile(seed, index, "easy") != "scatter":
                    continue
                attempts += 1
                grid = gen.generate(seed, index, difficulty="easy")
                if len(grid) == len(grid[0]) == 8:
                    selected = {"seed": seed, "sample_index": index, "difficulty": "easy", "overrides": {}, "input": grid}
                    break
            if selected is not None:
                break
        assert selected is not None, "No small default scatter in the bounded search."
        assert gen.self_check(selected["input"]) == []
        assert gen.SEMANTIC_WITNESSES["isolated_zeros_with_gaps"](selected["input"])
        minimal = json.loads((HERE / "minimal_input.json").read_text())
        report = {
            "task_id": TASK, "generator_sha256": EXPECTED_SHA,
            "question": json.loads((REPO / "REVIEW/questions/generator-shortcuts.json").read_text()),
            "selected_default_example": selected,
            "selection_method": "First exact 8x8 default scatter, traversing seeds 0..127 and indices 0..3, easy band; only scatter slots are generated.",
            "scatter_candidates_examined": attempts,
            "minimal_input": minimal,
            "prior_minimal_receipt": "checks/semantic-design/minimal_racket_label.json",
            "prior_minimal_receipt_sha256": sha(HERE / "minimal_racket_label.json"),
        }
        (HERE / "question_evidence.json").write_text(json.dumps(report, indent=2)+"\n")
        (HERE / "question_inputs.json").write_text(json.dumps({"inputs": [minimal, selected["input"]]}, indent=2)+"\n")
        print(json.dumps({"generator_sha256": EXPECTED_SHA, "selected": {k: v for k, v in selected.items() if k != "input"}, "candidates": attempts, "observed": gen.observe_overrides(selected["input"])}, indent=2))
        return
    assert mode == "analyze", "Use build or analyze."
    report = json.loads((HERE / "question_evidence.json").read_text())
    receipt = json.loads((HERE / "question_racket.json").read_text())
    assert receipt["generator_sha256"] == EXPECTED_SHA
    assert receipt["rule_hash_matches_catalog"]
    assert len(receipt["results"]) == 2
    from reviewer_support import canonical_pairs
    canonical = canonical_pairs(TASK, root=REPO)
    report["canonical_shortcuts"] = {
        name: {"matches": sum(fn(pair["input"]) == pair["output"] for pair in canonical),
               "total": len(canonical)}
        for name, fn in gen.CANONICAL_SHORTCUTS.items()
    }
    report["rule_hash"] = receipt["executed_rule_hash"]
    report["rule_text_sha256"] = receipt["rule_text_sha256"]
    report["racket_receipt_sha256"] = sha(HERE / "question_racket.json")
    report["reproducer_sha256"] = sha(Path(__file__))
    report["examples"] = []
    expected_inputs = [report["minimal_input"], report["selected_default_example"]["input"]]
    for index, (row, expected_input) in enumerate(zip(receipt["results"], expected_inputs, strict=True)):
        assert row["input"] == expected_input
        assert row["valid_output"] and row["error"] is None
        inp, out = row["input"], row["output"]
        rival_out = gen.CANONICAL_SHORTCUTS["global_zero_hull"](inp)
        diff = [[r, c, out[r][c], rival_out[r][c]]
                for r in range(len(inp)) for c in range(len(inp[0])) if out[r][c] != rival_out[r][c]]
        assert diff
        points, rows, cols = gen._support(inp)
        report["examples"].append({
            "name": "compact_reference_counterexample" if index == 0 else "final_default_scatter",
            "input": inp, "actual_racket_output": out, "global_zero_hull_output": rival_out,
            "input_sha256": row["input_sha256"], "output_sha256": row["output_sha256"],
            "validator_messages": gen.self_check(inp),
            "active_rows": sorted(rows), "active_columns": sorted(cols),
            "zero_cells": sorted(points), "hull_differences": diff,
            "declared_shortcut_disagreements": {name: fn(inp) != out for name, fn in gen.CANONICAL_SHORTCUTS.items()},
            "semantic_rival_disagreements": {name: fn(inp) != out for name, fn in gen.SEMANTIC_RIVALS.items()},
            "witnesses": {name: bool(fn(inp)) for name, fn in gen.SEMANTIC_WITNESSES.items()},
        })
    assert all(row["matches"] == row["total"] for row in report["canonical_shortcuts"].values())
    assert report["examples"][1]["validator_messages"] == []
    report["verification_commands"] = [
        {"argv": ["python3", "WORK/checks/semantic-design/question_probe.py", "build"], "cwd": str(PACKET), "returncode": 0},
        {"argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/semantic-design/question_inputs.json", "--out", "../checks/semantic-design/question_racket.json", "--timeout", "180"], "cwd": str(PACKET), "effective_payload_cwd": receipt["cwd"], "returncode": 0},
        {"argv": ["python3", "WORK/checks/semantic-design/question_probe.py", "analyze"], "cwd": str(PACKET), "returncode": 0},
    ]
    report["scope"] = "All current declared canonical shortcuts tested against all four canonical pairs; two public Racket labels including one chosen small final-source default scatter. No new lesson census."
    (HERE / "question_evidence.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({
        "canonical_shortcuts": report["canonical_shortcuts"],
        "rule_hash": report["rule_hash"], "rule_text_sha256": report["rule_text_sha256"],
        "examples": [{k: e[k] for k in ("name", "validator_messages", "active_rows", "active_columns", "hull_differences", "declared_shortcut_disagreements", "semantic_rival_disagreements", "witnesses")} for e in report["examples"]],
    }, indent=2))


if __name__ == "__main__":
    main()
