"""Independent contract tests for the unselected marker-area prototype.

Run with unittest; neither pytest nor a globally cached prototype is required.
The literal boundary witness deliberately repeats a marker color across rooms.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = (
    ROOT / "generators/36b22ff07a2e/workspace/parametric/prototype.py"
)
EXPECTED_SETTINGS = (
    {"minimum_marker_area": 1},
    {"minimum_marker_area": 2},
    {"minimum_marker_area": 4},
)


def _load_exact(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load exact source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SUPPORT = _load_exact(
    ROOT / "shared/runtime/reviewer_support.py",
    "_marker_area_test_reviewer_support",
)


def _boundary_witness():
    # Background 7, separating field 9. Room areas in row order are
    # 1, 2 (horizontal), 2 (vertical), 3, 4, 0. Color 1 has total area 4
    # across two rooms, but neither of those rooms qualifies at threshold 4.
    return [
        [int(cell) for cell in row.replace(" ", "")]
        for row in (
            "777777777777777777",
            "799999999999999997",
            "79 7777 9 7777 9 7377 97",
            "79 7177 9 7227 9 7377 97",
            "79 7777 9 7777 9 7777 97",
            "799999999999999997",
            "79 7777 9 7557 9 7777 97",
            "79 1117 9 7557 9 7777 97",
            "79 7777 9 7777 9 7777 97",
            "799999999999999997",
            "777777777777777777",
        )
    ]


BOUNDARY_OUTPUTS = {
    1: [[1, 2, 3], [1, 5, 7]],
    2: [[7, 2, 3], [1, 5, 7]],
    4: [[7, 7, 7], [7, 5, 7]],
}


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _public_files(out):
    return {
        path.relative_to(out / "public").as_posix(): path.read_bytes()
        for path in sorted((out / "public").rglob("*"))
        if path.is_file()
    }


class ParametricMarkerAreaTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(
            PROTOTYPE_PATH.is_file(),
            "marker-area prototype has not been implemented at its selected path",
        )
        self.proto = _load_exact(PROTOTYPE_PATH, "_parametric_marker_area_36b22ff07a2e")

    def test_default_program_is_exact_canonical_authority(self):
        """Catch changing the canonical default while adding threshold variants."""
        rules = set()
        with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                if row.get("task_id") == "36b22ff07a2e":
                    rules.add(row["program_solution"])
        self.assertEqual(len(rules), 1)
        canonical = rules.pop()
        self.assertEqual(tuple(self.proto.SETTINGS), EXPECTED_SETTINGS)
        self.assertEqual(self.proto.program(EXPECTED_SETTINGS[0]), canonical)
        self.assertEqual(len({self.proto.program(s) for s in EXPECTED_SETTINGS}), 3)

    def test_literal_boundaries_count_area_per_room_and_keep_empty_rooms(self):
        """Catch strict-greater, width/height, color-global, and dropped-room rules."""
        grid = _boundary_witness()
        before = deepcopy(grid)
        for threshold, expected in BOUNDARY_OUTPUTS.items():
            with self.subTest(threshold=threshold):
                actual = self.proto.transform(grid, {"minimum_marker_area": threshold})
                self.assertEqual(actual, expected)
                self.assertTrue(all(type(cell) is int for row in actual for cell in row))
                self.assertEqual(grid, before)

    def test_unknown_coerced_and_out_of_family_settings_reject(self):
        """Catch bool/float equality coercion and silently ignored parameter keys."""
        invalid = [None, {}, 2, {"unknown": 2},
                   {"minimum_marker_area": 2, "unknown": 0}]
        invalid += [{"minimum_marker_area": value}
                    for value in (True, False, 1.0, 2.0, 4.0, "2", 0, 3, 5)]
        for settings in invalid:
            for name, invoke in (
                ("program", lambda: self.proto.program(settings)),
                ("transform", lambda: self.proto.transform(_boundary_witness(), settings)),
                ("generate", lambda: self.proto.generate(0, settings)),
            ):
                with self.subTest(settings=settings, api=name):
                    with self.assertRaises((TypeError, ValueError)):
                        invoke()

    def test_seed_bounds_require_exact_integers(self):
        """Catch negative, overflowing, boolean, or coerced episode seeds."""
        for seed in (0, 2**63 - 1):
            demos, queries = self.proto.sample_inputs(seed, demos=2, queries=1)
            self.assertEqual((len(demos), len(queries)), (2, 1))
        for seed in (-1, 2**63, True, False, 0.0, 1.5, "0", None):
            for name, invoke in (
                ("sample_inputs", lambda: self.proto.sample_inputs(seed)),
                ("generate", lambda: self.proto.generate(seed, EXPECTED_SETTINGS[0])),
            ):
                with self.subTest(seed=seed, api=name):
                    with self.assertRaises((TypeError, ValueError)):
                        invoke()

    def test_demo_query_counts_have_independent_exact_bounds(self):
        """Catch unsupported counts and accidentally coupled demo/query counts."""
        for demo_count, query_count in ((2, 1), (8, 8)):
            demos, queries = self.proto.sample_inputs(
                12, demos=demo_count, queries=query_count
            )
            self.assertIs(type(demos), list)
            self.assertIs(type(queries), list)
            self.assertEqual((len(demos), len(queries)), (demo_count, query_count))
            episode = self.proto.generate(
                12, EXPECTED_SETTINGS[1], demos=demo_count, queries=query_count
            )
            self.assertEqual(
                (len(episode["train"]), len(episode["test"])), (demo_count, query_count)
            )
        for name, bad_values in (
            ("demos", (0, 1, 9, True, 2.0, "2", None)),
            ("queries", (0, 9, False, 1.0, "1", None)),
        ):
            for bad in bad_values:
                kwargs = {name: bad}
                for api, invoke in (
                    ("sample_inputs", lambda: self.proto.sample_inputs(0, **kwargs)),
                    ("generate", lambda: self.proto.generate(0, EXPECTED_SETTINGS[0], **kwargs)),
                ):
                    with self.subTest(count=name, bad=bad, api=api):
                        with self.assertRaises((TypeError, ValueError)):
                            invoke()

    def test_sampler_is_deterministic_distinct_and_teaches_all_area_boundaries(self):
        """Catch repeated scenes, lost marker orientations, or global-RNG changes."""
        generator, _, _ = SUPPORT.load_selected_generator("36b22ff07a2e", root=ROOT)
        self.addCleanup(random.setstate, random.getstate())
        random.seed(97031)
        state = random.getstate()
        first = self.proto.sample_inputs(31)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, self.proto.sample_inputs(31))
        self.assertEqual(tuple(map(len, first)), (2, 4))
        grids = first[0] + first[1]
        self.assertEqual(len({json.dumps(g) for g in grids}), len(grids))
        for index, grid in enumerate(grids):
            with self.subTest(scene=index):
                analysis = generator._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                facts = analysis["facts"]
                self.assertTrue({1, 2, 3, 4}.issubset(facts["marker_sizes"]))
                self.assertGreater(facts["empty_room_count"], 0)
                shapes = set()
                for room in facts["room_records"]:
                    top, left, bottom, right = room["bbox"]
                    cells = [(r, c) for r in range(top, bottom + 1)
                             for c in range(left, right + 1)
                             if grid[r][c] != facts["background_color"]]
                    if cells:
                        shapes.add((max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
                                    max(c for _, c in cells) - min(c for _, c in cells) + 1))
                self.assertTrue({(1, 2), (2, 1)}.issubset(shapes))

    def test_same_seed_settings_share_inputs_and_fix_one_rule_per_episode(self):
        """Catch private-setting leakage into sampling or pairwise rule resampling."""
        demos, queries = self.proto.sample_inputs(19, demos=3, queries=2)
        for settings in EXPECTED_SETTINGS:
            with self.subTest(settings=settings):
                episode = self.proto.generate(19, settings, demos=3, queries=2)
                self.assertEqual(_inputs(episode), demos + queries)
                self.assertEqual((len(episode["train"]), len(episode["test"])), (3, 2))
                self.assertEqual(episode["settings"], settings)
                self.assertEqual(episode["program_solution"], self.proto.program(settings))
                for pair in episode["train"] + episode["test"]:
                    self.assertEqual(pair["output"], self.proto.transform(pair["input"], settings))

    def test_certificate_uses_demos_and_ignores_every_query_answer_content(self):
        """Catch certificates borrowing hidden query labels to claim identification."""
        for settings in EXPECTED_SETTINGS:
            episode = self.proto.generate(27, settings)
            before = deepcopy(episode)
            certificate = self.proto.lesson_certificate(episode, settings)
            self.assertEqual(certificate["parameter_survivors"], [settings])
            self.assertEqual(certificate["query_identifiable"], [True] * 4)
            self.assertIs(type(certificate["rival_survivors"]), list)
            self.assertTrue(all(type(name) is str for name in certificate["rival_survivors"]))
            poisoned = deepcopy(episode)
            for pair, answer in zip(poisoned["test"], (None, "ignored", [[True]], [[9]])):
                pair["output"] = answer
            self.assertEqual(self.proto.lesson_certificate(poisoned, settings), certificate)
            for pair in poisoned["test"]:
                del pair["output"]
            self.assertEqual(self.proto.lesson_certificate(poisoned, settings), certificate)
            self.assertEqual(episode, before)

    def test_public_files_use_exact_visible_bytes_and_sorted_content_ids(self):
        """Catch leaking parameters/programs/answers or using noncanonical ID bytes."""
        episodes = [self.proto.generate(8, EXPECTED_SETTINGS[0]),
                    self.proto.generate(9, EXPECTED_SETTINGS[1])]
        expected = {SUPPORT.public_challenge_id(e): SUPPORT.public_challenge_bytes(e)
                    for e in episodes}
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "batch"
            manifest = self.proto.write_batch(episodes, out)
            self.assertEqual(manifest["public_ids"], sorted(expected))
            files = _public_files(out)
            self.assertEqual(len(files), 2)
            for name, content in files.items():
                public = json.loads(content)
                identity = SUPPORT.public_challenge_id(public)
                self.assertIn(identity, Path(name).stem)
                self.assertEqual(content, expected[identity])
                self.assertEqual(set(public), {"train", "test"})
                self.assertTrue(all(set(p) == {"input", "output"} for p in public["train"]))
                self.assertTrue(all(set(p) == {"input"} for p in public["test"]))

    def test_public_names_and_order_ignore_private_changes_and_input_batch_order(self):
        """Catch hidden answers or metadata influencing public filenames and ordering."""
        episodes = [self.proto.generate(51, EXPECTED_SETTINGS[0]),
                    self.proto.generate(52, EXPECTED_SETTINGS[1])]
        altered = deepcopy(episodes)
        for index, episode in enumerate(altered):
            episode["seed"] = 900 + index
            episode["settings"] = deepcopy(EXPECTED_SETTINGS[2])
            episode["program_solution"] = self.proto.program(EXPECTED_SETTINGS[2])
            episode["reviewer_note"] = "private metadata sentinel"
            for pair in episode["test"]:
                pair["output"] = [[9]]
        with tempfile.TemporaryDirectory() as temporary:
            first, second = Path(temporary) / "first", Path(temporary) / "second"
            manifest_a = self.proto.write_batch(episodes, first)
            manifest_b = self.proto.write_batch(list(reversed(altered)), second)
            self.assertEqual(manifest_a["public_ids"], manifest_b["public_ids"])
            self.assertEqual(_public_files(first), _public_files(second))

    def test_writer_rejects_repeated_demo_or_query_inputs(self):
        """Catch duplicate inputs within an episode, including across the split."""
        original = self.proto.generate(61, EXPECTED_SETTINGS[0])
        for split, index in (("train", 1), ("test", 0), ("test", 1)):
            episode = deepcopy(original)
            episode[split][index]["input"] = deepcopy(episode["train"][0]["input"])
            with self.subTest(split=split, index=index), tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary) / "duplicate-input"
                with self.assertRaises(ValueError):
                    self.proto.write_batch([episode], out)
                self.assertFalse(out.exists())

    def test_writer_rejects_duplicate_visible_episodes_despite_private_changes(self):
        """Catch admitting duplicate challenges under different hidden provenance."""
        episode = self.proto.generate(62, EXPECTED_SETTINGS[1])
        duplicate = deepcopy(episode)
        duplicate["seed"] = 999
        for pair in duplicate["test"]:
            pair["output"] = [[8]]
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "duplicate-episode"
            with self.assertRaises(ValueError):
                self.proto.write_batch([episode, duplicate], out)
            self.assertFalse(out.exists())

    def test_writer_rejects_boolean_or_float_cells_in_every_grid_role(self):
        """Catch Python equality treating a bool/float as a valid ARC color."""
        original = self.proto.generate(63, EXPECTED_SETTINGS[2])
        for split, key in (("train", "input"), ("train", "output"),
                           ("test", "input"), ("test", "output")):
            for cell in (True, 1.0):
                episode = deepcopy(original)
                episode[split][0][key][0][0] = cell
                with self.subTest(split=split, key=key, cell=cell), tempfile.TemporaryDirectory() as temporary:
                    out = Path(temporary) / "invalid-grid"
                    with self.assertRaises((TypeError, ValueError)):
                        self.proto.write_batch([episode], out)
                    self.assertFalse(out.exists())

    def test_existing_destination_is_preserved_and_public_tampering_rejects(self):
        """Catch destructive output reuse and verification that ignores public bytes."""
        episode = self.proto.generate(64, EXPECTED_SETTINGS[0], queries=1)
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing"
            existing.mkdir()
            sentinel = existing / "keep.txt"
            sentinel.write_text("keep me", encoding="utf-8")
            with self.assertRaises((FileExistsError, ValueError)):
                self.proto.write_batch([episode], existing)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
            out = Path(temporary) / "batch"
            self.proto.write_batch([episode], out)
            public_path = next(path for path in (out / "public").rglob("*") if path.is_file())
            public_path.write_bytes(public_path.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                self.proto.verify_batch(out)

if __name__ == "__main__":
    unittest.main()
