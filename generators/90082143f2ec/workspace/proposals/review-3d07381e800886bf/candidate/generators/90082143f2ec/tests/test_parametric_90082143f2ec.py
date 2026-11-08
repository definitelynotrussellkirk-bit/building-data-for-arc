"""Focused tests for the PROPOSED axis-policy parametric prototype.

The selected production generator and canonical Racket authority remain fixed.
These tests exercise only the task-local prototype, its promotion adapter, and
its public/private boundary.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)

TASK_ID = "90082143f2ec"
ROOT = find_root(__file__)
TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
README_PATH = PARAMETRIC / "README.md"
GEN, _GEN_PATH, _GEN_SHA = load_selected_generator(TASK_ID, root=ROOT)


def _load(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing required prototype file: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "axis_policy_parametric_prototype")


def _canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


class TestPrototypeContract(unittest.TestCase):
    def test_required_files_and_promotion_contract_exist(self):
        for path in (PROTOTYPE_PATH, ADAPTER_PATH, PROMOTION_PATH, README_PATH):
            self.assertTrue(path.is_file(), path)
        contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "arcpuzzles-parametric-adapter-v1")
        self.assertEqual(
            contract["adapter"],
            "generators/90082143f2ec/workspace/parametric/adapter.py",
        )
        self.assertEqual(
            contract["parameters"],
            {"axis_policy": ["more_coherent", "less_coherent"]},
        )
        self.assertEqual(contract["default"], {"axis_policy": "more_coherent"})
        self.assertEqual(contract["limits"], {"demos": [3, 8], "queries": [1, 8]})
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("from the outer extraction directory", readme)
        self.assertNotIn("from `WORK/`", readme)

    def test_exact_default_rule_and_bounded_setting_validation(self):
        proto = _prototype()
        self.assertEqual(proto.AXIS_POLICIES, ("more_coherent", "less_coherent"))
        self.assertEqual(proto.DEFAULT_AXIS_POLICY, "more_coherent")
        self.assertEqual(proto.program_for("more_coherent"), _canonical_program())
        self.assertNotEqual(proto.program_for("less_coherent"), _canonical_program())
        self.assertEqual(proto.choose_setting(0), "more_coherent")
        self.assertEqual(proto.choose_setting(1), "less_coherent")
        self.assertEqual(proto.choose_setting(2), "more_coherent")
        for bad in (True, -1, 1.5, "1"):
            with self.assertRaises((TypeError, ValueError)):
                proto.choose_setting(bad)
        for bad in ("dominant", "rows", None, True):
            with self.assertRaises((TypeError, ValueError)):
                proto.program_for(bad)

    def test_paired_seeds_share_seven_distinct_lawful_inputs(self):
        proto = _prototype()
        first = proto.episode_inputs(0, demos=3, queries=4, difficulty="medium")
        second = proto.episode_inputs(1, demos=3, queries=4, difficulty="medium")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 7)
        self.assertEqual(len({_frozen(grid) for grid in first}), 7)
        self.assertTrue(all(GEN.self_check(grid) == [] for grid in first))
        demo_orientations = {
            GEN.semantic_observables(grid)["orientation"] for grid in first[:3]
        }
        self.assertEqual(demo_orientations, {"vertical", "horizontal"})
        for name, value in (("demos", 2), ("demos", 9), ("queries", 0), ("queries", 9)):
            kwargs = {"demos": 3, "queries": 4, name: value}
            with self.assertRaises(ValueError):
                proto.episode_inputs(0, **kwargs)
        for name in ("demos", "queries"):
            kwargs = {"demos": 3, "queries": 4, name: True}
            with self.assertRaises(TypeError):
                proto.episode_inputs(0, **kwargs)


class TestPrototypeRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proto = _prototype()
        cls.engine = cls.proto.RuleEngine()
        cls.addClassCleanup(cls.engine.close)
        cls.more = cls.proto.generate_episode(
            0, demos=3, queries=4, difficulty="medium", engine=cls.engine
        )
        cls.less = cls.proto.generate_episode(
            1, demos=3, queries=4, difficulty="medium", engine=cls.engine
        )

    def test_complete_paired_episodes_use_one_setting_and_four_queries(self):
        self.assertEqual(self.more["axis_policy"], "more_coherent")
        self.assertEqual(self.less["axis_policy"], "less_coherent")
        for episode in (self.more, self.less):
            self.assertEqual((len(episode["train"]), len(episode["test"])), (3, 4))
            self.assertEqual(episode["demo_count"], 3)
            self.assertEqual(episode["query_count"], 4)
            self.assertEqual(
                episode["program_solution"],
                self.proto.program_for(episode["axis_policy"]),
            )
            self.assertEqual(
                len({_frozen(pair["input"]) for pair in episode["train"] + episode["test"]}),
                7,
            )
            for report in episode["query_identification"]:
                self.assertEqual(report["consistent_variants"], [episode["axis_policy"]])
                self.assertEqual(report["status"], "identified_within_declared_rivals")
                self.assertFalse(report["query_answer_used_for_demo_fit"])
        for more_pair, less_pair in zip(
            self.more["train"] + self.more["test"],
            self.less["train"] + self.less["test"],
            strict=True,
        ):
            self.assertEqual(more_pair["input"], less_pair["input"])
            self.assertNotEqual(more_pair["output"], less_pair["output"])

    def test_racket_default_matches_every_canonical_pair_and_alternate_axis(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 8)
        for pair in pairs:
            actual = self.engine.apply(pair["input"], "more_coherent")
            self.assertEqual(actual, pair["output"])
        witness = self.more["test"][0]["input"]
        facts = GEN.semantic_observables(witness)
        self.assertEqual(self.engine.apply(witness, "more_coherent"), facts["clean"])
        self.assertEqual(self.engine.apply(witness, "less_coherent"), facts["alternate"])
        self.assertNotEqual(facts["clean"], facts["alternate"])

    def test_public_projection_ignores_private_metadata_and_query_answers(self):
        public = self.proto.public_payload(self.more)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        self.assertEqual(self.proto.public_bytes(self.more), public_challenge_bytes(public))
        identifier = self.proto.public_id(self.more)
        mutated = copy.deepcopy(self.more)
        mutated["seed"] = 999999
        mutated["axis_policy"] = "less_coherent"
        mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
        self.assertEqual(self.proto.public_id(mutated), identifier)
        original = self.more["test"][0]["input"][0][0]
        public["test"][0]["input"][0][0] = (original + 1) % 10
        self.assertEqual(self.more["test"][0]["input"][0][0], original)

    def test_batch_writer_rejects_duplicate_visible_payload_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "duplicate visible payload"):
                self.proto.write_episodes(Path(tmp), [self.more, copy.deepcopy(self.more)])
            self.assertEqual(list(Path(tmp).rglob("*")), [])

    def test_adapter_delegates_exact_program(self):
        adapter = _load(ADAPTER_PATH, "axis_policy_parametric_adapter")
        self.assertEqual(
            adapter.program({"axis_policy": "more_coherent"}),
            _canonical_program(),
        )
        self.assertEqual(
            adapter.program({"axis_policy": "less_coherent"}),
            self.proto.program_for("less_coherent"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
