"""Focused contract tests for the proposed direction variant, not production approval."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "generators/cd818a9d92d1/workspace/parametric/prototype.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))
from reviewer_support import public_challenge_bytes, public_challenge_id


class ParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert SOURCE.is_file(), "The requested runnable prototype is not implemented yet"
        spec = importlib.util.spec_from_file_location("direction_prototype_under_test", SOURCE)
        cls.p = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.p
        spec.loader.exec_module(cls.p)
        context = cls.p.RacketOracle()
        cls.oracle = context.__enter__()
        cls.addClassCleanup(context.__exit__, None, None, None)
        cls.episodes = {}
        cls.canonicals = [
            json.loads(line)
            for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if json.loads(line).get("task_id") == "cd818a9d92d1"
        ]

    def episode(self, direction="right"):
        if direction not in self.episodes:
            self.episodes[direction] = self.p.make_episode(
                919, direction, demos=2, queries=4, input_seed=42, oracle=self.oracle
            )
        return copy.deepcopy(self.episodes[direction])

    def test_canonical_program_and_all_retained_labels(self):
        self.assertEqual(self.p.program(), self.canonicals[0]["program_solution"])
        for row in self.canonicals:
            self.assertEqual(self.p.program("right"), row["program_solution"])
            for pair in row["train"] + row["test"]:
                actual = self.oracle.predict(pair["input"], self.p.program("right"))
                self.assertEqual(actual, pair["output"])

    def test_hand_checked_bend_and_distractor_in_both_directions(self):
        grid = [[0] * 8 for _ in range(7)]
        grid[-1][1] = grid[-1][4] = 2
        grid[3][1], grid[1][6] = 5, 5
        for direction, destination in (("left", 0), ("right", 2)):
            with self.subTest(direction=direction):
                out = self.oracle.predict(grid, self.p.program(direction))
                self.assertEqual(out, self.p.predict_python(grid, direction))
                self.assertEqual([row[1] for row in out], [0, 0, 0, 5, 2, 2, 2])
                self.assertEqual([row[destination] for row in out], [2, 2, 2, 2, 2, 0, 0])
                self.assertEqual([row[4] for row in out], [2] * 7)
                self.assertEqual(out[1][6], 5)
                self.assertEqual([row[7] for row in out], [0] * 7)

    def test_common_support_rejects_edge_and_gray_overlap(self):
        edge = [[0] * 6 for _ in range(5)]
        edge[-1][0] = edge[-1][3] = 2
        edge[1][0], edge[2][5] = 5, 5
        overlap = [[0] * 7 for _ in range(5)]
        overlap[-1][1] = overlap[-1][4] = 2
        overlap[2][4], overlap[1][3] = 5, 5
        for grid in (edge, overlap):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.p.validate_input(grid)
        valid = self.p.sample_inputs(42, 1)[0]
        self.p.validate_input(valid)
        for cell in (True, 2.0, -1, 10):
            damaged = copy.deepcopy(valid)
            damaged[0][0] = cell
            with self.subTest(cell=cell), self.assertRaises(ValueError):
                self.p.validate_input(damaged)

    def test_sampler_exact_support_bound_and_replay(self):
        overrides = dict(grid_h=5, grid_w=6,
                         branch_profile="compact_one_bend_one_distractor")
        actual = self.p.sample_inputs(83, 4, input_overrides=overrides)
        self.assertEqual(len(actual), 4)
        self.assertEqual(len({json.dumps(grid) for grid in actual}), 4)
        self.assertEqual(actual, self.p.sample_inputs(83, 4, input_overrides=overrides))
        with self.assertRaises(ValueError):
            self.p.sample_inputs(83, 5, input_overrides=overrides, max_attempts=16)
        with self.assertRaises(ValueError):
            self.p.sample_inputs(83, 2, max_attempts=1)

    def test_counts_and_directions_are_strict(self):
        for value in (True, 2.0, 0, -1):
            with self.subTest(count=value), self.assertRaises(ValueError):
                self.p.sample_inputs(17, value)
            for field in ("demos", "queries", "max_attempts"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.p.make_episode(17, oracle=self.oracle, **{field: value})
        for value in ("up", "", 1, True):
            with self.subTest(direction=value), self.assertRaises(ValueError):
                self.p.program(value)

    def test_paired_episodes_have_six_distinct_inputs_and_racket_labels(self):
        right, left = self.episode(), self.episode("left")
        for direction, episode in (("right", right), ("left", left)):
            self.assertEqual(episode["settings"]["bend_direction"], direction)
            self.assertEqual(len(episode["train"]), 2)
            self.assertEqual(len(episode["test"]), 4)
            pairs = episode["train"] + episode["test"]
            self.assertEqual(len({json.dumps(pair["input"]) for pair in pairs}), 6)
            for pair in pairs:
                self.assertEqual(pair["output"],
                                 self.oracle.predict(pair["input"], episode["program_solution"]))
                self.assertEqual(pair["output"], self.p.predict_python(pair["input"], direction))
            self.assertIsInstance(self.p.certify_episode(episode, oracle=self.oracle), dict)
        self.assertEqual([p["input"] for p in right["train"] + right["test"]],
                         [p["input"] for p in left["train"] + left["test"]])
        self.assertNotEqual(right["train"][0]["output"], left["train"][0]["output"])

    def test_certifier_recomputes_and_rejects_tampering(self):
        valid = self.episode()
        fake_certificate = {"trusted_without_execution": True}
        valid["certificate"] = fake_certificate
        self.assertNotEqual(self.p.certify_episode(valid, oracle=self.oracle), fake_certificate)
        for field in ("train", "test"):
            forged = self.episode()
            forged[field][0]["output"][0][0] = (forged[field][0]["output"][0][0] + 1) % 10
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.p.certify_episode(forged, oracle=self.oracle)
        for field, value in (("program_solution", self.p.program("left")),
                             ("settings", {"bend_direction": "left"})):
            forged = self.episode()
            forged[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.p.certify_episode(forged, oracle=self.oracle)
        duplicate = self.episode()
        duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
        with self.assertRaises(ValueError):
            self.p.certify_episode(duplicate, oracle=self.oracle)

    def test_public_identity_ignores_private_data_and_query_answers(self):
        episode = self.episode()
        changed = copy.deepcopy(episode)
        changed["seed"], changed["input_seed"] = 99999, -333
        changed["private_note"] = "SECRET_PRIVATE_SENTINEL"
        changed["settings"] = {"bend_direction": "left"}
        changed["program_solution"] = "SECRET_PROGRAM_SENTINEL"
        changed["test"][0]["output"][0][0] = 9
        self.assertEqual(public_challenge_bytes(episode), public_challenge_bytes(changed))
        self.assertEqual(public_challenge_id(episode), public_challenge_id(changed))
        visible = json.loads(public_challenge_bytes(episode))
        self.assertEqual(set(visible), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))

    def test_writer_exports_visible_bytes_and_prevalidates_failures(self):
        right, left = self.episode(), self.episode("left")
        with tempfile.TemporaryDirectory(dir=REPO.parent / "checks") as temporary:
            base = Path(temporary)
            output = base / "good"
            self.p.write_batch([right, left], output, oracle=self.oracle)
            public_files = []
            for path in output.rglob("*.json"):
                payload = json.loads(path.read_bytes())
                if isinstance(payload, dict) and set(payload) == {"train", "test"}:
                    public_files.append(path)
                    self.assertEqual(path.stem, hashlib.sha256(path.read_bytes()).hexdigest())
                    self.assertTrue(all(set(pair) == {"input"} for pair in payload["test"]))
            self.assertEqual(len(public_files), 2)
            self.assertEqual({p.read_bytes() for p in public_files},
                             {public_challenge_bytes(right), public_challenge_bytes(left)})
            with self.assertRaises((ValueError, FileExistsError)):
                self.p.write_batch([right], output, oracle=self.oracle)
            same_visible = copy.deepcopy(right)
            same_visible["seed"] = 123456
            duplicate_target = base / "duplicate"
            with self.assertRaises(ValueError):
                self.p.write_batch([right, same_visible], duplicate_target, oracle=self.oracle)
            self.assertFalse(duplicate_target.exists())
            invalid = copy.deepcopy(left)
            invalid["test"][0]["output"][0][0] = (invalid["test"][0]["output"][0][0] + 1) % 10
            invalid_target = base / "invalid"
            with self.assertRaises(ValueError):
                self.p.write_batch([right, invalid], invalid_target, oracle=self.oracle)
            self.assertFalse(invalid_target.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
