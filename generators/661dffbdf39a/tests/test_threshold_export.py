"""Task-local public writer regressions; synthetic fixtures test projection only.

The integration test is the separately identified Racket semantic evidence.
Run this file with unittest through the packet's review.py run wrapper.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest


EXPORTER_PATH = (Path(__file__).resolve().parents[1] / "workspace" /
                 "parametric" / "export_challenges.py")


def synthetic_episode(marker=2):
    """Literal serialization fixture, deliberately not a threshold lesson."""
    program = "(rule! (lambda (g) g))"
    grids = [
        [[0, 5], [marker, 0]], [[marker, 0], [0, 5]],
        [[5, marker], [0, 0]], [[0, 0], [5, marker]],
    ]
    return {
        "train": [{"input": g, "output": copy.deepcopy(g)} for g in grids[:2]],
        "test": [{"input": g, "output": copy.deepcopy(g)} for g in grids[2:]],
        "metadata": {
            "threshold": "1/2", "seed": 101,
            "program": program,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "teaching": {"fixture": "synthetic projection only; no semantic evidence"},
        },
    }


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8")


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXPORTER_PATH.is_file():
            cls.export = None
            return
        spec = importlib.util.spec_from_file_location("threshold_export_tests", EXPORTER_PATH)
        cls.export = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.export)

    def setUp(self):
        self.assertIsNotNone(self.export, "The task-local public exporter has not been implemented")
        self.temp = tempfile.TemporaryDirectory(prefix="threshold-export-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def emit(self, episodes=None, name="export"):
        destination = self.root / name
        self.export.write_batch(episodes or [synthetic_episode()], destination)
        return destination

    def payload(self, destination):
        paths = list((destination / "public").glob("*.json"))
        self.assertEqual(len(paths), 1)
        return paths[0]

    def test_private_metadata_and_query_answers_cannot_change_public_file(self):
        original = synthetic_episode()
        changed = copy.deepcopy(original)
        changed["metadata"].update({"threshold": "2/3", "seed": 999, "note": "private"})
        changed["test"][0]["output"][0][0] = 9
        a = self.emit([original], "a")
        b = self.emit([changed], "b")
        self.assertEqual(self.payload(a).name, self.payload(b).name)
        self.assertEqual(self.payload(a).read_bytes(), self.payload(b).read_bytes())
        self.assertEqual((a / "index.json").read_bytes(), (b / "index.json").read_bytes())
        self.assertNotEqual(next((a / "private" / "episodes").iterdir()).read_bytes(),
                            next((b / "private" / "episodes").iterdir()).read_bytes())

    def test_public_file_uses_exact_shared_projection_and_id(self):
        episode = synthetic_episode()
        destination = self.emit([episode])
        payload = self.payload(destination)
        expected = self.export.public_challenge_bytes(episode)
        self.assertEqual(payload.read_bytes(), expected)
        self.assertEqual(payload.stem, hashlib.sha256(expected).hexdigest())
        public = read_json(payload)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))

    def test_each_visible_change_changes_the_content_id(self):
        original = synthetic_episode()
        original_id = self.payload(self.emit([original], "original")).stem
        for split, field in (("train", "input"), ("train", "output"), ("test", "input")):
            with self.subTest(split=split, field=field):
                changed = copy.deepcopy(original)
                changed[split][0][field][0][0] = 8
                changed_id = self.payload(self.emit([changed], split + field)).stem
                self.assertNotEqual(changed_id, original_id)

    def test_duplicate_visible_batch_rejected_before_any_output(self):
        first, second = synthetic_episode(), synthetic_episode()
        second["metadata"]["seed"] = 987
        second["test"][0]["output"][0][0] = 9
        out = self.root / "absent-parent" / "export"
        with self.assertRaisesRegex(ValueError, "duplicate public"):
            self.export.write_batch([first, second], out)
        self.assertFalse(out.parent.exists())

    def test_duplicate_demonstration_inputs_rejected(self):
        episode = synthetic_episode()
        episode["train"][1]["input"] = copy.deepcopy(episode["train"][0]["input"])
        with self.assertRaisesRegex(ValueError, "duplicate input"):
            self.emit([episode])
        self.assertFalse((self.root / "export").exists())

    def test_duplicate_query_inputs_rejected(self):
        episode = synthetic_episode()
        episode["test"][1]["input"] = copy.deepcopy(episode["test"][0]["input"])
        with self.assertRaisesRegex(ValueError, "duplicate input"):
            self.emit([episode])

    def test_demo_query_overlap_rejected(self):
        episode = synthetic_episode()
        episode["test"][0]["input"] = copy.deepcopy(episode["train"][0]["input"])
        with self.assertRaisesRegex(ValueError, "duplicate input"):
            self.emit([episode])

    def test_malformed_grids_and_missing_labels_rejected_before_writing(self):
        cases = {
            "empty grid": [], "empty row": [[]], "ragged": [[1], [1, 2]],
            "bool cell": [[True]], "float cell": [[1.0]], "negative": [[-1]],
            "too large color": [[10]], "too tall": [[0]] * 31,
            "too wide": [[0] * 31], "tuple row": [(0,)],
        }
        for label, grid in cases.items():
            with self.subTest(label=label):
                episode = synthetic_episode()
                episode["test"][0]["input"] = grid
                with self.assertRaises(ValueError):
                    self.emit([synthetic_episode(3), episode])
                self.assertFalse((self.root / "export").exists())
        for split in ("train", "test"):
            episode = synthetic_episode()
            del episode[split][0]["output"]
            with self.subTest(missing_output=split), self.assertRaises(ValueError):
                self.emit([episode])

    def test_empty_batch_and_empty_splits_rejected(self):
        with self.assertRaises(ValueError):
            self.export.write_batch([], self.root / "export")
        for split in ("train", "test"):
            episode = synthetic_episode()
            episode[split] = []
            with self.subTest(split=split), self.assertRaises(ValueError):
                self.emit([episode])

    def test_invalid_private_program_hash_rejected_before_writing(self):
        episode = synthetic_episode()
        episode["metadata"]["program_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "program hash"):
            self.emit([episode])
        self.assertFalse((self.root / "export").exists())

    def test_index_and_private_mapping_are_sorted_by_public_id(self):
        destination = self.emit([synthetic_episode(m) for m in (4, 2, 3)])
        index = read_json(destination / "index.json")
        self.assertEqual(set(index), {"public_challenge_ids"})
        ids = index["public_challenge_ids"]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(set(ids), {path.stem for path in (destination / "public").iterdir()})
        manifest = read_json(destination / "private" / "manifest.json")
        self.assertEqual([entry["public_challenge_id"] for entry in manifest["episodes"]], ids)
        report = self.export.verify_export(destination)
        self.assertEqual(report["episode_count"], 3)
        self.assertEqual(report["label_replay"], "not_run")

    def test_nonempty_destination_is_not_clobbered(self):
        destination = self.root / "export"
        destination.mkdir()
        sentinel = destination / "keep.txt"
        sentinel.write_text("existing user data", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.export.write_batch([synthetic_episode()], destination)
        self.assertEqual(sentinel.read_text(), "existing user data")
        self.assertEqual(list(destination.iterdir()), [sentinel])

    def test_empty_existing_destination_is_supported(self):
        destination = self.root / "export"
        destination.mkdir()
        self.export.write_batch([synthetic_episode()], destination)
        self.assertEqual(self.export.verify_export(destination)["episode_count"], 1)

    def test_symlink_destination_is_rejected(self):
        target = self.root / "target"
        target.mkdir()
        destination = self.root / "export"
        destination.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.export.write_batch([synthetic_episode()], destination)
        self.assertEqual(list(target.iterdir()), [])

    def test_public_value_corruption_is_detected(self):
        destination = self.emit()
        path = self.payload(destination)
        value = read_json(path)
        value["test"][0]["input"][0][0] = 9
        write_json(path, value)
        with self.assertRaisesRegex(ValueError, "content ID"):
            self.export.verify_export(destination)

    def test_noncanonical_public_bytes_are_rejected(self):
        destination = self.emit()
        path = self.payload(destination)
        path.write_text(json.dumps(read_json(path), indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "canonical bytes"):
            self.export.verify_export(destination)

    def test_public_extra_metadata_or_query_answer_is_rejected(self):
        for case in ("metadata", "query_answer", "pair_metadata"):
            with self.subTest(case=case):
                destination = self.emit(name=case)
                path = self.payload(destination)
                value = read_json(path)
                if case == "metadata":
                    value["metadata"] = {"seed": 101}
                elif case == "query_answer":
                    value["test"][0]["output"] = [[1]]
                else:
                    value["train"][0]["seed"] = 101
                write_json(path, value)
                with self.assertRaisesRegex(ValueError, "public schema"):
                    self.export.verify_export(destination)

    def test_duplicate_json_keys_are_rejected(self):
        destination = self.emit()
        path = self.payload(destination)
        raw = path.read_text(encoding="utf-8")
        path.write_text('{"train":[],' + raw[1:], encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.export.verify_export(destination)

    def test_duplicate_or_unsorted_index_is_rejected(self):
        for case in ("duplicate", "unsorted"):
            destination = self.emit([synthetic_episode(2), synthetic_episode(3)], name=case)
            index = read_json(destination / "index.json")
            ids = index["public_challenge_ids"]
            index["public_challenge_ids"] = ids + ids[:1] if case == "duplicate" else ids[::-1]
            write_json(destination / "index.json", index)
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.export.verify_export(destination)

    def test_extra_public_file_and_private_corruption_are_rejected(self):
        destination = self.emit(name="extra")
        (destination / "public" / "seed-101.txt").write_text("hidden", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "public file set"):
            self.export.verify_export(destination)
        destination = self.emit(name="private")
        private_path = next((destination / "private" / "episodes").iterdir())
        private_path.write_bytes(private_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "episode hash"):
            self.export.verify_export(destination)

    def test_verifier_rejects_duplicate_demo_query_inputs(self):
        for first, second in (("train", "train"), ("test", "test"), ("train", "test")):
            with self.subTest(first=first, second=second):
                destination = self.emit(name=first + second)
                path = self.payload(destination)
                value = read_json(path)
                value[second][1]["input"] = copy.deepcopy(value[first][0]["input"])
                write_json(path, value)
                with self.assertRaisesRegex(ValueError, "duplicate input"):
                    self.export.verify_export(destination)

    def test_reference_directory_symlink_rejected_before_reading_its_files(self):
        destination = self.emit()
        reference_dir = destination / "private" / "references"
        external = self.root / "external-references"
        reference_dir.rename(external)
        reference_dir.symlink_to(external, target_is_directory=True)
        manifest = read_json(destination / "private" / "manifest.json")
        reference_name = Path(manifest["episodes"][0]["program_path"]).name
        (external / reference_name).write_bytes(b"invalid external fixture")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.export.verify_export(destination)

    def test_replay_rejects_recorded_source_drift_before_execution(self):
        destination = self.emit()
        path = destination / "private" / "manifest.json"
        manifest = read_json(path)
        manifest["provenance"]["sources"]["exporter"]["sha256"] = "0" * 64
        write_json(path, manifest)
        with self.assertRaisesRegex(ValueError, "source hash"):
            self.export.verify_export(destination, replay=True)

    @unittest.skipUnless(os.environ.get("RACKET_PATH") or shutil.which("racket"),
                         "Racket not configured; run through review.py run")
    def test_real_racket_export_replay_and_answer_mutation(self):
        core = self.export.load_core()
        episode = core.make_episode(1729, threshold="1/2", train_count=3, query_count=4)
        destination = self.emit([episode], "real")
        report = self.export.verify_export(destination, replay=True)
        self.assertEqual(report["label_replay"], "passed")
        self.assertEqual(report["labels_checked"], 7)
        self.assertEqual(report["current_sources"], "matched")

        # The real writer preserves public identity under a private mutation;
        # its coherent hashes cannot turn a wrong answer into Racket evidence.
        changed = copy.deepcopy(episode)
        changed["metadata"]["seed"] = 999
        changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
        changed_destination = self.emit([changed], "real-private-mutation")
        self.assertEqual(self.payload(destination).name, self.payload(changed_destination).name)
        self.assertEqual(self.payload(destination).read_bytes(), self.payload(changed_destination).read_bytes())
        self.assertEqual(self.export.verify_export(changed_destination)["label_replay"], "not_run")
        with self.assertRaisesRegex(ValueError, "Racket label mismatch"):
            self.export.verify_export(changed_destination, replay=True)


if __name__ == "__main__":
    unittest.main()
