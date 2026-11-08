"""Exercise the verifier against real ZIP files, including hostile inventories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
import zlib


SCRIPT = Path(__file__).with_name("verify_packet_zip.py")
SCHEMA = "arcpuzzles-full-packet-v2"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_members(*, workspace=True):
    files = {
        "repo/README.md": "A small synthetic packet: snowman ☃.\n".encode(),
        "repo/src/example.py": b"raise RuntimeError('Archive code must never execute')\n",
    }
    manifest = {"schema": SCHEMA, "files": {name: sha(raw) for name, raw in files.items()}}
    prefix = "WORK/" if workspace else ""
    members = [(prefix + name, raw, stat.S_IFREG | 0o644) for name, raw in files.items()]
    if workspace:
        entries = {"START-HERE.md": b"Synthetic start.\n", "review.py": b"raise RuntimeError('Do not import')\n"}
        manifest["layout"] = {"workspace": "WORK", "entry_files": {name: sha(raw) for name, raw in entries.items()}}
        members.extend((name, raw, stat.S_IFREG | 0o644) for name, raw in entries.items())
    members.append((prefix + "PACKET-MANIFEST.json", canonical(manifest), stat.S_IFREG | 0o644))
    return members, manifest


def write_zip(path, members, *, compression=zipfile.ZIP_STORED):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, raw, mode in members:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = mode << 16
                info.compress_type = compression
                archive.writestr(info, raw)
    return path


def run_cli(path, *args):
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), *args],
                            cwd=path.parent, capture_output=True, text=True)
    assert result.stdout.strip().startswith("{"), f"Expected JSON report; exit={result.returncode}, stderr={result.stderr!r}"
    return result, json.loads(result.stdout)


def assert_rejected(path, code, *args):
    result, report = run_cli(path, *args)
    assert result.returncode == 1
    assert report["status"] == "failed"
    assert report["errors"][0]["code"] == code
    return report


def replace_manifest(members, manifest, *, workspace=True):
    name = ("WORK/" if workspace else "") + "PACKET-MANIFEST.json"
    return [(key, canonical(manifest) if key == name else raw, mode) for key, raw, mode in members]


def header_offsets(path, member):
    """Locate real fixture headers so a malformed producer can be simulated."""
    with zipfile.ZipFile(path) as archive:
        local = archive.getinfo(member).header_offset
        central = archive.start_dir
    data = bytearray(path.read_bytes())
    while data[central:central + 4] == b"PK\x01\x02":
        name_length, extra_length, comment_length = struct.unpack_from("<HHH", data, central + 28)
        name = bytes(data[central + 46:central + 46 + name_length]).decode("utf-8")
        if name == member:
            return data, local, central
        central += 46 + name_length + extra_length + comment_length
    raise AssertionError("Fixture member's central header not found")


class PacketZipTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="packet-zip-test-")
        self.addCleanup(directory.cleanup)
        self.tmp_path = Path(directory.name)

    def test_valid_workspace_is_verified_without_extraction_or_source_execution(self):
        members, manifest = fixture_members()
        path = write_zip(self.tmp_path / "packet.zip", members)
        before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns, sha(p.read_bytes())) for p in self.tmp_path.iterdir()}
        result, report = run_cli(path, "--expected-manifest-sha256", sha(canonical(manifest)))
        after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns, sha(p.read_bytes())) for p in self.tmp_path.iterdir()}
        assert result.returncode == 0
        assert result.stderr == ""
        assert report["status"] == "verified"
        assert report["manifest_file_count"] == 2
        assert report["outer_file_count"] == 2
        assert report["verified_file_count"] == 4
        assert report["member_count"] == 5
        assert report["expanded_bytes"] == sum(len(raw) for _, raw, _ in members)
        assert report["archive_sha256"] == sha(path.read_bytes())
        assert report["manifest_sha256"] == sha(canonical(manifest))
        assert before == after

    def test_flat_packet_is_supported(self):
        members, _ = fixture_members(workspace=False)
        result, report = run_cli(write_zip(self.tmp_path / "packet.zip", members))
        assert result.returncode == 0
        assert report["manifest_member"] == "PACKET-MANIFEST.json"
        assert report["outer_file_count"] == 0
        assert report["verified_file_count"] == 2

    def test_unsafe_member_paths_are_rejected(self):
        for name in ["../outside", "/absolute", "WORK/../outside", "WORK\\evil", "WORK//evil", "WORK/./evil", "C:/evil"]:
            with self.subTest(name=name):
                members, _ = fixture_members()
                members.append((name, b"untrusted", stat.S_IFREG | 0o644))
                assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "unsafe_member_path")

    def test_unsafe_manifest_paths_are_rejected(self):
        for name in ["../outside", "/absolute", "repo/../../outside", "repo\\evil", "repo//evil"]:
            with self.subTest(name=name):
                members, manifest = fixture_members()
                manifest["files"][name] = sha(b"untrusted")
                assert_rejected(write_zip(self.tmp_path / "packet.zip", replace_manifest(members, manifest)), "unsafe_manifest_path")

    def test_duplicate_archive_members_are_rejected_even_with_identical_bytes(self):
        members, _ = fixture_members()
        members.append(members[0])
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "duplicate_member")

    def test_nonregular_members_are_rejected_even_with_matching_hash(self):
        for mode in [stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o644, stat.S_IFCHR | 0o644]:
            with self.subTest(mode=mode):
                members, _ = fixture_members()
                name, raw, _ = members[0]
                members[0] = (name, raw, mode)
                assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "unsafe_member_type")

    def test_unlisted_file_is_rejected(self):
        members, _ = fixture_members()
        members.append(("WORK/repo/unlisted.py", b"extra", stat.S_IFREG | 0o644))
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "unexpected_member")

    def test_missing_manifest_file_is_rejected(self):
        members, _ = fixture_members()
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members[1:]), "missing_member")

    def test_modified_payload_and_outer_entry_are_rejected(self):
        for name in ["WORK/repo/README.md", "review.py"]:
            with self.subTest(name=name):
                members, _ = fixture_members()
                members = [(key, raw + b"changed" if key == name else raw, mode) for key, raw, mode in members]
                assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "hash_mismatch")

    def test_noncanonical_manifest_is_rejected(self):
        members, _ = fixture_members()
        members = [(name, raw + b"\n" if name.endswith("PACKET-MANIFEST.json") else raw, mode) for name, raw, mode in members]
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "noncanonical_manifest")

    def test_wrong_manifest_schema_is_rejected(self):
        members, manifest = fixture_members()
        manifest["schema"] = "not-an-arcpuzzles-packet"
        assert_rejected(write_zip(self.tmp_path / "packet.zip", replace_manifest(members, manifest)), "manifest_schema")

    def test_invalid_digest_in_manifest_is_rejected(self):
        members, manifest = fixture_members()
        manifest["files"]["repo/README.md"] = "not-a-sha256"
        assert_rejected(write_zip(self.tmp_path / "packet.zip", replace_manifest(members, manifest)), "manifest_inventory")

    def test_manifest_pin_binds_the_issued_identity(self):
        members, _ = fixture_members()
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "manifest_pin_mismatch", "--expected-manifest-sha256", "0" * 64)

    def test_manifest_location_must_be_unambiguous(self):
        for change in ["missing", "ambiguous"]:
            with self.subTest(change=change):
                members, manifest = fixture_members()
                if change == "missing":
                    members = [m for m in members if not m[0].endswith("PACKET-MANIFEST.json")]
                else:
                    members.append(("PACKET-MANIFEST.json", canonical(manifest), stat.S_IFREG | 0o644))
                assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "manifest_location")

    def test_workspace_outer_inventory_is_exact(self):
        members, manifest = fixture_members()
        del manifest["layout"]["entry_files"]["review.py"]
        assert_rejected(write_zip(self.tmp_path / "packet.zip", replace_manifest(members, manifest)), "manifest_layout")

    def test_declared_expansion_budget_is_enforced(self):
        members, _ = fixture_members()
        assert_rejected(write_zip(self.tmp_path / "packet.zip", members), "expanded_size_limit", "--max-expanded-bytes", "1")

    def test_invalid_zip_is_reported_as_json(self):
        path = self.tmp_path / "broken.zip"
        path.write_bytes(b"not a zip archive")
        assert_rejected(path, "invalid_zip")

    def test_crc_corruption_is_detected_while_streaming(self):
        members, _ = fixture_members()
        path = write_zip(self.tmp_path / "packet.zip", members)
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("WORK/repo/README.md")
            offset = info.header_offset
        data = bytearray(path.read_bytes())
        name_length, extra_length = struct.unpack_from("<HH", data, offset + 26)
        data[offset + 30 + name_length + extra_length] ^= 1
        path.write_bytes(data)
        assert_rejected(path, "invalid_zip")

    def test_understated_sizes_cannot_hide_unhashed_source_or_manifest_bytes(self):
        for compression in [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED]:
            for target in ["WORK/repo/README.md", "WORK/PACKET-MANIFEST.json"]:
                with self.subTest(compression=compression, target=target):
                    members, manifest = fixture_members()
                    if target == "WORK/repo/README.md":
                        prefix = b"OK"
                        manifest["files"]["repo/README.md"] = sha(prefix)
                        members = replace_manifest(members, manifest)
                    else:
                        prefix = canonical(manifest)
                    members = [(name, prefix + b" hidden bytes" if name == target else raw, mode)
                               for name, raw, mode in members]
                    path = write_zip(self.tmp_path / "packet.zip", members, compression=compression)
                    data, local, central = header_offsets(path, target)
                    for offset in [local + 14, central + 16]:
                        struct.pack_into("<I", data, offset, zlib.crc32(prefix))
                    for offset in [local + 22, central + 24]:
                        struct.pack_into("<I", data, offset, len(prefix))
                    path.write_bytes(data)
                    assert_rejected(path, "member_size_mismatch", "--expected-manifest-sha256", sha(canonical(manifest)))

    def test_malformed_utf8_member_name_returns_a_json_failure(self):
        members, _ = fixture_members()
        path = write_zip(self.tmp_path / "packet.zip", members)
        data, local, central = header_offsets(path, "WORK/repo/README.md")
        for offset in [local + 6, central + 8]:
            flags = struct.unpack_from("<H", data, offset)[0]
            struct.pack_into("<H", data, offset, flags | 0x800)
        data[local + 30] = 0xff
        data[central + 46] = 0xff
        path.write_bytes(data)
        assert_rejected(path, "invalid_zip")


if __name__ == "__main__":
    unittest.main()
