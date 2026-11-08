"""Small synthetic regressions found during the independent recovery review."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent


class RecoveryRegressionTests(unittest.TestCase):
    def test_corrupt_codecs_return_json_rejection_without_traceback(self):
        cases = ((zipfile.ZIP_DEFLATED, 0, 0x07),
                 (zipfile.ZIP_BZIP2, 0, 0x00),
                 (zipfile.ZIP_LZMA, 4, 0xFF))
        for compression, corrupt_offset, corrupt_byte in cases:
            with self.subTest(compression=compression):
                with tempfile.TemporaryDirectory(prefix="review-regression-", dir=HERE) as directory:
                    root = Path(directory)
                    archive = root / "corrupt.zip"
                    members = {
                        "START-HERE.md": b"Synthetic recovery test.\n",
                        "review.py": b"This fixture is never executed.\n",
                        "WORK/data.txt": b"Synthetic payload.\n",
                    }
                    digest = lambda data: hashlib.sha256(data).hexdigest()
                    manifest = {
                        "schema": "arcpuzzles-full-packet-v2",
                        "layout": {
                            "workspace": "WORK",
                            "entry_files": {name: digest(members[name]) for name in ("START-HERE.md", "review.py")},
                        },
                        "files": {"data.txt": digest(members["WORK/data.txt"])},
                    }
                    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
                    with zipfile.ZipFile(archive, "w", compression=compression) as zipped:
                        for name, data in members.items():
                            zipped.writestr(name, data)
                        zipped.writestr("WORK/PACKET-MANIFEST.json", encoded)
                    with zipfile.ZipFile(archive) as zipped:
                        header = zipped.getinfo("START-HERE.md").header_offset
                    damaged = bytearray(archive.read_bytes())
                    name_size, extra_size = struct.unpack_from("<HH", damaged, header + 26)
                    # Damage only compressed payload; retain the ZIP directory and manifest.
                    damaged[header + 30 + name_size + extra_size + corrupt_offset] = corrupt_byte
                    archive.write_bytes(damaged)
                    result = subprocess.run(
                        [sys.executable, "-B", str(HERE / "arc_packet_recover.py"), "verify", str(archive)],
                        cwd=root, capture_output=True, text=True, check=False, timeout=30,
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertTrue(result.stdout.strip(), result.stderr)
                    receipt = json.loads(result.stdout)
                    self.assertEqual(receipt["status"], "rejected")
                    self.assertEqual(receipt["code"], "invalid_archive")
                    self.assertNotIn("Traceback", result.stderr)


    def test_report_symlink_loop_preserves_primary_json_result(self):
        with tempfile.TemporaryDirectory(prefix="review-report-", dir=HERE) as directory:
            root = Path(directory)
            archive = root / "valid.zip"
            members = {"START-HERE.md": b"fixture", "review.py": b"fixture", "WORK/data.txt": b"fixture"}
            digest = hashlib.sha256(b"fixture").hexdigest()
            manifest = {
                "schema": "arcpuzzles-full-packet-v2",
                "layout": {"workspace": "WORK", "entry_files": {"START-HERE.md": digest, "review.py": digest}},
                "files": {"data.txt": digest},
            }
            encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
                for name, data in members.items():
                    zipped.writestr(name, data)
                zipped.writestr("WORK/PACKET-MANIFEST.json", encoded)
            report = root / "receipt-loop.json"
            report.symlink_to(report.name)
            result = subprocess.run(
                [sys.executable, "-B", str(HERE / "arc_packet_recover.py"), "verify", str(archive), "--report", str(report)],
                cwd=root, capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "verified")
            warning = json.loads(result.stderr)
            self.assertIs(warning["report_saved"], False)
            self.assertEqual(warning["primary_exit_code"], 0)
            self.assertTrue(report.is_symlink())
            self.assertEqual(report.readlink(), Path(report.name))



    def test_archive_symlink_loop_keeps_error_json_when_saving_report(self):
        with tempfile.TemporaryDirectory(prefix="review-source-loop-", dir=HERE) as directory:
            root = Path(directory)
            archive = root / "loop.zip"
            archive.symlink_to(archive.name)
            report = root / "report.json"
            result = subprocess.run(
                [sys.executable, "-B", str(HERE / "arc_packet_recover.py"), "verify", str(archive), "--report", str(report)],
                capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            primary = json.loads(result.stdout)
            self.assertEqual(primary["code"], "io_error")
            self.assertEqual(json.loads(report.read_text()), primary)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
