from pathlib import Path
import hashlib, json
from reviewer_support import canonical_path, find_root, load_selected_generator
OUT = Path(__file__).resolve().parent
probe = json.loads(OUT.joinpath("probe.json").read_text())
racket = json.loads(OUT.joinpath("racket.json").read_text())
root = find_root(Path.cwd() / "generators" / probe["task_id"] / "generator.py")
gen, path, digest = load_selected_generator(probe["task_id"], root=root)
assert digest == probe["generator_sha256"] == racket["generator_sha256"]
assert hashlib.sha256(canonical_path(root).read_bytes()).hexdigest() == probe["canonical_ledger_sha256"]
assert racket["executed_rule_hash"] == probe["rule_hash"] and racket["rule_hash_matches_catalog"]
assert len(racket["results"]) == len(probe["cases"]) == 9
rows=[]
for case,result in zip(probe["cases"],racket["results"]):
    assert result["input"] == case["input"] and result["index"] == case["apply_batch_index"]
    assert result["valid_output"] and result["error"] is None
    assert result["output"] == case["mirror_output"]
    assert gen.self_check(case["input"]) == []
    if case["origin"] == "canonical": assert result["output"] == case["recorded_output"]
    else: assert gen.generate(case["seed"],case["sample_index"],difficulty=case["difficulty"],**case["overrides"]) == case["input"]
    rows.append({"apply_batch_index":result["index"],"origin":case["origin"],"sample_index":case.get("sample_index"),"self_check":[],"rival_matches_racket":case["rival_output"] == result["output"],"racket_matches_mirror":True,"input_sha256":result["input_sha256"],"output_sha256":result["output_sha256"]})
assert all(row["rival_matches_racket"] for row in rows[:8])
assert rows[8]["rival_matches_racket"] is False
witness={"finding_id":"A4F1E-1","classification":"reproduced_direct_generator_lesson_ambiguity","task_id":probe["task_id"],"generator_sha256":digest,"rule_hash":racket["executed_rule_hash"],"rule_text_sha256":racket["rule_text_sha256"],"canonical_ledger_sha256":probe["canonical_ledger_sha256"],"rival":"Use exact red-cell count for controls 1..3; for controls 4..6 fill every room at the smallest red-cell count >=3, ignoring the exact high control.","lesson":probe["lesson"],"reference_command":racket["command"],"reference_cwd":"repo","cases":[]}
for case,result in zip(probe["cases"][5:],racket["results"][5:]):
    witness["cases"].append({k:v for k,v in case.items() if k not in ("mirror_output","recorded_output")}|{"actual_racket_output":result["output"],"input_sha256":result["input_sha256"],"output_sha256":result["output_sha256"]})
OUT.joinpath("counterexample.json").write_text(json.dumps(witness,indent=2)+"\n")
report={"generator_sha256":digest,"rule_text_sha256":racket["rule_text_sha256"],"verified_racket_cases":9,"canonical_fit":5,"generated_demo_fit":3,"generated_query_disagreement":1,"self_check_pass":9,"source_unchanged":True,"canonical_ledger_unchanged":True,"rows":rows}
OUT.joinpath("verification.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report))
