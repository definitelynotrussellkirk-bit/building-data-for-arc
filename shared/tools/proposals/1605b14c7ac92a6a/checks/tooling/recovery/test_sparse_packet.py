"""Synthetic tests: no issued task sources are opened by this test suite."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch
import zipfile

import sparse_packet as tool


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def packet(path, *, tamper=False, extra=None):
    files = {
        "repo/catalog/runtime_files.json": canonical([
            {"path": "shared/runtime/helper.py", "target": "helper.py"},
            {"path": "shared/data/raw/common.json", "target": "data/raw/common.json"},
            *[{"path": f"generators/{t}/generator.py", "target": f"generators/{t}.py"} for t in "abc"],
            *[{"path": f"shared/data/base/solutions/{t}.json", "target": f"data/base/solutions/{t}.json"} for t in "abc"],
        ]),
        "repo/catalog/authority_files.json": canonical({f"data/base/solutions/{t}.json": t for t in "abc"}),
        "repo/catalog/puzzles.jsonl": b"{}\n",
        "repo/shared/data/canonical/puzzles.jsonl": b"opaque canonical\n",
        "repo/shared/runtime/helper.py": b"# common\n",
        "repo/shared/data/raw/common.json": b"{}",
        "repo/REVIEW/questions/q.json": b"{}",
        "repo/src/arcpuzzles/__init__.py": b"",
        "WELCOME.md": b"welcome",
    }
    for t in "abc":
        files[f"repo/generators/{t}/generator.py"] = b"# opaque synthetic task\n"
        files[f"repo/generators/{t}/notes.md"] = b"opaque synthetic notes\n"
        files[f"repo/shared/data/base/solutions/{t}.json"] = b"{}"
    outer = {"START-HERE.md": b"start", "review.py": b"# entry\n"}
    manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {
        n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
        "main_ids": ["a", "b"], "all_ids": list("abc"),
        "generators": {t: {"generator": f"generators/{t}/generator.py", "rule_task_id": t,
                            "approved": t == "c"} for t in "abc"},
        "questions": [{"id": "q"}],
        "layout": {"workspace": "WORK", "entry_files": {
            n: hashlib.sha256(b).hexdigest() for n, b in outer.items()}}}
    with zipfile.ZipFile(path, "w") as z:
        for n, b in outer.items(): z.writestr(n, b)
        for n, b in files.items():
            z.writestr("WORK/" + n, b"tampered" if tamper and n == "WELCOME.md" else b)
        z.writestr("WORK/PACKET-MANIFEST.json", canonical(manifest))
        if extra: z.writestr(extra, b"unsafe")


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.archive = self.base / "packet.zip"
        self.target = self.base / "out"
        packet(self.archive)

    def test_unsafe_member_rejected_before_seed(self):
        packet(self.archive, extra="WORK/../escape")
        with self.assertRaisesRegex(ValueError, "[Uu]nsafe"):
            tool.recover(self.archive, self.target)
        self.assertFalse((self.target / ".recovery/seed.json").exists())

    def test_tampered_archive_source_rejected(self):
        packet(self.archive, tamper=True)
        with self.assertRaisesRegex(ValueError, "[Hh]ash"):
            tool.recover(self.archive, self.target)

    def test_resume_reuses_seed_and_hydrates_additional_task(self):
        first = tool.recover(self.archive, self.target)
        seed_path = self.target / ".recovery/seed.json"
        original = seed_path.read_bytes()
        main = first["main_task_id"]
        other = ({"a", "b"} - {main}).pop()
        self.assertFalse((self.target / f"WORK/repo/generators/{other}/generator.py").exists())
        # Simulate interrupted extraction by removing one already copied file.
        (self.target / "WORK/repo/shared/runtime/helper.py").unlink()
        with patch.object(tool.os, "urandom", side_effect=AssertionError("reroll")):
            second = tool.recover(self.archive, self.target, tasks=[other])
        self.assertEqual(seed_path.read_bytes(), original)
        self.assertEqual(second["main_task_id"], main)
        self.assertTrue((self.target / f"WORK/repo/generators/{other}/notes.md").is_file())
        self.assertTrue((self.target / "WORK/repo/shared/data/raw/common.json").is_file())
        self.assertFalse((self.target / "WORK/ASSIGNMENT.json").exists())

    def test_changed_local_source_is_never_overwritten(self):
        tool.recover(self.archive, self.target)
        source = self.target / "WORK/repo/shared/runtime/helper.py"
        source.write_bytes(b"local edit")
        with self.assertRaisesRegex(ValueError, "[Cc]hanged"):
            tool.recover(self.archive, self.target)
        self.assertEqual(source.read_bytes(), b"local edit")

    def test_changed_archive_binding_is_rejected(self):
        tool.recover(self.archive, self.target)
        with zipfile.ZipFile(self.archive, "a") as z:
            z.comment = b"different original archive bytes"
        with self.assertRaisesRegex(ValueError, "binding"):
            tool.recover(self.archive, self.target)

    def test_verify_only_creates_no_workspace_or_seed(self):
        result = tool.recover(self.archive, self.target, verify_only=True)
        self.assertGreater(result["verified_files"], 0)
        self.assertFalse(self.target.exists())

    def test_seed_published_before_selection_failure(self):
        with patch.object(tool, "selections", side_effect=RuntimeError("interrupted")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                tool.recover(self.archive, self.target)
        original = (self.target / ".recovery/seed.json").read_bytes()
        with patch.object(tool.os, "urandom", side_effect=AssertionError("reroll")):
            tool.recover(self.archive, self.target)
        self.assertEqual((self.target / ".recovery/seed.json").read_bytes(), original)

    def test_hydration_preserves_edited_main_and_immutable_receipt_history(self):
        initial = tool.recover(self.archive, self.target)
        first_receipt = Path(initial["receipt_file"])
        original_receipt = first_receipt.read_bytes()
        main = initial["main_task_id"]
        other = ({"a", "b"} - {main}).pop()
        state = json.loads((self.target / ".recovery/seed.json").read_bytes())
        (self.target / "WORK/ASSIGNMENT.json").write_bytes(canonical({
            "task_id": main, "seed": state["seed"], "packet_id": state["manifest_sha256"]}))
        source = self.target / f"WORK/repo/generators/{main}/generator.py"
        source.write_bytes(b"repaired main")
        second = tool.recover(self.archive, self.target, tasks=[other])
        self.assertEqual(source.read_bytes(), b"repaired main")
        self.assertEqual(first_receipt.read_bytes(), original_receipt)
        next_receipt = json.loads(Path(second["receipt_file"]).read_bytes())
        self.assertEqual(next_receipt["previous_receipt"]["filename"], first_receipt.name)
        self.assertGreater(len(next_receipt["files"]), len(json.loads(original_receipt)["files"]))
        self.assertEqual(next_receipt["files"][f"WORK/repo/generators/{main}/generator.py"],
                         hashlib.sha256(b"# opaque synthetic task\n").hexdigest())

    def test_hydration_cannot_preserve_edits_before_draw(self):
        initial = tool.recover(self.archive, self.target)
        source = self.target / f"WORK/repo/generators/{initial['main_task_id']}/generator.py"
        source.write_bytes(b"edited before draw")
        with self.assertRaisesRegex(ValueError, "[Cc]hanged"):
            tool.recover(self.archive, self.target, tasks=["a"])

    def test_symlink_destination_rejected(self):
        self.target.mkdir()
        (self.target / "WORK").symlink_to(self.base / "elsewhere")
        with self.assertRaisesRegex(ValueError, "[Ss]ymlink"):
            tool.recover(self.archive, self.target)


class AuditRecoveryTests(unittest.TestCase):
    """Real state/files with a synthetic generic official-draw dependency."""
    def setUp(self):
        RecoveryTests.setUp(self)
        initial = tool.recover(self.archive, self.target)
        self.main = initial['main_task_id']
        state = json.loads((self.target / '.recovery/seed.json').read_bytes())
        self.work = self.target / 'WORK'
        (self.work / 'ASSIGNMENT.json').write_bytes(canonical({
            'task_id': self.main, 'seed': state['seed'], 'packet_id': state['manifest_sha256']}))
        (self.work / 'BLIND_ASSIGNMENT.json').write_bytes(canonical({
            'task_id': initial['blind_task_id'], 'packet_id': state['manifest_sha256']}))
        frozen = self.work / f'.review/baseline/repo/generators/{self.main}/generator.py'
        frozen.parent.mkdir(parents=True)
        frozen.write_bytes((self.work / f'repo/generators/{self.main}/generator.py').read_bytes())

        class OfficialFixture:
            @staticmethod
            def audit_ids_for_seed(pool, seed):
                first = int.from_bytes(seed, 'big') % len(pool)
                second = int.from_bytes(hashlib.sha256(seed + b':second').digest(), 'big') % (len(pool) - 1)
                if second >= first:
                    second += 1
                return [pool[first], pool[second]]

            @staticmethod
            def draw_audit(work, seed):
                path = work / 'AUDIT_ASSIGNMENT.json'
                if path.is_file():
                    return json.loads(path.read_bytes())
                manifest = json.loads((work / 'PACKET-MANIFEST.json').read_bytes())
                main = json.loads((work / 'ASSIGNMENT.json').read_bytes())['task_id']
                ids = OfficialFixture.audit_ids_for_seed(['a', 'b'], seed)
                targets = []
                for tid in ids:
                    relative = f'repo/generators/{tid}/generator.py'
                    source = work / ('.review/baseline/' + relative if tid == main else relative)
                    targets.append({'task_id': tid, 'generator_sha256': tool.file_hash(source)})
                value = {'schema': 'arcpuzzles-full-audit-v3', 'packet_id': tool.file_hash(work / 'PACKET-MANIFEST.json'),
                         'seed': seed.hex(), 'targets': targets}
                with path.open('x') as handle:
                    handle.write(json.dumps(value, sort_keys=True, indent=2) + '\n')
                return value

        @contextmanager
        def module(work):
            yield OfficialFixture
        self.module_patch = patch.object(tool, 'official_module', module, create=True)
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)

    def test_audit_seed_durable_before_selection_and_sticky_after_interrupt(self):
        with patch.object(tool, 'audit_selection', side_effect=RuntimeError('interrupted'), create=True):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                tool.recover(self.archive, self.target, audit_draw=True)
        seed_path = self.target / '.recovery/audit-seed.json'
        original = seed_path.read_bytes()
        with patch.object(tool.os, 'urandom', side_effect=AssertionError('audit reroll')):
            result = tool.recover(self.archive, self.target, audit_draw=True)
        self.assertEqual(seed_path.read_bytes(), original)
        self.assertEqual(set(result['audit_task_ids']), {'a', 'b'})
        self.assertNotIn('c', result['audit_task_ids'])

    def test_audit_hydrates_both_targets_preserves_main_and_reuses_contract(self):
        main_source = self.work / f'repo/generators/{self.main}/generator.py'
        main_source.write_bytes(b'repaired main')
        result = tool.recover(self.archive, self.target, audit_draw=True)
        self.assertEqual(main_source.read_bytes(), b'repaired main')
        contract_path = self.work / 'AUDIT_ASSIGNMENT.json'
        original = contract_path.read_bytes()
        contract = json.loads(original)
        audit_seed = json.loads((self.target / '.recovery/audit-seed.json').read_bytes())
        self.assertEqual(contract['seed'], audit_seed['seed'])
        self.assertEqual(contract['packet_id'], audit_seed['manifest_sha256'])
        for tid in result['audit_task_ids']:
            self.assertTrue((self.work / f'repo/generators/{tid}/notes.md').is_file())
        receipt = json.loads(Path(result['receipt_file']).read_bytes())
        self.assertTrue(receipt['previous_receipt'])
        self.assertEqual(set(receipt['audit_task_ids']), {'a', 'b'})
        with patch.object(tool.os, 'urandom', side_effect=AssertionError('audit reroll')):
            again = tool.recover(self.archive, self.target, audit_draw=True)
        self.assertEqual(contract_path.read_bytes(), original)
        self.assertEqual(again['audit_assignment_sha256'], hashlib.sha256(original).hexdigest())

    def test_existing_audit_without_saved_seed_refuses_new_seed(self):
        (self.work / 'AUDIT_ASSIGNMENT.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'audit.*seed'):
            tool.recover(self.archive, self.target, audit_draw=True)
        self.assertFalse((self.target / '.recovery/audit-seed.json').exists())

    def test_partial_audit_contract_is_preserved_and_never_rerolled(self):
        tool.recover(self.archive, self.target, audit_draw=True)
        path = self.work / 'AUDIT_ASSIGNMENT.json'
        path.write_bytes(b'{partial')
        with patch.object(tool.os, 'urandom', side_effect=AssertionError('audit reroll')):
            with self.assertRaises(ValueError):
                tool.recover(self.archive, self.target, audit_draw=True)
        self.assertEqual(path.read_bytes(), b'{partial')

    def test_modified_official_sources_rejected_before_audit_selection(self):
        (self.work / 'repo/src/arcpuzzles/__init__.py').write_bytes(b'changed helper')
        with self.assertRaisesRegex(ValueError, 'official.*source'):
            tool.recover(self.archive, self.target, audit_draw=True)
        self.assertFalse((self.target / '.recovery/audit-seed.json').exists())


if __name__ == "__main__":
    unittest.main()
