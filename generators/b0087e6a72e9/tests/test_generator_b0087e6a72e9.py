from __future__ import annotations
import hashlib,importlib,json,random,unittest
from collections import Counter
from pathlib import Path
T="b0087e6a72e9";M=importlib.import_module(f"puzzle_generators.per_puzzle.{T}.generator");ROOT=Path(__file__).resolve().parents[1]
BASES=["data/base/solutions/training/ce602527__b0087e6a72e9.json","data/base/solutions/augmented/ce602527__c7dc10ef1595.json"]
def rows():return [json.loads(x) for x in (ROOT/"data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(x).get("task_id")==T]
def unique_pairs():
 seen=set();out=[]
 for row in rows():
  test=row.get("test",[]);ps=row["train"]+([test] if isinstance(test,dict) else test)
  for p in ps:
   k=tuple(map(tuple,p["input"]))
   if k not in seen:seen.add(k);out.append(p)
 return out
class Tests(unittest.TestCase):
 def test_all_canonical_occurrences_and_public_profiles(self):
  self.assertEqual(sum(len(r["train"])+(1 if isinstance(r.get("test"),dict) else len(r.get("test",[]))) for r in rows()),10);self.assertEqual(len(unique_pairs()),5)
  for profile,pair in zip(M.PUBLIC_PROFILES,unique_pairs()):
   self.assertEqual(M.rule_mirror(pair["input"]),pair["output"]);self.assertEqual(M.self_check(pair["input"]),[]);self.assertEqual(M.generate(1,2,scene_profile=profile),pair["input"])
 def test_every_profile_every_band(self):
  for b in ("easy","medium","hard"):
   for p in M.GENERAL_PROFILES:
    for s in range(30):
     g=M.generate(s,s*17,difficulty=b,scene_profile=p);a=M._analysis(g);self.assertEqual(a["errors"],[],(b,p,s,a));self.assertEqual(a["scene_profile"],p);self.assertEqual(M.observe_overrides(g),{"scene_profile":p})
 def test_rank_and_crop(self):
  for p in M.GENERAL_PROFILES:
   for s in range(30):
    g=M.generate(s,s*23,scene_profile=p);a=M._analysis(g);self.assertEqual(a["selected_rank"],min(M._rank(f) for f in a["candidates"]));self.assertEqual(M.rule_mirror(g),a["selected"]["crop"])
 def test_targeted_rank_lessons(self):
  a=M._analysis(M.generate(1,2,scene_profile="tall_over_wide"));self.assertGreater(a["selected"]["height"],a["selected"]["width"])
  a=M._analysis(M.generate(2,3,scene_profile="symmetric_over_asymmetric"));self.assertTrue(a["selected"]["symmetric"])
  a=M._analysis(M.generate(3,4,scene_profile="filter_decoys"));self.assertEqual(a["candidate_count"],1);self.assertGreaterEqual(len(a["features"]),4)
 def test_distribution(self):
  ps=Counter();ins=set();outs=set();shapes=set();colors=set();ranks=set()
  for s in range(2400):
   g=M.generate(s,s*29,difficulty=("easy","medium","hard")[s%3]);a=M._analysis(g);self.assertEqual(a["errors"],[]);ps[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])));colors.update(v for row in g for v in row);ranks.add(a["selected_rank"][:3])
  self.assertEqual(set(ps),set(M.SCENE_PROFILES));self.assertGreater(len(ins),1900);self.assertGreater(len(outs),500);self.assertGreater(len(shapes),35);self.assertEqual(colors,set(range(10)));self.assertGreaterEqual(len(ranks),8)
 def test_malformed(self):
  cases=[[],[[]],[[True]],[[10]],[[0]*8 for _ in range(8)]];g=M.generate(3,4,scene_profile="area_smallest");g[0].pop();cases.append(g)
  for g in cases:self.assertTrue(M.self_check(g))
 def test_determinism_and_overrides(self):
  for o in ({"scene_profile":"bad"},{"texture":"x"},{"grid_h":12}):
   with self.assertRaises(ValueError):M.generate(1,2,**o)
  random.seed(9);state=random.getstate();a=M.generate(4,5,difficulty="hard");self.assertEqual(state,random.getstate());b=M.generate(4,5,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_hash_and_sources(self):
  source=rows()[0]["program_solution"];self.assertTrue(all(r["program_solution"]==source for r in rows()));self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
  for path in BASES:
   b=json.loads((ROOT/path).read_text());self.assertEqual(b["racket_target"]["raw_code"],source);self.assertEqual(b["racket_target"]["target_code"],source)
if __name__=="__main__":unittest.main()
