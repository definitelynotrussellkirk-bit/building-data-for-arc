"""Focused semantic regressions for generator 299bf6bf9785."""
from __future__ import annotations
from collections import Counter
import copy, hashlib, importlib, json, random, unittest
from pathlib import Path

TASK_ID = "299bf6bf9785"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]

def _row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK_ID)
def _grid(value): return [[int(v) for v in row] if isinstance(row, str) else list(row) for row in value]
def _hash(source): return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]

class Generator299bf6bf9785Tests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        pairs = _row()["train"] + _row()["test"]; self.assertEqual(len(pairs), 5); profiles=[]
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), []); self.assertEqual(MODULE.rule_mirror(source), expected)
            profiles.append(MODULE.canonical_profile_signature(source)); self.assertEqual(len(MODULE._analysis(source)["candidates"]), 3)
        self.assertEqual(profiles, list(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_are_complete_linked_inputs(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen=set()
            for seed in range(40):
                grid=MODULE.generate(seed,seed*13+1,scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid),profile)
                self.assertEqual(MODULE.observe_overrides(grid),{"scene_profile":profile});seen.add(tuple(map(tuple,grid)))
            self.assertGreater(len(seen),5)

    def test_forced_profiles_are_exact_in_every_band(self):
        for band in ("easy","medium","hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid=MODULE.generate(seed+700,seed*19+3,difficulty=band,scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid),{"scene_profile":profile})
                    self.assertEqual(MODULE.self_check(grid,meta={"overrides":{"scene_profile":profile}}),[])

    def test_candidate_counts_and_upper_median(self):
        for profile,count in (("one_rectangle",1),("two_rectangles",2),("three_rectangles",3),("four_rectangles",4),("five_rectangles",5)):
            info=MODULE._analysis(MODULE.generate(101,203,scene_profile=profile))
            self.assertEqual(len(info["candidates"]),count)
            self.assertEqual(info["target"]["size"],info["candidate_sizes"][count//2])
        two=MODULE._analysis(MODULE.generate(103,207,scene_profile="two_rectangles"))
        four=MODULE._analysis(MODULE.generate(107,211,scene_profile="four_rectangles"))
        self.assertEqual(two["target"]["size"],max(two["candidate_sizes"]))
        self.assertEqual(four["target"]["size"],four["candidate_sizes"][2])

    def test_filtering_decoys(self):
        nonsolid=MODULE._analysis(MODULE.generate(211,307,scene_profile="nonsolid_blue_decoy"))
        other=MODULE._analysis(MODULE.generate(223,311,scene_profile="solid_other_color_decoy"))
        mixed=MODULE._analysis(MODULE.generate(227,313,scene_profile="mixed_filtered_decoys"))
        self.assertTrue(nonsolid["nonsolid_blue"]); self.assertFalse(nonsolid["solid_other"])
        self.assertTrue(other["solid_other"]); self.assertFalse(other["nonsolid_blue"])
        self.assertTrue(mixed["solid_other"] and mixed["nonsolid_blue"])
        for info in (nonsolid,other,mixed): self.assertEqual(len(info["candidates"]),3)

    def test_geometry_and_spatial_shortcuts(self):
        edge=MODULE._analysis(MODULE.generate(313,419,scene_profile="median_at_edge")); target=edge["target"]
        self.assertTrue(target["r1"]==0 or target["c1"]==0 or target["r2"]==edge["height"]-1 or target["c2"]==edge["width"]-1)
        skinny=MODULE._analysis(MODULE.generate(317,421,scene_profile="median_skinny"))["target"]
        self.assertTrue(skinny["r1"]==skinny["r2"] or skinny["c1"]==skinny["c2"])
        spatial=MODULE._analysis(MODULE.generate(331,431,scene_profile="spatial_order_counterexample"))
        self.assertEqual([o["size"] for o in spatial["candidates"]],sorted(spatial["candidate_sizes"],reverse=True))

    def test_default_prior_and_diversity(self):
        for band in ("easy","medium","hard"):
            profiles=Counter();inputs=set();outputs=set()
            for seed in range(800):
                grid=MODULE.generate(seed,seed*11+1,difficulty=band);profiles[MODULE.observe_overrides(grid)["scene_profile"]]+=1
                inputs.add(tuple(map(tuple,grid)));outputs.add(tuple(map(tuple,MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles),set(MODULE.SCENE_PROFILES));strict=sum(profiles[p] for p in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict,180);self.assertLess(strict,310);self.assertGreater(len(inputs),550);self.assertGreater(len(outputs),550)

    def test_self_check_mutations(self):
        base=MODULE.generate(401,503,scene_profile="three_rectangles");empty=[[0 for _ in row] for row in base]
        tied=copy.deepcopy(base); info=MODULE._analysis(tied); small,median=info["ordered"][:2]
        # Expand the smallest into an equal-area rectangle by replacing both scenes with two 2x2 candidates.
        tied=[[0 for _ in row] for row in base]
        for r,c in ((1,1),(1,2),(2,1),(2,2),(5,1),(5,2),(6,1),(6,2)): tied[r][c]=1
        tied[9][1]=tied[9][2]=5
        ragged=copy.deepcopy(base);ragged[0].pop();invalid=copy.deepcopy(base);invalid[0][0]=10;boolean=copy.deepcopy(base);boolean[0][0]=True
        for mutation in (empty,tied,ragged,invalid,boolean):self.assertTrue(MODULE.self_check(mutation),mutation)
        self.assertTrue(MODULE.self_check(base,meta={"overrides":{"scene_profile":"two_rectangles"}}))

    def test_override_determinism_and_freshness(self):
        for overrides in ({"scene_profile":"unknown"},{"n_rects":3},{"texture":"even_count"}):
            with self.assertRaises(ValueError):MODULE.generate(1,2,**overrides)
        random.seed(20260721);state=random.getstate();first=MODULE.generate(97,103,difficulty="hard")
        self.assertEqual(random.getstate(),state);second=MODULE.generate(97,103,difficulty="hard")
        self.assertEqual(first,second);self.assertIsNot(first,second);self.assertTrue(all(a is not b for a,b in zip(first,second)))

    def test_rule_authorities_and_pin(self):
        canonical=_row()["program_solution"];base=json.loads((ROOT/"data/base/solutions/banks/4e772fa039b8/M63__299bf6bf9785.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"],canonical);self.assertEqual(base["racket_target"]["target_code"],canonical)
        self.assertEqual(MODULE.RULE_HASH,_hash(canonical));self.assertEqual(MODULE.RULE_HASH,"3cd4b679fcd2")

if __name__ == "__main__": unittest.main()
