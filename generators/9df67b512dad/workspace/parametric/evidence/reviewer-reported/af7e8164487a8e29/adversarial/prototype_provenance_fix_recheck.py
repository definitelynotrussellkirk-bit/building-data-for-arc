from pathlib import Path
import importlib.util, sys, os, json, copy, hashlib
root=Path.cwd(); sys.path[:0]=[str(root/"src"),str(root/"shared/runtime")]
os.environ["RACKET_PATH"]=str(root.parent/".review/racket-runtime/racket/bin/racket")
path=root/"generators/9df67b512dad/workspace/parametric/prototype.py"
spec=importlib.util.spec_from_file_location("independent_zone_recheck",path)
p=importlib.util.module_from_spec(spec); sys.modules[spec.name]=p; spec.loader.exec_module(p)
out=root.parent/"checks/adversarial"
cases=[]
with p.RacketOracle() as oracle:
    episode=p.generate_episode(4381,demos=1,queries=1,oracle=oracle)
    for name in ("missing_seed","null_settings","missing_input_seed"):
        changed=copy.deepcopy(episode)
        if name=="null_settings": changed["_private"]["settings"]=None
        elif name=="missing_seed": del changed["_private"]["seed"]
        else: del changed["_private"]["input_seed"]
        dest=out/("recheck_"+name)
        try:
            p.write_export([changed],dest,oracle=oracle)
        except ValueError as exc:
            assert not dest.exists(),name
            cases.append({"name":name,"status":"rejected_before_destination","exception":str(exc)})
        else:
            raise AssertionError(name+" was accepted")
report=json.loads((out/"review.json").read_text())
recheck={"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"cases":cases,"exit_code":0}
(out/"prototype-recheck.json").write_text(json.dumps(recheck,indent=2)+"\n")
report["prototype_final_reviewed_sha256"]=recheck["source_sha256"]
for finding in report["findings"]:
    if finding["id"] in ("export_missing_seed_partial_write","export_null_settings"):
        finding["status"]="fixed_and_independently_verified"
        finding["verification"]="prototype-recheck.json"
report["limits"]=[x for x in report["limits"] if "await" not in x]
report["limits"].append("Final recheck is limited to reported provenance fixes; initial passing surfaces were inspected on the immediately preceding source.")
report["command_statuses"].append({"name":"prototype_provenance_fix_recheck","exit_code":0,"evidence":"prototype-recheck.json"})
(out/"review.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(recheck,indent=2))
