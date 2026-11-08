from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import unittest


try:
    from reviewer_support import canonical_path, find_root, load_selected_generator
except ModuleNotFoundError:
    import sys
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    "aea4d55345a1",
    root=ROOT,
)


def canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (
            row.get("task_id") == generator.TASK_ID
            and row.get("source") == "training"
        ):
            return row
    raise RuntimeError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def repeat_latest_diff_without_carry(grid):
    """Independent finite rival from the retained shortcut audit."""
    _separators, _height, sections = generator._split_sections(grid)
    older, previous, latest = sections[-3:]
    prior_diff = generator._diff(older, previous)
    latest_diff = generator._diff(previous, latest)
    shift = (
        min(item[1] for item in latest_diff)
        - min(item[1] for item in prior_diff)
        if prior_diff and latest_diff
        else 0
    )
    output = [row[:] for row in latest]
    for row, col, old, new in latest_diff:
        target = col + shift
        if 0 <= target < len(output[0]) and output[row][target] == old:
            output[row][target] = new
    return output


class GeneratorAea4d55345a1Tests(unittest.TestCase):
    def test_all_public_pairs_are_strict_and_exact(self):
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.solve_python(grid), pair["output"])

    def test_every_profile_and_band_is_exactly_observable(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(20):
                    grid = generator.generate(
                        10_000 * profile_index + 1_000 * band_index + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertNotEqual(
                        generator.solve_python(grid),
                        generator._split_sections(grid)[2][-1],
                    )

    def test_default_profile_prior_and_band_coverage(self):
        public = 0
        total = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            for index in range(2_000):
                grid = generator.generate(
                    500_000 + 10_000 * band_index + index,
                    index,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)["scene_profile"]
                seen.add(observed)
                public += observed in generator.PUBLIC_PROFILES
                total += 1
            self.assertEqual(seen, set(generator.SCENE_PROFILES))
        self.assertGreater(public / total, 0.22)
        self.assertLess(public / total, 0.28)

    def test_defaults_never_replay_a_public_literal(self):
        literals = {
            tuple(tuple(row) for row in pair["input"])
            for pair in canonical_pairs()
        }
        for index in range(3_000):
            grid = generator.generate(600_000 + index, index)
            self.assertNotIn(
                tuple(tuple(row) for row in grid),
                literals,
            )


    def test_every_query_rotation_retains_a_carry_refutation(self):
        for band in (None, "easy", "medium", "hard"):
            for seed in range(8):
                for start in range(6):
                    pairs = []
                    for offset in range(4):
                        grid = generator.generate(
                            seed,
                            start + offset,
                            difficulty=band,
                        )
                        pairs.append(
                            {"input": grid, "output": generator.solve_python(grid)}
                        )
                    for query_index in range(4):
                        demonstrations = [
                            pair
                            for index, pair in enumerate(pairs)
                            if index != query_index
                        ]
                        self.assertTrue(
                            any(
                                repeat_latest_diff_without_carry(pair["input"])
                                != pair["output"]
                                for pair in demonstrations
                            ),
                            (band, seed, start, query_index),
                        )

    def test_declared_no_carry_rival_and_lesson_contract(self):
        rival = generator.SEMANTIC_RIVALS[
            "repeat_latest_diff_without_carry"
        ]
        self.assertEqual(generator.CANONICAL_SHORTCUTS, {})
        self.assertIs(
            generator.LESSON_COMPETITORS[
                "repeat_latest_diff_without_carry"
            ],
            rival,
        )
        pairs = []
        for sample_index in range(4):
            grid = generator.generate(17, sample_index, difficulty="easy")
            pairs.append(
                {"input": grid, "output": generator.solve_python(grid)}
            )
        for query_index in range(4):
            demonstrations = [
                pair for index, pair in enumerate(pairs) if index != query_index
            ]
            self.assertEqual(
                generator.lesson_identifiable(
                    demonstrations,
                    pairs[query_index],
                ),
                [],
            )

    def test_staggered_profile_witnesses_carry_rows(self):
        for index in range(100):
            grid = generator.generate(
                700_000 + index,
                index,
                difficulty="hard",
                scene_profile="staggered_carry",
            )
            analysis = generator._analyze(grid)
            self.assertGreater(analysis["carry_row_count"], 0)
            self.assertEqual(analysis["col_shift"], 1)

    def test_mutations_are_rejected_from_final_grid(self):
        grid = generator.generate(
            800_000,
            0,
            scene_profile="staggered_carry",
        )
        missing_separator = copy.deepcopy(grid)
        missing_separator.pop(generator._analyze(grid)["section_height"])
        self.assertTrue(generator.self_check(missing_separator))

        gray_inside = copy.deepcopy(grid)
        gray_inside[0][0] = 5
        self.assertTrue(generator.self_check(gray_inside))

        no_latest_diff = copy.deepcopy(grid)
        _, section_height, sections = generator._split_sections(grid)
        start = 3 * section_height + 3
        for row in range(section_height):
            no_latest_diff[start + row] = sections[-2][row][:]
        self.assertTrue(generator.self_check(no_latest_diff))

        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        self.assertTrue(generator.self_check(ragged))

        invalid = copy.deepcopy(grid)
        invalid[0][0] = True
        self.assertTrue(generator.self_check(invalid))

    def test_broad_three_section_oracle_outside_training_grammar(self):
        sections = []
        for col in (1, 2, 3):
            section = generator._blank(2, 9)
            section[0][col] = 4
            sections.append(section)
        grid = generator._assemble(sections)
        self.assertTrue(generator.self_check(grid))
        expected = generator._blank(2, 9)
        expected[0][4] = 4
        self.assertEqual(generator.solve_python(grid), expected)

    def test_deterministic_fresh_and_rng_isolated(self):
        state = random.getstate()
        first = generator.generate(900_000, 17, difficulty="hard")
        second = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_both_matter(self):
        base = generator.generate(910_000, 1)
        self.assertNotEqual(base, generator.generate(910_001, 1))
        self.assertNotEqual(base, generator.generate(910_000, 2))

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 1, unknown_axis="x")
        with self.assertRaises(ValueError):
            generator.generate(1, 1, scene_profile="not_a_profile")

    def test_base_sources_and_canonical_program_replay_public_pairs(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import (
            strip_line_comments,
            wrap_rule,
        )

        base = json.loads(
            (
                DATA_ROOT
                / "base/solutions/training/351d6448__aea4d55345a1.json"
            ).read_text(encoding="utf-8")
        )
        raw = base["racket_target"]["raw_code"]
        target = base["racket_target"]["target_code"]
        program = canonical_row()["program_solution"]
        self.assertEqual(
            " ".join(strip_line_comments(raw).split()),
            " ".join(strip_line_comments(target).split()),
        )
        pairs = canonical_pairs()
        with RacketBridge(timeout=30, startup_timeout=60) as bridge:
            for program_index, source in enumerate((raw, target, program)):
                rule_name = f"__aea_rule_{program_index}"
                bridge.eval_text(
                    f"(define {rule_name} {wrap_rule(source)})"
                )
                for pair_index, pair in enumerate(pairs):
                    grid_name = f"__aea_grid_{program_index}_{pair_index}"
                    bridge.define_grid(grid_name, pair["input"])
                    self.assertEqual(
                        bridge.eval_text(f"({rule_name} {grid_name})"),
                        pair["output"],
                    )
        self.assertEqual(generator.RULE_HASH, "3af11f1e6cf1")


if __name__ == "__main__":
    unittest.main()
