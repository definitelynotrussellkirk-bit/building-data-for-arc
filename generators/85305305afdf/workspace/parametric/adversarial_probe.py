"""Bounded protected-Racket self-review for the 85305305afdf family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "85305305afdf"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_85305305afdf", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_SHIFT = """(define (shift-terminal-cells grid)
    (for*/fold ((out (empty-grid (rows grid) (cols grid) 0)))
               ((r (in-range (rows grid))) (c (in-range (cols grid))))
      (let ((v (at grid r c)))
        (cond ((= v 0) out)
              ((and (< (+ c 1) (cols grid)) (= (at grid r (+ c 1)) 0))
               (if (= (at out r (+ c 1)) 0) (set-cell out r (+ c 1) v) out))
              (else (if (= (at out r c) 0) (set-cell out r c v) out))))))"""


def _after_shift(body):
    return f"""(rule! (let ((dummy 0))
  {_SHIFT}
  (let* ((intermediate (shift-terminal-cells g))
         (regions (objects intermediate 0)))
    {body})))"""


def rivals(proto):
    return {
        "canonical": proto.program({"finish": "canonical"}),
        "sequential": proto.program({"finish": "fill_largest_bbox"}),
        "identity": "(rule! (lambda (g) g))",
        "all_zero": "(rule! (lambda (g) (empty-grid (rows g) (cols g) 0)))",
        "move_every_nonzero": """(rule! (let ((dummy 0))
  (for*/fold ((out (empty-grid (rows g) (cols g) 0)))
             ((r (in-range (rows g))) (c (in-range (cols g))))
    (let ((v (at g r c)))
      (if (= v 0) out
          (let ((cc (if (< (+ c 1) (cols g)) (+ c 1) c)))
            (if (= (at out r cc) 0) (set-cell out r cc v) out)))))))""",
        "move_only_isolated": """(rule! (let ((dummy 0))
  (for*/fold ((out (empty-grid (rows g) (cols g) 0)))
             ((r (in-range (rows g))) (c (in-range (cols g))))
    (let ((v (at g r c)))
      (if (= v 0) out
          (let* ((left-empty (or (= c 0) (= (at g r (- c 1)) 0)))
                 (right-empty (and (< (+ c 1) (cols g)) (= (at g r (+ c 1)) 0)))
                 (cc (if (and left-empty right-empty) (+ c 1) c)))
            (if (= (at out r cc) 0) (set-cell out r cc v) out)))))))""",
        "first_region_bbox": _after_shift(
            "(let ((chosen (first regions))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "smallest_region_bbox": _after_shift(
            "(let ((chosen (pick-min regions obj-size))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_region_whole": _after_shift(
            "(let ((chosen (pick-max regions obj-size))) "
            "(recolor-cells intermediate (obj-cells chosen) 9))"
        ),
        "fixed_top_left": _after_shift(
            "(draw-rect-filled intermediate 0 0 1 1 9)"
        ),
        "skip_shift": """(rule! (let ((dummy 0))
  (let* ((regions (objects g 0))
         (chosen (pick-max regions obj-size)))
    (draw-rect-filled g (obj-r1 chosen) (obj-c1 chosen)
                      (obj-r2 chosen) (obj-c2 chosen) 9))))""",
    }


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def build_report(seeds=(0, 17, 91)):
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
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "limits": "Finite declared settings plus nine plausible shortcuts on three seeds; no universal uniqueness claim.",
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
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["racket_evaluations"],
        "regression_count": report["regression_count"],
        "stress_30x30": report["stress_30x30"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
