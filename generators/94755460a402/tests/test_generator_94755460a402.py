from __future__ import annotations
import copy, hashlib, importlib, json, random, unittest
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_path, find_root, load_selected_generator

T="94755460a402"; ROOT=find_root(__file__); M, _, _=load_selected_generator(T, root=ROOT)
def row(): return next(json.loads(x) for x in canonical_path(ROOT).read_text().splitlines() if json.loads(x).get("task_id")==T)
def pairs(): return row()["train"]+row()["test"]

class GeneratorTests(unittest.TestCase):
 def test_all_canonical_pairs(self):
  self.assertEqual(len(pairs()),5)
  for p in pairs(): self.assertEqual(M.rule_mirror(p["input"]),p["output"])
 def test_public_profiles(self):
  for profile,p in zip(M.PUBLIC_PROFILES,pairs()):
   self.assertEqual(M.canonical_profile_signature(p["input"]),profile);g=M.generate(7,11,scene_profile=profile);self.assertEqual(g,p["input"]);self.assertIsNot(g,M._PUBLIC_INPUTS[profile])
 def test_general_profiles(self):
  for band in ("easy","medium","hard"):
   for profile,(count,index,branch,duplicate) in M.GENERAL_SPECS.items():
    for seed in range(30):
     a=M._analysis(M.generate(seed,seed*29,difficulty=band,scene_profile=profile));self.assertEqual(a["errors"],[]);self.assertEqual((len(a["frames"]),a["selected_index"],a["command_branch"],len(a["matching_indices"])>1),(count,index,branch,duplicate));self.assertEqual(M.observe_overrides(M.generate(seed,seed*29,difficulty=band,scene_profile=profile)),{"scene_profile":profile})
 def test_crop_and_transforms(self):
  for profile in M.GENERAL_PROFILES:
   for seed in range(40):
    g=M.generate(seed,seed*31,scene_profile=profile);a=M._analysis(g);r1,c1,r2,c2=a["chosen"]["bbox"];motif=[x[c1+1:c2] for x in g[r1+1:r2]];self.assertEqual(a["cropped"],M._crop(motif));self.assertEqual(a["output"],M._apply(a["cropped"],a["raw_cmd"]))
 def test_counts_positions_commands_and_output_shapes(self):
  counts,positions,commands,selectors,outshapes=set(),set(),set(),set(),set()
  for seed in range(4000):
   a=M._analysis(M.generate(seed,seed*37,difficulty=("easy","medium","hard")[seed%3]));counts.add(len(a["frames"]));positions.add((len(a["frames"]),a["selected_index"]));commands.add(a["command_branch"]);selectors.add(a["selector"]);outshapes.add((len(a["output"]),len(a["output"][0])))
  self.assertEqual(counts,{2,3,4});self.assertEqual(commands,{1,2,3,4,5});self.assertEqual(selectors,set(range(1,10)));self.assertGreater(len(positions),7);self.assertGreater(len(outshapes),20)
 def test_diversity(self):
  for band in ("easy","medium","hard"):
   profiles=Counter();ins=set();outs=set();shapes=set()
   for seed in range(800):
    g=M.generate(seed,seed*41,difficulty=band);a=M._analysis(g);self.assertEqual(a["errors"],[]);profiles[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])))
   self.assertEqual(set(profiles),set(M.SCENE_PROFILES));self.assertGreater(len(ins),650);self.assertGreater(len(outs),500);self.assertGreater(len(shapes),8)
 def test_malformed(self):
  g=M.generate(5,9,scene_profile="three_middle_transpose");cases=[[],[[0]],[[True,1]],[[10,1]]];rag=copy.deepcopy(g);rag[0].pop();cases.append(rag);no_selector=copy.deepcopy(g);no_selector[0][0]=0;cases.append(no_selector);no_cmd=copy.deepcopy(g);no_cmd[0][1]=0;cases.append(no_cmd);empty=copy.deepcopy(g);a=M._analysis(empty);r1,c1,r2,c2=a["chosen"]["bbox"]
  for r in range(r1+1,r2):
   for c in range(c1+1,c2): empty[r][c]=0
  cases.append(empty)
  for case in cases:self.assertTrue(M.self_check(case))
 def test_determinism_and_errors(self):
  for ov in ({"scene_profile":"bad"},{"cmd":1},{"texture":"no_frames"}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  with self.assertRaises(ValueError):M.generate(1,2,difficulty="extreme")
  random.seed(37);state=random.getstate();a=M.generate(17,23,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(17,23,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
 def test_source_sync(self):
  source=row()["program_solution"];self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]);base_path=next(p for p in (ROOT/"data/base/solutions/banks/be1bc1d91387/H140__94755460a402.json", ROOT/"shared/data/base/solutions/banks/be1bc1d91387/H140__94755460a402.json") if p.is_file());base=json.loads(base_path.read_text());self.assertEqual(base["racket_target"]["raw_code"],source);self.assertEqual(base["racket_target"]["target_code"],source)

if __name__=="__main__":unittest.main()
