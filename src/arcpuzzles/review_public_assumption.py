"""Explicit owner-only d8e07eb2 derived-spec admission.

This is not ordinary public-original verification. No official data is edited;
ordinary public preflight and verified_coverage remain strict and unchanged.
The exact owner-authorized interpretation, raw discrepancy and derived authority
are required. Native qualification/acceptance and protected labels are unchanged.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile
from .catalog import Catalog, sha256
from .review_public_creation import digest, authoring_contract, _base_generation
from .review_public_admission import _parent, _register, _approve, _write, _regular

TASK = 'public_eval_d8e07eb2'
RULE_SHA256 = 'a25ccaf803d30af2f2e3ed6d7766372da0ffd495074ed703b0a433ea7abfd651'
SOURCE_SHA256 = '6dece13d6599eea896cbb0ebece1f8098a602b601f2030026d3674cc08b4155c'
GOLD_SHA256 = '6ce07d1163e8f9669d0b539a6322265a57338acd269781d5e42f910a07093f86'
DISPUTED = [(1,7,1,2),(1,8,1,2),(1,9,1,3),(2,7,3,2),(2,8,1,2),
            (2,9,3,2),(3,7,1,3),(3,8,1,2),(3,9,1,3)]
REGISTRY = 'REVIEW/public-eval-owner-assumed-current.json'

def validate_authority(root, task_id=TASK):
    root = Path(root).resolve()
    if task_id != TASK:
        raise ValueError('Owner assumption authorized only for d8e07eb2')
    home = root / 'generators' / TASK
    target = json.loads(_regular(root, f'generators/{TASK}/workspace/public-parent.json').read_text())
    item = {k: target[k] for k in ('public_task_id','task_id','source_path','challenge_sha256','source_record_sha256','test_outputs_sha256','needs_creation')}
    if (item['source_record_sha256'] != SOURCE_SHA256 or item['challenge_sha256'] != SOURCE_SHA256
            or item['test_outputs_sha256'] != GOLD_SHA256):
        raise ValueError('Owner assumption is bound to exact original source/gold')
    parent = _parent(root, item)
    reference = _regular(root, f'generators/{TASK}/reference.rkt')
    if sha256(reference) != RULE_SHA256:
        raise ValueError('Owner assumption does not authorize different reference bytes')
    decision_path = _regular(root, f'generators/{TASK}/evidence/interpretation-decision-current.json')
    decision = json.loads(decision_path.read_text())
    if (decision.get('status') != 'owner_assumed_rule_selected' or decision.get('task_id') != TASK
            or decision.get('canonical_rule_sha256') != RULE_SHA256
            or decision.get('original_intent_verified') is not False
            or decision.get('owner_wait_revoked') is not True
            or decision.get('source_record_sha256') != SOURCE_SHA256
            or decision.get('test_outputs_sha256') != GOLD_SHA256):
        raise ValueError('Missing explicit exact-source owner assumption decision')
    return home, item, parent, reference.read_text(), sha256(decision_path)

def check_discrepancies(rows):
    mismatches = [r for r in rows if r['differences']]
    want = [{'row':r,'col':c,'derived':a,'original':b} for r,c,a,b in DISPUTED]
    if (len(rows) != 7 or len(mismatches) != 1 or mismatches[0]['split'] != 'train'
            or mismatches[0]['index'] != 0 or mismatches[0]['differences'] != want):
        raise ValueError('Raw original discrepancy differs from the nine-cell owner authorization')

def _derived_metadata(root, authority):
    """Label only the selected row and canonical record; preserve raw source."""
    from .review import _lock
    with _lock(root / 'REVIEW'):
        catalog = Catalog(root); rid = catalog._records[TASK]['rule_task_id']
        for path, field, value in [('catalog/puzzles.jsonl','id',TASK),
                                  ('shared/data/canonical/puzzles.jsonl','task_id',rid)]:
            p = root / path; lines = []
            for line in p.read_text().splitlines(keepends=True):
                row = json.loads(line)
                if row.get(field) == value:
                    row['label_authority'] = 'owner_assumed_derived_spec'
                    row['owner_assumption'] = authority
                    row['original_gold_verified'] = False
                    if field == 'id':
                        row['review_status'] = 'owner_assumed_derived_spec_executed'
                    line = json.dumps(row, ensure_ascii=False) + '\n'
                lines.append(line)
            pending = p.with_suffix(p.suffix + '.owner-assumption.tmp')
            try:
                pending.write_text(''.join(lines))
                pending.replace(p)
            finally:
                pending.unlink(missing_ok=True)
    return Catalog(root)

def accept_owner_assumption(root, *, task_id=TASK):
    """Owner action: fresh raw replay, generated-label checks and native admission."""
    from .parametric_worker import _local_imports, _real_evaluator, _grid
    from .parametric_manifest import build_manifest
    from . import parametric_promotion as native
    from .review_programs import strict_programs
    from .review_sequential_replay import replay_witness
    root = Path(root).resolve()
    home,item,parent,program,decision_hash = validate_authority(root,task_id)
    raw_paths = [root/item['source_path'],root/'shared/data/raw/arc-agi_evaluation_solutions.json']
    raw_hashes = [sha256(p) for p in raw_paths]
    base = home/'workspace/parametric'; contract = authoring_contract(root,TASK)
    folder = Path(tempfile.mkdtemp(prefix='execution-',dir=_make(home/'evidence/owner-assumption')))
    source = {p.relative_to(root).as_posix():sha256(p) for p in home.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))}
    corrected = copy.deepcopy(parent); original_rows=[]; episodes=[]; checks=[]; causal=[]
    with _local_imports(root/'shared/runtime',base):
        spec=importlib.util.spec_from_file_location('_owner_assumed_adapter',base/'adapter.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        programs={mode:adapter.program({'match':mode}) for mode in ('color_shape','shape_only')}
        if programs['color_shape'] != program:raise ValueError('Default differs from assumed rule')
        strict_programs(root,list(programs.values()))
        apply,identity,bridge = _real_evaluator(root/'shared/runtime')
        try:
            for split in ('train','test'):
                for i,pair in enumerate(parent[split]):
                    grid=lambda g:[[int(v) for v in r]for r in g]
                    inp=grid(pair['input']);gold=grid(pair['output']);actual=_grid(apply(program,inp))
                    differences=[dict(row=r,col=c,derived=v,original=gold[r][c]) for r,row in enumerate(actual) for c,v in enumerate(row) if v!=gold[r][c]]
                    original_rows.append(dict(split=split,index=i,differences=differences,input=inp,original_output=gold,derived_output=actual))
                    corrected[split][i]={'input':inp,'output':actual}
            check_discrepancies(original_rows)
            for mode in programs:
                for seed in (17,43):
                    ep=adapter.generate(seed,{'match':mode},4,4)
                    for split in ('train','test'):
                        for pair in ep[split]:
                            if _grid(apply(programs[mode],pair['input'])) != pair['output']:raise ValueError('Generated Racket label mismatch')
                    survivors=[other for other in programs if all(_grid(apply(programs[other],p['input']))==p['output'] for p in ep['train'])]
                    if survivors != [mode]:raise ValueError('Demonstrations do not identify parameter')
                    checks.append(dict(mode=mode,seed=seed,survivors=survivors,protected_labels=8))
                    episodes.append(dict(settings={'match':mode},seed=seed,**ep))
                    if mode=='color_shape':
                        p=ep['train'][2];other=_grid(apply(programs['shape_only'],p['input']))
                        if other==p['output']:raise ValueError('Causal match-set ablation has no effect')
                        causal.append(dict(input=p['input'],output=p['output'],program=program,
                                           counterfactual_program=programs['shape_only'],counterfactual_output=other,
                                           intermediate={'exact_matched_slots':sorted(adapter.matched_positions(adapter.parse(p['input']),'color_shape')),
                                                         'shape_only_slots':sorted(adapter.matched_positions(adapter.parse(p['input']),'shape_only'))}))
            spec=importlib.util.spec_from_file_location('_owner_assumed_base',home/'generator.py');generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
            base_checks=_base_generation(generator,apply,program)
        finally:bridge.close()
    _write(folder/'raw-original-execution.json',dict(status='six_of_seven_originals_match',matches=6,total=7,pairs=original_rows,racket=identity,original_intent_verified=False))
    _write(folder/'derived-spec.json',dict(schema='arcpuzzles-owner-assumed-derived-spec-v1',public_creation=item,original_source_sha256=SOURCE_SHA256,original_test_gold_sha256=GOLD_SHA256,decision_sha256=decision_hash,program_sha256=RULE_SHA256,derived_pairs=corrected,raw_original_matches=6,raw_original_total=7))
    authority=dict(schema='arcpuzzles-owner-assumed-label-authority-v1',kind='owner_assumed_derived_spec',decision_path=f'generators/{TASK}/evidence/interpretation-decision-current.json',decision_sha256=decision_hash,derived_spec_path=(folder/'derived-spec.json').relative_to(root).as_posix(),derived_spec_sha256=sha256(folder/'derived-spec.json'),raw_original_matches=6,raw_original_total=7,original_intent_verified=False)
    _write(folder/'execution.json',dict(checks=checks,episodes=episodes,base_generation=base_checks,racket=identity))
    witness=dict(step_a='Match header symbols to board slots under the episode matching rule.',intermediate='The matched slot set.',step_b='Highlight matched slots and decide whether the set contains a complete row or column.',why_b_depends_on_a='A differently colored same-shape near-line member changes the match set and thereby changes failure to success under shape-only matching.',cases=causal)
    _write(folder/'causal-witness.json',witness);_write(folder/'causal-replay.json',replay_witness(root,witness,timeout=60))
    if any(sha256(root/p)!=h for p,h in source.items()):raise ValueError('Task source changed during execution')
    live=_register(Catalog(root),item,corrected,program)
    live=_derived_metadata(root,authority)
    relocated=live.generate(TASK,seed=29,n_train=4,n_test=4,allow_unapproved=True)
    _write(folder/'relocated-base.json',dict(status='passed',episodes=relocated,scope='Copied runtime and protected Racket canonical labels'))
    live=_approve(live,TASK);live=_derived_metadata(root,authority)
    manifest=base/'evidence/manifest.json'
    build_manifest(live,TASK,evidence=folder.relative_to(root).as_posix(),include=[f'generators/{TASK}/tests',f'generators/{TASK}/evidence/interpretation-decision-current.json'],reported_checks='Owner-assumed derived spec only: raw originals 6/7; exact nine cells retained; generated labels protected-Racket checked, finite rivals and causal replay; relocated base executed.',replace_sha256=sha256(manifest) if manifest.exists() else None)
    scratch=root/'var/review/owner-assumed-native';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        qualified=native.qualify(Catalog(root),TASK,Path(tmp)/'qualification',demos=4)
        accepted=native.accept(Catalog(root),TASK,qualified['receipt'],reason='Explicit owner-assumed derived spec; raw originals remain 6/7; protected generated labels, causal/relocated checks and fresh native acceptance.')
    state=native.status(Catalog(root),TASK)
    if state['status']!='accepted' or accepted['status']!='accepted':raise ValueError('Native acceptance failed')
    if [sha256(p) for p in raw_paths]!=raw_hashes:raise ValueError('Immutable original source changed')
    result=dict(schema='arcpuzzles-owner-assumed-admission-v1',status='accepted',objective_met=True,task_id=TASK,public_creation=item,originals_owner_executed=True,original_gold_verified=False,original_intent_verified=False,raw_original_matches=6,raw_original_total=7,label_authority='owner_assumed_derived_spec',authority=authority,acceptance_sha256=state['acceptance_sha256'],reference_sha256=RULE_SHA256,training_admitted=False,verification_status='owner_assumed_native_admission',evidence_directory=folder.relative_to(root).as_posix())
    _write(home/'evidence/parametric-admission-current.json',result)
    _write(root/REGISTRY,dict(schema='arcpuzzles-public-eval-owner-assumed-coverage-v1',parents={item['public_task_id']:result}))
    return result

def _make(path):
    path.mkdir(parents=True,exist_ok=True)
    return path

def verified_assumed_coverage(root):
    """Current source-bound assumed coverage, deliberately separate from verified originals."""
    from . import parametric_promotion as native
    root=Path(root).resolve()
    try:
        home,item,parent,program,decision_hash=validate_authority(root)
        registry=json.loads(_regular(root,REGISTRY).read_text())
        if registry.get('schema')!='arcpuzzles-public-eval-owner-assumed-coverage-v1':return []
        result=registry['parents'][item['public_task_id']]
        if (result.get('status')!='accepted' or result.get('label_authority')!='owner_assumed_derived_spec'
                or result.get('original_gold_verified') is not False or result.get('original_intent_verified') is not False
                or result.get('raw_original_matches')!=6 or result.get('raw_original_total')!=7
                or result.get('public_creation')!=item):return []
        authority=result['authority']
        if authority['decision_sha256']!=decision_hash:return []
        specpath=_regular(root,authority['derived_spec_path'])
        if sha256(specpath)!=authority['derived_spec_sha256']:return []
        spec=json.loads(specpath.read_text())
        if (spec['public_creation']!=item or spec['program_sha256']!=RULE_SHA256
                or spec['decision_sha256']!=decision_hash):return []
        proof=json.loads(_regular(root,(specpath.parent/'raw-original-execution.json').relative_to(root).as_posix()).read_text())
        if not proof['racket']['protected'] or proof['racket']['backend']!='racket':return []
        check_discrepancies(proof['pairs'])
        grid=lambda g:[[int(v)for v in r]for r in g]
        for row in proof['pairs']:
            raw=parent[row['split']][row['index']]
            derived=spec['derived_pairs'][row['split']][row['index']]
            if (row['input']!=grid(raw['input']) or row['original_output']!=grid(raw['output'])
                    or derived!={'input':row['input'],'output':row['derived_output']}):return []
        catalog=Catalog(root);record=catalog._records[TASK]
        if record.get('owner_assumption')!=authority or record.get('label_authority')!='owner_assumed_derived_spec':return []
        variants=catalog._variants()[record['rule_task_id']]
        if len(variants)!=1:return []
        v=variants[0]
        if (v.get('owner_assumption')!=authority or v.get('label_authority')!='owner_assumed_derived_spec'
                or any(v[split]!=spec['derived_pairs'][split]for split in ('train','test'))):return []
        state=native.status(catalog,TASK)
        if state['status']!='accepted' or state['acceptance_sha256']!=result['acceptance_sha256']:return []
        return [item['public_task_id']]
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return []
