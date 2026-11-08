from pathlib import Path
import importlib.util
import unittest
H=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('test_union',H/'workspace/parametric/union.py');u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
class UnionTests(unittest.TestCase):
 def test_exact_default_and_aliases(self):
  self.assertEqual(u.program(),(H/'reference.rkt').read_text())
  for mode in ('ink','holes'):self.assertEqual(u.program({'tile_mask':mode}),u.program({'rule':mode}))
  self.assertEqual(u.program({'layout':'as_drawn'}),u.program({'rule':'ink'}))
  self.assertEqual(u.program({'layout':'clockwise'}),u.program({'rule':'clockwise'}))
 def test_minimum_lesson_32_seeds(self):
  for seed in range(32):
   bank=u.inputs(seed)
   self.assertEqual(len({repr(g) for g in bank}),10)
   self.assertEqual(sum(len(g)==len(g[0])==30 for g in bank[6:]),2)
   for mode in u.OPTIONS:
    for name in u.rivals(mode):self.assertTrue(any(u.solve(g,mode)!=u.rival_predict(g,mode,name) for g in bank[:2]),(seed,mode,name))
 def test_matched_settings_and_count_prefixes(self):
  for seed in (0,17,43):
   full=u.generate(seed,{'rule':'ink'},6,4)
   for mode in u.OPTIONS:
    for n in range(2,7):
     for q in range(1,5):
      x=u.generate(seed,{'rule':mode},n,q)
      self.assertEqual([p['input'] for p in x['train']],[p['input'] for p in full['train'][:n]])
      self.assertEqual([p['input'] for p in x['test']],[p['input'] for p in full['test'][:q]])
 def test_controls(self):
  for args in ((True,None,2,4),(0,None,1,4),(0,None,2,5),(0,{'rule':'bad'},2,4)):
   with self.assertRaises(ValueError):u.generate(*args)
