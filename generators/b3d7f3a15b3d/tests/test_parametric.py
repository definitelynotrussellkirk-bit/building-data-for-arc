"""Task-local prototype tests; canonical API and approval remain separate."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/prototype.py"

def scene(markers):
    g = [[0] * 26 for _ in range(26)]
    for i in range(5):
        for j in range(5):
            for dr in range(4):
                for dc in range(4):
                    g[1+5*i+dr][1+5*j+dc] = 8 if dr in (0,3) or dc in (0,3) else 1
    for i, j, dr, dc, color in markers:
        g[1+5*i+dr][1+5*j+dc] = color
    return g



class ParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.is_file():
            return
        spec = importlib.util.spec_from_file_location("framed_parametric", SOURCE)
        cls.proto = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.proto)
        cls.verifier = cls.proto.open_verifier()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "verifier"):
            cls.verifier.close()

    def test_00_prototype_source_is_available(self):
        self.assertTrue(SOURCE.is_file(), "requested parametric prototype is missing")

    def test_hand_derived_direction_threshold(self):
        markers = [(0,0,1,1,2), (0,4,1,1,2),
                   (0,2,2,2,3), (1,2,2,2,3), (4,2,2,2,3)]
        for direction, threshold in self.proto.SETTINGS:
            with self.subTest(direction=direction, threshold=threshold):
                source = scene(markers)
                expected = deepcopy(source)
                if threshold == 2 and direction != "vertical":
                    for j in (1,2,3):
                        expected[2][2+5*j] = 2
                if direction != "horizontal":
                    for i in (2,3):
                        expected[3+5*i][13] = 3
                self.assertEqual(self.verifier.apply(self.proto.emit_rule(direction, threshold), source), expected)
                self.assertEqual(self.proto.apply_python(source, direction, threshold), expected)
                self.assertEqual(source, scene(markers))

    def test_no_cascading_and_offsets_independent(self):
        markers = [(0,0,1,1,2), (0,4,1,1,2), (4,2,1,1,2),
                   (2,0,1,2,3), (2,4,2,1,3)]
        source = scene(markers)
        expected = deepcopy(source)
        for j in (1,2,3):
            expected[2][2+5*j] = 2
        self.assertEqual(self.verifier.apply(self.proto.emit_rule(), source), expected)
        self.assertEqual(self.proto.apply_python(source), expected)

    def test_default_canonical_parity(self):
        from reviewer_support import canonical_pairs
        pairs = canonical_pairs(self.proto.TASK_ID, root=self.proto.ROOT)
        self.assertTrue(pairs)
        for pair in pairs:
            actual = self.verifier.apply(self.proto.emit_rule(), pair["input"])
            self.assertEqual(actual, pair["output"])
            self.assertEqual(self.proto.apply_python(pair["input"]), actual)

    def test_invalid_settings_and_counts_fail(self):
        for settings in [("diagonal",2), ("both",1), ("both",True), (None,2)]:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.proto.emit_rule(*settings)
        for counts in [(2,4), (3,0), (True,4), (3,1.5), (129,4)]:
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                self.proto.generate_episode(7, n_train=counts[0], n_test=counts[1])

    def test_all_settings_episodes_public_separation_and_demo_identification(self):
        for direction, threshold in self.proto.SETTINGS:
            with self.subTest(direction=direction, threshold=threshold):
                episode = self.proto.generate_episode(7321, direction=direction, min_anchors=threshold,
                                                     n_train=3, n_test=4, verifier=self.verifier)
                public, private = episode["public"], episode["private"]
                self.assertEqual(set(public), {"train", "test"})
                self.assertEqual(len(public["train"]), 3)
                self.assertEqual(len(public["test"]), 4)
                self.assertTrue(all(set(p) == {"input"} for p in public["test"]))
                params = {"direction": direction, "min_anchors": threshold}
                self.assertEqual(private["parameters"], params)
                inputs = [p["input"] for split in ("train", "test") for p in public[split]]
                self.assertEqual(len({self.proto.grid_key(g) for g in inputs}), 7)
                self.assertEqual(self.proto.identify_from_demos(public["train"], self.verifier), [params])
                for query, expected in zip(public["test"], private["query_outputs"]):
                    self.assertEqual(self.verifier.apply(self.proto.emit_rule(direction, threshold), query["input"]), expected)

    def test_reproducible_seed_selection_and_separate_counts(self):
        first = self.proto.generate_episode(22, n_train=3, n_test=4, verifier=self.verifier)
        self.assertEqual(first, self.proto.generate_episode(22, n_train=3, n_test=4, verifier=self.verifier))
        changed = self.proto.generate_episode(22, n_train=4, n_test=2, verifier=self.verifier)
        self.assertEqual(changed["private"]["parameters"], first["private"]["parameters"])
        self.assertEqual(len(changed["public"]["train"]), 4)
        self.assertEqual(len(changed["public"]["test"]), 2)

    def test_public_writer_hashes_exact_visible_bytes_and_ignores_private_fields(self):
        episode = {
            "public": {
                "train": [{"input": [[1, 0]], "output": [[0, 1]]}],
                "test": [{"input": [[2, 0]]}],
            },
            "private": {
                "seed": 17,
                "parameters": {"direction": "horizontal", "min_anchors": 2},
                "rule": "(lambda (g) g)",
                "rule_sha256": "private-rule-hash",
                "query_outputs": [[[0, 2]]],
            },
        }
        visible = b'{"test":[{"input":[[2,0]]}],"train":[{"input":[[1,0]],"output":[[0,1]]}]}\n'
        public_id = hashlib.sha256(visible).hexdigest()

        changed_private = deepcopy(episode)
        changed_private["private"].update(
            seed=999,
            parameters={"direction": "vertical", "min_anchors": 3},
            rule="(lambda (g) (reverse g))",
            query_outputs=[[[9, 9]]],
        )

        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first_rows = self.proto.write_episode_batch(Path(first_tmp), [episode])
            second_rows = self.proto.write_episode_batch(Path(second_tmp), [changed_private])

            expected_path = f"public/{public_id}.json"
            self.assertEqual(first_rows[0]["public_id"], public_id)
            self.assertEqual(second_rows[0]["public_id"], public_id)
            self.assertEqual(first_rows[0]["public_path"], expected_path)
            self.assertEqual(second_rows[0]["public_path"], expected_path)
            self.assertEqual((Path(first_tmp) / expected_path).read_bytes(), visible)
            self.assertEqual((Path(second_tmp) / expected_path).read_bytes(), visible)

    def test_racket_backed_public_writer_sorts_separates_and_rejects_duplicates(self):
        episodes = [
            self.proto.generate_episode(81, direction="horizontal", min_anchors=2,
                                        n_train=3, n_test=4, verifier=self.verifier),
            self.proto.generate_episode(82, direction="vertical", min_anchors=3,
                                        n_train=3, n_test=4, verifier=self.verifier),
        ]
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first_rows = self.proto.write_episode_batch(Path(first_tmp), episodes)
            second_rows = self.proto.write_episode_batch(Path(second_tmp), list(reversed(episodes)))

            first_ids = [row["public_id"] for row in first_rows]
            self.assertEqual(first_ids, sorted(first_ids))
            self.assertEqual(first_ids, [row["public_id"] for row in second_rows])
            self.assertEqual(
                sorted(path.name for path in (Path(first_tmp) / "public").iterdir()),
                [f"{public_id}.json" for public_id in first_ids],
            )
            for row in first_rows:
                public_path = Path(first_tmp) / row["public_path"]
                private_path = Path(first_tmp) / row["private_path"]
                rule_path = Path(first_tmp) / row["rule_path"]
                self.assertTrue(public_path.is_file())
                self.assertTrue(private_path.is_file())
                self.assertTrue(rule_path.is_file())
                self.assertNotIn("private", public_path.parts)
                self.assertNotIn("public", private_path.parts)
                self.assertNotIn("query_outputs", public_path.read_text())

        with tempfile.TemporaryDirectory() as duplicate_tmp:
            duplicate_root = Path(duplicate_tmp) / "batch"
            with self.assertRaisesRegex(ValueError, "duplicate public payload"):
                self.proto.write_episode_batch(duplicate_root, [episodes[0], deepcopy(episodes[0])])
            self.assertFalse(duplicate_root.exists())

    def test_public_writer_prevalidates_private_serialization_before_any_writes(self):
        valid = self.proto.generate_episode(91, direction="both", min_anchors=2,
                                            n_train=3, n_test=4, verifier=self.verifier)
        invalid = deepcopy(valid)
        invalid["public"]["test"][0]["input"][0][0] = 9
        invalid["private"]["non_json_value"] = {"not", "serializable"}

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch"
            with self.assertRaises(TypeError):
                self.proto.write_episode_batch(out, [valid, invalid])
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
