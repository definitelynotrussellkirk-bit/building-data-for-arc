#!/usr/bin/env python3
"""Distill existing Racket evidence and verify the final shape-rejection fix."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_path, load_selected_generator


TASK="fc814cec3976"
EXPECTED_FINAL="416d21b39294a0c88facbf8a094b492fe5a2fc67ed24330852d0faa776b10189"
ROOT=Path.cwd().resolve()
WORK=ROOT.parent
OUT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest()


def write_new(path,value):
    if path.exists():
        raise FileExistsError(f"Refusing to replace retained evidence: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")


def main():
    gen,source,digest=load_selected_generator(TASK,root=ROOT)
    assert digest==EXPECTED_FINAL,digest
    intermediate=WORK / "checks/code-review.json"
    intermediate_hash=sha(intermediate)
    previous=json.loads((OUT / "malformed-validator-review.json").read_text())
    cropped=previous["input"]
    errors=gen.self_check(cropped)
    strict=gen.strict_canonical_like(cropped)
    observed=gen.observe_overrides(cropped)
    analysis=gen._analysis(cropped)
    assert errors and any("19x19" in error for error in errors)
    assert strict==errors and observed=={}
    assert analysis=={"errors":errors,"scene_code":None,"facts":{},"output":None}
    test_log=OUT / "final-shape-regression.log"
    assert "1 passed" in test_log.read_text(),test_log.read_text()

    bindings=json.loads((OUT / "structural-racket-verification.json").read_text())
    raw_path=OUT / "structural-racket-raw-receipt.json"
    raw=json.loads(raw_path.read_text())
    assert sha(raw_path)==bindings["raw_receipt_sha256"]
    row=next(row for row in bindings["rows"] if row["profile_index"]==1 and row["transform"]==2)
    indexes=row["racket_result_indexes"]
    original,modified=[raw["results"][index] for index in indexes]
    assert all(result["valid_output"] and result["error"] is None for result in (original,modified))
    for result in (original,modified):
        assert grid_sha(result["input"])==result["input_sha256"]
        assert grid_sha(result["output"])==result["output_sha256"]
    assert gen._red_key(original["input"])==gen._red_key(modified["input"])
    mutations=[[r,c,original["input"][r][c],modified["input"][r][c]] for r in range(19) for c in range(19) if original["input"][r][c]!=modified["input"][r][c]]
    assert mutations==row["changes"]==[[3,10,0,5]]
    assert gen._STRUCTURAL_EDITS[(1,2)]==((3,10,5),)
    rival=deepcopy(modified["input"])
    for r in range(19):
        for c in range(19):
            if original["output"][r][c]!=original["input"][r][c]:
                rival[r][c]=original["output"][r][c]
    assert rival==gen.red_layout_lookup(modified["input"])
    different=[[r,c,modified["output"][r][c],rival[r][c]] for r in range(19) for c in range(19) if modified["output"][r][c]!=rival[r][c]]
    assert len(different)==12

    programs=set()
    for line in canonical_path(ROOT).read_text().splitlines():
        candidate=json.loads(line)
        if candidate.get("task_id")==TASK:
            programs.add(candidate["program_solution"])
    assert len(programs)==1
    canonical=programs.pop()
    canonical_sha=hashlib.sha256(canonical.encode()).hexdigest()
    assert hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]==raw["executed_rule_hash"]==gen.RULE_HASH

    codes={}
    for code in range(gen.SCENE_COUNT):
        template=gen._template_for_code(code)
        if (template["profile_index"],template["transform_index"])==(1,2):
            kind="altered" if code%5 in (1,3) else "ordinary"
            codes.setdefault(kind,code)
        if len(codes)==2:
            break
    assert set(codes)=={"ordinary","altered"}
    protected=gen._TEMPLATES[(1,2)]["protected"]
    current_linkage={}
    for kind,old in (("ordinary",original),("altered",modified)):
        grid=gen.generate(0,0,scene_code=codes[kind])
        assert gen.self_check(grid)==[]
        assert gen.observe_overrides(grid)=={"scene_code":codes[kind]}
        assert all(grid[r][c]==old["input"][r][c] for r,c in protected)
        current_linkage[kind]={"scene_code":codes[kind],"input_sha256":grid_sha(grid),"self_check":[],"protected_context_equals_retained_pair":True}

    counter_path=ROOT / "generators" / TASK / "counterexamples/structural-contrast.json"
    counter={
        "schema":"fc814cec3976-structural-contrast-v1","task_id":TASK,
        "coordinate_convention":"zero-based [row, column]",
        "finding":"One fixed recolor mask per red-coordinate key cannot answer both Racket-labeled inputs.",
        "sources":{
            "racket_label_execution_generator_sha256":raw["generator_sha256"],
            "analytical_baseline_generator_sha256":bindings["analytical_baseline_sha256"],
            "final_generator_sha256":digest,
            "executed_rule_hash":raw["executed_rule_hash"],
            "executed_wrapped_rule_text_sha256":raw["rule_text_sha256"],
            "current_canonical_program_sha256":canonical_sha,
            "reference":"canonical Racket","canonical_path":"shared/data/canonical/puzzles.jsonl",
            "receipt_sha256":sha(raw_path),"receipt_result_indexes":indexes,
            "receipt_provenance":"WORK/checks/canonical-investigation/structural-racket-raw-receipt.json"
        },
        "label_scope":"The grids and labels below are exact copies of one earlier Racket execution under the baseline generator binding. They are not relabeled as a new final-source execution. The final selected generator contains the same protected structural edit; its exact encoded generated scenes differ in irrelevant texture.",
        "mutation":mutations,
        "same_red_key":True,
        "original":{k:original[k] for k in ("input","output","input_sha256","output_sha256","generator_domain")},
        "modified":{k:modified[k] for k in ("input","output","input_sha256","output_sha256","generator_domain")},
        "racket_verified_modified_facts":row["facts"],
        "lookup_counterexample":{
            "construction":"Copy the modified input and overwrite exactly the cells changed in the original input/output pair with their original output colors.",
            "output_sha256":grid_sha(rival),
            "differing_cells_authoritative_then_lookup":different,
            "mismatch_count":len(different)
        },
        "final_source_linkage":{
            "structural_edit":list(map(list,gen._STRUCTURAL_EDITS[(1,2)])),
            "profile":"public_2","transform_index":2,
            "generated_replay":current_linkage,
            "retained_raw_original_self_check":gen.self_check(original["input"]),
            "retained_raw_modified_self_check":gen.self_check(modified["input"]),
            "scope":"The raw retained pair is a hand-made context witness, not an assertion that these exact texture bytes are in final encoded support. The replay scene codes are admitted final generated inputs with identical respective candidate-protected cells. No new Racket labels were executed for these replay codes in this distillation."
        },
        "remaining_limit":"This refutes red coordinates alone as a key. The final generator still has a finite scene bank and recoverable scene-code bits; broader context/code lookup remains possible."
    }
    write_new(counter_path,counter)

    malformed_path=ROOT / "generators" / TASK / "counterexamples/malformed-known-red-key.json"
    malformed={
        "schema":"fc814cec3976-malformed-known-red-key-v1","task_id":TASK,
        "input":cropped,"shape":[16,16],"input_sha256":grid_sha(cropped),
        "replay":"Crop gen.generate(0, 0, scene_code=5) to [row[:16] for row in grid[:16]]. Its public_2 red key remains unchanged.",
        "before_generator_sha256":previous["generator_sha256"],
        "final_generator_sha256":digest,"declared_rule_hash":gen.RULE_HASH,
        "before": [{key:result[key] for key in ("hook","status","exception_type","error")} for result in previous["results"]],
        "after":{"self_check":errors,"strict_canonical_like":strict,"observe_overrides":observed,"analysis_output":analysis["output"]},
        "resolution":"The wrong-shape analysis returns rejection reasons before indexing the template's scene-code bit positions.",
        "scope":"Validator rejection regression outside generated support; no Racket label or valid generated-scene admission is claimed."
    }
    write_new(malformed_path,malformed)

    assert sha(source)==digest and sha(intermediate)==intermediate_hash
    resolution={
        "schema":"fc814cec3976-code-review-resolution-v1","task_id":TASK,
        "status":"resolved","finding_id":"known_red_key_wrong_shape",
        "intermediate_review":{"path":"checks/code-review.json","sha256":intermediate_hash,"generator_sha256":previous["generator_sha256"],"unchanged":True},
        "final_generator":{"path":"repo/generators/fc814cec3976/generator.py","version":gen.VERSION,"sha256":digest},
        "reviewed_change":"_analysis immediately returns errors, scene_code=None, facts={}, output=None after rejecting a non-19x19 shape. No template-bit position is accessed on that path.",
        "probe":{"input_sha256":grid_sha(cropped),"same_known_red_key":previous["same_red_key"],"self_check":errors,"strict_canonical_like":strict,"observe_overrides":observed},
        "commands":[
            {"cwd":str(WORK.parent),"argv":["WORK/.venv/bin/python","review.py","run","../.venv/bin/python","-m","pytest","-q","generators/fc814cec3976/tests/test_structural_support.py::test_known_red_layout_on_wrong_shape_is_rejected_without_indexing_error"],"exit_code":0,"result":"1 passed","log":"checks/canonical-investigation/final-shape-regression.log","log_sha256":sha(test_log)},
            {"cwd":str(WORK.parent),"argv":["WORK/.venv/bin/python","review.py","run","../.venv/bin/python","../checks/canonical-investigation/finalize_resolution.py"],"payload_cwd":str(ROOT),"exit_code":0,"result":"All exact-source, malformed-input, retained-label, and source-linkage assertions passed."}
        ],
        "counterexamples":[{"path":str(path.relative_to(WORK)),"sha256":sha(path)} for path in (counter_path,malformed_path)],
        "no_new_racket_execution":"The focused validator test and direct rejection probe need no new output labels. Structural counterexample labels were distilled unchanged from earlier canonical Racket results with baseline and final bindings stated separately.",
        "remaining_limits":"The intermediate review's finite-bank, recoverable scene-code, and named-rival scope limits remain unchanged.",
        "completed_utc":datetime.now(timezone.utc).isoformat()
    }
    write_new(WORK / "checks/code-review-resolution.json",resolution)
    print(json.dumps({"status":resolution["status"],"final_generator_sha256":digest,"intermediate_review_unchanged":True,"structural_racket_result_indexes":indexes,"final_generated_replay_codes":codes,"counterexample_paths":[str(path.relative_to(WORK)) for path in (counter_path,malformed_path)]}),flush=True)


if __name__=="__main__":
    main()
