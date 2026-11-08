from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import bootstrap_random_generator_assignment as bootstrap


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/bootstrap_random_generator_assignment.py"


class BootstrapRandomGeneratorAssignmentTests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        queue = repo / "data/derived/kimi_generator_assignment.jsonl"
        queue.parent.mkdir(parents=True)
        rows = [
            {
                "task_id": "already_safe",
                "path": "puzzle_generators/per_puzzle/already_safe/generator.py",
                "status": "complete",
                "train_safety": "reviewed_safe",
            },
            {
                "task_id": "semantic_veto",
                "path": "puzzle_generators/per_puzzle/semantic_veto/generator.py",
                "status": "pending",
                "train_safety": "unverified",
                "active_semantic_veto": True,
            },
            {
                "task_id": "chosen_task",
                "path": "puzzle_generators/per_puzzle/chosen_task/generator.py",
                "status": "pending",
                "train_safety": "unverified",
                "active_semantic_veto": False,
                "kind": "per_puzzle",
                "queue_rank": 17,
                "priority_score": 20,
                "findings": ["missing_rule_hash"],
                "finding_taxonomy": {
                    "source_authority": ["missing_rule_hash"],
                    "generator_oracle_semantics": [],
                },
                "assignment_checklist": {"profile": "per-puzzle-v13"},
            },
        ]
        queue.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        generator = (
            repo
            / "puzzle_generators/per_puzzle/chosen_task/generator.py"
        )
        generator.parent.mkdir(parents=True)
        generator.write_text("VERSION = 'test'\n", encoding="utf-8")
        authority = (
            repo
            / "data/base/solutions/training/source__chosen_task.json"
        )
        authority.parent.mkdir(parents=True)
        authority.write_text('{"task_id": "chosen_task"}\n', encoding="utf-8")
        return repo, generator

    def test_creates_hashed_random_receipt_for_only_eligible_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, generator = self.make_repo(root)
            output = root / "ASSIGNMENT.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                    "--worker-id",
                    "unit-worker",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            receipt = json.loads(output.read_text(encoding="utf-8"))
            assignment = receipt["assignments"][0]
            self.assertEqual("chosen_task", assignment["task_id"])
            self.assertEqual("unit-worker", assignment["worker_id"])
            self.assertEqual(1, assignment["candidate_count"])
            self.assertEqual(
                hashlib.sha256(generator.read_bytes()).hexdigest(),
                assignment["generator_sha256"],
            )
            authority = (
                repo
                / "data/base/solutions/training/source__chosen_task.json"
            )
            self.assertEqual(
                "task_local_base",
                assignment["authority_mode"],
            )
            self.assertEqual(
                ["missing_rule_hash"],
                assignment["finding_taxonomy"]["source_authority"],
            )
            self.assertEqual(
                [
                    {
                        "path": (
                            "2/repo/data/base/solutions/training/"
                            "source__chosen_task.json"
                        ),
                        "repo_relpath": (
                            "data/base/solutions/training/"
                            "source__chosen_task.json"
                        ),
                        "sha256": hashlib.sha256(
                            authority.read_bytes()
                        ).hexdigest(),
                    }
                ],
                assignment["authority_files"],
            )
            self.assertEqual(
                "disconnected_local_random",
                receipt["selection_mode"],
            )
            self.assertEqual(
                "priority_weighted_random_returned_repair_avoiding",
                receipt["selection_strategy"],
            )
            self.assertEqual("bundle_root", receipt["authority_path_base"])
            self.assertEqual("2/repo", receipt["repository_member_root"])
            self.assertFalse(
                receipt["collision_control"]["centrally_reserved"]
            )
            self.assertEqual(
                0,
                receipt["collision_control"][
                    "returned_repair_tasks_excluded"
                ],
            )
            self.assertTrue(
                receipt["return_policy"]["feedback_to_codex_required"]
            )
            self.assertEqual(
                "chosen_task",
                json.loads(result.stdout)["task_id"],
            )

    def test_avoids_tasks_already_in_returned_repair_ledger(self) -> None:
        candidates = [
            {"task_id": "already_returned"},
            {"task_id": "fresh_task"},
        ]

        filtered, excluded, fallback = bootstrap.avoid_returned_repairs(
            candidates,
            {"already_returned"},
        )

        self.assertEqual([{"task_id": "fresh_task"}], filtered)
        self.assertEqual(1, excluded)
        self.assertFalse(fallback)

    def test_returned_repair_filter_falls_back_only_when_exhausted(self) -> None:
        candidates = [{"task_id": "already_returned"}]

        filtered, excluded, fallback = bootstrap.avoid_returned_repairs(
            candidates,
            {"already_returned"},
        )

        self.assertEqual(candidates, filtered)
        self.assertEqual(1, excluded)
        self.assertTrue(fallback)

    def test_fresh_preflight_findings_are_added_to_repair_focus(self) -> None:
        row = {
            "task_id": "chosen_task",
            "findings": ["missing_rule_hash"],
            "finding_taxonomy": {
                "source_authority": ["missing_rule_hash"],
                "generator_oracle_semantics": [],
            },
            "assignment_checklist": {
                "repair_focus": ["resolve:missing_rule_hash"]
            },
        }
        preflight = {
            "status": "ok",
            "canonical_selfcheck_rejection_count": 3,
            "canonical_selfcheck_error_count": 0,
            "override_probe_errors": 0,
            "override_accepted_unconsumed_count": 1,
            "override_observation_failure_count": 0,
        }

        merged = bootstrap.merge_assignment_preflight(row, preflight)

        self.assertIn("canonical_selfcheck_rejection", merged["findings"])
        self.assertIn("override_preflight_failure", merged["findings"])
        self.assertIn(
            "resolve:canonical_selfcheck_rejection",
            merged["assignment_checklist"]["repair_focus"],
        )
        self.assertEqual(preflight, merged["assignment_preflight"])
        self.assertEqual(["missing_rule_hash"], row["findings"])

    def test_refuses_to_replace_existing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, _ = self.make_repo(root)
            output = root / "ASSIGNMENT.json"
            output.write_text('{"immutable": true}\n', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                "refusing to replace immutable assignment",
                result.stderr,
            )
            self.assertEqual(
                {"immutable": True},
                json.loads(output.read_text(encoding="utf-8")),
            )

    def test_explicitly_marks_canonical_only_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, _ = self.make_repo(root)
            for path in (repo / "data/base/solutions").rglob("*.json"):
                path.unlink()
            canonical = repo / "data/canonical/puzzles.jsonl"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                '{"task_id": "chosen_task"}\n',
                encoding="utf-8",
            )
            output = root / "ASSIGNMENT.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            assignment = json.loads(
                output.read_text(encoding="utf-8")
            )["assignments"][0]
            self.assertEqual(
                "canonical_only",
                assignment["authority_mode"],
            )
            self.assertEqual(
                "2/repo/data/canonical/puzzles.jsonl",
                assignment["authority_files"][0]["path"],
            )
            self.assertEqual(
                "data/canonical/puzzles.jsonl",
                assignment["authority_files"][0]["repo_relpath"],
            )
            self.assertEqual(
                hashlib.sha256(canonical.read_bytes()).hexdigest(),
                assignment["authority_files"][0]["sha256"],
            )

    def test_finds_task_authority_when_filename_uses_an_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, _ = self.make_repo(root)
            original = next(
                (repo / "data/base/solutions").rglob("*.json")
            )
            alias = original.with_name("source__alias.json")
            original.rename(alias)
            output = root / "ASSIGNMENT.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            files = json.loads(
                output.read_text(encoding="utf-8")
            )["assignments"][0]["authority_files"]
            self.assertEqual(
                ["data/base/solutions/training/source__alias.json"],
                [item["repo_relpath"] for item in files],
            )

    def test_canonical_only_requires_the_assigned_task_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, _ = self.make_repo(root)
            for path in (repo / "data/base/solutions").rglob("*.json"):
                path.unlink()
            canonical = repo / "data/canonical/puzzles.jsonl"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                '{"task_id": "some_other_task"}\n',
                encoding="utf-8",
            )
            output = root / "ASSIGNMENT.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("missing both task-local base", result.stderr)

    def test_generic_assignment_uses_embedded_program_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            queue = repo / "data/derived/kimi_generator_assignment.jsonl"
            queue.parent.mkdir(parents=True)
            generator = (
                repo
                / "puzzle_generators/generic/concepts/family/gen1.py"
            )
            generator.parent.mkdir(parents=True)
            generator.write_text("VERSION = 'test'\n", encoding="utf-8")
            queue.write_text(
                json.dumps(
                    {
                        "task_id": "generic_family_gen1",
                        "path": (
                            "puzzle_generators/generic/concepts/family/gen1.py"
                        ),
                        "kind": "generic",
                        "status": "pending",
                        "train_safety": "caution",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            output = root / "ASSIGNMENT.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    str(output),
                    "--seed",
                    "123",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            assignment = json.loads(
                output.read_text(encoding="utf-8")
            )["assignments"][0]
            self.assertEqual(
                "generic_embedded_program",
                assignment["authority_mode"],
            )
            self.assertEqual(
                "puzzle_generators/generic/concepts/family/gen1.py",
                assignment["authority_files"][0]["repo_relpath"],
            )


if __name__ == "__main__":
    unittest.main()
