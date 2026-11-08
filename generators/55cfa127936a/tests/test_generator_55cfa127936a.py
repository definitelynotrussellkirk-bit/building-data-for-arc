"""Focused semantic regressions for generator 55cfa127936a."""
from __future__ import annotations
from collections import Counter
import copy, hashlib, importlib, json, random, unittest
from pathlib import Path
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID="55cfa127936a"
ROOT=find_root(__file__)
M, _, _ = load_selected_generator(TASK_ID, root=ROOT)
def _row(): return next(json.loads(x) for x in canonical_path(ROOT).read_text().splitlines() if json.loads(x).get("task_id")==TASK_ID)
def _grid(g): return [[int(v) for v in row] if isinstance(row,str) else list(row) for row in g]
def _hash(s): return hashlib.sha256(" ".join(s.split()).encode()).hexdigest()[:12]

class Generator55cfa127936aTests(unittest.TestCase):
 def test_all_three_canonical_pairs(self):
  pairs=_row()["train"]+[_row()["test"]]; self.assertEqual(len(pairs),3)
  for pair in pairs:
   source,target=_grid(pair["input"]),_grid(pair["output"])
   self.assertEqual(M.rule_mirror(source),target); self.assertIn(M.canonical_profile_signature(source),M.PUBLIC_PROFILES)

 def test_public_profiles_exact(self):
  expected=[_grid(p["input"]) for p in _row()["train"]+[_row()["test"]]]
  self.assertEqual([M.generate(1,2,scene_profile=p) for p in M.PUBLIC_PROFILES],expected)

 def test_every_profile_every_band(self):
  for band in ("easy","medium","hard"):
   for profile in M.SCENE_PROFILES:
    for seed in range(25):
     grid=M.generate(seed,seed*19+3,difficulty=band,scene_profile=profile)
     self.assertEqual(M.observe_overrides(grid),{"scene_profile":profile}); self.assertEqual(M.self_check(grid),[]); self.assertNotEqual(M.rule_mirror(grid),grid)

 def test_exact_topmost_selection_and_inactive_columns(self):
  for profile in M.SCENE_PROFILES:
   grid=M.generate(101,203,scene_profile=profile); info=M._analysis(grid); output=M.rule_mirror(grid)
   for col,cells in enumerate(info["positions"]):
    kept=[row for row in range(len(grid)) if output[row][col]==4]
    self.assertEqual(kept,[cells[0]] if cells else [])

 def test_count_and_activity_profiles(self):
  infos={p:M._analysis(M.generate(211,307,scene_profile=p)) for p in ("one_inactive_column","many_inactive_columns","all_columns_active","all_multi_active","two_per_active","varied_counts")}
  self.assertEqual(infos["one_inactive_column"]["inactive_columns"],1)
  self.assertGreaterEqual(infos["many_inactive_columns"]["inactive_columns"],3)
  self.assertEqual(infos["all_columns_active"]["inactive_columns"],0)
  self.assertGreaterEqual(min(infos["all_multi_active"]["active_counts"]),2)
  self.assertEqual(set(infos["two_per_active"]["active_counts"]),{2})
  self.assertGreaterEqual(len(set(infos["varied_counts"]["active_counts"])),4)

 def test_geometric_stack_profiles(self):
  top=M._analysis(M.generate(223,311,scene_profile="top_boundary")); bottom=M._analysis(M.generate(227,313,scene_profile="bottom_topmost"))
  consecutive=M._analysis(M.generate(229,317,scene_profile="consecutive_stacks")); spaced=M._analysis(M.generate(233,319,scene_profile="spaced_stacks"))
  full=M._analysis(M.generate(239,323,scene_profile="full_columns")); shared=M._analysis(M.generate(241,327,scene_profile="shared_top_row"))
  self.assertTrue(all(cells[0]==0 for cells in top["positions"] if cells)); self.assertTrue(all(cells[0]>=bottom["height"]//2 for cells in bottom["positions"] if cells))
  self.assertTrue(all(all(b==a+1 for a,b in zip(c,c[1:])) for c in consecutive["positions"] if c))
  self.assertTrue(all(all(b>=a+2 for a,b in zip(c,c[1:])) for c in spaced["positions"] if c))
  self.assertTrue(all(len(c)==full["height"] for c in full["positions"] if c))
  self.assertEqual(len({c[0] for c in shared["positions"] if c}),1)

 def test_default_census_and_diversity(self):
  for band in ("easy","medium","hard"):
   profiles,pairs=Counter(),set()
   for seed in range(800):
    grid=M.generate(seed,seed*11+1,difficulty=band); profiles[M.observe_overrides(grid)["scene_profile"]]+=1
    pairs.add((tuple(map(tuple,grid)),tuple(map(tuple,M.rule_mirror(grid)))))
   self.assertEqual(set(profiles),set(M.SCENE_PROFILES)); public=sum(profiles[p] for p in M.PUBLIC_PROFILES)
   self.assertTrue(100<public<220); self.assertGreater(len(pairs),620)

 def test_self_check_rejects_minimal_and_malformed(self):
  base=M.generate(401,503,scene_profile="mixed_counts"); h,w=len(base),len(base[0]); empty=[[0]*w for _ in range(h)]
  singleton=copy.deepcopy(empty);singleton[1][1]=4
  line=copy.deepcopy(empty);line[1][1:5]=[4]*4
  block=copy.deepcopy(empty);block[1][1]=block[1][2]=block[2][1]=block[2][2]=4
  full=[[4]*w for _ in range(h)]; ragged=copy.deepcopy(base);ragged[0].pop(); invalid=copy.deepcopy(base);invalid[0][0]=3; boolean=copy.deepcopy(base);boolean[0][0]=True
  for mutation in (empty,singleton,line,block,full,ragged,invalid,boolean): self.assertTrue(M.self_check(mutation),mutation)
  self.assertTrue(M.self_check(base,meta={"overrides":{"scene_profile":"two_per_active"}}))

 def test_determinism_freshness_rng_unknown_axes(self):
  for o in ({"scene_profile":"unknown"},{"grid_h":6},{"active_cols":4},{"texture":"full_grid"}):
   with self.assertRaises(ValueError): M.generate(1,2,**o)
  random.seed(20260721); state=random.getstate(); first=M.generate(97,103,difficulty="hard"); self.assertEqual(random.getstate(),state)
  second=M.generate(97,103,difficulty="hard");self.assertEqual(first,second);self.assertIsNot(first,second);self.assertTrue(all(a is not b for a,b in zip(first,second)))

 def test_source_and_pin(self):
  canonical=_row()["program_solution"]; base=json.loads((ROOT/"shared/data/base/solutions/banks/6bdef6f37fa3/S7_E6__55cfa127936a.json").read_text())
  self.assertEqual(base["racket_target"]["raw_code"],canonical);self.assertEqual(base["racket_target"]["target_code"],canonical)
  self.assertEqual(M.RULE_HASH,_hash(canonical));self.assertEqual(M.RULE_HASH,"4ad262163127")

if __name__=="__main__": unittest.main()
