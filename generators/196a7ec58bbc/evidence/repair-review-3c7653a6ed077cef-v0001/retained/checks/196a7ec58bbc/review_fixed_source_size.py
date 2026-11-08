"""Bounded independent review: fixed 5x5 extraction survives repeated-size demos."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
HOME = ROOT / "generators/196a7ec58bbc/workspace/parametric"
spec = importlib.util.spec_from_file_location("quadrant_review_family", HOME / "native_family.py")
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)

settings = {"source_mode": "largest_component", "handedness": "clockwise"}
episode = family.generate(0, settings, demos=2, queries=4)
rival = """(rule! (lambda (g)
  (let* ((chosen (argmax obj-size (objects g 0)))
         (bb (obj-bbox chosen))
         (cells (obj-cells chosen))
         (tile (grid-from-fn 5 5
           (lambda (r c)
             (if (member (list (+ r (first bb)) (+ c (second bb))) cells)
                 (obj-color chosen) 0)))))
    (stack-grids 'vertical
      (list (stack-grids 'horizontal (list tile (rotate-cw tile)))
            (stack-grids 'horizontal (list (rotate-ccw tile) (rotate-180 tile))))))))"""

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
runtime = ROOT / "shared/runtime"
rows = []
with _local_imports(runtime, HOME.parent):
    apply, identity, bridge = _real_evaluator(runtime)
    try:
        for split, index, pair in [("train", i, p) for i,p in enumerate(episode["train"])] + [("test", 0, episode["test"][0])]:
            intended = _grid(apply(episode["program_solution"], pair["input"]))
            alternative = _grid(apply(rival, pair["input"]))
            assert intended == pair["output"]
            rows.append({"split": split, "index": index, "input": pair["input"],
                         "intended_output": intended, "rival_output": alternative,
                         "agrees": intended == alternative,
                         "selected_bbox_side": family.analyze_scene(pair["input"])["selected_bbox_side"]})
    finally:
        bridge.close()
report = {"task_id": "196a7ec58bbc", "seed": 0, "settings": settings,
          "source_sha256": hashlib.sha256((HOME / "native_family.py").read_bytes()).hexdigest(),
          "racket": identity, "intended_program": episode["program_solution"],
          "rival_program": rival, "executed_labels": 6, "cases": rows,
          "finding": "Fixed 5x5 source extraction fits both demos but differs on first query.",
          "rival_survives_demonstrations": all(row["agrees"] for row in rows[:2]),
          "query_disagrees": not rows[2]["agrees"]}
out = ROOT.parent / "checks/196a7ec58bbc/review-fixed-source-size.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"report": str(out), "source_sha256": report["source_sha256"],
                  "demo_agreement": [r["agrees"] for r in rows[:2]],
                  "query_agreement": rows[2]["agrees"],
                  "selected_bbox_sides": [r["selected_bbox_side"] for r in rows],
                  "executed_labels": 6}, sort_keys=True))
