"""Bounded, replayable count/size/rotation evidence for this prototype only."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_rank_metric_probe_subject", HERE / "prototype.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def run():
    from arc_repl.racket_bridge import RacketBridge
    requests = [(seed, demos, queries) for seed in (0, 17)
                for demos in (2, 3, 6) for queries in (1, 4)]
    requests += [(2, 2, 4), (83, 4, 2), (91, 5, 3)]
    rows, failures, boundaries, rotations = [], [], [], []
    matched = {}
    with RacketBridge(timeout=15) as bridge:
        for seed, demos, queries in requests:
            for metric in p.METRICS:
                try:
                    episode = p.generate_episode(seed, metric=metric, n_demo=demos,
                                                 n_query=queries, bridge=bridge)
                    raw_inputs = p.json_bytes([[x["input"] for x in episode[split]]
                                               for split in ("train", "test")])
                    key = (seed, demos, queries)
                    if key in matched and matched[key] != raw_inputs:
                        raise ValueError("inputs differ between settings")
                    matched[key] = raw_inputs
                    rows.append({"seed": seed, "metric": metric, "demos": demos,
                                 "queries": queries, "teaching_attempts": episode["sampling"]["teaching_attempts"],
                                 "public_id": p.public_challenge_id(episode),
                                 "survivors": episode["certificate"]["survivors"],
                                 "query_blue_counts": [sum(map(len, p.blue_objects(x["input"])))
                                                       for x in episode["test"]],
                                 "query_bbox_ties": [len({p.score(o, "bbox_area") for o in p.blue_objects(x["input"])}) < 3
                                                    for x in episode["test"]]})
                except Exception as exc:
                    failures.append({"seed": seed, "metric": metric, "demos": demos,
                                     "queries": queries, "error": f"{type(exc).__name__}: {exc}"})
        for height, width in ((10, 10), (10, 30), (30, 10), (30, 30)):
            grid = p.sample_input(51, index=9, height=height, width=width)
            objects = p.blue_objects(grid)
            outputs = {}
            for metric in p.METRICS:
                actual = p.racket_label(bridge, p.materialize_program(metric=metric), grid)
                if actual != p.transform(grid, metric=metric):
                    raise ValueError("boundary Racket mismatch")
                outputs[metric] = p.sha(p.json_bytes(actual))
            occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            boundaries.append({"shape": [height, width], "blue_sizes": list(map(len, objects)),
                               "blue_bbox_areas": [p.score(o, "bbox_area") for o in objects],
                               "nonzero_cells": len(occupied),
                               "occupied_span": [max(r for r, _ in occupied) - min(r for r, _ in occupied) + 1,
                                                 max(c for _, c in occupied) - min(c for _, c in occupied) + 1],
                               "input_sha256": p.sha(p.json_bytes(grid)), "output_sha256": outputs})
        base = p.sample_input(2, index=201, height=16, width=20)
        for code in range(8):
            grid = p._sampler.rotate_grid(base, code)
            for metric in p.METRICS:
                actual = p.racket_label(bridge, p.materialize_program(metric=metric), grid)
                if actual != p.transform(grid, metric=metric):
                    raise ValueError("rotated tied-area Racket mismatch")
                rotations.append({"code": code, "metric": metric,
                                  "input_sha256": p.sha(p.json_bytes(grid)),
                                  "output_sha256": p.sha(p.json_bytes(actual))})
        identity = p.runtime_identity(bridge)
    return {"schema": "blue-rank-bounded-probe-v1", "status": "passed" if not failures else "failed",
            "source_bindings": p.source_bindings(), "racket": identity,
            "requests": 2 * len(requests), "successful_episodes": len(rows), "failures": failures,
            "labeled_pair_slots": sum(r["demos"] + r["queries"] for r in rows),
            "parameter_executions": 2 * sum(r["demos"] + r["queries"] for r in rows),
            "matched_setting_requests": len(matched), "rows": rows,
            "size_boundary_labels": 2 * len(boundaries), "boundaries": boundaries,
            "rotated_tie_labels": len(rotations), "rotations": rotations,
            "limits": "Five fixed seeds; finite declared rivals; no full canonical battery or measured training gain",
            "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "requests", "successful_episodes",
          "failures", "labeled_pair_slots", "parameter_executions", "size_boundary_labels", "rotated_tie_labels")}))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
