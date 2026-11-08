from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import importlib
import importlib.util
import json
import random
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs as load_canonical_pairs
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK = "196a7ec58bbc"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
TASK_HOME = Path(__file__).resolve().parents[1]
BASE_CANDIDATES = (
    ROOT / "shared/data/base/solutions/training/46442a0e__196a7ec58bbc.json",
    ROOT / "data/base/solutions/training/46442a0e__196a7ec58bbc.json",
)
BASE_PATH = next((path for path in BASE_CANDIDATES if path.exists()), BASE_CANDIDATES[0])


def canonical_row() -> dict:
    matches = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row for {TASK}, got {len(matches)}")
    return matches[0]


def canonical_pairs() -> list[dict]:
    return list(load_canonical_pairs(TASK, root=ROOT, labeled_only=True))


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    original, clockwise, half_turn, counterclockwise = MOD._rotations(grid)
    top = [left + right for left, right in zip(original, clockwise)]
    bottom = [left + right for left, right in zip(counterclockwise, half_turn)]
    return top + bottom


def load_prototype():
    path = TASK_HOME / "workspace/parametric/prototype.py"
    if not path.exists():
        raise AssertionError(f"missing parametric prototype: {path}")
    spec = importlib.util.spec_from_file_location("rotation_kaleidoscope_parametric", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load parametric prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_prototype_verifier():
    path = TASK_HOME / "workspace/parametric/verify.py"
    if not path.exists():
        raise AssertionError(f"missing parametric verifier: {path}")
    spec = importlib.util.spec_from_file_location(
        "rotation_kaleidoscope_parametric_verify", path
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load parametric verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RotationKaleidoscopeGeneratorTests(unittest.TestCase):
    def test_every_canonical_input_is_accepted_and_matches_quadrants(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            grid = pair["input"]
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(expected_output(grid), pair["output"])

    def test_default_distribution_is_exact_rotation_distinct_and_reflection_distinguishing(self):
        medium_sizes = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = MOD.generate(seed, seed * 31 + 7, difficulty=band)
                errors = MOD.self_check(grid, difficulty=band)
                self.assertEqual(errors, [], (band, seed, grid, errors))
                side = len(grid)
                palette_size = len({value for row in grid for value in row})
                self.assertEqual(MOD._rotation_orbit_size(grid), 4)
                self.assertTrue(MOD.SEMANTIC_WITNESSES["rotation_not_reflection"](grid))
                self.assertEqual(
                    MOD.observe_overrides(grid),
                    {"grid_n": side, "palette_size": palette_size},
                )
                if side == 2:
                    self.assertIn(palette_size, (2, 3, 4))
                    if palette_size == 2:
                        self.assertEqual(sorted(Counter(sum(grid, [])).values()), [1, 3])
                else:
                    self.assertIn(palette_size, (2, 3, 4))
                    counts = Counter(sum(grid, []))
                    self.assertGreaterEqual(min(counts.values()), 2)
                if band == "easy":
                    self.assertEqual(side, 2)
                elif band == "hard":
                    self.assertEqual(side, 3)
                else:
                    medium_sizes.add(side)
        self.assertEqual(medium_sizes, {2, 3})

    def test_exact_overrides_and_internal_texture_priors(self):
        for side, palette_size in (
            (2, 2),
            (2, 3),
            (2, 4),
            (3, 2),
            (3, 3),
            (3, 4),
        ):
            for band in (None, "easy", "medium", "hard"):
                for seed in range(30):
                    grid = MOD.generate(
                        10_000 + seed,
                        seed * 17,
                        difficulty=band,
                        grid_n=side,
                        palette_size=palette_size,
                    )
                    self.assertEqual(len(grid), side)
                    self.assertEqual(
                        len({value for row in grid for value in row}), palette_size
                    )
                    self.assertEqual(MOD._rotation_orbit_size(grid), 4)
                    self.assertTrue(MOD.SEMANTIC_WITNESSES["rotation_not_reflection"](grid))
                    self.assertEqual(
                        MOD.observe_overrides(grid),
                        {"grid_n": side, "palette_size": palette_size},
                    )
                    if (side, palette_size) == (2, 2):
                        self.assertEqual(sorted(Counter(sum(grid, [])).values()), [1, 3])

        seen_textures = set()
        for seed in range(500):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = MOD.generate(20_000 + seed, seed, difficulty="hard")
            finally:
                set_ctx_observer(None)
            self.assertEqual(MOD.self_check(grid), [], (seed, grid))
            self.assertEqual(MOD._rotation_orbit_size(grid), 4)
            self.assertTrue(captured)
            seen_textures.add(captured[-1].recorded_draws()["texture"])
        self.assertEqual(seen_textures, set(MOD._TEXTURE_PRIORS))

        for seed in range(50):
            grid = MOD.generate(30_000 + seed, seed, palette_size=2)
            self.assertIn(len(grid), (2, 3))
            self.assertEqual(len({value for row in grid for value in row}), 2)

    def test_each_band_has_canonical_profile_support_in_twenty_draws(self):
        profiles = {
            (
                len(pair["input"]),
                len(pair["input"][0]),
                len({value for row in pair["input"] for value in row}),
            )
            for pair in canonical_pairs()
        }
        for band in ("easy", "medium", "hard"):
            hits = []
            for sample_index in range(20):
                grid = MOD.generate(41, sample_index, difficulty=band)
                profile = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                if profile in profiles:
                    hits.append((sample_index, profile))
            self.assertTrue(hits, (band, profiles))

    def test_invalid_call_scalars_and_overrides_fail_loudly(self):
        for bad_seed in (True, False, 1.0, 1.75, "1"):
            with self.subTest(seed=bad_seed):
                with self.assertRaises(ValueError):
                    MOD.generate(bad_seed, 0)
        for bad_index in (True, False, 1.0, 1.75, "1", -1):
            with self.subTest(sample_index=bad_index):
                with self.assertRaises(ValueError):
                    MOD.generate(0, bad_index)

        invalid = (
            {"grid_n": 1},
            {"grid_n": 4},
            {"grid_n": True},
            {"palette_size": 1},
            {"palette_size": 5},
            {"palette_size": False},
            {"texture": "not-a-public-axis"},
            {"unknown_axis": 3},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = {
            "empty": [],
            "ragged": [[1, 2], [3]],
            "non_square": [[1, 2, 3], [4, 5, 6]],
            "oversized": [[(r + c) % 3 for c in range(4)] for r in range(4)],
            "monochrome": [[1, 1], [1, 1]],
            "two_color_row_stripe": [[1, 1], [2, 2]],
            "center_singleton": [[1, 1, 1], [1, 2, 1], [1, 1, 1]],
            "rotation_symmetric_checker": [[1, 2, 1], [2, 1, 2], [1, 2, 1]],
            "invalid_color": [[1, 2], [3, 10]],
            "boolean_color": [[1, 2], [3, True]],
        }
        for name, grid in cases.items():
            with self.subTest(name=name):
                self.assertTrue(MOD.self_check(grid), (name, grid))

        canonical_exception = [[8, 6], [6, 8]]
        self.assertEqual(MOD.self_check(canonical_exception), [])
        self.assertEqual(MOD._rotation_orbit_size(canonical_exception), 2)

        generated_two_color = [[1, 2], [1, 1]]
        self.assertEqual(MOD.self_check(generated_two_color), [])
        self.assertEqual(MOD._rotation_orbit_size(generated_two_color), 4)

    def test_semantic_contract_reproduces_and_rejects_retained_mirror_ambiguity(self):
        mirror = MOD.SEMANTIC_RIVALS["mirror_quadrants"]
        for pair in canonical_pairs():
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])

        demo_inputs = (
            [[8, 2], [2, 7]],
            [[9, 0], [0, 7]],
            [[3, 1], [1, 5]],
        )
        query_input = [[0, 7], [5, 8]]
        demos = [
            {"input": grid, "output": expected_output(grid)} for grid in demo_inputs
        ]
        query = {"input": query_input, "output": expected_output(query_input)}
        self.assertTrue(all(mirror(pair["input"]) == pair["output"] for pair in demos))
        self.assertNotEqual(mirror(query_input), query["output"])
        reasons = MOD.lesson_identifiable(demos, query)
        self.assertTrue(any("mirror_quadrants" in reason for reason in reasons), reasons)

    def test_generated_three_demo_windows_identify_rotation_against_reflection(self):
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                pairs = []
                for offset in range(4):
                    grid = MOD.generate(500 + start, start * 11 + offset, difficulty=band)
                    pairs.append({"input": grid, "output": MOD.rule_mirror(grid)})
                for query_index, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    self.assertEqual(
                        MOD.lesson_identifiable(demos, query),
                        [],
                        (band, start, query_index),
                    )

    def test_determinism_freshness_and_global_random_state(self):
        for band in (None, "easy", "medium", "hard"):
            random.seed(47)
            state = random.getstate()
            first = MOD.generate(17, 23, difficulty=band)
            self.assertEqual(random.getstate(), state)
            second = MOD.generate(17, 23, difficulty=band)
            self.assertEqual(first, second)
            self.assertIsNot(first, second)
            self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_task_local_rule_sources_are_synchronized(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(digest, "24bc23963715")
        self.assertEqual(MOD.RULE_HASH, digest)

        from solvers.grounded_rules import GROUNDED_RULES

        self.assertEqual(GROUNDED_RULES[TASK], source)
        base = json.loads(BASE_PATH.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(
            base["racket_target"]["canonicalization_status"],
            "synchronized_to_canonical_program_solution",
        )

    def test_parametric_handedness_prototype_is_episode_stable_and_answer_masked(self):
        proto = load_prototype()
        grid = [[0, 1], [2, 3]]
        canonical = proto.solve(grid, handedness="clockwise")
        alternate = proto.solve(grid, handedness="counterclockwise")
        self.assertEqual(canonical, expected_output(grid))
        self.assertNotEqual(canonical, alternate)
        self.assertEqual(proto.DEFAULT_HANDEDNESS, "clockwise")
        self.assertEqual(set(proto.ALLOWED_HANDEDNESS), {"clockwise", "counterclockwise"})

        for seed in range(4):
            episode = proto.generate_episode(seed)
            setting = episode["parameters"]["handedness"]
            other = (
                "counterclockwise" if setting == "clockwise" else "clockwise"
            )
            pairs = episode["train"] + episode["test"]
            self.assertEqual(len(episode["train"]), 3)
            self.assertEqual(len(episode["test"]), 1)
            for pair in pairs:
                self.assertEqual(pair["output"], proto.solve(pair["input"], handedness=setting))
                self.assertNotEqual(pair["output"], proto.solve(pair["input"], handedness=other))

            public = proto.public_challenge(episode)
            self.assertNotIn("parameters", public)
            self.assertNotIn("program", public)
            self.assertTrue(all("output" in pair for pair in public["train"]))
            self.assertTrue(all("output" not in pair for pair in public["test"]))

    def test_parametric_counts_are_independent_unique_and_validated(self):
        proto = load_prototype()
        episode = proto.generate_episode(11, demonstration_count=3, query_count=4)
        self.assertEqual(len(episode["train"]), 3)
        self.assertEqual(len(episode["test"]), 4)
        self.assertEqual(episode["meta"]["demonstration_count"], 3)
        self.assertEqual(episode["meta"]["query_count"], 4)

        pairs = episode["train"] + episode["test"]
        input_hashes = [proto.grid_hash(pair["input"]) for pair in pairs]
        self.assertEqual(len(input_hashes), len(set(input_hashes)))

        setting = episode["parameters"]["handedness"]
        rival = next(value for value in proto.SETTINGS if value != setting)
        for pair in pairs:
            self.assertEqual(
                pair["output"],
                proto.solve(pair["input"], handedness=setting),
            )
            self.assertNotEqual(
                pair["output"],
                proto.solve(pair["input"], handedness=rival),
            )

        defaults = proto.generate_episode(12)
        self.assertEqual((len(defaults["train"]), len(defaults["test"])), (3, 1))

        for bad in (0, -1, True, 1.0, "4"):
            with self.subTest(demonstration_count=bad):
                with self.assertRaises(ValueError):
                    proto.generate_episode(0, demonstration_count=bad)
            with self.subTest(query_count=bad):
                with self.assertRaises(ValueError):
                    proto.generate_episode(0, query_count=bad)

    def test_parametric_public_writer_uses_visible_content_identity(self):
        proto = load_prototype()
        first = proto.generate_episode(21, handedness="clockwise", query_count=4)
        second = proto.generate_episode(22, handedness="counterclockwise", query_count=4)

        visible = proto.public_challenge(first)
        expected_bytes = public_challenge_bytes(visible)
        expected_id = public_challenge_id(visible)
        self.assertEqual(proto.public_bytes(first), expected_bytes)
        self.assertEqual(proto.public_id(first), expected_id)
        self.assertEqual(
            proto.public_filename(first),
            f"challenge-{expected_id}.json",
        )

        private_mutation = deepcopy(first)
        private_mutation["parameters"] = {"handedness": "counterclockwise"}
        private_mutation["program"] = "private replacement"
        private_mutation["meta"] = {"seed": 999, "private": True}
        for pair in private_mutation["test"]:
            pair["output"] = [[9]]
        self.assertEqual(proto.public_bytes(private_mutation), expected_bytes)
        self.assertEqual(proto.public_id(private_mutation), expected_id)

        visible_mutation = deepcopy(first)
        cell = visible_mutation["test"][0]["input"][0][0]
        visible_mutation["test"][0]["input"][0][0] = (cell + 1) % 10
        self.assertNotEqual(proto.public_id(visible_mutation), expected_id)

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            written = proto.write_public_batch([second, first], out)
            self.assertEqual(
                [row["public_id"] for row in written],
                sorted((proto.public_id(first), proto.public_id(second))),
            )
            for row in written:
                path = Path(row["path"])
                self.assertEqual(path.parent, out)
                self.assertEqual(path.name, f"challenge-{row['public_id']}.json")
                self.assertNotIn("clockwise", path.name)
                self.assertNotIn("counterclockwise", path.name)
                self.assertEqual(path.read_bytes(), row["public_bytes"])

            reversed_written = proto.write_public_batch([first, second], out)
            self.assertEqual(
                [(row["public_id"], row["path"]) for row in reversed_written],
                [(row["public_id"], row["path"]) for row in written],
            )
            with self.assertRaisesRegex(ValueError, "duplicate public payload"):
                proto.write_public_batch([first, deepcopy(first)], out)

    def test_parametric_public_cli_writes_content_addressed_file(self):
        proto = load_prototype()
        episode = proto.generate_episode(
            7,
            handedness="counterclockwise",
            demonstration_count=3,
            query_count=4,
        )
        expected_id = proto.public_id(episode)
        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            argv = [
                "prototype.py",
                "--seed",
                "7",
                "--handedness",
                "counterclockwise",
                "--demonstrations",
                "3",
                "--queries",
                "4",
                "--public-dir",
                directory,
            ]
            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                self.assertEqual(proto.main(), 0)

            receipt = json.loads(stdout.getvalue())
            path = Path(directory) / f"challenge-{expected_id}.json"
            self.assertEqual(receipt["public_id"], expected_id)
            self.assertEqual(Path(receipt["path"]), path)
            self.assertEqual(path.read_bytes(), proto.public_bytes(episode))

    def test_parametric_verifier_and_replay_documentation_are_present(self):
        verifier = load_prototype_verifier()
        self.assertEqual(
            verifier.REPORT_SCHEMA,
            "196a7ec58bbc-parametric-handedness-v2",
        )
        self.assertEqual(verifier.RETAINED_DEMONSTRATION_COUNT, 3)
        self.assertEqual(verifier.RETAINED_QUERY_COUNT, 4)
        episodes = TASK_HOME / "workspace/parametric/episodes"
        for name, expected in verifier.LEGACY_ARTIFACT_SHA256.items():
            path = episodes / name
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
        self.assertTrue(callable(verifier.build_report))
        readme = TASK_HOME / "workspace/parametric/README.md"
        self.assertTrue(readme.exists(), readme)
        text = readme.read_text()
        self.assertIn("workspace/parametric/verify.py", text)
        self.assertIn("../checks/parametric/196a7ec58bbc-handedness-v2.json", text)
        self.assertIn("--queries 4", text)


if __name__ == "__main__":
    unittest.main()
