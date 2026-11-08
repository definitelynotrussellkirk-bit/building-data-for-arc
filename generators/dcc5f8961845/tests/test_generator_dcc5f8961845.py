from __future__ import annotations

import random
import unittest
from puzzle_generators import base
from puzzle_generators.per_puzzle.dcc5f8961845 import generator
from reviewer_support import canonical_pairs as portable_canonical_pairs, find_root


ROOT = find_root(__file__)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    for pair in portable_canonical_pairs(
        generator.TASK_ID,
        root=ROOT,
        labeled_only=True,
    ):
        yield as_grid(pair["input"]), as_grid(pair["output"])


class Dcc5f8961845GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        commands = set()
        motifs = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
            scene = generator._analyze_scene(grid)
            commands.add((scene["cmd1"], scene["cmd2"]))
            motifs.add(scene["motif"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(commands), 5)
        self.assertEqual(len(motifs), 3)

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(500):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, generator.rule_mirror(grid)))
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 20)
                self.assertLessEqual(matches, 65)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 420)
                self.assertGreaterEqual(len(outputs), 420)

    def test_general_path_witnesses_every_axis_and_command_pair(self):
        sizes = set()
        motif_shapes = set()
        color_counts = set()
        command_pairs = set()
        output_shapes = set()
        for cmd1 in range(6):
            for cmd2 in range(6):
                for seed in range(3):
                    grid = generator.generate(
                        seed,
                        seed * 31 + cmd1 * 6 + cmd2,
                        difficulty="hard",
                        grid_h=14,
                        grid_w=16,
                        motif_h=2,
                        motif_w=5,
                        n_colors=3,
                        cmd1=cmd1,
                        cmd2=cmd2,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(observed["grid_h"], 14)
                    self.assertEqual(observed["grid_w"], 16)
                    self.assertEqual(observed["motif_h"], 2)
                    self.assertEqual(observed["motif_w"], 5)
                    self.assertEqual(observed["n_colors"], 3)
                    self.assertEqual(observed["cmd1"], cmd1)
                    self.assertEqual(observed["cmd2"], cmd2)
                    output = generator.rule_mirror(grid)
                    sizes.add((observed["grid_h"], observed["grid_w"]))
                    motif_shapes.add(
                        (observed["motif_h"], observed["motif_w"])
                    )
                    color_counts.add(observed["n_colors"])
                    command_pairs.add((cmd1, cmd2))
                    output_shapes.add((len(output), len(output[0])))
        self.assertEqual(sizes, {(14, 16)})
        self.assertEqual(motif_shapes, {(2, 5)})
        self.assertEqual(color_counts, {3})
        self.assertEqual(len(command_pairs), 36)
        self.assertEqual(output_shapes, {(2, 5), (5, 2)})

    def test_boundaries_and_strict_controls(self):
        axes = (
            ("grid_h", (8, 14)),
            ("grid_w", (9, 16)),
            ("motif_h", (2, 5)),
            ("motif_w", (2, 5)),
            ("n_colors", (2, 3)),
            ("cmd1", (0, 5)),
            ("cmd2", (0, 5)),
        )
        for label, values in axes:
            for value in values:
                for band in ("easy", "medium", "hard"):
                    grid = generator.generate(
                        17,
                        23,
                        difficulty=band,
                        **{label: value},
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid)[label],
                        value,
                    )

        mixed = (
            {
                "grid_h": 8,
                "grid_w": 9,
                "motif_h": 5,
                "motif_w": 5,
                "n_colors": 3,
                "cmd1": 0,
                "cmd2": 5,
            },
            {
                "grid_h": 14,
                "grid_w": 16,
                "motif_h": 2,
                "motif_w": 2,
                "n_colors": 2,
                "cmd1": 5,
                "cmd2": 0,
            },
        )
        for kwargs in mixed:
            grid = generator.generate(19, 29, **kwargs)
            self.assertEqual(generator.self_check(grid), [])
            observed = generator.observe_overrides(grid)
            for key, value in kwargs.items():
                self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "8"},
            {"grid_w": 9.0},
            {"motif_h": True},
            {"cmd1": "0"},
            {"grid_h": 7},
            {"grid_h": 15},
            {"grid_w": 8},
            {"grid_w": 17},
            {"motif_h": 1},
            {"motif_w": 6},
            {"n_colors": 1},
            {"n_colors": 4},
            {"cmd1": -1},
            {"cmd1": 6},
            {"cmd2": -1},
            {"cmd2": 6},
            {"texture": "no_motif"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 30)

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]

        no_motif = [row[:] for row in original]
        for r in range(1, len(no_motif)):
            for c in range(len(no_motif[0])):
                no_motif[r][c] = 0
        self.assertTrue(
            any(
                "missing motif" in error
                for error in generator.self_check(no_motif)
            )
        )

        bad_command = [row[:] for row in original]
        bad_command[0][0] = 6
        self.assertTrue(
            any(
                "commands" in error
                for error in generator.self_check(bad_command)
            )
        )

        extra_header = [row[:] for row in original]
        extra_header[0][2] = 4
        self.assertTrue(
            any(
                "first two" in error
                for error in generator.self_check(extra_header)
            )
        )

        no_separator = [row[:] for row in original]
        no_separator[1][3] = 2
        self.assertTrue(
            any(
                "blank row" in error
                for error in generator.self_check(no_separator)
            )
        )

        edge_motif = [row[:] for row in original]
        edge_motif[3][0] = 2
        self.assertTrue(
            any(
                "one-cell margin" in error
                for error in generator.self_check(edge_motif)
            )
        )

        fourth_color = [row[:] for row in original]
        fourth_color[3][4] = 8
        fourth_color[4][4] = 9
        self.assertTrue(
            any(
                "2..3 distinct" in error
                for error in generator.self_check(fourth_color)
            )
        )

        invalid_color = [row[:] for row in original]
        invalid_color[3][3] = 10
        self.assertTrue(
            any(
                "ARC colors" in error
                for error in generator.self_check(invalid_color)
            )
        )

    def test_reversed_commands_are_lawful_but_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        hybrid[0][0], hybrid[0][1] = hybrid[0][1], hybrid[0][0]
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertNotEqual(
            generator.rule_mirror(hybrid),
            generator.rule_mirror(grid),
        )
        self.assertFalse(generator.is_canonical_profile(hybrid))

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
