"""Focused tests for restart-safe Racket rule smoke probes."""

from __future__ import annotations

import shutil
import unittest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import (
    _grid_literal,
    calibrated_identity_is_lawful,
    load_canonical_identity_tasks,
    purity_body,
    rule_application,
)


SIMPLE_RULE = "(rule! (lambda (g) (set-cell g 0 0 9)))"


class RuleSmokePurityTests(unittest.TestCase):
    def test_canonical_identity_calibration_requires_a_mixed_diverse_curriculum(
        self,
    ) -> None:
        self.assertIn(
            "ea8116b3e778",
            load_canonical_identity_tasks({"ea8116b3e778"}),
        )
        self.assertTrue(
            calibrated_identity_is_lawful(
                identity=21,
                applied=120,
                distinct_outputs=94,
                min_outputs=5,
                canonical_identity=True,
            )
        )
        self.assertFalse(
            calibrated_identity_is_lawful(
                identity=120,
                applied=120,
                distinct_outputs=94,
                min_outputs=5,
                canonical_identity=True,
            )
        )
        self.assertFalse(
            calibrated_identity_is_lawful(
                identity=21,
                applied=120,
                distinct_outputs=94,
                min_outputs=5,
                canonical_identity=False,
            )
        )
        self.assertFalse(
            calibrated_identity_is_lawful(
                identity=21,
                applied=120,
                distinct_outputs=2,
                min_outputs=5,
                canonical_identity=True,
            )
        )

    def test_grid_literal_and_application_inline_the_input(self) -> None:
        grid = [[0, 1], [2, 3]]

        self.assertEqual("'((0 1) (2 3))", _grid_literal(grid))
        application = rule_application(SIMPLE_RULE, grid)
        self.assertIn("'((0 1) (2 3))", application)
        self.assertTrue(application.startswith("((lambda (g)"))

    @unittest.skipUnless(shutil.which("racket"), "racket is not installed")
    def test_application_and_a_b_a_probe_survive_bridge_restart(self) -> None:
        first = [[0, 1], [2, 3]]
        second = [[4, 5], [6, 7]]
        bridge = RacketBridge(max_calls_before_restart=1)
        try:
            # Consume the one-call budget so each tested expression first
            # crosses the automatic restart boundary.
            self.assertEqual(2, bridge.eval_text("(+ 1 1)"))
            self.assertEqual(
                [[9, 1], [2, 3]],
                bridge.eval_text(rule_application(SIMPLE_RULE, first)),
            )
            probe = bridge.eval_text(purity_body(SIMPLE_RULE, first, second))
        finally:
            bridge.shutdown()

        self.assertEqual(
            [
                [[9, 1], [2, 3]],
                [[9, 1], [2, 3]],
                first,
            ],
            probe,
        )


if __name__ == "__main__":
    unittest.main()


class MirrorParityTests(unittest.TestCase):
    """Python-mirror vs Racket parity (adopted 2026-07-29, bf9e0959b8ce WFB-001)."""

    def test_mirror_normalized_accepts_grid_and_coerces_ints(self) -> None:
        from scripts.rule_smoke import mirror_normalized

        self.assertEqual(mirror_normalized([[1, 0], [0, 2]]), [[1, 0], [0, 2]])
        self.assertEqual(mirror_normalized([[True, 0]]), [[1, 0]])

    def test_mirror_normalized_rejects_non_grids(self) -> None:
        from scripts.rule_smoke import mirror_normalized

        self.assertIsNone(mirror_normalized(None))
        self.assertIsNone(mirror_normalized([]))
        self.assertIsNone(mirror_normalized([1, 2, 3]))
        self.assertIsNone(mirror_normalized("grid"))

    def test_mismatch_is_detected_against_racket_output(self) -> None:
        from scripts.rule_smoke import mirror_normalized

        racket_out = [[1, 0], [0, 2]]
        self.assertEqual(mirror_normalized([[1, 0], [0, 2]]), racket_out)
        self.assertNotEqual(mirror_normalized([[1, 0], [0, 3]]), racket_out)
        self.assertNotEqual(mirror_normalized("not a grid"), racket_out)
