"""Test an authored solver against saved, labelled authoring lessons.

This does NOT score a review solve episode or read private query labels. Supply
an existing arcpuzzles lesson-census JSON and a local Python rival file exposing
solve(grid). The census labels are reused, not independently re-executed.
Exit 0 means no measured ambiguity, 1 means ambiguity, and 2 means bad evidence
or execution errors. Requires exactly one query per lesson; rotations hold out
each pair in turn against every other pair. The caller remains responsible for
rule/source provenance. Rival code is executed from a captured byte snapshot.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import types


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def rescore(census_path, rival_path, function="solve"):
    census_bytes = census_path.read_bytes()
    census = json.loads(census_bytes)
    if census.get("schema") != "arcpuzzles-lesson-census-v1":
        raise ValueError("expected a labelled authoring lesson-census, not a solve episode")
    lessons = census.get("lessons", [])
    summary = census.get("summary", {})
    if not lessons or len(lessons) != summary.get("requested") or summary.get("materialization_errors"):
        raise ValueError("census must be complete and free of materialization errors")
    rival_bytes = rival_path.read_bytes()
    rival_sha256 = hashlib.sha256(rival_bytes).hexdigest()
    module = types.ModuleType("authored_rival")
    module.__file__ = str(rival_path)
    exec(compile(rival_bytes, str(rival_path), "exec"), module.__dict__)
    rival = getattr(module, function)
    cache = {}
    errors = []
    ambiguous = []
    rotations = []
    refutation_counts = []
    for row in lessons:
        instance = row["instance"]
        if digest(instance) != row["instance_sha256"]:
            raise ValueError(f"lesson hash mismatch at {row['band']}:{row['index']}")
        if not instance.get("train") or len(instance.get("test", [])) != 1:
            raise ValueError("each lesson must have demonstrations and exactly one query")
        pairs = instance["train"] + instance["test"]
        matches = []
        predictions = []
        for pair in pairs:
            key = digest(pair["input"])
            if key not in cache:
                try:
                    result = rival(copy.deepcopy(pair["input"]))
                    if not isinstance(result,list) or not result or not isinstance(result[0],list) or not result[0]:
                        raise ValueError("rival must return a nonempty integer grid")
                    width = len(result[0])
                    if any(not isinstance(line,list) or len(line) != width or
                           any(type(v) is not int or not 0 <= v <= 9 for v in line) for line in result):
                        raise ValueError("rival returned a ragged or invalid grid")
                    cache[key] = (result,None)
                except Exception as exc:
                    cache[key] = (None,f"{type(exc).__name__}: {exc}")
            prediction,error = cache[key]
            predictions.append(prediction)
            matches.append(error is None and prediction == pair["output"])
            if error:
                errors.append({"band":row["band"],"lesson_index":row["index"],
                               "input_sha256":key,"error":error})
        identity = {k:row[k] for k in ("band","index","seed","sample_index","instance_sha256")}
        n_train = len(instance["train"])
        refutation_counts.append({**identity,"refuting_pairs":[i for i,v in enumerate(matches) if not v]})
        for qi in range(n_train,len(pairs)):
            if all(matches[:n_train]) and not matches[qi]:
                ambiguous.append({**identity,"query_index":qi,"prediction":predictions[qi]})
        for qi in range(len(pairs)):
            if all(matches[j] for j in range(len(pairs)) if j != qi) and not matches[qi]:
                rotations.append({**identity,"query_index":qi,"prediction":predictions[qi]})
    status = "error" if errors else "ambiguous" if ambiguous or rotations else "no_ambiguity_found"
    return {
        "schema":"arcpuzzles-authored-rival-rescore-v1", "status":status,
        "task_id":census["task_id"], "census_path":str(census_path),
        "census_sha256":hashlib.sha256(census_bytes).hexdigest(),
        "generator_sha256":census["generator_sha256"],
        "rule_source_sha256":census["rule_source_sha256"],
        "rival_path":str(rival_path), "rival_sha256":rival_sha256,
        "function":function, "scope":"saved labelled authoring lessons only; no private solve labels read",
        "summary":{"lessons":len(lessons),"rotations":sum(len(r['instance']['train'])+len(r['instance']['test']) for r in lessons),
                   "ambiguous_lessons":len(ambiguous),"ambiguous_rotations":len(rotations),
                   "unique_inputs":len(cache),"execution_errors":len(errors)},
        "ambiguous_lessons":ambiguous,"ambiguous_rotations":rotations,
        "refutations":refutation_counts,"errors":errors,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census",type=Path,required=True)
    parser.add_argument("--rival",type=Path,required=True)
    parser.add_argument("--function",default="solve")
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        parser.error("choose a new output path; preserve earlier evidence")
    try:
        report=rescore(args.census,args.rival,args.function)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}",file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"summary":report["summary"]},indent=2))
    return {"no_ambiguity_found":0,"ambiguous":1,"error":2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
