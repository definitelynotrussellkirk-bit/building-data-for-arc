from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from pathlib import Path
T="6c68e1b008a5";M=importlib.import_module(f"puzzle_generators.per_puzzle.{T}.generator");ROOT=Path(__file__).resolve().parents[1]
def row():return next(json.loads(x) for x in (ROOT/"data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(x).get("task_id")==T)
def pairs():
 r=row();return r["train"]+([r["test"]] if isinstance(r["test"],dict) else r["test"])
class Tests(unittest.TestCase):
 def test_canonical(self):
  self.assertEqual(len(pairs()),3)
  for p in pairs():self.assertEqual(M.rule_mirror(p["input"]),p["output"])
 def test_public(self):
  for profile,p in zip(M.PUBLIC_PROFILES,pairs()):self.assertEqual(M.canonical_profile_signature(p["input"]),profile)
 def test_profiles(self):
  for b in ("easy","medium","hard"):
   for p in M.GENERAL_PROFILES:
    for s in range(20):
     g=M.generate(s,s*11,difficulty=b,scene_profile=p);self.assertEqual(M.self_check(g),[]);self.assertEqual(M.observe_overrides(g),{"scene_profile":p});i=M._analysis(g);self.assertNotEqual(i["reference_support"],i["query_support"]);self.assertEqual(len(i["matches"]),1)
 def test_output(self):
  for p in M.SCENE_PROFILES:
   g=M.generate(3,5,scene_profile=p);before=copy.deepcopy(g);i=M._analysis(g);self.assertEqual(M.rule_mirror(g),[[8 if n in i["matches"] else 0 for n in range(3)]]);self.assertEqual(g,before)
 def test_diversity(self):
  for b in ("easy","medium","hard"):
   ps=Counter();ins=set();outs=set()
   for s in range(500):
    g=M.generate(s,s*17,difficulty=b);i=M._analysis(g);ps[i["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,i["output"])))
   self.assertEqual(set(ps),set(M.SCENE_PROFILES));self.assertGreater(len(ins),350);self.assertEqual(outs,{((8,0,0),),((0,8,0),),((0,0,8),)})
 def test_malformed(self):
  g=M.generate(1,2,scene_profile="match_1_compound");cases=[[],[[0]],[[True]],[[10]]];bad=copy.deepcopy(g);bad[0].pop();cases.append(bad);panels,_=M._split(g);panels[3]=copy.deepcopy(panels[4]);cases.append(M._assemble(panels))
  for x in cases:self.assertTrue(M.self_check(x))
 def test_determinism(self):
  for ov in ({"scene_profile":"x"},{"n_cands":3},{"texture":"x"}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  random.seed(9);state=random.getstate();a=M.generate(7,8,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(7,8,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source(self):
  base=json.loads((ROOT/"data/base/solutions/banks/9cb3cc0a41e6/S24_H1__6c68e1b008a5.json").read_text());source=row()["program_solution"];self.assertEqual(base["racket_target"]["raw_code"],source);self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]);self.assertIn("compatibility-anchor",base["racket_target"]["target_code"])
if __name__=="__main__":unittest.main()
