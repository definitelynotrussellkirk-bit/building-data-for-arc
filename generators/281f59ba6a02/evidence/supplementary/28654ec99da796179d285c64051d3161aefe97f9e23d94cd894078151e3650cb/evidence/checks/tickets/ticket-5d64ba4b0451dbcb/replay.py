"""One bounded, retained-witness replay; never run the original broad audit main."""
from pathlib import Path
import ast, hashlib, json, sys, time
start=time.perf_counter()
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK/"repo"
TID="281f59ba6a02"
ticket=next(x for x in json.loads((WORK/"AUDIT_ASSIGNMENT.json").read_text())["tickets"] if x["ticket_id"]==HERE.name)
sha=lambda b: hashlib.sha256(b).hexdigest()
identities={}
for key in ("source","audit_index","assets_manifest"):
    item=ticket[key]; raw=(WORK/item["path"]).read_bytes(); digest=sha(raw)
    assert digest==item["sha256"], (key,"identity drift")
    identities[key]={"path":item["path"],"sha256":digest}
index=json.loads((WORK/ticket["audit_index"]["path"]).read_text())
audit=next(x for x in index["audits"] if x["return_id"]==ticket["audit_return_id"])
digest=sha(json.dumps(audit,sort_keys=True,separators=(",",":")).encode())
assert digest==ticket["audit_record_sha256"]
identities["audit_record_sha256"]=digest
assets=json.loads((WORK/ticket["assets_manifest"]["path"]).read_text())
for asset in assets["files"]:
    raw=(REPO/asset["path"]).read_bytes();assert sha(raw)==asset["sha256"] and len(raw)==asset["bytes"]
    identities[asset["original_member"]]={"path":asset["path"],"sha256":sha(raw),"bytes":len(raw)}
evidence_asset=next(x for x in assets["files"] if x["original_member"]=="checks/audit-evidence.json")
retained=json.loads((REPO/evidence_asset["path"]).read_text())[TID]
script_asset=next(x for x in assets["files"] if x["original_member"]=="checks/audit_probe.py")
# Extract only the pinned audit rival helper; original main also targets another task.
tree=ast.parse((REPO/script_asset["path"]).read_text())
helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="starburst")
ns={};exec(compile(ast.Module(body=[helper],type_ignores=[]),str(REPO/script_asset["path"]),"exec"),ns)
starburst=ns["starburst"]
sys.path.insert(0,str(REPO/"shared/runtime"))
from reviewer_support import load_selected_generator,canonical_path
G,source,generator_sha=load_selected_generator(TID,root=REPO)
assert generator_sha==ticket["generator_sha256"]==ticket["audited_generator_sha256"]
programs={json.loads(line)["program_solution"] for line in canonical_path(REPO).read_text().splitlines() if json.loads(line).get("task_id")==TID}
assert len(programs)==1
program=programs.pop()
identities["canonical_program_sha256"]=sha(program.encode())
identities["pinned_rule_hash"]=ticket["rule_hash"]
original=retained["ignored_override_witness"]
actual=G.generate(original["seed"],original["sample_index"],difficulty=original["difficulty"],**original["requested"])
default=G.generate(original["seed"],original["sample_index"],difficulty=original["difficulty"])
b1={"requested":original["requested"],"observed_shape":[len(actual),len(actual[0])],"same_as_unoverridden":actual==default,"matches_retained_input":actual==original["input"],"input":actual}
b2={"color_10_3x3":G.self_check([[10]*3 for _ in range(3)]),"oversize_31x31":G.self_check([[4]*31 for _ in range(31)])}
from arc_repl.racket_bridge import RacketBridge
with RacketBridge(timeout=15) as bridge:
    witness=retained["asymmetric_arm_witness"]; grid=witness["input"]
    bridge.define_grid("g",grid)
    output=bridge.eval_text("("+program.rstrip()[len("(rule!"):-1].strip()+" g)")
    rival=starburst(grid,1)
    b3={"selfcheck":G.self_check(grid),"matches_retained_output":output==witness["output"],"matches_retained_rival":rival==witness["down_arm_rival_output"],"rule_mirror_matches":starburst(grid,-1)==output,"rival_disagrees":rival!=output,"coordinate_2_4":{"racket":output[2][4],"down_rival":rival[2][4]},"input":grid,"output":output,"down_arm_rival_output":rival}
assert b1["observed_shape"]==[16,17] and b1["same_as_unoverridden"] and b1["matches_retained_input"]
assert b2==retained["malformed_grid_selfcheck"]=={"color_10_3x3":[],"oversize_31x31":[]}
assert b3["matches_retained_output"] and b3["matches_retained_rival"] and b3["rival_disagrees"] and b3["rule_mirror_matches"] and b3["selfcheck"]==[]
result={"ticket_id":HERE.name,"task_id":TID,"audit_return_id":ticket["audit_return_id"],"identities":identities,"B1":b1,"B2":b2,"B3":b3,"targeted_probe_seconds":round(time.perf_counter()-start,6),"targeted_probes":1,"racket_applications":1,"assessment":"Pinned B1 and B2 contract failures and B3 concrete asymmetric-arm witness reproduce on identical current source. Historical 128-case census and all-canonical-pairs claim were not rerun. B3 retains its original executable-oracle versus intended-rule interpretation limit. Existing audit remains needs_triage; no audit cleared or approval implied."}
(HERE/"results.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"result":"reproduced","identities":identities,"B1_shape":b1["observed_shape"],"B2":b2,"B3_coordinate":b3["coordinate_2_4"],"probe_seconds":result["targeted_probe_seconds"]},indent=2))
