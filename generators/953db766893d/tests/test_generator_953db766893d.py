from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from reviewer_support import canonical_pairs, canonical_path, find_root
T="953db766893d";M=importlib.import_module(f"puzzle_generators.per_puzzle.{T}.generator");ROOT=find_root(__file__);CANONICAL=canonical_path(ROOT);DATA=CANONICAL.parent.parent
def rows():return [json.loads(x) for x in CANONICAL.read_text().splitlines() if json.loads(x).get("task_id")==T]
def occurrences():return canonical_pairs(T,root=ROOT)
def unique():
 d={}
 for p in occurrences():d.setdefault(tuple(map(tuple,p["input"])),p)
 return list(d.values())
class GeneratorTests(unittest.TestCase):
 def test_all_canonical(self):
  self.assertEqual(len(occurrences()),8)
  for p in occurrences():self.assertEqual(M.rule_mirror(p["input"]),p["output"])
 def test_public_exact(self):
  self.assertEqual(len(unique()),4)
  for profile,p in zip(M.PUBLIC_PROFILES,unique()):self.assertEqual(M.canonical_profile_signature(p["input"]),profile);g=M.generate(7,11,scene_profile=profile);self.assertEqual(g,p["input"]);self.assertIsNot(g,M._PUBLIC_INPUTS[profile])
 def test_general_profiles(self):
  for band in ("easy","medium","hard"):
   for profile,(rr,cc,merges) in M.GENERAL_SPECS.items():
    for seed in range(30):
     g=M.generate(seed,seed*29,difficulty=band,scene_profile=profile);a=M._analysis(g);self.assertEqual(a["errors"],[]);self.assertEqual((len(a["wall_rows"])+1,len(a["wall_cols"])+1,len(a["rooms"])),(rr,cc,rr*cc-merges));self.assertEqual(M.observe_overrides(g),{"scene_profile":profile})
 def test_rule_colors_all_tied_minima(self):
  for profile in M.GENERAL_PROFILES:
   for seed in range(40):
    g=M.generate(seed,seed*31,scene_profile=profile);a=M._analysis(g)
    for cells,size in zip(a["rooms"],a["room_sizes"]):
     for r,c in cells:self.assertEqual(a["output"][r][c],3 if size==a["minimum_size"] else 4)
    for r,row in enumerate(g):
     for c,v in enumerate(row):
      if v:self.assertEqual(a["output"][r][c],v)
 def test_counts_sizes_colors_dimensions(self):
  roomcounts=set();minties=set();colors=set();dims=set();mins=set()
  for seed in range(4000):
   g=M.generate(seed,seed*37,difficulty=("easy","medium","hard")[seed%3]);a=M._analysis(g);roomcounts.add(len(a["rooms"]));minties.add(a["minimum_count"]);colors.add(a["wall_color"]);dims.add((len(g),len(g[0])));mins.add(a["minimum_size"])
  self.assertGreater(len(roomcounts),6);self.assertTrue(all(x>=2 for x in minties));self.assertEqual(colors,{1,2,5,6,7,8,9});self.assertGreater(len(dims),20);self.assertGreater(len(mins),3)
 def test_diversity(self):
  for band in ("easy","medium","hard"):
   profiles=Counter();ins=set();outs=set();shapes=set()
   for seed in range(800):
    g=M.generate(seed,seed*41,difficulty=band);a=M._analysis(g);self.assertEqual(a["errors"],[]);profiles[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])))
   self.assertEqual(set(profiles),set(M.SCENE_PROFILES));self.assertGreater(len(ins),500);self.assertGreater(len(outs),500);self.assertGreater(len(shapes),10)
 def test_malformed(self):
  g=M.generate(5,9,scene_profile="three_by_three");cases=[[],[[0]],[[True]],[[10]]];rag=copy.deepcopy(g);rag[0].pop();cases.append(rag);multi=copy.deepcopy(g);r,c=next((r,c) for r,row in enumerate(multi) for c,v in enumerate(row) if v);multi[r][c]=next(v for v in (1,2,5,6,7,8,9) if v!=multi[r][c]);cases.append(multi);allzero=[[0]*8 for _ in range(8)];cases.append(allzero)
  for case in cases:self.assertTrue(M.self_check(case))
 def test_determinism_errors(self):
  for ov in ({"scene_profile":"bad"},{"wall_color":1},{"texture":"no_walls"}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  with self.assertRaises(ValueError):M.generate(1,2,difficulty="extreme")
  random.seed(37);state=random.getstate();a=M.generate(17,23,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(17,23,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync(self):
  source=rows()[0]["program_solution"];normalized=" ".join(source.split());self.assertTrue(all(r["program_solution"]==source for r in rows()));self.assertEqual(M.RULE_HASH,hashlib.sha256(normalized.encode()).hexdigest()[:12])
  for p in ("base/solutions/training/83302e8f__953db766893d.json","base/solutions/augmented/83302e8f__737c52c685fa.json"):
   b=json.loads((DATA/p).read_text());self.assertEqual(" ".join(b["racket_target"]["raw_code"].split()),normalized);self.assertEqual(" ".join(b["racket_target"]["target_code"].split()),normalized)
if __name__=="__main__":unittest.main()
