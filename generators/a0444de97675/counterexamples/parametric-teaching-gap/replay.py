"""Replay the frozen before-fix lesson and two finite rivals through Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


ORDER = """
(define (review-list< a b)
  (cond ((empty? a) #f)
        ((< (first a) (first b)) #t)
        ((> (first a) (first b)) #f)
        (else (review-list< (rest a) (rest b)))))
(define (review-larger a b)
  (if (= (obj-size a) (obj-size b))
      (review-list< (obj-bbox a) (obj-bbox b))
      (> (obj-size a) (obj-size b))))
(define (review-crop work target)
  (let ((bb (obj-bbox target)))
    (upscale (subgrid work (first bb) (second bb) (third bb) (fourth bb)) 2)))
"""

PROGRAMS = {
    "largest_multicolor_group": """(rule! (let ((dummy 0))
""" + ORDER + """
  (let* ((work (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (mono (objects work 0))
         (binary (map (lambda (row)
                        (map (lambda (v) (if (= v 0) 0 1)) row)) work))
         (mixed (filter
                   (lambda (obj)
                     (> (length (remove-duplicates
                          (map (lambda (p) (at work (first p) (second p)))
                               (obj-cells obj)))) 1))
                   (objects binary 0))))
    (if (empty? mixed)
        '((0))
        (let* ((group (first (sort mixed review-larger)))
               (inside (filter
                         (lambda (obj)
                           (all? (lambda (p) (member? p (obj-cells group)))
                                 (obj-cells obj))) mono))
               (target (first (sort inside review-larger))))
          (review-crop work target))))))""",
    "area_rank_2": """(rule! (let ((dummy 0))
""" + ORDER + """
  (let* ((work (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (ordered (sort (objects work 0) review-larger)))
    (if (< (length ordered) 2)
        '((0))
        (review-crop work (second ordered))))))""",
}


def main():
    here = Path(__file__).resolve().parent
    source = here / "original-lesson.json"
    receipt_path = here / "racket-replay.json"
    if receipt_path.exists():
        raise ValueError("The retained replay already exists")
    lesson = json.loads(source.read_text())
    for rival in lesson["rivals"]:
        rival["program"] = PROGRAMS[rival["name"]]
    source.write_text(json.dumps(lesson, indent=2) + "\n")

    execution = []
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        rules = [("canonical", lesson["episode"]["program_solution"],
                  {split: [pair["output"] for pair in lesson["episode"][split]]
                   for split in ("train", "test")})]
        rules.extend((r["name"], r["program"], r["predictions"])
                     for r in lesson["rivals"])
        for name, program, expected in rules:
            wrapped = wrap_rule(program)
            for split in ("train", "test"):
                for index, pair in enumerate(lesson["episode"][split]):
                    literal = "'(" + " ".join(
                        "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                    ) + ")"
                    output = bridge.eval_text(f"({wrapped} {literal})")
                    assert isinstance(output, list) and 1 <= len(output) <= 30
                    assert all(isinstance(row, list) and 1 <= len(row) <= 30
                               for row in output)
                    assert len({len(row) for row in output}) == 1
                    assert all(type(v) is int and 0 <= v <= 9
                               for row in output for v in row)
                    assert output == expected[split][index], (name, split, index)
                    execution.append({"rule": name, "split": split,
                                      "index": index, "output": output,
                                      "matches_canonical": output == pair["output"]})
    finally:
        bridge.shutdown()
    receipt = {
        "schema": "a0444de97675-original-teaching-gap-racket-replay-v1",
        "status": "verified_before_fix_counterexample",
        "lesson_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "replay_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": "python3 run_with_racket.py python3 generators/a0444de97675/counterexamples/parametric-teaching-gap/replay.py",
        "source_stage": "before-fix",
        "source_sha256": lesson["source_sha256"],
        "racket": identity,
        "protected_racket_evaluations": len(execution),
        "program_sha256": {name: hashlib.sha256(program.encode()).hexdigest()
                           for name, program, _ in rules},
        "execution": execution,
        "scope": "This frozen lesson and these two rivals only. Does not evaluate repaired sampling, grant owner acceptance, or admit training.",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "protected_racket_evaluations": len(execution),
                      "path": str(receipt_path)}))


if __name__ == "__main__":
    main()
