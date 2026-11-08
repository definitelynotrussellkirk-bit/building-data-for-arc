"""Replay a fixed-frame-area shortcut against the supported two-demo prefix."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2] / "repo"
TASK_ID = "bedcbc1cb6fb"
HOME = ROOT / "generators" / TASK_ID / "workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(out):
    if out.exists():
        raise FileExistsError(out)
    paths = [HOME.parent.parent / "generator.py", HOME / "prototype.py", HOME / "adapter.py",
             HOME / "rivals.py", HOME / "promotion.json", HOME / "self_audit.py",
             HOME / "evidence/manifest.json", ROOT / "src/arcpuzzles/parametric_worker.py"]
    source = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}
    with _local_imports(RUNTIME, HOME):
        proto = load("_bed_peer_prototype", HOME / "prototype.py")
        rivals = load("_bed_peer_rivals", HOME / "rivals.py")
        current_status = Catalog(ROOT).parametric_status(TASK_ID)
        selected = proto.program({"rule": "ring_area_fill"})
        marker = "(define key-area (count-center after-a))"
        if selected.count(marker) != 1:
            raise AssertionError("Expected exact input-dependent area marker")
        candidate = selected.replace(marker,
            "(define key-area (* (- 13 (* 2 (length palette))) (- 14 (* 2 (length palette)))))")
        pool = proto.sample_inputs(0, demos=3, queries=4)
        demos, query, distinguishing = pool["train"][:2], pool["test"][0], pool["train"][2]
        if len({json.dumps(g) for g in demos + [query, distinguishing]}) != 4:
            raise AssertionError("Demonstrations, query and extra demo must be distinct")
        def mirror(grid, wrong=False):
            info = rivals.analyze(grid)
            output = rivals.predict(grid, "rings")
            count = (13 - 2 * len(info["markerlist"])) * (14 - 2 * len(info["markerlist"]))
            if not wrong:
                top, left, bottom, right = info["innerbbox"]
                count = sum(output[r][c] == info["markerlist"][-1]
                            for r in range(top, bottom + 1) for c in range(left, right + 1))
            matches = [key for key in info["keys"] if key["area"] == count]
            if matches:
                top, left, bottom, right = matches[0]["bbox"]
                for r in range(top, bottom + 1):
                    for c in range(left, right + 1):
                        output[r][c] = info["markerlist"][-1]
            return output
        apply, identity, bridge = _real_evaluator(RUNTIME)
        executions = []
        try:
            def execute(program, grid, wrong, split, index):
                executions.append({"split": split, "index": index, "program": "fixed_frame_rival" if wrong else "intended"})
                output = _grid(apply(program, grid))
                if output != mirror(grid, wrong):
                    raise AssertionError("Racket/Python interpretation mismatch")
                return output
            # Fit the complete visible two-demo prefix before query execution.
            demo_truth = [execute(selected, grid, False, "train", i) for i, grid in enumerate(demos)]
            demo_rival = [execute(candidate, grid, True, "train", i) for i, grid in enumerate(demos)]
            if demo_truth != demo_rival:
                raise AssertionError("Fixed-frame rival does not fit both visible demonstrations")
            query_truth = execute(selected, query, False, "test", 0)
            query_rival = execute(candidate, query, True, "test", 0)
            if query_truth == query_rival:
                raise AssertionError("No query disagreement")
            third_truth = execute(selected, distinguishing, False, "extra_demo", 2)
            third_rival = execute(candidate, distinguishing, True, "extra_demo", 2)
            if third_truth == third_rival:
                raise AssertionError("Expected default third demo to refute fixed geometry")
        finally:
            bridge.close()
    report = {
        "schema": "bedcbc1cb6fb-fixed-frame-two-demo-counterexample-v1",
        "status": "reproduced_supported_prefix_underidentification", "seed": 0,
        "settings": {"rule": "ring_area_fill"}, "supported_demo_count": 2,
        "candidate": "Fill rings normally; choose the external object using (13-2*k)*(14-2*k), where k is diagonal marker count, instead of measuring the current frame's center.",
        "scope": "Two demonstrations are supported by the accepted parametric adapter. This finite novel rival is outside its retained named-rival selection/audit. It is not a canonical-production validator defect or a universal ambiguity claim.",
        "source_files_sha256": source, "probe_sha256": sha(Path(__file__).read_bytes()),
        "canonical_rule_hash": "7e5bd081e0cd",
        "native_status_at_review": {key: current_status.get(key) for key in ("status", "acceptance_sha256", "qualification_id", "training_admitted")},
        "programs": {"intended": {"source": selected, "sha256": sha(selected.encode())},
                     "fixed_frame_rival": {"source": candidate, "sha256": sha(candidate.encode())}},
        "racket": identity, "execution_order": executions, "racket_evaluations": len(executions),
        "demo_fit_frozen_before_query": True,
        "train": [{"input": grid, "output": demo_truth[i], "rival_output": demo_rival[i],
                   "facts": rivals.analyze(grid)} for i, grid in enumerate(demos)],
        "test": [{"input": query, "output": query_truth, "rival_output": query_rival,
                  "facts": rivals.analyze(query)}],
        "query_difference_cells": sum(a != b for ra, rb in zip(query_truth, query_rival) for a, b in zip(ra, rb)),
        "default_three_demo_mitigation": {"extra_demo": {"input": distinguishing, "output": third_truth,
                                                          "rival_output": third_rival, "facts": rivals.analyze(distinguishing)},
                                          "refuted": True, "original_query_remains_novel": True},
        "recommended_action": "Add fixed-frame-area inference to the finite rival set and change the two-demo construction to vary frame dimensions as well as marker count, then qualify changed source. Until then, use at least the existing default three demonstrations for this particular rival.",
        "production_changed": False, "parametric_source_changed": False, "training_admitted": False,
    }
    if source != {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}:
        raise AssertionError("Peer source changed during probe")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "racket_evaluations": len(executions),
                      "query_difference_cells": report["query_difference_cells"],
                      "default_third_demo_refutes": True, "report": str(out)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
