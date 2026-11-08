"""Bounded protected-Racket shortcut audit for the e06cc4c752b2 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "e06cc4c752b2"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("_probe_e06cc4c752b2", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_EXPAND_PREFIX = """(rule! (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define intermediate
    (for*/fold ((out g)) ((r (in-range (rows g))) (c (in-range (cols g))))
      (let ((v (at g r c)))
        (if (and (not (= v 0))
                 (all? (lambda (d)
                         (let ((nr (+ r (first d))) (nc (+ c (second d))))
                           (not (and (in-bounds? nr nc (rows g) (cols g))
                                     (not (= (at g nr nc) 0)))))) dirs4))
            (let* ((left (if (and (>= (- c 1) 0) (= (at out r (- c 1)) 0))
                             (set-cell out r (- c 1) v) out))
                   (right (if (and (< (+ c 1) (cols g)) (= (at left r (+ c 1)) 0))
                              (set-cell left r (+ c 1) v) left))) right)
            out))))
  (define regions (objects intermediate 0))
  %s))"""


def _expanded_rule(body):
    return _EXPAND_PREFIX % body


def rivals(proto):
    return {
        "canonical": proto.program({"finish": "canonical"}),
        "sequential": proto.program({"finish": "fill_largest_bbox"}),
        "first_component_bbox": _expanded_rule(
            "(let ((chosen (first regions))) (draw-rect-filled intermediate "
            "(obj-r1 chosen) (obj-c1 chosen) (obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "smallest_component_bbox": _expanded_rule(
            "(let ((chosen (pick-min regions obj-size))) (draw-rect-filled intermediate "
            "(obj-r1 chosen) (obj-c1 chosen) (obj-r2 chosen) (obj-c2 chosen) 9))"
        ),
        "largest_component_only": _expanded_rule(
            "(let ((chosen (pick-max regions obj-size))) "
            "(recolor-cells intermediate (obj-cells chosen) 9))"
        ),
        "largest_bbox_wrong_color": _expanded_rule(
            "(let ((chosen (pick-max regions obj-size))) (draw-rect-filled intermediate "
            "(obj-r1 chosen) (obj-c1 chosen) (obj-r2 chosen) (obj-c2 chosen) 8))"
        ),
        "skip_expansion": """(rule! (let* ((regions (objects g 0))
                                      (chosen (pick-max regions obj-size)))
  (draw-rect-filled g (obj-r1 chosen) (obj-c1 chosen)
                    (obj-r2 chosen) (obj-c2 chosen) 9)))""",
        "vertical_expansion_then_bbox": """(rule! (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define intermediate
    (for*/fold ((out g)) ((r (in-range (rows g))) (c (in-range (cols g))))
      (let ((v (at g r c)))
        (if (and (not (= v 0))
                 (all? (lambda (d)
                         (let ((nr (+ r (first d))) (nc (+ c (second d))))
                           (not (and (in-bounds? nr nc (rows g) (cols g))
                                     (not (= (at g nr nc) 0)))))) dirs4))
            (let* ((up (if (and (>= (- r 1) 0) (= (at out (- r 1) c) 0))
                           (set-cell out (- r 1) c v) out))
                   (down (if (and (< (+ r 1) (rows g)) (= (at up (+ r 1) c) 0))
                             (set-cell up (+ r 1) c v) up))) down)
            out))))
  (define chosen (pick-max (objects intermediate 0) obj-size))
  (draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen)
                    (obj-r2 chosen) (obj-c2 chosen) 9)))""",
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
                    for name, source in candidates.items():
                        outputs = [apply(source, pair["input"]) for pair in episode["train"]]
                        evaluations += len(outputs)
                        if outputs == [pair["output"] for pair in episode["train"]]:
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
                    rows.append({
                        "setting": setting_name,
                        "seed": seed,
                        "survivors": survivors,
                        "input_hashes": [proto.digest(pair["input"]) for pair in episode["train"]],
                        "query_hashes": [proto.digest(pair["input"]) for pair in episode["test"]],
                    })
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
            "marker_count": sum(cell != 0 for row in large for cell in row),
            "component_count_after_step_a": summary["component_count"],
            "largest_size_after_step_a": summary["largest_size"],
            "largest_bbox_after_step_a": summary["largest_bbox"],
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "limits": "Finite declared settings plus six plausible shortcuts on three seeds; no universal uniqueness claim.",
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
