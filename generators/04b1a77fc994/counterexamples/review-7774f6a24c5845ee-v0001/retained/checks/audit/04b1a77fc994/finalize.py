from pathlib import Path
import json, hashlib
OUT = Path(__file__).resolve().parent
manifest = json.loads((OUT / "instances.json").read_text())
receipt = json.loads((OUT / "racket.json").read_text())
records = manifest["records"]
assert receipt["generator_sha256"] == manifest["generator_sha256"]
assert receipt["executed_rule_hash"] == manifest["declared_rule_hash"]
assert receipt["rule_hash_matches_catalog"]
assert len(receipt["results"]) == len(records) == 40
for row, applied in zip(records, receipt["results"]):
    assert applied["valid_output"] and applied["error"] is None
    assert row["input"] == applied["input"]
    assert row["mirror"] == applied["output"]
    row["racket_output"] = applied["output"]
    row["rival_matches_racket"] = row["rival"] == applied["output"]
    row["mismatched_cells"] = sum(a != b for ar, br in zip(row["rival"],applied["output"]) for a,b in zip(ar,br))
generated = {(r["difficulty"], r["sample_index"]): r for r in records if r["kind"] == "generated"}
windows = []
for band in manifest["bands"]:
    for start in range(8):
        pairs = [generated[band,i] for i in range(start,start+5)]
        verdicts = []
        for query_position in range(5):
            demos = [r for position,r in enumerate(pairs) if position != query_position]
            query = pairs[query_position]
            verdicts.append({"query_position":query_position,"query_sample_index":query["sample_index"],"demo_sample_indices":[r["sample_index"] for r in demos],"rival_fits_all_demos":all(r["rival_matches_racket"] for r in demos),"query_matches":query["rival_matches_racket"],"wrong_query_teaching_shortcut":all(r["rival_matches_racket"] for r in demos) and not query["rival_matches_racket"],"query_mismatch_cells":query["mismatched_cells"]})
        windows.append({"difficulty":band,"seed":0,"start_sample_index":start,"sample_indices":list(range(start,start+5)),"ordered":verdicts[4],"query_rotations":verdicts})
summary = {"task_id":manifest["task_id"],"generator_sha256":manifest["generator_sha256"],"executed_rule_hash":receipt["executed_rule_hash"],"executed_rule_text_sha256":receipt["rule_text_sha256"],"canonical_rule_text_sha256":manifest["canonical_rule_text_sha256"],"canonical_pair_count":4,"canonical_rival_exact":sum(r["rival_matches_racket"] for r in records if r["kind"]=="canonical"),"generated_draw_count":36,"generated_unique_input_count":len({json.dumps(r["input"]) for r in generated.values()}),"racket_applications":40,"racket_errors":0,"mirror_racket_mismatches":0,"self_check_failures":0,"ordered_windows":24,"ordered_wrong_query_windows":sum(w["ordered"]["wrong_query_teaching_shortcut"] for w in windows),"query_rotation_cases":120,"query_rotation_wrong_query_cases":sum(v["wrong_query_teaching_shortcut"] for w in windows for v in w["query_rotations"]),"canonical_shortcuts_declared":False,"lesson_competitors_declared":False,"scope":"seed 0, three bands, starts 0..7, 4 demonstrations and 1 query, no overrides; named unsaturated rival only","windows":windows}
assert summary["ordered_wrong_query_windows"] == 3
assert summary["query_rotation_wrong_query_cases"] == 12
witness_rows = [generated["medium", i] for i in range(1,6)]
witness = {"task_id":manifest["task_id"],"generator_sha256":manifest["generator_sha256"],"executed_rule_hash":receipt["executed_rule_hash"],"executed_rule_text_sha256":receipt["rule_text_sha256"],"existing_finding_return_id":"review-2b87cd571a9526b8:v0001","classification":"reproduced existing unresolved wrong-query teaching shortcut","seed":0,"start_sample_index":1,"difficulty":"medium","overrides":{},"demo_count":4,"input_origin":"ordinary generated, not validator-only","records":witness_rows,"racket_evidence":"checks/audit/04b1a77fc994/racket.json","summary_evidence":"checks/audit/04b1a77fc994/summary.json"}
(OUT / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(OUT / "counterexample.json").write_text(json.dumps(witness,indent=2)+"\n")
print(json.dumps({k:v for k,v in summary.items() if k != "windows"},indent=2))
