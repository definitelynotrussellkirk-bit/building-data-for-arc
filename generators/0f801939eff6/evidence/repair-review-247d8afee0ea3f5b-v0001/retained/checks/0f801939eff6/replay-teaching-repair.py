"""Replay the retained teaching hole and its fix through protected Racket."""
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _real_evaluator

ROOT = Path.cwd()
HOME = ROOT / "generators/0f801939eff6/workspace/parametric"
CHECKS = ROOT.parent / "checks/0f801939eff6"
spec = importlib.util.spec_from_file_location("_teaching_repair", HOME / "prototype.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
before = json.loads((CHECKS / "teaching-hole-before.json").read_text())
qualification = json.loads((CHECKS / "qualification-v3/qualification.json").read_text())
settings = {"merge": "2_into_1"}
gold_program = p.program(settings)
rival_program = p.rival_programs(settings)["local_cluster_recolor"]
assert before["episode"]["program_solution"] == gold_program
after = p.generate(17, settings, 2, 4)
apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
cases = []
try:
    for stage, episode, choices in [
        ("before", before["episode"], [("train", 0), ("train", 1), ("test", 2)]),
        ("after", after, [("train", 0), ("train", 1)]),
    ]:
        for split, index in choices:
            pair = episode[split][index]
            gold = _grid(apply(gold_program, pair["input"]))
            rival = _grid(apply(rival_program, pair["input"]))
            assert gold == pair["output"]
            assert rival == p.rival_outputs(pair["input"], settings)["local_cluster_recolor"]
            cases.append({"stage": stage, "split": split, "index": index,
                          "input": pair["input"], "output": gold,
                          "rival_output": rival, "rival_matches": gold == rival})
finally:
    bridge.close()
assert [c["rival_matches"] for c in cases if c["stage"] == "before"] == [True, True, False]
assert [c["rival_matches"] for c in cases if c["stage"] == "after"] == [True, False]
report = {"schema": "arcpuzzles-bounded-teaching-repair-v1", "status": "passed",
          "source_binding": qualification["source_binding"],
          "before_prototype_sha256": before["source_sha256"],
          "current_prototype_sha256": hashlib.sha256((HOME / "prototype.py").read_bytes()).hexdigest(),
          "program": gold_program, "rival_program": rival_program,
          "racket": identity, "racket_evaluations": 10, "cases": cases,
          "finding": "Local-only recoloring fitted both old demonstrations but failed query 2.",
          "repair": "The second demonstration includes an eight-disconnected color-2 component.",
          "limits": "One retained minimal lesson and three regression seeds; finite-rival scope."}
out = CHECKS / "teaching-repair.json"
out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps({"status": "passed", "racket_evaluations": 10, "evidence": str(out)}))
