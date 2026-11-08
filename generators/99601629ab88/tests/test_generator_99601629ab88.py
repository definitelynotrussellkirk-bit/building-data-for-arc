from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from reviewer_support import canonical_pairs,canonical_path,find_root
T="99601629ab88";M=importlib.import_module(f"puzzle_generators.per_puzzle.{T}.generator");ROOT=find_root(__file__);CANONICAL=canonical_path(ROOT);DATA=CANONICAL.parent.parent
BASES=(DATA/"base/solutions/training/9f236235__99601629ab88.json",DATA/"base/solutions/augmented/9f236235__9fdcb4b428fd.json")
def rows():return [json.loads(x) for x in CANONICAL.read_text().splitlines() if json.loads(x).get("task_id")==T]
def pairs():return canonical_pairs(T,root=ROOT)
def unique():
 out=[]
 for p in pairs():
  if not any(x["input"]==p["input"] for x in out):out.append(p)
 return out
class Tests(unittest.TestCase):
 def test_canonical_and_exact_public(self):
  self.assertEqual((len(rows()),len(pairs()),len(unique())),(2,8,4))
  for p in pairs():self.assertEqual(M.rule_mirror(p["input"]),p["output"])
  for profile,p in zip(M.PUBLIC_PROFILES,unique()):
   self.assertEqual(M.canonical_profile_signature(p["input"]),profile);g=M.generate(1,2,scene_profile=profile);self.assertEqual(g,p["input"]);self.assertIsNot(g,M._PUBLIC_INPUTS[profile])
 def test_profiles_bands_and_uniform_blocks(self):
  for band in ("easy","medium","hard"):
   for profile in M.GENERAL_PROFILES:
    nr,nc=map(int,profile.removeprefix("lattice_").split("x"))
    for seed in range(30):
     g=M.generate(seed,seed*17,difficulty=band,scene_profile=profile);a=M._analysis(g);self.assertEqual(a["errors"],[]);self.assertEqual((len(a["matrix"]),len(a["matrix"][0])),(nr,nc));self.assertEqual(a["output"],[list(reversed(x)) for x in a["matrix"]]);self.assertEqual(M.observe_overrides(g),{"scene_profile":profile})
 def test_distribution(self):
  profiles=Counter();ins=set();outs=set();shapes=set();odims=set();colors=set()
  for seed in range(3000):
   g=M.generate(seed,seed*31,difficulty=("easy","medium","hard")[seed%3]);a=M._analysis(g);self.assertEqual(a["errors"],[]);profiles[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])));odims.add((len(a["output"]),len(a["output"][0])));colors.add(a["divider_color"])
  self.assertEqual(set(profiles),set(M.SCENE_PROFILES));self.assertGreater(len(ins),2500);self.assertGreater(len(outs),2500);self.assertGreater(len(shapes),100);self.assertEqual(len(odims),9);self.assertEqual(colors,set(range(1,10)))
 def test_flip_visible_and_irregular_sizes(self):
  sizes=set()
  for p in M.GENERAL_PROFILES:
   for s in range(100):
    a=M._analysis(M.generate(s,s*37,scene_profile=p));self.assertTrue(any(row!=list(reversed(row)) for row in a["matrix"]));sizes.update(b-a for a,b in a["row_ranges"]+a["col_ranges"])
  self.assertTrue({3,4,5}.issubset(sizes))
 def test_malformed(self):
  g=M.generate(4,7,scene_profile="lattice_3x4");cases=[[],[[0]],[[True]],[[10]]];rag=copy.deepcopy(g);rag[0].pop();cases.append(rag);broken=copy.deepcopy(g);r=M._analysis(g)["divider_rows"][0];broken[r][0]=0;cases.append(broken);nonuniform=copy.deepcopy(g);a=M._analysis(g);r0,r1=a["row_ranges"][0];c0,c1=a["col_ranges"][0];nonuniform[r1-1][c1-1]=next(v for v in range(10) if v!=nonuniform[r0][c0] and v!=a["divider_color"]);cases.append(nonuniform)
  for x in cases:self.assertTrue(M.self_check(x))
 def test_errors_determinism_rng(self):
  for ov in ({"scene_profile":"bad"},{"divider_count":2},{"texture":"warm"}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  with self.assertRaises(ValueError):M.generate(1,2,difficulty="extreme")
  random.seed(31);state=random.getstate();a=M.generate(8,9,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(8,9,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync(self):
  source=rows()[0]["program_solution"];normalized=" ".join(source.split());self.assertTrue(all(r["program_solution"]==source for r in rows()));self.assertEqual(M.RULE_HASH,hashlib.sha256(normalized.encode()).hexdigest()[:12])
  for p in BASES:
   b=json.loads(p.read_text());self.assertEqual(" ".join(b["racket_target"]["raw_code"].split()),normalized);self.assertEqual(" ".join(b["racket_target"]["target_code"].split()),normalized)
if __name__=="__main__":unittest.main()
