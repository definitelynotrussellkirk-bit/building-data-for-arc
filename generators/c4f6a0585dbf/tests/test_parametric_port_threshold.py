"""Focused prototype tests; deliberately separate from production approval."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

TASK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "port_threshold", TASK / "workspace/parametric/port_threshold.py"
)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class ParameterContractTests(unittest.TestCase):
    def test_exact_numeric_types_and_bounds(self):
        for keyword, values in {
            "seed": [True, 1.0, "1", -1, 2**64],
            "n_train": [True, 1.0, "1", 0, -1, 17],
            "n_test": [True, 1.0, "1", 0, -1, 17],
            "max_attempts": [True, 1.0, "1", 0, -1, 4097],
            "min_visible_ports": [True, 2.0, "2", 0, 1, 4],
        }.items():
            for value in values:
                with self.subTest(keyword=keyword, value=value):
                    args = {"seed": 17, keyword: value}
                    with self.assertRaises(ValueError):
                        p.generate_episode(**args)

    def test_default_program_is_byte_exact_authority(self):
        canonical = p.canonical_program()
        self.assertEqual(p.materialize_program(2), canonical)
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),
                         p.CANONICAL_PROGRAM_SHA256)
        self.assertEqual(p.materialize_program(3), canonical.replace(
            "(>= (length placed4) 2)", "(>= (length placed4) 3)"))
        self.assertEqual(canonical.count("(>= (length placed4) 2)"), 1)
        for value in [True, 2.0, "2", 1, 4]:
            with self.assertRaises(ValueError):
                p.materialize_program(value)


class RacketBackedPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = p.RacketOracle()
        cls.episodes = [p.generate_episode(seed=17, min_visible_ports=value,
                         n_train=1, n_test=4, oracle=cls.oracle)
                        for value in (2, 3)]

    @classmethod
    def tearDownClass(cls):
        cls.oracle.close()

    def test_episode_reproducible_and_four_distinct_queries(self):
        for original in self.episodes:
            repeated = p.generate_episode(seed=17,
                min_visible_ports=original["parameters"]["min_visible_ports"],
                n_train=1, n_test=4, oracle=self.oracle)
            self.assertEqual(original, repeated)
            self.assertEqual(len(original["train"]), 1)
            self.assertEqual(len(original["test"]), 4)
            hashes = [p.grid_sha256(pair["input"])
                      for pair in original["train"] + original["test"]]
            self.assertEqual(len(hashes), len(set(hashes)))

    def test_independent_counts_and_seed_selected_setting(self):
        episode = p.generate_episode(seed=23, n_train=2, n_test=1,
                                     oracle=self.oracle)
        self.assertEqual(len(episode["train"]), 2)
        self.assertEqual(len(episode["test"]), 1)
        self.assertIn(episode["parameters"]["min_visible_ports"], (2, 3))
        self.assertEqual(episode, p.generate_episode(
            seed=23, n_train=2, n_test=1, oracle=self.oracle))

    def test_labels_execute_matching_racket_and_are_nonidentity(self):
        for episode in self.episodes:
            threshold = episode["parameters"]["min_visible_ports"]
            for pair in episode["train"] + episode["test"]:
                self.assertEqual(pair["output"],
                                 self.oracle.evaluate(pair["input"], threshold))
                self.assertEqual(pair["output"], p.simulate(pair["input"], threshold))
                self.assertNotEqual(pair["input"], pair["output"])
                self.assertEqual(p.selected_generator().self_check(pair["input"]), [])

    def test_threshold_witnesses_survive_all_four_queries(self):
        for episode in self.episodes:
            threshold = episode["parameters"]["min_visible_ports"]
            certificate = episode["certificate"]
            self.assertEqual(certificate["surviving_parameters"], [threshold])
            self.assertEqual(certificate["evidence_source"], "demonstrations_only")
            self.assertEqual(len(certificate["queries"]), 4)
            self.assertTrue(all(q["identified"] for q in certificate["queries"]))
            self.assertTrue(all(q["rival_disagreement_cells"] > 0
                                for q in certificate["queries"]))
            for witness in episode["sampling"]["accepted"]:
                self.assertEqual(len(witness["clipped_visible_ports"]), 2)
                self.assertEqual(len(witness["full_visible_ports"]), 3)
                self.assertGreater(witness["threshold_disagreement_cells"], 0)
                self.assertGreater(witness["full_stamp_changed_cells_at_3"], 0)

    def test_certificate_never_reads_query_answers(self):
        episode = copy.deepcopy(self.episodes[0])
        original = p.certify_episode(episode["train"], episode["test"], self.oracle)
        for pair in episode["test"]:
            pair["output"] = [[9]]
            pair["private_parameter"] = "wrong"
        self.assertEqual(original, p.certify_episode(
            episode["train"], episode["test"], self.oracle))

    def test_nonidentifying_demonstrations_are_reported(self):
        grid = [[1] * 18 for _ in range(18)]
        certificate = p.certify_episode(
            [{"input": grid, "output": grid}],
            self.episodes[0]["test"], self.oracle)
        self.assertEqual(certificate["surviving_parameters"], [2, 3])
        self.assertTrue(all(not q["identified"] for q in certificate["queries"]))

    def test_canonical_default_parity_on_supplied_pairs(self):
        pairs = p.canonical_pairs(p.TASK_ID, root=p.REPO_ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 10)
        for pair in pairs:
            with self.subTest(variant=pair["variant"], split=pair["split"],
                              pair=pair["pair_index"]):
                self.assertEqual(self.oracle.evaluate(pair["input"], 2), pair["output"])
                self.assertEqual(p.simulate(pair["input"], 2), pair["output"])

    def test_bounded_duplicate_retry_exhausts_without_partial_episode(self):
        pair = self.episodes[0]["train"][0]
        witness = self.episodes[0]["sampling"]["accepted"][0]
        with mock.patch.object(p, "_make_scene", return_value=(pair["input"], witness)) as draw:
            with self.assertRaises(p.SamplingExhausted) as failure:
                p.generate_episode(seed=91, n_train=1, n_test=4,
                                   max_attempts=3, oracle=self.oracle)
            self.assertEqual(draw.call_count, 3)
            self.assertIn("accepted 1 of 5", str(failure.exception))

    def test_writer_exact_projection_opaque_sorted_ids_and_private_programs(self):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            receipt = p.write_batch(list(reversed(self.episodes)), out)
            ids = sorted(public_challenge_id(ep) for ep in self.episodes)
            self.assertEqual(receipt["public_ids"], ids)
            self.assertEqual(sorted(x.name for x in (out / "public").iterdir()),
                             [item + ".json" for item in ids])
            for episode in self.episodes:
                identity = public_challenge_id(episode)
                data = (out / "public" / (identity + ".json")).read_bytes()
                self.assertEqual(data, public_challenge_bytes(episode))
                visible = json.loads(data)
                self.assertEqual(set(visible), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
                code = out / "private/programs" / (episode["program_sha256"] + ".rkt")
                self.assertEqual(code.read_text(), episode["program_solution"])
            private = [json.loads(line) for line in
                       (out / "private/episodes.jsonl").read_text().splitlines()]
            self.assertEqual([row["public_id"] for row in private], ids)
            self.assertTrue(all("parameters" in row and "output" in row["test"][0]
                                for row in private))
            with self.assertRaises(FileExistsError):
                p.write_batch(self.episodes, out)

    def test_writer_identity_ignores_hidden_data_and_rejects_duplicate_visible_payload(self):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        original = self.episodes[0]
        changed = copy.deepcopy(original)
        changed["seed"] = 999
        changed["parameters"] = {"min_visible_ports": 3}
        changed["program_solution"] = "private metadata mutation"
        for pair in changed["test"]:
            pair["output"] = [[9]]
        self.assertEqual(public_challenge_bytes(original), public_challenge_bytes(changed))
        self.assertEqual(public_challenge_id(original), public_challenge_id(changed))
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            with self.assertRaisesRegex(ValueError, "duplicate visible"):
                p.write_batch([original, changed], out)
            self.assertFalse(out.exists())


class CommandLineTests(unittest.TestCase):
    def test_cli_retains_racket_execution_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            result = subprocess.run([
                sys.executable, str(TASK / "workspace/parametric/port_threshold.py"),
                "--seed", "17", "--settings", "2", "3", "--train", "1", "--test", "1",
                "--out", str(out)], text=True, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((out / "private/export.json").read_text())
            self.assertEqual(receipt["racket_evaluations"], 4)
            self.assertEqual(receipt["runtime_identity"]["backend"], "racket")
            self.assertTrue(receipt["runtime_identity"]["protected"])
            self.assertEqual(len(receipt["pair_counts"]), 2)
            self.assertTrue(all(row["train"] == 1 and row["test"] == 1
                                for row in receipt["pair_counts"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
