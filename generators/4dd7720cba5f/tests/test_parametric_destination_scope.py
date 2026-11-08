from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


TASK_ID = "4dd7720cba5f"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
CANONICAL_SHA256 = "83711946021311fb3b33477e3b2e385cc8f8f9a4c5831cfcaaa1660c0789888f"


def _load_module(path: Path, name: str):
    if not path.is_file():
        return None
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _require(module):
    if module is None:
        raise AssertionError(f"missing prototype module: {PROTOTYPE_PATH}")
    return module


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


class DestinationScopePrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prototype = _load_module(
            PROTOTYPE_PATH, "generator_4dd7720cba5f_destination_scope_prototype"
        )

    def test_contract_and_canonical_default_are_exact(self) -> None:
        module = _require(self.prototype)
        self.assertEqual(module.TASK_ID, TASK_ID)
        self.assertEqual(module.PARAMETER_NAME, "destination_scope")
        self.assertEqual(
            module.ALLOWED_SETTINGS,
            ("all_tiles", "empty_tiles_only"),
        )
        self.assertEqual(module.DEFAULT_SETTING, "all_tiles")
        canonical = module.canonical_program()
        self.assertEqual(
            hashlib.sha256(canonical.encode()).hexdigest(),
            CANONICAL_SHA256,
        )
        self.assertEqual(module.materialize_rule("all_tiles"), canonical)
        alternative = module.materialize_rule("empty_tiles_only")
        self.assertNotEqual(alternative, canonical)
        self.assertIn("blank-interior?", alternative)

    def test_canonical_source_drift_fails_closed(self) -> None:
        module = _require(self.prototype)
        canonical = module.canonical_program()
        with self.assertRaises(ValueError):
            module.materialize_rule(
                "empty_tiles_only", source=canonical + "\n"
            )

    def test_setting_choice_and_validation_are_strict(self) -> None:
        module = _require(self.prototype)
        chosen = {module.choose_setting(seed) for seed in range(64)}
        self.assertEqual(chosen, set(module.ALLOWED_SETTINGS))
        for invalid in (True, -1, 1.5, "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    module.choose_setting(invalid)
        for invalid in (None, "union", 1, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    module.materialize_rule(invalid)

    def test_python_semantics_disagree_on_a_lawful_union_profile(self) -> None:
        module = _require(self.prototype)
        grid = module.generate_input(17, 0)
        self.assertEqual(module.validate_input(grid), [])
        canonical = module.apply_python(grid, "all_tiles")
        alternative = module.apply_python(grid, "empty_tiles_only")
        self.assertNotEqual(canonical, alternative)
        self.assertEqual(canonical, module.production_generator().solve_python(grid))
        self.assertEqual(
            alternative,
            module.production_generator()._blank_targets_only(grid),
        )

    def test_episode_has_one_setting_three_demos_and_four_distinct_queries(self) -> None:
        module = _require(self.prototype)
        for setting in module.ALLOWED_SETTINGS:
            with self.subTest(setting=setting):
                episode = module.build_episode(
                    29,
                    setting=setting,
                    demo_count=3,
                    query_count=4,
                )
                self.assertEqual(episode["meta"][module.PARAMETER_NAME], setting)
                self.assertEqual(episode["meta"]["demo_count"], 3)
                self.assertEqual(episode["meta"]["query_count"], 4)
                self.assertEqual(len(episode["train"]), 3)
                self.assertEqual(len(episode["test"]), 4)
                pairs = episode["train"] + episode["test"]
                keys = [_grid_key(pair["input"]) for pair in pairs]
                self.assertEqual(len(keys), len(set(keys)))
                rival = next(
                    value for value in module.ALLOWED_SETTINGS if value != setting
                )
                for pair in pairs:
                    self.assertEqual(
                        pair["output"],
                        module.apply_python(pair["input"], setting),
                    )
                    self.assertNotEqual(
                        pair["output"],
                        module.apply_python(pair["input"], rival),
                    )
                consistent = [
                    candidate
                    for candidate in module.ALLOWED_SETTINGS
                    if all(
                        module.apply_python(pair["input"], candidate)
                        == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                self.assertEqual(consistent, [setting])

    def test_counts_reject_bool_zero_and_excess(self) -> None:
        module = _require(self.prototype)
        for name, kwargs in (
            ("demo_count", {"demo_count": True}),
            ("demo_count", {"demo_count": 0}),
            ("query_count", {"query_count": False}),
            ("query_count", {"query_count": 33}),
        ):
            with self.subTest(name=name, kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    module.build_episode(1, **kwargs)

    def test_public_projection_and_id_depend_only_on_visible_bytes(self) -> None:
        module = _require(self.prototype)
        episode = module.build_episode(
            41,
            setting="all_tiles",
            demo_count=3,
            query_count=4,
        )
        public = module.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        public_id = module.public_id(episode)
        self.assertEqual(len(public_id), 64)

        private_mutation = copy.deepcopy(episode)
        private_mutation["meta"][module.PARAMETER_NAME] = "empty_tiles_only"
        private_mutation["meta"]["seed"] = 999999
        for pair in private_mutation["test"]:
            pair["output"] = [[9]]
        self.assertEqual(
            module.public_challenge(private_mutation),
            public,
        )
        self.assertEqual(module.public_id(private_mutation), public_id)

        visible_mutation = copy.deepcopy(episode)
        visible_mutation["train"][0]["output"][1][1] ^= 1
        self.assertNotEqual(module.public_id(visible_mutation), public_id)

    def test_racket_evidence_writer_emits_private_and_opaque_public_artifacts(self) -> None:
        module = _require(self.prototype)
        status = module.racket_status()
        if not status["available"]:
            self.skipTest(status["reason"])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "evidence"
            report = module.write_evidence(
                out,
                seeds=(0, 2),
                demo_count=3,
                query_count=4,
            )
            self.assertEqual(report["settings_covered"], list(module.ALLOWED_SETTINGS))
            self.assertEqual(report["episode_count"], 2)
            self.assertEqual(report["racket_execution_count"], 28)
            self.assertTrue(report["all_python_racket_parity"])
            self.assertTrue(report["all_demo_identifiable"])
            self.assertTrue(report["all_queries_distinguish_rival"])
            self.assertTrue((out / "report.json").is_file())
            self.assertTrue((out / "private" / "distinguishing_witness.json").is_file())
            for setting in module.ALLOWED_SETTINGS:
                self.assertTrue((out / "private" / "rules" / f"{setting}.rkt").is_file())
            public_files = sorted((out / "public").glob("challenge-*.json"))
            private_files = sorted((out / "private").glob("episode-*.json"))
            self.assertEqual(len(public_files), 2)
            self.assertEqual(len(private_files), 2)
            for public_path in public_files:
                challenge = json.loads(public_path.read_text())
                self.assertEqual(set(challenge), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input"} for pair in challenge["test"]))
                expected_id = public_path.stem.removeprefix("challenge-")
                self.assertEqual(
                    hashlib.sha256(public_path.read_bytes()).hexdigest(),
                    expected_id,
                )

    def test_evidence_writer_rejects_duplicate_public_payloads(self) -> None:
        module = _require(self.prototype)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "duplicate public challenge"):
                module.write_evidence(
                    Path(temp) / "duplicate",
                    seeds=(0, 0),
                    demo_count=3,
                    query_count=4,
                )


if __name__ == "__main__":
    unittest.main()
