"""Bounded protected-Racket parity, teaching and sampler audit for this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arcpuzzles.parametric_worker import _real_evaluator


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
_spec = importlib.util.spec_from_file_location("_audit_bbox_threshold", HOME / "prototype.py")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def run(out):
    out = Path(out)
    if out.exists():
        raise ValueError("Choose a new audit output directory")
    out.mkdir(parents=True)
    start = time.monotonic()
    report = {"schema":"5c9fd75979d1-threshold-audit-v1", "task_id":p.TASK_ID,
        "status":"running", "source_sha256":{name:_sha((HOME/name).read_bytes()) for name in
            ("prototype.py","adapter.py","canonical.rkt","promotion.json","audit.py")},
        "scope":"Finite declared settings plus six named shortcut rules; no universal uniqueness claim.",
        "sampler":{"attempts":0,"successes":0,"failures":[]},
        "lessons":[], "racket_evaluations":0, "programs":{}, "errors":[]}
    witnesses = []
    bridge = None
    try:
        # Exercise every supported demo count. Query counts 1 and 4 are also
        # covered by behavior tests; this retained sampler census uses four.
        for seed in range(8):
            for demos in range(2,7):
                for cutoff in p.CUTOFFS:
                    report["sampler"]["attempts"] += 1
                    try:
                        episode = p.generate(seed,{"min_bbox_area":cutoff},demos,4)
                        pairs = episode["train"]+episode["test"]
                        assert len({json.dumps(v["input"]) for v in pairs}) == demos+4
                        for other in p.CUTOFFS:
                            if other != cutoff:
                                assert any(p.analyze(v["input"],other)["output"] != v["output"] for v in episode["train"])
                        report["sampler"]["successes"] += 1
                    except Exception as exc:
                        report["sampler"]["failures"].append({"seed":seed,"demos":demos,
                            "cutoff":cutoff,"error":f"{type(exc).__name__}: {exc}"})
        if report["sampler"]["failures"]:
            raise AssertionError("Bounded sampler failures; see sampler.failures")

        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        report["racket"] = identity

        def execute(source, grid):
            key = _sha(source.encode())
            report["programs"][key] = source
            report["racket_evaluations"] += 1
            return apply(source, grid)

        for seed in (0,17):
            for demos in (2,6):
                for cutoff in p.CUTOFFS:
                    settings = {"min_bbox_area":cutoff}
                    episode = p.generate(seed,settings,demos,4)
                    chosen = p.program(settings)
                    row = {"seed":seed,"settings":settings,"demos":demos,"queries":4,
                        "input_shapes":[[len(v["input"]),len(v["input"][0])] for v in episode["train"]+episode["test"]],
                        "declared_setting_survivors":[], "rivals":[]}
                    for pair in episode["train"]+episode["test"]:
                        assert execute(chosen,pair["input"]) == pair["output"], "Python/Racket label mismatch"
                    for other in p.CUTOFFS:
                        if other == cutoff:
                            row["declared_setting_survivors"].append(other)
                            continue
                        source = p.program({"min_bbox_area":other})
                        results = [execute(source,v["input"]) for v in episode["train"]]
                        if all(result == pair["output"] for result,pair in zip(results,episode["train"])):
                            row["declared_setting_survivors"].append(other)
                    assert row["declared_setting_survivors"] == [cutoff]
                    for name in p.RIVAL_NAMES:
                        source = p.rival_program(settings,name)
                        predictions = [execute(source,v["input"]) for v in episode["train"]]
                        mismatches = [i for i,(a,b) in enumerate(zip(predictions,episode["train"])) if a != b["output"]]
                        record = {"name":name,"survives_demonstrations":not mismatches}
                        if mismatches:
                            record["eliminating_demo_indices"] = mismatches
                            if seed == 0 and demos == 2:
                                i = mismatches[0]
                                witnesses.append({"settings":settings,"rival":name,"input":episode["train"][i]["input"],
                                    "program_sha256":_sha(chosen.encode()),"output":episode["train"][i]["output"],
                                    "rival_program_sha256":_sha(source.encode()),"rival_output":predictions[i]})
                        else:
                            matches = [execute(source,v["input"]) == v["output"] for v in episode["test"]]
                            record["query_agreement"] = matches
                            assert all(matches), f"Untaught query-changing shortcut: {name}"
                            if cutoff == 2 and name == "pixel_count":
                                record["reason"] = "Equivalent on 4-connected components at strict cutoff 2."
                        row["rivals"].append(record)
                    report["lessons"].append(row)

        # Small semantic witnesses separate bbox area from cell count without
        # relying on the scene constructor or a Python-only gold label.
        compact = [
            (4, [[1,1,1,0,2,2,2],[1,1,1,0,2,0,0],[1,1,1,0,0,0,0]], [[2,0,1],[0,0,1]]),
            (8, [[1,1,1,0,0,2,0],[1,1,1,0,2,2,2],[1,1,1,0,0,2,0]], [[2,0,1]]),
        ]
        report["compact_area_witnesses"] = []
        for cutoff,grid,expected in compact:
            settings = {"min_bbox_area":cutoff}
            chosen, rival = p.program(settings),p.rival_program(settings,"pixel_count")
            gold, wrong = execute(chosen,grid),execute(rival,grid)
            assert gold == expected and wrong == [[1]]
            report["compact_area_witnesses"].append({"settings":settings,"input":grid,
                "program_sha256":_sha(chosen.encode()),"output":gold,
                "rival_program_sha256":_sha(rival.encode()),"rival_output":wrong})
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if bridge is not None:
            bridge.close()
        report["elapsed_seconds"] = round(time.monotonic()-start,3)
        report["witness_count"] = len(witnesses)
        (out/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        (out/"shortcut-witnesses.json").write_text(json.dumps(witnesses,sort_keys=True,indent=2)+"\n")
    return {"status":report["status"],"sampler":report["sampler"],
        "protected_racket":report.get("racket",{}).get("protected"),
        "racket_evaluations":report["racket_evaluations"],"lessons":len(report["lessons"]),
        "witnesses":len(witnesses),"errors":report["errors"],"out":str(out)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
