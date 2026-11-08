"""Bounded nine-rival audit: keep one macro-position fixed, sort the other eight."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK = "3108da8bf9e8"
TARGETS = (6, 7, 8, 3, 4, 5, 0, 1, 2)


def rival(grid, anchor):
    blocks = [[[grid[4 * (i // 3) + r][4 * (i % 3) + c] for c in range(3)]
               for r in range(3)] for i in range(9)]
    sources = sorted((i for i in range(9) if i != anchor),
                     key=lambda i: sum(v == 1 for row in blocks[i] for v in row))
    output = copy.deepcopy(grid)
    for source, target in zip(sources, (i for i in TARGETS if i != anchor)):
        for r in range(3):
            for c in range(3):
                output[4 * (target // 3) + r][4 * (target % 3) + c] = blocks[source][r][c]
    return output


def rival_program(anchor):
    br, bc = divmod(anchor, 3)
    target_list = " ".join(f"(list {i // 3} {i % 3})" for i in TARGETS if i != anchor)
    return f"""(rule! (lambda (g)
      (let* ((sources (for*/list ((br (range 0 3)) (bc (range 0 3))
                         #:unless (and (= br {br}) (= bc {bc})))
                        (list br bc (for*/sum ((dr (range 0 3)) (dc (range 0 3)))
                          (if (= (at g (+ (* br 4) dr) (+ (* bc 4) dc)) 1) 1 0)))))
             (sorted (sort-by sources (lambda (x) (third x))))
             (targets (list {target_list})))
        (grid-from-fn 11 11 (lambda (r c)
          (if (or (= (mod r 4) 3) (= (mod c 4) 3)) 0
            (let ((br (floor (/ r 4))) (bc (floor (/ c 4))))
              (if (and (= br {br}) (= bc {bc})) (at g r c)
                (let* ((idx (find-first (lambda (i)
                               (and (= br (first (nth targets i)))
                                    (= bc (second (nth targets i))))) (range 0 8)))
                       (source (nth sorted idx)))
                  (at g (+ (* (first source) 4) (mod r 4))
                        (+ (* (second source) 4) (mod c 4))))))))))))"""


def main():
    gen, path, source_sha = load_selected_generator(TASK, root=ROOT)
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
            if '"3108da8bf9e8"' in line]
    canonical = next(row for row in rows if row.get("task_id") == TASK)
    report = {"schema": "bounded-peer-audit-v1", "task_id": TASK,
              "source_sha256": source_sha, "rule_sha256": hashlib.sha256(
                  canonical["program_solution"].encode()).hexdigest(),
              "scope": "Nine predefined anchor-preserving global sorts; at most 16 easy lessons of three demonstrations and one query.",
              "prototype_present": (path.parent / "workspace/parametric/prototype.py").exists(),
              "lessons_checked": 0, "draws_checked": 0, "named_rival_draw_matches": {},
              "status": "no_counterexample_in_bounded_probe", "racket_evaluations": 0,
              "limits": "Finite positional-rival audit, not universal identifiability or a full battery. No source repair or approval."}
    witness = None
    for seed in range(16):
        pairs = []
        for index in range(4):
            grid = gen.generate(seed, index, difficulty="easy")
            assert gen.self_check(grid) == []
            answer = gen.rule_mirror(grid)
            pairs.append({"input": grid, "output": answer})
            report["draws_checked"] += 1
            for name, competitor in gen.SEMANTIC_RIVALS.items():
                if competitor(copy.deepcopy(grid)) == answer:
                    report["named_rival_draw_matches"][name] = report["named_rival_draw_matches"].get(name, 0) + 1
        report["lessons_checked"] += 1
        survivors = [anchor for anchor in range(9)
                     if all(rival(pair["input"], anchor) == pair["output"] for pair in pairs[:3])]
        wrong = [anchor for anchor in survivors if rival(pairs[3]["input"], anchor) != pairs[3]["output"]]
        if wrong:
            anchor = wrong[0]
            witness = {"seed": seed, "difficulty": "easy", "demo_indices": [0, 1, 2],
                       "query_index": 3, "anchor_index": anchor, "anchor_macro_position": list(divmod(anchor, 3)),
                       "demo_only_surviving_anchors": survivors, "train": pairs[:3], "test": [pairs[3]],
                       "query_rival_output": rival(pairs[3]["input"], anchor),
                       "canonical_program": canonical["program_solution"], "rival_program": rival_program(anchor)}
            report["existing_lesson_identifiable_findings"] = gen.lesson_identifiable(pairs[:3], pairs[3])
            report["canonical_training_rival_fits"] = [rival(p["input"], anchor) == p["output"]
                                                       for p in canonical["train"]]
            break
    if witness:
        report["status"] = "counterexample_python_confirmed_racket_pending"
        (HERE / "counterexample.json").write_text(json.dumps(witness, indent=2) + "\n")
        runtime = ROOT / "shared/runtime"
        try:
            with _local_imports(runtime, path.parent):
                apply, identity, bridge = _real_evaluator(runtime)
                report["racket_runtime"] = identity
                try:
                    comparisons = []
                    for split in ("train", "test"):
                        for pair in witness[split]:
                            truth = _grid(apply(witness["canonical_program"], pair["input"]))
                            report["racket_evaluations"] += 1
                            alternate = _grid(apply(witness["rival_program"], pair["input"]))
                            report["racket_evaluations"] += 1
                            assert truth == pair["output"]
                            assert alternate == rival(pair["input"], witness["anchor_index"])
                            comparisons.append({"split": split, "rival_equals_canonical": alternate == truth})
                    assert [r["rival_equals_canonical"] for r in comparisons] == [True, True, True, False]
                    report["protected_comparisons"] = comparisons
                    report["status"] = "counterexample_protected_racket_confirmed"
                finally:
                    bridge.close()
        except Exception as error:
            report["racket_error"] = f"{type(error).__name__}: {error}"
        report["counterexample"] = "checks/3108da8bf9e8/counterexample.json"
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source_sha
    (HERE / "peer_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
