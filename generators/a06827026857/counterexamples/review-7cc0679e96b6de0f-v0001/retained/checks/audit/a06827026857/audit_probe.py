"""Adversarial top-level call-contract audit; does not invoke Racket."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK = "a06827026857"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args=p.parse_args()
    root=args.repo.resolve()
    out=args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen, source, source_sha=load_selected_generator(TASK, root=root)
    canonical=[]
    ledger_sha=hashlib.sha256()
    with (root/"shared/data/canonical/puzzles.jsonl").open("rb") as handle:
        for raw in handle:
            ledger_sha.update(raw)
            row=json.loads(raw)
            if row.get("task_id")==TASK:
                canonical.append((row,sha(raw)))
    assert len(canonical)==1
    rule=canonical[0][0]["program_solution"]
    normalized_rule=" ".join(rule.split()).encode()
    rule_sha=sha(normalized_rule)
    assert rule_sha[:12]==gen.RULE_HASH=="4f871ddb0a9d"
    cases=[
      ("seed_bool", {"seed":True,"sample_index":0,"difficulty":"medium"}),
      ("seed_float", {"seed":1.0,"sample_index":0,"difficulty":"medium"}),
      ("seed_string", {"seed":"1","sample_index":0,"difficulty":"medium"}),
      ("sample_index_bool", {"seed":1,"sample_index":True,"difficulty":"medium"}),
      ("sample_index_false", {"seed":1,"sample_index":False,"difficulty":"medium"}),
      ("sample_index_negative", {"seed":1,"sample_index":-1,"difficulty":"medium"}),
      ("difficulty_unknown", {"seed":1,"sample_index":0,"difficulty":"weird"}),
      ("difficulty_integer", {"seed":1,"sample_index":0,"difficulty":1}),
    ]
    results=[]
    for name, arguments in cases:
        record={"case":name,"arguments":arguments}
        try:
            grid=gen.generate(**arguments)
        except Exception as exc:
            record.update(accepted=False,exception=type(exc).__name__,message=str(exc))
        else:
            record.update(accepted=True,grid=grid,shape=[len(grid),len(grid[0])],
                grid_sha256=sha(json.dumps(grid,separators=(",",":")).encode()),
                self_check=gen.self_check(grid),observed=gen.observe_overrides(grid))
        results.append(record)
    controls=[]
    for value in (True,9.0,"9"):
        record={"arguments":{"seed":1,"sample_index":0,"difficulty":"medium","grid_h":value}}
        try:
            gen.generate(**record["arguments"])
        except Exception as exc:
            record.update(rejected=True,exception=type(exc).__name__,message=str(exc))
        else:
            record.update(rejected=False)
        controls.append(record)
    canonical_checks=[]
    for split in ("train","test"):
        for i,pair in enumerate(canonical[0][0].get(split,[])):
            canonical_checks.append({"split":split,"index":i,
                "self_check":gen.self_check(pair["input"]),
                "rivals_fitting_saved_output":[name for name,rival in gen.CANONICAL_SHORTCUTS.items()
                    if rival(pair["input"])==pair["output"]]})
    prior=root/"generators"/TASK/"evidence/review_index.json"
    prior_raw=prior.read_bytes()
    prior_index=json.loads(prior_raw)
    report={
      "schema":"arcpuzzles-adversarial-call-contract-audit-v1",
      "task_id":TASK,"generator_path":str(source.relative_to(root)),
      "generator_sha256":source_sha,"version":gen.VERSION,
      "rule_hash":gen.RULE_HASH,"normalized_rule_sha256":rule_sha,
      "canonical_ledger_sha256":ledger_sha.hexdigest(),
      "canonical_row_sha256":canonical[0][1],
      "classification":"Reproduced previously retained top-level call-contract validation gap; no wrong label demonstrated.",
      "accepted_invalid_calls":sum(row["accepted"] for row in results),
      "invalid_call_count":len(results),
      "accepted_calls_all_validator_clean":all(not row["self_check"] for row in results if row["accepted"]),
      "cases":results,"strict_override_controls":controls,
      "canonical_checks":canonical_checks,
      "prior_audit":{"path":str(prior.relative_to(root)),"sha256":sha(prior_raw),
        "matching_source_findings":[a["return_id"] for a in prior_index.get("audits",[]) if a["source_sha256"]==source_sha]},
      "source_unchanged":sha(source.read_bytes())==source_sha,
      "racket_subprocesses":0,
      "scope_limits":[
        "No fresh Racket labels or semantic battery; this finding concerns validation of caller arguments.",
        "Canonical comparisons use retained labelled pairs and actual declared rivals.",
        "No acceptance/admission state was changed.",
        "The documented finite component grammar is a domain limit, not newly classified as a defect.",
        "This confirms an existing unresolved finding; it is not claimed as a newly discovered issue."
      ]
    }
    report["reproduced"]=(report["accepted_invalid_calls"]==8
        and report["accepted_calls_all_validator_clean"]
        and all(x["rejected"] for x in controls)
        and report["source_unchanged"])
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:report[k] for k in ("task_id","generator_sha256","rule_hash","reproduced",
        "accepted_invalid_calls","invalid_call_count","accepted_calls_all_validator_clean",
        "source_unchanged","racket_subprocesses")},sort_keys=True))
    raise SystemExit(0 if report["reproduced"] else 1)

if __name__=="__main__":
    main()
