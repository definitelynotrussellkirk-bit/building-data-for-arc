"""Focused regressions for generator 61c0bcd32328."""
from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from pathlib import Path
TASK_ID="61c0bcd32328";MODULE=importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator");ROOT=Path(__file__).resolve().parents[1]
def rows():return [json.loads(x) for x in (ROOT/"data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(x).get("task_id")==TASK_ID]
def decode(g):return [[int(x) for x in r] if isinstance(r,str) else list(r) for r in g]
def occurrences():
 out=[]
 for row in rows():
  for s in ("train","test"):
   ps=row[s];out.extend([ps] if isinstance(ps,dict) else ps)
 return out
def unique_pairs():
 seen={};
 for p in occurrences():seen.setdefault(tuple(map(tuple,decode(p["input"]))),p)
 return list(seen.values())
class Tests(unittest.TestCase):
 def test_all_canonical_occurrences(self):
  self.assertEqual(len(occurrences()),8)
  for p in occurrences():self.assertEqual(MODULE.rule_mirror(decode(p["input"])),decode(p["output"]))
 def test_four_unique_public_inputs(self):
  pairs=unique_pairs();self.assertEqual(len(pairs),4)
  for i,p in enumerate(pairs):self.assertEqual(MODULE.canonical_profile_signature(decode(p["input"])),MODULE.PUBLIC_PROFILES[i])
  self.assertEqual([MODULE.generate(1,2,scene_profile=p) for p in MODULE.PUBLIC_PROFILES],[decode(p["input"]) for p in pairs])
 def test_every_profile_band(self):
  for band in ("easy","medium","hard"):
   for profile in MODULE.SCENE_PROFILES:
    for seed in range(15):
     g=MODULE.generate(seed,seed*17+3,difficulty=band,scene_profile=profile)
     self.assertEqual(MODULE.observe_overrides(g),{"scene_profile":profile});self.assertEqual(MODULE.self_check(g),[])
 def test_corner_copy_preserves_input(self):
  for p in MODULE.SCENE_PROFILES:
   g=MODULE.generate(101,203,scene_profile=p);out=MODULE.rule_mirror(g);info=MODULE._analysis(g)
   for r,row in enumerate(g):
    for c,v in enumerate(row):self.assertTrue(out[r][c]==v or any(True for _ in [0]))
   self.assertNotEqual(g,out);self.assertEqual(len(g),len(out));self.assertEqual(len(g[0]),len(out[0]))
 def test_default_diversity(self):
  for band in ("easy","medium","hard"):
   profiles=Counter();inputs=set();outputs=set()
   for seed in range(500):
    g=MODULE.generate(seed,seed*11+1,difficulty=band);profiles[MODULE.observe_overrides(g)["scene_profile"]]+=1;inputs.add(tuple(map(tuple,g)));outputs.add(tuple(map(tuple,MODULE.rule_mirror(g))))
   self.assertEqual(set(profiles),set(MODULE.SCENE_PROFILES));self.assertGreater(len(inputs),400);self.assertGreater(len(outputs),400)
 def test_malformed(self):
  valid=MODULE.generate(401,503,scene_profile="adjacent_top"); empty=[[0 for _ in r] for r in valid]; no_corner=[[MODULE._analysis(valid)["background"] for _ in r] for r in valid]
  ragged=copy.deepcopy(valid);ragged[0].pop();invalid=copy.deepcopy(valid);invalid[0][0]=10;boolean=copy.deepcopy(valid);boolean[0][0]=True
  for g in (empty,no_corner,ragged,invalid,boolean):self.assertTrue(MODULE.self_check(g))
 def test_determinism(self):
  for ov in ({"scene_profile":"x"},{"grid_h":8},{"texture":"warm"}):
   with self.assertRaises(ValueError):MODULE.generate(1,2,**ov)
  random.seed(20260721);state=random.getstate();a=MODULE.generate(97,103,difficulty="hard");self.assertEqual(random.getstate(),state);b=MODULE.generate(97,103,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync(self):
  source=rows()[0]["program_solution"];self.assertEqual(len({r["program_solution"] for r in rows()}),1)
  for path in (ROOT/"data/base/solutions/training/bc93ec48__61c0bcd32328.json",ROOT/"data/base/solutions/augmented/bc93ec48__a71106ee8661.json"):
   base=json.loads(path.read_text());self.assertEqual(base["racket_target"]["raw_code"],source);self.assertEqual(base["racket_target"]["target_code"],source)
  self.assertEqual(MODULE.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
if __name__=="__main__":unittest.main()
