"""Small stdlib regressions for the optional issued-POSIX replay contract."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("replay_helper_under_test", HERE / "replay_review_return.py")
assert SPEC is not None and SPEC.loader is not None
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


def archive_bytes(entries):
    stream = io.BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(stream, "w") as archive:
        warnings.simplefilter("ignore", UserWarning)  # Intentional duplicate-member fixtures.
        for name, content in entries:
            archive.writestr(name, content)
    return stream.getvalue()


class ReplayGuards(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="arcpuzzles-replay-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()

    def feature(self, name):
        function = getattr(REPLAY, name, None)
        self.assertTrue(callable(function), f"Required replay feature is missing: {name}")
        return function

    def validate(self, entries, *, allow=False):
        kwargs = {}
        if allow:
            self.assertIn("allow_case_distinct_paths", inspect.signature(REPLAY.validate_zip).parameters,
                          "The ZIP validator does not yet offer the explicit case-distinct policy")
            kwargs["allow_case_distinct_paths"] = True
        with zipfile.ZipFile(io.BytesIO(archive_bytes(entries))) as archive:
            return [info.filename for info in REPLAY.validate_zip(archive, **kwargs)]

    def arguments(self, **updates):
        values = dict(original_zip=self.base / "unopened.zip", delta=self.base / "unopened.patch",
                      destination=self.base / "fresh", task_id=None, expected_generator_sha256=None,
                      allow_case_distinct_zip_paths=True, expected_files_manifest=None)
        values.update(updates)
        return argparse.Namespace(**values)

    def test_default_policy_still_rejects_case_aliases(self):
        with self.assertRaisesRegex(REPLAY.ReplayError, "Duplicate ZIP member"):
            self.validate([("WORK/repo/MANIFEST.json", b"upper"),
                           ("WORK/repo/manifest.json", b"lower")])

    def test_case_distinct_pair_is_valid_after_real_destination_probe(self):
        probe = self.feature("destination_case_sensitive")
        if not probe(self.base):
            self.skipTest("This test requires a case-sensitive filesystem")
        entries = [("WORK/repo/MANIFEST.json", b"upper"),
                   ("WORK/repo/manifest.json", b"lower")]
        self.assertEqual(self.validate(entries, allow=True), [name for name, _ in entries])
        self.assertEqual(list(self.base.iterdir()), [], "The filesystem probe left temporary files behind")

    def test_exact_duplicates_are_rejected_even_with_opt_in(self):
        with self.assertRaisesRegex(REPLAY.ReplayError, "Duplicate ZIP member"):
            self.validate([("WORK/repo/Foo", b"one"), ("WORK/repo/Foo", b"two")], allow=True)

    def test_uppercase_file_parent_collisions_are_rejected_in_both_orders(self):
        entries = [("WORK/repo/Foo", b"file"), ("WORK/repo/Foo/bar", b"child")]
        for ordered in (entries, list(reversed(entries))):
            with self.subTest(entries=ordered), self.assertRaisesRegex(REPLAY.ReplayError, "file/directory collision"):
                self.validate(ordered, allow=True)
        with self.assertRaises(REPLAY.ReplayError):
            self.validate([("WORK/repo/Foo", b"file"), ("WORK/repo/Foo/", b"")], allow=True)

    def test_case_insensitive_destination_is_refused_before_reading_or_extracting(self):
        self.feature("destination_case_sensitive")
        with mock.patch.object(REPLAY, "destination_case_sensitive", return_value=False), \
                mock.patch.object(REPLAY, "extract_original") as extract:
            with self.assertRaisesRegex(REPLAY.ReplayError, "case-sensitive"):
                REPLAY.replay(self.arguments(), {"commands": []})
        extract.assert_not_called()
        self.assertFalse((self.base / "fresh").exists())

    def test_probe_io_failure_cannot_authorize_extraction(self):
        self.feature("destination_case_sensitive")
        with mock.patch.object(REPLAY, "destination_case_sensitive", side_effect=OSError("probe unavailable")), \
                mock.patch.object(REPLAY, "extract_original") as extract:
            with self.assertRaises((OSError, REPLAY.ReplayError)):
                REPLAY.replay(self.arguments(), {"commands": []})
        extract.assert_not_called()
        self.assertFalse((self.base / "fresh").exists())

    def test_symlink_destination_parent_remains_rejected(self):
        real = self.base / "real"
        real.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(REPLAY.ReplayError, "no symlink components"):
            REPLAY.replay(self.arguments(destination=alias / "fresh"), {"commands": []})
        self.assertFalse((real / "fresh").exists())

    def test_other_path_guards_and_return_zip_policy_remain_strict(self):
        for name in ("../outside", "WORK/repo/.git/config", "WORK/repo/CON", "WORK\\repo\\file"):
            with self.subTest(name=name), self.assertRaises(REPLAY.ReplayError):
                self.validate([(name, b"bad")], allow=True)
        path = self.base / "return.zip"
        path.write_bytes(archive_bytes([("patches/source.patch", b"patch"),
                                       ("REPORT.json", b"upper"), ("report.json", b"lower")]))
        with self.assertRaisesRegex(REPLAY.ReplayError, "Duplicate ZIP member"):
            REPLAY.read_delta(path)

    def manifest_fixture(self):
        work = self.base / "work"
        (work / "repo").mkdir(parents=True)
        files = {"repo/generator.py": b"repaired\n", "repo/new.txt": b""}
        paths = [{"path": name, "new_file": name.endswith("new.txt")} for name in files]
        changes = []
        for row in paths:
            content = files[row["path"]]
            (work / row["path"]).write_bytes(content)
            changes.append({**row, "after_sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
        manifest = self.base / "expected.json"
        manifest.write_text(json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": changes}))
        return work, paths, changes, manifest

    def test_all_path_verification_includes_modified_and_new_empty_file(self):
        load = self.feature("load_expected_files_manifest")
        verify = self.feature("verify_expected_files")
        work, paths, _changes, manifest = self.manifest_fixture()
        expected, identity = load(manifest, paths)
        receipt = {}
        verify(work, expected, receipt)
        self.assertEqual(identity["sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
        self.assertEqual(receipt["expected_files"]["status"], "passed")
        rows = receipt["expected_files"]["files"]
        self.assertEqual({row["path"] for row in rows}, {row["path"] for row in paths})
        self.assertTrue(all(row["matches_expected"] for row in rows))
        self.assertTrue(next(row for row in rows if row["path"] == "repo/new.txt")["new_file"])

    def test_manifest_path_set_must_equal_patch_exactly(self):
        load = self.feature("load_expected_files_manifest")
        _work, paths, changes, manifest = self.manifest_fixture()
        wrong_sets = [changes[:1], changes + [{**changes[0], "path": "repo/extra.py"}],
                      [changes[0], {**changes[1], "path": "repo/NEW.txt"}]]
        for changed in wrong_sets:
            with self.subTest(paths=[row["path"] for row in changed]):
                manifest.write_text(json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": changed}))
                with self.assertRaisesRegex(REPLAY.ReplayError, "path set"):
                    load(manifest, paths)

    def test_matching_generator_does_not_mask_wrong_new_file_hash(self):
        load = self.feature("load_expected_files_manifest")
        verify = self.feature("verify_expected_files")
        work, paths, changes, manifest = self.manifest_fixture()
        changes[1]["after_sha256"] = hashlib.sha256(b"different").hexdigest()
        manifest.write_text(json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": changes}))
        expected, _identity = load(manifest, paths)
        receipt = {}
        with self.assertRaisesRegex(REPLAY.ReplayError, "repo/new.txt"):
            verify(work, expected, receipt)
        rows = {row["path"]: row for row in receipt["expected_files"]["files"]}
        self.assertTrue(rows["repo/generator.py"]["matches_expected"])
        self.assertFalse(rows["repo/new.txt"]["matches_expected"])
        self.assertEqual(receipt["expected_files"]["status"], "failed")

    def test_manifest_rejects_duplicate_rows_keys_and_new_file_status_mismatch(self):
        load = self.feature("load_expected_files_manifest")
        _work, paths, changes, manifest = self.manifest_fixture()
        documents = [
            json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": changes + [changes[0]]}),
            '{"changes":[],"changes":' + json.dumps(changes) + '}',
            json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": [changes[0], {**changes[1], "new_file": False}]}),
            json.dumps({"schema": "arcpuzzles-all-changed-paths-v1", "changes": [changes[0], {**changes[1], "after_sha256": "not-a-hash"}]}),
        ]
        for text in documents:
            with self.subTest(document=text):
                manifest.write_text(text)
                with self.assertRaises(REPLAY.ReplayError):
                    load(manifest, paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
