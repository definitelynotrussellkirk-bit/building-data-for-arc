"""Real temporary-file and CLI tests for the lossless evidence tool."""

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "workspace" / "compact_evidence.py"
RELATIVE = "WORK/checks/nested/evidence.json"
PAYLOAD = (b'{"finding":"retained failure", "bytes":"\x00\xff"}\n' * 30000
           + bytes(range(256)))


class EvidenceCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.packet = self.base / "packet"
        self.packet.mkdir()
        self.retained = self.base / "retained"
        self.original = self.packet / RELATIVE
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(PAYLOAD)
        self.manifest = self.packet / "manifest.json"
        self.compressed = self.packet / (RELATIVE + ".gz")
        self.restored = self.base / "restored"

    def run_cli(self, *arguments, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                                text=True, capture_output=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def compact(self):
        return self.run_cli("compact", RELATIVE, "--root", self.packet,
                            "--manifest", "manifest.json", "--retain-original", self.retained)

    def test_round_trip_hashes_and_portable_mapping(self):
        self.compact()
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        manifest = json.loads(self.manifest.read_text())
        self.assertFalse(self.original.exists())
        self.assertEqual((self.retained / RELATIVE).read_bytes(), PAYLOAD)
        self.assertEqual(manifest["original"], {
            "path": RELATIVE, "size_bytes": len(PAYLOAD), "sha256": digest,
        })
        archive = self.compressed.read_bytes()
        self.assertEqual(gzip.decompress(archive), PAYLOAD)
        self.assertEqual(manifest["compressed"], {
            "path": RELATIVE + ".gz", "size_bytes": len(archive),
            "sha256": hashlib.sha256(archive).hexdigest(),
        })
        self.assertEqual(manifest["retained_copy"]["path"], RELATIVE)
        for key in ("original", "compressed", "retained_copy"):
            self.assertFalse(Path(manifest[key]["path"]).is_absolute())

        # The restored mapping works even after the whole packet is moved.
        moved = self.base / "moved-packet"
        shutil.move(self.packet, moved)
        self.run_cli("restore", moved / "manifest.json", "--root", self.restored)
        restored_bytes = (self.restored / RELATIVE).read_bytes()
        self.assertEqual(restored_bytes, PAYLOAD)
        self.assertEqual(hashlib.sha256(restored_bytes).hexdigest(), digest)
        self.assertTrue((moved / (RELATIVE + ".gz")).is_file())

    def test_deterministic_gzip(self):
        self.compact()
        other = self.base / "other-packet"
        other.mkdir()
        (other / "different-name.bin").write_bytes(PAYLOAD)
        self.run_cli("compact", "different-name.bin", "--root", other,
                     "--manifest", "manifest.json", "--retain-original", self.base / "other-retained")
        self.assertEqual(self.compressed.read_bytes(), (other / "different-name.bin.gz").read_bytes())

    def test_compact_refuses_overwrites_and_preserves_input(self):
        for collision in (self.compressed, self.manifest, self.retained / RELATIVE):
            with self.subTest(collision=collision):
                collision.parent.mkdir(parents=True, exist_ok=True)
                collision.write_bytes(b"existing evidence")
                self.run_cli("compact", RELATIVE, "--root", self.packet,
                             "--manifest", "manifest.json", "--retain-original", self.retained,
                             success=False)
                self.assertEqual(self.original.read_bytes(), PAYLOAD)
                self.assertEqual(collision.read_bytes(), b"existing evidence")
                collision.unlink()

    def test_missing_input_and_internal_retention_are_rejected(self):
        self.run_cli("compact", "missing.json", "--root", self.packet,
                     "--manifest", "manifest.json", "--retain-original", self.retained,
                     success=False)
        self.run_cli("compact", RELATIVE, "--root", self.packet,
                     "--manifest", "manifest.json", "--retain-original", self.packet / "retained",
                     success=False)
        self.assertEqual(self.original.read_bytes(), PAYLOAD)
        self.assertFalse(self.manifest.exists())
        self.assertFalse(self.compressed.exists())

    def test_restore_refuses_existing_destination(self):
        self.compact()
        destination = self.restored / RELATIVE
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"do not overwrite")
        self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
        self.assertEqual(destination.read_bytes(), b"do not overwrite")

    def test_unsafe_manifest_paths_are_rejected(self):
        self.compact()
        good_manifest = json.loads(self.manifest.read_text())
        unsafe_paths = ("../escape", "/absolute/escape", "folder/../../escape",
                        "..\\escape", "C:/escape", "folder//file", "folder/./file")
        for key in ("original", "compressed", "retained_copy"):
            for unsafe in unsafe_paths:
                with self.subTest(key=key, path=unsafe):
                    manifest = json.loads(json.dumps(good_manifest))
                    manifest[key]["path"] = unsafe
                    self.manifest.write_text(json.dumps(manifest))
                    self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
                    self.assertFalse(self.restored.exists())
        self.assertEqual((self.retained / RELATIVE).read_bytes(), PAYLOAD)

    def test_corrupt_archive_and_wrong_original_digest_do_not_restore(self):
        self.compact()
        archive = self.compressed.read_bytes()
        self.compressed.write_bytes(archive[:-1] + bytes([archive[-1] ^ 1]))
        self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
        self.assertFalse(self.restored.exists())
        self.compressed.write_bytes(archive)
        good_manifest = json.loads(self.manifest.read_text())
        for key, value in (("sha256", "0" * 64), ("size_bytes", len(PAYLOAD) - 1)):
            with self.subTest(key=key):
                manifest = json.loads(json.dumps(good_manifest))
                manifest["original"][key] = value
                self.manifest.write_text(json.dumps(manifest))
                self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
                self.assertFalse((self.restored / RELATIVE).exists())
                self.assertEqual(list(self.restored.rglob("*.tmp")), [])

    def test_restore_rejects_symlink_paths(self):
        self.compact()
        outside = self.base / "outside"
        outside.mkdir()
        self.restored.mkdir()
        (self.restored / "WORK").symlink_to(outside, target_is_directory=True)
        self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
        self.assertEqual(list(outside.iterdir()), [])
        (self.restored / "WORK").unlink()

        external_archive = outside / "archive.gz"
        self.compressed.rename(external_archive)
        self.compressed.symlink_to(external_archive)
        self.run_cli("restore", self.manifest, "--root", self.restored, success=False)
        self.assertFalse((self.restored / RELATIVE).exists())


if __name__ == "__main__":
    unittest.main()
