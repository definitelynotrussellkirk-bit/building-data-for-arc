"""Source-bound read-only audit of 55ff88a3cf8f; no private runner imports."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
PACKET = WORK.parent
TASK = "55ff88a3cf8f"
SOURCE = REPO / "generators" / TASK / "generator.py"
EXPECTED_SHA = "909cba5b96250d3c23c2cf5c3613a6213a24340a193d1a152bd4eb86067598bc"
PYTHON = "/workspace/scratch/6da8da487eb0/round2-venv/bin/python"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_gen():
    assert sha(SOURCE) == EXPECTED_SHA, "Audited source changed"
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_target55", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize(cells):
    top = min(r for r, c in cells)
    left = min(c for r, c in cells)
    return sorted((r-top, c-left) for r, c in cells)


def shape(grid):
    points = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 6}
    if not points:
        raise ValueError("no shape")
    start = min(points)
    points.remove(start)
    found = {start}
    stack = [start]
    while stack:
        r,c = stack.pop()
        for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if p in points:
                points.remove(p)
                found.add(p)
                stack.append(p)
    return normalize(found)


def controls(grid):
    return [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v in (1,2,3,4)]


def anchor(grid):
    return next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 8)


def predict(grid, *, minimum_control=False):
    candidates = controls(grid)
    code = min(v for r,c,v in candidates) if minimum_control else candidates[0][2]
    cells = shape(grid)
    for _ in range((code-1) % 4):
        cells = normalize([(c,-r) for r,c in cells])
    ar,ac = anchor(grid)
    output = [row[:] for row in grid]
    for r,c in cells:
        rr,cc = ar+r,ac+c
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            output[rr][cc] = 3
    return output


def geometry(grid):
    src = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 6}
    code = controls(grid)[0][2]
    cells = shape(grid)
    for _ in range((code-1) % 4):
        cells = normalize([(c,-r) for r,c in cells])
    ar,ac = anchor(grid)
    footprint = {(ar+r,ac+c) for r,c in cells}
    return {"stamp_fits": all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r,c in footprint),
            "stamp_overlaps_source": bool(footprint & src), "footprint": sorted(footprint)}


def main():
    gen = load_gen()
    from reviewer_support import canonical_pairs
    canonical = canonical_pairs(TASK, root=REPO)
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        original = next(p for p in canonical if p["variant"] == 0 and p["split"] == "train" and p["pair_index"] == 2)
        swapped = copy.deepcopy(original["input"])
        assert swapped[0][0] == 3 and swapped[9][12] == 4
        swapped[0][0], swapped[9][12] = 4,3

        search_count = 0
        for searched_seed in range(1000):
            candidate = gen.generate(searched_seed, 0, difficulty="easy")
            search_count += 1
            if gen.self_check(candidate):
                corrupt = candidate
                break
        else:
            raise AssertionError("No rejected default in bounded search")
        assert searched_seed == 131
        paint_trace = []
        original_paint = gen.paint_at
        def traced_paint(grid, top, left, cells, color):
            paint_trace.append({"top": top,"left": left,"normalized_shape": list(cells),
                                "color": color,"absolute_source_cells": [(top+r,left+c) for r,c in cells]})
            return original_paint(grid, top, left, cells, color)
        gen.paint_at = traced_paint
        try:
            traced_grid = gen.generate(131, 0, difficulty="easy")
        finally:
            gen.paint_at = original_paint
        assert traced_grid == corrupt and len(paint_trace) == 1
        ar,ac = anchor(corrupt)
        assert (ar,ac) in paint_trace[0]["absolute_source_cells"]
        code = controls(corrupt)[0][2]
        planned_footprint = [(ar+r,ac+c) for r,c in gen._rotk(paint_trace[0]["normalized_shape"], code-1)]
        assert (ar,ac) not in planned_footprint

        base = gen.generate(17, 0, difficulty="medium")
        override_cases = []
        for ov in ({"grid_h":22},{"grid_w":24},{"shape_size":7}):
            actual = gen.generate(17, 0, difficulty="medium", **ov)
            override_cases.append({"seed":17,"sample_index":0,"difficulty":"medium","overrides":ov,
                                   "equals_default":actual == base,"input_sha256":grid_sha(actual),
                                   "observed":{"grid_h":len(actual),"grid_w":len(actual[0]),"shape_size":sum(v==6 for row in actual for v in row)},
                                   "validator_messages":gen.self_check(actual)})
        examples = [
            {"name":"canonical_train_2","input":original["input"],"source":"canonical variant0/train2"},
            {"name":"swapped_control_order","input":swapped,"source":"canonical train2 with exactly two values swapped: (0,0)=4 and (9,12)=3"},
            {"name":"default_source_overwritten_by_anchor","input":corrupt,"source":"ordinary default draw","seed":131,"sample_index":0,"difficulty":"easy","overrides":{}},
            {"name":"ignored_override_baseline","input":base,"source":"ordinary default draw; same input for each of three tested legal overrides","seed":17,"sample_index":0,"difficulty":"medium","overrides":{}},
        ]
        for e in examples:
            e["validator_messages"] = gen.self_check(e["input"])
            e["geometry"] = geometry(e["input"])
            e["controls"] = controls(e["input"])
            e["shape_cells"] = [(r,c) for r,row in enumerate(e["input"]) for c,v in enumerate(row) if v==6]
        record = {"task_id":TASK,"generator_sha256":sha(SOURCE),"examples":examples,"override_cases":override_cases,
                  "corruption_trace":{"paint_calls":paint_trace,"selected_anchor":[ar,ac],"control":code,
                                      "anchor_was_original_source_cell":True,"anchor_is_in_planned_footprint":False,
                                      "planned_footprint_before_source_corruption":planned_footprint,
                                      "returned_source_cells":examples[2]["shape_cells"]},
                  "search_scope":{"description":"Stopped at first self_check-rejected ordinary easy draw while scanning seeds0..999,index0; found seed131 after132 draws.","tested_seeds_in_search":f"0..{searched_seed} inclusive","sample_index":0,"band":"easy","tested_count":search_count},
                  "canonical_validator_results":[{"variant":p["variant"],"split":p["split"],"pair_index":p["pair_index"],"messages":gen.self_check(p["input"])} for p in canonical]}
        (HERE/"input.json").write_text(json.dumps({"inputs":[e["input"] for e in examples]},indent=2)+"\n")
        (HERE/"evidence.json").write_text(json.dumps(record,indent=2)+"\n")
        print(json.dumps({"examples":[{"name":e["name"],"validator_messages":e["validator_messages"]} for e in examples],"override_cases":override_cases,"trace":record["corruption_trace"]},indent=2))
        return
    assert mode == "analyze"
    record = json.loads((HERE/"evidence.json").read_text())
    receipt = json.loads((HERE/"racket.json").read_text())
    assert receipt["task_id"] == TASK and receipt["generator_sha256"] == EXPECTED_SHA
    assert receipt["rule_hash_matches_catalog"]
    assert len(receipt["results"]) == len(record["examples"])
    for e,r in zip(record["examples"],receipt["results"],strict=True):
        assert e["input"] == r["input"] and r["valid_output"] and r["error"] is None
        assert predict(r["input"]) == r["output"]
        rival = predict(r["input"],minimum_control=True)
        e["actual_racket_output"] = r["output"]
        e["minimum_control_rival_output"] = rival
        e["rival_differences"] = [[rr,cc,r["output"][rr][cc],rival[rr][cc]] for rr in range(len(rival)) for cc in range(len(rival[0])) if r["output"][rr][cc] != rival[rr][cc]]
        e["input_sha256"] = r["input_sha256"]
        e["output_sha256"] = r["output_sha256"]
    record["canonical_minimum_control_rival_fit"] = {"matches":sum(predict(p["input"],minimum_control=True)==p["output"] for p in canonical),"total":len(canonical)}
    record["canonical_python_mirror_fit"] = {"matches":sum(predict(p["input"])==p["output"] for p in canonical),"total":len(canonical)}
    assert record["canonical_minimum_control_rival_fit"] == {"matches":5,"total":5}
    assert record["examples"][1]["rival_differences"]
    record["rule_hash"] = receipt["executed_rule_hash"]
    record["rule_text_sha256"] = receipt["rule_text_sha256"]
    record["racket_receipt_sha256"] = sha(HERE/"racket.json")
    record["reproducer_sha256"] = sha(Path(__file__))
    record["verification_commands"] = [
        {"argv":[PYTHON,"WORK/checks/audit/55ff88a3cf8f/probe.py","build"],"cwd":str(PACKET),"returncode":0},
        {"argv":[PYTHON,"review.py","run",PYTHON,"-m","arcpuzzles","apply",TASK,"--input","../checks/audit/55ff88a3cf8f/input.json","--out","../checks/audit/55ff88a3cf8f/racket.json","--timeout","180"],"cwd":str(PACKET),"environment":{"TMPDIR":"/dev/shm/arc-round2-tmp"},"effective_cwd":receipt["cwd"],"returncode":0},
        {"argv":[PYTHON,"WORK/checks/audit/55ff88a3cf8f/probe.py","analyze"],"cwd":str(PACKET),"returncode":0},
    ]
    (HERE/"evidence.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"canonical_minimum_control_rival_fit":record["canonical_minimum_control_rival_fit"],"canonical_python_mirror_fit":record["canonical_python_mirror_fit"],
                      "examples":[{"name":e["name"],"validator_messages":e["validator_messages"],"rival_difference_count":len(e["rival_differences"])} for e in record["examples"]],
                      "rule_hash":record["rule_hash"],"rule_text_sha256":record["rule_text_sha256"],"generator_sha256":record["generator_sha256"]},indent=2))


if __name__ == "__main__":
    main()
