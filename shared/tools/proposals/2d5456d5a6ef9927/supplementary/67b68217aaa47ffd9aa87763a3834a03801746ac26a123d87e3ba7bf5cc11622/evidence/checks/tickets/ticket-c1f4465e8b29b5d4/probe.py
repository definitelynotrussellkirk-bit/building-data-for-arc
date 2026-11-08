"""One bounded static allocation probe; no generator, Racket, or model execution."""
from __future__ import annotations
import argparse, ast, collections, datetime, hashlib, json, random, re, time, zipfile
from pathlib import Path

TICKET_ID='ticket-c1f4465e8b29b5d4'
SEED='46d0fc6ba2ecb5d90e0b6ff34203b12e8d4941710f6d226aa090c12e44e8c1b8'
parser=argparse.ArgumentParser()
parser.add_argument('--packet',type=Path,required=True)
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
started=time.monotonic(); start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
z=zipfile.ZipFile(args.packet)
infos={i.filename:i for i in z.infolist()}
manifest_raw=z.read('WORK/PACKET-MANIFEST.json'); manifest=json.loads(manifest_raw)
bindings={}
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(path,maximum=600000):
    if time.monotonic()-started>110: raise RuntimeError('Static probe budget reached')
    local=args.work/path
    issued='WORK/'+path
    if local.is_file() and not local.is_symlink():
        if local.stat().st_size>maximum: return None
        raw=local.read_bytes(); location='current_workspace'
    elif issued in infos:
        if infos[issued].file_size>maximum: return None
        raw=z.read(issued); location='issued_zip'
    else: return None
    actual=digest(raw); expected=manifest['files'].get(path)
    bindings[path]={'sha256':actual,'issued_sha256':expected,'matches_issued':actual==expected if expected else None,'read_from':location,'bytes':len(raw)}
    return raw

def excerpt(text,pattern,context=2,limit=100):
    lines=text.splitlines(); keep=set()
    for index,line in enumerate(lines):
        if re.search(pattern,line,re.I): keep.update(range(max(0,index-context),min(len(lines),index+context+1)))
    selected=sorted(keep)
    return {'total_matching_context_lines':len(selected),'truncated':len(selected)>limit,'lines':[f'{i+1}: {lines[i]}' for i in selected[:limit]]}

signal=re.compile(r'(status|pass|fail|reject|repair|ambigu|identif|grammar|linter|lint|racket|four|n_test|num_test|test_count|query_count|dedup|duplicate|shortcut|surviv|violation|timeout|cost|elapsed|minutes|seconds|backend|coverage|parameter|training|approval)',re.I)
def evidence_values(value,path='$',found=None):
    found=[] if found is None else found
    if len(found)>=70: return found
    if isinstance(value,dict):
        for key,item in value.items():
            branch=path+'.'+str(key)
            if signal.search(str(key)):
                shown=item if not isinstance(item,(dict,list)) else {'type':type(item).__name__,'length':len(item)}
                if isinstance(shown,str): shown=shown[:300]
                found.append({'path':branch,'value':shown})
            if isinstance(item,(dict,list)): evidence_values(item,branch,found)
            if len(found)>=70: break
    elif isinstance(value,list):
        for index,item in enumerate(value[:8]):
            if isinstance(item,(dict,list)): evidence_values(item,f'{path}[{index}]',found)
            if len(found)>=70: break
    return found

contract=json.loads((args.work/'AUDIT_ASSIGNMENT.json').read_text())
ticket=next(t for t in contract['tickets'] if t['ticket_id']==TICKET_ID)
assert ticket['seed']==SEED and ticket['type']=='allocation_quality'
pinned=read(ticket['source']['path'])
assert pinned is not None and digest(pinned)==ticket['source']['sha256']
catalog_raw=read('repo/catalog/puzzles.jsonl'); rows=[json.loads(line) for line in catalog_raw.decode().splitlines() if line.strip()]
by_id={r['id']:r for r in rows}
sample=random.Random(int(SEED,16)).sample(sorted(manifest['all_ids']),min(3,len(manifest['all_ids'])))
policy=manifest['main_draw_policy']; normal=set(policy['normal_ids']); anchors=policy['evaluation_focus']['anchors']
focus_related={tid for a in anchors for tid in a['main_ids']}
categories={}
for field in sorted({k for row in rows for k in row if re.search(r'kind|source|origin|split|approved|weight|generator',k)}):
    counter=collections.Counter(json.dumps(row.get(field),sort_keys=True) for row in rows)
    if len(counter)<=20: categories[field]=dict(counter)

global_sources={}
for path in ['repo/src/arcpuzzles/datasets.py','repo/src/arcpuzzles/review_full_draw.py','repo/src/arcpuzzles/cli.py']:
    raw=read(path)
    if raw is not None:
        pattern=r'weight|default|approved|kind' if path.endswith('datasets.py') else (r'weight|dataset' if path.endswith('cli.py') else r'def main_selection_for_seed|normal_ids|evaluation.focus|roll|related|probability')
        global_sources[path]=excerpt(raw.decode(),pattern,context=3,limit=160)

