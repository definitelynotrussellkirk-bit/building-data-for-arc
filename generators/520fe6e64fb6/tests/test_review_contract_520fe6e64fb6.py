"""Public contracts: valid controls, real teaching evidence, and authority identity."""
from __future__ import annotations

import copy
import json
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "520fe6e64fb6"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


class ReviewContractTests(unittest.TestCase):
    def test_seed_and_index_reject_lossy_or_boolean_controls(self):
        for band in ("easy", None, "hard"):
            for name, values in (("seed", (True, False, 1.0, 1.75, "1")),
                                 ("sample_index", (True, False, 1.0, 1.75, "1", -1))):
                for value in values:
                    arguments = {"seed": 991, "sample_index": 0, "difficulty": band}
                    arguments[name] = value
                    with self.subTest(band=band, axis=name, value=value):
                        with self.assertRaises((TypeError, ValueError)):
                            GEN.generate(**arguments)

    def test_public_profile_does_not_bypass_difficulty_validation(self):
        for bad in ("unknown", False, 1, 0.5):
            with self.subTest(difficulty=bad), self.assertRaises((TypeError, ValueError)):
                GEN.generate(1, 0, difficulty=bad, scene_profile="public_train_1")

    def test_explicit_null_profile_is_not_silently_ignored(self):
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 0, scene_profile=None)

    def test_declared_shortcuts_fit_every_canonical_occurrence(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 8)
        self.assertGreaterEqual(len(GEN.CANONICAL_SHORTCUTS), 3)
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            for pair in pairs:
                with self.subTest(rival=name, variant=pair["variant"], index=pair["pair_index"]):
                    self.assertEqual(rival(copy.deepcopy(pair["input"])), pair["output"])
                    self.assertEqual(GEN.strict_canonical_like(pair["input"]), [])

    def test_irregular_anchor_refutes_every_declared_rival(self):
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 991):
                grid = GEN.generate(seed, 0, difficulty=band, scene_profile="irregular_markers")
                expected = GEN.rule_mirror(grid)
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    with self.subTest(band=band, seed=seed, rival=name):
                        self.assertNotEqual(rival(copy.deepcopy(grid)), expected)

    def test_consecutive_four_pair_windows_have_no_single_disagreement(self):
        # Production census separately verifies Racket labels and accepted indices.
        self.assertEqual(GEN.EXAMPLES_NEEDED, 3)
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 991):
                for start in range(6):
                    grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(4)]
                    pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        disagreements = sum(rival(copy.deepcopy(p["input"])) != p["output"] for p in pairs)
                        with self.subTest(band=band, seed=seed, start=start, rival=name):
                            self.assertNotEqual(disagreements, 1)
                    for query_index in range(4):
                        demos = [p for i, p in enumerate(pairs) if i != query_index]
                        self.assertEqual(GEN.lesson_identifiable(demos, pairs[query_index]), [])

    def test_duplicate_filtering_preserves_two_refuters(self):
        # Real v3.1.0 regression: easy seed4484/start1 accepts [1,2,3,5],
        # rejecting duplicate anchor4. Holding out anchor2 then becomes ambiguous.
        pairs, seen, accepted = [], set(), []
        for index in range(1, 33):
            grid = GEN.generate(4484, index, difficulty="easy")
            output = GEN.rule_mirror(grid)
            fingerprint = json.dumps([grid, output], separators=(",", ":"))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            accepted.append(index)
            pairs.append({"input": grid, "output": output})
            if len(pairs) == 4:
                break
        self.assertEqual(len(pairs), 4, f"could not materialize four pairs: {accepted}")
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            with self.subTest(query=query_index, accepted=accepted):
                self.assertEqual(GEN.lesson_identifiable(demos, pairs[query_index]), [])

    def test_adjacent_anchors_are_structurally_distinct_refuters(self):
        # Prevent a version/seed shuffle from merely hiding the duplicate seed.
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 4484):
                for start in range(0, 10, 2):
                    anchors = [GEN.generate(seed, start + offset, difficulty=band) for offset in (0, 2)]
                    orders = []
                    for grid in anchors:
                        rows9 = [r for r, row in enumerate(grid) if 9 in row]
                        rows7 = [r for r, row in enumerate(grid) if 7 in row]
                        orders.append(max(rows9) < min(rows7))
                        for name, rival in GEN.LESSON_COMPETITORS.items():
                            with self.subTest(band=band, seed=seed, start=start, rival=name):
                                self.assertNotEqual(rival(grid), GEN.rule_mirror(grid))
                    with self.subTest(band=band, seed=seed, start=start):
                        self.assertEqual(set(orders), {False, True})
                        self.assertNotEqual(anchors[0], anchors[1])

    def test_known_ambiguous_public_only_lesson_is_rejected(self):
        demos = [{"input": GEN.generate(5, i, scene_profile=profile)}
                 for i, profile in enumerate(GEN.PUBLIC_PROFILES[:3])]
        for demo in demos:
            demo["output"] = GEN.rule_mirror(demo["input"])
        grid = GEN.generate(5, 3, scene_profile="irregular_markers")
        reasons = GEN.lesson_identifiable(demos, {"input": grid, "output": GEN.rule_mirror(grid)})
        self.assertTrue(reasons)
        self.assertTrue(any("equal_filled_rectangles_only" in reason for reason in reasons))

    def test_active_authorities_match_exactly_and_archives_remain_equivalent(self):
        rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID]
        selected = rows[0]["program_solution"]
        for row in rows:
            self.assertEqual(row["program_solution"], selected)
        base = ROOT / "shared/data/base/solutions"
        if not base.is_dir():
            base = ROOT / "data/base/solutions"
        for relative in ("training/fc10701f__520fe6e64fb6.json", "augmented/fc10701f__b1e2b0d3c0f8.json"):
            authority = json.loads((base / relative).read_text())["racket_target"]
            with self.subTest(authority=relative):
                self.assertEqual(authority["target_code"], selected)
                self.assertEqual(" ".join(authority["raw_code"].split()), " ".join(selected.split()))


if __name__ == "__main__":
    unittest.main()
