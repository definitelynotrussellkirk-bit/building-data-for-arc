"""Independent regression tests for the color-region rotation generator."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TASK_ID = "5bba6e671cec"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from src.core.canonical_pairs import load_task_pairs
from puzzle_generators import base

SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", TASK_DIR / "generator.py")
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)

BANDS = ("easy", "medium", "hard")
FRAME_COLORS = {4, 7}


def canonical_pairs():
    return load_task_pairs(TASK_ID, REPO / "shared" / "data" / "canonical" / "puzzles.jsonl")


def normalized(grid):
    return tuple(tuple(row) for row in grid)


def cycle_colors(grid):
    return set(v for row in grid for v in row) - FRAME_COLORS


def centroid_angle(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"missing color {color}")
    mr = sum(r for r, _ in cells) / len(cells)
    mc = sum(c for _, c in cells) / len(cells)
    cr = (len(grid) - 1) / 2
    cc = (len(grid[0]) - 1) / 2
    return math.atan2(mc - cc, -(mr - cr)) % (2 * math.pi)


def independent_oracle(grid):
    colors = sorted(cycle_colors(grid), key=lambda color: centroid_angle(grid, color))
    if len(colors) < 2:
        raise ValueError("need at least two rotating colors")
    mapping = {color: colors[(index - 1) % len(colors)] for index, color in enumerate(colors)}
    return [[value if value in FRAME_COLORS else mapping[value] for value in row] for row in grid]


def components(grid, *, include_zero=False):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if include_zero or value != 0
    }
    answer = []
    while unseen:
        origin = min(unseen)
        color = grid[origin[0]][origin[1]]
        unseen.remove(origin)
        stack = [origin]
        cells = {origin}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        answer.append((color, cells))
    return answer


def observed_axes(grid):
    colors = cycle_colors(grid)
    return {"region_count": len(colors), "include_zero": 0 in colors}


class GeneratorRegressionTests(unittest.TestCase):
    def test_rule_hash_and_metadata_bind_selected_rule(self):
        self.assertEqual(getattr(generator, "RULE_HASH", None), "f90a485d851e")
        self.assertEqual(generator.GENERATOR_ID, TASK_ID)
        self.assertEqual(generator.TASK_ID, TASK_ID)
        self.assertEqual(set(generator.AXES), {"region_count", "include_zero"})
        self.assertEqual(generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS, [])
        self.assertEqual(generator.EXAMPLES_NEEDED, 3)

    def test_independent_oracle_matches_all_canonical_outputs(self):
        pairs = canonical_pairs()
        self.assertGreaterEqual(len(pairs), 4)
        self.assertEqual(len({normalized(pair["input"]) for pair in pairs}), 4)
        for pair in pairs:
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(independent_oracle(pair["input"]), pair["output"])

    def test_canonical_inputs_are_accepted_and_generator_oracle_matches(self):
        for pair in canonical_pairs():
            before = normalized(pair["input"])
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(generator.self_check(pair["input"]), [])
                self.assertEqual(generator.strict_canonical_like(pair["input"]), [])
                self.assertEqual(generator._semantic_oracle(pair["input"]), pair["output"])
                self.assertEqual(normalized(pair["input"]), before)

    def test_default_draws_are_lawful_deterministic_and_do_not_touch_global_rng(self):
        self.addCleanup(random.setstate, random.getstate())
        random.seed(580013)
        initial_state = random.getstate()
        profiles = set()
        palette_profiles = set()
        for band, seed, sample_index in itertools.product(BANDS, range(8), range(6)):
            with self.subTest(band=band, seed=seed, sample_index=sample_index):
                grid = generator.generate(seed, sample_index, difficulty=band)
                duplicate = generator.generate(seed, sample_index, difficulty=band)
                self.assertEqual(grid, duplicate)
                self.assertIsNot(grid, duplicate)
                self.assertTrue(all(a is not b for a, b in zip(grid, duplicate)))
                self.assertEqual((len(grid), len(grid[0])), (8, 8))
                colors = set(v for row in grid for v in row)
                self.assertTrue(FRAME_COLORS <= colors)
                self.assertTrue(2 <= len(colors - FRAME_COLORS) <= 4)
                self.assertEqual(generator.self_check(grid, difficulty=band), [])
                self.assertEqual(generator.strict_canonical_like(grid), [])
                expected = independent_oracle(grid)
                self.assertEqual(generator._semantic_oracle(grid), expected)
                self.assertNotEqual(expected, grid)
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        if value in FRAME_COLORS:
                            self.assertEqual(expected[r][c], value)
                self.assertEqual(generator.observe_overrides(grid), observed_axes(grid))
                profiles.add(generator.schedule_profile(seed, sample_index, band))
                palette_profiles.add((len(grid), len(grid[0]), len(colors)))
        self.assertEqual(profiles, set(generator.SCHEDULE_PROFILES))
        self.assertTrue({(8, 8, 4), (8, 8, 5), (8, 8, 6)} <= palette_profiles)
        self.assertEqual(random.getstate(), initial_state)

    def test_every_declared_override_combination_is_constructive_and_exact(self):
        for band, region_count, include_zero in itertools.product(BANDS, range(2, 5), (False, True)):
            kwargs = {"region_count": region_count, "include_zero": include_zero}
            with self.subTest(band=band, **kwargs):
                grid = generator.generate(1901, 7, difficulty=band, **kwargs)
                self.assertEqual(observed_axes(grid), kwargs)
                self.assertEqual(generator.observe_overrides(grid), kwargs)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator._semantic_oracle(grid), independent_oracle(grid))

    def test_context_records_actual_axes_and_exact_overrides(self):
        cases = ({}, {"region_count": 2}, {"include_zero": True},
                 {"region_count": 4, "include_zero": False})
        for band, kwargs in itertools.product(BANDS, cases):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(77, 4, difficulty=band, **kwargs)
            finally:
                base.set_ctx_observer(None)
            with self.subTest(band=band, kwargs=kwargs):
                self.assertEqual(len(captured), 1)
                observed = observed_axes(grid)
                self.assertEqual({name: captured[0].axis_value(name) for name in generator.AXES}, observed)
                self.assertEqual(captured[0].overrides_used(), kwargs)

    def test_invalid_difficulty_unknown_axes_types_and_values_are_rejected(self):
        invalid_overrides = [
            {"bogus": 1}, {"texture": "warm"}, {"region_count": 1},
            {"region_count": 5}, {"region_count": True}, {"region_count": 3.0},
            {"region_count": "3"}, {"region_count": None}, {"include_zero": 1},
            {"include_zero": 0}, {"include_zero": "true"}, {"include_zero": None},
        ]
        for kwargs in invalid_overrides:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, difficulty="medium", **kwargs)
        for difficulty in ("expert", "", 0, 0.5, True, [], {}):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, difficulty=difficulty)

    def test_four_slot_schedule_covers_every_profile_in_each_complete_lesson(self):
        self.assertEqual(generator.SCHEDULE_PERIOD, 4)
        self.assertEqual(len(generator.SCHEDULE_PROFILES), 4)
        for band, seed, start in itertools.product(BANDS, range(8), range(9)):
            profiles = {
                generator.schedule_profile(seed, start + offset, band)
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            }
            with self.subTest(band=band, seed=seed, start=start):
                self.assertEqual(profiles, set(generator.SCHEDULE_PROFILES))

    def test_default_profile_axes_cover_four_three_with_zero_and_two_regions(self):
        expected = {
            "dual_zero_three": {"region_count": 3, "include_zero": True},
            "row_four": {"region_count": 4, "include_zero": False},
            "quadrant_zero_three": {"region_count": 3, "include_zero": True},
            "paired_two": {"region_count": 2, "include_zero": False},
        }
        self.assertEqual(set(expected), set(generator.SCHEDULE_PROFILES))
        for band, seed, sample_index in itertools.product(BANDS, range(5), range(9)):
            profile = generator.schedule_profile(seed, sample_index, band)
            grid = generator.generate(seed, sample_index, difficulty=band)
            with self.subTest(band=band, seed=seed, sample_index=sample_index, profile=profile):
                self.assertEqual(observed_axes(grid), expected[profile])

    def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs(self):
        self.assertTrue(generator.CANONICAL_SHORTCUTS)
        for name, rival in generator.CANONICAL_SHORTCUTS.items():
            for pair in canonical_pairs():
                with self.subTest(rival=name, split=pair["split"], pair=pair["pair_index"]):
                    self.assertEqual(rival(pair["input"]), pair["output"])

    def test_every_sliding_three_demo_lesson_refutes_all_declared_competitors(self):
        for band, seed, start in itertools.product(BANDS, range(30), range(6)):
            grids = [generator.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": independent_oracle(grid)} for grid in grids]
            demos, query = pairs[:3], pairs[3]
            with self.subTest(band=band, seed=seed, start=start):
                self.assertEqual(generator.lesson_identifiable(demos, query), [])
                for name, rival in generator.LESSON_COMPETITORS.items():
                    self.assertTrue(
                        any(rival(pair["input"]) != pair["output"] for pair in demos),
                        f"{name} survived all demonstrations",
                    )

    def test_every_query_rotation_of_a_four_pair_lesson_is_identifiable(self):
        for band, seed, start in itertools.product(BANDS, range(30), range(8)):
            grids = [generator.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": independent_oracle(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                with self.subTest(
                    band=band, seed=seed, start=start, query_index=query_index
                ):
                    self.assertEqual(generator.lesson_identifiable(demos, query), [])
                    for name, rival in generator.LESSON_COMPETITORS.items():
                        self.assertTrue(
                            any(rival(pair["input"]) != pair["output"] for pair in demos),
                            f"{name} survived rotation with query index {query_index}",
                        )

    def test_witness_claims_are_real_disagreements(self):
        fixtures = [pair["input"] for pair in canonical_pairs()]
        fixtures.extend(
            generator.generate(seed, index, difficulty=band)
            for band, seed, index in itertools.product(BANDS, range(8), range(3))
        )
        hit_counts = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        for grid in fixtures:
            correct = independent_oracle(grid)
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    hit_counts[name] += 1
                    rivals = generator.WITNESS_RIVALS[name]
                    self.assertTrue(rivals)
                    self.assertTrue(
                        any(generator.SEMANTIC_RIVALS[rival](grid) != correct for rival in rivals),
                        f"{name} fired without a named rival disagreement",
                    )
        self.assertTrue(all(count > 0 for count in hit_counts.values()), hit_counts)

    def test_zero_is_a_rotating_region_not_background(self):
        for band in BANDS:
            sample_index = next(
                index for index in range(6)
                if generator.schedule_profile(0, index, band) in {"dual_zero_three", "quadrant_zero_three"}
            )
            grid = generator.generate(0, sample_index, difficulty=band)
            expected = independent_oracle(grid)
            with self.subTest(band=band):
                self.assertIn(0, cycle_colors(grid))
                self.assertNotEqual(generator.SEMANTIC_RIVALS["zero_is_background"](grid), expected)
                self.assertTrue(any(grid[r][c] == 0 and expected[r][c] != 0
                                    for r in range(8) for c in range(8)))

    def test_structural_support_overlaps_canonical_component_scale(self):
        counts, maxima = set(), set()
        canonical_grids = {normalized(pair["input"]) for pair in canonical_pairs()}
        generated = set()
        for band, seed, index in itertools.product(BANDS, range(20), range(6)):
            grid = generator.generate(seed, index, difficulty=band)
            objects = components(grid)
            counts.add(len(objects))
            maxima.add(max(len(cells) for _, cells in objects))
            generated.add(normalized(grid))
        self.assertTrue(any(9 <= count <= 11 for count in counts), counts)
        self.assertTrue(any(13 <= size <= 25 for size in maxima), maxima)
        self.assertTrue(generated.isdisjoint(canonical_grids))
        self.assertGreater(len(generated), 80)

    def test_difficulty_bands_are_not_dead_aliases(self):
        differences = 0
        for seed, index in itertools.product(range(10), range(6)):
            grids = [normalized(generator.generate(seed, index, difficulty=band)) for band in BANDS]
            differences += int(len(set(grids)) > 1)
        self.assertGreaterEqual(differences, 45)

    def test_validators_reject_malformed_and_semantically_ambiguous_inputs(self):
        malformed = {
            "none": None,
            "scalar": 4,
            "string": "4477",
            "empty": [],
            "zero-width": [[]],
            "ragged": [[4, 7], [4]],
            "boolean": [[4, 7], [0, True]],
            "float": [[4, 7], [0, 1.0]],
            "negative": [[4, 7], [0, -1]],
            "large-color": [[4, 7], [0, 10]],
            "missing-four": [[7, 7], [1, 2]],
            "missing-seven": [[4, 4], [1, 2]],
            "one-cycle-color": [[4, 7], [1, 1]],
            "five-cycle-colors": [[4, 7, 0], [1, 2, 3], [5, 6, 4]],
        }
        for name, grid in malformed.items():
            with self.subTest(name=name):
                reasons = generator.self_check(grid)
                self.assertIsInstance(reasons, list)
                self.assertTrue(reasons)
                self.assertTrue(all(isinstance(reason, str) and reason for reason in reasons))
                self.assertTrue(generator.strict_canonical_like(grid))

    def test_default_none_and_fresh_return_contract(self):
        implicit = generator.generate(29, 3)
        explicit = generator.generate(29, 3, difficulty=None)
        self.assertEqual(implicit, explicit)
        self.assertIsNot(implicit, explicit)
        self.assertTrue(all(a is not b for a, b in zip(implicit, explicit)))
        implicit[0][0] = (implicit[0][0] + 1) % 10
        self.assertEqual(generator.generate(29, 3), explicit)

    def test_curriculum_probe_cli_is_source_bound_and_rotation_complete(self):
        script = TASK_DIR / "workspace" / "curriculum_probe.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "probe.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--seeds",
                    "2",
                    "--starts",
                    "4",
                    "--out",
                    str(report),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
            )
            payload = json.loads(report.read_text())
        expected_sha = hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()
        self.assertEqual(payload["status"], "no_ambiguity_found")
        self.assertEqual(payload["source"]["generator_sha256"], expected_sha)
        self.assertEqual(payload["source"]["version"], generator.VERSION)
        self.assertEqual(payload["configuration"]["bands"], list(BANDS))
        self.assertEqual(payload["summary"]["lessons"], 3 * 2 * 4)
        self.assertEqual(payload["summary"]["rotations"], 3 * 2 * 4 * 4)
        self.assertEqual(payload["summary"]["ambiguous_rotations"], 0)
        self.assertGreater(payload["summary"]["unique_inputs"], 20)
        self.assertEqual(
            set(payload["rivals"]),
            set(generator.LESSON_COMPETITORS),
        )
        self.assertEqual(
            set(payload["canonical_shortcuts"]),
            set(generator.CANONICAL_SHORTCUTS),
        )
        self.assertTrue(
            all(entry["fits_all_canonical_pairs"] for entry in payload["canonical_shortcuts"].values())
        )


if __name__ == "__main__":
    unittest.main()
