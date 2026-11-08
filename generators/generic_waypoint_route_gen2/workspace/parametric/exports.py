"""Proposed authoring exports and protected saved-file replay; no admission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_waypoint_history_local_adapter',HERE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(adapter)
ROOT=adapter.ROOT
SCHEMA='waypoint-history-prototype-export-v1'


def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(value).hexdigest()


def _path(root,name):
    if type(name) is not str or not name or str(PurePosixPath(name))!=name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or '\\' in name:raise ValueError('Unsafe export path')
    path=root/name
    for part in (path,*path.parents):
        if part.is_symlink():raise ValueError('Symlink in export path')
    return path


def source_files():
    paths=[HERE/'adapter.py',HERE/'history.rkt',HERE/'exports.py',
           ROOT/'generators'/adapter.TASK_ID/'generator.py',ROOT/'generators'/adapter.TASK_ID/'reference.rkt']
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in paths}


def public_projection(episode):
    return {'train':[{'input':adapter.grid(p['input']),'output':adapter.grid(p['output'])} for p in episode['train']],
            'test':[{'input':adapter.grid(p['input'])} for p in episode['test']]}


class Oracle:
    def __init__(self):
        import arc_repl.racket_bridge as bridge_module
        import puzzle_generators.rule_wrap as wrap_module
        for module in (bridge_module,wrap_module):
            if not Path(module.__file__).resolve().is_relative_to(ROOT/'shared/runtime'):raise ValueError('Use a fresh process with this checkout runtime')
        self.bridge=bridge_module.RacketBridge(timeout=10,startup_timeout=45);self.wrap=wrap_module.wrap_rule;self.calls=0
        identity=self.bridge.runtime_identity
        if identity.get('protected') is not True or identity.get('backend')!='racket':self.bridge.close();raise ValueError('A protected Racket backend is required')
        self.identity={k:identity[k] for k in ['schema','backend','protected','binary_sha256','prelude_sha256','bridge_sha256','boot_script_sha256','candidate_symbol_policy_sha256'] if k in identity}
        self.programs={mode:self.wrap(adapter.program({'mode':mode})) for mode in adapter.MODES}
    def __enter__(self):return self
    def __exit__(self,*args):self.bridge.close()
    def apply(self,mode,value):
        adapter.observe(value);literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in value)+')';self.calls+=1
        return adapter.grid(self.bridge.eval_text('('+self.programs[mode]+' '+literal+')'))
    def check(self,episode,mode):
        train,test=episode['train'],episode['test'];predictions={name:[self.apply(name,p['input']) for p in train] for name in adapter.MODES}
        survivors=[name for name in adapter.MODES if all(value==p['output'] for value,p in zip(predictions[name],train))]
        if survivors!=[mode]:raise ValueError('Racket demonstrations do not identify the chosen setting')
        # Query labels never enter the inference above or adapter.certificate.
        certificate=adapter.certificate(train,[p['input'] for p in test])
        for pair in test:
            adapter.grid(pair['output'])
            if self.apply(mode,pair['input'])!=pair['output']:raise ValueError('Saved query label differs from Racket')
        return certificate


def export_batch(output,jobs,*,demos=3,queries=4):
    output=Path(output).absolute()
    for p in (output,*output.parents):
        if p.is_symlink():raise ValueError('Symlink destination')
    if output.exists():raise FileExistsError(output)
    adapter._integer(demos,'demos',3,16);adapter._integer(queries,'queries',1,32)
    if type(jobs) is not list or not 1<=len(jobs)<=32:raise ValueError('Export1..32bounded jobs')
    assets={};records=[];seen=set();bindings=source_files()
    for mode in adapter.MODES:
        raw=adapter.program({'mode':mode}).encode();assets['private/programs/'+digest(raw)+'.rkt']=raw
    with Oracle() as oracle:
        for job in jobs:
            if type(job) is not dict or set(job)!={'seed','settings'}:raise ValueError('Each job needs seed and settings')
            episode=adapter.generate(job['seed'],job['settings'],demos,queries);mode=job['settings']['mode']
            cert=oracle.check(episode,mode);public=public_projection(episode);raw=public_challenge_bytes(public);identity=public_challenge_id(public)
            if identity in seen:raise ValueError('Duplicate visible challenge; output not created')
            seen.add(identity)
            private={'schema':'waypoint-history-prototype-episode-v1','task_id':adapter.TASK_ID,'source_task_id':adapter.PARENT_TASK_ID,
                     'relationship':'semantic_variant','reference':'proposed_parametric','variant_approved':False,'training_admitted':False,
                     'public_id':identity,'seed':job['seed'],'settings':job['settings'],'train':episode['train'],'test':episode['test'],
                     'program_sha256':digest(adapter.program(job['settings']).encode()),'certificate':cert}
            public_path='public/'+identity+'.json';private_path='private/'+identity+'.json';assets[public_path]=raw;assets[private_path]=encoded(private)
            records.append({'public_id':identity,'public':public_path,'private':private_path})
        runtime=oracle.identity;evaluations=oracle.calls
    if source_files()!=bindings:raise ValueError('Authoring sources changed during export')
    manifest={'schema':SCHEMA,'visibility':'controller-only','task_id':adapter.TASK_ID,'source_task_id':adapter.PARENT_TASK_ID,
        'relationship':'semantic_variant','variant_approved':False,'training_admitted':False,'source_files':bindings,
        'programs':{mode:digest(adapter.program({'mode':mode}).encode()) for mode in adapter.MODES},
        'records':sorted(records,key=lambda r:r['public_id']),'files':{name:digest(raw) for name,raw in sorted(assets.items())},
        'racket':runtime,'racket_evaluations':evaluations,'demos':demos,'queries':queries,
        'scope':'Proposed finite rule family; no production approval, original-evaluation correctness or training admission.'}
    output.mkdir(parents=True,exist_ok=False)
    for name,raw in sorted(assets.items()):
        path=_path(output,name);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    with (output/'manifest.json').open('xb') as stream:stream.write(encoded(manifest))
    return {'episodes':len(records),'labelled_pairs':len(records)*(demos+queries),'query_labels':len(records)*queries,
            'racket':runtime,'racket_evaluations':evaluations,'training_admitted':False}


def verify_export(output):
    output=Path(output).absolute()
    for p in (output,*output.parents):
        if p.is_symlink():raise ValueError('Symlink export')
    manifest=json.loads((output/'manifest.json').read_bytes())
    if (manifest.get('schema')!=SCHEMA or manifest.get('task_id')!=adapter.TASK_ID
            or manifest.get('source_task_id')!=adapter.PARENT_TASK_ID or manifest.get('relationship')!='semantic_variant'
            or manifest.get('visibility')!='controller-only' or manifest.get('variant_approved') is not False
            or manifest.get('training_admitted') is not False):raise ValueError('Wrong proposal/admission or lineage metadata')
    if manifest.get('source_files')!=source_files():raise ValueError('Use the exact source snapshot for this export')
    adapter._integer(manifest['demos'],'demos',3,16);adapter._integer(manifest['queries'],'queries',1,32)
    actual=[]
    for path in output.rglob('*'):
        if path.is_symlink():raise ValueError('Symlink in saved export')
        if path.is_file() and path!=output/'manifest.json':actual.append(path.relative_to(output).as_posix())
    if set(actual)!=set(manifest['files']):raise ValueError('Saved inventory differs')
    for name,wanted in manifest['files'].items():
        if digest(_path(output,name).read_bytes())!=wanted:raise ValueError('Saved file hash differs')
    for mode in adapter.MODES:
        expected=adapter.program({'mode':mode}).encode();identity=digest(expected)
        if manifest['programs'].get(mode)!=identity or _path(output,'private/programs/'+identity+'.rkt').read_bytes()!=expected:raise ValueError('Declared program differs')
    records=manifest['records'];adapter._integer(len(records),'episodes',1,32);seen=set()
    if records!=sorted(records,key=lambda row:row['public_id']):raise ValueError('Records are not sorted by public identity')
    expected_files={'private/programs/'+identity+'.rkt' for identity in manifest['programs'].values()}
    for record in records:expected_files.update((record['public'],record['private']))
    if set(manifest['files'])!=expected_files:raise ValueError('Unreferenced saved inventory entry')
    with Oracle() as oracle:
        for record in records:
            private=json.loads(_path(output,record['private']).read_bytes());public_raw=_path(output,record['public']).read_bytes()
            if (private.get('schema')!='waypoint-history-prototype-episode-v1' or private.get('task_id')!=adapter.TASK_ID
                    or private.get('source_task_id')!=adapter.PARENT_TASK_ID or private.get('relationship')!='semantic_variant'
                    or private.get('reference')!='proposed_parametric' or private.get('variant_approved') is not False or private.get('training_admitted') is not False):raise ValueError('Wrong private proposal metadata')
            adapter._integer(private['seed'],'seed',0,2**63-1);mode=private['settings'].get('mode');expected_program=adapter.program(private['settings'])
            if private['program_sha256']!=digest(expected_program.encode()):raise ValueError('Private program differs')
            if len(private['train'])!=manifest['demos'] or len(private['test'])!=manifest['queries']:raise ValueError('Saved counts differ')
            reproduced=adapter.generate(private['seed'],private['settings'],manifest['demos'],manifest['queries'])
            if encoded({'train':private['train'],'test':private['test']})!=encoded({'train':reproduced['train'],'test':reproduced['test']}):raise ValueError('Saved seed does not reproduce this episode')
            for pair in private['train']+private['test']:adapter.grid(pair['input']);adapter.grid(pair['output']);adapter.observe(pair['input'])
            inputs=[encoded(pair['input']) for pair in private['train']+private['test']]
            if len(inputs)!=len(set(inputs)):raise ValueError('Duplicate saved input')
            public=public_projection(private);identity=public_challenge_id(public)
            if (identity in seen or private['public_id']!=identity or record['public_id']!=identity
                    or record['public']!='public/'+identity+'.json' or record['private']!='private/'+identity+'.json'
                    or public_raw!=public_challenge_bytes(public)):raise ValueError('Public bytes/identity/projection differ')
            seen.add(identity);certificate=oracle.check(private,mode)
            if encoded(certificate)!=encoded(private['certificate']):raise ValueError('Saved certificate differs')
        return {'episodes':len(records),'query_labels':len(records)*manifest['queries'],'racket':oracle.identity,
                'racket_evaluations':oracle.calls,'training_admitted':False,'status':'replayed_proposed_export'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    write=sub.add_parser('export');write.add_argument('--out',type=Path,required=True);write.add_argument('--seed',type=int,default=0)
    write.add_argument('--count',type=int,default=2);write.add_argument('--demos',type=int,default=3);write.add_argument('--queries',type=int,default=4)
    write.add_argument('--mode',choices=adapter.MODES+('cycle',),default='cycle')
    replay=sub.add_parser('verify');replay.add_argument('directory',type=Path)
    args=parser.parse_args()
    if args.action=='verify':result=verify_export(args.directory)
    else:
        adapter._integer(args.count,'count',1,32);jobs=[{'seed':args.seed+i,'settings':{'mode':adapter.MODES[i%2] if args.mode=='cycle' else args.mode}} for i in range(args.count)]
        result=export_batch(args.out,jobs,demos=args.demos,queries=args.queries)
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
