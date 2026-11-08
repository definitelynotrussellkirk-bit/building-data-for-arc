import contextlib
import hashlib
import io
import json
import stat
import struct
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import selective_zip


class SelectiveZipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "source.zip"
        self.destination = self.root / "extracted"

    def make_zip(self, members):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(self.archive, "w", compression=ZIP_DEFLATED) as archive:
                for name, payload in members:
                    archive.writestr(name, payload)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = selective_zip.main(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_extract_selected_subtree_preserves_bytes_and_reports_omissions(self):
        payload = bytes(range(256)) + b"\x00\r\n\xff"
        self.make_zip([
            ("packet/runtime/run.bin", payload),
            ("packet/runtime/history/old.bin", b"omit history"),
            ("packet/answers.json", b"omit answers"),
        ])
        original_archive = self.archive.read_bytes()
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination),
            "--include", "packet/runtime/",
            "--exclude", "packet/runtime/history/", "--json",
        )
        self.assertEqual(code, 0, err)
        self.assertEqual((self.destination / "packet/runtime/run.bin").read_bytes(), payload)
        self.assertFalse((self.destination / "packet/answers.json").exists())
        self.assertFalse((self.destination / "packet/runtime/history").exists())
        self.assertEqual(self.archive.read_bytes(), original_archive)
        report = json.loads(out)
        self.assertEqual(report["selected_members"], 1)
        self.assertEqual(report["omitted_members"], 2)
        self.assertEqual(report["extracted_files"], 1)

    def test_extraction_requires_explicit_selection(self):
        self.make_zip([("run.py", b"print(1)")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertIn("explicit", json.loads(out)["errors"][0])
        self.assertFalse(self.destination.exists())

    def test_include_and_all_cannot_be_combined(self):
        self.make_zip([("run.py", b"print(1)")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination),
            "--include", "run.py", "--all", "--json",
        )
        self.assertEqual(code, 2, err)
        self.assertFalse(self.destination.exists())

    def test_exact_selection_does_not_accidentally_include_subtree(self):
        self.make_zip([("run.py", b"first"), ("run.py.backup", b"second")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination),
            "--include", "run.py", "--json",
        )
        self.assertEqual(code, 0, err)
        self.assertFalse((self.destination / "run.py.backup").exists())

    def test_unmatched_include_is_rejected_before_writing(self):
        self.make_zip([("run.py", b"print(1)")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination),
            "--include", "wrong/", "--json",
        )
        self.assertEqual(code, 2, err)
        self.assertIn("matched no", " ".join(json.loads(out)["errors"]))
        self.assertFalse(self.destination.exists())

    def test_unsafe_paths_are_rejected_before_any_member_is_written(self):
        names = [
            "../escaped.txt", str(self.root / "absolute.txt"),
            "nested/../../escaped.txt", "nested\\escaped.txt",
            "C:/drive.txt", "nested/./file.txt", "nested//file.txt",
            "nested/trailing.", "nested/trailing ", "nested/CON.txt",
            "nested/data:stream", "nested/control\x01.txt",
        ]
        for index, name in enumerate(names):
            with self.subTest(name=name):
                destination = self.root / f"unsafe-{index}"
                self.make_zip([("first.txt", b"safe"), (name, b"unsafe")])
                code, out, err = self.run_cli(
                    "extract", str(self.archive), str(destination), "--all", "--json"
                )
                self.assertEqual(code, 2, err)
                self.assertFalse(destination.exists())
        self.assertFalse((self.root / "escaped.txt").exists())
        self.assertFalse((self.root / "absolute.txt").exists())

    def test_duplicate_and_portable_alias_paths_are_rejected(self):
        cases = [
            ["same.txt", "same.txt"],
            ["File.txt", "file.txt"],
            ["\u00e9.txt", "e\u0301.txt"],
            ["dir/one.txt", "DIR/two.txt"],
        ]
        for index, names in enumerate(cases):
            with self.subTest(names=names):
                destination = self.root / f"collision-{index}"
                self.make_zip([(name, b"one") for name in names])
                code, out, err = self.run_cli(
                    "extract", str(self.archive), str(destination), "--all", "--json"
                )
                self.assertEqual(code, 2, err)
                self.assertFalse(destination.exists())

    def test_symlink_and_special_members_are_rejected(self):
        for index, kind in enumerate([stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR]):
            with self.subTest(kind=kind):
                member = ZipInfo("special")
                member.create_system = 3
                member.external_attr = (kind | 0o777) << 16
                self.make_zip([(member, b"../somewhere")])
                destination = self.root / f"special-{index}"
                code, out, err = self.run_cli(
                    "extract", str(self.archive), str(destination), "--all", "--json"
                )
                self.assertEqual(code, 2, err)
                self.assertFalse(destination.exists())

    def test_symbolic_link_parent_is_rejected(self):
        self.make_zip([("file.txt", b"payload")])
        parent = self.root / "actual"
        parent.mkdir()
        link = self.root / "link"
        link.symlink_to(parent, target_is_directory=True)
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(link / "output"), "--all", "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertFalse((parent / "output").exists())

    def test_list_groups_central_directory_sizes_without_extraction(self):
        self.make_zip([
            ("packet/src/a.py", b"123"), ("packet/src/b.py", b"45"),
            ("packet/history/old", b"1234567"),
        ])
        code, out, err = self.run_cli("list", str(self.archive), "--depth", "2", "--json")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        groups = {group["path"]: group for group in report["groups"]}
        self.assertEqual(groups["packet/src"]["members"], 2)
        self.assertEqual(groups["packet/src"]["uncompressed_bytes"], 5)
        self.assertEqual(report["selected_uncompressed_bytes"], 12)
        self.assertFalse(self.destination.exists())

    def test_preflight_returns_storage_estimate_without_creating_destination(self):
        self.make_zip([("packet/src/a.py", b"one"), ("packet/src/b.py", b"two")])
        code, out, err = self.run_cli(
            "preflight", str(self.archive), str(self.destination), "--json"
        )
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertGreaterEqual(report["estimated_disk_bytes"], 6)
        self.assertEqual(report["estimated_inodes"], 5)
        self.assertGreater(report["free_disk_bytes"], 0)
        self.assertFalse(self.destination.exists())

    def test_byte_and_member_budgets_stop_extraction_before_writing(self):
        self.make_zip([("one", b"123"), ("two", b"456")])
        for option, value, word in [("--max-bytes", "5", "bytes"), ("--max-members", "1", "members")]:
            with self.subTest(option=option):
                code, out, err = self.run_cli(
                    "extract", str(self.archive), str(self.destination),
                    "--all", option, value, "--json",
                )
                self.assertEqual(code, 2, err)
                self.assertTrue(out, err)
                self.assertIn(word, " ".join(json.loads(out)["errors"]))
                self.assertFalse(self.destination.exists())

    def test_disk_reserve_failure_is_reported_before_writing(self):
        self.make_zip([("one", b"123")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination),
            "--all", "--reserve-bytes", str(10**30), "--json",
        )
        self.assertEqual(code, 2, err)
        self.assertTrue(out, err)
        self.assertIn("disk", " ".join(json.loads(out)["errors"]).lower())
        self.assertFalse(self.destination.exists())

    def test_existing_destination_is_never_modified(self):
        self.make_zip([("existing.txt", b"replace")])
        self.destination.mkdir()
        original = self.destination / "existing.txt"
        original.write_bytes(b"keep")
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertEqual(original.read_bytes(), b"keep")

    def test_file_parent_conflict_is_rejected_in_either_archive_order(self):
        for index, names in enumerate([["dir", "dir/file"], ["dir/file", "dir"]]):
            with self.subTest(names=names):
                self.make_zip([(name, b"one") for name in names])
                destination = self.root / f"parent-collision-{index}"
                code, out, err = self.run_cli(
                    "extract", str(self.archive), str(destination), "--all", "--json"
                )
                self.assertEqual(code, 2, err)
                self.assertFalse(destination.exists())

    def test_explicit_directories_can_follow_children(self):
        self.make_zip([("dir/file", b"one"), ("dir/", b"")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 0, err)
        self.assertEqual((self.destination / "dir/file").read_bytes(), b"one")

    def test_sha256_report_matches_extracted_bytes(self):
        payload = b"one\x00two\r\n"
        self.make_zip([("file.bin", payload)])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 0, err)
        records = json.loads(out).get("files", [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(records[0]["path"], "file.bin")
        self.assertEqual(records[0]["bytes"], len(payload))

    def test_corrupt_member_removes_partial_destination(self):
        # Stored bytes make the corruption deterministic without a decompressor.
        with ZipFile(self.archive, "w") as archive:
            archive.writestr("first.txt", b"safe first member")
            archive.writestr("second.txt", b"unique-corrupt-me")
        data = self.archive.read_bytes()
        self.archive.write_bytes(data.replace(b"unique-corrupt-me", b"unique-corrupt-ME", 1))
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertFalse(self.destination.exists(), "partial output must be removed after CRC failure")
        self.assertIn("CRC", " ".join(json.loads(out)["errors"]))

    def test_budget_failures_are_reported_even_when_paths_collide(self):
        self.make_zip([("A", b"123"), ("a", b"456")])
        code, out, err = self.run_cli(
            "preflight", str(self.archive), str(self.destination),
            "--max-bytes", "1", "--max-members", "1", "--json",
        )
        self.assertEqual(code, 2, err)
        errors = " ".join(json.loads(out)["errors"])
        self.assertIn("max-bytes", errors)
        self.assertIn("max-members", errors)
        self.assertIn("collision", errors)
        self.assertFalse(self.destination.exists())

    def test_excessive_path_depth_is_rejected_before_writing(self):
        self.make_zip([("/".join(["sub"] * 129) + "/file", b"one")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertFalse(self.destination.exists())

    def test_null_in_raw_member_name_is_rejected(self):
        self.make_zip([("nulXtail", b"one")])
        self.archive.write_bytes(self.archive.read_bytes().replace(b"nulXtail", b"nul\x00tail"))
        code, out, err = self.run_cli(
            "preflight", str(self.archive), str(self.destination), "--json"
        )
        self.assertEqual(code, 2, err)
        self.assertIn("Unsafe archive path", " ".join(json.loads(out)["errors"]))

    def test_encrypted_and_unsupported_methods_are_rejected_by_preflight(self):
        for kind in ("encrypted", "strong_encryption", "patched_data", "compression"):
            with self.subTest(kind=kind):
                self.make_zip([("file", b"one")])
                data = bytearray(self.archive.read_bytes())
                local = data.index(b"PK\x03\x04")
                central = data.index(b"PK\x01\x02")
                if kind != "compression":
                    forbidden_bit = {"encrypted": 1, "strong_encryption": 64, "patched_data": 32}[kind]
                    for offset in (local + 6, central + 8):
                        flags = struct.unpack_from("<H", data, offset)[0]
                        struct.pack_into("<H", data, offset, flags | forbidden_bit)
                else:
                    for offset in (local + 8, central + 10):
                        struct.pack_into("<H", data, offset, 99)
                self.archive.write_bytes(data)
                code, out, err = self.run_cli(
                    "preflight", str(self.archive), str(self.destination), "--json"
                )
                self.assertEqual(code, 2, err)
                self.assertFalse(self.destination.exists())

    def test_preflight_does_not_claim_to_check_payload_crc(self):
        with ZipFile(self.archive, "w") as archive:
            archive.writestr("file", b"unique-original")
        self.archive.write_bytes(self.archive.read_bytes().replace(b"unique-original", b"unique-corrupte", 1))
        code, out, err = self.run_cli(
            "preflight", str(self.archive), str(self.destination), "--json"
        )
        self.assertEqual(code, 0, err)
        self.assertFalse(json.loads(out)["selected_contents_verified"])
        self.assertFalse(self.destination.exists())

    def test_extracted_files_are_private_and_owner_execute_bit_is_retained(self):
        member = ZipInfo("run.sh")
        member.create_system = 3
        member.external_attr = (stat.S_IFREG | 0o6777) << 16
        self.make_zip([(member, b"#!/bin/sh\n")])
        code, out, err = self.run_cli(
            "extract", str(self.archive), str(self.destination), "--all", "--json"
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(stat.S_IMODE((self.destination / "run.sh").stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
