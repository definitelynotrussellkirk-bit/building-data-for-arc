import json, hashlib, importlib.util, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root/'repo/src'),str(root/'repo/shared/runtime')]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
r=root/'checks/audit/311ebe067559'
c=json.loads((r/'candidate.json').read_text()); a=json.loads((r/'racket.json').read_text()); p=json.loads((r/'production.jsonl').read_text().splitlines()[0]); w=c['conditional_legend_rival_candidate']
g=load(root/'repo/generators/311ebe067559/generator.py','ray_source_verify')
prod=p['train']+p['test']; assert p['sample_indices']==[0,1,2,3]
assert len(a['results'])==5 and all(row['valid_output'] and not row['error'] for row in a['results'])
assert [x['input'] for x in prod]==w['inputs']
assert [x['output'] for x in prod]==[x['output'] for x in a['results'][:4]]==w['python_mirror_outputs']
assert all(not g.self_check(x['input']) for x in a['results'])
assert [x['output']==rival for x,rival in zip(prod,w['rival_outputs'])]==[True,True,True,False]
query=prod[-1]; wrong=w['rival_outputs'][-1]
diffs=[{'row':r0,'col':c0,'racket':v,'rival':wrong[r0][c0]} for r0,row in enumerate(query['output']) for c0,v in enumerate(row) if v!=wrong[r0][c0]]
report={'status':'reproduced','task_id':'311ebe067559','generator_sha256':a['generator_sha256'],
 'rule_source_sha256':a['rule_text_sha256'],'rule_hash':a['executed_rule_hash'],
 'seed':2,'difficulty':'medium','sample_indices':[0,1,2,3], 'assembly':'production generate --train 3 --test 1, contiguous samples',
 'rival':'numeric color priority instead of legend priority', 'demonstrations_fit':3,'demonstration_count':3,
 'query_disagrees':True,'query_difference_cells':diffs,'self_check_all_five_inputs':[],
 'documented_domain':'All five grids are ordinary generated inputs and pass the target self_check; no out-of-domain fabrication.',
 'actual_racket_outputs_match_production':True,'independent_mirror_matches_actual_racket':True,
 'input':query['input'],'racket_output':query['output'],'rival_output':wrong,
 'override_counterexample':c['override_counterexample'],
 'files':{name:sha(r/name) for name in ['candidate.json','input.json','racket.json','production.jsonl']},
 'replay_commands':[{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','311ebe067559','--input','../checks/audit/311ebe067559/input.json','--out','../checks/audit/311ebe067559/racket.json']},
 {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','generate','311ebe067559','--seed','2','--count','1','--train','3','--test','1','--difficulty','medium','--allow-unapproved','--out','../checks/audit/311ebe067559/production.jsonl']}]}
(r/'verified-counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
print('ray: actual Racket parity 5 records checked (four mirror-labeled lesson pairs); 3/3 demos fit rival; query difference cells',len(diffs))
r=root/'checks/audit/ba090ac77d54'; a=json.loads((r/'racket.json').read_text()); c=json.loads((r/'role-counterexample.json').read_text()); w=c['witness']
g=load(root/'repo/generators/ba090ac77d54/generator.py','voronoi_source_verify')
assert [x['input'] for x in a['results']]==[x['input'] for x in c['original_pairs']]
assert [x['output'] for x in a['results']]==[x['output'] for x in c['original_pairs']]
assert all(row['valid_output'] and not row['error'] for row in a['results'])
assert all(not g.self_check(x['input']) for x in a['results'])
fn=g.LESSON_COMPETITORS[w['rival']]; qi=w['query_index']
assert all(fn(x['input'])==x['output'] for i,x in enumerate(c['original_pairs']) if i!=qi)
assert fn(c['original_pairs'][qi]['input'])!=c['original_pairs'][qi]['output']
report={'status':'conditional_role_rotation_counterexample','task_id':'ba090ac77d54',
 'generator_sha256':a['generator_sha256'],'rule_hash':a['executed_rule_hash'],'rule_source_sha256':a['rule_text_sha256'],
 'seed':w['seed'],'difficulty':w['band'],'sample_index':w['sample_index'],
 'original_pair_indexes':list(range(5)), 'query_pair_index_after_rotation':qi,
 'demo_pair_indexes_after_rotation':w['demo_pair_indexes'], 'rival':w['rival'],
 'input':w['input'],'racket_output':w['racket_output'],'rival_output':w['rival_output'],
 'actual_racket_matches_retained_census':True, 'self_check_all_five_inputs':[],
 'documented_domain':'Unmodified production-generated inputs. The optional train/query role permutation is NOT established as a current production operation.',
 'original_order_census':{'lessons':72,'ambiguous':0},'rotated_roles':{'windows':360,'ambiguous':108,'unique_inputs':360},
 'files':{name:sha(r/name) for name in ['role-counterexample.json','input.json','racket.json']},
 'replay_command':{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','ba090ac77d54','--input','../checks/audit/ba090ac77d54/input.json','--out','../checks/audit/ba090ac77d54/racket.json']}}
(r/'verified-counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
print('voronoi: actual Racket parity 5/5; role',qi,'has 4/4 rival-consistent demonstrations and an incorrect query')
