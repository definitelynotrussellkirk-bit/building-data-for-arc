"""Regression tests for absence-only archive reads; no puzzle sources are used."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace/low_space"))

import archive_overlay as overlay_module
from archive_overlay import ArchiveOverlay, ArchiveOverlayError


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.tmp.name)
        self.work = self.root / "WORK"
        (self.work / "repo").mkdir(parents=True)
        self.rel = "repo/immutable.txt"
        self.raw = b"original archive bytes\n"
        self.manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {self.rel: sha(self.raw)}}
        self.contract = {"task_id": "selected", "baseline_sha256": {"repo/selected.txt": sha(b"selected")}}
        self.archive = self.root / "input.zip"
        self.make_archive()
        (self.work / "ASSIGNMENT.json").write_text(json.dumps(self.contract))

    def tearDown(self):
        self.tmp.cleanup()

    def make_archive(self, *, extra=(), stored=None, manifest=None):
        if manifest is not None:
            self.manifest = manifest
        manifest_bytes = json.dumps(self.manifest).encode()
        (self.work / "PACKET-MANIFEST.json").write_bytes(manifest_bytes)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_STORED) as z:
                z.writestr("WORK/PACKET-MANIFEST.json", manifest_bytes)
                z.writestr("WORK/" + self.rel, self.raw if stored is None else stored)
                for name, raw in extra:
                    z.writestr(name, raw)
        self.expected_hash = sha(self.archive.read_bytes())

    def overlay(self, **kwargs):
        values = dict(expected_zip_sha256=self.expected_hash, omitted_paths=[self.rel])
        values.update(kwargs)
        return ArchiveOverlay(self.work, self.archive, **values)

    def test_missing_immutable_reads_and_patch_restoration(self):
        originals = (Path.open, Path.exists, Path.is_file, Path.read_bytes)
        p = self.work / self.rel
        with self.overlay() as overlay:
            self.assertTrue(p.exists())
            self.assertTrue(p.is_file())
            self.assertEqual(p.read_bytes(), self.raw)
            self.assertEqual(p.read_text(), self.raw.decode())
            with p.open("rb") as f:
                self.assertFalse(f.writable())
                with self.assertRaises(io.UnsupportedOperation):
                    f.write(b"wrong")
            with self.assertRaises(FileNotFoundError):
                p.stat()
            self.assertFalse((self.root / self.rel).exists())
            with self.assertRaises(FileNotFoundError):
                (self.work / "repo" / ".." / self.rel).read_bytes()
        self.assertEqual(originals, (Path.open, Path.exists, Path.is_file, Path.read_bytes))
        self.assertFalse(p.exists())
        self.assertEqual(overlay.report()["verified_virtual_path_count"], 1)
        self.assertEqual(overlay.report(include_paths=True)["verified_virtual_paths"], [self.rel])

    def test_exception_restores_methods(self):
        originals = (Path.open, Path.exists, Path.is_file)
        with self.assertRaisesRegex(RuntimeError, "test exception"):
            with self.overlay():
                raise RuntimeError("test exception")
        self.assertEqual(originals, (Path.open, Path.exists, Path.is_file))

    def test_existing_corruption_is_visible_and_deletion_is_not_masked(self):
        p = self.work / self.rel
        p.write_bytes(b"corrupt existing file")
        with self.overlay():
            self.assertNotEqual(sha(p.read_bytes()), self.manifest["files"][self.rel])
            p.unlink()
            self.assertFalse(p.is_file())
            with self.assertRaises(FileNotFoundError):
                p.read_bytes()

    def test_symlinks_directories_and_fifo_are_not_virtualized(self):
        p = self.work / self.rel
        p.symlink_to(self.root / "missing")
        with self.overlay():
            self.assertTrue(p.is_symlink())
            self.assertFalse(p.exists())
            self.assertFalse(p.is_file())
            with self.assertRaises(FileNotFoundError):
                p.read_bytes()
        p.unlink()
        p.mkdir()
        with self.overlay():
            self.assertFalse(p.is_file())
            with self.assertRaises(IsADirectoryError):
                p.read_bytes()
        p.rmdir()
        if hasattr(os, "mkfifo"):
            os.mkfifo(p)
            with self.overlay():
                self.assertTrue(p.exists())
                self.assertFalse(p.is_file())

    def test_symlink_or_non_directory_ancestor_prevents_fallback(self):
        repo = self.work / "repo"
        repo.rmdir()
        repo.symlink_to(self.root / "missing-dir", target_is_directory=True)
        with self.overlay():
            self.assertFalse((self.work / self.rel).is_file())
        repo.unlink()
        repo.write_bytes(b"not a directory")
        with self.overlay():
            self.assertFalse((self.work / self.rel).is_file())

    def test_existing_file_created_during_context_wins(self):
        p = self.work / self.rel
        with self.overlay():
            self.assertEqual(p.read_bytes(), self.raw)
            p.write_bytes(b"actual new bytes")
            self.assertEqual(p.read_bytes(), b"actual new bytes")
            p.unlink()
            self.assertFalse(p.is_file())

    def test_write_opens_are_real_and_outputs_are_real(self):
        p = self.work / self.rel
        with self.overlay():
            with self.assertRaises(FileNotFoundError):
                p.open("r+")
            self.assertFalse(p.exists())
            out = self.work / "result.zip"
            with out.open("xb") as f:
                f.write(b"real output")
        self.assertEqual(out.read_bytes(), b"real output")
        self.assertFalse(p.exists())

    def test_wrong_archive_hash_and_local_manifest_rejected_before_patch(self):
        original = Path.open
        with self.assertRaisesRegex(ArchiveOverlayError, "ZIP SHA-256"):
            with self.overlay(expected_zip_sha256="0" * 64):
                self.fail("unreachable")
        self.assertIs(Path.open, original)
        (self.work / "PACKET-MANIFEST.json").write_text("{}")
        with self.assertRaisesRegex(ArchiveOverlayError, "Local packet manifest"):
            with self.overlay():
                self.fail("unreachable")
        self.assertIs(Path.open, original)

    def test_manifest_hash_mismatch_rejected(self):
        self.make_archive(stored=b"different archive bytes")
        with self.overlay():
            with self.assertRaisesRegex(ArchiveOverlayError, "Manifest SHA-256"):
                (self.work / self.rel).read_bytes()

    def test_corrupt_zip_entry_rejected(self):
        raw = self.archive.read_bytes()
        self.archive.write_bytes(raw.replace(self.raw, b"X" + self.raw[1:], 1))
        self.expected_hash = sha(self.archive.read_bytes())
        with self.overlay():
            with self.assertRaisesRegex(ArchiveOverlayError, "Cannot read ZIP member"):
                (self.work / self.rel).read_bytes()

    def test_duplicate_unsafe_and_nonregular_members_rejected(self):
        symlink = zipfile.ZipInfo("WORK/link")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases = [
            [("WORK/" + self.rel, self.raw)],
            [("WORK/../escape", b"bad")],
            [("/absolute", b"bad")],
            [("WORK/back\\slash", b"bad")],
            [("WORK/repo", b"ancestor is a file")],
            [(symlink, b"target")],
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                self.make_archive(extra=extra)
                original = Path.open
                with self.assertRaises(ArchiveOverlayError):
                    with self.overlay():
                        self.fail("unreachable")
                self.assertIs(Path.open, original)

    def test_selected_and_baseline_sources_cannot_be_omitted(self):
        for rel in ["repo/selected.txt", "repo/generators/selected/notes.md"]:
            self.manifest["files"] = {self.rel: sha(self.raw), rel: sha(b"selected")}
            self.make_archive(extra=[("WORK/" + rel, b"selected")])
            with self.assertRaisesRegex(ArchiveOverlayError, "Selected or baseline"):
                with self.overlay(omitted_paths=[rel]):
                    self.fail("unreachable")

    def test_unknown_and_nonrepo_omissions_rejected(self):
        for rel in ["repo/unknown", "repo/../escape", "ASSIGNMENT.json", ".review/baseline/repo/immutable.txt"]:
            with self.subTest(rel=rel), self.assertRaises(ArchiveOverlayError):
                with self.overlay(omitted_paths=[rel]):
                    self.fail("unreachable")

    def test_archive_mutation_during_context_rejected(self):
        with self.overlay():
            with self.archive.open("ab") as f:
                f.write(b"changed")
            with self.assertRaisesRegex(ArchiveOverlayError, "Archive changed"):
                (self.work / self.rel).read_bytes()

    def test_nested_context_rejected_and_other_threads_see_disk(self):
        with self.overlay():
            with self.assertRaisesRegex(RuntimeError, "already active"):
                with self.overlay():
                    self.fail("unreachable")
            observed = []
            t = threading.Thread(target=lambda: observed.append((self.work / self.rel).is_file()))
            t.start()
            t.join()
            self.assertEqual(observed, [False])
            self.assertTrue((self.work / self.rel).is_file())

    def test_context_object_is_single_use(self):
        overlay = self.overlay()
        with overlay:
            self.assertTrue((self.work / self.rel).is_file())
        original = Path.open
        with self.assertRaisesRegex(RuntimeError, "single-use"):
            with overlay:
                self.fail("unreachable")
        self.assertIs(Path.open, original)

    def test_cli_help_and_invalid_digest(self):
        cli = Path(overlay_module.__file__).with_name("package_sparse.py")
        help_result = subprocess.run([sys.executable, "-B", str(cli), "--help"],
                                     capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--omissions", help_result.stdout)
        bad_result = subprocess.run([sys.executable, "-B", str(cli), "--work", str(self.work),
                                    "--source-zip", str(self.archive), "--zip-sha256", "bad",
                                    "--omissions", "unused.json", "--out", "unused.zip"],
                                   capture_output=True, text=True)
        self.assertEqual(bad_result.returncode, 2)
        self.assertIn("64-character SHA-256", bad_result.stderr)


if __name__ == "__main__":
    unittest.main()
