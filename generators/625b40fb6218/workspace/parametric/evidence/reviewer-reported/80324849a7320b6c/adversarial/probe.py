from pathlib import Path
from copy import deepcopy
import hashlib, importlib.util, json, time
from reviewer_support import public_challenge_bytes, public_challenge_id

source=Path("generators/625b40fb6218/workspace/parametric/prototype.py")
spec=importlib.util.spec_from_file_location("adversarial_proto",source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=Path("../checks/adversarial")
began=time.monotonic()
report={"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"surfaces":["sampler count/retry/type boundaries","verifier rejection and public metadata exclusion"],"observations":[],"findings":[]}
def observe(name, callback, expected_reject=False):
    row={"name":name}
    try:
        value=callback()
        row["result"]="accepted"
        if expected_reject:
            report["findings"].append(name)
            row["finding"]="expected rejection but verifier accepted"
        elif value is not None:
            row["detail"]=value
    except ValueError as e:
        row["result"]="rejected"
        row["error"]=str(e)
        if not expected_reject:
            report["findings"].append(name)
    except Exception as e:
        row["result"]="error";row["error"]=repr(e);report["findings"].append(name)
    report["observations"].append(row)
def sample_edge(seed):
    a,b=m.sample_inputs(seed,n_demos=8,n_queries=16,max_attempts=24)
    assert len(a)==8 and len(b)==16
    assert len({m.grid_key(x) for x in a+b})==24
    return {"demos":len(a),"queries":len(b),"distinct":24}
observe("minimum seed and maximum counts exact attempt budget",lambda: sample_edge(0))
observe("maximum seed and maximum counts exact attempt budget",lambda: sample_edge(2**64-1))
for name,kw in [("boolean seed",{"input_seed":True}),("float demos",{"input_seed":2,"n_demos":2.0}),("zero queries",{"input_seed":2,"n_queries":0}),("too few attempts",{"input_seed":2,"max_attempts":5}),("excess attempts",{"input_seed":2,"max_attempts":4097})]:
    observe(name,lambda kw=kw:m.sample_inputs(**kw),True)
original=m.GEN.generate
constant=original(19,2)
calls=[]
def repeated(seed,index,**kw):
    calls.append(index)
    return original(seed,index,**kw) if index<2 else deepcopy(constant)
m.GEN.generate=repeated
try:
    observe("duplicate retry budget exhausted",lambda:m.sample_inputs(19,n_demos=2,n_queries=4,max_attempts=6),True)
finally:
    m.GEN.generate=original
report["retry_indices"]=calls
with m.RacketLabeler() as oracle:
    e=m.generate_episode(91,n_demos=2,n_queries=1,labeler=oracle)
    observe("untampered actual Racket episode",lambda:m.verify_episode(e,labeler=oracle))
    def tamper(name,mutator,expected=True):
        x=deepcopy(e);mutator(x)
        observe(name,lambda:m.verify_episode(x,labeler=oracle),expected)
    tamper("wrong query label",lambda x:x["challenge"]["test"][0]["output"][0].__setitem__(0,(x["challenge"]["test"][0]["output"][0][0]+1)%10))
    tamper("boolean query label",lambda x:x["challenge"]["test"][0]["output"][0].__setitem__(0,False))
    tamper("forged certificate",lambda x:x["certificate"].__setitem__("survivors",[]))
    def bad_program(x):
        x["program"]="(rule! g)"
        x["program_sha256"]=hashlib.sha256(x["program"].encode()).hexdigest()
    tamper("forged program with matching claimed hash",bad_program)
    tamper("duplicate input",lambda x:x["challenge"]["test"].__setitem__(0,deepcopy(x["challenge"]["train"][0])))
    tamper("forged source hash",lambda x:x.__setitem__("prototype_sha256","0"*64))
    tamper("training admitted",lambda x:x.__setitem__("training_admitted",True))
    tamper("forged episode schema",lambda x:x.__setitem__("schema","unrelated-schema"))
    tamper("forged parent lineage",lambda x:x.__setitem__("parent",{"source_split":"evaluation","source_task_id":"forged"}))
    tamper("forged protected runtime claim",lambda x:x.__setitem__("runtime",{"protected":False,"racket_executable_sha256":"0"*64}))
    raw=public_challenge_bytes(e["challenge"]);pid=public_challenge_id(e["challenge"])
    variant=deepcopy(e["challenge"]);variant["seed"]="PRIVATE_SENTINEL";variant["params"]={"secret":"PRIVATE_SENTINEL"};variant["program"]="PRIVATE_SENTINEL"
    variant["test"][0]["output"]=[[9]]
    assert public_challenge_bytes(variant)==raw
    assert public_challenge_id(variant)==pid
    assert pid==hashlib.sha256(raw).hexdigest()
    pub=json.loads(raw)
    assert set(pub)=={"train","test"} and all(set(p)=={"input"} for p in pub["test"])
    report["public_projection"]={"invariant_to_private_fields":True,"id_hashes_exact_bytes":True,"no_query_answers":True}
    report["racket_calls"]=oracle.calls
report["elapsed_seconds"]=round(time.monotonic()-began,3)
report["scope"]="Bounded independent probe; no full generator battery or training admission."
(out/"probe-result.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
