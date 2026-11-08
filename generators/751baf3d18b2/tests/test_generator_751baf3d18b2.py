"""Focused semantic and contract tests for generator 751baf3d18b2."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root
from scripts.coder_synth_verify import ProgramVerifier


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.751baf3d18b2.generator"
)
ROOT = find_root(__file__)
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/22a17f7a0399"
    / "E70__751baf3d18b2.json"
)


def canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only mirror; the live Racket rule remains output authority."""
    return [
        [
            grid[0][column]
            if row > 0
            and grid[row][column] != 0
            and grid[0][column] != 0
            else grid[row][column]
            for column in range(len(grid[0]))
        ]
        for row in range(len(grid))
    ]


def linked_signature(grid: list[list[int]]) -> tuple:
    width = len(grid[0])
    active = tuple(column for column, value in enumerate(grid[0]) if value)
    if active == tuple(range(0, width, 2)):
        phase = "alternating_even"
    elif active == tuple(range(1, width, 2)):
        phase = "alternating_odd"
    else:
        phase = "other"
    active_counts = tuple(
        sorted(
            sum(grid[row][column] != 0 for column in active)
            for row in range(1, len(grid))
        )
    )
    inactive_body = any(
        grid[row][column] != 0
        for row in range(1, len(grid))
        for column in range(width)
        if column not in active
    )
    palette = tuple(sorted({value for row in grid for value in row}))
    return (
        len(grid),
        width,
        phase,
        active_counts,
        "present" if inactive_body else "absent",
        palette,
    )


