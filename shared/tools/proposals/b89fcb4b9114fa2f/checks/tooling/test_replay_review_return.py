"""Synthetic regression tests; no issued task source or returned code is executed."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

import replay_review_return as replay_helper


GIT = shutil.which("git")
TASK_PATH = "repo/generators/example/generator.py"
BEFORE = b"answer = 'before'\n"
AFTER = b"answer = 'after'\n"
PATCH = (
    f"diff --git a/{TASK_PATH} b/{TASK_PATH}\n"
    f"--- a/{TASK_PATH}\n"
    f"+++ b/{TASK_PATH}\n"
    "@@ -1 +1 @@\n"
    "-answer = 'before'\n"
    "+answer = 'after'\n"
).encode()
HELPER = Path(__file__).with_name("replay_review_return.py")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_zip(path, members):
    with warnings.catch_warnings(), zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        warnings.simplefilter("ignore", UserWarning)  # Intentional duplicate-member fixtures.
        for name, raw in members:
            info = name if isinstance(name, zipfile.ZipInfo) else zipfile.ZipInfo(name)
            if not isinstance(name, zipfile.ZipInfo):
                info.external_attr = (0o40755 if info.is_dir() else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)


def git_env():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0")
    return env


class MetadataArchive:
    """Metadata-only stand-in; budget tests allocate no expanded member content."""
    def __init__(self, infos):
        self.infos = infos

    def infolist(self):
        return self.infos


def metadata_members(count, expanded_bytes):
    base, extra = divmod(expanded_bytes, count)
    infos = []
    for index in range(count):
        info = zipfile.ZipInfo(f"repo/metadata-{index}.txt")
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        info.file_size = base + (index < extra)
        infos.append(info)
    return infos


class ZipBudgetTests(unittest.TestCase):
    def test_original_limits_accept_observed_packet_scale(self):
        infos = metadata_members(55583, 764803815)
        self.assertEqual(len(replay_helper.validate_zip(MetadataArchive(infos))), 55583)

    def test_original_limits_reject_member_and_size_overages(self):
        single = metadata_members(1, 0)[0]
        for infos in ([single] * 100001, metadata_members(1, 2 * 1024 * 1024 * 1024 + 1)):
            with self.subTest(count=len(infos), total=sum(row.file_size for row in infos)):
                with self.assertRaisesRegex(replay_helper.ReplayError, "original ZIP exceeds limits"):
                    replay_helper.validate_zip(MetadataArchive(infos), kind="original")

    def test_return_limits_remain_at_256_members_and_25_mib(self):
        boundary = metadata_members(256, 25 * 1024 * 1024)
        self.assertEqual(len(replay_helper.validate_zip(MetadataArchive(boundary), kind="return")), 256)
        for infos in (metadata_members(257, 0), metadata_members(1, 25 * 1024 * 1024 + 1)):
            with self.subTest(count=len(infos), total=sum(row.file_size for row in infos)):
                with self.assertRaisesRegex(replay_helper.ReplayError, "return ZIP exceeds limits"):
                    replay_helper.validate_zip(MetadataArchive(infos), kind="return")


@unittest.skipUnless(GIT, "Git is required for replay tests")
class NestedRootRegression(unittest.TestCase):
    def test_legacy_apply_can_succeed_without_modifying_nested_source(self):
        """Reproduce the documented silent skip before exercising the proposed fix."""
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            subprocess.run([GIT, "init", "-q", "--template="], cwd=parent,
                           env=git_env(), check=True, capture_output=True)
            work = parent / "fresh" / "WORK"
            target = work / TASK_PATH
            target.parent.mkdir(parents=True)
            target.write_bytes(BEFORE)
            checked = subprocess.run([GIT, "apply", "--check", "-"], cwd=work,
                                     env=git_env(), input=PATCH, capture_output=True)
            applied = subprocess.run([GIT, "apply", "-"], cwd=work,
                                     env=git_env(), input=PATCH, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(target.read_bytes(), BEFORE)


@unittest.skipUnless(GIT, "Git is required for replay tests")
class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = self.root / "source.patch"
        self.patch.write_bytes(PATCH)
        self.sequence = 0

    def packet(self, prefix="WORK/", extra=()):
        self.sequence += 1
        path = self.root / f"original-{self.sequence}.zip"
        write_zip(path, [(prefix + TASK_PATH, BEFORE), (prefix + "repo/README.md", b"synthetic\n"), *extra])
        return path

    def call(self, packet, *, delta=None, destination=None, expected=None, environment=None, task_id="example"):
        self.sequence += 1
        destination = destination or self.root / f"fresh-{self.sequence}"
        argv = [sys.executable, "-B", str(HELPER), str(packet), str(delta or self.patch),
                str(destination)]
        if task_id:
            argv += ["--task-id", task_id]
        if expected is not None:
            argv += ["--expected-generator-sha256", expected]
        result = subprocess.run(argv, cwd=self.root, env=environment, capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["invocation"], {"cwd": str(self.root), "argv": argv})
        self.assertEqual(receipt["exit_code"], result.returncode)
        return result.returncode, receipt, destination

    def assert_rejected_before_extraction(self, packet, **kwargs):
        code, receipt, destination = self.call(packet, **kwargs)
        self.assertEqual(code, 2, receipt)
        self.assertEqual(receipt["commands"], [])
        self.assertFalse(os.path.lexists(destination))
        return receipt

    def test_nested_return_zip_ignores_parent_git_and_inherited_git_environment(self):
        subprocess.run([GIT, "init", "-q", "--template="], cwd=self.root,
                       env=git_env(), check=True, capture_output=True)
        parent_target = self.root / TASK_PATH
        parent_target.parent.mkdir(parents=True)
        parent_target.write_bytes(b"parent must stay unchanged\n")
        packet = self.packet(extra=[("WORK/review.py", b"raise RuntimeError('never run me')\n")])
        returned = self.root / "return.zip"
        write_zip(returned, [("patches/source.patch", PATCH), ("checks/ignored.json", b"{}")])
        environment = dict(os.environ, GIT_DIR=str(self.root / ".git"), GIT_WORK_TREE=str(self.root),
                           GIT_CONFIG_PARAMETERS="invalid inherited configuration")
        code, receipt, destination = self.call(packet, delta=returned, expected=digest(AFTER), environment=environment)
        self.assertEqual(code, 0, receipt)
        work = destination / "WORK"
        self.assertEqual((work / TASK_PATH).read_bytes(), AFTER)
        self.assertEqual(parent_target.read_bytes(), b"parent must stay unchanged\n")
        self.assertTrue((work / ".git").is_dir())
        self.assertEqual(receipt["work_root"], str(work))
        self.assertEqual(receipt["original_zip"]["sha256"], digest(packet.read_bytes()))
        self.assertEqual(receipt["delta"]["sha256"], digest(returned.read_bytes()))
        self.assertEqual(receipt["delta"]["patch_sha256"], digest(PATCH))
        self.assertEqual(receipt["generator"]["before_sha256"], digest(BEFORE))
        self.assertEqual(receipt["generator"]["after_sha256"], digest(AFTER))
        self.assertTrue(receipt["generator"]["matches_expected"])
        commands = receipt["commands"]
        self.assertEqual([row["stage"] for row in commands], ["init", "verify_root", "check", "apply"])
        self.assertTrue(all(row["cwd"] == str(work) and row["exit_code"] == 0 for row in commands))
        self.assertEqual(commands[1]["stdout"].strip(), str(work))
        self.assertEqual(commands[2]["argv"][-4:], ["apply", "-p1", "--check", "-"])
        self.assertTrue(all(row["stdin_sha256"] == digest(PATCH) for row in commands[2:]))

    def test_flat_packet_and_plain_patch(self):
        code, receipt, destination = self.call(self.packet(prefix=""), expected=digest(AFTER))
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["layout"], "flat")
        self.assertEqual(receipt["work_root"], str(destination))
        self.assertEqual((destination / TASK_PATH).read_bytes(), AFTER)

    def test_ambiguous_roots_are_rejected(self):
        receipt = self.assert_rejected_before_extraction(self.packet(extra=[(TASK_PATH, BEFORE)]))
        self.assertIn("found 2", receipt["error"])

    def test_patch_paths_split_between_roots_are_rejected(self):
        other = "repo/second.py"
        patch = PATCH + (f"diff --git a/{other} b/{other}\n--- a/{other}\n+++ b/{other}\n"
                         "@@ -1 +1 @@\n-old\n+new\n").encode()
        self.patch.write_bytes(patch)
        receipt = self.assert_rejected_before_extraction(self.packet(extra=[(other, b"old\n")]))
        self.assertIn("found 0", receipt["error"])

    def test_addition_only_and_empty_new_file_patches(self):
        for content in (b"new content\n", b""):
            with self.subTest(content=content):
                name = "repo/generators/example/tests/new_file.py"
                patch = f"diff --git a/{name} b/{name}\nnew file mode 100644\n".encode()
                if content:
                    patch += f"--- /dev/null\n+++ b/{name}\n@@ -0,0 +1 @@\n+".encode() + content
                self.patch.write_bytes(patch)
                code, receipt, destination = self.call(self.packet(), expected=digest(BEFORE))
                self.assertEqual(code, 0, receipt)
                self.assertEqual((destination / "WORK" / name).read_bytes(), content)

    def test_addition_only_patch_accepts_an_explicit_empty_repo_anchor(self):
        packet = self.root / "empty-repo.zip"
        write_zip(packet, [("WORK/repo/", b"")])
        name = "repo/new.txt"
        self.patch.write_text(f"diff --git a/{name} b/{name}\nnew file mode 100644\n"
                              f"--- /dev/null\n+++ b/{name}\n@@ -0,0 +1 @@\n+added\n")
        code, receipt, destination = self.call(packet, task_id=None)
        self.assertEqual(code, 0, receipt)
        self.assertEqual((destination / "WORK" / name).read_bytes(), b"added\n")

    def test_unsafe_zip_paths_are_rejected(self):
        names = ["../escape", "/absolute", "C:/drive", "back\\slash", "x//y", "./dot",
                 "x/../parent", "WORK/.git/config", "trailing.", "NUL.txt", "control\nname"]
        for name in names:
            with self.subTest(name=name):
                self.assert_rejected_before_extraction(self.packet(extra=[(name, b"bad")]))

    def test_nul_truncated_zip_name_is_rejected(self):
        packet = self.packet(extra=[("badXname", b"bad")])
        packet.write_bytes(packet.read_bytes().replace(b"badXname", b"bad\x00name"))
        receipt = self.assert_rejected_before_extraction(packet)
        self.assertIn("Truncated ZIP", receipt["error"])

    def test_duplicates_and_file_directory_collisions_are_rejected(self):
        variants = [
            [("duplicate", b"a"), ("duplicate", b"b")],
            [("Duplicate", b"a"), ("duplicate", b"b")],
            [("x", b"a"), ("x/", b"")],
            [("x", b"a"), ("x/y", b"b")],
            [("x/y", b"b"), ("x", b"a")],
        ]
        for members in variants:
            with self.subTest(members=members):
                self.assert_rejected_before_extraction(self.packet(extra=members))

    def test_symlink_special_and_executable_zip_members_are_rejected(self):
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o644, stat.S_IFREG | 0o755):
            with self.subTest(mode=mode):
                info = zipfile.ZipInfo("unsafe")
                info.external_attr = mode << 16
                self.assert_rejected_before_extraction(self.packet(extra=[(info, b"content")]))

    def test_explicit_directory_and_permissions_without_type_bits_are_supported(self):
        info = zipfile.ZipInfo("WORK/repo/permission_only.txt")
        info.external_attr = 0o600 << 16
        code, receipt, destination = self.call(self.packet(extra=[("WORK/repo/", b""), (info, b"ok")]))
        self.assertEqual(code, 0, receipt)
        self.assertEqual((destination / "WORK/repo/permission_only.txt").read_bytes(), b"ok")

    def test_existing_destinations_are_refused_and_preserved(self):
        packet = self.packet()
        directory = self.root / "existing-directory"
        directory.mkdir()
        (directory / "keep").write_bytes(b"keep")
        regular = self.root / "existing-file"
        regular.write_bytes(b"keep")
        link = self.root / "broken-symlink"
        link.symlink_to(self.root / "missing-target")
        for destination in (directory, regular, link):
            with self.subTest(destination=destination):
                code, receipt, _ = self.call(packet, destination=destination)
                self.assertEqual(code, 2, receipt)
                self.assertEqual(receipt["commands"], [])
                self.assertIn("already exists", receipt["error"])
        self.assertEqual((directory / "keep").read_bytes(), b"keep")
        self.assertEqual(regular.read_bytes(), b"keep")
        self.assertTrue(link.is_symlink())

    def test_destination_symlink_parent_is_refused(self):
        alias = self.root / "parent-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.assert_rejected_before_extraction(self.packet(), destination=alias / "fresh")

    def test_unsafe_or_unsupported_patch_headers_are_rejected(self):
        variants = [
            PATCH.replace(TASK_PATH.encode(), b"repo/../escape"),
            PATCH.replace(TASK_PATH.encode(), b"repo/.git/config"),
            PATCH.replace(f"+++ b/{TASK_PATH}".encode(), b"+++ b/elsewhere"),
            PATCH + b"--- a/repo/second.py\n+++ b/repo/second.py\n@@ -1 +1 @@\n-a\n+b\n",
            PATCH.replace(b"@@ -1 +1 @@", b"deleted file mode 100644\n@@ -1 +1 @@"),
            PATCH.replace(b"@@ -1 +1 @@", b"GIT binary patch\n@@ -1 +1 @@"),
        ]
        for raw in variants:
            with self.subTest(raw=raw[:100]):
                self.patch.write_bytes(raw)
                self.assert_rejected_before_extraction(self.packet())

    def test_failed_check_does_not_apply_and_keeps_original_source(self):
        self.patch.write_bytes(PATCH.replace(b"-answer = 'before'", b"-answer = 'wrong context'"))
        code, receipt, destination = self.call(self.packet())
        self.assertEqual(code, 2, receipt)
        self.assertEqual([row["stage"] for row in receipt["commands"]], ["init", "verify_root", "check"])
        self.assertNotEqual(receipt["commands"][-1]["exit_code"], 0)
        self.assertEqual((destination / "WORK" / TASK_PATH).read_bytes(), BEFORE)

    def test_hash_mismatch_is_an_explicit_failure_with_actual_hash(self):
        code, receipt, destination = self.call(self.packet(), expected="0" * 64)
        self.assertEqual(code, 2, receipt)
        self.assertFalse(receipt["generator"]["matches_expected"])
        self.assertEqual(receipt["generator"]["after_sha256"], digest(AFTER))
        self.assertEqual((destination / "WORK" / TASK_PATH).read_bytes(), AFTER)

    def test_return_zip_without_source_patch_is_rejected(self):
        returned = self.root / "no-change.zip"
        write_zip(returned, [("REVIEW.md", b"No source change\n")])
        receipt = self.assert_rejected_before_extraction(self.packet(), delta=returned)
        self.assertIn("no delta to replay", receipt["error"])

    def test_return_zip_paths_are_validated_even_when_not_read(self):
        returned = self.root / "unsafe-return.zip"
        write_zip(returned, [("patches/source.patch", PATCH), ("../unused", b"bad")])
        self.assert_rejected_before_extraction(self.packet(), delta=returned)

    def test_return_zip_uses_the_smaller_budget_in_the_cli(self):
        returned = self.root / "too-many-return-members.zip"
        write_zip(returned, [("patches/source.patch", PATCH),
                             *[(f"checks/entry-{index}.txt", b"") for index in range(256)]])
        receipt = self.assert_rejected_before_extraction(self.packet(), delta=returned)
        self.assertIn("return ZIP exceeds limits", receipt["error"])

    def test_malformed_huge_hunk_counts_emit_json(self):
        self.patch.write_bytes(PATCH.replace(b"@@ -1 +1 @@", b"@@ -1," + b"9" * 5000 + b" +1 @@"))
        self.assert_rejected_before_extraction(self.packet())

    def test_malformed_deflate_emits_json(self):
        packet = self.packet()
        with zipfile.ZipFile(packet) as archive:
            info = archive.getinfo("WORK/" + TASK_PATH)
            self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
        raw = bytearray(packet.read_bytes())
        name_size, extra_size = struct.unpack_from("<HH", raw, info.header_offset + 26)
        data_start = info.header_offset + 30 + name_size + extra_size
        raw[data_start] = 0x07  # DEFLATE final block with the reserved block type 3.
        packet.write_bytes(raw)
        code, receipt, _ = self.call(packet)
        self.assertEqual(code, 2, receipt)
        self.assertEqual(receipt["commands"], [])
        self.assertIn("error", receipt)

    def test_packet_code_is_never_executed(self):
        trap = b"from pathlib import Path\nPath('EXECUTED').write_text('bad')\n"
        packet = self.packet(extra=[("review.py", trap), ("WORK/run_with_racket.py", trap),
                                    ("WORK/repo/tests/test_trap.py", trap)])
        code, receipt, destination = self.call(packet)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(list(destination.rglob("EXECUTED")), [])
        self.assertTrue(all(Path(row["argv"][0]).resolve() == Path(GIT).resolve()
                            for row in receipt["commands"]))


if __name__ == "__main__":
    unittest.main()
