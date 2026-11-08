from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from reviewer_support import find_root, load_selected_generator


TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace/parametric/prototype.py"
VERIFY_PATH = TASK_DIR / "workspace/parametric/verify.py"
ROOT = find_root(__file__)


def load_prototype():
    if not PROTOTYPE_PATH.is_file():
        raise AssertionError(f"missing parametric prototype: {PROTOTYPE_PATH}")
    spec = importlib.util.spec_from_file_location(
        "ea8116b3e778_symmetry_mode_prototype",
        PROTOTYPE_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load prototype: {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_verifier():
    if not VERIFY_PATH.is_file():
        raise AssertionError(f"missing parametric verifier: {VERIFY_PATH}")
    spec = importlib.util.spec_from_file_location(
        "ea8116b3e778_symmetry_mode_verifier",
        VERIFY_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load verifier: {VERIFY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


class ParametricSymmetryModeTests(unittest.TestCase):
    def test_canonical_mode_preserves_exact_authority_and_programs_differ(self):
        proto = load_prototype()
        canonical = proto.canonical_source(root=ROOT)
        self.assertEqual(proto.DEFAULT_SYMMETRY_MODE, "both")
        self.assertEqual(
            proto.SYMMETRY_MODES,
            ("horizontal", "vertical", "half_turn", "both"),
        )
        self.assertEqual(proto.program_for("both", root=ROOT), canonical)
        programs = {
            mode: proto.normalized_program_hash(mode, root=ROOT)
            for mode in proto.SYMMETRY_MODES
        }
        self.assertEqual(len(set(programs.values())), 4)
        self.assertTrue(programs["both"].startswith("4e2d4d62614f"))

    def test_each_mode_changes_the_rule_and_canonical_mode_matches_generator(self):
        proto = load_prototype()
        grid = proto.prototype_input(17, 0, difficulty="hard")
        outputs = {
            mode: proto.solve(grid, symmetry_mode=mode)
            for mode in proto.SYMMETRY_MODES
        }
        self.assertEqual(len({grid_key(value) for value in outputs.values()}), 4)
        generator, _, _ = load_selected_generator(proto.TASK_ID, root=ROOT)
        self.assertEqual(outputs["both"], generator.solve_python(grid))
        self.assertEqual(grid, proto.prototype_input(17, 0, difficulty="hard"))

    def test_episode_has_fixed_setting_independent_counts_and_four_queries(self):
        proto = load_prototype()
        episode = proto.generate_episode(
            23,
            symmetry_mode="vertical",
            difficulty="medium",
            demonstration_count=2,
            query_count=4,
        )
        summary = proto.validate_episode(episode, root=ROOT)
        self.assertEqual(summary["symmetry_mode"], "vertical")
        self.assertEqual(summary["demonstration_count"], 2)
        self.assertEqual(summary["query_count"], 4)
        self.assertEqual(len(episode["train"]), 2)
        self.assertEqual(len(episode["test"]), 4)
        pairs = episode["train"] + episode["test"]
        self.assertEqual(len({grid_key(pair["input"]) for pair in pairs}), 6)
        for pair in pairs:
            self.assertEqual(
                pair["output"],
                proto.solve(pair["input"], symmetry_mode="vertical"),
            )
            for rival in proto.SYMMETRY_MODES:
                if rival != "vertical":
                    self.assertNotEqual(
                        pair["output"],
                        proto.solve(pair["input"], symmetry_mode=rival),
                    )

        paired = proto.generate_episode(
            23,
            symmetry_mode="horizontal",
            difficulty="medium",
            demonstration_count=2,
            query_count=4,
        )
        self.assertEqual(
            [pair["input"] for pair in pairs],
            [pair["input"] for pair in paired["train"] + paired["test"]],
        )
        self.assertNotEqual(
            [pair["output"] for pair in episode["test"]],
            [pair["output"] for pair in paired["test"]],
        )

    def test_public_projection_masks_answers_and_hidden_setting(self):
        proto = load_prototype()
        episode = proto.generate_episode(
            31,
            symmetry_mode="half_turn",
            demonstration_count=2,
            query_count=4,
        )
        public = proto.public_challenge(episode)
        self.assertTrue(all("output" in pair for pair in public["train"]))
        self.assertTrue(all("output" not in pair for pair in public["test"]))
        payload = proto.public_bytes(episode)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), proto.public_id(episode))
        text = payload.decode("utf-8")
        for secret in ("symmetry_mode", "parameters", "program", "seed"):
            self.assertNotIn(secret, text)

        with tempfile.TemporaryDirectory() as directory:
            path = proto.write_public(episode, directory)
            self.assertEqual(path.name, f"challenge-{proto.public_id(episode)}.json")
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(json.loads(payload), json.loads(path.read_text()))

    def test_public_id_depends_only_on_visible_challenge(self):
        proto = load_prototype()
        episode = proto.generate_episode(37, symmetry_mode="vertical")
        changed = copy.deepcopy(episode)
        changed["parameters"]["symmetry_mode"] = "horizontal"
        changed["program"] = "private replacement"
        changed["program_normalized_sha256"] = "private replacement"
        changed["meta"]["seed"] = 999999
        changed["test"][0]["output"] = [[9]]
        self.assertEqual(proto.public_challenge(changed), proto.public_challenge(episode))
        self.assertEqual(proto.public_bytes(changed), proto.public_bytes(episode))
        self.assertEqual(proto.public_id(changed), proto.public_id(episode))

    def test_verifier_cleanup_preserves_unrelated_files(self):
        verifier = load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            artifact_dir = Path(directory) / "artifacts"
            (artifact_dir / "public").mkdir(parents=True)
            (artifact_dir / "private").mkdir()
            (artifact_dir / "public/old.json").write_text("old")
            (artifact_dir / "private/old.json").write_text("old")
            (artifact_dir / "manifest.json").write_text("old")
            (artifact_dir / "keep.txt").write_text("keep")
            verifier._reset_artifacts(artifact_dir)
            self.assertEqual((artifact_dir / "keep.txt").read_text(), "keep")
            self.assertFalse((artifact_dir / "public").exists())
            self.assertFalse((artifact_dir / "private").exists())
            self.assertFalse((artifact_dir / "manifest.json").exists())

    def test_verifier_cleanup_rejects_broken_generated_symlink(self):
        verifier = load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            artifact_dir = base / "artifacts"
            artifact_dir.mkdir()
            (artifact_dir / "public").symlink_to(
                base / "missing-target", target_is_directory=True
            )
            with self.assertRaisesRegex(ValueError, "unsafe generated path"):
                verifier._reset_artifacts(artifact_dir)

    def test_verifier_executes_all_programs_and_materializes_masked_batch(self):
        verifier = load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            report = verifier.verify(
                seed=53,
                out_path=base / "verification.json",
                artifact_dir=base / "materialized",
                demonstration_count=2,
                query_count=4,
            )
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["counts"]["settings"], 4)
            self.assertEqual(report["counts"]["selected_pair_checks"], 24)
            self.assertEqual(report["counts"]["racket_program_pair_checks"], 96)
            self.assertTrue(report["canonical"]["exact_text_match"])
            self.assertTrue(report["all_racket_python_exact"])
            self.assertTrue(report["all_demos_refute_every_rival"])
            self.assertTrue(report["all_queries_setting_sensitive"])
            self.assertTrue(report["all_public_challenges_masked"])
            input_hashes = {
                tuple(row["input_hashes"])
                for row in report["episodes"].values()
            }
            self.assertEqual(len(input_hashes), 1)
            self.assertEqual(report["materialization"]["file_count"], 12)
            self.assertTrue((base / "verification.json").is_file())
            manifest_path = base / "materialized/manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            public_ids = manifest["public_challenge_ids"]
            self.assertEqual(public_ids, sorted(public_ids))
            self.assertEqual(len(public_ids), 4)

    def test_validation_rejects_tampering_and_invalid_boundaries(self):
        proto = load_prototype()
        episode = proto.generate_episode(
            41,
            symmetry_mode="both",
            demonstration_count=1,
            query_count=1,
        )
        tampered = copy.deepcopy(episode)
        tampered["test"][0]["output"][0][0] = (
            tampered["test"][0]["output"][0][0] + 1
        ) % 10
        with self.assertRaisesRegex(ValueError, "stored output"):
            proto.validate_episode(tampered, root=ROOT)

        with self.assertRaises(ValueError):
            proto.generate_episode(True)
        with self.assertRaises(ValueError):
            proto.generate_episode(1, symmetry_mode="diagonal")
        for bad in (0, True, 1.5):
            with self.assertRaises(ValueError):
                proto.generate_episode(1, demonstration_count=bad)
            with self.assertRaises(ValueError):
                proto.generate_episode(1, query_count=bad)
        with self.assertRaises(ValueError):
            proto.generate_episode(1, demonstration_count=32, query_count=33)


if __name__ == "__main__":
    unittest.main()
