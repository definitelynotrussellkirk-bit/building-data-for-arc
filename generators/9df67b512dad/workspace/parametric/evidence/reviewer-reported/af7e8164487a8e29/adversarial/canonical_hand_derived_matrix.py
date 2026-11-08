from pathlib import Path
import importlib.util, hashlib, json, sys
root = Path.cwd()
sys.path[:0] = [str(root/"src"), str(root/"shared/runtime")]
def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module)
    return module
current_path=root/"generators/9df67b512dad/generator.py"
baseline_path=root.parent/".review/baseline/repo/generators/9df67b512dad/generator.py"
current=load(current_path,"current_canonical")
baseline=load(baseline_path,"baseline_canonical")
def pair(multicolor):
    grid=[[2,0,2,0,7,0,2],[2,0,0,0,0,0,2],[0,0,0,0,0,0,0],[7,0,2,0,7,0,7],[2,0,2,0,7,0,0]]
    label=[[2,7,2],[7,7,7],[2,7,0]]
    if not multicolor:
        grid=[[2 if v==7 else v for v in row] for row in grid]
        label=[[2 if v==7 else v for v in row] for row in label]
    assert current.self_check(grid)==[]
    return {"input":grid,"output":label}
results=[]
for demo_multi in (False,True):
    for query_multi in (False,True):
        demos=[pair(demo_multi) for _ in range(4)]
        query=pair(query_multi)
        reasons=current.lesson_identifiable(demos,query)
        expected_reject=(not demo_multi and query_multi)
        assert bool(reasons)==expected_reject,(demo_multi,query_multi,reasons)
        results.append({"demo_multicolor":demo_multi,"query_multicolor":query_multi,"expected_reject":expected_reject,"reasons":reasons})
demos=[pair(True) for _ in range(4)]; query=pair(True)
query["output"][1][1]=9
assert current.lesson_identifiable(demos,query)
results.append({"case":"tampered_query_label","status":"rejected"})
# Probe Python numeric equality at the label boundary; compare old and current.
demos=[pair(True) for _ in range(4)]; query=pair(True)
for p in demos+[query]: p["output"]=[[float(v) for v in row] for row in p["output"]]
current_reasons=current.lesson_identifiable(demos,query)
baseline_reasons=baseline.lesson_identifiable(demos,query)
numeric={"case":"float_labels","current_reasons":current_reasons,"baseline_reasons":baseline_reasons,"baseline_label_validation_rejects":any("output does not match" in x for x in baseline_reasons)}
out=root.parent/"checks/adversarial"; out.mkdir(parents=True,exist_ok=True)
report={"schema":"bounded-independent-review-v1","task_id":"9df67b512dad","canonical_sha256":hashlib.sha256(current_path.read_bytes()).hexdigest(),"baseline_sha256":hashlib.sha256(baseline_path.read_bytes()).hexdigest(),"canonical_probes":results,"numeric_observation":numeric,"limits":["Hand-derived fixture cases only; not a full corpus or seed sweep.","Float-label acceptance is pre-existing Python equality behavior, outside the scoped semantic-hook repair."]}
(out/"canonical-probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
