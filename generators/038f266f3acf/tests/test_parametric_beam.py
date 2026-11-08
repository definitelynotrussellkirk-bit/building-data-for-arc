"""Proposed beam-width prototype checks; not production approval coverage."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TASK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("beam_width", TASK / "workspace/parametric/beam_width.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class ContractTests(unittest.TestCase):
    def test_exact_numeric_arguments_and_bounds(self):
        bad_values = {
            "seed": [True, 17.0, "17", -1, 2**64],
            "n_train": [True, 1.0, "1", 0, -1, 17],
            "n_test": [True, 1.0, "1", 0, -1, 17],
            "max_attempts": [True, 1.0, "1", 0, -1, 4097],
            "wing_multiplier": [True, 1.0, "1", 0, 3],
        }
        for name, values in bad_values.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        p.generate_episode(**dict({"seed": 17}, **{name: value}))

    def test_exact_canonical_program_and_only_wing_comparison_changes(self):
        canonical = p.canonical_program()
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), p.CANONICAL_PROGRAM_SHA256)
        self.assertEqual(p.materialize_program(1), canonical)
        self.assertEqual(p.materialize_program(2), canonical.replace(
            "(range 1 (+ half 1))", "(range 1 (+ (* 2 half) 1))"))
        for value in [True, 1.0, "1", 0, 3]:
            with self.assertRaises(ValueError):
                p.materialize_program(value)
        for value in [True, 4.0, "4", 0, 3, 5]:
            with self.assertRaises(ValueError):
                p.materialize_program(1, cap_depth=value)


class RacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = p.RacketOracle()
        cls.episodes = [p.generate_episode(seed=17, wing_multiplier=value,
                         n_train=1, n_test=4, oracle=cls.oracle) for value in (1, 2)]

    @classmethod
    def tearDownClass(cls):
        cls.oracle.close()

    def test_four_distinct_queries_reproducible_without_clones(self):
        for episode in self.episodes:
            self.assertEqual(len(episode["train"]), 1)
            self.assertEqual(len(episode["test"]), 4)
            identities = [p.grid_sha256(pair["input"]) for pair in episode["train"] + episode["test"]]
            self.assertEqual(len(identities), len(set(identities)))
            self.assertEqual(episode, p.generate_episode(seed=17,
                wing_multiplier=episode["parameters"]["wing_multiplier"],
                n_train=1, n_test=4, oracle=self.oracle))

    def test_independent_counts_and_seed_selected_parameter(self):
        episode = p.generate_episode(seed=23, n_train=2, n_test=1, oracle=self.oracle)
        self.assertEqual((len(episode["train"]), len(episode["test"])), (2, 1))
        self.assertIn(episode["parameters"]["wing_multiplier"], (1, 2))
        self.assertEqual(episode, p.generate_episode(seed=23, n_train=2, n_test=1, oracle=self.oracle))

    def test_actual_racket_labels_and_all_declared_models_match_mirror(self):
        for episode in self.episodes:
            chosen = "multiplier_" + str(episode["parameters"]["wing_multiplier"])
            for pair in episode["train"] + episode["test"]:
                self.assertEqual(p.selected_generator().self_check(pair["input"]), [])
                self.assertNotEqual(pair["input"], pair["output"])
                self.assertEqual(pair["output"], self.oracle.evaluate(pair["input"], chosen))
                for model, (multiplier, cap_depth) in p.MODELS.items():
                    self.assertEqual(self.oracle.evaluate(pair["input"], model),
                                     p.simulate(pair["input"], multiplier, cap_depth=cap_depth))

    def test_depth_five_six_and_clean_multiple_source_corridors(self):
        for episode in self.episodes:
            for witness in episode["sampling"]["accepted"]:
                self.assertEqual(sorted(witness["source_depths"]), [5, 6])
                self.assertTrue(witness["corridors_disjoint_at_multiplier_2"])
                self.assertTrue(witness["noncentral_marker"])
                self.assertEqual(witness["launch_axes"], ["horizontal", "vertical"])
                self.assertGreater(witness["parameter_disagreement_cells"], 0)
                self.assertTrue(all(count > 0 for count in witness["cap_four_disagreement_cells"].values()))

    def test_demo_certificate_rejects_both_parameter_and_cap_four_rivals(self):
        for episode in self.episodes:
            value = episode["parameters"]["wing_multiplier"]
            certificate = episode["certificate"]
            self.assertEqual(certificate["evidence_source"], "demonstrations_only")
            self.assertEqual(certificate["surviving_models"], ["multiplier_" + str(value)])
            self.assertEqual(certificate["surviving_parameters"], [value])
            self.assertEqual(certificate["surviving_cap_rivals"], [])
            self.assertEqual(len(certificate["queries"]), 4)
            self.assertTrue(all(row["identified"] for row in certificate["queries"]))
            self.assertTrue(all(row["cap_four_disagreement_cells"][str(value)] > 0
                                for row in certificate["queries"]))

    def test_query_answers_are_not_certificate_evidence(self):
        episode = copy.deepcopy(self.episodes[0])
        original = p.certify_episode(episode["train"], episode["test"], self.oracle)
        for pair in episode["test"]:
            pair["output"] = [[9]]
            pair["parameters"] = {"wing_multiplier": 2}
        self.assertEqual(original, p.certify_episode(episode["train"], episode["test"], self.oracle))

    def test_shallow_demo_leaves_cap_rival_for_deep_query(self):
        grid = p.selected_generator().generate(17, 0, difficulty="easy")
        actual = self.oracle.evaluate(grid, "multiplier_1")
        self.assertEqual(actual, self.oracle.evaluate(grid, "multiplier_1_cap_depth_4"))
        certificate = p.certify_episode([{"input": grid, "output": actual}],
                                       self.episodes[0]["test"], self.oracle)
        self.assertIn("multiplier_1_cap_depth_4", certificate["surviving_models"])
        self.assertTrue(all(not query["identified"] for query in certificate["queries"]))

    def test_canonical_default_reproduces_all_supplied_labeled_pairs(self):
        pairs = p.canonical_pairs(p.TASK_ID, root=p.REPO_ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 10)
        for pair in pairs:
            with self.subTest(variant=pair["variant"], split=pair["split"], index=pair["pair_index"]):
                self.assertEqual(self.oracle.evaluate(pair["input"], "multiplier_1"), pair["output"])
                self.assertEqual(p.simulate(pair["input"], 1), pair["output"])

    def test_retry_schedule_is_bounded_and_never_returns_partial_episode(self):
        grid = self.episodes[0]["train"][0]["input"]
        with mock.patch.object(p, "_make_scene", return_value=grid) as draw:
            with self.assertRaisesRegex(p.SamplingExhausted, "accepted 1 of 5"):
                p.generate_episode(seed=91, n_train=1, n_test=4, max_attempts=3, oracle=self.oracle)
            self.assertEqual(draw.call_count, 3)

    def test_public_writer_exact_bytes_sorted_ids_and_four_private_programs(self):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            receipt = p.write_batch(list(reversed(self.episodes)), out)
            identities = sorted(public_challenge_id(ep) for ep in self.episodes)
            self.assertEqual(receipt["public_ids"], identities)
            self.assertEqual(sorted(path.name for path in (out / "public").iterdir()),
                             [identity + ".json" for identity in identities])
            for episode in self.episodes:
                data = (out / "public" / (public_challenge_id(episode) + ".json")).read_bytes()
                self.assertEqual(data, public_challenge_bytes(episode))
                payload = json.loads(data)
                self.assertEqual(set(payload), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input"} for pair in payload["test"]))
                for record in episode["executed_programs"].values():
                    path = out / "private/programs" / (record["sha256"] + ".rkt")
                    self.assertEqual(path.read_text(), record["program_solution"])
            self.assertEqual(len(list((out / "private/programs").iterdir())), 4)
            rows = [json.loads(line) for line in (out / "private/episodes.jsonl").read_text().splitlines()]
            self.assertEqual([row["public_id"] for row in rows], identities)
            with self.assertRaises(FileExistsError):
                p.write_batch(self.episodes, out)

    def test_public_identity_ignores_private_changes_and_rejects_duplicate_payload(self):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        original = self.episodes[0]
        changed = copy.deepcopy(original)
        changed["seed"] = 999
        changed["parameters"] = {"wing_multiplier": 2}
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
    def test_real_cli_writes_execution_identity_and_complete_export(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            result = subprocess.run([
                sys.executable, str(TASK / "workspace/parametric/beam_width.py"),
                "--seed", "17", "--settings", "1", "2", "--train", "1", "--test", "1",
                "--out", str(out)], capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((out / "private/export.json").read_text())
            self.assertEqual(receipt["racket_evaluations"], 8)
            self.assertEqual(receipt["runtime_identity"]["backend"], "racket")
            self.assertTrue(receipt["runtime_identity"]["protected"])
            self.assertEqual(len(receipt["pair_counts"]), 2)
            self.assertTrue(all(row["train"] == 1 and row["test"] == 1 for row in receipt["pair_counts"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
