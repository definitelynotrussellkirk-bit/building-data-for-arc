"""Focused stdlib tests; all synthetic ZIPs are temporary and never retained."""
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile
from verify_packet_zip import verify_packet


def sha(value):
    return hashlib.sha256(value).hexdigest()


class PacketVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arc-zip-test-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "packet.zip"

    def packet(self, *, omit=(), change=None, extra=None, noncanonical=False,
               manifest_path="repo/example.txt", symlink=False):
        payloads = {"START-HERE.md": b"entry guide", "review.py": b"raise RuntimeError('ARCHIVE CODE MUST NEVER RUN')",
                    "WORK/repo/example.txt": b"small payload"}
        manifest = {"schema": "arcpuzzles-full-packet-v2",
                    "layout": {"workspace": "WORK", "entry_files": {n: sha(payloads[n]) for n in ("START-HERE.md", "review.py")}},
                    "files": {manifest_path: sha(payloads["WORK/repo/example.txt"])}}
        raw = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        if noncanonical:
            raw += b"\n"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("WORK/PACKET-MANIFEST.json", raw)
                for name, data in payloads.items():
                    if name in omit:
                        continue
                    if change and name in change:
                        data = change[name]
                    if symlink and name == "WORK/repo/example.txt":
                        info = zipfile.ZipInfo(name)
                        info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        z.writestr(info, data)
                    else:
                        z.writestr(name, data)
                if extra:
                    z.writestr(*extra)
        return verify_packet(self.path)

    def test_valid_hashes_both_root_entries_and_workspace(self):
        result = self.packet()
        self.assertTrue(result["verified"])
        self.assertEqual(result["counts"]["matched_required_files"], 3)
        self.assertEqual(result["counts"]["files"], 4)
        self.assertEqual(result["counts"]["directories_including_implicit"], 2)

    def test_missing_workspace_file(self):
        result = self.packet(omit={"WORK/repo/example.txt"})
        self.assertFalse(result["verified"])
        self.assertIn("WORK/repo/example.txt", result["missing"])

    def test_changed_workspace_bytes(self):
        result = self.packet(change={"WORK/repo/example.txt": b"changed"})
        self.assertFalse(result["verified"])
        self.assertEqual(result["changed"][0]["path"], "WORK/repo/example.txt")

    def test_changed_root_entry_bytes(self):
        result = self.packet(change={"review.py": b"changed"})
        self.assertFalse(result["verified"])
        self.assertEqual(result["changed"][0]["path"], "review.py")

    def test_duplicate_member(self):
        result = self.packet(extra=("WORK/repo/example.txt", b"duplicate"))
        self.assertFalse(result["verified"])
        self.assertEqual(result["duplicates"], [{"path": "WORK/repo/example.txt", "occurrences": 2}])

    def test_unsafe_archive_path(self):
        result = self.packet(extra=("../escape", b"not extracted"))
        self.assertFalse(result["verified"])
        self.assertTrue(any(x["path"] == "../escape" for x in result["unsafe"]))
        self.assertFalse((Path(self.temp.name).parent / "escape").exists())

    def test_unsafe_manifest_path(self):
        result = self.packet(manifest_path="../escape")
        self.assertFalse(result["verified"])
        self.assertTrue(any(x["reason"].startswith("manifest:") for x in result["unsafe"]))

    def test_symlink_member(self):
        result = self.packet(symlink=True)
        self.assertFalse(result["verified"])
        self.assertTrue(any("symlink" in x["reason"] for x in result["unsafe"]))

    def test_noncanonical_manifest(self):
        result = self.packet(noncanonical=True)
        self.assertFalse(result["verified"])
        self.assertIn("Manifest encoding is not canonical JSON", result["manifest_errors"])

    def test_unlisted_safe_file_matches_official_scope(self):
        result = self.packet(extra=("unused.txt", b"unlisted"))
        self.assertTrue(result["verified"])
        self.assertEqual(result["unlisted_files"], ["unused.txt"])
        self.assertEqual(result["counts"]["hashed_required_files"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
