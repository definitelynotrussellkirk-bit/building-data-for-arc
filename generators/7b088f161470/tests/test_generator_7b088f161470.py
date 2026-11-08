from __future__ import annotations
import copy,hashlib,json,random,unittest
from collections import Counter
from reviewer_support import canonical_path,find_root,load_selected_generator
T="7b088f161470";ROOT=find_root(__file__);DATA=canonical_path(ROOT).parents[1];M,_,_=load_selected_generator(T,root=ROOT)
def rows():return [json.loads(x) for x in canonical_path(ROOT).read_text().splitlines() if json.loads(x).get("task_id")==T]
def occurrences():
 out=[]
 for r in rows():
  for s in ("train","test"):
   ps=r[s];ps=[ps] if isinstance(ps,dict) else ps;out.extend(ps)
 return out
def unique():
 seen={}
 for p in occurrences():seen.setdefault(tuple(map(tuple,p["input"])),p)
 return list(seen.values())
class Tests(unittest.TestCase):
 def test_canonical(self):
  self.assertEqual(len(occurrences()),8)
  for p in occurrences():self.assertEqual(M.rule_mirror(p["input"]),p["output"])
 def test_public(self):
  self.assertEqual(len(unique()),4)
  for name,p in zip(M.PUBLIC_PROFILES,unique()):self.assertEqual(M.canonical_profile_signature(p["input"]),name);self.assertEqual(M.generate(1,2,scene_profile=name),p["input"])
 def test_profiles(self):
  for b in ("easy","medium","hard"):
   for p,counts in M.GENERAL_COUNTS.items():
    for s in range(20):
     g=M.generate(s,s*11,difficulty=b,scene_profile=p);self.assertEqual(M.self_check(g),[]);self.assertEqual(M.observe_overrides(g),{"scene_profile":p});self.assertEqual(M._analysis(g)["rung_counts"],counts)
 def test_minimum_tie_rule(self):
  expected={(0,2,3):1,(1,2,3):0,(2,2,2):2,(2,1,3):1,(3,2,1):2,(1,3,2):0,(1,0,1):2,(0,0,0):0}
  for p,c in M.GENERAL_COUNTS.items():self.assertEqual(M._analysis(M.generate(3,5,scene_profile=p))["gray_floor_idx"],expected[c])
 def test_diversity(self):
  for b in ("easy","medium","hard"):
   ps=Counter();ins=set();outs=set();shapes=set()
   for s in range(500):
    g=M.generate(s,s*17,difficulty=b);i=M._analysis(g);ps[i["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,i["output"])));shapes.add((len(g),len(g[0])))
   self.assertEqual(set(ps),set(M.SCENE_PROFILES));self.assertGreater(len(ins),400);self.assertGreater(len(outs),30);self.assertGreater(len(shapes),15)
 def test_malformed(self):
  g=M.generate(1,2,scene_profile="counts_213");cases=[[],[[0]],[[True]],[[10]]];bad=copy.deepcopy(g);bad[0].pop();cases.append(bad);bad=copy.deepcopy(g);r,c=M._analysis(g)["gray"][0];bad[r][c]=0;cases.append(bad);bad=copy.deepcopy(g);r=M._analysis(g)["floor_rows"][-1];bad[r]=[8]*len(bad[r]);cases.append(bad)
  for x in cases:self.assertTrue(M.self_check(x))
 def test_determinism(self):
  for ov in ({"scene_profile":"x"},{"floor_count":3},{"texture":"x"}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  random.seed(9);state=random.getstate();a=M.generate(7,8,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(7,8,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source(self):
  source=rows()[0]["program_solution"];self.assertTrue(all(r["program_solution"]==source for r in rows()));self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
  for p in (DATA/"base/solutions/training/a1aa0c1e__7b088f161470.json",DATA/"base/solutions/augmented/a1aa0c1e__094112f4defd.json"):
   b=json.loads(p.read_text());want=" ".join(source.split());self.assertEqual(" ".join(b["racket_target"]["raw_code"].split()),want);self.assertEqual(" ".join(b["racket_target"]["target_code"].split()),want)
if __name__=="__main__":unittest.main()
