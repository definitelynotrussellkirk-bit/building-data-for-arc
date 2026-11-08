from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
T="9e6e338d0ca7";ROOT=find_root(__file__);M,_,_=load_selected_generator(T,root=ROOT);BASE="shared/data/base/solutions/banks/0d41ded5f4cd/M88__9e6e338d0ca7.json"
def row():return next(json.loads(x) for x in canonical_path(ROOT).read_text().splitlines() if json.loads(x).get("task_id")==T)
def pairs():return [{"input":p["input"],"output":p["output"]} for p in canonical_pairs(T,root=ROOT,labeled_only=True)]
class Tests(unittest.TestCase):
 def test_all_canonical_and_public_exact(self):
  self.assertEqual(len(pairs()),5)
  for profile,p in zip(M.PUBLIC_PROFILES,pairs()):
   self.assertEqual(M.rule_mirror(p["input"]),p["output"]);self.assertEqual(M.canonical_profile_signature(p["input"]),profile);g=M.generate(1,2,scene_profile=profile);self.assertEqual(g,p["input"]);self.assertIsNot(g,M._PUBLIC_INPUTS[profile])
 def test_profiles_bands_and_seed_counts(self):
  for band in ("easy","medium","hard"):
   for profile,(nr,nc,signature,_) in M.GENERAL_SPECS.items():
    for seed in range(30):
     g=M.generate(seed,seed*19,difficulty=band,scene_profile=profile);a=M._analysis(g);self.assertEqual(a["errors"],[]);self.assertEqual((len(a["wall_rows"])-1,len(a["wall_cols"])-1),(nr,nc));self.assertEqual(tuple(sorted(a["seed_counts"])),signature);self.assertEqual(M.observe_overrides(g),{"scene_profile":profile})
 def test_generated_lessons_break_wall_only_shortcuts(self):
  def touches_wall(g,r,c):return any(0<=r+dr<len(g) and 0<=c+dc<len(g[0]) and g[r+dr][c+dc]==5 for dr,dc in M._DIRS)
  for band in ("easy","medium","hard"):
   for profile in M.GENERAL_PROFILES:
    for seed in range(30):
     g=M.generate(seed,seed*37+5,difficulty=band,scene_profile=profile);a=M._analysis(g)
     singleton_interior=any(len(seeds)==1 and not touches_wall(g,seeds[0][0],seeds[0][1]) for seeds in a["seed_cells"])
     mixed_pair=any(len(seeds)==2 and sum(touches_wall(g,r,c) for r,c,_ in seeds)==1 for seeds in a["seed_cells"])
     self.assertTrue(singleton_interior,(band,profile,seed,"no interior singleton"))
     self.assertTrue(mixed_pair,(band,profile,seed,"no mixed edge/interior pair"))

 def test_exactly_one_seed_rule(self):
  for profile in M.GENERAL_PROFILES:
   for seed in range(80):
    g=M.generate(seed,seed*23,scene_profile=profile);a=M._analysis(g);out=a["output"]
    for cells,seeds in zip(a["chambers"],a["seed_cells"]):
     if len(seeds)==1:
      color=seeds[0][2];self.assertTrue(all(out[r][c]==color for r,c in cells))
     else:self.assertTrue(all(out[r][c]==g[r][c] for r,c in cells))
 def test_same_color_conflict_stays_unfilled(self):
  for seed in range(100):
   g=M.generate(seed,seed*29,scene_profile="same_color_conflict");a=M._analysis(g)
   self.assertTrue(any(len(s)>1 and len({v for _,_,v in s})==1 for s in a["seed_cells"]))
   for cells,seeds in zip(a["chambers"],a["seed_cells"]):
    if len(seeds)>1:self.assertTrue(any(g[r][c]==0 and a["output"][r][c]==0 for r,c in cells))
 def test_distribution(self):
  ps=Counter();ins=set();outs=set();shapes=set();wall_shapes=set();qual=set();empty=set();multi=set();colors=set()
  for seed in range(3000):
   g=M.generate(seed,seed*31,difficulty=("easy","medium","hard")[seed%3]);a=M._analysis(g);self.assertEqual(a["errors"],[]);ps[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])));wall_shapes.add((len(a["wall_rows"])-1,len(a["wall_cols"])-1));qual.add(a["qualifying_count"]);empty.add(a["empty_count"]);multi.add(a["multi_count"]);colors.update(v for seeds in a["seed_cells"] for _,_,v in seeds)
  self.assertEqual(set(ps),set(M.SCENE_PROFILES));self.assertGreater(len(ins),2500);self.assertGreater(len(outs),2500);self.assertGreater(len(shapes),150);self.assertEqual(wall_shapes,{(2,2),(2,3),(3,2),(3,3)});self.assertGreater(len(qual),3);self.assertGreater(len(empty),2);self.assertGreater(len(multi),2);self.assertEqual(colors,{1,2,3,4})
 def test_malformed_and_semantic_mutations(self):
  g=M.generate(7,11,scene_profile="grid_3x3");cases=[[],[[0]],[[True]],[[10]]];rag=copy.deepcopy(g);rag[0].pop();cases.append(rag);broken=copy.deepcopy(g);broken[0][1]=0;cases.append(broken);partial=copy.deepcopy(g);r=M._analysis(g)["wall_rows"][1];partial[r][1]=0;cases.append(partial);bad=copy.deepcopy(g);r,c=next((r,c) for r,row in enumerate(bad) for c,v in enumerate(row) if v==0);bad[r][c]=7;cases.append(bad)
  for x in cases:self.assertTrue(M.self_check(x))
 def test_errors_determinism_rng(self):
  for ov in ({"scene_profile":"bad"},{"texture":"no_seed"},{"wall_rows":2}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  with self.assertRaises(ValueError):M.generate(1,2,difficulty="extreme")
  random.seed(43);state=random.getstate();a=M.generate(17,23,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(17,23,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync(self):
  source=row()["program_solution"];self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]);b=json.loads((ROOT/BASE).read_text());self.assertEqual(b["racket_target"]["raw_code"],source);self.assertEqual(b["racket_target"]["target_code"],source)
if __name__=="__main__":unittest.main()
