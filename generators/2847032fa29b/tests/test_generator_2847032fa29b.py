"""Focused semantic regressions for generator 2847032fa29b."""
from __future__ import annotations
from collections import Counter
import copy, hashlib, importlib, json, random, unittest
from pathlib import Path

TASK_ID = "2847032fa29b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]

def _canonical_row():
    return next(json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK_ID)

def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]

def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]

class Generator2847032fa29bTests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        row = _canonical_row(); pairs = row["train"] + row["test"]
        self.assertEqual(len(pairs), 5); profiles = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profiles.append(MODULE.canonical_profile_signature(source))
            self.assertEqual(len(MODULE._analysis(source)["components"]), 3)
        self.assertEqual(profiles, list(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_preserve_complete_linked_masks(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 30)

    def test_forced_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}), [])

    def test_sort_priority_and_object_counts(self):
        for profile, count in (("two_objects", 2), ("four_objects", 4), ("five_objects", 5)):
            info = MODULE._analysis(MODULE.generate(101, 203, scene_profile=profile))
            self.assertEqual(len(info["components"]), count)
        equal = MODULE._analysis(MODULE.generate(103, 207, scene_profile="equal_size_color_order"))
        self.assertEqual(len(set(equal["sizes"])), 1)
        self.assertEqual([c["color"] for c in equal["ordered"]], sorted(c["color"] for c in equal["ordered"]))
        priority = MODULE._analysis(MODULE.generate(107, 211, scene_profile="size_over_color"))
        self.assertEqual([c["color"] for c in priority["ordered"]], sorted(priority["colors"], reverse=True))

    def test_cell_count_not_bbox_area_and_top_alignment(self):
        counter = MODULE._analysis(MODULE.generate(211, 307, scene_profile="cell_count_not_bbox_area"))
        self.assertTrue(any(counter["bbox_areas"][i] > counter["bbox_areas"][i + 1] for i in range(2)))
        tall = MODULE._analysis(MODULE.generate(223, 311, scene_profile="tall_wide_alignment"))
        self.assertGreaterEqual(max(len(crop) for crop in tall["crops"]), 6)
        self.assertGreaterEqual(max(len(crop[0]) for crop in tall["crops"]), 6)
        self.assertEqual(tall["output_shape"][0], max(len(crop) for crop in tall["crops"]))

    def test_literal_foreign_hollow_and_same_color_crops(self):
        foreign = MODULE._analysis(MODULE.generate(313, 419, scene_profile="foreign_inside_crop"))
        hollow = MODULE._analysis(MODULE.generate(317, 421, scene_profile="hollow_object"))
        same = MODULE._analysis(MODULE.generate(331, 431, scene_profile="same_color_components"))
        self.assertTrue(foreign["foreign_inside"])
        self.assertTrue(hollow["hollow"])
        self.assertLess(len(set(same["colors"])), len(same["components"]))
        self.assertEqual(MODULE.rule_mirror(MODULE.generate(313, 419, scene_profile="foreign_inside_crop")), foreign["output"])

    def test_default_prior_coverage_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter(); inputs = set(); outputs = set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid))); outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[p] for p in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180); self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 780); self.assertGreater(len(outputs), 600)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="varied_sizes")
        empty = [[0 for _ in row] for row in base]
        one = [[0] * 5 for _ in range(5)]; one[1][1] = one[1][2] = 3
        six = copy.deepcopy(base)
        for index, color in enumerate((1, 2, 3)):
            six[-1][index * 2] = color
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (empty, one, six, ragged, invalid, boolean): self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "two_objects"}}))

    def test_override_and_determinism_contract(self):
        for overrides in ({"scene_profile": "unknown"}, {"n_blobs": 3}, {"texture": "equal_sizes"}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard"); self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_rule_authorities_and_pin_are_synchronized(self):
        canonical = _canonical_row()["program_solution"]
        base = json.loads((ROOT / "data/base/solutions/banks/be1bc1d91387/M135__2847032fa29b.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical)); self.assertEqual(MODULE.RULE_HASH, "4aee1598717a")

if __name__ == "__main__": unittest.main()
