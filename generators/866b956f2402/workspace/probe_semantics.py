"""Reproduce source-bound gravity witnesses and finite rival evidence via public Racket apply.

Run through review.py run PY generators/866b956f2402/workspace/probe_semantics.py
--out ../checks/independent-v2 --baseline ../checks/generator-baseline.py.
No private solve labels are read. All labels below are authoring evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

for parent in Path(__file__).resolve().parents:
    support = parent / "shared/runtime"
    if (support / "reviewer_support.py").is_file():
        sys.path.insert(0, str(support))
        break
from reviewer_support import canonical_pairs, find_root

TASK = "866b956f2402"
ROOT = find_root(__file__)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independently_settle(grid):
    columns = []
    for column in zip(*grid):
        result = []
        buffer = []
        for value in (*column, 8):
            if value == 8:
                values = [v for v in buffer if v != 0]
                result.extend([0] * (len(buffer) - len(values)) + values)
                result.append(8)
                buffer = []
            else:
                buffer.append(value)
        columns.append(result[:-1])
    return [list(row) for row in zip(*columns)]


def measures(grid):
    cols = list(zip(*grid))
    capacities = []
    tail_moves = False
    for col in cols:
        parts = []
        part = []
        for value in (*col, 8):
            if value == 8:
                parts.append(part)
                part = []
            else:
                part.append(value)
        capacities.extend(sum(v != 0 for v in part) for part in parts)
        if 8 in col:
            tail = list(col[len(col) - 1 - list(reversed(col)).index(8) + 1:])
            values = [v for v in tail if v]
            tail_moves |= tail != [0] * (len(tail) - len(values)) + values
    return {
        "wall_free": any(8 not in col and any(col) for col in cols),
        "color_one": any(1 in col for col in cols),
        "many_walls": any(col.count(8) > 2 for col in cols),
        "many_columns": sum(any(col) for col in cols) > 3,
        "many_pebbles": max(capacities, default=0) > 3,
        "moving_bottom_tail": tail_moves,
    }


def fixture(name, columns, expected, height=8, width=7, teaching=True):
    inp = [[0] * width for _ in range(height)]
    out = [[0] * width for _ in range(height)]
    for c, values in columns.items():
        assert len(values) == height
        for r, value in enumerate(values):
            inp[r][c] = value
    for c, values in expected.items():
        assert len(values) == height
        for r, value in enumerate(values):
            out[r][c] = value
    return {"name": name, "kind": "manual", "input": inp,
            "expected": out, "teaching_expected": teaching}


def fixtures():
    return [
        fixture("wall_free_without_one",
                {1:[0,2,0,3,0,0,0,0],4:[0,4,0,8,0,0,0,0]},
                {1:[0,0,0,0,0,0,2,3],4:[0,0,4,8,0,0,0,0]}),
        fixture("one_without_wall_free",
                {2:[0,2,0,1,0,8,0,0]}, {2:[0,0,0,2,1,8,0,0]}),
        fixture("bottom_tail",
                {2:[0,2,0,8,3,0,4,0]}, {2:[0,0,2,8,0,0,3,4]}),
        fixture("fourth_segment",
                {2:[0,2,8,0,0,8,0,0,8,3,0,0]},
                {2:[0,2,8,0,0,8,0,0,8,0,0,3]},height=12),
        fixture("four_pebbles_repeated_nonmonotone",
                {2:[7,2,7,3,0,0,8,0]}, {2:[0,0,7,2,7,3,8,0]}),
        fixture("four_populated_columns",
                {c:[p,0,0,0,8,0,0,0] for c,p in zip(range(1,5),range(2,6))},
                {c:[0,0,0,p,8,0,0,0] for c,p in zip(range(1,5),range(2,6))}),
        fixture("adjacent_cells_separate",
                {2:[0,2,0,0,8,0,0,0],3:[0,2,0,0,0,0,8,0]},
                {2:[0,0,0,2,8,0,0,0],3:[0,0,0,0,0,2,8,0]}),
        fixture("boundary_and_consecutive_walls",
                {2:[8,2,0,8,8,3,0,8]}, {2:[8,0,2,8,8,0,3,8]}),
        fixture("consecutive_walls",
                {2:[0,2,0,8,8,3,0,0]}, {2:[0,0,2,8,8,0,0,3]}),
        fixture("all_black_defined_but_not_teaching",{}, {},teaching=False),
        fixture("only_walls_defined_but_not_teaching",
                {2:[8,0,8,0,0,8,0,8]}, {2:[8,0,8,0,0,8,0,8]},teaching=False),
        fixture("no_walls_defined_but_not_teaching",
                {2:[2,0,3,0,0,0,0,0]}, {2:[0,0,0,0,0,0,2,3]},teaching=False),
        fixture("already_settled_defined_but_not_teaching",
                {2:[0,0,2,3,8,0,0,0]}, {2:[0,0,2,3,8,0,0,0]},teaching=False),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / "generators" / TASK / "generator.py"
    gen = load(source, "independently_probed_generator")
    source_hash = sha(source)
    cases = fixtures()
    for index, pair in enumerate(canonical_pairs(TASK, root=ROOT)):
        cases.append({"name": "canonical_" + str(index), "kind": "canonical",
                      "input": pair["input"], "expected": pair["output"]})
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 7, 31):
            for index in range(6):
                cases.append({"name": f"generated_{band}_{seed}_{index}",
                              "kind": "generated", "seed": seed, "sample_index": index,
                              "difficulty": band, "input": gen.generate(seed,index,difficulty=band)})

    baseline = None
    if args.baseline:
        old = load(args.baseline.resolve(), "original_generator_for_coverage")
        observations = []
        for band in ("easy", "medium", "hard"):
            for seed in range(20):
                grid = old.generate(seed,0,difficulty=band)
                observations.append({"seed":seed,"sample_index":0,"difficulty":band,
                                     "input":grid,"input_sha256":grid_hash(grid),
                                     "features":measures(grid)})
        baseline = {"generator_sha256":sha(args.baseline),"draws":len(observations),
                    "coverage":{name:sum(row["features"][name] for row in observations)
                                for name in observations[0]["features"]},
                    "observations":observations}
        (out/"baseline-coverage.json").write_text(json.dumps(baseline,separators=(",",":"))+"\n")

    results = []
    receipts = []
    reference = None
    for chunk_no, offset in enumerate(range(0,len(cases),64)):
        input_path = out / f"inputs-{chunk_no}.json"
        reference_path = out / f"reference-{chunk_no}.json"
        input_path.write_text(json.dumps({"inputs":[case["input"] for case in cases[offset:offset+64]]},separators=(",",":"))+"\n")
        argv = [sys.executable,"-m","arcpuzzles","apply",TASK,"--input",str(input_path),
                "--out",str(reference_path),"--timeout","600"]
        started = time.monotonic()
        with (out/f"reference-{chunk_no}.log").open("x") as log:
            proc = subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        receipt = {"argv":argv,"actual_cwd":str(ROOT),"exit_code":proc.returncode,
                   "elapsed_seconds":round(time.monotonic()-started,3),
                   "generator_sha256":source_hash,"case_offset":offset}
        receipts.append(receipt)
        (out/"reference.commands.json").write_text(json.dumps(receipts,indent=2)+"\n")
        if proc.returncode:
            raise SystemExit(proc.returncode)
        raw = json.loads(reference_path.read_text())
        assert raw["executed_rule_hash"] == gen.RULE_HASH
        assert raw["generator_sha256"] == source_hash
        if reference is None:
            reference = {key:value for key,value in raw.items() if key != "results"}
        for row in raw["results"]:
            results.append(dict(row,index=offset+row["index"],raw_chunk=chunk_no,raw_index=row["index"]))
    reference["schema"] = "arcpuzzles-apply-batch-joined-v1"
    reference["results"] = results
    reference["raw_chunk_sha256"] = {f"reference-{i}.json":sha(out/f"reference-{i}.json") for i in range(len(receipts))}
    (out/"reference.json").write_text(json.dumps(reference,separators=(",",":"))+"\n")
    issues = []
    canonical_fit = {name:True for name in gen.SEMANTIC_RIVALS}
    witness_counts = {name:0 for name in gen.SEMANTIC_RIVALS}
    generated_counts = {name:0 for name in gen.SEMANTIC_RIVALS}
    for case, result in zip(cases,reference["results"],strict=True):
        actual = result["output"]
        case["output"] = actual
        if result.get("error") or not result.get("valid_output"):
            issues.append([case["name"],"Racket execution failed"])
        if "expected" in case and actual != case["expected"]:
            issues.append([case["name"],"manual/canonical expected label mismatch"])
        if independently_settle(case["input"]) != actual:
            issues.append([case["name"],"independent Python model mismatch"])
        if gen._gravity(case["input"]) != actual:
            issues.append([case["name"],"generator semantic model mismatch"])
        if case["kind"] in ("generated","canonical") and gen.self_check(case["input"]):
            issues.append([case["name"],"teaching validation rejected"])
        if case["kind"] == "canonical" and gen.strict_canonical_like(case["input"]):
            issues.append([case["name"],"strict canonical hook rejected"])
        if "teaching_expected" in case and (not gen.self_check(case["input"])) != case["teaching_expected"]:
            issues.append([case["name"],"teaching/reference domain confusion"])
        case["rival_disagreements"] = []
        for name, rival in gen.SEMANTIC_RIVALS.items():
            disagrees = rival(case["input"]) != actual
            if case["kind"] == "canonical":
                canonical_fit[name] &= not disagrees
            if case["kind"] == "generated":
                generated_counts[name] += disagrees
            if gen.SEMANTIC_WITNESSES[name](case["input"]):
                witness_counts[name] += 1
                if not disagrees:
                    issues.append([case["name"],"false witness claim",name])
            if disagrees:
                case["rival_disagreements"].append(name)

    episode = [case for case in cases if case.get("difficulty")=="medium"
               and case.get("seed")==0 and case["kind"]=="generated"]
    rival = gen.SEMANTIC_RIVALS["wall_free_passthrough"]
    four = episode[:4]
    failures = [i for i,pair in enumerate(four) if rival(pair["input"])!=pair["output"]]
    teaching = {"kind":"intentional shorter-lesson negative diagnostic",
                "seed":0,"difficulty":"medium","rival":"wall_free_passthrough",
                "four_pair_error_indices":failures,"pairs":episode,
                "six_pair_error_indices":[i for i,pair in enumerate(episode)
                                          if rival(pair["input"])!=pair["output"]],
                "four_pair_holdouts":[],"six_pair_holdouts":[]}
    for length,label in ((4,"four_pair_holdouts"),(6,"six_pair_holdouts")):
        rows = episode[:length]
        for i, query in enumerate(rows):
            demos = [p for j,p in enumerate(rows) if j!=i]
            teaching[label].append({"query_index":i,"hook_reasons":gen.lesson_identifiable(demos,query),
                                     "rival_fits_demos":all(rival(p["input"])==p["output"] for p in demos),
                                     "rival_changes_query":rival(query["input"])!=query["output"]})
    if len(failures)!=1:
        issues.append(["shorter_lesson","expected a single diagnostic profile"])
    if any(item["hook_reasons"] for item in teaching["six_pair_holdouts"]):
        issues.append(["six_pair_lesson","actual ambiguity found"])
    (out/"teaching-counterexample.json").write_text(json.dumps(teaching,separators=(",",":"))+"\n")
    (out/"cases.json").write_text(json.dumps(cases,separators=(",",":"))+"\n")
    summary = {"schema":"segmented-gravity-independent-probe-v1",
               "generator_sha256":source_hash,"rule_hash":reference["executed_rule_hash"],
               "cases":len(cases),"generated_cases":72,
               "unique_inputs":len({grid_hash(case["input"]) for case in cases}),
               "manual_fixtures":13,"canonical_pairs":5,
               "canonical_fitting_rivals":[name for name,fit in canonical_fit.items() if fit],
               "rival_count":len(gen.SEMANTIC_RIVALS),
               "generated_refutations":generated_counts,"witness_firings":witness_counts,
               "baseline_coverage":{k:v for k,v in (baseline or {}).items() if k!="observations"},
               "issues":issues,"status":"pass" if not issues else "fail",
               "reference_sha256":sha(out/"reference.json"),
               "scope":"Named finite bank and these exact grids; no private solve labels or universal uniqueness claim."}
    assert sha(source)==source_hash
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))
    return 1 if issues else 0


if __name__=="__main__":
    raise SystemExit(main())
