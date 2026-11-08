import sys,copy,json,os
from pathlib import Path
sys.path.insert(0,"/workspace/scratch/509f1499e94c/arc_work/WORK/repo/generators/3f26d45b9f51/workspace/parametric")
import lattice_axes as m
base=Path("/workspace/scratch/509f1499e94c/arc_work/WORK/checks/axes-review")
results=[]
def probe(name, fn):
    try: fn()
    except Exception as e: results.append((name,"REJECT",type(e).__name__,str(e)))
    else: results.append((name,"ACCEPT"))
with m.RacketLabels() as r:
    ep=m.make_episode(17,axes="rows",n_demo=2,n_query=2,K=7,n_colors=3,racket=r)
    def verify_change(name, mutate):
        a=copy.deepcopy(ep);mutate(a);probe(name,lambda:m.verify_episode(a,racket=r))
    verify_change("certificate query_index false",lambda a:a["certificate"]["queries"][0].__setitem__("query_index",False))
    verify_change("certificate identifiable integer",lambda a:a["certificate"]["queries"][0].__setitem__("identifiable",1))
    verify_change("certificate prediction hash",lambda a:a["certificate"]["queries"][0].__setitem__("prediction_hashes",["0"*64]))
    verify_change("seed boolean",lambda a:a.__setitem__("seed",True))
    verify_change("approved status",lambda a:a.__setitem__("status","approved"))
    verify_change("hidden label tamper",lambda a:a["test"][0]["output"][0].__setitem__(0,(a["test"][0]["output"][0][0]+1)%10))
    verify_change("program tamper",lambda a:a.__setitem__("program",a["program"]+" "))
    out=base/"export"
    m.write_batch([ep],out,racket=r)
    manifest=out/"private/manifest.json"; original=manifest.read_text();x=json.loads(original)
    x["query_count"]=999;x["labels_per_setting"]=[999];x["episodes"]=True;x["status"]="approved"
    manifest.write_text(json.dumps(x));probe("false manifest aggregate status bool count",lambda:m.verify_export(out,racket=r));manifest.write_text(original)
    pub=next((out/"public").glob("*.json"));pub.write_bytes(pub.read_bytes()+b" ");probe("public bytes tamper",lambda:m.verify_export(out,racket=r))
print(json.dumps(results,indent=2))
(base/"results.json").write_text(json.dumps(results,indent=2))
