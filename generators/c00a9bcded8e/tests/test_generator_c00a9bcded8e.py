"""Focused regressions for the c00a9bcded8e rectangle-table generator."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import random
import unittest

from puzzle_generators import base
from puzzle_generators.per_puzzle.c00a9bcded8e import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source


def _old_fixed_anchor_output(grid):
    """Plausible shortcut for the pre-repair fixed rectangle coordinates."""
    facts, errors = gen._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    row_starts = {
        2: (4, 20),
        3: (2, 12, 22),
        4: (1, 8, 15, 22),
    }[facts["n_rect_rows"]]
    return [[grid[row][col] for col in (2, 12, 22)] for row in row_starts]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


class GeneratorC00a9bcded8eTests(unittest.TestCase):
    def test_canonical_inventory_rule_pin_and_outputs(self):
        pairs = canonical_pairs(gen.TASK_ID)
        self.assertEqual(4, len(pairs))
        actual_hash = hashlib.sha256(
            " ".join(canonical_rule_source(gen.TASK_ID).split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(actual_hash, gen.RULE_HASH)

        observed_rows = []
        observed_noise = []
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual([], gen.strict_canonical_like(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))
            self.assertEqual(before, pair["input"])
            facts, errors = gen._analyze(pair["input"])
            self.assertEqual([], errors)
            observed_rows.append(facts["n_rect_rows"])
            observed_noise.append(facts["noise_count"])
        self.assertEqual([2, 3, 3, 4], observed_rows)
        self.assertEqual([307, 322, 366, 292], observed_noise)

    def test_exact_override_boundaries_are_observable(self):
        cases = (
            {"n_rect_rows": 2},
            {"n_rect_rows": 4},
            {"size_profile": "uniform"},
            {"size_profile": "mixed"},
            {"color_pattern": "column_repeat"},
            {"color_pattern": "row_repeat"},
            {"color_pattern": "mixed"},
            {"noise_count": 260},
            {"noise_count": 370},
            {
                "n_rect_rows": 4,
                "size_profile": "uniform",
                "color_pattern": "row_repeat",
                "noise_count": 370,
            },
        )
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                with self.subTest(band=band, overrides=overrides):
                    grid = gen.generate(
                        700 + index,
                        900 + index,
                        difficulty=band,
                        **overrides,
                    )
                    observed = gen.observe_overrides(grid)
                    for name, expected in overrides.items():
                        self.assertEqual(expected, observed[name])
                    self.assertEqual(
                        [],
                        gen.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": overrides},
                        ),
                    )

    def test_ordinary_draw_provenance_matches_pixels(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = gen.generate(
                        1700 + seed,
                        13 * seed + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertEqual(1, len(captured))
                observed = gen.observe_overrides(grid)
                recorded = captured[0].recorded_draws()
                self.assertEqual(set(gen.AXES), set(recorded))
                self.assertEqual(observed, recorded)

    def test_linked_semantic_census_200_per_band(self):
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            inputs = set()
            outputs = set()
            matches = 0
            for index in range(200):
                grid = gen.generate(
                    5000 + index,
                    17 * index + 2,
                    difficulty=band,
                )
                facts, errors = gen._analyze(grid)
                output = gen.rule_mirror(grid)
                linked = (
                    not errors
                    and gen.strict_canonical_like(grid) == []
                    and len(output) == facts["n_rect_rows"]
                    and all(len(row) == 3 for row in output)
                    and facts["noise_colors"].isdisjoint(facts["target_colors"])
                    and all(rect["size"] == rect["area"] for rect in facts["rects"])
                )
                matches += int(linked)
                counts[("rows", facts["n_rect_rows"])] += 1
                counts[("sizes", facts["size_profile"])] += 1
                counts[("colors", facts["color_pattern"])] += 1
                inputs.add(_frozen(grid))
                outputs.add(_frozen(output))
            self.assertEqual(200, matches)
            self.assertEqual({2, 3, 4}, {key[1] for key in counts if key[0] == "rows"})
            self.assertEqual(
                {"uniform", "mixed"},
                {key[1] for key in counts if key[0] == "sizes"},
            )
            self.assertEqual(
                set(gen.COLOR_PATTERNS),
                {key[1] for key in counts if key[0] == "colors"},
            )
            self.assertGreaterEqual(len(inputs), 195)
            self.assertGreaterEqual(len(outputs), 180)

    def test_generated_support_covers_canonical_rectangle_dimensions(self):
        canonical_heights = set()
        canonical_widths = set()
        for pair in canonical_pairs(gen.TASK_ID):
            facts, errors = gen._analyze(pair["input"])
            self.assertEqual([], errors)
            canonical_heights.update(rect["h"] for rect in facts["rects"])
            canonical_widths.update(rect["w"] for rect in facts["rects"])

        generated_heights = set()
        generated_widths = set()
        for band in ("easy", "medium", "hard"):
            for sample_index in range(18):
                grid = gen.generate(4400 + sample_index, sample_index, difficulty=band)
                facts, errors = gen._analyze(grid)
                self.assertEqual([], errors)
                generated_heights.update(rect["h"] for rect in facts["rects"])
                generated_widths.update(rect["w"] for rect in facts["rects"])

        self.assertTrue(
            canonical_heights.issubset(generated_heights),
            (canonical_heights, generated_heights),
        )
        self.assertTrue(
            canonical_widths.issubset(generated_widths),
            (canonical_widths, generated_widths),
        )

    def test_each_lesson_refutes_the_old_fixed_anchor_shortcut(self):
        for band in ("easy", "medium", "hard"):
            for start in range(18):
                demonstrations = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(8300 + start, sample_index, difficulty=band)
                    demonstrations.append((grid, gen.rule_mirror(grid)))
                self.assertTrue(
                    any(
                        _old_fixed_anchor_output(grid) != expected
                        for grid, expected in demonstrations
                    ),
                    (band, start),
                )

    def test_semantic_contract_declares_fixed_anchor_rival(self):
        self.assertIn("fixed_anchor", gen.LESSON_COMPETITORS)

    def test_every_semantic_witness_names_a_rival_it_refutes(self):
        self.assertEqual(
            set(),
            set(gen.SEMANTIC_WITNESSES) - set(gen.WITNESS_RIVALS),
        )
        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            with self.subTest(witness=witness_name):
                self.assertTrue(rival_names)
                self.assertTrue(set(rival_names).issubset(gen.SEMANTIC_RIVALS))

    def test_every_declared_canonical_shortcut_fits_all_canonical_pairs(self):
        pairs = canonical_pairs(gen.TASK_ID)
        for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
            with self.subTest(shortcut=name):
                self.assertTrue(
                    all(shortcut(pair["input"]) == pair["output"] for pair in pairs),
                    name,
                )

    def test_every_three_demo_sliding_window_is_identifiable(self):
        for band in ("easy", "medium", "hard"):
            for start in range(18):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(9001 + start, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_index = start + gen.EXAMPLES_NEEDED
                query_grid = gen.generate(9001 + start, query_index, difficulty=band)
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                self.assertEqual([], gen.lesson_identifiable(demos, query))

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260726)
        state = random.getstate()
        first = gen.generate(717, 19, difficulty="hard")
        self.assertEqual(state, random.getstate())
        replay = gen.generate(717, 19, difficulty="hard")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, replay)
        self.assertIsNot(first, replay)
        self.assertTrue(all(left is not right for left, right in zip(first, replay)))

        expected = copy.deepcopy(replay)
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertEqual(expected, gen.generate(717, 19, difficulty="hard"))
        self.assertNotEqual(expected, gen.generate(718, 19, difficulty="hard"))

    def test_self_check_rejects_targeted_impostors(self):
        grid = gen.generate(991337, 5, difficulty="medium")
        facts, errors = gen._analyze(grid)
        self.assertEqual([], errors)
        rects = facts["rects"]

        all_background = [[0] * 30 for _ in range(30)]
        full_one_color = [[2] * 30 for _ in range(30)]

        missing_rectangle = copy.deepcopy(grid)
        for row, col in rects[0]["cells"]:
            missing_rectangle[row][col] = 0

        punched_rectangle = copy.deepcopy(grid)
        row, col = rects[-1]["cells"][0]
        punched_rectangle[row][col] = 0

        third_noise_color = copy.deepcopy(grid)
        target_cells = {cell for rect in rects for cell in rect["cells"]}
        changed = False
        for row in range(30):
            for col in range(30):
                if third_noise_color[row][col] == 0 and (row, col) not in target_cells:
                    # Recombine a target color into the noise field.  The
                    # baseline dimension-only checker accepted this role leak.
                    third_noise_color[row][col] = next(iter(facts["target_colors"]))
                    changed = True
                    break
            if changed:
                break

        extra_rectangle = copy.deepcopy(grid)
        for row in range(27, 30):
            for col in range(11, 14):
                extra_rectangle[row][col] = next(iter(facts["target_colors"]))

        for name, impostor in (
            ("all_background", all_background),
            ("full_one_color", full_one_color),
            ("missing_rectangle", missing_rectangle),
            ("punched_rectangle", punched_rectangle),
            ("third_noise_color", third_noise_color),
            ("extra_rectangle", extra_rectangle),
        ):
            with self.subTest(name=name):
                self.assertTrue(gen.self_check(impostor), name)

    def test_unknown_and_invalid_overrides_reject_loudly(self):
        bad_cases = (
            {"unknown_axis": 1},
            {"n_rect_rows": 1},
            {"n_rect_rows": True},
            {"noise_count": 259},
            {"noise_count": 371},
            {"size_profile": "tiny"},
            {"color_pattern": "sorted"},
        )
        for case in bad_cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    gen.generate(1, 1, difficulty="easy", **case)


if __name__ == "__main__":
    unittest.main()
