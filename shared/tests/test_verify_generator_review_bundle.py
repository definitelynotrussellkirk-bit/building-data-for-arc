from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts import verify_generator_review_bundle as verifier


class VerifyGeneratorReviewBundleTests(unittest.TestCase):
    def make_bundle(self, root: Path) -> Path:
        bundle = root / "2"
        repo = bundle / "repo"
        for relative in verifier.REQUIRED_BUNDLE_PATHS:
            path = bundle / relative
            if path.suffix or path.name in {
                "AGENTS.md",
                "CLAUDE.md",
                "GUIDE",
                "KIMIgeneratorASSIGNMENT.md",
                "README.md",
                "requirements.txt",
                "tests",
                "docs",
                "src",
            }:
                if path.name in {"GUIDE", "tests", "docs", "src"}:
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("fixture\n", encoding="utf-8")
            else:
                path.mkdir(parents=True, exist_ok=True)

        question_ids = [f"QT-{index:012x}" for index in range(1, 9)]
        bank = bundle / "questions/bank"
        bank.mkdir(parents=True, exist_ok=True)
        for question_id in question_ids:
            (bank / f"{question_id}.json").write_text(
                json.dumps(
                    {
                        "question_id": question_id,
                        "status": "open",
                        "priority": 1,
                    }
                ),
                encoding="utf-8",
            )
        (bundle / "STRATEGY-REVIEW-CADENCE.json").write_text(
            json.dumps(
                {
                    "round_size": 8,
                    "target_mix": {
                        "qwen": 4,
                        "supervision": 2,
                        "other_models": 1,
                        "unrestricted_random": 1,
                    },
                    "round_buckets": {
                        "qwen": question_ids[:4],
                        "supervision": question_ids[4:6],
                        "other_models": question_ids[6:7],
                    },
                }
            ),
            encoding="utf-8",
        )
        (bundle / "PACKET-CONFIG.json").write_text(
            json.dumps({"contract_version": 16}), encoding="utf-8"
        )
        (bundle / "CURRENT-GENERATOR-WORKER.md").write_text(
            "# Worker\n\nCONTRACT_VERSION: 16 (fixture).\n", encoding="utf-8"
        )

        rows = [
            {
                "task_id": "base_task",
                "kind": "per_puzzle",
                "path": "puzzle_generators/per_puzzle/base_task/generator.py",
                "rule_authority": "data/canonical/puzzles.jsonl",
                "status": "pending",
                "train_safety": "unsafe",
            },
            {
                "task_id": "canonical_task",
                "kind": "per_puzzle",
                "path": (
                    "puzzle_generators/per_puzzle/canonical_task/generator.py"
                ),
                "rule_authority": "data/canonical/puzzles.jsonl",
                "status": "pending",
                "train_safety": "unverified",
            },
            {
                "task_id": "generic_family_gen1",
                "kind": "generic",
                "path": (
                    "puzzle_generators/generic/concepts/family/gen1.py"
                ),
                "status": "pending",
                "train_safety": "caution",
            },
        ]
        queue = (
            repo / "data/derived/kimi_generator_assignment.jsonl"
        )
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        notes = repo / "data/derived/generator_associated_notes.jsonl"
        notes.write_text("", encoding="utf-8")
        canonical = repo / "data/canonical/puzzles.jsonl"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text(
            '{"task_id":"canonical_task"}\n',
            encoding="utf-8",
        )
        (repo / "data/canonical/puzzle_db.jsonl").write_text(
            "", encoding="utf-8"
        )
        authority = (
            repo / "data/base/solutions/training/aliased_source.json"
        )
        authority.parent.mkdir(parents=True, exist_ok=True)
        authority.write_text(
            '{"task_id":"base_task"}\n',
            encoding="utf-8",
        )
        for row in rows:
            generator = repo / row["path"]
            generator.parent.mkdir(parents=True, exist_ok=True)
            generator.write_text("VERSION = 'test'\n", encoding="utf-8")
        return bundle

    def test_all_candidate_authority_modes_are_covered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.make_bundle(Path(directory))
            manifest, errors = verifier.verify_bundle(bundle)
            self.assertEqual([], errors)
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(3, manifest["eligible_assignment_count"])
            self.assertEqual(
                {
                    "canonical_only": 1,
                    "generic_embedded_program": 1,
                    "task_local_base": 1,
                },
                manifest["authority_coverage"],
            )

    def test_missing_candidate_generator_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.make_bundle(Path(directory))
            (
                bundle
                / "repo/puzzle_generators/per_puzzle/base_task/generator.py"
            ).unlink()
            _, errors = verifier.verify_bundle(bundle)
            self.assertTrue(
                any("lack generators" in error for error in errors),
                errors,
            )

    def test_missing_canonical_task_row_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.make_bundle(Path(directory))
            (
                bundle / "repo/data/canonical/puzzles.jsonl"
            ).write_text("", encoding="utf-8")
            _, errors = verifier.verify_bundle(bundle)
            self.assertTrue(
                any("neither a task-local base" in error for error in errors),
                errors,
            )

    def test_malformed_strategy_mix_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.make_bundle(Path(directory))
            cadence_path = bundle / "STRATEGY-REVIEW-CADENCE.json"
            cadence = json.loads(cadence_path.read_text(encoding="utf-8"))
            cadence["target_mix"]["qwen"] = 3
            cadence_path.write_text(json.dumps(cadence), encoding="utf-8")
            _, errors = verifier.verify_bundle(bundle)
            self.assertTrue(
                any("does not sum to round_size" in error for error in errors),
                errors,
            )

    def test_worker_guide_contract_version_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.make_bundle(Path(directory))
            (bundle / "CURRENT-GENERATOR-WORKER.md").write_text(
                "CONTRACT_VERSION: 14 (stale).\n", encoding="utf-8"
            )
            manifest, errors = verifier.verify_bundle(bundle)
            self.assertEqual(16, manifest["contract_version"])
            self.assertTrue(
                any("disagrees with PACKET-CONFIG.json" in error for error in errors),
                errors,
            )


if __name__ == "__main__":
    unittest.main()
