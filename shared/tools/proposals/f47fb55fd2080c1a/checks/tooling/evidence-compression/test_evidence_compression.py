"""CLI contract tests, using synthetic files only inside this tool directory."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / "evidence_compression.py"


class CompressionCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "root"
        self.root.mkdir()
        self.path = "checks/before/report.json"
        self.raw = (b'{"failure":true,"example":[1,2,3]}\n' * 600)
        target = self.root / self.path
        target.parent.mkdir(parents=True)
        target.write_bytes(self.raw)

    def cli(self, *args, success=True):
        result = subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("error:", result.stderr)
        return result

    def compress(self, folder="packed", remove=False):
        out = self.home / folder
        args = ["compress", "--root", self.root, "--out", out, self.path]
        if remove:
            args.append("--remove-originals")
        self.cli(*args)
        return out

    def mutate_manifest(self, packed, mutate):
        path = packed / "MANIFEST.json"
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))

    def test_deterministic_roundtrip_with_exact_manifest(self):
        first = self.compress()
        second = self.compress("packed-again")
        self.assertEqual((first / "MANIFEST.json").read_bytes(),
                         (second / "MANIFEST.json").read_bytes())
        row = json.loads((first / "MANIFEST.json").read_text())["files"][0]
        self.assertEqual(row["path"], self.path)
        self.assertEqual(row["raw_size"], len(self.raw))
        self.assertEqual(row["raw_sha256"], hashlib.sha256(self.raw).hexdigest())
        gz = (first / row["compressed_path"]).read_bytes()
        self.assertEqual(gz, (second / row["compressed_path"]).read_bytes())
        self.assertEqual(row["compressed_size"], len(gz))
        self.assertEqual(row["compressed_sha256"], hashlib.sha256(gz).hexdigest())
        self.assertTrue((self.root / self.path).exists())
        self.cli("verify", "--bundle", first)
        restored = self.home / "restored"
        self.cli("restore", "--bundle", first, "--out", restored)
        self.assertEqual((restored / self.path).read_bytes(), self.raw)

    def test_explicit_removal_leaves_verified_restorable_copy(self):
        packed = self.compress(remove=True)
        self.assertFalse((self.root / self.path).exists())
        self.cli("verify", "--bundle", packed)
        restored = self.home / "restored"
        self.cli("restore", "--bundle", packed, "--out", restored)
        self.assertEqual((restored / self.path).read_bytes(), self.raw)

    def test_corrupt_compressed_stream_does_not_create_restore_directory(self):
        packed = self.compress()
        (packed / (self.path + ".gz")).write_bytes(b"broken")
        self.cli("verify", "--bundle", packed, success=False)
        out = self.home / "restored"
        self.cli("restore", "--bundle", packed, "--out", out, success=False)
        self.assertFalse(out.exists())
        self.assertEqual((self.root / self.path).read_bytes(), self.raw)

    def test_false_raw_hash_and_size_are_rejected(self):
        for field, value in [("raw_sha256", "0" * 64), ("raw_size", 1)]:
            with self.subTest(field=field):
                packed = self.compress("packed-" + field)
                self.mutate_manifest(packed, lambda d: d["files"][0].update({field: value}))
                self.cli("verify", "--bundle", packed, success=False)

    def test_traversal_and_duplicate_manifest_paths_are_rejected(self):
        for name, mutate in [
            ("traversal", lambda d: d["files"][0].update(path="../escaped")),
            ("absolute", lambda d: d["files"][0].update(compressed_path="/tmp/bad")),
            ("duplicate", lambda d: d["files"].append(dict(d["files"][0]))),
            ("prefix", lambda d: d["files"].append(dict(d["files"][0], path=self.path + "/child", compressed_path="other.gz"))),
        ]:
            with self.subTest(name=name):
                packed = self.compress("packed-" + name)
                self.mutate_manifest(packed, mutate)
                self.cli("verify", "--bundle", packed, success=False)

    def test_bad_explicit_targets_preserve_originals_and_create_no_bundle(self):
        for name, targets in [("traversal", ["../outside"]),
                              ("duplicate", [self.path, self.path]),
                              ("missing", [self.path, "missing.json"])]:
            with self.subTest(name=name):
                out = self.home / name
                self.cli("compress", "--root", self.root, "--out", out,
                         "--remove-originals", *targets, success=False)
                self.assertFalse(out.exists())
                self.assertEqual((self.root / self.path).read_bytes(), self.raw)

    def test_existing_output_and_symlink_source_are_rejected(self):
        out = self.home / "existing"
        out.mkdir()
        (out / "unrelated").write_bytes(b"keep")
        self.cli("compress", "--root", self.root, "--out", out, self.path, success=False)
        self.assertEqual((out / "unrelated").read_bytes(), b"keep")
        (self.root / "link").symlink_to(self.root / "checks", target_is_directory=True)
        self.cli("compress", "--root", self.root, "--out", self.home / "bad",
                 "link/before/report.json", success=False)

    def test_restore_existing_output_or_bundle_symlink_never_overwrites(self):
        packed = self.compress()
        out = self.home / "existing"
        out.mkdir()
        (out / "unrelated").write_bytes(b"keep")
        self.cli("restore", "--bundle", packed, "--out", out, success=False)
        self.assertEqual((out / "unrelated").read_bytes(), b"keep")
        gz = packed / (self.path + ".gz")
        gz.unlink()
        gz.symlink_to(self.root / self.path)
        self.cli("verify", "--bundle", packed, success=False)

    def test_generated_gzip_path_collision_is_explicitly_rejected(self):
        extra = self.root / (self.path + ".gz/child")
        extra.parent.mkdir(parents=True)
        extra.write_bytes(b"second")
        out = self.home / "packed"
        result = self.cli("compress", "--root", self.root, "--out", out,
                          "--remove-originals", self.path, self.path + ".gz/child",
                          success=False)
        self.assertIn("collision", result.stderr)
        self.assertFalse(out.exists())
        self.assertEqual((self.root / self.path).read_bytes(), self.raw)
        self.assertEqual(extra.read_bytes(), b"second")

    def test_symlink_root_and_destination_parent_are_rejected(self):
        link = self.home / "root-link"
        link.symlink_to(self.root, target_is_directory=True)
        self.cli("compress", "--root", link, "--out", self.home / "bad-root",
                 self.path, success=False)
        parent = self.home / "parent-link"
        parent.symlink_to(self.root, target_is_directory=True)
        self.cli("compress", "--root", self.root, "--out", parent / "bad-out",
                 self.path, success=False)
        packed = self.compress()
        self.cli("restore", "--bundle", packed, "--out", parent / "bad-restored",
                 success=False)
        self.assertFalse((self.root / "bad-restored").exists())

    def test_empty_file_and_multiple_explicit_targets_roundtrip(self):
        (self.root / "empty").write_bytes(b"")
        packed = self.home / "multiple"
        self.cli("compress", "--root", self.root, "--out", packed, self.path, "empty")
        restored = self.home / "restored"
        self.cli("restore", "--bundle", packed, "--out", restored)
        self.assertEqual((restored / "empty").read_bytes(), b"")
        self.assertEqual((restored / self.path).read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
