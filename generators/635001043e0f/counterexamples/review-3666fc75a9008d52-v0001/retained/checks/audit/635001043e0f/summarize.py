"""Compare retained actual Racket outputs with bounded audit cases."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path("shared/runtime").resolve()))
from reviewer_support import find_root

out=Path(__file__).resolve().parent
report=json.loads((out/"probe-report.json").read_text())
cases=json.loads((out/"cases.json").read_text())
racket=json.loads((out/"racket.json").read_text())
inputs=json.loads((out/"input.json").read_text())
assert len(cases)==len(racket["results"])==len(inputs)==40
assert report["generator_sha256"]==racket["generator_sha256"]
rows=[]
for i,(case,actual,inp) in enumerate(zip(cases,racket["results"],inputs)):
    assert actual["input"]==inp
    expected=case.get("expected_output",case.get("expected_mirror_output"))
    rows.append({"index":i,"kind":case["kind"],"valid_output":actual["valid_output"],"error":actual["error"],"racket_matches_expected":actual["output"]==expected,"small_frame_rival_matches_racket":case["rival_output"]==actual["output"],"full_copy_rival_matches_racket":case["full_copy_rival_output"]==actual["output"]})
source=find_root(__file__)/"generators/635001043e0f/generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest()==racket["generator_sha256"]
summary={"task_id":report["task_id"],"generator_sha256":racket["generator_sha256"],"executed_rule_text_sha256":racket["rule_text_sha256"],"executed_rule_short_hash":racket["executed_rule_hash"],"source_version":"2.1.0","canonical_pairs":4,"canonical_validator_accepted":sum(not x["self_check_errors"] for x in report["canonical"]),"canonical_racket_label_matches":sum(x["racket_matches_expected"] for x in rows if x["kind"]=="canonical"),"generated_cases":180,"generated_unique_inputs":len({x["input_sha256"] for x in report["generated"]}),"generated_self_check_accepted":sum(not x["self_check_errors"] for x in report["generated"]),"generation_errors":sum("exception" in x for x in report["generated"]),"generated_python_mirror_small_frame_rival_agreement":sum(x["small_frame_rival_matches_mirror"] for x in report["generated"]),"generated_python_mirror_full_copy_rival_agreement":sum(x["full_copy_rival_matches_mirror"] for x in report["generated"]),"racket_generated_cases":36,"racket_generated_label_matches":sum(x["racket_matches_expected"] for x in rows if x["kind"]=="generated"),"racket_generated_small_frame_rival_matches":sum(x["small_frame_rival_matches_racket"] for x in rows if x["kind"]=="generated"),"racket_generated_full_copy_rival_matches":sum(x["full_copy_rival_matches_racket"] for x in rows if x["kind"]=="generated"),"racket_errors":sum(bool(x["error"]) or not x["valid_output"] for x in rows),"seed_range":[0,2],"sample_index_range":[0,19],"difficulty_bands":["easy","medium","hard"],"racket_seed_range":[0,0],"racket_sample_index_range":[0,11],"lesson_demonstration_count":"not specified","lesson_ordering_query_policy":"no lesson contract declared","production_lesson_verdict":"unknown; not measured","query_rotation_verdict":"unknown; not measured","racket_case_results":rows}
(out/"summary.json").write_text(json.dumps(summary,indent=2))
witnesses=[]
for i in (0,3):
    case,actual=cases[i],racket["results"][i]
    rivals={"stamp_only_frames_sized_3_through_5":case["rival_output"],"skip_copy_if_any_cell_is_outside":case["full_copy_rival_output"]}
    differences={name:[[r,c,actual["output"][r][c],grid[r][c]] for r in range(len(grid)) for c in range(len(grid[r])) if grid[r][c]!=actual["output"][r][c]] for name,grid in rivals.items()}
    witnesses.append({"task_id":report["task_id"],"generator_sha256":racket["generator_sha256"],"rule_text_sha256":racket["rule_text_sha256"],"provenance":{"kind":"canonical","variant":case["variant"],"split":case["split"],"pair_index":case["pair_index"],"seed":None,"sample_index":None,"overrides":None,"generated":False},"self_check_errors":case["self_check_errors"],"documented_generator_domain":False,"domain_reason":"The default generator reserves every copy fully in bounds and emits only frame dimensions 3..5.","input":actual["input"],"actual_racket_output":actual["output"],"rival_outputs":rivals,"differences_coordinate_actual_rival":differences,"actual_racket_command":racket["command"],"actual_racket_cwd":racket["cwd"],"actual_racket_exit_code":0})
(out/"counterexamples.json").write_text(json.dumps(witnesses,indent=2))
commands={"task_id":report["task_id"],"generator_sha256":racket["generator_sha256"],"rule_text_sha256":racket["rule_text_sha256"],"verification_commands":[{"cwd":"packet_root","runtime_cwd":"repo","argv":["WORK/.venv/bin/python","review.py","run","../.venv/bin/python","../checks/audit/635001043e0f/probe.py"],"exit_code":0,"runs":2,"purpose":"Initial bounded source/domain probe; then add the full-copy rival and repeat the same deterministic census.","evidence_paths":["checks/audit/635001043e0f/probe.py","checks/audit/635001043e0f/probe-report.json","checks/audit/635001043e0f/input.json","checks/audit/635001043e0f/cases.json"]},{"cwd":"packet_root","runtime_cwd":"repo","argv":["WORK/.venv/bin/python","review.py","run","../.venv/bin/python","-m","arcpuzzles","apply","635001043e0f","--input","../checks/audit/635001043e0f/input.json","--out","../checks/audit/635001043e0f/racket.json"],"exit_code":0,"evidence_paths":["checks/audit/635001043e0f/input.json","checks/audit/635001043e0f/racket.json"]},{"cwd":"packet_root","runtime_cwd":"repo","argv":["WORK/.venv/bin/python","review.py","run","../.venv/bin/python","../checks/audit/635001043e0f/summarize.py"],"exit_code":0,"runs":2,"evidence_paths":["checks/audit/635001043e0f/summarize.py","checks/audit/635001043e0f/summary.json","checks/audit/635001043e0f/counterexamples.json"]}]}
(out/"commands.json").write_text(json.dumps(commands,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!="racket_case_results"},indent=2))
print(json.dumps({"canonical_witness_difference_cell_counts":[{name:len(coords) for name,coords in w["differences_coordinate_actual_rival"].items()} for w in witnesses]},indent=2))
