"""Portable standard-library regression tests; uses only artificial packet data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOTS = ("checks", "solve", "solve-blind")


def fixture(parent):
    """Construct a tiny, synthetic packet without drawing a real assignment."""
    from arcpuzzles.review_full_packet import canonical_json

    packet = parent / "packet"
    packet.mkdir()
    name = "repo/generators/artificial/generator.py"
    raw = b"# Artificial fixture, containing no puzzle implementation.\n"
    digest = hashlib.sha256(raw).hexdigest()
    for base in (packet, packet / ".review/baseline"):
        path = base / name
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
    generator = {"generator_sha256": digest}
    manifest = {"files": {name: digest}, "main_ids": ["artificial"],
                "all_ids": ["artificial"], "generators": {"artificial": generator},
                "questions": ["synthetic"]}
    manifest_raw = canonical_json(manifest)
    (packet / "PACKET-MANIFEST.json").write_bytes(manifest_raw)
    contract = {"schema": "arcpuzzles-full-assignment-v2",
                "packet_id": hashlib.sha256(manifest_raw).hexdigest(),
                "assignment_id": "review-" + "0" * 16, "task_id": "artificial",
                "generator": generator, "question": "synthetic",
                "baseline_sha256": manifest["files"]}
    (packet / "ASSIGNMENT.json").write_text(json.dumps(contract), encoding="utf-8")
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (packet / name).write_text("Artificial fixture.\n", encoding="utf-8")
    return packet


class EvidenceRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.packet = fixture(self.parent)
        self.out = self.parent / "return.zip"

    def build(self):
        from arcpuzzles.review_full_return import build_full_return
        return build_full_return(self.packet, self.out)


def root_symlink_test(root_name, dangling):
    def test(self):
        target = self.parent / "external"
        if not dangling:
            target.mkdir()
            (target / "toy.txt").write_bytes(b"toy external evidence\n")
        root = self.packet / root_name
        root.symlink_to(target, target_is_directory=True)
        expected = "Symlink check evidence:" if root_name == "checks" else "Symlink solve evidence:"
        with self.assertRaisesRegex(ValueError, expected) as error:
            self.build()
        self.assertIn(str(root), str(error.exception))
        self.assertFalse(self.out.exists(), "A rejected root must not leave a return ZIP")
    return test


def child_symlink_test(root_name):
    def test(self):
        root = self.packet / root_name
        root.mkdir()
        target = self.parent / "toy.txt"
        target.write_bytes(b"toy child evidence\n")
        (root / "linked.txt").symlink_to(target)
        expected = "Symlink check evidence:" if root_name == "checks" else "Symlink solve evidence:"
        with self.assertRaisesRegex(ValueError, expected):
            self.build()
        self.assertFalse(self.out.exists())
    return test


def normal_directory_test(root_name):
    def test(self):
        # Empty solve roots are valid for an in-progress packet without an episode.
        (self.packet / root_name).mkdir()
        result = self.build()
        self.assertEqual(result["completion_state"], "in_progress")
        self.assertTrue(self.out.is_file())
    return test


for root_name in ROOTS:
    suffix = root_name.replace("-", "_")
    setattr(EvidenceRootTests, f"test_{suffix}_existing_root_symlink", root_symlink_test(root_name, False))
    setattr(EvidenceRootTests, f"test_{suffix}_dangling_root_symlink", root_symlink_test(root_name, True))
    setattr(EvidenceRootTests, f"test_{suffix}_child_symlink", child_symlink_test(root_name))
    setattr(EvidenceRootTests, f"test_{suffix}_normal_directory", normal_directory_test(root_name))


def normal_nested_evidence(self):
    path = self.packet / "checks/nested/result.txt"
    path.parent.mkdir(parents=True)
    raw = b"toy retained receipt\n"
    path.write_bytes(raw)
    self.build()
    with zipfile.ZipFile(self.out) as archive:
        self.assertEqual(archive.read("checks/nested/result.txt"), raw)


EvidenceRootTests.test_normal_nested_checks_are_packaged = normal_nested_evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Repo or isolated tooling-copy root")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.repo.resolve() / "src"))
    from arcpuzzles import review_full_return
    source = Path(review_full_return.__file__)
    print(f"Tested source: {source}", flush=True)
    print(f"Source SHA-256: {hashlib.sha256(source.read_bytes()).hexdigest()}", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceRootTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("COUNTS " + json.dumps({"tests": result.testsRun, "failures": len(result.failures),
                                 "errors": len(result.errors), "skipped": len(result.skipped),
                                 "passed": result.testsRun - len(result.failures) - len(result.errors)
                                           - len(result.skipped)}), flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)
