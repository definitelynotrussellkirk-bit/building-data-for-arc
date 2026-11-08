"""Focused regressions for generator 661dffbdf39a."""
from __future__ import annotations
import copy, hashlib, importlib, json, random, unittest
from collections import Counter
from pathlib import Path
TASK_ID="661dffbdf39a"; MODULE=importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator"); ROOT=Path(__file__).resolve().parents[1]
def row(): return next(json.loads(x) for x in (ROOT/"data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(x).get("task_id")==TASK_ID)
def pairs(): return row()["train"]+row()["test"]
class Tests(unittest.TestCase):
 def test_all_canonical_pairs(self):
  self.assertEqual(len(pairs()),4)
  for p in pairs(): self.assertEqual(MODULE.rule_mirror(p["input"]),p["output"])
 def test_exact_public_profiles(self):
  for profile,pair in zip(MODULE.PUBLIC_PROFILES,pairs()):
   self.assertEqual(MODULE.canonical_profile_signature(pair["input"]),profile)
   for band in ("easy","medium","hard"): self.assertEqual(MODULE.generate(7,11,difficulty=band,scene_profile=profile),pair["input"])
 def test_every_general_profile_band(self):
  for band in ("easy","medium","hard"):
   for profile,counts in MODULE.GENERAL_COUNTS.items():
    for seed in range(20):
     g=MODULE.generate(seed,seed*17+3,difficulty=band,scene_profile=profile);info=MODULE._analysis(g)
     self.assertEqual(MODULE.self_check(g),[]);self.assertEqual((len(info["rows"]),len(info["cols"])),counts);self.assertEqual(MODULE.observe_overrides(g),{"scene_profile":profile})
 def test_clean_output_semantics(self):
  for profile in MODULE.SCENE_PROFILES:
   g=MODULE.generate(101,203,scene_profile=profile);before=copy.deepcopy(g);info=MODULE._analysis(g);out=MODULE.rule_mirror(g);self.assertEqual(g,before)
   for r in range(len(g)):
    for c in range(len(g[0])):
     expected=info["marker"] if r in info["rows"] and c in info["cols"] else 5 if r in info["rows"] or c in info["cols"] else 0
     self.assertEqual(out[r][c],expected)
 def test_default_diversity(self):
  for band in ("easy","medium","hard"):
   profiles=Counter();inputs=set();outputs=set();colors=set();shapes=set()
   for seed in range(600):
    g=MODULE.generate(seed,seed*19+1,difficulty=band);info=MODULE._analysis(g);profiles[info["scene_profile"]]+=1;inputs.add(tuple(map(tuple,g)));outputs.add(tuple(map(tuple,info["output"])));colors.add(info["marker"]);shapes.add((len(g),len(g[0])))
   self.assertEqual(set(profiles),set(MODULE.SCENE_PROFILES));self.assertGreater(len(inputs),480);self.assertGreater(len(outputs),480);self.assertEqual(colors,{1,2,3,4,6,7,8,9});self.assertGreaterEqual(len(shapes),8)
 def test_malformed_and_impostors(self):
  valid=MODULE.generate(401,503,scene_profile="grid_3x4");cases=[[],[[0]],[[5,5],[5]],[[True]],[[10]]]
  no_marker=copy.deepcopy(valid)
  for r,z in enumerate(no_marker):
   for c,v in enumerate(z):
    if v not in (0,5):no_marker[r][c]=0
  cases.append(no_marker);sparse=copy.deepcopy(valid)
  for r,z in enumerate(sparse):
   for c,v in enumerate(z):
    if v==5 and (r+c)%2:sparse[r][c]=0
  cases.append(sparse)
  for g in cases:self.assertTrue(MODULE.self_check(g))
 def test_determinism_and_rejections(self):
  for ov in ({"scene_profile":"x"},{"grid_h":12},{"texture":"spread"}):
   with self.assertRaises(ValueError):MODULE.generate(1,2,**ov)
  random.seed(20260721);state=random.getstate();a=MODULE.generate(97,103,difficulty="hard");self.assertEqual(random.getstate(),state);b=MODULE.generate(97,103,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync_hash(self):
  source=row()["program_solution"];base=json.loads((ROOT/"data/base/solutions/training/95a58926__661dffbdf39a.json").read_text());self.assertEqual(base["racket_target"]["raw_code"],source);self.assertEqual(base["racket_target"]["target_code"],source);self.assertEqual(MODULE.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
if __name__=="__main__":unittest.main()
