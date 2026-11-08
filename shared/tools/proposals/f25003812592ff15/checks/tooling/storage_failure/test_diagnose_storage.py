"""Focused behavior tests for ENOSPC evidence, not filesystem mutations."""
import errno
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("diagnose_storage.py")


class StorageDiagnosisTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), "The requested diagnosis CLI is not implemented")
        spec = importlib.util.spec_from_file_location("storage_diagnosis", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_classifies_each_measured_exhaustion_and_incomplete_evidence(self):
        module = self.module()
        for available_bytes, available_inodes, expected in (
            (0, 5, "bytes"), (14 * 1024**3, 0, "inodes"), (0, 0, "both"),
            (1024, 5, "neither"), (1024, None, "unknown"),
            (None, None, "unknown"), (0, None, "bytes"), (None, 0, "inodes"),
        ):
            with self.subTest(bytes=available_bytes, inodes=available_inodes):
                self.assertEqual(module.classify_enospc(available_bytes, available_inodes), expected)

    def test_fragment_size_and_available_counts_drive_diagnosis(self):
        module = self.module()
        stats = SimpleNamespace(f_bsize=8192, f_frsize=4096, f_bfree=100,
                                f_bavail=2, f_files=100, f_ffree=5, f_favail=0)
        with patch.object(module.os, "statvfs", return_value=stats):
            report = module.diagnose_path("existing-path")
        self.assertEqual(report["block_size_bytes"], 8192)
        self.assertEqual(report["fragment_size_bytes"], 4096)
        self.assertEqual(report["free_bytes"], 409600)
        self.assertEqual(report["available_bytes"], 8192)
        self.assertEqual(report["free_inodes"], 5)
        self.assertEqual(report["available_inodes"], 0)
        self.assertEqual(report["enospc_explanation"], "inodes")

    def test_unreported_inode_capacity_is_not_claimed_exhausted(self):
        module = self.module()
        stats = SimpleNamespace(f_bsize=4096, f_frsize=0, f_bfree=100,
                                f_bavail=100, f_files=0, f_ffree=0, f_favail=0)
        with patch.object(module.os, "statvfs", return_value=stats):
            report = module.diagnose_path("existing-path")
        self.assertIsNone(report["available_inodes"])
        self.assertIsNone(report["free_inodes"])
        self.assertEqual(report["available_bytes"], 409600)
        self.assertEqual(report["enospc_explanation"], "unknown")

    def test_statvfs_error_is_returned_with_errno_and_unknown_diagnosis(self):
        module = self.module()
        with patch.object(module.os, "statvfs", side_effect=OSError(errno.EACCES, "denied")):
            report = module.diagnose_path("inaccessible-path")
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["error"]["errno"], errno.EACCES)
        self.assertEqual(report["enospc_explanation"], "unknown")

    def test_statvfs_unavailable_is_reported_honestly(self):
        module = self.module()
        with patch.object(module.os, "statvfs", None):
            report = module.diagnose_path("existing-path")
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["enospc_explanation"], "unknown")

    def test_cli_mixed_success_and_error_still_emits_parseable_json(self):
        self.module()
        missing = SCRIPT.parent / "__missing_storage_diagnosis_path__"
        self.assertFalse(missing.exists())
        process = subprocess.run([sys.executable, str(SCRIPT), str(SCRIPT.parent), str(missing)],
                                 text=True, capture_output=True)
        self.assertEqual(process.returncode, 1)
        payload = json.loads(process.stdout)
        self.assertEqual(len(payload["paths"]), 2)
        self.assertEqual(payload["paths"][0]["status"], "ok")
        self.assertEqual(payload["paths"][1]["status"], "error")


if __name__ == "__main__":
    unittest.main()
