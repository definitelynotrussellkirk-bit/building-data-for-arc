"""Synthetic CLI integration tests; never opens the real ARCpuzzles source ZIP."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

SCRIPT = Path(__file__).with_name("packet_zip.py")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


class PacketZipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="packet-zip-tests-")
        self.root = Path(self.temp.name)
        self.source = self.root / "packet.zip"
        self.bodies = {
            "START-HERE.md": b"Start with the authentic entrypoint.\n",
            "review.py": b"# synthetic entrypoint; never executed\n",
            "WORK/repo/src/arcpuzzles/__init__.py": b"value = 42\n",
            "WORK/repo/generators/example/generator.py": b"# synthetic withheld body\n",
        }
        self.manifest = {
            "schema": "arcpuzzles-full-packet-v2",
            "layout": {"workspace": "WORK", "entry_files": {
                n: hashlib.sha256(self.bodies[n]).hexdigest() for n in ("START-HERE.md", "review.py")}},
            "files": {n.removeprefix("WORK/"): hashlib.sha256(raw).hexdigest()
                      for n, raw in self.bodies.items() if n.startswith("WORK/")},
        }
        self.bodies["WORK/PACKET-MANIFEST.json"] = canonical(self.manifest)
        self.write_zip()

    def tearDown(self):
        self.temp.cleanup()

    def write_zip(self, extra=()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.source, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, raw in self.bodies.items():
                    archive.writestr(name, raw)
                for name, raw in extra:
                    archive.writestr(name, raw)

    def run_cli(self, command, *args):
        return subprocess.run([sys.executable, str(SCRIPT), command, str(self.source), *map(str, args)],
                              text=True, capture_output=True, timeout=15)

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_inspect_does_not_claim_body_verification(self):
        data = self.ok(self.run_cli("inspect"))
        self.assertEqual(data["archive_file_count"], 5)
        self.assertEqual(data["body_hashes_verified"], 0)
        self.assertTrue(data["archive_inventory_matches_manifest"])

    def test_partial_materialization_preserves_exact_bytes_and_manifest(self):
        out = self.root / "partial"
        data = self.ok(self.run_cli("materialize", "--prefix", "WORK/repo/src", "--out", out))
        self.assertEqual(data["status"], "complete")
        self.assertEqual(data["selected_file_count"], 4)
        self.assertEqual(data["omitted_file_count"], 1)
        self.assertFalse(data["full_original_packet_extracted"])
        self.assertEqual(data["verified_file_count"], 4)
        for name in ("START-HERE.md", "review.py", "WORK/PACKET-MANIFEST.json", "WORK/repo/src/arcpuzzles/__init__.py"):
            self.assertEqual((out / "checkout" / name).read_bytes(), self.bodies[name])
        self.assertFalse((out / "checkout/WORK/repo/generators").exists())
        self.assertEqual(json.loads((out / "receipt.json").read_text()), data)

    def test_missing_selector_is_an_error_before_any_output_is_created(self):
        out = self.root / "missing"
        result = self.run_cli("materialize", "--member", "WORK/no-such-file", "--out", out)
        self.assertEqual(result.returncode, 2)
        self.assertIn("WORK/no-such-file", result.stderr)
        self.assertFalse(out.exists())

    def test_no_selection_never_silently_extracts_everything(self):
        result = self.run_cli("plan")
        self.assertEqual(result.returncode, 2)
        self.assertIn("selection", result.stderr.lower())

    def test_selected_corruption_records_failure_not_completion(self):
        self.bodies["WORK/repo/src/arcpuzzles/__init__.py"] = b"corrupted"
        self.write_zip()
        out = self.root / "corrupt"
        result = self.run_cli("materialize", "--prefix", "WORK/repo/src", "--out", out)
        self.assertEqual(result.returncode, 1)
        data = json.loads((out / "receipt.json").read_text())
        self.assertEqual(data["status"], "failed")
        self.assertIn("SHA-256", data["error"])

    def test_all_archive_verification_finds_corruption_outside_partial_scope(self):
        self.bodies["WORK/repo/generators/example/generator.py"] = b"corrupted"
        self.write_zip()
        selected = self.ok(self.run_cli("verify", "--prefix", "WORK/repo/src"))
        self.assertEqual(selected["verified_file_count"], 4)
        result = self.run_cli("verify", "--all")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["failure_count"], 1)
        self.assertEqual(data["failures"][0]["path"], "WORK/repo/generators/example/generator.py")

    def test_checkout_verification_reports_omitted_original_files_as_missing(self):
        out = self.root / "partial"
        self.ok(self.run_cli("materialize", "--prefix", "WORK/repo/src", "--out", out))
        result = self.run_cli("verify", "--all", "--checkout", out / "checkout")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["failure_count"], 1)
        self.assertIn("missing", data["failures"][0]["error"].lower())

    def test_unsafe_paths_are_rejected_even_when_unselected(self):
        for name in ("../escape", "/absolute", "WORK/../escape", "WORK\\escape", "C:/escape", "WORK/./dot"):
            with self.subTest(name=name):
                self.write_zip(extra=[(name, b"x")])
                result = self.run_cli("plan", "--prefix", "WORK/repo/src")
                self.assertEqual(result.returncode, 2)
                self.assertIn("unsafe", result.stderr.lower())

    def test_zip_symlink_is_rejected(self):
        link = zipfile.ZipInfo("WORK/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.write_zip(extra=[(link, b"/tmp/target")])
        result = self.run_cli("inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("type", result.stderr.lower())

    def test_duplicate_member_is_rejected(self):
        self.write_zip(extra=[("review.py", b"second value")])
        result = self.run_cli("inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate", result.stderr.lower())

    def test_missing_manifest_member_is_rejected(self):
        del self.bodies["WORK/repo/src/arcpuzzles/__init__.py"]
        self.write_zip()
        result = self.run_cli("inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("WORK/repo/src/arcpuzzles/__init__.py", result.stderr)

    def test_manifest_file_keys_cannot_silently_normalize_directory_names(self):
        key = "repo/src/arcpuzzles/__init__.py"
        self.manifest["files"][key + "/"] = self.manifest["files"].pop(key)
        self.bodies["WORK/PACKET-MANIFEST.json"] = canonical(self.manifest)
        self.write_zip()
        result = self.run_cli("inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("file", result.stderr.lower())

    def test_noncanonical_manifest_is_rejected(self):
        self.bodies["WORK/PACKET-MANIFEST.json"] += b"\n"
        self.write_zip()
        result = self.run_cli("inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("canonical", result.stderr.lower())

    def test_member_list_selects_exact_files_with_no_implicit_siblings(self):
        names = self.root / "members.txt"
        names.write_text("# exact runtime closure\nWORK/repo/src/arcpuzzles/__init__.py\n", encoding="utf-8")
        data = self.ok(self.run_cli("plan", "--members-file", names))
        self.assertEqual({row["path"] for row in data["selected_files"]}, {
            "WORK/repo/src/arcpuzzles/__init__.py", "START-HERE.md", "review.py", "WORK/PACKET-MANIFEST.json"})

    def test_budget_rejection_happens_before_destination_creation(self):
        out = self.root / "limited"
        result = self.run_cli("materialize", "--all", "--max-bytes", "1", "--out", out)
        self.assertEqual(result.returncode, 2)
        self.assertIn("budget", result.stderr.lower())
        self.assertFalse(out.exists())

    def test_existing_destination_is_never_overwritten(self):
        out = self.root / "existing"
        out.mkdir()
        (out / "sentinel").write_bytes(b"keep me")
        result = self.run_cli("materialize", "--all", "--out", out)
        self.assertEqual(result.returncode, 2)
        self.assertIn("destination", result.stderr.lower())
        self.assertEqual((out / "sentinel").read_bytes(), b"keep me")
        self.assertEqual(list(out.iterdir()), [out / "sentinel"])

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks unavailable")
    def test_destination_with_symlink_ancestor_is_rejected(self):
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        link.symlink_to(real, target_is_directory=True)
        result = self.run_cli("materialize", "--all", "--out", link / "output")
        self.assertEqual(result.returncode, 2)
        self.assertIn("symlink", result.stderr.lower())
        self.assertFalse((real / "output").exists())


if __name__ == "__main__":
    unittest.main()
