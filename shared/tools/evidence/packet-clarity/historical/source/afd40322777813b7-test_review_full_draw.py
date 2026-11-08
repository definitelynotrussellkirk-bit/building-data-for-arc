import json
import shutil
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main, draw_audit


def _packet(library, tmp_path, **options):
    questions = library / "REVIEW/questions"
    questions.mkdir(parents=True)
    (questions / "q.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1",
        "id": "q", "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "request.zip", **options)
    packet = tmp_path / "packet"
    packet.mkdir()
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(packet)
    return packet


def test_main_draw_is_stable_and_reproducible(library, tmp_path):
    packet = _packet(library, tmp_path)
    first = draw_main(packet, (2).to_bytes(32, "big"))
    assert first["task_id"] == "aaaa00000003"
    assert first["question"]["id"] == "q"
    assert first["schema"] == "arcpuzzles-full-assignment-v2"
    before = (packet / "ASSIGNMENT.json").read_bytes()
    (packet / "repo/generators/aaaa00000003/generator.py").write_text("changed\n")
    assert draw_main(packet, bytes([2]) * 32) == first
    assert (packet / "ASSIGNMENT.json").read_bytes() == before
    assert (packet / "DUTIES.md").is_file()


def test_draw_provides_editable_result_record_without_overwriting_it(library, tmp_path):
    packet = _packet(library, tmp_path)
    draw_main(packet, (2).to_bytes(32, "big"))
    result_path = packet / "RESULTS.json"
    result = json.loads(result_path.read_text())
    assert result["completion_state"] == "in_progress"
    assert result["verification_commands"] == []
    result_path.write_text('{"completion_state": "blocked", "stopping_reason": "Missing Racket"}\n')
    draw_main(packet, bytes([3]) * 32)
    assert json.loads(result_path.read_text())["stopping_reason"] == "Missing Racket"


def test_audit_draw_can_select_approved_and_repeat(library, tmp_path):
    packet = _packet(library, tmp_path)
    draw_main(packet, (2).to_bytes(32, "big"))
    audit = draw_audit(packet, bytes(32))
    assert [row["task_id"] for row in audit["targets"]][0] == "aaaa00000001"
    assert len({row["task_id"] for row in audit["targets"]}) == 2
    assert draw_audit(packet, bytes([3]) * 32) == audit
    assert audit["schema"] == "arcpuzzles-full-audit-v3"


def test_audit_can_draw_main_generator_after_its_working_source_changes(library, tmp_path):
    packet = _packet(library, tmp_path)
    draw_main(packet, (2).to_bytes(32, "big"))
    (packet / "repo/generators/aaaa00000003/generator.py").write_text("improved\n")
    audit = draw_audit(packet, (2).to_bytes(32, "big"))
    assert "aaaa00000003" in [row["task_id"] for row in audit["targets"]]


def test_tampered_manifest_or_selected_source_fails_before_assignment(library, tmp_path):
    packet = _packet(library, tmp_path)
    (packet / "repo/generators/aaaa00000003/generator.py").write_text("tampered")
    with pytest.raises(ValueError):
        draw_main(packet, (2).to_bytes(32, "big"))
    assert not (packet / "ASSIGNMENT.json").exists()


def test_welcome_is_sufficient_to_find_draw_command(library, tmp_path):
    packet = _packet(library, tmp_path)
    welcome = (packet / "WELCOME.md").read_text()
    assert "START-HERE.md" in welcome
    assert "DUTIES.md" in welcome
    assert "RETURN-GUIDE.md" in welcome
    draw_main(packet, (2).to_bytes(32, "big"))
    duties = (packet / "DUTIES.md").read_text()
    for word in ("before", "after", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md", "audit"):
        assert word in duties
    assert "two" in duties.lower()
    assert "linter" in duties.lower()
    assert "check only" in welcome.lower()


@pytest.mark.parametrize('tickets', [False, True])
def test_assignment_header_names_editable_paths_and_immutable_root_tests(library, tmp_path, tickets):
    packet = _packet(library, tmp_path, supplementary_tickets=tickets)
    assignment = draw_main(packet, (2).to_bytes(32, 'big'))
    intro = (packet / 'DUTIES.md').read_text().split('\n1.', 1)[0]
    assert f"repo/generators/{assignment['task_id']}/" in intro
    for path in ['generator.py', 'notes.md', 'SUMMARY.md', 'tests/', 'workspace/', 'counterexamples/']:
        assert f'`{path}`' in intro
    assert '`test_generator_*.py`' in intro and 'immutable' in intro


def test_check_help_states_required_audit_phase():
    from arcpuzzles.cli import parser
    check = parser()._subparsers._group_actions[0].choices['check']
    assert 'audit requires --phase audit' in ' '.join(check.format_help().split())
