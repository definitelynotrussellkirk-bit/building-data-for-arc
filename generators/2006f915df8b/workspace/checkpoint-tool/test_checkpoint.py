import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import checkpoint as cp


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.original = self.home / "original.zip"
        self.tree = self.home / "tree"
        self.bundle = self.home / "checkpoint.zip"
        self.entries = {"WORK/source.txt": b"original\n", "WORK/keep.txt": b"unchanged\n",
                        "WORK/remove.txt": b"retain on restore\n"}
        manifest = {"files": {n.removeprefix("WORK/"): hashlib.sha256(raw).hexdigest()
                              for n, raw in self.entries.items()}}
        self.entries["WORK/PACKET-MANIFEST.json"] = json.dumps(manifest).encode()
        with zipfile.ZipFile(self.original, "w") as archive:
            for name, raw in self.entries.items():
                archive.writestr(name, raw)
        self.fresh(self.tree)

    def fresh(self, destination):
        for name, raw in self.entries.items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return destination

    def write(self, name, raw=b"new\n"):
        path = self.tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def receipt(self):
        with zipfile.ZipFile(self.bundle) as archive:
            return json.loads(archive.read(cp.MEMBER))

    def test_roundtrip_modes_and_deletions_are_informational(self):
        self.write("WORK/source.txt", b"edited\n")
        self.write("WORK/ASSIGNMENT.json", b'{"draw":"fixed"}\n')
        self.write("WORK/.review/baseline/source.txt", b"original\n")
        self.write("WORK/checks/check.json", b'{"passed":true}\n')
        (self.tree / "WORK/remove.txt").unlink()
        cp.create(self.original, self.tree, self.bundle)
        receipt = self.receipt()
        self.assertEqual(receipt["original_zip_sha256"],
                         hashlib.sha256(self.original.read_bytes()).hexdigest())
        self.assertNotIn("WORK/keep.txt", receipt["files"])
        self.assertEqual(receipt["deletions"], ["WORK/remove.txt"])
        destination = self.fresh(self.home / "fresh")
        result = cp.restore(self.original, self.bundle, destination, "fresh")
        self.assertEqual((destination / "WORK/source.txt").read_bytes(), b"edited\n")
        self.assertTrue((destination / "WORK/remove.txt").is_file())
        self.assertEqual(result["deletions_not_applied"], ["WORK/remove.txt"])
        area = self.home / "area"
        cp.restore(self.original, self.bundle, area, "empty")
        self.assertEqual((area / "WORK/ASSIGNMENT.json").read_bytes(), b'{"draw":"fixed"}\n')
        self.assertFalse((area / "WORK/keep.txt").exists())
        with self.assertRaises(ValueError):
            cp.restore(self.original, self.bundle, self.home / "unspecified")

    def test_unsafe_paths_and_symlinks(self):
        for name in ("../escape", "/absolute", "a//b", "a/./b", "a\\b", "C:/escape"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                cp.safe(name)
        unsafe = self.home / "unsafe.zip"
        with zipfile.ZipFile(unsafe, "w") as archive:
            archive.writestr("../escape", b"unsafe")
        with self.assertRaises(ValueError):
            cp.create(unsafe, self.tree, self.bundle)
        (self.tree / "WORK/link").symlink_to(self.tree / "WORK/source.txt")
        with self.assertRaises(ValueError):
            cp.create(self.original, self.tree, self.bundle)
        self.assertFalse((self.home / "escape").exists())
        (self.tree / "WORK/link").unlink()
        self.write("WORK/New.txt")
        self.write("WORK/new.txt")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            cp.create(self.original, self.tree, self.bundle)
        self.assertFalse(self.bundle.exists())

    def test_conflict_refused_before_any_write(self):
        self.write("WORK/source.txt", b"edited\n")
        self.write("WORK/added.txt")
        cp.create(self.original, self.tree, self.bundle)
        destination = self.fresh(self.home / "conflicting")
        (destination / "WORK/source.txt").write_bytes(b"another edit\n")
        with self.assertRaisesRegex(ValueError, "conflicting"):
            cp.restore(self.original, self.bundle, destination, "fresh")
        self.assertEqual((destination / "WORK/source.txt").read_bytes(), b"another edit\n")
        self.assertFalse((destination / "WORK/added.txt").exists())
        with self.assertRaisesRegex(ValueError, "empty"):
            cp.restore(self.original, self.bundle, destination, "empty")

    def test_corruption_and_wrong_original_rejected(self):
        self.write("WORK/source.txt", b"edited\n")
        cp.create(self.original, self.tree, self.bundle)
        corrupt = self.home / "corrupt.zip"
        with zipfile.ZipFile(self.bundle) as source, zipfile.ZipFile(corrupt, "w") as target:
            for info in source.infolist():
                raw = source.read(info)
                target.writestr(info, b"corrupt" if info.filename.startswith("files/") else raw)
        destination = self.home / "area"
        with self.assertRaisesRegex(ValueError, "hash/size"):
            cp.restore(self.original, corrupt, destination, "empty")
        self.assertFalse(destination.exists())
        other = self.home / "other.zip"
        with zipfile.ZipFile(other, "w") as archive:
            archive.writestr("different", b"different")
        with self.assertRaisesRegex(ValueError, "identity"):
            cp.restore(other, self.bundle, destination, "empty")

    def test_exclusion_receipt_and_protected_paths(self):
        self.write("WORK/.review/racket-runtime/bin/racket", b"disposable")
        self.write("WORK/.review/baseline/source.txt", b"frozen")
        self.write("WORK/ASSIGNMENT.json", b"contract")
        self.write("WORK/checks/receipt.json", b"evidence")
        cp.create(self.original, self.tree, self.bundle,
                  exclude=["WORK/.review/racket-runtime"])
        receipt = self.receipt()
        self.assertEqual(receipt["exclusions"], ["WORK/.review/racket-runtime"])
        self.assertNotIn("WORK/.review/racket-runtime/bin/racket", receipt["files"])
        for name in ("WORK/.review/baseline/source.txt", "WORK/ASSIGNMENT.json",
                     "WORK/checks/receipt.json"):
            self.assertIn(name, receipt["files"])
        for name in ("WORK", "WORK/.review", "WORK/.review/baseline"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                cp.exclusions([name])
        with self.assertRaises(ValueError):
            cp.create(self.original, self.tree, self.tree / "inside.zip")

    def test_restore_rejects_unsafe_member_and_symlink_destination(self):
        self.write("WORK/added.txt")
        cp.create(self.original, self.tree, self.bundle)
        unsafe = self.home / "unsafe-checkpoint.zip"
        with zipfile.ZipFile(self.bundle) as source, zipfile.ZipFile(unsafe, "w") as target:
            for info in source.infolist():
                name = "files/../escape" if info.filename.startswith("files/") else info.filename
                target.writestr(name, source.read(info))
        area = self.home / "area"
        with self.assertRaises(ValueError):
            cp.restore(self.original, unsafe, area, "empty")
        self.assertFalse(area.exists())
        area.mkdir()
        linked = self.home / "linked"
        linked.symlink_to(area, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            cp.restore(self.original, self.bundle, linked, "empty")
        self.assertEqual(list(area.iterdir()), [])

    def test_partial_installation_is_reported_without_overwriting_conflict(self):
        self.write("WORK/a.txt", b"first")
        self.write("WORK/b.txt", b"second")
        cp.create(self.original, self.tree, self.bundle)
        area = self.home / "area"
        real_link = cp.os.link

        def competing_writer(source, target):
            if Path(target).name == "b.txt":
                Path(target).write_bytes(b"competing content")
            return real_link(source, target)

        with patch("checkpoint.os.link", side_effect=competing_writer):
            with self.assertRaisesRegex(RuntimeError, r"installed=\['WORK/a.txt'\]"):
                cp.restore(self.original, self.bundle, area, "empty")
        self.assertEqual((area / "WORK/a.txt").read_bytes(), b"first")
        self.assertEqual((area / "WORK/b.txt").read_bytes(), b"competing content")

    def test_checkpoint_cannot_replace_the_original_packet_manifest(self):
        cp.create(self.original, self.tree, self.bundle)
        data = self.receipt()
        name = "WORK/PACKET-MANIFEST.json"
        changed = self.entries[name] + b" "
        data["files"][name] = {"sha256": hashlib.sha256(changed).hexdigest(),
                               "size": len(changed), "mode": 0o644}
        forged = self.home / "forged.zip"
        with zipfile.ZipFile(forged, "w") as archive:
            archive.writestr(cp.MEMBER, json.dumps(data))
            archive.writestr("files/" + name, changed)
        area = self.home / "area"
        with self.assertRaisesRegex(ValueError, "protected"):
            cp.restore(self.original, forged, area, "empty")
        self.assertFalse(area.exists())

    def test_original_contract_is_retained_and_cannot_be_changed_or_omitted(self):
        name = "WORK/ASSIGNMENT.json"
        self.entries[name] = b"immutable original contract"
        with zipfile.ZipFile(self.original, "w") as archive:
            for path, raw in self.entries.items():
                archive.writestr(path, raw)
        self.fresh(self.tree)
        cp.create(self.original, self.tree, self.bundle)
        data = self.receipt()
        self.assertIn(name, data["files"])
        data["files"].pop(name)
        forged = self.home / "omitted.zip"
        with zipfile.ZipFile(forged, "w") as archive:
            archive.writestr(cp.MEMBER, json.dumps(data))
        with self.assertRaisesRegex(ValueError, "omits"):
            cp.restore(self.original, forged, self.home / "area", "empty")
        self.write(name, b"changed contract")
        with self.assertRaisesRegex(ValueError, "contract"):
            cp.create(self.original, self.tree, self.home / "changed.zip")


if __name__ == "__main__":
    unittest.main()
