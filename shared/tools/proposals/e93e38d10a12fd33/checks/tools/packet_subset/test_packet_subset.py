"""Synthetic packet tests: no real generator or private solve content is read."""
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

import packet_subset as ps


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


class PacketSubsetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / "packet.zip"
        self.destination = self.root / "subset"
        self.seed = bytes(range(32))
        files = {
            "assignment.py": b"# fixture bootstrap\n",
            "repo/AGENTS.md": b"fixture instructions\n",
            "repo/src/arcpuzzles/__init__.py": b"",
            "repo/shared/tools/runtime.py": b"# fixture runtime\n",
            "repo/shared/data/canonical/puzzles.jsonl": b"{}\n",
            "repo/shared/unneeded.txt": b"not needed\n",
            "repo/shared/reference-a.txt": b"# fixture runtime\n",
            "repo/shared/reference-b.txt": b"# fixture runtime\n",
            "repo/REVIEW/questions/q1.json": b'{"id":"q1"}',
            "repo/REVIEW/questions/q2.json": b'{"id":"q2"}',
            "vendor/runtime.bin": b"fixture vendor",
        }
        mapping, authorities, generators = [], {}, {}
        for task in ("alpha", "beta", "gamma"):
            for tail in ("generator.py", "notes.md", "tests/test_example.py", "workspace/example.json"):
                files[f"repo/generators/{task}/{tail}"] = (task + ":" + tail).encode()
            rule = f"data/base/solutions/{task}.rkt"
            path = "shared/" + rule
            files["repo/" + path] = ("fixture rule " + task).encode()
            mapping.append({"path": path, "target": rule})
            authorities[rule] = task
            generators[task] = {"generator": f"generators/{task}/generator.py",
                                "rule_task_id": task, "approved": task != "alpha"}
        for path in ("shared/tools/runtime.py", "shared/data/canonical/puzzles.jsonl"):
            mapping.append({"path": path, "target": path.removeprefix("shared/")})
        files["repo/catalog/runtime_files.json"] = canonical(mapping)
        files["repo/catalog/authority_files.json"] = canonical(authorities)
        entry = {"START-HERE.md": b"fixture start", "review.py": b"# fixture entry\n"}
        self.manifest = {"schema": "arcpuzzles-full-packet-v2", "main_ids": ["alpha", "beta", "gamma"],
            "all_ids": ["alpha", "beta", "gamma"], "generators": generators,
            "questions": [{"id": "q2"}, {"id": "q1"}], "reviewer_solve": {"blind": {"required": True}},
            "layout": {"workspace": "WORK", "entry_files": {n: ps.sha(v) for n, v in entry.items()}},
            "files": {n: ps.sha(v) for n, v in files.items()}}
        self.members = {**entry, **{"WORK/" + n: v for n, v in files.items()},
                        "WORK/PACKET-MANIFEST.json": canonical(self.manifest)}
        self.write_zip()

    def write_zip(self, extra=()):
        with zipfile.ZipFile(self.archive, "w") as archive:
            for name, raw in self.members.items():
                archive.writestr(name, raw)
            for name, raw in extra:
                archive.writestr(name, raw)

    def extract(self, **kwargs):
        return ps.run("extract", self.archive, self.destination, seed=self.seed, **kwargs)

    def test_verify_all_members_and_detect_tampering(self):
        result = ps.run("verify", self.archive)
        self.assertEqual(result["verified_files"], len(self.members))
        self.members["WORK/repo/shared/unneeded.txt"] = b"tampered"
        self.write_zip()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            ps.run("verify", self.archive)

    def test_exact_selection_deterministic_seed_and_actual_filenames(self):
        report = self.extract()
        with ps.Packet(self.archive) as packet:
            contract, tasks = packet.selection(self.seed)
            self.assertEqual((contract, tasks), packet.selection(self.seed))
            self.assertEqual(contract["task_id"], self.manifest["main_ids"][int.from_bytes(self.seed, "big") % 3])
            wanted = packet.members(tasks)
        actual = {str(p.relative_to(self.destination)) for p in self.destination.rglob("*")
                  if p.is_file() and str(p.relative_to(self.destination)) in self.members}
        self.assertEqual(actual, wanted)
        self.assertEqual({row["path"] for row in report["inventory"]}, wanted)
        for task in tasks:
            for name in self.members:
                if name.startswith(f"WORK/repo/generators/{task}/"):
                    self.assertIn(name, actual)
        self.assertNotIn("WORK/repo/shared/unneeded.txt", actual)
        pending = json.loads((self.destination / "WORK/.review/pending-main-draw.json").read_text())
        self.assertEqual(pending["contract"], contract)
        self.assertEqual((self.destination / "WORK/.review/pending-main-draw.json").read_bytes(),
                         (json.dumps(pending, sort_keys=True, indent=2) + "\n").encode())

    def test_unchanged_rerun_preserves_seed_bytes_and_payload_mtimes(self):
        first = self.extract()
        before = {n: (self.destination / n).stat().st_mtime_ns for n in self.members if (self.destination / n).exists()}
        journal = (self.destination / ".packet-subset/selection.json").read_bytes()
        second = ps.run("extract", self.archive, self.destination)
        self.assertEqual(first, second)
        self.assertEqual(before, {n: (self.destination / n).stat().st_mtime_ns for n in before})
        self.assertEqual(journal, (self.destination / ".packet-subset/selection.json").read_bytes())

    def test_interruption_never_rerolls(self):
        with mock.patch.object(ps, "install", side_effect=OSError(28, "fixture ENOSPC")):
            with self.assertRaises(OSError):
                ps.run("extract", self.archive, self.destination)
        saved = json.loads((self.destination / ".packet-subset/selection.json").read_text())
        self.assertEqual(len(bytes.fromhex(saved["seed"])), 32)
        with self.assertRaisesRegex(ValueError, "seed conflicts"):
            self.extract()
        final = ps.run("extract", self.archive, self.destination)
        self.assertEqual(final["seed"], saved["seed"])

    def test_selection_failure_and_corrupt_journal_never_reroll(self):
        with mock.patch.object(ps.Packet, "selection", side_effect=ValueError("fixture selection failure")):
            with self.assertRaisesRegex(ValueError, "selection failure"):
                ps.run("extract", self.archive, self.destination)
        journal = self.destination / ".packet-subset/selection.json"
        saved = json.loads(journal.read_bytes())
        with mock.patch.object(ps.os, "urandom", side_effect=AssertionError("must not reroll")):
            result = ps.run("extract", self.archive, self.destination)
        self.assertEqual(result["seed"], saved["seed"])
        journal.write_bytes(b"")
        with mock.patch.object(ps.os, "urandom", side_effect=AssertionError("must not reroll")):
            with self.assertRaises(ValueError):
                ps.run("extract", self.archive, self.destination)

    def test_conflict_preserved_and_add_keeps_edits(self):
        first = self.extract()
        target = self.destination / f"WORK/repo/generators/{first['task_id']}/generator.py"
        target.write_bytes(b"reviewer change")
        with self.assertRaisesRegex(ValueError, "Existing file differs"):
            self.extract()
        remaining = next(t for t in self.manifest["all_ids"] if t not in first["tasks"])
        result = ps.run("add", self.archive, self.destination, tasks=[remaining])
        self.assertEqual(target.read_bytes(), b"reviewer change")
        self.assertEqual(result["preserved_modified"], [str(target.relative_to(self.destination))])
        self.assertTrue((self.destination / f"WORK/repo/generators/{remaining}/workspace/example.json").is_file())

    def test_add_adopts_existing_valid_subset_and_assignment(self):
        with ps.Packet(self.archive) as packet:
            contract, _ = packet.selection(self.seed)
        work = self.destination / "WORK"
        work.mkdir(parents=True)
        for name in ("START-HERE.md", "review.py", "WORK/PACKET-MANIFEST.json"):
            (self.destination / name).write_bytes(self.members[name])
        (work / "ASSIGNMENT.json").write_bytes(canonical(contract))
        result = ps.run("add", self.archive, self.destination, tasks=["gamma"])
        self.assertEqual(result["seed"], self.seed.hex())
        self.assertEqual(json.loads((work / "ASSIGNMENT.json").read_text()), contract)

    def test_invalid_archive_paths_duplicate_symlink_and_parent_file(self):
        for name in ("../escape", "/escape", "WORK/../escape", "WORK\\escape", "WORK//escape"):
            with self.subTest(name=name):
                self.write_zip([(name, b"bad")])
                with self.assertRaises(ValueError):
                    ps.run("verify", self.archive)
        with __import__("warnings").catch_warnings():
            __import__("warnings").simplefilter("ignore", UserWarning)
            self.write_zip([("review.py", b"duplicate")])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ps.run("verify", self.archive)
        link = zipfile.ZipInfo("WORK/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.write_zip([(link, b"target")])
        with self.assertRaisesRegex(ValueError, "Unsafe member"):
            ps.run("verify", self.archive)
        self.write_zip([("review.py/child", b"bad")])
        with self.assertRaises(ValueError):
            ps.run("verify", self.archive)

    def test_destination_symlink_rejected(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.destination.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.extract()
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_complete_deduplicates_only_new_files_and_preserves_edits(self):
        first = self.extract()
        edited = self.destination / f"WORK/repo/generators/{first['task_id']}/generator.py"
        edited.write_bytes(b"reviewer change")
        selected = self.destination / "WORK/repo/shared/tools/runtime.py"
        selected_inode, selected_mode = selected.stat().st_ino, selected.stat().st_mode
        result = ps.run("complete", self.archive, self.destination, deduplicate=True)
        left = self.destination / "WORK/repo/shared/reference-a.txt"
        right = self.destination / "WORK/repo/shared/reference-b.txt"
        self.assertEqual(edited.read_bytes(), b"reviewer change")
        self.assertEqual(left.stat().st_ino, right.stat().st_ino)
        self.assertNotEqual(left.stat().st_ino, selected_inode)
        self.assertEqual(selected.stat().st_mode, selected_mode)
        self.assertEqual(left.stat().st_mode & 0o222, 0)
        self.assertTrue(all((self.destination / name).is_file() for name in self.members))
        self.assertIn(str(edited.relative_to(self.destination)), result["preserved_modified"])
        repeat = ps.run("complete", self.archive, self.destination, deduplicate=True)
        self.assertEqual(repeat["restored_files"], 0)
        self.assertEqual(left.stat().st_ino, right.stat().st_ino)
        self.assertEqual(edited.read_bytes(), b"reviewer change")

    def test_completion_dry_run_has_no_writes(self):
        self.extract()
        before = {str(path.relative_to(self.destination)): (path.stat().st_mtime_ns, path.stat().st_ino)
                  for path in self.destination.rglob("*")}
        plan = ps.run("complete", self.archive, self.destination, deduplicate=True, dry_run=True)
        after = {str(path.relative_to(self.destination)): (path.stat().st_mtime_ns, path.stat().st_ino)
                 for path in self.destination.rglob("*")}
        self.assertEqual(before, after)
        self.assertGreater(plan["missing_files"], plan["missing_unique_hashes"])
        self.assertEqual(plan["status"], "planned")

    def test_completion_verifies_each_member_before_duplicate_link(self):
        self.extract()
        self.members["WORK/repo/shared/reference-b.txt"] = b"corrupted duplicate member"
        self.write_zip()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            ps.run("complete", self.archive, self.destination, deduplicate=True)
        self.assertFalse((self.destination / "WORK/repo/shared/reference-b.txt").exists())
        self.assertEqual((self.destination / "WORK/repo/shared/tools/runtime.py").read_bytes(),
                         b"# fixture runtime\n")


if __name__ == "__main__":
    unittest.main()
