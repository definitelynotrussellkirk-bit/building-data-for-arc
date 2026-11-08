"""Executable export, lesson-identifiability and boundary regressions."""
import copy
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TASK = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK / "workspace/parametric"
REPO = TASK.parents[1]
sys.path[:0] = [str(PARAMETRIC), str(REPO / "shared/runtime")]


class EpisodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = None
        if (PARAMETRIC / "episodes.py").is_file():
            from arc_repl.racket_bridge import RacketBridge
            cls.bridge = RacketBridge(timeout=20)

    @classmethod
    def tearDownClass(cls):
        if cls.bridge is not None:
            cls.bridge.close()

    def setUp(self):
        self.assertTrue((PARAMETRIC / "episodes.py").is_file(), "episode engine is not implemented")
        self.e = importlib.import_module("episodes")
        self.s = importlib.import_module("strip_stack")

    def make_episode(self, **kwargs):
        return self.e.build_episode("strip", "top_to_bottom", 41, bridge=self.bridge, **kwargs)

    def test_focus_standalone_program_uses_shared_rule_normalizer(self):
        focus = importlib.import_module("focus_reconstruction")
        for setting in focus.SETTINGS:
            with self.subTest(setting=setting):
                self.assertTrue(focus.render_program(setting).startswith("(lambda (g)"))
                episode = self.e.build_episode("focus", setting, 41,
                                               n_demo=1, n_query=4, bridge=self.bridge)
                self.assertTrue(self.e.verify_episode(episode, self.bridge))
                self.assertEqual(episode["certificate"]["survivors"], [setting])
                self.assertEqual(len(episode["challenge"]["test"]), 4)

    def test_four_queries_and_independent_counts(self):
        episode = self.make_episode(n_demo=1, n_query=4)
        self.assertEqual(len(episode["challenge"]["train"]), 1)
        self.assertEqual(len(episode["challenge"]["test"]), 4)
        grids = [p["input"] for p in episode["challenge"]["train"] + episode["challenge"]["test"]]
        self.assertEqual(len({json.dumps(g) for g in grids}), 5)
        self.assertTrue(self.e.verify_episode(episode, self.bridge))
        self.assertEqual(episode["certificate"]["survivors"], ["top_to_bottom"])

    def test_fixed_settings_share_inputs_but_change_answers(self):
        a = self.make_episode(n_demo=2, n_query=4)
        b = self.e.build_episode("strip", "bottom_to_top", 41, n_demo=2, n_query=4, bridge=self.bridge)
        for split in ("train", "test"):
            self.assertEqual([p["input"] for p in a["challenge"][split]],
                             [p["input"] for p in b["challenge"][split]])
        self.assertNotEqual(a["challenge"]["train"][0]["output"], b["challenge"]["train"][0]["output"])

    def test_query_changing_surviving_rival_rejects_lesson(self):
        demo, query = self.s.sample_input(17, 3), self.s.sample_input(19, 0)
        lesson = {"train": [{"input": demo, "output": self.s.python_expected(demo)}],
                  "test": [{"input": query}]}
        with self.assertRaisesRegex(ValueError, "underidentified"):
            self.e.certify(lesson, "strip", self.bridge)

    def test_surviving_rival_that_agrees_on_queries_is_accepted(self):
        demo, query = self.s.sample_input(17, 3), self.s.sample_input(19, 7)
        lesson = {"train": [{"input": demo, "output": self.s.python_expected(demo)}],
                  "test": [{"input": query}]}
        certificate = self.e.certify(lesson, "strip", self.bridge)
        self.assertEqual(certificate["survivors"], list(self.s.SETTINGS))

    def test_query_answers_and_private_metadata_cannot_change_public_identity(self):
        from reviewer_support import public_challenge_id, public_challenge_bytes
        episode = self.make_episode(n_demo=1, n_query=2)
        challenge = copy.deepcopy(episode["challenge"])
        before = self.e.certify(challenge, "strip", self.bridge)
        challenge["test"][0]["output"] = [[True]]
        challenge["hidden_seed"] = "do not publish"
        self.assertEqual(before, self.e.certify(challenge, "strip", self.bridge))
        self.assertEqual(public_challenge_id(episode["challenge"]), public_challenge_id(challenge))
        self.assertNotIn(b"hidden_seed", public_challenge_bytes(challenge))

    def test_bad_demo_labels_and_bool_visible_cells_are_rejected(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        broken = copy.deepcopy(episode["challenge"])
        broken["train"][0]["output"][0][0] = 8
        with self.assertRaisesRegex(ValueError, "no declared"):
            self.e.certify(broken, "strip", self.bridge)
        broken = copy.deepcopy(episode["challenge"])
        broken["test"][0]["input"][0][0] = True
        with self.assertRaises(ValueError):
            self.e.certify(broken, "strip", self.bridge)

    def test_private_label_and_certificate_tampering_rejected(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        for field in ("answer", "certificate", "program"):
            with self.subTest(field=field):
                bad = copy.deepcopy(episode)
                if field == "answer":
                    bad["challenge"]["test"][0]["output"][0][0] = 8
                elif field == "certificate":
                    bad["certificate"]["survivors"] = []
                else:
                    bad["program"] = "(lambda (g) g)"
                with self.assertRaises(ValueError):
                    self.e.verify_episode(bad, self.bridge)

    def test_bad_counts_rejected_before_sampling(self):
        for changes in ({"n_demo": 0}, {"n_query": 0}, {"n_demo": True},
                        {"n_query": 9}, {"n_query": 1.5}, {"max_attempts": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.make_episode(**changes)

    def test_duplicate_sampler_exhausts_with_explicit_failure(self):
        grid = self.s.sample_input(41, 0)
        with patch.object(self.s, "sample_input", return_value=grid):
            with self.assertRaisesRegex(ValueError, "distinct"):
                self.make_episode(n_demo=1, n_query=1, max_attempts=3)

    def test_public_writer_hashes_exact_bytes_and_sorts_ids(self):
        from reviewer_support import public_challenge_id
        first = self.make_episode(n_demo=1, n_query=1)
        second = self.e.build_episode("strip", "bottom_to_top", 41, n_demo=1, n_query=1, bridge=self.bridge)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "batch"
            result = self.e.write_batch([second, first], out, self.bridge)
            ids = sorted([public_challenge_id(x["challenge"]) for x in (first, second)])
            self.assertEqual(result["public_ids"], ids)
            self.assertEqual(sorted(p.name for p in (out / "public").iterdir()), [i + ".json" for i in ids])
            for path in (out / "public").iterdir():
                import hashlib
                self.assertEqual(path.stem, hashlib.sha256(path.read_bytes()).hexdigest())
                data = json.loads(path.read_bytes())
                self.assertEqual(set(data), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input"} for pair in data["test"]))
            private = json.loads((out / "private/episodes.json").read_text())
            self.assertEqual([x["public_id"] for x in private], ids)

    def test_malformed_private_sampling_metadata_is_rejected(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        for field, value in (("seed", True), ("input_seed", "not-an-integer"),
                             ("attempts", -1), ("attempts", True), ("attempts", 4097)):
            bad = copy.deepcopy(episode)
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.e.verify_episode(bad, self.bridge)

    def test_boolean_certificate_count_is_not_an_integer(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        episode["certificate"]["query_count"] = True
        with self.assertRaises(ValueError):
            self.e.verify_episode(episode, self.bridge)

    def test_missing_or_forged_batch_report_is_rejected(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "batch"
            self.e.write_batch([episode], out, self.bridge)
            report_path = out / "private/verification.json"
            report = json.loads(report_path.read_text())
            for field, value in (("status", "approved"), ("training_admitted", True),
                                 ("episode_count", 999), ("label_count", 999),
                                 ("public_ids", []), ("episode_count", True)):
                bad = copy.deepcopy(report)
                bad[field] = value
                report_path.write_text(json.dumps(bad))
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.e.verify_batch(out, self.bridge)
            bad = copy.deepcopy(report)
            bad["runtime_identity"]["binary_sha256"] = "0" * 64
            report_path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                self.e.verify_batch(out, self.bridge)
            report_path.unlink()
            with self.assertRaises(ValueError):
                self.e.verify_batch(out, self.bridge)

    def test_duplicate_export_fails_without_partial_directory(self):
        episode = self.make_episode(n_demo=1, n_query=1)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "batch"
            with self.assertRaisesRegex(ValueError, "duplicate"):
                self.e.write_batch([episode, copy.deepcopy(episode)], out, self.bridge)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
