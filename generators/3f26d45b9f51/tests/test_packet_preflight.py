"""Synthetic, stdlib-only regressions for the proposed read-only preflight."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import contextlib
import tempfile
import unittest
import warnings
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "workspace/packet_preflight.py"

class PreflightTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SOURCE.is_file(), "preflight implementation is missing")
        spec = importlib.util.spec_from_file_location("packet_preflight", SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def packet(self, payload=b"abc", expected=None, extra=(), omitted=False, outer_payload=b"entry"):
        digest = lambda b: hashlib.sha256(b).hexdigest()
        manifest = {"files": {"repo/a.txt": digest(payload if expected is None else expected)},
                    "layout": {"entry_files": {"review.py": digest(b"entry")}}}
        stream = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("WORK/PACKET-MANIFEST.json", json.dumps(manifest))
                if not omitted:
                    z.writestr("WORK/repo/a.txt", payload)
                z.writestr("review.py", outer_payload)
                for name, content in extra:
                    z.writestr(name, content)
        stream.seek(0)
        return stream

    def test_valid_inventory_counts_unique_parents_and_hashes(self):
        m = self.module()
        report = m.verify_packet(self.packet())
        self.assertEqual(report["files"], 3)
        self.assertEqual(report["directories"], 2)
        self.assertEqual(report["required_inodes"], 5)
        self.assertEqual(report["outer_entry_sha256"]["review.py"], hashlib.sha256(b"entry").hexdigest())
        self.assertGreater(report["expanded_bytes"], 8)

    def test_corrupt_compressed_stream_has_packet_error(self):
        m = self.module()
        data = bytearray(self.packet().getvalue())
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo("WORK/repo/a.txt")
            offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
        data[offset] = 255  # reserved DEFLATE block type
        with self.assertRaises(m.PacketError):
            m.verify_packet(io.BytesIO(data))

    def test_payload_tamper_rejected(self):
        m = self.module()
        with self.assertRaises(m.PacketError):
            m.verify_packet(self.packet(expected=b"different"))

    def test_outer_tamper_rejected(self):
        m = self.module()
        with self.assertRaises(m.PacketError):
            m.verify_packet(self.packet(outer_payload=b"changed"))

    def test_missing_and_unlisted_members_rejected(self):
        m = self.module()
        for packet in (self.packet(omitted=True), self.packet(extra=[("WORK/unlisted", b"x")])):
            with self.assertRaises(m.PacketError):
                m.verify_packet(packet)

    def test_unsafe_paths_duplicates_and_collisions_rejected(self):
        m = self.module()
        for name in ("../escape", "/absolute", "C:/drive", "WORK/../x", "WORK\\x", "WORK//x", "WORK/./x", "WORK/repo/a.txt", "WORK/repo/a.txt/child"):
            with self.subTest(name=name), self.assertRaises(m.PacketError):
                m.verify_packet(self.packet(extra=[(name, b"x")]))

    def test_symlink_and_special_file_rejected(self):
        m = self.module()
        for mode in (stat.S_IFLNK, stat.S_IFIFO):
            info = zipfile.ZipInfo("WORK/special")
            info.create_system = 3
            info.external_attr = (mode | 0o644) << 16
            with self.assertRaises(m.PacketError):
                m.verify_packet(self.packet(extra=[(info, b"target")]))

    def test_expansion_limits_rejected(self):
        m = self.module()
        for limits in ({"max_entry_bytes": 2}, {"max_total_bytes": 2}):
            with self.assertRaises(m.PacketError):
                m.verify_packet(self.packet(), **limits)

    def test_cli_tamper_and_io_exit_codes_are_json(self):
        m = self.module()
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as directory:
            packet = Path(directory) / "packet.zip"
            packet.write_bytes(self.packet(expected=b"wrong").getvalue())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = m.main([str(packet), directory])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "invalid_packet")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = m.main([str(packet), directory + "/missing"])
            self.assertEqual(code, 4)
            self.assertEqual(json.loads(output.getvalue())["status"], "io_error")

    def test_capacity_checks_inodes_bytes_and_readonly(self):
        m = self.module()
        report = {"expanded_bytes": 10, "required_inodes": 5, "file_sizes": [1, 9], "directories": 3}
        good = m.capacity_report(report, free_bytes=100, free_inodes=5, block_size=4, readonly=False)
        self.assertEqual(good["required_allocated_bytes"], 28)
        self.assertTrue(good["sufficient"])
        for kw in ({"free_bytes": 27}, {"free_inodes": 4}, {"readonly": True}):
            args = dict(free_bytes=100, free_inodes=5, block_size=4, readonly=False)
            args.update(kw)
            self.assertFalse(m.capacity_report(report, **args)["sufficient"])

if __name__ == "__main__":
    unittest.main()
