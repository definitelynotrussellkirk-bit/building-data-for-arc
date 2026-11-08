"""Validate Racket receipts and render the findings-only audit section."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
probe=json.loads((HERE/"probe.json").read_text())
receipt=json.loads((HERE/"racket.json").read_text())
inputs=json.loads((HERE/"input.json").read_text())
rivals=json.loads((HERE/"rival_output.json").read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(WORK/probe["generator_path"])==probe["generator_sha256"]==receipt["generator_sha256"]
assert sha(WORK/probe["selected_rule_path"])==probe["selected_rule_file_sha256"]
assert receipt["task_id"]=="d9f6e69efb45" and receipt["executed_rule_hash"]=="1603ebb35068"
assert receipt["rule_hash_matches_catalog"] is True
rows=receipt["results"]
assert len(rows)==len(inputs)==4
for i,row in enumerate(rows):
    assert row["index"]==i and row["input"]==inputs[i]
    assert row["valid_output"] and row["error"] is None
    assert row["output"]!=row["input"]
assert rows[0]["output"]==rivals[0]
assert rows[3]["output"]==rivals[3]
for i,expected in enumerate(probe["canonical_expected_outputs"],1):
    assert rows[i]["output"]==expected and rows[i]["output"]!=rivals[i]

def differences(a,b):
    return [[r,c,a[r][c],b[r][c]] for r in range(len(a)) for c in range(len(a[0])) if a[r][c]!=b[r][c]]

cases=[]
for i in range(4):
    cases.append({"input_index":i,"kind":probe["input_inventory"][i]["kind"],"input":inputs[i],
                  "authority_output":rows[i]["output"],"restricted_frame_rival_output":rivals[i],
                  "authority_rival_disagreement_cells":differences(rows[i]["output"],rivals[i]),
                  "input_sha256":rows[i]["input_sha256"],"output_sha256":rows[i]["output_sha256"]})
report={
 "schema":"arcpuzzles-reviewer-counterexamples-v1","task_id":"d9f6e69efb45",
 "source_state":"unchanged audited source","generator_sha256":probe["generator_sha256"],
 "generator_version":probe["generator_version"],"executed_rule_hash":receipt["executed_rule_hash"],
 "rule_text_sha256":receipt["rule_text_sha256"],"rule_reference":receipt["reference"],
 "racket_receipt_path":"checks/audit/d9f6e69efb45/racket.json", "racket_receipt_sha256":sha(HERE/"racket.json"),
 "source_files_unchanged":True,
 "findings":[
  {"id":"AUD-D9-001","type":"exact frame-count override silently underproduced",
   "seed":0,"sample_index":0,"difficulty":"medium","overrides":probe["generation_case"]["overrides"],
   "input_index":0,"requested_n_frames":2,"recorded_n_frames":2,"observed_n_frames":1,"self_check":[],
   "feasible_same_dimension_input_index":3,
   "root_cause":"The 80-attempt placement loop returns the partial placed list without requiring len(placed)==n_frames; self_check checks at least one frame, not the requested count.",
   "scope":"One deterministic generated reproduction, not a failure-rate estimate. No reference-rule bug asserted."},
  {"id":"AUD-D9-002","type":"canonical frame branch excluded by generator and validator",
   "input_indices":[1,2],"canonical_inputs_checked":3,"canonical_inputs_rejected":2,
   "canonical_validation":probe["canonical_validation"],
   "root_cause":"_is_rect_frame rejects either outer side below 4 and normal placement draws both sides only from 4..5; the canonical rule accepts frames with side lengths at least 3 and both public training inputs contain a width-3 frame.",
   "rival":probe["rival"],
   "scope":"All three public canonical inputs checked; the two training examples were independently executed through the supported Racket authority. No reference-rule bug asserted."}
 ],
 "cases":cases,"authority_command":receipt["command"],"authority_cwd_relative_to_WORK":"repo",
 "command_records":"checks/audit/d9f6e69efb45/commands.json",
 "limits":"Focused exact-control and canonical-domain audit; no battery, exhaustive override sweep, broad stochastic rate estimate, or private solve access. Audit target and shared sources were not edited."
}
(HERE/"counterexample.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
section=f"""## d9f6e69efb45

**Finding: two independently reproduced generator-contract defects. Audit-only target left unchanged.**

