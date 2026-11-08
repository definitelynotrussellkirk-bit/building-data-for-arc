"""Bounded protected-Racket self-review for the 03478139591b family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "03478139591b"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_03478139591b", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _rule(body: str) -> str:
    return """(rule! (lambda (g)
  (let* ((color (find-first (lambda (c) (!= c 0)) (grid-colors g)))
         (mapped (casev color (hash 3 1 5 4 8 2) color))
         (intermediate (cellmap g (r c v) (if (!= v 0) 0 mapped)))
         (regions (objects intermediate 0)))
    %s)))""" % body


def rivals(proto):
    return {
        "canonical": proto.program({"finish": "canonical"}),
        "sequential": proto.program({"finish": "mark_largest_boundary"}),
        "first_region_boundary": _rule(
            "(recolor-cells intermediate (obj-boundary-cells (first regions)) color)"
        ),
        "smallest_region_boundary": _rule(
            "(let ((chosen (pick-min regions obj-size))) "
            "(recolor-cells intermediate (obj-boundary-cells chosen) color))"
        ),
        "largest_region_whole": _rule(
            "(let ((chosen (pick-max regions obj-size))) "
            "(recolor-cells intermediate (obj-cells chosen) color))"
        ),
        "largest_region_bbox": _rule(
            "(let ((chosen (pick-max regions obj-size))) "
            "(draw-rect-filled intermediate (obj-r1 chosen) (obj-c1 chosen) "
            "(obj-r2 chosen) (obj-c2 chosen) color))"
        ),
        "fixed_color_boundary": _rule(
            "(let ((chosen (pick-max regions obj-size))) "
            "(recolor-cells intermediate (obj-boundary-cells chosen) 9))"
        ),
        "skip_complement": """(rule! (lambda (g)
  (let* ((color (find-first (lambda (c) (!= c 0)) (grid-colors g)))
         (regions (objects g 0))
         (chosen (pick-max regions obj-size)))
    (recolor-cells g (obj-boundary-cells chosen) color))))""",
    }


def digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


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
            for setting_name in ("canonical", "mark_largest_boundary"):
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
    expected_regressions = len(seeds) * 0  # document that one witness per rival/setting is retained, not per seed
    large = proto.generate(5, {"finish": "mark_largest_boundary"}, 2, 4)["test"][-1]["input"]
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
