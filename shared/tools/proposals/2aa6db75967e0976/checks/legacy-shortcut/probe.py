"""One source-bound legacy lesson, public Racket labels, explicit shortcuts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import types

from reviewer_support import find_root
from puzzle_generators.helpers.selfcheck import components

ORIGIN_SHA256 = "b377352acbc2c53089f29f91ddd2d5f3e79d45411ea3264a0bc5f2cd86acb224"
EXPECTED_EXECUTION_SOURCE = "4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b"
RULE_HASH = "5af80c67d390"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def marker_neighbours(grid):
    objects = components(grid)
    marker, = [obj for obj in objects if obj["color"] == 1]
    (mr, mc), = marker["cells"]
    neighbours = [obj for obj in objects if obj["color"] != 1 and any(
        abs(r-mr) + abs(c-mc) == 1 for r,c in obj["cells"])]
    return (mr,mc), neighbours


def crop(obj):
    cells=set(obj["cells"])
    r0,c0=min(r for r,c in cells),min(c for r,c in cells)
    r1,c1=max(r for r,c in cells),max(c for r,c in cells)
    return [[8 if (r,c) in cells else 0 for c in range(c0,c1+1)] for r in range(r0,r1+1)]


def predictions(grid):
    (mr,mc), near = marker_neighbours(grid)
    first = min(near, key=lambda obj:min(obj["cells"]))
    above, = [obj for obj in near if (mr-1,mc) in obj["cells"]]
    return {"first_marker_neighbour": crop(first), "above_marker_neighbour": crop(above)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin",type=Path,required=True)
    args=parser.parse_args()
    root=find_root(__file__)
    out=Path(__file__).resolve().parent
    origin=args.origin.resolve()
    body=origin.read_bytes()
    assert sha(body) == ORIGIN_SHA256, "archived origin source hash differs"
    assert not (out/"inputs.json").exists(), "use a fresh evidence directory"
    archived=types.ModuleType("legacy_generator_b377352acbc2")
    archived.__file__=str(origin)
    sys.modules[archived.__name__]=archived
    exec(compile(body,str(origin),"exec"),archived.__dict__)
    cases=[]
    for index in range(5):
        grid=archived.generate(0,index,difficulty="easy")
        cases.append({"pair_index":index,"split":"train" if index < 4 else "test",
                      "origin_args":{"seed":0,"sample_index":index,"difficulty":"easy","overrides":{}},
                      "input":grid,"input_sha256_compact_json":grid_sha(grid),
                      "shortcut_predictions":predictions(grid)})
    inputs=[case["input"] for case in cases]
    write_json(out/"inputs.json",{"inputs":inputs})
    origin_record={"source_path":"checks/baseline-source/generator.py","source_sha256":ORIGIN_SHA256,
                   "generator_version":archived.VERSION,"sampler":"archived generate, exactly five ordinary consecutive calls",
                   "cases":cases,"inputs_file_sha256":sha((out/"inputs.json").read_bytes())}
    write_json(out/"input-origin.json",origin_record)
    argv=[sys.executable,"-m","arcpuzzles","apply","23a0c42b8a1c","--input",
          str(out/"inputs.json"),"--out",str(out/"public-apply-result.json")]
    start=time.monotonic()
    process=subprocess.run(argv,cwd=root,capture_output=True,text=True)
    (out/"apply.stdout.txt").write_text(process.stdout)
    (out/"apply.stderr.txt").write_text(process.stderr)
    write_json(out/"apply-command.json",{"argv":argv,"cwd":str(root),"exit_code":process.returncode,
        "elapsed_seconds":round(time.monotonic()-start,3),"stdout":"checks/legacy-shortcut/apply.stdout.txt",
        "stderr":"checks/legacy-shortcut/apply.stderr.txt","result":"checks/legacy-shortcut/public-apply-result.json",
        "inherited_runtime":"verified RACKET_PATH/PYTHONPATH from outer public review.py run wrapper"})
    if process.returncode != 0:
        raise RuntimeError("public apply failed; retain its receipt and outputs")
    applied=json.loads((out/"public-apply-result.json").read_text())
    assert applied["generator_sha256"] == EXPECTED_EXECUTION_SOURCE
    assert applied["executed_rule_hash"] == RULE_HASH and applied["rule_hash_matches_catalog"]
    assert len(applied["results"]) == 5
    pairs=[]
    for case,label in zip(cases,applied["results"],strict=True):
        assert label["input"] == case["input"] and label["error"] is None and label["valid_output"]
        pairs.append({"input":case["input"],"output":label["output"]})
    shortcuts=[]
    descriptions={
        "first_marker_neighbour":"Select the cardinal marker-neighbour whose top-left occupied cell is earliest in row-major order; crop only its cells and recolour to 8; ignore size.",
        "above_marker_neighbour":"Select the object containing the cell directly north of the single-cell marker; crop only its cells and recolour to 8; ignore size. Undefined if that object is absent.",
    }
    for name,description in descriptions.items():
        refuted=[i for i,(case,pair) in enumerate(zip(cases,pairs,strict=True))
                 if case["shortcut_predictions"][name] != pair["output"]]
        train_refuted=[i for i in refuted if i < 4]
        query_correct=4 not in refuted
        shortcuts.append({"name":name,"definition":description,"demonstration_refutation_indices":train_refuted,
                          "all_pair_refutation_indices":refuted,"demonstrations_fit":4-len(train_refuted),
                          "query_correct":query_correct,"status":"survived_all" if not refuted else "refuted",
                          "proposed_coverage_diagnostic_would_flag":len(train_refuted)==0,
                          "query_ambiguity":not train_refuted and not query_correct})
    report={"schema":"legacy-shortcut-lesson-evidence-v1","status":"completed",
            "task_id":"23a0c42b8a1c","seed":0,"sample_indices":list(range(5)),"difficulty":"easy",
            "n_train":4,"n_test":1,"overrides":{},
            "input_origin_generator_sha256":ORIGIN_SHA256,
            "public_execution_selected_generator_sha256":applied["generator_sha256"],
            "canonical_rule_hash":applied["executed_rule_hash"],
            "rule_text_sha256":applied["rule_text_sha256"],
            "distinct_inputs":len({grid_sha(p["input"]) for p in pairs}),
            "distinct_outputs":len({grid_sha(p["output"]) for p in pairs}),
            "shortcuts":shortcuts,"probe_sha256":sha(Path(__file__).read_bytes()),
            "evidence":{"origin":"checks/legacy-shortcut/input-origin.json",
                        "public_apply":"checks/legacy-shortcut/public-apply-result.json",
                        "public_apply_sha256":sha((out/"public-apply-result.json").read_bytes()),
                        "public_apply_command":"checks/legacy-shortcut/apply-command.json"},
            "interpretation":"Both shortcut candidates can answer this whole legacy lesson correctly without being refuted by its demonstrations. A proposed minimum-refutation diagnostic would flag absent shortcut coverage after those rivals are declared; this is not measured query ambiguity.",
            "limitations":["One ordinary archived-generator lesson, five fixed calls, no all-seed claim.",
                           "No Qwen model or model policy was run; this measures data shortcut coverage only.",
                           "The shortcut-coverage diagnostic is a proposal, not an implemented production gate.",
                           "Public apply labels saved legacy-origin inputs using the unchanged canonical Racket; its current selected-generator hash is not their sampling origin."]}
    write_json(out/"public-challenge.json",{"train":pairs[:4],"test":[{"input":pairs[4]["input"]}]})
    write_json(out/"private-lesson.json",{"train":pairs[:4],"test":pairs[4:],"origin":origin_record})
    write_json(out/"report.json",report)
    print(json.dumps({"status":report["status"],"input_origin_generator_sha256":ORIGIN_SHA256,
                      "public_execution_selected_generator_sha256":applied["generator_sha256"],
                      "distinct_inputs":report["distinct_inputs"],"distinct_outputs":report["distinct_outputs"],
                      "shortcuts":shortcuts},indent=2))


if __name__ == "__main__":
    main()
