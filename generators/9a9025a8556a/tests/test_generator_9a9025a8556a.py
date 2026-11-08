from __future__ import annotations
import copy,hashlib,importlib,json,random,unittest
from collections import Counter
from pathlib import Path
T="9a9025a8556a";M=importlib.import_module(f"puzzle_generators.per_puzzle.{T}.generator");ROOT=Path(__file__).resolve().parents[1];BASE="data/base/solutions/custom/558ea9b3__9a9025a8556a.json"
def rows():return [json.loads(x) for x in (ROOT/"data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(x).get("task_id")==T]
class Tests(unittest.TestCase):
 def test_canonical_record_and_hash(self):
  self.assertEqual(len(rows()),1);self.assertEqual(rows()[0]["train"]+rows()[0]["test"],[]);source=rows()[0]["program_solution"];self.assertEqual(M.RULE_HASH,hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]);base=json.loads((ROOT/BASE).read_text());self.assertEqual(base["racket_target"]["raw_code"],source);self.assertEqual(base["racket_target"]["target_code"],source)
 def test_every_profile_and_band(self):
  for band in ("easy","medium","hard"):
   for profile,counts in M.PROFILE_COUNTS.items():
    for seed in range(30):
     g=M.generate(seed,seed*19,difficulty=band,scene_profile=profile);a=M._analysis(g);self.assertEqual(a["errors"],[]);self.assertEqual(tuple(a["aspect_counts"][x] for x in ("tall","wide","square")),counts);self.assertEqual(a["scene_profile"],profile);self.assertEqual(M.observe_overrides(g),{"scene_profile":profile})
 def test_recolor_whole_objects_by_bbox(self):
  for profile in M.SCENE_PROFILES:
   for seed in range(80):
    g=M.generate(seed,seed*23,scene_profile=profile);a=M._analysis(g);out=a["output"]
    for x in a["records"]:
     expected=2 if x["aspect"]=="tall" else 8 if x["aspect"]=="wide" else 6
     self.assertTrue(all(out[r][c]==expected for r,c in x["cells"]))
 def test_broad_multicolor_oracle(self):
  g=[[0]*10 for _ in range(10)]
  for r in range(1,5):g[r][1]=3
  for c in range(3,8):g[1][c]=4
  for r in (6,7):
   for c in (6,7):g[r][c]=5
  expected=copy.deepcopy(g)
  for r in range(1,5):expected[r][1]=2
  for c in range(3,8):expected[1][c]=8
  self.assertEqual(M.rule_mirror(g),expected);self.assertTrue(M.self_check(g))
 def test_distribution(self):
  ps=Counter();ins=set();outs=set();shapes=set();areas=set();bboxes=set();boundary=0
  for seed in range(3000):
   g=M.generate(seed,seed*29,difficulty=("easy","medium","hard")[seed%3]);a=M._analysis(g);self.assertEqual(a["errors"],[]);ps[a["scene_profile"]]+=1;ins.add(tuple(map(tuple,g)));outs.add(tuple(map(tuple,a["output"])));shapes.add((len(g),len(g[0])))
   for x in a["records"]:areas.add(x["area"]);bboxes.add((x["bbox_height"],x["bbox_width"]));boundary+=x["touches_boundary"]
  self.assertEqual(set(ps),set(M.SCENE_PROFILES));self.assertGreater(len(ins),2900);self.assertGreater(len(outs),2900);self.assertGreater(len(shapes),150);self.assertGreater(len(areas),5);self.assertGreater(len(bboxes),12);self.assertGreater(boundary,100)
 def test_malformed_and_calibration_mutations(self):
  g=M.generate(7,11,scene_profile="dense");cases=[[],[[0]],[[True]],[[10]]];rag=copy.deepcopy(g);rag[0].pop();cases.append(rag);bad=copy.deepcopy(g);r,c=next((r,c) for r,row in enumerate(bad) for c,v in enumerate(row) if v==6);bad[r][c]=3;cases.append(bad);missing=copy.deepcopy(g);a=M._analysis(missing);x=next(x for x in a["records"] if x["aspect"]=="wide");
  for r,c in x["cells"]:missing[r][c]=0
  cases.append(missing)
  for x in cases:self.assertTrue(M.self_check(x))
 def test_errors_determinism_rng_fresh(self):
  for ov in ({"scene_profile":"bad"},{"texture":"all_tall"},{"n_tall":3}):
   with self.assertRaises(ValueError):M.generate(1,2,**ov)
  with self.assertRaises(ValueError):M.generate(1,2,difficulty="extreme")
  random.seed(41);state=random.getstate();a=M.generate(17,23,difficulty="hard");self.assertEqual(random.getstate(),state);b=M.generate(17,23,difficulty="hard");self.assertEqual(a,b);self.assertIsNot(a,b)
if __name__=="__main__":unittest.main()
