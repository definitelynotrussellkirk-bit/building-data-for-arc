from pathlib import Path
import runpy,json,copy
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())
M=runpy.run_path(str(HOME/'workspace/parametric/family.py'))
def test_all_supplied_originals_and_disconnected_template():
 raw=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['edb79dae']
 gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['edb79dae']
 for pair in raw['train']:assert M['predict'](pair['input'],'once')==pair['output']
 assert M['predict'](raw['test'][0]['input'],'once')==gold[0]
 assert M['predict'](raw['test'][0]['input'],'terminal')!=gold[0]
 p=M['parse_grid'](raw['test'][0]['input'])
 assert sorted(map(len,M['groups'](p['templates'][8])))==[2,13]
 assert M['program']({'mapping_policy':'once'})==(HOME/'reference.rkt').read_text()
def test_matched_teaching_prefixes_and_public_projection():
 for seed in range(16):
  inputs=None
  for v in M['VALUES']:
   e=M['generate'](seed,{'mapping_policy':v},2,4)
   assert not M['findings'](e,v)
   grids=[p['input'] for p in e['train']+e['test']]
   if inputs is not None:assert grids==inputs
   inputs=grids
   full=M['generate'](seed,{'mapping_policy':v},6,4)
   assert full['train'][:2]==e['train'] and full['test']==e['test']
   assert len({str(g) for g in grids})==6
   for q in range(1,5):assert M['generate'](seed,{'mapping_policy':v},2,q)['test']==e['test'][:q]
   for i in range(4):
    view=M['public_turn'](e,i);changed=copy.deepcopy(e);changed['program_solution']='secret'
    for pair in changed['test']:pair['output']=[[9]]
    for j,pair in enumerate(changed['test']):
     if i!=j:pair['input']=[[9]]
    assert M['public_turn'](changed,i)==view and set(view['test'][0])=={'input'}
  assert any(len(g)==len(g[0])==30 for g in inputs)
  assert len({M['parse_grid'](g)['tile_size'] for g in inputs[2:]})==3
  branch=M['parse_grid'](inputs[1]);assert len(set(branch['mapping'].values())-set(branch['mapping']))==2

def test_standalone_canonical_runtime_generator(tmp_path):
 # Normal runtime relocates generator.py alone into per_puzzle; no workspace
 # imports or reference-file reads may be required to sample valid inputs.
 import shutil
 from puzzle_generators.base import gen_ctx
 p=tmp_path/'relocated.py';shutil.copy2(HOME/'generator.py',p);g=runpy.run_path(str(p))
 assert g['get_info']()['task_id']=='public_eval_edb79dae'
 for index in range(4):
  ctx=gen_ctx(seed=17,sample_index=index,version='1.0.0',task_id='public_eval_edb79dae')
  grid=g['generate_input'](ctx);assert not g['self_check'](grid)
  assert grid==M['draw'](17,index,branched=bool(index%2))
  assert g['rule_mirror'](grid)==M['predict'](grid,'once')
