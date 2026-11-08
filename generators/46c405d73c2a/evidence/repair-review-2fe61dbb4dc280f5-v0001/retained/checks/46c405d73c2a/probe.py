"""Evidence-only replay of two finite distance rivals; no source repair."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rival(predicate):
    return f"""(rule!
 (let* ([colors (sort (grid-colors g 0) <)]
        [points (map (lambda (color) (first (find-color g color))) colors)]
        [n (length colors)])
   (grid-from-fn n n
    (lambda (r c)
     (if (= r c) 5
      (let* ([a (list-ref points r)] [b (list-ref points c)]
             [dr (abs (- (first a) (first b)))]
             [dc (abs (- (second a) (second b)))])
       (if {predicate} 8 0)))))))"""


def main():
    destination = HERE / "audit.json"
    if destination.exists():
        raise ValueError("refusing to replace existing audit evidence")
    source = ROOT / "generators/46c405d73c2a/generator.py"
    rule_path = ROOT / "shared/data/base/solutions/banks/1f065edbcf08/S17_H7__46c405d73c2a.json"
    canonical = json.loads(rule_path.read_bytes())
    programs = {"canonical": canonical["racket_target"]["target_code"],
                "horizontal_only": rival("(and (= dr 0) (<= dc 2))"),
                "manhattan_le2": rival("(<= (+ dr dc) 2)")}
    bound = [source, rule_path, ROOT / "generators/46c405d73c2a/notes.md",
             ROOT / "generators/46c405d73c2a/evidence/review_index.json", Path(__file__)]
    hashes = {str(path.relative_to(ROOT.parent)): sha(path) for path in bound}
    cache, evaluations, episodes, replay = {}, [], [], []
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, source.parent):
        spec = importlib.util.spec_from_file_location("_peer_46c405d73c2a", source)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        apply, identity, bridge = _real_evaluator(runtime)
        def outputs(grid):
            key = json.dumps(grid, separators=(",", ":"))
            if key not in cache:
                labels = {name: _grid(apply(program, grid)) for name, program in programs.items()}
                cache[key] = labels
                evaluations.append({"input": grid, "outputs": labels})
            return cache[key]
        try:
            # The source-bound existing report names seed1000/index3..6.
            # Only six additional windows are sampled; no prevalence claim.
            jobs = [(1000, 3)] + [(seed, start) for seed in (0, 17) for start in (0, 3, 6)]
            for seed, start in jobs:
                pairs = []
                for index in range(start, start + 4):
                    grid = generator.generate(seed, index, difficulty="easy")
                    errors = generator.self_check(grid)
                    if errors:
                        raise ValueError(f"generated input failed self_check: {errors}")
                    pairs.append({"sample_index": index, "input": grid, **outputs(grid)})
                results = {}
                for name in programs:
                    if name == "canonical":
                        continue
                    fits = [pair[name] == pair["canonical"] for pair in pairs[:3]]
                    disagree = pairs[3][name] != pairs[3]["canonical"]
                    results[name] = {"demo_fits": fits, "query_disagrees": disagree,
                                     "teaching_hole": all(fits) and disagree}
                episodes.append({"seed": seed, "difficulty": "easy", "demo_indices": list(range(start, start+3)),
                                 "query_index": start+3, "results": results,
                                 "train": pairs[:3], "test": pairs[3:]})
            visible = json.loads(canonical["visible_context"]["samples_text"])
            for pair in visible["train"]:
                labels = outputs(pair["input"])
                if labels["canonical"] != pair["output"]:
                    raise AssertionError("canonical visible demonstration replay mismatch")
                replay.append({"input": pair["input"], "output": pair["output"],
                               "rival_fits": {name: labels[name] == pair["output"]
                                              for name in programs if name != "canonical"}})
        finally:
            bridge.close()
    after = {str(path.relative_to(ROOT.parent)): sha(path) for path in bound}
    if after != hashes:
        raise AssertionError("bound sources changed during audit")
    holes = [{"seed": episode["seed"], "demo_indices": episode["demo_indices"],
              "query_index": episode["query_index"], "rival": name}
             for episode in episodes for name, result in episode["results"].items() if result["teaching_hole"]]
    result = {"schema": "arc-bounded-peer-rival-audit-v1", "task_id": "46c405d73c2a",
              "outcome": "existing_teaching_gap_reproduced" if holes else "no_new_issue_in_bounded_probe",
              "changed_components": [], "source_sha256": hashes, "source_after_sha256": after,
              "racket": identity, "programs": programs,
              "program_sha256": {name: hashlib.sha256(program.encode()).hexdigest() for name, program in programs.items()},
              "racket_evaluations": len(evaluations)*len(programs), "execution_errors": [],
              "episodes": episodes, "canonical_visible_replay": replay,
              "teaching_holes": holes, "all_evaluated_labels": evaluations,
              "interpretation": "Existing unresolved horizontal-only shortcut checked against current exact source. No generator or note changes; evidence is a proposal for triage.",
              "limits": ["Two concrete rivals, seven easy-band windows and two canonical visible demonstrations only.",
                         "Seed1000/index3..6 deliberately replays a previously retained finding; it is not independent discovery.",
                         "No prevalence, universal identifiability, safety approval or training admission claim."]}
    destination.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"audit": str(destination), "racket_evaluations": result["racket_evaluations"],
                      "windows": len(episodes), "teaching_holes": holes, "source_unchanged": hashes==after}))


if __name__ == "__main__":
    main()
