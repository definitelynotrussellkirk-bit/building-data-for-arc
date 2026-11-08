from __future__ import annotations

import copy
import importlib
import random
import unittest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule

gen = importlib.import_module("puzzle_generators.per_puzzle.401aff907774.generator")
TASK_ID = "401aff907774"


class Generator401aff907774Tests(unittest.TestCase):
    def test_three_profile_window_refutes_all_named_rivals(self):
        for start in range(6):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(19, index, difficulty="medium")
                demos.append({"input": grid, "output": gen._authoritative_python(grid)})
            query_grid = gen.generate(19, start + gen.EXAMPLES_NEEDED, difficulty="medium")
            query = {"input": query_grid, "output": gen._authoritative_python(query_grid)}
            self.assertEqual(gen.lesson_identifiable(demos, query), [])

    def test_exact_override_observation(self):
        requested = {
            "grid_h": 7,
            "grid_w": 14,
            "crop_h": 5,
            "crop_w": 2,
            "marker_diagonal": "anti",
            "interior_palette_size": 3,
            "ignored_distractor_count": 4,
        }
        grid = gen.generate(7, 4, difficulty="hard", **requested)
        self.assertEqual(gen.observe_overrides(grid), requested)
        self.assertEqual(gen.self_check(grid), [])

    def test_unknown_override_rejected(self):
        with self.assertRaises(TypeError):
            gen.generate(0, 0, typo_axis=1)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        state = random.getstate()
        first = gen.generate(444, 19, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = gen.generate(444, 19, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9
        self.assertEqual(gen.generate(444, 19, difficulty="medium"), second)

    def test_self_check_rejects_targeted_semantic_impostors(self):
        base = gen.generate(
            91,
            1,
            grid_h=10,
            grid_w=11,
            crop_h=3,
            crop_w=4,
            marker_diagonal="main",
            interior_palette_size=2,
            ignored_distractor_count=0,
        )
        facts = gen.semantic_observables(base)
        r0, r1, c0, c1 = facts["marker_box"]

        missing_marker = copy.deepcopy(base)
        missing_marker[r0][c0] = 0
        self.assertTrue(any("exactly two" in e for e in gen.self_check(missing_marker)))

        third_marker = copy.deepcopy(base)
        third_marker[r0][c0 + 1] = 4
        self.assertTrue(any("exactly two" in e for e in gen.self_check(third_marker)))

        collinear_markers = copy.deepcopy(base)
        collinear_markers[r1][c1] = 0
        collinear_markers[r0][c1] = 4
        self.assertTrue(any("2..5" in e for e in gen.self_check(collinear_markers)))

        empty_interior = copy.deepcopy(base)
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                empty_interior[r][c] = 0
        self.assertTrue(any("at least two colored" in e for e in gen.self_check(empty_interior)))

        solid_interior = copy.deepcopy(base)
        fill = next(v for row in base for v in row if v not in (0, 4))
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                solid_interior[r][c] = fill
        self.assertTrue(any("at least one zero" in e for e in gen.self_check(solid_interior)))

    def test_negative_recombination_rejected_but_oracle_executable(self):
        grid = gen.generate(
            123,
            1,
            grid_h=10,
            grid_w=11,
            crop_h=3,
            crop_w=4,
            marker_diagonal="main",
            interior_palette_size=2,
            ignored_distractor_count=0,
        )
        facts = gen.semantic_observables(grid)
        r0, r1, c0, c1 = facts["marker_box"]
        present = {v for row in grid for v in row}
        replacement = next(v for v in range(1, 10) if v not in present and v != 4)

        recombined = copy.deepcopy(grid)
        replaced = False
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if recombined[r][c] not in (0, 4):
                    recombined[r][c] = replacement
                    replaced = True
                    break
            if replaced:
                break
        self.assertTrue(replaced)
        self.assertEqual(sum(v == replacement for row in recombined for v in row), 1)
        recombined[r0][c0 + 1] = 4  # third marker; bbox and oracle output remain defined
        self.assertTrue(any("exactly two" in e for e in gen.self_check(recombined)))

        bundle = _load_bundle(TASK_ID)
        bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
        try:
            output = _apply_rule(bridge, fn_name, recombined)
        finally:
            bridge.shutdown()
        self.assertEqual(output, gen._interior_from_box(recombined, facts["marker_box"]))

    def test_canonical_inputs_are_strict(self):
        for h, w, interior in gen._CANONICAL_CASES:
            grid = gen._place_scene(h, w, interior, "main", 0, random.Random(0))
            self.assertEqual(gen.strict_canonical_like(grid), [])


if __name__ == "__main__":
    unittest.main()
