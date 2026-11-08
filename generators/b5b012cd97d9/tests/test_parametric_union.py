"""Regression checks for the exact-policy union and retained sampler coverage."""
from pathlib import Path
import hashlib,importlib.util,sys
import pytest
from reviewer_support import find_root
HOME=find_root(__file__)/'generators/b5b012cd97d9/workspace/parametric'
spec=importlib.util.spec_from_file_location('_b5_union_tests',HOME/'union_family.py')
u=importlib.util.module_from_spec(spec);sys.modules[spec.name]=u;spec.loader.exec_module(u)

def test_original_programs_keep_exact_identities():
 expected={'next_repeated':'27f6a42c783057ca3e60a9601751d5ce788cfc0b273a3249efdea9fca5b5e6b4','big_side_relay':'7ac6027ec310bd978825feadc80814c6c3f1c770f3cba5c8d0d26b29feeb0406','preserve_vertical':'5972e17ebef6d3917c42626294303de28e422e9b27548df8b149d05323c1d297'}
 for p,h in expected.items():assert hashlib.sha256(u.program({'secondary':p}).encode()).hexdigest()==h
 assert u.vertical.program({'placement':'canonical'})==u.program({'secondary':'next_repeated'})

def test_disjoint_banks_preserve_exact_original_queries_and_all_demo_profiles():
 seen={0:set(),1:set()}
 for source_seed in range(10):
  for bank in (0,1):
   inputs=u.sample_inputs(2*source_seed+bank,demos=6,queries=4)
   expected=(u.relay.sample_inputs(source_seed,demos=6,queries=4)[6:] if bank==0 else [u.vertical.sample_input(source_seed,'test',i) for i in range(4)])
   assert inputs[6:]==expected
   seen[bank].update((len(g),len(g[0])) for g in inputs[:6])
 for bank in (0,1):
  originals=(u.relay.sample_inputs(0,demos=6,queries=4)[:6] if bank==0 else [u.vertical.sample_input(0,'train',i) for i in range(6)])
  assert {(len(g),len(g[0])) for g in originals} <= seen[bank]

def test_common_lesson_identifies_all_policies_and_projection_hides_private_fields():
 for seed in (0,1,34,35):
  eps={p:u.generate(seed,{'secondary':p},3,4) for p in u.SECONDARY_SETTINGS}
  for p,e in eps.items():
   assert [q for q,v in eps.items() if v['train']==e['train']]==[p]
   short=u.generate(seed,{'secondary':p},3,1)
   assert u.public_turn(short)==u.public_turn(e)
   public=u.public_turn(e)
   assert set(public)=={'train','test'} and set(public['test'][0])=={'input'}

@pytest.mark.parametrize('seed,demos,queries',[(True,3,4),(-1,3,4),(0,2,4),(0,7,4),(0,True,4),(0,3,True),(0,3,0),(0,3,5)])
def test_union_request_bounds_are_strict(seed,demos,queries):
 with pytest.raises(ValueError):u.generate(seed,{'secondary':'next_repeated'},demos,queries)
