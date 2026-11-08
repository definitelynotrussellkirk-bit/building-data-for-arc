"""Small synthetic replay checks; no selected task or Racket is executed."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
TOOL = HERE / "manual_replay_selected.py"
sys.path.insert(0, str(HERE))
from verify_review_archive import verify


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


class ManualReplay(unittest.TestCase):
    def fixture(self, base):
        owner = base / "owner" / "WORK"
        owner.mkdir(parents=True)
        selected = "repo/generators/task/generator.py"
        added = "repo/generators/task/tests/test_added.py"
        sources = {
            selected: b"value = 1\n",
            "repo/shared/runtime/reviewer_support.py": b"# synthetic dependency; never imported\n",
            "repo/shared/data/canonical/puzzles.jsonl": b"{}\n",
            "repo/catalog/runtime_files.json": b"[]",
            "repo/catalog/authority_files.json": b"{}",
            "repo/README.md": b"Synthetic fixture.\n",
            "repo/shared/data/derived/omit.jsonl": b"must not be extracted\n",
        }
        api = WORK / "repo/src/arcpuzzles"
        for path in api.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                sources["repo/src/arcpuzzles/" + path.relative_to(api).as_posix()] = path.read_bytes()
        entry = {"START-HERE.md": b"Synthetic.\n", "review.py": b"# never executed\n"}
        manifest = {
            "schema": "arcpuzzles-full-packet-v2",
            "layout": {"workspace": "WORK", "entry_files": {k: sha(v) for k, v in entry.items()}},
            "files": {k: sha(v) for k, v in sources.items()},
            "main_ids": ["task"], "all_ids": ["task"], "questions": [{}],
            "generators": {"task": {"generator_sha256": sha(sources[selected]), "rule_task_id": "task"}},
        }
        manifest_raw = canonical(manifest)
        for name, raw in sources.items():
            target = owner / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (owner / "PACKET-MANIFEST.json").write_bytes(manifest_raw)
        original = base / "original.zip"
        with zipfile.ZipFile(original, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("WORK/PACKET-MANIFEST.json", manifest_raw)
            for name, raw in sources.items():
                z.writestr("WORK/" + name, raw)
            for name, raw in entry.items():
                z.writestr(name, raw)
        verified = base / "verified.json"
        verified.write_bytes(canonical(verify(original)))
        after = b"raise RuntimeError('returned generator must not execute')\n"
        new = b"raise RuntimeError('returned test must not execute')\n"
        (owner / selected).write_bytes(after)
        (owner / added).parent.mkdir(parents=True)
        (owner / added).write_bytes(new)
        patch = "diff --git a/{0} b/{0}\n".format(selected)
        patch += "".join(difflib.unified_diff(sources[selected].decode().splitlines(True), after.decode().splitlines(True), fromfile="a/" + selected, tofile="b/" + selected))
        patch += "diff --git a/{0} b/{0}\nnew file mode 100644\n".format(added)
        patch += "".join(difflib.unified_diff([], new.decode().splitlines(True), fromfile="/dev/null", tofile="b/" + added))
        contract = {"schema": "arcpuzzles-full-assignment-v2", "packet_id": sha(manifest_raw),
                    "assignment_id": "review-0123456789abcdef", "task_id": "task",
                    "generator": manifest["generators"]["task"], "question": {},
                    "baseline_sha256": {selected: sha(sources[selected])}}
        payload = {name: b"Synthetic fixture.\n" for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md")}
        payload["patches/source.patch"] = patch.encode()
        result = {"schema": "arcpuzzles-full-results-v2", "assignment_id": contract["assignment_id"],
                  "completion_state": "blocked", "artifacts": [{"path": k, "kind": "fixture", "sha256": sha(v)} for k, v in payload.items()]}
        returned = base / "return.zip"
        with zipfile.ZipFile(returned, "w") as z:
            z.writestr("ASSIGNMENT.json", canonical(contract))
            z.writestr("RESULTS.json", canonical(result))
            for name, raw in payload.items():
                z.writestr(name, raw)
        out = base / "replay"
        command = [sys.executable, "-B", str(TOOL), "--source-zip", str(original), "--return-zip", str(returned),
                   "--compare-work", str(owner), "--source-verification", str(verified), "--out", str(out)]
        return owner, original, verified, out, command

    def test_applies_authenticated_patch_and_compares_new_files_without_execution(self):
        self.assertTrue(TOOL.is_file(), "manual replay utility is missing")
        with tempfile.TemporaryDirectory() as temp:
            owner, original, verified, out, command = self.fixture(Path(temp))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((out / "replay.json").read_text())
            self.assertEqual(receipt["status"], "manual_patch_replay_passed_tests_pending")
            self.assertEqual(receipt["git_top_level"], str(out / "checkout/WORK"))
            self.assertFalse(receipt["tests_run"])
            self.assertFalse(receipt["official_runtime_closure"])
            self.assertEqual(receipt["new_paths"], ["repo/generators/task/tests/test_added.py"])
            self.assertEqual(len(receipt["changed_files"]), 2)
            self.assertFalse((out / "checkout/WORK/repo/shared/data/derived/omit.jsonl").exists())
            for row in receipt["changed_files"]:
                self.assertEqual((out / "checkout/WORK" / row["path"]).read_bytes(), (owner / row["path"]).read_bytes())

    def test_wrong_comparison_bytes_fail_visibly(self):
        self.assertTrue(TOOL.is_file(), "manual replay utility is missing")
        with tempfile.TemporaryDirectory() as temp:
            owner, original, verified, out, command = self.fixture(Path(temp))
            (owner / "repo/generators/task/generator.py").write_bytes(b"different final bytes\n")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads((out / "replay.json").read_text())["status"], "failed")

    def test_unsafe_archive_is_rejected_before_output_creation(self):
        self.assertTrue(TOOL.is_file(), "manual replay utility is missing")
        with tempfile.TemporaryDirectory() as temp:
            owner, original, verified, out, command = self.fixture(Path(temp))
            with zipfile.ZipFile(original, "a") as z:
                z.writestr("../escape", b"unsafe")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
