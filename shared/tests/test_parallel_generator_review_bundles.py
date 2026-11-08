from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts import make_parallel_generator_review_bundles as bundles


class ParallelGeneratorReviewBundleTests(unittest.TestCase):
    def test_authority_discovery_uses_json_task_id_not_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            authority = (
                root
                / "data/base/solutions/augmented/source__alias.json"
            )
            authority.parent.mkdir(parents=True)
            authority.write_text(
                '{"task_id": "assigned-task"}\n',
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "init", "-q"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "add", "."],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                cwd=root,
                check=True,
            )

            found = bundles.committed_task_authorities(
                "assigned-task",
                root,
            )

            self.assertEqual(
                {
                    "2/repo/data/base/solutions/augmented/"
                    "source__alias.json"
                },
                set(found),
            )

    def test_assigned_copy_requires_guide_and_refuses_second_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(bundles.WORKER_GUIDE_MEMBER, "guide\n")
                archive.writestr(bundles.FEEDBACK_GUIDE_MEMBER, "feedback\n")
                archive.writestr(bundles.RESULT_SCHEMA_MEMBER, "{}\n")
                archive.writestr(bundles.RESPONSE_SCHEMA_MEMBER, "{}\n")
            first = root / "first.zip"
            manifest = {"schema_version": 1, "assignments": [{"task_id": "a"}]}

            bundles.write_assigned_copy(source, first, manifest)

            with zipfile.ZipFile(first) as archive:
                stored = json.loads(archive.read(bundles.ASSIGNMENT_MEMBER))
            self.assertEqual(stored, manifest)
            with self.assertRaises(bundles.BundleError):
                bundles.write_assigned_copy(first, root / "second.zip", manifest)

    def test_manifest_records_hashes_and_candidate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "2.zip"
            generator_payload = b"VERSION = '1'\n"
            canonical_payload = b'{"task_id":"abc"}\n'
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("2/repo/generator.py", generator_payload)
                archive.writestr(
                    "2/repo/data/canonical/puzzles.jsonl",
                    canonical_payload,
                )
            row = {
                "task_id": "abc",
                "kind": "per_puzzle",
                "path": "generator.py",
                "status": "pending",
                "rule_hash_expected": "123456789abc",
                "findings": ["missing_rule_hash"],
                "finding_taxonomy": {
                    "source_authority": ["missing_rule_hash"],
                    "generator_oracle_semantics": [],
                },
                "assignment_checklist": {"profile": "per-puzzle-v13"},
            }
            claim = {
                "task_id": "abc",
                "worker": "worker-1",
                "expires_at": "2026-07-23T00:00:00+00:00",
                "selection_seed": 42,
                "candidate_count": 100,
            }

            manifest = bundles.build_manifest(
                batch_id="batch",
                slot=1,
                source_archive=source,
                source_archive_sha256="source-sha",
                base_commit="commit",
                queue_path=root / "queue.jsonl",
                queue_sha256="queue-sha",
                claims=[claim],
                rows={"abc": row},
                assignment_preflights={
                    "abc": {
                        "status": "ok",
                        "canonical_selfcheck_rejection_count": 1,
                        "canonical_selfcheck_error_count": 0,
                        "override_probe_errors": 0,
                        "override_accepted_unconsumed_count": 0,
                        "override_observation_failure_count": 0,
                    }
                },
            )

            assignment = manifest["assignments"][0]
            self.assertEqual(assignment["selection_seed"], 42)
            self.assertEqual(
                ["missing_rule_hash"],
                assignment["finding_taxonomy"]["source_authority"],
            )
            self.assertEqual(assignment["candidate_count"], 100)
            self.assertIn(
                "canonical_selfcheck_rejection",
                assignment["findings"],
            )
            self.assertIn(
                "resolve:canonical_selfcheck_rejection",
                assignment["assignment_checklist"]["repair_focus"],
            )
            self.assertEqual(
                bundles.canonical_digest(row),
                assignment["queue_row_sha256"],
            )
            self.assertEqual(
                "uniform_random",
                assignment["selection_strategy"],
            )
            self.assertEqual(
                assignment["generator_sha256"],
                bundles.archive_member_sha256(
                    source, "2/repo/generator.py"
                ),
            )
            self.assertEqual("canonical_only", assignment["authority_mode"])
            self.assertEqual(
                [
                    {
                        "path": "2/repo/data/canonical/puzzles.jsonl",
                        "repo_relpath": "data/canonical/puzzles.jsonl",
                        "sha256": bundles.archive_member_sha256(
                            source,
                            "2/repo/data/canonical/puzzles.jsonl",
                        ),
                    }
                ],
                assignment["authority_files"],
            )
            self.assertEqual("bundle_root", manifest["authority_path_base"])
            self.assertEqual("2/repo", manifest["repository_member_root"])
            self.assertTrue(manifest["return_policy"]["status_is_candidate_only"])
            self.assertTrue(
                manifest["return_policy"]["feedback_to_codex_required"]
            )
            self.assertTrue(
                manifest["return_policy"]["codex_response_supported"]
            )
            self.assertEqual(
                manifest["feedback_channel"]["worker_to_codex"]["results_field"],
                "feedback_to_codex",
            )
            self.assertEqual(
                manifest["feedback_channel"]["codex_to_worker"]["member"],
                "CODEX-RESPONSE.json",
            )

    def test_tar_zst_assigned_copy_contains_immutable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tree = root / "tree/2"
            for member in (
                bundles.WORKER_GUIDE_MEMBER,
                bundles.FEEDBACK_GUIDE_MEMBER,
                bundles.RESULT_SCHEMA_MEMBER,
                bundles.RESPONSE_SCHEMA_MEMBER,
            ):
                target = root / "tree" / member
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture\n", encoding="utf-8")
            source = root / "source.tar.zst"
            subprocess.run(
                [
                    "tar",
                    "-I",
                    "zstd",
                    "-cf",
                    str(source),
                    "-C",
                    str(tree.parent),
                    "2",
                ],
                check=True,
            )
            destination = root / "assigned.tar.zst"
            manifest = {
                "schema_version": 1,
                "assignments": [{"task_id": "a"}],
            }

            bundles.write_assigned_copy(source, destination, manifest)

            stored = json.loads(
                bundles.archive_member_bytes(
                    destination, bundles.ASSIGNMENT_MEMBER
                )
            )
            self.assertEqual(manifest, stored)
            with self.assertRaises(bundles.BundleError):
                bundles.write_assigned_copy(
                    destination,
                    root / "second.tar.zst",
                    manifest,
                )


if __name__ == "__main__":
    unittest.main()
