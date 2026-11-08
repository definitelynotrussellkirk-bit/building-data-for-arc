"""Bounded protected-Racket self-review for the 1ec277b81469 family.

The probe is intentionally executable evidence rather than prose.  It asks the
protected Racket evaluator to distinguish the intended finite settings from a
bank of plausible row-packing and second-stage shortcuts, retains a concrete
counterexample for every rejected rival, and records a dense 30x30 stress case.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "1ec277b81469"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_1ec277b81469", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_RIGHT_PACK = """(define (right-pack grid)
    (grid-from-fn (rows grid) (cols grid)
      (lambda (r c)
        (let* ((vals (filter (lambda (v) (not (= v 0))) (row-at grid r)))
               (start (- (cols grid) (length vals))))
          (if (< c start) 0 (list-ref vals (- c start)))))))"""

_LEFT_PACK = """(define (left-pack grid)
    (grid-from-fn (rows grid) (cols grid)
      (lambda (r c)
        (let ((vals (filter (lambda (v) (not (= v 0))) (row-at grid r))))
          (if (< c (length vals)) (list-ref vals c) 0)))))"""

_SORT_RIGHT = """(define (sort-right grid)
    (grid-from-fn (rows grid) (cols grid)
      (lambda (r c)
        (let* ((vals (sort (filter (lambda (v) (not (= v 0))) (row-at grid r)) <))
               (start (- (cols grid) (length vals))))
          (if (< c start) 0 (list-ref vals (- c start)))))))"""

_REVERSE_RIGHT = """(define (reverse-right grid)
    (grid-from-fn (rows grid) (cols grid)
      (lambda (r c)
        (let* ((vals (reverse (filter (lambda (v) (not (= v 0))) (row-at grid r))))
               (start (- (cols grid) (length vals))))
          (if (< c start) 0 (list-ref vals (- c start)))))))"""


def _after_pack(body: str) -> str:
    return f"""(rule! (let ((dummy 0))
  {_RIGHT_PACK}
  (let* ((intermediate (right-pack g))
         (regions (objects intermediate 0)))
    {body})))"""


def _after_named_transform(definition: str, function_name: str) -> str:
    return f"""(rule! (let ((dummy 0))
  {definition}
  (let* ((intermediate ({function_name} g))
         (regions (objects intermediate 0))
         (chosen (pick-max regions obj-size)))
    (draw-rect-filled intermediate
                      (obj-r1 chosen) (obj-c1 chosen)
                      (obj-r2 chosen) (obj-c2 chosen) 9))))"""


def rivals(proto):
    return {
        "canonical": proto.program({"finish": "canonical"}),
        "sequential": proto.program({"finish": "fill_largest_bbox"}),
        "identity": "(rule! (lambda (g) g))",
        "all_zero": "(rule! (lambda (g) (empty-grid (rows g) (cols g) 0)))",
        "left_pack": f"(rule! (let ((dummy 0)) {_LEFT_PACK} (left-pack g)))",
        "sort_right": f"(rule! (let ((dummy 0)) {_SORT_RIGHT} (sort-right g)))",
        "reverse_right": f"(rule! (let ((dummy 0)) {_REVERSE_RIGHT} (reverse-right g)))",
        "right_pack_recolor_9": f"""(rule! (let ((dummy 0))
  {_RIGHT_PACK}
  (let ((packed (right-pack g)))
    (grid-from-fn (rows packed) (cols packed)
      (lambda (r c) (if (= (at packed r c) 0) 0 9))))))""",
        "first_region_bbox": _after_pack(
            "(let ((chosen (first regions))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "smallest_region_bbox": _after_pack(
            "(let ((chosen (pick-min regions obj-size))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_region_whole": _after_pack(
            "(let ((chosen (pick-max regions obj-size))) "
            "(recolor-cells intermediate (obj-cells chosen) 9))"
        ),
        "largest_bbox_area": _after_pack(
            "(let ((chosen (pick-max regions (lambda (obj) "
            "(* (- (+ (obj-r2 obj) 1) (obj-r1 obj)) "
            "   (- (+ (obj-c2 obj) 1) (obj-c1 obj))))))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_bbox_height": _after_pack(
            "(let ((chosen (pick-max regions (lambda (obj) "
            "(- (+ (obj-r2 obj) 1) (obj-r1 obj)))))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_bbox_width": _after_pack(
            "(let ((chosen (pick-max regions (lambda (obj) "
            "(- (+ (obj-c2 obj) 1) (obj-c1 obj)))))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_8_connected": f"""(rule! (let ((dummy 0))
  {_RIGHT_PACK}
  (let* ((intermediate (right-pack g))
         (regions (objects-8 intermediate 0))
         (chosen (pick-max regions obj-size)))
    (draw-rect-filled intermediate
                      (obj-r1 chosen) (obj-c1 chosen)
                      (obj-r2 chosen) (obj-c2 chosen) 9))))""",
        "most_frequent_color": _after_pack(
            "(let* ((chosen-color (mode intermediate 0)) "
            "       (same-color (filter (lambda (obj) (= (obj-color obj) chosen-color)) regions)) "
            "       (chosen (pick-max same-color obj-size))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "all_cells_of_largest_color": _after_pack(
            "(let* ((largest (pick-max regions obj-size)) "
            "       (cells (find-color intermediate (obj-color largest))) "
            "       (rs (map first cells)) (cs (map second cells))) "
            "(draw-rect-filled intermediate (apply min rs) (apply min cs) "
            "(apply max rs) (apply max cs) 9))"
        ),
        "topmost_region_bbox": _after_pack(
            "(let ((chosen (pick-min regions obj-r1))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "bottommost_region_bbox": _after_pack(
            "(let ((chosen (pick-max regions obj-r2))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "rightmost_region_bbox": _after_pack(
            "(let ((chosen (pick-max regions obj-c2))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "fixed_top_left": _after_pack("(draw-rect-filled intermediate 0 0 2 2 9)"),
        "skip_pack": """(rule! (let ((dummy 0))
  (let* ((regions (objects g 0))
         (chosen (pick-max regions obj-size)))
    (draw-rect-filled g
                      (obj-r1 chosen) (obj-c1 chosen)
                      (obj-r2 chosen) (obj-c2 chosen) 9))))""",
        "left_pack_then_bbox": _after_named_transform(_LEFT_PACK, "left-pack"),
        "sort_right_then_bbox": _after_named_transform(_SORT_RIGHT, "sort-right"),
        "reverse_right_then_bbox": _after_named_transform(_REVERSE_RIGHT, "reverse-right"),
    }


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def build_report(seeds=(0, 7, 17, 41, 91)):
    proto = _load_prototype()
    candidates = rivals(proto)
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    rows = []
    regressions = {}
    evaluations = 0
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for setting_name in ("canonical", "fill_largest_bbox"):
                expected_name = "canonical" if setting_name == "canonical" else "sequential"
                for seed in seeds:
                    episode = proto.generate(seed, {"finish": setting_name}, 2, 4)
                    survivors = []
                    expected_outputs = [pair["output"] for pair in episode["train"]]
                    for name, source in candidates.items():
                        outputs = [apply(source, pair["input"]) for pair in episode["train"]]
                        evaluations += len(outputs)
                        if outputs == expected_outputs:
                            survivors.append(name)
                    if survivors != [expected_name]:
                        raise ValueError(
                            f"shortcut survivor set for {setting_name} seed {seed}: {survivors}"
                        )
                    for name, source in candidates.items():
                        if name == expected_name:
                            continue
                        for split in ("train", "test"):
                            found = False
                            for index, pair in enumerate(episode[split]):
                                actual = apply(source, pair["input"])
                                evaluations += 1
                                if actual != pair["output"]:
                                    regressions.setdefault(
                                        f"{setting_name}:{name}",
                                        {
                                            "setting": setting_name,
                                            "rival": name,
                                            "split": split,
                                            "index": index,
                                            "input": pair["input"],
                                            "expected": pair["output"],
                                            "rival_output": actual,
                                        },
                                    )
                                    found = True
                                    break
                            if found:
                                break
                    rows.append(
                        {
                            "setting": setting_name,
                            "seed": seed,
                            "survivors": survivors,
                            "input_hashes": [proto.digest(pair["input"]) for pair in episode["train"]],
                            "query_hashes": [proto.digest(pair["input"]) for pair in episode["test"]],
                        }
                    )
        finally:
            bridge.close()

    large = proto.generate(5, {"finish": "fill_largest_bbox"}, 2, 4)["test"][-1]["input"]
    summary = proto.stage_summary(large)
    return {
        "schema": "arcpuzzles-parametric-adversarial-self-review-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "demos": 2,
        "queries": 4,
        "candidate_program_sha256": {
            name: hashlib.sha256(source.encode()).hexdigest() for name, source in candidates.items()
        },
        "checks": rows,
        "regressions": list(regressions.values()),
        "regression_count": len(regressions),
        "stress_30x30": {
            "input_sha256": digest(large),
            "foreground_cells": sum(cell != 0 for row in large for cell in row),
            "component_count_after_step_a": summary["component_count"],
            "largest_size_after_step_a": summary["largest_size"],
            "largest_bbox_after_step_a": summary["largest_bbox"],
            "source_largest_size": summary["source_largest_size"],
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "limits": (
            "Finite declared settings plus twenty-three plausible shortcuts on five seeds; "
            "this is bounded falsification evidence, not a universal uniqueness claim."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "racket_evaluations": report["racket_evaluations"],
                "regression_count": report["regression_count"],
                "stress_30x30": report["stress_30x30"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
