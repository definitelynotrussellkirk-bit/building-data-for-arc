from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / "fa103c7aa88b"


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest()


def main():
    meta=json.loads((OUT/"probe_meta.json").read_text())
    racket=json.loads((OUT/"racket.json").read_text())
    assert racket["generator_sha256"] == meta["generator_sha256"]
    assert racket["executed_rule_hash"] == meta["rule_hash_expected"]
    assert racket["rule_hash_matches_catalog"] is True
    assert len(meta["records"]) == len(racket["results"]) == 64
    comparisons=[]
    for rec,res in zip(meta["records"],racket["results"]):
        comparisons.append(rec["shortcut_output"] == res["output"] and res["error"] is None)
    generated=comparisons[:-1]
    canonical=comparisons[-1]
    assert all(generated)
    assert canonical is False
    assert all(not r["self_check"] for r in meta["records"])
    assert all(r["template_family"] for r in meta["records"][:-1])
    assert meta["records"][-1]["template_family"] is False
    gen_idx=0; can_idx=63
    case={
      "schema":"arcpuzzles-audit-case-v1",
      "task_id":"fa103c7aa88b",
      "finding_id":"A-FA-1",
      "finding":"The production sampler always emits the same complementary rectangle pair, so a bbox-and-key shortcut is exact on sampled inputs but wrong on a lawful canonical shape pair.",
      "generator_path":meta["generator_path"],
      "generator_sha256":meta["generator_sha256"],
      "rule_hash":racket["executed_rule_hash"],
      "probe":{
        "generated_inputs":63,
        "seed_formula":"20261012 + i*7919",
        "sample_index_formula":"i*17+5",
        "difficulty_cycle":["easy","medium","hard"],
        "generated_template_family_hits":sum(r["template_family"] for r in meta["records"][:-1]),
        "generated_self_check_passes":sum(not r["self_check"] for r in meta["records"][:-1]),
        "generated_shortcut_matches_racket":sum(generated),
        "canonical_cases":1,
        "canonical_self_check_passes":int(not meta["records"][-1]["self_check"]),
        "canonical_shortcut_matches_racket":int(canonical),
      },
      "shortcut":"Ignore interior pixels. From the two largest component bounding boxes choose h=max heights and w=max widths; key 1 emits an h×w rectangle except bottom-right, key 2 emits a solid (h-1)×(w-1) rectangle, and key 3 emits the bottom row plus right column of an h×w rectangle.",
      "generated_witness":{
        "replay":{k:meta["records"][gen_idx][k] for k in ("seed","sample_index","difficulty")},
        "self_check":meta["records"][gen_idx]["self_check"],
        "template_family":meta["records"][gen_idx]["template_family"],
        "input":racket["results"][gen_idx]["input"],
        "racket_output":racket["results"][gen_idx]["output"],
        "shortcut_output":meta["records"][gen_idx]["shortcut_output"],
      },
      "canonical_counterexample":{
        "pair":"train[1]",
        "self_check":meta["records"][can_idx]["self_check"],
        "template_family":meta["records"][can_idx]["template_family"],
        "input":racket["results"][can_idx]["input"],
        "racket_output":racket["results"][can_idx]["output"],
        "shortcut_output":meta["records"][can_idx]["shortcut_output"],
      },
      "hashes":{
        "generated_input":grid_sha(racket["results"][gen_idx]["input"]),
        "generated_racket_output":grid_sha(racket["results"][gen_idx]["output"]),
        "canonical_input":grid_sha(racket["results"][can_idx]["input"]),
        "canonical_racket_output":grid_sha(racket["results"][can_idx]["output"]),
      },
      "commands":[
        {"cwd":"repo","argv":["python3","../checks/audit/fa103c7aa88b/build_inputs.py"]},
        {"cwd":"repo","argv":["python3","-m","arcpuzzles","apply","fa103c7aa88b","--input","../checks/audit/fa103c7aa88b/input.json","--out","../checks/audit/fa103c7aa88b/racket.json"]},
        {"cwd":"repo","argv":["python3","../checks/audit/fa103c7aa88b/finish_case.py"]},
      ],
      "evidence":{
        "authority":"checks/audit/fa103c7aa88b/racket.json",
        "inputs":"checks/audit/fa103c7aa88b/input.json",
        "probe_meta":"checks/audit/fa103c7aa88b/probe_meta.json",
        "semantic_gate":"checks/audit/fa103c7aa88b-combined/checks/fa103c7aa88b_audit_semantic_gate.log",
        "lint":"checks/audit/fa103c7aa88b-battery/checks/fa103c7aa88b_audit_lint.log",
      },
      "domain_note":"All 64 inputs pass the target's current self_check. The 63 generated inputs belong to the ordinary default sampler; canonical train[1] is authoritative and also lies in the declared validator domain.",
      "verdict":"shortcut_confirmed_on_sample; lawful_counterexample_confirmed",
    }
    (OUT/"case.json").write_text(json.dumps(case,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"verdict":case["verdict"],"generated_matches":sum(generated),"generated_total":len(generated),"canonical_matches":int(canonical),"out":str(OUT/"case.json")},sort_keys=True))

if __name__=="__main__":
    main()
