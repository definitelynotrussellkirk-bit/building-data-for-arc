from __future__ import annotations

import copy
import importlib
import unittest

from reviewer_support import canonical_pairs, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.4c4f94e7d611.generator")


class Generator4c4f94e7d611Tests(unittest.TestCase):
    def test_rule_hash_and_unknown_override(self):
        self.assertEqual("d1c2577e1828", gen.RULE_HASH)
        with self.assertRaisesRegex(ValueError, "unknown override"):
            gen.generate(0, 0, difficulty="easy", texture="big_template")

    def test_all_exact_boundary_overrides_are_observable(self):
        for values in (
            dict(grid_h=8, grid_w=10, template_size=3, n_markers=1, n_decoys=0, template_color=1),
            dict(grid_h=14, grid_w=18, template_size=6, n_markers=5, n_decoys=1, template_color=9),
        ):
            grid = gen.generate(41, 7, difficulty="hard", **values)
            self.assertEqual(values, gen.observe_overrides(grid))
            self.assertEqual([], gen.self_check(grid))

    def test_canonical_inputs_are_accepted(self):
        pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
        self.assertEqual(4, len(pairs))
        for pair in pairs:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_every_schedule_window_is_identifiable(self):
        for start in range(gen.EXAMPLES_NEEDED):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(100 + start, start + offset, difficulty="medium")
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            self.assertEqual([], gen.lesson_identifiable(pairs[:-1], pairs[-1]))

    def test_declared_schedule_period_matches_exact_profile_cycle(self):
        self.assertEqual(gen.EXAMPLES_NEEDED, gen.LESSON_SCHEDULE_PERIOD)
        self.assertEqual(gen.LESSON_SCHEDULE_PERIOD, len(gen.SCHEDULE_PROFILES))
        for sample_index in range(2 * gen.LESSON_SCHEDULE_PERIOD):
            self.assertEqual(
                gen.SCHEDULE_PROFILES[sample_index % gen.LESSON_SCHEDULE_PERIOD],
                gen.schedule_profile(999, sample_index, difficulty="hard"),
            )

    def test_every_single_holdout_refutes_all_declared_rivals(self):
        for band in ("easy", "medium", "hard"):
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    grid = gen.generate(0, start + offset, difficulty=band)
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                for query_index in range(len(pairs)):
                    demos = pairs[:query_index] + pairs[query_index + 1 :]
                    surviving = [
                        name
                        for name, rival in gen.LESSON_COMPETITORS.items()
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    ]
                    self.assertEqual(
                        [],
                        surviving,
                        msg=(
                            f"band={band} start={start} query_index={query_index} "
                            f"surviving={surviving}"
                        ),
                    )

    def test_color1_singleton_shortcut_fits_canonical_and_is_refuted(self):
        shortcut = gen.CANONICAL_SHORTCUTS["count_color_1_singletons"]
        pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
        for pair in pairs:
            self.assertEqual(pair["output"], shortcut(pair["input"]))

        witness = gen.generate(17, 1, difficulty="medium")
        self.assertTrue(gen._mixed_marker_colors(witness))
        self.assertTrue(gen.SEMANTIC_WITNESSES["non_color1_singleton_marker"](witness))
        self.assertIn(
            "count_color_1_singletons",
            gen.WITNESS_RIVALS["non_color1_singleton_marker"],
        )
        self.assertNotEqual(gen.rule_mirror(witness), shortcut(witness))

    def test_self_check_rejects_targeted_impostors(self):
        valid = gen.generate(3, 1, difficulty="medium")
        self.assertEqual([], gen.self_check(valid))

        no_markers = copy.deepcopy(valid)
        components = gen._components(no_markers)
        for component in components:
            if len(component["cells"]) == 1:
                row, col = component["cells"][0]
                no_markers[row][col] = 0
        self.assertTrue(any("marker" in reason for reason in gen.self_check(no_markers)))

        tie_largest = copy.deepcopy(valid)
        template = max(gen._components(tie_largest), key=lambda comp: len(comp["cells"]))
        shape = gen._normalize(template["cells"])
        h, w = len(tie_largest), len(tie_largest[0])
        placed = False
        for top in range(h - gen._dims(shape)[0] + 1):
            for left in range(w - gen._dims(shape)[1] + 1):
                cells = [(top + r, left + c) for r, c in shape]
                if all(tie_largest[r][c] == 0 for r, c in cells):
                    for r, c in cells:
                        tie_largest[r][c] = 9 if template["color"] != 9 else 8
                    placed = True
                    break
            if placed:
                break
        self.assertTrue(placed)
        self.assertTrue(any("unique largest" in reason for reason in gen.self_check(tie_largest)))

        oversized_template = [[0] * 10 for _ in range(8)]
        for col in range(7):
            oversized_template[2][col] = 5
        oversized_template[7][9] = 1
        self.assertTrue(any("template size" in reason for reason in gen.self_check(oversized_template)))

        too_many_decoys = [[0] * 12 for _ in range(8)]
        for cell in ((1, 1), (1, 2), (2, 1), (2, 2)):
            too_many_decoys[cell[0]][cell[1]] = 5
        for cells, color in ((((5, 1), (5, 2)), 3), (((5, 5), (5, 6)), 4)):
            for r, c in cells:
                too_many_decoys[r][c] = color
        too_many_decoys[7][10] = 1
        self.assertTrue(any("at most one" in reason for reason in gen.self_check(too_many_decoys)))


if __name__ == "__main__":
    unittest.main()