class Generator751baf3d18b2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()
        cls.official_signatures = {
            linked_signature(pair["input"]) for pair in cls.pairs
        }

    def test_rule_authorities_and_normalized_hash_pin(self):
        base = json.loads(BASE_FILE.read_text(encoding="utf-8"))
        canonical = self.row["program_solution"]
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(generator.RULE_HASH, normalized_rule_hash(canonical))
        self.assertEqual(generator.RULE_HASH, "56d0892cc35d")

    def test_all_canonical_inputs_are_accepted_and_match_the_rule(self):
        self.assertEqual(len(self.pairs), 3)
        for pair in self.pairs:
            source = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_exact_override_boundaries_and_observation_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for height in (4, 10):
                for width in (5, 14):
                    for header_pattern in generator.HEADER_PATTERNS:
                        for body_profile in generator.BODY_PROFILES:
                            for empty_header_body in generator.EMPTY_HEADER_BODY_MODES:
                                grid = generator.generate(
                                    401,
                                    503,
                                    difficulty=band,
                                    grid_h=height,
                                    grid_w=width,
                                    header_pattern=header_pattern,
                                    body_profile=body_profile,
                                    empty_header_body=empty_header_body,
                                )
                                expected = {
                                    "grid_h": height,
                                    "grid_w": width,
                                    "header_pattern": header_pattern,
                                    "body_profile": body_profile,
                                    "empty_header_body": empty_header_body,
                                }
                                self.assertEqual(generator.observe_overrides(grid), expected)
                                self.assertEqual(generator.self_check(grid), [])

    def test_default_distribution_covers_every_semantic_branch(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            patterns = set()
            profiles = set()
            empty_modes = set()
            inputs = set()
            outputs = set()
            for offset in range(400):
                grid = generator.generate(
                    20_000 + band_index * 10_000 + offset,
                    offset * 17 + 3,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                patterns.add(observed["header_pattern"])
                profiles.add(observed["body_profile"])
                empty_modes.add(observed["empty_header_body"])
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, rule_mirror(grid))))
                self.assertEqual(generator.self_check(grid), [])
            with self.subTest(band=band):
                self.assertEqual(patterns, set(generator.HEADER_PATTERNS))
                self.assertEqual(profiles, set(generator.BODY_PROFILES))
                self.assertEqual(empty_modes, set(generator.EMPTY_HEADER_BODY_MODES))
                self.assertGreater(len(inputs), 390)
                self.assertGreater(len(outputs), 390)

    def test_linked_official_prior_is_substantial_and_reaches_each_profile(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            counts = {signature: 0 for signature in self.official_signatures}
            for offset in range(600):
                grid = generator.generate(
                    70_000 + band_index * 10_000 + offset,
                    offset,
                    difficulty=band,
                )
                signature = linked_signature(grid)
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 150)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_self_check_rejects_targeted_structural_impostors(self):
        valid = generator.generate(
            11,
            13,
            difficulty="medium",
            grid_h=6,
            grid_w=9,
            header_pattern="alternating_even",
            body_profile="mixed_one_full",
            empty_header_body="present",
        )
        self.assertEqual(generator.self_check(valid), [])

        blank = [[0 for _ in range(9)] for _ in range(6)]

        irregular_header = copy.deepcopy(valid)
        irregular_header[0][1] = 9

        duplicate_headers = copy.deepcopy(valid)
        active = [column for column, value in enumerate(valid[0]) if value]
        duplicate_headers[0][active[1]] = duplicate_headers[0][active[0]]

        missing_active_column = copy.deepcopy(valid)
        for row in range(1, len(valid)):
            missing_active_column[row][active[-1]] = 0

        hidden_rule = copy.deepcopy(valid)
        for row in range(1, len(valid)):
            for column in active:
                if hidden_rule[row][column] != 0:
                    hidden_rule[row][column] = hidden_rule[0][column]

        one_passthrough_witness = copy.deepcopy(valid)
        inactive_positions = [
            (row, column)
            for row in range(1, len(valid))
            for column in range(len(valid[0]))
            if valid[0][column] == 0 and valid[row][column] != 0
        ]
        for row, column in inactive_positions[1:]:
            one_passthrough_witness[row][column] = 0

        for mutation in (
            blank,
            irregular_header,
            duplicate_headers,
            missing_active_column,
            hidden_rule,
            one_passthrough_witness,
        ):
            self.assertTrue(generator.self_check(mutation), mutation)
            with self.assertRaises(ValueError):
                generator.observe_overrides(mutation)

    def test_incompatible_header_body_recombination_is_rejected_but_executable(self):
        source = copy.deepcopy(self.pairs[0]["input"])
        header_colors = [source[0][column] for column in range(0, len(source[0]), 2)]
        source[0] = [0] * len(source[0])
        for column, color in zip(range(1, len(source[0]), 2), header_colors):
            source[0][column] = color

        errors = generator.self_check(source)
        self.assertTrue(errors)
        self.assertTrue(any("without body evidence" in error or "rule would be hidden" in error for error in errors))

        with ProgramVerifier(timeout=20) as verifier:
            output = verifier.apply(self.row["program_solution"], source)
        self.assertEqual(len(output), len(source))
        self.assertEqual(len(output[0]), len(source[0]))

    def test_racket_matches_test_mirror_and_is_a_b_a_reentrant(self):
        program = self.row["program_solution"]
        first = generator.generate(
            901,
            17,
            difficulty="hard",
            empty_header_body="present",
        )
        second = generator.generate(902, 19, difficulty="easy")
        with ProgramVerifier(timeout=20) as verifier:
            first_out = verifier.apply(program, first)
            verifier.apply(program, second)
            first_again = verifier.apply(program, first)
            self.assertEqual(first_out, first_again)
            self.assertEqual(first_out, rule_mirror(first))
            for pair in self.pairs:
                self.assertEqual(verifier.apply(program, pair["input"]), pair["output"])

    def test_self_check_rejects_declared_override_metadata_drift(self):
        grid = generator.generate(
            123,
            45,
            difficulty="medium",
            grid_h=6,
            grid_w=9,
            header_pattern="alternating_even",
            body_profile="mixed_one_full",
            empty_header_body="present",
        )
        observed = generator.observe_overrides(grid)
        self.assertEqual(
            generator.self_check(grid, meta={"overrides": observed}),
            [],
        )
        mismatched = dict(observed)
        mismatched["body_profile"] = "dense"
        errors = generator.self_check(grid, meta={"overrides": mismatched})
        self.assertTrue(any("override body_profile" in error for error in errors), errors)

    def test_determinism_freshness_global_rng_and_loud_rejection(self):
        random.seed(20260723)
        state = random.getstate()
        first = generator.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

        with self.assertRaises(TypeError):
            generator.generate(1, 2, texture="dense")
        for kwargs in (
            {"grid_h": 3},
            {"grid_w": 15},
            {"header_pattern": "all_active"},
            {"body_profile": "unknown"},
            {"empty_header_body": "sometimes"},
        ):
            with self.assertRaises(ValueError):
                generator.generate(1, 2, **kwargs)


if __name__ == "__main__":
    unittest.main()
