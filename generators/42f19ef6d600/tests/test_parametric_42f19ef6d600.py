"""Focused tests for the proposed task-local parametric rule prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "42f19ef6d600"
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load prototype at {PROTOTYPE_PATH}")
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def _grid(*rows: str) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in rows]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _input_key(pair: dict) -> str:
    return json.dumps(pair["input"], separators=(",", ":"))


SOLID = _grid(
    "7777777",
    "7777777",
    "7733377",
    "7733377",
    "7733377",
    "7777777",
    "7777777",
)
HOLLOW = _grid(
    "7777777",
    "7777777",
    "7733377",
    "7737377",
    "7733377",
    "7777777",
    "7777777",
)
SIDE_STRIPS_SOLID = _grid(
    "7777777",
    "7722277",
    "7233327",
    "7233327",
    "7233327",
    "7722277",
    "7777777",
)
CORNER_MARKS_SOLID = _grid(
    "7777777",
    "7727277",
    "7233327",
    "7733377",
    "7233327",
    "7727277",
    "7777777",
)
SIDE_STRIPS_HOLLOW = _grid(
    "7777777",
    "7722277",
    "7233327",
    "7237327",
    "7233327",
    "7722277",
    "7777777",
)
CORNER_MARKS_HOLLOW = _grid(
    "7777777",
    "7727277",
    "7233327",
    "7737377",
    "7233327",
    "7727277",
    "7777777",
)


class ParametricRuleUnitTests(unittest.TestCase):
    def test_branch_map_changes_hand_checked_solid_and_hollow_outputs(self):
        self.assertEqual(PROTOTYPE.python_apply(SOLID, "canonical"), SIDE_STRIPS_SOLID)
        self.assertEqual(PROTOTYPE.python_apply(SOLID, "swapped"), CORNER_MARKS_SOLID)
        self.assertEqual(PROTOTYPE.python_apply(HOLLOW, "canonical"), CORNER_MARKS_HOLLOW)
        self.assertEqual(PROTOTYPE.python_apply(HOLLOW, "swapped"), SIDE_STRIPS_HOLLOW)

    def test_canonical_program_retains_authority_pin_and_swapped_program_differs(self):
        canonical = PROTOTYPE.racket_program("canonical")
        swapped = PROTOTYPE.racket_program("swapped")
        self.assertEqual(_normalized_hash(canonical), "07ef8e3cc031")
        self.assertNotEqual(" ".join(canonical.split()), " ".join(swapped.split()))
        self.assertNotEqual(_normalized_hash(swapped), "07ef8e3cc031")

    def test_invalid_setting_or_counts_fail_before_sampling(self):
        invalid = (
            {"branch_map": "unknown", "demo_count": 4, "query_count": 4},
            {"branch_map": "canonical", "demo_count": 1, "query_count": 4},
            {"branch_map": "canonical", "demo_count": 5, "query_count": 4},
            {"branch_map": "canonical", "demo_count": 4, "query_count": 3},
            {"branch_map": "canonical", "demo_count": 4, "query_count": 9},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PROTOTYPE.build_episode(seed=17, **kwargs)


class ParametricEpisodeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = PROTOTYPE.build_episode(
            seed=1701, branch_map="canonical", demo_count=4, query_count=4
        )
        cls.swapped = PROTOTYPE.build_episode(
            seed=1701, branch_map="swapped", demo_count=4, query_count=4
        )

    def test_episode_fixes_one_setting_and_has_four_distinct_racket_backed_queries(self):
        for episode, setting in ((self.canonical, "canonical"), (self.swapped, "swapped")):
            with self.subTest(setting=setting):
                self.assertEqual(episode["parameter"]["value"], setting)
                self.assertEqual(episode["parameter"]["canonical_default"], "canonical")
                self.assertEqual((episode["demo_count"], episode["query_count"]), (4, 4))
                pairs = episode["train"] + episode["test"]
                self.assertEqual(len({_input_key(pair) for pair in pairs}), 8)
                self.assertEqual(episode["verification"]["racket_pairs"], 8)
                self.assertEqual(episode["verification"]["python_parity_pairs"], 8)
                self.assertTrue(episode["verification"]["all_inputs_distinct"])
                for rival in ("always_side_strips", "always_corner_marks"):
                    self.assertTrue(
                        episode["verification"]["rivals"][rival]["rejected_by_demo_indices"],
                        rival,
                    )
        # Exercise the full verifier once; both settings were already independently
        # labeled by protected Racket in setUpClass. Avoid redundant child-runtime
        # churn here because that obscures failures in the behavior under test.
        self.assertTrue(PROTOTYPE.verify_episode(self.canonical)["ok"])

    def test_same_seed_uses_same_inputs_but_setting_changes_outputs(self):
        canonical_pairs = self.canonical["train"] + self.canonical["test"]
        swapped_pairs = self.swapped["train"] + self.swapped["test"]
        self.assertEqual(
            [pair["input"] for pair in canonical_pairs],
            [pair["input"] for pair in swapped_pairs],
        )
        self.assertTrue(
            all(left["output"] != right["output"] for left, right in zip(canonical_pairs, swapped_pairs))
        )

    def test_minimum_demos_and_maximum_queries_remain_identifiable(self):
        train, test, _generator_sha256 = PROTOTYPE._sample_inputs(
            seed=1701, demo_count=2, query_count=8
        )
        self.assertEqual([pair["profile"] for pair in train], ["solid_square", "hollow_square"])
        self.assertEqual([pair["profile"] for pair in test], list(PROTOTYPE.QUERY_PROFILES))
        self.assertEqual(len({_input_key(pair) for pair in train + test}), 10)

        for branch_map in ("canonical", "swapped"):
            labeled_train = copy.deepcopy(train)
            labeled_test = copy.deepcopy(test)
            for pair in labeled_train + labeled_test:
                pair["output"] = PROTOTYPE.python_apply(pair["input"], branch_map)
            summary = PROTOTYPE._verification_summary(labeled_train, labeled_test)
            self.assertTrue(summary["all_inputs_distinct"])
            self.assertTrue(
                all(
                    receipt["rejected_by_demo_indices"]
                    for receipt in summary["rivals"].values()
                )
            )

        self.assertTrue(
            all(
                PROTOTYPE.python_apply(pair["input"], "canonical")
                != PROTOTYPE.python_apply(pair["input"], "swapped")
                for pair in test
            )
        )

    def test_public_projection_hides_private_rule_and_query_labels(self):
        public = PROTOTYPE.public_projection(self.canonical)
        self.assertEqual(set(public), {"train", "test"})
        public_id = PROTOTYPE.public_id(public)
        self.assertRegex(public_id, r"^[0-9a-f]{64}$")
        self.assertEqual(public_id, public_challenge_id(public))
        self.assertEqual(len(public["train"]), 4)
        self.assertEqual(len(public["test"]), 4)
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        serialized = json.dumps(public, sort_keys=True)
        for forbidden in ("branch_map", "parameter", "program", "seed", "profile", "sample_index"):
            self.assertNotIn(forbidden, serialized)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"challenge-{public_id}.json"
            PROTOTYPE.write_public_challenge(path, public, force=False)
            self.assertEqual(path.read_bytes(), public_challenge_bytes(public))

        private_metadata_changed = copy.deepcopy(self.canonical)
        private_metadata_changed["seed"] = 999999
        private_metadata_changed["test"][0]["output"] = [[0]]
        self.assertEqual(PROTOTYPE.public_projection(private_metadata_changed), public)

        visible_demo_changed = copy.deepcopy(self.canonical)
        visible_demo_changed["train"][0]["output"][0][0] = 0
        changed_public = PROTOTYPE.public_projection(visible_demo_changed)
        self.assertNotEqual(PROTOTYPE.public_id(changed_public), public_id)

    def test_verifiers_reject_cross_setting_query_and_public_label_leak(self):
        cross_setting = copy.deepcopy(self.canonical)
        cross_setting["test"][0]["output"] = copy.deepcopy(self.swapped["test"][0]["output"])
        with self.assertRaises(ValueError):
            PROTOTYPE.verify_episode(cross_setting)

        public = PROTOTYPE.public_projection(self.canonical)
        leaked = copy.deepcopy(public)
        leaked["test"][0]["output"] = copy.deepcopy(self.canonical["test"][0]["output"])
        with self.assertRaises(ValueError):
            PROTOTYPE.verify_public_projection(self.canonical, leaked)
        self.assertTrue(PROTOTYPE.verify_public_projection(self.canonical, public)["ok"])

    def test_private_verifier_rejects_sampler_provenance_tampering(self):
        mutations = (
            ("seed", lambda episode: episode.__setitem__("seed", episode["seed"] + 1)),
            (
                "profile",
                lambda episode: episode["test"][0].__setitem__("profile", "solid_square"),
            ),
            (
                "sample_index",
                lambda episode: episode["train"][0].__setitem__(
                    "sample_index", episode["train"][0]["sample_index"] + 1
                ),
            ),
        )
        for name, mutate in mutations:
            tampered = copy.deepcopy(self.canonical)
            mutate(tampered)
            with self.subTest(field=name), self.assertRaises(ValueError):
                PROTOTYPE.verify_episode(tampered)


if __name__ == "__main__":
    unittest.main()