samples=[]
for tid in sample:
    home='repo/generators/'+tid+'/'
    inventory={name[5:]:info.file_size for name,info in infos.items() if name.startswith('WORK/'+home)}
    local_home=args.work/home
    if local_home.is_dir():
        for path in local_home.rglob('*'):
            if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts: inventory[path.relative_to(args.work).as_posix()]=path.stat().st_size
    direct=[home+'generator.py',home+'notes.md',home+'SUMMARY.md',home+'evidence/review_index.json',home+'workspace/parametric/spec.md',home+'workspace/parametric/README.md']
    prototype_sources=sorted(n for n in inventory if '/workspace/parametric/' in n and n.endswith('.py'))[:8]
    candidates=[n for n in inventory if n.endswith(('.json','.md','.txt')) and re.search(r'evidence|checks|report|summary|receipt|audit|lint|grammar|parametric',n,re.I) and inventory[n]<=600000]
    def rank(name):
        return (0 if name.endswith(('review_index.json','report.json','summary.json','receipt.json')) else 1,1 if '/retained/' in name else 0,len(name.split('/')),name)
    evidence=sorted(candidates,key=rank)[:16]
    selected=list(dict.fromkeys(direct+prototype_sources+evidence))
    inspected={}
    for name in selected:
        raw=read(name)
        if raw is None: continue
        text=raw.decode(errors='replace')
        if name.endswith('.json'):
            try:
                obj=json.loads(text)
                inspected[name]={'kind':'json','top_keys':list(obj)[:30] if isinstance(obj,dict) else None,'signals':evidence_values(obj)}
            except json.JSONDecodeError: inspected[name]={'kind':'invalid_json','excerpt':text[:2000]}
        elif name.endswith('.py'):
            try:
                tree=ast.parse(text)
                defs=[{'name':n.name,'signature':ast.unparse(n.args),'line':n.lineno} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            except SyntaxError: defs=[]
            inspected[name]={'kind':'python','functions':defs,'excerpt':excerpt(text,r'param|n_test|num_test|n_train|query|rand|racket|backend|ambigu|identif|grammar|reject|repair|lint|dedup|duplicate|shortcut|def generate|yield',context=2,limit=100)}
        else: inspected[name]={'kind':'text','text':text[:12000],'truncated':len(text)>12000}
    samples.append({'task_id':tid,'catalog_record':by_id.get(tid),'manifest_record':manifest['generators'].get(tid),'in_main_ids':tid in manifest['main_ids'],'in_normal_pool':tid in normal,'in_evaluation_related_pool':tid in focus_related,'inventory':inventory,'inspected':inspected,'limits':{'inspected_evidence_candidates':min(16,len(candidates)),'available_evidence_candidates':len(candidates),'prototype_python_files_inspected':len(prototype_sources),'max_read_bytes_per_file':600000}})
result={'schema':'arcpuzzles-allocation-static-probe-v1','ticket':ticket,'source_packet':str(args.packet),'manifest_sha256':digest(manifest_raw),'started_at':start_utc,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,'method':{'sampling':'random.Random(int(ticket_seed,16)).sample(sorted(manifest.all_ids),3)','generator_executions':0,'racket_executions':0,'model_calls':0,'targeted_probe_count':1},'pools':{'all_count':len(manifest['all_ids']),'main_count':len(manifest['main_ids']),'normal_count':len(normal),'evaluation_related_count':len(focus_related),'evaluation_anchor_count':len(anchors),'evaluation_focus_policy':{k:v for k,v in policy['evaluation_focus'].items() if k!='anchors'},'evaluation_anchors':anchors,'normal_approved_count':sum(bool(manifest['generators'][t].get('approved')) for t in normal),'catalog_categories':categories},'global_source_excerpts':global_sources,'sample_ids':sample,'samples':samples,'source_bindings':bindings,'limits':['Static source/evidence inspection only; no current generator acceptance, Racket parity, linter, ambiguity, grammar, or deduplication rates measured.','At most 16 retained evidence candidates and eight parametric Python sources per sampled record; per-file limit 600000 bytes.','Historical retained results describe their recorded source/run; equal current hashes and reruns are required before treating them as current measurements.']}
args.out.parent.mkdir(parents=True,exist_ok=True)
with args.out.open('x') as out: json.dump(result,out,indent=2,sort_keys=True); out.write('\n')
print(json.dumps({'out':str(args.out),'sample_ids':sample,'elapsed_seconds':result['elapsed_seconds'],'source_count':len(bindings),'pools':result['pools'],'global_source_excerpts':global_sources,'samples':samples},indent=2,sort_keys=True))
