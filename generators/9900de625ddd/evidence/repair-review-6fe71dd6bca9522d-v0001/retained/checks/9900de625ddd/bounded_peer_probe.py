"""One bounded peer review; all emitted data are private authoring evidence."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK = ROOT / "generators/9900de625ddd"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

def sha(body):
    return hashlib.sha256(body).hexdigest()

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

helper_path = TASK / "workspace/review_probe.py"
spec = importlib.util.spec_from_file_location("bounded_peer_helpers", helper_path)
helper = importlib.util.module_from_spec(spec)
exec(compile(helper_path.read_bytes(), str(helper_path), "exec"), helper.__dict__)
generator = helper.load_selected_generator(ROOT)
canonical, row_hash = helper.selected_canonical(ROOT)
program = canonical["program_solution"]
paths = [TASK / "generator.py", helper_path, Path(__file__),
         ROOT / "src/arcpuzzles/parametric_worker.py"]
binding = {str(p.relative_to(ROOT.parent)): sha(p.read_bytes()) for p in paths}
rival_program = """(rule! (lambda (g)
  (first (for*/fold ((state (list (empty-grid (rows g) (cols g) 0) (list))))
    ((r (in-range (- (rows g) 2))) (c (in-range (- (cols g) 2))))
    (let* ((out (first state)) (used (second state))
           (cells (positions-in-rect r c (+ r 2) (+ c 2))) (v (at g r c)))
      (if (and (not (= v 0))
               (all? (lambda (p) (= (at g (first p) (second p)) v)) cells)
               (not (for/or ((p cells)) (member p used))))
          (list (set-cell out (+ r 1) (+ c 1) v) (append cells used))
          state))))))"""
requests = [("easy", 53061962744457), ("medium", 1), ("hard", 17)]
records, failures, known_case = [], [], None
calls = 0
with _local_imports(ROOT / "shared/runtime", TASK / "workspace"):
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    def execute(code, grid):
        global calls
        calls += 1
        return _grid(apply(code, copy.deepcopy(grid)))
    try:
        canonical_pairs = canonical["train"] + canonical["test"]
        canonical_checks = [execute(program, p["input"]) == p["output"]
                            for p in canonical_pairs]
        if not all(canonical_checks):
            failures.append("Canonical labels disagree with protected Racket")
        canonical_fits = {name: all(fn(copy.deepcopy(p["input"])) == p["output"]
                                   for p in canonical_pairs)
                          for name, fn in generator.LESSON_COMPETITORS.items()}
        for band, seed in requests:
            pairs = []
            for index in range(4):
                grid = generator.generate(seed, index, difficulty=band)
                errors = generator.self_check(grid)
                if errors:
                    failures.append({"band": band, "seed": seed, "index": index,
                                     "domain_errors": errors})
                pairs.append({"input": grid, "output": execute(program, grid)})
            checks = {}
            for name, fn in generator.LESSON_COMPETITORS.items():
                agrees = [fn(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs]
                checks[name] = {"demo_agreement": agrees[:3], "query_agreement": agrees[3],
                                "query_discriminating_survivor": all(agrees[:3]) and not agrees[3]}
            if any(item["query_discriminating_survivor"] for item in checks.values()):
                failures.append({"band": band, "seed": seed, "issue": "ordinary_lesson_underidentified"})
            records.append({"band": band, "seed": seed, "sample_indices": [0, 1, 2, 3],
                            "profiles": [generator.schedule_profile(seed, i) for i in range(4)],
                            "input_hashes": [helper.digest(p["input"]) for p in pairs],
                            "rivals": checks})
            if band == "easy":
                rival_outputs = [execute(rival_program, p["input"]) for p in pairs]
                mirror_match = all(out == generator.LESSON_COMPETITORS["disjoint_windows"](p["input"])
                                   for out, p in zip(rival_outputs, pairs))
                train_indices, query_index = [0, 2, 3], 1
                fits = all(rival_outputs[i] == pairs[i]["output"] for i in train_indices)
                differs = rival_outputs[query_index] != pairs[query_index]["output"]
                known_case = {"classification": "reproduced_preexisting_excluded_rotation",
                              "source_binding": binding, "racket": identity,
                              "band": band, "seed": seed, "train_indices": train_indices,
                              "query_index": query_index,
                              "train": [pairs[i] for i in train_indices], "query": pairs[query_index],
                              "program": program, "counterfactual_program": rival_program,
                              "counterfactual_query_output": rival_outputs[query_index],
                              "counterfactual_demo_outputs": [rival_outputs[i] for i in train_indices],
                              "rival_fits_demonstrations": fits, "rival_changes_query": differs,
                              "racket_rival_matches_declared_python_rival": mirror_match,
                              "recommendation": "Keep the consecutive-demo assembly contract; if rotation is enabled, select a second overlap/nonrectangular witness before holding out the first."}
                if not (fits and differs and mirror_match):
                    failures.append("Previously retained rotation did not reproduce exactly")
    finally:
        bridge.close()
unchanged = binding == {str(p.relative_to(ROOT.parent)): sha(p.read_bytes()) for p in paths}
if not unchanged:
    failures.append("Source drift during probe")
save("private-known-rotation.json", known_case)
report = {
    "schema": "arcpuzzles-bounded-peer-review-v1", "task_id": "9900de625ddd",
    "outcome": "unchanged" if not failures else "blocked", "failures": failures,
    "source_binding": binding, "source_unchanged": unchanged,
    "canonical_row_sha256": row_hash, "canonical_program_sha256": sha(program.encode()),
    "racket": identity, "racket_evaluations": calls,
    "command": {"cwd": str(ROOT.parent), "argv": [str(ROOT.parent / ".venv/bin/python"),
                str(ROOT.parent / "run_with_racket.py"), str(ROOT.parent / ".venv/bin/python"),
                "../checks/9900de625ddd/bounded_peer_probe.py"]},
    "counts": {"canonical_pairs": len(canonical_checks), "canonical_matches": sum(canonical_checks),
               "ordinary_lessons": len(records), "demonstrations_per_lesson": 3,
               "queries_per_lesson": 1, "generated_inputs": len(records) * 4,
               "distinct_generated_inputs": len({h for r in records for h in r["input_hashes"]}),
               "declared_rivals": len(generator.LESSON_COMPETITORS),
               "ordinary_rival_lesson_checks": sum(len(r["rivals"]) for r in records),
               "ordinary_rivals_eliminated_by_demos": sum(not all(c["demo_agreement"]) for r in records for c in r["rivals"].values()),
               "ordinary_query_discriminating_survivors": sum(c["query_discriminating_survivor"] for r in records for c in r["rivals"].values()),
               "preexisting_excluded_rotations_rechecked": 1},
    "canonical_rival_fits": canonical_fits, "ordinary_lessons": records,
    "known_rotation": {"path": "checks/9900de625ddd/private-known-rotation.json",
                       "sha256": sha((HERE / "private-known-rotation.json").read_bytes()),
                       "fits_demos_changes_query": bool(known_case["rival_fits_demonstrations"] and known_case["rival_changes_query"])},
    "limitations": ["Three direct-generator lessons and ten declared Python rivals only; not a production API census or universal uniqueness claim.",
                    "Target labels and the retained disjoint-window counterfactual were executed in protected Racket; other rival predictions used the unchanged declared Python helpers.",
                    "The reproduced rotation is already documented and outside the current consecutive-demo guarantee; no new defect in the supported assembly was found.",
                    "No generator, rule, notes, approval, or training state was changed. All artifacts here contain private authoring labels."]}
save("report.json", report)
print(json.dumps({"outcome": report["outcome"], "counts": report["counts"],
                  "racket_evaluations": calls, "failures": failures}, sort_keys=True))
raise SystemExit(bool(failures))
