import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_candidate import check_full_candidate
from arcpuzzles.review_full_integrate import integrate_full_candidate


@pytest.mark.parametrize("workspace_layout", [False, True])
def test_relocated_full_packet_round_trip(library, tmp_path, workspace_layout):
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(source / "src", library / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (library / "README.md").write_text("portable fixture\n")
    question = library / "REVIEW/questions/q.json"
    question.parent.mkdir(parents=True)
    question.write_text(json.dumps({"schema": "arcpuzzles-review-question-v1", "id": "q",
                              "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    (library / "generators/aaaa00000003/workspace").mkdir()
    (library / "generators/aaaa00000003/workspace/probe.txt").write_text("local notes\n")
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "request.zip", workspace_layout=workspace_layout)
    relocated = tmp_path / "isolated/packet"
    relocated.mkdir(parents=True)
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(relocated)
    outer = relocated
    if workspace_layout:
        relocated = outer / "WORK"
    assert len(list((relocated / "repo/generators").glob("*/generator.py"))) == 3
    assert (relocated / "repo/generators/aaaa00000003/workspace/probe.txt").is_file()
    welcome = (relocated / "WELCOME.md").read_text()
    assert "python3 assignment.py" in welcome
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("ARCPUZZLES_HOME", None)
    drawn = subprocess.run([sys.executable, str(outer / "review.py"), "start"] if workspace_layout
                           else [sys.executable, "assignment.py"], cwd=relocated, env=env,
                           capture_output=True, text=True, timeout=30)
    assert drawn.returncode == 0, drawn.stderr
    contract = json.loads((relocated / "ASSIGNMENT.json").read_text())
    tid = contract["task_id"]
    check_env = {**env, "PYTHONPATH": "src"}
    for phase in ("before", "after"):
        if phase == "after":
            (relocated / f"repo/generators/{tid}/generator.py").write_text("VERSION = '2.0'\n")
        subprocess.run([sys.executable, "-m", "arcpuzzles", "check", tid, "--battery", "--out",
                        f"../checks/{phase}"], cwd=relocated / "repo", env=check_env,
                       capture_output=True, text=True, timeout=40)
        assert (relocated / f"checks/{phase}/result.json").is_file()
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (relocated / name).write_text(f"{name}: reviewed {tid}\n")
    (relocated / "RESULTS.json").write_text(json.dumps({"completion_state": "complete",
                                                         "stopping_reason": "fixture round trip"}))
    subprocess.run([sys.executable, str(outer / "review.py"), "audit"] if workspace_layout
                   else [sys.executable, "assignment.py", "audit"], cwd=relocated, env=env,
                   check=True, capture_output=True, text=True, timeout=30)
    audit = json.loads((relocated / "AUDIT_ASSIGNMENT.json").read_text())
    (relocated / "AUDIT.md").write_text("".join(
        f"## {row['task_id']}\nFound one rival rule to probe\n\n" for row in audit["targets"]))
    returned = tmp_path / "review_response_relocated.zip"
    packaged = subprocess.run(([sys.executable, str(outer / "review.py"), "package"] if workspace_layout
                               else [sys.executable, "package_return.py"]) + ["--out", str(returned)],
                              cwd=relocated, env=env, capture_output=True, text=True, timeout=40)
    assert packaged.returncode == 0, packaged.stderr
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    assert any(r.get("assignment_id") == contract["assignment_id"] and r["validation_status"] == "accepted"
               for r in collected["receipts"])
    checked = check_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"], 1, timeout=3)
    assert Path(checked["receipt_path"]).is_file()
    assert checked["candidate_path"].startswith(str(library / "var/review"))
    assert (library / f"generators/{tid}/generator.py").read_text() != "VERSION = '2.0'\n"
    assert (Path(checked["candidate_path"]) / f"repo/generators/{tid}/generator.py").read_text() == "VERSION = '2.0'\n"
    with zipfile.ZipFile(returned) as archive:
        assert "ASSIGNMENT.json" in archive.namelist()
        assert not any(name.startswith("WORK/") for name in archive.namelist())
    integrated = integrate_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"],
                                         1, {"generator"}, reviewer_reported=True)
    assert integrated["status"] == "integrated"
    assert (library / f"generators/{tid}/generator.py").read_text() == "VERSION = '2.0'\n"
    assert Catalog(library).describe(tid)["approved"]


def test_operator_handoff_documents_one_zip_and_batch_intake():
    source = Path(__file__).resolve().parents[1]
    review = (source / "REVIEW/README.md").read_text()
    for command in ("review pack-full", "review collect", "review inbox", "review check", "review integrate"):
        assert command in review
