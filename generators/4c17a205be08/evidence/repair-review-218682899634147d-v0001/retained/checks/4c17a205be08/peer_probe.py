"""Bounded five-demo/four-query transfer audit with three executable rivals."""
from pathlib import Path
import hashlib
import json

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(Path.cwd())
TASK = "4c17a205be08"
gen, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
expected_sha = "bc804b9fdda08451fbd63dbfb2918d0f1e1e84074d71db7cf97973555722fe2b"
assert source_sha == expected_sha
rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines() if line.strip()]
sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
assert len(sources) == 1
canonical = sources.pop()
needle = "(apply-cmd (crop-to-content c) code)"
assert canonical.count(needle) == 1
programs = {"canonical": canonical}
for name, selector in {
    "observed_four_only": "(if (or (= code 1) (= code 6)) 2 code)",
    "ud_falls_back_to_cw": "(if (= code 6) 2 code)",
    "always_cw": "2",
}.items():
    programs[name] = canonical.replace(needle, f"(apply-cmd (crop-to-content c) {selector})")
cases = []
evaluations = 0
with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"] is True
    for index in range(9):
        grid = gen.generate(0, index, difficulty="medium")
        assert not gen._teaching_reasons(grid)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        answers = {name: bridge.eval_text(f"({wrap_rule(program)} {literal})") for name, program in programs.items()}
        evaluations += len(answers)
        assert answers["canonical"] == gen.rule_mirror(grid)
        cases.append({"sample_index": index, "split": "train" if index < 5 else "test",
                      "transform": gen.observe_overrides(grid)["transform"],
                      "input": grid, "output": answers["canonical"],
                      "rival_outputs": {k: v for k, v in answers.items() if k != "canonical"}})
train, queries = cases[:5], cases[5:]
rivals = {}
for name in programs.keys() - {"canonical"}:
    demo_disagreements = [p["sample_index"] for p in train if p["rival_outputs"][name] != p["output"]]
    query_disagreements = [p["sample_index"] for p in queries if p["rival_outputs"][name] != p["output"]]
    rivals[name] = {"fits_all_demos": not demo_disagreements, "demo_disagreement_indices": demo_disagreements,
                    "query_disagreement_indices": query_disagreements}
assert rivals["ud_falls_back_to_cw"]["fits_all_demos"]
assert rivals["ud_falls_back_to_cw"]["query_disagreement_indices"] == [5]
declared_gate = list(gen.lesson_identifiable(
    [{"input": p["input"], "output": p["output"]} for p in train],
    {"input": queries[0]["input"], "output": queries[0]["output"]}) or [])
report = {"schema": "4c17a205be08-bounded-peer-review-v1", "status": "finding", "task_id": TASK,
          "generator_sha256": source_sha, "rule_hash": gen.RULE_HASH, "generator_version": gen.VERSION,
          "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
          "seed": 0, "difficulty": "medium", "demos": 5, "queries": 4,
          "racket_evaluations": evaluations, "runtime_identity": identity,
          "rivals": rivals, "existing_declared_gate_findings": declared_gate,
          "finding": "A UD-to-CW fallback fits all five ordinary demonstrations but disagrees on the first query. The existing finite gate omits this single-missing-command rival.",
          "programs": programs, "cases": cases,
          "next_action": "Add single-missing-transform rivals and require six-branch teaching coverage, preferably six demonstrations for the ordinary six-branch schedule; retain this original lesson as alternative-answer evidence.",
          "limits": "One seed, medium difficulty, one five-demo/four-query lesson, three rivals. Canonical labels passed. No universal unlearnability, production repair, owner integration, or training admission claim."}
out = Path(__file__).with_name("peer-report.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ("status", "racket_evaluations", "rivals", "existing_declared_gate_findings")}))
