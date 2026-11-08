from pathlib import Path
import importlib.util, sys, os, json, copy, hashlib
root=Path.cwd(); sys.path[:0]=[str(root/"src"),str(root/"shared/runtime")]
os.environ["RACKET_PATH"]=str(root.parent/".review/racket-runtime/racket/bin/racket")
path=root/"generators/9df67b512dad/workspace/parametric/prototype.py"
spec=importlib.util.spec_from_file_location("independent_zone_prototype",path)
p=importlib.util.module_from_spec(spec); sys.modules[spec.name]=p; spec.loader.exec_module(p)
out=root.parent/"checks/adversarial"; out.mkdir(parents=True,exist_ok=True)
results=[]
with p.RacketOracle() as oracle:
    episode=p.generate_episode(4381,demos=1,queries=1,oracle=oracle)
    for mutation in ("missing_seed","null_settings","float_query_output"):
        case=copy.deepcopy(episode)
        if mutation=="missing_seed": del case["_private"]["seed"]
        elif mutation=="null_settings": case["_private"]["settings"]=None
        else: case["test"][0]["output"]=[[float(v) for v in row] for row in case["test"][0]["output"]]
        dest=out/mutation
        try:
            response=p.write_export([case],dest,oracle=oracle)
            outcome={"result":"accepted","response":response}
        except Exception as exc:
            outcome={"result":"rejected","exception":type(exc).__name__,"message":str(exc)}
        results.append({"mutation":mutation,**outcome,"destination_created":dest.exists(),"files_created":[str(x.relative_to(dest)) for x in dest.rglob("*") if x.is_file()] if dest.exists() else []})
    forged=copy.deepcopy(episode)
    forged["_private"]["demonstration_certificate"]={"survivors":[],"forged":True}
    altered=copy.deepcopy(forged); altered["_private"]["seed"]=999
    altered["test"][0]["output"]=[[0]]
    assert p.public_challenge_bytes(episode)==p.public_challenge_bytes(altered)
    response=p.write_export([forged],out/"forged_certificate",oracle=oracle)
    public_id=p.public_challenge_id(forged)
    saved=json.loads((out/"forged_certificate/private/episodes"/(public_id+".json")).read_text())
    assert saved["_private"]["demonstration_certificate"]==episode["_private"]["demonstration_certificate"]
    results.append({"mutation":"forged_certificate","result":"recomputed_and_replaced","public_identity_invariant_to_private_metadata_and_query_answers":True})
report={"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"runtime":oracle.runtime_identity,"cases":results}
(out/"prototype-probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