Audited generator version `2.0.0`, SHA-256 `{probe["generator_sha256"]}`; selected canonical Racket rule hash `{receipt["executed_rule_hash"]}`. The supported authority receipt matches that generator hash and reports four valid executions. These findings concern generation and validation; no reference-rule bug is asserted.

### AUD-D9-001 — Exact frame count is silently underproduced

`generate(0, 0, difficulty="medium", grid_h=8, grid_w=11, n_frames=2)` returns an 8×11 grid with **one** complete gray frame, bounding box `(0, 2, 4, 6)` (zero-based, inclusive). The public generation context records and consumes `n_frames=2`, while `self_check` returns `[]`.

The placement loop at `repo/generators/d9f6e69efb45/generator.py:94–105` stops after 80 attempts and returns whatever frames fit its random choices. It neither completes the requested count nor rejects underproduction. The validator only requires at least one valid frame. This lets a returned example disagree with its explicit control and recorded provenance.

The request is geometrically feasible. A retained 8×11 control places 4×4 frames at `(0, 0, 3, 3)` and `(0, 6, 3, 9)`. It passes the same validator and satisfies even the implementation's double-padded separation condition. Racket fills both frames correctly. Thus this reproduction is a packing failure, not an impossible dimension/count combination.

Evidence: `checks/audit/d9f6e69efb45/probe.json` records the exact draw and consumed controls; `input.json` index 0 is the generated counterexample and index 3 is the constructive feasibility control. `counterexample.json` includes both inputs, authoritative outputs, hashes, and findings. Scope: one deterministic generated reproduction at seed 0/sample index 0, with the exact overrides above; no failure-frequency estimate.

### AUD-D9-002 — The validator rejects canonical narrow frames, which normal generation never teaches

All **3 public canonical inputs** were checked. `self_check` rejects **both training inputs**, each with `color-5 component is not a complete rectangular frame`; it accepts the canonical test input. The rejected frames are complete gray rectangles with width 3, present in the task's own demonstrations.

The cause is `_is_rect_frame` at `generator.py:160–169`, which requires both outer sides to be at least 4. Normal placement at lines 96–97 also samples both sides only from 4 to 5. The selected reference instead accepts frame heights and widths of at least 3. The generated family therefore omits a positive branch already required by the canonical demonstrations, and its validator incorrectly labels those demonstrations malformed.

The supported Racket command reproduces the exact published outputs for both training inputs. An executable rival that fills only frames with both sides at least 4 fails on those same inputs: it misses {len(cases[1]["authority_rival_disagreement_cells"])} filled cells in training pair 0 and {len(cases[2]["authority_rival_disagreement_cells"])} in training pair 1. This is a directly witnessed domain/teaching gap; no claim is made that the rival fits every canonical example.

Evidence: `checks/audit/d9f6e69efb45/input.json` indices 1 and 2 are public canonical training pairs 0 and 1. `racket.json` contains the authoritative results and source binding; `rival_output.json` and `counterexample.json` retain rival predictions and exact differing cells. `audit_probe.py` contains the independent frame observer and rival.

### Reproduction and scope

Run `.venv-review/bin/python -B checks/audit/d9f6e69efb45/audit_probe.py` from `WORK`, then use the outer `review.py run python3 -B -m arcpuzzles apply d9f6e69efb45 --input ../checks/audit/d9f6e69efb45/input.json --out ../checks/audit/d9f6e69efb45/racket.json` command with the review environment on `PATH`. Run `.venv-review/bin/python -B checks/audit/d9f6e69efb45/finalize_audit.py` from `WORK` to validate the receipts. Exact argument arrays, relative working directories, exit codes, and evidence paths are in `checks/audit/d9f6e69efb45/commands.json`.

This was a focused audit of one generated exact-control reproduction, all three public canonical inputs, and one packing-feasibility control. Four retained inputs were executed through the public Racket command. No broad battery or exhaustive override sweep was run. The target, selected rule, and shared files were not edited, and no blind/post-repair private solve labels were read. Both findings remain unresolved.
"""
assert section.startswith("## d9f6e69efb45\n")
(HERE/"AUDIT_SECTION.md").write_text(section)
print(json.dumps({"verified":True,"findings":["AUD-D9-001","AUD-D9-002"],"authority_inputs":4,
                  "canonical_rival_disagreement_cells":[len(cases[1]["authority_rival_disagreement_cells"]),len(cases[2]["authority_rival_disagreement_cells"])],
                  "source_unchanged":True},sort_keys=True))
