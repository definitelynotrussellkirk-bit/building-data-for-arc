import json
from pathlib import Path

from scripts.generator_battery_subject import compute_subject


TASK = "abc123abc123"


def _fixture(root: Path) -> Path:
    generator = root / "puzzle_generators/per_puzzle" / TASK / "generator.py"
    generator.parent.mkdir(parents=True)
    generator.write_text('TASK_ID = "abc123abc123"\n', encoding="utf-8")
    canonical = root / "data/canonical/puzzles.jsonl"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        json.dumps({"task_id": TASK, "program_solution": "(rule! canonical)"})
        + "\n",
        encoding="utf-8",
    )
    base = root / "data/base/solutions/training/authority.json"
    base.parent.mkdir(parents=True)
    base.write_text(
        json.dumps(
            {
                "task_id": TASK,
                "racket_target": {
                    "canonicalization_status": "selected",
                    "code_form": "legacy_lambda_g",
                    "target_status": "verified_racket_available",
                    "target_code": "(rule! selected)",
                    "raw_code": "(rule! archival)",
                },
            }
        ),
        encoding="utf-8",
    )
    return base


def test_selected_source_only_edit_invalidates_subject(tmp_path: Path) -> None:
    base = _fixture(tmp_path)
    before = compute_subject(tmp_path, TASK)
    row = json.loads(base.read_text(encoding="utf-8"))
    row["racket_target"]["target_code"] = "(rule! selected-v2)"
    base.write_text(json.dumps(row), encoding="utf-8")
    after = compute_subject(tmp_path, TASK)

    assert after["generator_file_sha256"] == before["generator_file_sha256"]
    assert after["authority_set_sha256"] != before["authority_set_sha256"]
    assert after["battery_subject_sha16"] != before["battery_subject_sha16"]


def test_archival_source_and_role_metadata_invalidate_subject(tmp_path: Path) -> None:
    base = _fixture(tmp_path)
    before = compute_subject(tmp_path, TASK)
    row = json.loads(base.read_text(encoding="utf-8"))
    row["racket_target"]["raw_code"] = "(rule! archival-v2)"
    row["racket_target"]["canonicalization_status"] = "role-updated"
    base.write_text(json.dumps(row), encoding="utf-8")
    after = compute_subject(tmp_path, TASK)

    assert after["authority_set_sha256"] != before["authority_set_sha256"]
    assert after["battery_subject_sha16"] != before["battery_subject_sha16"]


def test_unrelated_task_authority_does_not_change_subject(tmp_path: Path) -> None:
    base = _fixture(tmp_path)
    before = compute_subject(tmp_path, TASK)
    other = base.with_name("other.json")
    other.write_text(
        json.dumps(
            {
                "task_id": "ffffffffffff",
                "racket_target": {"target_code": "changed elsewhere"},
            }
        ),
        encoding="utf-8",
    )

    assert compute_subject(tmp_path, TASK) == before


def test_generic_program_is_source_bound_authority(tmp_path: Path) -> None:
    task_id = "generic_hole_count_key_gen1"
    generator = (
        tmp_path
        / "puzzle_generators/generic/concepts/hole_count_key/gen1.py"
    )
    generator.parent.mkdir(parents=True)
    generator.write_text(
        'TASK_ID = "generic_hole_count_key_gen1"\nPROGRAM = "(rule! first)"\n',
        encoding="utf-8",
    )
    before = compute_subject(tmp_path, task_id)
    generator.write_text(
        'TASK_ID = "generic_hole_count_key_gen1"\nPROGRAM = "(rule! second)"\n',
        encoding="utf-8",
    )
    after = compute_subject(tmp_path, task_id)

    assert before["authority_set_sha256"] != after["authority_set_sha256"]
    assert before["battery_subject_sha16"] != after["battery_subject_sha16"]
