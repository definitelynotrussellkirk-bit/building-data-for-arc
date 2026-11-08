from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import generator_worker_feedback as feedback


class GeneratorWorkerFeedbackTests(unittest.TestCase):
    def test_ingest_respond_and_export_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "coordination.sqlite3"
            assignment_path = root / "ASSIGNMENT.json"
            results_path = root / "RESULTS.json"
            response_path = root / "CODEX-RESPONSE.json"
            assignment_path.write_text(
                json.dumps(
                    {
                        "copy_id": "batch-slot-001",
                        "assignments": [{"task_id": "0123456789ab"}],
                    }
                )
            )
            results_path.write_text(
                json.dumps(
                    {
                        "assignment_copy_id": "batch-slot-001",
                        "worker_id": "worker-1",
                        "tasks": [
                            {
                                "task_id": "0123456789ab",
                                "associated_notes": [
                                    {
                                        "note_key": "border_alignment",
                                        "category": "design_decision",
                                        "summary": "Align away from the missing border.",
                                        "rationale": "All canonical open frames agree.",
                                        "evidence": ["4/4 canonical pairs"],
                                        "future_check": "Recheck if a two-side-open frame appears.",
                                    }
                                ],
                            }
                        ],
                        "feedback_to_codex": {
                            "summary": "One gate gap.",
                            "response_requested": True,
                            "items": [
                                {
                                    "local_id": "WFB-001",
                                    "task_id": "0123456789ab",
                                    "category": "harness",
                                    "severity": "warning",
                                    "summary": "Divider mutation is missing.",
                                    "evidence": ["20/20 mutations passed"],
                                    "suggested_action": "Add the mutation.",
                                    "confidence": "high",
                                    "response_requested": True,
                                    "blocks_completion": False,
                                }
                            ],
                        },
                    }
                )
            )

            first = feedback.ingest_response(
                results_path,
                assignment_path,
                db_path=database,
            )
            second = feedback.ingest_response(
                results_path,
                assignment_path,
                db_path=database,
            )
            self.assertEqual(first["inserted"], ["EWF-000001"])
            self.assertEqual(second["existing"], ["EWF-000001"])
            self.assertEqual(first["notes_inserted"], ["GNOTE-000001"])
            self.assertEqual(second["notes_existing"], ["GNOTE-000001"])

            notes = feedback.associated_notes(
                database,
                task_id="0123456789ab",
            )
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["note_key"], "border_alignment")
            self.assertTrue(notes[0]["is_current"])

            inbox = feedback.inbox(database)
            self.assertEqual(len(inbox), 1)
            self.assertEqual(inbox[0]["local_id"], "WFB-001")
            self.assertTrue(inbox[0]["response_requested"])

            answered = feedback.respond(
                "EWF-000001",
                disposition="implemented",
                message="Added the focused divider mutation.",
                evidence=["commit abc123"],
                db_path=database,
            )
            self.assertEqual(answered["disposition"], "implemented")
            self.assertEqual(feedback.inbox(database), [])

            exported = feedback.export_responses(
                "batch-slot-001",
                response_path,
                db_path=database,
            )
            self.assertEqual(exported["responses"][0]["local_id"], "WFB-001")
            self.assertEqual(
                exported["responses"][0]["evidence"],
                ["commit abc123"],
            )
            self.assertEqual(json.loads(response_path.read_text()), exported)

    def test_new_note_version_supersedes_but_preserves_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "coordination.sqlite3"
            base = {
                "task_id": "0123456789ab",
                "note_key": "semantic_choice",
                "category": "design_decision",
                "summary": "First interpretation.",
                "rationale": "Initial canonical read.",
                "evidence": ["pair 1"],
                "future_check": "Inspect held-out symmetry.",
            }
            with feedback.connect(database) as connection:
                first_id, inserted = feedback.store_associated_note(
                    connection,
                    base,
                    worker_id="codex",
                    source_results="manual",
                )
                updated = dict(base)
                updated["summary"] = "Revised interpretation."
                second_id, inserted_second = feedback.store_associated_note(
                    connection,
                    updated,
                    worker_id="codex",
                    source_results="manual",
                )
                connection.commit()
            self.assertTrue(inserted)
            self.assertTrue(inserted_second)
            self.assertNotEqual(first_id, second_id)
            current = feedback.associated_notes(
                database,
                task_id="0123456789ab",
            )
            history = feedback.associated_notes(
                database,
                task_id="0123456789ab",
                include_history=True,
            )
            self.assertEqual([second_id], [current[0]["note_id"]])
            self.assertEqual(2, len(history))
            self.assertEqual(first_id, current[0]["supersedes_note_id"])

    def test_rejects_feedback_for_unassigned_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            assignment_path = root / "ASSIGNMENT.json"
            results_path = root / "RESULTS.json"
            assignment_path.write_text(
                json.dumps(
                    {
                        "copy_id": "copy",
                        "assignments": [{"task_id": "0123456789ab"}],
                    }
                )
            )
            results_path.write_text(
                json.dumps(
                    {
                        "assignment_copy_id": "copy",
                        "worker_id": "worker",
                        "feedback_to_codex": {
                            "summary": "Bad scope.",
                            "response_requested": True,
                            "items": [
                                {
                                    "local_id": "WFB-001",
                                    "task_id": "ffffffffffff",
                                    "summary": "Outside assignment.",
                                    "evidence": ["scope mismatch"],
                                }
                            ],
                        },
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "not in ASSIGNMENT"):
                feedback.ingest_response(
                    results_path,
                    assignment_path,
                    db_path=root / "db.sqlite3",
                )

    def test_partial_intake_preserves_scope_without_dropping_assigned_feedback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            assignment_path = root / "ASSIGNMENT.json"
            results_path = root / "RESULTS.json"
            assignment_path.write_text(
                json.dumps(
                    {
                        "copy_id": "copy",
                        "assignments": [{"task_id": "0123456789ab"}],
                    }
                )
            )
            results_path.write_text(
                json.dumps(
                    {
                        "assignment_copy_id": "copy",
                        "worker_id": "worker",
                        "feedback_to_codex": {
                            "items": [
                                {
                                    "local_id": "WFB-OWN",
                                    "task_id": "0123456789ab",
                                    "summary": "Assigned-task finding.",
                                    "evidence": ["assigned evidence"],
                                },
                                {
                                    "local_id": "WFB-PEER",
                                    "task_id": "ffffffffffff",
                                    "summary": "Peer-task finding.",
                                    "evidence": ["peer evidence"],
                                },
                            ]
                        },
                    }
                )
            )
            database = root / "db.sqlite3"
            result = feedback.ingest_response(
                results_path,
                assignment_path,
                db_path=database,
                allow_out_of_scope=True,
            )
            self.assertEqual(result["inserted"], ["EWF-000001"])
            self.assertEqual(
                result["out_of_scope"],
                [
                    {
                        "local_id": "WFB-PEER",
                        "task_id": "ffffffffffff",
                        "summary": "Peer-task finding.",
                    }
                ],
            )
            self.assertEqual(
                [item["local_id"] for item in feedback.inbox(database)],
                ["WFB-OWN"],
            )


if __name__ == "__main__":
    unittest.main()
